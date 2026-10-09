---
name: design-architecture
description: Guide for defining regular arch2code YAML architecture including blocks, instances, interfaces, connections, connectionMaps, memoryConnections, registerConnections, registers, memories, clocks and resets. Use for non-parameterized architecture wiring and general block hierarchy.
---
# Skill: Design architecture

## Purpose
Define hardware architecture in arch2code YAML: blocks, instances, interfaces, connections, connection maps, registers, memories, clocks and resets. For constants, types and structures, use `design-types-structures.md`. For parameterizable blocks, variants, `ipParameters` and per-port parameters, use `design-parameterizable-blocks.md`. For making registers and memories reachable by firmware, use `design-register-decode.md`.

## References
*   `ARCH2CODE_AI_RULES.md`, sections "Low-Level Architecture Elements", "Interfaces & Interface Types", "Blocks & Instances" and "Connections & Connection Maps".

## File structure

*   Design sections: `include`, `constants`, `types`, `variables`, `structures`, `interfaces`, `blocks`, `instances`, `connections`, `connectionMaps`, `memoryConnections`, `registerConnections`, `registers`, `memories`. Parameterizable designs add `ipParameters` and `parameters`.
*   The YAML is relational. Rows link by name through keys such as `container`, `instanceType`, `block`, `src` and `dst`.
*   Write one row per line with an inline dict for `instances:`, `connections:`, `connectionMaps:`, `memoryConnections:`, `registerConnections:`, `registers:` and `memories:`, as the examples below do.

## 1. Blocks (`blocks:`)

| Field | Meaning | Default |
| :--- | :--- | :--- |
| `desc` | Required. | |
| `hasRtl` | Generate RTL. | `true` |
| `hasMdl` | Generate a SystemC model. | `true` |
| `hasVl` | Generate a Verilator wrapper. | `false` |
| `hasTb` | Generate a testbench. | `false` |
| `hasSkt` | Generate a Python-socket shell, `<block>Socket.cppm`, and its socket catalog. A parameterizable block with `hasSkt` also needs `hasMdl`. An AXI socket carries a `data_t` of at most 16 bytes, checked at compile time. | `false` |
| `ports` | Explicit ports keyed by name: `{interface, direction, clock}`. `direction` is `src` or `dst`. A port whose interface differs from the connection's is adapted; see "Cross-parameter connections" in `design-parameterizable-blocks.md`. | inferred from connections |
| `clocks`, `resets` | The block's clock and reset ports. See [Clocks and resets](#7-clocks-and-resets). | one input `clk`, and `rst_n` on it |
| `addressBlock` | Makes the block a register-bus router. | |
| `registerPorts` | The block's own register-bus port. | |

*   A router's RTL is generated from the `apbDecodeModule` template. A router owns no registers or `regAccess` memories and declares no `registerPorts:`. `design-register-decode.md` lists the `addressBlock:` fields.
*   `registerPorts:` has at most one row, for example `registerPorts: { regs: { interface: ipReg } }`. A block with no `ports:` may omit it. Its register port is then inferred from what feeds it, the serving router or an enclosing passthrough container. See "Inferring the register bus" in `design-register-decode.md`, which also says when a block with `ports:` needs it.
*   A `hasRtl: true` block may contain only `hasRtl: true` blocks. A model-only child (`hasRtl: false`) needs a model-only parent.
*   A block that owns registers, `regAccess` memories or `registerPorts:` is a register consumer, and a router outside the block must serve it. `design-register-decode.md` says where the router goes and which instances carry `addressGroup:`.
*   Where generated files go depends on the project's layout. See `setup-project.md`.

```yaml
blocks:
  dma_controller:
    desc: "DMA Controller"
    hasVl: true
  stream_filter:
    desc: "Filter with explicit ports"
    ports:
      in_data:  {interface: stream_if, direction: dst}
      out_data: {interface: stream_if, direction: src}
```

## 2. Instances (`instances:`)

