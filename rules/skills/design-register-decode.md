---
name: design-register-decode
description: Greenfield guide for designing the register/memory decode hierarchy in arch2code - deciding where registers/memories live, declaring the generated apbDecode router (addressBlock:), routed leaves (registerPorts:/regAccess), nested routers, and the one upstream feed you author by hand. Use when making registers or memories firmware-accessible or adding a register-bus decoder.
---
# Skill: Design Register/Memory Decode

## Purpose
Guide greenfield design of the firmware register-bus decode hierarchy in
arch2code (`yamlFormat: 2`): how to decide where registers/memories live, how
the router (decoder) block is declared and generated, what gets auto-wired, and
what single upstream feed you author by hand.

This skill is the canonical home for the decode **decision rule**, the
**recipe**, the invariants, worked walkthroughs, and the **failure-mode →
diagnostic appendix**. `design-architecture.md` carries only the field reference;
`manage-address-space.md` covers address policy + firmware headers;
`rtl-registers.md` covers RTL-side `ext`/`ro`/`rw` register implementation.

## Source-of-truth artifacts
These in-tree projects compile and generate; copy real patterns from them or
verify behavior against them (each is walked through later). The auto-wiring
itself lives in `postParseRegisterPorts.py` — read it when you need to
understand or debug synthesis.
*   `builder/base/examples/apbDecode/` — single router, two leaves (§6).
*   `builder/base/examples/mixed/` — container `blockB` owns registers and
    forwards them via `registerConnections` (§7).
*   `builder/base/examples/ip_test/` — reusable-IP `registerPorts:` + nested
    router (§8).
*   `builder/base/config/postParseRegisterPorts.py` — the distribution pass that
    synthesizes everything below the primary router.

---

## 1. The mental model

A **router** (decoder) is a block with a populated `addressBlock:`. Its RTL is
**generated** from the `apbDecodeModule` template and scaffolded by
`make newmodule` — you never hand-write decode logic, demux, or a manual
top-level decoder.

A **routed leaf** is a block that owns `registers` or `regAccess` memories,
**or** authors a `registerPorts:` row. The framework synthesises its
`<block>_regs` handler and a router→leaf dispatch connection.

The single most important fact:

> **A router serves the other instances in its OWN container (its siblings),
> nested routers, and, through a chain of router-less single-consumer
> containers, a leaf further down. It NEVER decodes its own container block.**

So the decision is **not** "container vs leaf". It is: **is this block served by
a sibling/parent decoder, directly or through a router-less container that
passes the bus through to it alone?** A block that owns registers is fine as
long as some *other* decoder (a sibling in its container, a parent decoder, or
one reached through such a passthrough container) dispatches to it.

### The decision rule

A block that owns registers or `regAccess` memories is a routed leaf; a decoder
must dispatch to it from the **same container** (a sibling router) or from a
parent (the block is then itself a routed leaf of that parent). Apply:

*   **A container block MAY own registers/memories** — *provided none of its
    contained leaves needs its own register-decode block* (no contained
    sub-block owns registers / `regAccess` memories / `registerPorts:`). The
    container is then simply a routed leaf served by a sibling/parent decoder,
    and it forwards its own register values to sub-blocks via
    `registerConnections`. This is the common config-register pattern.
    **`examples/mixed` is the canonical example**: container `blockB` owns
    `rwD`/`roBsize` and is served by its sibling `uAPBDecode` (both in `mixed`);
    the blocks it contains (`uBlockD`/`uBlockF0`/`uBlockF1`) own no registers, so
    nothing inside `blockB` needs a decoder. Do **not** invent leaf blocks to
    "hold" the register.

*   **If a contained leaf DOES need a reg-decode block**, instance a decoder
    *inside* the container to serve that leaf — the container becomes a
    decoder-host. A decoder-host that **also** owns registers is the
    **nested-router case**: the container must itself be a routed leaf of a
    parent decoder (two address groups). Either nest deliberately (see the
    `ip_test` bridge), or move the container's registers onto a dedicated child
    leaf the inner decoder serves.

*   **The failure case** is a block that owns registers but has *no decoder
    serving its container* — classically a DUT-top block that contains the
    *only* decoder *inside itself* (that inner decoder serves the top's children,
    not the top). Fix: add a decoder in the parent/testbench so the top becomes a
    routed leaf, or move those registers onto a child leaf the inner decoder
    already serves. **Do not** "fix" it with a hand-authored `connectionMap`.

