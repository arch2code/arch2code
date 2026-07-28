#!/usr/bin/env python3
"""Unit tests for the legacy addressControl.yaml -> per-block addressBlock:
converter (Phase B core).

Each test builds a small synthetic legacy project on disk in a temp dir and
EXECUTES `migrateAddressControlInProject` over it, asserting on the resulting
file contents and the structured report:
  - the emitted addressBlock: body (verbatim hex preserved),
  - dropped dormant AddressGroups rows,
  - InstanceGroups/AddressObjects moved into project.yaml,
  - the removed addressControl: pointer,
  - the postParseRegister.py -> postParseRegisterPorts.py rewrite and base dedup,
  - the manual-TODO report for the interface-scope and routed-leaf cases,
  - that a dirty project is neither deleted nor signaled clean,
  - that a clean project is finalized (file deleted, signaled clean),
  - dry-run and idempotency are no-ops on disk."""

import os
import shutil
import sys
import tempfile

import yaml

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.migrateAddressControl import (
    migrateAddressControlInProject, routedLeafRegisterPortsAdvisory,
    ADDRESS_BLOCK, ADVISORY_LEAF_REGISTER_PORTS, DELETE_DEFERRED, DROP_DORMANT,
    POLICY_MOVE, POINTER_REMOVE, POSTPROCESS,
    TODO_INTERFACE_SCOPE, TODO_LEAF_REGISTER_PORTS, TODO_ROUTER_RESOLUTION,
)


# A legacy project whose top group resolves to a router (apbDecode), carries a
# dormant group (dead), routes one leaf (leafA), and names a register-bus
# interface (apbReg) that is NOT in the router file's scope. This exercises every
# applied edit plus the two delegated manual cases.
_DIRTY_TOP = (
    "blockDir: .\n"
    "\n"
    "blocks:\n"
    "    top_tb:\n"
    '        desc: "tb container"\n'
    "    top:\n"
    '        desc: "top container"\n'
    "    apbDecode:\n"
    '        desc: "APB router"\n'
    "        hasRtl: true\n"
    "    leafA:\n"
    '        desc: "routed leaf"\n'
    "    dormantBlk:\n"
    '        desc: "unused block"\n'
    "\n"
    "instances:\n"
    "    top_tb:   { container: top_tb, instanceType: top_tb }\n"
    "    uTop:     { container: top_tb, instanceType: top }\n"
    "    uApbDec:  { container: top,    instanceType: apbDecode }\n"
    "    uLeafA:   { container: top,    instanceType: leafA, addressGroup: top }\n"
)

_DIRTY_ADDR = (
    "AddressGroups:\n"
    "  top:\n"
    "    addressIncrement: 0x01000000\n"
    "    maxAddressSpaces: 16\n"
    "    varType: addr_id_top\n"
    "    varTypeContext: top.yaml\n"
    "    enumPrefix: ADDR_ID_TOP_\n"
    "    primaryDecode: True\n"
    "    decoderInstance: uApbDec\n"
    "  dead:\n"
    "    addressIncrement: 0x00100000\n"
    "    maxAddressSpaces: 16\n"
    "    varType: addr_id_dead\n"
    "    enumPrefix: ADDR_ID_DEAD_\n"
    "\n"
    "RegisterBusInterface: apbReg\n"
    "\n"
    "InstanceGroups:\n"
    "  top:\n"
    "    varType: inst_top\n"
    "    enumPrefix: INST_TOP_\n"
    "  blocks:\n"
    "    varType: blockID\n"
    "    enumPrefix: BLOCK_TOP_\n"
    "\n"
    "AddressObjects:\n"
    "  memories:\n"
    "    alignment: memsize\n"
    "    sizeRoundUpPowerOf2: True\n"
    "    sortDescending: True\n"
    "  registers:\n"
    "    alignment: 8\n"
    "    sortDescending: True\n"
)

_DIRTY_PROJECT = (
    "projectName: miniDirty\n"
    "projectFiles:\n"
    "  - top.yaml\n"
    "addressControl: addressControl.yaml\n"
    "topInstance: top_tb\n"
    "postProcess:\n"
    "  - $a2c/config/postParseRegister.py\n"
    "  - $a2c/config/postParseChecks.py\n"
    "  - $proj/config/customPass.py\n"
)

