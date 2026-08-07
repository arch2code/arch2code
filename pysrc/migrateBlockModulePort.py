"""Mechanized `.cpp`/`.h` -> `.cppm` port of the two user-code file families:
the block implementation (item 5) and the testbench External.

Both families are the SAME four-slot transplant over a different marker
vocabulary, so the mechanism below is parameterized by a `PortShape`. Three entry
points drive it, the third being a PARAM-line carry with no slots at all:

  `portBlockModules`  block implementation, `classDecl` + `constructor` regions.
                      Runs POST-`make gen` (`migrateYaml.py --port`).
  `portTbExternals`   testbench External, `tbExternal` header/init/body regions.
                      Runs between `make newmodule` and `make gen`
                      (`migrateYaml.py --port-tb`), because it also carries the
                      legacy GENERATED_CODE_PARAM across: the External's `--block`
                      is a documented user retarget at the `_tb` container, which
                      a fresh scaffold cannot know, and gen must see the retargeted
                      line to fill the regions for the right block.
  `portTbTops`        testbench top. NOT a slot transplant — the tb top has no user
                      code — but it sits here because it is the same
                      carry-the-PARAM-line-then-delete-the-pair operation, on the
                      same `--port-tb` schedule and for the same reason: only the
                      user's DUT `--variant=` survives the re-scaffold this way.

The rest of this docstring describes the block port (item 5).

Item 5 converts EVERY block implementation to a single C++20 module interface
unit (`<block>.cppm`), regardless of parameterization. After the `blockModule`
fileMap gate is relaxed to `cond: {hasMdl: true}`, a non-parameterized block's
current artifact is a `.cppm` that `make newmodule` + `make gen` scaffold with
empty user slots, while its hand-written code still lives in the legacy
`<block>.h` + `<block>.cpp` pair the orphan sweep reports as `TODO_PORT`. This
module performs the mechanical transplant the sweep only reports.

DB-backed and runs POST-`make gen`, unlike the text phases and unlike the sweep
(which runs pre-newmodule): the transplant target is the gen-FILLED `.cppm`, so
the `.cppm` must already carry its generated regions. Driven by
`migrateYaml.py --port --write --db <db>` as the final step of the `make migrate`
pipeline (after newmodule + gen). It opens the database READ-ONLY (`projectOpen`)
to enumerate owned blocks and resolve the legacy/current file paths, then edits
SOURCE files (never the DB): it moves the four user slots into the `.cppm` and
deletes the legacy pair.

Deterministic four-slot transplant, all boundaries found by the GENERATED_CODE
markers (never by string-manipulating a filename into a semantic name):

  1. class body       (from `<block>.h`, after `classDecl` END, before class `};`)
  2. constructor init  (from `.cpp`, between `constructor --section=init` END and
                        `--section=body` BEGIN)
  3. constructor body  (from `.cpp`, after `--section=body` END, before ctor `};`)
  4. out-of-line defs  (from `.cpp`, after ctor `};` to EOF) -> module tail

plus the top-of-file `#include`s: the include guard, `#include "systemc.h"`, and
the `.cpp`'s own `#include "<block>.h"` are dropped; a genuinely external header
(e.g. `testController.h`, `endOfTest.h`) is relocated to the `// user #includes
here` GMF slot so it attaches to the global module, not the block module.

DELETE-and-REGENERATE (no user code — the legacy pair is removed and `make gen`
recreates the .cppm in full from its scaffold; nothing to transplant, nothing to
hand-port):
  - a synthesized reg-handler (`isRegHandler`): its members, register/memory
    wiring, ctor init-list, and body are all emitted inside generated regions;
  - an apbDecode router (its block row carries `addressBlock:`): its decoder
    member, routerDecode thread, and ctor init are likewise fully generated.

DETECT-and-FLAG (never ported) — left for an agent, legacy pair untouched:
  - a parameterized block (`hasOwnParams`): its templatization (T2) is semantic;
  - a module-hostile library (e.g. OpenCV) in any user slot: needs a design call;
  - non-boilerplate content in a top-of-file slot (anything that is not a
    comment, blank, include guard, or `#include`): the port cannot place it.

Owner-gated (a composed build never ports a referenced child's block; the child
ports it in its own tree) and idempotent (a block whose legacy pair is already
gone is a no-op).
"""

import os
from dataclasses import dataclass, field

from pysrc import intf_gen_utils
from pysrc.migrateCommon import (_read, _write, _isGenerated, _loc, _regions,
                                 _find, _includeTarget, _importTarget,
                                 _noCodeMask, _stripBlankEnds, PARAM_MARKER,
                                 paramTail, paramVariant, replaceParamVariant,
                                 restampParamLine)
from pysrc.migrateOrphans import LEGACY_FILEMAP
from pysrc.processYaml import expandNewModulePath, fileMapCondMatch


# Applied-edit kinds.
BLOCK_PORTED = "BLOCK_PORTED"  # user block: four-slot transplant into the .cppm
BLOCK_REGEN = "BLOCK_REGEN"    # reg-handler / apbDecode router: legacy pair deleted, .cppm regenerated
TB_EXTERNAL_PORTED = "TB_EXTERNAL_PORTED"  # testbench External: four-slot transplant into the .cppm
TB_TOP_PORTED = "TB_TOP_PORTED"    # testbench top: DUT --variant= carried onto the .cppm, legacy pair deleted

# Manual-TODO kinds (block left un-ported, legacy pair untouched).
TODO_PORT_PARAM = "TODO_PORT_PARAM"            # parameterized block; templatize by hand (T2)
TODO_PORT_HOSTILE_LIB = "TODO_PORT_HOSTILE_LIB"  # module-hostile library in a user slot
TODO_PORT_SLOT0 = "TODO_PORT_SLOT0"            # non-boilerplate top-of-file content
TODO_PORT_NO_CPPM = "TODO_PORT_NO_CPPM"        # legacy pair present but no gen'd .cppm target
TODO_PORT_UNPLACED = "TODO_PORT_UNPLACED"      # no-silent-loss guard: source code the port could not place
TODO_PORT_PARAM_SPLIT = "TODO_PORT_PARAM_SPLIT"  # legacy .h/.cpp disagree on GENERATED_CODE_PARAM
TODO_PORT_NO_PARAM_LINE = "TODO_PORT_NO_PARAM_LINE"    # legacy file carries no GENERATED_CODE_PARAM line
TODO_PORT_TARGET_DAMAGED = "TODO_PORT_TARGET_DAMAGED"  # target .cppm lacks a PARAM line or a needed region
TODO_PORT_STALE_VARIANT = "TODO_PORT_STALE_VARIANT"    # carried --variant= is not a declared variant of the block
TODO_PORT_TAIL_UNPLACED = "TODO_PORT_TAIL_UNPLACED"    # legacy PARAM tail holds an argument the carry does not account for

