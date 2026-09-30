---
name: address-migration
description: Convert legacy arch2code projects from project-wide addressControl.yaml address control to per-block addressBlock: routers and project.yaml address-policy sections.
---
# Skill: Legacy Address Control Migration

## Run `make migrate` first

This skill is the **fallback** for the automated migration tool, not the
primary path. Run the converter before working through any step by hand:

```text
make migrate
```

`make migrate` wraps `migrateYaml.py --write <project.yaml>`. It converts every
case it can resolve mechanically — emits `addressBlock:` on each resolved
router, moves the policy sections to `project.yaml`, normalizes `postProcess:`,
removes the `addressControl:` pointer, deletes the legacy `addressControl.yaml`
once the project is clean, and stamps `yamlFormat: 2`. The cases it cannot
resolve unambiguously are printed under a `manual TODO:` heading and block the
stamp. **This skill covers exactly those manual-TODO cases.**

Each manual-TODO line is printed as:

```text
<file>:<line>  <KIND>  <message>
```

Resolve every reported item, then re-run `make migrate`. The tool is
idempotent: already-converted evals, an existing `addressBlock:`, and an absent
`addressControl:` pointer are skipped, and a project already carrying
`yamlFormat: 2` short-circuits to "already migrated".

In a **composed build**, run it once per sub-project from that project's own
`rundir/` — `make migrate` converts only the project `A2C_PRJ_YAML` names, and
each sub-project carries its own `addressControl:` pointer and its own routing to
convert. See "Composed builds" in the `migrate-project` skill, Section 1.

### Manual-TODO kinds and where each is resolved

| Tool report `KIND` | Meaning | Resolve in |
| --- | --- | --- |
| `TODO_ROUTER_RESOLUTION` | An `AddressGroups` row's router cannot be resolved — it names no `decoderInstance`, or its `decoderInstance` does not resolve to a router block. | Step 3 |
| `TODO_INTERFACE_SCOPE` | A router has no `addressBus: true` interface authored in its load-time scope. | Step 2 |
| `TODO_LEAF_REGISTER_PORTS` | A routed leaf needs a `registerPorts:` declaration — a judgment call the tool will not guess. Raised only on the migrating run; afterwards the same leaf appears as the advisory below. | The `registerPorts:` note under Migration Diagnostics |

One **advisory** kind is also emitted here. It prints on every run and never
blocks the stamp or the exit code:

| Tool report `KIND` | Meaning | Read about it in |
| --- | --- | --- |
| `ADVISORY_LEAF_REGISTER_PORTS` | A routed leaf declares no `registerPorts:`, so its register bus is inferred from the serving router. Correct for a top-down leaf, wrong for reusable IP. | The `registerPorts:` note under Migration Diagnostics |

A real-valued `eval` (for example `$DWORD / 2.0`) is reported by Phase A as a
`NEEDS_MANUAL` eval row and also blocks the stamp; convert it to a literal
`value:` by hand. That is an eval migration, not an address one, and is outside
this skill's scope.

## Purpose

Guide the user through converting an existing arch2code project that
uses `project.yaml` `addressControl:` and project-wide
`addressControl.yaml` declarations to the per-block address control
schema:

- Router blocks declare a top-level `addressBlock:` field.
- Address-policy sections move from legacy `InstanceGroups:` and
  `AddressObjects:` to top-level `project.yaml` fields named
  `instanceGroups:` and `addressObjects:`.

This skill is only for legacy migration. It is not a general guide for
authoring a new address space or redesigning an existing one.

## References

- `make migrate` → `builder/base/migrateYaml.py` — the automated converter
  this skill backstops; `pysrc/migrateAddressControl.py` is its Phase B address
  pass and the source of the `manual TODO:` messages quoted here.
- `builder/base/config/schema.yaml` — accepted YAML fields for
  `blocks.addressBlock`, `instanceGroups`, and `addressObjects`.
- `builder/base/pysrc/processYaml.py` — schema hooks, project-config
  normalization, and port validation.
- `manage-address-space.md` — the legacy address-control skill; still
  applies to projects that have not yet migrated.
- `design-architecture.md` — block hierarchy and wiring conventions
  that the new schema slots into.
- `design-yaml-includes.md` — include direction and load-time scope.

## When to Use

- Converting an existing project's `addressControl.yaml` `AddressGroups`
  into per-block `addressBlock:` declarations.
- Moving legacy `InstanceGroups:` and `AddressObjects:` into
  `project.yaml` under the new spellings as part of that conversion.

If the project is staying on the legacy schema, use
`manage-address-space.md` instead. If the project is already on the new
schema and only needs ordinary address-space edits, use the design and
address-management skills instead of this migration skill.

