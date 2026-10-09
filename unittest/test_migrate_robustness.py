#!/usr/bin/env python3
"""Unit tests for `make migrate` on project trees that are not tidy.

Covered:
  - a source file that is not valid UTF-8 is read and rewritten byte for byte;
  - a phase that raises is reported as TODO_PHASE_FAILED, the later phases still
    run, the stamp is blocked and the step exits non-zero;
  - if opening the database, the prefix move or its blocked report raises, the
    filename-prefix gate has not passed, so the sweep returns RC_BLOCKED,
    exit 2;
  - a sweep raise outside any phase exits RC_PHASE_FAILED on a writing and on a
    dry run, and keeps the phase failures recorded before it;
  - every unplaceable line of a legacy External is its own TODO_PORT_SLOT0,
    including a declaration after the class closer;
  - the unmanifested-source check skips dot-directories, ignores version
    control, and claims the retired scan compiled the directory only for a
    project built before the manifest;
  - the module scanner names a `module x;` unit as an implementation unit and
    never registers it as a provider;
  - a sibling `.cpp` including the External header the port deletes is reported;
  - the sweep reports user SV that names a module or package by its
    project-qualified pre-refactor name, and those old names match what a real
    project database derives;
  - only an instantiation type or a package scope is reported, not a signal or
    instance spelled like an old name, and only emitted artifacts' current
    names make an old name valid.

Fixtures come from the phase test files, so the staged shapes match the ones
those files prove the phases handle.
"""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

import migrateYaml
from migrateYaml import TODO_PHASE_FAILED
from pysrc import migrateCommon
from pysrc.gen_cpp_module_map import render_module_map
from pysrc.migrateBlockModulePort import (TODO_PORT_SLOT0, portBlockModules,
                                            portTbExternals, portTbTops)
from pysrc.migrateModuleEndlabel import restampModuleEndlabel
from pysrc.migrateOrphans import (TODO_UNMANIFESTED_SRC_DIR, TODO_USER_INCLUDE,
                                  sweepOrphans)
from pysrc.migrateStaleSvNames import _renamedSvNames, reportStaleSvNames
from pysrc.migrateTbConfig import restructureTbConfigs

import test_migrate_orphans as orphans
import test_migrate_tb_port as tbport
import test_migrate_yaml as yamlfx

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


@contextlib.contextmanager
def _isolatedTree():
    """Yield (parent, root): a temp project root that git cannot see past.
    GIT_CEILING_DIRECTORIES stops repository discovery at `parent`, so a work
    tree enclosing the temp directory is never found."""
    with tempfile.TemporaryDirectory() as parent:
        root = os.path.join(parent, "prj")
        os.makedirs(root)
        saved = os.environ.get("GIT_CEILING_DIRECTORIES")
        os.environ["GIT_CEILING_DIRECTORIES"] = parent
        try:
            yield parent, root
        finally:
            if saved is None:
                del os.environ["GIT_CEILING_DIRECTORIES"]
            else:
                os.environ["GIT_CEILING_DIRECTORIES"] = saved


def _raises(fn):
    """Run `fn`; return the exception it raised, or None."""
    try:
        fn()
    except Exception as exc:
        return exc
    return None


# A truncated UTF-8 trademark sign and a cp1252 one, as Propel and Radiant emit.
_VENDOR_BYTES = b"// PROPEL\xe2\x84 driver\n// uart \x99 core\nint iob;\n"


def test_non_utf8_file_round_trips():
    print("test_non_utf8_file_round_trips")
    with tempfile.TemporaryDirectory() as root:
        path = os.path.join(root, "iob.h")
        with open(path, "wb") as fh:
            fh.write(_VENDOR_BYTES)
        text = None

        def readBack():
            nonlocal text
            text = migrateCommon._read(path)
        exc = _raises(readBack)
        check(exc is None, f"a non-UTF-8 file reads without error ({exc!r})")
        if exc is None:
            migrateCommon._write(path, text.replace("int iob;", "int iob2;"))
            with open(path, "rb") as fh:
                written = fh.read()
            check(written == _VENDOR_BYTES.replace(b"int iob;", b"int iob2;"),
                  "a rewrite keeps every non-UTF-8 byte it did not edit")

        # The field crash: the sweep's user-include scan reads every source file.
        orphans._stage(root)
        vendor = os.path.join(root, "model", "vendor.h")
        with open(vendor, "wb") as fh:
            fh.write(_VENDOR_BYTES)
        exc = _raises(lambda: sweepOrphans(orphans._FakePrj(root), write=False))
        check(exc is None, f"the orphan sweep reads a non-UTF-8 user file ({exc!r})")


