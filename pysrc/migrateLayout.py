"""Functional -> hierarchical layout migration (the opt-in layout phase of the
project layout work).

Unlike the eval / address / includes phases, this is NOT part of yamlFormat: 2
and does not run on every `make migrate`. It is opt-in per project: a
project stays valid in functional layout forever, and this phase runs only when
the project has chosen hierarchical (`fileGeneration.layout: hierarchical`) but
its tree is still laid out functionally. It presupposes the project is already
yamlFormat: 2 and is invoked separately (`migrateYaml.py
--to-hierarchical` / `make migrate-hierarchical`), after the unconditional
phases, because it MOVES files where the other phases edit content in place.

Standalone and text-only, like `migrateIncludes`: it reads YAML as text and
never opens the project database. PyYAML supplies values.

This module covers the trigger + idempotence, the relocation map, applying that
map, and the relative-path re-rooting. It classifies
the project into one of three layout states and, for an unblocked candidate,
computes the source->dest move map plus the generated-source delete set. Files
are classified by the merged fileMap (the same base/pro/user merge processYaml
runs at create, via `mergeProjectConfig`): a recognized fully-generated file type
is deleted and recreated by make gen/newmodule, while every other source —
user-editable, or an unrecognized/custom fileMap type — MOVES byte-preserving so
its user content is never lost. Under `write=True` it executes the map (delete +
relocate + prune) and then re-roots the relative `include:` / `projectFiles:` /
user-region include references through the new `yaml/` levels; a reference that
cannot be re-rooted mechanically is reported for manual fixup, never mangled.

The layout flip (`fileGeneration.layout: hierarchical`) is NOT an edit this
migration makes: it is the opt-in precondition itself. `migrateLayoutInProject` only
reaches the relocation map when the project already declares hierarchical, so
there is nothing to flip.

The relocation transform:
  - Authored YAML `<yamlRoot>/<decomp>/*.yaml` -> `<root>/<decomp>/<yaml>/*.yaml`
    (decomp="" -> `<root>/<yaml>/*.yaml`; the functional central yaml root is the
    project file's own directory).
  - Project file -> `prj/yaml/<projectName>Project.yaml`; project-scope
    integration orphans (fwIpMain, sc_main, the vl_wrap aggregator) -> `prj/fw/`
    / `prj/verif/` (flattened). Build-config `include/` and `rundir/` stay at the
    project root as user-owned entry points; they do NOT move into
    prj/. The only harness edit is re-pointing the `A2C_PRJ_YAML` line in the
    root `include/make/shared.mk` at the moved project file.
  - The layout flip to hierarchical is the opt-in precondition itself
    (`fileGeneration.layout: hierarchical` is already declared in a candidate),
    so there is no flip edit to make here.
  - Generated functional source under the project's own declared `dirs:`
    functional segments is deleted (recreated later by `make newmodule`/`make
    gen`), marker-guarded by GENERATED_CODE_BEGIN: a name-matched source file
    lacking the marker is reported for manual review, never deleted. Orphans move
    (never deleted) even when generated, because they carry project-level user
    content or are the single project-wide aggregator.

States:
  - LAYOUT_FUNCTIONAL          declared layout is not hierarchical: not opted in,
                               a no-op.
  - LAYOUT_ALREADY_HIERARCHICAL declared hierarchical and the tree is already
                               hierarchical (project file under <prj>/<yaml>/): a
                               no-op (idempotent).
  - LAYOUT_NEEDS_MIGRATION     declared hierarchical and the tree is still
                               functional: relocation would run. Blocked
                               when the project is not yet yamlFormat: 2.
"""

import os
import re
import shutil
from collections import defaultdict
from dataclasses import dataclass, field

import yaml

from pysrc.migrateCommon import (
    _read, _write, _loc, _isGenerated, _projectFileSet, classifyGeneratedDir,
    SKIP_DIRS, SOURCE_EXTS,
)
from pysrc.processYaml import mergeProjectConfig


# Layout states.
LAYOUT_FUNCTIONAL = "LAYOUT_FUNCTIONAL"
LAYOUT_ALREADY_HIERARCHICAL = "LAYOUT_ALREADY_HIERARCHICAL"
LAYOUT_NEEDS_MIGRATION = "LAYOUT_NEEDS_MIGRATION"

# Manual-TODO kinds (delegated to the migration skill / user).
TODO_NOT_FORMAT2 = "TODO_NOT_FORMAT2"  # hierarchical opt-in before yamlFormat: 2
TODO_UNGENERATED_FILE = "TODO_UNGENERATED_FILE"  # source under a functional dir lacks the generated marker
TODO_UNREWRITABLE_PATH = "TODO_UNREWRITABLE_PATH"  # relative include/projectFiles path can't be re-rooted mechanically

# Move kinds (relocation-map rows).
MOVE_AUTHORED_YAML = "AUTHORED_YAML"   # a block/include YAML file
MOVE_PROJECT_FILE = "PROJECT_FILE"     # the project.yaml itself
MOVE_ORPHAN = "ORPHAN"                 # a project-scope integration file (no block YAML)
MOVE_SOURCE = "SOURCE"                 # user-editable generated source (carries user regions): preserved, not deleted

