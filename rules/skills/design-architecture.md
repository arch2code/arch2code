---
name: design-architecture
description: Guide for defining regular arch2code YAML architecture including blocks, instances, interfaces, connections, connectionMaps, registers, and memories. Use for non-parameterized architecture wiring and general block hierarchy.
---
# Skill: Design Architecture

## Purpose
Guide the user in defining regular hardware architecture using arch2code YAML. This includes blocks, instances, interfaces, connections, connectionMaps, registers, and memories. For constants, types, and structures, use `design-types-structures.md`. For parameterizable blocks, variants, `ipParameters`, and per-port parameters, use `design-parameterizable-blocks.md`.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See sections "Low-Level Architecture Elements", "Interfaces", "Blocks & Instances", "Connections")

## Instructions

1.  **File Structure:**
    *   **Root Keys:** `include`, `constants`, `types`, `structures`, `interfaces`, `blocks`, `instances`, `connections`, `connectionMaps`, `registers`, `memories`.
    *   **Philosophy:** The YAML structure is **relational**. Elements are linked by keys (e.g., `container`, `block`, `src`, `dst`).
    *   **Defaults:** Many fields are optional with sensible defaults (e.g., `hasRtl` defaults to `true`).

2.  **Block Definition (`blocks` dictionary):**

    *   **Properties:**
        *   `desc`: **(Required)** Description string.
        *   `hasRtl`: (Optional) Generate RTL skeleton. **Default: `true`**
        *   `hasMdl`: (Optional) Generate SystemC model. **Default: `true`**
        *   `hasVl`: (Optional) Generate Verilator wrapper. **Default: `false`**
        *   `hasTb`: (Optional) Generate Testbench. **Default: `false`**
        *   `ports`: (Optional) Explicit port map keyed by port name. Each entry names an `interface` and `direction`.
        *   `addressBlock`: (Optional) Marks the block as a **register-bus router (decoder)**. Its RTL is generated from the `apbDecodeModule` template. Fields: `addressGroup` (the group this router serves), `addressIncrement`, `maxAddressSpaces`, `varType`, `enumPrefix`, `upstreamPort` (the addressBus interface feeding it), `registerDecoderPort` (canonical downstream register-bus port). A router must **not** also declare `registerPorts:`.
        *   `registerPorts`: (Optional, **reusable-IP leaves only**) Exactly one row declaring the block's own register-bus port, e.g. `registerPorts: { regs: { interface: ipReg } }`. Lets a reusable IP carry a self-contained register-bus surface. Plain top-down leaves omit it (they infer the bus from the serving router).
        *   `clocks`: (Optional) The block's clock ports, keyed by name: `{desc, direction, default, period, timeUnit}`. A block that declares none gets one implicit input clock, `clk`. See **Clocks and Resets** below.
        *   `resets`: (Optional) The block's reset ports, keyed by name: `{desc, direction, default, clock, async}`. A block that declares none, and has a default clock, gets one implicit reset, `rst_n`, on it; an explicit `resets: {}` means the block has no reset at all.
    *   **RTL hierarchy rule:** If a block has `hasRtl: true`, every block it instantiates must also have `hasRtl: true`. A model-only subblock (`hasRtl: false`) is only valid under a model-only parent.
    *   **Decode-position rule (registers/memories):** A block that owns `registers` or `regAccess: true` memories (or `registerPorts:`) is a *routed leaf* and must be served by a decoder in the **same container** (a sibling router) or by a parent decoder (the block is then a routed leaf of that parent). A router never decodes its own container block. A **container block MAY own registers** — provided none of its contained leaves needs its own decode block — and forwards them to children via `registerConnections`. For the full decision rule, nested routers, the upstream feed, and worked examples, use the **Register/Memory Decode** skill (`design-register-decode.md`).
    *   **File placement:** A block's generated files (`base/`, `model/`, `rtl/`, `tb/`, `verif/vl_wrap/`) are placed in a subdirectory that mirrors the location of the YAML file defining the block, relative to `arch/yaml/`. This is automatic — do not set `blockDir:`/`dir:` to reproduce it. A top-level `blockDir:` (whole file) or per-block `dir:` field overrides this only for genuine exceptions. See `setup-project.md` (Directory Mirroring).

    ```yaml
    blocks:
      dma_controller:
        desc: "DMA Controller"
        # hasRtl: true (default)
        # hasMdl: true (default)
        hasVl: true    # Override default
      stream_filter:
        desc: "Filter with explicit ports"
        ports:
          in_data:  {interface: stream_if, direction: dst}
          out_data: {interface: stream_if, direction: src}
    ```

