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

Two further DB-backed modes run the agent-driven source ports:

    migrateYaml.py --port-tb [--write] --db <project.db>   # testbench family
    migrateYaml.py --port    [--write] --db <project.db>   # block implementations

`--port-tb` runs between `make newmodule` and `make gen`; `--port` runs after
`make gen`. All of the DB-backed modes are disjoint from the text phases: they
run only their own phase (no text phases, no project.yaml), and the text/default
path never opens the database.

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
import traceback
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
from pysrc.migrateAddressControl import (migrateAddressControlInProject,
                                         routedLeafRegisterPortsAdvisory)
from pysrc.migrateIncludes import migrateIncludesInProject
from pysrc.migrateLangDomain import migrateLangDomainInProject
from pysrc.migrateModuleHeader import migrateModuleHeaderInProject
from pysrc.migrateVariantSchema import migrateVariantSchemaInProject
from pysrc.migrateOrphans import renderReport as renderOrphanReport, sweepOrphans
from pysrc.migrateSubProjects import checkSubProjects
from pysrc.migrateProjectParam import (
    renderReport as renderProjectParamReport,
    restampProjectParam,
    restampContextParam,
)
from pysrc.migrateFilePrefix import moveRenamedFiles, renderFilePrefixReport
from pysrc.migrateModuleEndlabel import (
    restampModuleEndlabel,
    renderModuleEndlabelReport,
)
from pysrc.migrateStaleSvNames import reportStaleSvNames, renderStaleSvNameReport
from pysrc.migrateBlockModulePort import (
    portBlockModules,
    portTbExternals,
    portTbTops,
    renderBlockPortReport,
)
from pysrc.migrateTbConfig import (
    restructureTbConfigs,
    renderTbConfigReport,
)
from pysrc.processYaml import CURRENT_YAML_FORMAT, projectOpen


# Exit statuses. `make migrate` runs the phases as a chain, and it needs to tell
# three kinds of non-zero apart:
#   RC_TODO     manual work remains but the tree is consistent. The pipeline
#               carries on, because the generated tree must not be left
#               un-generated. The target still exits non-zero at the end while
#               the item is open.
#   RC_BLOCKED  the tree is in a state the FOLLOWING steps cannot safely
#               process, so the pipeline halts on it. A `<block>Config.cpp` still
#               carrying a bare `--template=tbConfig` region makes gen fail with a
#               template traceback. A file left at its unprefixed name next to its
#               prefixed one is a stale file to newmodule, which deletes it along
#               with the user code the TODO asks the user to keep.
#   RC_PHASE_FAILED  a --sweep phase raised, or a --sweep raised outside any
#               phase. On a writing run a write may be missing, and the
#               read-only sweep that ends `make migrate` cannot detect that.
#               The pipeline carries on, and the recipe exits 1 at the end. If
#               opening the database, the prefix move or its blocked report
#               raises, the filename-prefix gate has not passed, so the sweep
#               returns RC_BLOCKED, exit 2.
RC_CLEAN = 0
RC_TODO = 1
RC_BLOCKED = 2
RC_PHASE_FAILED = 3


TODO_PHASE_FAILED = "TODO_PHASE_FAILED"


@dataclass(frozen=True)
class PhaseFailure:
    kind: str
    location: str
    message: str


