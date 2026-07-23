#!/usr/bin/env python3
"""Unified YAML migration orchestrator — the `make migrate` driver.

Brings a pre-`yamlFormat: 2` arch2code project up to the current authoring
format and stamps the sentinel once the result is format-2 clean. It is the
single command the `projectCreate` gate names when it stops an un-migrated
project.

The text-conversion phases are standalone on purpose: a pre-migration project
cannot pass the `projectCreate` yamlFormat gate, so they must run WITHOUT opening
the database. They read and rewrite YAML as text, exactly as their phase
libraries do; they never invoke `arch2code.py`.

    migrateYaml.py [--write] <project.yaml>

A separate `--sweep` mode runs the post-database orphan sweep once the project
is stamped/format-2 and `make db` has built the database. Unlike the text
phases it opens the database READ-ONLY (`projectOpen`) to expand the legacy
fileMap to concrete paths, and deletes the purely-generated legacy orphans:

    migrateYaml.py --sweep [--write] --db <project.db>

The two modes are disjoint: `--sweep` runs only the orphan sweep (no text
phases, no project.yaml), and the text/default path never opens the database.

Three ordered phases run over the project's YAML file set (the project.yaml
`projectFiles:` entries plus their `include:` chains):

  Phase A  eval Python -> SV subset     (pysrc.evalPyToSv.convertEvalsInFile)
  Phase B  addressControl -> per-block  (pysrc.migrateAddressControl)
  Phase C  stamp yamlFormat: 2          (only when A and B leave no manual work)

Default is dry-run: the full combined report prints and nothing on disk
changes. `--write` applies the edits. A project already carrying
`yamlFormat: 2` short-circuits to "already migrated" — no phases run.

Phase C writes the single top-level `yamlFormat: 2` only when Phase A reports
no NEEDS_MANUAL eval rows and Phase B reports `clean` (its `clean` property is
true only when no manual TODO remains and the `addressControl:` pointer has
been removed). If either phase leaves manual work, the checklist prints and the
sentinel is not written, so the gate keeps failing until the project is
genuinely clean.
"""

import argparse
import os
import sys
from dataclasses import dataclass, field

import yaml

from pysrc.evalPyToSv import convertEvalsInFile
from pysrc.migrateCommon import _read, _write, _projectFileSet
from pysrc.migrateLayout import (
    LAYOUT_ALREADY_HIERARCHICAL,
    LAYOUT_FUNCTIONAL,
    LAYOUT_NEEDS_MIGRATION,
    migrateLayoutInProject,
)
from pysrc.migrateAddressControl import migrateAddressControlInProject
from pysrc.migrateIncludes import migrateIncludesInProject
from pysrc.migrateOrphans import renderReport as renderOrphanReport, sweepOrphans
from pysrc.processYaml import CURRENT_YAML_FORMAT, projectOpen


@dataclass
class MigrateResult:
    projectYaml: str
    alreadyMigrated: bool = False
    evalReports: list = field(default_factory=list)  # list[evalPyToSv.FileReport]
    addressReport: object = None                      # migrateAddressControl.MigrationReport
    includesReport: object = None                     # migrateIncludes.IncludesReport
    stamped: bool = False
    wrote: bool = False

    @property
    def evalManual(self):
        """(path, EvalRow) pairs for every NEEDS_MANUAL eval row across the file
        set. A non-empty list blocks the stamp."""
        return [(r.path, row) for r in self.evalReports for row in r.manual]

    @property
    def stampEligible(self):
        """True when nothing is left for the user to fix by hand: no manual eval
        rows, a clean Phase B report, and a clean includes phase. Phase B's
        `clean` encodes that no address TODO remains and the `addressControl:`
        pointer was removed; the includes phase's `clean` encodes that no
        user-code import rewrite remains. All three are part of yamlFormat: 2."""
        if self.addressReport is None or self.includesReport is None:
            return False
        return (not self.evalManual and self.addressReport.clean
                and self.includesReport.clean)


