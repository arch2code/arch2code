# VCS and Xcelium integration specification

This document specifies how Arch2Code builds and runs a project under Synopsys VCS and Cadence Xcelium, and what a site must install and set to bring both flows up. It covers the make interface, the generated files, the environment, and the known failure modes. The make targets and hooks are summarised here. The full hook table and the general build workflow are in the `manage-build` skill (`rules/skills/manage-build.md`), and the regression file format is in `run-regression-tests` (`rules/skills/run-regression-tests.md`). Section 9 covers the UVM testbench flow, which runs on both simulators.

## 1. Scope and architecture

### 1.1 What each flow builds

Every flow compiles the same SystemC testbench and models, written as C++20 modules. The flows differ in how the RTL DUT enters the simulation and in what links and runs the result.

| Flow | Switch | C++ compiled by | Linked and run by | RTL DUT | Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Plain model | none | Clang (`A2C_CLANG`) | Clang, standalone SystemC | none | `rundir/build/run` |
| Verilator | `VL_DUT=1` | Clang | Clang, standalone SystemC | verilated to C++ | `rundir/build/run` |
| VCS | `USE_VCS=1` | Clang | `vcs` (VCS SystemC kernel) | analysed by `vlogan`, elaborated by `vcs` | `rundir/build/run_<topology>` (a `simv`) |
| Xcelium | `USE_XCELIUM=1` | Clang, `-fPIC` | `xrun` (Cadence SystemC kernel) | compiled and elaborated by `xrun` | `rundir/build_xrun/run_<topology>` (a script) |

- `USE_VCS` and `USE_XCELIUM` are exclusive. Setting both stops make with `USE_VCS and USE_XCELIUM are exclusive`.
- Either switch implies `VL_DUT=1`. Pass an empty `VL_DUT=` on the command line for a model-only simulator binary.
- In the simulator flows Clang only compiles. The simulator links the objects with its own SystemC kernel and its own GCC.

### 1.2 Preprocessor macros

| Macro | Set when | Effect |
| :--- | :--- | :--- |
| `VCS` | `USE_VCS` | `main.cpp` registers an exit handler so `simv` returns the a2c exit code, and sets the lock hierarchy prefix `sc_main`, under which VCS roots every SystemC instance |
| `VCS_DUT` | `USE_VCS` and `VL_DUT` | registrars and SystemC HDL wrappers use the `vlogan -sc_model` shell `<top>` from `<top>.h` as the DUT class |
| `XCELIUM`, `NCSC`, `CADENCE`, `LNX86`, `XMSC`, `_GLIBCXX_USE_CXX11_ABI=1` | `USE_XCELIUM` | `main.cpp` rethrows `xmsc_elab_exception`, which xmelab uses to end the elaboration run of `sc_main`. The other defines are the ones xmsc passes to its own compiler |
| `XCELIUM_DUT` | `USE_XCELIUM` and `VL_DUT` | registrars and wrappers use the generated foreign-module shell `<top>` from `<top>_xcelium.h` |
| `VERILATOR` | `VL_DUT` with neither switch | the Verilator flow, including `--vlTrace` VCD tracing. `sc_main` passes its arguments to `Verilated::commandArgs`, so RTL plusargs read the run's command line |
| `VCS_DEBUG` (SystemVerilog) | `VCS_DEBUG=1` | the HDL wrapper calls `$fsdbDumpvars` when the run passes `+fsdbTrace` |
| `VERILATOR` (SystemVerilog) | Verilator, set by the tool | the HDL wrapper leaves out its X/Z checker instances (section 9.4) |
| `A2C_UVM_RTL_DUT` (SystemVerilog) | `USE_UVM` with `UVM_DUT=rtl` (section 9.7) | the generated UVM testbench module holds the RTL wrapper and ties off its pins toward SystemC |
| `A2C_UVM_PKG` (SystemVerilog) | `USE_UVM`, set to the `UVM_TOP` variant package (section 9.7) | the test package imports that variant package |

### 1.3 DUT topologies and snapshots

Both simulators fix the SystemC and HDL hierarchy when they build the snapshot.

- VCS runs `sc_main` up to its first `sc_start` to find the HDL models it must elaborate. It takes the arguments for that run from `-syscelab`, and it caches the discovered topology per output binary.
- Xcelium runs `sc_main` under `xmelab` up to its first `sc_start` and stores the whole SystemC object set in the snapshot. A run whose arguments build a different hierarchy fails with `xmsim *F,SCOBNF`.

A run must therefore use the topology its snapshot was built with, and each topology is its own snapshot. The make variables that select one are:

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `VL_INST` | `HDL_TOP_MODULE` under `VL_DUT`, else empty | `--vlInst` path of the RTL instance |
| `VL_TYPE` | `verif` | `--vlType`, `verif` (RTL) or `model` |
| `VL_TANDEM` | `0` | `1` adds `--vlTandem` |
| `DUT_TESTBENCH` | `HDL_TOP_MODULE` | testbench name passed as the first argument during elaboration. Set it when the testbench a project runs is not named after `HDL_TOP_MODULE` |
| `DUT_ELAB_ARGS` | `$(DUT_TESTBENCH)` plus the `--vlInst`, `--vlType` and `--vlTandem` options above | the `sc_main` arguments of the elaboration run |
| `DUT_TOPOLOGY` | `<VL_INST>_<VL_TYPE>[_tandem]`, or `model` when `VL_INST` is empty | snapshot name suffix |
| `DUT_TOPOLOGIES` | `$(HDL_TOP_MODULE):verif,verif:tandem` | topology list for `vcs_snapshots` and `xrun_snapshots` |

- The binary is `run_<DUT_TOPOLOGY>`. Dots in the instance path stay in the name, for example `run_top.u_child_verif`, so distinct paths never share a snapshot.
- `run_model` holds no RTL instance. It serves every test without `--vlInst` and every model test without `--vlTandem`.
- A model/model tandem test (`--vlType model --vlTandem`) constructs a second model instance, which a `run_model` snapshot does not hold under Xcelium. The dispatcher sends such a test to `run_<inst>_model_tandem` in both flows, so both need that snapshot.
- A `DUT_TOPOLOGIES` entry is `<inst>:<cfg>[,<cfg>]...`, where `<cfg>` is `verif`, `verif:tandem` or `model:tandem`.
- The `tandem` configurations need a builder layer that registers tandem blocks (`<block>_tandem`). Without one, set `DUT_TOPOLOGIES=<top>:verif`.
- Uninstantiated RTL tops cost nothing at run time under VCS (tested with VCS W-2024.09-SP2).

### 1.4 Dispatcher

`dutRun.py <base binary> <simulation arguments...>` (in `builder/base`, with a `builder/dutRun.py` link in a full builder tree) picks the snapshot from the test's own arguments and `exec`s it with those arguments unchanged.

| Test arguments | Snapshot |
| :--- | :--- |
| no `--vlInst` | `<base>_model` |
| `--vlInst X`, `--vlType verif` or no `--vlType` | `<base>_X_verif` |
| `--vlInst X --vlType verif --vlTandem` | `<base>_X_verif_tandem` |
| `--vlInst X --vlType model --vlTandem` | `<base>_X_model_tandem` |
| `--vlInst X --vlType model` without `--vlTandem` | `<base>_model` |
| `--uvmDut D --uvmTop T` (section 9.7) | `<base>_uvm_T_D` |

`--uvmDut` without `--uvmTop`, or `--uvmTop` without `--uvmDut`, stops `dutRun.py` with an error. A missing snapshot exits with `dutRun: no snapshot <binary> for arguments ...`. A regression file keeps one run command, for example `../builder/dutRun.py build/run <testbench>` for VCS and `../builder/dutRun.py build_xrun/run <testbench>` for Xcelium.

### 1.5 Generated boundary files

The RTL top of each DUT is the generated HDL verification wrapper (`<block>[_<variant>]_hdl_sv_wrapper`). Owner-qualified foreign tops (`<stub>_<label>_hdl_sv_wrapper`) and pair tops (`p<n>_<parentSv>_c<m>_<childSv>_<label>_hdl_sv_wrapper`) are tops too (`specs/spec-verilated-wrappers.md` §2). A top's pins are flat `bit` and `bit [N-1:0]` ports. Each top binds literal parameter values, so its widths are fixed, but they are written as parameter expressions (`specs/spec-verilated-wrappers.md` §5), which neither `vlogan -sc_model` nor a hand-written foreign module can size. So the generator evaluates them.

- `make db` evaluates the width of every parameterizable structure and type at each top's parameter values and stores them in the database.
- `make gen` runs `arch2code.py --vlBoundary` only when `USE_VCS` or `USE_XCELIUM` is set and the manifest lists HDL tops (`A2C_VL_TOPS`). It writes two whole files per top under `.gen/vl/`, with no user region:

| File | Consumer | Content |
| :--- | :--- | :--- |
| `.gen/vl/<top>.portmap` | `vlogan -sc_model <top> -sc_portmap` | one line per pin: `<pin> <width> bit bool` or `<pin> <width> bitvector sc_bv` |
| `.gen/vl/<top>_xcelium.h` | the registrar under `XCELIUM_DUT` | `class <top> : public xmsc_foreign_module` with one `sc_in<...>` or `sc_out<...>` per pin, typed `bool` or `sc_bv<W>`, and `hdl_name()` returning `<top>` |

- The VCS SystemC shells themselves (`<top>.h`) are written by `vlogan` into `$(VCS_RUNDIR)/csrc/sysc/include`.
- The same run writes both files for each UVM testbench top, at the paths the manifest records (section 9.3).

## 2. Prerequisites

### 2.1 Tested toolchain

| Component | Tested with | Notes |
| :--- | :--- | :--- |
| OS | RHEL 9.6 (glibc 2.34), RHEL 8.10 (glibc 2.28) | both simulator flows pass on both |
| Python | 3.10 with the packages in `requirements.txt` (`pip install -r requirements.txt`) | runs `arch2code.py`, `dutRun.py`, `regrLauncher.py` |
| GNU Make | 4.3 (RHEL 9), 4.2.1 (RHEL 8) | |
| Clang | 18.1.8 prebuilt LLVM release on both OS; 20.1.8 on RHEL 9 only | 20.1.8 prebuilt needs glibc 2.34. Only the `clang` driver and its `lib/clang/<ver>` resource directory are needed |
| libstdc++ | GCC 13.2 | headers for the compile, runtime for VCS |
| VCS | W-2024.09-SP2 | SystemC 2.3.4 shipped with VCS, GCC 13 build (`systemc234-gcc13`), `-sysc=234` |
| Xcelium | 26.03-s002 | bundled SystemC 2.3.4 (Cadence), link with the bundled GCC 12.4 (`-gcc_vers 12.4`) |
| Boost | headers 1.74; shared `program_options` 1.75 (RHEL 9) and 1.66 (RHEL 8) | stacktrace and system are header-only |
| Verilator | 5.038 | needed only for `make lint` in `rtl/` and the Verilator flow. `VL_TIMING=1` is supported only on 5.053 or later, currently master at or after `ea536a5` |

Tested and rejected:

- GCC 13.2 and GCC 14.2 fail on the generated C++ module units (module serialisation defects).
- Clang 16 fails on global-module-fragment consistency errors, for example `'X' has different definitions in different modules`.

### 2.2 Compiler and standard library constraints

- **Clang.** Use Clang for the simulator flows. The base makefiles do not reject `USE_GCC=1` with a simulator switch, but no tested GCC compiles the module units. `A2C_CLANG` names one compiler path. The build ignores an exported `CXX`.
- **Language standard.** The compile passes `-std=$(CPP_STD)`, default `c++23`. A Clang that only spells it `c++2b` takes `CPP_STD=c++2b`.
- **libstdc++ version.** The sources use C++23 `<format>`, so Clang must compile against GCC 13 or newer libstdc++ headers. Under VCS, the shipped `systemc234-gcc13` library needs `GLIBCXX_3.4.30` and `GLIBCXX_3.4.32`, so link and run with GCC 13.2 or newer libstdc++ (GCC 13.1 provides only `GLIBCXX_3.4.31`). Under Xcelium, the simulator loads its own `tools/lib/64bit/libstdc++.so.6` (26.03 provides up to `GLIBCXX_3.4.31`), and it must provide every `GLIBCXX` version the objects need. Tested with: objects compiled against GCC 13.2 headers stay within it. GCC 14 headers would not.
- **Pointing Clang at GCC 13.** The builder adds no `--gcc-install-dir` or `-isystem` flags. If the default Clang search does not find GCC 13's libstdc++, the site adds the flags through `EXTRA_CXX_FLAGS`. Tested in both simulator flows: `-nostdinc++ -isystem <gcc13>/include/c++/<ver> -isystem <gcc13>/include/c++/<ver>/<triple> --gcc-toolchain=<gcc13>`. `--gcc-install-dir=<gcc13>/lib/gcc/<triple>/<ver>` was tested in the plain flow and in an Xcelium compile probe.
- **DWARF version, VCS only.** VCS's SystemC pre-elaboration reads the objects' debug information and aborts on DWARF 5, which Clang emits by default with `-g` (tested with VCS W-2024.09-SP2). Add `-gdwarf-4` through `EXTRA_CXX_FLAGS`. The builder does not add it.
- **VCS link compiler.** `vcs` compiles its generated code and links `simv` with its configured GNU toolchain. Tested with GCC 13.2 from the Synopsys GNU package. Clang objects compiled against the same libstdc++ link with it.
- **Xcelium link compiler.** `xrun -gcc_vers $(XRUN_GCC_VERS)` links the objects into a shared library with the named bundled GCC. Choose `XRUN_GCC_VERS` from the bundled releases. No bundled GCC matches GCC 13.2 headers in 26.03. What must hold is that every `GLIBCXX` version the objects need is provided by Xcelium's `tools/lib/64bit/libstdc++.so.6` (26.03: up to 3.4.31). Tested with `-gcc_vers 12.4` and GCC 13.2 headers.

### 2.3 SystemC per flow

| Flow | SystemC headers | SystemC library |
| :--- | :--- | :--- |
| Plain, Verilator | `SYSTEMC_INCLUDE` (SystemC 2.3.4 install) | `-L$(SYSTEMC_LIBDIR) -lsystemc` |
| VCS | `SYSTEMC_INCLUDE`, set to the SystemC VCS ships. The `VL_DUT` compile adds `$(VCS_HOME)/include` and `$(VCS_RUNDIR)/csrc/sysc/include` | `-L$(SYSTEMC_LIBDIR) -lsystemc` on the `vcs` command line, with `-sysc=234`. `SYSTEMC_LIBDIR` must be the matching VCS SystemC library directory |
| Xcelium | `$(XCELIUM_TOOLS)/systemc/include` and its `cci`, `factory`, `tlm2` subdirectories, `$(XCELIUM_TOOLS)/include`, `$(XCELIUM_TOOLS)/inca/include` | linked by `xrun`. The build does not read `SYSTEMC_INCLUDE` or `SYSTEMC_LIBDIR` |

In a VCS install the GCC 13 build of SystemC 2.3.4 sits under `$VCS_HOME/etc/systemc/accellera_install/systemc234-gcc13/` (`include/` and `lib-linux64/`; tested with W-2024.09-SP2).

