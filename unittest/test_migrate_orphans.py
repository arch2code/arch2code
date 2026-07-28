#!/usr/bin/env python3
"""Unit tests for the post-database orphan sweep (pysrc/migrateOrphans.py).

The sweep DISPATCHES ON the embedded legacy fileMap's per-entry `migrate:`
disposition (there is no L\\C set-difference):
  - `delete`  purely-generated legacy artifacts, expanded over the current DB and
              swept (plus the explicit LEGACY_LITERAL_DELETE aggregates);
  - `port`    user code the migration ports later (agent-driven); only IDENTIFIED
              and REPORTED here when the current map now produces a different form;
  - `leave`   user testbench code; never expanded, never touched.

To exercise it without standing up a full projectCreate database, each test
stages a small synthetic project on disk and drives sweepOrphans against a
lightweight fake `prj` exposing exactly the attributes the enumerator reads
(projectLayout, contextOwningProject, includeName, filemap, data['blocks'/
'blocksparams'], and config.getConfig('INCLUDEFILES'/'PROJECTNAME')). The files on
disk are real; only the DB access surface is faked.

Coverage (the required assertions):
  (a) every `delete`-disposition entry + the explicit vl_wrap.{cpp,h,sv} aggregate
      is deleted (Includes.{h,cpp}, Base.h, _package.sv, the HDL wrappers,
      Tandem.{h,cpp}, vl_wrap.*);
  (b) `port`/`leave`-entry files (a block .cpp/.h/.sv and a tb file, WITH generated
      markers) are NEVER deleted — and are unreachable for deletion by construction;
  (c) a delete-target-named file WITHOUT the generated marker is REPORTED, not
      deleted;
  (d) a `port` block whose current form differs (parameterized -> .cppm) is
      reported TODO_PORT while a same-form (non-parameterized) block is a no-op;
  (e) user `#include` sites of a deleted header are reported.
"""

import os
import sys
import tempfile
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.migrateOrphans import (
    sweepOrphans,
    expandFileMap,
    _dispositionMap,
    _literalDeletePaths,
    _reconstructContexts,
    LEGACY_FILEMAP,
    LEGACY_LITERAL_DELETE,
    MIGRATE_DELETE,
    MIGRATE_PORT,
    MIGRATE_LEAVE,
    OrphansReport,
    ORPHAN_DELETE,
    TODO_UNGENERATED_FILE,
    TODO_PORT,
    TODO_UNMANIFESTED_SRC_DIR,
    TODO_USER_INCLUDE,
)

GEN_MARKER = "// GENERATED_CODE_BEGIN\n"

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {msg}")
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


# ---------------------------------------------------------------------------
# Fake projectOpen surface
# ---------------------------------------------------------------------------

class _FakeConfig:
    def __init__(self, values):
        self._values = values

    def getConfig(self, key):
        return self._values[key]


