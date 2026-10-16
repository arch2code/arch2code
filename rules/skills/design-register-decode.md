---
name: design-register-decode
description: Guide for designing the register/memory decode hierarchy in arch2code. It covers deciding where registers and memories live, declaring the generated apbDecode router (addressBlock:), routed leaves (registerPorts:/regAccess), passthrough containers, nested routers, worst-case address sizing of parameterizable registers and memories, and the one upstream feed you author by hand. Use when making registers or memories firmware-accessible or adding a register-bus decoder.
---
# Skill: design register and memory decode

## Purpose
This skill decides where registers and memories live, how the router that
decodes them is declared, what the generator wires for you, and the one
upstream feed you write by hand. It owns the decode rule, the address-group
naming rules, worst-case sizing of parameterizable registers and memories, and
the diagnostic table.

Other skills cover the rest:
*   `design-architecture.md` for general blocks, instances and wiring.
*   `manage-address-space.md` for address policy (`instanceGroups:`,
    `addressObjects:`) and firmware headers.
*   `rtl-registers.md` for the RTL side of `ext`/`ro`/`rw` registers.
*   `address-migration.md` for converting a legacy `addressControl.yaml` project.

## Reference projects
Each of these builds. Copy patterns from them.
*   `builder/base/examples/apbDecode/`: one router, two leaves (§8).
*   `builder/base/examples/mixed/`: container `blockB` owns registers and
    forwards them with `registerConnections` (§9).
*   `builder/base/examples/ip_test/`: reusable IP with `registerPorts:`, and a
    nested router inside `ipBridge` (§10).
*   `builder/base/examples/twoClk/`: a memory on a clock other than the
    register clock (§4).

---

## 1. The model and the decision rule

A **router** is a block with an `addressBlock:`. `make newmodule` scaffolds its
RTL from the `apbDecodeModule` template and `make gen` fills it. Never
hand-write decode logic or a demux. A router owns no registers and no
`regAccess` memories.

A **register consumer** is a block that owns registers or `regAccess`
memories, or declares `registerPorts:`. The generator synthesizes a handler
block for each block that owns registers or `regAccess` memories. It is named
`<block>` plus `fileGeneration.regBlockNaming.blockSuffix` from `project.yaml`,
which defaults to `_regs`. The examples set `Regs`, so `examples/apbDecode`
gets `blockARegs`.

A router dispatches to register consumers among its **siblings**, the other
instances in its own container. It never decodes the container it sits in.
The instance it dispatches to carries `addressGroup:` set to the router's
`addressBlock.addressGroup`.

For each register consumer, walk outward from its instance:

1.  **Its container holds a router.** The instance is a leaf of that router
    and carries the router's group.
2.  **Its container has no router, owns no registers or `regAccess` memories
    itself, and holds no other register consumer.** The container passes the
    bus through. The container instance is now the consumer, so apply the rule
    again one level up. Only the outermost passthrough container instance, the
    one beside the router, carries `addressGroup:`. Every register consumer
    inside it carries none, and the build rejects one that does.
3.  **Anything else needs a router in the container.** Add an `addressBlock:`
    router as a sibling of the consumers. If that container is itself served
    from above, it now hosts a **nested router**. Its instance must sit
    directly in the parent router's container, carries the parent router's
    group, and must not own registers or `regAccess` memories. Move any it had
    onto a child leaf the inner router serves.

What this means for common layouts:
*   **A container may own registers when nothing inside it is a register
    consumer.** It is then an ordinary leaf of a sibling router and forwards
    values to its children with `registerConnections`. Do not invent a leaf
    block to hold the register. `examples/mixed` is the case: `blockB` owns
    `rwD` and `roBsize`, its children own none, and its sibling `uAPBDecode`
    serves it.
*   **A container that owns registers and also holds a register consumer**
    has no legal router-less form. Adding a router makes it a nested-router
    host, which cannot own registers, so its registers move onto a child leaf.
*   **A DUT top that holds a router cannot own registers.** That router
    serves the top's children, not the top. A router added above would make
    the top a nested-router host, which cannot own registers either. Move the
    registers onto a child leaf the inner router serves. A DUT top with no
    router, no registers and one register consumer inside is an ordinary
    passthrough (§11).

---

## 2. Recipe

1.  **Mark the state.** Registers with `regType: rw|ro|ext`, memories with
    `regAccess: rw|ro|wo` (§4). Never add a custom interface to reach a memory.
2.  **Place routers by the rule in §1.** Declare each router block with an
    `addressBlock:` (§6) and instance it in the container it serves.
3.  **Set `addressGroup:` on each instance a router dispatches to**: a leaf, the
    outermost passthrough container, or a nested-router host.