### 2.4 Boost

- The build compiles against `BOOST_INCLUDE` and links only `program_options`. Boost.System and the stacktrace in `q_assert.cpp` are header-only, and the stacktrace needs only `-ldl`, which the builder adds.
- Under Xcelium, Boost enters a shared library, so it must be a shared or position-independent build. A static non-PIC Boost fails the link with `R_X86_64_32` relocation errors.
- Prefer Boost headers that match the shared library. A 1.74 header set against 1.75 and 1.66 runtimes worked in testing, but Boost does not support mixing versions.

### 2.5 Licences

- VCS reads its licence from the Synopsys licence variables, for example `SNPSLMD_LICENSE_FILE`. The default `VCS_OPTS` and `VLOGAN_OPTS` carry `+vcs+lic+wait`, so a build or run waits for a free licence. Every VCS binary, `run_model` included, is a `simv` and takes a runtime licence.
- Xcelium reads `LM_LICENSE_FILE`. The build writes the value set at build time into each run script, so a run started outside the build environment finds the same servers. The script captures no other licence variable.
- Keep regression parallelism within the licence seats the site holds under its vendor agreements (section 5.5).

## 3. Environment variables

"Checked" means the makefiles stop with an `$(error)` when the variable is unset. "Tool" means only the simulator, compiler or loader reads it. The builder variables in sections 3.2 to 3.5 can come from the environment or the make command line, and a command-line value replaces the environment value.

- Set `VCS_OPTS`, `VLOGAN_OPTS`, `VCS_ELAB_OPTS`, `VCS_LIB_SV_FILES` and `XRUN_OPTS` overrides in the project's `include/make/shared.mk`. The makefiles append to `XRUN_OPTS` and `VCS_LIB_SV_FILES`, and under `VCS_DEBUG` to `VLOGAN_OPTS` and `VCS_ELAB_OPTS`. A command-line value of one of those loses the additions (for example `XRUN_OPTS` loses `-gcc_vers`, and `VCS_ELAB_OPTS` loses the `VCS_DEBUG` flags). An environment value is appended to again in each sub-make.
- A command-line `EXTRA_CXX_FLAGS` or `EXTRA_LD_FLAGS` discards the project's `+=` additions. Export a site value in the environment instead.

### 3.1 Project settings

These are set in the project's `include/make/shared.mk` (and `rundir/Makefile`), not in a site script.

| Variable | Required | Meaning |
| :--- | :--- | :--- |
| `A2C_ROOT` | checked | root of the Arch2Code builder (`builder/base`, or `builder` in a tree with a builder layer) |
| `REPO_ROOT` | checked | project root |
| `PROJECTNAME` | checked | project name |
| `TB_TOP_MODULE`, `HDL_TOP_MODULE` | checked | testbench and HDL top. `HDL_TOP_MODULE` feeds the `VL_INST`, `DUT_TESTBENCH` and `DUT_TOPOLOGIES` defaults |
| `PROJECT_RUNDIR` | set by the builder | `$(REPO_ROOT)/rundir` |

### 3.2 Common to all flows

| Variable | Flows | Required | Default | Meaning | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `SYSTEMC_INCLUDE` | plain, Verilator, VCS | checked unless `USE_XCELIUM` | none | SystemC include directory | `/opt/systemc-2.3.4/include` |
| `SYSTEMC_LIBDIR` | plain, Verilator, VCS | checked unless `USE_XCELIUM` | none | SystemC library directory | `/opt/systemc-2.3.4/lib` |
| `BOOST_INCLUDE` | all | checked | none | Boost include directory | `/opt/boost/include` |
| `BOOST_LIBS` | all | optional | `-lboost_program_options -L$(LD_BOOST)` | whole Boost link line. An empty value, on the command line too, counts as unset and selects the default | `-L/opt/boost/lib -l:libboost_program_options.so.1.75.0` |
| `LD_BOOST` | all | checked when `BOOST_LIBS` is empty, Xcelium included | none | Boost library directory for the default link line | `/opt/boost/lib` |
| `A2C_CLANG` | all unless `USE_GCC` | optional | `clang++` on `PATH` | one Clang path, no launcher or flags | `/opt/llvm-18/bin/clang++` |
| `CPP_STD` | all | optional | `c++23` | value of `-std=` | `c++2b` |
| `EXTRA_CXX_FLAGS` | all | optional | empty | compile flags after every builder flag. The site route for libstdc++ selection and `-gdwarf-4` | see section 4 |
| `EXTRA_LD_FLAGS` | all | optional | empty | link flags. Under Xcelium each word becomes `-Wld,<word>` | `-L/opt/site/lib -lmylib` |
| `USE_GCC` | plain, Verilator | optional | unset | `1` selects `g++` and the GCC module rules. Not for the simulator flows | |
| `VERILATOR_ROOT` | Verilator | optional | `/usr/local/share/verilator` | Verilator runtime headers. Unused by the VCS and Xcelium compiles | `/opt/verilator/share/verilator` |
| `LD_LIBRARY_PATH` | all, at run time | tool | | must resolve the shared SystemC (plain, Verilator, VCS), the shared Boost, and a GCC 13.2 or newer libstdc++ where the binary needs one | see section 4 |

### 3.3 Selectors

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `USE_VCS` | unset | `1` selects the VCS flow and implies `VL_DUT=1` |
| `USE_XCELIUM` | unset | `1` selects the Xcelium flow and implies `VL_DUT=1` |
| `VL_DUT` | `1` under a simulator switch, else unset | RTL DUT in the build. `VL_DUT=` gives a model-only binary |
| `VL_TIMING` | unset | `1` verilates and lints with `--timing` and adds Verilator's timing runtime to the Verilator library. Verilator flow and `make lint` only. Set it in `shared.mk`, on the command line or in the environment. A rundir `Makefile` setting does not reach the Verilator build |
| `SKIP_GEN` | unset | `1` skips the `gen` step. Under `USE_VCS` or `USE_XCELIUM` the build still runs `--vlBoundary` when `.gen/vl` is older than the database, because the `vlogan -sc_model` step and the registrar objects depend on it |

The topology variables (`VL_INST`, `VL_TYPE`, `VL_TANDEM`, `DUT_*`) are in section 1.3.

### 3.4 VCS

| Variable | Required | Default | Meaning | Example |
| :--- | :--- | :--- | :--- | :--- |
| `VCS_HOME` | checked (parse time, even for `make -n`) | none | VCS install. Also read by VCS itself. The `VL_DUT` compile adds `-I$(VCS_HOME)/include` | `/opt/synopsys/vcs/W-2024.09-SP2` |
| `VCS` | optional | `vcs` | `vcs` command | `$VCS_HOME/bin/vcs` |
| `VLOGAN` | optional | `vlogan` | `vlogan` command | `$VCS_HOME/bin/vlogan` |
| `VCS_OPTS` | optional | `+vcs+lic+wait -full64 -timescale=1ns/1ps` | `vcs` options | |
| `VLOGAN_OPTS` | optional | `+vcs+lic+wait -full64 -sverilog -timescale=1ns/1ps` | `vlogan` options, both stages | |
| `VCS_ELAB_OPTS` | optional | `-sysc=234` | `vcs` elaboration options | |
| `VCS_DEBUG` | optional | unset | `1` adds `-kdb -debug_access` to the link and `+define+VCS_DEBUG` to `vlogan`, for FSDB dumps with `+fsdbTrace` at run time | `1` |
| `VCS_LIB_SV_FILES` | optional | every `interfaces/*/*_if.sv`, every `interfaces/*/*_xcheck.sv` and every `common/systemVerilog/*.sv` except `flops.sv` | units `vlogan` analyses explicitly because it does not search `-y` directories | |
| `VCS_RUNDIR` | optional | `$(PROJECT_RUNDIR)` | working directory of `vlogan` and `vcs` | |
| `SNPSLMD_LICENSE_FILE` | tool | | Synopsys licence servers | `27000@<license-server>` |
| `VG_GNU_PACKAGE` | tool | | Synopsys GNU toolchain selection, where the VCS release uses it | `<vcs-gnu-install>` |
| `PATH` | tool | | must reach `vcs`, `vlogan` and a GCC 13.2 or newer `g++` for the `vcs` link | |

### 3.5 Xcelium

| Variable | Required | Default | Meaning | Example |
| :--- | :--- | :--- | :--- | :--- |
| `XCELIUM_TOOLS` | checked (parse time) | none | the install's tools directory, the one holding `bin/xrun`, `systemc/include`, `include` and `inca/include` | `/opt/cadence/xcelium/26.03/tools` |
| `XRUN_GCC_VERS` | checked (parse time) | none | `-gcc_vers` release of a bundled GCC under `$XCELIUM_TOOLS/cdsgcc/gcc` | `12.4` |
| `XRUN` | optional | `xrun` | `xrun` command, also written into each run script | `$XCELIUM_TOOLS/bin/xrun` |
| `XRUN_OPTS` | optional | `-64bit -sv -sysc -sc_main -timescale 1ns/1ps` | snapshot build options. `-gcc_vers $(XRUN_GCC_VERS)` is appended | |
| `XRUN_R_OPTS` | optional | `-64bit -nolog` | per-simulation options in the run script. `-nolog` keeps concurrent runs off one `xrun.log` | |
| `XRUN_DUT_LIB` | optional | `a2c_dut` | `-makelib` library that holds the HDL | |
| `XRUN_RUNDIR` | optional | `$(PROJECT_RUNDIR)` | working directory of `xrun`, where the snapshots live | |
| `LM_LICENSE_FILE` | read by the builder and the tool | none | licence servers, captured into each run script | `5280@<license-server>` |

## 4. Sample site setup scripts

Adapt the placeholders. Source one script in the shell that runs `make`, and the same script in any shell that runs the binaries.

### 4.1 VCS

```bash
# site-vcs.sh: source before `make USE_VCS=1 ...` and before running build/run_<topology>.
export VCS_HOME=<vcs-install>                          # for example /opt/synopsys/vcs/W-2024.09-SP2
export PATH="$VCS_HOME/bin:$PATH"
export SNPSLMD_LICENSE_FILE=<port>@<license-server>

# GCC 13 toolchain for the vcs link, first on PATH (or select it the way your VCS release documents).
GCC13=<gcc13-install>                                  # GCC 13.2 or newer: bin/g++, include/c++/<ver>, lib64/libstdc++.so.6
export PATH="$GCC13/bin:$PATH"

# SystemC shipped with VCS, GCC 13 build, matching VCS_ELAB_OPTS -sysc=234.
export SYSTEMC_INCLUDE="$VCS_HOME/etc/systemc/accellera_install/systemc234-gcc13/include"
export SYSTEMC_LIBDIR="$VCS_HOME/etc/systemc/accellera_install/systemc234-gcc13/lib-linux64"

# Clang for the C++20 module units, against GCC 13's libstdc++, with DWARF 4 for VCS.
export A2C_CLANG=<llvm-install>/bin/clang++
GXX_VER=<13.2 or later>                                # directory name under $GCC13/include/c++
GXX_TRIPLE=<triple>                                    # for example x86_64-pc-linux-gnu
export EXTRA_CXX_FLAGS="-nostdinc++ -isystem $GCC13/include/c++/$GXX_VER \
 -isystem $GCC13/include/c++/$GXX_VER/$GXX_TRIPLE --gcc-toolchain=$GCC13 -gdwarf-4"

# Boost: headers, and a link line vcs accepts (no bare .so path).
export BOOST_INCLUDE=<boost-install>/include
export BOOST_LIBS="-L<boost-libdir> -l:libboost_program_options.so.<version>"

export LD_LIBRARY_PATH="$SYSTEMC_LIBDIR:<boost-libdir>:$GCC13/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

### 4.2 Xcelium

```bash
# site-xcelium.sh: source before `make USE_XCELIUM=1 ...` and before running build_xrun/run_<topology>.
export XCELIUM_TOOLS=<xcelium-tools-dir>               # holds bin/xrun, systemc/include, inca/include
export XRUN="$XCELIUM_TOOLS/bin/xrun"                  # the install binary, not a batch-submission wrapper
export XRUN_GCC_VERS=12.4                              # a release under $XCELIUM_TOOLS/cdsgcc/gcc
export LM_LICENSE_FILE=<port>@<license-server>

# Clang for the C++20 module units, against GCC 13's libstdc++ headers.
GCC13=<gcc13-install>
export A2C_CLANG=<llvm-install>/bin/clang++
GXX_VER=<13.2 or later>
GXX_TRIPLE=<triple>
export EXTRA_CXX_FLAGS="-nostdinc++ -isystem $GCC13/include/c++/$GXX_VER \
 -isystem $GCC13/include/c++/$GXX_VER/$GXX_TRIPLE --gcc-toolchain=$GCC13"

# Boost: shared or PIC. Each token reaches the linker as -Wld,<token>, so no spaces inside a token.
export BOOST_INCLUDE=<boost-install>/include
export BOOST_LIBS="-L<boost-libdir> -lboost_program_options"

