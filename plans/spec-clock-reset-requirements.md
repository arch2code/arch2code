# Requirement specification: clocks and resets

- **Status:** Normative.
- **Scope:** functional requirements and YAML specification. Implementation
  is recorded separately in
  [`plan-clock-container-model.md`](./plan-clock-container-model.md).
- **Source:** issue #129.
- **Audience:** designers authoring arch2code YAML, and IP integrators
  composing projects.

---

## 1. Purpose

A clock has one meaning in this specification: a clock port of a block's
module. There is no clock net that exists apart from the modules it passes
through.

- A **block** declares the clocks its implementation uses, by the names its
  RTL module and its model use: `clk`, `baudClk`, `clkPix`. A reusable block
  is written against its own names and knows nothing outside itself.
- An **instance** binds each clock of the instantiated block to a clock of the
  **container** it is placed in: one of the container's own declared clocks, or
  a clock produced by a sibling instance inside that container. This is how an
  RTL hierarchy connects clocks, and it is the shape used for parameters: a
  block declares them, a variant binds them at instantiation.
- The **project file** describes the **testbench**: the clocks and resets the
  simulation environment generates, with their periods and release timing. The
  top block is bound to them by the same instance rules. When a parent project
  instantiates this project's top block, the parent's binding replaces the
  testbench, and the child's project file plays no part in that binding.

For a clock the block consumes, the binding is automatic when the names agree.
For a clock the block produces, the binding is always written.

Three capabilities follow:

- a block names its own clocks, more than one where its implementation needs
  them, independently of any project;
- a block may **produce** a clock (a divider, a PLL wrapper, a clock mux) or a
  reset (a reset synchroniser), and that output is bound at instantiation to a
  net of the container, which sibling instances then consume;
- a composed child project's top block is bound to the assembling container's
  clocks, so one IP can be re-clocked, and instantiated twice on two clocks.

Resets follow the same structure throughout, with one addition: each reset
belongs to a clock, except an asynchronous reset input, which a synchroniser or
PLL wrapper takes in from no domain of its own.

## 2. Terminology

| Term | Meaning |
| :--- | :--- |
| Block clock | A clock named in a block's `clocks:` section. A clock port of the block's module. Has a direction, `input` or `output`. |
| Block reset | A reset named in a block's `resets:` section, associated with one block clock, or declared `async: true` and associated with none. |
| Block default clock | The `input` block clock marked `default: true`, or the block's only `input` clock when it has exactly one. The clock a block's ports and resets use when they name none. |
| Selected reset | For one clock of a block, the reset that generated logic clocked by it uses. Candidates are the block's declared resets on that clock and the local reset nets belonging to it inside the block, excluding a net consumed only by asynchronous reset inputs. The declared candidate marked `default: true` is selected, else the sole candidate (§4.2). A clock may have none. For a testbench clock: its reset marked `default: true`, else its sole reset. |
| Container | The block an instance is placed in, named by the instance's `container:`. A container is a block like any other; its clocks are its block clocks. |
| Container clock | A clock available for binding inside a container: one of the container's own block clocks, `input` or `output`, or a local net. Container resets likewise. |
| Local net | A clock or reset driven inside a container by a child instance's `output` binding, under the name that binding gives it, and not declared by the container. Visible only inside that container. |
| Clock map | The `clocks:` mapping on an instance, binding each block clock of the instantiated block to a container clock. `resets:` on an instance is the reset map. |
| Automatic binding | The binding taken for an `input` block clock or reset that the instance's map omits: the container clock or reset of the same name. Outputs are never bound automatically. |
| Default fallback | The binding taken for a block clock named `clk`, declared or implicit, when the map omits it and the container has no clock of that name: the container's default clock. Likewise a block reset named `rst_n`: the selected reset of the container clock that the reset's own block clock is bound to. |
| Driver | Within one container, the single source of a container clock or reset: a child instance's output, the container's own input port, or the container's own implementation behind a declared output. |
| Supplier | An instance whose `output` binding drives a container clock or reset. The block's own implementation produces it, or the block exports a supplier inside it. |
| Export | A container's `output` block clock or reset that a child instance's output drives. The declaration is what makes the inner net visible to the container's parent. |
| Testbench clock, testbench reset | A clock or reset declared in the project file's `clocks:` or `resets:` section. Generated by the simulation environment and bound to the top block. |
| Primary clock, primary reset | A block clock that resolves (below) to a testbench clock or reset. |
| Supplied clock, supplied reset | A block clock that resolves to a supplier's output. |
| Resolved clock | The net a block clock reaches by following bindings upward through `input` ports until a net whose driver is a child output; where that output is an export, following the exporting container's own binding upward again; stopping at a testbench clock, a local net, a top-block `output`, or `~`. Two block clocks with one resolved net are one clock. Used for simulation attributes and for the supply graph; never authored. |
| Asynchronous reset input | A block reset declared `async: true`. It is sampled by no block clock, so it belongs to no domain of the block; a synchroniser's or PLL wrapper's input. |
| Domain | Within a container, a container clock together with the container resets that belong to it. |
| Top-down port | A port defined by the connection that reaches it, the ordinary port of top-down design. Its domain is authored on the connection's `clock:` (§4.3). |
| Declared port | A port listed in a block's `ports:` or `registerPorts:`, used for reusable IP and parameterised blocks. Its domain is authored on the declaration (§4.3). |
| Child project | A project named in an assembling project's `projectFiles:`. |

The word **model** in this document means the design model, that is, the
block implementation in either language. The SystemC simulation kernel's own
notion of time is not a clock in this specification.

Two scope statements bound the vocabulary:

- Every pair of distinct container clocks is treated as mutually asynchronous.
  A divided or gated clock is in fact synchronous to its parent, but nothing
  here records that, so a connection between the two is a crossing (R16) like
  any other. A relationship declaration is Q4.
- A clock carried as a signal inside an interface, such as the serial clock of
  an SPI interface or a source-synchronous pixel clock in a video interface, is
  data to this specification, not a clock, unless the block also declares it as
  an `output` block clock.

## 3. Structure in one page

```
project file: testbench       design yaml: blocks                   design yaml: instances
-----------------------       -------------------                   ----------------------
clocks:                       blocks:                               instances:
  clkSys:    (default)          soc:                                  uSoc:
resets:                           clocks:                               instanceType: soc
  rstSys_n:  (on clkSys)            clkSys: { }                       uUart:
                                  resets:                               container: soc
                                    rstSys_n: { clock: clkSys }         instanceType: uart
                                uart:                                   clocks:
                                  clocks:                                 clk:     clkSys
                                    clk:     { }                          baudClk: ~
                                    baudClk: { direction: output }      resets:
                                  resets:                                 rst_n:   rstSys_n
                                    rst_n:   { clock: clk }
                                  ports:
                                    tx: { ..., clock: baudClk }

generated by the testbench    module ports                          binding: child clock -> container clock
```

Block clocks are module ports. An instance binds the child's ports to the
container's clocks, here `clkSys` declared by `soc`, or to a net a sibling
drives (§4.4), or to `~` for an output nothing consumes. The testbench binds
`soc`'s ports by the same rules. A block's ports each name the block clock
they are timed by, so the domain of every connection is known without stating
it on the connection.

## 4. YAML specification

### 4.1 Project file: the testbench's `clocks:` and `resets:`

```yaml
clocks:
    clkSys:
        desc: "system clock"
        default: true
        period: 10
        timeUnit: ns
    clkRef:
        desc: "PLL reference"
        period: 40
        timeUnit: ns

resets:
    rstSys_n:
        desc: "system reset"
        default: true
        clock: clkSys
    rstRef_n:
        desc: "reference-domain reset"
        clock: clkRef
        releaseCycles: 4
```

| Field | Section | Meaning |
| :--- | :--- | :--- |
| key | both | The testbench net name. It is bound to an `input` clock or reset of the top block by name match or default fallback (§4.8). |
| `desc` | both | Required description. |
| `default` | both | Exactly one clock and exactly one reset carries `true`; implied when the section has exactly one entry. Used for the default fallback of a top block that declares nothing. |
| `period`, `timeUnit` | clocks | The period at which the testbench generates the clock. Optional, default 1 ns. |
| `clock` | resets | The testbench clock this reset belongs to. Unstated means the default clock. |
| `releaseCycles` | resets | Cycles of `clock` after which the testbench releases the reset. Default 3. |

Rules:

- A project file that omits `clocks:` has one testbench clock, `clk`, default,
  at the default `period` of 1 ns. One that omits `resets:` has one testbench
  reset, `rst_n`, default, on the default clock. A plain project therefore
  declares nothing.
