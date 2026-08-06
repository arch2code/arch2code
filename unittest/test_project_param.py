#!/usr/bin/env python3
"""Unit tests for the project-mode --project GENERATED_CODE_PARAM support.

Two units, both driven at runtime against real on-disk files:

  (1) textfileHelper.codeText.parseParam accepts `--project` and exposes it as
      params.project (None when absent, so the older --context form is unchanged).

  (2) migrateProjectParam re-stamps a project-mode artifact's PARAM line from the
      retired `--context <basename>` form to `--project <projectName>`, identifies
      the file through the fileMap `mode: project` entry (not a filename guess),
      guards on the generated marker, and is idempotent.

Like test_migrate_orphans, the migration unit stages real files on disk and
drives restampProjectParam against a lightweight fake `prj` exposing exactly the
attributes _projectModePaths reads (config.getConfig('TOPCONTEXT'/'PROJECTNAME'),
contextOwningProject, projectLayout, filemap, data['instances'/'blocks']).
"""

import os
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.textfileHelper import codeText
from pysrc.genFileParam import contextParamTail
from pysrc.migrateProjectParam import (
    restampProjectParam,
    restampContextParam,
    _restampParamLine,
    PROJECT_PARAM_RESTAMP,
    CONTEXT_PARAM_RESTAMP,
    TODO_UNGENERATED_FILE,
    TODO_MISSING_PARAM_LINE,
)
from pysrc import processYaml

RTL_DOTF_CONTEXT = (
    "+libext+.sv\n"
    "// GENERATED_CODE_PARAM --context=proj.yaml\n"
    "// GENERATED_CODE_BEGIN --template=rtlDotF\n"
    "+incdir+.\n"
    "proj_package.sv\n"
    "// GENERATED_CODE_END\n"
)
RTL_DOTF_PROJECT = RTL_DOTF_CONTEXT.replace(
    "// GENERATED_CODE_PARAM --context=proj.yaml\n",
    "// GENERATED_CODE_PARAM --project=myProj\n")


class _FakeConfig:
    def __init__(self, values):
        self._values = values

    def getConfig(self, key):
        return self._values[key]


class _FakePrj:
    """The subset of a projectOpen handle _projectModePaths reads: a single
    functional-layout project `myProj` owning the top context, with a single
    project-mode fileMap entry (rtlDotF) placed at the rtl segment root."""

    def __init__(self, root):
        segments = {
            "root": {"path": root, "buildGroup": None},
            "rtl":  {"path": os.path.join(root, "rtl"), "buildGroup": "sv"},
        }
        layout = {"mode": "functional", "segments": segments, "root": root}
        self.projectLayout = {"myProj": layout}
        self.contextOwningProject = {"proj.yaml": "myProj"}
        self.filemap = {
            "rtlDotF": {"name": "rtl", "ext": {"f": "f"}, "mode": "project",
                        "basePath": "rtl"},
        }
        self.data = {"instances": {}, "blocks": {}}
        self.config = _FakeConfig({"TOPCONTEXT": "proj.yaml",
                                   "PROJECTNAME": "myProj"})


def _rtlPath(root):
    return os.path.join(root, "rtl", "rtl.f")


def _write(root, text):
    path = _rtlPath(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)
    return path


def test_parseParam_accepts_project():
    """parseParam accepts --project (project-mode) and leaves it None for a
    context-mode file, so both forms parse unambiguously."""
    with tempfile.TemporaryDirectory() as work:
        projFile = os.path.join(work, "rtl.f")
        with open(projFile, "w") as f:
            f.write(RTL_DOTF_PROJECT)
        code = codeText(projFile, "//")
        assert code.params.project == "myProj", \
            f"expected params.project 'myProj', got {code.params.project!r}"
        assert code.params.context is None, \
            f"project-mode file must not set --context, got {code.params.context!r}"

        ctxFile = os.path.join(work, "ctx.f")
        with open(ctxFile, "w") as f:
            f.write(RTL_DOTF_CONTEXT)
        code = codeText(ctxFile, "//")
        assert code.params.context == ["proj.yaml"], \
            f"expected params.context ['proj.yaml'], got {code.params.context!r}"
        assert code.params.project is None, \
            f"context-mode file must leave --project None, got {code.params.project!r}"
    print("PASS: parseParam accepts --project and keeps --context distinct")