# xrun cannot pass -Wl,-rpath,<dir>, so runtime library paths come from here.
export LD_LIBRARY_PATH="<boost-libdir>${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
```

A project's own `include/make/shared.mk` or `rundir/Makefile` must append to `EXTRA_CXX_FLAGS` and `EXTRA_LD_FLAGS` with `+=`. A plain `=` there discards the site value.

## 5. Make targets and commands

Run every command from the project's `rundir/`.

### 5.1 Targets

| Command | Builds |
| :--- | :--- |
| `make -j8 USE_VCS=1 all` | `build/run_<topology>` for `VL_INST`, `VL_TYPE`, `VL_TANDEM` (default `build/run_<HDL_TOP_MODULE>_verif`) |
| `make -j8 USE_VCS=1 VL_TANDEM=1 all` | `build/run_<HDL_TOP_MODULE>_verif_tandem` |
| `make -j8 USE_VCS=1 VL_INST=top.u_child all` | `build/run_top.u_child_verif` |
| `make -j8 USE_VCS=1 VL_DUT= all` | `build/run_model`, no RTL in the build |
| `make -j8 USE_VCS=1 vcs_snapshots` | `build/run_model` plus one snapshot per `DUT_TOPOLOGIES` configuration. The links run in sequence because they share `AN.DB` and `csrc` |
| `make -j8 USE_XCELIUM=1 all` | `build_xrun/run_<topology>`, same selection as VCS |
| `make -j8 USE_XCELIUM=1 xrun_snapshots` | `build_xrun/run_model` plus one snapshot per configuration. The elaborations run in parallel |
| `make USE_VCS=1 gen`, `make USE_XCELIUM=1 gen` | generation including `.gen/vl` boundary files |
| `make help USE_VCS=1`, `make help USE_XCELIUM=1` | targets and flow variables. The parse checks need `VCS_HOME`, or `XCELIUM_TOOLS` and `XRUN_GCC_VERS`, and also `BOOST_INCLUDE` and `LD_BOOST` or `BOOST_LIBS`, plus `SYSTEMC_INCLUDE` and `SYSTEMC_LIBDIR` under VCS. Placeholders satisfy them |
| `make help-hooks` | every `EXTRA_*` hook, the command it feeds, and its value |
| `make clean` | the database, `.gen/`, `build/`, `build_xrun/`, and in the rundir `AN.DB`, `csrc`, `vc_hdrs.h`, `vcs.log`, `vlogan_*.log`, `xcelium*.d`, `xrun*.log` and `xrun*.history`, whatever switch is set. Run it from the project root, which reads no toolchain variable. From `rundir/` it needs the same variables as a build |

- `vcs_snapshots` and `xrun_snapshots` stop when `VL_DUT=` is given.
- Objects compile once per flow. Each further VCS topology is a link, each further Xcelium topology an elaboration.
- Run a snapshot with the same `--vlInst`, `--vlType` and `--vlTandem` it was built with, or through `dutRun.py`:

```text
./build/run_top_verif top --vlInst top --vlType verif
./build_xrun/run_top_verif top --vlInst top --vlType verif
../builder/dutRun.py build/run top --vlInst top.u_child --vlType verif --vlTandem
```

### 5.2 What the VCS flow runs

1. `vlogan $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) -F a2c.f <HDL hooks> -F rtl.f <RTL modules> $(VCS_LIB_SV_FILES) +incdir+common/systemVerilog +incdir+<wrapper dirs>`, in `VCS_RUNDIR`, log `vlogan_rtl.log`.
2. Per HDL top: `vlogan ... -sc_model <top> -sc_portmap .gen/vl/<top>.portmap +incdir+common/systemVerilog +incdir+<wrapper dirs> <wrapper.sv>`, log `vlogan_<top>.log`. The wrapper includes `hdlBoundary.svh` from `common/systemVerilog`. The shells land in `csrc/sysc/include/<top>.h`, which the registrar objects include. `-sc_model` takes one source file per call and the calls share `AN.DB`, so they run in sequence.
3. Clang compiles the C++ with `-DVCS -DVCS_DUT`.
4. Before each link the recipe deletes VCS's cached per-binary topologies, every `csrc/sysc/<dir>` that holds a `sysc_skeleton.v`. Then `vcs $(VCS_OPTS) $(VCS_ELAB_OPTS) -syscelab <each DUT_ELAB_ARGS word> $(EXTRA_VCS_OPTS) <libs> <objects> sc_main -o build/run_<topology>`, with `MAKEFLAGS` and `MFLAGS` cleared so VCS's internal make inherits no jobserver. Log `vcs.log`.
5. A failed link deletes `csrc`, `AN.DB` and both analysis stamps, so the next build redoes the analysis.

### 5.3 What the Xcelium flow runs

1. Clang compiles the C++ with the Cadence defines and `-fPIC` into `build_xrun/<project>.build/`.
2. One `xrun $(XRUN_OPTS) -gcc_vers $(XRUN_GCC_VERS) -clean -xmlibdirname xcelium_<topology>.d $(EXTRA_XRUN_OPTS) -makelib a2c_dut -F a2c.f <HDL hooks> $(EXTRA_XRUN_LIB_OPTS) -F rtl.f <RTL modules> <wrapper tops> -endlib <objects> -Wld,<each link token> +systemc_args+<each DUT_ELAB_ARGS word>` in `XRUN_RUNDIR`, log `xrun_xcelium_<topology>.log`. It compiles the HDL, links the objects into a shared library, and elaborates the snapshot.
3. The build writes `build_xrun/run_<topology>`, a shell script that exports the captured `LM_LICENSE_FILE`, turns each argument into `+systemc_args+<arg>`, and runs `cd <XRUN_RUNDIR> && exec xrun -R -xmlibdirname xcelium_<topology>.d $(XRUN_R_OPTS) $(EXTRA_XRUN_R_OPTS)`.
4. No `-top` is passed. xmelab takes `sc_main` and elaborates every uninstantiated HDL unit as an idle top-level, the unused wrapper tops included.

### 5.4 Where outputs land

| Item | VCS | Xcelium |
| :--- | :--- | :--- |
| C++ objects | `build/<project>.build/` | `build_xrun/<project>.build/` |
| Runnable entry | `build/run_<topology>` (`simv`) | `build_xrun/run_<topology>` (script) |
| Snapshot data | VCS's `build/run_<topology>.daidir`, plus `AN.DB/`, `csrc/` in `VCS_RUNDIR` | `xcelium_<topology>.d/` in `XRUN_RUNDIR` |
| Logs | `vlogan_rtl.log`, `vlogan_<top>.log`, `vcs.log` in `VCS_RUNDIR` | `xrun_xcelium_<topology>.log` in `XRUN_RUNDIR` |
| Change stamps | `build/<project>.build/vcs/` | `build_xrun/<project>.build/xrun/xcelium_<topology>.d/` |
| Boundary files | `.gen/vl/<top>.portmap` | `.gen/vl/<top>_xcelium.h` |

- The stamps record each tool command's full option set (hooks, source lists, link libraries, elaboration arguments, and for the run script `XRUN_R_OPTS`, `EXTRA_XRUN_R_OPTS` and `LM_LICENSE_FILE`). A changed option reruns the affected step even when no file changed.
- The C++ objects do not record their compile flags. A build flavour stamp recompiles them when the flow or `VL_DUT` changes. A changed `A2C_CLANG`, `EXTRA_CXX_FLAGS`, `VCS_HOME` or `XCELIUM_TOOLS` does not. No stamp records `XRUN`, `XRUN_RUNDIR` or `VCS_RUNDIR`, so changing one rebuilds no snapshot and rewrites no run script, although the run scripts embed `XRUN` and `XRUN_RUNDIR`. Run `make clean` after changing any of these.
- VCS and Xcelium outputs coexist. VCS shares `build/` with the plain and Verilator flows, and Xcelium has its own `build_xrun/`.

### 5.5 Regressions

The builder provides the snapshot targets and the dispatcher. It has no simulator regression target. A project writes one regression file per simulator and runs it with `regrLauncher.py --build <file>`, optionally through its own `rundir/Makefile` target.

```json
"build": {
    "command": "make -j8 USE_VCS=1 vcs_snapshots",
    "command+": [
        "DUT_TOPOLOGIES+=top:verif,verif:tandem,model:tandem",
        "DUT_TOPOLOGIES+=top.u_child:verif,verif:tandem,model:tandem"
    ],
    "timeout": 900
},
"run": {
    "command": "../builder/dutRun.py build/run top",
    "rules": ["default.json", "vcs.json"],
    ...
}
```

- The launcher joins a `command+` list with spaces onto `build.command`. Command-line `DUT_TOPOLOGIES+=` entries replace the builder default.
- A command-line `DUT_TOPOLOGIES`, such as the regression build command's, replaces any value the rundir Makefile sets.
- Xcelium uses `make -j8 USE_XCELIUM=1 xrun_snapshots` and `../builder/dutRun.py build_xrun/run <testbench>`.
- Take the configurations from each block's tests: `verif` for `--vlType verif`, `verif:tandem` for `--vlType verif --vlTandem`, `model:tandem` for `--vlType model --vlTandem`. Tests that run on `run_model` need no entry.
- Set `session.jobs` to the runtime licence count and do not pass `-j` to the launcher, which overrides it. A `rundir/Makefile` target modelled on the examples' `regr` passes `-j$(REGR_JOBS)`. Drop it, or set `REGR_JOBS` to the licence count. A VCS run beyond the seat count waits in `Queuing for License` until its timeout.
- Allow for snapshot build time in `build.timeout`.

Sample rules files, kept in `rundir/` beside `default.json`. The regrLauncher matches each `re` in multiline mode over the whole log.

```json
{
  "name": "vcs",
  "filters": {
    "vcs_error": { "re": "^Error-\\[(?P<code>[^\\]]+)\\]\\s*(?P<msg>.*)$", "msg": "(\\g<code>) \\g<msg>", "file": null, "sev": "error" },
    "vcs_fatal": { "re": "^Fatal-\\[(?P<code>[^\\]]+)\\]\\s*(?P<msg>.*)$", "msg": "(\\g<code>) \\g<msg>", "file": null, "sev": "fatal" }
  },
  "modifiers": {}
}
```

```json
{
  "name": "xcelium",
  "filters": {
    "xm_error": { "re": "\\*E,(?P<code>[A-Z0-9_]+)\\b:?\\s*(?P<msg>.*)$", "msg": "(\\g<code>) \\g<msg>", "file": null, "sev": "error" },
    "xm_fatal": { "re": "\\*F,(?P<code>[A-Z0-9_]+)\\b:?\\s*(?P<msg>.*)$", "msg": "(\\g<code>) \\g<msg>", "file": null, "sev": "fatal" }
  },
  "modifiers": {}
}
```

## 6. User hooks

The project appends to the `EXTRA_*` hooks with `+=` in `include/make/shared.mk`. `make help-hooks` prints each one with its value, and `manage-build` holds the full table. The simulator hooks `EXTRA_VLOGAN_OPTS`, `EXTRA_VCS_LIB_SV_FILES`, `EXTRA_VCS_OPTS`, `EXTRA_XRUN_OPTS` and `EXTRA_XRUN_LIB_OPTS` are described there. These also matter for the simulator flows:

| Hook | Feeds |
| :--- | :--- |
| `EXTRA_XRUN_R_OPTS` | `xrun -R` in each run script, for simulation plusargs. No single quotes (`USE_XCELIUM`) |
| `EXTRA_HDL_FILES`, `EXTRA_HDL_F_FILES`, `EXTRA_HDL_INCDIRS`, `EXTRA_HDL_DEFINES` | Verilator, the `vlogan` RTL analysis and the `xrun` DUT library, after `a2c.f` and before `rtl.f`. Give absolute paths. Under VCS, name every file a `.f` list needs, because `vlogan` ignores `-y` |
| `EXTRA_LD_FLAGS` | the native link, the `vcs` link, and the `xrun` link as `-Wld,<word>` per word |
| `EXTRA_CXX_FLAGS` | the C++ compile, after every builder flag |

VCS has no run hook, because `simv` takes the test's own arguments.

A builder layer adds its own arguments through `A2C_LAYER_CXX_FLAGS`, `A2C_LAYER_CPP_INCLUDES`, `A2C_LAYER_LD_FLAGS` (which also reach the `xrun` link as `-Wld,`), `A2C_LAYER_HDL_F_FILES`, `A2C_LAYER_VCS_LIB_SV_FILES` and `A2C_LAYER_UVM_F_FILES` (the `-F` lists of its UVM agent packages). Their position relative to the builder and project arguments is in `manage-build`.

## 7. Bring-up checklist and troubleshooting

### 7.1 Checklist

1. Install Clang (section 2.1) and confirm it compiles and runs `<format>` code against GCC 13's libstdc++ with the flags you put in `EXTRA_CXX_FLAGS`:

    ```bash
    printf '#include <format>\nint main(){return std::format("{}",1).size()!=1;}\n' |
      "$A2C_CLANG" -std=c++23 $EXTRA_CXX_FLAGS -x c++ - -o /tmp/a2c_format_probe && /tmp/a2c_format_probe && echo format-ok
    ```

2. Install a shared or PIC Boost, or confirm the OS one, and its headers.
3. Write the site script from section 4 and source it.
4. In a scratch copy of an example, run `make db`, then dry-run the flow with `make -n USE_VCS=1 all` or `make -n USE_XCELIUM=1 all`. Check that the compile lines carry your Clang, `EXTRA_CXX_FLAGS` and the simulator macros, and that the link line carries `BOOST_LIBS`. With a current database the dry run prints the tool commands without running them. Make still writes its parse-time stamps, and GNU Make remakes an out-of-date database even under `-n`.
5. Build and run one topology (section 8.2).
6. Build the snapshot set and run a regression (section 5.5).

### 7.2 Failure modes

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `VCS_HOME is not set`, `XCELIUM_TOOLS is not set` or `XRUN_GCC_VERS is not set`, also under `make -n` or `make clean` | the checks run while make parses | source the site script, or give placeholder values for a dry run. Run `make clean` from the project root |
| `LD_BOOST is not set` | `BOOST_LIBS` unset or empty, Xcelium included | set a non-empty `BOOST_LIBS` or `LD_BOOST` |
| `vcs_snapshots links the DUT snapshots; VL_DUT= selects ...` or `xrun_snapshots builds the DUT snapshots; VL_DUT= selects the model-only snapshot` | `VL_DUT=` with a snapshot-set target | drop `VL_DUT=` |
| `'X' has different definitions in different modules` (Clang) | Clang 16 | use Clang 18 or newer |
| `recursive lazy load`, `Bad file data` or an internal compiler error on a `.cppm` | GCC on the module units | use Clang |
| `'format' file not found` | libstdc++ older than GCC 13 | point Clang at GCC 13 (section 2.2) |
| VCS `Error-[SC-VCS-SYSC-ELAB]` with an assertion in the DWARF reader of `simv_elab` | DWARF 5 objects | `-gdwarf-4` in `EXTRA_CXX_FLAGS`, then `make clean` |
| VCS link: undefined reference `...@GLIBCXX_3.4.32` from `libsystemc` | a libstdc++ older than GCC 13.2 at link or run time | GCC 13.2 or newer toolchain for `vcs`, its `lib64` on `LD_LIBRARY_PATH` |
| VCS compile errors on conflicting `int64` or `uint64` definitions | a third-party library that defines `int64` or `uint64` collides with the stock VCS SystemC headers | point `SYSTEMC_INCLUDE` at a copy of the VCS SystemC headers patched to avoid the collision |
| VCS `Error-[SE]` naming a `.so` file | `vcs` reads a bare library path in `BOOST_LIBS` as Verilog source | use `-L<dir> -l:<library file name>` |
| VCS `Error-[NTMES] No TopModule/Entity supplied` | `csrc` or `AN.DB` left by an interrupted link | rerun `make`. A failed link cleans them. After a killed build, `make clean` |
| VCS `Error-[SV-UIOT] Undefined interface or type` | a design unit reachable only through a `-y` directory, which `vlogan` does not search | add it with `EXTRA_VCS_LIB_SV_FILES`, or name the file in the `.f` list |
| VCS run `Warning-[SC-ELAB-VHAN-I2] Cannot find Verilog input object` | run arguments differ from the snapshot's topology | run through `dutRun.py` or with the build's `VL_*` values |
| VCS run `Warning-[RT_UO] Unsupported option` per a2c option | `simv` sees options it does not know | harmless. Do not add `-suppress=RT_UO` to the run arguments; the a2c option parser rejects it |
| VCS link `make[2]: *** read jobs pipe: Bad file descriptor` | VCS's internal make inheriting the jobserver (seen with GNU Make 4.2.1) | the builder clears `MAKEFLAGS` for `vcs`. The `jobserver unavailable: using -j1` warning that follows is expected |
| VCS runs `Queuing for License` until timeout | more parallel runs than runtime licences | lower `session.jobs` |
| Two VCS builds in one rundir fail or remove each other's `csrc` | they share `AN.DB`, `csrc` and `vcs.log` | one VCS build or regression per rundir at a time |
| Xcelium `*E,NODEFP` | an `EXTRA_HDL_*` unit with a parameter without default, elaborated as an idle top | give every parameter a default, or leave unused units off the list |
| Xcelium `*F,CUSCTOP` | `-top` given | do not pass `-top` |
| Xcelium `*E,SVNT2S` | a 2-state net type such as `wire int unsigned` in RTL | declare a variable and drive it with `assign` |
| Xcelium `xmsim *F,SCOBNF: SystemC object ... not found` | run arguments build a hierarchy the snapshot lacks, for example a model/model tandem test on `run_model` | add the configuration to `DUT_TOPOLOGIES` |
| Xcelium `SCK1026`, `sc_main` did not call `sc_start` | `sc_main` returned before its first `sc_start` during elaboration, for example with `Invalid testBench selected` because `DUT_TESTBENCH` names no testbench | set `DUT_TESTBENCH` |
| Xcelium link `R_X86_64_32 ... can not be used when making a shared object` | static non-PIC library, often Boost | use a shared or PIC build |
| Xcelium link options split wrongly | `xrun` forwards each `-Wld,` argument as one token, so `-Wl,-rpath,<dir>` and tokens with spaces cannot pass | keep `BOOST_LIBS` and `EXTRA_LD_FLAGS` tokens space-free, set runtime paths with `LD_LIBRARY_PATH` |
| Xcelium run `*F,VSPLIC` outside make | no licence in the run environment | set `LM_LICENSE_FILE` before the build so the script captures it |
| `xrun` returns at once with no snapshot | `xrun` on `PATH` is a batch-submission wrapper | set `XRUN=$XCELIUM_TOOLS/bin/xrun` |
| Xcelium compile error on `sc_bind` in project code | Cadence's SystemC defines `sc_bind` as a macro | bind with a lambda |
| `dutRun: no snapshot ...` | topology missing from the snapshot set | add the configuration to the block's `DUT_TOPOLOGIES+=` entry |
| Builds use stale settings after a tree move, a compiler or simulator path change, or an edit under `include/make/` | object flags, dependency files, run scripts and snapshots hold absolute paths and untracked flags | `make clean` from the project root, then rebuild |

Harmless warnings: Xcelium `*W,SCK910` on `sc_start(0)`, `SPDUSD` and `LIBNOU` for unused include and library directories from `a2c.f`.

### 7.3 Behaviour to know

- Under Xcelium, `sc_main` runs twice: once under xmelab during the snapshot build, up to the first `sc_start`, and again under xmsim for each run. Code before `sc_start` runs in both, so side effects such as file writes happen at build time too.
- The HDL wrappers fail a run on an X or Z at a port whose interface type has a UVM agent (section 9.4). That applies to every VCS and Xcelium run with an RTL DUT, not only to UVM runs.
- `xrun_snapshots` runs each topology's testbench while it builds the snapshot, so an X or Z in that run fails the snapshot build, before any regression test starts.
- `--vlTrace` has no effect under VCS or Xcelium. Under VCS, build with `VCS_DEBUG=1` and run with `+fsdbTrace` for FSDB waveforms. This needs Verdi's FSDB support in the VCS install. The Xcelium flow has no built-in waveform switch; pass the site's probe options through `EXTRA_XRUN_R_OPTS` or `EXTRA_XRUN_OPTS`.

## 8. Verification

### 8.1 Without a simulator

The unit tests `test_xcelium_boost_libs.py`, `test_make_user_hooks.py`, `test_vl_boundary_pin_widths.py`, `test_vl_boundary_widths_build.py` (which needs Verilator and Clang) and `test_transit_surface_classification.py` cover the Boost link rules, the hook placement and stamps in the `vlogan`, `vcs` and `xrun` commands, and the boundary widths and pins, with placeholder tool paths. Run each from `builder/base/unittest` with `python3 <test>.py`. The fixture at `unittest/fixtures/vl-boundary-widths/top/rundir` is intended as a simulator check through `make USE_VCS=1 vcs_snapshots` and `make USE_XCELIUM=1 xrun_snapshots`, but it is untested under either simulator.

### 8.2 With the simulator installed

Use `examples/hierVlDemo` (testbench and HDL top `hierVlDemo`). From `builder/base`, run each flow in its own shell, with only that flow's site script sourced, because the two scripts set `EXTRA_CXX_FLAGS`, `BOOST_LIBS` and `LD_LIBRARY_PATH` differently.

Xcelium:

```text
source site-xcelium.sh
cd examples/hierVlDemo && make clean && cd rundir
make -j8 USE_XCELIUM=1 all
./build_xrun/run_hierVlDemo_verif hierVlDemo --vlInst hierVlDemo
```

VCS:

```text
source site-vcs.sh
cd examples/hierVlDemo && make clean && cd rundir
make -j8 USE_VCS=1 all
./build/run_hierVlDemo_verif hierVlDemo --vlInst hierVlDemo
make -j8 USE_VCS=1 VL_DUT= all
./build/run_model hierVlDemo
```

- Each run ends with `No error` and exits 0. A VCS run also prints the VCS simulation report.
- Tested with: this example under Xcelium 26.03, `No error`. The VCS flow and both snapshot sets were tested on a larger multi-block design (a 44-test regression passing under each simulator), not on this example.
- If a run fails to start, check `ldd build/run_<topology>` (VCS) for unresolved libraries, and the log files of section 5.4.

## 9. UVM testbenches

A block with `hasUvm: true` gets a generated SystemVerilog UVM testbench that drives either its SystemC model or its RTL, under Xcelium or VCS. SystemC stays on top, and `sc_main` and `main.cpp` run as they do for every testbench. SystemC instantiates the UVM testbench module the way it instantiates an HDL wrapper top, through the `vlogan -sc_model` shell under VCS and an `xmsc_foreign_module` shell under Xcelium.

Base generates the testbench module, the variant package with its register model and `uvm_env`, the SystemC side, and a test package with a base test and a fail test. `make USE_UVM=1` builds and runs it (section 9.7). The project writes its scoreboards, sequences and tests in the user spans of the test package (section 9.6). isp_debayer and isp_gain are the worked examples.

### 9.1 Opting a block in

`hasUvm: optional(false)` is a block flag beside `hasVl`, independent of `hasTb`. `projectCreate.validateUvmBlocks` stops `make db` when a `hasUvm` block:

- has `hasVl: false`, because the testbench drives the block's HDL wrapper;
- has params but no standalone variant, so it would get no testbench top;
- declares no `ports:`;
- has an output clock or reset, because the testbench drives every clock and reset and samples none;
- has a boundary port whose interface type lacks `uvmAgent: true`. A boundary port comes from `ports:`, a `connectionMaps` boundary row, `registerPorts:`, or a `memoryConnections` or `registerConnections` row naming an instance of the block. A `memoryConnections` port has type `memory`, and a `registerConnections` port the type its register's `regType` maps to: `status` for `rw` and `ro`, `external_reg` for `ext`, `memory` for `memory`. The error names the port and the type, and the interface or the row it comes from. A type carries the flag in its definition, `interfaces/<type>/<type>_if.yaml`;
- has a port, clock or reset whose name the testbench module already uses: `dut`, `uvm_done`, `uvm_errors`, `rtl_dut`, `srv`, `<clock>_if` for any of its clocks, or `<port>_<signal>` for any of its pins;
- has a register named `block`, whose class `<block>_reg_block` would be the register block class;
- has a register field named like a `uvm_reg` member, or a register or memory named like a `uvm_reg_block` member;
- has a register or memory row wider than 64 bits (`UVM_REG_DATA_WIDTH`) at any standalone variant. A memory row within 64 bits can still exceed it once padded to the decoder's row stride (section 9.5); the message then names the parameters whose `maxValue` sizes that stride.

`raw` has limited support. It is complete against the RTL DUT and best effort against the model DUT, because the SystemC raw BFM is not transactional and can lose a word. `rules/dev-skills/authoring-interface-definitions.md` has the details.

### 9.2 Generated files

The files go in the `uvm` segment, `$root/uvm` in the functional layout and `<node>/uvm` in the hierarchical one. Its buildGroup is also `uvm`, which only the `USE_UVM` flow builds, so no UVM file reaches the model, Verilator or plain RTL compile lists. `<stem>` is `<block>_<variant>` for each standalone variant of a block with params, and `<block>` for a block without params, which has one top.

| fileMap entry | File | Per | Content | Template |
| :--- | :--- | :--- | :--- | :--- |
| `uvmPkg` | `<stem>_uvm_pkg.sv` | standalone variant | package `<stem>_uvm_pkg`. The `items` section holds the variant's parameter values as localparams, the block's parameterized types, per port the typedefs `<port>_agent_t`, `<port>_item_t`, `<port>_config_t` and `<port>_vif_t`, then the register model and `<block>_env` (section 9.5). A user region follows the items | `templates/systemVerilog/uvmPkg.py` |
| `uvmTest` | `<block>_uvm_test_pkg.sv` | block, shared by its variants | package `<block>_uvm_test_pkg`, which imports the variant package that `` `A2C_UVM_PKG `` names. Generated sections hold `<block>_base_test` and `<block>_fail_test`; two user spans hold the project's env subclass, scoreboards, sequences and tests (section 9.6) | `templates/systemVerilog/uvmTest.py` |
| `uvmTb` | `<stem>_uvm_tb.sv` | standalone variant | module `<stem>_uvm_tb`, which imports the test package so the factory registers its tests. Its ports are the HDL top's pins with port directions inverted, then the clocks and resets as inputs, then the completion outputs `uvm_done`, the 32-bit `uvm_errors` and `rtl_dut`. A one-bit pin is a scalar `bit`, matching the `bool` the simulator shell binds, and a vector payload width is `$bits` of the package-qualified type. It holds one `<type>_if` per port, one `a2c_clk_if` per clock, the RTL wrapper as instance `dut` under `` `ifdef A2C_UVM_RTL_DUT `` with the pins toward SystemC tied off, the `uvm_config_db` keys and `run_test()`. User regions take imports and module body | `templates/systemVerilog/uvmTb.py` |
| `uvmScWrap` | `<block>_uvm_sc_wrapper.h` | block | class template `<block>_uvm_sc_wrapper<TB_T, Config>` over the simulator shell `TB_T`, or `<TB_T>` alone for a block without params. It drives the clocks and resets into the shell, with resets born low. With the model DUT it also holds the model, its channels and the BFMs in the DUT's swapped roles. The BFMs change the pins only between a rising edge and the next falling edge, where the agents' monitors sample, so a model read through `memory_dst_bfm` takes two edges and the model's back-to-back reads run at one per two clocks. A block with params creates its model with `createInstance<<block><Config>>`, as a container creates a child typed by its Config, which has no factory registration; a registration under the variant still wins. It waits for `uvm_done` and ends the run | `templates/systemc/module_uvm_sc_wrapper.py` |
| `uvmTbConfig` | `<block>UvmConfig.cpp` | block | testbench config `uvmTbConfig`, registered under the testbench name `<block>_uvm`, with options `--uvmDut` and `--uvmTop`. `--uvmTop <stem>` selects the variant through a generated map, so the config serves every top of the block | `templates/systemc/uvmTbConfig.py` |
| `uvmRegistrar` | `<block>UvmRegistrar.cpp` | block | registers the wrapper as `<block>_uvm` once per standalone variant, over that variant's shell and Config | `templates/systemc/uvmRegistrar.py` |

