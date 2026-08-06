"""Mechanized `.cpp`/`.h` -> `.cppm` block-implementation port (item 5).

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
from pysrc.migrateCommon import _read, _write, _isGenerated, _loc
from pysrc.migrateOrphans import LEGACY_FILEMAP
from pysrc.processYaml import expandNewModulePath, fileMapCondMatch


# Applied-edit kinds.
BLOCK_PORTED = "BLOCK_PORTED"  # user block: four-slot transplant into the .cppm
BLOCK_REGEN = "BLOCK_REGEN"    # reg-handler / apbDecode router: legacy pair deleted, .cppm regenerated

# Manual-TODO kinds (block left un-ported, legacy pair untouched).
TODO_PORT_PARAM = "TODO_PORT_PARAM"            # parameterized block; templatize by hand (T2)
TODO_PORT_HOSTILE_LIB = "TODO_PORT_HOSTILE_LIB"  # module-hostile library in a user slot
TODO_PORT_SLOT0 = "TODO_PORT_SLOT0"            # non-boilerplate top-of-file content
TODO_PORT_NO_CPPM = "TODO_PORT_NO_CPPM"        # legacy pair present but no gen'd .cppm target
TODO_PORT_UNPLACED = "TODO_PORT_UNPLACED"      # no-silent-loss guard: source code the port could not place

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
# Marker-region walk (shared shape for source and target files)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Region:
    command: str   # raw text after GENERATED_CODE_BEGIN, e.g. "--template=classDecl"
    begin: int     # 0-based line index of the BEGIN line
    end: int       # 0-based line index of the matching END line


def _regions(text):
    """Ordered generated regions of a marker file as Region(command, begin, end),
    0-based line indices of each GENERATED_CODE_BEGIN and its matching END."""
    regions = []
    begin = None
    command = None
    for i, line in enumerate(text.splitlines()):
        if "GENERATED_CODE_BEGIN" in line:
            begin = i
            command = line.split("GENERATED_CODE_BEGIN", 1)[1].strip()
        elif "GENERATED_CODE_END" in line and begin is not None:
            regions.append(Region(command, begin, i))
            begin = None
            command = None
    return regions


def _find(regions, template, section=None):
    """The region whose command names `--template={template}` (and, when given,
    `--section={section}`), or None."""
    for r in regions:
        if f"--template={template}" not in r.command:
            continue
        if section is not None and f"--section={section}" not in r.command:
            continue
        return r
    return None


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


def _includeTarget(stripped):
    """The included header of an `#include "X"` / `#include <X>` line, or None."""
    if not stripped.startswith("#include"):
        return None
    rest = stripped[len("#include"):].strip()
    if len(rest) >= 2 and rest[0] in "\"<":
        close = "\"" if rest[0] == "\"" else ">"
        end = rest.find(close, 1)
        if end > 0:
            return rest[1:end]
    return None


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


def _classifyTopOfFile(topLines, blockName, guardSet, siblingModules, childHeaders, slots):
    """Classify a top-of-file (slot-0) span: drop boilerplate (copyright/marker
    comments, the include guard, `#include "systemc.h"`, the `.cpp`'s own
    `#include "<block>.h"`), convert a sibling-block header include to a module
    import (dropping it when the sibling is a contained instance the generator
    already auto-imports), collect a genuinely external `#include` for the GMF
    slot, and record anything else as an unplaceable flag. `guardSet` carries the
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
            if header == "systemc.h" or header == f"{blockName}.h":
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


def _extractSlots(hText, cppText, blockName, siblingModules, childHeaders):
    """Extract the four user slots (plus relocated includes/imports and flags) from
    the legacy `.h`/`.cpp` pair, keyed off the GENERATED_CODE markers."""
    slots = LegacySlots()

    # Header: class-body members between the classDecl END and the class `};`.
    hLines = hText.splitlines()
    slots.hLines = hLines
    hRegions = _regions(hText)
    for r in hRegions:                                 # dropped generated regions
        slots.hAccounted.update(range(r.begin, r.end + 1))
    hGuard = _guardLineSet(hLines)                     # dropped include guard
    slots.hAccounted.update(hGuard)
    cls = _find(hRegions, "classDecl")
    if cls is not None:
        _classifyTopOfFile(hLines[:cls.begin], blockName, hGuard,
                           siblingModules, childHeaders, slots)
        slots.hAccounted.update(range(0, cls.begin))   # slot0 (classifier-walked)
        classClose = _firstClosingBrace(hLines, cls.end + 1)
        body = hLines[cls.end + 1:classClose] if classClose is not None else []
        slots.classBody = _trimScaffold(body)
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
    ini = _find(cRegions, "constructor", "init")
    bod = _find(cRegions, "constructor", "body")
    if ini is not None and bod is not None:
        _classifyTopOfFile(cLines[:ini.begin], blockName, cGuard,
                           siblingModules, childHeaders, slots)
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


