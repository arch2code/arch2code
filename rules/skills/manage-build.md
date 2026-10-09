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
    *   `make newmodule` also removes stale generated files that a block, variant or instance rename left behind. In `registrar/` it deletes every stale marker-carrying file. In `vl_wrap` it deletes a stale file only when its text outside the generated regions matches its scaffold, because the SC wrapper header `<block>_hdl_sc_wrapper.h` holds user code in its `end_ctor_init()` body. A stale `vl_wrap` file that differs is kept and reported as a warning (`kept stale vl_wrap file ...`). Move any code you need into the current wrapper, then delete the file by hand.

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
    *   A builder layer such as a2cPro adds its arguments through `A2C_LAYER_CXX_FLAGS`, `A2C_LAYER_CPP_INCLUDES`, `A2C_LAYER_LD_FLAGS`, `A2C_LAYER_SRC_DIRS`, `A2C_LAYER_RULES_DIRS`, `A2C_LAYER_HDL_F_FILES` and `A2C_LAYER_VCS_LIB_SV_FILES`. Most of these go after the builder's own arguments and before the project's hooks. Three go in earlier:
        *   `A2C_LAYER_CXX_FLAGS` follows the builder's base compile flags but precedes its C++ module, include-path, simulator and `VL_DUT=1` flags.
        *   `A2C_LAYER_LD_FLAGS` precedes the Verilator library flags.
        *   `A2C_LAYER_CPP_INCLUDES` follows the Boost and SystemC include paths but precedes the builder's Verilator, simulator and source-directory paths, so a layer header directory is searched ahead of those.
    *   `EXTRA_CXX_FLAGS` and `EXTRA_LD_FLAGS` come after every builder flag, so a project flag can override a builder flag, for example `EXTRA_CXX_FLAGS += -Wsign-compare` under `VL_DUT=1`. `EXTRA_CPP_INCLUDES` follows `A2C_LAYER_CPP_INCLUDES` directly, ahead of the same builder paths.
    *   The HDL hooks (`A2C_LAYER_HDL_F_FILES`, then the `EXTRA_HDL_*` hooks) go after the builder's `a2c.f` and before the project's `rtl.f`. `EXTRA_XRUN_LIB_OPTS` follows them inside the xrun DUT library.
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
    | `VERILATOR_USER_OPTS` | Older name for `EXTRA_VERILATOR_OPTS`, with the same effect. It goes after the builder's options and just before `EXTRA_VERILATOR_OPTS` |
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
    | `EXTRA_LD_FLAGS` | Link flags for the simulation binary, after the builder's libraries, the Verilator library included. Under `USE_XCELIUM` each word goes to the xrun link as `-Wld,<word>` |
    | `EXTRA_HDL_FILES` | SystemVerilog/Verilog sources for `verilator` (lint and each per-top verilate), the `vlogan` RTL analysis and the `xrun` DUT library |
    | `EXTRA_HDL_F_FILES` | `-F` file lists, to the same three commands. Name every file in the list: `vlogan` ignores `-y` library dirs, which only Verilator and Xcelium resolve |
    | `EXTRA_HDL_INCDIRS` | `+incdir+` directories, to the same three commands |
    | `EXTRA_HDL_DEFINES` | `+define+` macros, `NAME` or `NAME=VAL`, to the same three commands |
    | `EXTRA_VLOGAN_OPTS` | `vlogan`, both the RTL analysis and each `-sc_model` shell (`USE_VCS`) |
    | `EXTRA_VCS_LIB_SV_FILES` | Design units `vlogan` analyses explicitly because it does not search `-y` dirs (`USE_VCS`) |
    | `EXTRA_VCS_OPTS` | `vcs` elaboration and link (`USE_VCS`) |
    | `EXTRA_XRUN_OPTS` | `xrun` snapshot build, outside the DUT library (`USE_XCELIUM`) |
    | `EXTRA_XRUN_LIB_OPTS` | `xrun` snapshot build, inside the DUT library after `a2c.f`, so its `-y` dirs use `a2c.f`'s `+libext+.sv` (`USE_XCELIUM`) |
    | `EXTRA_XRUN_R_OPTS` | `xrun -R`, each simulation, written into the `build_xrun/run_<topology>` script (`USE_XCELIUM`). Do not put single quotes in it |

    *   Give `EXTRA_HDL_*` paths as absolute paths, for example `$(REPO_ROOT)/vip/my_if.sv`. Lint, the Verilator sub-make, `vlogan` and `xrun` each run in a different directory.
    *   The files named in `EXTRA_HDL_FILES` and `EXTRA_HDL_F_FILES` are prerequisites of the verilate, `vlogan` and `xrun` steps, so editing one rebuilds. Verilator also tracks the files a `.f` list names, through its `-MMD` record. `vlogan` and `xrun` do not.
    *   HDL from outside arch2code, such as VIP, goes on the `EXTRA_HDL_*` hooks, and every HDL flow picks it up. Its C/C++ models go on `EXTRA_CPP_SRC`, `EXTRA_PRJ_SRC_DIRS`, `EXTRA_CPP_INCLUDES` and `EXTRA_LD_FLAGS`. Options only one tool understands, and precompiled libraries (`-reflib`, `synopsys_sim.setup` and the like), go on that tool's hooks. Simulation plusargs go on `EXTRA_XRUN_R_OPTS`. The VCS flow has no run hook: `simv` takes the test's own arguments.
    *   Under Xcelium, every unit in `EXTRA_HDL_FILES`, or in a `.f` on `EXTRA_HDL_F_FILES`, must elaborate on its own. `xmelab` also elaborates the units nothing instantiates, so one parameter without a default fails the whole snapshot with `*E,NODEFP`. Give every parameter a default, or leave unused units off the list. VCS builds the same files without error.
    *   `EXTRA_VL_LIB_OBJS` paths are relative to `rundir/build/vl`, or absolute under `$(A2C_VL_BUILD_DIR)`. Each verilated top builds in its own `obj_dir/<top>`. The archive waits for every verilate before reading the objects, so `-j` builds are safe. Adding a path to an existing tree does not relink the archive by itself. Delete `rundir/build/vl/lib<project>vl_s_wrap.a` once, or run `make clean`.

    ```make
    # A top verilated with --timing needs the Verilator timing runtime in the library.
    EXTRA_VL_OPTS     += --timing
    EXTRA_VL_LIB_OBJS += $(A2C_VL_BUILD_DIR)/obj_dir/<top>_hdl_sv_wrapper/verilated_timing.o
    ```

