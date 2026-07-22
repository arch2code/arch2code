#!/usr/bin/env python3
"""Unit tests for the unified YAML migration orchestrator (migrateYaml.py).

Each test builds a small synthetic project on disk in a temp dir and EXECUTES
the orchestrator end-to-end (the real Phase A eval pass, Phase B address pass,
and Phase C stamp), asserting on the resulting file contents, the combined
report, and the CLI exit code. Nothing is mocked; the phases run over real
files exactly as `make migrate` drives them.

Coverage:
  - a project with a Python-syntax eval AND legacy addressControl converts both
    and is stamped yamlFormat: 2 when the result is clean;
  - a project left with a Phase A NEEDS_MANUAL real eval is not stamped and the
    eval is named in the checklist;
  - a project left with a Phase B manual TODO is not stamped and the TODO is
    named in the checklist;
  - dry-run changes nothing on disk but reports all three phases;
  - an already-yamlFormat: 2 project short-circuits with no writes.
"""

import os
import shutil
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from migrateYaml import migrateProject, renderReport, main
from pysrc.processYaml import CURRENT_YAML_FORMAT


# A Python-syntax eval Phase A rewrites to the SV subset, and its converted form.
_EVAL_PY = "($DEPTH - 1).bit_length()"
_EVAL_SV = "$clog2($DEPTH)"


def _top(*, eval_line, with_interface):
    """Build a top.yaml with a router (apbDecode) resolved from a decoderInstance,
    optionally carrying the register-bus interface in its own scope, plus a
    constants section holding `eval_line`."""
    interface = ("interfaces:\n"
                 "    apbReg:\n"
                 '        desc: "register bus"\n'
                 "        interfaceType: apb\n"
                 "        structures: []\n"
                 "\n") if with_interface else ""
    return (
        "constants:\n"
        f"    DEPTHLOG2: {{ {eval_line}, desc: \"log2 of depth\" }}\n"
        "\n"
        "blocks:\n"
        "    top_tb:\n"
        '        desc: "tb container"\n'
        "    top:\n"
        '        desc: "top container"\n'
        "    apbDecode:\n"
        '        desc: "APB router"\n'
        "\n"
        f"{interface}"
        "instances:\n"
        "    top_tb:   { container: top_tb, instanceType: top_tb }\n"
        "    uTop:     { container: top_tb, instanceType: top }\n"
        "    uApbDec:  { container: top,    instanceType: apbDecode }\n"
    )


# A routed leaf added to the topology forces a Phase B manual registerPorts TODO.
_DIRTY_TOP = (
    "blocks:\n"
    "    top_tb:\n"
    '        desc: "tb container"\n'
    "    top:\n"
    '        desc: "top container"\n'
    "    apbDecode:\n"
    '        desc: "APB router"\n'
    "    leafA:\n"
    '        desc: "routed leaf"\n'
    "\n"
    "instances:\n"
    "    top_tb:   { container: top_tb, instanceType: top_tb }\n"
    "    uTop:     { container: top_tb, instanceType: top }\n"
    "    uApbDec:  { container: top,    instanceType: apbDecode }\n"
    "    uLeafA:   { container: top,    instanceType: leafA, addressGroup: top }\n"
)

_ADDR = (
    "AddressGroups:\n"
    "  top:\n"
    "    addressIncrement: 0x01000000\n"
    "    maxAddressSpaces: 16\n"
    "    varType: addr_id_top\n"
    "    enumPrefix: ADDR_ID_TOP_\n"
    "    decoderInstance: uApbDec\n"
    "\n"
    "RegisterBusInterface: apbReg\n"
    "\n"
    "InstanceGroups:\n"
    "  top:\n"
    "    varType: inst_top\n"
    "    enumPrefix: INST_TOP_\n"
    "\n"
    "AddressObjects:\n"
    "  registers:\n"
    "    alignment: 8\n"
    "    sortDescending: True\n"
)


# A clean addressControl whose copied `addressIncrement` field is a Python-syntax
# eval rather than a literal. Phase B copies AddressGroups field values verbatim
# into the emitted addressBlock:, so the eval must be converted (by Phase A
# sweeping this file) before it survives into top.yaml.
_ADDR_EVAL = (
    "AddressGroups:\n"
    "  top:\n"
    f'    addressIncrement: {{ eval: "{_EVAL_PY}" }}\n'
    "    maxAddressSpaces: 16\n"
    "    varType: addr_id_top\n"
    "    enumPrefix: ADDR_ID_TOP_\n"
    "    decoderInstance: uApbDec\n"
    "\n"
    "RegisterBusInterface: apbReg\n"
)


