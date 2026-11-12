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
| `A2C_UVM_BOTH_DUT` (SystemVerilog) | `USE_UVM` with `UVM_DUT=both` (section 9.7) | the generated UVM testbench module holds the RTL wrapper on the port interfaces and a second interface per port, `<port>_model`, on the pins toward the SystemC model (Mode B, section 9.12) |
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
- Xcelium reads `LM_LICENSE_FILE`. The snapshot build stops at elaboration, so it never simulates and checks out no simulation licence. Each test's `xrun -R` run takes the licence. The build writes the value set at build time into each run script, so a run started outside the build environment finds the same servers. The script captures no other licence variable.
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
| `XRUN_OPTS` | optional | `-64bit -sv -sysc -sc_main -timescale 1ns/1ps` | snapshot build options. `-gcc_vers $(XRUN_GCC_VERS)` and `-elaborate` are appended (section 5.3) | |
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
2. One `xrun $(XRUN_OPTS) -gcc_vers $(XRUN_GCC_VERS) -elaborate -clean -xmlibdirname xcelium_<topology>.d $(EXTRA_XRUN_OPTS) -makelib a2c_dut -F a2c.f <HDL hooks> $(EXTRA_XRUN_LIB_OPTS) -F rtl.f <RTL modules> <wrapper tops> -endlib <objects> -Wld,<each link token> +systemc_args+<each DUT_ELAB_ARGS word>` in `XRUN_RUNDIR`, log `xrun_xcelium_<topology>.log`. It compiles the HDL, links the objects into a shared library, and elaborates the snapshot. It stops after elaboration, so the build never simulates and checks out no simulation licence. Each test's `xrun -R` run (step 3) takes the licence.
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
- `--vlTrace` has no effect under VCS or Xcelium. Under VCS, build with `VCS_DEBUG=1` and run with `+fsdbTrace` for FSDB waveforms. This needs Verdi's FSDB support in the VCS install. The Xcelium flow has no built-in waveform switch. Elaboration access options such as `-access` go on `EXTRA_XRUN_OPTS`, and the site's probe commands on `EXTRA_XRUN_R_OPTS`, since the snapshot build simulates nothing.

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

A block with `hasUvm: true` gets a generated SystemVerilog UVM testbench that drives its SystemC model, its RTL, or both at once, under Xcelium or VCS. With both, Mode B, the RTL is the DUT under test and the model runs beside it as its reference (section 9.12). SystemC stays on top, and `sc_main` and `main.cpp` run as they do for every testbench. SystemC instantiates the UVM testbench module the way it instantiates an HDL wrapper top, through the `vlogan -sc_model` shell under VCS and an `xmsc_foreign_module` shell under Xcelium.

Base generates the testbench module, the variant package with its register model and `uvm_env`, the SystemC side, and a test package with a base test, a fail test and, for Mode B, a model mismatch test. `make USE_UVM=1` builds and runs it (section 9.7). The project writes its scoreboards, sequences and tests in the user spans of the test package (section 9.6). Base's `examples/uvmMem`, with rdy_vld and memory ports, and `examples/uvmVideo`, with a raw video input and an axi4_stream video output, are the worked examples.

### 9.1 Opting a block in

`hasUvm: optional(false)` is a block flag beside `hasVl`, independent of `hasTb`. `projectCreate.validateUvmBlocks` stops `make db` when a `hasUvm` block:

- has `hasVl: false`, because the testbench drives the block's HDL wrapper;
- has params but no standalone variant, so it would get no testbench top;
- declares no `ports:`;
- has an output clock or reset, because the testbench drives every clock and reset and samples none;
- has a boundary port whose interface type lacks `uvmAgent: true`. A boundary port comes from `ports:`, a `connectionMaps` boundary row, `registerPorts:`, or a `memoryConnections` or `registerConnections` row naming an instance of the block. A `memoryConnections` port has type `memory`, and a `registerConnections` port the type its register's `regType` maps to: `status` for `rw` and `ro`, `external_reg` for `ext`, `memory` for `memory`. The error names the port and the type, and the interface or the row it comes from. A type carries the flag in its definition, `interfaces/<type>/<type>_if.yaml`;
- has a port, clock or reset whose name the testbench module already uses: `dut`, `uvm_done`, `uvm_errors`, `rtl_dut`, `model_dut`, `srv`, `<clock>_if` for any of its clocks, `<port>_<signal>` for any of its pins, or, on a block with a model, `<port>_model` for any of its ports and, for a port of a type that sets `uvmModelCredit`, `<port>_model_credit`, `<port>_model_held` and `<port>_credit`;
- has a register named `block`, whose class `<block>_reg_block` would be the register block class;
- has a register field named like a `uvm_reg` member, or a register or memory named like a `uvm_reg_block` member or `a2c_map`, the generated `build()`'s map variable;
- has a register or memory row wider than 64 bits (`UVM_REG_DATA_WIDTH`) at any standalone variant. The decoder's row stride does not count, because the register model gives a memory its row width (section 9.5).

The same check rejects an interface definition, used or not, that sets `uvmMaxTransferBytes`, `uvmIdParam` or `uvmModelCredit` without `uvmAgent: true`, or whose `uvmIdParam` is not one of its `parameters`.

`raw` has limited support. It is complete against the RTL DUT and best effort against the model DUT, because the SystemC raw BFM is not transactional and can lose a word. `rules/dev-skills/authoring-interface-definitions.md` has the details.

### 9.2 Generated files

The files go in the `uvm` segment, `$root/uvm` in the functional layout and `<node>/uvm` in the hierarchical one. Its buildGroup is also `uvm`, which only the `USE_UVM` flow builds, so no UVM file reaches the model, Verilator or plain RTL compile lists. `<stem>` is `<block>_<variant>` for each standalone variant of a block with params, and `<block>` for a block without params, which has one top.

| fileMap entry | File | Per | Content | Template |
| :--- | :--- | :--- | :--- | :--- |
| `uvmPkg` | `<stem>_uvm_pkg.sv` | standalone variant | package `<stem>_uvm_pkg`. The `items` section holds the variant's parameter values as localparams, the block's parameterized types, per port the typedefs `<port>_agent_t`, `<port>_item_t`, `<port>_config_t` and `<port>_vif_t`, then the register model and `<block>_env` (section 9.5). A user region follows the items | `templates/systemVerilog/uvmPkg.py` |
| `uvmTest` | `<block>_uvm_test_pkg.sv` | block, shared by its variants | package `<block>_uvm_test_pkg`, which imports the variant package that `` `A2C_UVM_PKG `` names. Generated sections hold `<block>_base_test`, `<block>_fail_test` and `<block>_model_mismatch_test`; two user spans hold the project's env subclass, scoreboards, sequences and tests (section 9.6) | `templates/systemVerilog/uvmTest.py` |
| `uvmTb` | `<stem>_uvm_tb.sv` | standalone variant | module `<stem>_uvm_tb`, which imports the test package so the factory registers its tests. Its ports are the HDL top's pins with port directions inverted, then the clocks and resets as inputs, then, on a block with a model, for each DUT `src` port of a type whose definition sets `uvmModelCredit: true` (`memory`), the 32-bit output `<port>_model_credit` and the input `<port>_model_held`, then the completion outputs `uvm_done`, the 32-bit `uvm_errors`, `rtl_dut` and `model_dut`. A one-bit pin is a scalar `bit`, matching the `bool` the simulator shell binds, and a vector payload width is `$bits` of the package-qualified type. It holds one `<type>_if` per port, one `a2c_clk_if` per clock, three DUT branches, the `uvm_config_db` keys and `run_test()`. Under `` `ifdef A2C_UVM_BOTH_DUT `` it holds the RTL wrapper as instance `dut` on the port interfaces and one more interface per port, `<port>_model`, assigned to the pins toward SystemC. Under `` `elsif A2C_UVM_RTL_DUT `` it holds `dut` with the pins toward SystemC tied off. Under `` `else `` the port interfaces are assigned to the pins. `rtl_dut` and `model_dut` say which DUTs the branch holds. Every branch sets the `bit` key `a2c_dual_dut`, 1 only in the both branch, which also publishes each `<port>_model` interface under that name, and, per credited port, an `a2c_credit_if` `<port>_credit` on its two credit pins, published as `<port>_credit`. The other branches tie each `<port>_model_credit` to 0. User regions take imports and module body | `templates/systemVerilog/uvmTb.py` |
| `uvmScWrap` | `<block>_uvm_sc_wrapper.h` | block | class template `<block>_uvm_sc_wrapper<TB_T, Config>` over the simulator shell `TB_T`, or `<TB_T>` alone for a block without params. It drives the clocks and resets into the shell, with resets born low. With the model DUT or both DUTs it also holds the model, its channels and the BFMs in the DUT's swapped roles. The BFMs change the pins only between a rising edge and the next falling edge, where the agents' monitors sample, so a model read through `memory_dst_bfm` takes two edges and the model's back-to-back reads run at one per two clocks. A block with params creates its model with `createInstance<<block><Config>>`, as a container creates a child typed by its Config, which has no factory registration; a registration under the variant still wins. When the run holds the RTL and the model, it hands each credited port's `memory_dst_bfm` its credit and held pins through `setModelCredit()`, and when the run holds the model alone it gives the BFMs of two or more ports of a `bfmWriteOrder` type one `memory_write_order` through `setWriteOrder()` (section 9.12). It waits for `uvm_done` and ends the run | `templates/systemc/module_uvm_sc_wrapper.py` |
| `uvmTbConfig` | `<block>UvmConfig.cpp` | block | testbench config `uvmTbConfig`, registered under the testbench name `<block>_uvm`, with options `--uvmDut` and `--uvmTop`. `--uvmTop <stem>` selects the variant through a generated map, so the config serves every top of the block | `templates/systemc/uvmTbConfig.py` |
| `uvmRegistrar` | `<block>UvmRegistrar.cpp` | block | registers the wrapper as `<block>_uvm` once per standalone variant, over that variant's shell and Config | `templates/systemc/uvmRegistrar.py` |

`make newmodule` scaffolds the test package once, with a working `<block>_tb_env` and an empty `<block>_smoke_test` in its user spans, so the generated tests compile and pass before any user code exists. `make gen` rewrites only the generated sections of every file.

The templates guard two of these files with `#if defined(XCELIUM) || defined(VCS)`, each for its own reason:

- `<block>UvmRegistrar.cpp` includes the simulator shells, `<tbModule>_xcelium.h` under `XCELIUM` and the `vlogan` shell `<tbModule>.h` otherwise, and only those two builds write them.
- `<block>UvmConfig.cpp` includes no shell. It creates the wrapper through the factory key `<block>_uvm`, and only the guarded registrar registers that key. Unguarded, it would offer a `<block>_uvm` testbench in a build that cannot create its wrapper.

A block with `hasMdl: false` gets the RTL DUT only. Its testbench module holds the RTL with no DUT branches, its wrapper has no model, channels or BFMs, and its config accepts only `--uvmDut rtl`, the default. It has no Mode B.

`make gen` under `USE_VCS` or `USE_XCELIUM` also writes two boundary files per testbench top, in the same `--vlBoundary` run as the HDL tops' (section 1.5):

| File | Content |
| :--- | :--- |
| `.gen/vl/<tbModule>.portmap` | the VCS port map for `vlogan -sc_model <tbModule>` |
| `.gen/vl/<tbModule>_xcelium.h` | `class <tbModule> : public xmsc_foreign_module`, which the registrar includes under Xcelium |

Both come from `projectOpen.getUvmTopBoundaryPins`. It takes the HDL top's pins from `getVlTopBoundaryPins`, inverts the port directions, leaves clocks and resets as inputs, and adds the four completion pins.

### 9.3 Names and manifest records

`projectCreate.deriveUvmNames` persists every name as the `UVMNAMES` config, keyed by block. Templates and the manifest read it and never derive a name from a file name.

| Field | Value |
| :--- | :--- |
| `scWrapperClass`, `scWrapperHeader` | `<block>_uvm_sc_wrapper`, `<block>_uvm_sc_wrapper.h` |
| `runClass` | `<block>_uvm_run`, the static run state the config and the wrapper share |
| `testbenchName` | `<block>_uvm` |
| `duts` | `['model', 'rtl', 'both']`, or `['rtl']` for a block with `hasMdl: false`. The first is the default |
| `envClass`, `regBlockClass` | `<block>_env`, `<block>_reg_block` |
| `testPkgName`, `tbEnvClass` | `<block>_uvm_test_pkg`, `<block>_tb_env` |
| `baseTestClass`, `smokeTestClass`, `failTestClass`, `modelMismatchTestClass` | `<block>_base_test`, `<block>_smoke_test`, `<block>_fail_test`, `<block>_model_mismatch_test` |
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
- Under Xcelium the snapshot build stops at elaboration and simulates no time, so an X or Z fails a test run, never the build.
- The run's summary line shows the `A2C_XZ` reason unless a later `errorCode::fail` replaced it, because `errorCode::fail` keeps only the last reason. The `A2C_XZ` `$display` in the log always names the port and signal.

The per-type rules are in section 9.10, and what a new type's checker must ship is in `rules/dev-skills/authoring-interface-definitions.md`.

Tested with: the SystemC regressions of a ten-block image pipeline, run with the checkers elaborated under Xcelium and VCS.

### 9.5 The environment and the register model

The `items` section of the variant package holds both, generated whole. A project extends the env in its test package and never edits this file's generated sections.

`<block>_env extends uvm_env` holds:

- one `<port>_agent` per boundary port, in port order, configured in `build_phase` from a `<port>_config_t` object. The config takes the `virtual <type>_if` from `uvm_config_db` under the port name and `clk_vif` from the port's own clock domain, so a multi-clock block needs no hand wiring. Every agent gets a role, the opposite of the DUT port's direction, `A2C_SRC` on a DUT `dst` port. `no_backpressure` follows the port's effective backpressure on a type whose backpressure is overridable. On a port of a type whose definition sets `uvmMaxTransferBytes: true`, `axi_read` and `axi_write`, the env sets `max_transfer_bytes`. On a port that leaves unbound the parameter its type names in `uvmIdParam`, `id_t` on both AXI types, it sets `id_unbound` (section 9.10). The env sets no agent passive and no `cfg.mem`, so each memory-backed agent creates its own model. A DUT `src` port gets an `A2C_DST` agent that serves it: on a DUT apb `src` port that is `apb_slave_driver`, with no sequencer. The register model stays on the register-bus port, so a block that is a bus target and a bus master gets one `A2C_SRC` agent with the register model and one serving `A2C_DST` agent per downstream apb port;
- one `<port>_counter`, an `a2c_uvm_pkg::a2c_txn_counter`, per DUT output with a handshake: a `src` port of an elastic type that is not an address-bus type. Those types are `rdy_vld`, `axi4_stream`, `push_ack`, `notify_ack`, `req_ack`, `pop_ack`, `axi_read`, `axi_write` and Pro's `lmmi`. The counter counts the monitor's `ap` items, so on `pop_ack` it counts the DUT's pops, on `axi_read` its read bursts and on `axi_write` its write bursts. `connect_phase` connects the output monitor's `mon.ap` to its `analysis_export`;
- one `<port>_digest`, an `a2c_uvm_pkg::a2c_txn_digest`, per port, inputs and register bus included. `connect_phase` calls its `watch()` on the port's `mon`;
- one `virtual a2c_clk_if` per clock, as `<clock>_vif`;
- with a register model, `regmodel`, the bus's `<type>_reg_adapter` as `adapter`, and a `uvm_reg_predictor` as `predictor`. `build_phase` builds the model and calls `regmodel.reset()`. `connect_phase` sets the bus agent's sequencer and the adapter on `default_map`, turns auto-prediction off, and feeds the predictor from the bus monitor, so the mirror follows bus traffic from any sequence;
- `dual_dut`, read from the `bit` key `a2c_dual_dut` that the testbench module sets, and the Mode B wiring it turns on: each agent's `cfg.model_vif` from `<port>_model`, each credited port's `cfg.credit_vif` from `<port>_credit`, an `A2C_CFG` fatal when it is missing, each counter's and each digest's `dual` with the agent's `model_mon.ap` connected to the counter's `model_export` and the digest's `watch()` called on `model_mon`, the list `comparators` of every agent's `model_cmp`, each digest's `cmp` set to that `model_cmp`, `model_stable_point()`, and, with a register model, `guard`, an `a2c_midstream_guard`, fed through `reg_writes`, an `a2c_reg_write_subscriber` on the bus monitor. The env also gives the guard `regmodel.default_map` and gives the bus agent's `model_cmp` the guard, so the comparator can ask it about each read. Section 9.12 describes them. The predictor stays on the DUT lane's bus monitor, so register reads and the mirror test the RTL.

`a2c_txn_counter #(T)` (`common/systemVerilog/uvm/a2c_uvm_pkg.sv`) is a `uvm_subscriber`. It counts transactions and checks nothing about their content. `expect_count(n)` adds n to the expected count. `wait_for_count(clk_vif, deadline_cycles, quiet_cycles)` waits for the expected count, reports a shortfall as `UVM_ERROR` id `A2C_TXN_COUNT` when the deadline passes, then waits the quiet window and reports any excess the same way. A clock with no edge for the counter's `clock_stop_cycles` periods (default 1000) has stopped, which reports the shortfall or ends the quiet window at once. `check_phase` reports what no wait covered. A transaction that arrives after its shortfall was reported is logged as late, not counted again, until the next `expect_count()`.

`a2c_txn_digest #(T)` keeps a 64-bit FNV-1a hash per lane of every item its exports receive, over the item's fields and `$realtime` at the `write()`, in arrival order. `watch(mon, lane)` connects the monitor's `ap` to the lane's counted export, `analysis_export` or `model_export`, and every other analysis port of the monitor that carries the item type to the lane's `side_export` or `model_side_export`, which hash the item, tagged as a side item, without counting it. So the `external_reg` monitor's `rdata_ap` levels and the `req_ack` monitor's request-time `req_ap` items enter the digest. A monitor with no `ap` of the item type is an `A2C_CFG` error. The fields come from `digest_parts()` on an item that implements the interface class `a2c_digest_fields`, which appends them as a list of strings that the digest hashes one by one, so a long burst costs time in proportion to its length, and from `convert2string()` on any other. `axi_read_item` and `axi_write_item` implement it, adding every beat's data, response or strobe and user signal to the burst fields their `convert2string()` prints, so their `A2C_TXN` lines stay one line per burst. The other base and Pro items print their whole payload in `convert2string()`. A project item whose `convert2string()` leaves payload out implements `a2c_digest_fields` too. `report_phase` prints one `UVM_LOW` line per lane, the model lane only with `dual` set:

```
A2C_DIGEST <port> <DUT|model> paired=<0|1> items=<n> digest=<16 hex digits>
```

`items` counts the `ap` items only, the stream the Mode B comparator sees. `paired` is the digest's `cmp.pairs_every_item()` at `report_phase`, and 0 with no `cmp`; the env sets `cmp` in Mode B to the port's `model_cmp`. `a2c_in_order_comparator` and its subclasses, the keyed AXI, register and memory comparators included, return 1, since they pair every item of one lane with one of the other, unless an end-of-test drain left a cut in force (section 9.6, "The Mode B end-of-test drain"): the cut holds the items either lane delivers after it unpaired, so a DUT still flowing at the end can count more items than the model lane in a passing run, and the port prints `paired=0`. `a2c_status_comparator` and its subclasses, which compare the latest value at stable points, return 0: a status port under the `stable` policy can see more value changes on one lane than the other in a correct run.

The digest is the run's stimulus and response on that port, as its monitor reports them, in one value, so two runs can be compared without diffing their `A2C_TXN` lines. Items that move in time with unchanged content change it. It checks nothing itself; `seedRepro.py` compares two runs' lines (section 9.7).

The register model is generated from the block's address rows, so it cannot disagree with `fw/<block>RegAddresses.h` on an offset:

- one `<block>_reg_<register>` (`uvm_reg`) per `registers:` row, with one `uvm_reg_field` per structure member at its packed position, the first member most significant. Padding members are fields too, because the decoder flops them. Each field's reset is its share of `defaultValue`. `rw` registers are `RW` and their fields `rand`; `ro` and `ext` registers are volatile, and `ro` is `RO`;
- one `uvm_mem` per `memories:` row with `regAccess`, and one `RW` memory per `regType: memory` register. A `wo` memory is `RW` with `WO` map rights and gets `NO_MEM_TESTS`, because UVM reports WO rights as RW in a one-map model. A memory's `n_bits` is its row width at the variant. The decoder sizes its row stride for the widest variant's row, so a row can be narrower than its stride, and UVM 1.2 would step the memory by `ceil(n_bits / 32)` bus words. `default_map` is therefore an `a2c_reg_map` in every block with a memory, and `set_mem_stride()` gives each memory the decoder's stride, which for a row as wide as its stride is the stride UVM would use. An access moves only the row's own bus words, which is what the RTL decoder commits on, and `get_mem_by_offset()` counts the unused words of a row as the memory's. `get_size()` and a parent map's lookup still use UVM's stride, so an `a2c_reg_map` must be a root map, and `add_submap()` of one is an `A2C_CFG` fatal. `a2c_reg_map` reads UVM 1.2's map info, so a move to IEEE 1800.2 must check it;
- `<block>_reg_block`, with `default_map` at base 0, a 4-byte bus and little-endian order, each register and memory at its row's offset. Widths and depths are resolved per variant at `make db`. A register wider than the bus becomes consecutive 4-byte accesses.

