---
name: setup-project
description: Guide for initializing a new arch2code project, setting up directory structure, and configuring project.yaml
---
# Skill: Setup Project

## Purpose
Guide the user through initializing a new project, setting up the directory structure, and configuring the base `project.yaml`.

## References
*   **Main Rules:** `ARCH2CODE_AI_RULES.md` (See "Project Configuration" and "Directory Structure Mapping")

## Instructions

1.  **Directory Structure:**
    *   Create the standard directory layout if it doesn't exist.
    *   **Crucial:** Always include `arch/yaml/project.yaml` as the entry point.
    *   Typically, the build system (`Makefile`) lives in `rundir` or the project root.

    ```text
    project_root/
    ├── arch/
    │   └── yaml/
    │       ├── project.yaml          # Main configuration (defines the mirror root)
    │       ├── config/                    # Optional legacy address-control files
    │       └── <group>/             # Subsystem/module architecture (e.g. ip/, top/)
    │           └── <module>.yaml
    ├── model/                        # SystemC models      (mirrors arch/yaml layout)
    ├── rtl/                          # SystemVerilog RTL   (mirrors arch/yaml layout)
    ├── base/                         # Generated base classes (mirrors arch/yaml layout)
    ├── tb/                           # Testbench files     (mirrors arch/yaml layout)
    ├── verif/vl_wrap/                # Verilator wrappers  (mirrors arch/yaml layout)
    ├── rundir/                       # Run directory containing Makefile (standard practice)
    └── Makefile                      # Top-level Makefile
    ```

    ### Directory Mirroring (default behavior)
    *   **The generated implementation tree mirrors the architecture YAML tree.** A block's (and a YAML file's context) generated files are placed in a subdirectory, **relative to `arch/yaml/`**, that matches the location of the YAML file that defines it. There is no separate setting to enable this; it is the default.
    *   Example: a block defined in `arch/yaml/ip/ip.yaml` generates to `model/ip/`, `rtl/ip/`, `base/ip/`, and `verif/vl_wrap/ip/`. Per-file context artifacts (SystemC `*Includes.cppm`, SV `*_package.sv`) follow the same rule (e.g. `rtl/ip/ip_package.sv`).
    *   **Testbench files nest one extra level** by the block name: a `hasTb` block in `arch/yaml/top/ip_top.yaml` generates testbench files into `tb/top/ip_top/`.
    *   Put YAML into subdirectories purely to organize; keep `project.yaml` at the `arch/yaml/` root (it defines the mirror root). Update relative `include:` / `projectFiles:` paths accordingly (e.g. `include: [../common/shared_types.yaml]`).
    *   The build system discovers sources recursively, so no Makefile changes are needed when you add subdirectories.

    ### `blockDir` override (exception only)
    *   The default mirror is almost always what you want. **Do not add `blockDir:` just to reproduce the default.**
    *   A top-level `blockDir:` directive in a YAML file overrides the output directory for **all** blocks and context artifacts defined in that file (relative to each `dirs` base path). For example `blockDir: .` forces a flat layout (everything directly under `model/`, `rtl/`, etc.) regardless of where the YAML file lives.
    *   A per-block `dir:` field overrides the output directory for a single block.
    *   Use these only for genuine exceptions (e.g. placing one block's files outside the mirrored tree). Otherwise omit them and let the YAML location drive the layout.

2.  **`project.yaml` Configuration:**
    *   **Must** define `projectName`, `topInstance`, and `dirs`.
    *   Use `$root` and `$a2c` macros for portable paths.
    *   **Do not** define `fileGeneration` maps unless overriding defaults.

    ```yaml
    # Example project.yaml
    projectName: my_chip
    topInstance: top_tb
    
    projectFiles:
      - top.yaml
      - subsystem_a/subsystem_a.yaml
    
    dirs:
      root: ../..
      base: $root/base
      model: $root/model
      rtl: $root/rtl
      # ... standard paths
    
    # Optional: Custom schema or legacy address control
    dbSchema: config/schema.yaml
    addressControl: config/addressControl.yaml

    # Preferred project-level address-policy sections for new work
    instanceGroups:
      all_instances:
        varType: global_inst_id_t
        enumPrefix: GID_

    addressObjects:
      memories:
        alignment: memsize
        sizeRoundUpPowerOf2: true
        sortDescending: true
      registers:
        alignment: 8
        sortDescending: true
    ```

3.  **Address Policy and Register Decode:**
    *   For new projects, place reusable address-policy sections in `project.yaml`:
        *   `instanceGroups:` for non-address-space ID enumeration.
        *   `addressObjects:` for register and memory packing policy.
    *   Legacy projects may still use `addressControl.yaml` with `InstanceGroups:` and `AddressObjects:` during migration, but that path is expected to be deprecated. If both spellings exist, the rows must match exactly.
    *   If the project has register access, define at least one address group through the active address-decode schema. Legacy projects use `addressControl.yaml` `AddressGroups:`; migrated projects use per-router `addressBlock:`.
    *   **Critical:** You must manually define the decoder/router block and instance in your architecture YAML (e.g., `apb_decode_system`).

4.  **Makefile Setup:**
    *   Ensure the project `Makefile` includes `shared.mk` from the repository root.
    *   Include `a2c-systemc.mk` and `a2c-agents.mk` from the builder logic.

## Validation
*   Run `make db` to verify the project configuration loads correctly.