- Exactly one clock and one reset is the default, and the default reset
  belongs to the default clock (V23). The selected reset of a testbench clock
  is its reset marked `default: true`, else its sole reset; a clock with
  several unmarked resets has none.
- Every testbench clock and reset is bound to an `input` of the top block (V10).
  A declared entry that nothing consumes is an error, since the testbench would
  generate a clock the design does not have. A project file that declares no
  `topInstance:` is exempt from V10: it has no top block to bind, and its
  `clocks:`/`resets:` serve only as definitions, such as the standalone
  `period` and `releaseCycles` a block with `hasVl` reads (§4.8, V21).
  The testbench is the top block's container for reset membership (V6).
- Nothing here names a clock inside the design. A clock produced inside the
  design has no entry; a clock the top block exports as an `output` has no
  entry either, the testbench observes it (§4.8).
- When this project is a child of another, this section is not used to bind
  the top block; the assembling project's instance map binds it instead
  (§4.7).

### 4.2 Block: `clocks:` and `resets:`

A block declares the clocks and resets its implementation uses. These are the
names inside the module. They reference nothing outside the block.

```yaml
blocks:
    uart:
        desc: "UART with a generated baud clock"
        clocks:
            clk:     { desc: "register and datapath clock" }   # sole input, so the default
            baudClk: { desc: "generated baud clock", direction: output }
        resets:
            rst_n:   { desc: "datapath reset", clock: clk }   # baudClk has no reset (§4.2)
        ports:
            regs: { interface: apbIf,     direction: dst }
            tx:   { interface: uartTxIf,  direction: src, clock: baudClk }
```

| Field | Section | Meaning |
| :--- | :--- | :--- |
| key | both | The module port name. |
| `desc` | both | Optional description. |
| `direction` | both | `input` (default) or `output`. An `output` clock or reset is produced by the block: a divider or PLL wrapper for a clock, a reset synchroniser for a reset. |
| `default` | both | On a clock, `true` marks the block default clock. Required on exactly one `input` clock when the block declares more than one; forbidden on an `output`; implied when the block has exactly one `input` clock. On a reset, `true` marks the **selected reset** of the clock it belongs to. Required on exactly one of several declared resets on the block default clock, and on one of several candidates on any clock hosting generated logic, unless the consuming entry names `reset:` itself; implied when the clock has exactly one candidate, declared or local net. |
| `clock` | resets | The block clock this reset belongs to. Unstated means the block default clock. An `input` reset names an `input` clock. An `output` reset names either: a synchroniser's output reset belongs to its input clock, a PLL wrapper's output reset to its output clock. Not permitted together with `async`. |
| `async` | resets | `true` marks an asynchronous reset input: one the block does not sample in any of its clocks, as a synchroniser or PLL wrapper takes in. It belongs to no domain of the block, so the clock-membership part of V1 and the rule V6 do not apply to it, and it may be bound to any container reset. Only an `input` reset may be `async`. |
| `period`, `timeUnit` | clocks | Optional, `input` only (V18). The period a **standalone** simulation of this block uses for the clock when the design does not determine one (§4.8). Never used in an assembled design. |

Rules:

- **The declaration is complete.** A block's clocks are exactly the entries of
  its `clocks:`, and its resets exactly the entries of its `resets:`. Nothing
  is inferred from the block's children, connections or ports. This holds for a
  container as for a leaf: a container whose children use two clocks declares
  two clocks.
- A block that declares no `clocks:` has exactly one block clock, `clk`,
  `input`. A block that declares no `resets:` and has a default clock has
  exactly one block reset, `rst_n`, on that clock. A block with no default
  clock and no `resets:` has no resets. An empty `resets: {}` declares that
  the block has no reset; the implicit `rst_n` is for a block that says
  nothing.
- The **block default clock** is the `input` clock marked `default: true`. A
  block with exactly one `input` clock need not mark it; a block with several
  marks exactly one (V18). Declaration order carries no meaning, so reordering
  a block's clocks never changes a domain silently. A block whose declared
  clocks are all `output` has **no** default clock: every port and every reset
  of such a block names its clock explicitly (V15). This is the shape of a pure
  clock source such as an oscillator or PLL wrapper.
- The **selected reset** of a block clock is chosen among the candidates on
  that clock: the block's declared resets belonging to it and, inside a
  container, the local reset nets belonging to it (§4.4), except a local net
  consumed only by asynchronous reset inputs, which is not released
  synchronously to any clock (§4.9) and is never a candidate. The declared
  candidate marked `default: true` is selected, else the sole candidate. A
  block with several declared resets on its default clock marks one (V18), so
  that the reset its implementation refers to as `rst_n` is always defined.
  Generated logic clocked by a block clock uses its selected reset: a register
  handler or decode router on the clock of its bus port, the memory side of the
  R20 bridge on the memory's clock. A clock hosting generated logic with zero
  or several unmarked candidates is an error (V19); declaration order never
  decides. Where the implementation refers to the block default clock and its
  reset by the conventional names `clk` and `rst_n` without declaring them,
  those names denote the block default clock and its selected reset.
- A block clock need have **no reset**. Logic in such a domain is reset by the
  designer's means or not at all; the `baudClk` logic in the example above is
  divided from `clk` and left without one. Generated logic is never placed in
  a domain without a selected reset (V19).
- Within a block, the names of clocks, resets, interface ports and memories,
  together with the reserved names `clk` and `rst_n` when the block does not
  declare them, are pairwise distinct (V7). They share the module's namespace,
  and the reserved names are emitted as aliases of the default clock and its
  selected reset whenever the block does not declare them.
- **Short form.** `clocks: [clkSlow]` and `resets: [rst_n]` are accepted and
  mean the mapping form with every field defaulted. The clock short form admits
  **one** entry: a list of several input clocks has nowhere to mark the default
  and taking the first would reintroduce order dependence, so a multi-clock
  block uses the mapping form (V18). The reset short form may list several,
  each on the block default clock.

### 4.3 Where a port's domain is authored

Each port of a block is timed by one block clock. A top-down port is defined
by the connection that reaches it, and the connection's `clock:` is where its
domain is authored. `ports:` and `registerPorts:` declarations are the
mechanism for reusable IP and parameterised blocks; there a port's `clock:`
is authored on the declaration. Where a port is both declared and reached by
a connection carrying `clock:`, the two must agree (R7, V14).

**On a declared port, for reusable IP and parameterised blocks.** A block
that lists the port in `ports:` or `registerPorts:` names the block clock
there:

```yaml
        ports:
            regs: { interface: apbIf,    direction: dst }                 # block default clock
            tx:   { interface: uartTxIf, direction: src, clock: baudClk } # explicit
```

| Field | Meaning |
| :--- | :--- |
| `clock` | The block clock this port is timed by. Unstated means the block default clock, for a top-down port as for a declared one. May name an `input` or `output` block clock. |

**On the connection, for a top-down port.** A block need not declare
`ports:`; a top-down port is defined by the connections that reach it. For
such a port the `clock:` field on `connections:` names a **container**
clock of the container the connection sits in:

```yaml
connections:
    - { interface: dataIf, src: uSlowTick, srcport: out, dst: uSlowSink, dstport: in, clock: clkSlow }
```

A connection `clock:` states the domain of **both** ends of the wire. A
connection carrying it therefore cannot be a crossing; a crossing is authored
by declaring the two ports' clocks and leaving the connection field off.

**Only `connections:` carries the field.** `connectionMaps:`,
`memoryConnections:` and `registerConnections:` do not, because each of them
has a domain that is already determined:

- A **`connectionMaps:`** row routes a container's boundary port to an inner
  instance's port. The boundary port's domain is derived **from the inside
  out**: it is the inner port's derived container clock, which must be a block
  clock of the container, declared or implicit (V16). A boundary port timed by
  a local net the container does not export would carry data in a domain the
  parent cannot drive or name, so such a row is an error directing the author
  to declare the net as an `output` clock. The port's domain is then visible to
  the parent through the container's own binding, and an outer connection
  reaching the port derives to the same clock at that end. Maps chain upward
  through any number of levels by the same rule.
- A **`registerConnections:`** row reaches a register of another block. A
  register lives in the domain of the register bus that reaches its owning
  block's register port; the whole decode tree from the bus feed to the
  register handler is one domain (V8). The accessing side derives its own domain,
  and where the two differ the register value crosses domains on the wires into
  the block's logic, which is the designer's to handle, as any crossing is.
- A **`memoryConnections:`** row reaches a memory of another block. The memory's
  domain is its own declaration (below), and the accessing side must derive to
  the same container clock (V8). The generator wires the accessor's memory port
  straight into the primitive, so there is no place for a synchroniser; an
  accessor in another domain reaches the memory through a bridge block of the
  designer's own, which is then the accessor.

