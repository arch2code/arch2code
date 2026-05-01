---
name: design-architecture
description: Guide for defining hardware architecture in YAML including blocks, instances, interfaces, connections, registers, and memories
---
# Skill: Design Architecture

## Purpose
Guide the user in defining the hardware architecture using YAML. This includes defining Blocks, Instances, Interfaces, Connections, Registers, and Data Types, adhering strictly to the Arch2Code relational schema.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See sections "Low-Level Architecture Elements", "Interfaces", "Blocks & Instances", "Connections")

## Instructions

1.  **File Structure:**
    *   **Root Keys:** `include`, `ipParameters`, `constants`, `types`, `structures`, `interfaces`, `blocks`, `instances`, `connections`, `connectionMaps`, `registers`, `memories`, `parameters`.
    *   **Philosophy:** The YAML structure is **relational**. Elements are linked by keys (e.g., `container`, `block`, `src`, `dst`).
    *   **Defaults:** Many fields are optional with sensible defaults (e.g., `hasRtl` defaults to `true`).

2.  **Constants (`constants` dictionary):**
    *   **Properties:**
        *   `value`: Literal integer value. **Use `value` OR `eval`, not both.**
        *   `eval`: Python expression string. Reference other constants with `$NAME`.
        *   `maxValue`: Worst-case value for parameterizable constants.
        *   `desc`: **(Required)** Description.

    ```yaml
    constants:
      BUFFER_SIZE: {value: 1024, desc: "Buffer size"}
      ADDR_WIDTH: {eval: '($BUFFER_SIZE-1).bit_length()', desc: "Address bits"}
      IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
    ```

    *   `maxValue` is required for direct parameterizable constants. If an `eval` references a parameterizable constant, `maxValue` is auto-derived and should not be hand-written.

3.  **Types (`types` dictionary):**
    *   **Properties:**
        *   `width`: **(Required for non-enum types)** Bit width (number or constant).
        *   `widthLog2` / `widthLog2minus1`: Alternatives for address/index widths.
        *   `maxBitwidth`: Worst-case bit width for direct parameterizable types.
        *   `desc`: **(Required)** Description.
        *   `enum`: (Optional) List of enum values. Width is auto-calculated for enums.

    ```yaml
    types:
      byte_t: {width: 8, desc: "8-bit byte"}
      addr_t: {width: ADDR_WIDTH, desc: "Address type"}
      ip_data_t: {width: IP_DATA_WIDTH, desc: "Parameterized width type"}
      ip_literal_t: {width: 8, maxBitwidth: 16, desc: "Literal-width parameterized type"}
      status_t:
        desc: "Status enum"
        enum:
          - {enumName: STATUS_IDLE, value: 0, desc: "Idle"}
          - {enumName: STATUS_BUSY, value: 1, desc: "Busy"}
    ```

    *   `maxBitwidth` is required for direct parameterizable types unless the width expression references a parameterizable constant.

4.  **Structures (`structures` dictionary):**
    *   Each key is a field name. Fields are ordered as defined.
    *   **Field Properties:**
        *   `varType`: **(Required)** Type name from `types`.
        *   `subStruct`: Alternative to `varType` for nested structures.
        *   `desc`: **(Required)** Description.
        *   `arraySize`: (Optional) Array size. **Default: `1`**
        *   `generator`: (Optional) e.g., `tracker(trackerName)` for debug integration.
        *   `local`: (Optional) Field is local to model, not in RTL. **Default: `false`**

    ```yaml
    structures:
      packet_t:
        data: {varType: byte_t, desc: "Payload"}
        valid: {varType: bit_t, desc: "Valid flag"}
        tag: {varType: tag_t, generator: tracker(cmdTag), desc: "Tracker tag"}
      ip_burst_t:
        samples: {varType: ip_data_t, arraySize: IP_MEM_DEPTH, desc: "Parameterized burst"}
    ```

    *   Structure `isParameterizable` and `maxBitwidth` are generated metadata derived from fields and `arraySize` constants; do not write them manually.

