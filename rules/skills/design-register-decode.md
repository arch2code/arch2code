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

A **routed leaf** is a block that owns `registers` or `regAccess: true`
memories, **or** authors a `registerPorts:` row. The framework synthesises its
`<block>_regs` handler and a router→leaf dispatch connection.

The single most important fact:

> **A router serves the other instances in its OWN container (its siblings) and
> nested routers. It NEVER decodes its own container block.**

So the decision is **not** "container vs leaf". It is: **is this block served by
a sibling/parent decoder?** A block that owns registers is fine as long as some
*other* decoder (a sibling in its container, or a parent decoder) dispatches to
it.

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

`regAccess: true` (with `local:` absent) is the single switch that makes a
memory firmware-accessible. No custom streaming/"load" interface is ever needed.

---

## 2. Recipe

To make a block's registers/memories firmware-accessible:

1.  **Mark the state.** `regType: rw|ro|ext` registers and/or memories with
    `regAccess: true` (and no `local:`). Never substitute a custom interface.
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
    **and** the child-container boundary `connectionMap` into the nested router.

So for nested routers you author **nothing** for the register bus below the
primary feed. Over-authoring the nested boundary map is wrong.

`registerConnections:` is the one thing you still author when a block owns a
register that should be *consumed by a child instance* (forwarding a
container's own register down to a sub-block), as `examples/mixed`'s `blockB`
does.

---

## 4. The four invariants (keep these)

1.  **Co-location.** A routed leaf and its serving decoder share one container.
    The leaf instance's `addressGroup:` must name the serving router's
    `addressBlock.addressGroup`.
2.  **Decoder-as-generated-block.** The decoder is a first-class block whose RTL
    is generated from `apbDecodeModule` (auto-selected by `make newmodule`
    because the block carries `addressBlock:`). Never hand-write it.
3.  **Auto-wiring below the decoder.** Once routers and routed leaves are
    declared and co-located, the entire register-bus fan-out below the primary
    router is synthesized. A need to hand-plumb the bus below the primary feed is
    a symptom of a broken invariant, not a fix.
4.  **Single `regAccess` switch.** `regAccess: true` (with `local:` absent) is
    the only switch to make a memory firmware-accessible.

> There is **no** "leaf-ownership invariant." Container blocks may own
> registers/memories (see `examples/mixed`'s `blockB`). The real constraint is
> the decoder-position rule
> in §1: a block must be served by a sibling/parent decoder, and is never
> decoded by a decoder it contains.

---

## 5. `addressBlock:` / `registerPorts:` field reference

Router block (`addressBlock:`), as in `apbDecode.yaml` / `mixed.yaml`:

```yaml
blocks:
  apbDecode:
    desc: "APB register decoder"
    addressBlock:
      addressGroup: top            # leaves name this in their addressGroup:
      addressIncrement: 0x01000000 # byte spacing between address spaces
      maxAddressSpaces: 16
      varType: addr_id_top         # generated address-ID enum type
      enumPrefix: ADDR_ID_TOP_
      upstreamPort: apbReg         # the addressBus interface feeding this router
      registerDecoderPort: apbReg  # canonical downstream register-bus port
```

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
bus from the serving router. A block declaring `addressBlock:` must **not** also
declare `registerPorts:` (routers are not leaves).

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
| `Leaf instance '…' (block '…') is in container '…' which is not served by any router.` | Routed leaf has no decoder in its container (co-location). Classic: DUT-top owns registers but the only decoder is *inside* it. | Add a router as the leaf's sibling, or make the owning block a routed leaf of a parent decoder. Not a manual `connectionMap`. |
| `Leaf block '…' needs a register handler but no router was found serving any of its instances.` | Same co-location violation seen from handler synthesis. | Place the leaf in a router's container. |
| `No primary router could be inferred …` | Every router is nested under another; no dispatch-tree root. | Ensure exactly one router is not contained in another router's served scope. |
| `Multiple candidate primary routers: …` | Two+ routers are both un-nested. | Nest all but one under the primary (give the subsystem container an `addressGroup`). |
| `Router block '…' has multiple instances … Multi-instance routers are not supported …` | A router block is instanced more than once. | Use one instance per router block; add distinct router blocks per scope (see `apbDecode` vs `bridgeApbDecode`). |
| `Router blocks declare addressBlock: but have no instances in the design: …` | Router block declared but never instanced. | Instance the router in the container it serves. |
| `addressGroup '…' declared on block '…' duplicates a prior addressBlock: declaration on block '…' in …, both in project '…'. Each addressGroup may have at most one router-block declaration within a project.` | Two router blocks *in one project* name the same group. Only the cross-project case is legal — a group name is owned by the project declaring it. | Rename one group (and give it its own `varType:` / `enumPrefix:`), or drop the redundant router. |
| `'…' referenced address group '…', which project '…' does not declare. An addressGroup: reference resolves only within the project owning the referring file …` | A routed instance names a group its own project never declares. Resolution does not fall outward to a parent or sibling project. | Declare the group on a router block in that project, or move the referring row into the project that owns the name. The diagnostic lists the projects that *were* seen declaring the name — a parse-order observation, not a build-wide census. |
| `addressBlock: enum type name varType: '…' is used by two address groups: '…::…' (block '…' in …) and '…::…' (block '…' in …).` (same shape for `enum member prefix enumPrefix:`) | Two groups resolve one generated firmware enum identity. Group names are project-qualified; the emitted enum is not, because firmware shares one flat `fw_ns` namespace across every context. | Give one group a distinct `varType:` / `enumPrefix:`, qualified by its declaring project. |
| `Router block '…' declares address group '…::…' but no instance in this build's design tree is routed to it, so the decoder has no channels to dispatch.` | At generation time: the router's group resolved, but no instance reachable from the active `topInstance` carries that `addressGroup:`. A referenced child project's standalone-harness instances are in the database but are not part of this build's tree. | Route at least one reachable instance to the group, or remove the `addressBlock:` declaration. |
| `Router block '…' names upstreamPort '…', but no visible interface has that name` / `does not resolve to an addressBus: true interfaceType`. | `addressBlock.upstreamPort` does not name a visible `apb`-shaped (addressBus) interface in scope. | Point `upstreamPort` at the real register-bus interface (e.g. `apbReg`). |
| Decoder RTL is an empty skeleton (ports only). | `make newmodule` ran before `addressBlock:` was present, so the generic template was seeded. | Add `addressBlock:`, re-run `make newmodule`; it selects `apbDecodeModule`. Never hand-write the demux. |
| `<block>_regs` instantiated but its source file is missing. | Stale generated files or an out-of-date `.gen` cache. (`_regs` is synthesized for any block with registers **or** `regAccess` memories — register-only blocks DO get one.) | Remove orphaned generated files and `rm -rf .gen`, then `make db && make gen`. |
| `Nested register decoder '…' (group '…') routes a 0x…-byte footprint …, which exceeds the 0x…-byte window that parent decoder '…' allocates to slot '…'.` | db-time nested-decoder address-containment check. A routed slot whose block contains a nested decoder must fit that decoder's whole footprint (`addressIncrement × maxAddressSpaces`) inside the per-child window the parent allocates. A bare register-block slot is covered instead by the decoded-span check (a router owns no registers, so it needs this separate check); a project with no `addressBlock:` at all has no groups to check (the `ip_test` no-decoder fixture). | Reduce the nested decoder's `addressIncrement` or `maxAddressSpaces`, or widen the parent decoder's `addressIncrement`. |

---

## References
*   Field reference & general wiring: `design-architecture.md`
*   Address policy + firmware headers: `manage-address-space.md`
*   RTL `ext`/`ro`/`rw` register implementation: `rtl-registers.md`
*   Build/scaffold flow: `manage-build.md`
*   Legacy → per-block migration: `address-migration.md`