Only text unit tests cover the memory, ext and multi-word paths. Neither base UVM example has registers.

### 9.6 The test package

`uvm/<block>_uvm_test_pkg.sv` holds the project's tests. Its layout, top to bottom:

| Span | Owner | Content |
| :--- | :--- | :--- |
| `header` | generated | package `<block>_uvm_test_pkg`; imports of `uvm_pkg`, `a2c_uvm_pkg`, the agent packages, the block's type packages and `` `A2C_UVM_PKG ``. An undefined `A2C_UVM_PKG` expands to a package name that says to define it |
| user span 1 | project | `<block>_tb_env extends <block>_env`, with the scoreboards and any helpers; also sequences and other classes the tests use |
| `tests` | generated | `<block>_base_test` |
| user span 2 | project | `<block>_smoke_test` and the project's other tests |
| `footer` | generated | `<block>_fail_test`, `<block>_model_mismatch_test`, then `endpackage` |

`<block>_base_test extends uvm_test` creates the env as `<block>_tb_env::type_id::create("env", this)`, so the project's subclass needs no factory override. Its `run_phase` raises one objection, waits for each clock's reset release, calls `run_body()`, calls `wait_for_outputs()` and drops the objection. A test puts its stimulus in `run_body()` and never handles objections. `wait_for_outputs()` waits on every output counter at once, each on its own port's clock, and a test may call it between frames. In Mode B each return also calls the env's `model_stable_point()`, the stable point of the status policy (section 9.12). The deadline and quiet window are the members `output_deadline_cycles` (default 200000) and `quiet_cycles` (default 1000). A test sets its own defaults in its constructor, and `+a2c_output_deadline_cycles=<n>` and `+a2c_quiet_cycles=<n>` override them, because `build_phase` reads the plusargs afterwards. `clock_stop_cycles` (default 1000, `+a2c_clock_stop_cycles=<n>`) is the counters' stopped-clock threshold, and the Mode B drain's. Mode B is `UVM_DUT=both` (section 9.7): one snapshot holds the RTL, the DUT under test, and the model, its reference, and each agent drives and monitors both pin sets, its DUT lane and its model lane. The Mode B drain at the end of the run phase has its own knobs, described below. `build_phase` hands the clock stop and the drain's knobs to the env through the `uvm_config_db`.

#### The run timeout

The run timeout is a backstop. The progress rules detect a stop: the output deadline, the drain's deadline and catch-up, the joint stall rule, and in Mode B the lane skew and lone lane rules. The run timeout makes sure that a run none of them ends still gives a report, instead of a farm kill with none. It does not check a real-time requirement such as a frame finishing within its frame time; `a2c_rt_checker` does that ("Real-time checks" below).

`<block>_base_test` creates an `a2c_run_timeout` component, `run_timeout`, and gives it the block's first clock, the one `run_phase` waits on first. From that clock's reset release it counts rising edges. When the count reaches the budget and the run phase is still running, it raises one `A2C_RUN_TIMEOUT` `UVM_ERROR` and ends the run phase prematurely, together with every other task phase that is running, such as `main_phase`. From then on it ends each task phase other than the run phase as it begins, whether a runtime phase such as `shutdown_phase` or a user-defined one, in UVM's schedule or in the common one. UVM's own timeout, `+UVM_TIMEOUT`, is watched only while the run phase runs, so without this a later phase that waits for ever would hang the run. The phases end with their objections still raised, and `extract_phase` and `check_phase` run once each: the output counters report the transactions still missing, and the replay logs report what each lane owes. This behaviour is verified on UVM 1.2 with Xcelium and VCS.

The budget has three modes, set by `run_timeout_cycles`:

| `run_timeout_cycles` | Budget |
| :--- | :--- |
| -1, the default | derived: `run_timeout_floor_cycles + run_timeout_factor * W` |
| above 0 | fixed at that many clocks |
| 0 | off: the run timeout sets no time limit and only counts clocks for its info line. It still ends the run at a Mode A joint stall (section 9.10); `joint_stall_cycles` 0 turns that rule off |

A progress rule reports a stop in its own words, and a derived budget lets one that is counting have its say first. The derived budget holds three promises:

1. A progress rule that is counting toward its bound when the budget is reached may fire first, whatever its bound, with two exceptions that the clock-stop allowance below describes: a lane rule whose clock has stopped is left out, and a clock that pauses more than once can push any rule past the deferral. The rules are the output deadline of a `wait_for_count()`, a master's joint stall rule in either mode, a Mode B master's lane skew and lone lane rules, the drain's deadline and catch-up, and an `a2c_rt_checker`'s gap, deadline and refusal rules. A checker whose output clock has stopped is left out as a lane rule is.
2. Changing a bound during the run never makes a run time out before its budget: no bound enters the budget, so changing one never moves it. A bound counting when the budget is reached only lengthens the one deferral.
3. Every run still ends: the count defers once at most. A Mode A joint stall that fires during the deferral, or before the budget, ends the run itself (section 9.10), and the count then stops without an `A2C_RUN_TIMEOUT`.

When the count reaches a derived budget, it defers once to the rules counting at that clock:

- **What it collects.** Each rule counting at that clock, with the most clocks it may still take to report:
  - an output deadline's remaining clocks. When several `wait_for_count()` calls on one counter overlap, each counts, and the counter gives the one that ends last. A wait that ends, or that a `kill()`, `disable` or phase end stops, no longer counts;
  - the lone lane or joint stall rule's remaining clocks;
  - the lane skew rule's remaining clocks while one lane trails, or the whole bound on a master that counts the skew itself;
  - a draining replay log's remaining deadline plus its catch-up;
  - an `a2c_rt_checker` rule's clocks left to its bound: the nearest unreported deadline, the gap bound less the open unit's gap, or the refusal bound less the input unit's refusals.
- **The clock-stop allowance.** An output deadline or a drain whose clock stops reports `clock_stop_cycles` and a half of its periods after the clock's last edge instead of at its bound. A lane rule never reports a stop: its count holds still while its port clock is stopped, so it cannot report before the clock returns. The count therefore leaves out a lane rule whose clock has gone `clock_stop_cycles` and a half of its periods without a rising edge, the same test `next_rise()` applies with that limit. Every rule counts clock edges, so a clock that pauses for less than a stop delays any rule's report by the pause, and every rule takes `clock_stop_cycles` + 1 clocks more. That covers one pause. A clock that pauses again and again, each pause short of a stop, can delay any rule's report past the deferral, an output deadline's and a drain's as well as a lane rule's, and the timeout then reports instead. For example, with the default of 1000, a clock that is off for 900 periods and on for 10 never reads as stopped. A rule with 100 clocks left on it needs about ten such rounds, some 9100 periods, against the 1111 the deferral gives when the rule's clock is the run timeout's own clock. A lane rule reads `clock_stop_cycles` as `a2c_clock_stop_cycles` on its master's path, where the base test sets it.
- **The clock conversion.** Each rule counts clocks of its own port or log. The count converts them into clocks of the first clock by the periods that the two clocks' `a2c_clk_if`s measure, rounding up. A master's port clock is the `cfg.clk_vif` it hands its watchdog, and a clock with no period measured yet counts as the first clock.
- **The info.** If any rule is counting, the count logs one `A2C_RUN_TIMEOUT` `UVM_INFO` at `UVM_NONE` that names each rule and its clocks left. It defers to the last of them plus `A2C_RUN_TIMEOUT_DEFER_MARGIN`, 10 clocks: `the run phase has not ended after <n> clocks of <clock>, its run timeout, while progress rules count toward their own reports: <rules>. The run timeout defers to them, once, for <d> clocks, and then ends the run phase if it is still running<left out>`. `<left out>` is empty unless a lane rule was left out because its clock had stopped, and then reads `. Left out, clock stopped: the <rule> of <port> (<master>)`, with several separated by `; `. The `A2C_RUN_TIMEOUT` error carries the same text after `<how>`, so a timeout with no deferral still names the rules it left out. At the deferred clock the count expires unless W has grown the budget meanwhile, and it never defers again.
- **The trade-offs.**
  - Changing a bound never makes a run time out before its budget. But the deferral covers only the rules counting when the budget is reached, not the rest of the run. A rule that starts counting after that, or starts again with a new bound, gets no extra time, and a test of long waits, such as frames, sizes its budget with `fix()`.
  - A deferral always runs `clock_stop_cycles` + 1 clocks of the rule's clock longer than the rule's own clocks left, 1001 at the default, whether or not the clock ever stops. These clocks cannot be avoided: at the budget nothing tells a clock about to stop or pause from one that runs on, and without those clocks a rule whose clock stops or pauses would lose its report to the timeout. The extra clocks move only the timeout: a run that ends inside the deferral takes no longer, and one that hangs reports that much later.
  - A fixed budget is the test's own sizing and does not defer.

W is the work the test has declared: the items its input agents have sent plus the transactions its output counters expect. Work the DUT does through its own masters is not counted: memory or AXI-slave traffic the DUT pulls, and outputs on address buses, which have no output counter. A design whose work is mostly of that kind has a small W, and its test raises `run_timeout_factor` or fixes the budget. `stimulus_sent()` counts the items as `A2C_NO_STIMULUS` does, through `a2c_items_sent`. `outputs_declared()` sums each output counter's `declared()`. W is a sum, not a max, because a test's phases run one after the other: register configuration takes its clocks before the first frame does. Both functions are virtual, so a test whose work goes through other paths can add it. W is read at the reset release and again each time the count reaches the budget, so the budget grows with the stimulus sent meanwhile. Both counts only ever rise, so the budget never shrinks unless a test overrides one of the functions to return less.

A test can also fix the budget with `run_timeout.fix(<n>)`, from any phase once `run_timeout` exists, which is after the base test's `build_phase`. A test that computes its budget from its stimulus calls it in `run_body()`, before it sends. It takes effect from the next clock, so it can lower the budget as well as raise it, and `fix(0)` turns the timeout off. `fix()` overrides every `uvm_config_db` setting of `a2c_run_timeout_cycles`, whether the test made it or `+uvm_set_config_int` did. Only `+a2c_run_timeout_cycles` overrides `fix()`, and with any value, so `+a2c_run_timeout_cycles=-1` brings back the derived budget.

The message reads:

`<test>: the run phase has not ended after <n> clocks of <clock>, its run timeout: <rate>. <how><left out>. Ports waiting now: <ports>. Objections still raised by: <objectors>. <raise>`

- `<rate>` reads `<r> clocks per unit of the work declared, W <W>`, or `no work declared`. A design whose items take many clocks each, such as frames or DMA bursts, shows a large `<r>` here.
- `<how>` gives the budget's source: `The budget is run_timeout_floor_cycles <f> + run_timeout_factor <k> x <W>, the work the test has declared (input items sent <s>, output transactions expected <o>)`, followed after a deferral by `, deferred at <n> clocks by <d> to the progress rules then counting`, or `The budget is fixed by run_timeout_cycles (+a2c_run_timeout_cycles)`, or `... fixed by run_timeout.fix() in the test`.
- `<left out>` names the lane rules the deferral left out because their clocks had stopped, as in the info above, and is otherwise empty.
- `<ports>` lists each master whose port had a live lane waiting for a handshake on the port's last clock, in the words `A2C_JOINT_STALL` uses (section 9.10), such as `in (uvm_test_top.env.in_agent.drv), both lanes waiting for the transfer of 'h5`. With one DUT (`UVM_DUT=rtl` or `model`) a port has one lane and reads `in (uvm_test_top.env.in_agent.drv), waiting for the transfer of 'h5`. A port whose lanes are both dead is left out. With no master waiting the list is `none`, and something else holds the run: a sequence waiting on an event, a test's own wait, or a component's objection. The DUT's outputs are not listed; their counters report at `check_phase`.
- `<objectors>` are the components and sequences that hold a run-phase objection, from `get_objectors()`, in name order. While `run_body()` runs, the base test, `uvm_test_top`, is one of them. Each other running task phase that holds an objection follows, in domain and then phase name order, as `; <phase> phase: <objectors>`, for example `uvm_test_top; main phase: uvm_test_top.env.holder`. A phase of a domain other than UVM's own reads `; <phase> phase of domain <domain>: <objectors>`. A user-defined phase appears by its name.
- `<raise>` names the knobs to raise: the factor or floor for a derived budget, `run_timeout_cycles` or the value passed to `fix()` for a fixed one.

A task phase that the timeout ends as it begins, and in which something raised an objection, gets one `A2C_RUN_TIMEOUT` `UVM_INFO` at `UVM_NONE` when it ends: `the run timeout, which expired at <time>, ended the <phase> phase as it began. Objections raised by: <objectors>`. A phase in which nothing objected would have ended at once anyway, and is not reported. After a Mode A joint stall ends the run, the same info comes under `A2C_JOINT_STALL` and reads `the joint stall rule, which fired at <time>, ended the <phase> phase as it began. ...`.

The end-of-test reports of missing or unpaired items that follow a timeout end with `; the run timeout ended the run phase at <time> (A2C_RUN_TIMEOUT), which may account for this`: `A2C_TXN_COUNT` for transactions outstanding, `A2C_REPLAY`, and the `A2C_MODEL_CMP` reports of unpaired items and of a held read of X or Z. What they find missing is usually the timeout's doing, so read the `A2C_RUN_TIMEOUT` first. After a Mode A joint stall ends the run, the same reports end with `; the joint stall rule ended the run phase at <time> (A2C_JOINT_STALL), which may account for this` instead, and the `A2C_JOINT_STALL` is the one to read first. A report of extra transactions does not carry it, since a timeout adds none, and neither does a report the run phase raises in the timeout's own time step, such as an `A2C_SKEW`.

A run that ends in time logs one `A2C_RUN_TIMEOUT` `UVM_INFO` at `UVM_LOW` from `extract_phase`: `the run phase ended after <n> clocks of <clock>, within its run timeout of <budget>. <how>`, or `..., with no run timeout. <how> at 0` when the timeout is off. `<n>` is the count of rising edges, which keeps running with the timeout off. The count and W are what a project reads to set its own floor and factor.

The count runs until the run phase ends, so it also bounds a component that keeps an objection after the base test drops its own, and the Mode B drain.

| Knob | Plusarg | Default |
| :--- | :--- | :--- |
| `run_timeout_cycles` | `+a2c_run_timeout_cycles=<n>` | -1, derived |
| `run_timeout_floor_cycles` | `+a2c_run_timeout_floor_cycles=<n>` | `A2C_RUN_TIMEOUT_FLOOR_CYCLES`, 2500000 |
| `run_timeout_factor` | `+a2c_run_timeout_factor=<n>` | `A2C_RUN_TIMEOUT_FACTOR`, 20 |

A test sets them in its constructor, and the plusargs override them. Each left at -1 sets nothing. Otherwise `build_phase` sets it on the `run_timeout` child as `a2c_run_timeout_cycles`, `a2c_run_timeout_floor_cycles` or `a2c_run_timeout_factor`, which `run_timeout` reads in its `build_phase` with the same accepted types as the drain knobs. A design that takes many clocks per item, such as one whose items are whole frames or long bursts, sets `run_timeout_factor` once in the constructor of its base-test subclass, and every test inherits it.

The defaults come from measurement. A run takes about `a + b * W` clocks. `a` is fixed overhead, chiefly the output quiet window, `quiet_cycles`, 1000 clocks by default, which every `wait_for_outputs()` waits out once. `b` is the clocks per unit of work. Every test of the Xcelium regressions of base's two UVM examples, uvmMem and uvmVideo, in the `model_dut`, `rtl_dut` and `both_dut` groups, gave its run length and its W:

| Measured | Clocks | W | `b`, with `a` of 1050 |
| :--- | ---: | ---: | ---: |
| longest test: `uvmMem_fail_test`, `both_dut`, ended by the 200000-clock output deadline | 201156 | 65 | not work |
| `uvmVideo_fail_test`, ended the same way | 200839 | 1609 | not work |
| longest test that passes: `uvmMem_random_test`, `both_dut` | 3283 | 512 | 4.4 |
| `uvmMem_random_test` | 1975 to 3283 | 512 | 1.8 to 4.4 |
| `uvmVideo_video_test_random` | 2612 to 3170 | 3069 to 4157 | 0.5 |
| the other uvmVideo tests: smoke, model mismatch and the corners | 1703 to 1911 | 1344 to 1680 | 0.5 |
| `uvmMem_smoke_test` and `uvmMem_model_mismatch_test` | 1113 to 2160 | 64 | 1.0 to 17.3, inside the floor |

uvmVideo's input is a clocked stream, so every clock it sends is an item and W grows with the blanking: `b` is 0.5 in every test. A test that waits out more than one quiet window has a larger `a`, and the table counts the extra windows as work, so its `b` is high. A Mode B run adds the drain's quiet window, so `uvmMem_smoke_test` comes to 1.0 clock per unit of work on the model and to 17.3 in Mode B.

The defaults were first set from two larger streaming blocks, whose steepest slope was 14.8, in a test that waited out five quiet windows, and whose longest passing test took 19211 clocks for a W of 10902.

- The floor, 2500000, covers `a`. It is about 12.4 times the longest test, and it exceeds the default bounds of the progress rules together, 1200000 clocks, 200000 each for the output deadline, drain deadline, drain catch-up, lane skew, lone lane and joint stall, so they report first. The deferral keeps that true for a test that raises a bound.
- The factor, 20, covers `b`. It is above every slope measured, 17.3 at the steepest with a Mode B drain counted as work, and four or more times the slope of the random tests, 0.5 to 4.4. The measurement cannot pin it down further: for any factor up to about 600, the W term of even the largest measured test, W 4157, stays below the floor.
- Every measured test runs within a tenth of its derived budget. The tightest is `uvmMem_fail_test`, at about 1/12.4.
- A hang in a small test reports after 2500000 clocks. uvmVideo's fail test, which waits out the output deadline with the design idle, runs about 250000 clocks per CPU second on Xcelium, so such a hang costs about 10 s of CPU, and more on a bench whose design keeps busy. A hang in the largest measured test reports after 2583140 clocks.

A test whose transactions are pixels gets 20 clocks per pixel from the factor. That is more than a frame needs, so a hang in a long frame test reports late: two 1920x1080 frames at one pixel per clock declare a W of about 8.3 million, a budget of about 168 million clocks. A hang costs the budget divided by the bench's clocks per CPU second: about 11 minutes at uvmVideo's 250000, and longer on a bench whose design keeps busy. Such a test computes its budget from the frame and fixes it. The budget counts clocks of the block's first clock, so a frame timed on another clock, such as a pixel clock, is converted into clocks of the first one. The frame time in clocks is `(H_active + H_blank) * (V_active + V_blank) / pixels_per_clock`, and the budget is `margin * (configuration + N_frames * frame_time + latency + quiet window)`. For two 1920x1080 frames with 280 clocks of horizontal and 45 lines of vertical blanking at one pixel per clock, a frame takes 2200 * 1125 = 2475000 clocks. With 20 register writes of about 10 clocks each, a two-line latency of 4400 clocks and the output quiet window, `quiet_cycles`, of 1000, the sum is 4955600 clocks, and a margin of 2 makes the budget 9911200:

```systemverilog
virtual task run_body();
    int unsigned frame = (1920 + 280) * (1080 + 45) / 1;
    a2c_video_cfg c = new_video_cfg();
    c.width       = 1920;
    c.height      = 1080;
    c.frames      = 2;
    c.h_blank_min = 280;
    c.h_blank_max = 280;
    c.v_blank_min = 45 * (1920 + 280);
    c.v_blank_max = 45 * (1920 + 280);
    run_timeout.fix(2 * (20 * 10 + 2 * frame + 2 * 2200 + quiet_cycles));
    configure_dut(c);
    send_video(c);
endtask
```

The test calls `fix()` before it configures and sends, so the budget covers the configuration too.

The bound is in clocks rather than simulated time because the clock period differs per project and is not known at `build_phase`. A clock that stops stops the count, so if the first clock stops, only `+UVM_TIMEOUT` ends the run.

A test that keeps sending raises a derived budget each time the count reaches it. One that sends `r` items per clock moves the budget by `factor * r` clocks for each clock that passes. With `factor * r` of 1 or more, the count never reaches the budget, and the progress rules or `+UVM_TIMEOUT` bound the run. Below 1, the budget converges, and the run times out after about `floor / (1 - factor * r)` clocks: a test that sends an item every 40 clocks under the defaults times out after about 5000000.

`+UVM_TIMEOUT` and `uvm_top.set_timeout()` keep working as a second limit, in simulated time, and whichever comes first ends the run. UVM's limit raises a `PH_TIMEOUT` `UVM_FATAL`, which skips `check_phase`, so keep it above the run timeout. Its default is 9200 s of simulated time. A slow clock with a large budget reaches it first: at 1 MHz, any budget above 9.2e9 clocks.

The joint stall rule (section 9.10) reports a run in which nothing moves while a master holds an item, after `joint_stall_cycles`, 200000 by default. In Mode B it also ends the run, since every master's lanes die and the sequences complete. In Mode A no lane dies, so the run timeout ends the run at the stall, as it would at its budget, with no `A2C_RUN_TIMEOUT` (section 9.10). The run timeout also covers the hangs the rule cannot see: a port that waits while another keeps moving, a rule turned off, and an objection no port holds. It declares no lane dead. Ending the run phase prematurely skips the Mode B drain, or stops a drain that is running, so each replay log reports the state it was in at the timeout. UVM clears the objections still raised with one `OBJTN_CLEAR` `UVM_WARNING` per phase.