`make newmodule` scaffolds the test package once, with a working `<block>_tb_env` and an empty `<block>_smoke_test` in its user spans, so the generated tests compile and pass before any user code exists. `make gen` rewrites only the generated sections of every file.

The templates guard two of these files with `#if defined(XCELIUM) || defined(VCS)`, each for its own reason:

- `<block>UvmRegistrar.cpp` includes the simulator shells, `<tbModule>_xcelium.h` under `XCELIUM` and the `vlogan` shell `<tbModule>.h` otherwise, and only those two builds write them.
- `<block>UvmConfig.cpp` includes no shell. It creates the wrapper through the factory key `<block>_uvm`, and only the guarded registrar registers that key. Unguarded, it would offer a `<block>_uvm` testbench in a build that cannot create its wrapper.

A block with `hasMdl: false` gets the RTL DUT only. Its testbench module holds the RTL with no `A2C_UVM_RTL_DUT` branch, its wrapper has no model, channels or BFMs, and its config accepts only `--uvmDut rtl`, the default.

`make gen` under `USE_VCS` or `USE_XCELIUM` also writes two boundary files per testbench top, in the same `--vlBoundary` run as the HDL tops' (section 1.5):

| File | Content |
| :--- | :--- |
| `.gen/vl/<tbModule>.portmap` | the VCS port map for `vlogan -sc_model <tbModule>` |
| `.gen/vl/<tbModule>_xcelium.h` | `class <tbModule> : public xmsc_foreign_module`, which the registrar includes under Xcelium |

Both come from `projectOpen.getUvmTopBoundaryPins`. It takes the HDL top's pins from `getVlTopBoundaryPins`, inverts the port directions, leaves clocks and resets as inputs, and adds the three completion pins.

### 9.3 Names and manifest records

`projectCreate.deriveUvmNames` persists every name as the `UVMNAMES` config, keyed by block. Templates and the manifest read it and never derive a name from a file name.

| Field | Value |
| :--- | :--- |
| `scWrapperClass`, `scWrapperHeader` | `<block>_uvm_sc_wrapper`, `<block>_uvm_sc_wrapper.h` |
| `runClass` | `<block>_uvm_run`, the static run state the config and the wrapper share |
| `testbenchName` | `<block>_uvm` |
| `duts` | `['model', 'rtl']`, or `['rtl']` for a block with `hasMdl: false`. The first is the default |
| `envClass`, `regBlockClass` | `<block>_env`, `<block>_reg_block` |
| `testPkgName`, `tbEnvClass` | `<block>_uvm_test_pkg`, `<block>_tb_env` |
| `baseTestClass`, `smokeTestClass`, `failTestClass` | `<block>_base_test`, `<block>_smoke_test`, `<block>_fail_test` |
| `tops[<variant>]` | one row per standalone variant, or one row under `''` for a block without params. Each row holds `stem`, `tbModule`, `pkgName`, `hdlTop`, `portmap`, `xceliumShell`, `xceliumShellHeader`, `vcsShellHeader` and the per-variant register widths. `stem` is the name `UVM_TOP` and `--uvmTop` take. `hdlTop` is the HDL wrapper top the testbench instantiates, and `portmap` and `xceliumShell` are paths under `.gen/vl` |

The config creates the wrapper with `instanceFactory::createInstance("", "<block>", "<block>", <variant>, <project>)` after `registerInstance("<block>", "uvm")`. The wrapper instance therefore takes the block's name, and the model under it sits at `<block>.<block>`. Log paths and synchLock keys use that path.

`config/createBuildManifest.py` records one `uvmTops` entry per testbench top of the harness owner's `hasUvm` blocks, plus `uvmDirs`, the registrar sources and each block's default top. A reused child's UVM files belong to the child's own build. `.gen/build.mk` carries:

| Variable | Content |
| :--- | :--- |
| `A2C_UVM_TOPS` | every testbench module name |
| `A2C_UVM_TOP_STEMS` | every top's stem, the values `UVM_TOP` accepts |
| `A2C_UVM_DEFAULT_TOP_<block>` | the stem of the top at the variant of the block's DUT-top wrapper, the same choice as `A2C_VL_TOP_<block>` |
| `A2C_UVM_TB_TOP_<stem>` | the testbench module of that stem |
| `A2C_UVM_PKG_<top>` | the name of the top's variant package, which `a2c-uvm.mk` passes as `A2C_UVM_PKG` |
| `A2C_UVM_TESTBENCH_<top>` | the testbench name, `<block>_uvm` |
| `A2C_UVM_DUTS_<top>` | the block's DUT list; the first is `UVM_DUT`'s default |
| `A2C_UVM_PKG_SV_<top>` | that top's variant package file |
| `A2C_UVM_TEST_SV_<top>` | its block's test package file |
| `A2C_UVM_TB_SV_<top>` | that top's testbench module file |
| `A2C_UVM_PORTMAP_<top>` | `.gen/vl/<top>.portmap` |
| `A2C_UVM_REGISTRAR_SRC` | the registrar sources, which compile after the shells they include |
| `A2C_UVM_SRC_DIRS` | the `uvm` segment directories, which hold the generated C++ |

The manifest leaves the `uvm` rows' `.cpp` files out of the SystemC source list. `a2c-uvm.mk` adds `$(A2C_UVM_SRC_DIRS)` to the source directories under `USE_UVM` only. The only prerequisite of `VL_BOUNDARY_STAMP` is the database (`include/make/a2c-common.mk`). `A2C_VL_TOPS` decides only whether the stamp joins `GEN_DEPS`, and it is never empty for a `hasUvm` block, because it holds each testbench's HDL top.

### 9.4 X and Z checks on four-state simulators

The HDL wrapper's pins and the testbench module's pins are two-state `bit`, so an X from the RTL reaches the UVM monitors and the SystemC BFMs as 0. Every generated HDL wrapper therefore instantiates a `<type>_xcheck` module on each port of a flagged type, on the port's own clock and reset, as `specs/spec-verilated-wrappers.md` section 9 describes. A checker fails the run on its first X or Z once reset has been asserted and released. It always checks the control signals, and checks the payload only while the protocol's valid signals qualify it. It prints `A2C_XZ <time> <path>: <signal> is X or Z` and calls `errorCode::fail` through the DPI function `a2c_xz_fail` in `common/systemc/xzCheck.cpp`. The run exits non-zero, and the `exit_code` filter that projects keep in their `default.json` fails it.

- The checks run in every VCS and Xcelium run with an RTL DUT, UVM or not.
- Verilator never compiles them. The instances sit inside `` `ifndef VERILATOR ``.
- Under Xcelium, `xrun_snapshots` runs each topology's testbench once while it builds the snapshot, so a real X fails the snapshot build itself. A UVM snapshot is built with `-elaborate` and does not simulate at build time.
- The run's summary line shows the `A2C_XZ` reason unless a later `errorCode::fail` replaced it, because `errorCode::fail` keeps only the last reason. The `A2C_XZ` `$display` in the log always names the port and signal.

The per-type rules are in section 9.10, and what a new type's checker must ship is in `rules/dev-skills/authoring-interface-definitions.md`.

Tested with: the SystemC regressions of a ten-block image pipeline, run with the checkers elaborated under Xcelium and VCS.

### 9.5 The environment and the register model

The `items` section of the variant package holds both, generated whole. A project extends the env in its test package and never edits this file's generated sections.

`<block>_env extends uvm_env` holds:

- one `<port>_agent` per boundary port, in port order, configured in `build_phase` from a `<port>_config_t` object. The config takes the `virtual <type>_if` from `uvm_config_db` under the port name and `clk_vif` from the port's own clock domain, so a multi-clock block needs no hand wiring. Every agent gets a role, the opposite of the DUT port's direction, `A2C_SRC` on a DUT `dst` port. `no_backpressure` follows the port's effective backpressure on a type whose backpressure is overridable. On an `axi_read` or `axi_write` port the env sets `max_transfer_bytes` and, when the port binds no `id_t`, `id_unbound` (section 9.10). The env sets no agent passive and no `cfg.mem`, so each memory-backed agent creates its own model. A DUT `src` port gets an `A2C_DST` agent that serves it: on a DUT apb `src` port that is `apb_slave_driver`, with no sequencer. The register model stays on the register-bus port, so a block that is a bus target and a bus master gets one `A2C_SRC` agent with the register model and one serving `A2C_DST` agent per downstream apb port;
- one `<port>_counter`, an `a2c_uvm_pkg::a2c_txn_counter`, per DUT output with a handshake: a `src` port of an elastic type that is not an address-bus type. Those types are `rdy_vld`, `axi4_stream`, `push_ack`, `notify_ack`, `req_ack`, `pop_ack`, `axi_read`, `axi_write` and Pro's `lmmi`. The counter counts the monitor's `ap` items, so on `pop_ack` it counts the DUT's pops, on `axi_read` its read bursts and on `axi_write` its write bursts. `connect_phase` connects the output monitor's `mon.ap` to its `analysis_export`;
- one `virtual a2c_clk_if` per clock, as `<clock>_vif`;
- with a register model, `regmodel`, the bus's `<type>_reg_adapter` as `adapter`, and a `uvm_reg_predictor` as `predictor`. `build_phase` builds the model and calls `regmodel.reset()`. `connect_phase` sets the bus agent's sequencer and the adapter on `default_map`, turns auto-prediction off, and feeds the predictor from the bus monitor, so the mirror follows bus traffic from any sequence.

`a2c_txn_counter #(T)` (`common/systemVerilog/uvm/a2c_uvm_pkg.sv`) is a `uvm_subscriber`. It counts transactions and checks nothing about their content. `expect_count(n)` adds n to the expected count. `wait_for_count(clk_vif, deadline_cycles, quiet_cycles)` waits for the expected count, reports a shortfall as `UVM_ERROR` id `A2C_TXN_COUNT` when the deadline passes, then waits the quiet window and reports any excess the same way. A clock with no edge for the counter's `clock_stop_cycles` periods (default 1000) has stopped, which reports the shortfall or ends the quiet window at once. `check_phase` reports what no wait covered. A transaction that arrives after its shortfall was reported is logged as late, not counted again, until the next `expect_count()`.

The register model is generated from the block's address rows, so it cannot disagree with `fw/<block>RegAddresses.h` on an offset:

- one `<block>_reg_<register>` (`uvm_reg`) per `registers:` row, with one `uvm_reg_field` per structure member at its packed position, the first member most significant. Padding members are fields too, because the decoder flops them. Each field's reset is its share of `defaultValue`. `rw` registers are `RW` and their fields `rand`; `ro` and `ext` registers are volatile, and `ro` is `RO`;
- one `uvm_mem` per `memories:` row with `regAccess`, and one `RW` memory per `regType: memory` register. A `wo` memory is `RW` with `WO` map rights and gets `NO_MEM_TESTS`, because UVM reports WO rights as RW in a one-map model. A memory row is padded so that UVM's stride of `ceil(n_bits / 32)` bus words equals the decoder's row stride, and a padded memory gets `NO_MEM_WALK_TEST`. The padding rule holds for UVM 1.2 only: IEEE 1800.2 steps a memory by `ceil(n_bits / 8)` bytes;
- `<block>_reg_block`, with `default_map` at base 0, a 4-byte bus and little-endian order, each register and memory at its row's offset. Widths, depths and padding are resolved per variant at `make db`. A register wider than the bus becomes consecutive 4-byte accesses.

Only text unit tests cover the memory, ext and multi-word paths. The registers of isp_gain and isp_debayer each fit one 32-bit word.

### 9.6 The test package

`uvm/<block>_uvm_test_pkg.sv` holds the project's tests. Its layout, top to bottom:

| Span | Owner | Content |
| :--- | :--- | :--- |
| `header` | generated | package `<block>_uvm_test_pkg`; imports of `uvm_pkg`, `a2c_uvm_pkg`, the agent packages, the block's type packages and `` `A2C_UVM_PKG ``. An undefined `A2C_UVM_PKG` expands to a package name that says to define it |
| user span 1 | project | `<block>_tb_env extends <block>_env`, with the scoreboards and any helpers; also sequences and other classes the tests use |
| `tests` | generated | `<block>_base_test` |
| user span 2 | project | `<block>_smoke_test` and the project's other tests |
| `footer` | generated | `<block>_fail_test`, then `endpackage` |

`<block>_base_test extends uvm_test` creates the env as `<block>_tb_env::type_id::create("env", this)`, so the project's subclass needs no factory override. Its `run_phase` raises one objection, waits for each clock's reset release, calls `run_body()`, calls `wait_for_outputs()` and drops the objection. A test puts its stimulus in `run_body()` and never handles objections. `wait_for_outputs()` waits on every output counter at once, each on its own port's clock, and a test may call it between frames. The deadline and quiet window are the members `output_deadline_cycles` (default 200000) and `quiet_cycles` (default 1000). A test sets its own defaults in its constructor, and `+a2c_output_deadline_cycles=<n>` and `+a2c_quiet_cycles=<n>` override them, because `build_phase` reads the plusargs afterwards. `clock_stop_cycles` (default 1000, `+a2c_clock_stop_cycles=<n>`) is the counters' stopped-clock threshold, and the Mode B drain's. Mode B is `UVM_DUT=both` (section 9.7): one snapshot holds the RTL, the DUT under test, and the model, its reference, and each agent drives and monitors both pin sets, its DUT lane and its model lane. The Mode B drain at the end of the run phase has its own knobs, described below. `build_phase` hands the clock stop and the drain's knobs to the env through the `uvm_config_db`.

#### The Mode B end-of-test drain

In Mode B every `A2C_DST` agent that answers the DUT (push_ack, notify_ack, req_ack, pop_ack, memory, external_reg and the apb slave) serves both lanes from one model. The DUT lane applies each transaction and records its response in the driver's `a2c_replay_log`; the model lane replays the responses in order. The model lane often trails the DUT lane, so when the run phase's last objection drops, `a2c_replay_drain` holds the run phase until the model lanes catch up. It watches each log on the log's own clock:

- **Settle.** A log settles once both lanes have been idle for `drain_quiet_cycles` clocks in a row: no lane inside a transaction or starting one, no recorded response waiting for the model lane, and the model lane not waiting for one. The drain ends when every log has settled or been given up.
- **Cut.** A log not settled at `drain_deadline_cycles`, whose DUT lane started a transaction within its last `drain_quiet_cycles` clocks, is traffic that never pauses. The drain cuts it after the transactions the DUT lane has started, and both lanes have `drain_catchup_cycles` clocks to complete them. The transactions after the cut go unchecked on both lanes. `drain_catchup_cycles` defaults to the deadline, so a cut whose lanes never complete it takes up to twice the deadline to report. Lower the catch-up to fail sooner.
- **Re-cut.** A test may resume the run phase after a drain, by raising an objection in `phase_ready_to_end()`. The next drain undoes the earlier cuts and starts only if a lane has started a transaction since. A log cut before whose DUT lane has not paused for `drain_quiet_cycles` clocks since is cut again on the first clock.
- **Give-up.** Any other log not settled at its deadline is given up with an `A2C_DRAIN` warning, and its `check_phase` reports what the lanes still owe.
- **Clock stop.** A clock with no rising edge for `clock_stop_cycles` periods and a half has stopped. Its log settles if it is idle and not cut, and is given up otherwise. A settled log is watched again if its clock runs again; a given-up one is not. The steady period changes only when three intervals in a row agree within an eighth. Once a clock has one, neither a gated clock's gap nor a single runt pulse changes it, and a clock that slows by more than the stop limit in one step reads as stopped once. A clock gated in short bursts at uneven gaps may never have three agreeing intervals; until it does, its period is the shortest interval seen, and a runt in that time shortens its stop limit. Several runts in a row can agree with each other and set a short steady period, so with `clock_stop_cycles` of 0 or 1 a burst of glitches can read as a stop. Use 2 or more.

A hand-written test that raises objections only in `main_phase()` drains too: UVM 1.2 calls the run phase's `phase_ready_to_end()` once the runtime phases have ended, which takes no time when the later ones hold no objection.

A hand-written Mode B responder joins the drain by giving its `a2c_replay_log` an `a2c_replay_lanes` implementation. Its `lane_starts()` and `lane_busy()` must change away from the rising edge of the log's `clk_vif`, at the falling edge or the drive point, as the built-in drivers do. The drain reads them at the rising edge. A driver that counts in an `@(posedge clk)` process races it, so the drain can end in that time step before the count moves and leave a false `A2C_REPLAY`.

| Member of `<block>_base_test` | Plusarg | Default |
| :--- | :--- | :--- |
| `drain_quiet_cycles` | `+a2c_drain_quiet_cycles=<n>` | `quiet_cycles` (1000) |
| `drain_deadline_cycles` | `+a2c_drain_deadline_cycles=<n>` | `output_deadline_cycles` (200000) |
| `drain_catchup_cycles` | `+a2c_drain_catchup_cycles=<n>` | each log's `drain_deadline_cycles` |
| `clock_stop_cycles` | `+a2c_clock_stop_cycles=<n>` | 1000 |
| `drain_cut_expected` | `+a2c_drain_cut_expected=1` | 0 |

A test sets its own values in its constructor and the plusargs override them. The three drain cycle counts start at -1, which takes the default. To give one log its own value, a test sets `a2c_drain_quiet_cycles`, `a2c_drain_deadline_cycles`, `a2c_drain_catchup_cycles`, `a2c_clock_stop_cycles` or `a2c_drain_cut_expected` on the log's path in its `build_phase`, after `super.build_phase()`. The log reads each as `int unsigned`, `int` or `uvm_config_int`, and the flag also as `bit`; `+uvm_set_config_int` on the command line works the same way. The type does not change which value wins. The log takes the entry `uvm_config_db` would pick if every entry had one type: the highest precedence, which in `build_phase` is the setter nearest the top, and of those the last set. So a hand-written env's `int` default does not override the base test's `int unsigned` values, and a later set for one port overrides an earlier blanket one. A winning entry of any other type is ignored with an `A2C_CFG` warning.

| Id | Severity | Meaning | What to change |
| :--- | :--- | :--- | :--- |
| `A2C_CUT` | `UVM_WARNING`; `UVM_INFO` when the cut dropped nothing or `drain_cut_expected` is set | the drain cut a port that never paused; the message gives the transactions left unchecked on each lane, and says whether the cut came at the deadline or on a re-cut's first clock | lower `drain_deadline_cycles` to cut sooner, end the stimulus before the drop, or set `drain_cut_expected` where the port is meant to stay busy to the end |
| `A2C_DRAIN` | `UVM_WARNING` | a log neither settled nor still flowing at its deadline, or its clock stopped with a transaction open; the message says what kept it from settling | read the log's `A2C_REPLAY`. Raise `drain_deadline_cycles` only if the model lane is slow, not short |
| `A2C_REPLAY` | `UVM_ERROR` | at the end of the test a lane owes transactions: recorded responses the model lane never replayed, a model lane waiting for a response the DUT lane never recorded, or a cut the lanes did not reach within `drain_catchup_cycles` | a lane count mismatch is a design or model difference. If the model lane is only slow after a cut, raise `drain_catchup_cycles` |
| `A2C_CFG` | `UVM_ERROR`; `UVM_WARNING` for a knob set as an unread type | a log with `drain_deadline_cycles` below `drain_quiet_cycles`, or with no `clk_vif`; a drain knob whose winning `uvm_config_db` entry is not `int unsigned`, `int`, `uvm_config_int` or `bit` | raise the deadline or lower the window; give the driver's log its clock |

