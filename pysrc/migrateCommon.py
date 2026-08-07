"""Shared text-only helpers for the standalone YAML migration modules.

The migration modules (migrateYaml, migrateIncludes, migrateAddressControl,
migrateLayout, migrateOrphans) run BEFORE the project database exists — they read
and rewrite the on-disk YAML/source as text and never open the DB. They had each
grown a private copy of the same file-IO, YAML-node, project-file-walk, and
generated-marker helpers, which drifted apart. This module is their single home
so every module shares one contract.

Reading raw user YAML with `.get()` / `or {}` is correct here: the input is
pre-database user text that has not yet passed any validation gate.
"""

import os
import re
from dataclasses import dataclass

import yaml


# Build/output subtrees never walked when sweeping a project tree. `builder` is
# the vendored toolchain dir (this generator's own source), never project code.
SKIP_DIRS = ("build", ".gen", "obj_dir", ".git", "rundir", "builder")

# Generated/authored source file extensions. A file outside this set (Makefile,
# .f filelist, .gitignore) is build scaffolding the user manages, not generated
# source, and is left untouched by the migration sweeps.
SOURCE_EXTS = (".h", ".hpp", ".cpp", ".cc", ".cppm", ".sv", ".svh")

# Project-root build-config container (holds make/shared.mk etc). Not a fileMap
# segment; a user-owned root convention.
BUILD_CONFIG_DIR = "include"

# The two user-owned build makefiles, project-root-relative. Both stay at the
# project root under every layout, and between them they carry every EXTRA_*
# declaration — the only channel through which a project tells the build about a
# path the generator does not place. A pass that must know what the user declared
# reads exactly these.
HARNESS_MK = os.path.join(BUILD_CONFIG_DIR, "make", "shared.mk")
RUNDIR_MK = os.path.join("rundir", "Makefile")


# ---------------------------------------------------------------------------
# File IO
# ---------------------------------------------------------------------------

def _read(path):
    with open(path, "r") as fh:
        return fh.read()


def _write(path, text):
    with open(path, "w") as fh:
        fh.write(text)


def _loc(path, line):
    """Location tag for a report item: `basename:line` when a 1-based line is
    known, else the basename alone. Unified across all migration modules."""
    return f"{os.path.basename(path)}:{line}" if line else os.path.basename(path)


# ---------------------------------------------------------------------------
# GENERATED_CODE marker guard
# ---------------------------------------------------------------------------

def _isGenerated(path):
    """True when `path` carries the GENERATED_CODE_BEGIN marker the generator
    stamps into every in-place generated file. Deletion reuses this so a
    name-matched user file is never removed."""
    return "GENERATED_CODE_BEGIN" in _read(path)


def userRegionLines(text):
    """Yield `(lineIndex, lineText)` for every line OUTSIDE a generated region,
    tracking the GENERATED_CODE_BEGIN/END marker contract (the marker lines
    themselves are not yielded).

    A generated file is not uniformly generated: the spans between its regions
    are user purview. Content there is invisible to both halves of the toolchain
    — `make gen` rewrites only generated regions, and a migration pass that skips
    marker-carrying files wholesale never sees it — so a pass that must reach
    user content walks it through here rather than skipping the file."""
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


def classifyGeneratedDir(dirs):
    """Partition the SOURCE files found under each directory in `dirs` into
    `(generated, ungenerated)` by the GENERATED_CODE marker.

    Fully-generated segment directories (base, registrar, vl_wrap) hold only
    generated artifacts, so a migration sweep clears them by directory rather
    than by fileMap expansion — the marker (not a cond/ext/name gate) is the
    decider, so alternate-extension or renamed orphans a per-file expansion would
    miss (pre-`.cppm` `<block>Base.h`, model-only `<block>Tandem.*`, stale
    `*_hdl_sc_wrapper.h`) are still caught. `generated` files are safe to
    delete-and-regenerate; `ungenerated` files are surfaced for review and never
    deleted (a hand-authored file dropped into a generated segment is preserved).
    Non-source files (build scaffolding) are ignored. Missing directories are
    skipped."""
    generated = list()
    ungenerated = list()
    for directory in sorted(dirs):
        if not os.path.isdir(directory):
            continue
        for root, dirnames, names in os.walk(directory):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in sorted(names):
                if not name.endswith(SOURCE_EXTS):
                    continue
                path = os.path.join(root, name)
                (generated if _isGenerated(path) else ungenerated).append(path)
    return generated, ungenerated