A test that does not extend the generated base test has no run timeout.

#### Real-time checks

The progress rules catch a design that stops. `a2c_rt_checker` catches one that keeps moving but too slowly for its stream, such as a video pipeline that drops behind its source, or a packet engine that stalls inside a packet. It checks one output port of the DUT against one input port with three rules. Each rule is off at 0, and each bound is the first value that fails, as for `lane_skew_cycles`.

| Rule | Knob | Fails when |
| :--- | :--- | :--- |
| gap | `rt_gap_cycles` | an open output unit, from its first transfer to its end, goes this many clocks with no beat while the sink is ready, less the starvation credit below |
| deadline | `rt_lag_cycles` | output unit k has not ended this many clocks after its anchor input unit ended, less the stall credit below |
| refusal | `rt_refusal_cycles` | within one input unit the DUT refuses this many clocks of offered input, leaving out the clocks on which the sink stalled the output |

Together the deadline and refusal rules check throughput. A DUT that takes all its input but falls behind lags more each unit, and one that keeps up only by back-pressuring its source refuses. The deadline is anchored at the end of the input unit, not its start, so the testbench's pacing, blanking and Mode B throttling never cause a failure, and a pipeline's fill counts once, inside the bound. **Stall credit.** The deadline does not count the clocks on which the sink refused a beat the DUT offered, net of the input refusals they caused. A clock with ready low and no beat offered is not a stall and earns no credit. The credit for output unit k is the stall clocks after its anchor input unit ended, up to the output unit's end, plus the stall clocks before that input end, from unit k's first offered beat, less the clocks the DUT refused offered input from the earlier of that input unit's start and unit k's first offered beat up to the input end, never below 0. An output unit can start before its anchor input unit does, as with `in_units_per_out` above 1 or an offset `anchor()`; the refusals then count over the same window as the stalls they net. The refusals are counted raw, including the clocks the refusal rule leaves out because the sink stalled. All three counts restart whenever the output sits idle with its sink ready: the DUT had caught up, so no stall before that clock can have moved the unit's end, and the counts then start from that clock for every outstanding deadline. A stall the DUT absorbs in its buffer, and that it never catches up on, leaves the input end where it was and delays the output, so it is credited in full. A stall the DUT turns into refusals has already moved the input end later by those clocks, and crediting it again would hide that much real lag. A stall the DUT catches up on during an input gap delayed nothing and is not credited. The rule errs one way only: a DUT that refuses input for its own reasons during a stall has those refusals subtracted too, and a DUT that idles while still holding a backlog, as a pipeline bubble does, restarts the counts and loses the credit for earlier stalls. Both read high, never low. `A2C_RT_DEADLINE` and the late-unit info print the credit and the time the counts last restarted.

A unit is a run of beats that a rule marks: a frame, a line or a packet. `a2c_unit_rule #(T)` decides it. A subclass returns the end marker from `is_unit_end(t)`, such as `t.data.last`, and `ends_per_unit` closes the unit at the n-th marker. `a2c_beat_count_rule #(T)` makes every `beats_per_unit` beats a unit, for a stream that marks no end. `axi4_stream_tlast_rule` ends a unit at `tlast`. A per-line contract beside a per-frame one takes a second checker.

The checker pairs units one to one by default. `in_units_per_out` above 1 anchors output unit k at input unit `(k + 1) * in_units_per_out - 1`, for a decimator, and `out_units_per_in` above 1 anchors `out_units_per_in` output units at one input unit, for a splitter. A design with any other pairing overrides `anchor(k)`, which must not decrease and must grow without bound: an input unit end creates a deadline for every output unit whose anchor is at or below it, so a constant anchor never stops creating them. An output unit that ends before its anchor input unit has ended raises `A2C_RT_UNIT`, because the pairing does not match the design.

**Starvation credit.** Pipeline latency moves the output's idle later than the input's, so a gap rule that only looked at the output would fail every time the testbench paused. The gap therefore subtracts the clocks in the window (last output transfer - `rt_latency_cycles`, now] on which the testbench offered no input beat while the open unit's anchor input unit had not ended. A real stall is reported at most one window of testbench idle late. `rt_latency_cycles` 0 takes `rt_lag_cycles`. With no input connected there is no credit, and the gap is the raw output idle.

**Monitors measure, the checker judges.** The rdy_vld, axi4_stream and push_ack monitors implement `a2c_flow_counts`: from the reset release they count the clocks sampled, offered, ready and transferred, in the same step as the item they report. The checker counts the rising edges of the output port's clock and reads both monitors on each. A stopped clock holds every count still. An input on another clock is read on the output clock's edges, which is exact to one clock. On push_ack a clock counts as ready when `ack` is high or `push` is low. Request-response interfaces such as pop_ack, req_ack, AXI and memory have no real-time rule yet.

**The source must not wait for ready.** The gap and refusal rules read a clock with valid high and ready low as a beat offered and refused. A source whose valid waits for ready offers nothing until the DUT is ready, so the refusal rule sees no refusal and the gap credit sees input the testbench withheld. The rdy_vld, axi4_stream and push_ack interface definitions forbid it in the AMBA wording: the source must not wait for ready before asserting valid, and holds valid and its data until the transfer completes. The UVM src drivers and SystemC BFMs keep to it (section 9.10). The checker relies on it for the DUT's output as well.

The project creates the checker in its `<block>_tb_env` and wires it in `connect_phase`. `connect_in()` and `connect_out()` take the agent's `mon`, and `connect_out()` also takes the output's `a2c_txn_counter` and the agent's `model_cmp`, which is null outside Mode B:

```systemverilog
rt = a2c_rt_checker#(in_item_t, out_item_t)::type_id::create("rt", this);
rt.in_rule  = my_eof_rule#(in_item_t)::type_id::create("in_rule");
rt.out_rule = my_eof_rule#(out_item_t)::type_id::create("out_rule");
...
rt.connect_in(in_agent.mon);
rt.connect_out(out_agent.mon, out_counter, out_agent.model_cmp);
```

A checker with no `out_rule` and a counter passed to `connect_out()` runs the gap rule only, treating the time the counter has transactions pending on the DUT lane as one unit.

**Knobs.** The base test's members `rt_gap_cycles`, `rt_latency_cycles`, `rt_lag_cycles`, `rt_refusal_cycles` and `rt_on_model` start at -1, which sets nothing, so every rule is off. A test sets them in its constructor, and `+a2c_rt_gap_cycles=<n>` and the other plusargs in the knob table below override them. `build_phase` sets each one at 0 or more on `env*` as `a2c_rt_<name>`, so one value reaches every checker in the env. A checker outside the env, or one that needs its own bounds, takes them through its own fields after the checker's `build_phase` has read the knobs and before `end_of_elaboration_phase`, such as in the env's `connect_phase`; a field set in the env's `build_phase` is overwritten. `set_limits(gap, lag, refusal)` changes the bounds during the run: a negative argument keeps that bound, a plusarg for a bound still wins, and a new lag bound applies to units whose input ends after the call. `a2c_rt_off` set to 1 turns all three rules off for the run, and wins over the knobs, the plusargs, the fields and `set_limits()`. A rule whose wiring is missing, such as `rt_lag_cycles` with no input or no `in_rule`, is an `A2C_CFG` error at `end_of_elaboration_phase`.

**The model and Mode B.** The model's timing is approximate, so on the model DUT the checker measures and raises nothing, and logs one `A2C_RT` info that says so. The generated tb sets `a2c_model_dut` for it. `rt_on_model` (`+a2c_rt_on_model=1`) judges the model too. In Mode B the checker judges the RTL lane, `agent.mon`, and never compares the two lanes' timing. Once a Mode B master or the comparator declares the DUT lane dead, it stops judging, and its summary says when.

**Reports.** Each failure is a `UVM_ERROR` that does not stop the run. The first `max_reported`, 10 by default, are printed; `check_phase` counts the rest in one more `A2C_RT` error. A deadline raises `A2C_RT_DEADLINE` the clock it is reached, so a hang is reported at once, and the unit's late end adds an `A2C_RT_DEADLINE` info: `output unit <k>, reported late, ended <n> clocks after its deadline`. A slow design and a hung one therefore read differently. A unit whose deadline had not passed when the run ended raises nothing. Each rule reports once per unit. At `check_phase` each checker logs an `A2C_RT` summary at `UVM_LOW`: the units checked, the first, worst and last lag, the worst gap and refusal with their units, the input unit period, the share of input clocks the testbench withheld, and the units that completed late, never completed or were still pending. The worst values are also readable from a test through `worst_lag()`, `worst_gap()`, `worst_refusal()`, `units_checked()` and `failures_seen()`.

**The run timeout.** A checker rule counting toward its bound when a derived budget is reached is a progress rule like the others (property 1): the deferral names it, as in `the real-time deadline rule (rt_lag_cycles) of <port> (<checker>)`, and waits for its clocks left plus `clock_stop_cycles` + 1. A checker whose output clock has stopped is left out, as a lane rule is, because its counts hold still. A summary with units still pending carries the run timeout clause when the timeout ended the run.

**Wiring a checker into a project.** A project adds a checker in the user region of its `<block>_tb_env`, one per output stream whose timing is a contract. The steps:

1. Write a unit rule for the stream's natural unit, such as an end-of-packet flag or an end-of-frame flag, or use `a2c_beat_count_rule` or `axi4_stream_tlast_rule`.
2. Create the checker, set `in_rule` and `out_rule`, and connect it in `connect_phase` as shown above.
3. Run a passing test with the rules off and read the `A2C_RT` summary: the worst lag, gap and refusal. Set the bounds from those measurements with a stated margin, in the test's constructor through the `rt_*` knobs, and say in a comment what each bound guarantees.
4. Add a fire test that sets one bound below the measured value and expects exactly the failures that follow, such as one `A2C_RT_DEADLINE` per unit. Real RTL has no mutant hook, so this is what proves the checker is wired to the right ports and units; the loopback tests in `a2c_rt_checker_lb_tests.svh` cover each rule against a configurable pipeline.

A random test can turn on the gap rule alone as a stall detector.

Not yet built: a generated gap-only checker per output that needs no wiring, unit markers declared in YAML, and a request-to-response latency bound for pop_ack, req_ack, AXI, memory and Pro's `lmmi`.

#### Video framing tests

A block with a video stream port gets framing tests and an output check that does not read the model. Both come from `common/systemVerilog/uvm/a2c_video_pkg.sv`, which `a2c_uvm.f` compiles after `a2c_uvm_pkg.sv`. The bench writes one class and one macro line, and nothing in YAML or the generator changes. The package holds:

| Class | Role |
| :--- | :--- |
| `a2c_video_cfg` | the run: `width`, `height`, `frames`, the blanking ranges `h_blank_min`/`_max` and `v_blank_min`/`_max`, `lead_clocks`, `trail_clocks`, `v_front` and `v_back` (clocked), `beat_gap_max` (handshaked), `pixel_mode` (ramp, random or `pixel_value`), and the corner knobs, which apply to frame `corner_frame` only |
| `a2c_video_adapter #(ITEM)` | maps frame, line and pixel onto the port's item. Extend `a2c_video_handshake_adapter` for a stream with SOF and EOL markers, setting `has_eof` when it carries EOF, or `a2c_video_clocked_adapter` for fv and lv levels. Set `pixels_per_beat` and `pixel_bits`, and write `clear()`, the three setters and the three getters. `axi4_stream_video_adapter` in `axi4_stream_uvm_pkg` is the adapter for any `axi4_stream` port: SOF on `tuser[0]`, EOL on `tlast` |
| `a2c_video_seq #(ITEM)` | sends the planned frames through the adapter |
| `a2c_video_contract` | the frames a correct DUT makes of each frame sent, with their SOF, EOL and EOF. The default is the same frame out, markers re-derived, pixels unchecked. `crop_width` cuts long lines to `width`, `pixel_check = A2C_VIDEO_PIX_EXACT` compares pixels, `markers` selects where the markers come from, and a bench overrides `expected_frame()` or `expected_frames()` for anything else. A contract whose `preserves_frames()` returns 0 turns off the real-time checkers on its output |
| `a2c_video_checker #(ITEM)` | one per output lane; rebuilds the frames through the adapter's getters and compares each with the contract's frames |
| `a2c_video_unit_rule #(ITEM)` | the frame as an `a2c_rt_checker` unit: fv falling, EOF, or the EOL that completes the lines of the planned frame due |
| `a2c_video_flow_counts #(ITEM)` | the flow counts of a clocked stream, whose monitor counts nothing, for `connect_in()` |
| `a2c_video_test #(BASE)` | the base piece: extends `BASE`, the generated `<block>_base_test` |

The bench extends `a2c_video_test` once, with the generated base test as `BASE`, and the macro adds one test per corner:

```systemverilog
import a2c_video_pkg::*;
`include "uvm/a2c_video_macros.svh"

class blk_video_test extends a2c_video_test #(blk_base_test);
    `uvm_component_utils(blk_video_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    virtual function void video_ports();
        vin_adapter_t  ia = vin_adapter_t::type_id::create("vin_adapter");
        vout_adapter_t oa = vout_adapter_t::type_id::create("vout_adapter");
        add_video_input(a2c_video_input#(vin_item_t)::make("vin", ia));
        add_video_output(a2c_video_output#(vout_item_t)::make("vout", oa));
    endfunction

    virtual function void video_connect();
        connect_video_input(env.vin_agent);
        connect_video_output("vout", env.vout_agent, env.vout_counter);
    endfunction

    virtual function void configure_video(a2c_video_cfg cfg);
        cfg.width  = 128;
        cfg.height = 16;
    endfunction

    virtual task configure_dut(a2c_video_cfg cfg);
        uvm_status_e status;
        env.regmodel.width.write(status, cfg.width);
        if (status != UVM_IS_OK) `uvm_error("BLK", $sformatf("width write: %s", status.name()))
    endtask
endclass

`a2c_video_corner_tests(blk_video_test)
```

`a2c_video_test` is a parameterized class that extends its parameter rather than a component the bench adds, because the generated base test owns the run phase, the output wait and the run timeout's work count, and a video test has to change both `run_body()` and `stimulus_sent()`. It builds a child `video`, an `a2c_video_env`, and the bench fills it through two hooks, one per phase, so nothing depends on the order in which the test's children build. `video_ports()` runs in `video`'s `build_phase`: it creates each port's adapter, and a contract where the default does not fit, and adds one input and the checked outputs with `make()`. It reads nothing of the test's env. `video_connect()` runs in `video`'s `connect_phase`: it gives the input its agent with `connect_video_input()`, whose `sqr` takes the frames, and each output its agent and, optionally, its `a2c_txn_counter` with `connect_video_output()`. The checkers read the agent's `mon`, and in Mode B its `model_mon` too. After `video_ports()` the env applies, in order, the input adapter's stream kind and pixel shape, `configure_video()`, the corner and the `+a2c_video_<knob>=<n>` plusargs, and validates at `end_of_elaboration_phase`. The knobs a corner derives from the geometry, `cut_frame`'s and `cut_lv_high`'s cut, `short_line`'s beats and the line `short_line` and `long_line` change, are derived again from the geometry the plusargs leave, so `+a2c_video_height=12` on `cut_frame` keeps 6 lines. A plusarg that sets such a knob, such as `+a2c_video_cut_after_line`, still overrides the corner, and so does a value the test set after the corner. `run_body()` calls `configure_dut()` and `send_video()`, which declares each counted output's beats from the contract and sends. A test that overrides `run_body()` sends several runs, with register writes between them, by passing `send_video()` a cfg from `new_video_cfg()`. The plusargs apply to such a cfg too, when it is sent, with its corner's knobs derived again from the geometry they leave, and it is validated then. A cfg that is never sent is never validated, so a broken rule in it fails nothing at elaboration. `stimulus_sent()` adds the handshaked input's blanking clocks, so a derived run timeout grows with the blanking. Base never reads or writes a register: `configure_dut()` is the bench's.

`` `a2c_video_corner_tests(T) `` defines `T_<corner>` for each corner below; each sets `corner` in its constructor. `a2c_video_corner_test(T, C)` defines one. `a2c_video_cfg::corner_names()` returns the same list.

| Corner | Frame `corner_frame`, or the run |
| :--- | :--- |
| `blanking` | random blanking over the run: 1 to 6 clocks per line, 2 to 24 per frame, random lead and trail |
| `no_blank` | no blanking; handshaked only |
| `back_to_back` | the next frame's first beat on the clock after this one's last |
| `short_line` | line 1 at half its beats |
| `long_line` | line 1 two beats longer |
| `cut_frame` | the frame ends after line `height/2 - 1`, so it keeps `height/2` lines, with no EOF unless `cut_eof` |
| `cut_lv_high` | as `cut_frame`, with fv falling while lv is high; clocked only |
| `fv_rise_line` | the first line starts on the clock fv rises; clocked only |
| `lv_vblank` | lv high with fv low on the 2 clocks before fv rises and the 2 after it falls; clocked only |
| `random` | at least 8 frames, one corner the stream allows drawn for each frame but the first and the last |

`cut_frame` and `cut_lv_high` always cut after line `height/2 - 1` of the final height, so a test of either is repeatable and its cut frame keeps `height/2` lines. `+a2c_video_cut_after_line=<n>` keeps `n + 1` lines instead. A design whose state alternates by line and does not restart at SOF, such as a colour-filter phase, goes wrong only after a cut frame that keeps an odd number of lines. Make sure one `cut_frame` entry of its regression keeps an odd number of lines: where `height/2` is even, add an entry with `+a2c_video_cut_after_line=<n>`, `n` being the lines kept minus 1. At a height of 8 the corner keeps 4 lines, and `n` = 2 keeps 3. The `random` corner draws its cut line per frame and alternates the parity of the lines kept, odd then even or even then odd, where the height allows both.

`validate()` raises one `A2C_CFG` `UVM_FATAL` that names the corner and every broken rule: `geometry`, `blank_range`, `clocked_blank`, `level_corner`, `short_line`, `long_line`, `cut_line`, `line_range`, `corner_clash`, `corner_frame`, `back_to_back` (the last frame has no frame to follow it), `cut_last` (a cut last frame with no EOF on a stream that carries EOF, which nothing would end), `random_frames` (`random_corners` with fewer than 3 frames, so no frame between the plain first and last) and `pixel_value` (`A2C_PIX_CONST` with `pixel_value` unknown in the pixel's bits). So a corner the stream cannot carry fails at elaboration in one line, and a regression lists only the corners that apply.

**The contract.** `a2c_video_test` calls the contract's `expected_frames()` once per planned frame and output. For an output with an `a2c_txn_counter` on a handshaked stream, or with a real-time checker's unit rule, it calls it when `send_video()` plans the run; for any other output, when the output's first checker takes the frame's plan, just before the frame's first beat. Both calls fall inside `send_video()`, so the hook may read the frame, the cfg and whatever the test set before the run, such as the register mirror after `configure_dut()`. It must not read anything that changes while the run is sent: a register written during the run, the DUT's outputs, or the time. Then both call points give the same frames. It may return no frame, for a design that drops one, or several, for one that splits it; the checker then names them `frame <n> part <k>`. Its default returns the one frame `expected_frame()` makes. A frame the contract returns carries its markers: `sof`, `eof` and each line's `eol`, which the checker compares with the beats. `set_markers()` sets them as `markers` selects:

| `markers` | The expected frame's SOF, EOL and EOF | For |
| :--- | :--- | :--- |
| `A2C_VIDEO_MARKERS_DERIVED`, the default | SOF on the first beat, EOL on each line's last, EOF on the frame's last, whatever the input carried | a design that makes its own framing |
| `A2C_VIDEO_MARKERS_AS_RECEIVED` | each as the input frame carried it, so a cut frame sent with no EOF is expected with none | a streaming design that passes framing through |

A frame with no EOF closes on the EOL that completes its expected lines, or at the next SOF. When a line's width is not a multiple of the pixels per beat, the DUT may pad its last beat, as UG934 allows; the checker trims the padding before it compares. The output's checkers share the frames the contract returns, so the contract must not change them afterwards.

Each test logs the corner, the geometry and, once, the contract each output checks, as `A2C_VIDEO` `UVM_INFO` at `UVM_LOW`. A failure is an `A2C_VIDEO` `UVM_ERROR` per broken line or frame, such as `vout: frame 1 line 0: 60 pixels, expected 64` or `vout: frame 1: no EOF on its last beat; the next frame's SOF came first`. A marker the expected frame lacks is reported too, as in `vout: frame 1: EOF on its last beat, where the expected frame has none`. Under `A2C_VIDEO_PIX_EXACT` a line that holds the head of the next one is reported as `frame 1 line 0: no EOL on its last beat, so line 1 ran on into it with 4 of its 64 pixels`, and the lines after it are paired again. Beats outside any frame are reported once per run of them. `check_phase` closes a frame still open and compares it, ending each message with `the run ended before the frame did` and what ended the run, then reports the expected frames that never came out. It summarises each lane: `vout: 3 of 3 expected frames came out, from 3 planned, 24 lines, 384 beats; 0 frames failed, 0 failures`.

**Real-time checks on a video port.** At `start_of_simulation_phase` the env finds each `a2c_rt_checker` whose input or output is connected to a video port's `mon` and gives its `a2c_video_unit_rule` the frames the run plans: the planned frames for an input rule, the contract's frames for an output rule. On a stream with no EOF, or for a frame expected with none, the rule ends a unit on the EOL that completes the frame's lines, so a cut or a short frame stays one unit. A rule on a stream with no EOF that ends a line while no frame is due raises one `A2C_CFG` error, since it is not on a video port the test plans. When an output's contract returns 0 from `preserves_frames()`, the env turns off only the checkers on that output's monitor, with an `A2C_VIDEO` info naming each; the others keep their bounds.