4.  **Author the upstream feed into the primary router** (§3).
5.  **Declare `registerPorts:` where it is required.** A block that declares a
    block-level `ports:` section and needs a register bus must also declare
    one `registerPorts:` row. That covers a block that owns registers, hosts a
    nested router, or passes the bus through. A reusable IP declares it so its
    `<block>Base` stays self-contained. A block with no `ports:` section may
    omit it and infer its register bus (§6).
6.  **Forward a container's own register to a child** with a
    `registerConnections:` row.
7.  Run `make db`, `make newmodule`, then `make gen` (see `manage-build.md`).

Never create `<block>_regs` blocks by hand and never set `isRegHandler`. The
build rejects a block that sets it.

---

## 3. What you author and what is synthesized

You author only the feed into the **primary** router, the one not nested in
another router's scope:

1.  The bus-master to DUT `connection` (for example `cpu` to `dut` on the APB
    register-bus interface).
2.  The DUT-boundary `connectionMap` routing that interface into the primary
    router instance.

In the examples the master sits one level above the primary router, so both
rows are authored. When the master and the primary router share a container,
only the `connection` is needed.

`postParseRegisterPorts.py` synthesizes everything below the primary router:
*   each leaf's `<block>_regs` handler block, its instance, and the leaf to
    handler `connectionMap`;
*   each router to leaf dispatch connection, on router port
    `<registerDecoderPort>_<instance>` (for example `apbReg_uBlockA`);
*   for a nested router, the parent router to host connection and the host's
    boundary `connectionMap` into the nested router;
*   for a passthrough container, its boundary port and the `connectionMap`
    bridging it to the consumer inside.

Hand-plumbing the register bus below the primary feed means a rule in §1 is
broken. Fix the placement instead. The one thing you still author below the
feed is `registerConnections:`.

---

## 4. Firmware-accessible memories

`regAccess` makes a memory firmware-accessible. Its value is the access mode:
`rw` (also spelled `true`), `ro` (firmware only reads) or `wo` (firmware only
writes). `false` or absent means no firmware access. Any other value is
rejected. `local: true` is independent of `regAccess`. It keeps the memory in
flops the block can read as an array, and the generator instantiates
`memory_dp_ext` or `memory_sp_ext` for it.

The mode is a contract with firmware. Breaking it never raises `pslverr`:

| Access | RTL | Model |
| :--- | :--- | :--- |
| Firmware write to an `ro` memory | The transfer completes and the memory is unchanged. | The write is dropped and logged at `LOG_ALWAYS`, naming the memory and the offset. |
| Firmware read of a `wo` memory | The transfer completes with zero. The handler never reads the memory. | Returns zero, logged the same way. |

RTL simulation prints nothing for these accesses. The generated handler has no
write path for an `ro` memory and no read pipeline for a `wo` one.

### Which port the register handler takes

`memoryType` fixes what each port can do. The register handler takes one port
and the block keeps the rest. The generator keeps the ports that support the
mode (`ro` needs a port that can read, `wo` one that can write, `rw` one that
can do both), prefers the port whose capability matches the mode exactly, then
takes port B. A memory with no supporting port is rejected.

| `memoryType` | `rw` / `true` | `ro` | `wo` |
| :--- | :--- | :--- | :--- |
| `dualPort` | B | B | B |
| `portRportRW` | B | A | B |
| `portRWportW` | A | A | B |
| `portRportW` | error | A | B |
| `singlePort`, `register` | the port | the port | the port |

A table that firmware loads and the datapath reads is `portRportW` with
`regAccess: wo`. A capture buffer that the datapath fills and firmware reads is
`portRportW` with `regAccess: ro`. Because the handler takes a port, a
dual-port `regAccess` memory lists at most one block-side port in `ports:`, and
a single-port one lists none.

### A memory on another clock

The handler's port runs on the owning block's register clock, which
`design-architecture.md` defines under "Register bus clock". The block-side
port runs on the memory's `clock:`, which defaults to the block's default
clock. When the two differ, the ports cross inside the RAM with no extra bus
latency. The generated RTL uses `memory_dp` with one `clk` when both ports
share a clock, and `memory_dp_2clk` with `clkA` and `clkB` when they do not.

On FPGA only a memory with one writer synthesizes on two clocks: `portRportW`
or `portRportRW`. `dualPort` and `portRWportW` have two writers, so on two
clocks they suit simulation or an ASIC memory macro only.

A single-port memory (`singlePort`, `register`) and a `local: true` memory have
one clock. With `regAccess`, their `clock:` must be the register clock or the
build is rejected. A memory has no `reset:`.

The RAM does not order the two ports. Load a table while the datapath is not
reading it, or accept that a read colliding with a write returns undefined
data, as block RAM does in silicon.

