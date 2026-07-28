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

        # Dirty project is not finalized (leaf/interface TODOs remain), but the
        # router IS resolved, so routing is fully migrated: the pointer is removed
        # AND the legacy file is deleted together this run. The remaining manual
        # items are non-router hand tasks that do not need the legacy file, so
        # nothing is stranded and no DELETE_DEFERRED is reported.
        assert not report.clean, "manual TODOs present but report.clean is True"
        assert report.deletedAddressControl, "resolved routing did not delete legacy file"
        assert not os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "legacy file left on disk after routing fully migrated"
        assert not _find(report.applied, DELETE_DEFERRED), \
            "DELETE_DEFERRED reported though the file was deleted this run"
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
        # Unresolved router: pointer AND legacy file are kept together so a later
        # run (once the router is authored) still finds the pointer and deletes
        # through the subdir-honoring path. DELETE_DEFERRED explains the survivor.
        assert os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "legacy file must be kept while a router is unresolved"
        assert not report.deletedAddressControl, "deleted file while a router is unresolved"
        assert _find(report.applied, DELETE_DEFERRED), \
            "unresolved router did not report the kept file"
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


def test_leaf_todo_removes_pointer_and_file_together():
    # A first --write blocked only by a non-router manual TODO (routed-leaf
    # registerPorts) has a fully-resolved router, so routing is fully migrated:
    # the pointer AND the legacy file are removed together on that run. The leaf
    # TODO is one-shot (it needs the legacy table), so keeping the file would
    # re-raise it forever and never stamp. Nothing is stranded, so a later run is
    # a clean idempotent no-op — the pointer is never dropped while the file
    # survives, in any subdir.
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, _DIRTY_ADDR)
    try:
        first = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                               write=True)
        # First run: routing migrated. Pointer removed AND file deleted together.
        assert not first.clean, "dirty project signaled clean"
        assert _find(first.applied, POINTER_REMOVE), "pointer not removed on first run"
        assert first.deletedAddressControl, "legacy file not deleted with the pointer"
        projOut = open(os.path.join(d, "project.yaml")).read()
        assert "addressControl:" not in projOut, "pointer not removed on first run"
        assert not os.path.exists(os.path.join(d, "addressControl.yaml")), \
            "legacy file stranded after routing fully migrated"
        # The file is gone, so nothing is deferred.
        assert not _find(first.applied, DELETE_DEFERRED), \
            "DELETE_DEFERRED reported though the file was deleted this run"

        # Later run: pointer already gone, file already gone. Idempotent no-op.
        second = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        assert not second.deletedAddressControl, "second run tried to delete again"
        assert not second.written, "second run wrote to a fully-migrated project"
        assert second.clean
        assert not second.applied and not second.manual, "second run did work"
        assert not os.path.exists(os.path.join(d, "addressControl.yaml"))
        assert "addressControl:" not in open(os.path.join(d, "project.yaml")).read()
    finally:
        shutil.rmtree(d)
    return True


def test_config_subdir_pointer_not_stranded():
    # BUG 5: a project pointing at config/addressControl.yaml (a subdirectory)
    # must have that nested file deleted, never stranded. This is the path that
    # previously removed the pointer but kept the file, then a later pointer-is-
    # None run checked the wrong (project-root) path and stranded the config/-
    # nested file forever. Deletion now goes through os.path.join(projectDir,
    # pointer), which honors the subdir.
    d = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d, "config"))
        with open(os.path.join(d, "project.yaml"), "w") as fh:
            fh.write(_DIRTY_PROJECT.replace(
                "addressControl: addressControl.yaml\n",
                "addressControl: config/addressControl.yaml\n"))
        with open(os.path.join(d, "top.yaml"), "w") as fh:
            fh.write(_DIRTY_TOP)
        with open(os.path.join(d, "config", "addressControl.yaml"), "w") as fh:
            fh.write(_DIRTY_ADDR)
        addrPath = os.path.join(d, "config", "addressControl.yaml")

        report = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        # Router resolved (leaf TODO keeps it dirty) -> pointer removed AND the
        # config/-nested file deleted together.
        assert not report.clean, "leaf TODO should keep the project dirty"
        assert report.deletedAddressControl, "config/-nested file not deleted"
        assert not os.path.exists(addrPath), \
            "config/addressControl.yaml stranded on disk"
        assert "addressControl:" not in open(os.path.join(d, "project.yaml")).read()

        # A later run finds no pointer and no file: idempotent no-op, no strand.
        second = migrateAddressControlInProject(os.path.join(d, "project.yaml"),
                                                write=True)
        assert not second.written and not second.deletedAddressControl
        assert not os.path.exists(addrPath), "config/ file resurrected or stranded"
    finally:
        shutil.rmtree(d)
    return True