def test_failed_text_phase_does_not_stop_the_rest():
    print("test_failed_text_phase_does_not_stop_the_rest")
    d = yamlfx._make(yamlfx._project(),
                     yamlfx._top(eval_line='value: 3', with_interface=True))
    saved = migrateYaml.migrateModuleHeaderInProject

    def boom(*args, **kwargs):
        raise RuntimeError("module header exploded")
    migrateYaml.migrateModuleHeaderInProject = boom
    try:
        project = os.path.join(d, "project.yaml")
        result = None

        def run():
            nonlocal result
            with contextlib.redirect_stderr(io.StringIO()):
                result = migrateYaml.migrateProject(project, write=True)
        exc = _raises(run)
        check(exc is None, f"a raising phase does not abort the run ({exc!r})")
        if result is None:
            return
        failures = result.phaseFailures
        check(len(failures) == 1 and "module header" in failures[0].message
              and failures[0].location == project,
              "the failure names the phase and the file it was given")
        check(result.variantReport is not None and result.langDomainReport is not None
              and result.addressReport is not None,
              "the phases after the failed one still ran")
        check(not result.stamped and "yamlFormat" not in yamlfx._read(d, "project.yaml"),
              "a failed phase blocks the stamp")
        text = migrateYaml.renderReport(result, True)
        check(TODO_PHASE_FAILED in text and "module header exploded" in text,
              "the report lists the failure as a TODO")
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = migrateYaml.main(["--write", project])
        check(rc != 0, "the step exits non-zero")
    finally:
        migrateYaml.migrateModuleHeaderInProject = saved
        shutil.rmtree(d)


class _CleanReport:
    clean = True
    written = False
    applied = []
    manual = []


# Every --sweep phase except database open and the stale-SV-name report, with
# its renderer, stubbed to a clean no-op unless a test overrides it. _sweepWith
# stubs projectOpen separately.
_SWEEP_STUBS = {
    "moveRenamedFiles": lambda prj, write=False: _CleanReport(),
    "renderFilePrefixReport": lambda report, write: "",
    "sweepOrphans": lambda prj, write=False: _CleanReport(),
    "renderOrphanReport": lambda report, write: "",
    "restampProjectParam": lambda prj, write=False: _CleanReport(),
    "restampContextParam": lambda prj, write=False: _CleanReport(),
    "renderProjectParamReport": lambda report, write, label=None: "",
    "restampModuleEndlabel": lambda prj, write=False: _CleanReport(),
    "renderModuleEndlabelReport": lambda report, write: "",
}


def _sweepWith(prj, overrides, write=True):
    """Run `migrateYaml.py --sweep` against `prj` with the stubbed phases, and
    return (exception, rc, stdout). Phases not in _SWEEP_STUBS, other than
    projectOpen, run for real."""
    patches = dict(_SWEEP_STUBS, projectOpen=lambda db: prj)
    patches.update(overrides)
    saved = {n: getattr(migrateYaml, n) for n in patches}
    for n, fn in patches.items():
        setattr(migrateYaml, n, fn)
    out = io.StringIO()
    rc = None

    def run():
        nonlocal rc
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = migrateYaml.main(["--sweep"] + (["--write"] if write else [])
                                  + ["--db", "p.db"])
    try:
        exc = _raises(run)
    finally:
        for n, fn in saved.items():
            setattr(migrateYaml, n, fn)
    return exc, rc, out.getvalue()


def test_failed_sweep_phase_does_not_stop_the_restamps():
    """A raising orphan sweep does not stop the re-stamps after it, and the
    failure is reported as a TODO naming the phase."""
    print("test_failed_sweep_phase_does_not_stop_the_restamps")
    ran = []

    def boom(prj, write=False):
        raise UnicodeDecodeError("utf-8", b"\xe2", 0, 1, "invalid continuation byte")

    def restamp(label):
        def fn(prj, write=False):
            ran.append(label)
            return _CleanReport()
        return fn

    exc, rc, out = _sweepWith(object(), {
        "sweepOrphans": boom,
        "restampProjectParam": restamp("project"),
        "restampContextParam": restamp("context"),
        "restampModuleEndlabel": restamp("endlabel"),
        "reportStaleSvNames": lambda prj: _CleanReport(),
        "renderStaleSvNameReport": lambda report: ""})
    check(exc is None, f"a raising sweep phase does not abort the step ({exc!r})")
    check(ran == ["project", "context", "endlabel"],
          "every re-stamp after the failed sweep still ran")
    check(TODO_PHASE_FAILED in out and "orphan sweep" in out,
          "the failed sweep is reported as a TODO naming the phase")
    check(rc == migrateYaml.RC_PHASE_FAILED,
          "the step exits RC_PHASE_FAILED, so make migrate carries on and its "
          "recipe exits 1 at the end")