**Derivation of a port's domain**, per end of a connection. The two authored
sources are not a precedence order; both are read, and they must agree.

1. The port is declared with `clock:`: that block clock, mapped through the
   instance, is the port's container clock.
2. The connection row carries `clock:`: that container clock is the port's
   container clock. For a top-down port, its block clock is the one `input`
   entry of the instance's map bound to that container clock (V13).
3. Neither is written: the block default clock, mapped through the
   instance, except a synthesised register-bus port, which R25 governs.

Rule 2 applies to a top-down port. A declared port that names no
`clock:` is on the block default clock by rule 3, and a connection `clock:`
that maps to another clock is a V14 error.

**A declared port clock that does not match the connection clock is an
error** (V14). The tool never resolves the disagreement by preferring one
source; the author states the domain in two places and they conflict, so the
build stops. Rule 2 is what makes a one-clock-per-block project authorable
without declaring every port; the connection is the authoring site for a
top-down port's domain.

Both ends of a connection sit in one container, so the comparison that decides
a crossing is between two container clocks of that container. No identity
beyond the container is needed.

**Registers.** A register's domain is that of the bus feeding its owning
block's register port, derived like any other port: the `registerPorts:`
entry may name a block clock, else the feeding connection may. A top-down
leaf authors no `registerPorts:`, so its feed is synthesised and carries no
`clock:`. Its register-bus port instead takes the leaf's declared clock
port that the instance's `clocks:` map binds to the bus clock.

For a synthesised register-bus feed, the derivation of that bus clock runs
outward from the router, one container at a time. At each level, the block
whose synthesised register-bus port is fed selects its clock and reset port
by the same map match against the far end of the feed in its own
container, and the derivation terminates at the router's owner, whose
router domain is derived by the "Routers" paragraph below. Concretely, the
far end a leaf's map matches against is the router's `addressBlock` port
when the router sits in the leaf's immediate parent, or the parent's own
synthesised register-bus port otherwise, itself a block clock of the
parent by this same outward derivation. This runs the opposite direction
from a `connectionMaps:` row, whose boundary port derives its domain
inside out from the inner port (V16); V16 governs authored rows, not a
synthesised register-bus feed.

The reset follows independently: the register block's reset is the leaf's
declared reset port that the instance's `resets:` map binds to the bus's
reset, the selected reset of that far end's clock. Two leaf clock ports
bound to the same container clock are one net, and two leaf reset ports
bound to the same container reset likewise; the tool takes the first in
declaration order, and binding several block clocks or resets to one
container net this way is an ordinary deployment, such as an IP exposing
both a register-bus clock and a core clock that a design binds to one
clock. Because the leaf module is generated once, every instance of the
block must resolve to the same clock port and the same reset port, else an
error naming the instances (V26). A `registerPorts:` entry naming `clock:`
or `reset:` stays authoritative for a reusable IP leaf, and the bound bus
clock and reset must agree with it (V14 for the clock; the reset the same
way).

Every register and the handler that implements it sit in that one domain,
reset by the selected reset of that block clock; a `registerPorts:` entry may
name `reset:` to choose among several, mirroring memories (V19). The selected
ports are a block-level result computed from the design's instances, so a
leaf's standalone testbench and tandem wrapper drive the register-bus BFM on
the same selected clock and reset port; a leaf with no serving router has no
inferred register port, so there is nothing to select. Register values read
or written by logic in another domain cross on the register wires, and the
designer owns that crossing.

**Routers.** A decode router's domain is that of its `addressBlock`
upstream port, a port of the owning block derived as any port: the
`addressBlock:` entry may name `clock:` and `reset:` with the meaning they have
on `registerPorts:`; else the feed connection may name `clock:`; else the block
default applies. A nested router's feed is synthesised and carries no `clock:`,
so a nested router on a non-default clock names it on `addressBlock:`. A
router's clock is a block clock of its owner, never a local net of that owner,
so a register tree never enters a domain the owner produces and does not
export: registers of children clocked by such a net are reached by placing the
clock's supplier in a container above the one that routes to them, or by
exporting the clock and feeding the tree from that domain.

**Memories.** A memory belongs to one block and is clocked by that block: its
declaration carries `clock:` naming a block clock of the owning block, `input`
or `output` as a port's may, default the block default clock. The field matters
only for a multi-clock block choosing which of its clocks the store sits on. A
memory served by a register handler in another domain (R20) also needs a reset
in its own domain for the bridge's memory side: `reset:` names a block reset
belonging to the memory's clock, and defaults to the selected reset of that
clock. The memory array itself is never reset, so `reset:` is consulted only
when the bridge exists (V19).

```yaml
memories:
    lineBuf: { block: scaler, structure: pixelSt, addressStruct: lineAddrT, desc: "line store",
               clock: clkPixel, reset: rstPixel_n }
```

A memory has three access paths, and the specification treats them differently
because their rates and their wiring owners differ:

| Path | Domain rule |
| :--- | :--- |
| The owning block's own logic | Same domain as the memory by construction; this is the datapath path and sets the memory's clock. |
| A hardware accessor via `memoryConnections:` | Must be in the memory's domain (V8). A raw crossing on a memory interface at datapath rate is a functional defect, and the generated wiring has no place for a synchroniser. |
| Firmware via the register handler (`regAccess: true`) | May differ from the memory's domain. The **register handler provides the crossing** (R20): it is the one place the tool owns both sides, the bus clock from its feed and the memory clock from the declaration, and the access is a single request with a single response, which a handshake bridge carries safely. The bridge costs a few bus cycles per access. |

This makes the register handler the one place the tool generates
synchronisation logic. Everywhere else a crossing is the designer's, because
only here does the tool own both sides and the protocol. A memory is never
moved onto the bus clock to serve firmware access; the datapath sets the domain,
and the handler adapts. A memory whose own ports run on two clocks is not
provided; a design needing one implements it outside the generator, and any
crossing at its ports is the designer's (R17). The single-clock dual-port RTL
primitive (`memory_dp.sv`) returns old data on a same-address cross-port read
during a write. The SystemC memory model gives no ordering guarantee for a
same-time read and write on two ports, so a design must not rely on either
ordering across ports.

### 4.4 Instance: `clocks:` and `resets:` maps

An instance binds each block clock of the instantiated block to a clock of its
container, and each block reset to a reset of its container.

```yaml
blocks:
    soc:
        clocks:
            clkSys:        { default: true }
            clkPeripheral: { }
        resets:
            rstSys_n:        { clock: clkSys }
            rstPeripheral_n: { clock: clkPeripheral }

instances:
    uUartA: { container: soc, instanceType: uart,
              clocks: { clk: clkPeripheral, baudClk: clkBaudA },
              resets: { rst_n: rstPeripheral_n } }
    uUartB: { container: soc, instanceType: uart,
              clocks: { clk: clkSys, baudClk: ~ },
              resets: { rst_n: rstSys_n } }
    uBaudMon: { container: soc, instanceType: edgeMon,   # edgeMon: clocks {clk}, resets {}
                clocks: { clk: clkBaudA } }                 # consumes the local net
    uDma:   { container: soc, instanceType: dma }
```

| Field | Meaning |
| :--- | :--- |
| `clocks` | Mapping `<block clock>: <container clock>`. Keys are block clocks of `instanceType`. Values are container clocks of `container`: its declared clocks, or local nets; or `~` (null) to leave an `output` unconnected. Optional; an `input` entry is optional, an `output` entry is required. |
| `resets` | Mapping `<block reset>: <container reset>`. Same shape and rules. |

Rules:

- **Automatic binding, inputs only.** An `input` block clock the map omits is
  bound to the container clock of the same name. An `input` block reset the map
  omits is bound to the container reset of the same name.
- **Default fallback for `clk` and `rst_n`.** A block clock named `clk`,
  declared or implicit, that the map omits, in a container with no clock of
  that name, is bound to the container's **default** clock. A block reset named
  `rst_n` that the map omits, in a container with no reset of that name, is
  bound to the selected reset of the container clock that its own block clock,
  the block default clock or the clock its declaration names, was bound to,
  whether by map, name match or fallback. `uDma` above needs no map: `dma`
  declares nothing, `soc` has no `clk`, so `uDma` runs on `clkSys` and
  `rstSys_n`. This is what keeps a container that names its clocks from having
  to annotate every plain block inside it. It applies to those two names only.
  An asynchronous reset input gets no such fallback: it is bound by an
  explicit map entry or by name match only, and if neither applies, in a
  container with no reset of that name, it is an error (V4).
- **An undeclared container has only `clk` and `rst_n`.** A child inside it
  binds to those two names and to nothing else, by name match or fallback. A
  child that declares `clkPix` must write `clocks: { clkPix: clk }`; a child
  binding a name the container does not have is an error whose diagnostic
  lists the container's clocks (V4). Nothing is inferred from the children.
