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
    *   `make synthf` (in the rtl dir): Writes `.gen/synth.f` under the project root for synthesis. It lists every package in the compile closure, including child projects' packages, in rtl.f compile order, then the RTL modules from the build manifest, one absolute path per line with no tool switches. It leaves out the Verilator wrapper and any `RTL_SRC_FILES` additions. The synthesis project must add the interface `.sv` files the design uses, from `$(A2C_ROOT)/interfaces/<protocol>/`. It must also add the macro files `$(A2C_ROOT)/common/systemVerilog/flops.sv` and `asserts.svh` ahead of the synth.f entries. A design with memories also needs the memory models it uses from the same directory: `memory_sp.sv`, `memory_sp_ext.sv`, `memory_dp.sv` or `memory_dp_ext.sv`. synth.f also omits library and include directories passed through `VERILATOR_USER_OPTS`. In a pro tree, `pro/common/systemVerilog/a2cPro.f` adds `pro/common/systemVerilog` and `pro/interfaces/lmmi` as `+incdir+` and `-y` directories, so the synthesis project must also add that include directory (for `fsmDefs.svh`), the library modules the design uses from it (`memArb.sv`, `vldAckArb.sv`, the fifos and the rest), and `pro/interfaces/lmmi/lmmi_if.sv`.

2.  **Module and Implementation File Creation:**
    *   Use `make newmodule` before creating any implementation file (`.sv`, `.cppm`, `.cpp`, `.h`) that arch2code should scaffold.
    *   This applies to new blocks and to existing blocks that are gaining a previously skipped artifact, such as changing `hasRtl: false` to `hasRtl: true`.
    *   `make newmodule` creates the directory structure, initial YAML when needed, and implementation skeletons in `model/`, `rtl/`, and related generated locations. The `model/` skeleton is a single C++20 module file, `model/<block>.cppm` (the `blockModule` fileMap entry, gated `cond: hasMdl`), not a `.cpp`/`.h` pair.
    *   Do not use a direct file write for these scaffolds. Edit only the user-owned body regions after `make newmodule` and `make gen` have produced the file.
    *   `make newmodule` also removes stale generated files that a block, variant or instance rename left behind. In `registrar/` it deletes every stale marker-carrying file. In `vl_wrap` it deletes a stale file only when its text outside the generated regions matches its scaffold, because the SC wrapper header `<block>_hdl_sc_wrapper.h` holds user code in its `end_ctor_init()` body. A stale `vl_wrap` file that differs is kept and reported as a warning (`kept stale vl_wrap file ...`). Move any code you need into the current wrapper, then delete the file by hand.

3.  **Generated-region host files:**
    *   The build enumerates generated source from the DB-derived manifest (`A2C_SC_GEN_FILES` / `A2C_SV_GEN_FILES`, emitted by `config/createBuildManifest.py` and consumed wildcard-filtered in `a2c-common.mk`).
    *   Declare a host in `fileGeneration.fileMap` when arch2code owns the whole file. `make newmodule` scaffolds it, `make gen` updates its generated regions, and the manifest includes it in generation and compilation. A project-wide address header is one example: use `mode: project` and set `name:` and `basePath:` to the required basename and segment. The default entry uses `basePath: fwInc` and `langDomain: fw`.
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
    *   `VL_JOBS` (default 4) sets verilator's threads and its C++ build jobs. Under `make -jN` the verilator build uses the outer job pool instead; a bare `make -j` starts no job pool, so `VL_JOBS` applies there too. The verilate recipe is `+`-prefixed, so `make -n` still runs it.
    *   `A2C_CLANG` names the Clang for the whole build. It must be a single compiler path or name, such as `/opt/llvm/bin/clang++` or `clang++-20`, never a launcher plus compiler; Verilator's own `OBJCACHE` already adds ccache.
    *   The verilated objects follow `A2C_CLANG`. Under `USE_GCC` they keep the compiler Verilator was configured with, because verilated.mk's flags suit that compiler.
    *   A site can export `BOOST_LIBS` as the whole Boost link line, for example `-lboost_system -lboost_program_options -lboost_stacktrace_basic -L/site/lib`. `LD_BOOST` is then not needed.
    *   An exported site `EXTRA_LD_FLAGS` goes on the link line after the Boost and SystemC libraries and before the project's `EXTRA_LD_FLAGS +=` additions. A site `-L` there cannot override the default Boost search path; set `BOOST_LIBS` to change Boost.
    *   Site values use make syntax and then pass through the link command's shell, so a literal `$` is written `$$` inside shell quotes: `export EXTRA_LD_FLAGS="-Wl,-rpath,'\$\$ORIGIN/lib'"`.

5.  **Verification (Project Specific):**
    *   Check the project's specific `Makefile` for verification targets (e.g., `test`, `regr`, `verif`).
    *   Commonly, `make all` builds everything including verification components.

6.  **Regeneration triggers:**
    *   The db's YAML list tracks YAML edits, interface definitions included.
    *   `.gen/builder.stamp` tracks the builder's templates, `pysrc/`, `config/`, `arch2code.py`, and pro's templates and config. A change there rebuilds the db and regenerates every file.
    *   The build manifest `.gen/build.mk` records the project root it was written for. When a tree is copied or moved to a new path, or the manifest names YAML that no longer exists, the next `make` rebuilds the db. If that rebuild fails, the following `make` tries again. Each db build removes the manifest first. If `make` then warns that `build.mk` stays stale, no manifest was written under `REPO_ROOT`, because `REPO_ROOT` and the project file's `dirs: root:` name different directories.
    *   Nothing tracks templates kept inside the project tree, or other builder files such as `include/make/`. Run `make clean` after changing those.

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