`regAccess` (`rw`, `ro` or `wo`, with `local:` absent) is the single switch
that makes a memory firmware-accessible. No custom streaming/"load" interface
is ever needed.

---

## 2. Recipe

To make a block's registers/memories firmware-accessible:

1.  **Mark the state.** `regType: rw|ro|ext` registers and/or memories with
    `regAccess: rw|ro|wo` (`true` means `rw`; no `local:`). Never substitute
    a custom interface.
2.  **Place a router in the leaf's container.** Declare a decoder block with a
    populated `addressBlock:` and instance it as a sibling of the routed leaf
    (same container). Pick an `addressGroup` name for that router.
3.  **Tag the routed leaf instance** with `addressGroup: <that group>`.
4.  **Author the upstream feed** into the primary router only (§3).
5.  **(Reusable IP only)** add one `registerPorts:` row to the IP block (§5).
    Plain top-down leaves omit it and infer the register bus from the router.
6.  **(Container owns a register a child consumes)** add a `registerConnections:`
    row forwarding it to the child instance.
7.  `make db` → `make newmodule` (scaffolds the router with the
    `apbDecodeModule` template and any new blocks) → `make gen`.

Never create `<block>_regs` blocks by hand — they are synthesized. Never set
`isRegHandler` yourself.

---

## 3. Authored vs. synthesized (what you write by hand)

You author **only the upstream feed into the PRIMARY router**:

1.  The bus-master→DUT `connection` (e.g. `cpu → dut`, interface = the APB
    register bus).
2.  The DUT-boundary `connectionMap` routing that interface into the primary
    router instance.

In the in-tree examples the bus master sits one level above the primary router
(e.g. `apbDecode`'s `uCPU` in `top` feeds the DUT `uSomeRapper`, whose router is
`uAPBDecode`), so both the `connection` and the boundary `connectionMap` are
authored. If the master and the primary router instead share a container, the
`connectionMap` is unnecessary and only the `connection` is authored.

Everything below the primary router is **synthesized** by
`postParseRegisterPorts.py`:

*   each routed leaf's `<leaf>_regs` handler block, instance, and
    leaf-to-handler `connectionMap`;
*   the router→leaf dispatch connection;
*   for nested routers, **both** the parent-router→child-container connection
    **and** the child-container boundary `connectionMap` into the nested router;
*   for a router-less container passing the bus through to its single register
    consumer, the container's own boundary port and a `connectionMap` bridging
    it to that consumer.

So for nested routers you author **nothing** for the register bus below the
primary feed. Over-authoring the nested boundary map is wrong.