def test_escaped_sweep_exception_is_a_phase_failure():
    """A raise outside any phase, here the orphan report's render on a
    writing run, stops the sweep before its re-stamps. Uncaught, it
    would exit 1. make migrate reads 1 as work the final read-only sweep
    will report, but that sweep cannot see a re-stamp that never ran."""
    print("test_escaped_sweep_exception_is_a_phase_failure")
    ran = []

    def render(report, write):
        raise RuntimeError("orphan report render exploded")

    def restamp(prj, write=False):
        ran.append("project")
        return _CleanReport()

    exc, rc, out = _sweepWith(object(), {
        "renderOrphanReport": render,
        "restampProjectParam": restamp,
        "reportStaleSvNames": lambda prj: _CleanReport(),
        "renderStaleSvNameReport": lambda report: ""})
    check(exc is None, f"the exception does not escape the sweep ({exc!r})")
    check(rc == migrateYaml.RC_PHASE_FAILED,
          f"the sweep exits RC_PHASE_FAILED, not RC_TODO (got {rc})")
    check(TODO_PHASE_FAILED in out and "orphan report render exploded" in out,
          "the failure is reported as a TODO with its cause")
    check(ran == [], "the re-stamps after the raise did not run")


class _BlockedReport(_CleanReport):
    clean = False


def _raiser(message):
    def fn(*args, **kwargs):
        raise RuntimeError(message)
    return fn


def test_raise_before_the_prefix_gate_is_blocked():
    """newmodule deletes a file left at its unprefixed name, so any raise
    before the filename-prefix gate passes must halt make migrate."""
    print("test_raise_before_the_prefix_gate_is_blocked")
    cases = {
        "projectOpen": {"projectOpen": _raiser("db open exploded")},
        "the move": {"moveRenamedFiles": _raiser("prefix move exploded")},
        "the blocked report's render": {
            "moveRenamedFiles": lambda prj, write=False: _BlockedReport(),
            "renderFilePrefixReport": _raiser("prefix render exploded")},
    }
    for label, overrides in cases.items():
        exc, rc, out = _sweepWith(object(), overrides)
        check(exc is None and rc == migrateYaml.RC_BLOCKED,
              f"a raise in {label} exits RC_BLOCKED (got {rc}, {exc!r})")
        check(TODO_PHASE_FAILED in out, f"a raise in {label} is reported")


def test_escaped_raise_keeps_earlier_phase_failures():
    """A phase that raised is still reported when a later raise outside any
    phase ends the sweep."""
    print("test_escaped_raise_keeps_earlier_phase_failures")
    exc, rc, out = _sweepWith(object(), {
        "restampProjectParam": _raiser("project re-stamp exploded"),
        "renderModuleEndlabelReport": _raiser("end-label render exploded")})
    check(exc is None and rc == migrateYaml.RC_PHASE_FAILED,
          f"the sweep exits RC_PHASE_FAILED (got {rc}, {exc!r})")
    check(out.count(TODO_PHASE_FAILED) == 2
          and "project re-stamp exploded" in out
          and "end-label render exploded" in out,
          "both the phase failure and the escaped raise are reported")


def test_dry_run_escaped_raise_is_a_phase_failure():
    """A dry-run sweep that raises outside any phase exits RC_PHASE_FAILED like
    a writing one, so both runs take the same path."""
    print("test_dry_run_escaped_raise_is_a_phase_failure")
    exc, rc, out = _sweepWith(object(), {
        "renderOrphanReport": _raiser("orphan report render exploded")},
        write=False)
    check(exc is None and rc == migrateYaml.RC_PHASE_FAILED,
          f"the dry-run sweep exits RC_PHASE_FAILED (got {rc}, {exc!r})")
    check(TODO_PHASE_FAILED in out and "orphan report render exploded" in out,
          "the failure is reported as a TODO with its cause")


def test_every_slot0_line_is_reported():
    print("test_every_slot0_line_is_reported")
    with tempfile.TemporaryDirectory() as root:
        hText = tbport.LEGACY_H.replace(
            '#include "probe_pimpl.h"\n',
            '#include "probe_pimpl.h"\nimport first.stray;\nimport second.stray;\n')
        hText = hText.replace("};\n\n#endif",
                              "};\n\nextern std::string myblkTestSelection;\n\n#endif")
        p = tbport._stageExternal(root, hText=hText)
        report = portTbExternals(tbport._FakePrj(root), write=True)
        items = [i for i in report.manual if i.kind == TODO_PORT_SLOT0]
        quoted = " ".join(i.message for i in items)
        check(len(items) == 3, f"one TODO_PORT_SLOT0 per unplaceable line ({len(items)})")
        check("import first.stray;" in quoted and "import second.stray;" in quoted,
              "every stray import is quoted, not just the first")
        check("extern std::string myblkTestSelection;" in quoted,
              "a declaration after the class closer is reported as SLOT0")
        lines = hText.splitlines()
        expected = {f"myblkExternal.h:{lines.index(t) + 1}"
                    for t in ("import first.stray;", "import second.stray;",
                              "extern std::string myblkTestSelection;")}
        check({i.location for i in items} == expected,
              "each item is located at its own legacy line")
        check(os.path.exists(p["h"]) and os.path.exists(p["cpp"]),
              "the legacy pair survives the refusal")