| Field | Meaning |
| :--- | :--- |
| `container` | Required. The block that contains the instance. |
| `instanceType` | Required. The block to instantiate. |
| `addressGroup` | The group of the router that serves this instance. Set it on an instance a router serves directly. Leave it off an instance fed through a router-less container, because that container's instance carries it. `design-register-decode.md` gives the rule. |
| `clocks`, `resets` | Binding map from the block's clock and reset ports to the container's nets. See [Clocks and resets](#7-clocks-and-resets). |
| `count` | Not supported. `make db` rejects any value other than 1, so declare each instance separately. |

The project's `topInstance` is the root of the hierarchy, and its container is its own block:

```yaml
instances:
  soc_tb: {container: soc_tb, instanceType: soc_tb}   # topInstance
  u_soc:  {container: soc_tb, instanceType: soc}
  u_dma:  {container: soc, instanceType: dma_controller, addressGroup: system}
```

## 3. Interfaces (`interfaces:`)

| Field | Meaning |
| :--- | :--- |
| `interfaceType` | Required. The protocol, such as `rdy_vld`, `req_ack`, `apb` or `status`. |
| `desc` | Required. |
| `structures` | List of `{structureType, structure}` binding the protocol's payload slots. |
| `maxTransferSize` | For multi-cycle interfaces. Default `0`. |

*   Prefer handshaked protocols for links between arch2code blocks. Use `raw` only at a design boundary with a handshake-less external pinout. See `ARCH2CODE_AI_RULES.md` (raw).
*   Use `status` for level and pulse signals such as pps, fsync or GPIO pins. A `raw` output nobody reads stalls its writer. See `systemc-interfaces.md`.

```yaml
interfaces:
  dma_req_if:
    interfaceType: req_ack
    desc: "DMA Request"
    structures:
      - {structureType: data_t, structure: dma_req_t}
```

## 4. Connections (`connections:`)

A connection joins two sibling instances, both with the same `container`. To link a block to its own child, use a connection map. `make db` rejects a connection whose ends sit in different containers, or that names the topInstance.

| Field | Meaning |
| :--- | :--- |
| `interface` | Required. |
| `src`, `dst` | Required. Sibling instances. |
| `name` | Names the connection and, without `srcport`/`dstport`, its ports. Set it, or `srcport:`, when two connections of one interface leave the same instance. |
| `srcport`, `dstport` | Port name at each end. |
| `interfaceName` | Channel name in the container. |
| `clock` | A container clock that sets the domain of both ends. See [Clocks and resets](#7-clocks-and-resets). |

```yaml
connections:
  - {interface: dma_req_if, src: u_dma, dst: u_mem_ctrl}
  - {interface: dma_req_if, src: u_dma, dst: u_periph, name: periph_req}
```

## 5. Connection maps (`connectionMaps:`)

A connection map joins a port of `block` to a port of one of its child instances.

| Field | Meaning |
| :--- | :--- |
| `interface` | Required. |
| `block` | Required. The parent block. |
| `direction` | Required. `src` or `dst`, as seen from the parent's port. |
| `instance` | Required. A child instance of `block`. |
| `port` | The parent's port name. |
| `instancePort` | The child instance's port name. |
| `name` | Used for whichever of `port` and `instancePort` is not given. |

To reach a child port named `in_data` while keeping the parent's port named after the interface, set `instancePort: in_data`. `port: in_data` would rename the parent's port instead.

Bind the parent port where the block is instantiated, with a connection or an outer connection map whose direction matches and whose port name matches `port` (else `name`, else the interface name). The interface may differ, as in an adapted bind. `make db` rejects a connection map whose parent port nothing binds, and any connection map on the topInstance's block.

```yaml
instances:
  u_gen:    {container: soc_tb, instanceType: stream_gen}
  u_filter: {container: soc, instanceType: stream_filter}

connections:
  - {interface: stream_if, src: u_gen, dst: u_soc}   # binds soc's stream_if port

connectionMaps:
  - {interface: stream_if, block: soc, direction: dst, instance: u_filter, instancePort: in_data}
```

## 6. Registers, memories and their connections

### Registers (`registers:`)

| Field | Meaning |
| :--- | :--- |
| `register` | Required. Name. |
| `block` | Required. Owner block. |
| `regType` | Required. `rw`, `ro`, `ext` or `memory`. An `ext` register's structure is at most 32 bits wide, the register bus width, and `make db` rejects a wider one. |
| `structure` | Required. |
| `addressStruct`, `wordLines` | Required for `regType: memory`. `wordLines` is a literal or a constant. |
| `desc` | Required. |
| `defaultValue` | Reset value. Default `0`. |
| `offset` | Manual offset. Default `0`, auto-assigned. |

### Memories (`memories:`)

| Field | Meaning |
| :--- | :--- |
| `memory` | Required. Name. |
| `block` | Required. Owner block. |
| `structure`, `addressStruct` | Required. |
| `wordLines` | Required. Depth, a number or a constant. |
| `desc` | Required. |
| `regAccess` | Firmware access through the register handler: `false`, `rw`, `ro` (firmware only reads) or `wo` (firmware only writes). `true` means `rw`. Default `false`. |
| `local` | Flops instead of SRAM. Default `false`. |
| `memoryType` | What each port can do. `singlePort` has one read/write port. `dualPort` (the default) has two read/write ports, A and B. `portRportRW` has a read-only A and a read/write B. `portRWportW` has a read/write A and a write-only B. `portRportW` has a read-only A and a write-only B. `register` behaves as `singlePort`. |
| `ports` | Block-side port names, filling A then B. With `regAccess` the register handler takes one port, so a dual-port memory lists at most one and a `singlePort` memory lists none. With `regAccess`, no port may be named `reg`. |
| `clock` | One of the owning block's clocks, which the block-side port runs on. The register handler's port always runs on the register clock. Default: the block's default clock. |

A memory has no `reset:`, and setting one is an error.

```yaml
registers:
  - {register: config, block: dma_controller, regType: rw, structure: dma_config_t, desc: "Config"}

memories:
  - {memory: buffer, block: dma_controller, structure: buffer_data_t, addressStruct: buffer_addr_t, wordLines: 1024, desc: "Internal RAM", regAccess: true}
```

### Memory connections (`memoryConnections:`)

A memory connection gives an instance access to one block-side port of a memory. `block` is the memory's owner and `port` is one of the memory's `ports:`. The accessor `instance` must be a sibling of an instance of the owning block, or a child inside the owning block.

```yaml
memoryConnections:
  - {memory: blockBTable1, block: blockB, instance: uBlockD, port: port1}
```

### Register connections (`registerConnections:`)

A register connection wires a register the container owns to one of its child instances. The child reads an `rw` register and drives an `ro` register. An `ext` or `memory` register reaches the child as a `dst` port, as `rw` does.

```yaml
registerConnections:
  - {register: rwD, block: blockB, instance: uBlockF0}
```

## 7. Clocks and resets

A block declares its clocks and resets completely. Nothing is inferred from its connections or its children, so a container whose children use two clocks declares both itself. `clocks:` and `resets:` are maps keyed by port name:

```yaml
blocks:
  uart:
    desc: "UART with a generated baud clock"
    clocks:
      clk:     { desc: "register and datapath clock" }   # sole input, so the default
      baudClk: { desc: "generated baud clock", direction: output }
    resets:
      rst_n:   { desc: "datapath reset", clock: clk }    # baudClk has no reset
```

*   `direction` is `input` (the default) or `output`.
*   On a clock, `default: true` marks the block default clock. A block with one input clock does not need it. On a reset, `default: true` marks the selected reset of its clock. A clock with one candidate reset does not need it.
*   A reset's `clock:` defaults to the block default clock. `resets: {}` means the block has no reset.
*   `async: true` marks a reset input that the block samples in none of its own clocks, such as a synchroniser's raw input. It may bind to any container reset.
*   `period` and `timeUnit` (`ps`, `ns` or `us`) on an input clock set the rate for a standalone build of the block. A declared `period` wins. Without one, the clock takes the period of the testbench clock that every instance of the block resolves it to. A `hasVl` block must declare `period` when its clock comes from another block's output, resolves to two testbench clocks, or has no instance in its own project. An odd `period` in `ps` is rejected.

### Instance binding

An instance's `clocks:`/`resets:` map is `<block port>: <container net>`. Each input is bound by the first rule that applies:

1.  The instance map.
2.  A container net of the same name.
3.  For `clk` only, the container's default clock.
4.  For `rst_n` only, the container's selected reset on the clock net that the child's `rst_n` clock is bound to. If the child binds its `clk` to the container's `clkSlow`, `rst_n` binds to the selected reset of `clkSlow`, not the container default reset.

Any other unbound input is an error. Every `output` must appear in the map, bound to a net or to `~` to leave it unconnected. A name match never binds an output.

```yaml
instances:
  uSlowTick: { container: twoClk, instanceType: twoClkSlowTick,
               clocks: { clkTick: clkSlow }, resets: { rstTick_n: rstSlow_n } }
```

### Local nets and exports

Binding a child's `output` to a name the container does not declare creates a local net. The child drives it, and at least one input inside the container must consume it by name. Binding a child's `output` to an `output` the container declares exports it. In `examples/clkGen/yaml/clkGen.yaml`, `uDivider`'s `rstDivRaw_n` is a local net of `clkGen`, and `uDivider`'s `clkDiv` is exported through `clkGen`'s own `clkDiv` output.

### Port domains

*   A port that a block does not declare in `ports:` takes its domain from the connection that reaches it. A connection's `clock:` names a container clock, and each end must have exactly one input clock bound to that net. Without `clock:`, each end sits on its own block's default clock.

    ```yaml
    connections:
      # both instances bind one input clock to the container's clkSlow
      - {interface: tick_if, src: u_slowSrc, dst: u_slow, clock: clkSlow}
    ```

*   A block can fix a port's domain itself with `clock:` on a `ports:` or `registerPorts:` row, naming one of its own clocks. A connection `clock:` that reaches such a port must agree with it.
*   `connectionMaps:`, `memoryConnections:` and `registerConnections:` have no `clock:` field. Their domains come from the ports they reach.

### Register bus clock

*   A router's bus clock and reset are its `addressBlock:` `clock:` and `reset:`. Without them, they are the router's default clock and that clock's selected reset. The bus clock needs a synchronous input reset. A router declares at most one clock.
*   A leaf with `registerPorts:` runs its register port and handler on that row's `clock:`, which defaults to the block's default clock. Every instance must bind that clock to the serving router's bus clock. A `registerPorts:` `reset:` must likewise bind to the router's bus reset. Without `reset:`, the port uses the selected reset of its register clock, and `make db` does not check that it binds to the router's bus reset. State `reset:` when the two can differ.
*   A leaf without `registerPorts:` takes its reset from the reset port bound to the router's bus reset, and runs on that reset's clock. Every instance of the block must agree.

### Clock crossings

The generator does not synchronise, report or reject a connection between two container clocks. Crossings are the designer's job. Memories have fixed rules:
*   A `memoryConnections:` accessor must run on the memory's clock: its default clock must be bound to the net the memory's clock is on.
*   A `regAccess` memory may have its block-side port on another clock than the register bus, so a dual-port memory crosses inside the RAM. A `singlePort` or `local: true` memory with `regAccess` must be on the register clock. See `design-register-decode.md`.

### The testbench

The project file's `clocks:`/`resets:` are the testbench and bind the top block's inputs. See `setup-project.md`.

## 8. Names inside one block

A block's generated module and class hold its clocks, resets, ports, registers, memories, child instances and the channels of connections between its children in one scope. `make db` rejects two of them with the same name.

*   A connection's channel is named by `interfaceName:`, else `srcport:`, else `name:`, else the interface name.
*   A memory's channels are `<memory>_<port>` for a port wired to a child, and `<memory>_reg` for a `regAccess` memory.
*   Registers, connection map ports, memory channels and connection channels may not share a name.
*   Connections of one interface that share a channel name are numbered, so that shared name may also match a child instance, a memory, or a port that is not a connection map port. Connections of different interfaces may not share a channel name.
*   Wire each memory port to one instance.

## Validation
Run `make db` to parse and validate. Errors the sections above do not cover:
*   `regAccess: rw` on `portRportW`, which has no read/write port. Use `ro`, `wo` or another `memoryType`.
*   Nesting `instances` inside `blocks`.
