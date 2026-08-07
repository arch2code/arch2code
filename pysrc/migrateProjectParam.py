"""Re-stamp the GENERATED_CODE_PARAM line of each project-mode generated
artifact from the retired context/basename form (`--context <basename>`) to the
owning-project form (`--project <projectName>`).

A project-mode artifact (fileMap `mode: project`, e.g. the verilator file list
rtl.f) has exactly one instance per project, rooted at its segment. Its owner
was historically stamped as the top context's basename and recovered by a
basename round-trip through resolveContextKey; the current owner-resolution path
reads the projectName directly off a `--project` stamp. This phase converts an
existing artifact's create-only PARAM line so the next `gen` resolves its owner
through the direct project branch.

DB-backed, like migrateOrphans: identifying a project-mode file requires the
merged fileMap (base overlays the entry, not the per-project YAML) and the
layout-resolved placement, both of which come from a read-only projectOpen
handle. It therefore runs in the `migrateYaml.py --sweep` phase, after `make db`.

Mechanical and idempotent: a file already carrying `--project` is a no-op; a
file whose PARAM line still names a context is rewritten. The line is guarded by
the GENERATED_CODE marker (a project-mode path that is not a generated file is
left untouched). A generated artifact that carries no PARAM line at all cannot be
re-stamped and is reported as manual work, so `--sweep` signals it instead of
exiting clean. Only the PARAM line changes; the generated region content is
refilled by the following `make gen`.

The re-stamped tail is built by the same genFileParam.contextParamTail /
contextParamMode the scaffold templates use, so a re-stamped line is
byte-identical to a fresh scaffold and no per-fileType mode is spelled out here.
"""

import os
from dataclasses import dataclass, field

from pysrc.migrateCommon import (_read, _write, _isGenerated, _loc,
                                 PARAM_MARKER, restampParamLine)
from pysrc.processYaml import expandNewModulePath
from pysrc.genFileParam import contextParamTail, contextParamMode


# Applied-edit kind.
PROJECT_PARAM_RESTAMP = "PROJECT_PARAM_RESTAMP"  # --context/--contexts -> --project
CONTEXT_PARAM_RESTAMP = "CONTEXT_PARAM_RESTAMP"  # add --project + normalize --context

# Manual-TODO kinds (handed to the operator).
TODO_UNGENERATED_FILE = "TODO_UNGENERATED_FILE"  # project-mode path lacks the marker; not re-stamped
TODO_MISSING_PARAM_LINE = "TODO_MISSING_PARAM_LINE"  # generated artifact carries no PARAM line to re-stamp


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line (or file) the item refers to
    message: str     # human-facing description


@dataclass
class ProjectParamReport:
    projectName: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        """True when nothing is left for the operator to resolve by hand."""
        return not self.manual


def _projectModePaths(prj):
    """Layout-resolved on-disk paths of every project-mode artifact the current
    build owns, mirroring newModule.project_create_from_templates placement.

    A definitions-only project (no top context) owns no project-mode artifact,
    and only the project that owns the top context re-stamps its own copy, so a
    composed build never rewrites a referenced child's file.
    """
    topContext = prj.config.getConfig("TOPCONTEXT")
    if topContext is None:
        return []
    projectName = prj.config.getConfig("PROJECTNAME")
    if prj.contextOwningProject[topContext] != projectName:
        return []
    layout = prj.projectLayout[projectName]
    # Hierarchical anchors the single artifact to the top context's node dir (the
    # top block's dir); functional segments are $root-absolute (no node anchor).
    if layout["mode"] == "hierarchical":
        topBlockKey = next(row["instanceTypeKey"]
                           for row in prj.data["instances"].values()
                           if row["container"] == "_topInstance")
        nodeDir = prj.data["blocks"][topBlockKey]["dir"]
    else:
        nodeDir = ""
    paths = []
    for fileDef in prj.filemap.values():
        if fileDef.get("mode", "block") != "project":
            continue
        if fileDef["basePath"] not in layout["segments"]:
            continue
        filePath = expandNewModulePath(fileDef, nodeDir, "", "", layout,
                                       missingDirOk=True)
        for ext in fileDef["ext"]:
            paths.append(filePath + "." + fileDef["ext"][ext])
    return paths