# Module-hostile libraries: their headers pull SIMD-intrinsic / precompiled
# content that clashes with the global module when included in a module purview.
# Confining them is a per-block design decision, so the port flags rather than
# attempts them. Minimal and extend-as-needed; matched as a substring of the
# included header path.
_HOSTILE_LIB_MARKERS = ("opencv",)

# Scaffold boilerplate literal the block_hdr / blockModule_cppm scaffolds both
# emit after the class declaration; carried in the legacy header's class-body
# slot but already present in the target, so it is dropped on transplant.
_IMPL_MEMBERS_COMMENT = "// block implementation members"

# Its testbench-External counterpart (fileGen.py tbExternal_cppm).
_EXT_MEMBERS_COMMENT = "// external implementation members"


@dataclass(frozen=True)
class PortShape:
    """The marker vocabulary and boilerplate set of one ported file family.

    The transplant itself is one mechanism; only the region names, the scaffold
    class-body label, and the framework prerequisites the target's generated
    regions now own differ between a block implementation and a testbench
    External.
    """
    classTemplate: str    # class-region `--template=` (source header AND target)
    classSection: str     # its `--section=`, or None when the template has none
    ctorTemplate: str     # constructor init/body `--template=` (source AND target)
    gmfSection: str       # target `moduleScaffold --section=` owning the GMF
    implComment: str      # scaffold class-body label the target already carries
    dropIncludes: tuple   # framework headers a generated region now emits
    dropImports: tuple    # framework module imports `moduleExport` now emits


# Block implementation: `<block>.h` + `<block>.cpp` -> `<block>.cppm`. The GMF
# baseline the target generates is `systemc.h`; every other top-of-file include is
# user content and moves to the GMF user slot.
BLOCK_SHAPE = PortShape(
    classTemplate="classDecl", classSection=None,
    ctorTemplate="constructor", gmfSection="blockModuleHeader",
    implComment=_IMPL_MEMBERS_COMMENT,
    dropIncludes=("systemc.h",), dropImports=())

# Testbench External: `<block>External.h` + `.cpp` -> `<block>External.cppm`. The
# `tbExternalModuleHeader` GMF section emits the systemc/logging baseline its own
# generated lines need and `moduleExport` emits `import a2c.endOfTest;`, so the
# legacy pair's copies of those are dropped rather than relocated. `workerThread.h`
# is NOT dropped: no generated line names a `worker*` symbol, so it is the user's
# stimulus-thread prerequisite and relocates to the GMF user slot like any other
# genuinely external header.
TB_EXTERNAL_SHAPE = PortShape(
    classTemplate="tbExternal", classSection="header",
    ctorTemplate="tbExternal", gmfSection="tbExternalModuleHeader",
    implComment=_EXT_MEMBERS_COMMENT,
    dropIncludes=("systemc.h", "logging.h"),
    dropImports=("a2c.endOfTest",))


@dataclass(frozen=True)
class ReportItem:
    kind: str
    location: str
    message: str


@dataclass
class BlockPortReport:
    projectName: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        return not self.manual


# ---------------------------------------------------------------------------
# Slot-boundary walk (the scaffold's brace conventions)
# ---------------------------------------------------------------------------

def _firstClosingBrace(lines, start):
    """Index of the first line at or after `start` that is exactly `};` at column 0
    (the class or scaffolded-constructor closing brace), or None. Match only at
    column 0 so an INDENTED inner `};` — a nested struct/enum/union close or a
    brace-aggregate initializer (`video_frame_t {...};`) in the class body — is
    never mistaken for the class close. The class/module close and the generated
    scaffold's constructor close are always emitted at column 0; nested members are
    indented, so column anchoring is exact (mirrors `_firstCtorClose`)."""
    for i in range(start, len(lines)):
        line = lines[i]
        if line[:1] not in (" ", "\t") and line.rstrip() == "};":
            return i
    return None


def _firstCtorClose(lines, start):
    """Index of the first constructor-closing line (`}` or `};`) at column 0 at or
    after `start`, or None. The scaffold form is `};`, but a hand-edited ctor
    closes with the natural `}`. Match only at column 0 so an indented inner-block
    brace (a for/if body inside the ctor) is never mistaken for the ctor close."""
    for i in range(start, len(lines)):
        line = lines[i]
        if line[:1] not in (" ", "\t") and line.rstrip() in ("}", "};"):
            return i
    return None


# ---------------------------------------------------------------------------
# Legacy source slot extraction
# ---------------------------------------------------------------------------

@dataclass
class LegacySlots:
    classBody: list = field(default_factory=list)     # class-body member lines
    ctorInit: list = field(default_factory=list)      # constructor init-list lines
    ctorBody: list = field(default_factory=list)      # constructor body lines
    outOfLine: list = field(default_factory=list)     # trailing out-of-line def lines
    userIncludes: list = field(default_factory=list)  # external #includes -> GMF slot
    siblingImports: list = field(default_factory=list)  # sibling-block imports -> module purview
    slot0Flags: list = field(default_factory=list)    # unplaceable top-of-file lines
    hostileLib: str = None                            # first hostile-lib header seen
    # No-silent-loss accounting: the source lines and the 0-based line indices the
    # extraction accounted for (dropped generated region, slot0 the classifier
    # walked, a captured slot span, or a structural closer). Every index NOT here
    # is residual the guard must prove is whitespace/comment/recognized boilerplate.
    hLines: list = field(default_factory=list)        # legacy .h source lines
    cppLines: list = field(default_factory=list)      # legacy .cpp source lines
    hAccounted: set = field(default_factory=set)      # accounted .h line indices
    cppAccounted: set = field(default_factory=set)    # accounted .cpp line indices


def _ifndefIdent(stripped):
    """The identifier of a bare `#ifndef IDENT` line (no trailing tokens), or None."""
    parts = stripped.split()
    if len(parts) == 2 and parts[0] == "#ifndef" and parts[1].isidentifier():
        return parts[1]
    return None


def _defineGuardIdent(stripped):
    """The identifier of a value-less `#define IDENT` line (guard define), or None.
    A `#define X value` (macro with a replacement) is not a guard define."""
    parts = stripped.split()
    if len(parts) == 2 and parts[0] == "#define" and parts[1].isidentifier():
        return parts[1]
    return None


