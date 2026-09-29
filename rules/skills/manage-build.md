---
name: manage-build
description: Guide for building, simulating, creating implementation file scaffolds, and managing the arch2code project using make targets
---
# Skill: Manage Build

## Purpose
Guide the user on how to build, simulate, and manage the project using the `make` system, adhering to the standard workflow.

## Instructions

1.  **Standard Targets:**
    *   `make gen`: Generates all code (RTL headers, SystemC wrappers, etc.) from the architecture YAML. **Run this first after any YAML change.**
    *   `make db`: Loads the project configuration and architecture into the database. Useful for validation without full generation.
    *   `make clean`: Cleans generated files and build artifacts.
    *   `make help`: Lists available targets.
    *   `make`: Runs full build with just the model
    *   `make VL_DUT=1`: Runs full build with model and RTL
    *   `make compdb`: Generates `compile_commands.json` for clangd. Also refreshed automatically by `make newmodule` after sources are added.
    *   `make clangd`: Generates the `.clangd` IDE configuration at the repo root (depends on `compdb`). Reload your IDE after running to apply changes.

2.  **Module and Implementation File Creation:**
    *   Use `make newmodule` before creating any implementation file (`.sv`, `.cppm`, `.cpp`, `.h`) that arch2code should scaffold.
    *   This applies to new blocks and to existing blocks that are gaining a previously skipped artifact, such as changing `hasRtl: false` to `hasRtl: true`.
    *   `make newmodule` creates the directory structure, initial YAML when needed, and implementation skeletons in `model/`, `rtl/`, and related generated locations. The `model/` skeleton is a single C++20 module file, `model/<block>.cppm` (the `blockModule` fileMap entry, gated `cond: hasMdl`), not a `.cpp`/`.h` pair.
    *   Do not use a direct file write for these scaffolds. Edit only the user-owned body regions after `make newmodule` and `make gen` have produced the file.

3.  **Generated-region host files:**
    *   The build enumerates generated source from the DB-derived manifest (`A2C_SC_GEN_FILES` / `A2C_SV_GEN_FILES`, emitted by `config/createBuildManifest.py` and consumed wildcard-filtered in `a2c-common.mk`).
    *   Declare a host in `fileGeneration.fileMap` when arch2code owns the whole file. `make newmodule` scaffolds it, `make gen` updates its generated regions, and the manifest includes it in generation and compilation. A project-wide address header is one example: use `mode: project` and set `name:` and `basePath:` to the required basename and segment.
    *   Use the `EXTRA_` seam when the project owns the host and arch2code only injects generated regions. Such a file carries `GENERATED_CODE_BEGIN` markers but has no fileMap entry, so `make newmodule` does not create it and the manifest does not list it.
    *   Add each project-owned host to the matching variable in the project's `include/make/shared.mk`, above the `include … a2c-common.mk` line. Put SystemC/C++ hosts (`.h`/`.cpp`/`.cppm`) on `EXTRA_SC_GEN_FILES` and SystemVerilog hosts (`.sv`/`.svh`) on `EXTRA_SV_GEN_FILES`.
    *   The seams are empty by default. An unlisted project-owned host is omitted from both generation and compilation.

    ```make
    # Project-owned hosts whose generated regions arch2code updates.
    EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/mixedEncoders.h
    EXTRA_SV_GEN_FILES = $(REPO_ROOT)/rtl/mixedEncoder_package.sv
    ```

4.  **Simulation:**
    *   `make run`: Runs the compiled SystemC simulation.
    *   **Note:** The model binary is at `rundir/build/run`. The whole-design Verilator build (`make VL_DUT=1`) lands under `rundir/build/vl`.

5.  **Verification (Project Specific):**
    *   Check the project's specific `Makefile` for verification targets (e.g., `test`, `regr`, `verif`).
    *   Commonly, `make all` builds everything including verification components.

## Workflow
1.  **Edit YAML** (`arch/yaml/...`)
2.  **`make db`** (Validate Schema)
3.  **`make gen`** (Generate Code)
4.  **Implement** (`model/...` or `rtl/...`)
5.  **`make run`** (Build & Simulate)

## Constraints
*   **Do not** invoke Python scripts directly (e.g., `arch2code.py`). Always use the `make` targets which set up the correct environment and paths.
*   **Do not** edit generated files. They are overwritten by `make gen`.
*   Most commands should be run from the `rundir` or project root where the main `Makefile` resides. Exception is `make lint` in the rtl dir