In `examples/twoClk`, `twoClkTable`'s memory `tbl` is `portRportRW`. The
handler takes read/write port B on the `twoClkReg` bus clock `clk`, and the
block keeps read-only port A on `clkSlow`.

---

## 5. Address sizing of parameterizable registers and memories

The address map reserves each register and `regAccess` memory at its worst
case over every variant, so offsets do not move between variants.

*   **Width.** A parameterizable register or memory row sizes with its
    structure's `maxBitwidth`. `design-parameterizable-blocks.md` says how
    types and constants set that bound.
*   **Depth.** `wordLines` naming a parameterizable constant sizes with that
    constant's `maxValue`. `wordLines` naming a block parameter sizes with the
    `maxValue` of the `ipParameters:` constant backing that parameter, not
    with the largest variant binding. A variant that binds the parameter above
    that `maxValue` fails `make db`.

```yaml
ipParameters:
  constants:
    IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}

blocks:
  ip:
    desc: "Parameterized IP"
    params: [IP_MEM_DEPTH]

memories:
  # Reserves 32 rows in every variant.
  - {memory: ipMem, block: ip, structure: ipMemSt, addressStruct: ipMemAddrSt, wordLines: IP_MEM_DEPTH, regAccess: rw, desc: "IP scratch memory"}
```

Every variant decodes the worst-case footprint, in the RTL and the model alike.
A parameterizable `rw` or `ro` register spans the worst case's words. Row N of
a memory sits at `base + N * stride`, where the stride is the worst-case row
width in bytes rounded up to a power of two, at least 4. §7 says what an access
to the unused part returns.

---

## 6. `addressBlock:` and `registerPorts:` reference

A router block, as in `apbDecode.yaml` and `mixed.yaml`:

```yaml
blocks:
  apbDecode:
    desc: "APB register decoder"
    addressBlock:
      addressGroup: top            # instances it dispatches to name this in addressGroup:
      addressIncrement: 0x01000000 # bytes per address space, a power of two
      maxAddressSpaces: 16         # a power of two
      varType: addr_id_top         # generated address-ID enum type
      enumPrefix: ADDR_ID_TOP_
      upstreamPort: apbReg         # the addressBus interface feeding this router
      registerDecoderPort: apbReg  # downstream register-bus port name
```

`upstreamPort` and `registerDecoderPort` default to `apbReg`. Optional `clock:`
and `reset:` name the router's bus clock and reset from the block's own
`clocks:` and `resets:`. Without them the router uses the block's default clock
and its selected reset. A router declares at most one clock.

A block declaring `addressBlock:` must not also declare `registerPorts:`.

### Group naming

Both rules are `make db` errors.

1.  **A group reference resolves only within the project that owns the
    referring file.** An instance's `addressGroup: top` binds to the
    `addressBlock:` declaring `top` in the same project as the file that
    declares the instance. It never falls outward to a parent or sibling
    project, so two independently written projects may each declare `top` and
    still compose. Within one project, one router block at most may declare a
    group name. A reusable IP must therefore declare every group it
    references. An IP that names a group only its parent declares cannot
    compose, so move the declaration into the IP or the reference into the
    parent.
2.  **`varType:` and `enumPrefix:` must be unique across the whole build**,
    even across projects. Group names are project-qualified, but the generated
    firmware enum is not. Every context's firmware lands in one flat `fw_ns`
    namespace, and firmware headers include each other across projects. Two
    groups sharing a `varType:` either collide as a C++ redefinition or, in
    separate translation units, bind the same enumerator to different address
    IDs, which gives a wrong address with no build failure. In a reusable IP,
    qualify both by the declaring project (`varType: addr_id_isp_lut_top`,
    `enumPrefix: ADDR_ID_ISP_LUT_TOP_`). The bare `addr_id_top` above is safe
    only in a project nothing else composes.

### `registerPorts:`

A reusable IP declares its register-bus port, as `ip_test`'s `ip` block does:

```yaml
blocks:
  ip:
    desc: "Reusable IP"
    ports:
      ipDataIf: { interface: ipDataIf, direction: dst }
    registerPorts:
      regs: { interface: ipReg }   # exactly one row; ipReg is an apb interface
```

The row's interface must have an `addressBus: true` interface type, and it must
be visible in the block's own file.

A row may also set `clock:` and `reset:`, naming one of the block's own clocks
and resets. The register port and handler run on that clock, which defaults to
the block's default clock, and every instance must bind it to the serving
router's bus clock. Without `reset:` the handler takes that clock's selected
reset, and `make db` does not check that it binds to the router's bus reset.
State `reset:` whenever the two can differ. `design-architecture.md` gives the
full rule under "Register bus clock".

### Inferring the register bus

