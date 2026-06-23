"""Converter from the legacy header-mode `include` context file type to the
C++20 `.cppm` module-interface file type (the includes phase of the unified YAML
migration).

A legacy project pins the `include` context file type to paired `.h`/`.cpp` in
its `project.yaml` `fileGeneration.fileMap`, overriding the base project's
`cppm` module-interface definition. This phase removes that override so the
project inherits the base `cppm` definition, and deletes the orphaned generated
context-include `.h`/`.cpp` files. The `.cppm` module interfaces are recreated
afterwards by `make newmodule`; `newmodule` itself never deletes — the deletion
of the superseded generated files lives here, in the migration code.

Standalone and text-only, like `migrateAddressControl`: it reads YAML as text
and never opens the project database. PyYAML supplies values and `yaml.compose`
supplies line/column marks for targeted edits.

Mechanical (applied automatically):
  - remove the `include` override line from `fileGeneration.fileMap`,
  - delete the orphaned generated `<context>Includes.{h,cpp}` files in the
    include base path. The firmware `<context>IncludesFW.{h,cpp}` files are left
    in place; firmware headers remain header-mode by design.

Reported and handed to the migration skill (not mechanical):
  - hand-written user code (a source file with no generated regions) that
    `#include`s a migrated `"<context>Includes.h"` header and must switch to
    `import <module>;`. The skill explains the import rewrite.

When the manual-TODO list is non-empty the project still builds only after the
skill resolves those user-code includes, so `clean` is False.
"""

import glob
import os
from dataclasses import dataclass, field

import yaml


# Applied-edit kinds.
INCLUDE_OVERRIDE_REMOVE = "INCLUDE_OVERRIDE_REMOVE"  # legacy include override line removed
STALE_FILE_DELETE = "STALE_FILE_DELETE"              # orphaned generated .h/.cpp deleted

# Manual-TODO kinds (delegated to the migration skill).
TODO_USER_IMPORT = "TODO_USER_IMPORT"  # user code #includes a migrated context header


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line (or file) of the edited / offending declaration
    message: str     # human-facing description