# A clean legacy project: one router, no routed leaves, register-bus interface
# (apbReg) declared in the router file's own scope. Nothing is left for the skill,
# so the converter finalizes it.
_CLEAN_TOP = (
    "blocks:\n"
    "    top_tb:\n"
    '        desc: "tb container"\n'
    "    top:\n"
    '        desc: "top container"\n'
    "    apbDecode:\n"
    '        desc: "APB router"\n'
    "\n"
    "interfaces:\n"
    "    apbReg:\n"
    '        desc: "register bus"\n'
    "        interfaceType: apb\n"
    "        structures: []\n"
    "\n"
    "instances:\n"
    "    top_tb:   { container: top_tb, instanceType: top_tb }\n"
    "    uTop:     { container: top_tb, instanceType: top }\n"
    "    uApbDec:  { container: top,    instanceType: apbDecode }\n"
)

_CLEAN_ADDR = (
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

_CLEAN_PROJECT = (
    "projectName: miniClean\n"
    "projectFiles:\n"
    "  - top.yaml\n"
    "addressControl: addressControl.yaml\n"
    "topInstance: top_tb\n"
    "postProcess:\n"
    "  - $a2c/config/postParseRegister.py\n"
    "  - $a2c/config/postParseChecks.py\n"
)


# A project whose postProcess: override has a commented-out first entry before a
# real entry (the examples/simple shape). The sole real entry is a base dup, so
# the whole block must be removed without orphaning the trailing '- ' line, and
# the blank separating it from the next key must survive.
_COMMENT_PROJECT = (
    "projectName: miniComment\n"
    "projectFiles:\n"
    "  - top.yaml\n"
    "addressControl: addressControl.yaml\n"
    "postProcess:\n"
    "  #- $a2c/config/postParseRegister.py\n"
    "  - $a2c/config/postParseChecks.py\n"
    "\n"
    "topInstance: top_tb\n"
)

# A project mixing a base-dup entry, an interleaved comment, and a
# project-specific entry. The base dup and comment drop; the project-specific
# entry must survive under a still-present postProcess: key.
_MIXED_COMMENT_PROJECT = (
    "projectName: miniMixed\n"
    "projectFiles:\n"
    "  - top.yaml\n"
    "addressControl: addressControl.yaml\n"
    "postProcess:\n"
    "  - $a2c/config/postParseChecks.py\n"
    "  #- $proj/config/disabledPass.py\n"
    "  - $proj/config/customPass.py\n"
    "topInstance: top_tb\n"
)


def _makeProject(project, top, addr):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "project.yaml"), "w") as fh:
        fh.write(project)
    with open(os.path.join(d, "top.yaml"), "w") as fh:
        fh.write(top)
    with open(os.path.join(d, "addressControl.yaml"), "w") as fh:
        fh.write(addr)
    return d


def _kinds(items):
    return [i.kind for i in items]


def _find(items, kind):
    return [i for i in items if i.kind == kind]