def _runPhase(failures, phase, location, fn, *args, **kwargs):
    """Run one migration phase, or record why it failed and return None.

    The phases are independent, so one that raises on a file it cannot handle
    must not stop the rest from running and reporting. Any exception counts: the
    traceback goes to stderr, the failure becomes a TODO in the report, and the
    caller exits non-zero."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        failures.append(PhaseFailure(
            TODO_PHASE_FAILED, location,
            f"phase '{phase}' raised {type(exc).__name__}: {exc}. Its report is "
            f"missing and its edits may be partial; the traceback is on stderr. "
            f"Fix the cause and re-run"))
        return None


def _printPhaseFailures(failures):
    lines = []
    _renderPhaseFailures(failures, lines)
    if lines:
        print("\n".join(lines))


def _renderPhaseFailures(failures, lines):
    """Append the phase-failure section; silent when every phase ran."""
    if not failures:
        return
    lines.extend(["", "Phase failures", "  manual TODO:"])
    for item in failures:
        lines.append(f"    {item.location}  {item.kind}  {item.message}")


@dataclass
class MigrateResult:
    projectYaml: str
    alreadyMigrated: bool = False
    evalReports: list = field(default_factory=list)  # list[evalPyToSv.FileReport]
    addressReport: object = None                      # migrateAddressControl.MigrationReport
    includesReport: object = None                     # migrateIncludes.IncludesReport
    moduleHeaderReport: object = None                 # migrateModuleHeader.ModuleHeaderReport
    variantReport: object = None                      # migrateVariantSchema.VariantReport
    langDomainReport: object = None                   # migrateLangDomain.LangDomainReport
    subProjectsReport: object = None                  # migrateSubProjects.SubProjectsReport
    leafAdvisory: list = field(default_factory=list)  # list[migrateAddressControl.ReportItem]
    phaseFailures: list = field(default_factory=list)  # list[PhaseFailure]
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
        rows, a clean Phase B report, a clean includes phase, a clean
        module-header phase, a clean langDomain phase, and every referenced
        child project already migrated.
        Phase B's `clean` encodes that no address TODO remains and the
        `addressControl:` pointer was removed; the includes phase's `clean`
        encodes that no user-code import rewrite remains; the module-header
        phase's `clean` encodes that no stray GMF-zone import remains to
        relocate; the sub-project check's `clean` encodes that the rest of the
        composition is migrated too. All are part of yamlFormat: 2. A phase that
        failed leaves its report None, which blocks the stamp."""
        if self.phaseFailures:
            return False
        if (self.addressReport is None or self.includesReport is None
                or self.moduleHeaderReport is None
                or self.variantReport is None
                or self.langDomainReport is None
                or self.subProjectsReport is None):
            return False
        return (not self.evalManual and self.addressReport.clean
                and self.includesReport.clean and self.moduleHeaderReport.clean
                and self.variantReport.clean
                and self.langDomainReport.clean
                and self.subProjectsReport.clean)


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
    failures = result.phaseFailures

    # The include header -> cppm module conversion is part of yamlFormat: 2. It
    # runs on every invocation and is idempotent (a project whose include file
    # type is already the base cppm module is a no-op). It runs before the stamp
    # short-circuit so a project stamped before this phase existed still gets its
    # includes migrated; the eval/address phases already ran when it was stamped.
    result.includesReport = _runPhase(failures, "includes", projectYamlPath,
                                      migrateIncludesInProject, projectYamlPath,
                                      write=write)

    # The block-module header restructure (single header region -> GMF-only
    # blockModuleHeader + moduleExport + seeded user slots) is part of
    # yamlFormat: 2. Like the includes phase it runs on every invocation, is
    # idempotent (a file already in three-section form is a no-op), and runs
    # before the stamp short-circuit so a project stamped before this phase
    # existed still gets its block `.cppm` headers restructured.
    result.moduleHeaderReport = _runPhase(failures, "module header", projectYamlPath,
                                          migrateModuleHeaderInProject,
                                          projectYamlPath, write=write)

    # The nested variant-schema rewrite (per-row variant list -> nested mapping)
    # is part of yamlFormat: 2. It edits authored `parameters:` sections,
    # unrelated to addressControl, so it runs on every invocation, is idempotent
    # (an already-nested file is a no-op), and runs before the stamp short-circuit
    # so a project stamped before this phase existed still gets its variant
    # bindings regrouped.
    result.variantReport = _runPhase(failures, "variant schema", projectYamlPath,
                                     migrateVariantSchemaInProject, projectYamlPath,
                                     write=write)

    # Every fileMap entry names its langDomain. The phase edits the project
    # file's fileMap, is idempotent, and runs before the stamp short-circuit so
    # a project stamped before the key existed still gets it.
    result.langDomainReport = _runPhase(failures, "langDomain", projectYamlPath,
                                        migrateLangDomainInProject, projectYamlPath,
                                        write=write)

    # Composed builds: every child project this one names must be migrated in its
    # own tree. Runs before the short-circuit so a top stamped before a child was
    # added still reports it, and because it is the only check that looks past
    # this project at all.
    result.subProjectsReport = _runPhase(failures, "composed-build check",
                                         projectYamlPath, checkSubProjects,
                                         projectYamlPath, CURRENT_YAML_FORMAT)

    # Advisory, not a phase: it writes nothing and is excluded from stampEligible
    # by construction. It sits before the short-circuit because its whole purpose
    # is to outlive the stamp — Phase B's equivalent TODO can only be raised on
    # the one run that still has the legacy AddressGroups table to read.
    advisory = _runPhase(failures, "routed-leaf advisory", projectYamlPath,
                         routedLeafRegisterPortsAdvisory, projectYamlPath)
    if advisory is not None:
        result.leafAdvisory = advisory

    if projectData.get("yamlFormat") == CURRENT_YAML_FORMAT:
        result.alreadyMigrated = True
        result.wrote = write and _anyWritten([result.includesReport,
                                              result.moduleHeaderReport,
                                              result.variantReport,
                                              result.langDomainReport])
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
        evalReport = _runPhase(failures, "Phase A (eval)", path,
                               convertEvalsInFile, path, write=write)
        if evalReport is not None:
            result.evalReports.append(evalReport)

    # Phase B — convert legacy addressControl to the per-block schema. Reads the
    # files fresh from disk, so it sees Phase A's rewrites.
    result.addressReport = _runPhase(failures, "Phase B (addressControl)",
                                     projectYamlPath, migrateAddressControlInProject,
                                     projectYamlPath, write=write)

    # Phase C — stamp the sentinel only when both phases are clean.
    if write and result.stampEligible:
        _stamp(projectYamlPath)
        result.stamped = True

    result.wrote = write and (
        _anyWritten(result.evalReports + [result.addressReport,
                                          result.includesReport,
                                          result.moduleHeaderReport,
                                          result.variantReport,
                                          result.langDomainReport])
        or result.stamped
    )
    return result


