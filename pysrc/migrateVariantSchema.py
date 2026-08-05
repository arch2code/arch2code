"""Converter from the retired per-row variant-binding form to the nested-mapping
form (the variant-schema phase of the unified YAML migration).

The old schema repeated the variant label on every parameter row of a
`parameters:` block entry:

    parameters:
        ip:
            - { variant: variant1, param: IP_DATA_WIDTH, value: 70 }
            - { variant: variant1, param: IP_MEM_DEPTH,  value: 8 }

The current schema states the variant label once and nests its parameters:

    parameters:
        ip:
            variant1:
                IP_DATA_WIDTH: 70
                IP_MEM_DEPTH: 8

Standalone and text-only, like `migrateIncludes` / `migrateAddressControl`: it
reads YAML as text and never opens the project database. `yaml.compose` supplies
line/column marks; targeted line-range rewrites preserve every unrelated byte
(surrounding comments, the block key line, other sections).

Scope is `parameters:` sections ONLY. Instance `variant:` selectors (e.g.
`uBlockF0: {..., variant: variant0}`) are variant SELECTIONS, not parameter
bindings, and are never touched.

The conversion is purely mechanical and lossless — it groups the per-row rows by
`variant` (first-seen order) and rewrites the block entry — so it produces no
manual TODOs. `clean` is always True; an already-nested file is a no-op.
"""

import os
from dataclasses import dataclass, field

import yaml

from pysrc.migrateCommon import (
    _read, _write, _loc, _topValueNode, _projectFileSet,
)


# Applied-edit kind.
VARIANT_REGROUP = "VARIANT_REGROUP"  # per-row list rewritten to nested mapping


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line of the edited block entry
    message: str     # human-facing description


@dataclass
class VariantReport:
    projectYaml: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False

    @property
    def clean(self):
        """True when nothing is left for the skill to resolve by hand. The
        rewrite is mechanical, so this is always True."""
        return not self.manual


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def migrateVariantSchemaInProject(projectYamlPath, write=False):
    """Rewrite every project YAML file's `parameters:` block entries from the
    retired per-row list form to the nested-mapping form.

    Idempotent: a block entry already authored as a nested mapping is a no-op.
    When `write` is true the edits are applied in place.

    Returns a VariantReport.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectDir = os.path.dirname(projectYamlPath)
    report = VariantReport(projectYaml=projectYamlPath)

    projectData = yaml.safe_load(_read(projectYamlPath)) or {}
    for path in _projectFileSet(projectDir, projectData):
        _migrateFile(path, report, write)
    return report


# ---------------------------------------------------------------------------
# Per-file conversion
# ---------------------------------------------------------------------------

def _migrateFile(path, report, write):
    text = _read(path)
    root = yaml.compose(text)
    parametersNode = _topValueNode(root, "parameters")
    if not isinstance(parametersNode, yaml.MappingNode):
        return

    # Collect a (startLine0, endLine0, newLines) rewrite per per-row block entry.
    edits = []
    for keyNode, valNode in parametersNode.value:
        if not isinstance(valNode, yaml.SequenceNode) or not valNode.value:
            # Already nested (MappingNode) or empty; nothing to convert.
            continue
        blockKeyCol = keyNode.start_mark.column
        rewrite = _planBlockRewrite(text, keyNode.value, blockKeyCol, valNode)
        if rewrite is not None:
            edits.append(rewrite)

    if not edits:
        return

    for keyNode, valNode in parametersNode.value:
        if isinstance(valNode, yaml.SequenceNode) and valNode.value:
            report.applied.append(ReportItem(
                VARIANT_REGROUP, _loc(path, keyNode.start_mark.line + 1),
                f"parameters block '{keyNode.value}' regrouped from the per-row "
                f"variant list to the nested-mapping form"))

    if write:
        _write(path, _applyEdits(text, edits))
        report.written = True


def _planBlockRewrite(text, blockName, blockKeyCol, seqNode):
    """Build the (startLine0, endLine0Inclusive, newLines) rewrite that replaces
    one block entry's per-row sequence with the nested-mapping form. Returns None
    if the sequence is not the expected per-row variant list."""
    # Group rows by variant, first-seen order, preserving the raw value spelling.
    grouped = []  # list[(variant, list[(param, rawValue)])]
    index = dict()
    for itemNode in seqNode.value:
        if not isinstance(itemNode, yaml.MappingNode):
            return None
        fields = {k.value: v for k, v in itemNode.value}
        if "variant" not in fields or "param" not in fields or "value" not in fields:
            return None
        variant = fields["variant"].value
        param = fields["param"].value
        rawValue = _rawScalar(text, fields["value"])
        if variant not in index:
            index[variant] = len(grouped)
            grouped.append((variant, []))
        grouped[index[variant]][1].append((param, rawValue))

    # Indentation: the per-row `-` column becomes the variant-key column; the
    # step below the block key becomes the param indent under each variant.
    variantCol = seqNode.start_mark.column
    step = variantCol - blockKeyCol
    if step <= 0:
        step = 4
    paramCol = variantCol + step

    newLines = []
    for variant, params in grouped:
        newLines.append(f"{' ' * variantCol}{variant}:")
        for param, rawValue in params:
            newLines.append(f"{' ' * paramCol}{param}: {rawValue}")

    startLine0 = seqNode.value[0].start_mark.line
    endLine0 = _lastLine0(seqNode.value[-1])
    return (startLine0, endLine0, newLines)


# ---------------------------------------------------------------------------
# Node / text helpers
# ---------------------------------------------------------------------------

def _rawScalar(text, node):
    """The exact source spelling of a scalar value node, so ints, hex, and
    symbolic-constant references are preserved verbatim."""
    return text[node.start_mark.index:node.end_mark.index].strip()


def _lastLine0(node):
    """0-based last physical line a node occupies. A flow mapping row ends on its
    own line; guard the case where end_mark points at column 0 of the next
    line."""
    endLine0 = node.end_mark.line
    if endLine0 > node.start_mark.line and node.end_mark.column == 0:
        endLine0 -= 1
    return endLine0


def _applyEdits(text, edits):
    """Apply line-range replacements bottom-to-top so earlier line numbers stay
    valid. Each edit is (startLine0, endLine0Inclusive, newLines)."""
    lines = text.splitlines(keepends=True)
    for startLine0, endLine0, newLines in sorted(edits, key=lambda e: e[0], reverse=True):
        # Preserve whether the last replaced line carried a trailing newline
        # (a file with no final newline must stay that way).
        trailingNewline = lines[endLine0].endswith("\n")
        rendered = [nl + "\n" for nl in newLines]
        if not trailingNewline and rendered:
            rendered[-1] = rendered[-1][:-1]
        lines[startLine0:endLine0 + 1] = rendered
    return "".join(lines)
