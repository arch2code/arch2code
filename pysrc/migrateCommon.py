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

import yaml


# Build/output subtrees never walked when sweeping a project tree. `builder` is
# the vendored toolchain dir (this generator's own source), never project code.
SKIP_DIRS = ("build", ".gen", "obj_dir", ".git", "rundir", "builder")

# Generated/authored source file extensions. A file outside this set (Makefile,
# .f filelist, .gitignore) is build scaffolding the user manages, not generated
# source, and is left untouched by the migration sweeps.
SOURCE_EXTS = (".h", ".hpp", ".cpp", ".cc", ".cppm", ".sv", ".svh")


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