def _anyWritten(reports):
    """True when any phase that ran wrote an edit; a failed phase's report is None."""
    return any(r is not None and r.written for r in reports)


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
        _renderModuleHeader(result, lines)
        _renderVariant(result, lines)
        _renderLangDomain(result, lines)
        _renderSubProjects(result, lines)
        _renderLeafAdvisory(result, lines)
        _renderPhaseFailures(result.phaseFailures, lines)
        return "\n".join(lines)

    _renderPhaseA(result, lines)
    _renderPhaseB(result, lines)
    _renderIncludes(result, lines)
    _renderModuleHeader(result, lines)
    _renderVariant(result, lines)
    _renderLangDomain(result, lines)
    _renderSubProjects(result, lines)
    _renderLeafAdvisory(result, lines)
    _renderPhaseFailures(result.phaseFailures, lines)
    _renderPhaseC(result, write, lines)
    return "\n".join(lines)


def _phaseFailed(report, lines):
    """True, after saying so, when the section's phase failed and left no report."""
    if report is not None:
        return False
    lines.append("  FAILED; see Phase failures")
    return True


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
    if _phaseFailed(report, lines):
        return
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
    if _phaseFailed(report, lines):
        return
    if not report.applied and not report.manual:
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


def _renderModuleHeader(result, lines):
    lines.append("")
    lines.append("Module header - single region -> GMF + moduleExport sections")
    report = result.moduleHeaderReport
    if _phaseFailed(report, lines):
        return
    if not report.applied and not report.manual:
        lines.append("  block module headers already three-section; nothing to do")
        return
    if report.applied:
        lines.append("  applied:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO (see the migration skill):")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")