def _guardLineSet(lines):
    """0-based indices of a structural include guard, or an empty set. Recognized
    macro-name-agnostically and strictly: a top-of-file `#ifndef IDENT` (first
    code-bearing line) whose IMMEDIATELY following line is `#define IDENT` with the
    SAME identifier and no replacement value opens the guard; the last `#endif`
    closes it. A bare `#ifndef FEATURE` conditional (no paired define) or a valued
    `#define X value` is not a guard. A `.cpp` has no such pair, so this is empty."""
    firstIdx = None
    for i, line in enumerate(lines):
        s = line.strip()
        if s == "" or s.startswith("//"):
            continue
        firstIdx = i
        break
    if firstIdx is None:
        return set()
    ifn = _ifndefIdent(lines[firstIdx].strip())
    if ifn is None:
        return set()
    defIdx = firstIdx + 1
    if defIdx >= len(lines) or _defineGuardIdent(lines[defIdx].strip()) != ifn:
        return set()
    guard = {firstIdx, defIdx}
    for i in range(len(lines) - 1, defIdx, -1):
        if lines[i].strip().startswith("#endif"):
            guard.add(i)
            break
    return guard


def _classifyTopOfFile(topLines, dropIncludes, dropImports, guardSet,
                       siblingModules, childHeaders, slots):
    """Classify a top-of-file (slot-0) span: drop boilerplate (copyright/marker
    comments, the include guard, the framework prerequisites in `dropIncludes` and
    `dropImports` that a generated region of the target now emits, and the file's
    own header), convert a sibling-block header include to a module import
    (dropping it when the sibling is a contained instance the generator already
    auto-imports), collect a genuinely external `#include` for the GMF slot, and
    record anything else as an unplaceable flag. `guardSet` carries the
    file-absolute indices of the structural include guard; the top slice begins at
    line 0, so its indices are file-absolute too."""
    for i, raw in enumerate(topLines):
        s = raw.strip()
        if s == "" or s.startswith("//"):
            continue
        if i in guardSet:
            continue
        header = _includeTarget(s)
        if header is not None:
            if header in dropIncludes:
                continue
            if any(marker in header for marker in _HOSTILE_LIB_MARKERS):
                if slots.hostileLib is None:
                    slots.hostileLib = header
                continue
            base = os.path.basename(header)
            if base in childHeaders:
                # A contained instance is auto-imported (`.base`) by the generator
                # regardless of owning project, so its legacy include is vestigial
                # and simply dropped — whether or not it is a project-local sibling.
                # (A cross-project contained child is NOT in `siblingModules`, so
                # this drop must be checked before the sibling-conversion branch.)
                continue
            if base in siblingModules:
                # A sibling now built as a `.cppm` has no `.h`; import its `.block`
                # module instead.
                imp = f"import {siblingModules[base]};"
                if imp not in slots.siblingImports:
                    slots.siblingImports.append(imp)
                continue
            line = raw.rstrip()
            if line not in slots.userIncludes:
                slots.userIncludes.append(line)
            continue
        if _importTarget(s) in dropImports:
            continue
        slots.slot0Flags.append(s)


def _scanHostile(lines, slots):
    """Record the first module-hostile-library header `#include`d anywhere in a
    span (a hostile header in a method body is as fatal as one at the top)."""
    if slots.hostileLib is not None:
        return
    for raw in lines:
        header = _includeTarget(raw.strip())
        if header and any(marker in header for marker in _HOSTILE_LIB_MARKERS):
            slots.hostileLib = header
            return


def _extractSlots(hText, cppText, shape, dropIncludes, siblingModules, childHeaders):
    """Extract the four user slots (plus relocated includes/imports and flags) from
    the legacy `.h`/`.cpp` pair, keyed off the GENERATED_CODE markers. `shape` names
    the family's region vocabulary; `dropIncludes` is its framework prerequisite set
    plus this file's own header basename."""
    slots = LegacySlots()

    # Header: class-body members between the class region's END and the class `};`.
    hLines = hText.splitlines()
    slots.hLines = hLines
    hRegions = _regions(hText)
    for r in hRegions:                                 # dropped generated regions
        slots.hAccounted.update(range(r.begin, r.end + 1))
    hGuard = _guardLineSet(hLines)                     # dropped include guard
    slots.hAccounted.update(hGuard)
    cls = _find(hRegions, shape.classTemplate, shape.classSection)
    if cls is not None:
        _classifyTopOfFile(hLines[:cls.begin], dropIncludes, shape.dropImports,
                           hGuard, siblingModules, childHeaders, slots)
        slots.hAccounted.update(range(0, cls.begin))   # slot0 (classifier-walked)
        classClose = _firstClosingBrace(hLines, cls.end + 1)
        body = hLines[cls.end + 1:classClose] if classClose is not None else []
        slots.classBody = _trimScaffold(body, shape.implComment)
        _scanHostile(slots.classBody, slots)
        if classClose is not None:                     # class-body span + `};` closer
            slots.hAccounted.update(range(cls.end + 1, classClose + 1))

    # Source: init-list, ctor body, and out-of-line defs off the constructor
    # sections; the top-of-file span carries the external includes.
    cLines = cppText.splitlines()
    slots.cppLines = cLines
    cRegions = _regions(cppText)
    for r in cRegions:                                 # dropped generated regions
        slots.cppAccounted.update(range(r.begin, r.end + 1))
    cGuard = _guardLineSet(cLines)                     # a `.cpp` has no guard (empty)
    slots.cppAccounted.update(cGuard)
    ini = _find(cRegions, shape.ctorTemplate, "init")
    bod = _find(cRegions, shape.ctorTemplate, "body")
    if ini is not None and bod is not None:
        _classifyTopOfFile(cLines[:ini.begin], dropIncludes, shape.dropImports,
                           cGuard, siblingModules, childHeaders, slots)
        slots.cppAccounted.update(range(0, ini.begin))          # slot0 (classifier-walked)
        slots.ctorInit = _stripBlankEnds(cLines[ini.end + 1:bod.begin])
        slots.cppAccounted.update(range(ini.end + 1, bod.begin))  # ctor init-list span
        ctorClose = _firstCtorClose(cLines, bod.end + 1)
        if ctorClose is not None:
            slots.ctorBody = _stripBlankEnds(cLines[bod.end + 1:ctorClose])
            slots.outOfLine = _stripBlankEnds(cLines[ctorClose + 1:])
            # ctor-body span + `}`/`};` closer, then the out-of-line tail to EOF.
            slots.cppAccounted.update(range(bod.end + 1, len(cLines)))
        _scanHostile(slots.ctorBody + slots.outOfLine, slots)

    return slots


def _trimScaffold(lines, implComment):
    """Drop the scaffold class-body label (the target already carries it) and blank
    ends from a class-body span."""
    kept = [ln for ln in lines if ln.strip() != implComment]
    return _stripBlankEnds(kept)