def test_generated_region_after_closer_is_not_flagged():
    print("test_generated_region_after_closer_is_not_flagged")
    with tempfile.TemporaryDirectory() as root:
        hText = tbport.LEGACY_H.replace(
            "};\n\n#endif",
            "};\n\n// GENERATED_CODE_BEGIN --template=tbExternal --section=tail\n"
            "int generatedTail;\n// GENERATED_CODE_END\n\n#endif")
        tbport._stageExternal(root, hText=hText)
        report = portTbExternals(tbport._FakePrj(root), write=False)
        check(not [i for i in report.manual if i.kind == TODO_PORT_SLOT0],
              "a generated region after the class closer is not a SLOT0 line")


def test_dot_directory_include_site_is_not_reported():
    print("test_dot_directory_include_site_is_not_reported")
    with tempfile.TemporaryDirectory() as root:
        orphans._stage(root)
        for rel in (os.path.join(".opencode", "src", "tool.cpp"),
                    os.path.join("model", "consumer.cpp")):
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as fh:
                fh.write('#include "topIncludes.h"\n')
        report = sweepOrphans(orphans._FakePrj(root), write=False)
        sites = sorted(i.location for i in report.manual if i.kind == TODO_USER_INCLUDE)
        check(sites == ["consumer.cpp:1"],
              f"an include site under a dot-directory is not reported ({sites})")


def _unmanifested(root):
    report = sweepOrphans(orphans._FakePrj(root), write=False)
    return report, sorted(i.location for i in report.manual
                          if i.kind == TODO_UNMANIFESTED_SRC_DIR)


def _git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True)


def test_dot_directories_are_not_unmanifested():
    print("test_dot_directories_are_not_unmanifested")
    with _isolatedTree() as (_, root):
        orphans._stage(root)
        orphans._write(os.path.join(root, "model", ".opencode", "node_modules",
                                    "msgpackr", "src", "extract.cpp"), False)
        orphans._write(os.path.join(root, "fw", "src", "fwMain.cpp"), False)
        report, found = _unmanifested(root)
        check(found == [os.path.join("fw", "src")],
              f"a dot-directory under a scan root is skipped ({found})")
        message = next(i.message for i in report.manual
                       if i.kind == TODO_UNMANIFESTED_SRC_DIR)
        check("A project built before the manifest compiled it" in message
              and "A project already on the manifest never compiled it" in message,
              "the message claims the retired scan compiled the directory only "
              "for a project built before the manifest")

        # Migration never reads version control, so an ignore rule changes nothing.
        _git(root, "init", "-q")
        with open(os.path.join(root, ".gitignore"), "w") as fh:
            fh.write("fw/\n")
        _, found = _unmanifested(root)
        check(found == [os.path.join("fw", "src")],
              f"a .gitignore entry changes nothing ({found})")


def test_module_implementation_unit_is_not_a_missing_module():
    print("test_module_implementation_unit_is_not_a_missing_module")
    with tempfile.TemporaryDirectory() as root:
        provider = os.path.join(root, "myblkExternal.cppm")
        impl = os.path.join(root, "myblkTests.cppm")
        with open(provider, "w") as fh:
            fh.write("module;\nexport module myblk.external;\n")
        with open(impl, "w") as fh:
            fh.write("module;\n#include \"systemc.h\"\nmodule myblk.external;\n"
                     "import myblk_tb;\n")
        warnings = io.StringIO()
        with contextlib.redirect_stderr(warnings):
            rendered = render_module_map([provider, impl])
        check("CPP_MODULE_NAMES := myblk.external\n" in rendered
              and impl not in rendered,
              "the implementation unit is not taken for a provider")
        check("module implementation unit" in warnings.getvalue()
              and "module myblk.external;" in warnings.getvalue()
              and ".cpp" in warnings.getvalue(),
              "the warning names it an implementation unit and says to use .cpp")


class _PrjWithModuleNames(tbport._FakePrj):
    def __init__(self, root):
        super().__init__(root)
        self.blockModuleName = {tbport.BLOCK: tbport.BLOCK}


def test_sibling_cpp_including_the_external_header():
    print("test_sibling_cpp_including_the_external_header")
    with tempfile.TemporaryDirectory() as root:
        p = tbport._stageExternal(root)
        tests = os.path.join(os.path.dirname(p["h"]), "myblkTests.cpp")
        with open(tests, "w") as fh:
            fh.write('#include <string>\n#include "myblkExternal.h"\n\n'
                     "void myblkExternal::t1(void) {}\n")
        report = portTbExternals(_PrjWithModuleNames(root), write=True)
        items = [i for i in report.manual if i.kind == TODO_USER_INCLUDE]
        check(len(items) == 1 and items[0].location == "myblkTests.cpp:2",
              "the sibling's include is reported at its line")
        check(items and "module myblk.external;" in items[0].message,
              "the TODO suggests the module implementation unit")
        check(not os.path.exists(p["h"]), "the External port itself still ran")
        again = portTbExternals(_PrjWithModuleNames(root), write=True)
        check([i.location for i in again.manual if i.kind == TODO_USER_INCLUDE]
              == ["myblkTests.cpp:2"],
              "the TODO persists after the header is gone, until the include is")