class _FakePrj:
    """The subset of a projectOpen handle sweepOrphans/expandFileMap read.

    Two blocks: `myblk` (non-parameterized) and `paramblk` (parameterized). The
    current merged map keeps `block` as .h/.cpp for non-param blocks and emits a
    `.cppm` (`blockModule`) for param blocks; `rtlModule` stays .sv. Two contexts:
    `top` (genuine generated context) and `usr` (hand-authored look-alike).
    """

    def __init__(self, root):
        model = os.path.join(root, "model")
        rtl = os.path.join(root, "rtl")

        def seg(sub, group):
            return {"path": os.path.join(root, sub), "buildGroup": group}

        segments = {
            "root":      {"path": root, "buildGroup": None},
            "base":      seg("base", "sc"),
            "registrar": seg("registrar", "sc"),
            "model":     seg("model", "sc"),
            "rtl":       seg("rtl", "sv"),
            "vl_wrap":   seg("verif/vl_wrap", "vl"),
            "tb":        seg("tb", "sc"),
            "fwInc":     seg("fw/include", "sc"),
        }
        # `root` is a first-class layout field (present in both layout modes),
        # matching _buildLayoutFor; the sweep reads the walk root from here.
        layout = {"mode": "functional", "segments": segments, "root": root}
        self.projectLayout = {"t": layout}
        self.contextOwningProject = {"top.yaml": "t", "usr.yaml": "t"}
        self.includeName = {"top.yaml": "top", "usr.yaml": "usr"}
        # Current merged map: context includes are cppm-only; a non-param block
        # emits the classic .h/.cpp while a param block emits a single .cppm
        # module; rtl stays .sv.
        self.filemap = {
            "include":     {"name": "Includes", "ext": {"cppm": "cppm"},
                            "cond": {"smartInclude": True}, "mode": "context",
                            "basePath": "model"},
            "package":     {"name": "_package", "ext": {"sv": "sv"},
                            "cond": {"smartInclude": True}, "mode": "context",
                            "basePath": "rtl"},
            "block":       {"name": "", "ext": {"hdr": "h", "src": "cpp"},
                            "cond": {"hasMdl": True}, "condAnd": {"hasOwnParams": False},
                            "mode": "block", "basePath": "model"},
            "blockModule": {"name": "", "ext": {"cppm": "cppm"},
                            "cond": {"hasMdl": True}, "condAnd": {"hasOwnParams": True},
                            "mode": "block", "basePath": "model"},
            "rtlModule":   {"name": "", "ext": {"sv": "sv"},
                            "cond": {"hasRtl": True}, "mode": "block",
                            "basePath": "rtl"},
        }
        includeFiles = {
            "include_cppm": {
                "top.yaml": {"baseName": "topIncludes.cppm",
                             "fileName": os.path.join(model, "topIncludes.cppm")},
                "usr.yaml": {"baseName": "usrIncludes.cppm",
                             "fileName": os.path.join(model, "usrIncludes.cppm")},
            },
            "package_sv": {
                "top.yaml": {"baseName": "top_package.sv",
                             "fileName": os.path.join(rtl, "top_package.sv")},
            },
        }
        # The build manifest as `make db` would emit it: the segment roots
        # arch2code itself places artifacts in, and nothing else. Every staged
        # C++ directory is covered, so the unmanifested-source detector is silent
        # here and only the test that stages an undeclared directory sees it.
        manifest = {
            "scSrcDirs": [os.path.join(root, "base"),
                          os.path.join(root, "registrar"),
                          model,
                          os.path.join(root, "tb"),
                          os.path.join(root, "fw", "include")],
            "vlWrapDirs": [os.path.join(root, "verif", "vl_wrap")],
        }
        self.config = _FakeConfig({"INCLUDEFILES": includeFiles, "PROJECTNAME": "t",
                                   "BUILDMANIFEST": manifest})

        def block(key, hasMdl, hasTb, hasRtl, hasVl):
            return {"blockKey": key, "_context": "top.yaml", "dir": "", "block": key,
                    "hasMdl": hasMdl, "hasTb": hasTb, "hasRtl": hasRtl, "hasVl": hasVl}

        blocks = OrderedDict()
        blocks["myblk"] = block("myblk", 1, 1, 1, 1)      # non-param, full surface
        blocks["paramblk"] = block("paramblk", 1, 0, 0, 0)  # parameterized (cppm)
        # projectOpen groups blocksparams as {yamlFile: [paramRow, ...]} (a
        # list-mode subtable); each row carries its owning blockKey.
        blocksparams = OrderedDict()
        blocksparams["top.yaml"] = [{"blockKey": "paramblk"}]
        self.data = {"blocks": blocks, "blocksparams": blocksparams}


def _write(path, marker):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(GEN_MARKER if marker else "// hand written, no generated regions\n")
    return path


