"""Converter from the legacy project-wide `addressControl.yaml` schema to the
per-block `addressBlock:` / `project.yaml` address-policy schema (Phase B of the
unified YAML migration).

The legacy schema declared address decode in a single project-wide file
(`addressControl.yaml`: `AddressGroups`, `RegisterBusInterface`, `InstanceGroups`,
`AddressObjects`) pointed at by a `project.yaml` `addressControl:` key. The new
schema dissolves that table into a top-level `addressBlock:` field on each router
block, with the policy sections moved to `project.yaml` as `instanceGroups:` /
`addressObjects:`.

The in-generator legacy loader was removed, so this converter runs standalone: it
reads the on-disk YAML as text and never opens the project database. PyYAML
supplies values; targeted line-capturing write-back applies edits, preserving
every unrelated byte (the same split `evalPyToSv` uses for the eval pass).

Single public entry point:
  `migrateAddressControlInProject(projectYamlPath, write=False)` discovers the
  project YAML file set, plans the conversion, reports it, and applies the edits
  when `write` is true.

The conversion is automated where it is mechanical and reports the cases it
cannot resolve unambiguously. The reported cases are the ones the
`address-migration.md` skill resolves by hand; their messages reuse the skill's
diagnostics so the two surfaces match:
  - interface-scope placement (skill Step 2),
  - routed-leaf `registerPorts:` authoring (skill Steps 4 / 6.2),
  - ambiguous / missing router resolution (skill Step 3).

When the manual-TODO list is non-empty the converter does NOT delete
`addressControl.yaml` and reports the project as not format-2 clean, so the future
orchestrator does not stamp it.
"""

import os
from dataclasses import dataclass, field

import yaml

from pysrc.migrateCommon import (
    _read, _write, _loc, _topValueNode, _projectFileSet, _includeList,
)


# Applied-edit kinds.
ADDRESS_BLOCK = "ADDRESS_BLOCK"     # addressBlock: emitted on a resolved router
DROP_DORMANT = "DROP_DORMANT"       # dormant AddressGroups row dropped, not converted
POLICY_MOVE = "POLICY_MOVE"         # InstanceGroups/AddressObjects moved to project.yaml
POINTER_REMOVE = "POINTER_REMOVE"   # addressControl: pointer removed from project.yaml
POSTPROCESS = "POSTPROCESS"         # postProcess: normalized (rewrite / dedup / keep)
DELETE_DEFERRED = "DELETE_DEFERRED"  # addressControl.yaml kept as reference; next run removes it

# Manual-TODO kinds (delegated to address-migration.md).
TODO_INTERFACE_SCOPE = "TODO_INTERFACE_SCOPE"        # skill Step 2
TODO_LEAF_REGISTER_PORTS = "TODO_LEAF_REGISTER_PORTS"  # skill registerPorts: note (Migration Diagnostics)
TODO_ROUTER_RESOLUTION = "TODO_ROUTER_RESOLUTION"    # skill Step 3

# Advisory kinds: reported on every run, never block the stamp or the exit code.
ADVISORY_LEAF_REGISTER_PORTS = "ADVISORY_LEAF_REGISTER_PORTS"  # routed leaf infers its register bus

# Fields copied verbatim from a legacy AddressGroups row into addressBlock:.
# primaryDecode / varTypeContext / decoderInstance are the retired fields and are
# never copied (the new schema infers them).
_COPY_FIELDS = ("addressIncrement", "maxAddressSpaces", "varType", "enumPrefix")


@dataclass(frozen=True)
class ReportItem:
    kind: str        # one of the kind constants above
    location: str    # file:line of the edited / offending declaration
    message: str     # human-facing description; manual items reuse skill wording