def migrateProject(projectYamlPath, write=False):
    """Run the three migration phases over one project and return a MigrateResult.

    Idempotent: a project already stamped `yamlFormat: CURRENT_YAML_FORMAT`
    short-circuits with no phases run and no writes. When `write` is true the
    phase edits are applied and the sentinel is stamped only when the project is
    format-2 clean.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    result = MigrateResult(projectYaml=projectYamlPath)

    projectData = yaml.safe_load(_read(projectYamlPath)) or {}

    # The include header -> cppm module conversion is part of yamlFormat: 2. It
    # runs on every invocation and is idempotent (a project whose include file
    # type is already the base cppm module is a no-op). It runs before the stamp
    # short-circuit so a project stamped before this phase existed still gets its
    # includes migrated; the eval/address phases already ran when it was stamped.
    result.includesReport = migrateIncludesInProject(projectYamlPath, write=write)

    if projectData.get("yamlFormat") == CURRENT_YAML_FORMAT:
        result.alreadyMigrated = True
        result.wrote = write and result.includesReport.written
        return result

    projectDir = os.path.dirname(projectYamlPath)
    files = _projectFileSet(projectDir, projectData)

    # The addressControl file (named by the `addressControl:` pointer) is not in
    # the projectFiles/include closure, but Phase B copies its AddressGroups
    # field values verbatim into the emitted addressBlock:. Add it to the Phase-A
    # sweep so a Python-syntax eval there is converted to the SV subset before
    # Phase B reads the file fresh from disk and copies the value on. Phase B
    # deletes the legacy file afterwards, so only the values that survive into
    # addressBlock: need the conversion — which this provides.
    pointer = projectData.get("addressControl")
    if pointer:
        addrCtlPath = os.path.abspath(os.path.join(projectDir, pointer))
        if addrCtlPath not in files and os.path.isfile(addrCtlPath):
            files = files + [addrCtlPath]

    # Phase A — convert Python-syntax evals to the SV subset in each project
    # file. CONVERTED rows are rewritten under --write; NEEDS_MANUAL rows are
    # reported and block the stamp.
    for path in files:
        result.evalReports.append(convertEvalsInFile(path, write=write))

    # Phase B — convert legacy addressControl to the per-block schema. Reads the
    # files fresh from disk, so it sees Phase A's rewrites.
    result.addressReport = migrateAddressControlInProject(projectYamlPath,
                                                          write=write)

    # Phase C — stamp the sentinel only when both phases are clean.
    if write and result.stampEligible:
        _stamp(projectYamlPath)
        result.stamped = True

    result.wrote = write and (
        any(r.written for r in result.evalReports)
        or result.addressReport.written
        or result.includesReport.written
        or result.stamped
    )
    return result


def _stamp(projectYamlPath):
    """Write the single top-level `yamlFormat:` sentinel at the head of
    project.yaml. Called only when the project is otherwise format-2 clean and
    not already stamped, so there is never a duplicate sentinel."""
    text = _read(projectYamlPath)
    _write(projectYamlPath, f"yamlFormat: {CURRENT_YAML_FORMAT}\n" + text)


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def renderReport(result, write):
    """Render the full combined dry-run / write report as text."""
    lines = [f"=== YAML migration: {result.projectYaml} ==="]
    if result.alreadyMigrated:
        lines.append(f"Already migrated (yamlFormat: {CURRENT_YAML_FORMAT}); "
                     f"eval/address phases skipped.")
        _renderIncludes(result, lines)
        return "\n".join(lines)

    _renderPhaseA(result, lines)
    _renderPhaseB(result, lines)
    _renderIncludes(result, lines)
    _renderPhaseC(result, write, lines)
    return "\n".join(lines)


def _renderPhaseA(result, lines):
    lines.append("")
    lines.append("Phase A - eval Python -> SV subset")
    anyRows = False
    for rep in result.evalReports:
        converted = rep.converted
        manual = rep.manual
        if not converted and not manual:
            continue
        anyRows = True
        lines.append(f"  {os.path.basename(rep.path)}:")
        for row in converted:
            lines.append(f"    line {row.line}: CONVERTED    "
                         f"{row.original}  ->  {row.result.expr}")
        for row in manual:
            lines.append(f"    line {row.line}: NEEDS_MANUAL  "
                         f"{row.original}   ({row.result.reason})")
    if not anyRows:
        lines.append("  no Python-syntax eval rows; all already in the SV subset")


def _renderPhaseB(result, lines):
    lines.append("")
    lines.append("Phase B - addressControl -> per-block schema")
    report = result.addressReport
    if not report.applied and not report.manual:
        lines.append("  no legacy addressControl: pointer; nothing to do")
        return
    if report.applied:
        lines.append("  applied:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO:")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")


def _renderIncludes(result, lines):
    lines.append("")
    lines.append("Includes - include header -> cppm module")
    report = result.includesReport
    if report is None or (not report.applied and not report.manual):
        lines.append("  include file type already cppm; nothing to do")
        return
    if report.applied:
        lines.append("  applied:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO (see the migration skill):")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")


def _renderPhaseC(result, write, lines):
    lines.append("")
    lines.append(f"Phase C - stamp yamlFormat: {CURRENT_YAML_FORMAT}")
    if result.stampEligible:
        if write and result.stamped:
            lines.append(f"  STAMPED yamlFormat: {CURRENT_YAML_FORMAT}")
        else:
            lines.append(f"  WOULD STAMP yamlFormat: {CURRENT_YAML_FORMAT} "
                         f"(dry-run; re-run with --write to apply)")
        return
    lines.append("  BLOCKED - project is not yet format-2 clean:")
    for path, row in result.evalManual:
        lines.append(f"    - {os.path.basename(path)}:{row.line} eval needs "
                     f"manual conversion: {row.original}")
    for item in result.addressReport.manual:
        lines.append(f"    - {item.location} {item.message}")
    for item in result.includesReport.manual:
        lines.append(f"    - {item.location} {item.message}")
    lines.append("  Resolve the items above (see address-migration.md for the "
                 "address TODOs and the migration skill for the include "
                 "import rewrites), then re-run.")


# ---------------------------------------------------------------------------
# Layout migration (opt-in functional -> hierarchical; separate invocation)
# ---------------------------------------------------------------------------

def renderLayoutReport(report, write):
    """Render the opt-in layout-migration report as text."""
    lines = [f"=== layout migration: {report.projectYaml} ===",
             f"declared layout: {report.declaredLayout}"]
    if report.state == LAYOUT_FUNCTIONAL:
        lines.append("Project has not opted into hierarchical layout "
                     "(fileGeneration.layout: functional); nothing to do.")
    elif report.state == LAYOUT_ALREADY_HIERARCHICAL:
        lines.append("Project is already hierarchical on disk "
                     "(project file under <prj>/<yaml>/); nothing to do.")
    elif report.state == LAYOUT_NEEDS_MIGRATION:
        if any(i.kind == "TODO_NOT_FORMAT2" for i in report.manual):
            lines.append("BLOCKED - cannot migrate layout yet:")
            for item in report.manual:
                lines.append(f"  {item.location}  {item.kind}  {item.message}")
        else:
            _renderRelocationMap(report, write, lines)
    return "\n".join(lines)


def _renderRelocationMap(report, write, lines):
    """Render the relocation move/delete map. Under `--write` the map has been
    applied on disk; without it this is a dry-run preview and nothing
    changed."""
    root = report.projectRoot

    def rel(path):
        return os.path.relpath(path, root) if root and path.startswith(root) else path

    lines.append("Project is functional on disk and opted into hierarchical.")
    if write and report.written:
        lines.append("  APPLIED relocation map:")
    else:
        lines.append("  DRY-RUN relocation map (re-run with --write to apply):")

    lines.append(f"  moves ({len(report.moves)}):")
    for mv in report.moves:
        lines.append(f"    [{mv.kind}] {rel(mv.src)}  ->  {rel(mv.dst)}")

    lines.append(f"  deletes ({len(report.deletes)}) "
                 f"[fully-generated source; recreated by make newmodule/gen]:")
    for path in report.deletes:
        lines.append(f"    {rel(path)}")

    lines.append(f"  path rewrites ({len(report.rewrites)}) "
                 f"[relative include/projectFiles/user-region references re-rooted]:")
    for rw in report.rewrites:
        lines.append(f"    [{rw.kind}] {rel(rw.path)}: {rw.old}  ->  {rw.new}")

    lines.append(f"  harness edits ({len(report.harnessEdits)}) "
                 f"[A2C_PRJ_YAML re-pointed at the moved project file; "
                 f"include/ stays at root]:")
    for edit in report.harnessEdits:
        verb = "replace" if edit.old else "insert"
        lines.append(f"    [{verb}] {rel(edit.path)}: {edit.new}")

    if report.manual:
        lines.append("  manual review (not moved or deleted):")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Migrate an arch2code project's user YAML to the current "
                    "authoring format (yamlFormat: %d)." % CURRENT_YAML_FORMAT)
    parser.add_argument("--write", action="store_true",
                        help="Apply the edits. Without it the tool is a dry-run "
                             "that prints the report and changes nothing.")
    parser.add_argument("--to-hierarchical", action="store_true",
                        dest="toHierarchical",
                        help="Run the opt-in functional -> hierarchical layout "
                             "migration instead of the unconditional yamlFormat "
                             "phases. Presupposes the project is already "
                             "yamlFormat: 2 and has declared "
                             "fileGeneration.layout: hierarchical.")
    parser.add_argument("--sweep", action="store_true",
                        help="Run the post-database orphan sweep instead of the "
                             "text-conversion phases. Requires --db and opens the "
                             "database READ-ONLY; run after `make db`.")
    parser.add_argument("--db",
                        help="Path to the built project database (required with "
                             "--sweep).")
    parser.add_argument("projectYaml", nargs="?",
                        help="Path to the project's project.yaml (required unless "
                             "--sweep is given).")
    args = parser.parse_args(argv)

    if args.sweep:
        if not args.db:
            parser.error("--sweep requires --db")
        prj = projectOpen(args.db)
        report = sweepOrphans(prj, write=args.write)
        print(renderOrphanReport(report, args.write))
        # A sweep that leaves manual items (ungenerated delete targets, pending
        # ports, user include sites) signals work remains, mirroring how the
        # text phases fail when manual TODOs block the stamp.
        return 0 if report.clean else 1

    if not args.projectYaml:
        parser.error("projectYaml is required unless --sweep is given")

    if args.toHierarchical:
        report = migrateLayoutInProject(args.projectYaml, write=args.write)
        print(renderLayoutReport(report, args.write))
        # A no-op (not opted in, or already hierarchical) always succeeds. A
        # candidate blocked on a manual precondition (e.g. not yet yamlFormat: 2)
        # fails so the make target signals work remains.
        return 0 if (report.isNoOp or report.clean) else 1

    result = migrateProject(args.projectYaml, write=args.write)
    print(renderReport(result, args.write))

    # Dry-run and an already-migrated project always succeed. A --write run that
    # could not stamp (manual work remains) fails so `make migrate` signals the
    # project is not yet buildable.
    # A --write run succeeds when the project is format-2 clean: either it was
    # stamped this run, or it already carried the stamp and the includes phase
    # (the one part of format 2 that can post-date the stamp) left no manual
    # work. Anything else means migration work remains, so signal non-zero.
    if args.write:
        ok = result.stamped or (result.alreadyMigrated
                                and result.includesReport.clean)
        if not ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