def _stage(root):
    """Stage the synthetic project on disk. Returns key paths by role."""
    j = lambda *p: os.path.join(root, *p)
    paths = {
        # delete targets WITH marker (should be swept)
        "base":      _write(j("base", "myblkBase.h"), True),
        "svWrap":    _write(j("verif", "vl_wrap", "myblk_hdl_sv_wrapper.sv"), True),
        "scWrap":    _write(j("verif", "vl_wrap", "myblk_hdl_sc_wrapper.h"), True),
        "tandemH":   _write(j("base", "myblkTandem.h"), True),
        "tandemCpp": _write(j("base", "myblkTandem.cpp"), True),
        "incH":      _write(j("model", "topIncludes.h"), True),
        "incCpp":    _write(j("model", "topIncludes.cpp"), True),
        "pkg":       _write(j("rtl", "top_package.sv"), True),
        "vlwCpp":    _write(j("verif", "vl_wrap", "vl_wrap.cpp"), True),
        "vlwH":      _write(j("verif", "vl_wrap", "vl_wrap.h"), True),
        "vlwSv":     _write(j("verif", "vl_wrap", "vl_wrap.sv"), True),
        # delete target WITHOUT marker (reported, never deleted)
        "usrH":      _write(j("model", "usrIncludes.h"), False),
        "usrCpp":    _write(j("model", "usrIncludes.cpp"), False),
        # current-format siblings (leave)
        "topCppm":   _write(j("model", "topIncludes.cppm"), True),
        "usrCppm":   _write(j("model", "usrIncludes.cppm"), True),
        # port old-form user files WITH marker (never deleted)
        "myH":       _write(j("model", "myblk.h"), True),      # non-param: same form
        "myCpp":     _write(j("model", "myblk.cpp"), True),    # non-param: same form
        "mySv":      _write(j("rtl", "myblk.sv"), True),       # rtl stays .sv
        "paramH":    _write(j("model", "paramblk.h"), True),   # param: -> .cppm (TODO_PORT)
        "paramCpp":  _write(j("model", "paramblk.cpp"), True), # param: -> .cppm (TODO_PORT)
        # leave: user testbench code (never deleted)
        "tb":        _write(j("tb", "myblk", "myblkTestbench.h"), True),
    }
    return paths


DELETE_BASENAMES = {
    "myblkBase.h", "myblk_hdl_sv_wrapper.sv", "myblk_hdl_sc_wrapper.h",
    "myblkTandem.h", "myblkTandem.cpp", "topIncludes.h", "topIncludes.cpp",
    "top_package.sv", "vl_wrap.cpp", "vl_wrap.h", "vl_wrap.sv",
}


def test_delete_dispatch_sweeps_delete_entries_and_literals():
    print("test_delete_dispatch_sweeps_delete_entries_and_literals")
    with tempfile.TemporaryDirectory() as root:
        paths = _stage(root)
        prj = _FakePrj(root)
        report = sweepOrphans(prj, write=True)

        deleted = {i.location for i in report.applied if i.kind == ORPHAN_DELETE}
        # (a) exactly the marker-bearing delete-disposition entries + vl_wrap.* are
        # deleted (usrIncludes.{h,cpp} lack the marker so are not in this set).
        check(deleted == DELETE_BASENAMES,
              "delete-disposition entries + vl_wrap.* aggregate are swept")
        gone = ["base", "svWrap", "scWrap", "tandemH", "tandemCpp", "incH",
                "incCpp", "pkg", "vlwCpp", "vlwH", "vlwSv"]
        check(all(not os.path.exists(paths[k]) for k in gone),
              "every swept delete target is removed from disk")
        # the current-format .cppm siblings are never delete targets
        check(os.path.exists(paths["topCppm"]) and os.path.exists(paths["usrCppm"]),
              "current-format .cppm siblings left on disk")