- **Outputs are always explicit.** Every `output` entry of the block appears in
  the map, bound to a container clock or reset, or to `~` to state that it is
  unused. A name match never creates a supplier, and an omitted output is an
  error rather than a silently dropped net (V3). The top block is the
  exception: it has no map, and the testbench observes its outputs (§4.8).
- **An output binding may create a local net.** `baudClk: clkBaudA` above
  names no clock of `soc`; it creates the local net `clkBaudA`, driven by
  `uUartA`, which sibling instances may consume by binding to that name. A
  local net's name may not collide with a container clock or reset (V7), and
  at least one child `input` binding consumes it (V22), so a misspelt export
  binding is an error rather than an undriven port. An output bound to a
  container's declared `output` clock drives that port instead: that is the
  export (§4.5). An output may not be bound to a container's `input` clock,
  which already has a driver (V5). A clock output binds a clock net and a reset
  output a reset net (V4).
- An `input` block clock that neither the map nor automatic binding nor the
  fallback resolves is an error (V3).
- Two `input` block clocks of one instance may be bound to the same container
  clock; the block then runs both of its clock ports from one net. An `output`
  may not share its net with any other entry of the same instance, input or
  output (V5).
- One instance may have both maps, either, or neither.
- The `count:` field on an instance applies the same map to every element, so
  all elements share one set of clocks and resets. Per-element clocks, such as
  one clock per lane, require unrolled instances. An instance with `count`
  greater than one may bind no `output` entry to a net, since every element
  would drive it (V12); its outputs are `~`.

### 4.5 Output clocks, output resets, and suppliers

A block clock or reset declared `direction: output` is produced inside the
block. Its map entry names the container clock or reset the block **drives**.

```yaml
blocks:
    soc:
        clocks:
            clkRef: { }                       # sole input, so the default; the testbench drives it
        resets:
            rstRef_n: { clock: clkRef }
    clkGen:
        desc: "PLL wrapper: one reference in, two clocks out"
        clocks:
            refClk:  { }
            clkCore: { direction: output }
            clkIo:   { direction: output }
        resets:
            rst_n:        { clock: refClk }
            rstCoreRaw_n: { clock: clkCore, direction: output,
                            desc: "asserted while rst_n is asserted or the PLL is unlocked" }
    rstSync:
        desc: "reset synchroniser: asynchronous assert, synchronous release"
        clocks:
            clk:      { }
        resets:
            rstIn_n:  { async: true }
            rstOut_n: { clock: clk, direction: output }

instances:
    uClkGen:  { container: soc, instanceType: clkGen,
                clocks: { refClk: clkRef, clkCore: clkSys, clkIo: ~ },
                resets: { rst_n: rstRef_n, rstCoreRaw_n: rstSysRaw_n } }
    uRstSys:  { container: soc, instanceType: rstSync,
                clocks: { clk: clkSys },
                resets: { rstIn_n: rstSysRaw_n, rstOut_n: rstSys_n } }
    uCore:    { container: soc, instanceType: core,
                clocks: { clk: clkSys }, resets: { rst_n: rstSys_n } }
```

`clkSys`, `rstSysRaw_n` and `rstSys_n` are local nets of `soc`: `soc`
declares none of them, so they exist only inside it; `clkIo` is unused here
and bound to `~`. `rstSysRaw_n` is consumed only by a synchroniser, so it is
not a candidate for the selected reset of `clkSys`; it carries the PLL's lock
status into the reset tree, and `rstSys_n`, the sole candidate, is what
`clkSys` logic and any generated logic on `clkSys` samples.

Rules:

- The instance whose output is bound to a container clock or reset is the
  **supplier** of that net within the container. It is the net's one driver
  (V5). Whether the block's own implementation produces the clock or the block
  exports a supplier inside it is the block's business and changes nothing at
  this level.
- **A local net exists by being driven.** Its name is the one the output
  binding gives it. Consumers bind to the name; a name no output drives and no
  declaration provides is an error (V4).
- **A supplied net leaves its container only by declaration.** A container that
  exports a clock produced inside it declares an `output` block clock in its
  own `clocks:`, and the child's output is bound to that name; the declared
  port and the inner net are one. A child output bound to any other name is a
  local net and is invisible to the parent. Nothing about where consumers sit
  is consulted, so a block's ports never depend on a future assembling project.
- **A reset belonging to a supplied clock is supplied.** The testbench can
  release only a reset of a clock it generates, and the parent of a container
  can drive a reset only onto a port the container declares. In the example,
  `clkSys` is produced by `uClkGen`, so `rstSys_n` is produced by `uRstSys`
  inside the same container. At the design top this is a check (V9): an input
  reset of the top block belongs to an input clock of the top block. Below the
  top it follows from an `input` reset naming an `input` clock (§4.2).
- **A supplied clock's supplier defines when the clock is valid**, and every
  reset in that clock's domain is asserted whenever the clock's supplier is in
  reset or reports the clock invalid, and does not release before the clock is
  valid (R22). A PLL that has not locked, or a divider that is being
  reprogrammed, has a domain that must be held in reset. The recommended shape
  is the example's: the clock's supplier also supplies a raw reset of the
  domain, asserted by its own reset and by loss of lock, and a synchroniser in
  the domain takes that raw reset as its asynchronous input. Binding the
  synchroniser's input to the reference reset instead releases the domain a
  few edges after that reset, whether or not the clock is valid, and leaves no
  reset event when the supplier is later re-reset. The specification states
  this contract and does not check it.
- **A supplied clock runs from reset release** at a rate its supplier defines,
  or the project documents that its domain is held in reset until firmware
  enables the clock (R23). A programmable divider whose ratio resets to
  "disabled" produces no edges, so the synchroniser in its domain never
  releases and every consumer sits in reset; a simulation of such a design
  ends with no activity and, without the end-of-run report of §4.8, no
  diagnostic.
- **Supply graph.** At every instance of a block, for each `output` of the
  block that no child of the block drives, an edge runs from the resolved net
  of each of the block's `input` clocks and resets, asynchronous reset inputs
  included, to the resolved net of that `output`. A block with no `input` clock
  or reset is a root, an oscillator. The graph so formed over resolved nets is
  acyclic, and every supplied net reaches a testbench net or a root along it
  (V20). An exported output contributes no edge of its own; the child that
  drives it does.
  Two dividers each clocked by the other's output, or two synchronisers each
  taking the other's output as its asynchronous input, satisfy every per-net
  rule and describe a design that never starts. The edge rule takes every
  input of a block as feeding every output it produces. A block whose register
  interface runs on a clock it produces is therefore a cycle even when the
  clock depends on a reference input only; such a block is split into the
  producer and its register interface.
- An `output` reset whose clock is bound to `~` belongs to no clock. Only an
  asynchronous reset input may consume the net it drives.
- A clock mux is a supplier like any other. Switching sources under a live
  domain, glitch-free, is its implementation; its consumers see one clock.
- An `output` bound to `~` is left unconnected, as an unused output port is.
  There is no other way to leave one unconnected: outputs are never bound by
  name match and never omitted (§4.4).

### 4.6 Containers

A container's clock ports are the block clocks it declares, or the implicit
`clk` when it declares none; its reset ports likewise. Inside it, the nets
available for binding are those ports and the local nets its children drive.
Every child binding lands on one of them or is an error.

| Net inside container B | Driver | Consumers |
| :--- | :--- | :--- |
| B's declared `input` clock or reset, or its implicit `clk`/`rst_n` | B's parent, through B's own instance binding; the testbench when B is the top | child `input` entries bound to it, B's own logic |
| B's declared `output` clock or reset that a child output drives | that child (the export) | child `input` entries bound to it, B's own logic, B's parent through B's instance binding |
| B's declared `output` that no child drives | B's own implementation | the same |
| A local net | the child whose output binding names it | child `input` entries bound to it, at least one (V22); B's own logic may also use it |

Two properties follow, and both are requirements:

- A block's boundary is fixed by its own declaration alone (R8). Where it is
  instantiated, and what its children do, change nothing at its ports. A child
  project therefore has a stable boundary whether it is built alone or
  composed.
- Every instance map is validated against the declared clocks of the
  instantiated block and the nets of the container (V3, V4), so a mistyped
  name is an error at the line that carries it, never a silently created port.

A container that runs its own logic on a clock its children also use declares
it once and its children bind to it. The container's module carries one net
per local net, under the binding's name (R18); a local net is spelled
hierarchically in diagnostics, `uSoc.uUart.clkBaud`, since its name is scoped
to its container.

### 4.7 Nested projects