## Core Rules

1. Preserve the legacy topology. Each live legacy `AddressGroups:` row
   becomes one router block with a top-level `addressBlock:` field.
2. `primaryDecode`, `varTypeContext`, and `decoderInstance` from the
   legacy `AddressGroups` row do not migrate. The primary router is
   inferred from the router hierarchy; `varType` is resolved in the
   router block's own scope; the router instance is resolved by
   container-locality.
3. Do not mix legacy `addressControl:` with authored `addressBlock:`.
   A project that declares any `addressBlock:` must remove the
   `addressControl:` pointer from `project.yaml`. The only dual
   spelling allowed during migration is for address-policy sections:
   legacy `InstanceGroups:` / `AddressObjects:` may overlap with
   `project.yaml` `instanceGroups:` / `addressObjects:` if the rows
   are identical.
4. Make the minimum edits required to express the
   existing address topology in the new schema. Do not create new
   user YAML files or reorganize unrelated declarations; edit the
   files that already author the relevant blocks, interfaces,
   policy sections, and project config.

## Migration Steps

### Step 1 — Inventory the legacy declarations

Open the project's `addressControl.yaml`. Record:

- Each `AddressGroups:` row, its key fields (`addressIncrement`,
  `maxAddressSpaces`, `varType`, `enumPrefix`), and the
  `decoderInstance` it names.
- The legacy `RegisterBusInterface:` value, if present. This becomes
  the router `addressBlock:` `upstreamPort` and `registerDecoderPort`
- The `InstanceGroups:` and `AddressObjects:` sections.

For each `decoderInstance`, follow the instance row in the
architecture YAML back to the router block type. That block type is
the one that will grow an `addressBlock:`.

Legacy `AddressGroups:` rows can also appear with **no** `decoderInstance:`
field and with no instance row using them as `addressGroup:`. Those
groups are dormant — they describe an address space the project does
not actually decode. Drop them during migration; do not author a
matching `addressBlock:`. (A still-referenced group with no router is
a project error; the post-parse pass will diagnose it.)

Note that `InstanceGroups:` is independent of `AddressGroups:`. The
legacy `InstanceGroups:` section frequently contains rows that have
nothing to do with the router hierarchy (for example a `blocks:` row
used for general instance enumeration). Carry every active `InstanceGroups:`
row across to the new `instanceGroups:` spelling in `project.yaml`
(Step 4), not just the row matching the address-decoder group.

### Step 2 — Place the address-bus interface so every router can see it

Walk each router file and check whether the interface (typically
`apbReg`) and its supporting types/structures are already visible
through the existing `include:` chain. If they are, leave them alone.

If some router's file does not see the interface, **relocate** the
interface, its structures, and their types into a file that satisfies
the constraint for every router. Use an existing shared or router file
that already fits the include graph; do not create a new user YAML file
just to hold migrated declarations.

In practice, move the declarations into the deepest existing router or
shared file that all consuming router files already see through normal
include direction.

Do not give a router file a new `include:` directive pointing at the
top integration file — that inverts the include direction and breaks
parsing.

After the move the `DWORD` / `apbAddrT` / `apbDataT` constants and
types simply live wherever the address-bus interface they support
now lives.

**Tool report item.** This step resolves the converter's
`TODO_INTERFACE_SCOPE` items: `Router block '<block>' (file <file>) has no
addressBus: true interface authored in its load-time scope.` The tool emits the
`addressBlock:` but cannot relocate the interface (that requires reasoning about
the include graph), so it reports the router and leaves the placement to you.

### Step 3 — Declare `addressBlock:` on each router

For every router block, add a top-level `addressBlock:` field.
Copy the legacy row's body verbatim except for the retired fields:

```yaml
blocks:
    topRegRouter:
        desc: "Top register-bus router"
        hasVl: true
        hasMdl: true
        hasRtl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
```

Do not author `primaryDecode:`, `varTypeContext:`, or
`decoderInstance:`.

If the legacy file named `RegisterBusInterface:`, carry it into
`upstreamPort:` and `registerDecoderPort:`. These fields may be omitted
only when the router should use the schema default interface name.

**Tool report item.** This step resolves the converter's
`TODO_ROUTER_RESOLUTION` items, which the tool reports in one of two forms and
will not author for you:

- `AddressGroups row '<group>' is referenced by an instance but names no
  decoderInstance, so its router block cannot be resolved — author addressBlock:
  by hand — see address-migration.md Step 3.`
- `AddressGroups row '<group>' decoderInstance '<inst>' does not resolve to a
  router block — author addressBlock: by hand — see address-migration.md
  Step 3.`