class _SvNamePrj:
    """The projectOpen surface the stale-SV-name report reads, for project
    `holoscan`: block `mailbox` lost the prefix, `holoscan_ctrl` led with the
    project and was renamed by an `svFilePrefix`, `holoscan_dma` led with the
    project and kept its name, and `swModel` has no RTL. Context `holoscan.yaml`
    lost the prefix on its package, and `holoscan_io.yaml` led with the project
    and was renamed by the prefix."""

    def __init__(self, root):
        self.config = orphans._FakeConfig({
            "PROJECTNAME": "holoscan",
            "INCLUDEFILES": {"package_sv": {"holoscan.yaml": {}, "holoscan_io.yaml": {}}}})
        rtl = {"name": "", "ext": {"sv": "sv"}, "cond": {"hasRtl": True},
               "mode": "block", "basePath": "rtl", "langDomain": "sv"}
        self.projectLayout = {"holoscan": {"root": root, "fileMap": {"rtlModule": rtl}}}
        self.contextOwningProject = {"holoscan.yaml": "holoscan"}
        self.data = {"blocks": {
            key: {"blockKey": key, "block": key, "_context": "holoscan.yaml",
                  "hasRtl": hasRtl}
            for key, hasRtl in (("mailbox", 1), ("holoscan_ctrl", 1),
                                ("holoscan_dma", 1), ("swModel", 0))}}
        self.blockModuleName = {"mailbox": "holoscan_mailbox",
                                "holoscan_ctrl": "holoscan_ctrl",
                                "holoscan_dma": "holoscan_dma",
                                "swModel": "holoscan_swModel"}
        self.blockSvModuleName = {"mailbox": "mailbox", "holoscan_ctrl": "p_holoscan_ctrl",
                                  "holoscan_dma": "holoscan_dma", "swModel": "swModel"}
        self.includeName = {"holoscan.yaml": "holoscanTypes", "holoscan_io.yaml": "holoscan_io"}
        self.contextModuleIdentity = {"holoscan.yaml": "holoscan_holoscanTypes",
                                      "holoscan_io.yaml": "holoscan_io"}
        self.contextSvPackageName = {"holoscan.yaml": "holoscanTypes_package",
                                     "holoscan_io.yaml": "p_holoscan_io_package"}

    def getBlockCondRow(self, qualBlock):
        return dict(self.data["blocks"][qualBlock], hasOwnParams=0)


_FPGA_TOP = """// hand-written FPGA top
import holoscan_holoscanTypes_package::*;
module fpga_top;
  holoscan_mailbox u_mb ();
  holoscan_ctrl u_ctrl ();
  holoscan_swModel u_sw ();
  mailbox u_new ();
  holoscan_mailbox_shim u_shim ();
  // was holoscan_mailbox before the rename
  holoscan_io_package::t x;
  holoscan_dma u_dma ();
endmodule
"""

_GEN_HOST = """// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
  holoscan_mailbox u_gen ();
// GENERATED_CODE_END
  holoscan_mailbox u_user ();
  holoscan_mailbox
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
  u_tail ();
// GENERATED_CODE_END
"""


def test_stale_sv_names_reported_by_sweep():
    print("test_stale_sv_names_reported_by_sweep")
    with tempfile.TemporaryDirectory() as root:
        files = {os.path.join("fpga", "rtl", "fpga_top.sv"): _FPGA_TOP.encode(),
                 os.path.join("rtl", "host.sv"): _GEN_HOST.encode(),
                 os.path.join("ip", "uart.v"):
                     b"// uart \x99 core\nholoscan_mailbox u_v ();\n",
                 os.path.join("build", "stale.sv"): b"holoscan_mailbox u_b ();\n"}
        for rel, data in files.items():
            path = os.path.join(root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)
        exc, rc, out = _sweepWith(_SvNamePrj(root), {})
        check(exc is None, f"the sweep runs ({exc!r})")
        todo = [line.split()[0] for line in out.splitlines()
                if "TODO_STALE_SV_NAME" in line]
        expected = [os.path.join("fpga", "rtl", "fpga_top.sv") + ":2",
                    os.path.join("fpga", "rtl", "fpga_top.sv") + ":4",
                    os.path.join("fpga", "rtl", "fpga_top.sv") + ":5",
                    os.path.join("fpga", "rtl", "fpga_top.sv") + ":10",
                    os.path.join("ip", "uart.v") + ":2",
                    os.path.join("rtl", "host.sv") + ":4",
                    os.path.join("rtl", "host.sv") + ":5"]
        check(todo == expected,
              f"each old module/package name in user SV is reported at its line ({todo})")
        check("'holoscan_holoscanTypes_package'" in out
              and "now emits 'holoscanTypes_package'" in out
              and "now emits 'mailbox'" in out,
              "the TODO names the old identifier and the current one")
        check(rc == migrateYaml.RC_TODO, "a stale SV name keeps the sweep non-clean")