`registerConnections:` is the one thing you still author when a block owns a
register that should be *consumed by a child instance* (forwarding a
container's own register down to a sub-block), as `examples/mixed`'s `blockB`
does.

---

## 4. The four invariants (keep these)

1.  **Co-location.** A routed leaf and its serving decoder share one container,
    or reach one another through a chain of router-less containers that each
    pass the bus through to exactly one register consumer. The instance the
    decoder actually dispatches to (the leaf itself, the outermost such
    passthrough container, or the container instance hosting a nested
    router) carries `addressGroup:` naming the serving
    router's `addressBlock.addressGroup`; a leaf fed through a passthrough
    container carries none. A nested router's container must sit directly in
    its dispatching router's container; a passthrough chain ends at a leaf or
    a `registerPorts:` IP, never at another router.
2.  **Decoder-as-generated-block.** The decoder is a first-class block whose RTL
    is generated from `apbDecodeModule` (auto-selected by `make newmodule`
    because the block carries `addressBlock:`). Never hand-write it.
3.  **Auto-wiring below the decoder.** Once routers and routed leaves are
    declared and co-located, the entire register-bus fan-out below the primary
    router is synthesized. A need to hand-plumb the bus below the primary feed is
    a symptom of a broken invariant, not a fix.
4.  **Single `regAccess` switch.** `regAccess` (with `local:` absent) is the
    only switch to make a memory firmware-accessible. Its value is the
    firmware access mode, below.

> There is **no** "leaf-ownership invariant." Container blocks may own
> registers/memories (see `examples/mixed`'s `blockB`). The real constraint is
> the decoder-position rule
> in §1: a block must be served by a sibling/parent decoder, and is never
> decoded by a decoder it contains.

### Firmware access modes

`regAccess` sets what firmware may do to a memory: `rw` (also spelled
`true`), `ro` (firmware only reads) or `wo` (firmware only writes). Any other
value is rejected. The mode is a contract with firmware. Breaking it never
raises `pslverr`.

| Access | RTL | Model |
| :--- | :--- | :--- |
| Firmware write to an `ro` memory | The transfer completes and the memory is unchanged. | The write is dropped and logged at `LOG_ALWAYS`, naming the memory and the offset. |
| Firmware read of a `wo` memory | The transfer completes with zero. The handler never reads the memory. | Returns zero, logged the same way. |

RTL simulation prints nothing for these accesses. The generated handler has
no write path for an `ro` memory and no read pipeline for a `wo` one.

### Which port the register handler takes

`memoryType` fixes what each port can do. The register handler takes one
port and the block keeps the other. The generator keeps the ports that
support the mode (`ro` needs a port that can read, `wo` one that can write,
`rw` one that can do both), then prefers the port whose capability matches
the mode exactly, then takes port B. A memory with no supporting port is
rejected.

| `memoryType` | `rw` / `true` | `ro` | `wo` |
| :--- | :--- | :--- | :--- |
| `dualPort` | B | B | B |
| `portRportRW` | B | A | B |
| `portRWportW` | A | A | B |
| `portRportW` | error | A | B |
| `singlePort` | the port | the port | the port |

A table that firmware loads and the datapath reads is `portRportW` with
`regAccess: wo`. A capture buffer that the datapath fills and firmware reads
is `portRportW` with `regAccess: ro`. Because the handler takes a port, a
dual-port `regAccess` memory lists at most one block-side port in `ports:`,
and a `singlePort` one lists none.

### A memory on another clock

The register handler's port runs on the owning block's register clock. The
block-side port runs on the memory's `clock:`, which defaults to the block's
default clock. A dual-port `regAccess` memory may sit on any clock its block
declares, and the two ports cross inside the RAM with no extra bus latency.
A `singlePort` memory has one clock, so with `regAccess` its `clock:` must be
the register clock, or the build is rejected. A memory has no `reset:`.

The RAM does not order the two ports. Firmware should load a table while the
datapath is not reading it, or accept that a read colliding with a write
returns undefined data, as the block RAM does in silicon.

`examples/twoClk` is the worked case. `twoClkTable`'s memory `tbl` is
`portRportRW`. The generated handler takes the read/write port B on the
`twoClkReg` bus clock `clk`, and the block keeps the read-only port A on
`clkSlow`.

---

## 5. `addressBlock:` / `registerPorts:` field reference

Router block (`addressBlock:`), as in `apbDecode.yaml` / `mixed.yaml`:

```yaml
blocks:
  apbDecode:
    desc: "APB register decoder"
    addressBlock:
      addressGroup: top            # leaves name this in their addressGroup:
      addressIncrement: 0x01000000 # byte spacing between address spaces, a power of two
      maxAddressSpaces: 16         # a power of two
      varType: addr_id_top         # generated address-ID enum type
      enumPrefix: ADDR_ID_TOP_
      upstreamPort: apbReg         # the addressBus interface feeding this router
      registerDecoderPort: apbReg  # canonical downstream register-bus port
```

Two kinds of access read `32'hBADD_C0DE` and drop the write, in both the model and the RTL. The router answers an access to an address space no instance fills. The block's handler answers an access to an address in the block's decoded range that no register or memory claims. Rows the address map reserves past a parameterizable memory's depth belong to no memory, so they read `32'hBADD_C0DE` too. A data bus narrower than 32 bits reads the value truncated to its width, such as `0xC0DE` at 16 bits. The access still completes, with PSLVERR low. The model also prints a warning naming the decoder or the block, and the address. An address past the block's decoded range but inside its address space aliases through the handler's address mask onto an address in the range, so it reads whatever is there.

### Group naming — two build-wide constraints

Both are hard `make db` errors.

1.  **A group reference resolves only within the project owning the referring
    file.** An instance's `addressGroup: top` binds to the `addressBlock:`
    declaring `top` in the same project as the file that instance is declared in.
    Resolution never falls outward to a parent or sibling project, so two
    independently authored projects may each declare a group named `top` and
    still compose. Within one project a group name may be declared by at most one
    router block.

    **Corollary for reusable IP: an IP must declare every group it references.**
    An IP naming a group its own project does not declare has hard-coded a name
    its parent owns, and is no longer independently composable. Fix it by moving
    the declaration into the IP or the reference into the parent — never by
    relying on the parent's declaration being visible.

2.  **`varType:` and `enumPrefix:` must be unique across the whole build.** Two
    address groups may share neither, even in different projects. The reason:
    group *names* are project-qualified, but the generated firmware enum is not.
    Every context's firmware is emitted into one flat namespace (`fw_ns`) and
    firmware headers include each other across project boundaries, so two groups
    sharing a `varType:` either collide as a C++ redefinition or, in separate
    translation units, silently bind the same enumerator to a different address
    ID — a wrong address rather than a build failure. In a reusable IP, qualify
    both by the declaring project (`varType: addr_id_isp_lut_top`,
    `enumPrefix: ADDR_ID_ISP_LUT_TOP_`); the bare `addr_id_top` above is only
    safe in a project nothing else composes.

    A project declaring several groups (§8's `top` and `bridge`) needs distinct
    names *and* distinct `varType:` / `enumPrefix:` values.

Reusable-IP routed leaf (`registerPorts:`), as in `ip_test`'s `ip` block — the
IP authors its own register-bus surface so `<block>Base.h` stays self-contained
across projects that instantiate it:

```yaml
blocks:
  ip:
    desc: "Reusable IP"
    registerPorts:
      regs: { interface: ipReg }   # exactly one row; ipReg is an apb interface
```

A plain top-down leaf authors **no** `registerPorts:`; it infers its register
bus from the nearest authored boundary of each of its instances: the
`registerPorts:` boundary of the innermost router-less passthrough container
that encloses the instance, if one does, else the serving router. Each boundary
offers a port name and an interface: the container's `registerPorts:` key and
interface (so a wrapper IP's own `regs: { interface: ipReg }` reaches the leaf
inside it), or the router's `registerDecoderPort` and register-bus interface.
A block declaring `addressBlock:` must **not** also declare `registerPorts:`
(routers are not leaves).

The inferring block has one register-bus port, and its name depends only on the
block, never on which instance is declared first:

- When every instance's boundary offers the same name, the port takes that
  name.
- When the names differ (for example two wrappers with different
  `registerPorts:` keys, routers with different `registerDecoderPort`s, or a
  leaf served directly by a router and also behind a wrapper), the port takes
  the name of the inferred register-bus interface.

Each instance's own wiring lives on its own rows: the router's dispatch
`connections` row lands on the block's port through its `dstport`, and a
passthrough container's `connectionMaps` row bridges the container's own port
to it. The router side of a dispatch stays named after the router
(`<registerDecoderPort>_<instance>`).

A synthesised `<block>_regs` handler's register-bus port takes the leaf's own
port name: the authored `registerPorts:` key for a reusable IP (so `ip`'s
`regs:` names its handler's port `regs` in every build that instantiates it),
or the per-block name above for a top-down leaf. A router's
`registerDecoderPort` reaches the handler only through the leaf's own port
name, so routers with different `registerDecoderPort`s may serve the same
block.

A name difference is never rejected. An interface difference
is: every instance must infer the same interface. When instances reach
boundaries on different interfaces, the build is rejected, naming each boundary
and the interface and file it supplies:

- Different interfaces between authored boundaries: give the boundaries the
  same `registerPorts:` interface, or use a separate block per boundary; a
  block has one register port type.
- Different interfaces where a source is a router, which cannot declare
  `registerPorts:`: make the `registerPorts:` boundary use that router's
  `upstreamPort` interface, or use a separate block per boundary. With no
  authored boundary among the sources (two routers on different interfaces),
  use a separate block per boundary.

The inferred interface is named unqualified in the file where the block's
register-bus rows are synthesised: the block's own file for a block that gets
a handler, and, on the passthrough path, the file that declares the inner
instance the container feeds. The build is rejected if that file sees a
different interface of the same name, or no interface of that name at all.
Rename one of the interfaces, include the file that declares the interface, or
declare `registerPorts:` on the block.

---

## 6. Walkthrough A — single router (`examples/apbDecode`)

DUT `someRapper` contains the router `uAPBDecode` and two leaves
`uBlockA`/`uBlockB`; the `cpu` master lives one level up in `top`.

```yaml
blocks:
  apbDecode:
    addressBlock: { addressGroup: top, ..., upstreamPort: apbReg, registerDecoderPort: apbReg }
instances:
  uAPBDecode: { container: someRapper, instanceType: apbDecode }
  uBlockA:    { container: someRapper, instanceType: blockA, addressGroup: top }
  uBlockB:    { container: someRapper, instanceType: blockB, addressGroup: top }
connections:
  - {interface: apbReg, src: uCPU, dst: uSomeRapper}                 # upstream feed (master→DUT)
connectionMaps:
  - {interface: apbReg, block: someRapper, direction: dst, instance: uAPBDecode}  # DUT boundary → router
memories:
  - {memory: blockATable0, block: blockA, ..., regAccess: true}      # FW-accessible
registers:
  - {register: roA, regType: ro, block: blockA, ...}
```

Authored: the master→DUT `connection` + the DUT-boundary `connectionMap` into
`uAPBDecode`. Synthesized: `blockA_regs`/`blockB_regs`, their instances and
maps, and `uAPBDecode → uBlockA`/`uBlockB` dispatch. `blockA`/`blockB` own
registers and `regAccess` memories and are served by their sibling `uAPBDecode`.

## 7. Walkthrough B — container owns a config register (`examples/mixed`)

Container `blockB` owns `rwD` (rw) plus `roBsize` and memories, and forwards
them to its children (`uBlockD`/`uBlockF0`/`uBlockF1`) with
`registerConnections`. Those children own no registers, so nothing inside
`blockB` needs a decoder. `blockB` (instance `uBlockB`) is a routed leaf served
by its **sibling** `uAPBDecode` (both in container `mixed`):

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
  - {interface: apbReg, src: uCPU, dst: u_mixed, name: cpu_main}              # upstream feed (master one level up)
connectionMaps:
  - {interface: apbReg, block: mixed, direction: dst, instance: uAPBDecode, name: cpu_main}
```

Correct decision: **keep the register on the container** and forward it with
`registerConnections`. Do **not** invent a leaf block to hold it.

## 8. Walkthrough C — reusable IP + nested router (`examples/ip_test`)

Primary router `uAPBDecode` (group `top`) is in `ip_top` and serves siblings
`uIp0`/`uIp1` (reusable `ip` leaves, `registerPorts:`) and the **container**
`uBridge`. Inside `uBridge` is a *second* router `uBridgeAPBDecode` (group
`bridge`) serving `uBridgeIp0`/`uBridgeIp1`. Two address groups (`top`,
`bridge`); `uBridge` carries `addressGroup: top` so the parent serves it as a
routed leaf, and the nested decoder serves the bridge's own children.

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
  - {interface: apbReg, src: uCPU, dst: u_ip_top, name: cpu_main}            # upstream feed
connectionMaps:
  - {interface: apbReg, block: ip_top, direction: dst, instance: uAPBDecode, name: cpu_main}

# ipBridge.yaml  (nested router + its leaves only — NO apbReg feed authored here)
blocks:
  bridgeApbDecode:
    addressBlock: { addressGroup: bridge, ..., upstreamPort: apbReg, registerDecoderPort: apbReg }
instances:
  uBridgeAPBDecode: { container: ipBridge, instanceType: bridgeApbDecode }
  uBridgeIp0:       { container: ipBridge, instanceType: ip, addressGroup: bridge, variant: variant0 }
  uBridgeIp1:       { container: ipBridge, instanceType: ip, addressGroup: bridge, variant: variant1 }
```

Authored: still only the single upstream feed into `uAPBDecode`. Synthesized for
the nested router: the `uAPBDecode → uBridge` dispatch **and** the `ipBridge`
boundary `connectionMap` into `uBridgeAPBDecode`. Author **nothing** for that
nested feed.

---

## Appendix — Failure-mode → diagnostic table (when the generator errors)

Most decode problems are structural YAML misconfigurations, not RTL/logic bugs.
Match the generator message to the violated rule; fix the declaration, not the
output.

| Symptom / message | Root cause | Fix |
| --- | --- | --- |
| `Leaf instance '…' (block '…') is in container '…' which is not served by any router, directly or through single-consumer containers.` | Routed leaf has no decoder in its container, and no chain of router-less single-consumer containers reaches one either (co-location). Classic: DUT-top owns registers but the only decoder is *inside* it. | Add a router as the leaf's sibling, place it under a chain of containers a router ultimately serves and that each hold no other register consumer, or make the owning block a routed leaf of a parent decoder. Not a manual `connectionMap`. |
| `Container block '…' hosts N instances that need a register bus (…) but no register-decode router (addressBlock:).` | A router-less container has two or more register consumers; it can pass the bus through to only one. | Add an `addressBlock:` router to the container, or move all but one consumer under a routed container. |
| `Container block '…' owns firmware-accessible registers/memories itself and also hosts register-bus consumer(s) (…) but no register-decode router (addressBlock:).` | A router-less container that owns registers/memories is already its own boundary's consumer; it cannot also pass the bus through to another. | Add an `addressBlock:` router to the container, or move its registers/memories onto a leaf the router serves. |
| `Leaf block '…' needs a register handler but no router was found serving any of its instances, directly or through single-consumer containers.` | Same co-location violation seen from handler synthesis. | Place the leaf in a router's container, or in a container that a router serves and that holds no other register consumer. |
| `Block '…' declares no registerPorts: and infers its register-bus interface from the nearest authored boundary of each instance, but its instances infer different interfaces: …` | A leaf or passthrough container that infers its register bus has instances whose nearest authored boundaries (a container's `registerPorts:` boundary, else the serving router) supply different interfaces; the block has one register port type. This includes a leaf served directly by a router and also behind a wrapper. Different port names alone are not rejected: the block's port takes the interface name. | Different interfaces between authored boundaries: give the boundaries the same `registerPorts:` interface, or use a separate block per boundary. Different interfaces where a source is a router: make the `registerPorts:` boundary use the router's `upstreamPort` interface, or use a separate block per boundary (only the latter when every source is a router). |
| `Block '…' declares no registerPorts: and infers register-bus interface '…' declared in file …, but in file …, where its register-bus rows are synthesised, …` | The inferred interface name resolves to a different interface, or to none, in the file where the block's register-bus rows are emitted: the block's own file for a block that gets a handler, or the file declaring the inner instance on the passthrough path. | Rename one of the interfaces, include the file that declares the interface, or declare `registerPorts:` on the named block. |
| `No primary router could be inferred …` | Every router is nested under another; no dispatch-tree root. | Ensure exactly one router is not contained in another router's served scope. |
| `Multiple candidate primary routers: …` | Two+ routers are both un-nested. | Nest all but one under the primary (give the subsystem container an `addressGroup`). |
| `Nested router '…' (block '…') is hosted by block '…', whose instance '…' sits in router-less container '…' … not supported.` | The nested router's container is instantiated inside a router-less container rather than directly in the dispatching router's container; passthrough does not carry the bus to another router. | Move the named instance directly into the dispatching router's container, or add an `addressBlock:` router to the router-less container so it becomes a real nested-router hop. |
| `Router block '…' has multiple instances … Multi-instance routers are not supported …` | A router block is instanced more than once. | Use one instance per router block; add distinct router blocks per scope (see `apbDecode` vs `bridgeApbDecode`). |
| `Block '…' hosts nested router '…' (block '…') and has N instances: '…', '…'.` | A block hosting a nested router is instanced more than once, so its router would be too. Only one instance gets a working dispatch. | Give each instance its own block, hosting its own router block with a distinct `addressBlock.addressGroup`. |
| `Router blocks declare addressBlock: but have no instances in the design: …` | Router block declared but never instanced. | Instance the router in the container it serves. |
| `addressGroup '…' declared on block '…' duplicates a prior addressBlock: declaration on block '…' in …, both in project '…'. Each addressGroup may have at most one router-block declaration within a project.` | Two router blocks *in one project* name the same group. Only the cross-project case is legal — a group name is owned by the project declaring it. | Rename one group (and give it its own `varType:` / `enumPrefix:`), or drop the redundant router. |
| `'…' referenced address group '…', which project '…' does not declare. An addressGroup: reference resolves only within the project owning the referring file …` | A routed instance names a group its own project never declares. Resolution does not fall outward to a parent or sibling project. | Declare the group on a router block in that project, or move the referring row into the project that owns the name. The diagnostic lists the projects that *were* seen declaring the name — a parse-order observation, not a build-wide census. |
| `addressBlock: enum type name varType: '…' is used by two address groups: '…::…' (block '…' in …) and '…::…' (block '…' in …).` (same shape for `enum member prefix enumPrefix:`) | Two groups resolve one generated firmware enum identity. Group names are project-qualified; the emitted enum is not, because firmware shares one flat `fw_ns` namespace across every context. | Give one group a distinct `varType:` / `enumPrefix:`, qualified by its declaring project. |
| `Router '…' (block '…') serves addressGroup '…', but no instance in this build's design tree carries addressGroup: …, so the router has nothing to dispatch to.` | Reported by `make db`. No instance reachable from the active `topInstance` carries the router's group. A referenced child project's standalone-harness instances are in the database but not in this build's tree. | Set the group on a register-bus instance in the router's container, or remove the `addressBlock:` declaration. |
| `Router '…' (block '…') serves addressGroup '…', but no instance carrying addressGroup: … has a register bus for it to dispatch to: ….` | Every instance in the group lacks registers, `regAccess` memories and `registerPorts:`, so the router connects to none of them. | Give one of the listed blocks registers, a `regAccess` memory or a `registerPorts:` entry, or remove the `addressBlock:`. |
| `Instance '…' (block '…') has a register bus, and router '…' (block '…') in container '…' dispatches to it, but it carries no addressGroup:.` (same shape with `passes the register bus to '…'` for a passthrough container) | The router dispatches to every register-bus instance in its container, but allocates a decode slot only to one carrying its group. | Set the router's group on the named instance. |
| `… dispatches to it, but it carries addressGroup: …. Change addressGroup: … to …` | The instance names another router's group while sitting in this router's container. | Change the group to this router's, or move the instance into the container of the router that serves the group it names. |
| `Instance '…' (block '…') hosts nested router '…', and router '…' (block '…') in container '…' dispatches to it, but it carries no addressGroup:.` (or `carries addressGroup: <group>`, naming the group of a router anywhere inside it) | Invariant 1: the container instance hosting a nested router is a slot in the parent router's group. The group of a router inside it belongs to that router's children, not to the container. | Set the parent router's group on the container instance, as `uBridge` in `examples/ip_test/top/yaml/ip_top.yaml` carries `addressGroup: top`. |
| `… Its addressGroup: … resolves in project '…', but the router serves group … of project '…'. Declare instance '…', with addressGroup: …, in a file project '…' owns, or move it into a container that a router of project '…' serves and set addressGroup: to that router's group.` (`Any addressGroup: set on it resolves …` when the instance carries none) | A group name resolves in the project owning the file that declares the instance. The instance is declared in a file of a different project from the router's, so no addressGroup: it carries can name the router's group. | Declare the instance, with the router's group, in a file the router's project owns, or move it into a container that a router of the instance's project serves and set `addressGroup:` to that router's group. |
| `Router block '…' names upstreamPort '…', but no visible interface has that name` / `does not resolve to an addressBus: true interfaceType`. | `addressBlock.upstreamPort` does not name a visible `apb`-shaped (addressBus) interface in scope. | Point `upstreamPort` at the real register-bus interface (e.g. `apbReg`). |
| Decoder RTL is an empty skeleton (ports only). | `make newmodule` ran before `addressBlock:` was present, so the generic template was seeded. | Add `addressBlock:`, re-run `make newmodule`; it selects `apbDecodeModule`. Never hand-write the demux. |
| `<block>_regs` instantiated but its source file is missing. | Stale generated files or an out-of-date `.gen` cache. (`_regs` is synthesized for any block with registers **or** `regAccess` memories — register-only blocks DO get one.) | Remove orphaned generated files and `rm -rf .gen`, then `make db && make gen`. |
| `In …, addressBlock: of block '…' (addressGroup '…') sets maxAddressSpaces …, which is not a power of two. The decoder selects an address space from address bits. Use ….` (same shape for `addressIncrement`) | The RTL decoder masks the address with `addressIncrement × maxAddressSpaces - 1`, and the model decoder shifts it right by the bit length of `addressIncrement`. Both pick the slot from address bits, so a value that is not a power of two aliases or misroutes slots. | Use the suggested next power of two. Raising either value enlarges the decoder footprint, which can trip the nested-decoder window check in the next row. |
| `Nested register decoder '…' (group '…') routes a 0x…-byte footprint …, which exceeds the 0x…-byte window that parent decoder '…' allocates to slot '…'.` | db-time nested-decoder address-containment check. A routed slot whose block contains a nested decoder must fit that decoder's whole footprint (`addressIncrement × maxAddressSpaces`) inside the per-child window the parent allocates. A bare register-block slot is covered instead by the decoded-span check (a router owns no registers, so it needs this separate check); a project with no `addressBlock:` at all has no groups to check (the `ip_test` no-decoder fixture). | Reduce the nested decoder's `addressIncrement` or `maxAddressSpaces`, or widen the parent decoder's `addressIncrement`. |
| `… field regAccess, … is not in the allowed values …` | `regAccess` is not one of `true`, `false`, `rw`, `ro`, `wo`. | Use one of those values. |
| `… memory '…' of block '…' has regAccess: rw, which needs a port that can both read and write, and no port of a portRportW memory does. Change memoryType or regAccess.` | No port of the memory supports the firmware access mode. Only `rw` on `portRportW` hits this. | Use `ro` or `wo`, or a `memoryType` with a read/write port. |
| `… memory '…' of block '…' lists N ports ('…') but has M free. A … memory has K ports and the register handler takes one. …` | `ports:` names more block-side ports than the memory has free: its port count, less one when the register handler takes a port. | List fewer ports, or use a dual-port `memoryType`. If the memory has `regAccess`, removing it frees the handler's port. The message lists the fixes that apply. |
| `Memory '…' of block '…' has regAccess and is on clock '…', but the block's register bus is on '…'. A singlePort memory has one clock, so firmware can reach it only on the register bus clock. …` | A `singlePort` `regAccess` memory's `clock:` is not the register clock. | Set the memory's `clock:` to the register clock, or use a dual-port `memoryType`. |
| `In file …, memory '…' sets a reset field. A memory has no reset state, so remove the field.` | A memory row sets `reset:`. | Remove `reset:`. |
| `Container block '…' declares registerPorts: key '…', but the nested router '…' it hosts names upstreamPort '…'. The registerPorts: key must match the served router's upstreamPort.` | The synthesised boundary map wires the container's `registerPorts:` port straight through to the nested router's upstream port by name, so the two names are one port. | Rename the `registerPorts:` key to the nested router's `upstreamPort` (as `ipBridge.yaml` does with `apbReg`). |
| `In …, ext register '…' of block '…' is N bits wide, wider than the 32-bit register bus. …` (for a parameterizable structure: `… can be up to N bits wide, the width of structure '…' with its parameterizable fields at their maximum, …`) | An `ext` register must reach its owner as one command carrying the whole value, so it must fit one 32-bit bus access. A parameterizable structure is checked at its width with its parameterizable fields at their maximum, fixed fields included. | Narrow the structure to 32 bits or split it into several `ext` registers. For a parameterizable structure, narrow its fixed fields, or lower the `maxBitwidth` of its field types and the `maxValue` of any parameterizable constant that sets their width, so the structure fits in 32 bits. |
| `Interface '…' has interfaceType '…', an address-bus interface, but carries parameterizable structure(s) ….` | A register bus is fixed-width on every side of every router; registers and memories behind it may be parameterized (address allocation scopes them at their maximum), the bus structure may not. | Move the parameter onto the register or memory payload and give the bus a fixed-width structure. |

---

## References
*   Field reference & general wiring: `design-architecture.md`
*   Address policy + firmware headers: `manage-address-space.md`
*   RTL `ext`/`ro`/`rw` register implementation: `rtl-registers.md`
*   Build/scaffold flow: `manage-build.md`
*   Legacy → per-block migration: `address-migration.md`
