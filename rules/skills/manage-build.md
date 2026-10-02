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
    *   Put SystemC/C++ hosts (`.h`/`.cpp`/`.cppm`) on `EXTRA_SC_GEN_FILES` and SystemVerilog hosts (`.sv`/`.svh`) on `EXTRA_SV_GEN_FILES`. See **User hooks** below for where to set them.
    *   The seams are empty by default. An unlisted project-owned host is omitted from both generation and compilation.

    ```make
    # Project-owned hosts whose generated regions arch2code updates.
    EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/mixedEncoders.h
    EXTRA_SV_GEN_FILES = $(REPO_ROOT)/rtl/mixedEncoder_package.sv
    ```

4.  **User hooks:**
    *   The project appends to the `EXTRA_*` hooks with `+=` in `include/make/shared.mk`. Base and the a2cPro layer read them and never assign them, so a hook set on the make command line replaces only the project's value.
    *   A hooked command carries the builder's own arguments first, then those of a builder layer (a2cPro adds through `A2C_LAYER_VERILATOR_OPTS`, `A2C_LAYER_CXX_FLAGS`, `A2C_LAYER_CPP_INCLUDES`, `A2C_LAYER_LD_FLAGS`, `A2C_LAYER_SRC_DIRS` and `A2C_LAYER_RULES_DIRS`), then the project's hooks. A project flag can therefore override a builder flag, for example `EXTRA_CXX_FLAGS += -Wsign-compare` under `VL_DUT=1`. `EXTRA_CPP_INCLUDES` is the exception. It sits after the Boost, SystemC and layer include paths but before the Verilator and source-directory paths, so a project header directory is searched ahead of those.
    *   These commands take no hook: the `migrateYaml.py` calls of `make migrate` and `make migrate-hierarchical`, the C++ module scanner (`gen_cpp_module_map.py`), `gen_compile_commands.py` (it reads the compile commands, hooks included, from a `make -n` run), and `ar -s` on the Verilator library.
    *   `make help-hooks` lists each hook, the command it feeds, and its current value.
    *   Set `EXTRA_SC_GEN_FILES` and `EXTRA_SV_GEN_FILES` above the `include … a2c-common.mk` line, since `gen` expands them as it parses. The other hooks can go anywhere in `shared.mk`.
    *   The Verilator library build (`make VL_DUT=1`) runs a sub-make in `rundir/build/vl` that reads `shared.mk` and never the rundir `Makefile`. The verilate and archive hooks only take effect from `shared.mk` or the command line.
    *   The rundir `Makefile` that `make newmodule` scaffolds seeds `EXTRA_CPP_SRC`, `EXTRA_CPP_INCLUDES` and `EXTRA_LD_FLAGS` with `+=`, so values from `shared.mk` survive. Rundir Makefiles scaffolded before this assign them, and often `EXTRA_O3_CPP_SRC`, with `=`, which overwrites what `shared.mk` appended. Change those lines to `+=` before moving a value into `shared.mk`.

    | Hook | Tool command it feeds |
    | :--- | :--- |
    | `EXTRA_GEN_OPTS` | `arch2code.py`, every call in the make flow: the db build, `gen` (`--systemc`/`--systemVerilog` per file) and `newmodule` |
    | `EXTRA_SC_GEN_FILES` | Extra files for `arch2code.py --systemc --file` (`gen`) and the C++ build |
    | `EXTRA_SV_GEN_FILES` | Extra files for `arch2code.py --systemVerilog --file` (`gen`) and verilation |
    | `EXTRA_VERILATOR_OPTS` | `verilator`, every call: `make lint` and the model wrapping of `make VL_DUT=1` |
    | `VERILATOR_USER_OPTS` | Older name for `EXTRA_VERILATOR_OPTS`, with the same effect. It goes after `A2C_LAYER_VERILATOR_OPTS` and just before `EXTRA_VERILATOR_OPTS` |
    | `EXTRA_LINT_OPTS` | `verilator --lint-only` (`make lint`) |
    | `EXTRA_VL_OPTS` | `verilator` model wrapping only: the runtime build (`vl_dummy`) and each verilated top |
    | `EXTRA_VL_CFLAGS` | C++ flags for Verilator-generated code, appended inside the single quoted `-CFLAGS '...'` argument of each model-wrapping verilate. Do not put single quotes in it |
    | `EXTRA_VL_LIB_OBJS` | `ar` script `ADDMOD` lines for `lib<project>vl_s_wrap.a`. Names objects a verilate already builds. The builder does not compile them |
    | `EXTRA_CXX_FLAGS` | C++ compile flags, after every builder flag |
    | `EXTRA_CPP_INCLUDES` | C++ include paths |
    | `EXTRA_CPP_SRC` | Extra C++ sources to compile |
    | `EXTRA_O3_CPP_SRC` | Extra C++ sources compiled at `-O3` |
    | `EXTRA_CPP_MODULE_SRC` | C++20 module interface units outside the project source dirs |
    | `EXTRA_PRJ_SRC_DIRS` | Extra project source directories (every `.cpp` and `.cppm` in each is compiled) |
    | `EXTRA_A2C_SRC_DIRS` | Extra builder-side source directories, such as the firmware BSP `$(A2C_ROOT)/common/fw/bsp` |
    | `EXTRA_LD_FLAGS` | Link flags for the simulation binary, after the builder's libraries, the Verilator library included |

    *   `EXTRA_VL_LIB_OBJS` paths are relative to `rundir/build/vl`, or absolute under `$(A2C_VL_BUILD_DIR)`. Each verilated top builds in its own `obj_dir/<top>`. The archive waits for every verilate before reading the objects, so `-j` builds are safe. Adding a path to an existing tree does not relink the archive by itself. Delete `rundir/build/vl/lib<project>vl_s_wrap.a` once, or run `make clean`.

    ```make
    # A top verilated with --timing needs the Verilator timing runtime in the library.
    VERILATOR_USER_OPTS += --timing
    EXTRA_VL_LIB_OBJS   += $(A2C_VL_BUILD_DIR)/obj_dir/<top>_hdl_sv_wrapper/verilated_timing.o
    ```

5.  **Simulation:**
    *   `make run`: Runs the compiled SystemC simulation.
    *   **Note:** The model binary is at `rundir/build/run`. The whole-design Verilator build (`make VL_DUT=1`) lands under `rundir/build/vl`.

6.  **Verification (Project Specific):**
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
