"""Adds the `langDomain` key to the project file's own fileMap entries (the
langDomain phase of the unified YAML migration).

projectCreate requires every fileMap entry to name its langDomain (sv, sc or
fw), which picks the filename prefix the entry's files take. Before the key
existed the prefix kind came from the entry itself: an sv or svh ext value
meant sv, basePath fwInc meant fw, and anything else sc. This phase writes that
same value into each entry that lacks the key, so every generated filename
stays as it was.

Standalone and text-only, like `migrateIncludes`: it reads YAML as text and
never opens the project database. `yaml.compose` supplies the marks for the
insertions, and every other byte of the file stays as written.

Mechanical (applied automatically):
  - a flow-style entry gets `, langDomain: <value>` right after its basePath
    value,
  - a block-style entry gets a `langDomain: <value>` line after its basePath
    line, at the indent of its other keys.

Reported for a manual edit: an entry the insertion cannot place safely, such as
one without a plain basePath or ext mapping, or a block-style basePath whose
value runs past its own line. An alias to an entry earlier in the fileMap
shares that entry's text, so the one insertion covers both.

Idempotent: an entry that already has langDomain is left alone.
"""

import os
from dataclasses import dataclass, field

import yaml

from pysrc.migrateCommon import _read, _write, _loc, _topValueNode
from pysrc.migrateIncludes import _childValueNode


# Applied-edit kind.
LANGDOMAIN_ADD = "LANGDOMAIN_ADD"          # langDomain key added to a fileMap entry

# Manual-TODO kind.
TODO_LANGDOMAIN = "TODO_LANGDOMAIN"        # entry the phase cannot edit mechanically

# ext values that give an entry langDomain sv.
SV_EXTS = {"sv", "svh"}


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line of the fileMap entry
    message: str     # human-facing description


@dataclass
class LangDomainReport:
    projectYaml: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        """True when no entry is left for a manual edit."""
        return not self.manual


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def migrateLangDomainInProject(projectYamlPath, write=False):
    """Add `langDomain` to each entry of the project file's
    `fileGeneration.fileMap` that lacks it. When `write` is true the edits are
    applied in place.

    Returns a LangDomainReport.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    report = LangDomainReport(projectYaml=projectYamlPath)

    text = _read(projectYamlPath)
    fileGen = _topValueNode(yaml.compose(text), "fileGeneration")
    fileMap = _childValueNode(fileGen, "fileMap")
    if not isinstance(fileMap, yaml.MappingNode):
        return report

    insertions = []   # list[(textIndex, insertedText)]
    seen = set()
    for keyNode, entryNode in fileMap.value:
        location = _loc(projectYamlPath, keyNode.start_mark.line + 1)
        name = keyNode.value
        if id(entryNode) in seen:
            continue
        seen.add(id(entryNode))
        if isinstance(entryNode, yaml.MappingNode) and \
                any(k.value == "langDomain" for k, _ in entryNode.value):
            continue
        planned = _planInsertion(text, entryNode)
        if isinstance(planned, str):
            report.manual.append(ReportItem(
                TODO_LANGDOMAIN, location,
                f"fileMap entry '{name}' {planned}; add langDomain: sv, sc or fw "
                f"by hand (sv for sv/svh files, fw for basePath fwInc, sc otherwise)"))
            continue
        index, value, inserted = planned
        insertions.append((index, inserted))
        report.applied.append(ReportItem(
            LANGDOMAIN_ADD, location,
            f"fileMap entry '{name}' gets langDomain: {value}"))

    if write and insertions:
        for index, inserted in sorted(insertions, reverse=True):
            text = text[:index] + inserted + text[index:]
        _write(projectYamlPath, text)
        report.written = True
    return report


# ---------------------------------------------------------------------------
# Per-entry planning
# ---------------------------------------------------------------------------

def _planInsertion(text, entryNode):
    """(textIndex, value, insertedText) for one entry, or a string saying why
    the entry needs a manual edit."""
    if not isinstance(entryNode, yaml.MappingNode):
        return "is not a mapping"
    fields = {k.value: (k, v) for k, v in entryNode.value}
    if "basePath" not in fields or "ext" not in fields:
        return "has no basePath or no ext"
    baseKey, baseValue = fields["basePath"]
    extNode = fields["ext"][1]
    if not isinstance(baseValue, yaml.ScalarNode):
        return "has a basePath that is not a plain value"
    if not isinstance(extNode, yaml.MappingNode) or \
            not all(isinstance(v, yaml.ScalarNode) for _, v in extNode.value):
        return "has an ext that is not a mapping of plain values"

    if SV_EXTS & {v.value for _, v in extNode.value}:
        value = "sv"
    elif baseValue.value == "fwInc":
        value = "fw"
    else:
        value = "sc"

    if entryNode.flow_style:
        return (baseValue.end_mark.index, value, f", langDomain: {value}")

    if baseValue.end_mark.line != baseKey.start_mark.line:
        return "has a basePath value that runs past its own line"
    lineEnd = text.find("\n", baseValue.end_mark.index)
    newLine = f"{' ' * baseKey.start_mark.column}langDomain: {value}"
    if lineEnd == -1:
        return (len(text), value, "\n" + newLine)
    return (lineEnd + 1, value, newLine + "\n")
