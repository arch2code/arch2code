# Specification: Register-Bus Distribution

A register bus carries firmware accesses from one authored feed down to every
block that owns registers or firmware-accessible memories. The author declares
routers (`addressBlock:`), optional leaf boundaries (`registerPorts:`) and the
`addressGroup:` on each routed instance. `projectCreate` does the rest: it
registers each router's address group under the owning project, allocates
address slots, synthesizes every handler block and every dispatch connection
below the primary router, checks the interfaces at each junction, sizes each
block's footprint and checks that it fits its window, and emits the firmware
address enum. `projectOpen` then gives the router and handler templates a view
of the resolved design. This document specifies that mechanism.

**Scope.** This spec covers the generator side: data flow, ordering, synthesis,
validation placement and the views. It does not cover YAML authoring or the
diagnostics a user acts on, which `rules/skills/design-register-decode.md`
teaches; address policy and firmware headers (`rules/skills/manage-address-space.md`);
conversion of legacy `addressControl.yaml` projects
(`rules/skills/address-migration.md`); the hand-written RTL behind registers
(`rules/skills/rtl-registers.md`); register-bus clock and reset domains
(`specs/spec-clock-reset-requirements.md`); or memory port access modes
(`specs/spec-memory-access-modes.md`).

---

## 1. Inputs

