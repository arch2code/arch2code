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
    │       ├── project.yaml          # Main configuration
    │       ├── config/                    # Optional legacy address-control files
    │       └── <module>/             # Module-specific architecture
    ├── model/                        # SystemC models
    ├── rtl/                          # SystemVerilog RTL
    ├── tb/                           # Testbench files
    ├── rundir/                       # Run directory containing Makefile (standard practice)
    └── Makefile                      # Top-level Makefile
    ```

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
