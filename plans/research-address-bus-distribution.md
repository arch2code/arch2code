# Research: Distributing Address-Bus Information Out of `addressControl`

## Purpose

`plan-variant-config-unification.md` Stage 5 (bottom-up `ports:` schema)
landed with one acknowledged architectural gap, recorded as the
"Synthesised register-bus ports under bottom-up declaration" entry under
**Deferred Decisions** (plan lines 1148–1189). The gap is that a leaf
block such as `ip` cannot include its register-bus port in its bottom-up
`ports:` map, because the register-bus interface is owned by the
project-wide `addressControl` file and the port itself does not exist
in `self.data` until `config/postParseRegister.py` has synthesised it
during post-parse.

The plan exempts ports inferred from a `_context: '_global'` entry from
the partial-declaration diagnostic so the existing examples regenerate,
but flags that this is a stop-gap: an IP reused under a different
address-decode configuration (different register-bus interface,
different address group, different decoder placement) cannot capture
that contract on itself.

This document records the design direction for closing that gap by
moving the relevant pieces of `addressControl.yaml` onto the blocks
themselves: leaves declare `registerPorts:` alongside `ports:`, and
router blocks declare a top-level `addressBlock:` field that carries
the per-router attributes that today live in
`addressControl.AddressGroups`. The result is that every load-bearing
piece of register-bus information lives at the block that owns it,
`addressControl.RegisterBusInterface` retires, and the project-wide
`AddressGroups` table dissolves into per-router declarations.

## Background

### What `addressControl` carries today

`examples/ip_test/arch/yaml/exampleAddress.yaml` is representative:

- **`AddressGroups`** — one entry per address group. Each entry
  specifies `addressIncrement`, `maxAddressSpaces`, `varType`,
  `enumPrefix`, an optional `primaryDecode` flag, and a
  `decoderInstance` reference naming the instance that decodes that
  group. One group is marked `primaryDecode: True` (the project-wide
  root decoder).
- **`RegisterBusInterface`** — a single project-wide interface name
  (here `apbReg`). Every block that has registers or memory-mapped
  memories acquires a synthesised port speaking this one interface
  type.
- **`InstanceGroups`** — `varType` / `enumPrefix` entries for
  instance-ID enumeration. Orthogonal to the address-bus story.
- **`AddressObjects`** — alignment / sort / packing rules for
  memories and registers within an address group. Orthogonal to the
  address-bus story.

The relevant subset for this research is `AddressGroups` (the part that
encodes which decoder serves which group of blocks) and
`RegisterBusInterface` (the part that encodes which interface type the
register bus speaks).

### How the synthesised register-bus port is built today

`config/postParseRegister.py::postProcess` runs after YAML parsing but
before block-data view construction. The pass:

- reads `prj.addressControl.RegisterBusInterface` to pick the project-
  wide register-bus interface name (`reg_interface`, default `apbReg`);
- walks `prj.data['registers']` and `prj.data['memories']` to find
  blocks that need a register-bus connection;
- emits one `<block>_regs` handler block per such block plus an
  instance, and a `connectionMap` per block that wires the register-
  bus port to the synthesised handler;