3.  **Instance Definition (`instances` dictionary):**
    *   **Properties:**
        *   `container`: **(Required)** Parent block name (or `top`).
        *   `instanceType`: **(Required)** Block definition to instantiate.
        *   `addressGroup`: **(Required if Regs exist)** Address space group (e.g., `system`).

    ```yaml
    instances:
      u_dma:
        container: top
        instanceType: dma_controller
        addressGroup: system
    ```

4.  **Interface Definition (`interfaces` dictionary):**
    *   **Properties:**
        *   `interfaceType`: **(Required)** Protocol (e.g., `apb`, `req_ack`).
        *   `desc`: **(Required)** Description.
        *   `structures`: **(Required)** List mapping structures to interface data types.
        *   `maxTransferSize`: (Optional) For multi-cycle interfaces. **Default: `0`**

    ```yaml
    interfaces:
      dma_req_if:
        interfaceType: req_ack
        desc: "DMA Request"
        structures:
          - {structureType: data_t, structure: dma_req_t}
    ```

5.  **Connections (`connections` list):**
    *   **Properties:**
        *   `interface`: **(Required)** Interface name defined in `interfaces`.
        *   `src`: **(Required)** Source instance.
        *   `dst`: **(Required)** Destination instance.
        *   `name`: (Optional) Disambiguation name if multiple connections exist.
        *   `srcport` / `dstport`: (Optional) Override port names.
        *   `interfaceName`: (Optional) Override channel instance name.
        *   `clock`: (Optional) Container clock both ends of this wire run on. **Default: the block default clock of each end.** Declared only on `connections:`; `connectionMaps:`, `memoryConnections:`, and `registerConnections:` carry no `clock:` because their domains derive from the ports they reach. See **Clocks and Resets** below.

    ```yaml
    connections:
      - {interface: dma_req_if, src: u_dma, dst: u_mem_ctrl}
      - {interface: dma_req_if, src: u_dma, dst: u_periph, name: "periph_req"}
      - {interface: dma_req_if, src: u_dma, dst: u_slow, clock: clkSlow}
    ```

    ### Clocks and Resets
    *   **A block declares its clocks and resets completely.** Nothing is inferred from its connections or its children; a container whose children use two clocks declares both itself. `clocks:`/`resets:` are keyed maps, not references to anything outside the block:

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

    *   `direction` is `input` (default) or `output`. `default: true` marks the block default clock (implied with one input clock) and, on a reset, that clock's **selected reset** (implied with one candidate). `period`/`timeUnit` on an input clock set the rate a *standalone* simulation of the block uses when nothing else determines one; an assembled design never reads them. `async: true` on a reset marks an input the block samples in none of its own clocks, such as a synchroniser's raw input; it may bind to any container reset.
    *   **Instances bind by map.** An instance's `clocks:`/`resets:` mapping is `<block port>: <container net>`. An input entry the map omits binds to the container net of the same name, or, for the reserved names `clk`/`rst_n` only, to the container's default clock and its selected reset when the container has no net of that name. Every `output` entry must appear in the map, bound to a container net or to `~` to leave it unconnected — a name match never creates a supplier:

    ```yaml
    instances:
      uSlowTick: { container: twoClk, instanceType: twoClkSlowTick,
                   clocks: { clkTick: clkSlow }, resets: { rstTick_n: rstSlow_n } }
    ```

    *   **Local nets.** Binding a child's `output` to a name the container has not declared creates a local net, driven by that child and consumed by name inside the container (at least one input must consume it). `clkDiv`/`rstDivRaw_n` in `examples/clkGen/yaml/clkGen.yaml` are local nets of `clkGen` until `clkGen` re-declares `clkDiv` as its own `output` and `uDivider`'s map binds `clkDiv` onto it — that binding is the export.
    *   **A top-down port's domain is authored on the connection.** A block with no `ports:` gets each port's domain from the connection reaching it: `clock:` on `connections:` names a container clock and states the domain of both ends, so such a connection is never a crossing. Left unstated, a port sits on its block's default clock, mapped through the instance.
    *   **`ports:`/`registerPorts:` `clock:`** is how a reusable IP or parameterized block declares a port's domain instead, naming one of the block's own clocks (`clock: baudClk`). Where a port is both declared this way and reached by a connection carrying `clock:`, the two must agree. `connectionMaps:`, `memoryConnections:`, and `registerConnections:` carry no `clock:` field of their own; their domains derive from the ports they reach.
    *   **Register decode** follows the bus: a router's domain is its `addressBlock:` `clock:`, else its feed connection's, else the block default; the handler it serves runs on the same clock. A top-down leaf's register port takes whichever of its own declared clocks the instance map binds to that bus clock (R25) — see `design-register-decode.md`.
    *   **Crossings are the designer's responsibility.** The generator neither rejects, reports, nor synchronises a connection between two container clocks. A memory reached by more than one clock, and a register bus reached from two clocks, are rejected for `memoryConnections:` accessors. Firmware access through the generated handler is the exception: it may come from another domain, and the handler bridges it (see `design-register-decode.md` §4).
    *   **The project file is the testbench**, not a namespace design YAML references. Its `clocks:`/`resets:` bind the top block's inputs by name; a `period` defaults to 1 ns. See `setup-project.md`.