def test_dirty_applied_edits():
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, _DIRTY_ADDR)
    try:
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        assert report.written, "expected edits to be written"

        # addressBlock: body emitted on the router, hex preserved verbatim.
        topOut = open(os.path.join(d, "top.yaml")).read()
        expected = (
            "        addressBlock:\n"
            "            addressGroup: top\n"
            "            addressIncrement: 0x01000000\n"
            "            maxAddressSpaces: 16\n"
            "            varType: addr_id_top\n"
            "            enumPrefix: ADDR_ID_TOP_\n"
            "            upstreamPort: apbReg\n"
            "            registerDecoderPort: apbReg\n"
        )
        if expected not in topOut:
            raise AssertionError(f"addressBlock body missing/mismatched:\n{topOut}")
        # Retired fields never migrate.
        assert "varTypeContext" not in topOut.split("addressBlock:")[1].split("desc")[0]
        assert "primaryDecode" not in topOut
        assert "decoderInstance" not in topOut

        # Dormant group dropped (reported, not emitted).
        assert any("dead" in i.message for i in _find(report.applied, DROP_DORMANT)), \
            "dormant group 'dead' not reported dropped"
        assert "addr_id_dead" not in topOut, "dormant group must not be emitted"

        # Policy sections moved into project.yaml.
        projOut = open(os.path.join(d, "project.yaml")).read()
        for token in ("instanceGroups:", "INST_TOP_", "BLOCK_TOP_",
                      "addressObjects:", "sizeRoundUpPowerOf2"):
            assert token in projOut, f"policy token {token!r} missing from project.yaml"
        assert _find(report.applied, POLICY_MOVE), "no POLICY_MOVE reported"

        # addressControl: pointer removed.
        assert "addressControl:" not in projOut, "pointer not removed"
        assert _find(report.applied, POINTER_REMOVE), "no POINTER_REMOVE reported"

        # postProcess rewrite + base dedup; project-specific entry kept.
        pp = _find(report.applied, POSTPROCESS)
        assert any("postParseRegisterPorts.py" in i.message for i in pp), \
            "postParseRegister.py -> postParseRegisterPorts.py rewrite not reported"
        assert "postParseRegister.py" not in projOut, "legacy script name survived"
        assert "postParseChecks.py" not in projOut, "base dup not stripped"
        assert "customPass.py" in projOut, "project-specific script dropped"

        # Delegated manual cases reported, naming both sides.
        iface = _find(report.manual, TODO_INTERFACE_SCOPE)
        assert iface, "interface-scope TODO missing"
        assert ("Router block 'apbDecode'" in iface[0].message
                and "addressBus: true interface authored in its load-time scope"
                in iface[0].message), iface[0].message

        leaf = _find(report.manual, TODO_LEAF_REGISTER_PORTS)
        assert leaf, "leaf-registerPorts TODO missing"
        assert ("leafA" in leaf[0].message and "apbDecode" in leaf[0].message
                and "Migration Diagnostics" in leaf[0].message), leaf[0].message

        # Dirty project is not finalized.
        assert not report.clean, "manual TODOs present but report.clean is True"
        assert not report.deletedAddressControl, "deleted addressControl.yaml while dirty"
        assert os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "addressControl.yaml deleted while dirty"
    finally:
        shutil.rmtree(d)
    return True


def test_clean_finalizes():
    d = _makeProject(_CLEAN_PROJECT, _CLEAN_TOP, _CLEAN_ADDR)
    try:
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        assert report.written
        # No manual work: interface in scope, no routed leaves.
        assert not report.manual, [i.message for i in report.manual]
        assert report.clean, "clean project not signaled clean"
        assert report.deletedAddressControl, "clean project did not delete legacy file"
        assert not os.path.exists(os.path.join(d, "addressControl.yaml"))

        projOut = open(os.path.join(d, "project.yaml")).read()
        assert "addressControl:" not in projOut
        assert "postProcess:" not in projOut, "base-only postProcess not removed"
        assert "instanceGroups:" in projOut and "addressObjects:" in projOut

        topOut = open(os.path.join(d, "top.yaml")).read()
        assert "addressBlock:" in topOut and "addressGroup: top" in topOut
    finally:
        shutil.rmtree(d)
    return True


def test_dry_run_changes_nothing():
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, _DIRTY_ADDR)
    try:
        before = {name: open(os.path.join(d, name)).read()
                  for name in ("project.yaml", "top.yaml", "addressControl.yaml")}
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=False)
        # Report is fully populated, including the project.yaml edits...
        assert _find(report.applied, ADDRESS_BLOCK)
        assert _find(report.applied, POINTER_REMOVE)
        assert _find(report.applied, POLICY_MOVE)
        assert _find(report.applied, POSTPROCESS)
        assert _find(report.manual, TODO_INTERFACE_SCOPE)
        assert not report.written
        # ...but nothing on disk changed.
        for name, text in before.items():
            assert open(os.path.join(d, name)).read() == text, f"{name} changed in dry-run"
    finally:
        shutil.rmtree(d)
    return True


def test_idempotent_after_migration():
    d = _makeProject(_CLEAN_PROJECT, _CLEAN_TOP, _CLEAN_ADDR)
    try:
        migrateAddressControlInProject(os.path.join(d, "project.yaml"), write=True)
        snapshot = open(os.path.join(d, "project.yaml")).read()
        # Re-running a migrated project (no addressControl: pointer) is a no-op.
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        assert not report.applied and not report.manual, "second pass did work"
        assert not report.written, "second pass wrote"
        assert report.clean
        assert open(os.path.join(d, "project.yaml")).read() == snapshot
    finally:
        shutil.rmtree(d)
    return True


