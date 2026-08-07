"""Restructure the user-owned `<block>Config.cpp` from the legacy single
`tbConfig` region into the three-section form (`prerequisites` / `class` /
`registration`).

`<block>Config.cpp` is the one member of the testbench family that stays a plain
translation unit, so nothing moves and no zone rule applies: its single user slot
accepts `#include` and `import` interleaved in any order. What changes is
ownership. Three pieces that used to live in the create-once scaffold now live in
generated regions, and all three edits are mandatory — a Config.cpp carrying only
the first no longer builds:

  1. INSERT the `prerequisites` and `registration` region markers, and DELETE the
     framework prerequisites the first of them now emits (`systemc.h`, `<string>`,
     `instanceFactory.h`, `testBenchConfigFactory.h`, `import a2c.endOfTest;`).
     Whatever else the legacy preamble held is genuine user content and is moved,
     in order, into the seeded user slot below the new region.
  2. RENAME the bare `--template=tbConfig` region to `--section=class`. The
     template now routes on `--section`, and a region command with none arrives as
     the EMPTY STRING, so gen aborts with
     `ValueError: Unknown section '' for template 'tbConfig'`.
  3. DELETE the stranded out-of-class definition
     `<blk>Config::registerTestBenchConfig <blk>Config::registerTestBenchConfig_;`.
     The nested `registerTestBenchConfig` struct it names is gone from the class
     region, replaced by an `A2C_REGISTRATION_RETAIN` anonymous-namespace static in
     the new `registration` region, so the line is left naming a type that no
     longer exists. It sits in the user-owned tail, where gen never looks.

The retired definition line is also the anchor the `registration` region replaces:
losing the registration is a RUN-time failure (the testbench is never registered
with the factory), not a build error, so a Config.cpp with no such line is
reported rather than silently left without the region.

DB-backed, like migrateProjectParam: resolving the owned `<block>Config.cpp` set
needs the merged fileMap and the layout placement from a read-only projectOpen
handle. It runs in the `migrateYaml.py --port-tb` phase, after `make newmodule` and
BEFORE `make gen`, because gen cannot render the file until edit 2 is done.

Owner-gated (a composed build never rewrites a referenced child's Config) and
idempotent (a file whose `tbConfig` region already names a `--section` is a
no-op).
"""

import os
from dataclasses import dataclass, field

from pysrc.migrateCommon import (_read, _write, _isGenerated, _loc, _regions,
                                 _find, _includeTarget, _importTarget,
                                 _noCodeMask, _stripBlankEnds, PARAM_MARKER)
from pysrc.processYaml import expandNewModulePath, fileMapCondMatch


GEN_BEGIN = "// GENERATED_CODE_BEGIN"
GEN_END = "// GENERATED_CODE_END"

# The framework baseline `tbConfig --section=prerequisites` now emits
# (templates/systemc/testbench.py::tb_config_prerequisites). A legacy preamble copy
# of any of these is deleted; anything else there is user content and is moved.
# unittest/test_migrate_tb_port.py pins this set against what that template really
# emits, so the two cannot drift: gaining an entry there without gaining one here
# leaves a duplicate include behind, and losing one drops a user line.
# The region's one project-dependent line, `#include "<context>VariantConfig.h"`, is
# deliberately absent from both tuples: the header is include-guarded, so a legacy
# hand-added copy left in the user slot is a no-op, and dropping a user line by a name
# the migrator would have to derive per block is the riskier of the two.
# `systemc.h` is deliberately absent too: the region no longer emits it, so a legacy
# copy is user content and relocates to the user slot like any other header.
PREREQ_INCLUDES = ("string", "instanceFactory.h",
                   "testBenchConfigFactory.h")
PREREQ_IMPORTS = ("a2c.endOfTest",)

# The retired registration mechanism's identifier. The out-of-class definition of
# the in-class `static registerTestBenchConfig registerTestBenchConfig_;` is the
# only part of it that survives in user-owned text, so this fixed framework spelling
# locates it without composing the Config class name from a filename or block name.
RETIRED_REGISTRATION_TOKEN = "::registerTestBenchConfig_"

# Inserted above the `class` region: the prerequisites region plus the seeded user
# slot. Byte for byte the fresh-scaffold shape (fileGen.py tbConfigTemplate), whose
# wording deliberately differs from the two module-unit slots because this file has
# no zone rules; the two must change together.
_PREREQ_INSERT = (
    f"{GEN_BEGIN} --template=tbConfig --section=prerequisites\n"
    f"{GEN_END}\n"
    "// user #includes and imports here\n"
    "// A plain translation unit, not a module: either may appear here in any order.\n"
)

# Replaces the retired out-of-class registration definition.
_REGISTRATION_INSERT = (
    f"{GEN_BEGIN} --template=tbConfig --section=registration\n"
    f"{GEN_END}\n"
)

# Applied-edit kind.
TB_CONFIG_RESTRUCTURE = "TB_CONFIG_RESTRUCTURE"

