---
name: manage-address-space
description: Guide for configuring address maps, address groups, address-policy sections, and firmware header generation using addressControl.yaml and project.yaml
---
# Skill: Manage Address Space

## Purpose
Guide the user in configuring the project's address map, managing address groups, moving reusable address-policy sections into `project.yaml`, and setting up firmware header generation.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Registers & Address Management" and "Address Control File")

## Instructions

1.  **Address Configuration Sources:**
    *   Legacy projects keep address decode policy in `addressControl.yaml`, typically at `arch/yaml/config/addressControl.yaml`.
    *   The legacy `addressControl.yaml` path is supported during migration but is expected to be deprecated; prefer the new `project.yaml` and per-block schema for new work.
    *   New and migrated projects should put reusable address-policy sections in top-level `project.yaml` fields:
        *   `instanceGroups:` replaces legacy `InstanceGroups:`.
        *   `addressObjects:` replaces legacy `AddressObjects:`.
    *   `AddressGroups:` and `RegisterBusInterface:` still belong to the legacy `addressControl.yaml` path until the per-block `addressBlock:` / `registerPorts:` migration is complete.

2.  **Defining Address Groups (`AddressGroups`):**
    *   Address groups define hierarchical address spaces.
    *   **Top-Level Group:** Must have `primaryDecode: true` and define the `decoderInstance` that routes the system bus.
    *   **Sub-Groups:** Define regions for subsystems.

    ```yaml
    AddressGroups:
      system:
        addressIncrement: 0x01000000  # 16MB per block in this group
        maxAddressSpaces: 16
        varType: system_addr_id_t
        enumPrefix: SYSTEM_ADDR_
        decoderInstance: u_apb_decode_system  # CRITICAL: References your manual top-level decoder
        primaryDecode: true
    ```

3.  **Connecting the Decoder (`decoderInstance`):**
    *   The `decoderInstance` field **must** reference a valid instance in your architecture YAML.
    *   This instance (e.g., `u_apb_decode_system`) corresponds to the manual top-level decoder you created to route the register bus.

4.  **Instance Groups (`instanceGroups:` / legacy `InstanceGroups:`):**
    *   Used for ID enumeration without address space implications (e.g., for error reporting IDs).
    *   Prefer top-level `project.yaml` spelling for new work. The row body is unchanged from legacy `InstanceGroups:`.

    ```yaml
    # In project.yaml
    instanceGroups:
      all_instances:
        varType: global_inst_id_t
        enumPrefix: GID_
    ```

5.  **Firmware Header Generation (`includeFW`):**
    *   To generate C/C++ header files for firmware, configure `fileGeneration` in `project.yaml`.
    *   **Configuration:**
        *   `smartInclude: true`: Only generate files if content (regs/mem) exists.
        *   `mode: context`: Generate one header per YAML file.
        *   `basePath`: Directory to output headers.

    ```yaml
    # In project.yaml
    fileGeneration:
      fileMap:
        includeFW:
          name: "IncludesFW"
          ext: {hdr: "h", src: "cpp"}
          cond: {smartInclude: true}
          mode: context
          basePath: fwInc  # defined in dirs section
          desc: "Firmware include file"
    ```

6.  **Address Object Sorting (`addressObjects:` / legacy `AddressObjects:`):**
    *   Control how objects are packed in the address space using `AddressObjects`.
    *   **Best Practice:** Sort memories by size (`memsize` alignment) to optimize decoding.
    *   Prefer top-level `project.yaml` spelling for new work. The row body is unchanged from legacy `AddressObjects:`.

    ```yaml
    # In project.yaml
    addressObjects:
      memories:
        alignment: memsize
        sizeRoundUpPowerOf2: true
        sortDescending: true
      registers:
        alignment: 8
        sortDescending: true
    ```

    If a project carries both `project.yaml` and legacy
    `addressControl.yaml` spellings, the rows must match exactly.
    Disagreement is a configuration error.

7.  **Parameterizable Register/Memory Sizing:**
    *   Register and firmware-accessible memory offsets are allocated from worst-case sizes when the referenced structure or `wordLines` is parameterizable.
    *   Structure width uses generated `maxBitwidth`; `wordLines` uses a parameterizable constant's `maxValue` or the maximum value bound in `parameters:` for pure block params.
    *   YAML authors should provide explicit bounds (`maxValue` for constants, `maxBitwidth` for literal-width types) so the address map reserves enough space for every variant.

    ```yaml
    ipParameters:
      constants:
        IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}

    blocks:
      ip:
        desc: "Parameterized IP"
        params: [IP_MEM_DEPTH, IP_NONCONST_DEPTH]

    memories:
      - memory: ip_mem
        block: ip
        structure: ip_data_st
        addressStruct: ip_mem_addr_st
        wordLines: IP_MEM_DEPTH   # Address sizing uses maxValue=32
        regAccess: true
        desc: "Parameterized memory"
      - memory: ip_variant_mem
        block: ip
        structure: ip_data_st
        addressStruct: ip_mem_addr_st
        wordLines: IP_NONCONST_DEPTH  # Uses max variant binding
        regAccess: true
        desc: "Pure block-param memory depth"
    ```
