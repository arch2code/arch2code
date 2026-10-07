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
        *   `addressObjects:` — register/memory packing policy (see step 7).
    *   The decode hierarchy is declared per-block: routers carry `addressBlock:` and reusable-IP leaves carry `registerPorts:`. There is no project-wide address-decode file to author. See `design-register-decode.md`.
    *   Converting a pre-existing `addressControl.yaml` project to this schema is a one-time migration handled entirely by `migrate-project.md` / `address-migration.md`.

2.  **Address groups (per-block schema):**
    *   An address group is named by a router block's `addressBlock.addressGroup`; routed leaves select it via their instance `addressGroup:`. The router block defines the group and its RTL is generated (`apbDecodeModule`); the primary router is inferred by hierarchy walk. There is no `decoderInstance:`/`primaryDecode:` to author.
    *   Multi-level decode uses **nested routers** (a second `addressBlock:` block inside a container that is itself a routed leaf of the parent). See `design-register-decode.md`.
    *   **A group name is owned by the project that declares it.** An `addressGroup:` reference resolves only within the project owning the referring YAML file; it never falls outward to a parent or sibling project. Two independently authored projects may therefore each declare a group named `top` and compose cleanly, but a reusable IP must declare every group it references — an IP naming a group its own project does not declare has hard-coded a name its parent owns. Within one project, at most one router block may declare a given group name. Both violations are hard `make db` errors; see the diagnostic table in `design-register-decode.md`.
    *   **`varType:` and `enumPrefix:` must be unique across the whole build** — two address groups may share neither, even in different projects. Group *names* are project-qualified; the generated firmware enum is not, because every context's firmware is emitted into one flat namespace (`fw_ns`) and firmware headers include each other across project boundaries. Two groups sharing a `varType:` therefore either collide as a C++ redefinition or, in separate translation units, silently bind the same enumerator to a different address ID — a wrong address rather than a build failure. `make db` rejects it (`addressBlock: enum type name varType: '…' is used by two address groups: …`). In a reusable IP, qualify both by the declaring project, e.g. `varType: addr_id_isp_lut_top` / `enumPrefix: ADDR_ID_ISP_LUT_TOP_`; a bare `addr_id_top` is only safe in a project nothing else composes.

3.  **Making memory firmware-accessible:**
    *   `regAccess` (with `local:` absent) is the single switch. Its value is the firmware access mode: `rw` (or `true`), `ro` or `wo`. No custom interface is needed. The serving router is a generated `addressBlock:` block. See `design-register-decode.md`.

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
        *   `smartInclude: true`: Generate a context's files only when the context has types, structures or constants. These come from `types:` (or its alias `enums:`), `structures:` and `constants:`, from `encoders:`, and from the address enum of a router's `addressBlock:`, which lands in the router block's own YAML file. A context whose YAML holds only registers, memories or `ipParameters:` gets no file.
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
          langDomain: fw   # takes fwFilePrefix
          desc: "Firmware include file"
    ```

6.  **Project-wide address header (`regAddresses`):**
    *   One header for the whole project with the instance and register address defines. It is opt-in, because not every project has firmware.
    *   A firmware project created by `--newproject` carries the entry commented out after `includeFW`. Uncomment it, or add it yourself:

    ```yaml
    # In project.yaml, under fileGeneration.fileMap
    regAddresses: {name: "regAddresses", ext: {hdr: "h"}, mode: project, basePath: fwInc, langDomain: fw, desc: "Per-project instance and register address defines"}
    ```

    *   `name:` is the basename verbatim, with no project stem, so a project normally spells its own (e.g. `debayerRegAddresses`). `basePath:` picks the segment, commonly `model` or `fwInc`. The default entry uses `fwInc` with `langDomain: fw`.
    *   Run `make newmodule` to scaffold the file, then `make gen` to fill it.
    *   If the project owns the file, leave the entry out. Write the file yourself with a `GENERATED_CODE_PARAM --project=<projectName>` line and the `includes` template's `addresses` and `regAddresses` regions, then list it on `EXTRA_SC_GEN_FILES` in `include/make/shared.mk`. See `manage-build.md`.

7.  **Address Object Sorting (`addressObjects:`):**
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

8.  **Parameterizable Register/Memory Sizing:**
    *   Register and firmware-accessible memory offsets are allocated from worst-case sizes when the referenced structure or `wordLines` is parameterizable.
    *   Structure width uses generated `maxBitwidth`; `wordLines` uses a parameterizable constant's `maxValue` or the maximum value bound in `parameters:` for pure block params.
    *   YAML authors should provide explicit bounds (`maxValue` for constants, `maxBitwidth` for literal-width types) so the address map reserves enough space for every variant.
    *   Every variant decodes the worst-case footprint, in the RTL and the model alike. A parameterizable `rw` or `ro` register spans the worst case's words. Row N of a memory sits at `base + N * stride`, where the stride is the worst-case row width in bytes rounded up to a power of two, at least 4. Bytes above the bound variant's width read 0 and drop writes. Rows past the variant's depth read `32'hBADD_C0DE`.

    ```yaml
    ipParameters:
      constants:
        IP_MEM_DEPTH: {value: 16, maxValue: 32, desc: "Per-instance memory depth"}

    blocks:
      ip:
        desc: "Parameterized IP"
        params: [IP_MEM_DEPTH, IP_NONCONST_DEPTH]

    memories:
      - {memory: ip_mem, block: ip, structure: ip_data_st, addressStruct: ip_mem_addr_st, wordLines: IP_MEM_DEPTH, regAccess: true, desc: "Parameterized memory"}  # Address sizing uses maxValue=32
      - {memory: ip_variant_mem, block: ip, structure: ip_data_st, addressStruct: ip_mem_addr_st, wordLines: IP_NONCONST_DEPTH, regAccess: true, desc: "Pure block-param memory depth"}  # Uses max variant binding
    ```