def test_restamp_line_conversion_and_idempotency():
    """_restampParamLine converts the context form and is a no-op once the line
    already carries --project."""
    hasParam, converted = _restampParamLine(RTL_DOTF_CONTEXT, "--project=myProj")
    assert hasParam, "the context form does carry a PARAM line"
    assert converted == RTL_DOTF_PROJECT, "context form must convert to --project form"
    # Everything below the PARAM line is untouched.
    assert "+incdir+.\nproj_package.sv\n" in converted
    assert _restampParamLine(RTL_DOTF_PROJECT, "--project=myProj") == (True, None), \
        "already --project must be a no-op (idempotent)"
    print("PASS: _restampParamLine converts context form and is idempotent")


def test_restamp_line_reports_missing_param_line():
    """A file with NO GENERATED_CODE_PARAM line is distinguished from
    'already correct': hasParamLine is False, so callers can report it as manual
    work instead of silently skipping it."""
    noParam = (
        "+libext+.sv\n"
        "// GENERATED_CODE_BEGIN --template=rtlDotF\n"
        "// GENERATED_CODE_END\n"
    )
    assert _restampParamLine(noParam, "--project=myProj") == (False, None), \
        "a file with no PARAM line must report hasParamLine False"
    print("PASS: _restampParamLine distinguishes a missing PARAM line from a no-op")


def test_restamp_project_mode_file():
    """restampProjectParam re-stamps the project-mode artifact identified through
    the fileMap mode:project entry, writes only under --write, and is idempotent."""
    with tempfile.TemporaryDirectory() as work:
        path = _write(work, RTL_DOTF_CONTEXT)
        prj = _FakePrj(work)

        # Dry-run: reports the re-stamp but leaves the file unchanged.
        report = restampProjectParam(prj, write=False)
        assert any(i.kind == PROJECT_PARAM_RESTAMP for i in report.applied), \
            "dry-run must report the project-mode re-stamp"
        assert report.clean
        with open(path) as f:
            assert "--context=proj.yaml" in f.read(), "dry-run must not write"

        # Write: the PARAM line becomes --project, content below is unchanged.
        report = restampProjectParam(prj, write=True)
        assert report.written
        with open(path) as f:
            after = f.read()
        assert after == RTL_DOTF_PROJECT, "written file must match the --project form"

        # Idempotent: a second write finds nothing to do.
        report = restampProjectParam(prj, write=True)
        assert not report.applied and not report.written, \
            "re-stamp must be idempotent once converted"
    print("PASS: restampProjectParam re-stamps the mode:project artifact idempotently")


def test_restamp_skips_ungenerated_file():
    """A project-mode path that lacks the generated marker is reported, never
    re-stamped (a hand-authored file wearing the artifact name is protected)."""
    with tempfile.TemporaryDirectory() as work:
        path = _write(work, "+libext+.sv\n// GENERATED_CODE_PARAM --context=proj.yaml\n")
        prj = _FakePrj(work)
        report = restampProjectParam(prj, write=True)
        assert not report.applied, "unmarked file must not be re-stamped"
        assert any(i.kind == TODO_UNGENERATED_FILE for i in report.manual)
        assert not report.clean
        with open(path) as f:
            assert "--context=proj.yaml" in f.read(), "unmarked file must be untouched"
    print("PASS: restampProjectParam protects an unmarked project-mode path")


NO_PARAM_GENERATED = (
    "+libext+.sv\n"
    "// GENERATED_CODE_BEGIN --template=rtlDotF\n"
    "+incdir+.\n"
    "// GENERATED_CODE_END\n"
)