_MASKED_SV = """/* holoscan_mailbox
   holoscan_mailbox */
module m;
  initial $display("holoscan_mailbox \\" done");
  /* note */ holoscan_mailbox u_after ();
endmodule : holoscan_mailbox
"""


def test_stale_sv_names_skip_comments_strings_and_endlabels():
    print("test_stale_sv_names_skip_comments_strings_and_endlabels")
    with tempfile.TemporaryDirectory() as root:
        with open(os.path.join(root, "masked.sv"), "w") as fh:
            fh.write(_MASKED_SV)
        with open(os.path.join(root, "inc.vh"), "w") as fh:
            fh.write("holoscan_mailbox u_vh ();\n")
        report = reportStaleSvNames(_SvNamePrj(root))
        found = [i.location for i in report.manual]
        check("masked.sv:5" in found,
              "a reference after a block comment on the same line is reported")
        check(not {"masked.sv:1", "masked.sv:2", "masked.sv:4"} & set(found),
              f"names in a multi-line block comment and a string are not ({found})")
        check("masked.sv:6" not in found,
              "an endmodule label, which the end-label re-stamp owns, is not reported")
        check("inc.vh:1" in found, "a .vh file is scanned")


def test_endmodule_label_across_lines_keeps_line_numbers():
    print("test_endmodule_label_across_lines_keeps_line_numbers")
    with tempfile.TemporaryDirectory() as root:
        with open(os.path.join(root, "label.sv"), "w") as fh:
            fh.write("endmodule // c\n: holoscan_mailbox\nholoscan_mailbox w();\n")
        report = None

        def run():
            nonlocal report
            report = reportStaleSvNames(_SvNamePrj(root))
        exc = _raises(run)
        check(exc is None, f"a label split across lines does not crash the scan ({exc!r})")
        check(report is not None and [i.location for i in report.manual] == ["label.sv:3"],
              "the reference after it is reported at its own line")