def restampProjectParam(prj, write=False):
    """Re-stamp every project-mode artifact this project owns from the context
    form to the `--project` form. Returns a ProjectParamReport."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = ProjectParamReport(projectName=projectName)
    wrote = False
    for path in _projectModePaths(prj):
        if not os.path.exists(path):
            continue
        if not _isGenerated(path):
            report.manual.append(ReportItem(
                TODO_UNGENERATED_FILE, os.path.basename(path),
                f"project-mode path {os.path.basename(path)} has no generated "
                f"marker; left in place for manual review (not re-stamped)"))
            continue
        text = _read(path)
        hasParamLine, newText = restampParamLine(
            text, f"--project={projectName}")
        if not hasParamLine:
            report.manual.append(ReportItem(
                TODO_MISSING_PARAM_LINE, os.path.basename(path),
                f"generated project-mode file {os.path.basename(path)} has no "
                f"{PARAM_MARKER} line to re-stamp; add "
                f"`{PARAM_MARKER} --project={projectName}` by hand"))
            continue
        if newText is None:
            continue  # already --project (idempotent)
        report.applied.append(ReportItem(
            PROJECT_PARAM_RESTAMP, _loc(path, 0),
            f"re-stamped {os.path.basename(path)} GENERATED_CODE_PARAM to "
            f"--project={projectName}"))
        if write:
            _write(path, newText)
            wrote = True
    report.written = wrote
    return report


def _contextModeFiles(prj):
    """Yield (fileType, contextKey, mode, path) for every context-mode generated file
    (module Includes, VariantConfig, _package, firmware IncludesFW) this project
    OWNS. INCLUDEFILES is keyed identically to contextOwningProject, so only this
    project's own contexts are re-stamped; foreign child copies are left to their
    owning project's migration (mirrors restampProjectParam's owner guard).

    `mode` comes from genFileParam.contextParamMode, the same table the fileGen
    scaffold templates stamp from, so the re-stamp reproduces the token that file
    type's artifacts already carry and an unrecorded file type fails loud there
    rather than being re-stamped without its --mode."""
    projectName = prj.config.getConfig("PROJECTNAME")
    includeFiles = prj.config.getConfig("INCLUDEFILES")
    for fileType, contexts in includeFiles.items():
        mode = contextParamMode(fileType)
        for contextKey, entry in contexts.items():
            if prj.contextOwningProject[contextKey] != projectName:
                continue
            yield fileType, contextKey, mode, entry["fileName"]


def restampContextParam(prj, write=False):
    """Add --project and normalize --context on every context-mode artifact this
    project owns. Returns a ProjectParamReport."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = ProjectParamReport(projectName=projectName)
    wrote = False
    for fileType, contextKey, mode, path in _contextModeFiles(prj):
        if not os.path.exists(path):
            continue  # smartInclude skipped an empty context
        if not _isGenerated(path):
            report.manual.append(ReportItem(
                TODO_UNGENERATED_FILE, os.path.basename(path),
                f"context-mode path {os.path.basename(path)} has no generated "
                f"marker; left in place for manual review (not re-stamped)"))
            continue
        text = _read(path)
        # An owned file a foreign build root scaffolded carries a divergent
        # --context spelling and no --project; the canonical tail normalizes both.
        tail = contextParamTail(projectName, contextKey, mode)
        hasParamLine, newText = restampParamLine(text, tail)
        if not hasParamLine:
            report.manual.append(ReportItem(
                TODO_MISSING_PARAM_LINE, os.path.basename(path),
                f"generated context-mode file {os.path.basename(path)} has no "
                f"{PARAM_MARKER} line to re-stamp; add "
                f"`{PARAM_MARKER} {tail}` by hand"))
            continue
        if newText is None:
            continue  # already canonical --context + --project (idempotent)
        report.applied.append(ReportItem(
            CONTEXT_PARAM_RESTAMP, _loc(path, 0),
            f"re-stamped {os.path.basename(path)} GENERATED_CODE_PARAM to "
            f"--project={projectName} --context={contextKey}"))
        if write:
            _write(path, newText)
            wrote = True
    report.written = wrote
    return report


def renderReport(report, write, label="project-mode"):
    """Render a re-stamp report as text. label names which artifact class the
    report covers (project-mode rtl.f vs context-mode include/config/package/fw)."""
    lines = [f"=== {label} param re-stamp: {report.projectName} ==="]
    if not report.applied and not report.manual:
        lines.append(f"  no {label} artifact to re-stamp; nothing to do")
        return "\n".join(lines)
    if report.applied:
        verb = "re-stamped" if write else "would re-stamp (dry-run)"
        lines.append(f"  {verb}:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO:")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    return "\n".join(lines)