`<block>_fail_test extends <block>_smoke_test` is a self-checking negative test of the counters. After `super.run_body()` it calls `expect_count(missing_count)` on the first output counter, so that output owes more transactions than the DUT sends. `missing_count` defaults to 1 and `+a2c_fail_missing_count=<n>` sets it. An `a2c_error_demoter` turns each `A2C_TXN_COUNT` `UVM_ERROR` into `UVM_INFO` and counts it. In `report_phase` the test raises `A2C_FAIL_TEST` as a `UVM_ERROR` unless exactly one was demoted and no other `UVM_ERROR` or `UVM_FATAL` was raised. A block with no counted output gets no fail test.

The test package reaches the build through the manifest, as `A2C_UVM_TEST_SV_<top>`. A project that needs more SV files adds them by its own means. isp_gain (`uvm/isp_gain_uvm_test_pkg.sv`) holds a scoreboard that computes each output from the register model's mirror, a frame sequence, and smoke, register, unity-gain, per-colour, random and fail tests.

### 9.7 Building and running

`USE_UVM=1` with `USE_XCELIUM=1` or `USE_VCS=1` includes `include/make/a2c-uvm.mk`. It stops make without one of the two, and with `VL_DUT=` empty. `VL_DUT` compiles the block's RTL into the snapshot, which every UVM snapshot needs, because the testbench module instantiates the RTL in its rtl branch.

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `UVM_TOP` | `A2C_UVM_DEFAULT_TOP_<HDL_TOP_MODULE>` | the testbench top's stem, `<block>_<variant>` or `<block>` |
| `UVM_DUT` | the first of `A2C_UVM_DUTS_<top>`: `model`, or `rtl` for a block with no model | the DUT the snapshot holds. `rtl` adds `+define+A2C_UVM_RTL_DUT`. `both` adds `+define+A2C_UVM_BOTH_DUT` and builds Mode B, the RTL beside the model as its reference (section 9.6). A block with no model has neither `model` nor `both` |
| `UVM_TEST` | empty | the `+UVM_TESTNAME` the run script adds when a run names none |
| `UVM_TOPOLOGIES` | `<UVM_TOP>:<each DUT of its block>` | what `uvm_snapshots` builds: space-separated `<top>:<dut>[,<dut>]` entries |

`make gen` checks `UVM_TOP` and `UVM_DUT` against the manifest and names the valid values. Under `USE_UVM` the flow sets `VL_INST` empty, `DUT_TOPOLOGY` to `uvm_<UVM_TOP>_<UVM_DUT>` and `DUT_ELAB_ARGS` to `<block>_uvm --uvmDut <dut> --uvmTop <top>`. It adds `common/systemVerilog/uvm/a2c_uvm.f`, then `-F` of each builder layer list in `A2C_LAYER_UVM_F_FILES`, and the defines `A2C_UVM_PKG=<variant package>` and, for `rtl`, `A2C_UVM_RTL_DUT` to the HDL arguments. It appends the variant package, the test package and the testbench module to `A2C_SV_FILES`, after `rtl.f`, and makes them, the UVM library files, the agent packages, each layer list and each file a layer list names prerequisites of the snapshot. A layer list holds file paths only, relative to its own directory. It adds `$(A2C_UVM_SRC_DIRS)` to the C++ sources, and on VCS `common/systemc/uvm/uvmVcsElabStub.cpp` too.

| Command | Builds |
| :--- | :--- |
| `make -j8 USE_UVM=1 USE_XCELIUM=1 all` | the snapshot of `UVM_TOP` and `UVM_DUT`: `build_xrun/run_uvm_<top>_<dut>`, a script, over the snapshot directory `xcelium_uvm_<top>_<dut>.d` in the rundir |
| `make -j8 USE_UVM=1 USE_VCS=1 all` | `build/run_uvm_<top>_<dut>`, a run script, beside the simv `build/run_uvm_<top>_<dut>.simv` |
| `make -j8 USE_UVM=1 USE_<VENDOR>=1 uvm_snapshots` | one snapshot per top and DUT that `UVM_TOPOLOGIES` names, built one after another, because they link the same C++ objects and, under VCS, share `AN.DB` |

Vendor recipe items, under `ifdef USE_UVM`:

- Xcelium (`a2c-xrun.mk`): `-uvm -uvmhome CDNS-1.2 -elaborate`. Without `-uvmhome`, xrun picks UVM 1.1d. Without `-elaborate`, the snapshot build would simulate with no `+UVM_TESTNAME` and end in a `UVM_FATAL`. The registrar objects depend on the boundary stamp, because they include every top's shell from `.gen/vl`.
- VCS (`a2c-vcs.mk`): `-ntb_opts uvm-1.2` on `vlogan` and `vcs`. In the `vlogan` flow that option only adds the UVM include directories, so a `vlogan` run with no source files analyses `uvm_pkg` first. Its stamp `AN.DB/uvm_pkg.a2c_stamp` sits in `AN.DB`, which a failed link deletes, and an options file re-analyses it when the `vlogan` options or `VCS_HOME` change.
- VCS: after the wrapper tops' `-sc_model` runs, one `-sc_model` run per UVM top makes every top's shell, because the registrar includes them all. The defines are repeated, because `A2C_UVM_RTL_DUT` changes the testbench module's body. Before the shells, each other top's variant package is analysed, and each other block's test package is analysed once, with `A2C_UVM_PKG` naming one of that block's variant packages. These steps take the RTL analysis's options, defines and library files (`a2c.f` and the HDL arguments, `a2c_uvm.f` among them), minus the selected top's `A2C_UVM_PKG`, so the library units they re-analyse into `AN.DB` match the RTL analysis. They leave out `rtl.f` and the other SV files, which the RTL analysis has already put in `AN.DB`. Other tops are never elaborated.
- VCS: `common/systemc/uvm/uvmVcsElabStub.cpp` gives the `-syscelab` discovery link a weak `m__uvm_report_dpi`. `-ntb_opts uvm-1.2` puts the UVM DPI C code into both links, and only the simv link defines that SV export. The stub aborts if it is ever called.

The run scripts take the test's arguments unchanged, apart from the seed:

- Xcelium: arguments starting with `+` go to the simulator, every other argument goes to `sc_main` as `+systemc_args+<arg>`, and `--seed N` or `--seed=N` also adds `-svseed N`. This applies to every topology, so non-UVM Xcelium runs also get `-svseed`. The script exports the build's `LM_LICENSE_FILE`.
- VCS: simv passes its whole command line to `sc_main`, so the script only converts the seed. Its `dec()` reads `0x` or `0X` as hex, a leading `0` as octal, as `sc_main`'s `std::stoul` does, and anything else as decimal. `random` draws a 32-bit value from `/dev/urandom`. The script then passes one decimal value both as `--seed` and as `+ntb_random_seed`, the only form the SV solver reads, so the `Cmd line:` line of the log records the seed. A seed that is not one of those forms, or that does not fit 32 bits, stops the run with exit status 2 before simv starts. The digit count is checked before the arithmetic, which would wrap past 64 bits.
- Both: with `UVM_TEST` set, a run that names no `+UVM_TESTNAME` gets `+UVM_TESTNAME=$(UVM_TEST)`. The script records `UVM_TEST`, so a change rewrites it.

Xcelium's `-svseed` reads the same three forms as `std::stoul` with base 0, so the Xcelium script passes the value through. A malformed or over-32-bit `-svseed` value only warns there (`SVSEEDW`, seed 1). A probe on Xcelium 26.03 showed `010` giving seed 8, `0x1f` and `0X1F` giving 31, and `08`, `1f` and 4294967296 warning. `sc_main` still parses `--seed` itself, and stops with exit status 2 on a value with no leading digits. `--seed random` draws separately on the two sides under Xcelium and once under VCS. A seed never gives the same stimulus on both vendors.

A run names its testbench, DUT and top the way it does at elaboration. `dutRun.py` maps a test with `--uvmDut <dut> --uvmTop <top>` to `<base>_uvm_<top>_<dut>` and stops with an error when only one of the two is given. The config rejects a `--uvmDut` its block does not have and a `--uvmTop` that is not one of its block's stems, and the wrapper fails a run whose `--uvmDut` does not match the snapshot (section 9.8).

```
../builder/dutRun.py build_xrun/run isp_gain_uvm --seed 7 --verbosity=low \
    --uvmTop isp_gain_default --uvmDut rtl +UVM_TESTNAME=isp_gain_smoke_test
```

A regression file builds with `make -j8 USE_UVM=1 USE_<VENDOR>=1 uvm_snapshots` and runs `../builder/dutRun.py build_xrun/run <block>_uvm` or `build/run <block>_uvm`, with `--uvmTop` in the shared arguments, `--uvmDut` per group and `+UVM_TESTNAME` per test entry. isp_gain's `rundir/regr_gain_uvm_xcelium.json` and `regr_gain_uvm_vcs.json` are the reference, and isp_debayer's `rundir/regr_debayer_uvm_*.json` add a model-against-RTL group through `uvm/xcheck_uvm.sh`. List the rule files in this order: `config/regrRules/uvm.json` by its relative path from the rundir, then any project rule file, then `default.json` and the vendor file. The JUnit report of `regrLauncher.py` keeps only the first failure, so the order decides which failure it shows. `uvm.json` ships in base, and projects reference it in place. It fails a run on a `UVM_ERROR` or `UVM_FATAL` report, a non-zero summary count, or a log with no UVM report summary.

### 9.8 Completion and the verdict

The testbench module clears `uvm_root`'s `finish_on_completion`, so `run_test()` returns after the report phase. It then writes the `UVM_ERROR` plus `UVM_FATAL` count to `uvm_errors` and raises `uvm_done` one clock later. The wrapper's `uvm_watch` thread reads both pins and `rtl_dut`. It fails the run with a reason through `errorCode::fail` when the count is not zero or the snapshot holds the other DUT, marks the run completed and casts the one end-of-test vote. Its `eot_thread` calls `sc_stop()`, because the testbench has no External to do it. The config's `final()` passes a completed run that nothing failed, and fails one where `uvm_done` never rose with `UVM testbench did not finish: uvm_done never rose`.

| Event | Verdict |
| :--- | :--- |
| `UVM_ERROR` | counted on `uvm_errors`; the wrapper fails the run with `UVM reported <n> UVM_ERROR/UVM_FATAL` |
| `UVM_FATAL` | `$finish` inside `run_test()`, so `uvm_done` never rises. Under Xcelium `sc_start` returns and `final()` fails the run. Under VCS the `$finish` exits through `main.cpp`'s `VcsSetExitFunc` handler, which fails the run with `simulation ended by $finish before the end of test` when nothing had set an exit code, and prints the recorded reason when something had. The handler acts from just before the zero-time `sc_start`, because a `UVM_FATAL` such as an unknown test name fires inside it |
| wrong snapshot | `--uvmDut <dut> does not match the snapshot, whose SV testbench holds the <DUT> DUT` |
| X or Z at an RTL port | section 9.4 |
| BFM contract break | the UVM config sets `bfmContractCheck::failOnBreak`, so the first break of each rdy_vld, axi4_stream or memory check, such as `SystemC stalled a backpressure: false producer`, fails the run. raw's missed-edge count is built warn-only and never fails. Other flows keep these checks as warnings |
| `Q_ASSERT` | unchanged; the UVM report summary is missing, and `uvm.json` reports that too |

`try_sc_start` keeps a failure reason set during the run and appends the elapsed time to it. A passing run's summary is unchanged. `errorCode::fail` overwrites, so the summary shows the last failure recorded.

### 9.9 Farm-only tests in base

Two tests need a four-state simulator with UVM and run only on the farm. Source the simulator setup, then run from any scratch directory:

| Command | Builds | Passes when |
| :--- | :--- | :--- |
| `common/systemVerilog/xcheck_test/run_xcheck_test.sh xcelium\|vcs [<tb.sv> <source>...]` | `xcheck_tb.sv` with the checker of each type in the script's `TYPES` into `./xcheck_<sim>`. `xz_count.c` stands in for `a2c_xz_fail` and counts each checker's reports. Given a testbench, the script builds it instead, after the sources that follow it, with the testbench file's stem as the top. A builder layer runs its own checker cases this way, for example Pro's `pro/common/systemVerilog/xcheck_test/lmmi_xcheck_tb.sv` | every case logs `XC_PASS`, and the number that pass equals `CASES` in `xcheck_tb.sv`. The cases cover qualified and unqualified X per type, every control signal, X before arming and during a later reset, a power-on X reset, one report per instance, the apb completion qualifiers, `rdata` only while `ack` for req_ack and pop_ack, memory `read_data` X after a read followed by a write of that address, a write elsewhere, a read, no access, or a reset, external_reg `wdata` only while `write` is non-zero, bound and unbound `tuser`, bound and unbound AXI ID and USER signals, and a reset released in delta cycles before the first edge |
| `common/systemVerilog/uvm/loopback/run_loopback.sh xcelium\|vcs [seed [<layer.f>...]]` | `a2c_uvm_loopback_tb.sv` with every agent package `a2c_uvm.f` lists and the `<type>_if.sv` beside each, into `./loopback_<sim>`. Each `<layer.f>` adds a builder layer's agent packages after `a2c_uvm.f`, the `<type>_if.sv` beside each, and the `*.sv` files in the `loopback/` directory beside the list, compiled after the testbench | every test logs `LB_PASS` with zero `UVM_ERROR` and `UVM_FATAL`. The tests are the classes each `*_lb_tests.svh` file registers with `` `uvm_component_utils `` under a name ending in `_test`. The script fails when a file registers none |

Run both from a scratch directory with the simulator setup sourced. `$A2C_ROOT/common` resolves in a builder checkout and in a base-only checkout; Pro's files sit under `$A2C_ROOT/pro`. Replace `xcelium` with `vcs` for VCS. The seed defaults to 1:

```
$A2C_ROOT/common/systemVerilog/xcheck_test/run_xcheck_test.sh xcelium
$A2C_ROOT/common/systemVerilog/uvm/loopback/run_loopback.sh xcelium 7

# with Pro: lmmi's checker cases, then the loopback with Pro's agents and tests
$A2C_ROOT/common/systemVerilog/xcheck_test/run_xcheck_test.sh xcelium \
    $A2C_ROOT/pro/common/systemVerilog/xcheck_test/lmmi_xcheck_tb.sv \
    $A2C_ROOT/pro/interfaces/lmmi/lmmi_if.sv $A2C_ROOT/pro/interfaces/lmmi/lmmi_xcheck.sv
$A2C_ROOT/common/systemVerilog/uvm/loopback/run_loopback.sh xcelium 7 \
    $A2C_ROOT/pro/common/systemVerilog/uvm/a2cPro_uvm.f
```

Base's checker test holds 154 cases over the 13 base types, and Pro's `lmmi_xcheck_tb.sv` 15.