@dataclass
class MigrationReport:
    projectYaml: str
    applied: list = field(default_factory=list)   # list[ReportItem]
    manual: list = field(default_factory=list)    # list[ReportItem]
    written: bool = False
    deletedAddressControl: bool = False

    @property
    def clean(self):
        """A project is format-2 clean only when nothing is left for the skill to
        resolve by hand. The orchestrator stamps `yamlFormat: 2` only when clean."""
        return not self.manual


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def routedLeafRegisterPortsAdvisory(projectYamlPath):
    """List every routed leaf block that declares no `registerPorts:`, read from
    the MIGRATED schema. Returns list[ReportItem]; advisory, never blocking.

    A routed leaf with no `registerPorts:` has its register bus inferred from the
    serving router — correct for a top-down block, wrong for reusable IP, whose
    `<block>Base` must stay self-contained. Both are legitimate, so this can only
    inform: making it block would leave every honestly top-down project
    permanently un-stampable.

    It re-derives the set rather than reusing Phase B's because Phase B's
    equivalent TODO is ONE-SHOT: it is computed from the legacy `AddressGroups`
    table, which the first run consumes and deletes, so an unanswered decision
    would silently resolve itself as top-down on run 2. Reading the post-migration
    schema instead (`addressBlock.addressGroup` names the router, `addressGroup:`
    places the leaf) keeps the question in front of the reader every run until the
    leaf either declares `registerPorts:` or stops being routed. On a project that
    has not migrated yet no block carries `addressBlock:`, so this is silent and
    the blocking Phase B TODO owns that run.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectDir = os.path.dirname(projectYamlPath)
    projectData = yaml.safe_load(_read(projectYamlPath)) or {}

    files = _projectFileSet(projectDir, projectData)
    blockRows = _buildBlockRows(files)
    blockIndex = _buildBlockIndex(files)
    instances = _buildInstanceIndex(files)

    routerForGroup = {}
    for blockName, row in blockRows.items():
        addressBlock = row.get("addressBlock")
        if not isinstance(addressBlock, dict):
            continue
        group = addressBlock.get("addressGroup")
        if group is not None:
            routerForGroup[group] = blockName

    items = []
    for leafBlock, leafInst, group in _routedLeaves(instances, routerForGroup,
                                                    blockIndex):
        if (blockRows.get(leafBlock) or {}).get("registerPorts"):
            continue
        keyLine0, _, _, leafFile = blockIndex[leafBlock]
        items.append(ReportItem(
            ADVISORY_LEAF_REGISTER_PORTS, _loc(leafFile, keyLine0 + 1),
            f"routed leaf '{leafBlock}' (instance '{leafInst}', group '{group}') "
            f"declares no registerPorts:, so its register bus is inferred from "
            f"the router '{routerForGroup[group]}'. Correct for a top-down block; "
            f"for reusable IP declare registerPorts: on the leaf instead. See the "
            f"registerPorts: note under Migration Diagnostics in "
            f"address-migration.md. Advisory: never blocks the stamp."))
    return items


def migrateAddressControlInProject(projectYamlPath, write=False):
    """Convert one project from the legacy address-control schema.

    Idempotent: a project with no `addressControl:` pointer (already migrated, or
    never used the legacy schema) is a no-op. When `write` is true the resolved
    mechanical edits are applied; `addressControl.yaml` is deleted only when the
    project is clean (no manual TODOs).

    Returns a MigrationReport.
    """
    projectYamlPath = os.path.abspath(projectYamlPath)
    projectDir = os.path.dirname(projectYamlPath)
    report = MigrationReport(projectYaml=projectYamlPath)

    projectText = _read(projectYamlPath)
    projectData = yaml.safe_load(projectText) or {}
    projectRoot = yaml.compose(projectText)

    pointer = projectData.get("addressControl")
    if pointer is None:
        # No legacy pointer. Either the project never used the legacy schema, or a
        # prior run already migrated the routing and removed the pointer. The
        # pointer is removed as soon as routing is accounted for, but the legacy
        # file is kept as reference until the project is fully clean; a run that
        # finalized the project after the pointer was already gone would otherwise
        # strand addressControl.yaml on disk. Delete that leftover here so the
        # pointer and file stay consistent (both gone once routing is migrated).
        leftover = os.path.join(projectDir, "addressControl.yaml")
        if write and os.path.isfile(leftover):
            os.remove(leftover)
            report.deletedAddressControl = True
            report.written = True
        return report

    addrCtlPath = os.path.join(projectDir, pointer)
    try:
        addrCtlText = _read(addrCtlPath)
    except OSError as exc:
        raise RuntimeError(
            f"address-control migration: cannot read the addressControl file "
            f"'{pointer}' referenced by {os.path.basename(projectYamlPath)}: {exc}")
    addrCtlRoot = yaml.compose(addrCtlText)
    addrCtl = yaml.safe_load(addrCtlText) or {}

    files = _projectFileSet(projectDir, projectData)
    blockIndex = _buildBlockIndex(files)
    instances = _buildInstanceIndex(files)
    fileInterfaces = {path: _interfaceNames(_read(path)) for path in files}

    groups = addrCtl.get("AddressGroups") or {}
    regBusIf = _normalizeRegisterBusInterface(addrCtl.get("RegisterBusInterface"))

    # Liveness of an AddressGroups row: it names a decoderInstance, or some
    # instance places itself in the group via addressGroup:.
    referenced = {inst["addressGroup"] for inst in instances.values()
                  if inst.get("addressGroup") is not None}

    # Resolve each group to its router block and collect emissions.
    emissions = []                 # (block, groupName, fieldNodes)
    routerForGroup = {}            # groupName -> routerBlock
    groupsForRouter = {}           # routerBlock -> [groupName]
    for groupName, body in groups.items():
        groupLoc = _loc(addrCtlPath, _mappingKeyLine(addrCtlRoot, "AddressGroups", groupName))
        decoderInstance = (body or {}).get("decoderInstance")

        if decoderInstance is None and groupName not in referenced:
            report.applied.append(ReportItem(
                DROP_DORMANT, groupLoc,
                f"dropped dormant AddressGroups row '{groupName}' "
                f"(no decoderInstance and no instance references it)"))
            continue

        if decoderInstance is None:
            report.manual.append(ReportItem(
                TODO_ROUTER_RESOLUTION, groupLoc,
                f"AddressGroups row '{groupName}' is referenced by an instance "
                f"but names no decoderInstance, so its router block cannot be "
                f"resolved — author addressBlock: by hand — see "
                f"address-migration.md Step 3."))
            continue

        inst = instances.get(decoderInstance)
        block = inst["instanceType"] if inst else None
        if block is None or block not in blockIndex:
            report.manual.append(ReportItem(
                TODO_ROUTER_RESOLUTION, groupLoc,
                f"AddressGroups row '{groupName}' decoderInstance "
                f"'{decoderInstance}' does not resolve to a router block — "
                f"author addressBlock: by hand — see address-migration.md "
                f"Step 3."))
            continue

        routerForGroup[groupName] = block
        groupsForRouter.setdefault(block, []).append(groupName)
        emissions.append((block, groupName,
                          _groupFieldNodes(addrCtlRoot, groupName)))

    # Two live groups resolving to the same router block is ambiguous; the
    # post-parse pass reports a duplicate addressBlock:, so do the same here.
    emissions = [e for e in emissions if _routerIsUnambiguous(
        e[0], groupsForRouter, blockIndex, addrCtlPath, addrCtlRoot, report)]

    # Emit addressBlock: on each resolved router and check interface scope.
    addressBlockEdits = {}    # path -> [(line, col, childCol, bodyLines)]
    for block, groupName, fieldNodes in emissions:
        line, col, childCol, blockFile = blockIndex[block]
        bodyLines = _addressBlockLines(addrCtlText, groupName, fieldNodes,
                                       regBusIf, col, childCol)
        addressBlockEdits.setdefault(blockFile, []).append((line, bodyLines))
        report.applied.append(ReportItem(
            ADDRESS_BLOCK, _loc(blockFile, line + 1),
            f"emitted addressBlock: on router block '{block}' "
            f"from AddressGroups row '{groupName}'"))

        if regBusIf is not None and not _interfaceInScope(
                blockFile, regBusIf, fileInterfaces):
            report.manual.append(ReportItem(
                TODO_INTERFACE_SCOPE, _loc(blockFile, line + 1),
                f"Router block '{block}' (file {os.path.basename(blockFile)}) "
                f"has no addressBus: true interface authored in its load-time "
                f"scope."))

    # Every routed leaf needs a registerPorts: decision; registerPorts: is a
    # new-schema concept absent from legacy designs, so the tool reports each
    # routed leaf rather than guessing whether it is reusable IP or top-down.
    for leafBlock, leafInst, groupName in _routedLeaves(
            instances, routerForGroup, blockIndex):
        line = blockIndex[leafBlock][0]
        leafFile = blockIndex[leafBlock][3]
        router = routerForGroup[groupName]
        report.manual.append(ReportItem(
            TODO_LEAF_REGISTER_PORTS, _loc(leafFile, line + 1),
            f"Routed leaf block '{leafBlock}' (instance '{leafInst}', served by "
            f"router '{router}' for group '{groupName}') needs a registerPorts: "
            f"declaration authored by hand — see the registerPorts: note under "
            f"Migration Diagnostics in address-migration.md."))

    # Plan the project.yaml edits and report them. These items appear in both the
    # dry-run report and the applied write, so they are built unconditionally; the
    # file is only touched under `write` below.
    pointerLine = _topKeyLine(projectRoot, "addressControl")
    instGroups = addrCtl.get("InstanceGroups")
    addrObjects = addrCtl.get("AddressObjects")

    ptext = projectText
    # Remove the pointer once every AddressGroups row is accounted for (converted
    # to an addressBlock or dropped as dormant). A live group left unresolved
    # keeps the pointer so its decode information is not lost before the skill
    # authors the missing router by hand.
    unresolvedRouter = any(i.kind == TODO_ROUTER_RESOLUTION for i in report.manual)
    if not unresolvedRouter:
        ptext, _ = _removePointer(ptext)
        report.applied.append(ReportItem(
            POINTER_REMOVE, _loc(projectYamlPath, pointerLine),
            "removed addressControl: pointer from project.yaml"))
    ptext = _rewritePostProcess(ptext, _baseScriptBasenames(), report,
                                projectYamlPath)
    if instGroups or addrObjects:
        ptext = _appendPolicySections(ptext, instGroups, addrObjects)
        report.applied.append(ReportItem(
            POLICY_MOVE, _loc(projectYamlPath, pointerLine),
            "moved InstanceGroups:/AddressObjects: to project.yaml "
            "instanceGroups:/addressObjects:"))

    # A survivor looks like a migration failure. Say why it is still there, or
    # the operator hand-deletes a file the next run removes on its own (the
    # pointer-is-None cleanup at the top of this function).
    if not report.clean:
        report.applied.append(ReportItem(
            DELETE_DEFERRED, _loc(addrCtlPath, 0),
            f"keeping {os.path.basename(addrCtlPath)} as reference while manual "
            f"items remain; it is removed automatically on the next run — do not "
            f"delete it by hand"))

    if not write:
        return report

    # ---- write phase -------------------------------------------------------
    wrote = False

    for path, edits in addressBlockEdits.items():
        text = _read(path)
        # Inject bottom-to-top so earlier line numbers stay valid as lines shift.
        for line, bodyLines in sorted(edits, key=lambda e: e[0], reverse=True):
            text = _insertAfterLine(text, line, bodyLines)
        _write(path, text)
        wrote = True

    if ptext != projectText:
        _write(projectYamlPath, ptext)
        wrote = True

    # Delete the legacy file only when the project is clean; a non-empty manual
    # list means the skill still has work, so the file stays as reference
    # (DELETE_DEFERRED above says so).
    if report.clean:
        try:
            os.remove(addrCtlPath)
        except OSError as exc:
            raise RuntimeError(
                f"address-control migration: cannot delete the migrated "
                f"{os.path.basename(addrCtlPath)}: {exc}")
        report.deletedAddressControl = True

    report.written = wrote
    return report


# ---------------------------------------------------------------------------
# Project file-set discovery and indexing
# ---------------------------------------------------------------------------

def _buildBlockIndex(files):
    """Map every block name to (keyLine0, keyCol, childCol, filePath). keyLine0 is
    the 0-based line of the block's `name:` key; childCol is the column of its
    first child field (or keyCol+4 when the block has none)."""
    index = {}
    for path in files:
        root = yaml.compose(_read(path))
        blocksNode = _topValueNode(root, "blocks")
        if blocksNode is None:
            continue
        for keyNode, valNode in blocksNode.value:
            col = keyNode.start_mark.column
            childCol = col + 4
            if isinstance(valNode, yaml.MappingNode) and valNode.value:
                childCol = valNode.value[0][0].start_mark.column
            index[keyNode.value] = (keyNode.start_mark.line, col, childCol, path)
    return index


def _buildBlockRows(files):
    """Map every block name to its authored row dict (an empty dict when the
    block declares no fields). Values only — `_buildBlockIndex` carries the
    positions the emitters need."""
    rows = {}
    for path in files:
        data = yaml.safe_load(_read(path)) or {}
        for name, row in (data.get("blocks") or {}).items():
            rows[name] = row or {}
    return rows


def _buildInstanceIndex(files):
    """Map every instance name to its row dict (instanceType, addressGroup,
    container, ...). Instance names are unique across the project file set."""
    instances = {}
    for path in files:
        data = yaml.safe_load(_read(path)) or {}
        for name, row in (data.get("instances") or {}).items():
            instances[name] = row or {}
    return instances


def _interfaceNames(text):
    data = yaml.safe_load(text) or {}
    return set((data.get("interfaces") or {}).keys())


def _includeClosure(startPath):
    """Set of files visible from `startPath` through its own downward `include:`
    chain (the file itself plus everything it pulls in, transitively)."""
    closure = set()
    queue = [os.path.abspath(startPath)]
    while queue:
        path = queue.pop(0)
        if path in closure:
            continue
        closure.add(path)
        for inc in _includeList(_read(path)):
            queue.append(os.path.abspath(os.path.join(os.path.dirname(path), inc)))
    return closure


def _interfaceInScope(routerFile, interfaceName, fileInterfaces):
    """True if `interfaceName` is declared in a file visible to `routerFile`
    through its include chain (its own load-time scope)."""
    for path in _includeClosure(routerFile):
        if interfaceName in fileInterfaces.get(path, set()):
            return True
    return False


def _routedLeaves(instances, routerForGroup, blockIndex):
    """Yield (leafBlock, instanceName, groupName) for each routed leaf instance:
    one placed in a resolved address group whose block is not itself a router.
    De-duplicated per leaf block (registerPorts: is authored on the block)."""
    seen = set()
    for instName, inst in instances.items():
        group = inst.get("addressGroup")
        if group is None or group not in routerForGroup:
            continue
        block = inst.get("instanceType")
        if block is None or block not in blockIndex:
            continue
        if block == routerForGroup[group]:
            continue
        if block in seen:
            continue
        seen.add(block)
        yield block, instName, group


def _routerIsUnambiguous(block, groupsForRouter, blockIndex, addrCtlPath,
                         addrCtlRoot, report):
    """Emit a manual TODO and drop the emission when two live groups resolve to
    the same router block (mirrors the post-parse duplicate-addressBlock check).
    The TODO is reported once per offending router."""
    groups = groupsForRouter.get(block, [])
    if len(groups) <= 1:
        return True
    # Report once, on the first emission seen for this router.
    already = any(item.kind == TODO_ROUTER_RESOLUTION and f"router '{block}'" in item.message
                  for item in report.manual)
    if not already:
        line = blockIndex[block][0]
        report.manual.append(ReportItem(
            TODO_ROUTER_RESOLUTION, _loc(blockIndex[block][3], line + 1),
            f"AddressGroups rows {sorted(groups)} both resolve to router "
            f"'{block}'; this group duplicates a prior addressBlock: — resolve "
            f"by hand — see address-migration.md Step 3."))
    return False


# ---------------------------------------------------------------------------
# addressBlock: emission
# ---------------------------------------------------------------------------

def _addressBlockLines(addrCtlText, groupName, fieldNodes, regBusIf, blockCol,
                       childCol):
    """Build the `addressBlock:` block as a list of text lines, indented for a
    block whose key sits at `blockCol` and whose fields sit at `childCol`. Copied
    field values are captured verbatim from the legacy source so spellings such
    as the `0x01000000` hex literal survive unchanged."""
    unit = childCol - blockCol
    keyIndent = " " * childCol
    fieldIndent = " " * (childCol + unit)
    lines = [f"{keyIndent}addressBlock:",
             f"{fieldIndent}addressGroup: {groupName}"]
    for fieldName in _COPY_FIELDS:
        node = fieldNodes.get(fieldName)
        if node is not None:
            lines.append(f"{fieldIndent}{fieldName}: {_rawValue(addrCtlText, node)}")
    if regBusIf is not None:
        lines.append(f"{fieldIndent}upstreamPort: {regBusIf}")
        lines.append(f"{fieldIndent}registerDecoderPort: {regBusIf}")
    return [line + "\n" for line in lines]


def _normalizeRegisterBusInterface(value):
    """Treat YAML null and the legacy literal string `None` as 'no interface
    named'; otherwise return the interface name."""
    if value is None or value == "None":
        return None
    return value