def test_unresolved_router_reports_manual():
    # A live group whose decoderInstance does not resolve to a block is reported,
    # never auto-authored.
    addr = (
        "AddressGroups:\n"
        "  top:\n"
        "    addressIncrement: 0x01000000\n"
        "    maxAddressSpaces: 16\n"
        "    varType: addr_id_top\n"
        "    enumPrefix: ADDR_ID_TOP_\n"
        "    decoderInstance: uMissing\n"
        "\nRegisterBusInterface: apbReg\n"
    )
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, addr)
    try:
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        rr = _find(report.manual, TODO_ROUTER_RESOLUTION)
        assert rr, "router-resolution TODO missing"
        assert "uMissing" in rr[0].message and "top" in rr[0].message
        assert not _find(report.applied, ADDRESS_BLOCK), "emitted addressBlock for unresolved router"
        # No addressBlock emitted -> pointer must NOT be removed (project keeps decode).
        projOut = open(os.path.join(d, "project.yaml")).read()
        assert "addressControl:" in projOut, "pointer removed with nothing converted"
        assert not report.clean
    finally:
        shutil.rmtree(d)
    return True


def test_commented_first_entry_no_orphan():
    # The simple shape: a commented-out first entry before a real base-dup entry.
    # The block's only real entry is a base dup, so the whole block is removed;
    # the commented line goes too and no bare '- ' line may be orphaned.
    d = _makeProject(_COMMENT_PROJECT, _CLEAN_TOP, _CLEAN_ADDR)
    try:
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        projOut = open(os.path.join(d, "project.yaml")).read()
        # No bare orphaned postProcess sequence item survives.
        for line in projOut.splitlines():
            assert not line.lstrip().startswith("- $a2c"), \
                f"orphaned postProcess entry survived:\n{projOut}"
        # The commented and real entries are both gone.
        assert "postParseRegister.py" not in projOut, "commented entry survived"
        assert "postParseChecks.py" not in projOut, "base dup survived"
        # Result is valid YAML with no postProcess key, and the next top-level
        # key (across the blank separator) is intact.
        loaded = yaml.safe_load(projOut)
        assert isinstance(loaded, dict), "migrated project.yaml failed to parse"
        assert "postProcess" not in loaded, "postProcess block not fully removed"
        assert loaded.get("topInstance") == "top_tb", "separator ate the next key"
        # The report says removed, not a misleading keep.
        pp = _find(report.applied, POSTPROCESS)
        assert any("removed postProcess: override" in i.message for i in pp), \
            [i.message for i in pp]
    finally:
        shutil.rmtree(d)
    return True


def test_mixed_keep_with_interleaved_comment():
    # A base-dup entry, an interleaved comment, and a project-specific entry.
    # The base dup and the comment drop; the project-specific entry survives
    # under a still-present postProcess: key and the result is valid YAML.
    d = _makeProject(_MIXED_COMMENT_PROJECT, _CLEAN_TOP, _CLEAN_ADDR)
    try:
        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        projOut = open(os.path.join(d, "project.yaml")).read()
        loaded = yaml.safe_load(projOut)
        assert isinstance(loaded, dict), "migrated project.yaml failed to parse"
        # Base dup and the disabled (commented) entry are gone.
        assert "postParseChecks.py" not in projOut, "base dup survived"
        assert "disabledPass.py" not in projOut, "interleaved comment survived"
        # Project-specific entry kept under a still-present postProcess: key.
        assert loaded.get("postProcess") == ["$proj/config/customPass.py"], \
            loaded.get("postProcess")
        assert loaded.get("topInstance") == "top_tb", "separator ate the next key"
        # The keep is reported for review.
        pp = _find(report.applied, POSTPROCESS)
        assert any("kept project-specific" in i.message for i in pp), \
            [i.message for i in pp]
    finally:
        shutil.rmtree(d)
    return True


