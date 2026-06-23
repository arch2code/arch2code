#!/usr/bin/env python3
"""Unit tests for the includes (header -> cppm module) migration phase
(pysrc/migrateIncludes.py).

Each test builds a small synthetic project on disk in a temp dir and EXECUTES
migrateIncludesInProject end-to-end against real files, asserting on the
resulting file contents and the report. Nothing is mocked.

Coverage:
  - a project with a legacy header-mode `include` override has the override
    removed and its orphaned generated <context>Includes.{h,cpp} deleted, while
    the firmware <context>IncludesFW.{h,cpp} files are kept;
  - hand-written user code that #includes a migrated context header is reported
    as a TODO_USER_IMPORT, while a generated file (carrying GENERATED_CODE_BEGIN)
    that includes the same header is NOT reported;
  - dry-run changes nothing on disk;
  - a project whose include file type is already cppm is a no-op (idempotent).
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc.migrateIncludes import (
    migrateIncludesInProject,
    INCLUDE_OVERRIDE_REMOVE,
    STALE_FILE_DELETE,
    TODO_USER_IMPORT,
)

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


def _project(rootDir, includeExt):
    """Write a synthetic project under rootDir/arch/project.yaml. includeExt is
    the ext map literal for the `include` fileMap entry. Returns the path."""
    archDir = os.path.join(rootDir, "arch")
    modelDir = os.path.join(rootDir, "model")
    fwDir = os.path.join(rootDir, "fw")
    for d in (archDir, modelDir, fwDir):
        os.makedirs(d, exist_ok=True)
    projectYaml = os.path.join(archDir, "project.yaml")
    with open(projectYaml, "w") as fh:
        fh.write(
            "yamlFormat: 2\n"
            "projectName: t\n"
            "projectFiles:\n"
            "  - top.yaml\n"
            "dirs:\n"
            "  root: ..\n"
            "  model: $root/model\n"
            "  fwInc: $root/fw\n"
            "fileGeneration:\n"
            "  template: $a2c/templates/fileGen/fileGen.py\n"
            "  fileMap:\n"
            "    block       : { name: \"\",         ext: {hdr: \"h\", src: \"cpp\"}, cond: {hasMdl: true}, mode: block,   basePath: model }\n"
            f"    include     : {{ name: \"Includes\",  ext: {includeExt}, cond: {{smartInclude: true}}, mode: context, basePath: model }}\n"
            "    includeFW   : { name: \"IncludesFW\", ext: {hdr: \"h\", src: \"cpp\"}, cond: {smartInclude: true}, mode: context, basePath: fwInc }\n"
            "  fileCopyrightStatement: \"\"\n"
        )
    # The top.yaml in the file set is only walked for include chains; an empty
    # mapping is enough for this phase (it does not read block content).
    with open(os.path.join(archDir, "top.yaml"), "w") as fh:
        fh.write("blocks: {}\n")
    return projectYaml, modelDir, fwDir


def test_migrate_removes_override_and_stale_files():
    print("test_migrate_removes_override_and_stale_files")
    with tempfile.TemporaryDirectory() as root:
        projectYaml, modelDir, fwDir = _project(root, '{hdr: "h", src: "cpp"}')
        # Orphaned generated context include (the migration target) ...
        open(os.path.join(modelDir, "topIncludes.h"), "w").close()
        open(os.path.join(modelDir, "topIncludes.cpp"), "w").close()
        # ... firmware context include (must be kept) ...
        open(os.path.join(fwDir, "topIncludesFW.h"), "w").close()
        open(os.path.join(fwDir, "topIncludesFW.cpp"), "w").close()
        # ... a generated file that includes the header (NOT a gap; regen fixes) ...
        with open(os.path.join(modelDir, "top_base.h"), "w") as fh:
            fh.write('// GENERATED_CODE_BEGIN\n#include "topIncludes.h"\n')
        # ... and a hand-written user file that includes it (a gap).
        with open(os.path.join(modelDir, "utils.h"), "w") as fh:
            fh.write('#include "topIncludes.h"\n')

        report = migrateIncludesInProject(projectYaml, write=True)

        text = open(projectYaml).read()
        check("include     :" not in text, "include override removed from project.yaml")
        check(not os.path.exists(os.path.join(modelDir, "topIncludes.h")),
              "stale topIncludes.h deleted")
        check(not os.path.exists(os.path.join(modelDir, "topIncludes.cpp")),
              "stale topIncludes.cpp deleted")
        check(os.path.exists(os.path.join(fwDir, "topIncludesFW.h")),
              "firmware topIncludesFW.h kept")
        check(any(i.kind == INCLUDE_OVERRIDE_REMOVE for i in report.applied),
              "override removal reported")
        check(sum(1 for i in report.applied if i.kind == STALE_FILE_DELETE) == 2,
              "two stale-file deletions reported")
        userTodos = [i for i in report.manual if i.kind == TODO_USER_IMPORT]
        check(len(userTodos) == 1, "exactly one TODO_USER_IMPORT (user file only)")
        check(userTodos and "utils.h" in userTodos[0].location,
              "TODO_USER_IMPORT points at the user file, not the generated base")
        check(not report.clean, "report not clean while a user import remains")


def test_dry_run_changes_nothing():
    print("test_dry_run_changes_nothing")
    with tempfile.TemporaryDirectory() as root:
        projectYaml, modelDir, _ = _project(root, '{hdr: "h", src: "cpp"}')
        open(os.path.join(modelDir, "topIncludes.h"), "w").close()
        before = open(projectYaml).read()
        report = migrateIncludesInProject(projectYaml, write=False)
        check(open(projectYaml).read() == before, "project.yaml unchanged in dry-run")
        check(os.path.exists(os.path.join(modelDir, "topIncludes.h")),
              "stale file not deleted in dry-run")
        check(any(i.kind == INCLUDE_OVERRIDE_REMOVE for i in report.applied),
              "dry-run still reports the planned override removal")


def test_already_cppm_is_noop():
    print("test_already_cppm_is_noop")
    with tempfile.TemporaryDirectory() as root:
        projectYaml, _, _ = _project(root, '{cppm: "cppm"}')
        report = migrateIncludesInProject(projectYaml, write=True)
        check(not report.applied and not report.manual,
              "already-cppm project is a no-op")


if __name__ == "__main__":
    test_migrate_removes_override_and_stale_files()
    test_dry_run_changes_nothing()
    test_already_cppm_is_noop()
    print(f"\nResult: {'PASS' if FAIL == 0 else 'FAIL'} ({PASS} checks, {FAIL} failures)")
    sys.exit(1 if FAIL else 0)