# Manual-TODO kinds (file left untouched).
TODO_TBCONFIG_NO_REGION = "TODO_TBCONFIG_NO_REGION"      # no tbConfig region to rename
TODO_TBCONFIG_NO_PARAM = "TODO_TBCONFIG_NO_PARAM"        # no GENERATED_CODE_PARAM line
TODO_TBCONFIG_NO_REGISTRATION = "TODO_TBCONFIG_NO_REGISTRATION"  # retired definition absent
TODO_TBCONFIG_UNPLACED = "TODO_TBCONFIG_UNPLACED"        # no-silent-loss guard tripped
TODO_TBCONFIG_UNGENERATED = "TODO_TBCONFIG_UNGENERATED"  # path lacks the generated marker
TODO_TBCONFIG_DIRECTIVE = "TODO_TBCONFIG_DIRECTIVE"      # preamble directive the move would re-scope


@dataclass(frozen=True)
class ReportItem:
    kind: str
    location: str
    message: str


@dataclass
class TbConfigReport:
    projectName: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        return not self.manual


# ---------------------------------------------------------------------------
# Restructure computation
# ---------------------------------------------------------------------------

def _paramLineIndex(lines):
    """0-based index of the file's GENERATED_CODE_PARAM line, or None."""
    for i, line in enumerate(lines):
        if PARAM_MARKER in line:
            return i
    return None


def _isPrerequisite(stripped):
    """True for a legacy preamble line the `prerequisites` region now emits."""
    return (_includeTarget(stripped) in PREREQ_INCLUDES
            or _importTarget(stripped) in PREREQ_IMPORTS)


def _movedDirectives(moved):
    """Preprocessor directives other than `#include` in the relocated preamble.

    The relocation puts the residual preamble BELOW the `prerequisites` region, so a
    directive whose effect depends on preceding it — a feature macro such as
    `#define SC_INCLUDE_DYNAMIC_PROCESSES`, a conditional, an `#undef` — would change
    meaning without changing text, which the no-loss guard cannot see. Reported so
    the move is refused rather than made silently."""
    out = []
    for line in moved:
        s = line.strip()
        if s.startswith("#") and _includeTarget(s) is None:
            out.append(s)
    return out


def _leadingCommentRun(lines, limit):
    """Index of the first line before `limit` that is neither blank nor a `//`
    comment — the end of the file's copyright header, which stays at the top."""
    i = 0
    while i < limit:
        s = lines[i].strip()
        if s != "" and not s.startswith("//"):
            break
        i += 1
    return i


def _registrationLineIndex(lines, start):
    """0-based index of the retired out-of-class registration definition at or after
    `start`, or None."""
    for i in range(start, len(lines)):
        if RETIRED_REGISTRATION_TOKEN in lines[i]:
            return i
    return None


@dataclass
class _Restructure:
    text: str                    # the rewritten file
    movedUserLines: list         # preamble lines relocated into the user slot
    droppedPrereqs: list         # framework prerequisite lines the region now owns
    droppedRegistration: list    # the retired out-of-class registration definition

    @property
    def droppedLines(self):
        return self.droppedPrereqs + self.droppedRegistration


def _restructure(text, classRegion, paramIdx, registrationIdx):
    """Build the restructured file.

    The head (copyright comment run) stays put and the PARAM line moves directly
    below it so the result reads in the canonical scaffold order: PARAM,
    prerequisites region, user slot, class region. Everything from the class region
    onwards is carried across verbatim except the retired registration definition,
    which the registration region replaces in place.

    The whole span from the head to the class region is accounted for: the lines
    above the PARAM line become the relocated preamble, and the lines BETWEEN the
    PARAM line and the class region are carried with them (that span is empty in
    every measured file, but nothing here relies on that).
    """
    lines = text.splitlines(keepends=True)
    headEnd = _leadingCommentRun(lines, paramIdx)

    preamble = lines[headEnd:paramIdx] + lines[paramIdx + 1:classRegion.begin]
    dropped = [ln for ln in preamble if _isPrerequisite(ln.strip())]
    moved = _stripBlankEnds([ln for ln in preamble
                             if not _isPrerequisite(ln.strip())])

    tail = list(lines[classRegion.begin:])
    tailOffset = classRegion.begin
    registration = []
    if registrationIdx is not None:
        registration = [lines[registrationIdx]]
        tail[registrationIdx - tailOffset] = _REGISTRATION_INSERT

    # Rename the bare region command in place; the class region content itself is
    # refilled by the next gen.
    tail[0] = tail[0].rstrip("\n") + " --section=class\n"

    out = (lines[:headEnd] + [lines[paramIdx]] + [_PREREQ_INSERT]
           + moved + tail)
    return _Restructure(text="".join(out), movedUserLines=moved,
                        droppedPrereqs=dropped, droppedRegistration=registration)