# fileMap keys whose generated files are FULLY generated (no user regions worth
# preserving): the migration deletes them and lets `make gen`/`make newmodule`
# recreate them at the hierarchical location. This is a migrate-side maintenance
# classification, deliberately keyed on the base-config fileMap key names
# (config/project.yaml). A project's own or custom fileMap key NOT listed here is
# treated as user-editable and its files MOVE (content preserved) rather than
# delete — the safe default for content the migrator does not recognize.
# tandem, blockVlRegistrar, foreignConfig and vlSvWrapForeign are the
# verilated/foreign siblings of already-listed generated keys (blockBase,
# blockRegistrar, config, vlSvWrap): each is a single whole-file generated block
# with no user regions, emitted into an all-generated segment (base, registrar,
# vl_wrap). Listing them makes those segments classify fully-generated so the
# migration clears them by directory (below).
FULLY_GENERATED_FILEMAP_KEYS = frozenset({
    "blockBase", "blockRegistrar", "include", "config", "package",
    "vlSvWrap", "vlSvWrapBody", "vlScWrap",
    "tandem", "blockVlRegistrar", "foreignConfig", "vlSvWrapForeign",
})

# Relative include references rewritten inside moved source user regions:
# C/C++/module `#include "rel"` and SystemVerilog `` `include "rel" ``. Only the
# quoted (local) relative form is a candidate; <...> and absolute paths are left.
_SOURCE_INCLUDE_RE = re.compile(r'^\s*(?:#\s*include|`include)\s*"([^"]+)"')

# Project-scope integration files (orphans) with no block YAML. They MOVE into
# the prj/ container (flattened: verif/vl_wrap -> verif) instead of being deleted
# and regenerated, because sc_main carries project-level user content and vl_wrap
# is the single project-wide aggregator. Keyed by the file's role basename ->
# prj/ subsegment. These verif basenames are framework-general (base config /
# shared tooling), so they stay literal. Firmware entry sources are NOT listed
# here: their basename is project-defined, so they are routed data-drivenly by
# the firmware-segment rule below (see FW_HIER_SEGMENT).
ORPHAN_DESTS = {
    "sc_main.cpp": "verif",
    "vl_wrap.cpp": "verif", "vl_wrap.h": "verif", "vl_wrap.sv": "verif",
    "vl_dummy.sv": "verif",
}

# Base-config hierarchical firmware subsegment (hierarchicalDirs maps the
# firmware functional segment `fwInc` -> "fw"; a project-declared `$root/fw`
# segment defaults to the same "fw" basename). A user-owned (non-generated,
# non-block) source under a functional segment that maps to this hierarchical
# name is a project-scope firmware orphan routed to prj/fw, regardless of its
# basename — so any project's firmware entry file relocates, not just fwIpMain.
FW_HIER_SEGMENT = "fw"

# Project-root build-config container (holds make/shared.mk etc). Not a fileMap
# segment; a user-owned root convention that STAYS at the project root. It is not
# relocated; the migration only re-points the A2C_PRJ_YAML line in the harness
# makefile below, because the project file moves to prj/yaml/.
BUILD_CONFIG_DIR = "include"

# The user-owned project build harness (root-relative) whose A2C_PRJ_YAML sets
# the DB-build input path. It stays at the project root; only its A2C_PRJ_YAML
# line is re-pointed at the moved project file.
HARNESS_MK = os.path.join(BUILD_CONFIG_DIR, "make", "shared.mk")

# Existing `A2C_PRJ_YAML [:?]?= ...` assignment (replaced in place when present),
# and the first makefile `include`/`-include` line (the new line is inserted
# before it so it wins over a2c-common.mk's `?=` default on the first build).
_A2C_PRJ_YAML_RE = re.compile(r'^[ \t]*A2C_PRJ_YAML[ \t]*[:?]?=.*$', re.M)
_MK_INCLUDE_RE = re.compile(r'^[ \t]*-?include[ \t]', re.M)

# Root-relative user-owned build makefile (stays at the project root) that can
# carry EXTRA_* make-variable references to relocatable segment roots.
RUNDIR_MK = os.path.join("rundir", "Makefile")

# An EXTRA_* make-variable assignment, and a `$(REPO_ROOT)/<top>` path reference
# within it. <top> is the first path component under the repo root — the
# functional segment (model, rtl, fw, verif, ...) the layout migration relocates.
# Matched against one backslash-folded LOGICAL line (see _foldedLines), so a
# continued list is scanned whole; a line-anchored match would see only the first
# physical line and silently miss every path on the continuations.
_EXTRA_VAR_RE = re.compile(r'^[ \t]*(EXTRA_\w+)[ \t]*[:+?]?=(?P<rhs>.*)$')
_REPO_ROOT_REF_RE = re.compile(r'\$\(REPO_ROOT\)/(?P<top>[^\s/):]+)')

# The yamlFormat value the layout migration presupposes. Kept local so
# this module stays text-only and never imports processYaml (which opens the DB
# path); migrateYaml passes the authoritative CURRENT_YAML_FORMAT through the
# report check.
REQUIRED_YAML_FORMAT = 2

# Default project-scope segment names (base config fileGeneration.hierarchicalDirs:
# prj is "$root/prj" -> basename "prj"; yaml is the authored-YAML subdir). A user
# project file that overrides hierarchicalDirs is honored; one that inherits the
# base defaults (the common case) falls back to these.
DEFAULT_PRJ_SEGMENT = "prj"
DEFAULT_YAML_SEGMENT = "yaml"


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line (or file) of the offending declaration
    message: str     # human-facing description


@dataclass(frozen=True)
class Move:
    src: str         # absolute source path
    dst: str         # absolute destination path
    kind: str        # one of the MOVE_* constants


@dataclass(frozen=True)
class HarnessEdit:
    path: str        # absolute path of the harness makefile to edit
    old: str         # existing A2C_PRJ_YAML line replaced, or "" when inserted
    new: str         # the A2C_PRJ_YAML line written


