---
name: manage-build
description: Guide for building, simulating, creating implementation file scaffolds, and managing the arch2code project using make targets
---
# Skill: Manage build

## Workflow
1.  Edit the YAML. Set the artifact flags on each block: `hasMdl` and `hasRtl` default to true, `hasTb` and `hasVl` to false.
2.  `make db` validates the YAML and builds the database.
3.  `make newmodule` creates any implementation file that does not exist yet.
4.  `make gen` fills the generated regions of files that exist. It never creates a file.
5.  Write code in the user regions under `model/` or `rtl/`.
6.  From `rundir/`, `make` builds the model and `make run` runs it.

## Where to run each target
*   **Project root.** The root `Makefile` has the common targets `db`, `gen`, `newmodule`, `migrate`, `migrate-hierarchical`, `clean` and `help`, plus the agent-setup targets `agents-setup`, `agents-clean`, `agent-dev-setup` and `agent-dev-clean`. `agents-setup` deploys the rules and skills for Claude Code, Gemini CLI, OpenCode, Cursor and the cross-tool `.agents/` directory, and `agents-clean` removes them. `.agents-setup.md5` records a checksum for each deployed file. A rerun of `agents-setup` or `agent-dev-setup` replaces each deployed file unless its recorded checksum shows you edited it. It keeps and names each edited file. A file with no checksum line is replaced, except an `AGENTS.md` that agents-setup did not create. That file stays in place, and `make agents-clean FORCE=1` removes it. `agents-clean` and `agent-dev-clean` remove the same files and leave edited ones in place. `cursor-setup` and `cursor-clean` are aliases of the two. The root `Makefile` has no build or simulation targets.
*   **`rundir/`.** Build and simulation: `make` (the default `all` target), `make VL_DUT=1`, `make run`, `make compdb`, `make clangd`, and the project's own targets such as `regr` or `run-vl`. The common targets work here too.
*   **`rtl/`.** `make lint` and `make synthf`.

`make help` in each directory lists its targets.

## Targets
*   `make db` builds the project database from the YAML. It validates the YAML without generating code.
*   `make gen` regenerates every `GENERATED_CODE_BEGIN`/`GENERATED_CODE_END` region and keeps everything outside them.
*   `make newmodule` creates the missing files that the `fileGeneration.fileMap` entries name, such as the block files in `model/` and `rtl/` and the testbench files in `tb/`. It never rewrites an existing file and never creates YAML.
*   `make clean` removes the database, `.gen/` and `rundir/build/`. It leaves source files alone, generated regions included.
*   `make` in `rundir/` regenerates and builds the model binary, `rundir/build/run`.
*   `make VL_DUT=1` in `rundir/` regenerates, verilates the RTL into `rundir/build/vl`, and builds the binary with it linked in.
*   `make run` builds the binary when its sources changed and runs it. It does not regenerate, so after a YAML edit run `make` first. `make run VL_DUT=1` substitutes the RTL for `HDL_TOP_MODULE` only. Where a project has `run-vl`, use it to cover every RTL instance. See `verify-cosimulation`.
*   `make lint` in `rtl/` checks that the RTL compiles.
*   `make compdb` writes `compile_commands.json` for clangd at the project root, `REPO_ROOT`. `make newmodule` also refreshes it and discards any error. That refresh leaves out a new `.cppm` scaffold, which has no `export module` line until `make gen` fills it. After adding a block, run `make compdb` once `make gen` has run.
*   `make clangd` writes `.clangd` at the project root. Reload the IDE afterwards.

Run arch2code only through these targets. Two tools run directly: `arch2code.py --newproject`, before a makefile exists (see `setup-project`), and `regrLauncher.py` (see `run-regression-tests`).

## Creating implementation files
*   Run `make newmodule` before you write any implementation file (`.sv`, `.cppm`, `.cpp`, `.h`) that arch2code scaffolds. This covers new blocks and existing blocks gaining an artifact, for example `hasRtl: false` changed to `hasRtl: true`.
*   The model file is one C++20 module, `model/<block>.cppm`, not a `.cpp`/`.h` pair.
*   Never write a scaffold by hand. After `make newmodule` and `make gen`, edit only the user regions.
*   `make newmodule` also deletes stale generated files left by a block, variant or instance rename. In `registrar/` it deletes every stale file that carries generated markers. In `vl_wrap/` it deletes a stale file only when its text outside the generated regions matches the scaffold, because `<block>_hdl_sc_wrapper.h` holds user code in `end_ctor_init()`. It keeps a stale `vl_wrap` file that differs and warns `kept stale vl_wrap file ...`. Move any code you need into the current wrapper, then delete the file by hand.

