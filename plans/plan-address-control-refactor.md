# Plan: `addressControl` Refactor — Leaf `registerPorts:` and Router `addressBlock:`

This plan implements the design direction recorded in
[`research-address-bus-distribution.md`](./research-address-bus-distribution.md):
the project-wide `addressControl.RegisterBusInterface` value and the
project-wide `AddressGroups` table are dissolved into per-block
declarations. Leaf blocks declare a `registerPorts:` map alongside
`ports:`; router blocks declare a top-level `addressBlock:` field that
carries the per-router attributes that today live in one row of
`addressControl.AddressGroups`.

The original rollout delivered the new authoring path end-to-end on
`examples/ip_test` while temporarily keeping the legacy
`addressControl.yaml` path available. That coexistence phase is historical:
Stage 8 retired `config/postParseRegister.py` and the legacy loader, and the
per-block schema is now the only accepted input.

The legacy `addressControl.yaml` path was treated as deprecated once
the new schema was available, then retired in Stage 8 (2026-06-12).
The decision was to **remove** the legacy path rather than carry
dual-spelling support indefinitely. The new schema (per-block
`addressBlock:` / `registerPorts:` plus `project.yaml`
`instanceGroups:` / `addressObjects:`) is now the only accepted input.

## Current Status

Stages 1 through 6 are **committed**. Stage 7 is **complete**
(2026-06-22): the Stage 7 checklist in the companion
`plan-address-control-test-coverage.md` is fully committed — Topology
Batch A/B, Batch C migrated-`ip_test` DB assertions, error Batch A/B,
the E3.1-E3.4 register-bus/independence diagnostics, the E3.3
no-`_global` invariant, and the skill-doc cross-check — with "No Stage 7
coverage rows remain open." Stage 8 is **complete** (2026-06-12) — see
the Stage 8 section for the executed steps and the two deviations from
the original outline (the `_global` exemptions were kept; the
no-in-tree-dependency gate was waived because example/fixture migration
is owned separately).

### Amendment 2026-06-12 — leaf `registerPorts:` is optional (inference)

The original Stage 4.4 / Stage 5.3 rule that a register-owning routed
leaf *must* declare `registerPorts:` (erroring on zero rows) is
**overturned**. The corrected contract:

- `registerPorts:` is the **boundary marker** for a bottom-up reusable
  IP — the only block kind that must declare it, so its `<block>Base.h`
  carries the register-bus interface in its own load-time scope. In
  `examples/ip_test` only the `ip` block declares it.
- A **top-down leaf** that owns registers/memories but declares no
  `registerPorts:` is valid. The post-parse pass **infers** its
  register-bus interface and canonical port from the serving router
  (the router's resolved upstream interface and `registerDecoderPort`),
  exactly as the legacy pass sourced them from the project-wide
  `RegisterBusInterface`. Implemented by `_leafRegisterBinding` in
  `config/postParseRegisterPorts.py`; the router-to-leaf dispatch now
  fires for a leaf that declares `registerPorts:` **or** that needs a
  synthesised handler (`blocksNeedingHandler`).
- `registerPorts:` is a **parse-time construct** consumed by
  projectCreate to infer connectivity. projectOpen must read only the
  resolved design and prop up nothing: `_registerBusInterfacePort` no
  longer reads the authored `registerPorts:` block-row field — routers
  read `addressBlock`, while synthesised handlers and routed leaves both
  read the leaf-to-handler `connectionMap` (one uniform path, authored
  and inferred alike). The dead `declaredRegisterPorts` view field was
  removed. The new-schema router upstream that fails to resolve locally
  now **errors** instead of falling back to `_legacyRegisterBusInterface`.

Coverage: `unittest/test_addrctl_top_down_leaf_infers.py` (T5.5) is the
positive inference fixture; the obsolete negative test
`test_error_leaf_no_register_port.py` (E2.6) was removed.

**Stage-5 follow-up (validation home) — RESOLVED 2026-06-12.**
`registerPorts:` is a block's register-bus declaration surface — "a
special case of `ports:` used to identify register ingress" — so
cross-interface checking uses the union `ports: ∪ registerPorts:`. The
gate splits by whether the bind has a declared-port surface:

- **Router→leaf** (authored reusable-IP leaf): now validated by
  `validatePorts`. Its connection loop reads the child port from `ports`
  first, then `registerPorts`; on a `registerPorts` match it emits a
  router+leaf-named "Register-bus dispatch ..." diagnostic and resolves
  the parent side from the router (other) end. The old `if authored:`
  `checkInterfacePair` in `config/postParseRegisterPorts.py` was removed;
  post-parse only emits the bind. E3.1/E3.2 now fail the build via
  `validatePorts` (verified).
- **Router→router** (nested router with its own
  `addressBlock.upstreamPort`): stays in `postParseRegisterPorts.py`.
  Both ends are `addressBlock:` routers with no `ports:`/`registerPorts:`
  surface, so the superset cannot reach it; the synthesis script that
  creates the bind keeps that one check. The guard is reachable (a nested
  router whose upstream interface is structurally incompatible with its
  parent fires it) and early-returns when interfaces match.

The decision deliberately avoids teaching the central validator about
synthesised data shapes (which would not scale per post-parse script);
folding `registerPorts:` into the port surface achieves the move without
that coupling.

`annotate` (projectOpen, `getBDCrossInterfaceBinds`) now derives the
register-bus child interface from the resolved leaf-to-handler
`connectionMap` (helper `registerBusChildBind`) rather than the
parse-time block-row `registerPorts:` field, removing the last
projectOpen read of that authored construct.

### Amendment 2026-08-07 — the `AddressGroups` registry key is `(projectName, group)`

Delivered by [`plan-addressgroup-qualification.md`](./plan-addressgroup-qualification.md),
which owns the design and the rationale. Recorded here because this plan owns the
`addressBlock:` schema and `_post_registerAddressBlock`.

- **The registry key is the tuple `(owningProjectName, group)`, not the bare
  group string.** All four dicts `_post_registerAddressBlock` populates
  (`counterGroup['AddressGroups']`, `counterGroupControl['AddressGroups']`,
  `counterData['AddressGroups']`, `self.addressControl['AddressGroups']`) are
  keyed on that tuple. The owning project is
  `contextOwningProject[<declaring yamlFile>]`; ownership is assigned before
  `processYamls`, so the lookup is parse-time safe. Diagnostics spell the key
  `project::group` via `addressGroupLabel()`. **Do not reintroduce the flat key** —
  it is what made two independently authored projects that each name a group
  `top` uncomposable.
- **The duplicate-declaration check is within-project, not build-wide.** It fires
  only when one project declares the same group name on two router blocks, and
  names both declaring blocks, both declaring files, and the project. Two
  projects each declaring `top` is legal.
- **Reference resolution is project-scoped.** `_auto_addressGroup` resolves an
  `addressGroup:` reference against `(contextOwningProject[referring file],
  name)` only; there is no outward fall to ancestor projects. An unresolved
  reference is an error.
- **Consumers form the tuple themselves** from the row's `_context` (the
  `calcAddresses` space check, the nested-decoder containment check,
  `generateAddressEnums`) or from `yamlFile` (`_auto_addressGroup`,
  `_auto_addressID`, `_post_registerAddressBlock`). `getBDAddressDecode` forms it
  from the router block row's `_context` and publishes `routedInstances`.
- **`varType` / `enumPrefix` are NOT qualified, and are gated instead.** The
  authored values reach generated text unchanged, so the new build-wide
  `validateAddressGroupEnumIdentity()` (called from `projectCreate` immediately
  before `generateAddressEnums`) rejects two groups sharing either field. The
  firmware surface is one flat `fw_ns` namespace, so a shared `varType` would
  otherwise redefine the enum or silently bind one enumerator to two address IDs.
  This also closes the pre-existing hole where two *differently named* groups
  shared one `varType`, which was never checked.