def test_old_sv_names_match_a_real_database():
    """The fixtures above state old names by hand; this checks the derivation
    against a database built from the hierarchical fixture (project `hier`)."""
    print("test_old_sv_names_match_a_real_database")
    tmp = tempfile.mkdtemp(prefix="migrate_robust_hier_", dir=test_dir)
    try:
        for node in ("prj", "core", "leaf"):
            shutil.copytree(os.path.join(orphans.HIER_FIXTURE, node),
                            os.path.join(tmp, node))
        proj = os.path.join(tmp, "prj", "yaml", "hierProject.yaml")
        db = os.path.join(tmp, "hier.db")
        built = subprocess.run([sys.executable, orphans.ARCH2CODE, "--yaml", proj,
                                "--db", db], capture_output=True, text=True,
                               timeout=120, cwd=tmp)
        check(built.returncode == 0, f"the fixture db builds ({built.stderr[-300:]})")
        prj = orphans.projectOpen(db)
        try:
            modules, packages = _renamedSvNames(prj)
            renamed = {old: new for old, (new, _) in (modules | packages).items()}
        finally:
            orphans.g.db.close()
            orphans.g.db = None
        expected = {"hier_core": "core", "hier_gen": "gen", "hier_leaf": "leaf",
                    "hier_core_package": "core_package"}
        # Interface-library and empty contexts never emitted a package.
        check(renamed == expected, f"old names are <project>_<block> and "
              f"<context identity>_package ({renamed})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _writeTree(root, files):
    for rel, text in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(text)


_NAME_POSITIONS_SV = """module fpga_top;
  logic holoscan_mailbox;
  mailbox holoscan_ctrl ();
  holoscan_mailbox u_mb ();
  holoscan_mailbox #(.W(8)) u_mb2 (.a(a));
  import holoscan_x_package::*;
  holoscan_x_package::T v;
  holoscan_mailbox #(
    .W(8)
  ) u_mb3 (.a(a));
  assign holoscan_mailbox = holoscan_x_package;
  (* DONT_TOUCH = "TRUE" *) holoscan_mailbox u_attr (.a(a));
  if (EN) holoscan_mailbox u_if (.a(a));
  if (EN) begin : g holoscan_mailbox u_blk (.a(a)); end
  holoscan_mailbox
    #(.W(8)) u_mb4 (.a(a));
  holoscan_mailbox u_mb5
    (.a(a));
  holoscan_mailbox u_arr [1:0] ();
  holoscan_mailbox foo [3:0];
  holoscan_mailbox iff (en);
  holoscan_mailbox within (x);
  case (SEL) 0: holoscan_mailbox u_case (.a(a)); endcase
  lbl: holoscan_mailbox u_lbl (.a(a));
  holoscan_mailbox
    u_mb6 ();
  import holoscan_x_package
    ::*;
  begin : holoscan_mailbox
    if (x) y = 1;
  end
  assert property (@(posedge clk) holoscan_mailbox ##1 ack);
`ifdef FPGA holoscan_mailbox u_def (); `endif
`endif holoscan_mailbox u_end ();
  (* black_box *) module holoscan_mailbox (input a); endmodule
  cell holoscan_mailbox use work.mbx;
  module
  holoscan_mailbox #(parameter W = 8) (input a); endmodule
  module automatic holoscan_mailbox (input a); endmodule
  cell work.holoscan_mailbox use work.m;
endmodule
"""


def test_stale_sv_names_only_at_reference_positions():
    """A signal or instance spelled like an old name is not a reference. A
    module name counts as the type of an instantiation at a statement start, a
    package name before `::`."""
    print("test_stale_sv_names_only_at_reference_positions")
    with tempfile.TemporaryDirectory() as root:
        _writeTree(root, {"top.sv": _NAME_POSITIONS_SV})
        prj = _SvNamePrj(root)
        prj.config.getConfig("INCLUDEFILES")["package_sv"]["x.yaml"] = {}
        prj.includeName["x.yaml"] = "x"
        prj.contextModuleIdentity["x.yaml"] = "holoscan_x"
        prj.contextSvPackageName["x.yaml"] = "x_package"
        found = [(i.location, i.message.split("'")[1])
                 for i in reportStaleSvNames(prj).manual]
        check(found == [("top.sv:4", "holoscan_mailbox"),
                        ("top.sv:5", "holoscan_mailbox"),
                        ("top.sv:6", "holoscan_x_package"),
                        ("top.sv:7", "holoscan_x_package"),
                        ("top.sv:8", "holoscan_mailbox"),
                        ("top.sv:12", "holoscan_mailbox"),
                        ("top.sv:13", "holoscan_mailbox"),
                        ("top.sv:14", "holoscan_mailbox"),
                        ("top.sv:15", "holoscan_mailbox"),
                        ("top.sv:17", "holoscan_mailbox"),
                        ("top.sv:19", "holoscan_mailbox"),
                        ("top.sv:23", "holoscan_mailbox"),
                        ("top.sv:24", "holoscan_mailbox"),
                        ("top.sv:25", "holoscan_mailbox"),
                        ("top.sv:27", "holoscan_x_package"),
                        ("top.sv:33", "holoscan_mailbox"),
                        ("top.sv:34", "holoscan_mailbox"),
                        ("top.sv:35", "holoscan_mailbox"),
                        ("top.sv:36", "holoscan_mailbox"),
                        ("top.sv:38", "holoscan_mailbox"),
                        ("top.sv:39", "holoscan_mailbox"),
                        ("top.sv:40", "holoscan_mailbox")],
              f"instantiation types and package scopes are reported, a signal, "
              f"array, instance or SVA operand named like an old name is not "
              f"({found})")


def test_stale_sv_name_line_matches_user_regions():
    """A line break other than `\\n` before a generated region does not shift a
    reference after it into the region."""
    print("test_stale_sv_name_line_matches_user_regions")
    with tempfile.TemporaryDirectory() as root:
        _writeTree(root, {"top.sv": "\f\nmodule m;\n// GENERATED_CODE_BEGIN --x\n  wire a;\n"
                                    "// GENERATED_CODE_END\n  holoscan_mailbox u ();\n"})
        found = [i.location for i in reportStaleSvNames(_SvNamePrj(root)).manual]
        check(found == ["top.sv:7"],
              f"the reference after the region is reported at its split line ({found})")


def test_model_only_name_does_not_hide_a_stale_module():
    """A block with no RTL emits no module, so its current SV name does not make
    another block's old name valid."""
    print("test_model_only_name_does_not_hide_a_stale_module")
    with tempfile.TemporaryDirectory() as root:
        _writeTree(root, {"top.sv": "module t;\n  holoscan_fifo u_f ();\nendmodule\n"})
        prj = _SvNamePrj(root)
        for key, hasRtl, old, new in (("fifo", 1, "holoscan_fifo", "fifo"),
                                      ("swFifo", 0, "holoscan_swFifo", "holoscan_fifo")):
            prj.data["blocks"][key] = {"blockKey": key, "block": key,
                                       "_context": "holoscan.yaml", "hasRtl": hasRtl}
            prj.blockModuleName[key] = old
            prj.blockSvModuleName[key] = new
        found = [i.location for i in reportStaleSvNames(prj).manual]
        check(found == ["top.sv:2"],
              f"the old name of an RTL block is reported although a model-only "
              f"block's current name matches it ({found})")


def test_stale_sv_modules_reported_without_an_sv_package():
    """A project with no types, structures or constants emits no context
    files, so INCLUDEFILES is empty. Its old module names are still
    reported."""
    print("test_stale_sv_modules_reported_without_an_sv_package")
    with tempfile.TemporaryDirectory() as root:
        _writeTree(root, {"top.sv": "module t;\n  holoscan_mailbox u_mb ();\nendmodule\n"})
        prj = _SvNamePrj(root)
        prj.config = orphans._FakeConfig({
            "PROJECTNAME": "holoscan",
            "INCLUDEFILES": {}})
        report = None

        def run():
            nonlocal report
            report = reportStaleSvNames(prj)
        exc = _raises(run)
        check(exc is None, f"a project with no SV package does not crash the scan ({exc!r})")
        check(report is not None and [i.location for i in report.manual] == ["top.sv:2"],
              "the old module name is reported")


def test_rtl_module_cond_on_has_own_params():
    """A fileMap block entry may test hasOwnParams, which is not a block
    column."""
    print("test_rtl_module_cond_on_has_own_params")
    tmp = tempfile.mkdtemp(prefix="migrate_robust_ownparams_", dir=test_dir)
    try:
        for node in ("prj", "core", "leaf"):
            shutil.copytree(os.path.join(orphans.HIER_FIXTURE, node),
                            os.path.join(tmp, node))
        proj = os.path.join(tmp, "prj", "yaml", "hierProject.yaml")
        with open(proj) as fh:
            text = fh.read()
        anchor = "cond: {hasRtl: true},"
        check(anchor in text, "the rtlModule entry anchor is present")
        check("    includeFW" in text, "the includeFW entry anchor is present")
        ownParamsEntries = "".join(
            f"    {key:<12}: {{ name : \"{name}\", ext: {ext}, cond: {{{cond}: true}}, "
            f"condAnd: {{hasOwnParams: true}}, {extra}mode: block, basePath: {base}, "
            f"langDomain: sc, desc: \"{key}\"}}\n"
            for key, name, ext, cond, extra, base in (
                ("blockModule", "", "{cppm: cppm}", "hasMdl", "", "model"),
                ("testBench", "Testbench", "{cppm: cppm}", "hasTb", "blockDir: true, ", "tb"),
                ("tbConfig", "Config", "{src: cpp}", "hasTb", "blockDir: true, ", "tb"),
                ("tbExternal", "External", "{cppm: cppm}", "hasTb", "blockDir: true, ", "tb")))
        text = text.replace(anchor, "cond: {hasRtl: true}, condAnd: {hasOwnParams: true},", 1)
        with open(proj, "w") as fh:
            fh.write(text.replace("    includeFW", ownParamsEntries + "    includeFW", 1))
        db = os.path.join(tmp, "hier.db")
        built = subprocess.run([sys.executable, orphans.ARCH2CODE, "--yaml", proj,
                                "--db", db], capture_output=True, text=True,
                               timeout=120, cwd=tmp)
        check(built.returncode == 0, f"the fixture db builds ({built.stderr[-300:]})")
        prj = orphans.projectOpen(db)
        try:
            for what, fn in (
                    ("the old-name map is derived", lambda: _renamedSvNames(prj)),
                    ("the end-label re-stamp runs", lambda: restampModuleEndlabel(prj, write=False)),
                    ("the block port runs", lambda: portBlockModules(prj, write=False)),
                    ("the tb External port runs", lambda: portTbExternals(prj, write=False)),
                    ("the tb top port runs", lambda: portTbTops(prj, write=False)),
                    ("the tb Config restructure runs", lambda: restructureTbConfigs(prj, write=False))):
                exc = _raises(fn)
                check(exc is None, f"{what} without error ({exc!r})")
        finally:
            orphans.g.db.close()
            orphans.g.db = None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    test_non_utf8_file_round_trips()
    test_failed_text_phase_does_not_stop_the_rest()
    test_failed_sweep_phase_does_not_stop_the_restamps()
    test_escaped_sweep_exception_is_a_phase_failure()
    test_raise_before_the_prefix_gate_is_blocked()
    test_escaped_raise_keeps_earlier_phase_failures()
    test_dry_run_escaped_raise_is_a_phase_failure()
    test_every_slot0_line_is_reported()
    test_generated_region_after_closer_is_not_flagged()
    test_dot_directory_include_site_is_not_reported()
    test_dot_directories_are_not_unmanifested()
    test_module_implementation_unit_is_not_a_missing_module()
    test_sibling_cpp_including_the_external_header()
    test_stale_sv_names_reported_by_sweep()
    test_stale_sv_names_skip_comments_strings_and_endlabels()
    test_endmodule_label_across_lines_keeps_line_numbers()
    test_old_sv_names_match_a_real_database()
    test_stale_sv_names_only_at_reference_positions()
    test_stale_sv_name_line_matches_user_regions()
    test_model_only_name_does_not_hide_a_stale_module()
    test_stale_sv_modules_reported_without_an_sv_package()
    test_rtl_module_cond_on_has_own_params()
    print(f"\nResult: {'PASS' if FAIL == 0 else 'FAIL'} "
          f"({PASS} checks, {FAIL} failures)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
