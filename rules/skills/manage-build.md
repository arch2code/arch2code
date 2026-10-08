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
*   `make clean` removes the database, `.gen/`, `rundir/build/` and `rundir/build_xrun/`, and the VCS and Xcelium analysis, snapshot and log files. It leaves source files alone, generated regions included.
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
*   The default Boost link line is `-lboost_program_options -L$(LD_BOOST)`. A site can export `BOOST_LIBS` as the whole Boost link line instead, for example `-lboost_program_options -L/site/lib` for a shared Boost. `LD_BOOST` is then not needed.
*   A site `EXTRA_LD_FLAGS` goes on the link line after the Boost and SystemC libraries and before the project's `EXTRA_LD_FLAGS +=` additions. A `-L` there cannot override the Boost search path, so set `BOOST_LIBS` to change Boost.
*   Site values are make syntax and then pass through the shell, so write a literal `$` as `$$` inside shell quotes: `export EXTRA_LD_FLAGS="-Wl,-rpath,'\$\$ORIGIN/lib'"`.

## Synthesis file list
`make synthf` in `rtl/` writes `.gen/synth.f`, one absolute path per line with no tool switches. It lists every package in the compile closure, child projects' packages included, in `rtl.f` order, then the RTL modules from the manifest. It leaves out the Verilator wrapper, `RTL_SRC_FILES` additions, the directories passed through `VERILATOR_USER_OPTS`, and the HDL hooks (`EXTRA_HDL_*`).

The synthesis project adds the rest itself:
*   `$(A2C_ROOT)/common/systemVerilog/flops.sv` and `asserts.svh`, ahead of the `synth.f` entries.
*   The interface `.sv` files the design uses, from `$(A2C_ROOT)/interfaces/<protocol>/`.
*   The memory models the design uses, from `$(A2C_ROOT)/common/systemVerilog/`: `memory_sp.sv`, `memory_sp_ext.sv`, `memory_dp.sv`, `memory_dp_2clk.sv` or `memory_dp_ext.sv`.
*   In an A2C Pro tree, `pro/common/systemVerilog` as an include directory (for `fsmDefs.svh`), the library modules the design uses from it (`memArb.sv`, `vldAckArb.sv`, the FIFOs and the rest), and `pro/interfaces/lmmi/lmmi_if.sv`. `a2cPro.f` adds these for Verilator only.

## User hooks
*   The project appends to the `EXTRA_*` hooks with `+=` in `include/make/shared.mk`. Base and the a2cPro layer read them and never assign them, so a hook set on the make command line replaces only the project's value.
*   A hooked command carries the builder's own arguments first, then those of a builder layer such as a2cPro (`A2C_LAYER_VERILATOR_OPTS`, `A2C_LAYER_CXX_FLAGS`, `A2C_LAYER_CPP_INCLUDES`, `A2C_LAYER_LD_FLAGS`, `A2C_LAYER_SRC_DIRS`, `A2C_LAYER_RULES_DIRS`, `A2C_LAYER_HDL_F_FILES` and `A2C_LAYER_VCS_LIB_SV_FILES`), then the project's hooks. A project flag can therefore override a builder flag, for example `EXTRA_CXX_FLAGS += -Wsign-compare` under `VL_DUT=1`. `EXTRA_CPP_INCLUDES` is the exception. It sits after the Boost, SystemC and layer include paths but before the Verilator and source-directory paths, so a project header directory is searched ahead of those.
*   The HDL hooks (`A2C_LAYER_HDL_F_FILES`, then the `EXTRA_HDL_*` hooks) go after the builder's `a2c.f` and before the project's `rtl.f`. `EXTRA_XRUN_LIB_OPTS` follows them inside the xrun DUT library.
*   These commands take no hook: the `migrateYaml.py` calls of `make migrate` and `make migrate-hierarchical`, the C++ module scanner (`gen_cpp_module_map.py`), `gen_compile_commands.py` (it reads the compile commands, hooks included, from a `make -n` run), and `ar -s` on the Verilator library.
*   `make help-hooks` lists each hook, the command it feeds, and its current value.
*   Set `EXTRA_SC_GEN_FILES`, `EXTRA_SV_GEN_FILES` and `EXTRA_A2C_RULES_DIRS` above the `include ... a2c-common.mk` line, because a2c-common.mk reads them as it parses. The other hooks can go anywhere in `shared.mk`.
*   The Verilator library build (`make VL_DUT=1`) runs a sub-make in `rundir/build/vl` that reads `shared.mk` and never the rundir `Makefile`. The verilate and archive hooks only take effect from `shared.mk` or the command line.
*   The rundir `Makefile` that `make newmodule` scaffolds seeds `EXTRA_CPP_SRC`, `EXTRA_CPP_INCLUDES` and `EXTRA_LD_FLAGS` with `+=`, so values from `shared.mk` survive. A rundir `Makefile` that assigns one of them, or `EXTRA_O3_CPP_SRC`, with `=` overwrites what `shared.mk` appended. Change such a line to `+=` before moving a value into `shared.mk`.