@dataclass(frozen=True)
class Rewrite:
    path: str        # absolute path of the relocated file to edit
    start: int       # char offset of the reference value to replace
    end: int         # char offset just past it (exclusive)
    old: str         # current reference value (splice guard)
    new: str         # re-rooted reference value
    kind: str        # 'include' | 'projectFiles' | 'source'


@dataclass
class LayoutReport:
    projectYaml: str
    state: str                                      # one of the LAYOUT_* constants
    declaredLayout: str                             # 'functional' | 'hierarchical'
    applied: list = field(default_factory=list)     # list[ReportItem]
    manual: list = field(default_factory=list)      # list[ReportItem]
    moves: list = field(default_factory=list)       # list[Move]
    deletes: list = field(default_factory=list)     # list[str] (abs paths of generated files)
    rewrites: list = field(default_factory=list)    # list[Rewrite] (relative-path re-rooting)
    harnessEdits: list = field(default_factory=list) # list[HarnessEdit] (A2C_PRJ_YAML re-point)
    relocatableRoots: set = field(default_factory=set) # top-level dir names of the functional segments the migration relocates
    projectRoot: str = ""                           # abs dirs.root (map anchor; "" until computed)
    written: bool = False

    @property
    def isNoOp(self):
        """True when the project needs no layout migration: not opted in, or
        already hierarchical on disk."""
        return self.state in (LAYOUT_FUNCTIONAL, LAYOUT_ALREADY_HIERARCHICAL)

    @property
    def clean(self):
        """True when nothing is left for the user to resolve by hand."""
        return not self.manual


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def migrateLayoutInProject(projectYamlPath, write=False):
    """Classify one project's layout-migration state and return a LayoutReport.

    Idempotent: a project that has not opted in (declared layout is not
    hierarchical) and a project already laid out hierarchically are both no-ops.
    Only a project that has declared `fileGeneration.layout: hierarchical` while
    its tree is still functional is a migration candidate.

    For an unblocked candidate the source->dest map is computed; under
    `write=True` it is applied to disk. A no-op or blocked project writes
    nothing regardless of `write`.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectData = yaml.safe_load(_read(projectYamlPath)) or {}

    declared = _declaredLayout(projectData)
    if declared != "hierarchical":
        return LayoutReport(projectYaml=projectYamlPath,
                            state=LAYOUT_FUNCTIONAL, declaredLayout=declared)

    if _onDiskLayout(projectYamlPath, projectData) == "hierarchical":
        return LayoutReport(projectYaml=projectYamlPath,
                            state=LAYOUT_ALREADY_HIERARCHICAL,
                            declaredLayout=declared)

    report = LayoutReport(projectYaml=projectYamlPath,
                          state=LAYOUT_NEEDS_MIGRATION, declaredLayout=declared)

    # Precondition: relocation presupposes the unconditional phases have
    # run and stamped yamlFormat: 2. A project that opts into hierarchical before
    # being format-2 clean must run `make migrate` first; report it rather than
    # relocate a half-migrated tree.
    if projectData.get("yamlFormat") != REQUIRED_YAML_FORMAT:
        report.manual.append(ReportItem(
            TODO_NOT_FORMAT2, _loc(projectYamlPath, 0),
            f"layout: hierarchical declared but project is not yamlFormat: "
            f"{REQUIRED_YAML_FORMAT}; run `make migrate` first, then "
            f"`make migrate-hierarchical`"))
        return report

    # Compute the relocation map for the unblocked candidate.
    _buildRelocationMap(projectYamlPath, projectData, report)

    # Plan the relative-path re-rooting from the pre-move (src) files. The
    # moves preserve bytes, so offsets computed here stay valid against the
    # relocated copies; references that cannot be mechanically re-rooted are
    # reported (never mangled). Planning reads src, so it must run before apply.
    _planPathRewrites(report)

    # Plan the single A2C_PRJ_YAML re-point into the root build harness (which
    # stays at root), derived from the project-file move.
    _planHarnessEdit(report)

    # Warn on EXTRA_* make-variable references to relocatable segment roots in the
    # root-relative build makefiles; these cannot be rewritten mechanically.
    _planExtraPathWarnings(report)

    # Under --write, execute the map then apply the rewrites and the
    # harness re-point. The layout flip is a no-op (reaching here means
    # hierarchical is already declared), so the apply is the moves + deletes +
    # emptied-dir prune, then the planned path rewrites on the relocated files,
    # then the A2C_PRJ_YAML re-point. A candidate with only a
    # TODO_UNGENERATED_FILE / TODO_UNREWRITABLE_PATH manual item still applies its
    # safe moves/deletes/rewrites; the flagged item is left for review.
    if write:
        _applyRelocationMap(report)
        _applyPathRewrites(report)
        _applyHarnessEdits(report)
        report.written = True
    return report


# ---------------------------------------------------------------------------
# Relocation map (computed, never applied)
# ---------------------------------------------------------------------------

def _buildRelocationMap(projectYamlPath, projectData, report):
    """Fill `report.moves` / `report.deletes` / `report.manual` for an unblocked
    functional->hierarchical candidate. Text-only: resolves paths from the
    project file's own `dirs:` and its `projectFiles:`/`include:` closure, never
    opening the database. Writes nothing."""
    projectDir = os.path.dirname(projectYamlPath)
    dirs = projectData.get("dirs") or {}
    projectRoot = os.path.abspath(os.path.join(projectDir, dirs["root"]))
    prjSeg, yamlSeg = _prjYamlSegments(projectData)
    prjDir = os.path.join(projectRoot, prjSeg)
    report.projectRoot = projectRoot

    # 1. Authored YAML. The functional central yaml root is the project file's own
    # directory; each file's decomposition is its dir relative to that root, and
    # it lands in that node's yaml/ subdir under the project root.
    yamlRoot = projectDir
    nodes = set()  # decomposition nodes, derived from authored-YAML locations
    for src in _projectFileSet(projectDir, projectData):
        absSrc = os.path.abspath(src)
        if not (absSrc == projectRoot or absSrc.startswith(projectRoot + os.sep)):
            # An authored YAML resolved (through a projectFiles/include chain)
            # outside the project root has no place in the hierarchical tree and
            # cannot be relocated mechanically; report it rather than mangle a
            # move to a phantom node.
            report.manual.append(ReportItem(
                TODO_UNREWRITABLE_PATH, _loc(src, 0),
                f"authored YAML {os.path.basename(src)} resolves outside the "
                f"project root; cannot relocate into the hierarchical tree, "
                f"fix by hand"))
            continue
        decomp = os.path.relpath(os.path.dirname(src), yamlRoot)
        if decomp == ".":
            decomp = ""
        nodes.add(decomp)
        dst = os.path.join(projectRoot, decomp, yamlSeg, os.path.basename(src))
        report.moves.append(Move(src, dst, MOVE_AUTHORED_YAML))

    # 2a. Project file -> prj/yaml/<projectName>Project.yaml.
    projDst = os.path.join(prjDir, yamlSeg,
                           f"{projectData['projectName']}Project.yaml")
    report.moves.append(Move(projectYamlPath, projDst, MOVE_PROJECT_FILE))

    # 2b. Build-config include/ stays at the project root: it is a
    # user-owned entry point, not a prj/ orphan, so nothing under it moves. The
    # only harness change is re-pointing its A2C_PRJ_YAML line (planned separately
    # by _planHarnessEdit, since the project file moves to prj/yaml/).

    # 2c + 4. Sweep the merged functional segments (the same base/pro/user merge
    # processYaml runs at create). A FULLY-GENERATED segment (every fileMap entry
    # whole-file generated: base, registrar, vl_wrap) is cleared by DIRECTORY —
    # every marker-carrying file deleted, so alternate-extension / renamed orphans
    # a per-file name+ext match would miss go too. A MIXED/user segment (model,
    # rtl, tb, fwInc) is classified per file: project-scope orphans move into prj/;
    # its recognized generated files (include/package) are deleted (marker-guarded)
    # and recreated by make gen/newmodule; a name-matched file lacking the marker
    # is reported, never deleted; every other (user-editable / unrecognized) source
    # MOVES byte-preserving to its hierarchical <decomp>/<segment> location, content
    # preserved for the re-root pass. Both paths are recreated by the hierarchical
    # newmodule/gen at the node dirs.
    _, _, _, _, mergedProj = mergeProjectConfig(projectYamlPath)
    fileGen = mergedProj["fileGeneration"]
    fileMap = fileGen["fileMap"]
    hdirs = fileGen.get("hierarchicalDirs") or {}
    mergedDirs = mergedProj.get("dirs") or {}
    fullyGenerated = _fullyGeneratedSegments(fileMap)
    for segKey, segDir in _functionalSegments(projectRoot, mergedDirs):
        # Every functional segment relocates under hierarchical layout (its root is
        # no longer a valid $(REPO_ROOT)-relative top-level path), so record its
        # top-level project-root component for the EXTRA_* reference warning.
        top = _topSegment(segDir, projectRoot)
        if top is not None:
            report.relocatableRoots.add(top)
        hierName = hdirs.get(segKey, os.path.basename(segDir))
        if segKey in fullyGenerated:
            # Directory-level clear. A project-scope orphan (sc_main.cpp,
            # vl_dummy.sv, the retired vl_wrap.* aggregator) MOVES to prj/
            # regardless of its marker — ORPHAN_DESTS wins first. A remaining
            # marker file is deleted (recreated at the node dir by newmodule/gen);
            # a remaining non-marker file is user content wearing a generated name,
            # reported and left in place (never deleted, never moved).
            generated, ungenerated = classifyGeneratedDir({segDir})
            for src in generated:
                base = os.path.basename(src)
                if base in ORPHAN_DESTS:
                    report.moves.append(Move(
                        src, os.path.join(prjDir, ORPHAN_DESTS[base], base),
                        MOVE_ORPHAN))
                else:
                    report.deletes.append(src)
            for src in ungenerated:
                base = os.path.basename(src)
                if base in ORPHAN_DESTS:
                    report.moves.append(Move(
                        src, os.path.join(prjDir, ORPHAN_DESTS[base], base),
                        MOVE_ORPHAN))
                else:
                    report.manual.append(ReportItem(
                        TODO_UNGENERATED_FILE, _loc(src, 0),
                        f"non-marker file {base} in fully-generated segment "
                        f"'{segKey}'; left in place for manual review (not "
                        f"deleted, not moved)"))
            continue
        genEntries = [fileMap[k] for k in FULLY_GENERATED_FILEMAP_KEYS
                      if k in fileMap and fileMap[k]["basePath"] == segKey]
        # The verilator whole-design build dir is make infrastructure
        # (rundir/build/vl, driven by a2c-vl-build-entry.mk), not a relocated
        # per-example file, so the source sweep is all that runs here; the
        # buildGroup 'vl' segment holds only node-scoped wrapper sources.
        for src in sorted(_sourceFiles(segDir)):
            base = os.path.basename(src)
            if base in ORPHAN_DESTS:
                dst = os.path.join(prjDir, ORPHAN_DESTS[base], base)
                report.moves.append(Move(src, dst, MOVE_ORPHAN))
            elif _matchesFullyGenerated(base, genEntries):
                if _isGenerated(src):
                    report.deletes.append(src)
                else:
                    report.manual.append(ReportItem(
                        TODO_UNGENERATED_FILE, _loc(src, 0),
                        f"name-matched {base} under functional dir has no generated "
                        f"marker; left in place for manual review (not deleted)"))
            elif hierName == FW_HIER_SEGMENT and not _isGenerated(src):
                # User-owned firmware source under the firmware segment: a
                # project-scope orphan (hand-authored entry file, no block YAML)
                # moved into prj/fw (flattened), never deleted.
                dst = os.path.join(prjDir, hierName, base)
                report.moves.append(Move(src, dst, MOVE_ORPHAN))
            else:
                # The node is the authored-YAML decomposition, not the raw
                # source subdir: a blockDir segment (e.g. tb/<block>/) adds a
                # block level below the node, so match the longest directory
                # prefix that is a known decomposition node and keep the rest
                # (block subdir + filename) as the tail. Functional
                # <seg>/<node>/<tail> maps to hierarchical <node>/<hierName>/<tail>.
                relDir = os.path.relpath(os.path.dirname(src), segDir)
                node = _decompPrefix("" if relDir == "." else relDir, nodes)
                tail = os.path.relpath(src, os.path.join(segDir, node))
                dst = os.path.join(projectRoot, node, hierName, tail)
                # A root-node source file already sits at its hierarchical
                # location; only append a real relocation.
                if os.path.abspath(dst) != os.path.abspath(src):
                    report.moves.append(Move(src, dst, MOVE_SOURCE))


# ---------------------------------------------------------------------------
# Relocation apply (execute the computed map under --write)
# ---------------------------------------------------------------------------

def _applyRelocationMap(report):
    """Execute the map `_buildRelocationMap` computed: delete the generated
    functional source, relocate every user-content file (byte-preserving), then
    prune the emptied source directories. Reuses the map exactly; recomputes
    nothing. Called only for an unblocked candidate under `write=True`."""
    for path in report.deletes:
        os.remove(path)
    for mv in report.moves:
        _applyMove(mv)
    _pruneEmptyDirs(report)


def _applyMove(mv):
    """Relocate one file, creating destination parents and preserving content
    exactly. Refuses to overwrite: a pre-existing destination means the tree is
    not the clean functional shape this migration assumes, so it is an error to
    surface rather than silent data loss."""
    if os.path.lexists(mv.dst):
        raise RuntimeError(
            f"layout migration: destination already exists, refusing to "
            f"overwrite {mv.dst} (moving {mv.src})")
    os.makedirs(os.path.dirname(mv.dst), exist_ok=True)
    shutil.move(mv.src, mv.dst)


def _pruneEmptyDirs(report):
    """Remove source directories left empty by the moves/deletes, walking upward
    toward (but never removing) the project root. Only-if-empty: a directory that
    still holds a user or unguarded file (e.g. a name-matched source left for
    manual review, or non-source scaffolding) is kept."""
    vacated = {os.path.dirname(mv.src) for mv in report.moves}
    vacated |= {os.path.dirname(p) for p in report.deletes}
    for d in vacated:
        _pruneUp(d, report.projectRoot)


def _pruneUp(start, root):
    """Remove `start` if empty, then its parents, stopping at the first non-empty
    (or missing) directory or when reaching the project root (never removed)."""
    root = os.path.abspath(root)
    cur = os.path.abspath(start)
    while cur != root and cur.startswith(root + os.sep):
        if os.path.isdir(cur) and not os.listdir(cur):
            os.rmdir(cur)
            cur = os.path.dirname(cur)
        else:
            break


def _functionalSegments(projectRoot, dirs):
    """`(segmentKey, absDir)` for every merged `dirs:` entry except `root` whose
    functional directory exists on disk. These are the decomposition subtrees
    swept for generated source; the key ties each file back to its fileMap
    `basePath` for classification. `$root` is expanded the same way
    `migrateIncludes._resolveDir` does."""
    out = []
    for key, spec in dirs.items():
        if key == "root":
            continue
        segDir = os.path.abspath(spec.replace("$root", projectRoot))
        if os.path.isdir(segDir):
            out.append((key, segDir))
    return out


def _fullyGeneratedSegments(fileMap):
    """Segments (`basePath`) whose EVERY fileMap entry is a FULLY_GENERATED_-
    FILEMAP_KEYS key and that carry at least one entry — the segment holds only
    whole-file generated artifacts, so the migration clears it by directory rather
    than classifying per file. A segment with any non-fully-generated entry
    (`model`'s block, `rtl`'s rtlModule/rtlDotF, `tb`'s testbench, a custom key)
    is MIXED/user and stays on the per-file path. Against the current merged
    fileMap this resolves to {base, registrar, vl_wrap}."""
    bySegment = dict()
    for key, fileDef in fileMap.items():
        bySegment.setdefault(fileDef["basePath"], []).append(
            key in FULLY_GENERATED_FILEMAP_KEYS)
    return {segment for segment, flags in bySegment.items()
            if flags and all(flags)}


def _matchesFullyGenerated(base, genEntries):
    """True when `base` matches a recognized fully-generated fileMap entry's
    `name` suffix + extension. Every recognized fully-generated entry carries a
    non-empty `name` (Base, Registrar, Includes, VariantConfig, _package,
    _hdl_sv_wrapper, _hdl_sc_wrapper), so no entry matches every file."""
    for entry in genEntries:
        name = entry["name"]
        for ext in entry["ext"].values():
            if base.endswith(f"{name}.{ext}"):
                return True
    return False


def _decompPrefix(relDir, nodes):
    """The longest leading directory prefix of `relDir` that is a known
    decomposition node (`nodes` always contains "" for the root node). Used to
    separate a source file's decomposition node from any block-dir subdir a
    blockDir segment appends below it."""
    parts = relDir.split(os.sep) if relDir else []
    for i in range(len(parts), -1, -1):
        cand = os.sep.join(parts[:i])
        if cand in nodes:
            return cand
    return ""


def _sourceFiles(rootDir):
    """Generated-source candidate files under `rootDir`, excluding build trees."""
    for dirpath, dirnames, filenames in os.walk(rootDir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(SOURCE_EXTS):
                continue
            path = os.path.join(dirpath, fn)
            # os.walk lists directory entries by name; a dangling symlink is one
            # such entry with no readable target, so skip anything not a real file.
            if os.path.isfile(path):
                yield path


# ---------------------------------------------------------------------------
# Relative-path rewrite (re-root references through the new yaml/ levels)
# ---------------------------------------------------------------------------

def _planPathRewrites(report):
    """Plan the relative-path re-rooting from the pre-move files, using the
    relocation map to find where each reference target moved. Records byte-offset
    edits in `report.rewrites` (applied later to the relocated copies, whose bytes
    the moves preserve) and reports references that cannot be mechanically
    re-rooted in `report.manual` (never mangled).

    Scope: `include:` directives in every moved authored YAML, `projectFiles:`
    entries in the moved project file, and relative includes inside the user
    regions of moved source. A reference whose target did not move and whose
    includer did not move needs no edit and is skipped."""
    root = report.projectRoot
    moveIndex = {os.path.abspath(mv.src): os.path.abspath(mv.dst)
                 for mv in report.moves}
    for mv in report.moves:
        srcDir = os.path.dirname(mv.src)
        dstDir = os.path.dirname(mv.dst)
        if mv.kind == MOVE_AUTHORED_YAML:
            _planYamlListRewrite(mv, "include", srcDir, dstDir, moveIndex, root, report)
        elif mv.kind == MOVE_PROJECT_FILE:
            _planYamlListRewrite(mv, "projectFiles", srcDir, dstDir, moveIndex, root, report)
            _planDirsStrip(mv, report)
        elif mv.kind in (MOVE_SOURCE, MOVE_ORPHAN):
            _planSourceRewrite(mv, srcDir, dstDir, moveIndex, root, report)


def _planYamlListRewrite(mv, listKey, srcDir, dstDir, moveIndex, root, report):
    """Re-root the relative entries of a top-level YAML sequence (`include:` or
    `projectFiles:`). Byte offsets come from `yaml.compose`, so only the scalar
    value is spliced and comments/quoting are preserved. `$macro` and absolute
    entries are left alone; an entry that cannot be re-rooted is reported."""
    text = _read(mv.src)
    for item in _topSequenceItems(yaml.compose(text), listKey):
        refVal = item.value
        if refVal.startswith("$") or os.path.isabs(refVal):
            continue
        newRel, ok = _reRoot(refVal, srcDir, dstDir, moveIndex, root)
        if not ok:
            report.manual.append(ReportItem(
                TODO_UNREWRITABLE_PATH, _loc(mv.src, item.start_mark.line + 1),
                f"{listKey} entry '{refVal}' resolves outside the migrated tree "
                f"and cannot be re-rooted mechanically; fix by hand"))
            continue
        if newRel != refVal:
            start, end, oldText = _scalarValueSpan(text, item)
            report.rewrites.append(Rewrite(
                mv.dst, start, end, oldText, newRel, listKey))


def _planSourceRewrite(mv, srcDir, dstDir, moveIndex, root, report):
    """Re-root relative quoted includes inside the user regions of a moved source
    file. Source includes routinely name headers reached via build include paths
    rather than relative to the file, so a reference whose target is not in the
    relocation map is left unchanged (not reported) — only a relative include
    whose target actually moved is rewritten. Generated regions are skipped; make
    gen refreshes their includes in place."""
    text = _read(mv.src)
    lineOffsets = _lineStartOffsets(text)
    for lineIdx, line in _userRegionLines(text):
        m = _SOURCE_INCLUDE_RE.match(line)
        if not m:
            continue
        refVal = m.group(1)
        if refVal.startswith("$") or os.path.isabs(refVal):
            continue
        newRel, ok = _reRoot(refVal, srcDir, dstDir, moveIndex, root)
        if not ok or newRel == refVal:
            continue
        start = lineOffsets[lineIdx] + m.start(1)
        report.rewrites.append(Rewrite(
            mv.dst, start, start + len(refVal), refVal, newRel, "source"))


def _reRoot(refVal, includerSrcDir, includerDstDir, moveIndex, root):
    """Recompute a relative reference after relocation. Returns `(newRel, ok)`:
    `newRel` is the reference relative to the includer's new directory (equal to
    `refVal` when nothing changed); `ok` is False when the reference cannot be
    mechanically re-rooted (its target moved outside — or already lives outside —
    the migrated project tree)."""
    targetOld = os.path.normpath(os.path.join(includerSrcDir, refVal))
    targetNew = moveIndex.get(targetOld)
    if targetNew is None:
        if not os.path.exists(targetOld):
            return None, False
        targetNew = targetOld  # target stayed in place
    if not (targetNew == root or targetNew.startswith(root + os.sep)):
        return None, False
    return os.path.relpath(targetNew, includerDstDir), True


def _topSequenceItems(root, key):
    """Scalar item nodes of a top-level `key:` sequence, or [] when absent."""
    if not isinstance(root, yaml.MappingNode):
        return []
    for keyNode, valNode in root.value:
        if keyNode.value == key and isinstance(valNode, yaml.SequenceNode):
            return valNode.value
    return []


def _topMappingItems(root, key):
    """(keyNode, valNode) pairs of a top-level `key:` mapping, or [] when absent."""
    if not isinstance(root, yaml.MappingNode):
        return []
    for keyNode, valNode in root.value:
        if keyNode.value == key and isinstance(valNode, yaml.MappingNode):
            return valNode.value
    return []


def _entryLineSpan(text, keyNode, valNode):
    """Full-line char span `[lineStart, nextLineStart)` of a single-line mapping
    entry, including leading indentation and any trailing end-of-line comment. The
    project `dirs:` entries are always single-line (`key: $root/seg  # comment`)."""
    start = text.rfind("\n", 0, keyNode.start_mark.index) + 1
    end = text.find("\n", valNode.end_mark.index)
    return (start, len(text)) if end == -1 else (start, end + 1)


def _planDirsStrip(mv, report):
    """Reduce the project file's `dirs:` mapping to `root:` only on the
    functional->hierarchical flip. Node-relative artifact placement is then
    governed by the base-config `hierarchicalDirs:`; a project-declared functional
    segment map (base/model/rtl/vl_wrap/tb/fwInc, plus any custom override) is
    redundant with the base defaults, and its multi-level functional tails
    (verif/vl_wrap, fw/include) fight the hierarchical layout. Every non-root entry
    is deleted line-for-line via the same byte-offset splice the include/
    projectFiles re-rooting uses, so `root:` and its comment are preserved
    verbatim; offsets computed on mv.src stay valid against the byte-identical
    relocated mv.dst."""
    text = _read(mv.src)
    for keyNode, valNode in _topMappingItems(yaml.compose(text), "dirs"):
        if keyNode.value == "root":
            continue
        start, end = _entryLineSpan(text, keyNode, valNode)
        report.rewrites.append(Rewrite(mv.dst, start, end, text[start:end], "", "dirsStrip"))


def _scalarValueSpan(text, item):
    """Return the source span containing only a YAML scalar's value text.

    PyYAML's scalar marks include surrounding quotes for quoted scalars. Splicing
    inside those delimiters preserves the user's quoting style and keeps the
    rewrite guard aligned with the text being replaced.
    """
    start = item.start_mark.index
    end = item.end_mark.index
    raw = text[start:end]
    if item.style in ("'", '"') and raw.startswith(item.style) and raw.endswith(item.style):
        return start + 1, end - 1, raw[1:-1]
    return start, end, raw


def _userRegionLines(text):
    """Yield `(lineIndex, lineText)` for every line OUTSIDE a generated region,
    tracking the GENERATED_CODE_BEGIN/END marker contract (the marker lines
    themselves are not yielded). Generated regions are excluded so their includes
    are never hand-edited; make gen refreshes them."""
    inGen = False
    for i, line in enumerate(text.splitlines()):
        if "GENERATED_CODE_BEGIN" in line:
            inGen = True
            continue
        if "GENERATED_CODE_END" in line:
            inGen = False
            continue
        if not inGen:
            yield i, line


def _lineStartOffsets(text):
    """Absolute char offset of the start of each line, index-aligned with
    `text.splitlines()`."""
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _applyPathRewrites(report):
    """Apply the planned rewrites to the relocated files. Edits are grouped per
    file and spliced back-to-front so earlier offsets stay valid; a splice guard
    verifies each offset still holds the expected value (it must, since the moves
    preserve bytes)."""
    byPath = defaultdict(list)
    for rw in report.rewrites:
        byPath[rw.path].append(rw)
    for path, rws in byPath.items():
        text = _read(path)
        for rw in sorted(rws, key=lambda r: r.start, reverse=True):
            if text[rw.start:rw.end] != rw.old:
                raise RuntimeError(
                    f"layout migration: rewrite offset drift in {path} "
                    f"(expected {rw.old!r}, found {text[rw.start:rw.end]!r})")
            text = text[:rw.start] + rw.new + text[rw.end:]
        _write(path, text)


# ---------------------------------------------------------------------------
# Build harness re-point (A2C_PRJ_YAML follows the project file)
# ---------------------------------------------------------------------------

def _planHarnessEdit(report):
    """Plan the single A2C_PRJ_YAML re-point into the root build harness.

    The project file moves to `prj/yaml/`, but the harness (`include/make/
    shared.mk`) stays at the project root, so the DB-build input
    path it hands `arch2code.py` must be updated. The new value is derived from
    the project-file move so it matches the relocation exactly (`$(REPO_ROOT)` is
    the project root in the harness).

    Scoped to the conventional a2c harness (`include/make/shared.mk`). A project
    with a bespoke harness (no conventional shared.mk) is left untouched — the
    migration cannot know where such a project sets A2C_PRJ_YAML; the report's
    empty harness-edits list signals nothing was re-pointed."""
    projMove = next((m for m in report.moves if m.kind == MOVE_PROJECT_FILE), None)
    if projMove is None:
        return
    harness = os.path.join(report.projectRoot, HARNESS_MK)
    if not os.path.isfile(harness):
        return
    relProjYaml = os.path.relpath(projMove.dst, report.projectRoot)
    newLine = f"A2C_PRJ_YAML = $(REPO_ROOT)/{relProjYaml}"
    match = _A2C_PRJ_YAML_RE.search(_read(harness))
    report.harnessEdits.append(
        HarnessEdit(harness, match.group(0) if match else "", newLine))


def _topSegment(path, projectRoot):
    """The first path component of `path` relative to `projectRoot`, or None when
    `path` lies outside the project root."""
    rel = os.path.relpath(os.path.abspath(path), os.path.abspath(projectRoot))
    if rel == os.pardir or rel.startswith(os.pardir + os.sep):
        return None
    return rel.split(os.sep)[0]


def _foldedLines(text):
    """Yield (1-based start line, logical line) with make's trailing-backslash
    continuations folded into one string, so a multi-line variable assignment is
    matched as a whole. The reported line is where the assignment STARTS, which is
    the line the user edits."""
    physical = text.splitlines()
    i = 0
    while i < len(physical):
        start = i
        logical = physical[i]
        while logical.endswith("\\") and i + 1 < len(physical):
            i += 1
            logical = logical[:-1] + " " + physical[i].strip()
        yield start + 1, logical
        i += 1


def _planExtraPathWarnings(report):
    """Warn on EXTRA_* make-variable references to relocatable segment roots.

    A user's root-relative build harness (`include/make/shared.mk`) or
    `rundir/Makefile` can point EXTRA_* variables (EXTRA_SC_GEN_FILES,
    EXTRA_SV_GEN_FILES, EXTRA_PRJ_SRC_DIRS, ...) at a functional segment root via
    `$(REPO_ROOT)/<segment>/...`. Those roots relocate under hierarchical layout,
    so the reference dangles after the move. The migration does NOT rewrite EXTRA_*
    text (it uses the $(REPO_ROOT) macro and free-form make); it surfaces each such
    reference as a TODO_UNREWRITABLE_PATH manual item so the user re-points it by
    hand, the same mechanism used for unrewritable include/projectFiles paths. One
    item per (assignment, referenced root), so a continued list naming several
    segments reports each of them.

    The relocatable roots are the functional segments the migration moves
    (`report.relocatableRoots`, the top-level project-root component of each), so
    only references to a segment root that actually relocates warn."""
    relocatedTops = report.relocatableRoots
    if not relocatedTops:
        return
    for rel in (HARNESS_MK, RUNDIR_MK):
        path = os.path.join(report.projectRoot, rel)
        if not os.path.isfile(path):
            continue
        for line, logical in _foldedLines(_read(path)):
            m = _EXTRA_VAR_RE.match(logical)
            if m is None:
                continue
            var = m.group(1)
            # Every distinct relocating root the assignment references is
            # reported: one continued list commonly names several segments, and a
            # single item per assignment would leave the rest silently dangling.
            tops = sorted({r.group("top")
                           for r in _REPO_ROOT_REF_RE.finditer(m.group("rhs"))
                           if r.group("top") in relocatedTops})
            for top in tops:
                report.manual.append(ReportItem(
                    TODO_UNREWRITABLE_PATH, _loc(path, line),
                    f"{var} references '$(REPO_ROOT)/{top}' which relocates under "
                    f"hierarchical layout and cannot be rewritten mechanically; "
                    f"re-point it by hand"))


def _applyHarnessEdits(report):
    """Apply the planned A2C_PRJ_YAML re-point: replace an existing assignment in
    place, or insert the line before the first makefile `include` so it wins over
    a2c-common.mk's `?=` default on the first post-migration build."""
    for edit in report.harnessEdits:
        text = _read(edit.path)
        if edit.old:
            text = text.replace(edit.old, edit.new, 1)
        else:
            inc = _MK_INCLUDE_RE.search(text)
            block = edit.new + "\n\n"
            if inc:
                text = text[:inc.start()] + block + text[inc.start():]
            else:
                if text and not text.endswith("\n"):
                    text += "\n"
                text += edit.new + "\n"
        _write(edit.path, text)