def test_port_and_leave_never_deleted():
    print("test_port_and_leave_never_deleted")
    with tempfile.TemporaryDirectory() as root:
        paths = _stage(root)
        prj = _FakePrj(root)
        report = sweepOrphans(prj, write=True)

        # (b) port (block .cpp/.h, rtl .sv) and leave (tb) files survive the sweep.
        survivors = ["myH", "myCpp", "mySv", "paramH", "paramCpp", "tb"]
        check(all(os.path.exists(paths[k]) for k in survivors),
              "port/leave user files are left on disk")
        deleted = {i.location for i in report.applied if i.kind == ORPHAN_DELETE}
        check(deleted.isdisjoint({"myblk.h", "myblk.cpp", "myblk.sv",
                                  "paramblk.h", "paramblk.cpp", "myblkTestbench.h"}),
              "no port/leave file appears in the delete set")

        # unreachability by construction: the delete-target set (delete entries +
        # literals) is disjoint from the port/leave expansion.
        r = OrphansReport(projectName="t")
        contexts = _reconstructContexts(prj, r)
        deleteTargets = expandFileMap(prj, _dispositionMap(MIGRATE_DELETE), r, contexts)
        deleteTargets |= _literalDeletePaths(prj, r)
        portLeave = (expandFileMap(prj, _dispositionMap(MIGRATE_PORT), r, contexts)
                     | expandFileMap(prj, _dispositionMap(MIGRATE_LEAVE), r, contexts))
        check(portLeave and portLeave.isdisjoint(deleteTargets),
              "port/leave paths are unreachable for deletion by construction")


def test_ungenerated_delete_target_reported_not_deleted():
    print("test_ungenerated_delete_target_reported_not_deleted")
    with tempfile.TemporaryDirectory() as root:
        paths = _stage(root)
        prj = _FakePrj(root)
        report = sweepOrphans(prj, write=True)

        # (c) delete-target names without the generated marker are reported, kept.
        skipped = sorted(i.location for i in report.manual
                         if i.kind == TODO_UNGENERATED_FILE)
        check(skipped == ["usrIncludes.cpp", "usrIncludes.h"],
              "un-marked delete-target look-alikes are reported for manual review")
        check(os.path.exists(paths["usrH"]) and os.path.exists(paths["usrCpp"]),
              "un-marked look-alikes left on disk")


def test_port_todo_only_for_changed_form():
    print("test_port_todo_only_for_changed_form")
    with tempfile.TemporaryDirectory() as root:
        _stage(root)
        prj = _FakePrj(root)
        report = sweepOrphans(prj, write=True)

        ports = sorted(i.location for i in report.manual if i.kind == TODO_PORT)
        # (d) the parameterized block's .cpp/.h await the .cppm port; the
        # non-parameterized block (current map still emits .h/.cpp) is a no-op.
        check(ports == ["paramblk.cpp", "paramblk.h"],
              "only the parameterized (changed-form) block is reported TODO_PORT")
        check("myblk.h" not in ports and "myblk.cpp" not in ports
              and "myblk.sv" not in ports,
              "same-form (non-parameterized) block yields no TODO_PORT")


def test_user_include_site_handoff():
    print("test_user_include_site_handoff")
    with tempfile.TemporaryDirectory() as root:
        _stage(root)
        # A hand-authored user source that #includes a to-be-deleted header, and
        # also a port-pending one. Only the deleted header's include is stale:
        # paramblk.h survives the sweep (reported TODO_PORT) until the agent-driven
        # port converts it, so including it is still valid and must not be flagged.
        userFile = os.path.join(root, "model", "consumer.cpp")
        with open(userFile, "w") as fh:
            fh.write('#include "topIncludes.h"\n#include "paramblk.h"\n'
                     'int main(){return 0;}\n')
        prj = _FakePrj(root)
        report = sweepOrphans(prj, write=True)
        todos = [i for i in report.manual if i.kind == TODO_USER_INCLUDE]
        # (e) exactly one hand-off, pointing at the user file.
        check(len(todos) == 1, "exactly one user-include-site hand-off")
        check(todos and "consumer.cpp" in todos[0].location,
              "hand-off points at the user file that includes the deleted header")
        check(todos and todos[0].location.endswith(":1"),
              "hand-off names the deleted header's line, not the port-pending one")