In Mode B, when the testbench sets `a2c_dual_dut`, each output gets a checker on each lane, named `<port>_checker` and `<port>_model_checker`, whose messages say `DUT lane` or `model lane`. The model lane's checker reads the agent's `model_mon`; an agent with none is an `A2C_CFG` error, since the model lane would go unchecked. The `no_blank` and `back_to_back` corners plan beats on consecutive clocks. On a handshaked input the env's `a2c_video_lane_watch` counts, per lane, the planned beats whose valid was high on every clock since the lane's previous transfer, read from the monitor's flow counts. So a sink that refuses a beat does not count against the stimulus, and in Mode A the count equals the plan unless the test itself holds the input's sequencer. The env finds a planned beat by the monitor's own beat count when the sequencer grants it, so items another sequence sends on the same agent, before, between or during the runs, do not move it. This needs the input's driver to ask for the next item only after every live lane transferred the previous one, so the beat the sequencer grants is the next one each lane's monitor reports. Base's handshaked drivers do. Its pipelined drivers, `memory`, `axi_read` and `axi_write`, return a response after `item_done()`, but carry no video input, so the requirement does not reach them. A run's first beat is never planned, since the plan does not time it against what came before. In Mode B the driver holds each beat until both lanes took the one before, so a trailing lane gives the other idle clocks the plan never asked for. `report_phase` logs the counts, and in Mode B a corner test of either corner warns when the DUT lane got fewer than planned.

#### The Mode B end-of-test drain