# ---------------------------------------------------------------------------
# Layout detection
# ---------------------------------------------------------------------------

def _declaredLayout(projectData):
    """The project file's declared layout, defaulting to 'functional' (the base
    config default; absent selector == no opt-in)."""
    fileGen = projectData.get("fileGeneration") or {}
    return fileGen.get("layout") or "functional"


def _onDiskLayout(projectYamlPath, projectData):
    """'hierarchical' when the project file sits in the hierarchical project
    container (`<prj>/<yaml>/<name>Project.yaml`), else 'functional'.

    This mirrors the layout's own discovery rule: a hierarchical project's file
    lives under the `$prj` container's `yaml/` subdir, while a functional
    project's file lives under the central functional yaml root (`arch/yaml/`).
    Path-based, so it needs no database and is correct before any relocation."""
    prjSeg, yamlSeg = _prjYamlSegments(projectData)
    parent = os.path.basename(os.path.dirname(projectYamlPath))
    grandparent = os.path.basename(os.path.dirname(os.path.dirname(projectYamlPath)))
    if parent == yamlSeg and grandparent == prjSeg:
        return "hierarchical"
    return "functional"


def _prjYamlSegments(projectData):
    """The (prj, yaml) project-scope segment basenames. Honors a project file
    that overrides `fileGeneration.hierarchicalDirs`; otherwise the base-config
    defaults. The prj entry is a `$root`-rooted spec (`$root/prj`), so its
    basename is taken."""
    hdirs = ((projectData.get("fileGeneration") or {}).get("hierarchicalDirs")) or {}
    prj = os.path.basename(hdirs.get("prj", DEFAULT_PRJ_SEGMENT))
    yamlSeg = hdirs.get("yaml", DEFAULT_YAML_SEGMENT)
    return prj, yamlSeg