def test_restamp_reports_generated_file_without_param_line():
    """A GENERATED file whose PARAM line is missing entirely is reported as
    manual work (not silently skipped as 'already correct'), so --sweep exits
    non-zero via report.clean."""
    with tempfile.TemporaryDirectory() as work:
        path = _write(work, NO_PARAM_GENERATED)
        prj = _FakePrj(work)
        report = restampProjectParam(prj, write=True)
        assert not report.applied, "there is no PARAM line to re-stamp"
        assert any(i.kind == TODO_MISSING_PARAM_LINE for i in report.manual), \
            f"missing PARAM line must be a manual TODO, got {report.manual}"
        assert not report.clean, "a missing PARAM line must fail the sweep"
        assert not report.written
        with open(path) as f:
            assert f.read() == NO_PARAM_GENERATED, "the file must be untouched"
    print("PASS: restampProjectParam reports a generated file with no PARAM line")


# --- context-mode --project + canonical --context stamping ---------------

# A firmware IncludesFW header, stale form: a non-canonical --context spelling
# (build-root-relative basename) and no --project, as a foreign build root left
# it. Migration must normalize --context to the canonical yamlContext key AND add
# --project, preserving the file type's --mode.
CTX_FW_STALE = (
    "#ifndef GUARD\n#define GUARD\n"
    "// GENERATED_CODE_PARAM --context=ipLeaf.yaml --mode=fw\n"
    "// GENERATED_CODE_BEGIN --template=headers --fileMapKey=includeFW_hdr\n"
    "// GENERATED_CODE_END\n#endif\n"
)
CTX_FW_CANONICAL = CTX_FW_STALE.replace(
    "// GENERATED_CODE_PARAM --context=ipLeaf.yaml --mode=fw\n",
    "// GENERATED_CODE_PARAM --project=myProj --context=../../leaf/yaml/ipLeaf.yaml --mode=fw\n")


class _FakeContextPrj:
    """The subset restampContextParam reads: PROJECTNAME, INCLUDEFILES (fileType
    -> {canonical context key: {fileName}}), and contextOwningProject keyed by the
    same canonical keys. Two contexts, one owned by this project and one by a
    child, exercise the owner guard. The --mode token is not per file: it comes
    from the fileType, via genFileParam.contextParamMode."""

    def __init__(self, ownedPath, foreignPath):
        self.contextOwningProject = {
            "../../leaf/yaml/ipLeaf.yaml": "myProj",
            "../../ip/yaml/ip.yaml": "childProj",
        }
        includeFiles = {
            "includeFW_hdr": {
                "../../leaf/yaml/ipLeaf.yaml": {"fileName": ownedPath},
                "../../ip/yaml/ip.yaml": {"fileName": foreignPath},
            },
        }
        self.config = _FakeConfig({"PROJECTNAME": "myProj",
                                   "INCLUDEFILES": includeFiles})


def test_context_restamp_line_conversion_and_idempotency():
    """The shared _restampParamLine, fed the canonical contextParamTail,
    normalizes --context to the canonical key, adds --project, preserves --mode,
    and is a no-op once the line is canonical."""
    tail = contextParamTail("myProj", "../../leaf/yaml/ipLeaf.yaml", "fw")
    hasParam, converted = _restampParamLine(CTX_FW_STALE, tail)
    assert hasParam
    assert converted == CTX_FW_CANONICAL, "stale context form must normalize + gain --project"
    # The generated region below the PARAM line is untouched.
    assert "--fileMapKey=includeFW_hdr" in converted
    assert _restampParamLine(CTX_FW_CANONICAL, tail) == (True, None), \
        "already-canonical line must be a no-op (idempotent)"
    print("PASS: context param tail normalizes --context and adds --project idempotently")