In Mode B every `A2C_DST` agent that answers the DUT (push_ack, notify_ack, req_ack, pop_ack, memory, external_reg, the apb slave, the AXI slaves and Pro's `lmmi`) serves both lanes from one model. The DUT lane applies each transaction and records its response in the driver's `a2c_replay_log`; the model lane replays the responses in order. An AXI slave that reorders records which burst the DUT lane answered, and the model lane answers the same burst, matched by ID and its arrival index within the ID, so both lanes complete bursts in one order (section 9.10). The model lane often trails the DUT lane, so when the run phase's last objection drops, `a2c_replay_drain` holds the run phase until the model lanes catch up. It watches each log on the log's own clock:

- **Settle.** A log settles once both lanes have been idle for `drain_quiet_cycles` clocks in a row: no lane inside a transaction or starting one, no recorded response waiting for the model lane, and the model lane not waiting for one. The drain ends when every log has settled or been given up.
- **Cut.** A log not settled at `drain_deadline_cycles`, whose DUT lane started a transaction within its last `drain_quiet_cycles` clocks, is traffic that never pauses. The drain cuts it after the transactions the DUT lane has started, and both lanes have `drain_catchup_cycles` clocks to complete them. The transactions after the cut go unchecked on both lanes. `drain_catchup_cycles` defaults to the deadline, so a cut whose lanes never complete it takes up to twice the deadline to report. Lower the catch-up to fail sooner.
  - The comparator keeps the DUT lane's first `cut_at` completions and holds back the rest. Of each key it keeps as many model lane completions as those carry with that key, so the lanes may complete different keys in different orders across a cut. Without a key it keeps the model lane's first `cut_at`, so a responder whose lanes complete in different orders needs a keyed comparator.
  - With `reorder`, the first `cut_at` completions are not the first `cut_at` requests, so the counts `A2C_CUT` gives are approximate.
- **Re-cut.** A test may resume the run phase after a drain, by raising an objection in `phase_ready_to_end()`. The next drain undoes the earlier cuts and starts only if a lane has started a transaction since. A log cut before whose DUT lane has not paused for `drain_quiet_cycles` clocks since is cut again on the first clock.
- **Give-up.** Any other log not settled at its deadline is given up with an `A2C_DRAIN` warning, and its `check_phase` reports what the lanes still owe.
- **Clock stop.** A clock with no rising edge for `clock_stop_cycles` periods and a half has stopped. Its log settles if it is idle and not cut, and is given up otherwise. A settled log is watched again if its clock runs again; a given-up one is not. The steady period changes only when three intervals in a row agree within an eighth. Once a clock has one, neither a gated clock's gap nor a single runt pulse changes it, and a clock that slows by more than the stop limit in one step reads as stopped once. A clock gated in short bursts at uneven gaps may never have three agreeing intervals; until it does, its period is the shortest interval seen, and a runt in that time shortens its stop limit. Four rising edges whose three intervals agree set the period, so a burst of evenly spaced glitches can set a steady period of the glitch spacing. The real clock's next edge then reads as a stop unless `clock_stop_cycles` and a half exceeds the clock period divided by the glitch spacing. 2 or more covers runts near half the period.

A model lane whose master withdraws a request before the DUT lane has recorded the response it waits for, which the lane's monitor reports as `A2C_HOLD`, gets no ack for it. The push_ack, notify_ack, req_ack, pop_ack and Pro `lmmi` responders count no transaction for it and stop waiting for the record, so the drain does not wait on it. An `lmmi` request withdrawn after the model lane raised `lmmi_ready` leaves the response held, which `check_phase` reports as `A2C_REPLAY`.

A hand-written test that raises objections only in `main_phase()` drains too: UVM 1.2 calls the run phase's `phase_ready_to_end()` once the runtime phases have ended, which takes no time when the later ones hold no objection.

A `UVM_PASSIVE` agent can watch a Mode B port beside the agent that drives it, on the same `vif` and `model_vif`, for example the agent of a reused block env inside a top env. It builds its monitors and `model_cmp` and no driver, so it sees neither a lane's death nor the drain's cut by itself. Left alone, its monitors would report the dead lane's open transfers as `A2C_PROTO` errors, and its `model_cmp` would report the pairs past a cut or a death as `A2C_MODEL_CMP` errors. The agents meet in `a2c_pin_registry`, one table per virtual interface type keyed by the virtual interface handle of each pin set, so the link needs no component path. The one condition is that the passive agent's `vif` and `model_vif` are the interface instances the active agent has: a second interface instance on the same nets, such as one a block env `bind`s into the block, is a different handle and does not match. In `connect_phase` a passive agent adds its `model_cmp` under `vif`, and a passive AXI agent also adds its monitor under `vif` and its `model_mon` under `model_vif`. The active agent marks the entry under its `vif` as its own. The active agent's replay log cuts and uncuts every `model_cmp` registered under its `vif`, and a Mode B master that declares a lane dead (section 9.10) tells every monitor registered under that lane's pin set and every `model_cmp` registered under `vif`. In `end_of_elaboration_phase` a passive AXI or `lmmi` monitor takes the replay log of the active responder on its pin set, so it reports transfers left open after a cut as info, as the active agent's monitor does. With no such log the monitor keeps any `replay` a hand-written env gave it.

A passive Mode B agent whose `vif` no active agent has marked reports it in `end_of_elaboration_phase` with one `UVM_LOW` `A2C_PASSIVE` info from the agent that names the port and points at its `cfg.vif`, and then runs as before. That is expected on a port no agent drives, such as an internal port of a top design. Where an active agent does drive the port, the info means the two agents have different interface instances, and the passive agent's `model_cmp` will report the pairs past a cut or a death as `A2C_MODEL_CMP` errors. The passive agents that report it are those that can learn of a cut or a death: the `A2C_DST` agents of the handshake families, memory and external_reg, and the req_ack, pop_ack, apb, Pro's `lmmi` and AXI agents in either role.

The registry is a global pool, the role `uvm_pool` plays in UVM, keyed by pin set. It is not a `uvm_pool`, because an associative array cannot take a virtual interface as its index: a virtual interface has `==` and no ordering. It is not analysis-port wiring either. A death and a cut are control events, not transactions, and a reused block env shares no component path with the top env through which to connect ports.

A hand-written Mode B responder joins the drain by giving its `a2c_replay_log` a `clk_vif` and an `a2c_replay_lanes` implementation, as the built-in drivers do; the log registers itself with the drain at `start_of_simulation_phase`. A responder whose comparator holds pairs back at a cut implements `cut()` and `uncut()` on it. A passive agent's comparator is cut with the active agent's, so a factory override of a passive agent's `model_cmp` must implement them too. The base comparator's `cut()` stops the run with an `A2C_CFG` fatal; `a2c_in_order_comparator` has both, keyed by `key()` or not. Its `lane_starts()` and `lane_busy()` must change away from the rising edge of the log's `clk_vif`, at the falling edge or the drive point, as the built-in drivers do. The drain reads them at the rising edge. A driver that counts in an `@(posedge clk)` process races it, so the drain can end in that time step before the count moves and leave a false `A2C_REPLAY`.

| Member of `<block>_base_test` | Plusarg | Default |
| :--- | :--- | :--- |
| `drain_quiet_cycles` | `+a2c_drain_quiet_cycles=<n>` | `quiet_cycles` (1000) |
| `drain_deadline_cycles` | `+a2c_drain_deadline_cycles=<n>` | `output_deadline_cycles` (200000) |
| `drain_catchup_cycles` | `+a2c_drain_catchup_cycles=<n>` | each log's `drain_deadline_cycles` |
| `clock_stop_cycles` | `+a2c_clock_stop_cycles=<n>` | 1000 |
| `drain_cut_expected` | `+a2c_drain_cut_expected=1` | 0 |
| `lane_skew_cycles` | `+a2c_lane_skew_cycles=<n>` | the Mode B master's own 200000; 0 turns the bound off |
| `lone_lane_cycles` | `+a2c_lone_lane_cycles=<n>` | the Mode B master's own 200000; 0 turns the rule off |
| `joint_stall_cycles` | `+a2c_joint_stall_cycles=<n>` | the master's own 200000, in either mode; 0 turns the rule off |
| `no_stimulus_expected` | `+a2c_no_stimulus_expected=1` | 0 |
| `run_timeout_cycles`, `run_timeout_floor_cycles`, `run_timeout_factor` | `+a2c_run_timeout_cycles=<n>`, `+a2c_run_timeout_floor_cycles=<n>`, `+a2c_run_timeout_factor=<n>` | a budget derived from the test's work; see "The run timeout" above |
| `rt_gap_cycles`, `rt_lag_cycles`, `rt_refusal_cycles` | `+a2c_rt_gap_cycles=<n>`, `+a2c_rt_lag_cycles=<n>`, `+a2c_rt_refusal_cycles=<n>` | -1, which sets nothing: every checker's rule stays off; see "Real-time checks" above |
| `rt_latency_cycles` | `+a2c_rt_latency_cycles=<n>` | -1; a checker left at 0 takes its lag bound as the starvation credit window |
| `rt_on_model` | `+a2c_rt_on_model=1` | -1; the checkers only measure on the model DUT |

A test sets its own values in its constructor and the plusargs override them. The three drain cycle counts, `lane_skew_cycles`, `lone_lane_cycles` and `joint_stall_cycles` start at -1, which takes the default. The last three are not drain knobs. `lane_skew_cycles` bounds how many clocks one lane of a master in Mode B may trail the other before the master declares it dead, `lone_lane_cycles` how many clocks the one lane left after a death may go without progress, and `joint_stall_cycles` how many clocks a lane may wait while no port anywhere makes a handshake (section 9.10). `build_phase` hands each to the env as `a2c_lane_skew_cycles`, `a2c_lone_lane_cycles` or `a2c_joint_stall_cycles` when it is 0 or more; left at -1 it sets nothing, and the master keeps its own default, as under a hand-written env. `no_stimulus_expected` is not a drain knob either: at `check_phase` a run whose input agents sent no item and whose output counters were declared no transaction raises `A2C_NO_STIMULUS`, as the scaffolded `<block>_smoke_test` does until its `run_body()` sends stimulus, unless the flag is set. The base test counts the items through `a2c_items_sent`: from each input agent's `sqr`, or, for a status input, which has no sequencer, the values its driver applied from `cfg.value` that differ from the one before, counting from the default 0. A test whose stimulus bypasses both also needs an `expect_count()` or the flag. An input agent with neither a sequencer of its item type nor a driver that counts (`a2c_items_driven`) is an `A2C_CFG` error. The warning says only what the base test counted; a Mode B comparator or a check of the test's own may still have run. To give one log its own value, a test sets `a2c_drain_quiet_cycles`, `a2c_drain_deadline_cycles`, `a2c_drain_catchup_cycles`, `a2c_clock_stop_cycles` or `a2c_drain_cut_expected` on the log's path in its `build_phase`, after `super.build_phase()`. The log reads each as `int unsigned`, `int` or `uvm_config_int`, and the flag also as `bit`; `+uvm_set_config_int` on the command line works the same way. The type does not change which value wins. The log takes the entry `uvm_config_db` would pick if every entry had one type: the highest precedence, which in `build_phase` is the setter nearest the top, and of those the last set. So a hand-written env's `int` default does not override the base test's `int unsigned` values, and a later set for one port overrides an earlier blanket one. A winning entry of any other type, such as `longint unsigned` or `string`, is skipped with an `A2C_CFG` warning, and the knob takes the best entry of an accepted type, so the stray set costs only itself. The warning gives the value the knob takes. The drain reads these entries through `uvm_resource_pool`, not `uvm_config_db::get()`, so `+UVM_CONFIG_DB_TRACE` does not show its reads.

| Id | Severity | Meaning | What to change |
| :--- | :--- | :--- | :--- |
| `A2C_CUT` | `UVM_WARNING`; `UVM_INFO` when the cut dropped nothing or `drain_cut_expected` is set | the drain cut a port that never paused; the message gives the transactions left unchecked on each lane, and says whether the cut came at the deadline or on a re-cut's first clock | lower `drain_deadline_cycles` to cut sooner, end the stimulus before the drop, or set `drain_cut_expected` where the port is meant to stay busy to the end |
| `A2C_DRAIN` | `UVM_WARNING` | a log neither settled nor still flowing at its deadline, or its clock stopped with a transaction open; the message says what kept it from settling | read the log's `A2C_REPLAY`. Raise `drain_deadline_cycles` only if the model lane is slow, not short |
| `A2C_REPLAY` | `UVM_ERROR`; `UVM_FATAL` when a driver calls `replay()` with nothing recorded | at the end of the test a lane owes transactions: recorded responses the model lane never replayed, a model lane waiting for a response the DUT lane never recorded, a response or pick the model lane holds whose request it has not made, or a cut the lanes did not reach within `drain_catchup_cycles`. On `memory`, a model lane its BFM holds for credit is a model lane waiting for a record, and accesses the model lane made without credit are one more error at `check_phase`, with their count and the first of them. The fatal is a driver bug: the driver must check `can_replay()` first | a lane count mismatch is a design or model difference. A memory model lane held to the end made an access the RTL never made, or waits for input the RTL takes before that access (section 9.12). Memory accesses without credit mean the model's BFM ignores `<port>_model_credit`: it must hold access n until the credit exceeds n, as `memory_dst_bfm` does. A held AXI pick means the model keeps fewer requests outstanding than the RTL, which is a model defect (section 9.10). A held `lmmi` response means the model's master withdrew a request, which its monitor reports as `A2C_HOLD`. If the model lane is only slow after a cut, raise `drain_catchup_cycles` |
| `A2C_SKEW` | `UVM_ERROR` | a master in Mode B declared a lane dead (section 9.10). The other lane completed the item, or on AXI took a burst's AR or AW, took one of its W beats, or completed it, and this lane had not `lane_skew_cycles` clocks later. Or this lane, alone since the other died, went `lone_lane_cycles` clocks without progress; that message calls the death a likely consequence of the first `A2C_SKEW`. A death declared earlier on another port, which may have stalled this one, is named in the clause described under the drain, right after "declares the <lane> lane dead". Before the sentence about the lane that serves from then on, one that starts "Responders whose model lane waits" names each `A2C_DST` driver whose model lane waits for a transaction the DUT lane has not made, with the transaction and since when, such as a memory port held for its credit. The message names the item or burst, on AXI the channel, the dead lane, the knob that bounded it, and the lane that serves the sequence from then on. The master raises it once per lane | a lane that stopped answering is a design or model difference. If the model is only slow, raise `lane_skew_cycles`. A named responder on the model lane points at the model: it waits there for a transaction before taking the input the RTL takes first (section 9.12, input coupling). Read the first `A2C_SKEW` before the second, and raise `lone_lane_cycles` only if the live lane just stalls longer than it allows |
| `A2C_JOINT_STALL` | `UVM_ERROR` | no lane of any port made a handshake for `joint_stall_cycles` clocks of a master's port while a lane of it waited, in Mode A or Mode B. Raised once per run; it names every port whose live lanes waited and what each lane waited for, each responder whose model lane waits, in the sentence `A2C_SKEW` gives, and the deaths declared before it. In Mode B the masters then declare the live lanes of every port dead, whatever each port's own `joint_stall_cycles`. In Mode A no lane dies, and the run ends at the stall the way the run timeout ends it; in a test with no run timeout the masters go on waiting and count toward no second stall | the whole environment stopped, so the cause may lie in the DUT, the model or the stimulus: look for a deadlock between ports or an event nothing produces. Raise `joint_stall_cycles` if the environment legitimately goes that long with no handshake anywhere |
| `A2C_RUN_TIMEOUT` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` for a run that ended in time | the run phase of a generated test had not ended after its budget of clocks of the block's first clock, counted from its reset release. The budget is derived from the work the test declared, or fixed by `run_timeout_cycles` or `run_timeout.fix()`, and the message says which. Raised once; it gives the clocks per unit of declared work and names the ports whose masters wait and the objectors of the run phase and of each other running task phase. Those phases then end, and so does each task phase other than the run phase as it begins, so `check_phase` reports what is missing. An info at `UVM_NONE` names the progress rules a derived budget defers to, once, and another each phase ended as it began that held an objection. The info at `UVM_LOW` gives a passing run's length and budget, or says the run had no run timeout | read the ports and objectors it names and the `check_phase` reports after it. If the test is legitimately longer, raise `run_timeout_factor` or `run_timeout_floor_cycles`, or fix the budget with `run_timeout_cycles` or `run_timeout.fix()` |
| `A2C_NO_STIMULUS` | `UVM_WARNING` | a generated test sent no transaction on any input, through an input agent's sequencer or a status input's `cfg.value`, and declared no transaction on any output counter | send stimulus in `run_body()` and declare the outputs with `expect_count()`, or set `no_stimulus_expected` in a test meant to send nothing |
| `A2C_PASSIVE` | `UVM_INFO` at `UVM_LOW` | a passive Mode B agent that can learn of a cut or a death found no active agent with its `cfg.vif` as its own, so it learns of neither on the port | nothing on a port no agent drives, such as an internal port of a top design. Where an active agent drives the port, give the passive agent that agent's interface instances |
| `A2C_RT_GAP` | `UVM_ERROR` | an open output unit went `rt_gap_cycles` clocks with no beat while its sink was ready, after the starvation credit. Raised once per unit; the message gives the unit's beats so far, its last beat, the raw idle and the credit | find the stall in the DUT; if the input caused it from further back than the window, raise `rt_latency_cycles` |
| `A2C_RT_DEADLINE` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` when a reported unit ends late | output unit k had not ended `rt_lag_cycles` clocks after its anchor input unit ended, less the stall credit. Raised the clock the deadline is reached; the info at the unit's end gives how late it was | a late unit is a slow design, one with no info a hung one; compare the lag with the summary's first and worst |
| `A2C_RT_REFUSAL` | `UVM_ERROR` | the DUT refused `rt_refusal_cycles` clocks of offered input within one input unit, not counting the clocks on which the sink stalled its output. Raised once per input unit | find why the DUT back-pressures its source |
| `A2C_RT_UNIT` | `UVM_ERROR` | an output unit ended before its anchor input unit had ended | the unit rules or the pairing (`in_units_per_out`, `out_units_per_in`, `anchor()`) do not match the design |
| `A2C_RT` | `UVM_INFO` at `UVM_LOW`; `UVM_ERROR` when failures went unprinted | the checker's summary at `check_phase`; the measure-only note on the model DUT; the count of failures beyond `max_reported` | read the summary's worst values to size the bounds |
| `A2C_VIDEO` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` for the corner, the contract and the summaries; `UVM_WARNING` for a zero-gap corner that did not reach the DUT lane as planned in Mode B | a video output frame that breaks its contract, an expected frame that never came out, or beats outside any frame | the DUT, or the contract when the specification says otherwise |
| `A2C_CFG` | `UVM_ERROR`; `UVM_WARNING` for a knob set as an unread type | a log with `drain_deadline_cycles` below `drain_quiet_cycles`, or with no `clk_vif`; an input agent that `a2c_items_sent` cannot count; a drain knob, `a2c_lane_skew_cycles`, `a2c_lone_lane_cycles` or `a2c_joint_stall_cycles` whose winning `uvm_config_db` entry is not `int unsigned`, `int`, `uvm_config_int` or, for `a2c_drain_cut_expected`, `bit`; an `a2c_rt_checker` with no output, with a rule whose input or unit rule is missing, or with a monitor that has no flow counts; a video port with no agent, or whose agent has no `mon`, or no `sqr` on the input, or no `model_mon` in Mode B; an `a2c_video_unit_rule` on a stream with no EOF that ends a line while no planned frame is due | raise the deadline or lower the window; give the driver's log its clock; set the knob as `int unsigned`, or the flag as `bit`, which the warning names; wire the checker or the video port as the error says |

`<block>_fail_test extends <block>_smoke_test` is a self-checking negative test of the counters. After `super.run_body()` it calls `expect_count(missing_count)` on the first output counter, so that output owes more transactions than the DUT sends. `missing_count` defaults to 1 and `+a2c_fail_missing_count=<n>` sets it. An `a2c_error_demoter` turns each `A2C_TXN_COUNT` `UVM_ERROR` into `UVM_INFO` and counts it. In `report_phase` the test raises `A2C_FAIL_TEST` as a `UVM_ERROR` unless exactly one was demoted, the counter's lane ends exactly `missing_count` short, and no other `UVM_ERROR` or `UVM_FATAL` was raised. In Mode B the counter holds both lanes to the count, so the test expects one demoted `A2C_TXN_COUNT` per lane and each lane `missing_count` short. It sets `a2c_rt_off` on `env*`, which wins over the `rt_*` knobs, their plusargs and `set_limits()`, so a missing transaction never also fails a real-time rule. A block with no counted output gets no fail test.

`<block>_model_mismatch_test extends <block>_smoke_test` is the self-checking negative test of the Mode B compare. It calls `inject_mismatch(mismatch_at)` on the `model_cmp` of the first counted output's agent, so that pair reports a mismatch whatever its items hold. `mismatch_at` defaults to 1 and `+a2c_model_mismatch_at=<n>` sets it. An `a2c_error_demoter` demotes only the `A2C_MODEL_CMP` error whose text carries `(injected mismatch)`, so a real mismatch stays an error. In `report_phase` the test raises `A2C_MISMATCH_TEST` as a `UVM_ERROR` unless exactly one injected report was demoted, the comparator compared at least `mismatch_at` pairs, and nothing else raised a `UVM_ERROR` or `UVM_FATAL`. Outside Mode B it stops in `connect_phase` with an `A2C_CFG` `UVM_FATAL`. Only a block with a model and a counted output gets it.

The test package reaches the build through the manifest, as `A2C_UVM_TEST_SV_<top>`. A project that needs more SV files adds them by its own means. `examples/uvmVideo` (`uvm/uvmVideo_uvm_test_pkg.sv`, section 9.9) is the reference for a video test package: its adapters, the two hooks, an exact-pixel contract and the corner tests.

### 9.7 Building and running

`USE_UVM=1` with `USE_XCELIUM=1` or `USE_VCS=1` includes `include/make/a2c-uvm.mk`. It stops make without one of the two, and with `VL_DUT=` empty. `VL_DUT` compiles the block's RTL into the snapshot, which every UVM snapshot needs, because the testbench module instantiates the RTL in its rtl branch.

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `UVM_TOP` | `A2C_UVM_DEFAULT_TOP_<HDL_TOP_MODULE>` | the testbench top's stem, `<block>_<variant>` or `<block>` |
| `UVM_DUT` | the first of `A2C_UVM_DUTS_<top>`: `model`, or `rtl` for a block with no model | the DUT the snapshot holds. `rtl` adds `+define+A2C_UVM_RTL_DUT`. `both` adds `+define+A2C_UVM_BOTH_DUT` and builds Mode B, the RTL beside the model as its reference (section 9.12). A block with no model has neither `model` nor `both` |
| `UVM_TEST` | empty | the `+UVM_TESTNAME` the run script adds when a run names none |
| `UVM_TOPOLOGIES` | `<UVM_TOP>:<each DUT of its block>` | what `uvm_snapshots` builds: space-separated `<top>:<dut>[,<dut>]` entries |

`make gen` checks `UVM_TOP` and `UVM_DUT` against the manifest and names the valid values. Under `USE_UVM` the flow sets `VL_INST` empty, `DUT_TOPOLOGY` to `uvm_<UVM_TOP>_<UVM_DUT>` and `DUT_ELAB_ARGS` to `<block>_uvm --uvmDut <dut> --uvmTop <top>`. It adds `common/systemVerilog/uvm/a2c_uvm.f`, then `-F` of each builder layer list in `A2C_LAYER_UVM_F_FILES`, and the defines `A2C_UVM_PKG=<variant package>` and, for `rtl`, `A2C_UVM_RTL_DUT` or, for `both`, `A2C_UVM_BOTH_DUT` to the HDL arguments. It appends the variant package, the test package and the testbench module to `A2C_SV_FILES`, after `rtl.f`, and makes them, the UVM library files, the agent packages, each layer list and each file a layer list names prerequisites of the snapshot. A layer list holds file paths only, relative to its own directory. It adds `$(A2C_UVM_SRC_DIRS)` to the C++ sources, and on VCS `common/systemc/uvm/uvmVcsElabStub.cpp` too.

| Command | Builds |
| :--- | :--- |
| `make -j8 USE_UVM=1 USE_XCELIUM=1 all` | the snapshot of `UVM_TOP` and `UVM_DUT`: `build_xrun/run_uvm_<top>_<dut>`, a script, over the snapshot directory `xcelium_uvm_<top>_<dut>.d` in the rundir |
| `make -j8 USE_UVM=1 USE_VCS=1 all` | `build/run_uvm_<top>_<dut>`, a run script, beside the simv `build/run_uvm_<top>_<dut>.simv` |
| `make -j8 USE_UVM=1 USE_<VENDOR>=1 uvm_snapshots` | one snapshot per top and DUT that `UVM_TOPOLOGIES` names, built one after another, because they link the same C++ objects and, under VCS, share `AN.DB` |

Vendor recipe items, under `ifdef USE_UVM`:

- Xcelium (`a2c-xrun.mk`): `-uvm -uvmhome CDNS-1.2`. Without `-uvmhome`, xrun picks UVM 1.1d. Every Xcelium snapshot build takes `-elaborate` (section 5.3). Without it, a UVM build would simulate with no `+UVM_TESTNAME` and end in a `UVM_FATAL`. The registrar objects depend on the boundary stamp, because they include every top's shell from `.gen/vl`.
- VCS (`a2c-vcs.mk`): `-ntb_opts uvm-1.2` on `vlogan` and `vcs`. In the `vlogan` flow that option only adds the UVM include directories, so a `vlogan` run with no source files analyses `uvm_pkg` first. Its stamp `AN.DB/uvm_pkg.a2c_stamp` sits in `AN.DB`, which a failed link deletes, and an options file re-analyses it when the `vlogan` options or `VCS_HOME` change.
- VCS: after the wrapper tops' `-sc_model` runs, one `-sc_model` run per UVM top makes every top's shell, because the registrar includes them all. The defines are repeated, because `A2C_UVM_RTL_DUT` and `A2C_UVM_BOTH_DUT` change the testbench module's body. Before the shells, each other top's variant package is analysed, and each other block's test package is analysed once, with `A2C_UVM_PKG` naming one of that block's variant packages. These steps take the RTL analysis's options, defines and library files (`a2c.f` and the HDL arguments, `a2c_uvm.f` among them), minus the selected top's `A2C_UVM_PKG`, so the library units they re-analyse into `AN.DB` match the RTL analysis. They leave out `rtl.f` and the other SV files, which the RTL analysis has already put in `AN.DB`. Other tops are never elaborated.
- VCS: `common/systemc/uvm/uvmVcsElabStub.cpp` gives the `-syscelab` discovery link a weak `m__uvm_report_dpi`. `-ntb_opts uvm-1.2` puts the UVM DPI C code into both links, and only the simv link defines that SV export. The stub aborts if it is ever called.

The run scripts take the test's arguments unchanged, apart from the seed:

- Xcelium: arguments starting with `+` go to the simulator, every other argument goes to `sc_main` as `+systemc_args+<arg>`, and `--seed N` or `--seed=N` also adds `-svseed N`. This applies to every topology, so non-UVM Xcelium runs also get `-svseed`. The script exports the build's `LM_LICENSE_FILE`.
- VCS: simv passes its whole command line to `sc_main`, so the script only converts the seed. Its `dec()` reads `0x` or `0X` as hex, a leading `0` as octal, as `sc_main`'s `std::stoul` does, and anything else as decimal. `random` draws a 32-bit value from `/dev/urandom`. The script then passes one decimal value both as `--seed` and as `+ntb_random_seed`, the only form the SV solver reads, so the `Cmd line:` line of the log records the seed. A seed that is not one of those forms, or that does not fit 32 bits, stops the run with exit status 2 before simv starts. The digit count is checked before the arithmetic, which would wrap past 64 bits.
- Both: with `UVM_TEST` set, a run that names no `+UVM_TESTNAME` gets `+UVM_TESTNAME=$(UVM_TEST)`. The script records `UVM_TEST`, so a change rewrites it.

Xcelium's `-svseed` reads the same three forms as `std::stoul` with base 0, so the Xcelium script passes the value through. A malformed or over-32-bit `-svseed` value only warns there (`SVSEEDW`, seed 1). A probe on Xcelium 26.03 showed `010` giving seed 8, `0x1f` and `0X1F` giving 31, and `08`, `1f` and 4294967296 warning. `sc_main` still parses `--seed` itself, and stops with exit status 2 on a value with no leading digits. `--seed random` draws separately on the two sides under Xcelium and once under VCS. A seed never gives the same stimulus on both vendors.

A run names its testbench, DUT and top the way it does at elaboration. `dutRun.py` maps a test with `--uvmDut <dut> --uvmTop <top>` to `<base>_uvm_<top>_<dut>` and stops with an error when only one of the two is given. The config rejects a `--uvmDut` its block does not have and a `--uvmTop` that is not one of its block's stems, and the wrapper fails a run whose `--uvmDut` does not match the snapshot (section 9.8). From `examples/uvmVideo/rundir`:

```
../../../dutRun.py build_xrun/run uvmVideo_uvm --seed 7 --verbosity=low \
    --uvmTop uvmVideo --uvmDut rtl +UVM_TESTNAME=uvmVideo_smoke_test
```

A regression file builds with `make -j8 USE_UVM=1 USE_<VENDOR>=1 uvm_snapshots` and runs `../builder/dutRun.py build_xrun/run <block>_uvm` or `build/run <block>_uvm`, with `--uvmTop` in the shared arguments, `--uvmDut` per group and `+UVM_TESTNAME` per test entry. In a base example the runner is `../../../dutRun.py`. `examples/uvmVideo/rundir/regr_uvmVideo_uvm_xcelium.json` and `regr_uvmVideo_uvm_vcs.json` are the reference. Each has three groups, `model_dut`, `rtl_dut` and `both_dut`, with `--uvmDut model`, `rtl` or `both` and the labels `mdl`, `hdl` and `both`; the `both_dut` group runs the Mode B snapshot and adds `<block>_model_mismatch_test`. Each group runs the smoke test, a test per corner the input carries and the fail test, and the `blanking` and `random` corners three times with seed `random`. `examples/uvmMem/rundir/regr_uvmMem_uvm_*.json` follow the same layout with a smoke, a random and a fail test, the random test three times per group with seed `random`. List the rule files in this order: `config/regrRules/uvm.json` by its relative path from the rundir, then any project rule file, then `default.json` and the vendor file. The JUnit report of `regrLauncher.py` keeps only the first failure, so the order decides which failure it shows. `uvm.json` ships in base, and projects reference it in place. It fails a run on a `UVM_ERROR` or `UVM_FATAL` report, a non-zero summary count, or a log with no UVM report summary.

#### Seed reproducibility

A test run twice with one seed on one simulator must give the same transactions on every port. `seedRepro.py`, beside `regrLauncher.py` in base and `../builder/seedRepro.py` from a project's rundir, checks it. It runs one command twice, echoes both runs' output to stdout as it arrives, each after an `A2C_SEED_REPRO run <n>: <command>` line, and ends with an `A2C_SEED_REPRO PASS:` or `A2C_SEED_REPRO FAIL:` line that names the reason. A run passes when it exits with status 0, prints a UVM report summary, and has no `UVM_ERROR` or `UVM_FATAL` report and no non-zero count of either, before or after the summary. It fails when every digest it prints counts no transaction, because such digests match whatever the seed; one empty port among others is fine. It also fails when a port with `paired=1` reports both lanes with different item counts: its comparator pairs every item, so a correct run counts the same on both lanes, and a difference is the sign of a lane whose monitor feeds no digest. A port with `paired=0` is left out of this rule, since its lanes may count apart in a correct run. The command passes, with exit status 0, when both runs pass and the two runs' `A2C_DIGEST` lines are the same, in the same order.

The command must carry its seed as `--seed N` or `--seed=N`, so a regression entry repeats the value the launcher resolved, including the value it drew for seed `random`. `--seed-arg=<option>` names another option, such as `-svseed` or `+ntb_random_seed`, for a command that calls the simulator directly. `--differ <seed>` inverts the check: the second run takes that seed in place of the command's, and the command passes only when the lines differ, which shows the digests follow the stimulus a seed draws. The loopback runs both modes (section 9.9).

A regression file gives the runner a group of its own, `seed_repro`, whose `command` puts `seedRepro.py` before the group's usual command, for example:

```json
"seed_repro": {
    "command": "../builder/seedRepro.py ../builder/dutRun.py build_xrun/run <block>_uvm",
    "timeout": 1800,
    "labels+": ["seed"],
    "test_group": {
        "<block>_random_test_both": {
            "args+": "--uvmDut both +UVM_TESTNAME=<block>_random_test",
            "seed": "random"
        }
    }
}
```

The group's `timeout` is twice the file's, because each entry runs twice. Both runs' output lands in the launcher's one log for the entry, so the rule files check both, and the retention policy keeps or drops both. Reproduction is per simulator. The same seed gives different stimulus on Xcelium and VCS, so a `seed_repro` entry never compares across them.

### 9.8 Completion and the verdict

The testbench module clears `uvm_root`'s `finish_on_completion`, so `run_test()` returns after the report phase. It then writes the `UVM_ERROR` plus `UVM_FATAL` count to `uvm_errors` and raises `uvm_done` one clock later. The wrapper's `uvm_watch` thread reads both pins, `rtl_dut` and `model_dut`: (0, 1) is the model snapshot, (1, 0) the rtl one and (1, 1) the both one. It fails the run with a reason through `errorCode::fail` when the count is not zero or the snapshot holds another DUT set than `--uvmDut` asks for, marks the run completed and casts the one end-of-test vote. Its `eot_thread` calls `sc_stop()`, because the testbench has no External to do it. The config's `final()` passes a completed run that nothing failed, and fails one where `uvm_done` never rose with `UVM testbench did not finish: uvm_done never rose`.

| Event | Verdict |
| :--- | :--- |
| `UVM_ERROR` | counted on `uvm_errors`; the wrapper fails the run with `UVM reported <n> UVM_ERROR/UVM_FATAL` |
| `UVM_FATAL` | `$finish` inside `run_test()`, so `uvm_done` never rises. Under Xcelium `sc_start` returns and `final()` fails the run. Under VCS the `$finish` exits through `main.cpp`'s `VcsSetExitFunc` handler, which fails the run with `simulation ended by $finish before the end of test` when nothing had set an exit code, and prints the recorded reason when something had. The handler acts from just before the zero-time `sc_start`, because a `UVM_FATAL` such as an unknown test name fires inside it |
| wrong snapshot | `--uvmDut <dut> does not match the snapshot: the run expects the <set>, and the SV testbench holds the <set>`, where each `<set>` is `model DUT`, `RTL DUT` or `model and RTL DUTs` |
| X or Z at an RTL port | section 9.4 |
| BFM contract break | the UVM config sets `bfmContractCheck::failOnBreak`, so the first break of each rdy_vld, axi4_stream or memory check, such as `SystemC stalled a backpressure: false producer`, fails the run. raw's missed-edge count is built warn-only and never fails. Other flows keep these checks as warnings |
| `Q_ASSERT` | unchanged; the UVM report summary is missing, and `uvm.json` reports that too |

`try_sc_start` keeps a failure reason set during the run and appends the elapsed time to it. A passing run's summary is unchanged. `errorCode::fail` overwrites, so the summary shows the last failure recorded.

### 9.9 Farm-only tests in base

Two tests need a four-state simulator with UVM and run only on the farm. Source the simulator setup, then run from any scratch directory:

| Command | Builds | Passes when |
| :--- | :--- | :--- |
| `common/systemVerilog/xcheck_test/run_xcheck_test.sh xcelium\|vcs [<tb.sv> <source>...]` | `xcheck_tb.sv` with the checker of each type in the script's `TYPES` into `./xcheck_<sim>`. `xz_count.c` stands in for `a2c_xz_fail` and counts each checker's reports. Given a testbench, the script builds it instead, after the sources that follow it, with the testbench file's stem as the top. A builder layer runs its own checker cases this way, for example Pro's `pro/common/systemVerilog/xcheck_test/lmmi_xcheck_tb.sv` | every case logs `XC_PASS`, and the number that pass equals `CASES` in `xcheck_tb.sv`. The cases cover qualified and unqualified X per type, every control signal, X before arming and during a later reset, a power-on X reset, one report per instance, the apb completion qualifiers, `rdata` only while `ack` for req_ack and pop_ack, memory `read_data` X after a read followed by a write of that address, a write elsewhere, a read, no access, or a reset, external_reg `wdata` only while `write` is non-zero, bound and unbound `tuser`, bound and unbound AXI ID and USER signals, and a reset released in delta cycles before the first edge |
| `common/systemVerilog/uvm/loopback/run_loopback.sh xcelium\|vcs [seed [<layer.f>...]]` | `a2c_uvm_loopback_tb.sv` with every agent package `a2c_uvm.f` lists and the `<type>_if.sv` beside each, into `./loopback_<sim>`. Each `<layer.f>` adds a builder layer's agent packages after `a2c_uvm.f`, the `<type>_if.sv` beside each, and the `*.sv` files in the `loopback/` directory beside the list, compiled after the testbench | every test logs `LB_PASS` with zero `UVM_ERROR` and `UVM_FATAL`. The tests are the classes each `*_lb_tests.svh` file registers with `` `uvm_component_utils `` under a name ending in `_test`. The script fails when a file registers none. Then each `seed_repro_*` check runs `txn_digest_rv_test`, `txn_digest_er_test`, `txn_digest_axi_test`, `txn_digest_cut_test` or a test with no digest twice under `seedRepro.py` and must end with its verdict: the same seed matches; two seeds differ when the seed changes the data, only the timing, only the `external_reg` rdata levels, or only the AXI read data; two seeds on fixed stimulus fail; the same seed fails when one port's stream changes between the runs; a `paired=1` port whose lanes count different items fails, and a `paired=0` port whose lanes count different items passes, a status port or one whose in-order comparator a drain cut; and a test with no digest fails. Each check's log is `<check>.log` |

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

The loopback testbench includes one `<type>_lb_tests.svh` per agent type, plus `no_backpressure_lb_tests.svh`, `a2c_txn_counter_lb_tests.svh`, `a2c_mem_model_lb_tests.svh`, and the Mode B files `a2c_model_cmp_lb_tests.svh`, `a2c_replay_drain_lb_tests.svh`, `a2c_lane_watchdog_lb_tests.svh`, `a2c_gen_base_test_lb_tests.svh`, `a2c_reg_read_lb_tests.svh` and `axi_mode_b_lb_tests.svh`. Base holds 543 tests:

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
| `txn_count_*_test` | the counter's clean, missing, extra, unwaited, repeated, dropped and late cases; the two-lane counter of Mode B, each lane short or extra; a clock that stops, slows, pauses or runs a runt pulse |
| `a2c_mem_model_test` | reads, writes and the three fill policies, unwritten words reading the same in any order, one `A2C_MEM` line per model |
| `lmmi_random_test`, `lmmi_reuse_test`, `lmmi_counter_test`, `lmmi_monitor_checks_test` (Pro) | as the other types |
| `model_cmp_*`, `status_cmp_*`, `midstream_guard_*`, `replay_log_*` (`a2c_model_cmp_lb_tests.svh`) | the Mode B classes of section 9.12 on their own: match, mismatch, leftovers on either side, keyed order, injection, the report cap, cut and uncut, a dead lane; the three status policies; the guard's error and its `+a2c_predict_midstream` demotion; the replay log's record, replay and leftovers |
| `reg_read_*` (`a2c_reg_read_lb_tests.svh`) | register reads in Mode B. A read of a volatile register, of a register with one volatile field, or of a read-only memory while outputs are pending, with and without `+a2c_predict_midstream`, its compare demoted per read and no window opened, also with `inject_mismatch()` and across `cut()` and `uncut()`. Volatile reads when quiescent, after a lane death, and non-volatile, read-write memory or unmapped reads while pending. The skip list by address, `skip_reg()` with and without a map and `skip_mem()`, each also with a map that does not hold the register or memory, with the response and writes still compared and the `A2C_REG_SKIP` lines. The same reads through a register model and the apb agent's pins in Mode B and Mode A. `a2c_reg_map` memories whose rows are narrower than their stride, written by burst and by row and read back over the pins, each row in its own bus words at its stride, with `get_mem_by_offset()` and `get_addresses()` on a byte-addressed and a word-addressed map |
| `<type>_mode_b_test`, `<type>_mode_b_mismatch_test` and the other `<type>_mode_b_*` tests, every base type in both roles; `axi_mode_b_lb_tests.svh` for the AXI agents | two lanes of one interface type looped back, the same traffic compared on both and, where the type compares data, a mismatch forced on one lane; a lane that leads or trails; the responders' replay and drain; the AXI keyed compare and `reorder` with each lane leading in turn; lane deaths, lone lanes and passive agents; on `memory`, the model lane's credit, accesses made without it, two ports of one shared model, a model lane read that must return the DUT lane's word after another port rewrote it (`memory_mode_b_dst_rewrite_between_test`), the driver's held counts against the peer's, and a master's stall that a held memory read causes, under the lane skew rule and under the joint stall rule (`memory_mode_b_d1_stall_test`, `memory_mode_b_d1_joint_stall_test`) |
| `drain_*` (`a2c_replay_drain_lb_tests.svh`) | the end-of-test drain: settle, cut, re-cut, catch-up and clock stop, with deaths during each |
| `a2c_lane_watchdog_rules_test`, `joint_stall_*` (`a2c_lane_watchdog_lb_tests.svh`) | the lane skew, lone lane and joint stall rules, and which transfers count as progress |
| `js_rv_*`, `js_axi_*` (`a2c_joint_stall_lb_tests.svh`) | the joint stall rule in Mode A on a configurable pipeline: a DUT that stops taking input, one that is slow but keeps moving, a wait beside a moving port, an idle test, the bound at 0, two waiting ports, the run timeout's deferral to the rule and its leaving out a rule whose clock has stopped, and the run's end at the stall; and AXI read and write masters whose slave never returns R or B, held by the outstanding burst alone |
| `gen_base_*` (`a2c_gen_base_test_lb_tests.svh`) | the generated base test's knobs: the drain and lane rule settings, `A2C_NO_STIMULUS`, the run timeout's budget, deferral and phase handling, and a Mode A joint stall ending the run (`gen_base_joint_end_*`) |
| `lb_vid_*_test_<corner>`, `vid_*` (`a2c_video_lb_tests.svh`) | the video library against `lb_video_pipe`, a configurable pipeline: every corner that applies, on three families, `raw` into `axi4_stream`, `axi4_stream` into `axi4_stream`, and `rdy_vld` into `rdy_vld` with a struct payload that carries EOF, each with fixed and random blanking, and a fourth, `lb_video_pack`, that packs one pixel per beat into two with a padded last beat; one rejection per `validate()` rule, through the macro, and for a Mode B output agent with no `model_mon`; one defect per pipe knob (a lost first beat, a missing EOL, also under an exact pixel check, a missing EOF, merged frames, lv in the blanking, a cropped line, a flipped pixel, a dropped frame, last line or EOF) with the exact `A2C_VIDEO` reports; markers passed through as received, and an EOF added or lost against them; a contract that drops a frame; Mode B on both lanes, a model-lane defect, a model lane that trails on a zero-gap corner, and a DUT lane that trails, so a model-lane frame ends before the sequence has sent all of it; Mode A exactness of the zero-gap corners under DUT backpressure, and Mode B exactness with another sequence's items on the input before, between and during the runs; a corner's knobs derived from the geometry plusargs, on the test's cfg and on a cfg the test sends, and a plusarg or test value that overrides one; the run timeout following the blanking; a test env that builds after `video`; the random corner's cut parity; `a2c_video_unit_rule` fed from the plan, on cut and random frames, and `a2c_video_flow_counts` under `a2c_rt_checker`, and the rt checkers turned off only on an output whose contract drops frames |

A test file adds tests that a macro defines with a line `// LB_TESTS <test>...`, because `run_loopback.sh` finds the others by their `` `uvm_component_utils `` lines.

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
- `test_memory_bfms.py`, the memory BFMs' read timing, the src BFM's skipped-access count, the dst BFM holding each access for its credit, and dst BFMs keeping the model's program order across ports under a write order, with and without it, including a port behind a producer-shape thunker and a port on a slower clock;
- `test_uvm_model_credit.py`, the Mode B credit pins, the testbench module's `a2c_credit_if` per credited port, the env's fetch and the wrapper's `setModelCredit()` call and its `setWriteOrder()` call only in a model-only run, on a copy of `examples/uvmMem`, and no credit pins on the same copy without a model;
- `test_axi_write_src_bfm_w_first.py`, `axi_write_src_bfm` holding `wready` low for a W beat that comes before its AW;
- `test_port_transfer_size.py` and `test_uvm_max_transfer_bytes_flag.py`, the per-port transfer size and the agents that declare `max_transfer_bytes`;
- `test_watchdog_uvm_stall_check.py`, the SystemC watchdog's stall check turned off under UVM (section 9.11).

The UVM runs of `examples/uvmMem` need such a simulator too; its SystemC and Verilator runs are the `uvm-mem` pipeline target. The example is the end-to-end bench for a block with RTL and a model on UVM. Its DUT reads and writes one memory through two `memory` `src` ports, and its env shares one `a2c_mem_model` between them, so its Mode B runs pass the credit pins through the shells, the wrapper and `memory_dst_bfm`. From its `rundir`, with the simulator setup sourced:

```
make regr_uvm_xcelium        # or regr_uvm_vcs
```

Each runs the smoke, random and fail tests on the model, the RTL and both, and `model_mismatch` on both. The example sets `A2C_ROOT` to the base checkout. In a builder checkout whose layer sets the toolchain, pass `A2C_ROOT=<builder root> REPO_ROOT=<example>` to `make` so the layer's settings apply.

`examples/uvmVideo` is the end-to-end bench for the video library. Its DUT takes a `raw` video stream, fv, lv and two pixels per clock, and sends an `axi4_stream` with SOF on `tuser[0]` and EOL on `tlast`, through a registered stage. `uvmVideo_video_test` uses `axi4_stream_video_adapter` on the output and checks pixels exactly, and `` `a2c_video_corner_tests `` adds a test for each corner a clocked input allows. Its SystemC and Verilator runs and RTL lint are the `uvm-video` pipeline target, which `make push-test` runs. From its `rundir`, `make regr_uvm_xcelium` or `make regr_uvm_vcs` runs smoke, the nine corners, with `blanking` and `random` at three random seeds, and fail on the model, the RTL and both, and `model_mismatch` on both.

### 9.10 Agents

Every interface type with `uvmAgent: true` ships one agent package, `interfaces/<type>/<type>_uvm_pkg.sv`, or `builder/pro/interfaces/<type>/<type>_uvm_pkg.sv` for a Pro type. The 13 base types and Pro's `lmmi` carry the flag. A package holds `<type>_item`, `<type>_config`, the drivers, `<type>_monitor` with the analysis port `ap`, a sequencer, except for `status` and the `A2C_DST` drivers that choose nothing per transfer, and `<type>_agent`, which exports `item_t` and `config_t`. Every config has `vif`, `model_vif` (null outside Mode B, section 9.12), `clk_vif`, `port_name`, `is_active` (default `UVM_ACTIVE`) and `role` (default `A2C_SRC`). The role is the side of the interface the agent plays, so an `A2C_SRC` agent drives a DUT `dst` port and an `A2C_DST` agent serves a DUT `src` port. A `UVM_PASSIVE` agent builds only its monitor.

Handshake and memory types have one `<type>_driver` that switches on the role. The AMBA types have `<type>_master_driver` for `A2C_SRC` and `<type>_slave_driver` for `A2C_DST`. Their package headers give the AMBA 5 names: Requester and Completer for APB, Manager and Subordinate for AXI.

The pin-timing rule: drivers change pins 100 ps after a rising edge through `a2c_clk_if.drive_edge()`, and monitors sample at the falling edge through `sample_edge()`. Every other source of boundary pins, the RTL and the SystemC BFMs, changes them only between a rising edge and the next falling edge, so a monitor sees the value the next rising edge transfers. On rdy_vld, axi4_stream and push_ack every src driver raises valid without waiting for ready and holds it, with its data, until the transfer completes, as the interface definitions require.

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
- **Memory-backed**, `memory`, `lmmi` and the apb and AXI slaves. The driver serves each access from `cfg.mem`, an `a2c_mem_model`, which the agent creates when the test leaves it null. A `memory` read takes its word at the sample edge, before the rising edge applies a write, so a same-clock read and write of one address through two agents sharing a model return the old word, as `memory_dp` does. In Mode B the `memory` `A2C_DST` driver also drives `cfg.credit_vif`, which holds the model lane's accesses (section 9.12). The apb slave maps bus byte k to `paddr + k`, with no alignment, and writes every byte, because `apb_if` has no `pstrb`. An address in `error_ranges` gets `pslverr` or `SLVERR`, leaves the memory untouched and reads 0. An AXI write burst with any beat in a range writes nothing.
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
- **Sharing.** The env creates no model, so two ports of one memory keep separate models. To share one, create it in the `<block>_tb_env` subclass's `build_phase` after `super.build_phase(phase)`, fetch each port's config with `uvm_config_db#(<port>_config_t)::get(this, "<port>_agent", "cfg", cfg)`, and set `cfg.mem` on both. The env's `<port>_cfg` handles are locals of its `build_phase`, and the agents read their configs later in the build, so the objects set here are the ones the agents use. In Mode B each port's model lane waits for its credit, so a read through one port that the DUT lane makes after another port's write gets the written word on both lanes (section 9.12).

#### The AXI burst limit

One AXI item is one burst. The item's constraints keep AXI4 legality: INCR up to 256 beats, FIXED and WRAP up to 16, WRAP of 2, 4, 8 or 16 beats from an aligned address, `size` within the bus, and no INCR burst across a 4 KB page, or across the address space when that is smaller. `axi_write` needs `$bits(data_t) == 8 * $bits(strb_t)`, one strobe bit per byte, or the agent stops at build with `A2C_CFG`. A bus that is not a power-of-two number of whole bytes carries only full-width transfers.

- The env sets `max_transfer_bytes` to the port's transfer size, per variant (`pysrc/processYaml.py`, `getBDUvm`). A type gets it when its definition sets `uvmMaxTransferBytes: true`, and its `<type>_config` must declare the member, which a unit test checks.
- The transfer size is a connection's `maxTransferSize` override where one reaches the port at that variant, directly or through `connectionMaps`, and otherwise the interface's `maxTransferSize`. An end that a block declares with another interface is bound through an adapter and keeps its own interface's size. An interface `maxTransferSize` that names a param of the block takes each variant's binding.
- `make db` works the size out once (`calcPortTransferSizes`), for the ports of each block whose generated code builds one `<block>Channels`: a `hasTb` or `hasUvm` block, and a block made by a fileMap entry that sets `buildsChannels: true`, as Pro's `tandem` wrapper entry does. It persists the sizes as `PORTTRANSFERSIZES`. The env and `<block>Channels` (`templates/systemc/baseClassDecl.py`, `channelConstructor`) both read it, so the agent limit never exceeds the model's burst buffer. Those blocks build one channel per port, and the testbenches one agent per port, so `make db` rejects connections that give one such port different sizes at one variant, naming them, where the port uses its size: on a multi-cycle interface, whose channel splits bursts at it, or on a `hasUvm` block's port whose type sets `uvmMaxTransferBytes`. Any other block gets a channel per connection, sized by that connection, so one block type may sit on connections of different sizes.
- `<block>Channels<Config>` is one class template, so on a parameterized block `make db` also rejects a multi-cycle port that an override sizes differently between variants. A variant no override reaches takes the interface value, and an override equal to the interface's value at a variant is no override there. The error offers two fixes: remove the override, or replace it by binding the interface's `maxTransferSize` to a parameter of the block so each Config carries its own size. That binding sizes every port of the interface, not only this one.
- An override is a positive number of bytes, a project constant or an enumerator, which resolves as the interface's own `maxTransferSize` does, or a parameter of the block that holds the connection. The holder's channel for the connection spells the name in the holder's scope, where it reads the holder's Config. Each end takes the holder's binding: at its own variant when it inherits the holder's Config, and otherwise at every variant the holder is built at, so a testbench end that the holder's variants size differently is rejected as one port with two sizes. `make db` rejects an undeclared name, a value that is not a whole number, a value of zero or below, and a parameter the holder does not take, naming the connection. A literal 0 is the default and means no override.
- The limit counts bytes, `(len + 1) << size`. The SystemC channel counts the same value in beats, and a beat carries at least one byte, so the byte reading is safe on every bus width.
- `<type>_base_seq::new_item()` returns an item whose constraint holds it within the port's limit. The master refuses any item above the limit with an `A2C_CFG` `UVM_ERROR`, because an item made without `new_item()` carries no limit. `axi_write_master_driver` also refuses an item without one data, strobe and `wuser` entry per beat.
- `id_unbound` is set on a port that leaves unbound the parameter its type names in `uvmIdParam`, `id_t` on `axi_read` and `axi_write`. The design behind it carries no ID and may answer every burst with ID 0, so the master sends every burst with ID 0, and the `axi_write` monitor does not compare `wid` with `awid`. `axi_write` drives the AXI3-style `wid` equal to `awid`.
- `reorder` lets a slave answer any burst whose delay has passed, as long as each ID's bursts keep their AR or AW order. With `reorder` at 0 it answers in AR or AW order. The slaves accept W beats before their AW and hold them until the AW arrives.
- The master keeps up to `max_outstanding` bursts open on any mix of IDs and takes R beats of different bursts interleaved, as the monitor does. The slaves never interleave: a read burst's beats go out together once it is picked.

#### Lane deaths in Mode B masters

Every `A2C_SRC` driver in Mode B that waits for each lane's own handshake puts each item on both lanes and moves on only when both are done: push_ack, notify_ack, req_ack, pop_ack, rdy_vld, axi4_stream, the apb master, Pro's `lmmi` and the AXI masters. A lane that stops answering would stop both lanes, so each of these masters bounds its lanes through `a2c_lane_watchdog`, with three rules. Each reads its knob from the `uvm_config_db` as `a2c_<knob>` at the start of the master's run phase, with a default of 200000 clocks, and 0 turns it off:

- **Skew**, `lane_skew_cycles`. One lane completed the item, or on AXI took a burst's AR, AW or W beat or completed the burst, and the other has not `lane_skew_cycles` clocks later. The master raises `A2C_SKEW` and declares the trailing lane dead.
- **Lone lane**, `lone_lane_cycles`. Once one lane is dead, the live lane goes `lone_lane_cycles` clocks in a row without progress while it has something to wait for. The master declares it dead too, with an `A2C_SKEW` that names `lone_lane_cycles` and calls the death a likely consequence of the first.
- **Joint stall**, `joint_stall_cycles`. Both lanes are live, at least one has something to wait for, and no lane of any port makes a handshake for `joint_stall_cycles` of the port's clocks in a row. The rule fires only when the whole environment has stopped: a port that waits a frame for a configuration word while the streams of the frame move, or a store-and-forward block that holds its input while it outputs, never stalls, however long it waits. The first master to reach the bound raises one `A2C_JOINT_STALL` for the run. It names every Mode B port whose live lanes waited, a port with one lane dead included, and what each lane waited for, and says that no port made progress, so the cause may lie in the DUT, the model or the stimulus. Every Mode B master then declares the live lanes of its port dead, so no second stall can follow. A port's `joint_stall_cycles` decides only whether that port can raise the stall: a port with it at 0 never raises it, but is named if it waits and loses its lanes like every other. While the skew bound is on, a lane that trails the other belongs to the skew rule, so the two rules never fire on one stall.

A lane with nothing to wait for counts as making progress, so an idle port never stalls. A dead lane never comes back. What a death does:

- **The dead lane freezes.** The master drives no new item on it. A request it had raised stays up with its payload until that handshake, as the protocols require, and then drops for good.
- **The live lane serves the sequence.** Every open and later item completes on the live lane. The response the sequence gets, `rdata` on req_ack and pop_ack, the read word on `lmmi`, `prdata` and `pslverr` on apb, comes from the DUT lane, or from the model lane once the DUT lane is dead. Once both lanes are dead, every open and later item completes at once, a response with what it was sent with.
- **The comparator and the passive agents learn of it.** A master whose agent has a `model_cmp` in the `A2C_SRC` role, req_ack, pop_ack, apb, `lmmi` and the AXI agents, tells it through `lane_dead()`, and tells the passive agents on the pin set through `a2c_pin_registry`, as the AXI subsection below describes.
- **The drain keeps the death to name it** in later reports, with the clause the AXI subsection below describes.

The memory and external_reg `A2C_SRC` drivers put each access on both lanes in one clock and wait for no lane's handshake, so neither lane can trail, and status has no handshake. They declare no death.

The handshakes the joint stall rule counts, in one record, `a2c_joint_watch`, come from the monitors, one count per transfer a monitor sees, whatever the agent's role and lane count: a Mode A port, and a single-lane responder in a hand-written Mode B env, count as a Mode B port does. A transfer is a push_ack, notify_ack, req_ack or pop_ack ack, a rdy_vld or axi4_stream transfer, an apb transfer, a memory access, an external_reg write, an AXI AR, R beat, AW, W beat or B, and an `lmmi` request that ready takes or a read's `rdata_valid`. Status and raw have no handshake, and an external_reg `rdata` is a level, so none of them counts. A master's watchdog asks, on each clock its port waits, whether any monitor counted a handshake since it last asked. A handshake counted in the same time step is left to the next ask, whichever process ran first, so the stall fires on the same clock on every simulator. The count starts on the second clock the port waits after the last handshake, so a port that waits from the clock after it raises the stall `joint_stall_cycles` + 1 clocks after that handshake. A master that asks only in part of its protocol starts later: the apb master asks only in its access phase, so it raises the stall one clock later.

`joint_stall_cycles` must exceed the longest the whole environment may legitimately go with no handshake anywhere while a lane waits. Some such waits:

- a test that holds every output sink's ready low on purpose;
- the DUT's own latency when no port moves during it, such as a timer, a long internal computation or a low-power phase;
- a wait that only status or raw ports move through, since they count nothing;
- a responder delay that a sequence sets, such as an ack delay, since the monitors count a transfer only when it completes.

The bound is counted in the waiting port's clocks. When the only port that moves runs on a slower clock, the gap between its transfers, in the waiting port's clocks, must stay below the bound.

The rule detects that the whole simulation is quiet, not that one port is stuck, so it is not a liveness check:

- Any activity hides a stall elsewhere. A free-running output stream, or a DUT that polls a testbench memory or register for a value the test never sets, keeps the rule from firing while another port waits for ever.
- The record spans the whole simulation. In a top env with several block envs, one block's traffic hides another block's stall until the traffic ends.

The generated base test's run timeout (section 9.6) ends such a partial stall, with the waiting ports named. A test that does not extend the base test ends it only at UVM's global timeout; bound it with `+UVM_TIMEOUT` or `uvm_top.set_timeout()`, as the AXI subsection below describes. With the rule off, a run that stops, behind a shared slave or a deadlock in both the DUT and the model, ends the same way.

#### The joint stall rule in Mode A

With one DUT (`UVM_DUT=rtl` or `model`) a master has one lane, so the skew and lone lane rules have nothing to compare, and the joint stall rule is the one that applies. It keeps the knob, the default, the count and the message of Mode B. It catches a DUT that stops taking input while the test still has items to send, which otherwise only the run timeout reports.

The rule counts only while a master holds an item, which means its lane waits for the DUT:

- A single-transfer master (push_ack, notify_ack, req_ack, pop_ack, rdy_vld, axi4_stream, apb and Pro's `lmmi`) holds an item from the drive point that raises its request until the item completes.
- An AXI master holds one while an AR, an AW or a W beat is on the bus, or a burst is outstanding.
- An item the sequence has started that the driver has not put on the pins yet is not held, whether it waits at the sequencer or in the driver's `gap` clocks. The DUT owes nothing for it, and those clocks are the test's own pacing.
- A responder, an `A2C_DST` driver, never holds one. A DUT that stops producing output is the output deadline's (section 9.6), and on a stream the real-time gap rule's. The memory and external_reg masters wait for no handshake and hold nothing either.

A handshake on any port restarts the count, so the stall fires `joint_stall_cycles` + 1 clocks after the last handshake anywhere, as in Mode B. The `A2C_JOINT_STALL` names each port that waited, as `in (uvm_test_top.env.in_agent.drv), waiting for the transfer of 'h5`. Its last sentence reads "With one DUT no lane dies, and the run ends here." in place of the Mode B one about declaring lanes dead.

The stall then ends the run through the test's run timeout (section 9.6), the way the timeout ends it at its budget: the run phase and every running task phase end at once, each task phase that begins later ends as it begins, `extract_phase`, `check_phase` and `report_phase` run once, and no `A2C_RUN_TIMEOUT` follows. The end-of-test reports of what is missing name the joint stall rule as the end, as section 9.6 describes. A test that does not extend the generated base test has no run timeout, so its masters go on waiting, no port counts toward a second stall, and the message ends "With one DUT no lane dies, and with no run timeout to end the run the masters go on waiting." A budget of 0 turns off the run timeout's time limit, not the component, so the run still ends at the stall; a reported stall should not become a hang that only the UVM phase timeout ends, since that skips `check_phase`. If a fixed budget runs out in the same time step as the stall fires, the simulator's process order decides which ends the run, and the log may carry both `A2C_RUN_TIMEOUT` and `A2C_JOINT_STALL`; a derived budget defers past the stall, so this needs a fixed one. A derived budget defers to a joint stall that is counting when the budget is reached, and leaves it out when its port clock has stopped, as for the Mode B rules (section 9.6).

#### AXI in Mode B

Each AXI agent drives both lanes and compares them through `model_cmp`, an `a2c_in_order_comparator` keyed by ID, so pairs are matched in order within an ID and the order across IDs is free.

| Role | Both lanes get | Compared | Not compared |
| :--- | :--- | :--- | :--- |
| master on a DUT `dst` port (`A2C_SRC`) | each AR, or AW and W, at one drive point, with each lane's own handshake and `max_outstanding` per lane. The sequence's response comes from the DUT lane, or from the model lane once the DUT lane is dead | R data and `rresp`, or `bresp`, per burst in order per ID | valid and ready timing, the order across IDs |
| slave on a DUT `src` port (`A2C_DST`) | one memory, `cfg.mem`. The DUT lane applies each burst, draws the delays and, with `reorder`, picks the next burst; the model lane answers the same burst by ID and arrival index once its own AR or AW is in, and waits otherwise | the AR bursts, or the AW bursts with their W data | none |

The model lane never chooses a burst, so both lanes answer in the DUT lane's order. At `check_phase` the slave reports two things as `A2C_REPLAY`:

- a pick the model lane holds whose AR it has not issued, or whose burst it has not ended. The error names the pick by ID and arrival index within the ID, and the model lane's own requests waiting behind it. A cut does not hide a held pick the cut keeps, and the replay log's error for the unreached cut then names the held pick as the cause instead of advising `drain_catchup_cycles`;
- bursts the model lane issued that the DUT lane never did, naming the first.

The slave's log joins the drain. A drain cut holds back the comparator's pairs after the cut, and the monitors report bursts left open after a cut as `UVM_INFO`.

**A model that keeps fewer requests outstanding than the DUT.** The model lane serves the DUT lane's picks in the DUT lane's order and never chooses, so the model must queue and arbitrate as the RTL does. A model that keeps fewer bursts outstanding than the DUT has a defect, and Mode B reports it. If the model's master sends the next AR or AW only after an earlier burst's response, the request for a pick the DUT lane reordered never comes, because the response the master waits for is behind the pick. The model lane stops, together with any agent that drives both lanes in step. The drain gives up or the catch-up runs out, and the slave reports the held pick and the requests behind it in an `A2C_REPLAY` error. Fix the model: issue each request ahead of its response, from a thread other than the one that takes the responses, and put a `synchLock` where those threads contend for shared state or a shared port. Setting `reorder` to 0 on the port is only a stopgap. The error goes away, and the port then checks none of the DUT's reordering.

Each AR or AW goes to both lanes at one drive point and the next waits for both handshakes. A lane that stops taking addresses or W beats would stop both lanes at once, and one that stops answering would stop both once it held `max_outstanding` bursts. The master bounds the lanes instead, with the rules of the previous subsection. On each burst it counts the clocks one lane trails the other at the AR or AW handshake, at each W beat, and at completion, the last R beat or the B. When a lane trails by `lane_skew_cycles` clocks at any of these, the master raises `A2C_SKEW` and declares the lane dead for the rest of the run. Later skews on a dead lane raise nothing. When another port's master declared a lane dead earlier, the `A2C_SKEW` names it in the clause described under the drain below, right after "declares the <lane> lane dead", because a death on one port can stall the DUT or the model and so make a lane on another port fall behind.

- **The dead lane freezes.** The master never drives a new AR, AW or W beat on it. A valid it had raised stays high with the same payload until that handshake completes, as AXI requires, and then drops for good. `rready` and `bready` go low at the next drive point and stay low, so the master consumes none of the lane's responses again. AXI lets a master drop READY at any time, and low is the one level that takes nothing, whatever the lane does next. A beat or B the lane offers in the clock of the death may still transfer on that edge, and the master records it whichever process saw the death first.
- **The sequence gets every burst from the live lane.** Every open burst and every later one completes on the live lane, and the sequence gets that lane's response, its own data and `rresp` or `bresp`. A burst the dead lane had already completed still returns the live lane's response, once the live lane completes it. Each ID's bursts return in order: before a burst the live lane completes after the death returns, the master returns every older one the dead lane still owed.
- **The comparator stops.** The master calls `model_cmp.lane_dead()`. `model_cmp` compares the pairs completed up to and including the time step of the death, whatever the order of the monitor and the master in that step, and none after it. So the death causes no `A2C_MODEL_CMP` mismatch, and the pair count does not depend on the simulator. At `check_phase` it reports the death in one `UVM_MEDIUM` line: the pairs compared, the dead lane and the time, and per lane the items it delivered that were never compared. Only a comparator that reports through `check_pair()` and counts each lane's items in `seen[]` gets this from `a2c_comparator_base`, as `a2c_in_order_comparator` does, keyed or not. `lane_dead()` is virtual, so a subclass can override it, and `is_dead(lane)` and `died_at(lane)` let any checker that holds the comparator ask about a lane.
- **The drain carries on.** A master's port has no replay log, so the logs a death can starve belong to other ports, the slave ports the dead lane's model feeds. The master tells the drain, which keeps the death only to name it. Every log still settles, is cut, catches up or is given up as it would without the death, within its own deadline and catch-up. Only the comparator of the port whose lane died stops.
- **Later reports name the death.** A report of an event that came after a lane began to trail ends with `; the <lane> lane of <port> (<master path>) began to trail at <time> and was declared dead at <time> (<id>), which may be related`, where `<id>` is `A2C_SKEW` or `A2C_JOINT_STALL`, one entry per such death on any port, since a model starved by the dead lane may be the cause. A lane begins to trail when the other lane takes the AR, AW or W beat it then misses, or completes the burst or item it then fails to complete; a lane left alone, or both lanes in a joint stall, begin when they last made progress. The master declares the death `lane_skew_cycles`, `lone_lane_cycles` or `joint_stall_cycles` clocks later, so a report can name a death declared after the event. An `A2C_DRAIN` warning, raised during the run, names only the deaths declared before it. A death declared by `a2c_replay_drain::lane_dead()` with no start time began to trail when it was declared, and its entry reads `was declared dead at <time>`. A lane that began to trail after the event is left out, since it cannot have caused it. So is one that began in the event's own time step, and one declared in the time step the clause is made, which keeps the text independent of process order. These reports carry the clause, each dated by the event it reports:
  - every `A2C_DRAIN` warning, dated when it is raised;
  - an `A2C_CUT` warning and the `A2C_CUT` info of a cut under `drain_cut_expected`, dated by the cut. The `A2C_CUT` info of a cut that dropped nothing carries no clause;
  - the replay log's `A2C_REPLAY` error for a cut the lanes did not complete, dated when the drain gave up waiting for them: at the end of `drain_catchup_cycles`, or when it found the log's clock stopped. A death during the catch-up can be what kept the lanes from the cut;
  - the replay log's `A2C_REPLAY` errors for records the model lane never replayed, dated by the first of them, and for a model lane left waiting, dated by when it started to wait;
  - an AXI slave's `A2C_REPLAY` errors for a held pick, dated by the pick, and for bursts only the model lane issued, dated by the first of them;
  - the memory agent's `A2C_REPLAY` error for model lane accesses made without credit, dated by the first of them, whose time its text gives as it is reported at `check_phase`;
  - a master's `A2C_SKEW`, dated by its own death, naming deaths on other ports only, and the `A2C_JOINT_STALL`, dated by the deaths it declares and naming every death before it.

  Other reports, such as `A2C_MODEL_CMP` mismatches and `A2C_PROTO` errors, carry no clause.
- **The dead lane's monitor reports its open bursts as info.** The master tells the dead lane's monitor too. At the end of the test the monitor reports the bursts the lane left open in one `UVM_LOW` `A2C_PROTO` info line that names the death. A protocol error it saw before the death stays an error.
- **The live lane must keep moving.** Once one lane is dead, the master watches the other. If it has an AR, AW or W beat on the bus, or a burst open, and takes no address or W beat and completes no beat or B for `lone_lane_cycles` clocks, the master declares it dead too. That `A2C_SKEW` names `lone_lane_cycles` and calls the death a likely consequence of the first. Without this rule a live lane that stops after the other died would hang the run, for example a model lane waiting on a slave port's replay that the dead DUT lane never records.
- **Both lanes dead.** The master's second `A2C_SKEW` says no lane is left, as does the `A2C_JOINT_STALL` for every port. It returns every open burst to the sequence at once, and every later one once its `gap` has passed, with no beats, so the sequence's waits end instead of hanging.

So the run ends when one lane goes on and the other stops, and when the whole environment stops, as behind a shared slave or a deadlock in both the DUT and the model, after `joint_stall_cycles`. With `joint_stall_cycles` at 0, nothing declares a death when everything stops. The generated base test's run timeout (section 9.6) then ends the run. A test that does not extend the base test ends only at UVM's default timeout of 9200 s of simulated time. Bound it with `+UVM_TIMEOUT=<n>` on the command line, where `<n>` is an integer in the time unit `uvm_pkg` was compiled with, ns under the flow's `-timescale 1ns/1ps`, or with `uvm_top.set_timeout()` in the test's `build_phase`. A `set_timeout()` call in the test overrides the plusarg unless the plusarg ends in `,NO`, as in `+UVM_TIMEOUT=50000000,NO`.

The bound must exceed the worst skew a correct model and DUT reach. Each lane has its own slave latency and ready pattern, so a lane may trail by about `max_outstanding` times the longest burst in beats divided by the ready rate, plus any difference between the model's and the DUT's response latency. A smaller bound declares a slow but correct lane dead and ends the comparison there. `lone_lane_cycles` is a separate bound, since a skew bound limits the difference between the lanes and says nothing about how long one lane may stall. It must exceed the longest stall of one lane on its own: the slave's longest response latency, or the longest the DUT holds `arready`, `awready` or `wready` low. A smaller one declares the healthy lane dead after the first death, and every later burst returns with no beats. The master reads `a2c_lane_skew_cycles`, `a2c_lone_lane_cycles` and `a2c_joint_stall_cycles` from the `uvm_config_db` at the start of its run phase, and 0 turns any rule off. The generated base test sets them from `lane_skew_cycles`, `lone_lane_cycles` and `joint_stall_cycles` when those are 0 or more. Otherwise the master keeps its own defaults of 200000, as it does under a hand-written env that sets nothing.

#### Checking outputs without the model

Mode B compares the RTL with the model, so it catches a disagreement and misses an error both make. A bench therefore checks each output stream against the specification too, from the stimulus and never from the model: a scoreboard that computes the expected value, a contract of `a2c_video_pkg` for a video stream (section 9.6), or a check of its own. The check runs in every mode, and in Mode B on both lanes, so a model error shows as an independent failure on the model lane and not only as a mismatch. Base does not warn about an output with no such check: whether a check is complete is the bench's call.

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
| `a2c_video_test #(BASE)` extends its parameter | the generated base test owns the run phase and the run timeout's work count, which a video test changes; a component the bench adds could not change them |
| corner tests defined by `` `a2c_video_corner_tests ``, not a sequence library | each corner is a test name a regression lists, as `+UVM_TESTNAME` selects it |
| knobs on `a2c_video_cfg`, not on the sequence, and passed to the env directly, not through `uvm_config_db` | the sequence, the contract and the checkers read one geometry, and `configure_video()`, the corner and the plusargs apply to it in one order |
| blanking as idle items on `raw`, as `gap` on handshaked items | a raw driver sends an item every clock and has no idle state, and handshaked items already carry `gap` |
| `a2c_video_checker`, not a scoreboard | it checks framing against the specification and holds no reference model |
| `a2c_video_adapter` setters and getters, not `uvm_reg_adapter`-style `bus2reg`/`reg2bus` | a beat carries both a level or a marker and up to `pixels_per_beat` pixels, set one field at a time |

### 9.11 The SystemC side under UVM

With the model DUT, and in Mode B, the generated wrapper drives the pins through the SystemC BFMs in the DUT's swapped roles. Every BFM follows the pin-timing rule of 9.10.

- `memory_dst_bfm` drives an access after a rising edge, samples `read_data` at the falling edge, and resumes the model at the next rising edge. A model read therefore takes two edges, and a model's back-to-back reads run at one per two clocks. A Verilated memory returns the same word as a UVM agent. In Mode B the wrapper gives it the port's credit and held pins, and it holds access n, the model blocked in `request()`, until the credit exceeds n (section 9.12). An access still held at the end of the simulation is logged at `LOG_IMPORTANT` with the credit it saw, which names a missed wake-up when the credit had released it. With a write order it holds an access until the earlier accesses on the other ports allow it, and logs an access still waiting at the end with the earlier access it waits for (section 9.12).
- `memory_src_bfm`'s `request()` must not consume simulated time. An enabled edge that passes while it waits is never served. The BFM counts each one as a `bfmContractCheck` break, which fails a UVM run.
- `axi_write_src_bfm` holds `wready` low while its channel would wait for an address: a transactional receiver, a new burst and no address queued. A master that sends W before AW then holds the beat instead of losing it.
- `lmmi_dst_bfm` drops `lmmi_request` before `complete()`, which waits out the channel's timed delay, so a slave does not see a second read.
- `req_ack_dst_bfm` and `pop_ack_dst_bfm` drop the request for a clock between requests. The UVM src drivers may send requests back to back, and the src BFMs accept that.

Tests and end-of-test voters live outside the DUT. The UVM testbench config never calls `set_test_names`, so a model that calls `register_test_name` or `ADD_TEST` exits with `the test list is empty`.

#### The SystemC watchdog

`sc_main` runs `watchDogHandler()` in every flow. Once every registered enabler has voted it on, its stall check fails the run with a `Q_ASSERT` if no model tickles it for one second of wall clock. Under UVM the test drives the DUT, so a model can idle while UVM waits, and the `Q_ASSERT` would end the run before the report phase. The UVM config's `createTestBench()` therefore sets `watchDog::stallCheckDisabledByUvm`, and the handler logs at startup, at every verbosity, that the check is off. The no-terminator check stays on.

The UVM checks that bound a stall instead depend on the DUT:

- Mode B: the lane skew, lone lane and joint stall rules (section 9.10), then the output deadline, the drain and the run timeout (section 9.6).
- Mode A, `rtl` or `model`: the joint stall rule (section 9.10), the output deadline, once `run_body()` returns, and the run timeout (section 9.6). A DUT that stops taking input blocks `run_body()`. The joint stall rule reports it once no port moves and ends the run there.
- A test that does not extend `<block>_base_test` has neither the output deadline nor the run timeout.

A model whose tickles stand for internal progress that no port shows loses that check under UVM. Report the stall from the model with `errorCode::fail`, or expose the progress on a port the test checks.

#### Builder layers

A builder layer ships its agents through `A2C_LAYER_UVM_F_FILES`, a list of `-F` files of agent packages, each path relative to its list. Under `USE_UVM` the flow compiles them after `a2c_uvm.f`, which lists `a2c_clk_if.sv`, `a2c_credit_if.sv` and `a2c_uvm_pkg.sv` first, so a layer package can import `a2c_uvm_pkg`. Make reads each list with `$(file <)`, which needs GNU Make 4.2, and makes the lists and every file they name prerequisites of the snapshot. Pro adds `pro/common/systemVerilog/uvm/a2cPro_uvm.f` in `a2cPro.mk`, and its checkers through the `-y` line of `a2cPro.f` and `A2C_LAYER_VCS_LIB_SV_FILES`.

### 9.12 Mode B: the model against the RTL

`UVM_DUT=both` builds one snapshot that holds the RTL and the model. The RTL, instance `dut`, is the DUT under test. The model runs beside it on the same stimulus and is the reference its outputs are compared with, port by port, in order. The tests, sequences and register model are the Mode A ones. The only selection a test sees is the env's `dual_dut`.

Each port has two pin sets, called lanes. The DUT lane is the port's interface, `cfg.vif`, wired to the RTL. The model lane is `<port>_model`, `cfg.model_vif`, wired through the testbench module's pins and the SystemC BFMs to the model. One agent per port drives and monitors both lanes, so `<port>_agent.sqr`, `<port>_agent.mon.ap` and `<port>_counter` keep their Mode A names. `mon` watches the DUT lane. With `model_vif` set the agent also builds `model_mon` on the model lane and, where the type compares something in that role, `model_cmp`, which takes `mon`'s items on `dut_export` and `model_mon`'s on `model_export`. With `model_vif` null the agent builds neither and draws no extra random numbers, so Mode A and rtl runs keep their stimulus. The register predictor stays on the DUT lane's bus monitor, so register reads and the mirror test the RTL.

Mode B passes no transaction through DPI. Both DUTs see the same values on the same cycles, and each lane completes on its own handshake, so the model does not see the RTL's exact input timing. That suits a block whose outputs depend on the order of its inputs and its registers. A block whose outputs depend on when its inputs arrive needs a transport that replays the RTL's input timing to the model, which is not built.

#### Lane rules

- **A master**, an `A2C_SRC` driver that starts transfers, puts the same values on both lanes at one drive point. Each lane completes on its own handshake, sampled at the falling edge, and drops its request at the next drive point. The next item starts when both lanes are done. A response the sequence gets back, such as `rdata`, `prdata` and `pslverr`, or an AXI burst's beats, comes from the DUT lane. Random values are drawn once per item or per clock, never per lane. The memory and external_reg masters put each access on both lanes on the same clock and wait for neither.
- **A ready level** the agent draws, such as `rdy` and `tready`, an AXI master's `rready` and `bready`, or an AXI slave's `arready`, `awready` and `wready`, is drawn once per clock and driven on both lanes.
- **A responder**, an `A2C_DST` driver that answers, serves both lanes from one model: one `cfg.mem` or one responder sequence. The DUT lane applies transaction n and records its response and the delay it drew in the driver's `a2c_replay_log`. The model lane replays the record in order, and when it reaches transaction n first it waits, by holding its ready or ack low, or on `memory` through its BFM's credit. The model lane never applies a transaction and never makes a decision. A choice such as which AXI burst a slave answers next is made by the DUT lane and replayed by the model lane, the way `synchLock::arb()` shares a decision in tandem, where the RTL is always the sender (`systemc-synchronization` skill, section 2).
- **A master's lanes are bounded** by the lane skew, lone lane and joint stall rules of section 9.10. **A responder's model lane** is held at the end of the run phase by the drain of section 9.6 until it catches up. The run timeout of section 9.6 ends a run that none of these rules ends.

**The model must queue and arbitrate as the RTL does.** The model lane follows the DUT lane's responses and choices in the DUT lane's order. A model that keeps fewer requests outstanding than the RTL, or arbitrates differently, stalls or differs on the model lane, and Mode B reports it as `A2C_REPLAY`, `A2C_SKEW` or `A2C_MODEL_CMP`. That is a defect of the model, not a limit of the flow. The AXI slaves' `A2C_REPLAY` error for a held pick says so and says how to fix the model (section 9.10, "AXI in Mode B").

**memory responders.** memory has no handshake to hold, so the model lane waits before its pins. The `A2C_DST` driver drives `cfg.credit_vif.credit`, the testbench module's `<port>_model_credit`, with the number of accesses the DUT lane has made, and the model's `memory_dst_bfm` holds its access n until the credit exceeds n, with `<port>_model_held` high while it waits. The credit changes at the drive point, so the model's access n reaches the pins at least one clock after the DUT lane's and finds its record: a read takes the DUT lane's word, and a write changes nothing. A read through one port that the RTL makes after another port's write therefore gets the written word on both lanes, as a tandem memory tee holds the model for the RTL. Every memory port the DUT drives is held this way. A model lane access made without credit, from a BFM that ignores the pins, is answered from `cfg.mem` and reported as one `A2C_REPLAY` error at `check_phase`. At `report_phase` the driver reports, as `A2C_CREDIT` at `UVM_MEDIUM`, the accesses the BFM held, counted by the rises of held, the sample edges at which held was high, and the accesses made without credit; `held_access_count()`, `held_clock_count()` and `uncredited_count()` return them for a test's own check.

- **Write order across ports, Mode A.** A model's write is posted, so its later access through another memory port can reach the pins on the write's edge or before it, and a memory that serves both at one edge reads first. When the run holds the model alone, the UVM SystemC wrapper gives the `memory_dst_bfm`s of the DUT's memory ports, two or more of a type with `bfmWriteOrder: true`, one `memory_write_order`. Each memory channel stamps an access in the model's program order as `request()` starts, in the caller's thread. A producer-shape `memory_port_thunker` passes the stamp up through `observeRelayed()` as the child's `request()` starts, so a thunked port is stamped in the child's thread, not the thunker's, and the relay is not stamped again; the consumer shapes relay toward a completer and pass nothing, and Pro's `memory_port_tee` sits only in the generated `<block>Tandem` wrappers, which a UVM SystemC wrapper never holds, and merges two requesters that have no single program order. The BFM holds an access until the earlier accesses on the other ports allow it: a read is sampled after every earlier write, and a write is sampled after every earlier write and no earlier than every earlier read. On one clock the write may go once the read is on the pins, so it lands on the read's edge or later; on another clock it waits until the read has been sampled. A read whose BFM has not yet driven it, as while its port is in reset, holds the write either way. An access released by the edge of another clock waits for its own clock's next rising edge before it drives the pins, so they change only between its own rising edge and the next falling edge, where the agent samples. Reads never hold reads. An access waits only for accesses issued before it, but the wait is not limited to one clock: an access issued behind a stream of posted writes on another port waits for each of them to be sampled, so every such access costs at least one clock, and a write behind a read on a slower clock waits for that clock's edge. Two model threads that issue accesses in one evaluation phase race: the stamps follow the order the kernel runs them, so the outcome can differ between the Accellera kernel in the model's SystemC testbench and the Xcelium or VCS kernel in a UVM run. An access still waiting at the end of the simulation is logged with the earlier access it waits for. In Mode B the model lane takes the RTL's words from the replay log, so the wrapper leaves the order off, and a BFM given both a credit and an order asserts at the end of elaboration.
- **Coverage boundary.** The model lane reads the RTL's words, so Mode B does not check that the model's own order of accesses across ports would read the same words from a memory of its own. Tandem has the same boundary. A Mode A run on the model DUT with a scoreboard covers it.
- **Input coupling.** A held access blocks the model thread that makes it. When that thread also takes input on a port, and the RTL makes the access only after taking more input than the model lane has taken, the model lane stops taking input. Its master then reports `A2C_SKEW`, or the env `A2C_JOINT_STALL`, and both name the memory port as a responder whose model lane waits. The stop comes from the master's lockstep, which gives the model lane one item of slack on its port, not from a functional difference: a model that buffers less input than the RTL ahead of an access can be correct and still stop here. Until masters give the model lane more slack (section 10; such a change must revisit `a2c_video_lane_watch`, which relies on the driver taking the next item only after both lanes transferred the last, section 9.6), the model must take no more input before an access than the RTL does, for example by taking input in a thread of its own or through a FIFO as deep as the RTL's. A memory access inside a register callback couples the register bus the same way; the generated register handler runs in its own thread.

#### What each type compares

Each agent package header lists, for each role, what the DUT produces that is not compared. The table gathers them. A role with nothing compared has no `model_cmp`.

| Type | Role | Compared, in order | Not compared |
| :--- | :--- | :--- | :--- |
| `rdy_vld`, `axi4_stream` | `A2C_SRC` | nothing | `rdy` or `tready` timing |
| `rdy_vld`, `axi4_stream` | `A2C_DST` | each beat, the fields `do_compare` covers | `vld` or `tvalid` timing |
| `raw` | either | nothing | `A2C_DST`: the word stream, which has no transfer boundary, and whose model lane is best effort (section 9.1) |
| `status` | `A2C_SRC` | nothing: the agent drives the level, and the DUT produces nothing on the port | none |
| `status` | `A2C_DST` | the value under the port's status policy | intermediate values under `stable` |
| `apb` | master | `write`, `addr`, `data` (`prdata` on a read) and `slverr`; `prdata` is left out on a read of an address on the skip list | wait states |
| `apb` | slave | `write`, `addr` and `data` (the DUT's `pwdata` on a write) of each transfer the DUT makes. The item's `slverr`, and its `prdata` on a read, are compared too, but they are the slave's own response, which the model lane replays from the DUT lane, so they match by construction | none |
| `push_ack` | `A2C_DST` | the pushed data | `A2C_SRC`: `ack` timing |
| `notify_ack` | `A2C_DST` | the count of events, by pairing them | `A2C_SRC`: `ack` timing |
| `req_ack` | either | `A2C_SRC`: `rdata`; `A2C_DST`: the request data | `A2C_SRC`: `ack` delay |
| `pop_ack` | either | `A2C_SRC`: `rdata`; `A2C_DST`: the count of pops | `A2C_SRC`: `ack` delay |
| `memory` | either | each access, read data included on `A2C_SRC`, through `memory_comparator`, which holds a pair whose read word has X or Z; `A2C_DST`: the access stream | none |
| `external_reg` | `A2C_SRC` | `rdata` under the port's status policy, through `external_reg_comparator`, because the model's `rdata` trails a write by a clock more than the RTL's | intermediate `rdata` |
| `external_reg` | `A2C_DST` | the writes | none |
| `axi_read` | master | each burst's AR fields, beats, `rresp` and `ruser`, in order per ID | valid and ready timing, the order across IDs |
| `axi_read` | slave | the AR bursts, in order per ID | none |
| `axi_write` | master | each burst's AW fields, W beats, `bresp` and `buser`, in order per ID | channel timing, the order across IDs |
| `axi_write` | slave | the AW bursts with their W data and strobes, in order per ID | none |
| `lmmi` (Pro) | either | direction, offset and the word written or read; the word is left out on a read of an offset on the skip list | `A2C_SRC`: ready and `rdata_valid` timing |

#### Comparators

The comparator classes are in `common/systemVerilog/uvm/a2c_uvm_pkg.sv`:

- `a2c_comparator_base` holds what every comparator shares: `midstream_beats` (64), `max_reported` (10), `auto_stable` (1), `counted` (0), `stable_point()`, `inject_mismatch()`, `get_pairs()`, `cut()`, `uncut()` and `lane_dead()`. The env's `comparators` list holds every agent's `model_cmp` as this type.
- `a2c_in_order_comparator #(T)` pairs the DUT lane's item n with the model lane's item n, in arrival order on each lane, and compares them with `T::compare()`. A mismatch is an `A2C_MODEL_CMP` `UVM_ERROR` naming the comparator and the pair, with both items printed. After `max_reported` mismatches the rest are counted, and `check_phase` reports how many went unprinted. At `check_phase` items either lane left unpaired are `A2C_MODEL_CMP` errors, unless `counted` is set, which the env sets on a counted port because its counter already reports the shortfall or excess, or a lane is dead, because the `A2C_SKEW` or `A2C_JOINT_STALL` error that declared it dead has already failed the run and the comparison stopped at the death. A subclass that overrides `key()` pairs in order per key: the AXI comparators key by ID. `uvm_in_order_class_comparator` is not used, because it has no leftover check and none of these hooks.
- `a2c_status_comparator #(T)` applies the status policy. `status_comparator` and `external_reg_comparator` extend it.
- `a2c_reg_comparator #(T)` extends `a2c_in_order_comparator` for an agent that can carry register reads. It adds the skip list and asks the guard about each read. A subclass defines `is_read()`, which returns whether an item is a read and its address, and `same_but_data()`, which compares two items in everything but the read data. `apb_comparator` and Pro's `lmmi_comparator` are the `model_cmp` of their agents.

**Status policy.** The model updates a status level sooner than the RTL, so a status value is not compared beat for beat. Each comparator of this kind has `policy`:

| `policy` | Check |
| :--- | :--- |
| `A2C_STATUS_STABLE`, the default | at each stable point, the latest DUT value against the latest model value, as one pair. A lane that has reported no value yet is an `A2C_MODEL_CMP` error |
| `A2C_STATUS_BOUNDS`, with `lo` and `hi` | every value either lane reports lies within `lo`..`hi`, or it is an `A2C_MODEL_CMP` error naming the lane. A value with X or Z is an `A2C_XZ` error |
| `A2C_STATUS_OFF` | each value is logged with id `A2C_STATUS` at `UVM_MEDIUM`, unchecked |

The default stable point is each return of `wait_for_outputs()`, where every counter has its count on both lanes and the quiet window has passed: the base test then calls the env's `model_stable_point()`, which calls `stable_point()` on each comparator with `auto_stable` set. A port whose status settles later clears `auto_stable` on its `model_cmp` and calls `stable_point()` from its own event. Set the policy and the stable point in the `<block>_tb_env` subclass, after the agents are built, for example `<port>_agent.model_cmp.policy = a2c_uvm_pkg::A2C_STATUS_BOUNDS;` in its `connect_phase`.

#### The quiescent-configuration rule

The RTL pipelines a beat and the model does not, so a register write while data is in flight can take effect on a different beat in each. Mode B tests therefore change configuration only while the datapath is quiescent: program the registers, stream, wait for the outputs with `wait_for_outputs()`, and only then program again. `a2c_midstream_guard` enforces the rule. The env builds it in Mode B when the block has a register model, and feeds it from `a2c_reg_write_subscriber` on the DUT lane's bus monitor. The subscriber passes on every write the monitor sees, a memory write, an unmapped write and each bus word of a multi-word register included, because the predictor reports only writes that complete a whole register.

- A write while any output counter has transactions pending on either lane, a reported shortfall included, is an `A2C_MIDSTREAM` `UVM_ERROR` naming the register and the pending counts.
- The guard sees only traffic a test has declared with `expect_count()`. A test that streams before it declares its outputs escapes the guard.
- `+a2c_predict_midstream=1` turns the rule into a debugging aid. The write is then an `A2C_MIDSTREAM` `UVM_INFO` at `UVM_LOW`, and opens a midstream window on every comparator. A mismatch inside the window is an `A2C_MODEL_CMP_MIDSTREAM` `UVM_WARNING` instead of an error. On an in-order comparator the window covers the pairs above the slower lane's item count at the write, up to the faster lane's count plus `midstream_beats`, so it holds the beats already in flight on either lane plus the pipeline. Set `midstream_beats` in the env subclass to the block's pipeline depth in output beats. On a status comparator the window covers the next stable point only. No regression entry should set the plusarg.

Reads follow the same rule. Every read on the register bus is compared, and a read of a volatile register or a read-only memory counts as midstream, because the RTL and the model may update its value at different times. The register model marks a register volatile when its `regType` is `ro` or `ext`, and a memory with `regAccess: ro` is a `uvm_mem` with `RO` access, which only the design writes.

- The bus agent's `model_cmp`, an `a2c_reg_comparator`, passes each DUT-lane read to the guard as it arrives. The comparator asks the guard rather than the guard listening to the bus monitor. A monitor's analysis port calls its subscribers in the order of their names, which the env does not choose, and the guard's verdict must reach the comparator before the pair is compared.
- A read of a volatile register or a read-only memory while any output counter has transactions pending on either lane is an `A2C_MIDSTREAM` `UVM_ERROR`. It names the register or memory, the address and the pending counts. Read it after `wait_for_outputs()`, or put its address on the skip list.
- Under `+a2c_predict_midstream=1` the read is an `A2C_MIDSTREAM` `UVM_INFO`, and a mismatch of that read alone is an `A2C_MODEL_CMP_MIDSTREAM` warning.
- The read opens no window on the other comparators. That depends on nothing in the design seeing a read. The generated register handler's `external_reg_if` has no read strobe, and the SystemC external_reg channel gives the block no read event, so even an `ext` register cannot clear on read, and a data mismatch after a read is a real defect. A register interface that gains a read strobe, or a clear-on-read access policy, must make `judge_read()` open a window for that read.
- The guard says nothing about a read of a register that is not volatile, of a memory with RW access (`regAccess: rw` or `regType: memory`), or of an unmapped address. Such a read is compared like any other transfer. A design can also write an `rw` memory through a port of its own, and the guard does not judge that memory's reads. Read it only when quiescent, or skip it.
- A field's volatility comes from the register model. To exempt an `ext` register that is plain storage, call `set_volatility(0)` on each of its fields in the `<block>_tb_env` subclass.
- After the time step of a lane death the comparison has stopped, and the comparator no longer asks the guard, so no later `A2C_MIDSTREAM` follows the `A2C_SKEW` or `A2C_JOINT_STALL` error. A read in that time step is still judged, because `check_pair()` still compares a pair that completes in it.

**The skip list.** Some reads cannot be compared at any time, such as a free-running counter. List them on the register bus comparator in the `<block>_tb_env` subclass, in `connect_phase` under `if (dual_dut)`. `model_cmp` exists only in Mode B, so without the `if` the default Mode A run stops on a null `model_cmp`. Here the register-bus port is `regs`:

```systemverilog
if (dual_dut) begin
    regs_agent.model_cmp.skip_reg(regmodel.cycle_count);  // every bus word of the register
    regs_agent.model_cmp.skip_mem(regmodel.trace_buf);    // every bus word of the memory
    regs_agent.model_cmp.skip_address('h40);
end
```

- A read of a listed address is compared without its data. The direction, the address and the response (`slverr` on apb) are still compared, and the monitor still checks the protocol. The guard never sees the read. Writes to a listed address are compared in full.
- `skip_reg(rg, map)` lists every bus word of `rg` in `map`, or in the register's default map. `skip_mem(m, map)` does the same for every row of a memory. Each call adds one entry, an address range, so a large memory costs no more than a register. A register or memory that the map does not hold, or holds unmapped, is an `A2C_CFG` `UVM_FATAL` naming it and the map. `is_skipped(addr)` reads the list.
- At `check_phase` the comparator reports one `A2C_REG_SKIP` `UVM_INFO` at `UVM_LOW`, with one line per entry. Where entries overlap, a read counts only on the first entry that holds it. A line gives the register or memory name and its address range, or the address alone, and the number of reads it matched, 0 included.
- The list is on `a2c_reg_comparator`, so any agent whose `model_cmp` extends it has one. Pro's lmmi agent has one too. No generated env uses lmmi as a register bus, because lmmi has no register adapter, so the guard never judges its reads.

#### Messages

| Id | Severity | Meaning | What to change |
| :--- | :--- | :--- | :--- |
| `A2C_MODEL_CMP` | `UVM_ERROR`; `UVM_INFO` at `UVM_NONE` for the line that says later mismatches are counted, and at `UVM_MEDIUM` for a comparison a lane death stopped | the model's output differs from the RTL's on a pair, a lane left items unpaired, or a status check failed | the RTL and the model disagree: find which matches the specification and fix the other. The message prints both items and the pair index |
| `A2C_MODEL_CMP_MIDSTREAM` | `UVM_WARNING` | a mismatch inside a midstream window, or of a midstream read of a volatile register or read-only memory, under `+a2c_predict_midstream=1` | expected near a midstream write or read; remove the access or the plusarg to check those beats |
| `A2C_MIDSTREAM` | `UVM_ERROR`; `UVM_INFO` under `+a2c_predict_midstream=1` | a register write, or a read of a volatile register or read-only memory, while outputs had transactions pending | move the access to after `wait_for_outputs()`, or skip the read's address on the register bus comparator |
| `A2C_REG_SKIP` | `UVM_INFO` at `UVM_LOW` | at `check_phase`, the reads each entry of a register bus comparator's skip list matched, one line per entry | nothing |
| `A2C_STATUS` | `UVM_INFO` at `UVM_MEDIUM` | a status value logged under the `off` policy | nothing |
| `A2C_XZ` | `UVM_ERROR` | a status value with X or Z under the `bounds` policy | the lane named drives an unknown status |
| `A2C_MISMATCH_TEST` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` on a pass | `<block>_model_mismatch_test` did not see exactly one injected mismatch and nothing else (section 9.6) | read the other errors first; a comparator that compared fewer pairs than `mismatch_at` means the port received too little traffic |

`A2C_TXN_COUNT` names its lane in Mode B. `A2C_REPLAY`, `A2C_CUT`, `A2C_DRAIN`, `A2C_SKEW`, `A2C_JOINT_STALL` and `A2C_PASSIVE` are in section 9.6.

#### Names

The Mode B names follow the agent conventions of section 9.10. These depart from common UVM practice:

| Name | Reason |
| :--- | :--- |
| lanes, the DUT lane and the model lane | one agent drives two pin sets of one port; "lane" names a pin set without implying a second agent |
| the `model_` prefix: `model_vif`, `model_mon`, `model_cmp`, `<port>_model` | it names what the lane holds and matches `UVM_DUT=model`; `ref_` would hide which DUT it is |
| the comparator inside the agent, not a scoreboard in the env | each type knows what it can compare; a generated per-port scoreboard would need a new interface definition key |
| `a2c_in_order_comparator`, not `uvm_in_order_class_comparator` | it reports a mismatch as an error, reports leftovers, and has the cut, death, midstream and injection hooks |
| `a2c_replay_log`, record and replay | the responder's DUT lane records and its model lane replays, as `synchLock` tandem does |
| the skip list, an address list on `a2c_reg_comparator`, with `same_but_data()` comparing what a skipped read still checks | a DV engineer would first reach for the register model's field compare control, volatility or `set_compare(UVM_NO_CHECK)`. Owner ruling Q4 asks for an address list, and only an address list covers an unmapped address and lmmi, which has no register model |

## 10. Open items

- Under Xcelium every uninstantiated HDL wrapper top is elaborated as an idle top-level. That is harmless at the tested size, but its memory cost on a large SoC is unmeasured.
- SystemC 3.0.1 is untested in both flows (VCS `-sysc=301` with a GCC 13 build, Xcelium `-sc_301`). The default `VCS_ELAB_OPTS` selects 2.3.4.
- The comment and `$(error)` text at `a2c-xrun.mk:8-13` say `XRUN_GCC_VERS` must match the compiler's libstdc++. For 26.03 that is inaccurate (section 2.2).
- Whether a later Xcelium bundling GCC 13 should be linked with it is untested.
- The Xcelium documentation reviewed during testing states that a snapshot records `LD_LIBRARY_PATH` and rejects a different value at simulation time. The builder does not record it. Keep `LD_LIBRARY_PATH` the same for the build and every run.
- An exported `XRUN_OPTS` or `VCS_LIB_SV_FILES`, or under `VCS_DEBUG` an exported `VLOGAN_OPTS` or `VCS_ELAB_OPTS`, is appended to again in each sub-make, so the builder's additions appear twice (section 3).
- The builder default `DUT_TOPOLOGIES` includes `verif:tandem`, which needs a builder layer that registers tandem blocks (section 1.3).
- Tandem: Pro's 1-in-2-out external_reg tee (`builder/pro/common/systemc/external_reg_port_tee.h`, `port_tee`) forwards a CPU write with `write()`, not `reg_write_cmd()`. A tandem dst model that waits in `read()` for CPU writes never sees one.
- UVM: a second `make USE_UVM=1 USE_VCS=1 uvm_snapshots` is not a no-op. The model, rtl and both snapshots share one `AN.DB` and one analysis-options stamp, and the rtl build adds `+define+A2C_UVM_RTL_DUT` and the both build `+define+A2C_UVM_BOTH_DUT`, so each build re-analyses after the one before. A no-op needs a per-DUT analysis library or a DUT selection without a define. Xcelium is not affected.
- UVM Mode B: a block whose outputs depend on when its inputs arrive, not only on their order, cannot be compared, because the transport that would replay the RTL's input timing to the model is not built (section 9.12).
- UVM Mode B: a master gives the model lane one item of slack on its port, so a model that takes less input than the RTL before a memory access the BFM holds for credit stops both lanes, although the model may be correct (section 9.12, input coupling). More slack per master, bounded by the lane skew rule, would remove it. `a2c_video_lane_watch` relies on a driver that takes the next item only after every live lane transferred the last, so that change must revisit it (section 9.6, video framing tests).
- UVM Mode B: the status policies run only in the loopback. No base UVM example has a status output or an external_reg port.
- UVM: the VCS steps for a second `hasUvm` block are checked by unit tests only. Each base UVM example has one `hasUvm` block with one top.
- UVM: a clock that slows by more than `clock_stop_cycles` periods in one step reads as stopped once, to a waiting counter and to the Mode B drain. Nothing tells a stop from a large step in frequency until the next edge. A counter reports its shortfall then. In the drain, a log idle at that point settles and is watched again from the next edge, but a log that is not idle, or is cut, is given up and never watched again. The run can then end with an `A2C_DRAIN` warning and an `A2C_REPLAY` error for what the model lane still owes, even if it would have caught up on the slower clock.
- UVM: the random-ready form of back-pressure is untested in a block bench. uvmVideo's output is `backpressure: false`, and uvmMem's output agent keeps the default `ready_pct` of 100, so both hold ready high.
- UVM: no base simulation has exercised the generated register model's memory, ext or multi-word paths, or a non-default variant. Unit tests generate them, and `reg_read_pins_stride_test` runs `a2c_reg_map` memories over the apb agent.
- UVM: an rtl-only (`hasMdl: false`) `hasVl` block's `<block>_hdl_sc_wrapper.h` imports `<ctx>_<block>.base`, which such a block never gets, so its C++ fails to compile in a `VL_DUT`, VCS or Xcelium build. The unit tests generate the files but never compile them.
- UVM: the flow compiles UVM 1.2 on both vendors. The IEEE 1800.2 libraries both installs ship have never been compiled against. A move needs `set_finish_on_completion()` in the testbench module and a check of `a2c_reg_map`'s memory stride (section 9.5).
- UVM: the JUnit report of `regrLauncher.py` records only the first failure (`regrLauncher/report.py`), so the order of the rule files decides which failure it shows.
- UVM: no base example has real RTL behind a `req_ack` or `pop_ack` port, or behind an AXI port. mixed declares req_ack ports only, pySocket's `dut.sv` drives nothing, and axiDemo's producer and consumer RTL are stubs. Only the loopback and scratch model-DUT benches have exercised these agents.
- UVM: the `notify_ack` `A2C_DST` driver has not run against RTL. The mixed example, whose blockA has a notify_ack `src` port, does not build on Xcelium (`URRNG` in blockB's `memory_dp.sv`), and its blockA RTL fails VCS elaboration (`ICPD`).
- UVM: an `axi4_stream` src agent can send a packet longer than the buffer of a multi-cycle model channel. Its items carry no `maxTransferSize` limit.
- UVM: the memory next-access rule passes an X `read_data` word whose next access writes the same address, even when the design used the X word.
- UVM: the AXI burst limit counts bytes, so on a bus wider than a byte it is below the channel's beat capacity. On a 32-bit bus with `maxTransferSize` 256, INCR bursts stop at 64 beats.
- UVM: the AXI slaves do not interleave R beats of different bursts. `reorder` reorders whole bursts. The master and monitors accept interleaved R.
- UVM: with `id_unbound` set, an AXI master's response carries ID 0, not the ID of the item it answers.
- UVM: a UVM failure that leaves a model's end-of-test voter waiting hangs the run, because the run ends only when every voter has voted. Pass `--scTimeLimit <us>` on model-DUT benches.
- UVM: a model that calls `register_test_name` or `ADD_TEST` exits under UVM, because the UVM testbench config lists no tests (section 9.11). Some base example models do, such as simple's producer and mixed's blockD, so those blocks cannot run as a model DUT under UVM.
- UVM: Pro's lmmiDemo RTL does not elaborate on Xcelium, which rejects `$bits` of a hierarchical name in a typedef.