def test_retry_after_failed_delete_no_duplicate_addressblock():
    # The write phase injects addressBlock: on the resolved router BEFORE it
    # os.remove()s the legacy file, and the delete is ordered before the pointer-
    # removal write for retry safety. So a delete that fails mid-run leaves the
    # addressBlock: already injected, the pointer still present, and the legacy
    # file on disk. The next run re-enters emission against a router file that
    # already carries its addressBlock:; without the idempotency guard it would
    # re-inject and produce a DUPLICATE. This simulates that exact sequence by
    # making the first os.remove fail, then asserts the retry finalizes with
    # exactly one addressBlock:.
    import pysrc.migrateAddressControl as mac
    d = _makeProject(_DIRTY_PROJECT, _DIRTY_TOP, _DIRTY_ADDR)
    projectYaml = os.path.join(d, "project.yaml")
    addrPath = os.path.join(d, "addressControl.yaml")
    topPath = os.path.join(d, "top.yaml")
    realRemove = os.remove
    calls = {"n": 0}

    def flakyRemove(path):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("simulated mid-run filesystem failure")
        return realRemove(path)

    try:
        mac.os.remove = flakyRemove
        # First run: addressBlock: injected, then the delete fails -> RuntimeError.
        try:
            migrateAddressControlInProject(projectYaml, write=True)
            raise AssertionError("expected RuntimeError from the failed delete")
        except RuntimeError:
            pass

        # Retry safety held: the pointer survives and the file is still on disk,
        # but the addressBlock: was already injected exactly once.
        assert open(topPath).read().count("addressBlock:") == 1, \
            "first run must inject exactly one addressBlock:"
        assert "addressControl:" in open(projectYaml).read(), \
            "pointer must survive a failed delete (never dropped while file lives)"
        assert os.path.exists(addrPath), "legacy file must survive a failed delete"

        # Retry: os.remove now succeeds. The already-present addressBlock: must be
        # detected and NOT re-injected; the run finalizes cleanly.
        report = migrateAddressControlInProject(projectYaml, write=True)
        topOut = open(topPath).read()
        assert topOut.count("addressBlock:") == 1, \
            f"retry duplicated addressBlock::\n{topOut}"
        # The router was reported as already migrated (skipped), not re-emitted.
        skipped = _find(report.applied, ADDRESS_BLOCK)
        assert any("already present" in i.message for i in skipped), \
            [i.message for i in skipped]
        # Router still resolved -> pointer removed and legacy file deleted together.
        assert report.deletedAddressControl, "retry did not delete the legacy file"
        assert not os.path.exists(addrPath), "legacy file stranded after retry"
        assert "addressControl:" not in open(projectYaml).read(), \
            "pointer not removed on the successful retry"
    finally:
        mac.os.remove = realRemove
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
    ("leaf TODO removes pointer and file together", test_leaf_todo_removes_pointer_and_file_together),
    ("config/-subdir pointer file not stranded", test_config_subdir_pointer_not_stranded),
    ("retry after failed delete: no duplicate addressBlock", test_retry_after_failed_delete_no_duplicate_addressblock),
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