# ---------------------------------------------------------------------------
# No-silent-loss guard
# ---------------------------------------------------------------------------

def _unplacedLines(lines, accounted, dropIncludes, dropImports):
    """The (1-based lineNo, stripped text) of every source line the extraction did
    NOT account for that still carries code. A line is accounted when it is in
    `accounted` (dropped generated region, dropped include guard, classifier-walked
    slot0, a captured slot span, or a structural closer); the residual must be
    whitespace, comment, or a recognized boilerplate line the port intentionally
    drops (a framework prerequisite in `dropIncludes`/`dropImports`, or the file's
    own header). Anything else is code the port would silently lose."""
    noCode = _noCodeMask(lines)
    unplaced = []
    for i, line in enumerate(lines):
        if i in accounted or noCode[i]:
            continue
        s = line.strip()
        if _includeTarget(s) in dropIncludes:
            continue
        if _importTarget(s) in dropImports:
            continue
        unplaced.append((i + 1, s))
    return unplaced


def _verifyNoLoss(slots, shape, dropIncludes):
    """No-silent-loss guard. Prove the extraction placed every code-bearing line of
    the legacy `.h`/`.cpp`; return a list of `(fileTag, lineNo, text)` for any line
    it did not, so the caller can HARD-ERROR and refuse to delete the legacy pair.

    This is the true safety net: it is computed from the SAME region/closer
    boundaries the extraction used, so a brace-finder miss (the bare-`}` class, or
    anything like it) that drops a slot leaves those lines unaccounted here and
    turns silent loss into a loud, localized failure. An empty result means every
    code byte of both files is accounted for."""
    misses = []
    for tag, lines, accounted in (("h", slots.hLines, slots.hAccounted),
                                  ("cpp", slots.cppLines, slots.cppAccounted)):
        for lineNo, text in _unplacedLines(lines, accounted, dropIncludes,
                                           shape.dropImports):
            misses.append((tag, lineNo, text))
    return misses


# ---------------------------------------------------------------------------
# Transplant into the generated .cppm
# ---------------------------------------------------------------------------

def _asLines(rawLines):
    return [ln + "\n" for ln in rawLines]


def _afterCommentBlock(lines, start):
    """Index of the first line at or after `start` that is not a plain `//` comment
    — the insertion point directly below a seeded user-slot label of any length. A
    generated-region marker is a comment too, so it terminates the scan; otherwise
    an empty slot would push the insertion inside the next region."""
    i = start
    while i < len(lines):
        s = lines[i].strip()
        if not s.startswith("//") or "GENERATED_CODE" in s:
            break
        i += 1
    return i