# ---------------------------------------------------------------------------
# project.yaml edits
# ---------------------------------------------------------------------------

def _removePointer(text):
    """Remove the top-level `addressControl:` line. Returns (text, removedLine0)."""
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.lstrip().startswith("addressControl:") and not line.startswith(" "):
            del lines[i]
            return "".join(lines), i
    return text, None


def _rewritePostProcess(text, baseBasenames, report, projectYamlPath):
    """Normalize a project `postProcess:` override.

    Rewrites a `postParseRegister.py` reference to `postParseRegisterPorts.py`
    (the current register-ports post-parse script), then strips any entry that
    duplicates a base script.
    An emptied block is removed entirely; a block that retains genuinely
    project-specific entries keeps them and is reported for review.

    The block spans the `postProcess:` key line plus every following line that
    belongs to it — real `- ` entries and any interleaved comment/blank lines —
    terminating at the next top-level construct (a non-indented, non-comment,
    non-blank line) or EOF. Trailing blank line(s) before that terminator are
    the separator and are always left in place, so neither a kept nor a removed
    block swallows the blank line that follows it."""
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.rstrip("\n") == "postProcess:" or (
                line.startswith("postProcess:") and not line.startswith(" ")):
            start = i
            break
    if start is None:
        return text

    # Scan the whole block. `contentEnd` advances only past entry/comment lines
    # so trailing blank separators are excluded from the spliced-out region.
    end = start + 1
    contentEnd = start + 1
    items = []
    while end < len(lines):
        line = lines[end]
        stripped = line.strip()
        isBlank = stripped == ""
        isComment = stripped.startswith("#")
        if not isBlank and not isComment and not line[:1].isspace():
            break
        if stripped.startswith("- "):
            items.append(line)
        end += 1
        if not isBlank:
            contentEnd = end

    kept = []
    rewritten = False
    for item in items:
        prefix, ref = item.split("- ", 1)
        ref = ref.rstrip("\n")
        base = os.path.basename(ref)
        if base == "postParseRegister.py":
            ref = ref[:-len(base)] + "postParseRegisterPorts.py"
            base = "postParseRegisterPorts.py"
            rewritten = True
        if base in baseBasenames:
            continue
        kept.append(f"{prefix}- {ref}\n")

    loc = _loc(projectYamlPath, start + 1)
    if rewritten:
        report.applied.append(ReportItem(
            POSTPROCESS, loc,
            "rewrote postProcess: postParseRegister.py -> "
            "postParseRegisterPorts.py and stripped base-script duplicates"))
    if kept:
        report.applied.append(ReportItem(
            POSTPROCESS, loc,
            "kept project-specific postProcess: entries — review: "
            + ", ".join(os.path.basename(k.split('- ', 1)[1].strip()) for k in kept)))
        block = lines[start:start + 1] + kept
    else:
        report.applied.append(ReportItem(
            POSTPROCESS, loc,
            "removed postProcess: override (only base-script duplicates remained)"))
        block = []

    return "".join(lines[:start] + block + lines[contentEnd:])