5.  **Simulation:**
    *   `make run`: Runs the compiled SystemC simulation.
    *   **Note:** The model binary is at `rundir/build/run`. The whole-design Verilator build (`make VL_DUT=1`) lands under `rundir/build/vl`.

6.  **Verification (Project Specific):**
    *   Check the project's specific `Makefile` for verification targets (e.g., `test`, `regr`, `verif`).
    *   Commonly, `make all` builds everything including verification components.

7.  **Simulator Flows (VCS, Xcelium):**
    *   Set the flow's environment before `make`. The builder checks these:
        *   Every flow: `BOOST_INCLUDE`, and `LD_BOOST` unless `BOOST_LIBS` is set.
        *   The Verilator and `USE_VCS` builds: `SYSTEMC_INCLUDE` and `SYSTEMC_LIBDIR`.
        *   `USE_VCS`: `VCS_HOME`. `SYSTEMC_LIBDIR` must name the SystemC that VCS ships or was built against, because the `vcs` link takes `-lsystemc` from it alongside `-sysc=234`.
        *   `USE_XCELIUM`: `XCELIUM_TOOLS` and `XRUN_GCC_VERS`. The SystemC headers come from `XCELIUM_TOOLS`, so `SYSTEMC_*` are not read. The run script exports `LM_LICENSE_FILE` when it is set at build time.
    *   A builder layer can require more. `make help USE_VCS=1` / `make help USE_XCELIUM=1` list the flow variables. The simulator hooks are in the hook table above.
    *   Both simulators fix the SystemC/HDL topology when the snapshot is elaborated, so each DUT topology is its own binary named `run_<inst>_<type>[_tandem]`, or `run_model` when no RTL instance is elaborated. `make USE_VCS=1 -j8 all` links `build/run_<topology>` for the topology given by `VL_INST`, `VL_TYPE`, and `VL_TANDEM` (defaults: `HDL_TOP_MODULE`, `verif`, `0`); `make USE_XCELIUM=1 -j8 all` builds the equivalent `build_xrun/run_<topology>` script. Pass `VL_DUT=` for the model-only snapshot.
    *   Run a snapshot with the same `--vlInst`, `--vlType`, and `--vlTandem` it was built with. The dispatcher `dutRun.py <base binary> <args>` selects the matching snapshot from the arguments, which is how the regressions keep one run command.
    *   `make USE_VCS=1 vcs_snapshots` and `make USE_XCELIUM=1 xrun_snapshots` build `run_model` plus one snapshot per topology in `DUT_TOPOLOGIES` (`<inst>:<cfg>[,<cfg>]...`, cfg `verif|model[:tandem]`). Regression files pass that list on the build command line, one `DUT_TOPOLOGIES+=` entry per block; do not define it in the project `rundir/Makefile`. See `run-regression-tests` for the regression files and `run-tandem` for tandem runs on a snapshot.
    *   Run `make clean` when switching between hosts or between container and host paths: the generated build makefile stores absolute paths.

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