- walks `AddressGroups` to pick the address router for each group
  (today named by the `decoderInstance` field), marks the primary
  router, and validates that every register-needing instance sits in
  the same container as its router (the current "same level as
  decoder" rule);
- emits direct router-to-instance `connections` for the primary path
  and parent-to-child router `connections` plus `connectionMaps` for
  hierarchical routers.

Every entry the pass produces is attributed to `_context: '_global'`
because the pass synthesises rows that no source YAML file authored.

### How the synthesised port surfaces downstream

Several downstream consumers each read the project-wide
`RegisterBusInterface` directly:

- `pysrc/processYaml.py::getBDAddressBus` (line 2117) — fetches
  `addressConfig['RegisterBusInterface']`, looks up the interface
  definition, and records the interface's structures on the block
  view's `addressDecode.registerBusStructs`. This is consumed by both
  hierarchy-level routers (`addressDecode.isApbRouter`) and
  block-level register/memory decoders (`addressDecode.hasDecoder`),
  including generated register handlers.
- `pysrc/processYaml.py::getBDIncludes` (line 2188) — adds the
  register-bus interface's structures to the include set for apb-router
  blocks, so the router's class declaration can spell the interface
  types.
- `pysrc/processYaml.py::validateDeclaredPorts` — exempts
  `_context: '_global'` ports from the partial-declaration diagnostic
  so leaf blocks that declare a bottom-up `ports:` map can validly
  omit the synthesised register-bus port (line 3496).
- `pysrc/processYaml.py::validatePorts` — exempts `_context:
  '_global'` ends from the cross-interface packed-form compatibility
  barrier (line 3559), for the same reason.

The leaf block's own YAML file (`ip.yaml`) declares neither the
`apbReg` interface nor an `apbReg` port. Both are reachable only after
the parent file (`ip_top.yaml`) has been parsed and post-parse has
run.

### Worked example of the gap

In `examples/ip_test`:

- `ip.yaml` defines the `ip` block. Its bottom-up `ports:` map
  declares `ipDataIf: { interface: ipDataIf, direction: dst }` only.
- `ip_top.yaml` defines the `apbReg` interface and (via the
  `connections:` from `uCPU` to `u_ip_top`) wires the parent register
  bus.
- `exampleAddress.yaml` carries `RegisterBusInterface: apbReg` and the
  `AddressGroups: top { ... decoderInstance: uAPBDecode,
  primaryDecode: True }` / `AddressGroups: bridge { ...
  decoderInstance: uBridgeAPBDecode }` entries.
- `postParseRegister.py` synthesises `apb_uIp0` / `apb_uIp1` ports on
  the `ip` block (via the `_global`-context register handler) and the
  parent connections that wire them.

If the same `ip` block were lifted into a different project whose
register bus is `axiLite` instead of `apbReg`, or whose decoder
hierarchy differs, `ip.yaml` communicates nothing about that
contract. The leaf is implicitly coupled to its containing project.
The bridge fixture (`ipBridge` / `uBridgeAPBDecode`) already
exercises a non-trivial decoder topology within a single project, but
the project-wide `RegisterBusInterface` remains a single value across
both decoders.

## Problem Statement

Two related contracts currently live in `addressControl.yaml` that
belong, in part, on the block:

1. **Register-bus protocol.** Which interface (and therefore which
   structures, which address/data widths) a block's register file
   speaks. Today this is one value project-wide.
2. **Decoder placement / address-group attributes.** Which decoder
   serves a block instance, and what address-layout attributes
   (`addressIncrement`, `varType`, `enumPrefix`, `primaryDecode`,
   etc.) apply. Today this is partly per-instance (the `addressGroup`
   field on the `instances:` row) and partly project-wide (the
   `AddressGroups` table that maps a group to its decoder instance
   and to its layout attributes).

The Stage 5 partial-declaration exemption is the visible symptom: a
leaf block that wants to participate in bottom-up port declaration
cannot describe its full port surface because part of its contract is
held by a project-level file the leaf does not see.

Goals for the redistribution:

- The leaf block's reusability must not depend on the parent project's
  `addressControl` choices. A leaf used in two projects with different
  register-bus interfaces should be authored once.
- The text-stability rule for `<block>.h` and `<block>Base.h` from the
  Stage 5 follow-up text must hold: the reusable base header may not
  import a parent-only context, in the same way that `ipBase.h` must
  be typed by `ipDataIf` and not by the parent-owned `data8If` /
  `data70If`.
- The cross-interface bridging path used for sibling-Configed cross-
  Config binds (the Q10/R2 thunker) is the natural mechanism for the
  same shape on the register bus: the parent owns the parent-side
  interface, the child block declares its own, and a generator-emitted
  bridge reconciles the two when their packed forms are compatible.
  Different resolved APB address or data widths are not compatible;
  the generator must error and name both sides.
- `ports:` is a new schema affordance with no installed-base burden.
  The redistribution does not need to preserve any project-wide
  fallback or synthesise a port that the leaf could just as well
  declare.

## Direction — Leaf-owned `registerPorts:` plus router-owned `addressBlock:`

The direction has two halves. Together they retire the project-wide
`addressControl.RegisterBusInterface` value and dissolve the
`AddressGroups` table into per-router block declarations.

### Leaf side — `registerPorts:` mirrors `ports:`

A block that declares a bottom-up `ports:` map also declares a sibling
`registerPorts:` map. Each entry has the same row shape as `ports:`
(port name, interface, direction). Two constraints:

- The interface named by every `registerPorts:` row must be defined in
  the block's own load-time scope: either in the block's YAML file
  directly, or in a file the block transitively pulls in through
  `include:`. The structures the interface carries must be defined in
  that same scope. This is the load-bearing invariant: it pins the
  leaf's reusability, because `<block>Base.h` cites the leaf's own
  interface and structure types and nothing else.
- The interface's `interfaceType` must be a register-bus meta-
  protocol. Today that means `apb`; in future this set may grow
  (`axiLite`, `lmmi`, etc.) as new register-bus protocols are
  promoted.
- The leaf's `interfaceType` must match the router's at wiring
  time. Cross-`interfaceType` adaptation on the register bus
  (`apb` ↔ `axiLite` and the like) is out of scope for this
  redistribution. When a project genuinely needs to bridge
  protocols, the user must instantiate an explicit protocol-changer
  block at the appropriate point in the hierarchy; the wiring pass
  does not invent one. This is a deliberate scope limit, not an
  architectural ceiling: it keeps the wiring pass to one cross-
  interface mechanism (the Stage 10 thunker pool under the
  Stage 6.2 packed-form check, which handles same-`interfaceType`
  structure differences only when resolved field widths and bit
  layout match), and defers protocol adaptation to a follow-on plan.
  Different resolved APB address or data widths are a generator error,
  not a thunker case.

The pairing rule — "a block that declares `ports:` also declares
`registerPorts:`" — is exact. A block that opts into bottom-up port
declaration may not have an implicit register-bus port. A block
without `ports:` continues to fall back to top-down inference for its
non-register ports (per Stage 5) and acquires its register-bus port
from the wiring pass against the router block's declared interface
rather than from any project-wide value.

The plural shape is intentional, but only the single-entry case is in
scope for the initial migration. Most IP blocks have one register-bus
port; blocks that need multiple register access surfaces are a
follow-on use case. Until that follow-on lands, a routed IP with more
than one `registerPorts:` entry should produce a diagnostic rather than
guessing which register ingress to use.

Worked example:

```yaml
# ip.yaml — the reusable leaf
constants:
    IP_REG_ADDR_WIDTH: { value: 32, desc: "Register address width" }
    IP_REG_DATA_WIDTH: { value: 32, desc: "Register data width" }

types:
    ipRegAddrT: { width: IP_REG_ADDR_WIDTH, desc: "IP register address" }
    ipRegDataT: { width: IP_REG_DATA_WIDTH, desc: "IP register data" }

structures:
    ipRegAddrSt:
        address: { varType: ipRegAddrT, generator: address }
    ipRegDataSt:
        data: { varType: ipRegDataT, generator: data }

interfaces:
    ipReg:
        desc: "Register bus the IP consumes"
        interfaceType: apb
        structures:
            - { structure: ipRegAddrSt, structureType: addr_t }
            - { structure: ipRegDataSt, structureType: data_t }

blocks:
    ip:
        desc: "Parameterizable IP under test"
        params: [IP_DATA_WIDTH, IP_MEM_DEPTH, IP_NONCONST_DEPTH]
        hasVl: true
        hasMdl: true
        hasTb: true
        hasRtl: true
        ports:
            ipDataIf: { interface: ipDataIf, direction: dst }
        registerPorts:
            regs: { interface: ipReg, direction: dst }
```

The leaf is now self-describing. Its register-bus interface and the
structures it carries are defined in the leaf's own scope, and its
register-bus port is declared in the same form as any other port.
`ipBase.h` cites only the leaf's own types; a different project whose
router speaks a different `apb`-typed register bus can consume the
same `ip.yaml` only when the two interfaces pass the Stage 6.2
packed-form compatibility check. Distinct structure names or packed
storage widths are fine when the resolved field layout and field
widths match. Different resolved APB address or data widths are not
compatible and must produce a generator error. A project whose router
speaks a different `interfaceType` entirely (`axiLite` rather than
`apb`) is out of scope for the wiring pass; the user authors a
protocol-changer block at the appropriate hierarchy point.

### Router side — `addressBlock:` flags the address router

A block becomes an address router by declaring a top-level
`addressBlock:` field. The presence of `addressBlock:` is the
schema-level signal that this block routes an address group; its body
carries the attributes that today live in one row of
`addressControl.AddressGroups`. The router block does **not** declare
`registerPorts:`. Its upstream and downstream register-bus ports are
inferred from the authored or generated routing connections, as they
are today.

Terminology matters in the generator:

- **Router** means the hierarchy-level address-bus block that selects
  the appropriate downstream register interface port for a target
  instance or nested router. Today this is the `apbDecode` /
  `bridgeApbDecode` role.
- **Decoder** means the block-level register/memory decode performed by
  the generated register handler (`<block>_regs` and its
  `registerHandler` flow). It consumes the selected register-bus
  transaction and decodes offsets within that block's registers and
  memories.

The `addressBlock:` field belongs to routers. Leaf `registerPorts:`
belong to the block-level decode surface consumed by the generated
register handler. Router ports remain normal inferred `ports:`, not
authored `registerPorts:`.

Worked example:

```yaml
# apbDecode.yaml — the top router
interfaces:
    apbReg:
        desc: "Top-level register bus the router drives"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    apbDecode:
        desc: "APB address router"
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

The router's incoming port is supplied by the parent wiring. For a
primary router that is an authored `connectionMap` from the parent
boundary to the router instance; for a nested router it is the
post-parse-generated connection from the parent router.

Field correspondence with today's `addressControl.AddressGroups` row:

- `addressBlock.addressGroup` — name of the group this router
  serves. Replaces the map key in `AddressGroups`.
- `addressBlock.addressIncrement`, `maxAddressSpaces`, `varType`,
  `enumPrefix` — carry over unchanged.
- `addressBlock.upstreamPort` — port-name convention for the
  router's upstream input. Defaults to `apbReg` for legacy
  compatibility. This is not an authored `registerPorts:` entry; it is
  the name the inferred upstream router port should take when a
  connection or generated router-to-router bind does not explicitly
  provide `instancePort`.
- `addressBlock.registerDecoderPort` — port-name convention for the
  generated block-level register decoder (`<block>_regs`) upstream
  port. Defaults to `apbReg` for legacy compatibility. The generated
  leaf-to-handler `connectionMap` should use this as the handler-side
  `instancePort` unless the selected leaf `registerPorts:` entry or an
  explicit mapping overrides it.
- `addressBlock.varTypeContext` — retires. Under the project-wide
  table, `varTypeContext` named the YAML file in which the `varType`
  enum is defined, because the `AddressGroups` row itself had no
  natural context. Under the per-router declaration the
  `varType` is resolved in the router block's own load-time scope
  (the same scope rule used by `registerPorts:`), so the field is
  redundant and is dropped from the schema.
- `addressBlock.primaryDecode` — retires. The primary router is
  inferred hierarchically: it is the router whose served container
  is not itself served by another router. In `ip_test`,
  `apbDecode` serves the `top` group; the `bridgeApbDecode` instance
  (`uBridgeAPBDecode`) sits inside a container (`ipBridge`) that is
  itself served by `apbDecode`, so `apbDecode` is the root of the
  router tree and is therefore the primary. The post-parse pass
  performs this walk once and records the result; the explicit flag
  no longer needs to be authored.
- `addressBlock.decoderInstance` — retires. The router block already
  names itself through the declaration; the router instance is
  resolved by container-locality at wiring time (the existing "same
  level as decoder" rule, restated as "same level as router").

Nested routers follow the same shape. A `bridgeApbDecode` block
declares its own `addressBlock: { addressGroup: bridge, ... }`. The
parent-router-to-child-router connection is wired by the post-parse
pass like any other router-to-leaf connection, with the nested
router's inferred upstream port acting as the consumer side.

The instance row keeps `addressGroup:` as today; it is genuinely a
per-instance placement property. `uIp0`'s `addressGroup: top` binds
the instance to the router block whose `addressBlock.addressGroup ==
"top"`, and the wiring pass routes it to whichever instance of that
block is in the same container.

### Inferred Port Naming Convention

The new post-parse path must make two generated surfaces explicit in
the block-data view: the register-bus **interface** and the
register-bus **port name**. Today's view largely conflates the two via
`addressDecode.registerBusInterface`, which works only while every
generated APB port is named after the project-wide interface.

`addressBlock.upstreamPort` and
`addressBlock.registerDecoderPort` provide the per-address-group
configuration for these inferred names. Both default to `apbReg` so
existing APB examples keep their generated surfaces unless a project
opts into new names.

The convention is:

- **Router upstream port.** A router's incoming register-bus port is a
  normal inferred port from the connection or `connectionMap` that
  targets the router instance. The port name follows the existing
  `connectionMap` priority: `instancePort`, then `name`, then
  `interface`, with `addressBlock.upstreamPort` acting as the
  default `instancePort` value when the binding row does not provide a
  more specific name. New generated router-to-router binds should set
  the target `instancePort` to the child router's
  `upstreamPort`, so nested routers get stable input port names.
  Primary router authoring may still override the name by providing
  `instancePort` on the parent `connectionMap`. Any inferred router
  port must carry the router block's YAML context, not `_global`; the
  router owns the port surface even when the bind row is generated.
- **Router dispatch ports.** Per-target downstream router outputs stay
  generator-owned and follow the existing shape: one generated output
  per routed target. The new naming rule is
  `<registerDecoderPort>_<target>`, where `<target>` is the routed
  instance name (for example, with `registerDecoderPort: apbReg`,
  `apbReg_uIp0` and `apbReg_uBridgeAPBDecode`). These inferred
  dispatch ports also inherit the router block's YAML context, since
  the generated router class must be stable and self-contained from
  that context.
- **Leaf register ingress port.** A reusable leaf block's authored
  `registerPorts:` key is the externally visible register-bus ingress
  for that block. The initial migration supports exactly one entry and
  selects it automatically. Multiple entries are deferred; if authored,
  they should produce a diagnostic that says multi-register-port
  routing is not implemented yet. The router-side end of the generated
  bind uses the owning router's `registerDecoderPort` dispatch naming;
  `registerPorts:` selects the IP-side ingress, not a router-side port
  name.
- **Generated register-decoder port.** The generated `<block>_regs`
  handler receives a normal inferred port connected from the selected
  leaf `registerPorts:` entry. The generated `connectionMap` should
  name both sides explicitly: `port: <selected register port>` on the
  leaf block and `instancePort: <registerDecoderPort>` on the handler
  instance. `registerDecoderPort` defaults to `apbReg`, preserving the
  legacy generated handler port name. If a block has multiple
  `registerPorts:` entries, the user-selected leaf port and the
  handler-side `registerDecoderPort` stay distinct: one identifies the
  reusable block's external ingress, the other identifies the generated
  decoder's upstream port. The handler-facing inferred port should
  carry the generated register-handler block's context; the leaf-facing
  bind remains in the leaf block's context.

Templates should consume distinct view fields, e.g.
`addressDecode.registerBusInterface` for the interface definition and
`addressDecode.registerBusPort` for the port object to bind/read. A
router view also needs the resolved upstream port and generated
dispatch-port map; a generated register-handler view needs the selected
decoder port.

### Generator impact

A new post-parse script should implement this migration path rather
than rewriting `config/postParseRegister.py` in place. The existing
script remains available for legacy projects that still use
`addressControl.RegisterBusInterface` and `AddressGroups` during the
migration. The new script becomes a wiring engine rather than a
port-and-interface synthesiser:

- Build the router index from `prj.data['blocks']` rows that carry
  `addressBlock:`, indexed by `addressBlock.addressGroup`. Each row
  resolves its incoming register-bus interface and port from the
  connection or `connectionMap` that targets the router instance. The
  router's dispatch ports remain generated from the routed instances.
  Missing `upstreamPort` and `registerDecoderPort` values normalize
  to `apbReg` during project creation.
- Infer the primary router by walking the router index: the primary is
  the one whose router-instance container is not itself served by
  another router. Exactly one primary must exist;
  otherwise the post-parse pass errors with a diagnostic that lists
  the candidates. The result is recorded once, replacing today's
  explicit `primaryDecode: True` lookup.
- For each instance whose `addressGroup:` field references a known
  group, resolve the matching router instance by container-locality,
  find the leaf's declared `registerPorts:` entry, and emit the
  connection between the router's generated source-side register-bus
  port named `<registerDecoderPort>_<target instance>` and the leaf's
  single `registerPorts:` row. If the leaf has multiple
  `registerPorts:` entries, error for now; multi-register-port routing
  is deferred.
- Verify that the router's and the leaf's declared register-bus
  interfaces share the same `interfaceType`. If they match: emit the
  connection only if the Stage 6.2 packed-form compatibility check
  passes. Distinct structure names and packed storage widths are
  bridgeable; different resolved address/data field widths are not.
  If the `interfaceType` differs, the wiring
  pass errors with a diagnostic that names both sides and instructs
  the user to insert an explicit protocol-changer block.
- For nested routers, emit the parent-router-to-child-router
  connection the same way; the nested router is a routing target with
  an inferred upstream port, not a `registerPorts:` declaration. The
  generated bind should set the child-side `instancePort` to the child
  router's `addressBlock.upstreamPort`.

The four downstream consumers of `addressControl.RegisterBusInterface`
update in lockstep:

- `pysrc/processYaml.py::getBDAddressBus` reads the router's inferred
  upstream interface or the register-handler target block's selected
  `registerPorts:` interface instead of reading
  `addressConfig['RegisterBusInterface']`. The view should keep
  `addressDecode.registerBusInterface` / `registerBusStructs` for type
  selection and add an explicit register-bus port field for binding.
- `pysrc/processYaml.py::getBDIncludes` aggregates each resolved
  register-bus interface context the same way it aggregates other
  interface contexts. The project-wide special case retires.
- `pysrc/processYaml.py::validateDeclaredPorts` no longer needs the
  `_context: '_global'` exemption for leaf register ingress: the leaf's
  externally visible register-bus port is now an authored
  `registerPorts:` row. Router dispatch ports and generated
  register-handler ports remain generator-owned surfaces, so their
  exemption or equivalent generated-port classification should remain
  explicit rather than accidentally requiring authors to list them in
  `ports:`. That classification must not be expressed by assigning
  `_context: '_global'`; inferred router ports inherit the router
  block's YAML context, and inferred register-handler ports inherit the
  generated handler block's context.
- `pysrc/processYaml.py::validatePorts` should run the Stage 6.2
  packed-form check for leaf `registerPorts:` binds just like any other
  cross-interface bind. Generated router dispatch and register-handler
  internal binds still need a clear generated-bind classification so
  validation can distinguish them from user-authored cross-interface
  ports.

Block-data view augmentations are minimal:

- A `registerPorts:` field on the block view, parallel to `ports:`.
- An `addressBlock:` field on router block views, carrying the
  per-group attributes templates need (`varType`, `enumPrefix`,
  `addressIncrement`, etc.).
- Explicit view fields for the resolved register-bus port name
  alongside the register-bus interface name, including the normalized
  `upstreamPort` and `registerDecoderPort` values.
- The synthesised `<block>_regs` handler block and instance machinery
  is unchanged in shape; only the source of the interface name
  changes.

### What replaces `addressControl.yaml`

After the redistribution:

- `AddressGroups` retires. Each row becomes the body of one router
  block's `addressBlock:` declaration. Discovery is by block-walk for
  `addressBlock:` rather than by reading a project-wide table. The
  per-row `primaryDecode`, `varTypeContext`, and `decoderInstance`
  fields all retire: primary is inferred from the router hierarchy,
  `varType` resolves in the router block's own context, and the
  router instance is resolved by container-locality. The new
  `upstreamPort` and `registerDecoderPort` fields live here as
  address-group policy with legacy defaults of `apbReg`.
- `RegisterBusInterface` retires. Each router's register-bus interface
  is inferred from its upstream connection or `connectionMap`; each
  leaf declares its own through `registerPorts:`. The two need not
  name the same interface, but they must share the same
  `interfaceType` and pass the packed-form compatibility check.
  Different resolved APB address/data widths are a generator error.
  Cross-`interfaceType` adaptation is out of scope and requires a
  user-authored protocol-changer block.
- `InstanceGroups` and `AddressObjects` are orthogonal to the
  address-bus distribution. In the new schema they move to
  `project.yaml` as project-level policy. The existing
  `addressControl.yaml` spelling remains accepted for backwards
  compatibility during migration; project creation should normalize
  both spellings into the same persisted address-policy view.

### Migration of `examples/ip_test`

The current `ip_test` fixture migrates as follows:

- The `apbReg` interface and `apbAddrSt` / `apbDataSt` structures move
  out of `ip_top.yaml` into the router block's scope (`apbDecode.yaml`,
  newly split out for this purpose).
- The `ip` block grows a `registerPorts:` declaration naming a leaf-
  scoped register-bus interface (`ipReg` defined in `ip.yaml`, with
  its own address / data structures). The leaf's interface declares
  `interfaceType: apb` to match the router; the wiring pass emits
  a same-`interfaceType` cross-interface bind through the thunker
  pool only if the packed-form check passes (or a same-interface
  direct bind if the leaf chooses to name the router's interface
  directly — the leaf-scope rule does not forbid reusing a name as
  long as the structures are defined in the leaf's scope). If the leaf
  and router resolve different APB address/data widths, generation
  errors.
- The `apbDecode` router block grows an `addressBlock:` declaration with
  `addressGroup: top, addressIncrement: 0x01000000, ...`, plus
  optional `upstreamPort: apbReg` and
  `registerDecoderPort: apbReg` entries (or omitted to take the same
  defaults). It does not declare `registerPorts:`; its incoming bus
  remains inferred from the parent `connectionMap` that targets
  `uAPBDecode`.
  No `primaryDecode:` flag is authored; the post-parse pass infers
  `apbDecode` as primary because no router is above it.
- The `bridgeApbDecode` block grows its own `addressBlock:` with
  `addressGroup: bridge, ...`. Its incoming bus is inferred from the
  post-parse-generated parent-router-to-child-router bind. The split
  that Stage 8.2
  introduced manually (so the per-block port aggregation in
  `apbDecodeBase` does not merge two contexts with different
  connectivity) becomes the natural consequence of the schema: each
  router declares itself.
- `exampleAddress.yaml` shrinks away for new-schema projects. Residual
  policy (`InstanceGroups`, `AddressObjects`) moves to `project.yaml`;
  legacy projects may continue to provide it through
  `addressControl.yaml`.

A new post-parse script walks the new declarations, resolves each
instance's owning router by container-locality, and emits the
register-bus connections. `postParseRegister.py` remains available for
legacy `addressControl` projects during migration. The broad
`_context: '_global'` exemption retires for leaf register ingress
because there is no longer a leaf port that the leaf failed to
declare; generated router dispatch and register-handler internal binds
should keep an explicit generated-bind classification while preserving
their owning block contexts. In particular, inferred router ports are
tagged with the router block's YAML context, never `_global`.

## Deferred / Out Of Scope

- **Multi-`registerPorts:` mapping syntax.** The field shape remains
  plural and map-like, matching `ports:`, but only one entry is
  supported by the initial migration. The follow-on design must decide
  how an explicit mapping names the target register port when an IP
  exposes more than one register access surface.
- **Protocol-changer authoring convention.** Cross-`interfaceType`
  adaptation is out of scope for the wiring pass; the user must
  instantiate an explicit protocol-changer block. The convention for
  how such a block is authored, named, and inserted (instance row
  placement, `registerPorts:` declarations on both sides, address-
  group membership) is a follow-on schema-level question. The
  redistribution itself only needs to emit a clean diagnostic that
  names the mismatch and points the user at the protocol-changer
  remedy.
- **Register-handler synthesis.** `isRegHandler:` and the synthesised
  `<block>_regs` handler stay unchanged. Today `postParseRegister.py`
  invents a `<block>_regs` handler block per registered block, marked
  `isRegHandler: True`; the new post-parse path should keep that shape
  and only change how the register-bus interface and port names are
  selected.
- **Legacy address-control input.** `InstanceGroups:` and
  `AddressObjects:` move to `project.yaml` for the new schema, but the
  existing `addressControl.yaml` input remains supported for backwards
  compatibility. Conflict rules between the two spellings should be
  explicit if both are present.
- **Primary-router inference rules and multi-instance routers.**
  The primary router is inferred hierarchically: the router whose
  container is not itself served by another router. The walk needs
  to handle two edge cases. First, multiple primary candidates (two
  router trees with no common ancestor) — the post-parse pass must
  error explicitly rather than picking one. Second, a single router
  block instantiated more than once for the same group, today
  disallowed implicitly. If multi-instance routers ever become
  legal, the rule needs extension; surface the case before
  committing.
- **Cross-block-type group sharing.** Today two distinct router
  block types (`apbDecode` and `bridgeApbDecode`) serve two distinct
  groups (`top` and `bridge`). The schema rule
  "`addressBlock.addressGroup` is unique across all router blocks"
  is natural under this proposal. If two router block types ever
  need to serve the same logical group (for example, two flavours of
  router in different containers), the schema admits this as long
  as the hierarchical-inference rule yields exactly one primary; the
  wiring pass routes each contained instance to its container-local
  router instance regardless of which block type implements it.

## Related Plans / Documents

- [`plan-variant-config-unification.md`](./plan-variant-config-unification.md)
  — Stage 5 (bottom-up `ports:` schema); the deferred-decision text on
  lines 1148–1189 is the canonical statement of the gap this document
  expands on.
- [`research-multi-config-bindings.md`](./research-multi-config-bindings.md)
  — D10 (bottom-up port declaration) and Q10/R2 (cross-interface bind
  via thunker), the two mechanisms this redistribution composes with.
- [`plan-foundation-address-decode.md`](./plan-foundation-address-decode.md)
  — original design of the address-decode infrastructure;
  `addressControl.yaml` schema lives here.
- `config/postParseRegister.py` — the legacy post-parse pass that
  synthesises the register-bus connections today; retained during
  migration while the new `registerPorts:` path is implemented in a
  separate post-parse script.
- `pysrc/processYaml.py::getBDAddressBus` / `getBDIncludes` /
  `validateDeclaredPorts` / `validatePorts` — the four downstream
  consumers of the project-wide `RegisterBusInterface` value; each
  updates to read the per-router / per-leaf declarations instead.