A block with no `registerPorts:` infers its register bus from the nearest
authored boundary of each of its instances. That boundary is the innermost
router-less passthrough container enclosing the instance that declares
`registerPorts:`, if there is one. Otherwise it is the serving router. A
container boundary offers its `registerPorts:` key and interface. A router
offers its `registerDecoderPort` and register-bus interface.

The block gets one register-bus port, named by the block alone and never by
which instance is declared first. When every instance's boundary offers the
same name, the port takes it. When the names differ, the port takes the name of
the inferred interface. The name must differ from every register, memory, port,
clock and reset of the block. A `<block>_regs` handler's register-bus port
takes the leaf's port name. For a reusable IP that is the `registerPorts:` key,
so `ip`'s handler port is `regs` in every build.

Names may differ, but interfaces may not. Every instance must infer the same
interface. The inferred interface name must also resolve to that interface in
the file where the block's register-bus rows are synthesized. The appendix
gives the fix for each error.

---

## 7. Unmapped and out-of-range accesses

Generated handlers and the router's unmapped response tie PSLVERR low. A
hand-written leaf behind `registerPorts:` can raise it, and the router forwards
it upstream. The read value depends on who answers:

*   **An address space no instance fills.** The router answers. Reads return
    `32'hBADD_C0DE` and writes are dropped.
*   **An address in a block's decoded range that no register or memory
    claims.** The block's handler answers with `32'hBADD_C0DE` and drops the
    write. This includes rows the address map reserves past a parameterizable
    memory's bound depth (§5).
*   **Words of a parameterizable register, or bytes of a memory row, above the
    bound variant's width.** These belong to the register or row, so they read
    0 and drop the write.
*   **An address past the block's decoded range but inside its address space.**
    It aliases through the handler's address mask onto an address in the
    range, and reads whatever is there.

A data bus narrower than 32 bits returns the value truncated to its width, such
as `0xC0DE` at 16 bits. For both `BADD_C0DE` cases the model also logs at
`LOG_ALWAYS`, naming the decoder or block and the address. The RTL prints
nothing.

---

## 8. Walkthrough A: one router (`examples/apbDecode`)

DUT `someRapper` holds the router `uAPBDecode` and two leaves. The `cpu` master
is one level up in `top`.

```yaml
blocks:
  apbDecode:
    addressBlock: { addressGroup: top, ..., upstreamPort: apbReg, registerDecoderPort: apbReg }
instances:
  uAPBDecode: { container: someRapper, instanceType: apbDecode }
  uBlockA:    { container: someRapper, instanceType: blockA, addressGroup: top }
  uBlockB:    { container: someRapper, instanceType: blockB, addressGroup: top }
connections:
  - {interface: apbReg, src: uCPU, dst: uSomeRapper}                             # upstream feed
connectionMaps:
  - {interface: apbReg, block: someRapper, direction: dst, instance: uAPBDecode}  # DUT boundary to router
memories:
  - {memory: blockATable0, block: blockA, ..., regAccess: true}
registers:
  - {register: roA, regType: ro, block: blockA, ...}
```

You author the master to DUT `connection` and the boundary `connectionMap`. The
generator adds `blockARegs` and `blockBRegs`, their instances and maps, and
the dispatch from `uAPBDecode` to `uBlockA` and `uBlockB`.

## 9. Walkthrough B: a container owns a config register (`examples/mixed`)

Container `blockB` owns `rwD`, `roBsize` and memories, and forwards them to its
children with `registerConnections`. Its children own no registers, so nothing
inside `blockB` needs a router. Its sibling `uAPBDecode` serves it.

```yaml
# mixed.yaml
blocks:
  apbDecode:
    addressBlock: { addressGroup: top, ..., upstreamPort: apbReg, registerDecoderPort: apbReg }
instances:
  u_mixed:    { container: mixed_tb, instanceType: mixed }
  uCPU:       { container: mixed_tb, instanceType: cpu }
  uBlockB:    { container: mixed,    instanceType: blockB, addressGroup: top }
  uAPBDecode: { container: mixed,    instanceType: apbDecode }
  uBlockD:    { container: blockB,   instanceType: blockD }
  uBlockF0:   { container: blockB,   instanceType: blockF, variant: variant0 }
registers:
  - {register: rwD, regType: rw, block: blockB, structure: dRegSt, desc: A Read Write register}
registerConnections:
  - {register: rwD, block: blockB, instance: uBlockD }
  - {register: rwD, block: blockB, instance: uBlockF0 }
connections:
  - {interface: apbReg, src: uCPU, dst: u_mixed, name: cpu_main}
connectionMaps:
  - {interface: apbReg, block: mixed, direction: dst, instance: uAPBDecode, name: cpu_main}