def test_restamp_context_mode_files_owner_guard():
    """restampContextParam re-stamps only the context files this project OWNS
    (owner == PROJECTNAME); a foreign-owned copy is left for its own migration."""
    with tempfile.TemporaryDirectory() as work:
        owned = os.path.join(work, "ipLeafIncludesFW.h")
        foreign = os.path.join(work, "ipIncludesFW.h")
        with open(owned, "w") as f:
            f.write(CTX_FW_STALE)
        with open(foreign, "w") as f:
            f.write(CTX_FW_STALE)
        prj = _FakeContextPrj(owned, foreign)

        report = restampContextParam(prj, write=True)
        assert report.written
        assert any(i.kind == CONTEXT_PARAM_RESTAMP for i in report.applied)
        with open(owned) as f:
            assert f.read() == CTX_FW_CANONICAL, "owned file must be re-stamped canonical"
        with open(foreign) as f:
            assert f.read() == CTX_FW_STALE, "foreign-owned file must be left untouched"

        # Idempotent: a second write finds nothing to do.
        report = restampContextParam(prj, write=True)
        assert not report.applied and not report.written, \
            "context re-stamp must be idempotent once canonical"
    print("PASS: restampContextParam re-stamps owned context files under the owner guard")


def test_unregistered_context_filekey_fails_loud():
    """A context file key with no _CONTEXT_FILE_MODE entry is rejected rather than
    re-stamped without its --mode. The token selects the emission flavor the file
    regenerates with (model / fw / module), so a silently dropped --mode would
    change what the next `make gen` writes into the file; adding a context fileType
    to a fileMap therefore fails loud until its mode is recorded in
    pysrc/genFileParam.py."""
    class _UnknownTypePrj:
        def __init__(self):
            self.contextOwningProject = {"a.yaml": "myProj"}
            self.config = _FakeConfig({
                "PROJECTNAME": "myProj",
                "INCLUDEFILES": {
                    "brandNewType_hdr": {"a.yaml": {"fileName": "a.h"}},
                },
            })

    try:
        restampContextParam(_UnknownTypePrj(), write=False)
    except SystemExit:
        print("PASS: an unregistered context file key fails loud")
        return
    assert False, "an unregistered context file key must not be silently accepted"


def test_resolveContextKey_no_basename_fallback():
    """resolveContextKey returns an exact yamlContext key and now ERRORS on a
    non-exact (e.g. basename) name: the basename-matching fallback is removed, so
    an owned file's --context must be the canonical key (added by migration)."""
    fake = SimpleNamespace(yamlContext={"../../leaf/yaml/ipLeaf.yaml": {}})
    assert processYaml.projectOpen.resolveContextKey(fake, "../../leaf/yaml/ipLeaf.yaml") \
        == "../../leaf/yaml/ipLeaf.yaml", "exact key must resolve unchanged"
    try:
        processYaml.projectOpen.resolveContextKey(fake, "ipLeaf.yaml")
    except SystemExit:
        pass  # expected: a bare basename no longer matches (fallback removed)
    else:
        assert False, "a non-exact context name must error, not basename-match"
    print("PASS: resolveContextKey has no basename fallback (non-exact name errors)")


def test_resolveFileOwner_context_file_via_project():
    """A context file carrying --project resolves its owner directly through
    params.project, never touching resolveContextKey (which would raise on this
    fake, proving the context path is not exercised)."""
    def _boom(self, name):
        raise AssertionError("resolveContextKey must not be called for a --project file")
    fake = SimpleNamespace(
        projectLayout={"childProj": {}},
        resolveContextKey=lambda name: _boom(fake, name))
    params = SimpleNamespace(project="childProj", parent=None, block=None, context=None)
    owner = processYaml.projectOpen.resolveFileOwner(fake, params)
    assert owner == "childProj", f"owner must come straight from --project, got {owner!r}"
    print("PASS: resolveFileOwner resolves a context file's owner via --project")


def run_all_tests():
    test_parseParam_accepts_project()
    test_restamp_line_conversion_and_idempotency()
    test_restamp_line_reports_missing_param_line()
    test_restamp_project_mode_file()
    test_restamp_skips_ungenerated_file()
    test_restamp_reports_generated_file_without_param_line()
    test_context_restamp_line_conversion_and_idempotency()
    test_restamp_context_mode_files_owner_guard()
    test_unregistered_context_filekey_fails_loud()
    test_resolveContextKey_no_basename_fallback()
    test_resolveFileOwner_context_file_via_project()
    print("\nAll project-param tests passed.")


if __name__ == "__main__":
    run_all_tests()