# ---------------------------------------------------------------------------
# Generated-region walk
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Region:
    command: str   # raw text after GENERATED_CODE_BEGIN, e.g. "--template=classDecl"
    begin: int     # 0-based line index of the BEGIN line
    end: int       # 0-based line index of the matching END line


def _regions(text):
    """Ordered generated regions of a marker file as Region(command, begin, end),
    0-based line indices of each GENERATED_CODE_BEGIN and its matching END.

    The counterpart of `userRegionLines`: that one yields the user spans, this one
    the generated ones with their commands, which is what a pass needs when it
    anchors an edit on a particular template/section rather than on file text."""
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
    """The FIRST region whose command names `--template={template}` (and, when
    given, `--section={section}`), or None."""
    for r in regions:
        if f"--template={template}" not in r.command:
            continue
        if section is not None and f"--section={section}" not in r.command:
            continue
        return r
    return None


# ---------------------------------------------------------------------------
# GENERATED_CODE_PARAM line
# ---------------------------------------------------------------------------

PARAM_MARKER = "GENERATED_CODE_PARAM"


def paramTail(text):
    """The argument tail of a file's GENERATED_CODE_PARAM line, or None when the
    file carries no such line."""
    for line in text.splitlines():
        pos = line.find(PARAM_MARKER)
        if pos >= 0:
            return line[pos + len(PARAM_MARKER):].strip()
    return None


# The DUT-variant argument of a PARAM line. The tail is an argv line, and argparse
# (textfileHelper.codeText.parseParam) accepts several spellings of it; the ONE
# recognized here is `--variant=<name>`, which is what every producer of the line
# writes (templates/fileGen/fileGen.py::_tb_variant_param). A caller that must not
# lose an unrecognized spelling has to reject the tail rather than read it, because
# an unrecognized spelling is indistinguishable here from no variant at all.
_VARIANT_ARG = "--variant"


def paramVariant(text):
    """The variant named by the `--variant=<name>` argument of a file's
    GENERATED_CODE_PARAM line, or None when the line names none (or the file
    carries no such line).

    `--variant` on a testbench artifact is a USER edit on an otherwise generated
    file: `make newmodule` seeds only the block's first declared variant, and the
    operator changes it to point a testbench at a different DUT variant. A migration
    pass that replaces such a file therefore reads the selection back here so it can
    carry it onto the replacement."""
    tail = paramTail(text)
    if tail is None:
        return None
    for token in tail.split():
        if token.startswith(_VARIANT_ARG + "="):
            return token[len(_VARIANT_ARG) + 1:] or None
    return None


def replaceParamVariant(tail, variant):
    """`tail` with its `--variant=` argument set to `variant`, or None when the tail
    carries no such argument to replace.

    Sets that one argument and leaves every other token — and their order —
    token-for-token as written (inter-token whitespace is normalized to one space,
    which is what every producer writes), so a line rewritten through here differs
    from what the scaffold emitted only in the value carried onto it. The scaffold always writes
    the `--variant=<name>` spelling, so returning None rather than appending an
    argument keeps the caller honest: a target that carries no `--variant` is not
    the shape a carry expects, which is a condition to report, not to patch."""
    tokens = tail.split()
    for i, token in enumerate(tokens):
        if token.startswith(_VARIANT_ARG + "="):
            tokens[i] = f"{_VARIANT_ARG}={variant}"
            return " ".join(tokens)
    return None