def _renderVariant(result, lines):
    lines.append("")
    lines.append("Variant schema - per-row variant list -> nested mapping")
    report = result.variantReport
    if _phaseFailed(report, lines):
        return
    if not report.applied and not report.manual:
        lines.append("  variant bindings already nested; nothing to do")
        return
    if report.applied:
        lines.append("  applied:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO (see the migration skill):")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")


def _renderLangDomain(result, lines):
    lines.append("")
    lines.append("langDomain - fileMap entries name their langDomain")
    report = result.langDomainReport
    if _phaseFailed(report, lines):
        return
    if not report.applied and not report.manual:
        lines.append("  every fileMap entry has langDomain; nothing to do")
        return
    if report.applied:
        lines.append("  applied:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO:")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")


def _renderSubProjects(result, lines):
    """Render the composed-build check. Silent on a project that references no
    child projects, which is most of them."""
    report = result.subProjectsReport
    if report is None or report.clean:
        return
    lines.append("")
    lines.append("Composed build - child projects not yet migrated")
    lines.append("  manual TODO (see the migration skill):")
    for item in report.manual:
        lines.append(f"    {item.location}  {item.kind}  {item.message}")


def _renderLeafAdvisory(result, lines):
    """Render the routed-leaf advisory. Silent when there is nothing to say — it
    prints on every run and would otherwise be noise in the common case."""
    if not result.leafAdvisory:
        return
    lines.append("")
    lines.append("Advisory - routed leaves with no registerPorts: "
                 "(informational; does not block the stamp)")
    for item in result.leafAdvisory:
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
    for item in result.phaseFailures:
        lines.append(f"    - {item.location} {item.message}")
    for path, row in result.evalManual:
        lines.append(f"    - {os.path.basename(path)}:{row.line} eval needs "
                     f"manual conversion: {row.original}")
    for report in (result.addressReport, result.includesReport,
                   result.moduleHeaderReport, result.variantReport,
                   result.langDomainReport, result.subProjectsReport):
        if report is None:
            continue
        for item in report.manual:
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