A child project's top block declares its own clocks and resets, as any block
does, and the child's instances bind to them. The assembling project
instantiates that block like any other, and its map binds the child's block
clocks to the assembler's container clocks:

```yaml
# child project 'sensorIp': its top block declares clocks clkPix (default), clkCfg
#                            and resets rstPix_n (on clkPix), rstCfg_n (on clkCfg)

# assembling project 'camera': its container block declares clkSys (default), clkPixel, clkPixel2
instances:
    uSensor: { container: camera, instanceType: sensorTop,
               clocks: { clkPix: clkPixel, clkCfg: clkSys },
               resets: { rstPix_n: rstPixel_n, rstCfg_n: rstSys_n } }
    uSensor2: { container: camera, instanceType: sensorTop,
                clocks: { clkPix: clkPixel2, clkCfg: clkSys },
                resets: { rstPix_n: rstPixel2_n, rstCfg_n: rstSys_n } }
```

Rules:

- The map keys are the child block's declared clocks and resets. No
  cross-project name resolution is written by the author, and the child's
  project file is not consulted for that binding: it describes the child's
  testbench, which the assembler has replaced.
- Automatic binding and the default fallback apply across the boundary for
  inputs exactly as within a project. A child `output` is bound explicitly, as
  everywhere.
- Renaming is free at every level. The assembler may bind `clkPix` to
  `clkPixel`; a container above may bind `clkPixel` to something else again.
  Nothing carries a name across a boundary except the binding.
- A clock or reset produced inside the child is a local net of the child block
  unless the child block declares it as an `output`. A declared output is bound
  by the assembler like any other output. The child's boundary is fixed by the
  child alone.

### 4.8 Design top and simulation environment

- The block of the instance named by `topInstance:` is bound to the testbench
  clocks and resets of the project file by the instance rules of §4.4: an
  `input` by name match, `clk` and `rst_n` by default fallback, an `output`
  observed. The top instance has `count` 1. The top block's `input` clocks and
  resets are the design's **primary** clocks and resets; every testbench entry
  binds one of them (V10), every top input reset belongs to a top input clock
  (V9), and a top input reset bound to testbench reset R, whose block clock is
  bound to testbench clock C, requires R to belong to C (V6).
- The simulation environment generates each testbench clock at its `period`
  and `timeUnit`, and asserts each testbench reset at time zero, releasing it
  after `releaseCycles` cycles of its clock. Supplied clocks and resets are
  driven by their suppliers; an `output` of the top block is observed and not
  generated. In lockstep with a co-simulation partner, each testbench reset
  follows the partner's assertion and release at the partner's event, without
  waiting on its own clock; both sides receive the release at the same
  quantum boundary and sample it at the same next edge. Two testbench clocks
  declared with equal `period` still have no guaranteed phase relationship
  (below) and remain mutually asynchronous to the design (§2).
- **No phase relationship** between testbench clocks is guaranteed, even when
  their periods are equal or in integer ratio, and a design shall not rely on
  one. Whether the environment randomises the initial phase of each testbench
  clock, seeded, so that simulation exposes the crossings silicon will, is Q7.
- Testbench resets on different clocks release independently, each after its
  own `releaseCycles`. No inter-domain release ordering exists unless the
  design builds it with suppliers.
- **End-of-run report.** The environment reports, at the end of an assembled
  simulation, every supplied clock that produced no edge and every supplied
  reset, and every exported output reset of the design top, that never
  released. These are the symptoms of a supplier that does not run from reset
  (§4.5, R23) and of a broken supply chain, and they otherwise end a run with
  no activity and no diagnostic.
- **A block simulated alone** is its own top: every `input` clock and reset it
  declares is generated. This applies to a block for which a co-simulation
  wrapper is generated, that is, one with `hasVl`. A `hasTb` block's testbench
  is SystemC only and generates no clocks; standalone clocks and resets exist
  only for the Verilated co-simulation wrapper of a `hasVl` block. Its
  attributes come from the block clock's own `period`/`timeUnit` when declared
  (§4.2), else from the block clock's **resolved clock** among the instances
  of the block in the project that declares it: the testbench clock every such
  instance reaches by following bindings upward. An assembling project does
  not re-evaluate a child project's standalone attributes. When the block has
  no instance, is instantiated on clocks that resolve to different testbench
  clocks, or its clock resolves to a supplier's output, the design determines
  no period and the block clock must declare one (V21). A reset is released
  after the `releaseCycles` of the testbench reset it resolves to, under the
  same rule, default 3 where the block declares `period`; an asynchronous
  reset input counts them on the block default clock. A block with `hasVl`
  whose default clock is not an `input` clock, or that has none, cannot
  release an asynchronous reset input, an error under V21. V9 applies to the
  standalone block as to the design top. The environment binds a signal to
  each `output` clock and reset of the block and observes it. A port's
  bus-functional model lives in the co-simulation wrapper, on the RTL side,
  and is clocked by the port's block clock, generated or observed, and reset
  by that clock's selected reset; it is generated logic under V19, so every
  clock that times a port of such a block has a selected reset.

### 4.9 Reset semantics

Reset behaviour is fixed by this specification rather than declared per reset.

- **Polarity.** Every reset is active-low. The name is the author's, `rst_n` by
  convention; the behaviour is not. Polarity is not declarable; a block
  needing an active-high reset inverts it in its own implementation.
- **Primary reset, assertion and release.** The simulation environment asserts
  a testbench reset at time zero, a release-to-assert transition at time zero
  being permitted, holds it, and releases it after the
  `releaseCycles`-th rising edge of its clock and before the next edge. Release
  is therefore synchronous to the reset's own clock and never coincides with an
  edge. Under co-simulation lockstep, release instead follows the partner's
  event and does not wait on the reset's own clock (§4.8).
- **Release is synchronous for every sampled reset.** A reset that any block
  samples in its domain, that is, one bound to any block reset other than an
  asynchronous reset input, is released synchronously to the clock it belongs
  to; assertion may be asynchronous. The environment guarantees this for a
  testbench reset, except under co-simulation lockstep, where the partner owns
  release timing and the environment copies it at the partner's event instead
  (§4.8); the supplier guarantees it for a supplied reset, which is what a
  reset synchroniser is for. A reset consumed only by asynchronous reset
  inputs, such as a PLL wrapper's raw lock reset, is exempt, since nothing
  samples it. Generated logic samples its reset synchronously and relies on
  this contract (R21); the specification does not check a supplier's timing.
- **Supplied reset, assertion.** A reset supplier implements its assertion path
  with explicitly asynchronous flops written outside the macro library, so
  that the domain is reset even while its clock is stopped. The macro
  library's bodies follow the selected style; these explicit flops do not.
- **Flop-level style.** Whether a flop treats its reset synchronously,
  asynchronously, or not at all (initial value only, for an FPGA image) is a
  property of the build flow, selected once per compilation, not of the YAML.
  The three are not equivalent, and the design carries these obligations
  toward them:
  - under the synchronous style a domain is reset only while its clock runs,
    so a supplied clock toggles while the resets of its domain are asserted
    (R23), and a domain whose clock is stopped during reset is not reset;
  - under the initial-value style a reset asserted after initialisation has no
    effect on generated flops, so a design that re-asserts any reset at run
    time, by firmware soft reset, watchdog, or a re-reset supplier, shall not
    be built in that style;
  - under the asynchronous style, release that is not synchronous to the
    domain clock is a recovery and removal violation, which the release rule
    above excludes.
  A design meeting the release rule, the clock validity contract (§4.5) and
  these obligations is correct under whichever style its flow selects.
- **Domain.** A reset is used only by logic clocked by the clock it belongs to.
  V6 enforces this at the instance map; a block using a reset across its own
  clocks is the designer's business, as any crossing is.

### 4.10 Constraints and test

Out of scope, stated so that nothing is assumed:

- No constraint file (SDC, XDC) is generated. Where a flow writes one by hand,
  the top block's clock port is the anchor for a primary clock, and the
  supplier's output pin the anchor for a generated clock.
- The module-local alias by which a block's implementation refers to its
  default clock and selected reset by the names `clk` and `rst_n` is a net
  alias. It defines no clock and needs no constraint.
- A supplied clock or reset produced inside a block is that block's to make
  testable: scan bypass or on-chip clock control muxing of a supplied clock,
  and test-mode override of a supplied reset, live in the supplier block's
  implementation. The specification places nothing on the path between a
  supplier and its consumers.
- On an FPGA a flop-driven divided clock should be routed through a global
  buffer or replaced by a clock enable; the choice is the supplier block's.

### 4.11 Model boundary