def _buildPorted(cppmText, slots, shape):
    """Return the `.cppm` text with the four user slots transplanted into their
    marker-delimited target gaps, plus the relocated GMF includes. Insertions are
    applied bottom-to-top so earlier line indices stay valid."""
    lines = cppmText.splitlines(keepends=True)
    regions = _regions(cppmText)
    hdr = _find(regions, "moduleScaffold", shape.gmfSection)
    exp = _find(regions, "moduleExport")
    cls = _find(regions, shape.classTemplate, shape.classSection)
    ini = _find(regions, shape.ctorTemplate, "init")
    bod = _find(regions, shape.ctorTemplate, "body")

    inserts = []  # list[(index, [lines])] — insert before `index`

    # Below the whole `// user #includes here` label, mirroring the imports slot, so
    # the relocated includes read as belonging under their label. A legacy header or
    # plain `.cpp` include attached to the GLOBAL module, so the GMF slot is the one
    # placement that preserves its attachment; moving it into the preamble would
    # silently re-attach it to this module.
    if slots.userIncludes:
        inserts.append((_afterCommentBlock(lines, hdr.end + 1),
                        _asLines(slots.userIncludes)))

    # Sibling-block imports belong in the module purview (after `export module`
    # and the generated imports), not the GMF — imports must precede any other
    # module-purview declaration. Insert below the whole `// user imports here`
    # label the generator seeds immediately after the moduleExport region, so they
    # read as belonging under their label and stay ahead of the classDecl region's
    # `using namespace`. The label is a multi-line comment block, so skip it by
    # shape rather than by a fixed offset.
    if slots.siblingImports:
        inserts.append((_afterCommentBlock(lines, exp.end + 1), _asLines(slots.siblingImports)))

    classClose = _firstClosingBrace(lines, cls.end + 1)
    if slots.classBody:
        inserts.append((classClose, _asLines(slots.classBody)))

    if slots.ctorInit:
        inserts.append((ini.end + 1, _asLines(slots.ctorInit)))

    ctorClose = _firstClosingBrace(lines, bod.end + 1)
    if slots.ctorBody:
        inserts.append((ctorClose, _asLines(slots.ctorBody)))
    if slots.outOfLine:
        inserts.append((ctorClose + 1, _asLines([""] + slots.outOfLine)))

    for index, newLines in sorted(inserts, key=lambda e: e[0], reverse=True):
        lines[index:index] = newLines
    return "".join(lines)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def portBlockModules(prj, write=False):
    """Port every owned non-parameterized block's legacy `.h`/`.cpp` into its
    generated `.cppm`, deleting the legacy pair. Flags the edges it must not
    attempt. Returns a BlockPortReport."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = BlockPortReport(projectName=projectName)
    legacyDef = LEGACY_FILEMAP["block"]
    moduleDef = prj.filemap["blockModule"]
    wrote = False

    # Sibling-block header -> `.block` module name, so a legacy `#include "X.h"`
    # of a sibling now built as a `.cppm` becomes `import <X module>;`. Built from
    # persisted block rows the same way each block's own legacy path is resolved;
    # the module name comes from the block identity, never the filename. Keyed by
    # header basename: sibling detection assumes a header-basename <-> block-name
    # correspondence (last-wins on any same-basename collision). Kept project-
    # scoped: a cross-project sibling *type* reference is out of scope here.
    siblingModules = dict()     # legacy header basename -> sibling module name
    layout = prj.projectLayout[projectName]
    for row in prj.data["blocks"].values():
        if prj.contextOwningProject[row["_context"]] != projectName:
            continue
        if not fileMapCondMatch(moduleDef, row):
            continue
        base = expandNewModulePath(legacyDef, row["dir"], row["block"],
                                   row["block"], layout, missingDirOk=True)
        header = os.path.basename(base) + ".h"
        siblingModules[header] = intf_gen_utils.cpp_block_module_name(prj.blockModuleName[row["blockKey"]])

    # Legacy header basename per block key across ALL blocks, ANY owning project.
    # The contained-instance DROP set is drawn from this UNFILTERED map (not the
    # project-scoped sibling map above), so a cross-project contained child's
    # vestigial `#include "child.h"` is dropped too: that header disappears once
    # the child migrates, and the generator auto-imports the child's `.base`
    # regardless of owning project. Only the basename is consumed, so resolving a
    # cross-project block under this project's layout still yields the correct
    # block-name-derived header name.
    allBlockHeaders = dict()    # block key -> legacy header basename
    for row in prj.data["blocks"].values():
        if not fileMapCondMatch(moduleDef, row):
            continue
        base = expandNewModulePath(legacyDef, row["dir"], row["block"],
                                   row["block"], layout, missingDirOk=True)
        allBlockHeaders[row["blockKey"]] = os.path.basename(base) + ".h"

    # Contained-instance block keys per container block (a DB fact). A contained
    # child is auto-imported (`.base`) by the generator, so its legacy include is
    # dropped rather than converted. containerKey/instanceTypeKey are contracted,
    # always-present instance fields (processYaml.py:370,373), read directly.
    childKeys = dict()          # container block key -> set(child block key)
    for inst in prj.data["instances"].values():
        childKeys.setdefault(inst["containerKey"], set()).add(inst["instanceTypeKey"])

    for blockRow in prj.data["blocks"].values():
        if prj.contextOwningProject[blockRow["_context"]] != projectName:
            continue
        if not fileMapCondMatch(moduleDef, blockRow):
            continue
        legacyBase = expandNewModulePath(legacyDef, blockRow["dir"],
                                         blockRow["block"], blockRow["block"],
                                         layout, missingDirOk=True)
        hPath = legacyBase + ".h"
        cppPath = legacyBase + ".cpp"
        # Idempotent: a block whose legacy pair is gone is already ported.
        if not (os.path.exists(hPath) and os.path.exists(cppPath)):
            continue

        blockName = blockRow["block"]
        location = os.path.relpath(cppPath, layout["root"])
        cppmPath = expandNewModulePath(moduleDef, blockRow["dir"], blockName,
                                       blockName, layout, missingDirOk=True) + ".cppm"
        cppmReady = os.path.exists(cppmPath) and _isGenerated(cppmPath)
        noCppmMsg = (f"block '{blockName}' has a legacy .h/.cpp but no generated "
                     f"{os.path.basename(cppmPath)}; run `make newmodule` + `make gen` first")

        # Reg-handlers and apbDecode routers carry no user code: every member,
        # ctor init-list, and body sits inside a generated region, so `make gen`
        # repopulates the .cppm in full. Migrate deletes the legacy pair rather
        # than transplanting (nothing to move) or flagging (nothing to hand-port).
        # A reg-handler stays a reg-handler even when parameterized, so this
        # precedes the hasOwnParams flag. addressBlock is the router's own schema
        # field, the same signal getBDAddressDecode reads to set isApbRouter.
        isDecoder = bool(blockRow.get("addressBlock"))
        if blockRow["isRegHandler"] or isDecoder:
            if not cppmReady:
                report.manual.append(ReportItem(TODO_PORT_NO_CPPM, location, noCppmMsg))
                continue
            kind = "reg-handler" if blockRow["isRegHandler"] else "apbDecode router"
            report.applied.append(ReportItem(
                BLOCK_REGEN, location,
                f"block '{blockName}' is a {kind} (100% generated); deleted its "
                f"legacy .h/.cpp so `make gen` recreates {os.path.basename(cppmPath)}"))
            if write:
                os.remove(hPath)
                os.remove(cppPath)
                wrote = True
            continue

        # A parameterized block's templatization (T2) is semantic; leave it.
        if bool(prj.getBlockConfigView(blockRow["blockKey"])["hasOwnParams"]):
            report.manual.append(ReportItem(
                TODO_PORT_PARAM, location,
                f"block '{blockName}' is parameterized; templatize (T2) and port "
                f"its .h/.cpp by hand"))
            continue

        if not cppmReady:
            report.manual.append(ReportItem(TODO_PORT_NO_CPPM, location, noCppmMsg))
            continue

        # A gen-filled .cppm carries every region the transplant anchors on. One that
        # has lost a region would fault inside _buildPorted mid-loop, after earlier
        # blocks had already been written and their legacy pairs deleted; report it.
        cppmText = _read(cppmPath)
        missing = _missingRegions(cppmText, BLOCK_SHAPE)
        if missing:
            report.manual.append(ReportItem(
                TODO_PORT_TARGET_DAMAGED, location,
                f"{os.path.basename(cppmPath)} is missing the region(s) "
                f"{', '.join(missing)}; delete it and re-scaffold with "
                f"`make newmodule`, then `make gen`"))
            continue

        childHeaders = {allBlockHeaders[key]
                        for key in childKeys.get(blockRow["blockKey"], set())
                        if key in allBlockHeaders}
        # The file's own header is dropped alongside the family's framework
        # prerequisites. Taken from the fileMap-resolved legacy path, never
        # composed from the block name.
        dropIncludes = BLOCK_SHAPE.dropIncludes + (os.path.basename(hPath),)
        slots = _extractSlots(_read(hPath), _read(cppPath), BLOCK_SHAPE,
                              dropIncludes, siblingModules, childHeaders)
        if slots.hostileLib is not None:
            report.manual.append(ReportItem(
                TODO_PORT_HOSTILE_LIB, location,
                f"block '{blockName}' includes module-hostile header "
                f"'{slots.hostileLib}'; confine it (pimpl / non-module) by hand"))
            continue
        if slots.slot0Flags:
            report.manual.append(ReportItem(
                TODO_PORT_SLOT0, location,
                f"block '{blockName}' has non-boilerplate top-of-file content the "
                f"port cannot place ({slots.slot0Flags[0]!r}); port it by hand"))
            continue

        # No-silent-loss guard: prove the four-slot extraction placed every
        # code-bearing line of the legacy pair before deleting it. A brace-finder
        # miss that dropped a slot surfaces here as unaccounted code, so the port
        # HARD-ERRORS (leaving the legacy pair intact) instead of losing user code.
        misses = _verifyNoLoss(slots, BLOCK_SHAPE, dropIncludes)
        if misses:
            srcByTag = {"h": os.path.basename(hPath), "cpp": os.path.basename(cppPath)}
            tag, lineNo, text = misses[0]
            report.manual.append(ReportItem(
                TODO_PORT_UNPLACED, _loc(srcByTag[tag], lineNo),
                f"block '{blockName}': the port could not place {len(misses)} "
                f"source line(s); first unplaced at {srcByTag[tag]}:{lineNo}: "
                f"{text!r}. Refusing to delete the legacy pair (extraction miss — "
                f"fix the slot boundaries, do not lose this code)"))
            continue

        # The block's interface-context imports (the ones a method body may spell
        # unqualified, e.g. tag_st / NUM_TAGS) are re-emitted by the generator into
        # the classDecl-region head in module mode, mirroring classic .h/.cpp mode
        # — so the port is a pure four-slot transplant and adds no imports itself.
        portedText = _buildPorted(cppmText, slots, BLOCK_SHAPE)
        report.applied.append(ReportItem(
            BLOCK_PORTED, location,
            f"ported {blockName}.h/.cpp into {os.path.basename(cppmPath)} and "
            f"deleted the legacy pair"))
        if write:
            _write(cppmPath, portedText)
            os.remove(hPath)
            os.remove(cppPath)
            wrote = True

    report.written = wrote
    return report


# The file-level parameter that routes the testbench templates to their
# module-mode branches (fileGen.py `_tb_param_line`). Appended to the legacy
# argument tail the port carries across; a legacy `.h`/`.cpp` never carries it.
MODULE_MODE_PARAM = "--mode=module"

# Regions the transplant anchors on, per shape: (template, section) of the GMF, the
# export preamble, the class, and the two constructor sections. A target missing any
# of them cannot be transplanted, so the driver reports it instead of letting
# `_buildPorted` fault on a None region.
def _missingRegions(cppmText, shape):
    """The `--template=[ --section=]` names of the target regions `_buildPorted`
    needs that `cppmText` does not carry. Empty when the target is complete."""
    regions = _regions(cppmText)
    wanted = [("moduleScaffold", shape.gmfSection), ("moduleExport", None),
              (shape.classTemplate, shape.classSection),
              (shape.ctorTemplate, "init"), (shape.ctorTemplate, "body")]
    return [f"--template={t}" + (f" --section={s}" if s else "")
            for t, s in wanted if _find(regions, t, s) is None]


def portTbExternals(prj, write=False):
    """Merge every owned testbench External's legacy `.h`/`.cpp` pair into its
    scaffolded `<block>External.cppm`, carrying the legacy GENERATED_CODE_PARAM
    across, and delete the pair. Returns a BlockPortReport.

    Runs BETWEEN `make newmodule` and `make gen`. The scaffold already carries every
    region marker the transplant anchors on (empty regions), and the PARAM retarget
    has to be in place before gen fills them: the External's `--block` is routinely
    retargeted by hand at the `_tb` container with `--excludeInst=<dut>`, which a
    fresh scaffold seeds as the bare DUT, so a gen run against the un-retargeted line
    would emit an External for the wrong block.

    Owner-gated and idempotent (a block whose legacy pair is already gone is a
    no-op)."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = BlockPortReport(projectName=projectName)
    legacyDef = LEGACY_FILEMAP["tbExternal"]
    moduleDef = prj.filemap["tbExternal"]
    layout = prj.projectLayout[projectName]
    wrote = False

    for blockRow in prj.data["blocks"].values():
        if prj.contextOwningProject[blockRow["_context"]] != projectName:
            continue
        if not fileMapCondMatch(moduleDef, blockRow):
            continue
        blockName = blockRow["block"]
        legacyBase = expandNewModulePath(legacyDef, blockRow["dir"], blockName,
                                         blockName, layout, missingDirOk=True)
        hPath = legacyBase + ".h"
        cppPath = legacyBase + ".cpp"
        if not (os.path.exists(hPath) and os.path.exists(cppPath)):
            continue

        location = os.path.relpath(cppPath, layout["root"])
        cppmPath = expandNewModulePath(moduleDef, blockRow["dir"], blockName,
                                       blockName, layout, missingDirOk=True) + ".cppm"
        if not (os.path.exists(cppmPath) and _isGenerated(cppmPath)):
            report.manual.append(ReportItem(
                TODO_PORT_NO_CPPM, location,
                f"block '{blockName}' has a legacy External .h/.cpp but no "
                f"scaffolded {os.path.basename(cppmPath)}; run `make newmodule` first"))
            continue

        hText = _read(hPath)
        cppText = _read(cppPath)
        cppmText = _read(cppmPath)

        # The `--block`/`--excludeInst`/`--variant` selection is a documented user
        # edit carried on BOTH legacy files. They must agree, or the port cannot tell
        # which one the user meant; that is a judgment call, not a default.
        hTail = paramTail(hText)
        cppTail = paramTail(cppText)
        if hTail is None or cppTail is None:
            report.manual.append(ReportItem(
                TODO_PORT_NO_PARAM_LINE, location,
                f"block '{blockName}': legacy External is missing its "
                f"{PARAM_MARKER} line "
                f"({'.h' if hTail is None else '.cpp'}); the port carries that line "
                f"across, so restore it by hand, then re-run"))
            continue
        if hTail != cppTail:
            report.manual.append(ReportItem(
                TODO_PORT_PARAM_SPLIT, location,
                f"block '{blockName}': legacy External {PARAM_MARKER} lines "
                f"disagree ({hTail!r} in .h vs {cppTail!r} in .cpp); reconcile them "
                f"by hand, then re-run"))
            continue
        # The tail is carried VERBATIM, so a `--variant=` in it lands on the target
        # unexamined. Migration can rename or retire a variant, and stamping one the
        # block no longer declares makes the next `gen` fail (or, on a block whose
        # variant is only an instanceFactory key, silently select the wrong DUT
        # configuration). Only the variant token is validated: the rest of the tail —
        # `--block=<blk>_tb --excludeInst=<dut>` — is a documented user retarget and
        # legitimate as written.
        carriedVariant = paramVariant(hText)
        declared = _generatorValidatedVariants(prj, blockRow, hTail)
        if (carriedVariant is not None and declared is not None
                and carriedVariant not in declared):
            report.manual.append(ReportItem(
                TODO_PORT_STALE_VARIANT, location,
                f"block '{blockName}': the legacy External {PARAM_MARKER} line "
                f"carries DUT variant {carriedVariant!r}, which the block no longer "
                f"declares (declared: {', '.join(declared) if declared else 'none'}). "
                f"The tail is carried across verbatim, so stamping it would make "
                f"`make gen` resolve the wrong config or fail; the legacy pair is "
                f"left in place. Decide which variant this testbench drives, correct "
                f"`--variant=<name>` on both legacy files, then re-run"))
            continue
        # A scaffold always emits a PARAM line and every region the transplant
        # anchors on, so a target lacking either has been damaged. Both are checked
        # up front: the retarget is a silent no-op on a file with no PARAM line
        # (gen would then render the External with no --block at all), and a missing
        # region would fault mid-loop instead of reporting.
        missing = _missingRegions(cppmText, TB_EXTERNAL_SHAPE)
        if paramTail(cppmText) is None or missing:
            detail = (f"is missing the region(s) {', '.join(missing)}" if missing
                      else f"carries no {PARAM_MARKER} line to retarget")
            report.manual.append(ReportItem(
                TODO_PORT_TARGET_DAMAGED, location,
                f"{os.path.basename(cppmPath)} {detail}; delete it and re-scaffold "
                f"with `make newmodule`"))
            continue

        # An External's top-of-file span is a closed boilerplate set in every
        # measured instance, so there is no sibling-block or contained-child header
        # to convert: a genuinely external header simply relocates to the GMF slot,
        # which is the placement that preserves the global-module attachment it
        # already had as a plain header/TU include.
        dropIncludes = TB_EXTERNAL_SHAPE.dropIncludes + (os.path.basename(hPath),)
        slots = _extractSlots(hText, cppText, TB_EXTERNAL_SHAPE, dropIncludes,
                              dict(), set())
        if slots.hostileLib is not None:
            report.manual.append(ReportItem(
                TODO_PORT_HOSTILE_LIB, location,
                f"block '{blockName}' External includes module-hostile header "
                f"'{slots.hostileLib}'; confine it (pimpl / non-module) by hand"))
            continue
        if slots.slot0Flags:
            report.manual.append(ReportItem(
                TODO_PORT_SLOT0, location,
                f"block '{blockName}' External has non-boilerplate top-of-file "
                f"content the port cannot place ({slots.slot0Flags[0]!r}); a stray "
                f"`import` has to go in the `// user imports here` slot and a "
                f"declaration in the class or module purview — place it by hand"))
            continue

        # No-silent-loss guard: prove the extraction placed every code-bearing line
        # of the legacy pair before deleting it. A boundary miss that dropped a
        # slot surfaces here as unaccounted code, so the port refuses rather than
        # losing user code.
        misses = _verifyNoLoss(slots, TB_EXTERNAL_SHAPE, dropIncludes)
        if misses:
            srcByTag = {"h": os.path.basename(hPath), "cpp": os.path.basename(cppPath)}
            tag, lineNo, text = misses[0]
            report.manual.append(ReportItem(
                TODO_PORT_UNPLACED, _loc(srcByTag[tag], lineNo),
                f"block '{blockName}' External: the port could not place "
                f"{len(misses)} source line(s); first unplaced at "
                f"{srcByTag[tag]}:{lineNo}: {text!r}. Refusing to delete the legacy "
                f"pair (extraction miss — fix the slot boundaries, do not lose this "
                f"code)"))
            continue

        portedText = _buildPorted(cppmText, slots, TB_EXTERNAL_SHAPE)
        # (True, None) means the line already reads the retargeted tail (the sentinel
        # path, where the scaffold's seeded `--block=<dut>` is already correct).
        _, retargeted = restampParamLine(portedText, f"{hTail} {MODULE_MODE_PARAM}")
        if retargeted is not None:
            portedText = retargeted
        report.applied.append(ReportItem(
            TB_EXTERNAL_PORTED, location,
            f"merged {os.path.basename(hPath)}/{os.path.basename(cppPath)} into "
            f"{os.path.basename(cppmPath)} ({PARAM_MARKER} carried across as "
            f"`{hTail} {MODULE_MODE_PARAM}`) and deleted the legacy pair"))
        if write:
            _write(cppmPath, portedText)
            os.remove(hPath)
            os.remove(cppPath)
            wrote = True

    report.written = wrote
    return report


