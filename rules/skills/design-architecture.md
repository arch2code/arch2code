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
        *   `clocks`: (Optional) List of project clock names the block carries **in addition to** those its connections imply. Use it for a block whose logic runs in a domain no connection reaches (a free-running counter, a block with no ports). See **Clocks and Resets** below.
        *   `resets`: (Optional) The block's **complete** reset list. When absent the block takes one project reset per clock it carries. Every listed reset must be declared on a clock the block carries, and every carried clock must have a reset in the list.
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
        *   `clock`: (Optional) Project clock this wire runs in. **Default: the project's default clock.** Both endpoint blocks then carry that clock. Also accepted on `connectionMaps`, `memoryConnections`, and `registerConnections`.

    ```yaml
    connections:
      - {interface: dma_req_if, src: u_dma, dst: u_mem_ctrl}
      - {interface: dma_req_if, src: u_dma, dst: u_periph, name: "periph_req"}
      - {interface: dma_req_if, src: u_dma, dst: u_slow, clock: clkSlow}
    ```

    ### Clocks and Resets
    *   Clocks and resets are **declared in `project.yaml`** (`clocks:` / `resets:`, see `setup-project.md`), never in design YAML. A project that declares neither gets a built-in `clk` (1 ns) and active-low `rst_n`, so existing projects build unchanged.
    *   **A clock belongs to a connection.** Set `clock:` on the connection; both endpoint blocks carry that clock. A block's clock set is the union of its connections' clocks, its own `clocks:` list, and every child's clocks. A leaf with no connections and no `clocks:` list takes the default clock.
    *   **A reset belongs to a block** and is released on the clock it is declared with. A block with no `resets:` list takes one project reset per clock it carries, so every clock a block declares has a matching reset.
    *   **Emitted ports.** Every generated module, wrapper, and register handler declares exactly the block's clocks then resets, in project declaration order with the default first. A container binds each child's clock and reset ports to its own signal for the same domain, so the container carries every domain its children do.
    *   **Register decode** follows the bus: a generated router and `<block>Regs` handler run on the clock of the register-bus feed reaching the router. A router must resolve to exactly one clock; a `clocks:` entry, child instance, or connection that adds a second domain to it is rejected.
    *   **Crossings are the designer's responsibility.** The generator neither rejects, reports, nor synchronises a connection between blocks in different domains. A memory reached from two clocks, and a register bus reached from two clocks, are rejected.
    *   **Hand-written RTL** uses the bare `` `DFF `` family in any domain. When a block carries no clock named `clk` or no reset named `rst_n`, its generated region declares `wire clk = <first clock>;` / `wire rst_n = <first reset>;`, so the bare macros land on the block's first clock. The explicit `_CLK` family (`` `DFF_CLK(clkSlow, q, d) ``, `` `DFF_INST_CLK(clkSlow, type, name) ``) is needed only to place a flop on a second clock of a multi-clock block. See `rtl-core.md`.
    *   **Composition.** Clock names are per project. A child IP's clock resolves in the child's own project; the assembler drives the child's clock port from its own clock of the same name, or its default clock when it declares none of that name. The child's declared `period` therefore governs only its standalone co-simulation wrapper.

    ```yaml
    blocks:
      slow_counter:
        desc: "Free-running counter with no ports, wholly in clkSlow"
        clocks: [clkSlow]
        resets: [rstSlow_n]
    ```

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
