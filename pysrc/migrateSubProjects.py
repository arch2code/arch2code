"""Composed-build check: every child project a project references must itself be
migrated.

`make migrate` migrates exactly ONE project — the one `A2C_PRJ_YAML` names. A
composed build (a top-level project whose `projectFiles:` lists child
`*Project.yaml` files) is several projects, each with its own build harness and
its own `yamlFormat:` stamp, and the top-level run neither stamps nor fully
converts the children: the text phases walk the top's `projectFiles:` plus the
`include:` chains below them, so a child's OWN `projectFiles:` list is never
followed.

Nothing else catches this. `projectCreate`'s yamlFormat gate reads only the
project YAML it was invoked on, so a composition whose children are un-migrated
passes the gate and builds happily — and each child is refused the moment anyone
builds it standalone, which is the entire point of a reusable IP sub-project. The
failure therefore surfaces in a different tree, long after the migration was
called done, which is why it is reported here rather than left to the operator.

Direct children only. A grandchild is invisible from here for the same reason it
is invisible to the text phases, and it does not need to be visible: the child's
own `make migrate` run reports it. Resolving bottom-up — which is the documented
order — walks the whole composition one level at a time.

Text-only: reads YAML, writes nothing, never opens the database.
"""

import os
from dataclasses import dataclass, field

import yaml

from pysrc.migrateCommon import _read, _loc


# The sentinel that makes a referenced file a child PROJECT rather than a design
# file. Mirrors processYaml.projectCreate._isChildProjectFile, which is the
# authority: the two must agree, or a file the generator treats as a project
# would go unchecked here.
_CHILD_PROJECT_KEYS = ("projectName", "dirs", "fileGeneration")

TODO_UNMIGRATED_SUBPROJECT = "TODO_UNMIGRATED_SUBPROJECT"  # child project lacks the current stamp


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file (or file:line) the item refers to
    message: str     # human-facing description


@dataclass
class SubProjectsReport:
    projectYaml: str
    manual: list = field(default_factory=list)   # list[ReportItem]

    @property
    def clean(self):
        """True when every referenced child project carries the current stamp.
        Blocks the top-level stamp while it does not: a composition is not
        migrated until its parts are."""
        return not self.manual


def checkSubProjects(projectYamlPath, currentFormat):
    """Report each child project referenced by `projectYamlPath` that does not
    carry `yamlFormat: currentFormat`. Returns a SubProjectsReport."""
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectDir = os.path.dirname(projectYamlPath)
    report = SubProjectsReport(projectYaml=projectYamlPath)

    projectData = yaml.safe_load(_read(projectYamlPath)) or {}
    for entry in projectData.get("projectFiles") or []:
        childPath = os.path.abspath(os.path.join(projectDir, entry))
        if not os.path.isfile(childPath):
            continue
        childData = yaml.safe_load(_read(childPath)) or {}
        if not all(key in childData for key in _CHILD_PROJECT_KEYS):
            continue
        childFormat = childData.get("yamlFormat")
        if childFormat == currentFormat:
            continue
        state = (f"it declares yamlFormat: {childFormat}"
                 if childFormat is not None else "it carries no yamlFormat:")
        report.manual.append(ReportItem(
            TODO_UNMIGRATED_SUBPROJECT, _loc(childPath, 0),
            f"child project '{childData['projectName']}' ({entry}) is not "
            f"migrated — {state}, not {currentFormat}. This run stamps only the "
            f"project it was given, and the projectCreate gate reads only that "
            f"file, so the composition would build while the child is refused "
            f"whenever it is built on its own. Run `make migrate` from "
            f"{_childRundir(childPath, childData, projectDir)}, then re-run here; "
            f"see 'Composed builds' in migrate-project.md, Section 1"))
    return report


def _childRundir(childPath, childData, fromDir):
    """The child project's `rundir/`, spelled relative to the invoking project's
    directory. Derived from the child's own `dirs.root` (the project root,
    relative to the project file) so a project that nests its YAML differently
    still gets a usable path rather than a guessed one."""
    childRoot = os.path.join(os.path.dirname(childPath),
                             (childData.get("dirs") or {}).get("root", "."))
    return os.path.relpath(os.path.join(childRoot, "rundir"), fromDir)