5.  **Parameterizable IP Parameters (`ipParameters` dictionary):**

    *   Use `ipParameters` in the IP-root YAML for constants and types that vary by instance/variant.
    *   Direct constants require `maxValue`; direct literal-width types require `maxBitwidth`.
    *   Derived constants/types inherit worst-case bounds from referenced parameterizable constants.
    *   Do not place `ipParameters` in shared include files that only contain common constants/types/structures.

    ```yaml
    ipParameters:
      constants:
        IP_DATA_WIDTH: {value: 8, maxValue: 16, desc: "Per-instance data width"}
        IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}
      types:
        ip_data_t: {width: IP_DATA_WIDTH, desc: "IP data word"}
    ```

6.  **Block Definition (`blocks` dictionary):**

    *   **Properties:**
        *   `desc`: **(Required)** Description string.
        *   `hasRtl`: (Optional) Generate RTL skeleton. **Default: `true`**
        *   `hasMdl`: (Optional) Generate SystemC model. **Default: `true`**
        *   `hasVl`: (Optional) Generate Verilator wrapper. **Default: `false`**
        *   `hasTb`: (Optional) Generate Testbench. **Default: `false`**
        *   `params`: (Optional) Block parameters bound by variants in `parameters:`.

    ```yaml
    blocks:
      dma_controller:
        desc: "DMA Controller"
        # hasRtl: true (default)
        # hasMdl: true (default)
        hasVl: true    # Override default
      ip:
        desc: "Parameterized IP"
        params: [IP_DATA_WIDTH, IP_MEM_DEPTH, IP_NONCONST_DEPTH]
    ```

7.  **Instance Definition (`instances` dictionary):**
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

8.  **Interface Definition (`interfaces` dictionary):**
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

9.  **Connections (`connections` list):**
    *   **Properties:**
        *   `interface`: **(Required)** Interface name defined in `interfaces`.
        *   `src`: **(Required)** Source instance.
        *   `dst`: **(Required)** Destination instance.
        *   `name`: (Optional) Disambiguation name if multiple connections exist.
        *   `srcport` / `dstport`: (Optional) Override port names.
        *   `interfaceName`: (Optional) Override channel instance name.

    ```yaml
    connections:
      - {interface: dma_req_if, src: u_dma, dst: u_mem_ctrl}
      - {interface: dma_req_if, src: u_dma, dst: u_periph, name: "periph_req"}
    ```

10. **Connection Maps (`connectionMaps` list):**
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

11. **Registers (`registers` list):**
    *   **Properties:**
        *   `register`: **(Required)** Name.
        *   `block`: **(Required)** Owner block.
        *   `regType`: **(Required)** `rw` (Read/Write), `ro` (Read-Only), `ext` (External), or `memory`.
        *   `structure`: **(Required)** Data structure.
        *   `addressStruct`: Required for `regType: memory`.
        *   `wordLines`: Required for `regType: memory`; may be literal, constant, `ipParameters` constant, or pure block param.
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

    *   Parameterizable registers use worst-case structure width for address allocation. Generated metadata such as `isParameterizable` and `maxBytes` is internal.

12. **Memories (`memories` list):**
    *   **Properties:**
        *   `memory`: **(Required)** Name.
        *   `block`: **(Required)** Owner block.
        *   `structure`: **(Required)** Data structure.
        *   `addressStruct`: **(Required)** Address structure.
        *   `wordLines`: **(Required)** Depth (number, constant, `ipParameters` constant, or pure block param).
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

    *   If the memory structure or `wordLines` is parameterizable, address allocation uses worst-case sizing (`maxBitwidth`, `maxValue`, or the maximum variant-bound value).

13. **Parameter Bindings (`parameters` dictionary):**

    ```yaml
    parameters:
      ip:
        - {variant: variant0, param: IP_DATA_WIDTH, value: 8}
        - {variant: variant0, param: IP_NONCONST_DEPTH, value: 24}
        - {variant: variant1, param: IP_DATA_WIDTH, value: 12}
        - {variant: variant1, param: IP_NONCONST_DEPTH, value: 12}
    ```

## Validation
*   **Syntax Check:** Run `make db` to parse and validate.
*   **Common Errors:**
    *   Missing `desc` (Required everywhere).
    *   Missing `addressStruct` in memories (Required).
    *   Assuming `regAccess` is true (Default is `false`).
    *   Nesting `instances` inside `blocks`.
