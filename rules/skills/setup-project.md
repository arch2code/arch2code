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
    *   Source discovery is manifest-driven: `projectCreate` records the layout's source/include dirs in the DB and emits them to `.gen/build.mk`, so no Makefile changes are needed when you add subdirectories.

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
    
    # Optional: Custom schema
    dbSchema: config/schema.yaml

    # Project-level address-policy sections
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

    # Optional: project-scoped clocks and resets (omit both for the built-in
    # clk / rst_n). Exactly one entry per section carries default: true.
    clocks:
      clk:     { desc: "main clock",  default: true, period: 1, timeUnit: ns }
      clkSlow: { desc: "slow clock",  period: 3, timeUnit: ns }
    resets:
      rst_n:     { desc: "main reset", default: true, clock: clk }
      rstSlow_n: { desc: "slow reset", clock: clkSlow, releaseCycles: 4 }
    ```

    *   **`clocks:` / `resets:`** are project-scoped: declared here, referenced by name from any design file of this project, and invisible to other projects in a composed build. Design YAML must not declare them.
        *   `clocks.<name>`: `desc` (required), `default` (exactly one `true` per project), `period` (positive integer, default `1`), `timeUnit` (`ps`, `ns`, `us`; default `ns`). `period`/`timeUnit` drive only the co-simulation wrapper's `sc_clock`; they carry no synthesis meaning.
        *   `resets.<name>`: `desc` (required), `default` (exactly one `true`), `clock` (the domain the reset is released in; default: the project default clock), `releaseCycles` (positive integer, default `3`; edges of the reset's own clock before release).
        *   The declared key is the emitted port name verbatim (`rst_n`, not `rst` plus a suffix). A clock name and a reset name may not collide. Every reset is active-low; there is no polarity field.
    *   For how blocks and connections pick up these domains, see **Clocks and Resets** in `design-architecture.md`.

3.  **Address Policy and Register Decode:**
    *   Place reusable address-policy sections in `project.yaml`:
        *   `instanceGroups:` for non-address-space ID enumeration.
        *   `addressObjects:` for register and memory packing policy.
    *   If the project has register access, define at least one address group via the per-block schema: a router block carries `addressBlock:` and routed leaves tag their instance `addressGroup:`.
    *   The register-bus decoder/router is a **generated** block: declare it with a populated `addressBlock:` and instance it in the container of the leaves it serves (its RTL comes from `apbDecodeModule`). Do **not** hand-author it. For the decode hierarchy decision rule and the upstream feed you do author, use the **Register/Memory Decode** skill (`design-register-decode.md`).
    *   Converting an existing `addressControl.yaml` project to this schema is a one-time migration — see `migrate-project.md` / `address-migration.md`.

4.  **Makefile Setup:**
    *   For a brand-new project in a clean repository, run `arch2code.py --newproject`. It writes the project file and seed design, builds the database, and scaffolds all four build files (`Makefile`, `include/make/shared.mk`, `rundir/Makefile`, `rtl/Makefile`) for you. Do not copy makefiles from an example, and do not hand-author `project.yaml`. See `readme.md` for the full bootstrap sequence.
    *   The same four files are scaffolded create-once by `make newmodule` for an existing project, so a project that predates them picks them up without manual copying.
    *   The per-project `include/make/shared.mk` sets `PROJECTNAME` / `TB_TOP_MODULE` / `HDL_TOP_MODULE` and then includes `a2c-common.mk`; the `rundir/Makefile` includes it and then `a2c-systemc.mk`.
    *   The build is manifest-driven: `make db` derives the source/include dirs and the generated-file set from the layout and emits `.gen/build.mk`; no Makefile edits are needed as blocks are added. Model output lands in `rundir/build/run`, the whole-design Verilator build in `rundir/build/vl`.
    *   If the project hosts **user-authored files that arch2code injects generated regions into** (address headers, encoder units — files `make newmodule` does not scaffold), wire them onto the `EXTRA_SC_GEN_FILES` / `EXTRA_SV_GEN_FILES` seam in `shared.mk`. See the **Build/Run** skill (`manage-build.md`).

## Validation
*   Run `make db` to verify the project configuration loads correctly.
