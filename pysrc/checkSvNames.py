#!/usr/bin/env python3
"""Check that every SV module and package name equals its file stem.

Usage: checkSvNames.py <project_dir> [<project_dir> ...]

Scans every .sv and .svh file below each project directory, in either layout.
Build output (.gen, build, obj_dir) is skipped.

Rules:
- The first `module <name>` or `package <name>` in a file must equal the file
  stem. An .svh that declares neither is an include-only file and is skipped.
- A later design unit in the same file must be a pair top,
  `p<N>_<parent>_c<M>_<child><tail>`, where N and M are the lengths of
  <parent> and <child>, and <tail> ends the file stem. The generator writes
  these beside the variant top that shares the file.
- Every `endmodule : <label>` or `endpackage : <label>` must name a unit the
  same file declares, so a label left stale by a rename fails.

Comments are stripped first, so a commented-out declaration does not count.
Exits 1 and lists every mismatch, or exits 0 when there are none.
"""

import os
import re
import sys

SKIP_DIRS = {".gen", "build", "obj_dir", "__pycache__"}
DECL_RE = re.compile(r"^\s*(module|package)\s+(?:automatic\s+|static\s+)?([A-Za-z_]\w*)", re.M)
ENDLABEL_RE = re.compile(r"\b(endmodule|endpackage)\s*:\s*([A-Za-z_]\w*)")
PAIR_TOP_RE = re.compile(r"^p(\d+)_(.*)$")
PAIR_CHILD_RE = re.compile(r"^c(\d+)_(.*)$")


def stripComments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def isPairTop(name, stem):
    m = PAIR_TOP_RE.match(name)
    if not m:
        return False
    parentLength, rest = int(m.group(1)), m.group(2)
    if len(rest) <= parentLength or rest[parentLength] != "_":
        return False
    m = PAIR_CHILD_RE.match(rest[parentLength + 1:])
    if not m:
        return False
    childLength, rest = int(m.group(1)), m.group(2)
    tail = rest[childLength:]
    return len(rest) > childLength and stem.endswith(tail)


def svFiles(projectDir):
    for root, dirs, names in os.walk(projectDir):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if name.endswith((".sv", ".svh")):
                yield os.path.join(root, name)


def checkFile(path):
    """Mismatch messages for one file, or None when it declares no unit."""
    stem = os.path.splitext(os.path.basename(path))[0]
    with open(path, errors="replace") as f:
        text = stripComments(f.read())
    decls = DECL_RE.findall(text)
    if not decls:
        return None
    mismatches = list()
    kind, first = decls[0]
    if first != stem:
        mismatches.append(f"{kind} {first} != stem {stem}")
    for kind, name in decls[1:]:
        if kind == "module" and isPairTop(name, stem):
            continue
        mismatches.append(f"extra {kind} {name} is not a pair top for stem {stem}")
    declared = {name for _, name in decls}
    for kind, label in ENDLABEL_RE.findall(text):
        if label not in declared:
            mismatches.append(f"{kind} label {label} names no unit declared in this file")
    return mismatches


def checkProject(projectDir):
    """Return (checked, includeOnly, mismatches) for one project directory;
    includeOnly and mismatches hold paths relative to projectDir."""
    checked = 0
    includeOnly = list()
    mismatches = list()
    for path in svFiles(projectDir):
        rel = os.path.relpath(path, projectDir)
        found = checkFile(path)
        if found is None:
            includeOnly.append(rel)
            continue
        checked += 1
        mismatches += [f"{rel}: {m}" for m in found]
    return checked, includeOnly, mismatches


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    failed = False
    for projectDir in argv:
        checked, includeOnly, mismatches = checkProject(os.path.abspath(projectDir))
        print(f"checked {checked} files under {projectDir}")
        for rel in includeOnly:
            print(f"skipped (no module or package): {rel}")
        for line in mismatches:
            print(f"MISMATCH {line}")
        print(f"{len(mismatches)} mismatch(es)")
        failed = failed or bool(mismatches)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