| Hook | Tool command it feeds |
| :--- | :--- |
| `EXTRA_GEN_OPTS` | `arch2code.py`, every call in the make flow: the db build, `gen` (every per-file `--systemc`, `--systemc --python` and `--systemVerilog` call, and the VCS/Xcelium `--vlBoundary` call) and `newmodule` |
| `EXTRA_SC_GEN_FILES` | Extra files for `arch2code.py --systemc --file` (`gen`) |
| `EXTRA_SV_GEN_FILES` | Extra files for `arch2code.py --systemVerilog --file` (`gen`). An edit to one re-verilates every verilated top |
| `EXTRA_VERILATOR_OPTS` | `verilator`, every call: `make lint` and the model wrapping of `make VL_DUT=1` |
| `VERILATOR_USER_OPTS` | Same effect as `EXTRA_VERILATOR_OPTS`. It goes after `A2C_LAYER_VERILATOR_OPTS` and just before `EXTRA_VERILATOR_OPTS` |
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
*   HDL from outside arch2code, such as VIP, goes on the `EXTRA_HDL_*` hooks, and lint, Verilator, VCS and Xcelium all pick it up. Its C/C++ models go on `EXTRA_CPP_SRC`, `EXTRA_PRJ_SRC_DIRS`, `EXTRA_CPP_INCLUDES` and `EXTRA_LD_FLAGS`. Options only one tool understands, and precompiled libraries (`-reflib`, `synopsys_sim.setup` and the like), go on that tool's hooks. Simulation plusargs go on `EXTRA_XRUN_R_OPTS`. The VCS flow has no run hook, because `simv` takes the test's own arguments.
*   Under Xcelium, every unit in `EXTRA_HDL_FILES`, or in a `.f` on `EXTRA_HDL_F_FILES`, must elaborate on its own. `xmelab` also elaborates the units nothing instantiates, so one parameter without a default fails the whole snapshot with `*E,NODEFP`. Give every parameter a default, or leave unused units off the list. VCS builds the same files without error.
*   `EXTRA_VL_LIB_OBJS` paths are relative to `rundir/build/vl`, or absolute under `$(A2C_VL_BUILD_DIR)`. Each verilated top builds in its own `obj_dir/<top>`. The archive waits for every verilate before reading the objects, so `-j` builds are safe. Adding a path to an existing tree does not relink the archive by itself. Delete `rundir/build/vl/lib<project>vl_s_wrap.a` once, or run `make clean`.

```make
# A top verilated with --timing needs the Verilator timing runtime in the library.
VERILATOR_USER_OPTS += --timing
EXTRA_VL_LIB_OBJS   += $(A2C_VL_BUILD_DIR)/obj_dir/<top>_hdl_sv_wrapper/verilated_timing.o
```

## Simulator flows (VCS, Xcelium)
*   Source the site setup script first. VCS needs `VCS_HOME`. Xcelium needs `XCELIUM_TOOLS`, `XRUN_GCC_VERS` and `LM_LICENSE_FILE`. Both need `A2C_CLANG` and the SystemC and Boost roots. `make help USE_VCS=1` and `make help USE_XCELIUM=1` list the flow variables. The simulator hooks are in the hook table above.
*   Both simulators fix the SystemC/HDL topology when they elaborate the snapshot, so each DUT topology is its own binary, named `run_<inst>_<type>[_tandem]`, or `run_model` when no RTL instance is elaborated. `make USE_VCS=1 -j8 all` links `build/run_<topology>` for the topology that `VL_INST`, `VL_TYPE` and `VL_TANDEM` give (defaults `HDL_TOP_MODULE`, `verif`, `0`). `make USE_XCELIUM=1 -j8 all` builds the equivalent `build_xrun/run_<topology>` script. Pass `VL_DUT=` for the model-only snapshot.
*   Run a snapshot with the same `--vlInst`, `--vlType` and `--vlTandem` it was built with. The dispatcher `dutRun.py <base binary> <args>` picks the matching snapshot from the arguments, so a regression keeps one run command.
*   `make USE_VCS=1 vcs_snapshots` and `make USE_XCELIUM=1 xrun_snapshots` build `run_model` plus one snapshot per topology in `DUT_TOPOLOGIES` (`<inst>:<cfg>[,<cfg>]...`, where cfg is `verif|model[:tandem]`). Regression files pass that list on the build command line, one `DUT_TOPOLOGIES+=` entry per block. Do not define it in the project `rundir/Makefile`. See `run-regression-tests` for the regression files and `run-tandem` for tandem runs on a snapshot.

## Project verification targets
Check the project's `rundir/Makefile` for its own targets, such as `regr` or `run-vl`.

## Constraints
*   Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`. `make gen` rewrites those regions.