def _generatorValidatedVariants(prj, blockRow, tail):
    """The declared variant set the GENERATOR will check a carried `--variant=`
    against, or None when it checks nothing.

    Mirrors the real resolution rather than assuming it. `systemcGen` resolves the
    block view from the file's OWN `--block=` argument
    (`prj.getQualBlock(self.code.block)`), and
    `intf_gen_utils.resolve_dut_variant_selection` then rejects a `--variant=` that is
    not in that block's declared variant set — but ONLY when that block has own
    `params:`; without them it early-returns and passes the variant straight through
    as the instanceFactory key, unchecked. Both conditions are therefore skips here,
    because refusing either would refuse a migration `make gen` accepts:

      * the tail retargets `--block=` away from the block being ported (the `_tb`
        container an External is routinely pointed at), so this block's variants are
        not the ones resolved against;
      * that block has no own `params:` (`xif_tb` is parameterizable transitively yet
        owns none), so nothing is resolved at all.

    `getQualBlockVariants` is the declared set the generator compares against: its
    labels are identical to the `variantConfigs` descriptors
    `resolve_dut_variant_selection` reads, both being the block's declared variants.
    """
    if f"--block={blockRow['block']}" not in tail.split():
        return None
    if not prj.getBlockConfigView(blockRow["blockKey"])["hasOwnParams"]:
        return None
    return prj.getQualBlockVariants(blockRow["blockKey"])


