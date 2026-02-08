# Skill: Manage Address Space

## Purpose
Guide the user in configuring the project's address map, managing address groups, and setting up firmware header generation using `addressControl.yaml` and `project.yaml`.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Registers & Address Management" and "Address Control File")

## Instructions

1.  **Address Control File (`addressControl.yaml`):**
    *   This file is central to the project's memory map.
    *   **Location:** Typically `arch/yaml/config/addressControl.yaml`.
    *   **Key Sections:** `AddressGroups`, `InstanceGroups`, `AddressObjects`, `RegisterBusInterface`.

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

4.  **Instance Groups (`InstanceGroups`):**
    *   Used for ID enumeration without address space implications (e.g., for error reporting IDs).

    ```yaml
    InstanceGroups:
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

6.  **Address Object Sorting:**
    *   Control how objects are packed in the address space using `AddressObjects`.
    *   **Best Practice:** Sort memories by size (`memsize` alignment) to optimize decoding.

    ```yaml
    AddressObjects:
      memories:
        alignment: memsize
        sizeRoundUpPowerOf2: true
        sortDescending: true
      registers:
        alignment: 8
        sortDescending: true
    ```