## Files with generated regions
*   The build takes its generated file set from the manifest the database build writes (`A2C_SC_GEN_FILES` and `A2C_SV_GEN_FILES` in `.gen/build.mk`).
*   When arch2code owns the whole file, declare it in `fileGeneration.fileMap`. `make newmodule` creates it, `make gen` fills it, and the manifest lists it. The project-wide address header is one case; see `manage-address-space`.
*   When the project owns the file and arch2code only fills its generated regions, list the file in the project's `include/make/shared.mk`, above the `include $(A2C_ROOT)/include/make/a2c-common.mk` line. C++ hosts (`.h`, `.cpp`, `.cppm`) go on `EXTRA_SC_GEN_FILES`, SystemVerilog hosts (`.sv`, `.svh`) on `EXTRA_SV_GEN_FILES`. Both are empty by default, and `make gen` skips an unlisted host.
*   These two lists drive regeneration. They do not add the host to the compile. The build compiles the host the way it compiles any project file: a C++ host through its source directory or an `#include`, an SV host through Verilator options you supply, such as `VERILATOR_USER_OPTS`. An edit to an `EXTRA_SV_GEN_FILES` host also re-verilates every verilated top.

    ```make
    EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/mixedEncoders.h
    EXTRA_SV_GEN_FILES = $(REPO_ROOT)/rtl/mixedEncoder_package.sv
    ```

## Regeneration triggers
*   The manifest records the YAML include closure as `A2C_YAML_FILES`. An edit to any of those files, interface definitions included, rebuilds the database.
*   `.gen/builder.stamp` tracks `templates/`, `pysrc/`, `config/*.yaml`, `config/*.py`, `arch2code.py`, and Pro's `templates/` and `config/`. An edit to any of these rebuilds the database and regenerates everything on the next `make`.
*   After an edit to `include/make/`, or to a template kept inside the project tree, run `make clean` first. Nothing tracks those.
*   The manifest records the project root it was written for. The next `make` rebuilds the database when the tree has moved to a new path or the manifest names YAML that no longer exists. A failed rebuild is retried on the following `make`.
*   Each database build deletes the manifest before it writes a new one. A warning that `build.mk` stays stale means no manifest appeared under `REPO_ROOT`, because `REPO_ROOT` and the project file's `dirs: root:` name different directories.

## Toolchain
*   Clang is the recommended compiler. Use GCC (`USE_GCC=1`) only where a simulator requires it.
*   `A2C_CLANG` names the Clang for the whole build. Give one compiler path or name, such as `/opt/llvm/bin/clang++` or `clang++-20`, never a launcher plus a compiler. Verilator's `OBJCACHE` already adds ccache. The build ignores an exported `CXX`.
*   The verilated objects use `A2C_CLANG` too. Under `USE_GCC` they use the compiler Verilator was configured with, because `verilated.mk` sets flags for that compiler.
*   `VL_JOBS` (default 4) sets Verilator's threads and its C++ build jobs. Under `make -jN` the Verilator build shares the outer job pool instead. A bare `make -j` has no job pool, so `VL_JOBS` applies there too. `make -n` does not run the verilate step.
*   A site can export `BOOST_LIBS` as the whole Boost link line, for example `-lboost_system -lboost_program_options -lboost_stacktrace_basic -L/site/lib`. `LD_BOOST` is then not needed.
*   A site `EXTRA_LD_FLAGS` goes on the link line after the Boost and SystemC libraries and before the project's `EXTRA_LD_FLAGS +=` additions. A `-L` there cannot override the Boost search path, so set `BOOST_LIBS` to change Boost.
*   Site values are make syntax and then pass through the shell, so write a literal `$` as `$$` inside shell quotes: `export EXTRA_LD_FLAGS="-Wl,-rpath,'\$\$ORIGIN/lib'"`.

## Synthesis file list
`make synthf` in `rtl/` writes `.gen/synth.f`, one absolute path per line with no tool switches. It lists every package in the compile closure, child projects' packages included, in `rtl.f` order, then the RTL modules from the manifest. It leaves out the Verilator wrapper, `RTL_SRC_FILES` additions, and the directories passed through `VERILATOR_USER_OPTS`.

The synthesis project adds the rest itself:
*   `$(A2C_ROOT)/common/systemVerilog/flops.sv` and `asserts.svh`, ahead of the `synth.f` entries.
*   The interface `.sv` files the design uses, from `$(A2C_ROOT)/interfaces/<protocol>/`.
*   The memory models the design uses, from `$(A2C_ROOT)/common/systemVerilog/`: `memory_sp.sv`, `memory_sp_ext.sv`, `memory_dp.sv`, `memory_dp_2clk.sv` or `memory_dp_ext.sv`.
*   In an A2C Pro tree, `pro/common/systemVerilog` as an include directory (for `fsmDefs.svh`), the library modules the design uses from it (`memArb.sv`, `vldAckArb.sv`, the FIFOs and the rest), and `pro/interfaces/lmmi/lmmi_if.sv`. `a2cPro.f` adds these for Verilator only.

## Project verification targets
Check the project's `rundir/Makefile` for its own targets, such as `regr` or `run-vl`.

## Constraints
*   Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`. `make gen` rewrites those regions.