```

## 10. Walkthrough C: reusable IP and a nested router (`examples/ip_test`)

The primary router `uAPBDecode` (group `top`) sits in `ip_top` and serves the
reusable `ip` leaves `uIp0` and `uIp1` and the container `uBridge`. Inside
`ipBridge` a second router, `uBridgeAPBDecode` (group `bridge`), serves
`uBridgeIp0` and `uBridgeIp1`. `uBridge` carries `addressGroup: top`, the
parent router's group. The key of `ipBridge`'s `registerPorts:` row must equal
the nested router's `upstreamPort`.

```yaml
# ip_top.yaml
blocks:
  apbDecode:
    addressBlock: { addressGroup: top, ..., upstreamPort: apbReg, registerDecoderPort: apbReg }
instances:
  uAPBDecode: { container: ip_top, instanceType: apbDecode }
  uIp0:       { container: ip_top, instanceType: ip,       addressGroup: top, variant: variant0 }
  uIp1:       { container: ip_top, instanceType: ip,       addressGroup: top, variant: variant1 }
  uBridge:    { container: ip_top, instanceType: ipBridge, addressGroup: top }
connections:
  - {interface: apbReg, src: uCPU, dst: u_ip_top, name: cpu_main}
connectionMaps:
  - {interface: apbReg, block: ip_top, direction: dst, instance: uAPBDecode, name: cpu_main}

# ipBridge.yaml: no register-bus feed is authored here
blocks:
  ipBridge:
    ports:
      data8In:  { interface: data8If,  direction: dst }
      data70In: { interface: data70If, direction: dst }
    registerPorts:
      apbReg: { interface: apbReg }   # key matches bridgeApbDecode's upstreamPort
  bridgeApbDecode:
    addressBlock: { addressGroup: bridge, ..., upstreamPort: apbReg, registerDecoderPort: apbReg }
instances:
  uBridgeAPBDecode: { container: ipBridge, instanceType: bridgeApbDecode }
  uBridgeIp0:       { container: ipBridge, instanceType: ip, addressGroup: bridge, variant: variant0 }
  uBridgeIp1:       { container: ipBridge, instanceType: ip, addressGroup: bridge, variant: variant1 }
```

You still author only the feed into `uAPBDecode`. The generator adds the
dispatch from `uAPBDecode` to `uBridge` and the `ipBridge` boundary
`connectionMap` into `uBridgeAPBDecode`.

## 11. Walkthrough D: a passthrough container

This is the top-down case from
`builder/base/unittest/test_addrctl_passthrough_single_consumer.py`. `wrapTD`
has no router, owns no registers, and holds one register consumer, so it passes
the bus through. The router dispatches to `uWrapTD`, which carries the group.
The leaf inside carries none.

```yaml
instances:
  uTop:        { container: top,    instanceType: top }        # the topInstance
  uCPU:        { container: top,    instanceType: cpu }
  uAPBDecode:  { container: top,    instanceType: apbDecode }
  uWrapTD:     { container: top,    instanceType: wrapTD, addressGroup: top }
  uInnerLeaf:  { container: wrapTD, instanceType: innerLeaf }   # no addressGroup:
connections:
  - { interface: apbReg, src: uCPU, dst: uAPBDecode }
registers:
  - { register: cfg, regType: rw, block: innerLeaf, structure: cfgRegSt, desc: "" }