def test_dry_run_changes_nothing():
    print("test_dry_run_changes_nothing")
    with tempfile.TemporaryDirectory() as root:
        paths = _stage(root)
        prj = _FakePrj(root)
        report = sweepOrphans(prj, write=False)
        check(any(i.kind == ORPHAN_DELETE for i in report.applied),
              "dry-run still reports the planned deletes")
        check(all(os.path.exists(p) for p in paths.values()),
              "dry-run deletes nothing on disk")
        check(not report.written, "dry-run report marked not written")


def test_literal_delete_resolves_against_layout():
    print("test_literal_delete_resolves_against_layout")
    with tempfile.TemporaryDirectory() as root:
        prj = _FakePrj(root)
        report = OrphansReport(projectName="t")
        literals = _literalDeletePaths(prj, report)
        vlDir = os.path.join(root, "verif", "vl_wrap")
        expected = {os.path.join(vlDir, fn) for _, fn in LEGACY_LITERAL_DELETE}
        check(literals == expected,
              "literal deletes resolve to <vl_wrap segment>/vl_wrap.{cpp,h,sv}")
        check(not report.manual, "no missing-segment note for a full layout")


def test_unmanifested_src_dir_reported_and_clears():
    """C++ the manifest does not compile is surfaced as a decision, and clears.

    The retired glob walked the whole tree, so a directory the manifest does not
    list stops being compiled AND stops being an include path — and because the
    include path is shared, the first failure usually lands in an unrelated
    translation unit. Two shapes must both be caught: a directory outside every
    segment root, and a SUBDIRECTORY of one (the manifest globs a root one level
    deep, so nesting is not covered either).

    It must also converge. `EXTRA_PRJ_SRC_DIRS` is the operator's answer, so a
    wired directory falls silent while the un-wired one still reports; an item
    that survived its own fix would leave `make migrate` permanently non-clean.
    """
    print("test_unmanifested_src_dir_reported_and_clears")
    with tempfile.TemporaryDirectory() as root:
        _stage(root)
        _write(os.path.join(root, "fw", "src", "fwMain.cpp"), False)
        _write(os.path.join(root, "model", "helpers", "helper.cpp"), False)
        prj = _FakePrj(root)

        report = sweepOrphans(prj, write=False)
        found = sorted(i.location for i in report.manual
                       if i.kind == TODO_UNMANIFESTED_SRC_DIR)
        check(found == [os.path.join("fw", "src"), os.path.join("model", "helpers")],
              "undeclared directory and un-globbed subdirectory both reported")
        message = next((i.message for i in report.manual
                        if i.kind == TODO_UNMANIFESTED_SRC_DIR), "")
        check("EXTRA_PRJ_SRC_DIRS" in message and "Decide" in message,
              "TODO states the decision and names the seam that answers it")

        os.makedirs(os.path.join(root, "rundir"))
        with open(os.path.join(root, "rundir", "Makefile"), "w") as fh:
            fh.write("EXTRA_PRJ_SRC_DIRS += $(REPO_ROOT)/fw/src\n")
        report = sweepOrphans(prj, write=False)
        found = sorted(i.location for i in report.manual
                       if i.kind == TODO_UNMANIFESTED_SRC_DIR)
        check(found == [os.path.join("model", "helpers")],
              "a directory wired onto EXTRA_PRJ_SRC_DIRS stops being reported")


if __name__ == "__main__":
    test_delete_dispatch_sweeps_delete_entries_and_literals()
    test_port_and_leave_never_deleted()
    test_ungenerated_delete_target_reported_not_deleted()
    test_port_todo_only_for_changed_form()
    test_user_include_site_handoff()
    test_dry_run_changes_nothing()
    test_literal_delete_resolves_against_layout()
    test_unmanifested_src_dir_reported_and_clears()
    print(f"\nResult: {'PASS' if FAIL == 0 else 'FAIL'} ({PASS} checks, {FAIL} failures)")
    sys.exit(1 if FAIL else 0)
