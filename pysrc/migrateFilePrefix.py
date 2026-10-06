"""Move generated files to the names a filename prefix gives them.

Setting `svFilePrefix`, `scFilePrefix` or `fwFilePrefix` on a project that
had none renames every artifact of that kind. The files on disk hold user code
between their generated regions, so each one is moved byte for byte.
Scaffolding it afresh would lose that code, and `make newmodule` deletes a
generated file that no current artifact names.

The old name of an artifact is its current name without the prefix, in the
same directory. Changing one non-empty prefix to another is not migrated.
A file already at its current name stays put. When a file is missing and its
old name is some artifact's current name (block `foo` at `p_foo.sv` next to a
new block `p_foo`), nothing records whose code the old file holds, so no file
is moved at all.

DB-backed, because the new names come from the owning project's layout, so
this runs in the `migrateYaml.py --sweep` phase, ahead of the other passes.
Owner-gated: a composed build never moves a referenced child's file.
"""

import os
from dataclasses import dataclass, field

from pysrc.artifactPaths import currentArtifactRows, fileNamePrefix


# Applied-edit and manual-item kinds.
FILE_PREFIX_MOVE = "FILE_PREFIX_MOVE"
TODO_FILE_PREFIX_BOTH_EXIST = "TODO_FILE_PREFIX_BOTH_EXIST"
TODO_FILE_PREFIX_CHAIN = "TODO_FILE_PREFIX_CHAIN"


@dataclass(frozen=True)
class ReportItem:
    kind: str
    location: str
    message: str


@dataclass
class FilePrefixReport:
    projectName: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        return not self.manual


def moveRenamedFiles(prj, write=False):
    """Move each owned artifact from its unprefixed path to its prefixed one.
    Returns a FilePrefixReport."""
    projectName = prj.config.getConfig('PROJECTNAME')
    report = FilePrefixReport(projectName=projectName)
    allRows = currentArtifactRows(prj)
    currentPaths = {path for row in allRows for path in row['files'].values()}
    rows = [row for row in allRows
            if row['mode'] in ('block', 'registrar', 'context') and row['owner'] == projectName]
    # Two rows can name one file (a variant top also holds its pair tops).
    moves = dict()
    for row in rows:
        prefixLength = len(fileNamePrefix(row['fileDef'], row['layout']))
        if prefixLength == 0:
            continue
        for path in row['files'].values():
            directory, baseName = os.path.split(path)
            moves[path] = os.path.join(directory, baseName[prefixLength:])
    # A file already at its prefixed name is in place, even when its old name
    # is another artifact's current file.
    pending = {path: oldPath for path, oldPath in moves.items()
               if os.path.exists(oldPath)
               and not (os.path.exists(path) and oldPath in currentPaths)}
    # A missing file whose old name is another artifact's current file cannot
    # be attributed, so the whole move stops before any file changes.
    chained = sorted(path for path, oldPath in pending.items() if oldPath in currentPaths)
    for path in chained:
        chain = [moves[path], path]
        while chain[0] in moves:
            chain.insert(0, moves[chain[0]])
        report.manual.append(ReportItem(
            TODO_FILE_PREFIX_CHAIN, os.path.basename(path),
            f"{moves[path]} is the unprefixed name of {path} and also another "
            f"artifact's current name (names {' -> '.join(chain)}), so migrate "
            f"cannot tell whose code it holds and moved no file. Put each "
            f"artifact's code at its current name by hand"))
    if chained:
        return report
    wrote = False
    for path, oldPath in pending.items():
        if os.path.exists(path):
            report.manual.append(ReportItem(
                TODO_FILE_PREFIX_BOTH_EXIST, os.path.basename(path),
                f"both {oldPath} and {path} exist; keep the one holding your code "
                f"at {path} and delete the other"))
            continue
        report.applied.append(ReportItem(FILE_PREFIX_MOVE, os.path.basename(path),
                                         f"{oldPath} -> {path}"))
        if write:
            os.rename(oldPath, path)
            wrote = True
    report.written = wrote
    return report


def renderFilePrefixReport(report, write):
    lines = [f"=== filename-prefix move: {report.projectName} ==="]
    if not report.applied and not report.manual:
        lines.append("  no generated file needs a new name; nothing to do")
        return "\n".join(lines)
    verb = "moved" if write else "would move (dry-run; re-run with --write)"
    for item in report.applied:
        lines.append(f"  {verb}: {item.message}")
    for item in report.manual:
        lines.append(f"  TODO: {item.message}")
    return "\n".join(lines)