Block clocks and resets are RTL boundary facts. The SystemC model carries no
clock or reset ports and is untimed with respect to block clocks; the
SystemC simulation kernel's own notion of time is not a clock in this
specification (§2). An `output` block clock or reset has no SystemC-model
counterpart: nothing in model space produces or observes one. The
co-simulation wrapper drives every clock and reset to the RTL side of the DUT
it wraps and compares data ports only; no clock or reset is compared between
the SystemC model and the RTL (R26).

## 5. Functional requirements

Each requirement is testable from authored YAML and the emitted design alone,
except R17, R21 and R22, which the specification does not check, and R23,
whose violation the end-of-run report covers (§4.8). The V items are
build-time diagnostics; a requirement that describes the emitted design or
the binding the generator performs is verified by generation tests against
the emitted design rather than by a diagnostic.

### Testbench level

- **R1.** A project file declares the testbench clocks in `clocks:` and the
  testbench resets in `resets:`, each reset belonging to one clock. A clock's
  `period` is optional, default 1 ns. Omitting either section yields `clk`, or
  `rst_n` on the default clock.
- **R2.** Exactly one testbench clock and one testbench reset is the default,
  and the default reset belongs to the default clock (V23).
- **R3.** Every testbench clock and reset binds an `input` of the top block by
  the instance rules; an entry that binds nothing is an error (V10). The
  project file is not used to bind the top block when the project is a child
  of another; a block's own `period` and `releaseCycles` for standalone
  simulation still come from it (V21).

### Block level

- **R4.** A block declares the clocks its implementation uses, each with a
  direction, and the resets it uses, each with a direction and each belonging
  to one of the block's clocks, except an asynchronous reset input, which
  belongs to none.
- **R5.** The declaration is complete. A block's clocks and resets are exactly
  its declared entries, for a container as for a leaf, and nothing is inferred
  from children, connections or ports. A block declaring no clocks has `clk`;
  declaring no resets has `rst_n` on its default clock, except a block with no
  `input` clock, which then has no reset (V15).
- **R6.** Each block clock has at most one selected reset, chosen among its
  declared resets and, in a container, the local reset nets belonging to it
  other than one consumed only by asynchronous inputs: the declared one marked
  `default: true`, or the sole candidate. Generated logic on a
  block clock uses that clock's selected reset, and a clock hosting generated
  logic without one is an error (V19). A block clock may have no reset; logic
  in such a domain is the designer's to reset.
- **R7.** Every port of a block is timed by one of the block's clocks: the one
  its declaration names, or, for a top-down port, the one its connection
  names, or else the block default clock, except a synthesised register-bus
  port, which R25 governs. A declared port's clock and a connection's
  `clock:` are not read as a precedence; where both are present they must
  agree (V14). A block with no default clock names every port's clock.
- **R8.** A block's `clocks:`, `resets:` and `ports:` declarations reference
  nothing outside the block, and its boundary is fixed by them alone. It is
  therefore valid in any container unchanged (V1, V2).

### Instance level

- **R9.** An instance binds each block clock and reset of the instantiated
  block to a clock or reset of its container: a declared clock of the
  container, or a local net driven inside it.
- **R10.** An `input` binding omitted by the author is taken by name match,
  and for a block clock named `clk` by the container's default clock, and for a
  block reset named `rst_n` by the selected reset of the container clock its
  own block clock is bound to. An undeclared container offers only `clk` and
  `rst_n`. An asynchronous reset input takes no such fallback: only map or
  name match binds it, else it is an error (V4).
- **R11.** An `output` binding is always written, to a container clock, to a
  new local net name, or to `~`, except at the top block, whose outputs the
  testbench observes. No supplier is ever created by name match, and no output
  is ever dropped silently.
- **R12.** The same block may be instantiated more than once, each instance on
  different container clocks.
- **R13.** Within a container, each clock or reset is one net with exactly one
  driver, decided by the table in §4.6.

### Composition

- **R14.** A child project's top block is bound by the assembling project's
  instance map under the child block's own clock names; the child's project
  file is not used for that binding, though a block's own `period` and
  `releaseCycles` for standalone simulation still come from it (V21).
- **R15.** An assembling project may bind a child block's clocks to any of its
  container's clocks, including binding two instances of the same child block
  to different clocks.

### Derived facts

- **R16.** The container clock of each end of every connection is derived from
  the port's block clock and the instance's map. A connection whose two ends
  derive to different container clocks is a clock domain crossing.
- **R17.** A crossing is the designer's responsibility. The tool neither
  rejects nor synthesises one. It is not reported (Q2).
- **R18.** Each block module carries exactly its declared clocks and resets as
  ports, in declaration order, clocks before resets; an undeclared block
  carries `clk` and `rst_n`. A container's module additionally carries one
  internal net per local net, under the binding's name.
- **R19.** A memory is in one domain, the block clock its declaration names,
  default the owning block's default clock. Every hardware access to it is in
  that domain.
- **R20.** A register handler serving a memory whose domain differs from the
  handler's bus domain provides a domain-safe access path to that memory, with
  these properties:
  - the access crosses on a request and acknowledge handshake, each side
    synchronised into the other's domain, with address, write data and write
    enable held stable from request until acknowledge;
  - the memory-side access is performed by logic clocked by the memory's clock
    and reset by the block's reset in that domain, and read data is captured
    there after the primitive's read latency and held until the bus side has
    acknowledged it;
  - the bus stalls the access until the response is in the bus domain, and
    at most one access is outstanding per memory;
  - the memory's datapath access is unaffected, and the memory is never
    re-clocked to the bus to avoid the crossing;
  - the bridge's memory side drives the memory-side port the handler already
    owns, clocked by the memory's `clock` and reset by its `reset`. The port
    topology is unchanged by this specification and contains no arbiter: a
    dual-port memory gives the handler one port and the datapath the other; a
    single-port memory gives the handler its only port, and the datapath
    reaches such a memory only when it is `local`, by reading the array
    directly inside the block. Every one of those accesses is in the memory
    domain, so nothing is shared across the crossing and nothing needs
    arbitration;
  - a reset on either side returns that side to idle and discards any
    outstanding request, and the handshake re-synchronises so that neither a
    permanent bus stall nor a duplicated access can result. If the memory side
    resets while a bus access is outstanding, the bridge completes that access
    with the bus protocol's error indication, `pslverr` on APB, read data
    undefined, and does not retry it; firmware re-issues the access. If the bus
    side resets, the bus transaction no longer exists and the memory side
    returns to idle without completing anything;
  - a request that arrives while the memory side is held in reset completes
    with the same error indication without touching the memory; the memory
    side's reset state is synchronised into the bus domain for this purpose.
    A request whose memory clock is not running stalls the bus: no timeout is
    specified, the bus protocol has none, and firmware shall not access a
    memory whose domain clock is not running;
  - the error indication reaches the bus master: every generated router between
    the handler and the bus feed propagates it, since an error absorbed at the
    first router leaves firmware reading undefined data as valid.
  This is the only crossing for which the tool generates synchronisation logic.
  Generated wiring carries every crossing the designer authors, and those remain
  the designer's. A generator that does not implement R20 rejects a memory
  served by a handler in another domain (V24).
- **R21.** Every reset is active-low. A testbench reset is asserted from time
  zero and released synchronously to its own clock by the environment. Under
  co-simulation lockstep, the partner owns release timing and the environment
  copies it at the partner's event instead (§4.8). Every reset that a block
  samples in its domain is released synchronously to the clock it belongs to,
  by the environment for a testbench reset and by the supplier for a supplied
  reset; a reset consumed only by asynchronous reset inputs is exempt.
  Generated logic relies on this and samples its reset synchronously. A
  supplier's timing is not checked (§4.9).
- **R22.** The supplier of a clock defines when the clock is valid. Every reset
  belonging to a supplied clock is asserted whenever that supplier is in reset
  or reports the clock invalid, and releases only once the clock is valid. The
  recommended shape is a raw reset supplied by the clock's supplier and
  consumed by a synchroniser's asynchronous input (§4.5). A reset supplier
  asserts through explicitly asynchronous flops regardless of the flop style
  selected for the build (§4.9). Not checked.
- **R23.** A supplied clock's supplier produces the clock from reset release
  onward at a defined reset-default rate, or the project documents that the
  domain is held in reset until firmware enables the clock. The simulation
  environment reports at end of run every supplied clock that produced no edge
  and every supplied or exported reset that never released (§4.8).
- **R24.** A block simulated alone generates its declared `input` clocks and
  resets, each with the attributes of its own declaration when present, else
  of the testbench clock or reset it resolves to in the design (§4.8).