def restampParamLine(text, tail):
    """Rewrite the argument tail of the file's GENERATED_CODE_PARAM line to `tail`.
    The comment prefix and PARAM keyword are preserved; only the argument tail is
    replaced, so a re-stamped line is byte-identical to a fresh scaffold.

    Returns (hasParamLine, newText):
      (True, <text>)  the line was re-stamped to `tail`
      (True, None)    the line already reads exactly `tail` (idempotent no-op)
      (False, None)   the file carries NO GENERATED_CODE_PARAM line. The marker
                      guard (_isGenerated) only looks for GENERATED_CODE_BEGIN,
                      so a generated artifact can reach here without a PARAM
                      line; it cannot be re-stamped, and callers report it as
                      manual work rather than treating it as already correct."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        pos = line.find(PARAM_MARKER)
        if pos < 0:
            continue
        newline = "\n" if line.endswith("\n") else ""
        newLine = f"{line[:pos]}{PARAM_MARKER} {tail}{newline}"
        if newLine == line:
            return True, None
        lines[i] = newLine
        return True, "".join(lines)
    return False, None


# ---------------------------------------------------------------------------
# Source-line classification
# ---------------------------------------------------------------------------

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


def _importTarget(stripped):
    """The module name of an `import <name>;` declaration line, or None."""
    if not (stripped.startswith("import ") and stripped.endswith(";")):
        return None
    return stripped[len("import "):-1].strip()


def _noCodeMask(lines):
    """Per-line booleans: True where the line carries no code — it is whitespace
    or lies entirely inside a comment. Tracks `//` line comments and multi-line
    `/* */` block comments across the whole file so a residual line inside a
    block comment opened earlier is correctly seen as code-free.

    Not string-literal aware: a `//` or `/*` inside a string reads as a comment
    start. That can only make a line look MORE comment-like, never less — any such
    marker is preceded in its line by the opening quote, which is itself code, so
    a line holding real code is never mis-seen as code-free. This is sufficient for
    the no-loss guards that consume it, whose only question is whether a residual
    line bears code at all."""
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


def _stripBlankEnds(lines):
    """`lines` with leading and trailing blank lines removed."""
    out = list(lines)
    while out and out[0].strip() == "":
        out.pop(0)
    while out and out[-1].strip() == "":
        out.pop()
    return out


# ---------------------------------------------------------------------------
# Build-makefile scanning
# ---------------------------------------------------------------------------

# An EXTRA_* make-variable assignment, and a `$(REPO_ROOT)/<path>` reference
# within it. The WHOLE relative path is captured, not just its first component:
# callers need to know which segment the reference sits in, and a top-level
# component is ambiguous between siblings (`fw/src` vs an `fw/include` segment).
_EXTRA_VAR_RE = re.compile(r'^[ \t]*(EXTRA_\w+)[ \t]*[:+?]?=(?P<rhs>.*)$')
_REPO_ROOT_REF_RE = re.compile(r'\$\(REPO_ROOT\)/(?P<path>[^\s):]+)')


def foldedLines(text):
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


def extraVarRefs(projectRoot):
    """Yield (makefilePath, startLine, varName, ref) for every distinct
    `$(REPO_ROOT)/<ref>` reference inside an `EXTRA_*` assignment in the project's
    two build makefiles. `ref` is project-root-relative, posix-spelled, with any
    trailing slash stripped.

    Scanned per LOGICAL line, because a make list is written across
    backslash-continuations as soon as it holds more than one path; matching per
    physical line would see only the first and silently drop the rest. References
    are de-duplicated and sorted within one assignment, and every one is yielded —
    a single item per assignment would hide the other paths a continued list
    names."""
    for rel in (HARNESS_MK, RUNDIR_MK):
        path = os.path.join(projectRoot, rel)
        if not os.path.isfile(path):
            continue
        for line, logical in foldedLines(_read(path)):
            match = _EXTRA_VAR_RE.match(logical)
            if match is None:
                continue
            refs = sorted({r.group("path").rstrip("/")
                           for r in _REPO_ROOT_REF_RE.finditer(match.group("rhs"))})
            for ref in refs:
                yield path, line, match.group(1), ref


# ---------------------------------------------------------------------------
# YAML node helpers
# ---------------------------------------------------------------------------

def _topValueNode(root, key):
    """The value node of a top-level mapping `key`, or None."""
    if root is None:
        return None
    for keyNode, valNode in root.value:
        if keyNode.value == key:
            return valNode
    return None


# ---------------------------------------------------------------------------
# Project file-set discovery
# ---------------------------------------------------------------------------

def _includeList(text):
    data = yaml.safe_load(text) or {}
    return data.get("include") or []


def _projectFileSet(projectDir, projectData):
    """Ordered, de-duplicated list of project YAML files: the project.yaml
    `projectFiles:` entries plus everything reachable through their `include:`
    chains. Paths are resolved relative to the including file's directory."""
    files = []
    seen = set()
    queue = [os.path.join(projectDir, f) for f in projectData.get("projectFiles", [])]
    while queue:
        path = os.path.abspath(queue.pop(0))
        if path in seen:
            continue
        seen.add(path)
        files.append(path)
        for inc in _includeList(_read(path)):
            queue.append(os.path.join(os.path.dirname(path), inc))
    return files