- **No schema change, no YAML migration.** Authored YAML still spells
  `addressGroup: top`.

## Related Documents

| Document | Relevance |
| -------- | --------- |
| [`research-address-bus-distribution.md`](./research-address-bus-distribution.md) | Canonical design discussion; this plan does not re-derive any of its decisions. |
| [`plan-variant-config-unification.md`](./plan-variant-config-unification.md) | Stage 5 (bottom-up `ports:` schema) and the deferred-decision text on lines 1148-1189 that this plan closes. |
| [`research-multi-config-bindings.md`](./research-multi-config-bindings.md) | D10 (bottom-up port declaration) and Q10/R2 (cross-interface bind through the thunker pool) — both load-bearing for the leaf `registerPorts:` path. |
| [`plan-foundation-address-decode.md`](./plan-foundation-address-decode.md) | Original `addressControl.yaml` schema; this plan supersedes its `AddressGroups` and `RegisterBusInterface` sections. |
| `config/postParseRegister.py` | Legacy post-parse pass kept available during migration. |
| `pysrc/processYaml.py::getBDAddressBus` / `getBDIncludes` / `validateDeclaredPorts` / `validatePorts` | Four downstream consumers updated in lockstep with the new declarations. |
| `rules/skills/address-migration.md` | Canonical AI skill that guides a user through the new authoring path and the conversion from the legacy schema. |
| [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md) | Companion test plan; owns the Stage 7 topology matrix, the error-case matrix, the coverage map, and the remaining Batch C / skill-doc status checklist. |

## Goals

- Leaf blocks become self-describing on the register bus. A leaf used
  in two projects with different register-bus interfaces is authored
  once, and `<block>Base.h` cites only types defined in the leaf's
  own load-time scope.
- Router blocks own the per-address-group attributes (`addressGroup`,
  `addressIncrement`, `maxAddressSpaces`, `varType`, `enumPrefix`,
  `upstreamPort`, `registerDecoderPort`). Discovery of routers
  happens by walking `prj.data['blocks']` rather than by reading a
  project-wide table.
- The Stage 5 partial-declaration exemption that classifies leaf
  register ingress under `_context: '_global'` is retired. Generated
  router-dispatch and register-handler ports remain generator-owned
  but are classified explicitly rather than by `_global` context.
- The legacy `addressControl.yaml` input remains accepted during
  migration. New-schema and legacy projects coexist within the same
  generator build.

## Non-Goals

- **Cross-`interfaceType` adaptation** (for example `apb` to
  `axiLite` on the register bus) is out of scope; the wiring pass
  emits a diagnostic that names both sides and points the user at an
  explicit protocol-changer block. The schema for that block is
  itself out of scope.
- **Multi-`registerPorts:` mapping syntax**. The schema accepts a
  plural map, but only the single-entry case is supported by the
  initial migration. Multiple entries produce a diagnostic.
- **Multi-instance routers** serving the same group. Today disallowed
  implicitly; the post-parse pass continues to disallow it
  explicitly.
- **Register-handler synthesis shape**. The `<block>_regs` handler
  block, its `isRegHandler: true` flag, and the synthesised handler
  instance keep their current shape. Only the source of the
  register-bus interface and port names changes.

## Architectural Overview