For each, identify the router block by following the named (or intended)
`decoderInstance` back through the architecture YAML per Step 1, then author the
`addressBlock:` shown above on that block.

Nested routers get their own `addressBlock:` row in the same shape,
with the appropriate `addressGroup:`. Edit the nested router's block
declaration in place in whatever file already authors it; do not split
it out.

If you see the diagnostic `Router block '<name>' (file <file>) has no
addressBus: true interface authored in its load-time scope`, the
nested router's file does not see the address-bus interface — revisit
Step 2's placement decision rather than adding `include:` directives
or creating new files.

### Step 4 — Move address-policy sections to `project.yaml`

Move `InstanceGroups:` and `AddressObjects:` from
`addressControl.yaml` into `project.yaml` under their new spellings:

```yaml
# project.yaml
instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_
    blocks:
        varType: blockID
        enumPrefix: BLOCK_TOP_

addressObjects:
    memories:
        alignment: memsize
        sizeRoundUpPowerOf2: true
        sortDescending: true
    registers:
        alignment: 8
        sortDescending: true
```

Carry **every active** legacy `InstanceGroups:` row across, not just the
address-decoder group. Rows like `blocks:` in the example above are
unrelated to the router hierarchy but are still consumed by the
generator for instance enumeration; dropping them produces a missing-
symbol failure later in generation. Do not activate commented example
rows during migration.

These fields use the same row bodies as the legacy sections but lower
camel-case section names. `instanceGroups:` rows have `varType` and
`enumPrefix`; `addressObjects:` rows have `alignment`,
`sizeRoundUpPowerOf2`, and `sortDescending`.

If both legacy and new spellings of these two policy sections are
present, the validator errors on any disagreement and names both files.
Agreement passes silently, which is useful while converting one
project. The completed migration should leave the policy sections in
`project.yaml`.

### Step 5 — Leave `postProcess:` to the base config

Prefer removing any existing `postProcess:` override entirely. The base
config already includes the standard scripts in the correct order. The
merge rules treat lists as `list_append`, so any base script repeated
in the project's `postProcess:` runs twice.

A typical legacy `project.yaml` carries an override block like:

```yaml
# project.yaml (before — typical legacy override)
postProcess:
    - $a2c/config/postParseRegister.py
    - $a2c/config/postParseChecks.py
```

Delete the entire block as part of this migration; the base config's
`postProcess:` is the canonical list.

If a project must keep a `postProcess:` block (for additional
project-specific scripts), it must contain only those project-specific
entries — never the base scripts.

### Step 6 — Retire `addressControl:`

Before any authored `addressBlock:` is committed, remove the
`addressControl:` pointer from `project.yaml`. The new per-block router
schema and legacy project-wide `AddressGroups:` schema are mutually
exclusive.

**Do not delete `addressControl.yaml` by hand.** `make migrate` owns that
delete: it removes the file on the run that finds the project clean, and while
manual TODOs remain it deliberately keeps the file as reference and reports
`DELETE_DEFERRED` saying so. Because the pointer is removed as soon as the
routing is accounted for, the next run removes the leftover on its own. A
survivor after a non-clean run is expected, not a failure — resolve the reported
TODOs and re-run rather than deleting it.

The one thing to check by hand is references: if another project still names the
file, search for any remaining `addressControl:` pointer or direct reference
before the final run.

### Step 7 — Regenerate and diff

Run the project's normal build:

```text
make db
make gen
```

Compare the generated SystemC and SystemVerilog output to the
pre-migration snapshot. Byte-identical output is the goal; any
deliberate naming or context change must be reviewed.

## Migration Diagnostics

If conversion fails, focus on mistakes introduced by the migration
rather than redesigning the address space. The generator fails the
build and names both sides of the offending relationship. The
diagnostics below are grouped by the stage that emits them.

These diagnostics are the same vocabulary the `make migrate` tool uses: the
converter's `manual TODO:` messages (`TODO_INTERFACE_SCOPE`,
`TODO_ROUTER_RESOLUTION`, `TODO_LEAF_REGISTER_PORTS`) quote the generator
diagnostics below word for word, so a reported TODO and the eventual build error
for the same unresolved relationship read identically.

A note on `registerPorts:`: a reusable-IP leaf (one whose
`<block>Base.cppm` must carry its own register-bus interface) declares a
single `registerPorts:` row naming that interface. A plain top-down
leaf needs no `registerPorts:` — it infers its register bus from the
serving router. The first group below only applies when the migration
touches a leaf that declares `registerPorts:`.