def _appendPolicySections(text, instGroups, addrObjects):
    """Append `instanceGroups:` / `addressObjects:` sections to project.yaml,
    carrying the legacy row bodies verbatim under the new lower-camel-case keys."""
    chunks = [text if text.endswith("\n") else text + "\n"]
    if instGroups:
        chunks.append("\n" + yaml.dump({"instanceGroups": instGroups},
                                       default_flow_style=False, sort_keys=False,
                                       indent=4))
    if addrObjects:
        chunks.append("\n" + yaml.dump({"addressObjects": addrObjects},
                                       default_flow_style=False, sort_keys=False,
                                       indent=4))
    return "".join(chunks)


def _baseScriptBasenames():
    """Basenames of the base config's postProcess scripts; entries duplicating
    these are stripped from a migrated project's override."""
    baseProject = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "project.yaml")
    data = yaml.safe_load(_read(baseProject)) or {}
    return {os.path.basename(entry) for entry in data.get("postProcess", [])}


# ---------------------------------------------------------------------------
# YAML node helpers (line / verbatim-value capture)
# ---------------------------------------------------------------------------

def _topKeyLine(root, key):
    """1-based line of a top-level key, or None."""
    if root is None:
        return None
    for keyNode, _ in root.value:
        if keyNode.value == key:
            return keyNode.start_mark.line + 1
    return None


def _mappingKeyLine(root, topKey, childKey):
    """1-based line of `childKey` inside the top-level mapping `topKey`."""
    node = _topValueNode(root, topKey)
    if node is None:
        return None
    for keyNode, _ in node.value:
        if keyNode.value == childKey:
            return keyNode.start_mark.line + 1
    return None


def _groupFieldNodes(root, groupName):
    """Map field name -> value node for one AddressGroups row, for verbatim
    value capture."""
    groupsNode = _topValueNode(root, "AddressGroups")
    if groupsNode is None:
        return {}
    for keyNode, valNode in groupsNode.value:
        if keyNode.value == groupName and isinstance(valNode, yaml.MappingNode):
            return {k.value: v for k, v in valNode.value}
    return {}


def _rawValue(text, valueNode):
    """The original source slice spanning a scalar value node, carrying its
    spelling (for example a hex literal) through unchanged."""
    return text[valueNode.start_mark.index:valueNode.end_mark.index]


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------

def _insertAfterLine(text, line0, newLines):
    """Insert `newLines` (each newline-terminated) immediately after 0-based
    source line `line0`."""
    lines = text.splitlines(keepends=True)
    lines[line0 + 1:line0 + 1] = newLines
    return "".join(lines)