def _project(*, yaml_format=None):
    sentinel = f"yamlFormat: {yaml_format}\n" if yaml_format is not None else ""
    return (
        f"{sentinel}"
        "projectName: miniProj\n"
        "projectFiles:\n"
        "  - top.yaml\n"
        "addressControl: addressControl.yaml\n"
        "topInstance: top_tb\n"
        "postProcess:\n"
        "  - $a2c/config/postParseRegister.py\n"
        "  - $a2c/config/postParseChecks.py\n"
    )


def _make(project, top, addr=_ADDR):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "project.yaml"), "w") as fh:
        fh.write(project)
    with open(os.path.join(d, "top.yaml"), "w") as fh:
        fh.write(top)
    if addr is not None:
        with open(os.path.join(d, "addressControl.yaml"), "w") as fh:
            fh.write(addr)
    return d


def _read(d, name):
    return open(os.path.join(d, name)).read()


def test_clean_converts_both_and_stamps():
    # A clean project: interface in router scope, no routed leaves, one Python
    # eval. Both phases convert and the sentinel is stamped.
    d = _make(_project(), _top(eval_line=f'eval: "{_EVAL_PY}"', with_interface=True))
    try:
        result = migrateProject(os.path.join(d, "project.yaml"), write=True)
        assert result.stamped, "clean project was not stamped"
        assert result.stampEligible

        proj = _read(d, "project.yaml")
        assert proj.startswith(f"yamlFormat: {CURRENT_YAML_FORMAT}\n"), \
            f"sentinel not stamped at head:\n{proj}"
        assert "addressControl:" not in proj, "pointer not removed"
        assert "instanceGroups:" in proj and "addressObjects:" in proj

        top = _read(d, "top.yaml")
        assert _EVAL_SV in top, f"eval not converted:\n{top}"
        assert _EVAL_PY not in top, "Python-syntax eval survived"
        assert "addressBlock:" in top and "addressGroup: top" in top

        assert not os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "clean project did not delete legacy file"

        # CLI wrapper succeeds and reports a stamp.
        rc = main(["--write", os.path.join(d, "project.yaml")])
        assert rc == 0
    finally:
        shutil.rmtree(d)
    return True


def test_addresscontrol_eval_converted_into_addressblock():
    # A Python-syntax eval living in a COPIED addressControl field must be
    # converted before Phase B copies it into the emitted addressBlock:. The
    # addressControl file is not in the projectFiles/include closure, so this
    # exercises the orchestrator adding it to the Phase-A sweep.
    d = _make(_project(),
              _top(eval_line=f'eval: "{_EVAL_PY}"', with_interface=True),
              addr=_ADDR_EVAL)
    try:
        # Dry-run: Phase A reports the converted addressControl eval row.
        result = migrateProject(os.path.join(d, "project.yaml"), write=False)
        converted = [r for rep in result.evalReports for r in rep.converted]
        assert any(os.path.basename(rep.path) == "addressControl.yaml"
                   and rep.converted
                   for rep in result.evalReports), \
            "addressControl eval not swept/converted by Phase A"

        # Write: the emitted addressBlock carries the SV-subset form, never the
        # Python-syntax original.
        result = migrateProject(os.path.join(d, "project.yaml"), write=True)
        assert result.stamped, "clean project was not stamped"
        top = _read(d, "top.yaml")
        assert "addressBlock:" in top
        assert _EVAL_SV in top, f"converted eval not in emitted addressBlock:\n{top}"
        assert _EVAL_PY not in top, "Python-syntax eval survived into addressBlock"
        assert not os.path.exists(os.path.join(d, "addressControl.yaml"))
    finally:
        shutil.rmtree(d)
    return True


def test_phase_a_real_eval_blocks_stamp():
    # A real-valued eval is NEEDS_MANUAL; even with Phase B clean the project is
    # not stamped, and the eval is named in the checklist.
    d = _make(_project(),
              _top(eval_line='eval: "$DWORD / 2.0", valueType: real',
                   with_interface=True))
    try:
        result = migrateProject(os.path.join(d, "project.yaml"), write=True)
        assert not result.stamped, "stamped despite a manual eval"
        assert not result.stampEligible
        assert result.evalManual, "expected a NEEDS_MANUAL eval row"

        proj = _read(d, "project.yaml")
        assert "yamlFormat:" not in proj, "sentinel written while blocked"

        report = renderReport(result, write=True)
        assert "BLOCKED" in report
        assert "$DWORD / 2.0" in report, "manual eval not named in checklist"

        rc = main(["--write", os.path.join(d, "project.yaml")])
        assert rc == 1, "blocked --write run must return non-zero"
    finally:
        shutil.rmtree(d)
    return True