| Input | Where | Shape |
| :--- | :--- | :--- |
| `addressBlock:` | `blocks` row, `config/schema.yaml` | `dataGroup` with `post(registerAddressBlock)`. Required: `addressGroup`, `addressIncrement`, `maxAddressSpaces`, `varType`, `enumPrefix`. Optional: `upstreamPort` and `registerDecoderPort` (both default `apbReg`), `clock`, `reset` (block-local names; unstated means the block default clock and its selected reset). |
| `registerPorts:` | `blocks` row | One row keyed by port name, with `interface` (resolved in the block's load-time scope) and optional `clock`/`reset`. Direction is implicitly `dst`. |
| `addressGroup:` | `instances` row | `auto(addressGroup)`; the bare authored group name. Siblings: `addressMultiples` (default 1) and `addressID` (always computed, see §3). |
| `addressBus:` | `interface_defs` row | `optional(false)`. Marks an interface type as a register-bus protocol. |
| `instanceGroups:`, `addressObjects:` | root `project.yaml` | Loaded by `pysrc/processYaml.py::loadProjectAddressPolicy` from the root project file only. `addressObjects:` drives `calcAddresses` packing; `instanceGroups:` drives `instGroup:`/`instID`. |

Parse-time block checks (`pysrc/processYaml.py::_post_validateBlockAddressDecl`,
`_post_validateRegisterPortInterface`):

- A block declaring both `registerPorts:` and `addressBlock:` is rejected.
- More than one `registerPorts:` row is rejected.
- A `registerPorts:` interface whose `interfaceType` lacks `addressBus: true`
  is rejected.

The post-parse pass is wired as the first entry of `postProcess:` in
`config/project.yaml` (`$a2c/config/postParseRegisterPorts.py`).

## 2. Terms

| Term | Meaning in code |
| :--- | :--- |
| Router | A block whose row carries `addressBlock:` (`_collectRouterBlocks`). Owns no registers and no `regAccess` memories. Exactly one reachable instance. |
| Register consumer | A block that owns registers or `regAccess` memories (`collectBlocksNeedingRegHandler`), or declares `registerPorts:`, or is a passthrough container. |
| Routed leaf | A register consumer that a router dispatches to directly. |
| Handler | The synthesized `<block><blockSuffix>` block (`regBlockNaming`, default `_regs`) holding a register-owning block's registers and decode. Row flag `isRegHandler: true`. Its instance name is `regBlockNaming.instancePrefix` (default `u_`) plus the handler block name, camel-cased when `regBlockNaming.camelCase` is set. |
| Primary router | The one router with no parent router (`_findPrimaryRouter`). The authored feed enters here. |
| Nested router | A router whose host container is instanced in the container of another router. The host is a slot in the parent router's group. |
| Passthrough container | A router-less, non-root container that owns no registers and holds exactly one register consumer. It is itself a consumer of its parent. |
| Routed slot | The instance carrying `addressGroup:` that a router allocates a window to: a leaf, a nested-router host, or the outermost passthrough container. |

## 3. `projectCreate` order

### 3.1 Parse time

`_post_registerAddressBlock` runs for each `addressBlock:` as its file is
parsed. It keys the group registry on `(owning project of the declaring file,
group name)`, using `contextOwningProject`, which is assigned before
`processYamls`. It:

- rejects a second declaration of the same key in one project;
- rejects a non-power-of-two `addressIncrement` or `maxAddressSpaces`;
- records the group row (`addressIncrement`, `maxAddressSpaces`, `varType`,
  `varTypeContext` = the router's own file, `enumPrefix`, `upstreamPort`,
  `registerDecoderPort`, declaring block and file) in `counterGroup`,
  `counterGroupControl` and `addressControl` under `AddressGroups`.

Instance fields resolve in schema order:

- `_auto_addressGroup` resolves the reference against the referring file's own
  project and errors when that project has no such group. It stores the bare
  name.
- `_auto_addressID` takes the group's running counter as `addressID`, sets
  `offset = addressID * addressIncrement`, advances the counter by
  `addressMultiples`, and errors once the counter exceeds `maxAddressSpaces`.
  Slots are therefore allocated in parse order, per `(project, group)`. The
  computed `addressID` replaces any authored one.

### 3.2 `postParseRegisterPorts.postProcess`

Run from `postYamlExternalScript`, after `generateHierarchy`. In order:

1. Reject any authored `isRegHandler`. Validate that every `addressBus`
   interface is fixed width (§5). With no routers, persist an empty
   `REGAPB_PASSTHROUGH` and return.
2. **Router index.** Reject a router block with no instance anywhere, and a
   router the current project owns that is instanced only outside its
   reachable top. `_resolveRouterInstances` takes the single instance of each
   router block within `prj.reachableInstanceKeys()` and rejects a second.
   Routers present only in a referenced project's standalone harness drop out
   of the working set.
3. **Primary router.** `_findRouterParent` walks from each router's container
   to a router in the container's container. Exactly one router without a
   parent must remain. When several remain and one sits behind a router-less
   container, the error names that shape instead.
4. **Host limits.** A nested router's host block may have one reachable
   instance.
5. **Passthrough fixed point.** Starting from the handler-bearing blocks and
   the `registerPorts:` blocks that host no router, a container joins the
   consumer set when it holds exactly one consumer instance, is not a router,
   hosts no router and is not a root block. Iterate until stable. A router-less
   container with several consumers, or one that owns registers and also hosts
   a consumer, is rejected. An inner consumer of a passthrough must not carry
   `addressGroup:`.
6. **Structural checks.** A nested-router host may not own registers; a router
   may not own registers or `regAccess` memories; a consumer that declares a
   `ports:` section must also declare `registerPorts:`.
7. **Binding resolution.** `_routerServingLeaf` gives each passthrough
   container and each handler-bearing block a `(portName, interfaceName,
   ifaceContext)` binding (§4). Containers resolve first, so a conflict names
   the container.
8. **Handler synthesis.** `synthesiseRegHandler` builds the handler block
   (`params:` = the leaf's own `params:`), its instance inside the leaf
   (`inheritContainerParam: true` when the leaf has params), and the
   leaf-to-handler `connectionMap`. The map's `port` and `instancePort` are
   both the leaf's register-bus port name, so the handler's port carries the
   leaf's name.
9. **Router-to-leaf dispatch.** For each reachable consumer instance whose
   container holds a router, check its group (`_checkDispatchedGroup`) and emit
   a connection from the router on `srcport` `<registerDecoderPort>_<instance>`
   to the leaf's port, typed by the router's `upstreamPort` interface. An
   instance in a passthrough container gets no direct dispatch, and an
   instance of a block that hosts a router is left to router-to-router
   dispatch. A consumer instance whose container neither holds a router nor
   is a passthrough consumer is rejected here ("Leaf instance ... not served
   by any router").
10. **Router-to-router dispatch.** For each non-primary router, emit a
    connection from the parent router on `<parent registerDecoderPort>_<host
    instance>` to the host instance's port named by the child's
    `upstreamPort`, typed by the child router's interface, and check the pair
    (§5). The host takes a slot in the parent's group.
11. **Every router dispatches.** A router with no dispatched member of its
    group is rejected, with or without members carrying the group.
12. **Nested boundary map.** For each non-primary router, and for a primary
    router whose host declares `registerPorts:` (the standalone reusable-IP
    harness), emit a host `connectionMap` from port `<upstreamPort>` to the
    router instance. A host `registerPorts:` key must equal that
    `upstreamPort`.
13. **Passthrough boundary maps.** One `connectionMap` per chain level, from
    the container's boundary port to the inner consumer's port, after a
    junction check per container instance (§5).
14. **Owner-context emission.** Rows are bucketed by owning file and fed
    through `prj.processSingleFile(ownerContext, ...)`, never `_global`:

    | Row | Owner context |
    | :--- | :--- |
    | Handler block, instance, leaf-to-handler map | The leaf block's file |
    | Router-to-leaf connection | The file declaring the leaf instance (the container's file) |
    | Router-to-router connection | The file declaring the host instance |
    | Nested boundary map | The file declaring the nested router instance |
    | Passthrough boundary map | The file declaring the inner consumer instance |

    No synthesized row states `clock:`; `pysrc/clockTree.py` derives each
    feed's domain from the instance binds.

15. **Persisted state.** `INSTANCES_WITH_REGAPB` lists every dispatched
    instance key. `REGAPB_PASSTHROUGH` maps each passthrough container to its
    `boundaryPort`, inner instance, inner port, and routed slot instance keys.
    `calcAddresses` and `clockTree.build` read the latter.

The script returns `None`, which skips the dispatcher's `_global` re-feed.

### 3.3 After post-processing

- `calcAddresses` packs each block's registers and `regAccess` memories using
  `addressObjects:`, at the worst-case width (`maxBitwidth`) and depth
  (`maxValue` of a parameterizable `wordLines`). It persists `offset` and
  `decodeSize` per row and `maxAddress` per block. Then two checks:
  - **Decoded span.** For each instance of a block with address objects, the
    block's span must fit `addressIncrement * addressMultiples` of its group.
    An instance with no `addressGroup:` uses the windows of the routed slots
    in `REGAPB_PASSTHROUGH`. A reachable instance with neither is an error.
  - **Nested footprint.** For each routed slot whose block hosts a router,
    the nested router's `addressIncrement * maxAddressSpaces` must fit the
    parent's `addressIncrement * addressMultiples`.
- `validateAddressGroupEnumIdentity` rejects two groups, build-wide, sharing a
  `varType` or an `enumPrefix`.
- `generateAddressEnums` builds one enum per group, named `varType`, with one
  member `<enumPrefix><INSTANCE>` = `addressID` for every instance carrying
  that group. It adds the enum as a `types:` row to the group's
  `varTypeContext` through `processSingleFile`, so it is emitted wherever that
  context's types are. A group with no carrying instance emits no enum. The
  members are not filtered by reachability, so they include the instances of
  a referenced project's standalone harness.
- `validatePorts` runs last (§5).

## 4. Top-down leaf inference

A block without `registerPorts:` infers its register bus.

- **Nearest authored boundary.** `_servingRouters` walks each reachable
  instance outward. A container holding a router yields `(router, None)`. A
  passthrough container yields its own serving pairs, with the boundary
  replaced by the container when it declares `registerPorts:`. The innermost
  authored boundary wins.
- **Binding per source.** `_leafRegisterBinding` takes the boundary's
  `registerPorts:` key and interface, or else the router's
  `registerDecoderPort` and its `upstreamPort` interface
  (`_resolveRouterRegisterBusInterface`, which also requires that name to
  resolve in the router's file to an `addressBus` interface).
- **Same interface.** All sources must yield one `(interface, declaring
  context)` pair. A block has one register port type.
- **Port name.** The common port name when all sources agree, else the
  interface name. `_checkInferredPortName` rejects a name already used by a
  register, memory, port, clock, reset, connection port or map port of the
  block.
- **Scope.** `_checkInferredInterfaceScope` requires the inferred interface
  name to resolve to the same declaration in the file where the rows are
  emitted.

The result is one register-bus type per router path. Interface names may
differ along the path, but each junction must agree on `interfaceType` and
packed form.

## 5. Validation placement

| Check | Where |
| :--- | :--- |
| Address-bus interfaces carry no parameterizable structure | `postParseRegisterPorts._validateAddressBusFixedWidth`, before synthesis |
| Router-to-leaf junction for a leaf with `registerPorts:` | `validatePorts`, which looks up a connection end's port in `ports:` and then `registerPorts:` |
| Router-to-router junction | `prj.checkInterfacePair` during router-to-router dispatch (§3.2), once per binding pair from `SiteBindingIndex.nestedRouterBindings` |
| Passthrough junction | `prj.checkInterfacePair` while emitting the passthrough boundary maps (§3.2), once per binding pair from `SiteBindingIndex.junctionBindings` |

`checkInterfacePair` skips a pair only when both sides are the same
`interfaceKey` under equal bindings. Otherwise the two `interfaceType`s must
match and three conditions hold:

- Both sides carry the same set of `structureType`s; a payload for an optional
  parameter may be missing on one side.
- Each paired payload is the same kind of declaration on both sides.
- Fields agree positionally on `(width, offset)`, each side evaluated under
  its own resolved bindings. Field names are not compared.

Different interface names with the same packed form are therefore accepted.

## 6. `projectOpen` views

`getBlockData` calls these in order: `getBDRegistersMemories`,
`getBDAddressDecode`, `getBDAddressBus`, and later `getBDAddressBlockView`.

- **`getBDRegistersMemories`.** For a handler, reads the leaf's registers and
  `regAccess` memories and the leaf instance's `addressGroup`. Sets
  `hasDecoder` when any register or `regAccess` memory exists, with
  `addressBits` from the block's `maxAddress`. Adds `worstBitwidth` and, for
  memories, `rowBytes`.
- **`getBDAddressDecode`.** For a router: `isApbRouter`, `addressGroupData`
  (the authored `addressBlock:`), `containerBlock`, `instanceWithRegApb`
  (`INSTANCES_WITH_REGAPB`), and `routedInstances`. `routedInstances` holds the
  reachable instances whose `(owning project, addressGroup)` equals the
  router's, sorted by `addressID`. The list is empty only for a referenced
  project's harness router. The parent never generates that router's files
  (ownership gate, `specs/spec-project-composition.md` §4), and the router
  templates do not accept an empty list.
- **`getBDAddressBus`.** For a router or a block with `hasDecoder`:
  `registerBusInterface`, `registerBusPort` and `registerBusStructs`
  (`addr_t`, `data_t`). A router takes its `upstreamPort`. A handler reads the
  leaf-to-handler `connectionMap` from its instance side; a leaf reads the same
  map from its block side, picking the map whose interface type is
  `addressBus`. `registerPorts:` is not read here.
- **`getBDAddressBlockView`.** Copies `addressBlock:` onto a router's view.

## 7. Generated outputs

- **Router RTL** (`templates/systemVerilog/apbDecodeModule.py`, fileMap key
  `apbDecodeModule`). Masks `paddr` with
  `addressIncrement * maxAddressSpaces - 1`, decodes `routedInstances` that have
  a dispatch port into address arms by `offset`, and adds an arm for any
  unfilled range. Child `pslverr` is forwarded. An unmapped access returns
  `32'hBADD_C0DE` with `pslverr` low. Every flop runs on the router's bus
  clock and reset. An instance with `addressMultiples` above 1 gets one arm
  spanning all its slots.
- **Router model** (`templates/systemc/constructor.py::addressDecoder`,
  `common/systemc/apbBusDecode.h`). An `abpBusDecode` built with
  `maxAddressSpaces`, `log2(addressIncrement)` and a channel array indexed by
  `addressID`, with `nullptr` for empty slots and for slots of instances not in
  `instanceWithRegApb`. An instance with `addressMultiples` above 1 fills that
  many consecutive channels.
- **Handler RTL** (`templates/systemVerilog/moduleRegs.py`). Takes the leaf's
  module parameters. Decodes each register and memory at its worst-case
  footprint. Words of a parameterizable register above the bound variant's
  width are elaborated away and read 0. A parameterizable memory decodes only
  the bound depth, and rows past it fall to the default arm. The default arm
  ACKs with `32'hBADD_C0DE`. `pslverr` is tied `0`. Under the default module
  parameter `APB_READY_1WS = 0`, `pready` never stalls; setting it to 1
  registers ready and read data, adding one wait state.
- **Handler model** (`templates/systemc/blockRegs.py`, `hwRegisterIf` /
  `addressMap`). Binds the port named by `registerBusPort`.
- **Firmware address enum.** The `types:` row from `generateAddressEnums`
  is emitted into the router file's `includeFW` header inside
  `fw_ns::<owner>_<includeName>`, folded into `fw_ns` by `using namespace`
  (`fw_ns::ip_test_ip_top` in the example below). In
  `examples/ip_test`, `top/fw/ip_topIncludesFW.h` carries `addr_id_top` with
  `ADDR_ID_TOP_UIP0`, `ADDR_ID_TOP_UIP1` and `ADDR_ID_TOP_UBRIDGE`.

## 8. Invariants and limits

- One `registerPorts:` row per block. `registerPorts:` and `addressBlock:` are
  exclusive.
- One reachable instance per router block. A nested-router host has one
  reachable instance. A topInstance block may not be a router
  (`_validateTopInstanceBlockNotRouter`).
- One primary router per build.
- A nested router's host sits directly in the parent router's container. A
  passthrough never leads to a router.
- No adaptation between `interfaceType`s on the register bus. A protocol change
  needs a user block.
- Within a project, at most one router block declares a given group name, so
  a group belongs to one router block and two router block types cannot share
  it.
- A `(project, group)` key never falls outward to an ancestor or sibling
  project. The view, the slot counter, the span check and the enum all use the
  key of the referring file's own project.
- The enum is not project-qualified. Every context's firmware names fold into
  `fw_ns`, so `varType` and `enumPrefix` must be unique build-wide; the
  `validateAddressGroupEnumIdentity` gate enforces it.

## 9. Reference fixtures

- `examples/apbDecode`: one router, two leaves.
- `examples/mixed`: a register-owning container served by a sibling router.
- `examples/ip_test`: a reusable `registerPorts:` IP, a nested router in
  `ipBridge`, and the IP's standalone harness router `ipStdDecode`.
- `unittest/test_addrctl_*.py`: topologies (single router, two- and
  three-level chains, fan-out, block reuse across levels, passthrough,
  inference, port naming).
- `unittest/test_addrgroup_*.py`, `unittest/test_error_addrgroup_*.py`:
  project-qualified groups and the enum identity gate.
- `unittest/test_error_*router*.py`, `unittest/test_error_register_*.py`,
  `unittest/test_error_nested_decoder_overflow.py`: diagnostics.