def _sweep(args, failures):
    """The post-database --sweep mode: every phase, then its exit status.
    Phase failures accumulate in the caller's `failures`."""
    prj = _runPhase(failures, "database open", args.db, projectOpen, args.db)
    # Files a filename-prefix change renamed move first, so every pass
    # below finds them at their current names.
    prefixReport = None if prj is None else _runPhase(
        failures, "filename-prefix move", args.db,
        moveRenamedFiles, prj, write=args.write)
    # A prefix conflict stops here, ahead of the orphan sweep deletions. So
    # does any failure up to here: newmodule would delete a file left unmoved.
    if prefixReport is None or not prefixReport.clean:
        if prefixReport is not None:
            _runPhase(failures, "filename-prefix report", args.db,
                      lambda: print(renderFilePrefixReport(prefixReport, args.write)))
        _printPhaseFailures(failures)
        return RC_BLOCKED
    print(renderFilePrefixReport(prefixReport, args.write))
    report = _runPhase(failures, "orphan sweep", args.db,
                       sweepOrphans, prj, write=args.write)
    if report is not None:
        print(renderOrphanReport(report, args.write))
    # Re-stamp project-mode artifacts (rtl.f) from the retired context form to
    # the --project form. Same DB-backed --sweep phase: identifying a
    # project-mode file needs the merged fileMap and layout placement.
    paramReport = _runPhase(failures, "project-mode re-stamp", args.db,
                            restampProjectParam, prj, write=args.write)
    if paramReport is not None:
        print(renderProjectParamReport(paramReport, args.write))
    # Re-stamp context-mode artifacts (module Includes, _package, firmware
    # IncludesFW) to carry both --context (canonical yamlContext key) and
    # --project (owning project). Same DB-backed phase: the owned-file set
    # and canonical keys come from INCLUDEFILES + contextOwningProject.
    contextReport = _runPhase(failures, "context-mode re-stamp", args.db,
                              restampContextParam, prj, write=args.write)
    if contextReport is not None:
        print(renderProjectParamReport(contextReport, args.write,
                                       label="context-mode"))
    # Re-stamp the user-owned `endmodule: <label>` of each RTL block module to
    # the block's SV module name (blockSvModuleName), matching the
    # generator-owned begin-label. DB-backed because the name depends on the
    # owning project's svFilePrefix.
    endlabelReport = _runPhase(failures, "module end-label re-stamp", args.db,
                               restampModuleEndlabel, prj, write=args.write)
    if endlabelReport is not None:
        print(renderModuleEndlabelReport(endlabelReport, args.write))
    # Report hand-written SV that still names a module or package by its
    # pre-refactor project-qualified name. DB-backed: both names are persisted.
    svNameReport = _runPhase(failures, "stale SV names", args.db,
                             reportStaleSvNames, prj)
    if svNameReport is not None:
        print(renderStaleSvNameReport(svNameReport))
    _printPhaseFailures(failures)
    if failures:
        return RC_PHASE_FAILED
    # A sweep that leaves manual items (ungenerated delete targets, pending
    # ports, user include sites), or a re-stamp that hit an ungenerated
    # project- or context-mode path, signals work remains, mirroring how the
    # text phases fail when manual TODOs block the stamp.
    return RC_CLEAN if (report.clean and paramReport.clean
                        and contextReport.clean
                        and endlabelReport.clean
                        and svNameReport.clean) else RC_TODO


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
    parser.add_argument("--port", action="store_true",
                        help="Run the block-module port (.h/.cpp -> .cppm) instead "
                             "of the text-conversion phases. Requires --db and opens "
                             "the database READ-ONLY; run after `make gen` so the "
                             ".cppm transplant target already carries its generated "
                             "regions.")
    parser.add_argument("--port-tb", action="store_true", dest="portTb",
                        help="Run the testbench-family port (Config.cpp region "
                             "split, External .h/.cpp -> .cppm, tb-top DUT variant "
                             "carry + legacy pair delete) instead of the "
                             "text-conversion phases. Requires --db and opens the "
                             "database READ-ONLY; run AFTER `make newmodule` and "
                             "BEFORE `make gen` - both edits have to be in place "
                             "before gen renders the files.")
    parser.add_argument("--db",
                        help="Path to the built project database (required with "
                             "--sweep, --port-tb or --port).")
    parser.add_argument("projectYaml", nargs="?",
                        help="Path to the project's project.yaml (required unless "
                             "one of the DB-backed modes above is given).")
    args = parser.parse_args(argv)

    if args.sweep:
        if not args.db:
            parser.error("--sweep requires --db")
        failures = []
        # A raise outside any phase skips the phases after it, so report it as
        # a failed phase.
        try:
            return _sweep(args, failures)
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            failures.append(PhaseFailure(
                TODO_PHASE_FAILED, args.db,
                f"the sweep raised {type(exc).__name__}: {exc} outside any "
                f"phase, so the phases after it did not run; the traceback is "
                f"on stderr. Fix the cause and re-run"))
            _printPhaseFailures(failures)
            return RC_PHASE_FAILED

    if args.portTb:
        if not args.db:
            parser.error("--port-tb requires --db")
        prj = projectOpen(args.db)
        failures = []
        # Config first: it is the only file in the family gen cannot render at all
        # until its region carries a --section, so reporting it before the External
        # port puts the blocking item at the head of the output.
        configReport = _runPhase(failures, "tbConfig restructure", args.db,
                                 restructureTbConfigs, prj, write=args.write)
        if configReport is not None:
            print(renderTbConfigReport(configReport, args.write))
        configClean = configReport is not None and configReport.clean
        # A refused Config restructure blocks the pipeline below, so the two ports
        # that follow are reported but NOT applied on such a run: their targets are
        # files the blocked `gen` will never fill, and both delete a legacy pair.
        # They still run so one invocation reports every TODO in the family.
        portWrite = args.write and configClean
        extReport = _runPhase(failures, "testbench External port", args.db,
                              portTbExternals, prj, write=portWrite)
        if extReport is not None:
            print(renderBlockPortReport(extReport, portWrite,
                                        label="testbench External port"))
        # The tb top carries no user code, only its DUT --variant= selection, so it
        # is the cheapest member of the family and runs last.
        topReport = _runPhase(failures, "testbench top port", args.db,
                              portTbTops, prj, write=portWrite)
        if topReport is not None:
            print(renderBlockPortReport(topReport, portWrite,
                                        label="testbench top port"))
        _printPhaseFailures(failures)
        # The two refusals are not equivalent. A refused Config restructure is
        # BLOCKING: the file keeps its bare `--template=tbConfig` region and the
        # next `make gen` aborts on it (templates/systemc/testbench.py raises on the
        # empty section), so the caller must stop here and act on this report. A
        # refused External port only leaves user code un-ported, which gen tolerates,
        # so it is the ordinary pending-work status.
        if not configClean:
            return RC_BLOCKED
        if failures:
            return RC_TODO
        return RC_CLEAN if (extReport.clean and topReport.clean) else RC_TODO

    if args.port:
        if not args.db:
            parser.error("--port requires --db")
        prj = projectOpen(args.db)
        failures = []
        report = _runPhase(failures, "block module port", args.db,
                           portBlockModules, prj, write=args.write)
        if report is not None:
            print(renderBlockPortReport(report, args.write,
                                        label="block module port"))
        _printPhaseFailures(failures)
        # Non-zero while any block is flagged for a hand port (parameterized,
        # reg-handler, module-hostile library, non-boilerplate slot-0), mirroring
        # how the sweep signals remaining TODO_PORT work.
        return RC_CLEAN if (report is not None and report.clean) else RC_TODO

    if not args.projectYaml:
        parser.error("projectYaml is required unless --sweep, --port-tb or --port "
                     "is given")

    if args.toHierarchical:
        report = migrateLayoutInProject(args.projectYaml, write=args.write)
        print(renderLayoutReport(report, args.write))
        # A no-op (not opted in, or already hierarchical) always succeeds. A
        # candidate blocked on a manual precondition (e.g. not yet yamlFormat: 2)
        # fails so the make target signals work remains.
        return RC_CLEAN if (report.isNoOp or report.clean) else RC_TODO

    result = migrateProject(args.projectYaml, write=args.write)
    print(renderReport(result, args.write))
    if result.phaseFailures:
        return RC_TODO

    # Dry-run and an already-migrated project always succeed. A --write run that
    # could not stamp (manual work remains) fails so `make migrate` signals the
    # project is not yet buildable.
    # A --write run succeeds when the project is format-2 clean: either it was
    # stamped this run, or it already carried the stamp and the checks that can
    # post-date the stamp left no manual work. Those are the includes and
    # module-header phases plus the composed-build check, which can start
    # reporting long after the stamp — a child project added to `projectFiles:`
    # later is un-migrated on a project that is itself already format 2.
    if args.write:
        ok = result.stamped or (result.alreadyMigrated
                                and result.includesReport.clean
                                and result.moduleHeaderReport.clean
                                and result.variantReport.clean
                                and result.langDomainReport.clean
                                and result.subProjectsReport.clean)
        if not ok:
            return RC_TODO
    return RC_CLEAN


if __name__ == "__main__":
    sys.exit(main())