The work splits into six complete committed stages, one partial
coverage stage, plus Stage 8 (legacy retirement), completed 2026-06-12.
Stages 1 through 5 deliver the new authoring path behind a runtime
switch (presence of `addressBlock:` on at least one block); the
legacy path runs unchanged when the new declarations are absent.
Stage 6 migrates the `ip_test` exemplar. Stage 7 owns the
hierarchical test coverage defined in
[`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md),
which exercises the new post-parse pass against the full topology
matrix and pins every Stage 5.3 diagnostic to a failing unit
fixture. Stage 7 is **partial** until the companion plan's remaining
Batch C and skill-doc items are closed. Stage 8 (legacy retirement) is
**complete** — the legacy path was removed rather than carried as
dual-spelling support; the new schema is the only accepted input.

```
S1 schema  -> S2 project.yaml policy  -> S3 view-helper updates        [COMPLETE]
   |                                       |
   |                                       v
   +-------------------------------> S4 new post-parse script           [COMPLETE]
                                           |
                                           v
                                    S5 validation updates               [COMPLETE]
                                           |
                                           v
                                    S6 ip_test migration                [COMPLETE]
                                           |
                                           v
                                    S7 hierarchical test coverage       [PARTIAL]
                                           |
                                           v
                                    S8 legacy retirement                [COMPLETE]
```

S1 and S2 are independent and may land in either order; S3 has a soft
dependency on both. S4 requires S1 in place. S5 is a follow-on to S4.
S6 is the first end-to-end exercise of S1 through S5. S7 reuses the
migrated `ip_test` from S6 as one of its example fixtures and adds
the unit-test matrix on top. Stage 8 (legacy retirement) was taken as a
separate decision and completed 2026-06-12.

## Stage 1 — Schema additions

**Files:** `builder/base/config/schema.yaml`,
`builder/base/pysrc/processYaml.py` (schema loader / validator).

### 1.1 — `blocks.registerPorts:`

Add an optional `registerPorts:` node on `blocks:`, parallel in shape
to the existing `ports:` node. Each entry names a leaf-owned
register-bus ingress port and the interface it consumes. Direction is
not authored; every `registerPorts:` entry is semantically `dst`.

```yaml
blocks:
  # ...
  registerPorts:
    _attribs: [optional, multiple]
    port: key
    interface:
      _type: required
      _validate:
        section: interfaces
        field: interface
```

Additional load-time constraints, enforced in `projectCreate`:

- The interface named by each row must be defined in the block's own
  load-time scope: the block's YAML file or a file the block
  transitively pulls in through `include:`. The structures the
  interface carries must be defined in that same scope. This is the
  reusability invariant for `<block>Base.h`.
- The interface's `interfaceType` must resolve to an
  `interface_defs` entry whose `addressBus: true` (see Stage 1.5).
  Today only `apb` carries the flag; the set may grow without
  further schema edits as new register-bus protocols are added.

The `direction` field is intentionally absent from `registerPorts:`.
The parser/view layer treats every leaf register ingress as `dst`
when it emits or validates the corresponding bind. If a future design
needs source-like register-bus behavior, that should be a new schema
extension rather than a second value accepted by this field.

A block that declares `registerPorts:` does **not** have to declare
`ports:`. The two maps are independent. A leaf whose only externally
visible interface is its register bus may declare `registerPorts:`
on its own; the block is treated as a bottom-up declarer (Stage 5
inference still applies to any non-register interface it may
acquire later through top-down wiring). Conversely, a block may
continue to declare `ports:` without `registerPorts:` when it has no
register bus surface.

### 1.2 — `blocks.addressBlock:`

Add an optional top-level `addressBlock:` field on `blocks:`. Its
body carries the row that today lives under
`addressControl.AddressGroups`.

```yaml
blocks:
  # ...
  addressBlock:
    _attribs: [optional, post(registerAddressBlock)]
    addressGroup:
      _type: required
    addressIncrement: required
    maxAddressSpaces: required
    varType: required
    enumPrefix: required
    upstreamPort: optional("apbReg")
    registerDecoderPort: optional("apbReg")
```

Notes:

- `varTypeContext` from the legacy row is intentionally absent. The
  `varType` is resolved in the router block's own load-time scope.
- `primaryDecode` from the legacy row is intentionally absent. The
  post-parse pass infers the primary router by hierarchy walk (see
  Stage 4).
- `decoderInstance` from the legacy row is intentionally absent. The
  router instance is resolved by container-locality at wiring time.
- A block that declares `addressBlock:` must not declare
  `registerPorts:`. The router block's upstream and downstream
  register-bus ports are inferred from connections, not authored.

The `post(registerAddressBlock)` callout maps to
`processYaml.py::_post_registerAddressBlock`. While the block row is
processed, this post function registers `addressBlock.addressGroup`
into the same normalized address-group state that legacy
`validateAddressControl()` populates today: `counterGroup['AddressGroups']`,
`counterGroupControl['AddressGroups']`, `counterData['AddressGroups']`,
and the persisted `ADDRESS_CONFIG.AddressGroups` view. This is
deliberately done during normal YAML processing, not by a separate
pre-scan. The project already requires block definitions to be
processed before instance rows, so `_auto_addressGroup` and
`_auto_addressID` can continue to validate and allocate instance
placement against the registered groups. Duplicate `addressGroup`
declarations error in `_post_registerAddressBlock` and name both router
blocks. **Amended 2026-08-07:** the registry is keyed on
`(owningProjectName, group)` and the duplicate check is *within-project*;
see the amendment above.

### 1.3 — `interface_defs.addressBus` attribute

The `interface_defs:` node gains an optional boolean field:

```yaml
interface_defs:
  # ...
  addressBus: optional(false)
```

The flag identifies an interface type as a register-bus / address-bus
meta-protocol. A subsequent edit to
`builder/base/interfaces/apb/apb_if.yaml` sets `addressBus: true` on
the `apb` entry. The schema reuses the same attribute to validate
both `registerPorts:` (Stage 1.1) and any future router upstream
inference that wants to confirm the interface is appropriate. No
allowlist constant inside `processYaml` is needed; the truth lives
on the interface definition itself.

A diagnostic surfaces when a `registerPorts:` row points at an
interface whose `interfaceType` resolves to `addressBus: false`,
naming both the offending row and the interface definition.

### 1.4 — Address-policy fields on `project.yaml`

Add optional top-level `instanceGroups:` and `addressObjects:`
sections on `project.yaml`, accepting the same row shape as today's
`addressControl.InstanceGroups` and `addressControl.AddressObjects`.
This is Stage 2's place to land, but the schema definitions go in at
Stage 1 so both spellings are accepted before any consumer change.

### 1.5 — Parse-time checks outside schema validation

Keep custom parse-time checks limited to invariants that the existing
schema engine cannot express. Do not duplicate built-in behavior:
required / optional field handling, unknown-field rejection,
`_validate.values`, `_validate.section` resolution, context-scoped
lookups, and generated `*Key` fields all remain owned by the schema
engine.

The new custom checks are:

- A block must not declare both `addressBlock:` and `registerPorts:`
  (router-versus-leaf separation). This is a cross-field block check,
  not a field validator.
- A block must not declare more than one `registerPorts:` row during
  the initial migration. The schema shape remains plural for the
  future extension, but Stage 1 rejects multiple entries at
  block-parse time so later wiring does not have to choose a row.
- A `registerPorts:` row's already-resolved `interfaceKey` must point
  to an interface whose resolved `interfaceTypeKey` names an
  `interface_defs` row with `addressBus: true`. This is the only
  meta-protocol gate; no additional in-code allowlist is needed.
- The legacy `addressControl.yaml`'s `InstanceGroups:` and
  `AddressObjects:` are accepted alongside `project.yaml`'s new
  spelling. If both are present with disagreeing values, project
  configuration normalization errors and names both files. If both
  agree, normalization passes silently.

No validator change is required to insist that `registerPorts:`
imply `ports:`. The two maps are independent.

## Stage 2 — Project-config migration

**Files:** `builder/base/pysrc/processYaml.py` (project-config
loader and `addressBlock:` custom processing), `builder/base/config/project.yaml`
(defaults), `builder/base/examples/*/arch/yaml/project.yaml`
(per-project defaults).

`instanceGroups:` and `addressObjects:` are read directly from
`project.yaml` and persisted into the existing config blobs
(`ADDRESS_CONFIG` is the natural home; renaming is out of scope for
this stage). The legacy `addressControl.yaml` reader continues to
populate the same blobs when those sections are present, with the
conflict rules listed in Stage 1.4.

`AddressGroups` are normalized from either source:

- Legacy projects keep loading `AddressGroups` from
  `addressControl.yaml`.
- New-schema projects populate `AddressGroups` incrementally from
  `blocks.*.addressBlock` through the Stage 1.2 custom hook.

The two `AddressGroups` sources are mutually exclusive. If any block
declares `addressBlock:`, the project must not also declare a legacy
`addressControl:` file with `AddressGroups:`. A project migrates
`AddressGroups` all at once; partially converted projects error.

Project creation normalizes both spellings into the same persisted
view, so downstream consumers do not branch on which spelling fed
them.

## Stage 3 — Block-data view changes

**Files:** `builder/base/pysrc/processYaml.py`
(`projectOpen.getBDAddressBus`, `getBDIncludes`, view helpers),
`builder/base/templates/systemc/constructor.py`,
`builder/base/templates/systemc/blockRegs.py`,
`builder/base/templates/systemVerilog/moduleRegs.py`.

The view changes are additive in this stage; the legacy fields are
not removed until Stage 8.

### 3.1 — Split `registerBusInterface` into two view fields

- `addressDecode.registerBusInterface` continues to name the
  interface definition used for type selection on the router or the
  generated register-handler.
- A new `addressDecode.registerBusPort` field names the port object
  templates bind or read on the block-data view. For a router this
  is the resolved upstream port; for a generated register handler
  this is the handler-side downstream port.

Both fields are populated in legacy and new-schema modes. Legacy mode
sets `registerBusPort` to the legacy
`addressConfig['RegisterBusInterface']` value so existing output stays
stable. New-schema mode may set `registerBusInterface` and
`registerBusPort` to different values; templates must use
`registerBusInterface` only for interface/type lookup and
`registerBusPort` for emitted port references.

### 3.2 — Source the interface from per-block declarations

- A router block's view reads its `addressBlock:` row directly and
  resolves the upstream interface from the inferred upstream port,
  not from `addressConfig['RegisterBusInterface']`.
- A generated register-handler view reads the selected leaf
  `registerPorts:` entry's interface for its incoming side and the
  router's `registerDecoderPort` naming for the handler-side port
  surface.
- Legacy projects continue to fall back to
  `addressConfig['RegisterBusInterface']` until Stage 8. The fallback
  is a single helper (`_legacyRegisterBusInterface(view)`) so Stage 8
  removes one call site.

### 3.3 — `getBDIncludes`

The current code path that aggregates the project-wide
`RegisterBusInterface` structures for apb-router blocks (line 2188
range) is replaced by an aggregation over each router's resolved
upstream interface. For new-schema projects the resolved interface
comes from the router's own context, not `_global`. The legacy
project-wide fallback is preserved during migration.

### 3.4 — Block-view register-port and `addressBlock:` exposure

- A `declaredRegisterPorts` field appears on every block view,
  parallel in shape to `ports:`. For new-schema leaves this is the
  authored YAML `registerPorts:` map; for legacy leaves this is empty.
  The existing block-data `registerPorts` view key remains the
  synthesized register-connection port aggregate used by register
  handler templates.
- A `addressBlock:` field appears on every router block view. For
  new-schema routers this is the authored row, normalized with
  defaulted `upstreamPort` and `registerDecoderPort`. For legacy
  routers (those resolved through the project-wide `AddressGroups`)
  the view helper synthesises an equivalent record from the legacy
  table so templates have a single shape to read.

The template updates in this stage replace every use of
`addressDecode.registerBusInterface` as an emitted port name with
`addressDecode.registerBusPort`. No template should branch on legacy
versus new mode.

## Stage 4 — New post-parse script

**Files:** `builder/base/config/postParseRegisterPorts.py` (new),
`builder/base/config/project.yaml` (post-parse registration),
`builder/base/pysrc/processYaml.py` (post-parse dispatch).

`postParseRegisterPorts.py` runs after YAML parsing and before
block-data view construction, in the same pipeline slot as
`postParseRegister.py`. The two are mutually exclusive: if any block
declares `addressBlock:`, the new script runs and the legacy script
is skipped; otherwise the legacy script runs unchanged.

The new script performs the following steps:

1. **Build the router index.** Walk `prj.data['blocks']` for rows
   that carry `addressBlock:`, indexed by
   `addressBlock.addressGroup`. Normalize defaulted
   `upstreamPort` / `registerDecoderPort` to `apbReg` if absent.
   Error if two router blocks declare the same `addressGroup`
   (**amended 2026-08-07:** within the same project — the group registry
   is keyed on `(projectName, group)`).

2. **Resolve the router instance per group by container-locality.**
   Walk `prj.data['instances']` for instances whose `instanceType`
   resolves to a known router block. Record the qualified router
   instance and its container. Error if a router block has more
   than one instance for the same group (multi-instance routers are
   deferred).

3. **Infer the primary router.** A router is the primary if and
   only if its instance's container is not itself routed by another
   router (the router-tree root). Exactly one primary must exist; if
   zero or two-or-more candidates are found, error with a diagnostic
   that lists them.

4. **Synthesise the `<block>_regs` handler block, instance, and
   leaf-to-handler `connectionMap` per routed block.** Same shape as
   today (the script reuses the helper that `postParseRegister.py`
   uses today, refactored out of that file into a shared helper),
   but the connection map names the interface and ports separately:
   - `interface` is the interface from the leaf's selected
     `registerPorts:` row, or — for a top-down leaf with no
     `registerPorts:` — the serving router's resolved register-bus
     interface (see the 2026-06-12 amendment).
   - `port` is the leaf's selected `registerPorts:` key, or the
     router's `registerDecoderPort` when inferred.
   - `instancePort` is the owning router's normalized
     `registerDecoderPort`, defaulting to `apbReg`.
   More than one `registerPorts:` row errors (parse-time block hook).
   Zero rows is **not** an error: the leaf infers its register-bus
   interface and canonical port from the serving router.

5. **Emit the router-to-leaf connection per routed instance.** The
   source is `<registerDecoderPort>_<dst-instance>` on the router;
   the destination is the leaf instance's `registerPorts:` entry.
   `registerDecoderPort` is a port-name convention, not an authored
   interface reference, so the script must not resolve it through
   `interfaces:` or require an include solely for that name. The
   emitted connection's interface is the selected leaf
   `registerPorts:` interface; Stage 5 validates the actual authored
   register interfaces and rejects unsupported mixed downstream
   protocol use until the protocol-changer design exists.

6. **Emit the parent-router-to-child-router connection per nested
   router.** Same shape as step 5, with the child's
   `addressBlock.upstreamPort` driving the child-side `instancePort`.
   `upstreamPort` is likewise a port-name convention for this stage;
   it is not resolved as an `interfaces:` row by the post-parse
   script.

7. **Tag synthesised binds with their owning block's YAML context.**
   Router upstream ports and dispatch ports carry the router block's
   context; handler-internal binds carry the generated handler
   block's context. The script must never assign `_context: '_global'`
   to a bind whose owner is a known block.

The script returns the same shape of dict that
`postParseRegister.py` returns today (`blocks`, `instances`,
`connections`, `connectionMaps`) so the existing merge step in
`projectCreate` consumes it unchanged.

### 4.1 — Pre-Stage 5 drift reconciliation

Before Stage 5 starts, re-check the executed Stage 4 script against
the contract above. Two behaviors are load-bearing for validation and
must not be pushed into validator work:

- **Router-to-leaf dispatch is per `registerPorts:` instance, not per
  handler-bearing block.** A leaf that declares `registerPorts:` but
  owns no registers or memories still has a register-bus surface. The
  post-parse pass must emit the router-to-leaf connection for that
  instance even though it does not synthesise a `<block>_regs`
  handler. Validation should not have to infer or repair a missing
  connection.
- **Router port names are not interface names.** `upstreamPort` and
  `registerDecoderPort` remain port-name conventions. Router-to-router
  and router-to-leaf emitted rows must resolve their `interface` from
  the authored router / leaf interface declarations, not by treating
  those port-name strings as `interfaces:` keys. Stage 5 validates the
  resolved interfaces; it must not encode a fallback that preserves a
  mistaken port-name-as-interface shape.

## Stage 5 — Validation updates

**Files:** `builder/base/pysrc/processYaml.py`
(`validateDeclaredPorts`, `validatePorts`).

Stage 5 is scoped to the new-schema register-bus path. It does **not**
retire, tighten, or add coverage for the legacy `addressControl.yaml`
path. Existing legacy `_context: '_global'` exemptions remain exactly
as they are so un-migrated projects keep the Stage 1-4 coexistence
behavior.

Current status: the `registerPorts:` / `ports:` independence behavior
from 5.1 is **committed**. The E3.1 / E3.2 register-bus compatibility
diagnostics are **committed** and **verified** by
`unittest/test_error_register_interface_type_mismatch.py` and
`unittest/test_error_register_packed_form.py`; the router→leaf check now
runs in `validatePorts` via the `ports: ∪ registerPorts:` superset (see
the resolved Stage-5 follow-up above), while router→router remains in
`postParseRegisterPorts.py`. The E1.5 out-of-scope diagnostic is
**committed** as a generic `_validate` enrichment rather than a
`registerPorts:`-only validator.

### 5.1 — `validateDeclaredPorts`

- Treat leaf register ingress as its own declaration surface:
  `registerPorts:`. The partial `ports:` declaration diagnostic must
  not require a duplicate `ports:` row for the same register-bus
  ingress. A block may declare `ports:` for non-register interfaces
  and `registerPorts:` for register ingress in the same file without
  either map being considered incomplete because of entries owned by
  the other map.
- The new register-plumbing path does not emit binds with
  `_context: '_global'`. Leaf register ingress is now authored in
  `registerPorts:`, so any validation for the new path should use that
  declaration directly rather than relying on the broad `_global`
  exemption.
- Router dispatch ports and generated register-handler internals are
  identified structurally from the new post-parse rows and the owning
  `addressBlock:` / `isRegHandler` blocks, not by a persisted marker
  field on each bind and not by special-casing legacy
  `RegisterBusInterface`.
- `_context: '_global'` is **not** retired. It remains a valid
  context for any other use today or in future. The change here is
  scoped: the new register-bus wiring stops minting `_global` rows
  and stops relying on the broad `_global` exemption for leaf
  register ingress. Legacy `postParseRegister.py` continues to emit
  `_global` rows for as long as it runs, and the existing exemption
  remains in place for that path.

### 5.2 — `validatePorts`

The register-bus packed-form check uses the union `ports: ∪
registerPorts:` as the child's declared-port surface (see the resolved
Stage-5 follow-up above). Concretely:

- The `validatePorts` connection loop reads the child port from `ports`
  first, then `registerPorts`. A `registerPorts` match is the routed
  leaf's register ingress; it resolves and compares the connection's
  parent interface (the router-side register interface) against the
  leaf's authored `registerPorts:` interface via `checkInterfacePair()`.
- The check runs even when the leaf and router name the same interface.
  Same-name binds with identical structures pass trivially, but
  parameterized widths and independently declared same-name interfaces
  are still resolved and compared.
- The existing `_global` exemption is unchanged. It still applies to any
  `_global`-tagged bind, including those emitted by the legacy
  `postParseRegister.py` path. The new wiring does not produce `_global`
  rows for register plumbing.

Router→leaf is **committed** in `validatePorts` (E3.1/E3.2 fail the
build there). Router→router has no declared-port surface on either end
and remains in `postParseRegisterPorts.py` via `checkInterfacePair()`.

### 5.3 — Diagnostic surface

The new diagnostics that must be present and tested:

- Leaf declares `registerPorts:` whose interface is outside the
  leaf's load-time scope.
- Leaf declares more than one `registerPorts:` row (parse-time block
  diagnostic).
- Two router blocks declare the same `addressGroup` (amended 2026-08-07:
  within one project).
- An `addressGroup:` reference names a group the referring file's own
  project does not declare (added 2026-08-07).
- Two address groups resolve the same `varType` or the same `enumPrefix`
  (added 2026-08-07, `validateAddressGroupEnumIdentity()`).
- Two router instances exist for the same group.
- Zero or multiple primary-router candidates.
- Leaf and router resolve to different `interfaceType` values.
- Leaf and router resolve to the same `interfaceType` but fail the
  packed-form check on resolved address or data width.
- A leaf whose register-bus ingress is declared only in
  `registerPorts:` passes partial-`ports:` validation without a
  duplicate `ports:` row.
- A bind emitted by the new post-parse pass carries `_context:
  '_global'` (repository regression guard).

Each diagnostic must name both sides of the offending relationship
and quote the file and field that the user must edit.

The first five bullets above are owned by Stage 1 / Stage 4
implementation and Stage 7 tests; Stage 5 only wires the final four
validator behaviors. Do not add new legacy-schema diagnostics as part
of this validation update.

Per the 2026-06-12 amendment, a register-owning routed leaf with **zero**
`registerPorts:` rows is **not** a diagnostic — it infers from the
serving router. (The earlier E2.6 "leaf has registers but no
registerPorts" error and its test were removed.)

## Stage 6 — Migrate `examples/ip_test` — **COMPLETE**

**Status:** All sub-stages 6.1 through 6.6 are complete. The
migration landed via base submodule commit
`16da8ca #116 migrate ip_test to addressBlock register routing`; the
`address-migration.md` skill received the iteration that Stage 6.6
requires.

**Files:** `builder/base/examples/ip_test/arch/yaml/*.yaml`,
with `addressBlock:` declarations on the `apbDecode` router in
`ip_top.yaml` and the `bridgeApbDecode` router in `ipBridge.yaml`.

The migration must be driven by the `address-migration.md` skill
(authored alongside this plan). The `ip_test` exemplar is the first
real exercise of the skill; using the skill to drive the work is the
acceptance test for the skill itself. If a step in the migration
cannot be completed by following the skill's written procedure, the
skill is incomplete or wrong and must be edited before Stage 6
proceeds. Each sub-step below names the skill step the implementer
should be following.

### 6.1 — Move `apbReg` and its structures into the router scope — **COMPLETE**

Follow `address-migration.md` Step 2 ("Promote the address-bus
interface").

- Move the `apbAddrT` / `apbDataT` types, the `apbAddrSt` /
  `apbDataSt` structures, and the `apbReg` interface into a scope
  visible to both router blocks. In the landed migration this shared
  register-bus interface lives in `shared_types.yaml`, which is pulled
  into `ip_top.yaml` and `ipBridge.yaml` through their existing include
  chains.
- Keep the `apbDecode` block declaration in `ip_top.yaml` and the
  `bridgeApbDecode` block declaration in `ipBridge.yaml`. No dedicated
  router YAML files were needed for the landed layout.

### 6.2 — Add `registerPorts:` to `ip.yaml` — **COMPLETE**

Follow `address-migration.md` Step 4 ("Declare `registerPorts:` on
each routed leaf").

- Add a leaf-scoped register-bus interface `ipReg` in `ip.yaml`,
  with its own `ipRegAddrSt` / `ipRegDataSt` structures and
  `ipRegAddrT` / `ipRegDataT` types. The interface declares
  `interfaceType: apb`.
- Declare `registerPorts: { regs: { interface: ipReg } }` on the
  `ip` block. The `ports:` map already exists.

### 6.3 — Add `addressBlock:` to each router — **COMPLETE**

Follow `address-migration.md` Step 3 ("Declare `addressBlock:` on
each router").

- `ip_top.yaml`: declare `addressBlock: { addressGroup: top,
  addressIncrement: 0x01000000, maxAddressSpaces: 16, varType:
  addr_id_top, enumPrefix: ADDR_ID_TOP_, upstreamPort: apbReg,
  registerDecoderPort: apbReg }` on the `apbDecode` block.
- `ipBridge.yaml`: declare `addressBlock: { addressGroup:
  bridge, addressIncrement: 0x00100000, maxAddressSpaces: 16,
  varType: addr_id_bridge, enumPrefix: ADDR_ID_BRIDGE_,
  upstreamPort: apbReg, registerDecoderPort: apbReg }` on the
  `bridgeApbDecode` block.
- The `ip` address group from today's `exampleAddress.yaml` is unused
  by instance placement and has no decoder. It is dropped during
  migration rather than converted to `addressBlock:`. The general
  migration rule is: unreferenced non-decoder legacy groups are
  removed; a still-referenced legacy group without a router is an
  error unless a future schema deliberately adds a replacement for
  that use case. The instance rows for `uIp0` / `uIp1` retain
  `addressGroup: top`; the bridge instances retain `addressGroup:
  bridge`. No instance edits should be needed in this stage if the
  per-instance `addressGroup:` values are already correct, but the
  plan must inspect each instance row and confirm.

### 6.4 — Shrink `exampleAddress.yaml` — **COMPLETE**

Follow `address-migration.md` Steps 5 ("Move address-policy
sections to `project.yaml`") and 6 ("Retire
`addressControl.yaml`").

- Remove the `AddressGroups:` and `RegisterBusInterface:` sections.
- Move `InstanceGroups:` and `AddressObjects:` into
  `examples/ip_test/arch/yaml/project.yaml` under the new
  `instanceGroups:` / `addressObjects:` keys.
- Delete `exampleAddress.yaml` once the project no longer references
  it.

### 6.5 — Regenerate and diff — **COMPLETE**

Follow `address-migration.md` Step 7 ("Regenerate and diff").

- `make -C examples/ip_test db` and `make -C examples/ip_test gen`
  must succeed.
- The generated SystemC and SystemVerilog output must be
  byte-identical (or, where field naming changes, diff-reviewable
  and explicitly approved) compared with the pre-migration snapshot.
- Stage 7 reopens the migrated database through the unit-test
  matrix; its T2.3 / T2.4 / T2.5 rows are the runtime gate for the
  view-side correctness of the migration. Stage 6 itself ships when
  the example build succeeds; Stage 7 batches confirm the
  post-parse output one topology at a time.

### 6.6 — Skill effectiveness review — **COMPLETE**

Stage 6 closes by recording the skill's performance:

- Capture every place the implementer had to depart from
  `address-migration.md` (missing step, ambiguous wording, missing
  diagnostic guidance, missing worked example). Each departure is
  an edit to the skill, made before Stage 6 ships.
- The final commit message references the skill and lists the
  diffs landed against it. This makes the skill the canonical
  reference for future migrations rather than a stale snapshot of
  the first one.

The skill required iteration during the `ip_test` migration; those
edits are now in `rules/skills/address-migration.md`, and the skill
is treated as the canonical reference going forward.

## Stage 7 — Hierarchical test coverage

**Status:** **partial**. Batch A and Batch B unit/error tests are
**committed**. The E3.1 / E3.2 diagnostics are **committed** and were
**verified** during this documentation cleanup. The companion test plan
is the current owner for remaining Batch C `ip_test` view-assertion
status and skill-doc cross-check closure.

**Files:** `builder/base/unittest/test_addrctl_*.py`,
`builder/base/unittest/test_error_*.py`,
`builder/base/examples/tests/<topology>/`,
and any reuse-extensions to `builder/base/examples/ip_test/`.

This stage implements
[`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md).
It runs after Stage 6 because most of its example-test rows
read assertions off the migrated `ip_test` database; staging it
before the migration would force test fixtures to track legacy
generator output.

The stage delivers, in the batches the test plan defines:

1. **Stand-alone unit tests under `unittest/`** that build mocked
   YAML, run `arch2code.py` to populate a temporary database, and
   assert on `projectOpen` view attributes and on the rows the new
   post-parse pass synthesises. These cover every topology in the
   parent test plan's matrix that does not require template
   coverage to prove the case, and every diagnostic in this plan's
   Stage 5.3 list.
2. **Example fixtures under `examples/tests/`** (or extensions
   to `ip_test`) for the topologies whose value depends on running
   the generator templates end-to-end. The example builds compile
   the generated output so a template regression is a build break,
   not a silent diff.
3. **A repository-wide no-`_global` invariant** on register-bus
   binds emitted by the new post-parse pass.

The test plan owns the topology matrix, the coverage map, and the
diagnostic-substring assertions. This plan does not duplicate
them. This stage is complete when every row in the test plan
matrix has its named fixture committed and green under
`unittest/run_all_tests.sh` plus the example build sweep.

### 7.1 — Stage gate

Stage 7 is organized in the three batches defined in the test plan's
"Implementation Phasing" section:

- **Batch A** — single-router positives, the diagnostic skeleton,
  and the lowest-cost no-IP examples.
- **Batch B** — three-level and thunker cases, including the
  block-reuse-across-levels case (T3.4) and the mixed-sibling case
  (T3.5) that exercise the multi-hop walk.
- **Batch C** — per-context emission guards (T1.6, T2.3 / T2.4 /
  T2.5 read off the migrated `ip_test`), and the validation-stage
  diagnostics including the no-`_global` invariant.

Each batch is independently mergeable. The stage as a whole closes
when Batch C is green.

## Stage 8 — Retire the legacy path — **COMPLETE (2026-06-12)**

**Status:** Done. The legacy `addressControl.yaml` path is removed;
the new schema is the only accepted input.

**Files touched:** `builder/base/config/postParseRegister.py` (deleted),
`builder/base/config/postParseRegisterPorts.py`,
`builder/base/config/project.yaml`,
`builder/base/pysrc/processYaml.py`,
`builder/base/unittest/mixed_test_arch/*` (fixture migrated).

**Two deviations from the original outline:**

1. **The no-in-tree-dependency gate was waived.** Five `examples/`
   (apbDecode, hierInclude, mixed, simple, axi4sDemo) and several unit
   fixtures still used the legacy schema at retirement time. Their
   migration is owned by a separate migration effort; the legacy path
   was removed without waiting on them, so those examples do not build
   until migrated. The one unit fixture whose migration was in scope
   (`unittest/mixed_test_arch`, consumed by six non-address tests) was
   migrated here so those tests stay green.
2. **The `_global` exemptions were KEPT.** `_global` is a feature (the
   include-scope sentinel and a general synthesized-bind marker), not a
   legacy artifact. The retirement-step bullet that proposed removing the
   `validateDeclaredPorts` / `validatePorts` `_global` exemption was
   overridden; all `_global` handling is left intact.

**Executed retirement steps:**

- **Done.** Deleted `config/postParseRegister.py` and its `postProcess:`
  registration in `config/project.yaml`. Its three reusable helpers
  (`collectBlocksNeedingRegHandler`, `regHandlerNaming`,
  `synthesiseRegHandler`) were moved into
  `config/postParseRegisterPorts.py`, which is now self-contained.
- **Done.** Deleted the `addressControl.yaml` loader and
  `validateAddressControl`. Accepted input is now the new-schema
  `project.yaml` plus per-block `addressBlock:` / `registerPorts:`.
  `loadProjectAddressPolicy` and the address-policy merge helpers were
  simplified to read `project.yaml` as the sole source (the legacy-file
  reconciliation and the now-unused `_addressRowsEqual` were removed).
- **Done.** Removed `_legacyRegisterBusInterface`; `_registerBusInterfacePort`
  now errors (naming the block) when no new-schema register-bus surface
  resolves, rather than falling back.
- **KEPT (deviation 2).** The `_global` exemptions in
  `validateDeclaredPorts` / `validatePorts` are unchanged.
- **Done.** Removed the view-helper legacy branches: the `AddressGroups`
  walk in `getBDAddressDecode` and the `AddressGroups`-from-ADDRESS_CONFIG
  synthesis in `getBDAddressBlockView`.
- **N/A in `schema.yaml`.** The legacy `AddressGroups` /
  `RegisterBusInterface` / `InstanceGroups` / `AddressObjects` sections
  were never schema-engine entries — they lived in the `validGen` table
  inside `validateAddressControl`, so deleting that function removed them.
  The new `project.yaml` `instanceGroups:` / `addressObjects:` and the
  per-block `addressBlock:` / `registerPorts:` schema entries are unchanged.

**Verification:**

- `make -C examples/ip_test clean db gen` succeeds and regenerates
  **byte-identical** source output (the legacy path was already inert for
  `ip_test`).
- `unittest/run_all_tests.sh`: the six `mixed_test_arch` consumers pass and
  38 `test_addrctl_*` / `test_error_*` suites pass. The only remaining red
  suites (`test_error_parameterizable`, `T4.3`, `TT.4`, `TT.5`) fail in the
  parallel parameterized-eval (C4) parser / validators, unrelated to this
  removal.

## Validation

Each stage lands behind the following gates. The detailed topology
matrix, error-case matrix, and coverage map live in
[`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md);
this section names only the gates that the parent plan itself
commits, so a reader can tell at a glance which artefact owns each
check.

- **Per-stage `make`.** `make -C examples/ip_test db` and
  `make -C examples/ip_test gen` must succeed at every stage
  boundary. Stages 1 through 5 may not change the generated output
  of `ip_test`; Stage 6 produces the explicit new-schema output;
  Stage 7 reopens the migrated database through the unit-test
  matrix. `proto/model` runtime targets are not a Stage gate for
  this refactor.
- **Stage 1 parse-time invariants.** Stage 1 lands the schema
  fragments and the custom parse-time hooks. Positive coverage is
  taken on by Stage 7's topology matrix; negative coverage (the
  parse-time block diagnostics on lines 252-258 above) is taken on
  by Stage 7's error-case matrix (E1.* rows). Do not add fixtures
  whose only purpose is to prove existing schema mechanics such as
  unknown-field, required-field, context-scope, or
  `_validate.section` failures.
- **Stage 4 post-parse behavior.** Stage 4 commits the script
  itself; correctness across the topology matrix and across the
  hierarchy diagnostics is asserted by the Stage 7 unit-test
  fixtures (T1.* through T5.* and E2.* rows). The script lands
  with the Stage 4 entrypoints in place; the assertions land in
  Stage 7.
- **Stage 5 validation behavior.** Stage 5 wires the new-schema
  validators only. The `registerPorts:` / `ports:` independence guard
  is present; the E3.1 / E3.2 register-bus checks for
  same-`interfaceType` packed-form incompatibility and
  cross-`interfaceType` rejection are **committed** — router→leaf via
  the `validatePorts` `ports: ∪ registerPorts:` superset, router→router
  via `postParseRegisterPorts.py` — and covered by their named error
  tests. The new-post-parse no-`_global` invariant is asserted through
  the shared Stage 7 topology-test helper. Legacy `addressControl.yaml`
  validation is not expanded by this stage.
- **Cross-example regression.** Stage 8 verified `examples/ip_test`
  regenerates byte-identical after the legacy removal. A full
  every-example rerun was **not** done: the five un-migrated examples
  (apbDecode, hierInclude, mixed, simple, axi4sDemo) intentionally do not
  build until their separately-owned migration lands.

## Risks

- **Generated-output drift.** Stage 6 moves type and interface
  declarations between files. Even when the resolved type set is
  identical, generated include lists may reorder. Mitigation: land
  Stage 6 against a committed snapshot of the pre-migration
  generated output, diff against it, and require reviewer sign-off
  on every non-byte-identical change.
- **Container-locality assumption.** The post-parse script resolves
  the router instance per group by walking instances of the router
  block type. Today the same-container rule is enforced by
  `postParseRegister.py` with an explicit error. The new script
  must preserve this enforcement; missing it would silently route
  to the wrong router.
- **Primary-router inference.** The hierarchical walk depends on
  every nested router being itself routed. In a project that
  declares a nested router whose container is not yet served by a
  parent router, the walk will incorrectly classify that nested
  router as primary. Mitigation: detect the case at the start of
  step 3 by counting routers whose containers fall outside any
  router's served set, and error if more than one is found.
- **Same-name interfaces in different scopes.** The leaf's `apb`
  interface (`ipReg`) and the router's `apb` interface (`apbReg`)
  may have identical structure names and shapes. The packed-form
  check must compare resolved field widths, not names, to avoid a
  false positive when the leaf simply reuses the router's structure
  names. The existing Stage 6.2 implementation already does this;
  the risk is a regression introduced by the Stage 4 emission
  changes.
- **Migration window length (resolved).** Stages 1 through 7 were
  additive; Stage 8 (destructive) was taken on 2026-06-12, removing the
  legacy path. The trade-off was decided in favour of removal over
  long-lived dual support. The residual cost now lives with the
  separately-owned migration of the five un-migrated `examples/`, which
  do not build until converted.

## Open Questions

The following items are deliberately not resolved by this plan and
must be answered before Stage 6 lands. Each is small enough that the
plan does not block on its outcome, but the wrong choice forces a
later edit to generated output.

- **Default-naming policy.** `addressBlock.upstreamPort` and
  `registerDecoderPort` default to `apbReg` for compatibility with
  the legacy generated port names. Should the defaults instead
  derive from the router block's name (for example
  `<routerBlock>Reg`), so a project that renames its router does
  not silently keep the legacy port name? Decision needed before
  Stage 6.3.
- **Schema spelling of the address-policy keys on `project.yaml`.**
  The new spellings (`instanceGroups:`, `addressObjects:`) match
  the legacy capitalization. Should the migration take the
  opportunity to converge on lower-camel-case across the whole
  schema?
- **Test-fixture location.** Resolved by
  [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md):
  unit fixtures live under `builder/base/unittest/` following the
  existing `test_error_*.py` and `test_thunker_view.py` conventions;
  example fixtures live under `builder/base/examples/tests/<name>/`
  or extend `examples/ip_test/`. No new top-level `tests/`
  directory is introduced.

## Deferred / Out of Scope

The following items are explicitly out of scope for this plan and
remain open per the research document.

- Multi-`registerPorts:` mapping syntax for IP blocks that expose
  more than one register access surface.
- Protocol-changer authoring convention for cross-`interfaceType`
  adaptation.
- Register-handler synthesis re-shaping (kept identical to today's
  shape; only the source of the interface and port names changes).
- Multi-instance routers serving the same group.
- Cross-block-type group sharing (two router block types serving
  the same logical group); admitted by the schema but not exercised
  by any existing example.

## #116 Review Follow-Up — Item 4: Nested Address Containment Validation (Execution, 2026-07-29)

This section hardens item 4 of
[`plan-116-review-feedback.md`](./plan-116-review-feedback.md)
("Address Increment Validation") into an execution-ready contract.
The intent: at db time, error if a nested slot's address footprint
escapes the per-child window the higher-level decoder allocates to
that slot. Per the item, the two cases key on **different quantities**:
a nested **decoder** is judged by its routed footprint; a bare
**register block** is judged by the space it actually decodes, not by
its larger nominal addressable range.

### Key finding — the no-decoder case is already enforced

The register-block (no-decoder) half of item 4 **already exists**.
`processYaml.py::calcAddresses` (`pysrc/processYaml.py:4243`) runs in
`projectCreate` after the register-wiring post-parse pass
(`postYamlExternalScript()` at `:3558`, then `calcAddresses()` at
`:3562`). Its post-allocation space check
(`pysrc/processYaml.py:4358-4370`) accumulates each register/memory-
owning block's **decoded span** into `blockAddressCurrent[blockKey]`
and compares it against the per-child window:

```
availableSpace = addressControl['AddressGroups'][group]['addressIncrement']
                 * instData['addressMultiples']          # per-child window × slots
if blockAddressCurrent[blockType] > availableSpace: error "overflowed its address space"
```

`blockAddressCurrent` is the sum of the per-object allocation `size`
(power-of-2 / alignment-rounded, computed at `:4306`/`:4318`), i.e. the
space the decoder **actually maps**; it is persisted as
`blocks.maxAddress = span-1` (`:4368-4369`) and re-consumed as
`addressDecode.addressBits = maxAddress.bit_length()`
(`getBDRegistersMemories`, `:2049`). It is emphatically **not** the
block's nominal addressable range (e.g. `2^IP_REG_ADDR_WIDTH`). So the
"must key on decode space, not nominal" nuance is satisfied by
construction, and this half needs no new code — only a named negative
fixture (below) to lock it.

The genuinely **new** work in item 4 is the **nested-decoder** half:
nothing today checks that a nested router's routed footprint fits the
per-child window of the slot its container occupies. A router block
owns no registers/memories, so it never enters `blockAddressCurrent`
and is invisible to the `:4358-4370` check.

### Data sources available at db time

All quantities are already persisted before/within `calcAddresses`;
no new computation of "decode space occupied" is required.

| Quantity | Source | Where produced |
| --- | --- | --- |
| Parent per-child increment (window) | `addressControl['AddressGroups'][group]['addressIncrement']` | `_post_registerAddressBlock`, `:6588-6635` |
| Router `maxAddressSpaces` | `addressControl['AddressGroups'][group]['maxAddressSpaces']` | same |
| Router-block identity per group | `AddressGroups[group]['_declaringBlock']` / `['_declaringFile']` | same |
| Container slot multiples | `instData['addressMultiples']` | `_auto_addressMultiples`, `:6903` |
| Container slot's parent group | `instData['addressGroup']` | `_auto_addressGroup`/`_auto_addressID`, `:6850-6873` |
| Reg block's **decoded span** | `blockAddressCurrent[blockKey]` → `blocks.maxAddress+1` | `calcAddresses`, `:4335-4369` |
| Nested-router hierarchy (parent/child, container sibling) | `decoderContainer`, `_findRouterParent`, per-router-to-router loop | `config/postParseRegisterPorts.py:148-202,626-716` |

Derived quantities the new check needs:

- **Nested decoder footprint** = `AddressGroups[childGroup]['addressIncrement']
  * AddressGroups[childGroup]['maxAddressSpaces']` — the total span the
  child router can route.
- **Parent per-child window for the slot** =
  `AddressGroups[parentGroup]['addressIncrement'] * containerInst['addressMultiples']`,
  where `parentGroup = containerInst['addressGroup']` and `containerInst`
  is the instance of the block that contains the nested router instance.

### Hook site

Add the nested-decoder pass to **`calcAddresses`
(`pysrc/processYaml.py:4243`), immediately after the existing space
check at `:4370`**, so both containment checks live together, run over
the same `AddressGroups`/`instances` tables, and emit the same style of
diagnostic. This keeps address-containment truth in `calcAddresses`
(where the plan and the `builder-base-development` skill say
address computation belongs) rather than splitting it into the
register-wiring pass.

Resolution of each nested router's container slot at this site reuses
only the already-persisted tables: for each `AddressGroups` group, take
`_declaringBlock` (the router block); find its instance's `containerKey`
(the container block); find that container block's instance; if that
container instance carries an `addressGroup` it is nested and that group
is `parentGroup` (if it carries none, the router is the dispatch-tree
root/primary and is skipped — a root decoder has no parent window to
fit). **Implementation caveat:** `_declaringBlock` is stored as the raw
block *name* (`itemkey` at `:6629`), while instance rows carry qualified
`instanceTypeKey`/`containerKey`. Resolve through the block row's
qualified key rather than a raw string compare. (Alternatively, the
parent/child mapping is already resolved in
`postParseRegisterPorts.py`; if the implementer prefers to persist it
there for reuse, that is acceptable, but the *comparison* stays in
`calcAddresses` next to the sibling check.)

### Per-case rule and error text

Checked **per nested slot**; error if not met.

1. **Nested decoder present** (the slot's block declares `addressBlock:`
   — a nested router): `childFootprint = childIncrement × childMaxAddressSpaces`
   must be `<= parentWindow`. Error otherwise:

   ```
   Nested register decoder '<childRouterBlock>' (group '<childGroup>')
   routes a <childFootprint>-byte footprint
   (addressIncrement <childIncrement> × maxAddressSpaces <childMaxAddressSpaces>),
   which exceeds the <parentWindow>-byte window that parent decoder
   '<parentRouterBlock>' (group '<parentGroup>') allocates to slot
   '<containerInstance>' (addressIncrement <parentIncrement> ×
   addressMultiples <multiples>). Reduce the nested decoder's increment
   or maxAddressSpaces, or widen the parent's addressIncrement.
   ```

2. **No nested decoder** (a bare register block in the slot): the block's
   **decoded span** (`blocks.maxAddress+1` = `blockAddressCurrent`) must
   be `<= parentWindow`. This is the **existing** `:4365` check; its
   message names the block, the used span, and the available window.
   No change beyond confirming coverage.

Both messages name the offending nested block and **both** spans
(allocated window vs the checked span), per the item's placement note.

**Wording flag (carry into implementation):** the feedback item calls
the nested-decoder quantity its "address increment", but the containing
quantity is the **product** `increment × maxAddressSpaces` (the routed
footprint), not the increment alone. `ip_test`'s bridge (below) fits its
parent slot only when measured as the product — increment alone
(`0x00100000`) would trivially pass and never catch an escaping
`maxAddressSpaces`. The rule above uses the product; the item's prose
should be read as shorthand for "routed footprint".

### `ip_test` PASS confirmation

`ip_test` passes both halves. Structure (from
`top/yaml/ip_top.yaml`, `bridge/yaml/ipBridge.yaml`, `ip/yaml/ip.yaml`):

- **Top router** `apbDecode`, group `top`: `addressIncrement 0x01000000`
  (16 MiB), `maxAddressSpaces 16`.
- **No-decoder leaves** `uIp0`/`uIp1` (block `ip`, `addressGroup: top`,
  `addressMultiples` 1): `ip` declares `registerPorts:` + registers +
  memories and **no `addressBlock:`** — the routed-leaf / no-decoder
  case. Its register bus `ipReg` has `IP_REG_ADDR_WIDTH = 32` →
  **nominal** addressable range `2^32` = 4 GiB, far larger than the
  16 MiB per-child window. Its **decoded span** (`blocks.maxAddress+1`,
  the handful of registers + `regAccess` memories) is in the KiB range,
  well under 16 MiB. A nominal-range check would wrongly reject it; the
  decode-span check at `:4365` accepts it — which is exactly why the
  no-decoder case must key on decode space. `ip_test` builds green
  today, so this check already passes.
- **Nested decoder** `bridgeApbDecode`, group `bridge`:
  `addressIncrement 0x00100000` (1 MiB), `maxAddressSpaces 16` →
  footprint `0x01000000` (16 MiB). Its container `ipBridge` is
  instanced as `uBridge` (`addressGroup: top`, `addressMultiples` 1) →
  parent window `0x01000000 × 1 = 16 MiB`. `16 MiB <= 16 MiB` → fits
  (exact, zero slack). The new nested-decoder check passes.

### Negative fixture and validation plan

**Negative fixture (new, must FAIL):** a two-level project — primary
router + one nested router — where the nested router's footprint
escapes the parent slot. Concretely, set the parent
`addressIncrement` small (e.g. `0x00100000`, one slot = 1 MiB,
`addressMultiples` 1 on the container) and the nested router
`addressIncrement 0x00100000 × maxAddressSpaces 16 = 0x01000000`
(16 MiB) → `16 MiB > 1 MiB`, error. Assert the exit is non-zero and
that stderr contains the child router block name, `0x1000000`
(footprint) and `0x100000` (window). Follow the `unittest/test_error_*.py`
convention: `unittest/test_error_nested_decoder_overflow.py`.

**Test-coverage matrix placement:** this is a new
address-calculation-time diagnostic, distinct from the parse-time
(E1.*), post-parse-hierarchy (E2.*), and Stage-5 port-validation (E3.*)
categories. Add it to
[`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md)
as a new **"Address-containment diagnostics (`calcAddresses`)"**
subsection:

- **E4.1** — nested router footprint exceeds parent per-child window
  → `unittest/test_error_nested_decoder_overflow.py` (the new negative).
- **E4.2** — bare register block decoded span exceeds parent per-child
  window → covers the pre-existing `:4365` check
  (`unittest/test_error_reg_block_decode_overflow.py`), a leaf whose
  registers/memories overrun a deliberately tiny parent increment.
- Positives are already carried by the migrated `ip_test` (nested
  bridge exact-fit; `ip` leaf decode-span-fits-nominal-would-not);
  no new positive fixture is required, but the `ip_test` view test
  (`test_addrctl_ip_test_view.py`) is the regression anchor.

**Validation:**

- `make gen -j` across the full base **and** pro example suites — the
  new check must be a no-op on every currently-green example (it fires
  only on genuine escape); a false positive there is a bug.
- `make -C examples/ip_test run` (and, if a register-decode regression
  target exists, the targeted `make regr` for `ip_test`) to confirm the
  exact-fit nested bridge and the decode-span leaves still route
  correctly at runtime.
- `unittest/run_all_tests.sh` green for the new E4.1/E4.2 fixtures with
  their diagnostic substrings asserted verbatim.
- Per the `builder-base` submodule rule, do not stage or commit
  `builder/base`; the user manages that tree.

## Update 2026-08-04 — review item 4: nested decode containment validation LANDED

This plan is the owner for #116 review item 4 ("add a check that a nested
decoder's address footprint is contained within the higher-level decoder that
routes to it"). It is closed.

A containment pass runs in `calcAddresses` (`pysrc/processYaml.py:4484` onward,
guarded so a project with no `AddressGroups` is unaffected) and reports a durable
error naming the offending nested block and both spans — the window the parent
allocates versus the span actually needed (`:4535`).

The rule deliberately checks **two different quantities**, which is the substance
of the item rather than an implementation detail:

- **Nested decoder present:** validate against the nested decoder's routed
  footprint, `addressIncrement × addressMultiples`. The increment alone would miss
  escapes past the first multiple.
- **No nested decoder:** validate against the decode space actually occupied by
  the nested register block — the space genuinely decoded, not any larger nominal
  allocation.

`ip_test` is the regression fixture for the second case and is why the no-decoder
check must be decode-space-based: it is a nested register block whose nominal
space is larger than the parent's per-child window but whose decoded span fits, so
it is valid and a nominal-space check would reject it incorrectly. The negative
fixture is `unittest/test_error_nested_decoder_overflow.py`.

One coverage note recorded during the 2026-08-04 status refresh: that negative
fixture was never registered in `unittest/run_all_tests.sh` and was only picked up
implicitly by the parallel runner's globbing. It is now registered in the
`ADDRCTL_TESTS` array, so it runs in both runners.