def test_phase_b_todo_blocks_stamp():
    # A routed leaf leaves a Phase B manual TODO (registerPorts authoring); the
    # surfacing --write run does not stamp and returns non-zero. (Re-running a
    # partially-migrated project is governed by Phase B's idempotency, so the
    # check is on the single surfacing run, on a fresh project.)
    d = _make(_project(), _DIRTY_TOP)
    try:
        rc = main(["--write", os.path.join(d, "project.yaml")])
        assert rc == 1, "blocked --write run must return non-zero"
        proj = _read(d, "project.yaml")
        assert "yamlFormat:" not in proj, "sentinel written while blocked"
        # Legacy file is preserved while the address migration is incomplete.
        assert os.path.exists(os.path.join(d, "addressControl.yaml"))
    finally:
        shutil.rmtree(d)

    # Structured assertions on a fresh project via dry-run (nothing mutated).
    d = _make(_project(), _DIRTY_TOP)
    try:
        result = migrateProject(os.path.join(d, "project.yaml"), write=False)
        assert not result.stampEligible
        assert not result.addressReport.clean
        assert result.addressReport.manual

        report = renderReport(result, write=False)
        assert "BLOCKED" in report
        assert "leafA" in report, "leaf TODO not named in checklist"
    finally:
        shutil.rmtree(d)
    return True


def test_dry_run_changes_nothing_reports_all():
    d = _make(_project(), _top(eval_line=f'eval: "{_EVAL_PY}"', with_interface=True))
    try:
        before = {name: _read(d, name)
                  for name in ("project.yaml", "top.yaml", "addressControl.yaml")}
        result = migrateProject(os.path.join(d, "project.yaml"), write=False)

        # All three phases are reported even though nothing is written.
        assert any(r.converted for r in result.evalReports), "Phase A not reported"
        assert result.addressReport.applied, "Phase B not reported"
        assert result.stampEligible, "Phase C eligibility not reported"
        assert not result.stamped and not result.wrote

        report = renderReport(result, write=False)
        assert "Phase A" in report and "Phase B" in report and "Phase C" in report
        assert "WOULD STAMP" in report

        for name, text in before.items():
            assert _read(d, name) == text, f"{name} changed in dry-run"

        rc = main([os.path.join(d, "project.yaml")])
        assert rc == 0, "dry-run must succeed"
        for name, text in before.items():
            assert _read(d, name) == text, f"{name} changed by CLI dry-run"
    finally:
        shutil.rmtree(d)
    return True


def test_already_migrated_short_circuits():
    d = _make(_project(yaml_format=CURRENT_YAML_FORMAT),
              _top(eval_line=f'eval: "{_EVAL_PY}"', with_interface=True))
    try:
        before = {name: _read(d, name)
                  for name in ("project.yaml", "top.yaml", "addressControl.yaml")}
        result = migrateProject(os.path.join(d, "project.yaml"), write=True)

        assert result.alreadyMigrated, "stamped project not recognized"
        assert not result.evalReports, "Phase A ran on a migrated project"
        assert result.addressReport is None, "Phase B ran on a migrated project"
        assert not result.stamped and not result.wrote

        # Nothing on disk changed, including the still-present legacy fixtures.
        for name, text in before.items():
            assert _read(d, name) == text, f"{name} changed for migrated project"

        rc = main(["--write", os.path.join(d, "project.yaml")])
        assert rc == 0, "already-migrated --write must succeed"
    finally:
        shutil.rmtree(d)
    return True


_TESTS = [
    ("clean project converts both phases and is stamped", test_clean_converts_both_and_stamps),
    ("addressControl eval is converted into the emitted addressBlock", test_addresscontrol_eval_converted_into_addressblock),
    ("Phase A real eval blocks the stamp", test_phase_a_real_eval_blocks_stamp),
    ("Phase B manual TODO blocks the stamp", test_phase_b_todo_blocks_stamp),
    ("dry-run reports all phases but changes nothing", test_dry_run_changes_nothing_reports_all),
    ("already-migrated project short-circuits", test_already_migrated_short_circuits),
]


def main_tests():
    print("=" * 70)
    print("TESTING unified YAML migration orchestrator (migrateYaml.py)")
    print("=" * 70)

    all_ok = True
    for label, fn in _TESTS:
        try:
            fn()
            print(f"  PASS: {label}")
        except AssertionError as e:
            all_ok = False
            print(f"  FAIL: {label}\n        {e}")

    print(f"\nResult: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main_tests())