**Tool report item.** The converter routes its `TODO_LEAF_REGISTER_PORTS`
items here — `Routed leaf block '<leaf>' (instance '<inst>', served by router
'<router>' for group '<group>') needs a registerPorts: declaration authored by
hand — see the registerPorts: note under Migration Diagnostics in
address-migration.md.` Authoring `registerPorts:` is a judgment call, not a
mechanical edit: a plain top-down leaf needs no `registerPorts:`, and only a
reusable-IP leaf must author one, per the rule just above.

**It is asked twice, in two forms.** `TODO_LEAF_REGISTER_PORTS` is computed from
the legacy `AddressGroups` table, which the migrating run consumes and deletes,
so it can only be raised on that one run — and it blocks the stamp while it is.
From then on the same set is recomputed from the migrated schema and re-reported
every run as `ADVISORY_LEAF_REGISTER_PORTS`:

```text
Advisory - routed leaves with no registerPorts: (informational; does not block the stamp)
    top.yaml:14  ADVISORY_LEAF_REGISTER_PORTS  routed leaf 'leafA' (instance
    'uLeafA', group 'top') declares no registerPorts:, so its register bus is
    inferred from the router 'apbDecode'. ...
```

The advisory cannot block, because a top-down leaf is a legitimate answer and
blocking on it would leave such a project permanently un-stampable. It also
never clears itself: it stops only when the leaf declares `registerPorts:` or
stops being routed. So a leaf you have decided is top-down keeps appearing, by
design — that line is a statement of what the design resolved to, not an
outstanding task. Read it once per leaf and move on.

### `registerPorts:` / `addressBlock:` authoring (parse time)

- A block `declares both` `addressBlock:` and `registerPorts:`. These
  are `mutually exclusive`: a block is either a router (`addressBlock:`)
  or a routed leaf (`registerPorts:`). Remove whichever field does not
  belong on that block.
- A leaf `declares multiple` `registerPorts:` rows. Blocks support
  `exactly` one register-bus ingress today; collapse the entries to a
  single row.
- A `registerPorts:` row names an interface whose `interfaceType` is
  not `addressBus: true` (for example `push_ack`). Point the row at the
  register-bus interface (`apb`), whose `interface_defs` entry carries
  `addressBus: true`.
- A `registerPorts:` row's interface is not visible in the leaf's
  load-time scope: `no interfaces row named` ... in
  `any context processed before` this one. Author or `include:` the interface in
  the leaf's own scope so its `<block>Base.cppm` is self-contained.

### Router topology (post parse)

- Two router blocks declare the same `addressGroup` (the diagnostic
  reports the group `duplicates a prior addressBlock:`). Rename one, or
  merge the two router block types if the duplication was accidental.
- A router block declares `addressBlock:` but has no instance in the
  design (`Router blocks declare addressBlock:` ... but the named block
  has no instance). Instantiate the router, or drop its `addressBlock:`.
- A router block has more than one instance (`Multi-instance` routers
  serving one group are not supported). Use distinct router blocks and
  address groups instead of reinstantiating one router.
- Zero or multiple primary-router candidates:
  `Multiple candidate primary routers` or
  `No primary router could be inferred`. Adjust the router declarations
  so the migrated legacy hierarchy still has exactly one top router.
- A routed leaf instance sits in a container
  `not served by any router`. Place the leaf under a routed container, or add the serving
  router for that container.
- `Router block '<name>' (file <file>) has no addressBus: true
  interface authored in its load-time scope.` The router block's
  YAML file does not see a register-bus interface. Move the interface
  declaration into an existing router or lower-level/shared file the
  router file already includes. Do not include the parent integration
  file from the nested router file.

### Register-bus compatibility (validation)

- A `Register-bus dispatch` where the leaf and router resolve different
  `interfaceType` values (the diagnostic notes they must share the
  `same interface meta-protocol` and points at a `protocol changer`).
  Cross-`interfaceType` adaptation needs an explicit protocol-changer
  block (out of scope); make both sides the same `interfaceType`.
- A `Register-bus dispatch` where the leaf and router share an
  `interfaceType` but disagree on `per-field _bitWidth` (the diagnostic
  names the offending `field index` and both `_bitWidth` values, and
  prints a `parent side` / `child side` block naming each interface, its
  declaring file, owning project, block and resolved variant). Align the
  field widths of the leaf and router register interfaces.

  These checks fire whether or not the leaf and router interfaces share
  a name; matching names do not exempt a dispatch from validation.

## Validation

- `make db` succeeds; the project loads under the new schema.
- `make gen` succeeds; generated output matches the pre-migration
  snapshot or its differences are reviewer-approved.
- Tandem / model regressions (for example `make step6` in the
  proto-model build) continue to pass.
- Each new diagnostic exercised by an intentional negative test
  reports the expected file and field.