- `run_xcheck_test.sh` takes a testbench and the sources it needs. It builds the sources first and the testbench last, with the testbench file's stem as the top.
- `run_loopback.sh` takes the seed second and layer lists after it. The seed must come first: a list path in its place is read as the seed. The script never reads `A2C_LAYER_UVM_F_FILES`, because exporting that variable for it would make every later `make` in the same shell add Pro's list a second time. Pro's `a2cPro_uvm_loopback.sv` binds its interfaces into the testbench and runs the tests of `lmmi_lb_tests.svh`.

The loopback testbench includes one `<type>_lb_tests.svh` per agent type, plus `no_backpressure_lb_tests.svh`, `a2c_txn_counter_lb_tests.svh` and `a2c_mem_model_lb_tests.svh`:

| Tests | What they check |
| :--- | :--- |
| `rdy_vld_random_test`, `rdy_vld_burst_test`, `axi4_stream_test`, `raw_test`, `status_test`, `no_backpressure_test` | a src agent against a dst agent; what arrives is checked, in order, against what the src sent |
| `monitor_checks_test` | pins driven by hand under passive monitors: exactly six `A2C_STALL` and four `A2C_HOLD` reports |
| `apb_random_test`, `apb_wait_error_test`, `apb_monitor_checks_test` | master against slave, each transfer against the slave's memory and the monitor; up to three wait clocks and an error range; one `A2C_PROTO` and five `A2C_HOLD` from hand-driven pins |
| `<type>_random_test`, `<type>_monitor_checks_test`, `<type>_counter_test` for push_ack, notify_ack, req_ack and pop_ack | src against dst with ack delays of 0 to 3 clocks, in order; exact `A2C_HOLD` and `A2C_PROTO` counts; the transaction counter on that type |
| `req_ack_config_db_responder_test`, `req_ack_factory_responder_test`, and the same two for pop_ack | the default responder replaced through `uvm_config_db` and through a factory override, and the rdata the responder sent coming back to the src sequence |
| `memory_random_test`, `memory_write_read_test`, `memory_shared_model_test` | back-to-back random accesses against a copy the test keeps; a read on the clock after each write, every access through one reused item; two ports on one `a2c_mem_model` |
| `external_reg_strobe_test`, `external_reg_level_test` | write strobes back to back and with gaps, and the `rdata` level after each; `rdata` following `cfg.value` with `update_on_write` off |
| `axi_read_random_test`, `axi_read_reorder_test`, `axi_read_reuse_test`, `axi_read_max_transfer_test`, `axi_read_monitor_checks_test` | FIXED, INCR, WRAP and narrow bursts with up to four outstanding against the slave's memory; `reorder` with response delays; one item object reused for every burst; an over-limit item refused; exact `A2C_HOLD` and `A2C_PROTO` counts |
| the same five for axi_write, plus `axi_write_w_before_aw_test` | as axi_read, with strobes; W beats sent before their AW |
| `txn_count_*_test` (seven) | the counter's clean, missing, extra, unwaited, repeated, dropped and late cases |
| `a2c_mem_model_test` | reads, writes and the three fill policies, unwritten words reading the same in any order, one `A2C_MEM` line per model |
| `lmmi_random_test`, `lmmi_reuse_test`, `lmmi_counter_test`, `lmmi_monitor_checks_test` (Pro) | as the other types |

The loopback does not run on Verilator, because 5.052 and master stop with an internal error on `typedef <agent>::item_t`.

These unit tests cover the generator and make side without a simulator:

- `test_error_uvm_blocks.py`, the validation;
- `test_uvm_register_view.py` and `test_uvm_pkg_regmodel.py`, the register view and the generated register model and env;
- `test_uvm_test_pkg.py`, the test package;
- `test_uvm_boundary_pins.py`, the pins, port maps, shells and generated files, on two variants and a block without a model, and in `check_vcs_shells` the order, count and defines of the VCS analysis steps;
- `test_build_manifest.py`, the manifest records;
- `test_dut_run.py`, the snapshot `dutRun.py` picks, including `--uvmDut` and `--uvmTop`;
- `test_uvm_agent_companions.py`, the agent and checker files;
- `test_hdl_wrapper_xcheck.py`, the checker instances;
- `test_regr_rules_uvm.py`, the `uvm.json` filters;
- `test_raw_src_bfm_missed_edges.py`, the raw BFM's missed-edge warning;
- `test_memory_bfms.py`, the memory BFMs' read timing and the src BFM's skipped-access count;
- `test_axi_write_src_bfm_w_first.py`, `axi_write_src_bfm` holding `wready` low for a W beat that comes before its AW.

### 9.10 Agents

Every interface type with `uvmAgent: true` ships one agent package, `interfaces/<type>/<type>_uvm_pkg.sv`, or `builder/pro/interfaces/<type>/<type>_uvm_pkg.sv` for a Pro type. The 13 base types and Pro's `lmmi` carry the flag. A package holds `<type>_item`, `<type>_config`, the drivers, `<type>_monitor` with the analysis port `ap`, a sequencer, except for `status` and the `A2C_DST` drivers that choose nothing per transfer, and `<type>_agent`, which exports `item_t` and `config_t`. Every config has `vif`, `clk_vif`, `port_name`, `is_active` (default `UVM_ACTIVE`) and `role` (default `A2C_SRC`). The role is the side of the interface the agent plays, so an `A2C_SRC` agent drives a DUT `dst` port and an `A2C_DST` agent serves a DUT `src` port. A `UVM_PASSIVE` agent builds only its monitor.

Handshake and memory types have one `<type>_driver` that switches on the role. The AMBA types have `<type>_master_driver` for `A2C_SRC` and `<type>_slave_driver` for `A2C_DST`. Their package headers give the AMBA 5 names: Requester and Completer for APB, Manager and Subordinate for AXI.

The pin-timing rule: drivers change pins 100 ps after a rising edge through `a2c_clk_if.drive_edge()`, and monitors sample at the falling edge through `sample_edge()`. Every other source of boundary pins, the RTL and the SystemC BFMs, changes them only between a rising edge and the next falling edge, so a monitor sees the value the next rising edge transfers.

| Type | `A2C_SRC` driver, with its knobs and defaults | `A2C_DST` driver | `A2C_DST` knobs and defaults |
| :--- | :--- | :--- | :--- |
| `rdy_vld` | items from `sqr`, back to back | drives `rdy` | `ready_pct` 100, `burst` 0, `burst_max` 8, `no_backpressure` 0 |
| `axi4_stream` | items from `sqr`, back to back | drives `tready` | `ready_pct` 100, `no_backpressure` 0 |
| `raw` | one item from `sqr` per clock | nothing | |
| `status` | holds `data` at `cfg.value`, default 0; no sequencer | nothing | |
| `apb` | `apb_master_driver`, one transfer per item | `apb_slave_driver`, memory-backed, no sequencer | `max_wait` 0, `error_ranges` empty |
| `push_ack`, `notify_ack` | items from `sqr`, back to back | ack-only, no sequencer | `ack_delay_min` 0, `ack_delay_max` 0 |
| `req_ack`, `pop_ack` | items from `sqr`, one in flight | data responder running `<type>_responder_seq`, one item from `sqr` per request | none; the item's `delay` sets the wait |
| `memory` | one access per clock from `sqr` | memory-backed, no sequencer | `mem`, created when null |
| `external_reg` | one write strobe per item; `write` defaults to `2'b01` | holds `rdata` at a value, no sequencer | `value` 0, `update_on_write` 1 |
| `axi_read` | `axi_read_master_driver`; `max_outstanding` 1, `rready_pct` 100 | `axi_read_slave_driver`, memory-backed, no sequencer | `arready_pct` 100, `resp_delay_min` and `resp_delay_max` 0, `reorder` 0, `error_ranges` empty |
| `axi_write` | `axi_write_master_driver`; `max_outstanding` 1, `bready_pct` 100 | `axi_write_slave_driver`, memory-backed, no sequencer | `awready_pct` and `wready_pct` 100, `resp_delay_min` and `resp_delay_max` 0, `reorder` 0, `error_ranges` empty |
| `lmmi` (Pro) | one transfer per item, one in flight | memory-backed, no sequencer | `ready_delay_min` and `ready_delay_max` 0, `rdata_latency` 1 |

Every item except `apb`, `raw` and `status` has a `gap` field, the idle clocks the src driver inserts first. A `req_ack` or `pop_ack` item also has `delay`, the extra clocks the dst driver waits before `ack`. Neither takes part in `do_compare`. An agent stops at build with `A2C_CFG` when a delay minimum is above its maximum, when an AXI `_pct` knob, `max_outstanding`, `rdata_latency` or, with `burst` set, `burst_max` is 0, or when a width rule fails: the apb slave needs a `data_t` of whole bytes, and `axi_write` the strobe rule of the burst-limit section below.

#### The kinds of `A2C_DST` driver

- **Ack-only**, `push_ack` and `notify_ack`. The driver raises `ack` for one clock, `ack_delay_min` to `ack_delay_max` extra clocks after it samples the request, drawn per transfer. With the defaults a transfer takes two clocks.
- **Data responder**, `req_ack` and `pop_ack`. For each request it samples, the driver takes one item from `sqr` and drives `ack` and the item's `rdata` for one clock after the item's `delay`. The agent sets `<type>_responder_seq` as the `default_sequence` of `sqr.run_phase` through `uvm_config_db`. The default answers with random `rdata` and no delay, and a failed `randomize()` is `A2C_RAND`. A test replaces it with its own `default_sequence` set on `<agent>.sqr.run_phase` in `build_phase`, which wins because the test is higher in the hierarchy; the precedence holds only for sets made during `build_phase`. The other way is a factory override, which must name the port's specialization, `req_ack_responder_seq #(<data_t>, <rdata_t>)::type_id::set_type_override(...)` or `pop_ack_responder_seq #(<rdata_t>)`. The variant package declares no typedef for the responder, so the test spells the parameters itself. A replacement extends the same specialization and overrides `respond()`. `common/systemVerilog/uvm/loopback/req_ack_lb_tests.svh` shows both. `req_ack`'s sequencer is `req_ack_sequencer`. Its `uvm_tlm_analysis_fifo` `request_fifo` receives each request, data only, from the monitor's `req_ap`, and the default `body()` hands it to `respond()`, so a responder can compute `rdata` from the request. A replacement `body()` must take one request per response. The sequencer reports `A2C_RESPONDER` at `check_phase` when more than one is left.
- **Memory-backed**, `memory`, `lmmi` and the apb and AXI slaves. The driver serves each access from `cfg.mem`, an `a2c_mem_model`, which the agent creates when the test leaves it null. A `memory` read takes its word at the sample edge, before the rising edge applies a write, so a same-clock read and write of one address through two agents sharing a model return the old word, as `memory_dp` does. The apb slave maps bus byte k to `paddr + k`, with no alignment, and writes every byte, because `apb_if` has no `pstrb`. An address in `error_ranges` gets `pslverr` or `SLVERR`, leaves the memory untouched and reads 0. An AXI write burst with any beat in a range writes nothing.
- **Level**, `external_reg`. The driver holds `rdata` at `cfg.value`. With `update_on_write` set it loads each write's `wdata` into `value`, so `rdata` changes one clock after the write, as a register flop does.

#### Read data back to the sequence

| Return | Types | How |
| :--- | :--- | :--- |
| in the request | `req_ack`, `pop_ack`, `lmmi`, the apb master | one transfer in flight. The driver writes the read data, and on apb `slverr`, into `req` before `item_done()` |
| pipelined response | `memory`, `axi_read`, `axi_write` | `item_done()` when the access, AR or AW is accepted, and `put_response()` with `set_id_info()` when the read data or B arrives. A sequence extends `memory_base_seq`, `axi_read_base_seq` or `axi_write_base_seq`. Each turns on `use_response_handler`, counts in `send()`, passes each response to `read_done()` or `write_done()`, and waits in `wait_for_reads()` or `wait_for_writes()`, because a response to a sequence that has ended is dropped |

A pipelined driver builds the response when it accepts the request: a new object with the request's fields and `set_id_info()`. A sequence may reuse the request object for its next item, so a response built later would carry the next item's fields. The `memory` driver takes a read's word at the sample edge after the access, so at most one read response is pending. An AXI master refuses an item it cannot drive, as the burst-limit section below describes, and completes it at once with a response that has no beats.

#### Monitor checks

Every monitor writes one `ap` item per transaction and logs it as `A2C_TXN` at `UVM_MEDIUM`, except `raw`, which logs each word at `UVM_HIGH`. The AXI monitors also log each beat at `UVM_HIGH`, and write their item at a read burst's last beat or a write burst's B. The `external_reg` monitor writes writes to `ap` and `rdata` levels to a second port, `rdata_ap`: one item at reset release, then one per change of `rdata`. `A2C_HOLD` and `A2C_PROTO` are `UVM_ERROR` reports:

| Type | `A2C_HOLD` | `A2C_PROTO` | At the end of the run |
| :--- | :--- | :--- | :--- |
| `rdy_vld`, `axi4_stream` | a stalled source drops valid or changes its payload; `A2C_STALL` on a stalled `backpressure: false` port | | |
| `apb` | `paddr`, `pwrite` or a write's `pwdata` changes, or `psel` drops, before `pready` | `psel` and `penable` high with no setup phase on the clock before | |
| `push_ack`, `req_ack` | the request drops or its data changes before `ack` | `ack` with no request | |
| `notify_ack`, `pop_ack` | the request drops before `ack` | `ack` with no request | |
| `axi_read` | AR or R valid drops, or its payload changes, while stalled | reserved `arburst`; `arsize` wider than the bus; FIXED over 16 beats; WRAP not 2, 4, 8 or 16 beats, or not aligned; INCR across 4 KB; `rlast` on the wrong beat; `rid` matching no open burst | bursts still waiting for their last beat |
| `axi_write` | as `axi_read`, on AW, W and B | as `axi_read` on AW; `wid` not its burst's `awid`, unless `id_unbound`; `wstrb` setting a lane the beat does not carry; `wlast` on the wrong beat; B before the burst's last W; `bid` matching no burst | W beats no AW claimed, bursts whose W has not ended, bursts waiting for B |
| `lmmi` | the request drops, or `lmmi_wr_rdn`, `lmmi_offset` or a write's `lmmi_wdata` changes, before `lmmi_ready` | `lmmi_rdata_valid` with no read outstanding; a request taken while a read is outstanding | a read waiting for `lmmi_rdata_valid` |
| `memory`, `external_reg`, `raw`, `status` | | | |

The AXI slaves also report `A2C_PROTO` for a narrow transfer on a bus that is not a power-of-two number of whole bytes. The `rdy_vld`, `push_ack`, `notify_ack`, `req_ack` and `pop_ack` monitors report `A2C_XZ` too, but only on a four-state boundary such as the loopback. The generated testbench's pins are two-state, so the checkers of the next table cover X and Z. Other end-of-run reports are `a2c_txn_counter`'s `A2C_TXN_COUNT` and `req_ack_sequencer`'s `A2C_RESPONDER`.

#### X/Z checker rules

Each `<type>_xcheck` checks its control signals on every clock and its payload only while the protocol qualifies it:

| Type | Every clock | When qualified |
| :--- | :--- | :--- |
| `rdy_vld` | `vld`, `rdy` | `data` while `vld` |
| `axi4_stream` | `tvalid`, `tready` | every other signal while `tvalid`; `tuser` only under `CHECK_TUSER` |
| `apb` | `psel`, `penable`, `pready` | `paddr`, `pwrite` while `psel`; `pwdata` while `psel && pwrite`; `pslverr`, and `prdata` on a read, on `psel && penable && pready` |
| `raw`, `status` | `data` | |
| `push_ack` | `push`, `ack` | `data` while `push` |
| `notify_ack` | `notify`, `ack` | |
| `req_ack` | `req`, `ack` | `data` while `req`; `rdata` while `ack` |
| `pop_ack` | `pop`, `ack` | `rdata` while `ack` |
| `memory` | `enable` | `addr`, `wr_en` while `enable`; `write_data` on a write; `read_data` on the clock after a read, under the next-access rule |
| `external_reg` | `write`, `rdata` | `wdata` while `write` is non-zero |
| `axi_read` | `arvalid`, `arready`, `rvalid`, `rready` | `araddr`, `arlen`, `arsize`, `arburst` while `arvalid`; `rdata`, `rresp`, `rlast` while `rvalid`; `arid`, `aruser`, `rid`, `ruser` only under `CHECK_ARID`, `CHECK_ARUSER`, `CHECK_RID`, `CHECK_RUSER` |
| `axi_write` | `awvalid`, `awready`, `wvalid`, `wready`, `bvalid`, `bready` | AW fields while `awvalid`; `wdata`, `wstrb`, `wlast` while `wvalid`; `bresp` while `bvalid`; `awid`, `awuser`, `wid`, `wuser`, `bid`, `buser` only under their `CHECK_` parameters |
| `lmmi` (Pro) | `lmmi_request`, `lmmi_ready`, `lmmi_rdata_valid` | `lmmi_wr_rdn`, `lmmi_offset` while `lmmi_request`; `lmmi_wdata` on a write request; `lmmi_rdata` while `lmmi_rdata_valid` |

The memory next-access rule: an X or Z `read_data` word fails unless the port's next access writes the same address. A read-modify-write of a word never written, such as a firmware register update's pre-read of the memory's power-on X, then passes, because the write replaces the word. An X word that no access follows fails at the end of the run, and a reset drops it. The rule needs no per-address storage.

The wrapper sets each `CHECK_<SIGNAL>` to `1'b1` when the port binds the optional parameter that types the signal and `1'b0` when it does not. A src block leaves an unbound optional payload undriven, so no checker checks it, and an AXI port that binds no `id_t` gets no ID check.

#### `a2c_mem_model`

`a2c_mem_model #(type word_t)`, in `common/systemVerilog/uvm/a2c_uvm_pkg.sv`, is the storage of every memory-backed driver. It is a sparse store keyed by a 64-bit index, with `read()`, `write()` and `exists()`. A test preloads it with `write()` and inspects it with `read()` and `exists()`. It is not a `uvm_mem`, which needs a register model and a map.

- **Fill.** A read of an unwritten word returns the fill without storing it, so `exists()` reports only written words. `fill` is `A2C_MEM_FILL_ZERO` by default, `A2C_MEM_FILL_RANDOM`, or `A2C_MEM_FILL_FIXED` with `fill_value`. The random fill is a splitmix64 hash of `seed` and the index, so a word reads the same in any order of reads. `seed` comes from `$urandom()` when the model is created, so it follows the simulation seed.
- **Log.** The first read of an unwritten word logs one `A2C_MEM` line at `UVM_LOW`, with the index and the fill policy. Later ones are not logged.
- **Words.** The apb, `axi_read` and `axi_write` slaves use byte words, `bit [7:0]`, at byte addresses. `memory` and `lmmi` use their `data_t` word, indexed by `addr` or `lmmi_offset`.
- **Sharing.** The env creates no model, so two ports of one memory keep separate models. To share one, create it in the `<block>_tb_env` subclass's `build_phase` after `super.build_phase(phase)`, fetch each port's config with `uvm_config_db#(<port>_config_t)::get(this, "<port>_agent", "cfg", cfg)`, and set `cfg.mem` on both. The env's `<port>_cfg` handles are locals of its `build_phase`, and the agents read their configs later in the build, so the objects set here are the ones the agents use.

#### The AXI burst limit

One AXI item is one burst. The item's constraints keep AXI4 legality: INCR up to 256 beats, FIXED and WRAP up to 16, WRAP of 2, 4, 8 or 16 beats from an aligned address, `size` within the bus, and no INCR burst across a 4 KB page, or across the address space when that is smaller. `axi_write` needs `$bits(data_t) == 8 * $bits(strb_t)`, one strobe bit per byte, or the agent stops at build with `A2C_CFG`. A bus that is not a power-of-two number of whole bytes carries only full-width transfers.

- The env sets `max_transfer_bytes` to the interface's `maxTransferSize`, per variant (`pysrc/processYaml.py`, `getBDUvm`). A `maxTransferSize` constant that is a param of the block takes each variant's binding.
- A connection's `maxTransferSize` override is ignored. The UVM run's `<block>Channels` (`templates/systemc/baseClassDecl.py`, `channelConstructor`) sizes the model's AXI channel from the interface value, and an agent limit above it would overrun the model's burst buffer.
- The limit counts bytes, `(len + 1) << size`. The SystemC channel counts the same value in beats, and a beat carries at least one byte, so the byte reading is safe on every bus width.
- `<type>_base_seq::new_item()` returns an item whose constraint holds it within the port's limit. The master refuses any item above the limit with an `A2C_CFG` `UVM_ERROR`, because an item made without `new_item()` carries no limit. `axi_write_master_driver` also refuses an item without one data, strobe and `wuser` entry per beat.
- `id_unbound` is set on a port that binds no `id_t`. The design behind it carries no ID and may answer every burst with ID 0, so the master sends every burst with ID 0, and the `axi_write` monitor does not compare `wid` with `awid`. `axi_write` drives the AXI3-style `wid` equal to `awid`.
- `reorder` lets a slave answer any burst whose delay has passed, as long as each ID's bursts keep their AR or AW order. With `reorder` at 0 it answers in AR or AW order. The slaves accept W beats before their AW and hold them until the AW arrives.

#### Names that depart from common UVM practice

The agents use IEEE 1800.2 class roles and names: item, config, driver, monitor with `ap`, sequencer `sqr`, agent, `default_sequence`, `put_response()` with `set_id_info()`. The names below depart from common practice, each with its reason:

| Name | Reason |
| :--- | :--- |
| roles `A2C_SRC` and `A2C_DST` | they match the interface modports and the SystemC BFM names |
| one role-switched `<type>_driver` for handshake and memory types | each role's code is short, as in `rdy_vld` |
| master and slave for the AMBA driver classes | they match `apb_master_driver` and UVM 1.2-era VIPs; each package header gives the AMBA 5 terms |
| ack-only, memory-backed and level `A2C_DST` drivers with no sequencer | nothing is chosen per transaction |
| `a2c_mem_model`, not `uvm_mem` | `uvm_mem` needs a register model and a map |
| item fields `gap` and `delay` | stimulus timing, left out of `do_compare` |
| `a2c_clk_if` edge tasks, not clocking blocks: drive at the rising edge plus 100 ps, sample at the falling edge | a clocking block in a shared clock interface cannot drive the signals of other interface instances, and a `#1` output skew is a whole period of a 1 ns clock |
| `status_driver` extends `uvm_component`, not `uvm_driver` | it holds a level from its config and takes no items |

### 9.11 The SystemC side under UVM

With the model DUT, the generated wrapper drives the pins through the SystemC BFMs in the DUT's swapped roles. Every BFM follows the pin-timing rule of 9.10.

- `memory_dst_bfm` drives an access after a rising edge, samples `read_data` at the falling edge, and resumes the model at the next rising edge. A model read therefore takes two edges, and a model's back-to-back reads run at one per two clocks. A Verilated memory returns the same word as a UVM agent.
- `memory_src_bfm`'s `request()` must not consume simulated time. An enabled edge that passes while it waits is never served. The BFM counts each one as a `bfmContractCheck` break, which fails a UVM run.
- `axi_write_src_bfm` holds `wready` low while its channel would wait for an address: a transactional receiver, a new burst and no address queued. A master that sends W before AW then holds the beat instead of losing it.
- `lmmi_dst_bfm` drops `lmmi_request` before `complete()`, which waits out the channel's timed delay, so a slave does not see a second read.
- `req_ack_dst_bfm` and `pop_ack_dst_bfm` drop the request for a clock between requests. The UVM src drivers may send requests back to back, and the src BFMs accept that.

Tests and end-of-test voters live outside the DUT. The UVM testbench config never calls `set_test_names`, so a model that calls `register_test_name` or `ADD_TEST` exits with `the test list is empty`.

#### Builder layers

A builder layer ships its agents through `A2C_LAYER_UVM_F_FILES`, a list of `-F` files of agent packages, each path relative to its list. Under `USE_UVM` the flow compiles them after `a2c_uvm.f`, which lists `a2c_clk_if.sv` and `a2c_uvm_pkg.sv` first, so a layer package can import `a2c_uvm_pkg`. Make reads each list with `$(file <)`, which needs GNU Make 4.2, and makes the lists and every file they name prerequisites of the snapshot. Pro adds `pro/common/systemVerilog/uvm/a2cPro_uvm.f` in `a2cPro.mk`, and its checkers through the `-y` line of `a2cPro.f` and `A2C_LAYER_VCS_LIB_SV_FILES`.

## 10. Open items

- Under Xcelium every uninstantiated HDL wrapper top is elaborated as an idle top-level. That is harmless at the tested size, but its memory cost on a large SoC is unmeasured.
- SystemC 3.0.1 is untested in both flows (VCS `-sysc=301` with a GCC 13 build, Xcelium `-sc_301`). The default `VCS_ELAB_OPTS` selects 2.3.4.
- The comment and `$(error)` text at `a2c-xrun.mk:8-13` say `XRUN_GCC_VERS` must match the compiler's libstdc++. For 26.03 that is inaccurate (section 2.2).
- Whether a later Xcelium bundling GCC 13 should be linked with it is untested.
- The Xcelium documentation reviewed during testing states that a snapshot records `LD_LIBRARY_PATH` and rejects a different value at simulation time. The builder does not record it. Keep `LD_LIBRARY_PATH` the same for the build and every run.
- An exported `XRUN_OPTS` or `VCS_LIB_SV_FILES`, or under `VCS_DEBUG` an exported `VLOGAN_OPTS` or `VCS_ELAB_OPTS`, is appended to again in each sub-make, so the builder's additions appear twice (section 3).
- The builder default `DUT_TOPOLOGIES` includes `verif:tandem`, which needs a builder layer that registers tandem blocks (section 1.3).
- Tandem: Pro's 1-in-2-out external_reg tee (`builder/pro/common/systemc/external_reg_port_tee.h`, `port_tee`) forwards a CPU write with `write()`, not `reg_write_cmd()`. A tandem dst model that waits in `read()` for CPU writes never sees one.
- UVM: a second `make USE_UVM=1 USE_VCS=1 uvm_snapshots` is not a no-op. The model and rtl snapshots share one `AN.DB` and one analysis-options stamp, and only the rtl build adds `+define+A2C_UVM_RTL_DUT`, so each build re-analyses after the other. A no-op needs a per-DUT analysis library or a DUT selection without a define. Xcelium is not affected.
- UVM: the VCS steps for a second `hasUvm` block are checked by unit tests only. The two IPs on UVM have one top each.
- UVM: a clock that slows by more than `clock_stop_cycles` periods in one step reads as stopped once, to a waiting counter and to the Mode B drain. Nothing tells a stop from a large step in frequency until the next edge. A counter reports its shortfall then. In the drain, a log idle at that point settles and is watched again from the next edge, but a log that is not idle is given up and never watched again. The run can then end with an `A2C_DRAIN` warning and an `A2C_REPLAY` error for what the model lane still owes, even if it would have caught up on the slower clock.
- UVM: the random-ready form of back-pressure is untested in a block bench. Both blocks on UVM have `backpressure: false` streams, so their sinks hold ready high.
- UVM: no simulation has exercised the register model's memory, ext or multi-word paths, or a non-default variant. Unit tests generate them.
- UVM: an rtl-only (`hasMdl: false`) `hasVl` block's `<block>_hdl_sc_wrapper.h` imports `<ctx>_<block>.base`, which such a block never gets, so its C++ fails to compile in a `VL_DUT`, VCS or Xcelium build. The unit tests generate the files but never compile them.
- UVM: the flow compiles UVM 1.2 on both vendors. The IEEE 1800.2 libraries both installs ship have never been compiled against. A move needs `set_finish_on_completion()` in the testbench module and a different memory stride rule (section 9.5).
- UVM: the JUnit report of `regrLauncher.py` records only the first failure (`regrLauncher/report.py`), so the order of the rule files decides which failure it shows.
- UVM: no base example or ISP block has real RTL behind a `req_ack` or `pop_ack` port, or behind an AXI port. mixed declares req_ack ports only, pySocket's `dut.sv` drives nothing, and axiDemo's producer and consumer RTL are stubs. Only the loopback and scratch model-DUT benches have exercised these agents.
- UVM: the `notify_ack` `A2C_DST` driver has not run against RTL. The mixed example, whose blockA has a notify_ack `src` port, does not build on Xcelium (`URRNG` in blockB's `memory_dp.sv`), and its blockA RTL fails VCS elaboration (`ICPD`).
- UVM: an `axi4_stream` src agent can send a packet longer than the buffer of a multi-cycle model channel. Its items carry no `maxTransferSize` limit.
- UVM: the memory next-access rule passes an X `read_data` word whose next access writes the same address, even when the design used the X word.
- UVM: the AXI burst limit counts bytes, so on a bus wider than a byte it is below the channel's beat capacity. On a 32-bit bus with `maxTransferSize` 256, INCR bursts stop at 64 beats.
- UVM: the AXI slaves do not interleave R beats of different bursts. `reorder` reorders whole bursts.
- UVM: with `id_unbound` set, an AXI master's response carries ID 0, not the ID of the item it answers.
- UVM: a UVM failure that leaves a model's end-of-test voter waiting hangs the run, because the run ends only when every voter has voted. Pass `--scTimeLimit <us>` on model-DUT benches.
- UVM: a model that calls `register_test_name` or `ADD_TEST` exits under UVM, because the UVM testbench config lists no tests (section 9.11). Some base example models do, such as simple's producer and mixed's blockD, so those blocks cannot run as a model DUT under UVM.
- UVM: Pro's lmmiDemo RTL does not elaborate on Xcelium, which rejects `$bits` of a hierarchical name in a typedef.
- UVM: the view chooses the AXI ports that get `max_transfer_bytes` by the type names `axi_read` and `axi_write` (`pysrc/processYaml.py`, `getBDUvm`). `sc_channel.multicycle_types` is also declared by `rdy_vld` and `axi4_stream`, so it cannot make the choice. A per-type flag in the interface definition would need a schema change.
- UVM: the UVM run's `<block>Channels` sizes an AXI channel from the interface's `maxTransferSize` and ignores a connection override, as the agents do. Channels built from a connection row in other flows honour the override (`pysrc/intf_gen_utils.py`, `sc_multicycle_ctor_args`).