- **R25.** The register port of a top-down leaf, one that authors no
  `registerPorts:`, takes the clock its instance's `clocks:` map binds to
  the bus clock, the container clock, in the leaf's own container, of the
  far end of the leaf's synthesised feed (§4.3), and independently the reset
  its `resets:` map binds to that clock's selected reset (V8, V25). Every
  instance of the block resolves to the same clock port and the same reset
  port (V26). A `registerPorts:` entry naming `clock:` or `reset:` stays
  authoritative and must agree with the bound bus clock and reset (V14).
- **R26.** The SystemC model carries no clock or reset ports. Co-simulation
  drives clocks and resets to the RTL side only and compares data ports.

## 6. Validation requirements

Each is an error at project build with a diagnostic naming the YAML file and
line of the offending entry.

- **V1.** A block reset's `clock` names a block clock of the same block. A
  reset declared `async: true` carries no `clock` and is an `input`.
- **V2.** A port's `clock` names a block clock of the same block.
- **V3.** Every `input` clock and reset of an instantiated block resolves to a
  container clock or reset, by map, name match, or the default fallback of
  §4.4. Every `output` appears in the map, bound to a container net, a new
  local net name, or `~`.
- **V4.** A map key names a block clock or reset of the instantiated block. A
  map value on an `input` names a declared clock or reset of the container or
  a local net some child output drives; the diagnostic for a name that is
  neither lists the container's declared clocks or resets and its local nets. A
  map value on an `output` names a declared `output` of the container, a local
  net name, or `~`. A clock entry binds a clock and a reset entry a reset. An
  asynchronous reset input that the map omits, in a container with no reset of
  that name, is reported here.
- **V5.** Within a container, each clock or reset has exactly one driver
  (§4.6). Two outputs bound to one name, an output bound to a container
  `input`, and an instance binding two of its own entries to a net one of them
  drives, are each rejected.
- **V6.** A block reset bound to container reset R, where the reset's block
  clock is bound to container clock C, requires R to belong to C. For a
  declared container reset, membership is the container's `clock` field; for a
  local net, it is the clock the supplying output's block reset belongs to,
  mapped through the supplier's instance, and nothing further is checked at
  the binding that creates it. The rule applies equally to an `output` reset
  bound onto a container's declared `output` reset: the child reset's clock,
  mapped through the child instance, is the container clock the declaration
  names. The testbench is the top block's container for this rule. A reset
  released in a domain other than the one it resets is a design defect, not a
  crossing. An asynchronous reset input has no block clock and is exempt.
- **V7.** Within a block, the names of block clocks, block resets, interface
  ports, memories and local nets driven inside it, together with the reserved
  names `clk` and `rst_n` when the block does not declare them, are pairwise
  distinct. Within a project file, a clock and a reset may not share a name.
- **V8.** A memory's `clock` names a block clock of its owning block. Every
  `memoryConnections:` row reaching the memory derives, on the accessing side,
  to the same container clock as the memory mapped through its owning
  instance; a mismatch is an error whose diagnostic names both domains and
  directs the author to a bridge block. A memory with accessors may not have
  its clock bound to `~` at the owning instance. Firmware access through the
  register handler is exempt (R20). A register-bus tree is one domain throughout,
  through the bindings at each level, the domain of the feed reaching the
  primary router's port, and every register, router and handler in the tree is
  in it. A top-down leaf none of whose declared clock ports is bound to the
  bus clock (R25) is reported here, at the instance map.
- **V9.** Every `input` reset of the top block, other than an asynchronous
  reset input, belongs to an `input` clock of the top block. The testbench can
  release only a reset of a clock it generates.
- **V10.** Every testbench clock and reset binds an `input` of the top block by
  name match or default fallback. An entry that binds nothing is an error. A
  project file that declares no `topInstance:` is exempt: it has no top block
  to bind, and its `clocks:`/`resets:` serve as definitions for standalone
  evaluation elsewhere (V21).
- **V11.** The default fallback of §4.4 binds `rst_n` to the selected reset of
  the container clock its own block clock is bound to, so it satisfies V6 by
  construction; a container clock with no selected reset makes the fallback an
  error naming that clock.
- **V12.** An instance with `count` greater than one binds every `output` entry
  to `~`.
- **V13.** A connection `clock:` used to derive a top-down port's domain
  names a container clock that exactly one `input` block clock of the instance
  resolves to, by map, name match or fallback. Two on the same net leave the
  block clock ambiguous; none means the block does not run on that clock.
- **V14.** Where a declared port, whether or not it names `clock:`, has a
  connection that also carries `clock:`, the port's block clock, the one it
  declares or the block default clock when it declares none, mapped through
  the instance must equal the connection's container clock. A mismatch is an
  error, not a precedence: neither source overrides the other.
- **V15.** A block with no `input` block clock names a clock on every port and
  on every reset it declares other than an asynchronous reset input, and has no
  implicit `rst_n`.
- **V16.** A `connectionMaps:` row's boundary port takes the inner port's
  derived domain, which is a block clock of the container, declared or
  implicit; an inner domain that is an unexported local net is an error at the
  row, directing the author to declare the net as an `output` clock. Where a
  connection reaches the boundary port from outside, its derived domain at that
  end equals the port's domain mapped through the container's instance. The
  row carries no `clock:` of its own.
- **V17.** `registerConnections:` and `memoryConnections:` rows carry no
  `clock:`. Each side's domain is derived: the register from its bus, the memory
  from its declaration, the accessor from its own block and instance.
- **V18.** A block declaring more than one `input` clock marks exactly one
  `default: true`; `default` and `period` never appear on an `output` clock. At
  most one reset per block clock carries `default: true`, and a block with
  several declared resets on its default clock marks exactly one.
- **V19.** A block clock that hosts generated logic, the bus clock of a
  register port or the memory clock of a memory served by a handler in another
  domain, the clock of a decode router's upstream port, or the clock of a port
  of a block with `hasVl`, has exactly one selected reset: the one
  the `registerPorts:`, `addressBlock:` or memory `reset:` names, or, for a
  top-down leaf's register port, the leaf reset port its `resets:` map binds
  to the bus reset (R25); else the declared reset on that clock marked
  `default: true`, else the sole candidate among the declared resets and local
  reset nets on that clock, a local net consumed only by asynchronous inputs
  excluded. Zero or several unmarked candidates is an error. A `reset:` so
  named is a declared reset or local net belonging to the entry's clock;
  otherwise an error. A memory not served across a crossing needs no reset,
  and a block clock hosting no generated logic needs none.
- **V20.** The supply graph is acyclic and rooted. Its edges are taken at
  every instance of a block, for each `output` of the block that no child of
  the block drives: from the resolved net of each `input` clock or reset of
  the block, asynchronous reset inputs included, to the resolved net of that
  `output`. A block with no `input` clock or reset is a root. No net reaches
  itself, and every supplied net reaches a testbench net or a root. The
  diagnostic names the instances on the cycle, hierarchically, or the supplied
  net with nothing behind it.
- **V21.** For a block with `hasVl`, evaluated in the project that
  declares the block and never re-evaluated by an assembler, each of its
  `input` clocks either declares `period` or resolves to one testbench clock
  through every instance of the block in that project, of which there is at
  least one. A clock that resolves to different testbench clocks, or to a
  supplier's output, or has no instance, and declares no `period` is an error
  naming the instances that disagree. Each `input` reset resolves to one
  testbench reset by the same rule, else the block declares `period` and the
  reset takes the default `releaseCycles`. An asynchronous reset input of a
  block whose default clock is not an `input` clock, or that has no default
  clock, is an error naming the reset.
- **V22.** A local net is consumed by at least one child `input` binding of
  the container that holds it. A net driven and never consumed is an error
  naming the driving binding and any similarly named declared `output` of the
  container; `~` is the way to leave an output unused.
- **V23.** A project file's `clocks:` and `resets:` each carry exactly one
  `default: true`, implied for a single entry, and the default reset belongs to
  the default clock.
- **V24.** A memory served by a register handler in another domain (R20) is
  rejected at build when the generator does not implement the R20 bridge.
- **V25.** A top-down leaf none of whose declared reset ports is bound to
  the bus's reset (R25) is an error at the instance map; the fix is to map a
  leaf reset port to that container reset.
- **V26.** Two instances of a top-down leaf whose `clocks:` or `resets:`
  maps resolve the register port (R25) to a different clock port or a
  different reset port is an error naming the disagreeing instances.

## 7. Deferred features

- **Q2. Crossing report.** Every crossing is derivable inside its container.
  A crossing summary is not emitted; the tool adds one, naming each end's
  resolved clock, on request.
- **Q3. Clock attributes.** `period` and `timeUnit` are the only clock
  attributes. Duty cycle, phase offset and a per-instance period override are
  added on request.
- **Q4. Supplied clock relationships.** A supplied clock carries no `period`
  or relationship attribute. A consumer's standalone period comes from its
  own declaration (V21). A `derivedFrom:` relationship with a ratio is added
  when a design needs one.