def test_stranded_file_cleaned_on_later_run():
    # A first --write blocked by a non-router manual TODO (routed-leaf
    # registerPorts) removes the pointer but keeps addressControl.yaml as
    # reference. The pointer is now gone, so a later run must idempotently clean
    # up the leftover rather than strand it on disk forever.
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, _DIRTY_ADDR)
    try:
        first = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                               write=True)
        # First run: routing migrated (pointer removed), but dirty so file kept.
        assert not first.clean, "dirty project signaled clean"
        assert _find(first.applied, POINTER_REMOVE), "pointer not removed on first run"
        assert not first.deletedAddressControl, "file deleted while dirty"
        projOut = open(os.path.join(d, "project.yaml")).read()
        assert "addressControl:" not in projOut, "pointer not removed on first run"
        assert os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "file must be kept as reference while dirty"
        # The survivor must be explained, or the operator hand-deletes a file the
        # next run removes on its own.
        assert _find(first.applied, DELETE_DEFERRED), \
            "first run did not report that the leftover is cleaned on a later run"

        # Later run: pointer already gone. The leftover must be cleaned up.
        second = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        assert second.deletedAddressControl, "stranded file not cleaned on later run"
        assert second.written, "cleanup not reflected in written"
        assert second.clean
        assert not os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "addressControl.yaml left stranded on disk"
        # Pointer and file are now consistent: both absent.
        assert "addressControl:" not in open(os.path.join(d, "project.yaml")).read()
    finally:
        shutil.rmtree(d)
    return True


def test_advisory_outlives_the_one_shot_todo():
    """The routed-leaf question keeps being asked after the migrating run.

    Phase B's TODO_LEAF_REGISTER_PORTS can only be raised while the legacy
    AddressGroups table still exists, so run 2 has nothing to derive it from and
    an unanswered leaf would quietly settle as top-down. The advisory recomputes
    the same set from the migrated schema, so it must be silent BEFORE the
    migration (the blocking TODO owns that run), name the same leaf after it, and
    fall silent once the leaf answers with registerPorts: — an advisory that
    nags a project which already decided just teaches readers to skip the list.
    """
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, _DIRTY_ADDR)
    try:
        projectYaml = os.path.join(d, "project.yaml")
        assert not routedLeafRegisterPortsAdvisory(projectYaml), \
            "pre-migration project has no addressBlock: to read; must be silent"

        report = migrateAddressControlInProject(projectYaml, write=True)
        assert _find(report.manual, TODO_LEAF_REGISTER_PORTS), \
            "expected the one-shot Phase B TODO on the migrating run"

        after = routedLeafRegisterPortsAdvisory(projectYaml)
        assert _kinds(after) == [ADVISORY_LEAF_REGISTER_PORTS], \
            f"expected exactly one advisory after migration, got {_kinds(after)}"
        assert "leafA" in after[0].message and "apbDecode" in after[0].message, \
            f"advisory must name the leaf and its router: {after[0].message}"

        topPath = os.path.join(d, "top.yaml")
        answered = open(topPath).read().replace(
            '    leafA:\n        desc: "routed leaf"\n',
            '    leafA:\n        desc: "routed leaf"\n'
            "        registerPorts:\n"
            "            apbReg: { interface: apbReg }\n")
        with open(topPath, "w") as fh:
            fh.write(answered)
        assert not routedLeafRegisterPortsAdvisory(projectYaml), \
            "a leaf that declares registerPorts: must not be reported"
    finally:
        shutil.rmtree(d)


_TESTS = [
    ("dirty project: all applied edits + delegated TODOs", test_dirty_applied_edits),
    ("routed-leaf advisory outlives the one-shot TODO", test_advisory_outlives_the_one_shot_todo),
    ("stranded addressControl.yaml cleaned on later run", test_stranded_file_cleaned_on_later_run),
    ("clean project finalized (deleted + signaled clean)", test_clean_finalizes),
    ("dry-run reports but changes nothing on disk", test_dry_run_changes_nothing),
    ("migrated project is idempotent (no-op)", test_idempotent_after_migration),
    ("unresolved router reported, never auto-authored", test_unresolved_router_reports_manual),
    ("commented first entry: block removed, no orphan", test_commented_first_entry_no_orphan),
    ("mixed keep with interleaved comment", test_mixed_keep_with_interleaved_comment),
]


def main():
    print("=" * 70)
    print("TESTING addressControl -> addressBlock CONVERTER (Phase B)")
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
    sys.exit(main())