@dataclass
class IncludesReport:
    projectYaml: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        """True when nothing is left for the skill to resolve by hand."""
        return not self.manual


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def migrateIncludesInProject(projectYamlPath, write=False):
    """Migrate one project's `include` context file type from header mode to the
    base `cppm` module-interface definition.

    Idempotent: a project whose `fileGeneration.fileMap` has no `include`
    override, or whose override is already `cppm`, is a no-op (already migrated
    or never legacy). When `write` is true the override line is removed and the
    orphaned generated `.h`/`.cpp` files are deleted.

    Returns an IncludesReport.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectDir = os.path.dirname(projectYamlPath)
    report = IncludesReport(projectYaml=projectYamlPath)

    projectText = _read(projectYamlPath)
    projectData = yaml.safe_load(projectText) or {}
    projectRoot = yaml.compose(projectText)

    fileMap = (((projectData.get("fileGeneration") or {}).get("fileMap")) or {})
    include = fileMap.get("include")
    if not include:
        # No project-level override: inherits the base cppm definition already.
        return report
    exts = (include.get("ext") or {})
    if "cppm" in exts:
        # Override is already a module interface; nothing to migrate.
        return report

    # Legacy header-mode override present. Resolve the context-include base path
    # and the generated file stem suffix so the orphaned files can be located.
    includeDir = _resolveDir(projectDir, projectData.get("dirs") or {},
                             include["basePath"])
    name = include["name"]  # e.g. "Includes"
    staleFiles = []
    for ext in exts.values():
        staleFiles.extend(sorted(glob.glob(os.path.join(includeDir, f"*{name}.{ext}"))))

    overrideLine0 = _fileMapIncludeLine(projectRoot)
    if overrideLine0 is not None:
        report.applied.append(ReportItem(
            INCLUDE_OVERRIDE_REMOVE, _loc(projectYamlPath, overrideLine0 + 1),
            "removed fileGeneration.fileMap include override; inherits the base "
            "cppm module-interface definition"))
    for path in staleFiles:
        report.applied.append(ReportItem(
            STALE_FILE_DELETE, _loc(path, 0),
            f"deleted orphaned generated context include {os.path.basename(path)}"))

    # Hand-off: hand-written user code that includes a migrated context header.
    staleHeaders = {os.path.basename(p) for p in staleFiles
                    if p.endswith(".h")}
    for path, line in _userIncludeSites(projectDir, projectData, staleHeaders):
        report.manual.append(ReportItem(
            TODO_USER_IMPORT, _loc(path, line),
            f"user code #includes a migrated context header; replace with "
            f"`import <module>; using namespace <module>_ns;` (see the migration skill)"))

    if write:
        wrote = False
        if overrideLine0 is not None:
            _write(projectYamlPath, _deleteLine(projectText, overrideLine0))
            wrote = True
        for path in staleFiles:
            os.remove(path)
            wrote = True
        report.written = wrote

    return report


# ---------------------------------------------------------------------------
# Directory / file-set resolution
# ---------------------------------------------------------------------------

def _resolveDir(projectDir, dirs, key):
    """Resolve a `dirs:` entry to an absolute path. `root` is relative to the
    project file directory; other keys expand the `$root` macro against it."""
    rootDir = os.path.abspath(os.path.join(projectDir, dirs["root"]))
    spec = dirs[key]
    return os.path.abspath(spec.replace("$root", rootDir))


def _userIncludeSites(projectDir, projectData, staleHeaders):
    """Yield (path, 1-based-line) for every hand-written source file that
    `#include`s one of `staleHeaders`. A file carrying a GENERATED_CODE_BEGIN
    marker is generated (its include is rewritten to an import by `make gen`) and
    is skipped; only user files need the manual import rewrite."""
    if not staleHeaders:
        return
    dirs = projectData.get("dirs") or {}
    rootDir = os.path.abspath(os.path.join(projectDir, dirs["root"]))
    for path in sorted(_sourceFiles(rootDir)):
        text = _read(path)
        if "GENERATED_CODE_BEGIN" in text:
            continue
        for i, line in enumerate(text.splitlines()):
            stripped = line.strip()
            if not stripped.startswith("#include"):
                continue
            if any(f'"{hdr}"' in stripped for hdr in staleHeaders):
                yield path, i + 1


def _sourceFiles(rootDir):
    """All C/C++ source files under the project root, excluding build trees."""
    for dirpath, dirnames, filenames in os.walk(rootDir):
        dirnames[:] = [d for d in dirnames
                       if d not in ("build", ".gen", "obj_dir", ".git")]
        for fn in filenames:
            if fn.endswith((".h", ".hpp", ".cpp", ".cc")):
                yield os.path.join(dirpath, fn)


# ---------------------------------------------------------------------------
# YAML node / text helpers
# ---------------------------------------------------------------------------

def _fileMapIncludeLine(root):
    """0-based source line of the `include` key inside
    `fileGeneration.fileMap`, or None."""
    fileGen = _topValueNode(root, "fileGeneration")
    if fileGen is None:
        return None
    fileMap = _childValueNode(fileGen, "fileMap")
    if fileMap is None:
        return None
    for keyNode, _ in fileMap.value:
        if keyNode.value == "include":
            return keyNode.start_mark.line
    return None


def _topValueNode(root, key):
    if root is None:
        return None
    for keyNode, valNode in root.value:
        if keyNode.value == key:
            return valNode
    return None


def _childValueNode(mappingNode, key):
    if not isinstance(mappingNode, yaml.MappingNode):
        return None
    for keyNode, valNode in mappingNode.value:
        if keyNode.value == key:
            return valNode
    return None


def _deleteLine(text, line0):
    lines = text.splitlines(keepends=True)
    del lines[line0]
    return "".join(lines)


def _loc(path, line):
    return f"{os.path.basename(path)}:{line}" if line else os.path.basename(path)


def _read(path):
    with open(path, "r") as fh:
        return fh.read()


def _write(path, text):
    with open(path, "w") as fh:
        fh.write(text)