- **Q7. Testbench clock phase.** The environment starts every testbench
  clock at time zero with the same phase; no phase relationship is
  guaranteed to the design (§4.8). Seeded, reproducible phase randomisation
  is added on request.

## 8. Worked examples

### 8.1 One IP, two clocks

```yaml
# project file
clocks:
    clkSys:  { desc: "system", default: true, period: 10, timeUnit: ns }
    clkSlow: { desc: "housekeeping", period: 100, timeUnit: ns }
resets:
    rst_n:     { desc: "system reset", default: true, clock: clkSys }
    rstSlow_n: { desc: "housekeeping reset", clock: clkSlow }

# design yaml; the top block declares both clocks, the timer declares nothing
blocks:
    soc:
        desc: "design top"
        clocks:
            clkSys:  { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clkSys }
            rstSlow_n: { clock: clkSlow }
    timer:
        desc: "free-running timer"
        ports:
            regs: { interface: apbIf, direction: dst }

instances:
    uTimerFast: { container: soc, instanceType: timer }
    uTimerSlow: { container: soc, instanceType: timer,
                  clocks: { clk: clkSlow }, resets: { rst_n: rstSlow_n } }
```

The testbench binds `soc`'s four ports by name. `uTimerFast` binds `clk` to
`clkSys` by the default fallback, since `soc` has no clock named `clk`, and
`rst_n` to `rst_n` by name. `uTimerSlow` is re-clocked. Had `soc` declared
nothing, both timers would run on `clk`, and `clocks: { clk: clkSlow }` would be
an error naming `clk` as the only clock `soc` has.

### 8.2 A block producing a clock, and the reset in its domain

```yaml
# project file (extract)
clocks:
    clkSys: { desc: "system", default: true, period: 10, timeUnit: ns }
resets:
    rst_n:  { desc: "system reset", default: true, clock: clkSys }

# design yaml
blocks:
    uart:
        desc: "UART; declares nothing, so its one clock is clk and its one reset rst_n"
    baudGen:
        desc: "programmable baud divider; ratio resets to a running default (R23)"
        clocks:
            clk:     { }
            baudClk: { direction: output }
        ports:
            regs: { interface: apbIf, direction: dst }
    baudRstSync:
        desc: "reset synchroniser for the baud domain"
        clocks:
            clk: { }
        resets:
            rstIn_n:  { async: true }
            rstOut_n: { clock: clk, direction: output }
    uartTx:
        desc: "serialiser"
        ports:
            din: { interface: byteIf,   direction: dst }
            tx:  { interface: uartTxIf, direction: src }

instances:
    uBaudGen: { container: uart, instanceType: baudGen,
                clocks: { baudClk: clkBaud } }                   # clk binds to uart's clk by name
    uBaudRst: { container: uart, instanceType: baudRstSync,
                clocks: { clk: clkBaud },
                resets: { rstIn_n: rst_n, rstOut_n: rstBaud_n } }
    uTx:      { container: uart, instanceType: uartTx,
                clocks: { clk: clkBaud }, resets: { rst_n: rstBaud_n } }
```

`clkBaud` and `rstBaud_n` are local nets of `uart`, created by the two output
bindings and consumed by name inside `uart`. `uart` declares nothing, so its
boundary is `clk` and `rst_n`, and the testbench, or a parent container, drives
those two and sees nothing of the baud domain. The synchroniser takes `rst_n`
in as an asynchronous input, so binding it to a `clk`-domain reset while the
block runs on `clkBaud` is legal, and it releases `rstBaud_n` on `clkBaud`
edges, inside the domain. That binding satisfies R22 because `rst_n` is also
the divider's own reset: `clkBaud` is invalid exactly while `uBaudGen` is in
reset. It satisfies R23 only because the divider's ratio resets to a running
default; a divider that resets to "disabled" would hold `uTx` in reset until
firmware programmed it, and the design would have to say so.

`uartTx` and `baudRstSync` run on `clkBaud`, a supplier's output, so a
standalone testbench for either needs a declared period: `uartTx` would declare
`clocks: { clk: { period: 8680, timeUnit: ns } }` (V21). Blocks without
`hasVl` need nothing. With `hasVl`, `uart` needs no period, since its `clk`
resolves to the testbench clock, so no port of `uart` lacks a selected
reset.

Had another block outside `uart` needed the baud clock, `uart` would declare
`clocks: { clk: { }, baudClk: { direction: output } }` and `uBaudGen` would bind
`baudClk: baudClk`. The declaration exports the net; nothing about the
consumer's position does. Because the declaration is complete, `uart` then
declares `clk` too, and its resets.

### 8.3 A child project on two assembler clocks

```yaml
# child project 'sensorIp': project file, used only when sensorIp is simulated alone
clocks:
    clkPix: { desc: "pixel clock", default: true, period: 13, timeUnit: ns }
    clkCfg: { desc: "configuration clock", period: 20, timeUnit: ns }
resets:
    rstPix_n: { desc: "pixel reset", default: true, clock: clkPix }
    rstCfg_n: { desc: "configuration reset", clock: clkCfg }

# child project 'sensorIp': its top block
blocks:
    sensorTop:
        desc: "sensor IP top"
        clocks:
            clkPix: { default: true }
            clkCfg: { }
        resets:
            rstPix_n: { clock: clkPix }
            rstCfg_n: { clock: clkCfg }

# assembler 'camera' design yaml
blocks:
    camera:
        desc: "camera assembler top"
        clocks:
            clkSys:    { default: true }
            clkPixelL: { }
            clkPixelR: { }
        resets:
            rstSys_n:    { clock: clkSys }
            rstPixelL_n: { clock: clkPixelL }
            rstPixelR_n: { clock: clkPixelR }
instances:
    uSensorL: { container: camera, instanceType: sensorTop,
                clocks: { clkPix: clkPixelL, clkCfg: clkSys },
                resets: { rstPix_n: rstPixelL_n, rstCfg_n: rstSys_n } }
    uSensorR: { container: camera, instanceType: sensorTop,
                clocks: { clkPix: clkPixelR, clkCfg: clkSys },
                resets: { rstPix_n: rstPixelR_n, rstCfg_n: rstSys_n } }
```

`sensorTop`'s clocks are the two it declares. Each assembler instance binds
them independently, so the two sensors run on two pixel clocks. The child's
project file is read only when `sensorIp` is simulated on its own, where its
four entries bind `sensorTop`'s four ports by name; in `camera` the periods
come from `camera`'s own project file through `camera`'s ports. A standalone
testbench for `sensorTop` takes its periods from `sensorIp`'s project file,
where `sensorTop` is the top; `camera`'s two pixel clocks do not enter that
evaluation (V21).

### 8.4 A top-down leaf whose registers run on a non-default clock

```yaml
# project file
clocks:
    clkSys:     { desc: "system", default: true, period: 10, timeUnit: ns }
    clkCapture: { desc: "capture", period: 20, timeUnit: ns }
resets:
    rstSys_n:     { desc: "system reset", default: true, clock: clkSys }
    rstCapture_n: { desc: "capture reset", clock: clkCapture }

# design yaml
blocks:
    top:       { desc: "design top",
                 clocks: { clkSys: { default: true }, clkCapture: { } },
                 resets: { rstSys_n: { }, rstCapture_n: { clock: clkCapture } } }
    apbDecode: { desc: "register-bus router",
                 addressBlock: { addressGroup: top, addressIncrement: 0x1000,
                                  maxAddressSpaces: 4, varType: addr_id_capture,
                                  enumPrefix: ADDR_ID_CAPTURE_ } }
    sampler:   { desc: "top-down leaf; owns registers, authors no registerPorts:",
                 clocks: { clk: { default: true }, clkCap: { } }, resets: { rst_n: { }, rstCap_n: { clock: clkCap } } }
instances:
    uDecode:  { container: top, instanceType: apbDecode,
                clocks: { clk: clkCapture }, resets: { rst_n: rstCapture_n } }
    uSampler: { container: top, instanceType: sampler,
                clocks: { clk: clkSys, clkCap: clkCapture }, resets: { rst_n: rstSys_n, rstCap_n: rstCapture_n } }
```

`top` declares `clkSys` (default) and `clkCapture`, each with its own
reset. `uDecode` binds onto `clkCapture`, so the register tree it feeds is
in that domain (V8). `sampler`'s register port takes `clkCap`, not the
default `clk`, because `clkCap` is the port `uSampler`'s map binds to
`clkCapture`, the clock the feed resolves to (R25). Its reset is
`rstCap_n`, bound to `clkCapture`'s selected reset (V19). Because `sampler`
is generated once, every instance of it must resolve to the same clock and
reset port (V26).
