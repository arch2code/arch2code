#!/usr/bin/env python3
"""Unit tests for the langDomain migration phase (pysrc/migrateLangDomain.py).

Each test writes a small project file to a temp dir and runs the phase on it.
Nothing is mocked.

Coverage:
  - a flow-style entry gets `, langDomain: <value>` right after its basePath
    value, and a block-style entry gets a line after its basePath line at its
    siblings' indent;
  - the value follows the ext and basePath rule (sv/svh -> sv, fwInc -> fw,
    otherwise sc), and each addition is reported with the entry and value;
  - an entry that already has langDomain is left alone;
  - an entry the phase cannot edit is a manual TODO and its text is unchanged;
  - dry-run changes nothing, and a second run is a no-op;
  - through migrateYaml.migrateProject, a project already at yamlFormat 2 still
    gets the key, and the report shows it.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from pysrc.migrateLangDomain import (
    migrateLangDomainInProject,
    LANGDOMAIN_ADD,
    TODO_LANGDOMAIN,
)
from migrateYaml import migrateProject, renderReport

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


FILEMAP = (
    "fileGeneration:\n"
    "  fileMap:\n"
    "    rtlX   : { name: \"_x\", ext: {sv: \"sv\"}, mode: block, basePath: rtl,   desc: \"sv\" }\n"
    "    bodyX  : { name: \"_b\", ext: {svh: \"svh\"}, mode: block, basePath: vl_wrap }\n"
    "    fwX    : { name: \"Fw\", ext: {hdr: \"h\", src: \"cpp\"}, mode: context, basePath: fwInc, desc: \"fw\" }\n"
    "    scX    : { name: \"Sc\", ext: {cppm: \"cppm\"}, mode: block, basePath: \"model\", desc: \"sc\" }\n"
    "    doneX  : { name: \"D\", ext: {hdr: \"h\"}, mode: block, basePath: fwInc, langDomain: sc }\n"
    "    blockX:\n"
    "      name: \"Blk\"\n"
    "      ext: {sv: \"sv\"}\n"
    "      basePath: rtl  # a comment\n"
    "      desc: \"block style\"\n"
    "    lastX:\n"
    "      ext:\n"
    "        hdr: h\n"
    "      basePath: fwInc\n"
)

EXPECTED = (
    "fileGeneration:\n"
    "  fileMap:\n"
    "    rtlX   : { name: \"_x\", ext: {sv: \"sv\"}, mode: block, basePath: rtl, langDomain: sv,   desc: \"sv\" }\n"
    "    bodyX  : { name: \"_b\", ext: {svh: \"svh\"}, mode: block, basePath: vl_wrap, langDomain: sv }\n"
    "    fwX    : { name: \"Fw\", ext: {hdr: \"h\", src: \"cpp\"}, mode: context, basePath: fwInc, langDomain: fw, desc: \"fw\" }\n"
    "    scX    : { name: \"Sc\", ext: {cppm: \"cppm\"}, mode: block, basePath: \"model\", langDomain: sc, desc: \"sc\" }\n"
    "    doneX  : { name: \"D\", ext: {hdr: \"h\"}, mode: block, basePath: fwInc, langDomain: sc }\n"
    "    blockX:\n"
    "      name: \"Blk\"\n"
    "      ext: {sv: \"sv\"}\n"
    "      basePath: rtl  # a comment\n"
    "      langDomain: sv\n"
    "      desc: \"block style\"\n"
    "    lastX:\n"
    "      ext:\n"
    "        hdr: h\n"
    "      basePath: fwInc\n"
    "      langDomain: fw\n"
)


def _project(rootDir, body, yamlFormat=False):
    """Write rootDir/arch/project.yaml with `body` as its fileGeneration
    section. Returns the path."""
    archDir = os.path.join(rootDir, "arch")
    os.makedirs(archDir, exist_ok=True)
    projectYaml = os.path.join(archDir, "project.yaml")
    with open(projectYaml, "w") as fh:
        fh.write(("yamlFormat: 2\n" if yamlFormat else "")
                 + "projectName: t\nprojectFiles:\n  - top.yaml\ndirs:\n  root: ..\n" + body)
    with open(os.path.join(archDir, "top.yaml"), "w") as fh:
        fh.write("blocks: {}\n")
    return projectYaml


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_adds_key_to_flow_and_block_entries():
    print("test_adds_key_to_flow_and_block_entries")
    with tempfile.TemporaryDirectory() as root:
        projectYaml = _project(root, FILEMAP)
        before = _read(projectYaml)

        dry = migrateLangDomainInProject(projectYaml, write=False)
        check(_read(projectYaml) == before, "dry-run leaves the file unchanged")
        check(not dry.written, "dry-run reports nothing written")

        report = migrateLangDomainInProject(projectYaml, write=True)
        text = _read(projectYaml)
        check(text == before.replace(FILEMAP, EXPECTED),
              "flow entries gain the key after basePath, block entries a line after it")
        applied = [(i.kind, i.message) for i in report.applied]
        for name, value in (("rtlX", "sv"), ("bodyX", "sv"), ("fwX", "fw"), ("scX", "sc"),
                            ("blockX", "sv"), ("lastX", "fw")):
            check((LANGDOMAIN_ADD, f"fileMap entry '{name}' gets langDomain: {value}") in applied,
                  f"report lists {name} with langDomain {value}")
        check(len(report.applied) == 6, "the entry that already has langDomain is not reported")
        check(report.clean and report.written, "report is clean and written")
        fileMap = yaml.safe_load(text)["fileGeneration"]["fileMap"]
        check({k: v["langDomain"] for k, v in fileMap.items()} ==
              {"rtlX": "sv", "bodyX": "sv", "fwX": "fw", "scX": "sc", "doneX": "sc",
               "blockX": "sv", "lastX": "fw"},
              "the edited file parses with every entry's langDomain")

        again = migrateLangDomainInProject(projectYaml, write=True)
        check(_read(projectYaml) == text, "second run leaves the file unchanged")
        check(not again.applied and not again.manual and not again.written,
              "second run reports nothing")


def test_uneditable_entry_is_manual():
    print("test_uneditable_entry_is_manual")
    body = (
        "fileGeneration:\n"
        "  fileMap:\n"
        "    noExt  : { name: \"N\", mode: block, basePath: model }\n"
        "    folded:\n"
        "      ext: {hdr: h}\n"
        "      basePath: >-\n"
        "        fwInc\n"
        "    okX    : { name: \"O\", ext: {hdr: \"h\"}, mode: block, basePath: model }\n"
    )
    with tempfile.TemporaryDirectory() as root:
        projectYaml = _project(root, body)
        report = migrateLangDomainInProject(projectYaml, write=True)
        text = _read(projectYaml)
        manual = {i.message.split("'")[1]: i for i in report.manual}
        check(set(manual) == {"noExt", "folded"}, "the two uneditable entries are manual TODOs")
        check(all(i.kind == TODO_LANGDOMAIN for i in report.manual), "TODOs carry TODO_LANGDOMAIN")
        check(manual.get("noExt") is not None and manual["noExt"].location.endswith(":8"),
              "the TODO points at the entry's line")
        check("noExt  : { name: \"N\", mode: block, basePath: model }\n" in text
              and "      basePath: >-\n        fwInc\n    okX" in text,
              "the uneditable entries are left as written")
        check("basePath: model, langDomain: sc }" in text, "the editable entry still gets its key")
        check(not report.clean, "report is not clean while a TODO remains")


def test_runs_on_project_already_at_format_2():
    print("test_runs_on_project_already_at_format_2")
    with tempfile.TemporaryDirectory() as root:
        projectYaml = _project(root, FILEMAP, yamlFormat=True)
        result = migrateProject(projectYaml, write=True)
        check(result.alreadyMigrated, "the project short-circuits as already migrated")
        check(result.wrote, "the run still reports a write")
        check("langDomain: fw, desc: \"fw\"" in _read(projectYaml),
              "the already-stamped project gets the key")
        rendered = renderReport(result, True)
        check("fileMap entry 'fwX' gets langDomain: fw" in rendered,
              "the rendered report lists the addition")
        again = migrateProject(projectYaml, write=True)
        check(not again.wrote and again.langDomainReport.clean, "a second run writes nothing")
        check("every fileMap entry has langDomain; nothing to do" in renderReport(again, True),
              "the second report says there is nothing to do")


def main():
    test_adds_key_to_flow_and_block_entries()
    test_uneditable_entry_is_manual()
    test_runs_on_project_already_at_format_2()
    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