```

The generator gives `wrapTD` a boundary port `apbReg` and a `connectionMap`
onto `uInnerLeaf`, and synthesizes `innerLeaf_regs`.

If `wrapTD` declared a `ports:` section, it would also need one
`registerPorts:` row (§2 step 5). The key names its register-bus port. The
interface may be any `addressBus: true` interface with the router's
`interfaceType` and field widths. The router's `upstreamPort` interface is the
simple choice: `registerPorts: { apbReg: { interface: apbReg } }`.

---

## Appendix: diagnostics

Most decode errors are YAML placement mistakes. Match the message, fix the
declaration, and never patch generated output.

| Message | Cause | Fix |
| --- | --- | --- |
| `Leaf instance '…' (block '…') is in container '…' which is not served by any router, directly or through single-consumer containers. …` | No router in the leaf's container, and no passthrough chain reaches one. | Add a router as the leaf's sibling. Or apply §1 rule 2, putting the leaf under passthrough containers a router serves, with `addressGroup:` on the outermost one. A hand-written `connectionMap` is not a fix. |
| `Leaf block '…' needs a register handler but no router was found serving any of its instances, directly or through single-consumer containers. …` | The same placement error, found during handler synthesis. A DUT top that owns registers while its only router is inside it is the usual case. | As above. For a DUT top that holds the router, move its registers onto a child leaf that router serves (§1). |
| `Container block '…' hosts N instances that need a register bus (…) but no register-decode router (addressBlock:). …` | A router-less container holds two or more consumers. A passthrough feeds exactly one. | Add an `addressBlock:` router to the container, or move all but one consumer under a routed container. |
| `Container block '…' owns firmware-accessible registers/memories itself and also hosts register-bus consumer(s) (…) but no register-decode router (addressBlock:). …` | A container that owns registers already uses its boundary for its own handler. | Move its registers onto a child leaf and add a router to the container (§1). |
| `block '…' hosts a nested register-decode router but also owns firmware-accessible registers/memories. …` | A nested-router host cannot also deliver its own handler. | Move the registers and memories onto a child leaf the inner router serves. |
| `block '…' is a register-decode router (addressBlock:) but also owns register '…'.` (or `owns regAccess memory '…'`) | A router's module is generated whole from `addressBlock:`. | Declare the register or memory on a leaf the router serves. |
| `Instance '…' (block '…') is fed through router-less container '…' and must not carry addressGroup: (the routed slot is instance '…'); remove it.` | Only the outermost passthrough container carries the group. | Remove `addressGroup:` from the named instance and set it on the routed slot the message names. |
| `block '…' requires a register-bus interface (…) but declares no registerPorts:. A reusable IP must declare its register-bus boundary under registerPorts:.` | The block declares a `ports:` section and needs a register bus. | Add one `registerPorts:` row naming the register-bus interface. |
| `In …, block '…' declares both registerPorts: and addressBlock:; these are mutually exclusive.` | A router is not a leaf. | Remove whichever field does not belong on the block. |
| `In …, block '…' declares multiple registerPorts: entries ('…'). Blocks support exactly one register-bus ingress.` | More than one `registerPorts:` row. | Keep one row. |
| `In …, registerPorts port '…' references interface '…' whose interfaceType '…' is not marked addressBus: true.` | The row names a non-register-bus interface, such as a `push_ack` one. | Name the register-bus interface, whose interface type carries `addressBus: true`. |
| `In file …, section …, key:… field interface, value … was not valid in context …`, on a `registerPorts:` row | The `registerPorts:` interface is not visible in the block's file. | Declare or `include:` the interface in the block's own file so its `<block>Base` is self-contained. |
| `block '…' sets isRegHandler: true. …` | `isRegHandler` is set only by synthesis. | Remove it. |
| `Block '…' declares no registerPorts: and infers its register-bus interface from the nearest authored boundary of each instance, but its instances infer different interfaces: …` | The block's instances reach boundaries on different interfaces. A block has one register port type. | Use a separate block per boundary. If no source is a router, you may instead give the boundaries one `registerPorts:` interface. If the routers among the sources share one `upstreamPort` interface, you may instead give the `registerPorts:` boundaries that interface. |
| `Block '…' declares no registerPorts: and infers register-bus interface '…' declared in file …, but in file …, where its register-bus rows are synthesised, …` | The inferred interface name resolves to a different interface, or none, where the rows are emitted. That is the block's own file for a block that gets a handler, and on the passthrough path the file declaring the inner instance the container feeds. | Rename one interface, include the file that declares it, or declare `registerPorts:` on the block. |
| `Block '…' declares no registerPorts: and takes its register-bus port name '…' from …, but block '…' already uses '…' as a …` | The inferred port name clashes with a register, memory, port, clock or reset of the block. | Rename the clashing item or the source of the name, or declare `registerPorts:` on the block. |
| `No primary router could be inferred …` | Every router is nested under another. | Leave exactly one router outside every other router's scope. |
| `Multiple candidate primary routers: …` | Two or more routers are un-nested. | Nest all but one under the primary by giving each host container the parent's `addressGroup`. |
| `Nested router '…' (block '…') is hosted by block '…', whose instance '…' sits in router-less container '…' … not supported. …` | A passthrough does not carry the bus to another router. | Move the host instance into the dispatching router's container, or add a router to the router-less container. |
| `Router block '…' has multiple instances ('…' in '…', '…' in '…'). …` | A router block is instanced more than once. | Use one router block per scope, as `apbDecode` and `bridgeApbDecode` do. |
| `Block '…' hosts nested router '…' (block '…') and has N instances: '…', '…'. …` | The host would instance its router more than once. | Give each instance its own host block with its own router block and group. |
| `Router blocks declare addressBlock: but have no instances in the design: …` | A router block is never instanced. | Instance it in the container it serves. |
| `Register-decode router(s) owned by project '…' are instantiated only outside its reachable top, …` | The project's router is instanced only in another project's tree. | Instance the router under this project's `topInstance`, or move it to the project whose top instances it. |
| `In …, addressGroup '…' declared on block '…' duplicates a prior addressBlock: declaration on block '…' in …, both in project '…'. …` | Two router blocks in one project declare one group. | Rename one group, with its own `varType:` and `enumPrefix:`, or drop the redundant router. |
| `In …, '…' referenced address group '…', which project '…' does not declare. …` | The group is not declared in the project owning the referring file. | Declare it on a router in that project, or move the reference into the project that owns the name. The message lists the projects seen declaring the name so far, not every project in the build. |
| `addressBlock: enum type name varType: '…' is used by two address groups: …` (also for `enumPrefix:`) | Two groups share a firmware enum identity. | Give one group a distinct `varType:` and `enumPrefix:`, qualified by its project. |
| `Router '…' (block '…') serves addressGroup '…', but no instance in this build's design tree carries addressGroup: …` | No instance reachable from the active `topInstance` carries the group. A child project's standalone harness does not count. | Set the group on a register consumer the router dispatches to, or remove the `addressBlock:`. |
| `Router '…' (block '…') serves addressGroup '…', but no instance carrying addressGroup: … has a register bus for it to dispatch to: …. …` | None of the instances in the group is a register consumer. | Give one a register, a `regAccess` memory or `registerPorts:`, or remove the `addressBlock:`. |
| `Instance '…' (block '…') has a register bus, and router '…' … dispatches to it, but it carries no addressGroup:. …` (also `passes the register bus to '…'` for a passthrough container) | The router allocates a slot only to an instance carrying its group. | Set the router's group on the named instance. |
| `… dispatches to it, but it carries addressGroup: …. Change addressGroup: … to …` | The instance names another router's group. | Use this router's group, or move the instance next to the router that owns the group it names. |
| `Instance '…' (block '…') hosts nested router '…', and router '…' … dispatches to it, but it carries no addressGroup:. …` (or names the inner router's group) | A nested-router host is a slot in the parent router's group. | Set the parent's group, as `uBridge` in `examples/ip_test/top/yaml/ip_top.yaml` does. |
| `… Its addressGroup: … resolves in project '…', but the router serves group … of project '…'. …` | The instance is declared in a file of a different project from the router's. | Declare the instance in a file the router's project owns, or move it next to a router of its own project. |
| `Router block '…' (file …) names upstreamPort '…', but no visible interface has that name` (or `does not resolve to an addressBus: true interfaceType`) | `upstreamPort` does not name a visible register-bus interface. | Point it at the register-bus interface, such as `apbReg`, and make that interface visible in the router's file. |
| `Register-bus dispatch from router '…' …: the two interfaces at this junction must share the same interface meta-protocol, …` (or `per-field _bitWidth must agree at every payload position`) | The router and leaf register-bus interfaces differ in `interfaceType` or field widths. Matching names do not exempt the pair. | Use one `interfaceType` on both sides and align the field widths. Different protocols need a protocol-changer block. |
| `Container block '…' (file …) declares registerPorts: key '…', but the nested router '…' (file …) it hosts names upstreamPort '…'. …` | The boundary map wires the container's port straight to the nested router's upstream port by name. | Rename the `registerPorts:` key to the router's `upstreamPort`, as `ipBridge.yaml` does with `apbReg`. |
| `In …, addressBlock: of block '…' (addressGroup '…') sets maxAddressSpaces …, which is not a power of two. …` (also `addressIncrement`) | The RTL decoder masks the address with `addressIncrement × maxAddressSpaces - 1`, and the model decoder shifts it right by log2(`addressIncrement`). A value that is not a power of two aliases or misroutes slots. | Use the suggested power of two. A larger value enlarges the decoder footprint, which can trip the next row. |
| `Block … overflowed its address space. Used: …. Available: …` | The block's worst-case registers and memories need more bytes than its address space holds. | Raise the router's `addressIncrement`, or shrink the block's worst-case footprint (§5). |
| `Nested register decoder '…' (group '…') routes a 0x…-byte footprint …, which exceeds the 0x…-byte window that parent decoder '…' (group '…') allocates to slot '…' …` | A nested router's footprint (`addressIncrement × maxAddressSpaces`) must fit in the window its parent allocates to the host slot. | Reduce the nested router's `addressIncrement` or `maxAddressSpaces`, or raise the parent's `addressIncrement`. |
| `… field regAccess, … is not in the allowed values …` | `regAccess` is not `true`, `false`, `rw`, `ro` or `wo`. | Use one of those. |
| `… memory '…' of block '…' has regAccess: rw, which needs a port that can both read and write, and no port of a portRportW memory does. …` | No port supports the mode (§4). | Use `ro` or `wo`, or a `memoryType` with a read/write port. |
| `… memory '…' of block '…' lists port 'reg', but with regAccess the register handler's port is channel '…', …` | With `regAccess`, the handler's port takes the channel `<memory>_reg`. | Rename the port. |
| `… memory '…' of block '…' lists N ports ('…') but has M free. …` | `ports:` names more block-side ports than remain after the handler takes one. | List fewer ports, or use a dual-port `memoryType`. The message lists the fixes that apply. |
| `Memory '…' of block '…' has regAccess and is on clock '…', but the block's register bus is on '…'. A … memory has one clock, …` | A single-port `regAccess` memory is not on the register clock. | Set its `clock:` to the register clock, or use a dual-port `memoryType`. |
| `In …, memory '…' of block '…' is local, and its ports run on two clocks: …` | A `local: true` `regAccess` memory is not on the register clock. | Set its `clock:` to the register clock, or remove `local`. |
| `In file …, memory '…' sets a reset field. …` | A memory row sets `reset:`. | Remove it. |
| `Register-decode router block '…' declares more than one clock (…). …` | A router runs entirely on its register-bus clock. | Declare at most one clock in the router's `clocks:`. |
| `Block '…' addressBlock: runs its register bus on clock '…', but '…' has no selected reset and addressBlock: names no reset:. …` (or `the selected reset of '…' is '…', an output reset of '…',`) | The router's bus clock has no input reset. | Declare a synchronous input reset on that clock in the router's `resets:`, marked `default: true` if the clock already has a synchronous reset, or name a synchronous input reset of that clock in `addressBlock:` `reset:`. |
| `Instance '…' of block '…' declares its register port on clock '…', but that is not bound to the same container clock as the serving router's own bus clock. …` | A `registerPorts:` leaf's register port runs on a clock not bound to the router's bus clock. | Bind that clock to the router's bus clock in the instance's `clocks:` map, or change the `registerPorts:` `clock:`. |
| `Instance '…' of block '…' declares its register port's reset as '…' (registerPorts: reset:), but that is not bound to the same container reset as the serving router's own bus reset. …` | The instance binds the `registerPorts:` `reset:` to a different container reset from the router's bus reset. | Bind that reset to the router's bus reset in the instance's `resets:` map, or change the `registerPorts:` `reset:`. |
| `Instance '…' of block '…' needs a register-bus port, but none of its declared clock ports is bound to the register bus's clock, and the register port runs on that clock. …` | A block that infers its register bus has no input clock bound to the router's bus clock. | Bind one of the block's clock ports, in its `clocks:` map, to the container clock the router's bus clock is bound to. |
| `Instance '…' of block '…' needs a register-bus port, but none of its declared reset ports is bound to the register bus's reset, and the register port uses that reset. …` | A block that infers its register bus has no synchronous input reset bound to the router's bus reset. A reset with `async: true` does not count. | Bind one of the block's synchronous input resets, in its `resets:` map, to the container reset the router's bus reset is bound to. |
| `Block '…' is generated once, but its instances resolve the register port to different clock/reset pairs (…): …. …` | Instances of a block that infers its register bus bind different clock or reset ports to the bus. | Bind the same clock and reset ports to the register bus in every instance's `clocks:` and `resets:` maps. |
| `Block '…' registerPorts: entry '…' runs on clock '…' and names reset: '…', which belongs to clock '…'. …` (or `an asynchronous reset input belonging to no clock`) | The register handler runs on the entry's clock, so its reset must be a synchronous reset of that clock. | Name a reset of that clock in `reset:`, or remove `reset:` to use the clock's selected reset. |
| `In …, ext register '…' of block '…' is N bits wide, wider than the 32-bit register bus. …` (or `can be up to N bits wide` for a parameterizable structure) | An `ext` register reaches its owner as one command, so it must fit one 32-bit access, measured at its worst case. | Narrow or split the register. For a parameterizable structure, narrow its fixed fields or lower the `maxBitwidth` and `maxValue` bounds that set its width. |
| `Interface '…' (file …) has interfaceType '…', an address-bus interface, but carries parameterizable structure(s) …` | A register bus is fixed-width. Registers and memories behind it may be parameterizable, the bus may not. | Give the bus a fixed-width structure. |
| The router's RTL is an empty skeleton with ports only. | `make newmodule` ran before `addressBlock:` existed. | Add `addressBlock:`. Move any hand edits out of the router's `.sv`, delete the file, then run `make newmodule` and `make gen`. |
| A `<block>_regs` handler's `.sv` or `.cppm` is missing at build time. | The block gained its first register or `regAccess` memory after the last `make newmodule`. `make gen` fills only files that exist. | Run `make newmodule`, then `make gen`. |

---

## References
*   General blocks and wiring: `design-architecture.md`
*   Address policy and firmware headers: `manage-address-space.md`
*   RTL `ext`/`ro`/`rw` registers: `rtl-registers.md`
*   Build and scaffold targets: `manage-build.md`
*   Legacy `addressControl.yaml` conversion: `address-migration.md`
*   `builder/base/config/postParseRegisterPorts.py`: the pass that synthesizes
    everything below the primary router and raises most of the diagnostics in
    the appendix
