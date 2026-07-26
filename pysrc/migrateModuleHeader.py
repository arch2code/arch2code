"""Restructure the generated block-module `.cppm` header from the legacy single
generated region into the three-section form (the module-header phase of the
unified YAML migration).

The legacy block `.cppm` carried the whole module header — `module;`, the global
module fragment `#include`s, `export module <block>.block;`, and every `import` —
in ONE generated region (`moduleScaffold --section=blockModuleHeader`). Its only
user-editable slot was the gap AFTER that region, which sits in the module
purview: a non-modular shared `#include` (e.g. `endOfTest.h`) forced there
attaches its declarations to the block module and clashes with textual includes
of the same header elsewhere.

The generator template split (templates/systemc/moduleScaffold.py) makes
`blockModuleHeader` GMF-only and adds a sibling `moduleExport` region that owns
`export module` + the imports, with two seeded user slots (`// user #includes
here` in the GMF zone, `// user imports here` in the preamble). This phase brings
an existing block `.cppm` up to that form so the next `gen` repopulates the
regions correctly.

Standalone and text-only, like `migrateIncludes`: it reads source as text and
never opens the project database. It manipulates markers only — every span below
the class region is untouched.

Mechanical (applied automatically): for each module-form block `.cppm` (one
carrying the `blockModuleHeader` region), insert the missing `moduleExport`
region and the `// user imports here` slot immediately BEFORE the class region's
`GENERATED_CODE_BEGIN` (the `classDecl` region for a normal block, the `blockRegs
--section=header` region for a reg-handler). On the next `gen` the old single
header region refills to GMF-only and the export/imports populate `moduleExport`.
A neat consequence: the old user gap (between the old header region and the class
region) ends up BEFORE `moduleExport` — i.e. in the GMF zone — so an existing
`#include "endOfTest.h"` there lands in the GMF slot automatically.

Reported and handed to the migration skill (not mechanical): any hand-added
`import` line left in that old gap (now in the GMF zone) must move down to the
`// user imports here` slot — imports before `export module` are illegal. The
tool only reports this (`TODO_MODULE_IMPORT`); it never moves an import, which is
the migrating agent's judgment step.

Idempotent: a file already carrying a `moduleExport` region is a no-op.
"""

import os
from dataclasses import dataclass, field

import yaml

from pysrc.migrateCommon import _read, _write, _loc, SKIP_DIRS


# Marker fragments the phase keys on.
BLOCK_HEADER_MARKER = "--template=moduleScaffold --section=blockModuleHeader"
MODULE_EXPORT_MARKER = "--template=moduleExport"
GEN_BEGIN = "// GENERATED_CODE_BEGIN"
GEN_END = "// GENERATED_CODE_END"

# The three lines inserted before the class region's GENERATED_CODE_BEGIN. Byte
# for byte the fresh-scaffold shape (templates/fileGen/fileGen.py): the empty
# moduleExport region plus the seeded preamble user slot.
_INSERT = (
    f"{GEN_BEGIN} {MODULE_EXPORT_MARKER}\n"
    f"{GEN_END}\n"
    "// user imports here\n"
)

# Applied-edit kind.
MODULE_HEADER_RESTRUCTURE = "MODULE_HEADER_RESTRUCTURE"  # moduleExport region inserted

# Manual-TODO kind (delegated to the migration skill).
TODO_MODULE_IMPORT = "TODO_MODULE_IMPORT"  # hand-added import left in the GMF gap


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line (or file) of the edited / offending line
    message: str     # human-facing description