def portTbTops(prj, write=False):
    """Carry each owned testbench top's legacy DUT `--variant=` selection onto its
    scaffolded `<block>Testbench.cppm`, then delete the legacy `.h`/`.cpp` pair.
    Returns a BlockPortReport.

    The tb top is the one member of the testbench family with NO user code slots to
    transplant — measured across every instance in base, pro and the isp workspace,
    every slot is empty — so `make gen` recreates the module unit in full. Its
    file-level GENERATED_CODE_PARAM line is not generated content though: the
    `--variant=` there selects which DUT variant this testbench drives and is a user
    edit, while a create-only re-scaffold seeds the block's first declared variant.
    Deleting the pair without carrying that value would silently point the testbench
    at another variant, so the carry happens here (same place, and for the same
    reason, portTbExternals carries the External's whole tail) and the delete only
    follows a successful stamp.

    Only the `--variant` argument is carried. The rest of the legacy tail is
    `--block=<dut>`, which a fresh scaffold already seeds correctly for the tb top —
    unlike the External, whose `--block` is routinely retargeted by hand.

    Refuses, leaving the legacy pair on disk and the target untouched, when the
    value cannot be carried safely: the legacy line holds an argument beyond the
    `--block=<dut>` a fresh scaffold writes anyway (so carrying only the variant
    would drop it), the two legacy files name different variants (which the user
    meant is a judgment call), or the named variant is not among the block's
    DECLARED variants — migration may have renamed or removed it, and stamping a
    variant the block no longer has makes the next `gen` resolve the wrong config or
    fail. A pair naming no variant at all, or carrying no PARAM line, has nothing to
    carry and is simply deleted.

    Runs in `--port-tb`, between `make newmodule` and `make gen`: the scaffold has
    to exist before its line can be stamped, and the stamp has to be in place before
    gen renders the file. Owner-gated and idempotent (a block whose legacy pair is
    already gone is a no-op)."""
    projectName = prj.config.getConfig("PROJECTNAME")
    report = BlockPortReport(projectName=projectName)
    legacyDef = LEGACY_FILEMAP["testBench"]
    moduleDef = prj.filemap["testBench"]
    layout = prj.projectLayout[projectName]
    wrote = False

    for blockRow in prj.data["blocks"].values():
        if prj.contextOwningProject[blockRow["_context"]] != projectName:
            continue
        if not fileMapCondMatch(moduleDef, blockRow):
            continue
        blockName = blockRow["block"]
        legacyBase = expandNewModulePath(legacyDef, blockRow["dir"], blockName,
                                         blockName, layout, missingDirOk=True)
        legacyPaths = [f"{legacyBase}.{ext}" for ext in legacyDef["ext"].values()]
        # A half-present pair is deliberately accepted (the External requires both):
        # there is no slot transplant that needs the missing file, and leaving one
        # orphan of the pair behind is worse than removing what is there.
        present = [p for p in legacyPaths if os.path.exists(p)]
        if not present:
            continue
        location = os.path.relpath(present[0], layout["root"])

        targetBase = expandNewModulePath(moduleDef, blockRow["dir"], blockName,
                                         blockName, layout, missingDirOk=True)
        targets = [f"{targetBase}.{ext}" for ext in moduleDef["ext"].values()]
        absent = [p for p in targets if not (os.path.exists(p) and _isGenerated(p))]
        if absent:
            report.manual.append(ReportItem(
                TODO_PORT_NO_CPPM, location,
                f"block '{blockName}' has a legacy Testbench .h/.cpp but no "
                f"scaffolded {os.path.basename(absent[0])}; run `make newmodule` "
                f"first"))
            continue

        # No-silent-loss guard on the tail. Only `--variant` is carried, so every
        # other argument the legacy line holds has to be one the fresh scaffold
        # writes anyway — for the tb top that is `--block=<dut>` alone. Anything
        # else is a hand edit the carry would drop without a trace (a retargeted
        # `--block`, an `--excludeInst`, or a space-spelled `--variant v`, which
        # reads here as two unaccounted tokens rather than as a selection).
        texts = [_read(p) for p in present]
        # One token stream over both legacy files: which of the pair carries the line
        # does not change what the pair as a whole selects, and the split check below
        # covers the case where they disagree.
        legacyTail = " ".join(paramTail(text) or "" for text in texts)
        unaccounted = sorted({tok for tok in legacyTail.split()
                              if tok != f"--block={blockName}"
                              and not tok.startswith("--variant=")})
        if unaccounted:
            report.manual.append(ReportItem(
                TODO_PORT_TAIL_UNPLACED, location,
                f"block '{blockName}': the legacy Testbench {PARAM_MARKER} line "
                f"carries argument(s) the port does not account for "
                f"({', '.join(repr(t) for t in unaccounted)}); it carries only "
                f"`--variant=<name>` across, so these would be lost. Put them on the "
                f"{PARAM_MARKER} line of "
                f"{', '.join(os.path.basename(p) for p in targets)} by hand, then "
                f"delete {', '.join(os.path.basename(p) for p in present)}"))
            continue

        selected = sorted({v for v in (paramVariant(text) for text in texts)
                           if v is not None})
        if len(selected) > 1:
            report.manual.append(ReportItem(
                TODO_PORT_PARAM_SPLIT, location,
                f"block '{blockName}': the legacy Testbench {PARAM_MARKER} lines "
                f"name different DUT variants "
                f"({', '.join(repr(v) for v in selected)}), so the port cannot tell "
                f"which the user meant; make the two lines agree, then re-run"))
            continue
        # Same membership rule as the External path. The tail-accounting guard above
        # has already established that any `--block=` here names this block, so only
        # the own-params condition can skip the check.
        declared = _generatorValidatedVariants(prj, blockRow, legacyTail)
        if selected and declared is not None and selected[0] not in declared:
            report.manual.append(ReportItem(
                TODO_PORT_STALE_VARIANT, location,
                f"block '{blockName}': the legacy Testbench selects DUT variant "
                f"{selected[0]!r}, which the block no longer declares "
                f"(declared: {', '.join(declared) if declared else 'none'}). "
                f"Carrying it would make `make gen` resolve the wrong config or "
                f"fail, so the legacy pair is left in place. Decide which variant "
                f"this testbench drives, set `--variant=<name>` on the "
                f"{PARAM_MARKER} line of "
                f"{', '.join(os.path.basename(p) for p in targets)}, then delete "
                f"{', '.join(os.path.basename(p) for p in present)}"))
            continue

        # Write before delete, as the block/External ports do: the value has to be
        # safely on the target before its only other copy goes away. `stamped` stays
        # empty when there is nothing to carry, and an already-correct target is an
        # idempotent no-op (restampParamLine returns no new text).
        stamped = dict()
        damaged = None
        for path in targets if selected else []:
            text = _read(path)
            tail = paramTail(text)
            if tail is None:
                damaged = (path, f"carries no {PARAM_MARKER} line to carry the "
                                 f"legacy DUT variant onto")
                break
            newTail = replaceParamVariant(tail, selected[0])
            if newTail is None:
                damaged = (path, f"carries no {PARAM_MARKER} `--variant=` argument "
                                 f"for the legacy selection {selected[0]!r} to "
                                 f"replace")
                break
            _, newText = restampParamLine(text, newTail)
            if newText is not None:
                stamped[path] = newText
        if damaged is not None:
            path, detail = damaged
            report.manual.append(ReportItem(
                TODO_PORT_TARGET_DAMAGED, location,
                f"{os.path.basename(path)} {detail}; delete it and re-scaffold with "
                f"`make newmodule`"))
            continue

        carried = (f"carried {PARAM_MARKER} --variant={selected[0]} onto "
                   f"{', '.join(os.path.basename(p) for p in targets)} and "
                   if selected else "")
        report.applied.append(ReportItem(
            TB_TOP_PORTED, location,
            f"{carried}deleted the legacy pair "
            f"{', '.join(os.path.basename(p) for p in present)} "
            f"(the tb top holds no user code; gen recreates it in full)"))
        if write:
            for path, text in stamped.items():
                _write(path, text)
            for path in present:
                os.remove(path)
            wrote = True

    report.written = wrote
    return report


def renderBlockPortReport(report, write, label):
    lines = [f"=== {label} (.h/.cpp -> .cppm): {report.projectName} ==="]
    if not report.applied and not report.manual:
        lines.append("  no legacy .h/.cpp pairs to port; nothing to do")
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
