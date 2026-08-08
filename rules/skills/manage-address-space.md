---
name: manage-address-space
description: Guide for configuring address-policy sections (instance groups, address-object packing) and firmware header generation in project.yaml
---
# Skill: Manage Address Space

## Purpose
Guide the user in configuring the project's address **policy** (instance groups,
address-object sorting/alignment) and setting up firmware header generation.

For the **decode hierarchy** itself — where registers/memories live, declaring
the generated `addressBlock:` router, routed leaves, nested routers, and the one
upstream feed you author — use the **Register/Memory Decode** skill
(`design-register-decode.md`). The router is a generated block; you never
hand-create a top-level decoder.

## References
*   **Decode hierarchy:** `design-register-decode.md` (router/leaf model, `regAccess`)
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Registers & Address Management" and "Address Policy and Address Control")

## Instructions

1.  **Address Configuration Sources:**
    *   Address-policy sections live in top-level `project.yaml`:
        *   `instanceGroups:` — ID enumeration (see step 4).
        *   `addressObjects:` — register/memory packing policy (see step 6).
    *   The decode hierarchy is declared per-block: routers carry `addressBlock:` and reusable-IP leaves carry `registerPorts:`. There is no project-wide address-decode file to author. See `design-register-decode.md`.
    *   Converting a pre-existing `addressControl.yaml` project to this schema is a one-time migration handled entirely by `migrate-project.md` / `address-migration.md`.

2.  **Address groups (per-block schema):**
    *   An address group is named by a router block's `addressBlock.addressGroup`; routed leaves select it via their instance `addressGroup:`. The router block defines the group and its RTL is generated (`apbDecodeModule`); the primary router is inferred by hierarchy walk. There is no `decoderInstance:`/`primaryDecode:` to author.
    *   Multi-level decode uses **nested routers** (a second `addressBlock:` block inside a container that is itself a routed leaf of the parent). See `design-register-decode.md`.
    *   **A group name is owned by the project that declares it.** An `addressGroup:` reference resolves only within the project owning the referring YAML file; it never falls outward to a parent or sibling project. Two independently authored projects may therefore each declare a group named `top` and compose cleanly, but a reusable IP must declare every group it references — an IP naming a group its own project does not declare has hard-coded a name its parent owns. Within one project, at most one router block may declare a given group name. Both violations are hard `make db` errors; see the diagnostic table in `design-register-decode.md`.
    *   **`varType:` and `enumPrefix:` must be unique across the whole build** — two address groups may share neither, even in different projects. Group *names* are project-qualified; the generated firmware enum is not, because every context's firmware is emitted into one flat namespace (`fw_ns`) and firmware headers include each other across project boundaries. Two groups sharing a `varType:` therefore either collide as a C++ redefinition or, in separate translation units, silently bind the same enumerator to a different address ID — a wrong address rather than a build failure. `make db` rejects it (`addressBlock: enum type name varType: '…' is used by two address groups: …`). In a reusable IP, qualify both by the declaring project, e.g. `varType: addr_id_isp_lut_top` / `enumPrefix: ADDR_ID_ISP_LUT_TOP_`; a bare `addr_id_top` is only safe in a project nothing else composes.

3.  **Making memory firmware-accessible:**
    *   `regAccess: true` (with `local:` absent) is the single switch. No custom interface is needed. The serving router is a generated `addressBlock:` block. See `design-register-decode.md`.

4.  **Instance Groups (`instanceGroups:`):**
    *   Used for ID enumeration without address space implications (e.g., for error reporting IDs).
    *   Declared in top-level `project.yaml`.

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

6.  **Address Object Sorting (`addressObjects:`):**
    *   Control how objects are packed in the address space using `addressObjects`.
    *   **Best Practice:** Sort memories by size (`memsize` alignment) to optimize decoding.
    *   Declared in top-level `project.yaml`.

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