def _verifyNoLoss(original, result):
    """No-silent-loss guard. Every code-bearing line of the original must appear in
    the rewritten file, except the framework prerequisites and the retired
    registration definition the restructure deliberately drops. Returns the
    (1-based lineNo, text) of any line that does not, so the caller can refuse the
    edit rather than lose user code."""
    lines = original.splitlines()
    noCode = _noCodeMask(lines)
    kept = set()
    for ln in result.text.splitlines():
        kept.add(ln.strip())
    droppedText = {ln.strip() for ln in result.droppedLines}
    misses = []
    for i, line in enumerate(lines):
        if noCode[i]:
            continue
        s = line.strip()
        if s in kept or s in droppedText:
            continue
        misses.append((i + 1, s))
    return misses


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def restructureTbConfigs(prj, write=False):
    """Restructure every owned `<block>Config.cpp` into the three-section form.
    Returns a TbConfigReport."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = TbConfigReport(projectName=projectName)
    fileDef = prj.filemap["tbConfig"]
    layout = prj.projectLayout[projectName]
    wrote = False

    for blockRow in prj.data["blocks"].values():
        if prj.contextOwningProject[blockRow["_context"]] != projectName:
            continue
        if not fileMapCondMatch(fileDef, blockRow):
            continue
        blockName = blockRow["block"]
        path = expandNewModulePath(fileDef, blockRow["dir"], blockName, blockName,
                                   layout, missingDirOk=True)
        for ext in fileDef["ext"].values():
            if _restructureOne(report, layout, blockName, f"{path}.{ext}", write):
                wrote = True
    report.written = wrote
    return report


def _restructureOne(report, layout, blockName, path, write):
    """Restructure one `<block>Config.cpp`. Returns True when the file was written."""
    if not os.path.exists(path):
        return False
    location = os.path.relpath(path, layout["root"])
    if not _isGenerated(path):
        report.manual.append(ReportItem(
            TODO_TBCONFIG_UNGENERATED, location,
            f"{os.path.basename(path)} has no generated marker; left in place for "
            f"manual review (not restructured)"))
        return False

    text = _read(path)
    regions = _regions(text)
    classRegion = _find(regions, "tbConfig")
    if classRegion is None:
        report.manual.append(ReportItem(
            TODO_TBCONFIG_NO_REGION, location,
            f"{os.path.basename(path)} carries no `--template=tbConfig` region to "
            f"split; restore it from a fresh scaffold by hand"))
        return False
    if "--section=" in classRegion.command:
        return False  # already three-section (idempotent)

    lines = text.splitlines(keepends=True)
    paramIdx = _paramLineIndex(lines)
    if paramIdx is None or paramIdx > classRegion.begin:
        report.manual.append(ReportItem(
            TODO_TBCONFIG_NO_PARAM, location,
            f"{os.path.basename(path)} has no GENERATED_CODE_PARAM line above its "
            f"tbConfig region; the restructure anchors the new regions on it"))
        return False

    registrationIdx = _registrationLineIndex(lines, classRegion.end + 1)
    if registrationIdx is None:
        report.manual.append(ReportItem(
            TODO_TBCONFIG_NO_REGISTRATION, location,
            f"{os.path.basename(path)} has no out-of-class "
            f"`{RETIRED_REGISTRATION_TOKEN}` definition after the class; that line "
            f"is the anchor the `--section=registration` region replaces, and "
            f"without the region the testbench is never registered with the factory "
            f"(a run-time failure, not a build error). Add the region by hand from a "
            f"fresh scaffold"))
        return False

    result = _restructure(text, classRegion, paramIdx, registrationIdx)
    directives = _movedDirectives(result.movedUserLines)
    if directives:
        report.manual.append(ReportItem(
            TODO_TBCONFIG_DIRECTIVE, location,
            f"{os.path.basename(path)} has preprocessor directive(s) in its preamble "
            f"({directives[0]!r}) that the restructure would move BELOW the new "
            f"prerequisites region, changing what they apply to. Place them by hand "
            f"relative to the region, then re-run"))
        return False
    misses = _verifyNoLoss(text, result)
    if misses:
        lineNo, missText = misses[0]
        report.manual.append(ReportItem(
            TODO_TBCONFIG_UNPLACED, _loc(path, lineNo),
            f"block '{blockName}' Config: the restructure could not place "
            f"{len(misses)} source line(s); first unplaced at line {lineNo}: "
            f"{missText!r}. Refusing to rewrite the file"))
        return False

    report.applied.append(ReportItem(
        TB_CONFIG_RESTRUCTURE, location,
        f"split the tbConfig region into prerequisites/class/registration, dropped "
        f"{len(result.droppedPrereqs)} framework prerequisite line(s) and the retired "
        f"out-of-class registration definition, and moved "
        f"{len(result.movedUserLines)} user preamble line(s) into the seeded slot"))
    if write:
        _write(path, result.text)
        return True
    return False


def renderTbConfigReport(report, write):
    lines = [f"=== testbench config restructure: {report.projectName} ==="]
    if not report.applied and not report.manual:
        lines.append("  every <block>Config.cpp is already three-section; nothing to do")
        return "\n".join(lines)
    if report.applied:
        verb = "applied" if write else "would apply (dry-run; re-run with --write)"
        lines.append(f"  {verb}:")
        for item in report.applied:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    if report.manual:
        lines.append("  manual TODO (see the migration skill):")
        for item in report.manual:
            lines.append(f"    {item.location}  {item.kind}  {item.message}")
    return "\n".join(lines)