6.  **Connection Maps (`connectionMaps` list):**
    *   **Properties:**
        *   `interface`: **(Required)** Interface name.
        *   `block`: **(Required)** Parent block (boundary).
        *   `direction`: **(Required)** `src` or `dst`.
        *   `instance`: **(Required)** Internal instance to route to.
        *   `port`: (Optional) Must match `srcport`/`dstport` if used in connection.

    ```yaml
    connectionMaps:
      - {interface: dma_req_if, block: top, direction: src, instance: u_dma}
    ```

7.  **Registers (`registers` list):**
    *   **Properties:**
        *   `register`: **(Required)** Name.
        *   `block`: **(Required)** Owner block.
        *   `regType`: **(Required)** `rw` (Read/Write), `ro` (Read-Only), `ext` (External), or `memory`.
        *   `structure`: **(Required)** Data structure.
        *   `addressStruct`: Required for `regType: memory`.
        *   `wordLines`: Required for `regType: memory`; may be a literal or constant. For parameterized sizing, use `design-parameterizable-blocks.md`.
        *   `desc`: **(Required)** Description.
        *   `defaultValue`: (Optional) Reset value. **Default: `0`**
        *   `offset`: (Optional) Manual offset. **Default: `0` (Auto-assigned)**

    ```yaml
    registers:
      - register: config
        block: dma_controller
        regType: rw
        structure: dma_config_t
        desc: "Config"
    ```

8.  **Memories (`memories` list):**
    *   **Properties:**
        *   `memory`: **(Required)** Name.
        *   `block`: **(Required)** Owner block.
        *   `structure`: **(Required)** Data structure.
        *   `addressStruct`: **(Required)** Address structure.
        *   `wordLines`: **(Required)** Depth as a number or constant. For parameterized depth, use `design-parameterizable-blocks.md`.
        *   `desc`: **(Required)** Description.
        *   `regAccess`: (Optional) FW accessible? **Default: `false`**
        *   `local`: (Optional) Local flops (not SRAM)? **Default: `false`**
        *   `memoryType`: (Optional) `singlePort`, `dualPort`. **Default: `dualPort`**

    ```yaml
    memories:
      - memory: buffer
        block: dma_controller
        structure: buffer_data_t
        addressStruct: buffer_addr_t
        wordLines: 1024
        desc: "Internal RAM"
        regAccess: true  # FW accessible
        memoryType: singlePort
    ```

## Validation
*   **Syntax Check:** Run `make db` to parse and validate.
*   **Common Errors:**
    *   Missing `desc` (Required everywhere).
    *   Missing `addressStruct` in memories (Required).
    *   Assuming `regAccess` is true (Default is `false`).
    *   Nesting `instances` inside `blocks`.
    *   Placing a `hasRtl: false` block inside a `hasRtl: true` parent. Either generate RTL for the child or make the parent model-only.