@dataclass
class ModuleHeaderReport:
    projectYaml: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        """True when nothing is left for the skill to resolve by hand."""
        return not self.manual


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def migrateModuleHeaderInProject(projectYamlPath, write=False):
    """Restructure every module-form block `.cppm` under one project into the
    three-section header form.

    Idempotent: a file already carrying a `moduleExport` region is skipped; a
    file with no `blockModuleHeader` region is not a block module and is skipped.
    When `write` is true the moduleExport region and the `// user imports here`
    slot are inserted before the class region.

    Returns a ModuleHeaderReport.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectDir = os.path.dirname(projectYamlPath)
    report = ModuleHeaderReport(projectYaml=projectYamlPath)

    projectData = yaml.safe_load(_read(projectYamlPath)) or {}
    dirs = projectData.get("dirs") or {}
    if "root" not in dirs:
        return report
    rootDir = os.path.abspath(os.path.join(projectDir, dirs["root"]))

    wrote = False
    for path in sorted(_cppmFiles(rootDir)):
        text = _read(path)
        if BLOCK_HEADER_MARKER not in text:
            continue  # not a block-module .cppm
        if MODULE_EXPORT_MARKER in text:
            continue  # already in three-section form (idempotent)

        anchor0, gapImports = _restructureSites(text)
        if anchor0 is None:
            continue  # malformed: no class region after the header; leave it

        report.applied.append(ReportItem(
            MODULE_HEADER_RESTRUCTURE, _loc(path, anchor0 + 1),
            "inserted moduleExport region and `// user imports here` slot before "
            "the class region; the next gen refills blockModuleHeader to GMF-only "
            "and populates moduleExport"))
        for line0 in gapImports:
            report.manual.append(ReportItem(
                TODO_MODULE_IMPORT, _loc(path, line0 + 1),
                "hand-added import now sits in the GMF zone (before `export "
                "module`); move it down to the `// user imports here` slot"))

        if write:
            _write(path, _insertExportRegion(text, anchor0))
            wrote = True

    report.written = wrote
    return report


# ---------------------------------------------------------------------------
# File-set discovery
# ---------------------------------------------------------------------------

def _cppmFiles(rootDir):
    """All `.cppm` files under the project root, excluding build trees."""
    for dirpath, dirnames, filenames in os.walk(rootDir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".cppm"):
                continue
            path = os.path.join(dirpath, fn)
            # A dangling symlink is a directory entry with no readable target;
            # skip anything that is not a real file.
            if os.path.isfile(path):
                yield path


# ---------------------------------------------------------------------------
# Restructure computation
# ---------------------------------------------------------------------------

def _restructureSites(text):
    """Locate the class-region insertion anchor and any stray gap imports.

    Returns `(anchor0, gapImports)` where `anchor0` is the 0-based line index of
    the class region's `GENERATED_CODE_BEGIN` (the `moduleExport` region and the
    user slot are inserted just before it) and `gapImports` is the list of 0-based
    line indices of hand-added `import` lines in the gap between the block header
    region's `GENERATED_CODE_END` and that anchor. `anchor0` is None when the file
    is malformed (no class region follows the header region)."""
    lines = text.splitlines()

    headerBegin0 = _firstIndex(lines, lambda s: GEN_BEGIN in s and BLOCK_HEADER_MARKER in s)
    if headerBegin0 is None:
        return None, []
    headerEnd0 = _firstIndex(lines, lambda s: s.strip() == GEN_END, start=headerBegin0 + 1)
    if headerEnd0 is None:
        return None, []
    # The class region is the first generated region opened after the header
    # region's end — classDecl for a normal block, blockRegs for a reg-handler.
    anchor0 = _firstIndex(lines, lambda s: GEN_BEGIN in s, start=headerEnd0 + 1)
    if anchor0 is None:
        return None, []

    gapImports = [i for i in range(headerEnd0 + 1, anchor0)
                  if _isImportLine(lines[i])]
    return anchor0, gapImports


def _insertExportRegion(text, anchor0):
    """Insert the moduleExport region + `// user imports here` slot before the
    0-based `anchor0` line, preserving the file's original newline handling."""
    lines = text.splitlines(keepends=True)
    lines.insert(anchor0, _INSERT)
    return "".join(lines)


def _isImportLine(line):
    """True for a C++20 module import declaration (`import <name>;`). A
    using-namespace or a commented line is not an import."""
    s = line.strip()
    return s.startswith("import ") and s.endswith(";")


def _firstIndex(lines, pred, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    return None