def _trimScaffold(lines):
    """Drop the scaffold `// block implementation members` comment (the target
    already carries it) and blank ends from a class-body span."""
    kept = [ln for ln in lines if ln.strip() != _IMPL_MEMBERS_COMMENT]
    return _stripBlankEnds(kept)


def _stripBlankEnds(lines):
    out = list(lines)
    while out and out[0].strip() == "":
        out.pop(0)
    while out and out[-1].strip() == "":
        out.pop()
    return out


# ---------------------------------------------------------------------------
# No-silent-loss guard
# ---------------------------------------------------------------------------

def _noCodeMask(lines):
    """Per-line booleans: True where the line carries no code — it is whitespace
    or lies entirely inside a comment. Tracks `//` line comments and multi-line
    `/* */` block comments across the whole file so a residual line inside a
    block comment opened earlier is correctly seen as code-free.

    Not string-literal aware: a `//` or `/*` inside a string reads as a comment
    start. That can only make a line look MORE comment-like, never less — any such
    marker is preceded in its line by the opening quote, which is itself code, so
    a line holding real code is never mis-seen as code-free. This is sufficient for
    the guard, whose only question is whether a residual line bears code at all."""
    inBlock = False
    mask = []
    for line in lines:
        hasCode = False
        i = 0
        n = len(line)
        while i < n:
            if inBlock:
                if line[i] == "*" and i + 1 < n and line[i + 1] == "/":
                    inBlock = False
                    i += 2
                    continue
                i += 1
                continue
            if line[i] == "/" and i + 1 < n and line[i + 1] == "/":
                break                                  # line comment: rest is comment
            if line[i] == "/" and i + 1 < n and line[i + 1] == "*":
                inBlock = True
                i += 2
                continue
            if not line[i].isspace():
                hasCode = True
            i += 1
        mask.append(not hasCode)
    return mask


def _unplacedLines(lines, accounted, blockName):
    """The (1-based lineNo, stripped text) of every source line the extraction did
    NOT account for that still carries code. A line is accounted when it is in
    `accounted` (dropped generated region, dropped include guard, classifier-walked
    slot0, a captured slot span, or a structural closer); the residual must be
    whitespace, comment, or a recognized boilerplate line the port intentionally
    drops (`#include "systemc.h"` or the block's own `#include "<block>.h"`).
    Anything else is code the port would silently lose."""
    noCode = _noCodeMask(lines)
    unplaced = []
    for i, line in enumerate(lines):
        if i in accounted or noCode[i]:
            continue
        s = line.strip()
        if _includeTarget(s) in ("systemc.h", f"{blockName}.h"):
            continue
        unplaced.append((i + 1, s))
    return unplaced


def _verifyNoLoss(slots, blockName):
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
        for lineNo, text in _unplacedLines(lines, accounted, blockName):
            misses.append((tag, lineNo, text))
    return misses


# ---------------------------------------------------------------------------
# Transplant into the generated .cppm
# ---------------------------------------------------------------------------

def _asLines(rawLines):
    return [ln + "\n" for ln in rawLines]


def _buildPorted(cppmText, slots):
    """Return the `.cppm` text with the four user slots transplanted into their
    marker-delimited target gaps, plus the relocated GMF includes. Insertions are
    applied bottom-to-top so earlier line indices stay valid."""
    lines = cppmText.splitlines(keepends=True)
    regions = _regions(cppmText)
    hdr = _find(regions, "moduleScaffold", "blockModuleHeader")
    exp = _find(regions, "moduleExport")
    cls = _find(regions, "classDecl")
    ini = _find(regions, "constructor", "init")
    bod = _find(regions, "constructor", "body")

    inserts = []  # list[(index, [lines])] — insert before `index`

    if slots.userIncludes:
        inserts.append((hdr.end + 1, _asLines(slots.userIncludes)))

    # Sibling-block imports belong in the module purview (after `export module`
    # and the generated imports), not the GMF — imports must precede any other
    # module-purview declaration. Insert on the line AFTER the `// user imports
    # here` GMF label (which the generator emits immediately after the
    # moduleExport region, at exp.end + 1) so they read as belonging under their
    # label, still ahead of the classDecl region's `using namespace`.
    if slots.siblingImports:
        inserts.append((exp.end + 2, _asLines(slots.siblingImports)))

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

        childHeaders = {allBlockHeaders[key]
                        for key in childKeys.get(blockRow["blockKey"], set())
                        if key in allBlockHeaders}
        slots = _extractSlots(_read(hPath), _read(cppPath), blockName,
                              siblingModules, childHeaders)
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
        misses = _verifyNoLoss(slots, blockName)
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
        cppmText = _read(cppmPath)
        portedText = _buildPorted(cppmText, slots)
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


def renderBlockPortReport(report, write):
    lines = [f"=== block module port (.h/.cpp -> .cppm): {report.projectName} ==="]
    if not report.applied and not report.manual:
        lines.append("  no legacy .h/.cpp block pairs to port; nothing to do")
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
