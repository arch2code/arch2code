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
| `VCS_DEBUG` (SystemVerilog) | `VCS_DEBUG=1`, or `WAVES=1` under `USE_VCS` | when the run passes `+fsdbTrace`, the HDL wrapper and the UVM testbench module call `$fsdbDumpvars` on the scope `+a2c_waves_scope` names, or else on themselves |
| `VERILATOR` (SystemVerilog) | Verilator, set by the tool | the HDL wrapper leaves out its X/Z checker instances (section 9.4) |
| `A2C_UVM_RTL_DUT` (SystemVerilog) | `USE_UVM` with `UVM_DUT=rtl` (section 9.7) | the generated UVM testbench module holds the RTL wrapper and ties off its pins toward SystemC |
| `A2C_UVM_BOTH_DUT` (SystemVerilog) | `USE_UVM` with `UVM_DUT=both` (section 9.7) | the generated UVM testbench module holds the RTL wrapper on the port interfaces and a second interface per port, `<port>_model`, on the pins toward the SystemC model (paired mode, section 9.12) |
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
| Verilator | 5.038 | needed only for `make lint` in `rtl/` and the Verilator flow |

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
| `WAVES` | optional | unset | `1` sets `VCS_DEBUG`, and the UVM run script adds `+fsdbTrace +fsdbfile+waves.fsdb`, so each run writes `waves.fsdb` in the directory it starts from. A non-UVM run passes `+fsdbTrace` itself (section 9.14) | `1` |
| `WAVES_SCOPE` | optional, read at run time | the UVM testbench module | the instance a `WAVES=1` UVM run dumps, passed to the simv as `+a2c_waves_scope` | `sc_main.uvmMem.tb_hdl.dut` |
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
| `WAVES` | optional | unset | `1` elaborates with `-access +r` and has every run script source `include/make/a2c-waves-xrun.tcl`, which probes `WAVES_SCOPE` into `waves.shm` in the directory the run starts from. Read access slows the simulation | `1` |
| `WAVES_SCOPE` | optional, read at run time | `sc_main` | the scope a `WAVES=1` run probes, with every level below it | `sc_main.uvmMem.tb_hdl.dut` |

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
| `make clean` | the database, `.gen/`, `build/`, `build_xrun/`, and in the rundir `AN.DB`, `csrc`, `vc_hdrs.h`, `vcs.log`, `vlogan_*.log`, `xcelium*.d`, `xrun*.log`, `xrun*.history`, and any `waves.shm`, `waves.fsdb` or `tr_db.log`, whatever switch is set. Run it from the project root, which reads no toolchain variable. From `rundir/` it needs the same variables as a build |

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
- `--vlTrace` has no effect under VCS or Xcelium. Build with `WAVES=1` for waveforms instead (section 9.14). Under VCS this needs Verdi's FSDB support in the VCS install. Other Xcelium access options go on `EXTRA_XRUN_OPTS`, and other probe commands on `EXTRA_XRUN_R_OPTS`, since the snapshot build simulates nothing.

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

A block with `hasUvm: true` gets a generated SystemVerilog UVM testbench that drives its SystemC model, its RTL, or both at once, under Xcelium or VCS. With both, paired mode, the RTL is the DUT under test and the model runs beside it as its reference (section 9.12). SystemC stays on top, and `sc_main` and `main.cpp` run as they do for every testbench. SystemC instantiates the UVM testbench module the way it instantiates an HDL wrapper top, through the `vlogan -sc_model` shell under VCS and an `xmsc_foreign_module` shell under Xcelium.

Base generates the testbench module, the variant package with its register model and `uvm_env`, the SystemC side, and a test package with a base test, a fail test and, for paired mode, a model mismatch test. `make USE_UVM=1` builds and runs it (section 9.7). The project writes its scoreboards, sequences and tests in the user spans of the test package (section 9.6). Base's `examples/uvmMem`, with rdy_vld and memory ports, and `examples/uvmRegs`, with a hierarchical register model, are the worked examples.

Where to read:

- New to the flow: "Terms" and "A first test" below.
- Writing tests: section 9.6, and the `verify-uvm` skill.
- A failing run: section 9.14, and the message catalogue in section 9.17.
- Where the flow differs from common UVM practice: section 9.13.
- What the flow does not verify, and its other limits: section 10.

#### Terms

| Term | Meaning |
| :--- | :--- |
| DUT, `UVM_DUT`, `--uvmDut` | what a snapshot holds: `model`, the SystemC model behind its BFMs; `rtl`, the RTL; `both`, the two side by side |
| single mode | a run with one DUT, `model` or `rtl`. Each port has one pin set |
| paired mode | a run with `both`. The RTL is the DUT under test, and the model runs beside it on the same stimulus as its reference, compared port by port (section 9.12) |
| lane | one pin set of a port in paired mode. The DUT lane, `cfg.vif`, reaches the RTL. The model lane, `cfg.model_vif` on the testbench module's `<port>_model` interface, reaches the model. One agent drives and monitors both |
| comparator, pair | each agent's `model_cmp` in paired mode matches an item of the DUT lane with one of the model lane, in order, or in order per key such as an AXI ID. The two items are a pair, and a report's `pair <n>` counts from 1 |
| drive point | 100 ps after a rising edge (`DRIVE_SKEW`), where the agents' drivers change pins |
| sample point | one time-resolution step before the falling edge, where a SystemC BFM completes a model's call (section 9.11). The agents' monitors sample at the falling edge itself |
| unit | a run of beats that a rule marks, such as a frame, a line or a packet |
| real-time checker | `a2c_rt_checker`: checks one output stream against one input stream, unit by unit, for stalls and throughput (section 9.6, "Real-time checks") |
| credit | three unrelated things. The real-time checker's starvation and hold credits are clocks the testbench caused, which excuse an idle or late output (section 9.6). The paired-mode memory credit, `<port>_model_credit`, counts the DUT lane's accesses so the model's BFM can hold the model's (section 9.12) |
| progress rules | the checks that end a run that stops moving: the output deadline, the joint stall rule, and in paired mode the lane skew and lone lane rules and the drain's deadline (sections 9.6 and 9.10). The run timeout is their backstop |
| drain | the end-of-test wait, in paired mode, for each responder's model lane to replay what its DUT lane recorded (section 9.6) |
| stable point | where a status comparator compares the latest value of each lane; by default each return of `wait_for_outputs()` (section 9.12) |
| top, stem | one testbench per standalone variant, named by its stem, `<block>_<variant>`, or `<block>` for a block without params. `UVM_TOP` and `--uvmTop` take the stem |
| snapshot | the simulator build of one top and one DUT, such as `build_xrun/run_uvm_<stem>_<dut>` |
| variant package, test package | the generated `<stem>_uvm_pkg.sv` holds the register model and `<block>_env`. `<block>_uvm_test_pkg.sv` holds the tests: the generated base test and the project's code in two user spans (section 9.6) |

#### A first test

This walks through `examples/uvmMem` on Xcelium. Its DUT takes commands on `cmd`, reads and writes one memory through the `memory` ports `wr` and `rd`, and sends each word it read on `out`. The example's test package already holds a scoreboard, a sequence, a smoke test and a random test. On VCS, use `USE_VCS=1` and `build/run` where the steps say `USE_XCELIUM=1` and `build_xrun/run`. Source the simulator setup first (section 4).

1. **Generate.** From the project directory, `make gen` writes the generated sections of every file. A new block sets `hasUvm: true` and runs `make newmodule` once before it, to create the UVM files (section 9.2).

   ```
   make gen
   ```

2. **Build** one snapshot from `rundir`. `UVM_DUT=rtl` puts the RTL in it; `model` is the model alone and `both` is paired mode. The result is `build_xrun/run_uvm_uvmMem_rtl`.

   ```
   make -j8 USE_UVM=1 USE_XCELIUM=1 UVM_DUT=rtl all
   ```

3. **Run** one test with a seed. `--uvmDut` and `--uvmTop` pick the snapshot, `+UVM_TESTNAME` the test, and `--seed` seeds both the SystemC side and the SV solver. In a project's own rundir the dispatcher is `../builder/dutRun.py`.

   ```
   ../../../dutRun.py build_xrun/run uvmMem_uvm --seed 7 --verbosity=low --uvmTop uvmMem --uvmDut rtl \
       +UVM_TESTNAME=uvmMem_smoke_test
   ```

4. **Read the result.** A passing run exits with status 0. Near the end of its log:
   - `[A2C_TXN_COUNT] out: received the 32 expected transactions`, the output counter's check;
   - `[UVM_MEM_SB] 32 words checked`, the example's own scoreboard;
   - an `A2C_RUN_TIMEOUT` info with the run's length in clocks, and one `A2C_DIGEST` line per port;
   - the UVM report summary, with `UVM_ERROR :    0` and `UVM_FATAL :    0`;
   - the SystemC side's verdict, `UVM finished with 0 UVM_ERROR/UVM_FATAL; the SV testbench was built with the RTL DUT`.

   A failing run exits with a non-zero status, and an `A2C_RERUN` line sits beside its first `UVM_ERROR`. Section 9.14 takes it from there.

5. **Add a test.** A test goes in the second user span of `uvm/uvmMem_uvm_test_pkg.sv`, after `uvmMem_random_test` and before the generated `footer` section. It extends the base test and puts its stimulus in `run_body()`:

   ```systemverilog
   // 64 commands with up to 5 idle clocks before each.
   class uvmMem_gap_test extends uvmMem_base_test;
       `uvm_component_utils(uvmMem_gap_test)

       function new(string name, uvm_component parent);
           super.new(name, parent);
       endfunction

       virtual task run_body();
           env.send(64, 5);
       endtask
   endclass : uvmMem_gap_test
   ```

   `send()` is a helper of the example's `uvmMem_tb_env`. It declares 64 words on the `out` counter with `expect_count()` and starts the command sequence on `cmd_agent.sqr`. After `run_body()` returns, the base test waits for every declared output. Rebuild, and run the test by name:

   ```
   make -j8 USE_UVM=1 USE_XCELIUM=1 UVM_DUT=rtl all
   ../../../dutRun.py build_xrun/run uvmMem_uvm --seed 7 --verbosity=low --uvmTop uvmMem --uvmDut rtl \
       +UVM_TESTNAME=uvmMem_gap_test
   ```

   It ends with `out: received the 64 expected transactions` and `64 words checked`.

6. **Run it in paired mode, then in the regression.** `UVM_DUT=both` on the build and `--uvmDut both` on the run compare the same test's RTL with the model. Add the test to each DUT group of `rundir/regr_uvmMem_uvm_xcelium.json` and of the VCS file; `make regr_uvm_xcelium` builds every snapshot and runs the list (section 9.7).

### 9.1 Opting a block in

`hasUvm: optional(false)` is a block flag beside `hasVl`, independent of `hasTb`. `projectCreate.validateUvmBlocks` stops `make db` when a `hasUvm` block:

- has `hasVl: false`, because the testbench drives the block's HDL wrapper;
- has params but no standalone variant, so it would get no testbench top;
- declares no `ports:`;
- has an output clock or reset, because the testbench drives every clock and reset and samples none;
- has an input clock whose period is 200 ps or less. Drivers change pins `DRIVE_SKEW`, 100 ps, after a rising edge and monitors sample at the falling edge, so the period must exceed twice the skew (`UVM_DRIVE_SKEW_PS` in `pysrc/processYaml.py`, `DRIVE_SKEW` in `a2c_clk_if.sv`). A block with no input clock never reaches this check: every port of a `hasVl` block needs a clock with a reset, and a reset belongs to an input clock;
- has a boundary port whose interface type lacks `uvmAgent: true`. A boundary port comes from `ports:`, a `connectionMaps` boundary row, `registerPorts:`, or a `memoryConnections` or `registerConnections` row naming an instance of the block. A `memoryConnections` port has type `memory`, and a `registerConnections` port the type its register's `regType` maps to: `status` for `rw` and `ro`, `external_reg` for `ext`, `memory` for `memory`. The error names the port and the type, and the interface or the row it comes from. A type carries the flag in its definition, `interfaces/<type>/<type>_if.yaml`;
- has a port, clock or reset whose name the testbench module already uses: `dut`, `uvm_done`, `uvm_errors`, `rtl_dut`, `model_dut`, `uvm_reset_req`, `srv`, `<clock>_if` for any of its clocks, `<port>_<signal>` for any of its pins, or, on a block with a model, `<port>_model` for any of its ports and, for a port of a type that sets `uvmModelCredit`, `<port>_model_credit`, `<port>_model_held` and `<port>_credit`;
- has a register named `block`, whose class `<block>_reg_block` would be the register block class;
- has a register field named like a `uvm_reg` member, or a register or memory named like a `uvm_reg_block` member or `a2c_map`, the generated `build()`'s map variable;
- has a register or memory row wider than 64 bits (`UVM_REG_DATA_WIDTH`) at any standalone variant. The decoder's row stride does not count, because the register model gives a memory its row width (section 9.5);
- has a register model whose bus port, the block's own register bus or a tree's (section 9.5), has an interface type whose agent package declares no `<type>_reg_adapter` class. The env drives the model through that class, so the testbench would not compile. The package is `<type>_uvm_pkg.sv` beside the file that defines the interface type, as for every shipped type; only `apb` ships an adapter.

A `hasUvm` block that owns no rows itself but reaches them through a router or a passthrough gets a hierarchical register model (section 9.5). The register checks above then apply to every row it reaches, at the variant of the instance that owns the row, and each message names the instance path. The check also rejects an instance on the way named like a `uvm_reg_block` member, and two instance paths whose classes would get one name.

The same check rejects an interface definition, used or not, that sets `uvmMaxTransferBytes`, `uvmIdParam` or `uvmModelCredit` without `uvmAgent: true`, or whose `uvmIdParam` is not one of its `parameters`.

`raw` has limited support. It is complete against the RTL DUT and best effort against the model DUT, because the SystemC raw BFM is not transactional and can lose a word. `rules/dev-skills/authoring-interface-definitions.md` has the details.

### 9.2 Generated files

The files go in the `uvm` segment, `$root/uvm` in the functional layout and `<node>/uvm` in the hierarchical one. Its buildGroup is also `uvm`, which only the `USE_UVM` flow builds, so no UVM file reaches the model, Verilator or plain RTL compile lists. `<stem>` is `<block>_<variant>` for each standalone variant of a block with params, and `<block>` for a block without params, which has one top.

| fileMap entry | File | Per | Content | Template |
| :--- | :--- | :--- | :--- | :--- |
| `uvmPkg` | `<stem>_uvm_pkg.sv` | standalone variant | package `<stem>_uvm_pkg`. The `items` section holds the variant's parameter values as localparams, the block's parameterized types, per port the typedefs `<port>_agent_t`, `<port>_item_t`, `<port>_config_t` and `<port>_vif_t`, then the register model and `<block>_env` (section 9.5). A user region follows the items | `templates/systemVerilog/uvmPkg.py` |
| `uvmTest` | `<block>_uvm_test_pkg.sv` | block, shared by its variants | package `<block>_uvm_test_pkg`, which imports the variant package that `` `A2C_UVM_PKG `` names. Generated sections hold `<block>_base_test`, `<block>_fail_test`, `<block>_rt_fire_test` and `<block>_model_mismatch_test`; two user spans hold the project's env subclass, scoreboards, sequences and tests (section 9.6) | `templates/systemVerilog/uvmTest.py` |
| `uvmTb` | `<stem>_uvm_tb.sv` | standalone variant | module `<stem>_uvm_tb`, which imports the test package so the factory registers its tests. Its ports are the HDL top's pins with port directions inverted, then the clocks and resets as inputs, then, on a block with a model, for each DUT `src` port of a type whose definition sets `uvmModelCredit: true` (`memory`), the 32-bit output `<port>_model_credit` and the input `<port>_model_held`, then the completion outputs `uvm_done`, the 32-bit `uvm_errors`, `rtl_dut` and `model_dut`, then `uvm_reset_req`, the test's reset request (section 9.6, "A reset during the test"). A one-bit pin is a scalar `bit`, matching the `bool` the simulator shell binds, and a vector payload width is `$bits` of the package-qualified type. It holds one `<type>_if` per port, one `a2c_clk_if` per clock, three DUT branches, the `uvm_config_db` keys and `run_test()`. Under `` `ifdef A2C_UVM_BOTH_DUT `` it holds the RTL wrapper as instance `dut` on the port interfaces and one more interface per port, `<port>_model`, assigned to the pins toward SystemC. Under `` `elsif A2C_UVM_RTL_DUT `` it holds `dut` with the pins toward SystemC tied off. Under `` `else `` the port interfaces are assigned to the pins. `rtl_dut` and `model_dut` say which DUTs the branch holds. Every branch sets the `bit` key `a2c_dual_dut`, 1 only in the both branch, which also publishes each `<port>_model` interface under that name, and, per credited port, an `a2c_credit_if` `<port>_credit` on its two credit pins, published as `<port>_credit`. The other branches tie each `<port>_model_credit` to 0. On a block with a model it imports `a2c_bfm_contract_break` through DPI and raises each queued SystemC BFM contract break as an `A2C_BFM_CONTRACT` `UVM_ERROR` (section 9.8). User regions take imports and module body | `templates/systemVerilog/uvmTb.py` |
| `uvmScWrap` | `<block>_uvm_sc_wrapper.h` | block | class template `<block>_uvm_sc_wrapper<TB_T, Config>` over the simulator shell `TB_T`, or `<TB_T>` alone for a block without params. It drives the clocks and resets into the shell, with resets born low, and asserts every reset again while the testbench raises `uvm_reset_req`. With the model DUT or both DUTs it also holds the model, its channels and the BFMs in the DUT's swapped roles. The BFMs change the pins between a rising edge and the sample point, one time-resolution step before the falling edge where the agents' monitors sample, including at the sample point itself (section 9.11). A block with params creates its model with `createInstance<<block><Config>>`, as a container creates a child typed by its Config, which has no factory registration; a registration under the variant still wins. When the run holds the RTL and the model, it hands each credited port's `memory_dst_bfm` its credit and held pins through `setModelCredit()`, and when the run holds the model alone it gives the BFMs of two or more ports of a `bfmWriteOrder` type one `memory_write_order` through `setWriteOrder()` (section 9.12). It waits for `uvm_done` and ends the run | `templates/systemc/module_uvm_sc_wrapper.py` |
| `uvmTbConfig` | `<block>UvmConfig.cpp` | block | testbench config `uvmTbConfig`, registered under the testbench name `<block>_uvm`, with options `--uvmDut` and `--uvmTop`. `--uvmTop <stem>` selects the variant through a generated map, so the config serves every top of the block | `templates/systemc/uvmTbConfig.py` |
| `uvmRegistrar` | `<block>UvmRegistrar.cpp` | block | registers the wrapper as `<block>_uvm` once per standalone variant, over that variant's shell and Config | `templates/systemc/uvmRegistrar.py` |

`make newmodule` scaffolds the test package once, with a working `<block>_tb_env` and an empty `<block>_smoke_test` in its user spans, so the generated tests compile and pass before any user code exists. `make gen` rewrites only the generated sections of every file.

The templates guard two of these files with `#if defined(XCELIUM) || defined(VCS)`, each for its own reason:

- `<block>UvmRegistrar.cpp` includes the simulator shells, `<tbModule>_xcelium.h` under `XCELIUM` and the `vlogan` shell `<tbModule>.h` otherwise, and only those two builds write them.
- `<block>UvmConfig.cpp` includes no shell. It creates the wrapper through the factory key `<block>_uvm`, and only the guarded registrar registers that key. Unguarded, it would offer a `<block>_uvm` testbench in a build that cannot create its wrapper.

A block with `hasMdl: false` gets the RTL DUT only. Its testbench module holds the RTL with no DUT branches, its wrapper has no model, channels or BFMs, and its config accepts only `--uvmDut rtl`, the default. It has no paired mode.

`make gen` under `USE_VCS` or `USE_XCELIUM` also writes two boundary files per testbench top, in the same `--vlBoundary` run as the HDL tops' (section 1.5):

| File | Content |
| :--- | :--- |
| `.gen/vl/<tbModule>.portmap` | the VCS port map for `vlogan -sc_model <tbModule>` |
| `.gen/vl/<tbModule>_xcelium.h` | `class <tbModule> : public xmsc_foreign_module`, which the registrar includes under Xcelium |

Both come from `projectOpen.getUvmTopBoundaryPins`. It takes the HDL top's pins from `getVlTopBoundaryPins`, inverts the port directions, leaves clocks and resets as inputs, and adds the four completion pins and `uvm_reset_req`.

### 9.3 Names and manifest records

`projectCreate.deriveUvmNames` persists every name as the `UVMNAMES` config, keyed by block. Templates and the manifest read it and never derive a name from a file name.

| Field | Value |
| :--- | :--- |
| `scWrapperClass`, `scWrapperHeader` | `<block>_uvm_sc_wrapper`, `<block>_uvm_sc_wrapper.h` |
| `runClass` | `<block>_uvm_run`, the static run state the config and the wrapper share |
| `testbenchName` | `<block>_uvm` |
| `duts` | `['model', 'rtl', 'both']`, or `['rtl']` for a block with `hasMdl: false`. The first is the default |
| `envClass`, `regBlockClass` | `<block>_env`, `<block>_reg_block` |
| `registerTreeBusPort` | the register-bus port of a hierarchical register model (section 9.5), null when the block's own rows are its model or it reaches none |
| `testPkgName`, `tbEnvClass` | `<block>_uvm_test_pkg`, `<block>_tb_env` |
| `baseTestClass`, `smokeTestClass`, `failTestClass`, `rtFireTestClass`, `modelMismatchTestClass` | `<block>_base_test`, `<block>_smoke_test`, `<block>_fail_test`, `<block>_rt_fire_test`, `<block>_model_mismatch_test` |
| `tops[<variant>]` | one row per standalone variant, or one row under `''` for a block without params. Each row holds `stem`, `tbModule`, `pkgName`, `hdlTop`, `portmap`, `xceliumShell`, `xceliumShellHeader`, `vcsShellHeader`, the per-variant register widths and `registerTree`, the instance tree of a hierarchical register model at that variant, null when the block's own rows are its model or it reaches none, and `reuse`, the child blocks whose variant packages the top reuses (section 9.15). `stem` is the name `UVM_TOP` and `--uvmTop` take. `hdlTop` is the HDL wrapper top the testbench instantiates, and `portmap` and `xceliumShell` are paths under `.gen/vl` |

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
| `A2C_UVM_REUSED_SV_<top>` | the variant package files of the child blocks the top reuses (section 9.15), compiled before the top's own variant package |
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

Tested with: the SystemC regressions of a multi-block streaming design, run with the checkers elaborated under Xcelium and VCS.

### 9.5 The environment and the register model

The `items` section of the variant package holds both, generated whole. A project extends the env in its test package and never edits this file's generated sections.

`<block>_env extends uvm_env` holds:

- one `<port>_agent` per boundary port, in port order, configured in `build_phase` from a `<port>_config_t` object. The config takes the `virtual <type>_if` from `uvm_config_db` under the port name and `clk_vif` from the port's own clock domain, so a multi-clock block needs no hand wiring. Every agent gets a role, the opposite of the DUT port's direction, `A2C_SRC` on a DUT `dst` port. `no_backpressure` follows the port's effective backpressure on a type whose backpressure is overridable. On a port of a type whose definition sets `uvmMaxTransferBytes: true`, `axi_read` and `axi_write`, the env sets `max_transfer_bytes`. On a port that leaves unbound the parameter its type names in `uvmIdParam`, `id_t` on both AXI types, it sets `id_unbound` (section 9.10). The env sets no agent passive and no `cfg.mem`, so each memory-backed agent creates its own model. A DUT `src` port gets an `A2C_DST` agent that serves it: on a DUT apb `src` port that is `apb_slave_driver`, with no sequencer. The register model stays on the register-bus port, so a block that is a bus target and a bus master gets one `A2C_SRC` agent with the register model and one serving `A2C_DST` agent per downstream apb port;
- one `<port>_counter`, an `a2c_uvm_pkg::a2c_txn_counter`, per DUT output with a handshake: a `src` port of an elastic type that is not an address-bus type. Those types are `rdy_vld`, `axi4_stream`, `push_ack`, `notify_ack`, `req_ack`, `pop_ack`, `axi_read`, `axi_write` and Pro's `lmmi`. The counter counts the monitor's `ap` items, so on `pop_ack` it counts the DUT's pops, on `axi_read` its read bursts and on `axi_write` its write bursts. `connect_phase` connects the output monitor's `mon.ap` to its `analysis_export`;
- one `<port>_digest`, an `a2c_uvm_pkg::a2c_txn_digest`, per port, inputs and register bus included. `connect_phase` calls its `watch()` on the port's `mon`;
- one `virtual a2c_clk_if` per clock, as `<clock>_vif`;
- with a register model, `regmodel`, the bus's `<type>_reg_adapter` as `adapter`, and a `uvm_reg_predictor` as `predictor`. `build_phase` builds the model and calls `regmodel.reset()`. `connect_phase` sets the bus agent's sequencer and the adapter on `default_map`, turns auto-prediction off, and feeds the predictor from the bus monitor, so the mirror follows bus traffic from any sequence. `write_reg(rg, value)` writes a register through the front door and reads it back, an `A2C_REG` error on a bad status or a read-back that differs, and returns once the write has reached the DUT;
- `dual_dut`, read from the `bit` key `a2c_dual_dut` that the testbench module sets, and the paired-mode wiring it turns on: each agent's `cfg.model_vif` from `<port>_model`, each credited port's `cfg.credit_vif` from `<port>_credit`, an `A2C_CFG` fatal when it is missing, each counter's and each digest's `dual` with the agent's `model_mon.ap` connected to the counter's `model_export` and the digest's `watch()` called on `model_mon`, the list `comparators` of every agent's `model_cmp`, each digest's `cmp` set to that `model_cmp`, `model_stable_point()`, and, with a register model, `guard`, an `a2c_midstream_guard`, fed through `reg_writes`, an `a2c_reg_write_subscriber` on the bus monitor. The env also gives the guard `regmodel.default_map` and gives the bus agent's `model_cmp` the guard, so the comparator can ask it about each read. Section 9.12 describes them. The predictor stays on the DUT lane's bus monitor, so register reads and the mirror test the RTL.

`a2c_txn_counter #(T)` (`common/systemVerilog/uvm/a2c_uvm_pkg.sv`) is a `uvm_subscriber`. It counts transactions and checks nothing about their content. `expect_count(n)` adds n to the expected count. `wait_for_count(clk_vif, deadline_cycles, quiet_cycles)` waits for the expected count, reports a shortfall as `UVM_ERROR` id `A2C_TXN_COUNT` when the deadline passes, then waits the quiet window and reports any excess the same way. A clock with no edge for the counter's `clock_stop_cycles` periods (default 1000) has stopped, which reports the shortfall or ends the quiet window at once. `check_phase` reports what no wait covered. A transaction that arrives after its shortfall was reported is logged as late, not counted again, until the next `expect_count()`.

`a2c_txn_digest #(T)` keeps a 64-bit FNV-1a hash per lane of every item its exports receive, over the item's fields and `$realtime` at the `write()`, in arrival order. `watch(mon, lane)` connects the monitor's `ap` to the lane's counted export, `analysis_export` or `model_export`, and every other analysis port of the monitor that carries the item type to the lane's `side_export` or `model_side_export`, which hash the item, tagged as a side item, without counting it. So the `external_reg` monitor's `rdata_ap` levels and the `req_ack` monitor's request-time `req_ap` items enter the digest. A monitor with no `ap` of the item type is an `A2C_CFG` error. The fields come from `digest_parts()` on an item that implements the interface class `a2c_digest_fields`, which appends them as a list of strings that the digest hashes one by one, so a long burst costs time in proportion to its length, and from `convert2string()` on any other. `axi_read_item` and `axi_write_item` implement it, adding every beat's data, response or strobe and user signal to the burst fields their `convert2string()` prints, so their `A2C_TXN` lines stay one line per burst. The other base and Pro items print their whole payload in `convert2string()`. A project item whose `convert2string()` leaves payload out implements `a2c_digest_fields` too. `report_phase` prints one `UVM_LOW` line per lane, the model lane only with `dual` set:

```
A2C_DIGEST <port> <DUT|model> paired=<0|1> items=<n> digest=<16 hex digits>
```

`items` counts the `ap` items only, the stream the paired-mode comparator sees. `paired` is the digest's `cmp.pairs_every_item()` at `report_phase`, and 0 with no `cmp`; the env sets `cmp` in paired mode to the port's `model_cmp`. `a2c_in_order_comparator` and its subclasses, the keyed AXI, register and memory comparators included, return 1, since they pair every item of one lane with one of the other, unless an end-of-test drain left a cut in force (section 9.6, "The paired-mode end-of-test drain"): the cut holds the items either lane delivers after it unpaired, so a DUT still flowing at the end can count more items than the model lane in a passing run, and the port prints `paired=0`. `a2c_status_comparator` and its subclasses, which compare the latest value at stable points, return 0: a status port under the `stable` policy can see more value changes on one lane than the other in a correct run.

The digest is the run's stimulus and response on that port, as its monitor reports them, in one value, so two runs can be compared without diffing their `A2C_TXN` lines. Items that move in time with unchanged content change it. It checks nothing itself; `seedRepro.py` compares two runs' lines (section 9.7).

The register model is generated from the block's address rows, so it cannot disagree with `fw/<block>RegAddresses.h` on an offset:

- one `<block>_reg_<register>` (`uvm_reg`) per `registers:` row, with one `uvm_reg_field` per structure member at its packed position, the first member most significant. Padding members are fields too, because the decoder flops them. Each field's reset is its share of `defaultValue`. `rw` registers are `RW` and their fields `rand`; `ro` and `ext` registers are volatile, and `ro` is `RO`;
- one `uvm_mem` per `memories:` row with `regAccess`, and one `RW` memory per `regType: memory` register. A `wo` memory is `RW` with `WO` map rights and gets `NO_MEM_TESTS`, because UVM reports WO rights as RW in a one-map model. A memory's `n_bits` is its row width at the variant. The decoder sizes its row stride for the widest variant's row, so a row can be narrower than its stride, and UVM 1.2 would step the memory by `ceil(n_bits / 32)` bus words. `default_map` is therefore an `a2c_reg_map` in every block with a memory, and `set_mem_stride()` gives each memory the decoder's stride, which for a row as wide as its stride is the stride UVM would use. An access moves only the row's own bus words, which is what the RTL decoder commits on, and `get_mem_by_offset()` counts the unused words of a row as the memory's. `get_size()` still uses UVM's stride. `a2c_reg_map` reads UVM 1.2's map info, so a move to IEEE 1800.2 must check it;
- `<block>_reg_block`, with `default_map` at base 0, a 4-byte bus and little-endian order, each register and memory at its row's offset. Widths and depths are resolved per variant at `make db`. A register wider than the bus becomes consecutive 4-byte accesses.
- a hierarchical model for a top that owns no registers or `regAccess` memories itself, because it hosts a router (`addressBlock:`) or passes its register bus through to one consumer. The model then mirrors the instance tree from the top's register port down to every block that owns rows. Each routed instance, nested-router host and passthrough container on the way is a child `uvm_reg_block`, a member named after the instance, so a test writes `regmodel.uBridge.uDeep.cfg`. A child is at its slot offset in its parent, `addressID` times the router's `addressIncrement`. A passthrough's consumer is at offset 0. Subtrees with no rows are left out. A leaf's classes are `<top>_<instance path>_reg_<register>` and `<top>_<instance path>_reg_block`, the path joined with `_`. Their widths and depths come from the instance's own variant, so two instances of one block at different variants get classes of their own. Offsets and strides stay worst case, as the decoder lays them out. `make db` rejects a routed row wider than 64 bits, an instance named like a `uvm_reg_block` member, and two paths that join to one class name, each naming the instance path. The env is the same as a leaf top's. Its bus port is the top's `registerPorts:` key, or else the one boundary port that a `connectionMaps` row maps onto the router the top hosts, which feeds the router's upstream port whatever name the row gives it. `make db` rejects a top with neither, or with more than one such port, naming the top and the router instance.
- in a hierarchical model, generated or hand-built, each child block's map joins its parent block's map through `add_submap()` at the child's offset. The root map, and every map above an `a2c_reg_map`, must itself be an `a2c_reg_map`, even in a block with no memory. An `a2c_reg_map` under any other parent is an `A2C_CFG` fatal, because the parent's `get_mem_by_offset()` would find the child's rows only within UVM's stride. So is one whose bus width or addressing differs from its parent's. A memoryless child with no `a2c_reg_map` below it may keep a plain `uvm_reg_map`. Call `set_mem_stride()` on the map of the memory's own block. The root map's `get_mem_by_offset()` searches the root map and every `a2c_reg_map` below it, so a child's memory resolves at its root-map address, unused row words included. `check_overlaps_once()` checks every strided range against the others and against every register below the root. It is an `A2C_CFG` fatal before `lock_model()`, when the addresses are not yet final. A generated root block with an `a2c_reg_map` calls it after `lock_model()`, so the check runs at build even when no test looks anything up, and the root map's first `get_mem_by_offset()` calls it too. UVM's own overlap warnings use UVM's stride and miss these, so an overlap is an `A2C_CFG` fatal naming both elements. UVM fills the offset tables behind `get_reg_by_offset()` and `get_mem_by_offset()` only on the root map, so the predictor, the paired-mode guard and `a2c_reg_write_subscriber` take the root map. The guard and the subscriber raise an `A2C_CFG` fatal at `end_of_elaboration_phase` when given any other map. `skip_reg()` and `skip_mem()` take no map, the element's own map or the root map, and all three give the same root-map addresses.
- in UVM 1.2, `uvm_reg_block::configure()` puts each block in the resource database under its full name, and the `.` in a child block's full name makes the resource raise a `UVM/RSRC/NOREGEX` warning, one per child block. IEEE 1800.2 drops that registration. A generated root block with children therefore calls `a2c_uvm_pkg::a2c_child_block_catcher::install(this)` before it builds them and `remove(this)` once they are built. While installed, the catcher turns a `UVM/RSRC/NOREGEX` warning into a `UVM_INFO` at `UVM_HIGH` when its message names a block below the root, and puts the reason in front of the text, so a run at `UVM_HIGH` still shows each one. A resource of any other name, or one created while the catcher is not installed, still warns. The catcher goes ahead of every other report catcher, so the others see the info. A hand-built hierarchical model can make the same two calls around building its children. A second `install()` for one root, or a `remove()` for a root with no catcher, is an `A2C_CFG` fatal. A leaf top's model has no child blocks and installs no catcher. Against an IEEE 1800.2 library, which raises no such warning, `install()` and `remove()` keep their checks and add no catcher.

Only text unit tests cover the multi-word path. `examples/uvmRegs` runs a hierarchical model with `rw`, `ro` and `ext` registers, a `regAccess: ro` memory and a `regType: memory` table narrower than its stride (section 9.9).

### 9.6 The test package

`uvm/<block>_uvm_test_pkg.sv` holds the project's tests. Its layout, top to bottom:

| Span | Owner | Content |
| :--- | :--- | :--- |
| `header` | generated | package `<block>_uvm_test_pkg`; imports of `uvm_pkg`, `a2c_uvm_pkg`, the agent packages, the block's type packages and `` `A2C_UVM_PKG ``. An undefined `A2C_UVM_PKG` expands to a package name that says to define it |
| user span 1 | project | `<block>_tb_env extends <block>_env`, with the scoreboards and any helpers; also sequences and other classes the tests use |
| `tests` | generated | `<block>_base_test` |
| user span 2 | project | `<block>_smoke_test` and the project's other tests |
| `footer` | generated | `<block>_fail_test`, `<block>_rt_fire_test`, `<block>_model_mismatch_test`, then `endpackage` |

`<block>_base_test extends uvm_test` creates the env as `<block>_tb_env::type_id::create("env", this)`, so the project's subclass needs no factory override. Its `run_phase` raises one objection, waits for each clock's reset release, calls `run_body()`, calls `wait_for_outputs()` and drops the objection. A test puts its stimulus in `run_body()` and never handles objections. `wait_for_outputs()` waits on every output counter at once, each on its own port's clock, and a test may call it between frames. In paired mode each return also calls the env's `model_stable_point()`, the stable point of the status policy (section 9.12). The deadline and quiet window are the members `output_deadline_cycles` (default 200000) and `quiet_cycles` (default 1000). A test sets its own defaults in its constructor, and `+a2c_output_deadline_cycles=<n>` and `+a2c_quiet_cycles=<n>` override them, because `build_phase` reads the plusargs afterwards. `clock_stop_cycles` (default 1000, `+a2c_clock_stop_cycles=<n>`) is the counters' stopped-clock threshold, and the paired-mode drain's. Paired mode is `UVM_DUT=both` (section 9.7): one snapshot holds the RTL, the DUT under test, and the model, its reference, and each agent drives and monitors both pin sets, its DUT lane and its model lane. The paired-mode drain at the end of the run phase has its own knobs, described below. `build_phase` hands the clock stop and the drain's knobs to the env through the `uvm_config_db`.

#### The run timeout

The run timeout is a backstop. The progress rules detect a stop: the output deadline, the drain's deadline and catch-up, the joint stall rule, and in paired mode the lane skew and lone lane rules. The run timeout makes sure that a run none of them ends still gives a report, instead of a farm kill with none. It does not check a real-time requirement such as a frame finishing within its frame time; `a2c_rt_checker` does that ("Real-time checks" below).

`<block>_base_test` creates an `a2c_run_timeout` component, `run_timeout`, and gives it the block's first clock, the one `run_phase` waits on first. From that clock's reset release it counts rising edges. When the count reaches the budget and the run phase is still running, it raises one `A2C_RUN_TIMEOUT` `UVM_ERROR` and ends the run phase prematurely, together with every other task phase that is running, such as `main_phase`. From then on it ends each task phase other than the run phase as it begins, whether a runtime phase such as `shutdown_phase` or a user-defined one, in UVM's schedule or in the common one. UVM's own timeout, `+UVM_TIMEOUT`, is watched only while the run phase runs, so without this a later phase that waits for ever would hang the run. The phases end with their objections still raised, and `extract_phase` and `check_phase` run once each: the output counters report the transactions still missing, and the replay logs report what each lane owes. This behaviour is verified on UVM 1.2 with Xcelium and VCS.

The budget has three modes, set by `run_timeout_cycles`:

| `run_timeout_cycles` | Budget |
| :--- | :--- |
| -1, the default | derived: `run_timeout_floor_cycles + run_timeout_factor * W` |
| above 0 | fixed at that many clocks |
| 0 | off: the run timeout sets no time limit and only counts clocks for its info line. It still ends the run at a single-mode joint stall (section 9.10); `joint_stall_cycles` 0 turns that rule off |

A progress rule reports a stop in its own words, and a derived budget lets one that is counting have its say first. The derived budget holds three promises:

1. A progress rule that is counting toward its bound when the budget is reached may fire first, whatever its bound, with two exceptions that the clock-stop allowance below describes: a lane rule whose clock has stopped is left out, and a clock that pauses more than once can push any rule past the deferral. The rules are the output deadline of a `wait_for_count()`, a master's joint stall rule in either mode, a paired-mode master's lane skew and lone lane rules, the drain's deadline and catch-up, and an `a2c_rt_checker`'s gap, deadline and refusal rules. A checker whose output clock has stopped is left out as a lane rule is.
2. Changing a bound during the run never makes a run time out before its budget: no bound enters the budget, so changing one never moves it. A bound counting when the budget is reached only lengthens the one deferral.
3. Every run still ends: the count defers once at most. A single-mode joint stall that fires during the deferral, or before the budget, ends the run itself (section 9.10), and the count then stops without an `A2C_RUN_TIMEOUT`.

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

W is the work the test has declared: the items its input agents have sent plus the transactions its output counters expect. Work the DUT does through its own masters is not counted: memory or AXI-slave traffic the DUT pulls, and outputs on address buses, which have no output counter. A design whose work is mostly of that kind has a small W, and its test raises `run_timeout_factor` or fixes the budget. `stimulus_sent()` counts the items of every input agent, the register bus's included, through `a2c_items_sent`. `outputs_declared()` sums each output counter's `declared()`. W is a sum, not a max, because a test's phases run one after the other: register configuration takes its clocks before the first frame does. Both functions are virtual, so a test whose work goes through other paths can add it. W is read at the reset release and again each time the count reaches the budget, so the budget grows with the stimulus sent meanwhile. Both counts only ever rise, so the budget never shrinks unless a test overrides one of the functions to return less.

A test can also fix the budget with `run_timeout.fix(<n>)`, from any phase once `run_timeout` exists, which is after the base test's `build_phase`. A test that computes its budget from its stimulus calls it in `run_body()`, before it sends. It takes effect from the next clock, so it can lower the budget as well as raise it, and `fix(0)` turns the timeout off. `fix()` overrides every `uvm_config_db` setting of `a2c_run_timeout_cycles`, whether the test made it or `+uvm_set_config_int` did. Only `+a2c_run_timeout_cycles` overrides `fix()`, and with any value, so `+a2c_run_timeout_cycles=-1` brings back the derived budget.

The message reads:

`<test>: the run phase has not ended after <n> clocks of <clock>, its run timeout: <rate>. <how><left out>. Ports waiting now: <ports>. Objections still raised by: <objectors>. <raise>`

- `<rate>` reads `<r> clocks per unit of the work declared, W <W>`, or `no work declared`. A design whose items take many clocks each, such as frames or DMA bursts, shows a large `<r>` here.
- `<how>` gives the budget's source: `The budget is run_timeout_floor_cycles <f> + run_timeout_factor <k> x <W>, the work the test has declared (input items sent <s>, output transactions expected <o>)`, followed after a deferral by `, deferred at <n> clocks by <d> to the progress rules then counting`, or `The budget is fixed by run_timeout_cycles (+a2c_run_timeout_cycles)`, or `... fixed by run_timeout.fix() in the test`.
- `<left out>` names the lane rules the deferral left out because their clocks had stopped, as in the info above, and is otherwise empty.
- `<ports>` lists each master whose port had a live lane waiting for a handshake on the port's last clock, in the words `A2C_JOINT_STALL` uses (section 9.10), such as `in (uvm_test_top.env.in_agent.drv), both lanes waiting for the transfer of 'h5`. With one DUT (`UVM_DUT=rtl` or `model`) a port has one lane and reads `in (uvm_test_top.env.in_agent.drv), waiting for the transfer of 'h5`. A port whose lanes are both dead is left out. With no master waiting the list is `none`, and something else holds the run: a sequence waiting on an event, a test's own wait, or a component's objection. The DUT's outputs are not listed; their counters report at `check_phase`.
- `<objectors>` are the components and sequences that hold a run-phase objection, from `get_objectors()`, in name order. While `run_body()` runs, the base test, `uvm_test_top`, is one of them. Each other running task phase that holds an objection follows, in domain and then phase name order, as `; <phase> phase: <objectors>`, for example `uvm_test_top; main phase: uvm_test_top.env.holder`. A phase of a domain other than UVM's own reads `; <phase> phase of domain <domain>: <objectors>`. A user-defined phase appears by its name.
- `<raise>` names the knobs to raise: the factor or floor for a derived budget, `run_timeout_cycles` or the value passed to `fix()` for a fixed one.

A task phase that the timeout ends as it begins, and in which something raised an objection, gets one `A2C_RUN_TIMEOUT` `UVM_INFO` at `UVM_NONE` when it ends: `the run timeout, which expired at <time>, ended the <phase> phase as it began. Objections raised by: <objectors>`. A phase in which nothing objected would have ended at once anyway, and is not reported. After a single-mode joint stall ends the run, the same info comes under `A2C_JOINT_STALL` and reads `the joint stall rule, which fired at <time>, ended the <phase> phase as it began. ...`.

The end-of-test reports of missing or unpaired items that follow a timeout end with `; the run timeout ended the run phase at <time> (A2C_RUN_TIMEOUT), which may account for this`: `A2C_TXN_COUNT` for transactions outstanding, `A2C_REPLAY`, and the `A2C_MODEL_CMP` reports of unpaired items and of a held read of X or Z. What they find missing is usually the timeout's doing, so read the `A2C_RUN_TIMEOUT` first. After a single-mode joint stall ends the run, the same reports end with `; the joint stall rule ended the run phase at <time> (A2C_JOINT_STALL), which may account for this` instead, and the `A2C_JOINT_STALL` is the one to read first. A report of extra transactions does not carry it, since a timeout adds none, and neither does a report the run phase raises in the timeout's own time step, such as an `A2C_SKEW`.

A run that ends in time logs one `A2C_RUN_TIMEOUT` `UVM_INFO` at `UVM_LOW` from `extract_phase`: `the run phase ended after <n> clocks of <clock>, within its run timeout of <budget>. <how>`, or `..., with no run timeout. <how> at 0` when the timeout is off. `<n>` is the count of rising edges, which keeps running with the timeout off. The count and W are what a project reads to set its own floor and factor.

The count runs until the run phase ends, so it also bounds a component that keeps an objection after the base test drops its own, and the paired-mode drain.

| Knob | Plusarg | Default |
| :--- | :--- | :--- |
| `run_timeout_cycles` | `+a2c_run_timeout_cycles=<n>` | -1, derived |
| `run_timeout_floor_cycles` | `+a2c_run_timeout_floor_cycles=<n>` | `A2C_RUN_TIMEOUT_FLOOR_CYCLES`, 2500000 |
| `run_timeout_factor` | `+a2c_run_timeout_factor=<n>` | `A2C_RUN_TIMEOUT_FACTOR`, 20 |

A test sets them in its constructor, and the plusargs override them. Each left at -1 sets nothing. Otherwise `build_phase` sets it on the `run_timeout` child as `a2c_run_timeout_cycles`, `a2c_run_timeout_floor_cycles` or `a2c_run_timeout_factor`, which `run_timeout` reads in its `build_phase` with the same accepted types as the drain knobs. A design that takes many clocks per item, such as one whose items are whole frames or long bursts, sets `run_timeout_factor` once in the constructor of its base-test subclass, and every test inherits it.

The defaults come from measurement. A run takes about `a + b * W` clocks. `a` is fixed overhead, chiefly the output quiet window, `quiet_cycles`, 1000 clocks by default, which every `wait_for_outputs()` waits out once. `b` is the clocks per unit of work. Every test of the Xcelium regression of base's uvmMem example, in the `model_dut`, `rtl_dut` and `both_dut` groups, gave its run length and its W:

| Measured | Clocks | W | `b`, with `a` of 1050 |
| :--- | ---: | ---: | ---: |
| longest test: `uvmMem_fail_test`, `both_dut`, ended by the 200000-clock output deadline | 201156 | 65 | not work |
| longest test that passes: `uvmMem_random_test`, `both_dut` | 3283 | 512 | 4.4 |
| `uvmMem_random_test` | 1975 to 3283 | 512 | 1.8 to 4.4 |
| `uvmMem_smoke_test` and `uvmMem_model_mismatch_test` | 1113 to 2160 | 64 | 1.0 to 17.3, inside the floor |

A test that waits out more than one quiet window has a larger `a`, and the table counts the extra windows as work, so its `b` is high. A paired-mode run adds the drain's quiet window, so `uvmMem_smoke_test` comes to 1.0 clock per unit of work on the model and to 17.3 in paired mode.

The defaults were first set from two larger streaming blocks, whose steepest slope was 14.8, in a test that waited out five quiet windows, and whose longest passing test took 19211 clocks for a W of 10902.

- The floor, 2500000, covers `a`. It is about 12.4 times the longest test, and it exceeds the default bounds of the progress rules together, 1200000 clocks, 200000 each for the output deadline, drain deadline, drain catch-up, lane skew, lone lane and joint stall, so they report first. The deferral keeps that true for a test that raises a bound.
- The factor, 20, covers `b`. It is above every slope measured, 17.3 at the steepest with a paired-mode drain counted as work, and four or more times the slope of the random test, 1.8 to 4.4. The measurement cannot pin it down further: for any factor up to about 4800, the W term of even the largest measured test, W 512, stays below the floor.
- Every measured test runs within a tenth of its derived budget. The tightest is `uvmMem_fail_test`, at about 1/12.4.
- A hang in a small test reports after 2500000 clocks. A fail test that waits out the output deadline with the design idle runs about 250000 clocks per CPU second on Xcelium, so such a hang costs about 10 s of CPU, and more on a bench whose design keeps busy. A hang in the largest measured test reports after 2510240 clocks.

A test whose transactions are pixels gets 20 clocks per pixel from the factor. That is more than a frame needs, so a hang in a long frame test reports late: two 1920x1080 frames at one pixel per clock declare a W of about 8.3 million, a budget of about 168 million clocks. A hang costs the budget divided by the bench's clocks per CPU second: about 11 minutes at 250000, and longer on a bench whose design keeps busy. Such a test computes its budget from the frame and fixes it. The budget counts clocks of the block's first clock, so a frame timed on another clock, such as a pixel clock, is converted into clocks of the first one. The frame time in clocks is `(H_active + H_blank) * (V_active + V_blank) / pixels_per_clock`, and the budget is `margin * (configuration + N_frames * frame_time + latency + quiet window)`. For two 1920x1080 frames with 280 clocks of horizontal and 45 lines of vertical blanking at one pixel per clock, a frame takes 2200 * 1125 = 2475000 clocks. With 20 register writes of about 10 clocks each, a two-line latency of 4400 clocks and the output quiet window, `quiet_cycles`, of 1000, the sum is 4955600 clocks, and a margin of 2 makes the budget 9911200:

```systemverilog
virtual task run_body();
    int unsigned frame = (1920 + 280) * (1080 + 45) / 1;
    run_timeout.fix(2 * (20 * 10 + 2 * frame + 2 * 2200 + quiet_cycles));
    configure_dut();
    send_frames(2);
endtask
```

`configure_dut()` and `send_frames()` are the bench's own tasks. The test calls `fix()` before it configures and sends, so the budget covers the configuration too.

The bound is in clocks rather than simulated time because the clock period differs per project and is not known at `build_phase`. A clock that stops stops the count, so if the first clock stops, only `+UVM_TIMEOUT` ends the run.

A test that keeps sending raises a derived budget each time the count reaches it. One that sends `r` items per clock moves the budget by `factor * r` clocks for each clock that passes. With `factor * r` of 1 or more, the count never reaches the budget, and the progress rules or `+UVM_TIMEOUT` bound the run. Below 1, the budget converges, and the run times out after about `floor / (1 - factor * r)` clocks: a test that sends an item every 40 clocks under the defaults times out after about 5000000.

`+UVM_TIMEOUT` and `uvm_top.set_timeout()` keep working as a second limit, in simulated time, and whichever comes first ends the run. UVM's limit raises a `PH_TIMEOUT` `UVM_FATAL`, which skips `check_phase`, so keep it above the run timeout. Its default is 9200 s of simulated time. A slow clock with a large budget reaches it first: at 1 MHz, any budget above 9.2e9 clocks.

The joint stall rule (section 9.10) reports a run in which nothing moves while a master holds an item, after `joint_stall_cycles`, 200000 by default. In paired mode it also ends the run, since every master's lanes die and the sequences complete. In single mode no lane dies, so the run timeout ends the run at the stall, as it would at its budget, with no `A2C_RUN_TIMEOUT` (section 9.10). The run timeout also covers the hangs the rule cannot see: a port that waits while another keeps moving, a rule turned off, and an objection no port holds. It declares no lane dead. Ending the run phase prematurely skips the paired-mode drain, or stops a drain that is running, so each replay log reports the state it was in at the timeout. UVM clears the objections still raised with one `OBJTN_CLEAR` `UVM_WARNING` per phase.

A test that does not extend the generated base test has no run timeout.

#### Real-time checks

The progress rules catch a design that stops. `a2c_rt_checker` catches one that keeps moving but too slowly for its stream, such as a pixel pipeline that drops behind its source, or a packet engine that stalls inside a packet. It checks one output port of the DUT against one input port with three rules. Each rule is off at 0, and each bound is the first value that fails, as for `lane_skew_cycles`.

| Rule | Knob | Fails when |
| :--- | :--- | :--- |
| gap | `rt_gap_cycles` | an open output unit, from its first transfer to its end, has this many charged clocks since its last beat: clocks with the sink ready and no beat offered that no starvation credit explains, or on which the DUT has sat on input it could have delivered |
| deadline | `rt_lag_cycles` | output unit k has not ended this many clocks after its anchor input unit ended, less its hold credit |
| refusal | `rt_refusal_cycles` | within one input unit the DUT refuses this many clocks of offered input that no hold credit explains |

Together the deadline and refusal rules check throughput. A DUT that takes all its input but falls behind lags more each unit, and one that keeps up only by back-pressuring its source refuses. The deadline is anchored at the end of the input unit, not its start, so the testbench's pacing, blanking and paired-mode throttling never cause a failure, and a pipeline's fill counts once, inside the bound.

**Window and credits.** W, the window, is `rt_latency_cycles`, or `rt_lag_cycles` when that is 0: the most clocks the DUT takes from a cause to its effect, a beat accepted to the beat offered, input withheld to the output idling, the sink refusing to the input refused. W counts free clocks only, those on which the testbench held nothing up, so a hold never ages a credit. The testbench *withholds* on a clock when the input offers no beat, or a further source (`connect_source()`, below) makes the DUT wait. Each such clock, per source, is one *starvation credit*. An input credit belongs to the input unit it delays, the open one or, between units, the next, and can explain only an output unit whose anchor is that unit or a later one, so idle the testbench gives the next input unit while the output still drains this one is never credited to this one. The testbench *holds the DUT up* on a clock when the sink refuses an offered beat or a further source withholds. Each such clock is one *hold credit*. A clock with ready low and no beat offered is not a hold.

**Invariants.** The rules rest on these, which the checker keeps on every clock:

1. A credit explains at most one clock, and only a clock within W of it, since one withheld or refused clock delays one beat by one slot.
2. Credits pair with clocks earliest credit first. For clocks that each take a credit from the W before them, this pairs as many clocks as any pairing can, so a rule never charges a clock that some assignment of credits would explain.
3. Only an open output unit's idle clocks take starvation credits. Idle between units, such as a pipeline filling, is never charged, and leaves its credits for the open unit.
4. An idle clock is charged regardless of credits when the DUT has had work and room for it: it accepted a beat of a unit the open output unit needs, after that unit's last beat, and W idle clocks have passed since that beat and since any further source last withheld.
5. The hold debt is how far holds have put the output behind. It grows by each hold clock and falls by each input clock with no transfer, withheld or refused: on such a clock either the output caught up one clock or the hold moved the input end instead. It clears when the output idles with its sink ready and no further source has withheld within W, since the DUT had caught up. Output unit k's hold credit is the debt when its anchor input unit ended plus the hold clocks since, or, after such an idle, the hold clocks since the idle. A DUT that idles with a backlog, as a pipeline bubble does, clears the debt, and the lag reads high. Input gaps already inside the DUT when a hold begins are not counted against it, so the lag can read low by at most the input clocks with no transfer in the DUT's latency before a hold.
6. A reset of the output clock's domain abandons every open unit, pending deadline, credit and debt. Units pair afresh from the release, and the summary counts the resets and the units they abandoned.

**The class of DUT.** The rules suit a streaming DUT that processes beats in order, one output beat per input beat within the unit pairing below, and that offers each beat within W free clocks of when it could first work on it: once accepted, once its whole input unit has arrived if it stores and forwards a unit, and while no further source withholds. It refuses input only when its sink or a further source has held it up within W. Such a DUT raises no error with `rt_gap_cycles` 1 or more, `rt_refusal_cycles` 1, `rt_latency_cycles` its latency and `rt_lag_cycles` its latency plus, for store and forward, one less than the beats of its input unit, plus 1. Each of its idle clocks inside an open unit has its own cause within W, a withheld clock or a further source's, and that causal pairing is one invariant 2 can find. A DUT that changes rate inside a unit, reorders, or waits on a port the checker cannot see is outside the class: it needs looser bounds, measured as in step 3 of the wiring steps below. The rules detect stalls within the bounds that follow and check throughput; they do not prove a latency.

**Detection bound.** A DUT that stops offering beats of an open output unit from clock s is reported as `A2C_RT_GAP` by the first clock c that meets either of:

- the idle clocks with the sink ready in s to c, less the starvation credits that could still pair with them, those alive at s and those earned since, reach `rt_gap_cycles` (G);
- the idle clocks after the later of the first beat the DUT accepts for the open unit from s on and the last further-source withholding reach W + G - 1.

With the sink always ready and no further source, that is at most s + d + W + G - 1, where d is the clocks from s on which the input withheld a unit the open output unit needs before it offered one. A further source that withholds through the stall can postpone the report while it withholds: the DUT may be waiting on it.

**Self-test.** `a2c_rt_ref_lb_tests.svh` checks the rules against a reference pipeline with no pins that steps on the loopback clock: random latency 1 to 12, buffer depth, combinational or registered ready, store and forward, unit merges and splits, source gaps and blanking, sink ready rate and hold bursts, and a further source in either form that blocks processing. Each conforming pipeline must raise no real-time error at the tightest bounds above, and each injected stall must be reported within its bound, worked out from the trial's own trace. `rt_ref_random_test` runs 96 such trials at once and `rt_ref_reset_test` 48 conforming ones through three resets.

`A2C_RT_DEADLINE` and the late-unit info print the hold credit and when the output last idled with its sink ready. `A2C_RT_GAP` prints how many of the idle clocks since the last beat starvation credits explained and, when the work rule charged the clock, how long the DUT has held input of the unit.

A unit is a run of beats that a rule marks: a frame, a line or a packet. `a2c_unit_rule #(T)` decides it. A subclass returns the end marker from `is_unit_end(t)`, such as `t.data.last`, and `ends_per_unit` closes the unit at the n-th marker. `a2c_beat_count_rule #(T)` makes every `beats_per_unit` beats a unit, for a stream that marks no end. `axi4_stream_tlast_rule` ends a unit at `tlast`. A per-line contract beside a per-frame one takes a second checker.

The checker pairs units one to one by default. `in_units_per_out` above 1 anchors output unit k at input unit `(k + 1) * in_units_per_out - 1`, for a decimator, and `out_units_per_in` above 1 anchors `out_units_per_in` output units at one input unit, for a splitter. A design with any other pairing overrides `anchor(k)`, which must not decrease and must grow without bound: an input unit end creates a deadline for every output unit whose anchor is at or below it, so a constant anchor never stops creating them. An output unit that ends before its anchor input unit has ended raises `A2C_RT_UNIT`, because the pairing does not match the design.

**Monitors measure, the checker judges.** The rdy_vld, axi4_stream and push_ack monitors implement `a2c_flow_counts`: from the reset release they count the clocks sampled, offered, ready and transferred, in the same step as the item they report. The checker counts the rising edges of the output port's clock and reads both monitors on each. A stopped clock holds every count still. An input on another clock is read on the output clock's edges, which is exact to one clock. On push_ack a clock counts as ready when `ack` is high or `push` is low. **Further sources.** `connect_source(mon)` adds a port the DUT waits on, whose withheld clocks are starvation credits of every output unit and hold credits. A stream the testbench drives passes its `a2c_flow_counts` monitor and withholds on each clock it offers no beat. A responder's monitor implements `a2c_starvation_source`, `starvation_counts(samples, withheld)` and `starvation_port()`: pop_ack withholds on clocks with `pop` high and `ack` low, req_ack with `req` high and `ack` low, axi_read on clocks an offered AR is refused or a burst is open with no R beat, and axi_write on clocks an offered AW or W is refused. A posted write does not wait for B, so B is not counted. Memory has no handshake, so it never withholds and is not a source. Request-response interfaces have no real-time rule of their own yet.

**The source must not wait for ready.** The gap and refusal rules read a clock with valid high and ready low as a beat offered and refused. A source whose valid waits for ready offers nothing until the DUT is ready, so the refusal rule sees no refusal and the gap credit sees input the testbench withheld. The rdy_vld, axi4_stream and push_ack interface definitions forbid it in the AMBA wording: the source must not wait for ready before asserting valid, and holds valid and its data until the transfer completes. The UVM src drivers and SystemC BFMs keep to it (section 9.10). The checker relies on it for the DUT's output as well.

The project creates the checker in its `<block>_tb_env` and wires it in `connect_phase`. `connect_in()` and `connect_out()` take the agent's `mon`, and `connect_out()` also takes the output's `a2c_txn_counter` and the agent's `model_cmp`, which is null outside paired mode:

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

**The model and paired mode.** The model's timing is approximate, so on the model DUT the checker measures and raises nothing, and logs one `A2C_RT` info that says so. The generated tb sets `a2c_model_dut` for it. `rt_on_model` (`+a2c_rt_on_model=1`) judges the model too. In paired mode the checker judges the RTL lane, `agent.mon`, and never compares the two lanes' timing. Once a paired-mode master or the comparator declares the DUT lane dead, it stops judging, and its summary says when.

**Reports.** Each failure is a `UVM_ERROR` that does not stop the run. The first `max_reported`, 10 by default, are printed; `check_phase` counts the rest in one more `A2C_RT` error. A deadline raises `A2C_RT_DEADLINE` the clock it is reached, so a hang is reported at once, and the unit's late end adds an `A2C_RT_DEADLINE` info: `output unit <k>, reported late, ended <n> clocks after its deadline`. A slow design and a hung one therefore read differently. A unit whose deadline had not passed when the run ended raises nothing. Each rule reports once per unit. At `check_phase` each checker logs an `A2C_RT` summary at `UVM_LOW`: the units checked, the first, worst and last lag, the worst gap and refusal with their units, the input unit period, the share of input clocks the testbench withheld, and the units that completed late, never completed or were still pending. The worst values are also readable from a test through `worst_lag()`, `worst_gap()`, `worst_refusal()`, `units_checked()` and `failures_seen()`.

**The run timeout.** A checker rule counting toward its bound when a derived budget is reached is a progress rule like the others (property 1): the deferral names it, as in `the real-time deadline rule (rt_lag_cycles) of <port> (<checker>)`, and waits for its clocks left plus `clock_stop_cycles` + 1. A checker whose output clock has stopped is left out, as a lane rule is, because its counts hold still. A summary with units still pending carries the run timeout clause when the timeout ended the run.

**Wiring a checker into a project.** A project adds a checker in the user region of its `<block>_tb_env`, one per output stream whose timing is a contract. The steps:

1. Write a unit rule for the stream's natural unit, such as an end-of-packet flag or an end-of-frame flag, or use `a2c_beat_count_rule` or `axi4_stream_tlast_rule`.
2. Create the checker, set `in_rule` and `out_rule`, and connect it in `connect_phase` as shown above.
3. Run a passing test with the rules off and read the `A2C_RT` summary: the worst lag, gap and refusal. Set the bounds from those measurements with a stated margin, in the test's constructor through the `rt_*` knobs, and say in a comment what each bound guarantees.
4. Add a fire test that sets one bound below the measured value and expects exactly the failures that follow, such as one `A2C_RT_DEADLINE` per unit. Real RTL has no mutant hook, so this is what proves the checker is wired to the right ports and units; the loopback tests in `a2c_rt_checker_lb_tests.svh` cover each rule against a configurable pipeline.

A random test can turn on the gap rule alone as a stall detector.

Not yet built: a generated gap-only checker per output that needs no wiring, unit markers declared in YAML, and a request-to-response latency bound for pop_ack, req_ack, AXI, memory and Pro's `lmmi`.

#### Completion from the model lane

An output whose count depends on the data, such as a filter that drops items, has no count the test can declare without computing the result. A paired-mode run can take that count from the model instead. The base test member `expect_from_model` (`+a2c_expect_from_model=1`) sets the `bit` config key `a2c_expect_from_model` on every counter below the env in a paired-mode run, and the counter then needs no `expect_count()`:

- In paired mode every model lane transaction beyond the expected count raises the expected count of both lanes by one, so the model lane's count becomes the DUT lane's expectation. A DUT lane short of it, or beyond it, is an `A2C_TXN_COUNT` error naming the DUT lane, as for a declared count.
- `wait_for_count()` ends once both lanes have been quiet for the quiet window with nothing outstanding. A transaction on either lane starts the window again, and a model lane transaction the DUT lane has not matched sends the wait back to its deadline.
- A run with one DUT, `rtl` or `model`, has no model lane to take the count from. The base test's `build_phase` clears `expect_from_model` there, so a test that also runs in the `rtl_dut` group declares its counts when `expect_from_model` reads 0 after `super.build_phase()`. The generated fail test clears it in every run, so its smoke test declares them there too. A counter given `a2c_expect_from_model` without `dual` is an `A2C_CFG` error, since raising the count on each arrival would pass a DUT that delivered nothing.
- A count declared with `expect_count()` still adds to the expectation, so a test can declare the part of the output it knows.

The model lane's count is only as good as the model, and the quiet window is the only end of the model's output. Set `quiet_cycles` above the longest gap the design can leave in an output, counting its latency from the last input to the last output: a shorter window ends the wait while output is still due, and a model lane that pauses longer while the DUT lane is ahead has the DUT lane's lead reported as extra. `wait_for_count()` logs each lane's count at `UVM_LOW` with the quiet window that ended it, so a window too short for the design shows in the log. The comparator still pairs every item of the two lanes.

#### A reset during the test

A test pulses the block's resets with the base test's `reset_dut()`, which returns once every clock with a reset samples it released again. A test that waits on one clock calls `<clock>_vif.request_reset()` itself. The pulse goes through SystemC, which owns every clock and reset:

1. `request_reset()` raises the `a2c_clk_if`'s `reset_request`. The testbench module drives `uvm_reset_req` from the requests of the clocks that have a reset.
2. The wrapper's reset driver asserts each reset at the next rising edge of its clock and holds it while the request is raised. `request_reset()` drops the request at the first rising edge that samples the reset asserted.
3. Each reset is released `releaseCycles` rising edges of its clock after the request drops, as at time 0. `request_reset()` returns at the first rising edge that samples the release.

`uvm_reset_req` is one pin, so the pulse asserts every reset of the block, each on its own clock.

The model has no mid-run reset. A model or both snapshot ties `uvm_reset_req` low, and `reset_dut()` raises an `A2C_RESET` error naming `--uvmDut rtl` and returns without a pulse. A paired-mode test resets nothing, and a reset belongs in a single-mode test on the RTL.

The UVM components do not restart a phase at the reset. Each runs its run loop through `a2c_run_reset_aware()`: at the first rising edge that samples its domain's reset asserted, the edge where a reset-aware RTL flop first sees it, it kills the loop, calls `on_reset()` and starts the loop again, which waits for the release as at time 0. What each part abandons there:

| Part | At the reset |
| :--- | :--- |
| monitors (`a2c_monitor`) | publish no transfer at a sample point where the reset is asserted; the AXI monitors drop their open bursts and `lmmi`'s its pending read |
| lane drivers (`a2c_lane_driver`) | return the item they hold, or have fetched and not taken, with `item_done()`, after `abandon_held()` answers it for a protocol whose sequence waits for a response or reads a status, set the lane counts to 0, empty the replay log and clear the lane watchdog. A lane death stays declared. The pins go back to their reset values. The sequencer fetch runs in a process the reset does not kill, because UVM 1.2's sequencer takes the next `get_next_item()` after a killed one as a second call |
| AXI masters | return each open burst to its sequence with no beats through `put_response()`, and a burst held in its gap before its address went out the same way, and drop the queued addresses and W beats |
| `apb` master | completes a transfer the reset cut short with `slverr` set, so `apb_reg_adapter` gives the register layer `UVM_NOT_OK`, not `UVM_IS_OK` with the data the item was sent with. Pro's `lmmi` has no error response and no register adapter, so its item completes as it was sent |
| AXI slaves, `memory`, `external_reg` and `lmmi` drivers | drop their queued bursts and responses; a `memory` read the sequence waits for is answered with data 0, also one the master held in its gap or its enable clock |
| `raw` and `status` drivers | keep the level they hold |
| counters (`a2c_txn_counter`) | lower each lane's expected count to the count it has received, and clear a reported shortfall. A test declares the traffic after the release with `expect_count()` |
| comparators | drop each lane's unpaired items and close any midstream window. `get_pairs()` keeps counting the pairs compared before the reset. A status comparator keeps the latest value of each lane, a level the reset does not end |
| replay logs, lane watchdogs | start empty, with nothing owed by either lane |
| real-time checkers | abandon every open unit, as rule 6 of "Real-time checks" says |
| register model (`env.regmodel`) | goes back to its reset values: `reset_dut()` calls `env.regmodel.reset()` after the release. A test that pulses one clock's reset with `request_reset()` calls it itself |

Each component watches the reset of its own port's clock. The base test's run timeout and the paired-mode drain do not restart. An agent not built on `a2c_monitor` and `a2c_lane_driver`, such as a project's own, gets none of this: it implements `a2c_reset_aware` and runs its loops through `a2c_run_reset_aware()` itself.

#### The paired-mode end-of-test drain

In paired mode every `A2C_DST` agent that answers the DUT (push_ack, notify_ack, req_ack, pop_ack, memory, external_reg, the apb slave, the AXI slaves and Pro's `lmmi`) serves both lanes from one model. The DUT lane applies each transaction and records its response in the driver's `a2c_replay_log`; the model lane replays the responses in order. An AXI slave that reorders records which burst the DUT lane answered, and the model lane answers the same burst, matched by ID and its arrival index within the ID, so both lanes complete bursts in one order (section 9.10). The model lane often trails the DUT lane, so when the run phase's last objection drops, `a2c_replay_drain` holds the run phase until the model lanes catch up. It watches each log on the log's own clock:

- **Settle.** A log settles once both lanes have been idle for `drain_quiet_cycles` clocks in a row: no lane inside a transaction or starting one, no recorded response waiting for the model lane, and the model lane not waiting for one. The drain ends when every log has settled or been given up.
- **Cut.** A log not settled at `drain_deadline_cycles`, whose DUT lane started a transaction within its last `drain_quiet_cycles` clocks, is traffic that never pauses. The drain cuts it after the transactions the DUT lane has started, and both lanes have `drain_catchup_cycles` clocks to complete them. The transactions after the cut go unchecked on both lanes. `drain_catchup_cycles` defaults to the deadline, so a cut whose lanes never complete it takes up to twice the deadline to report. Lower the catch-up to fail sooner.
  - The comparator keeps the DUT lane's first `cut_at` completions and holds back the rest. Of each key it keeps as many model lane completions as those carry with that key, so the lanes may complete different keys in different orders across a cut. Without a key it keeps the model lane's first `cut_at`, so a responder whose lanes complete in different orders needs a keyed comparator.
  - With `reorder`, the first `cut_at` completions are not the first `cut_at` requests, so the counts `A2C_CUT` gives are approximate.
- **Re-cut.** A test may resume the run phase after a drain, by raising an objection in `phase_ready_to_end()`. The next drain undoes the earlier cuts and starts only if a lane has started a transaction since. A log cut before whose DUT lane has not paused for `drain_quiet_cycles` clocks since is cut again on the first clock.
- **Give-up.** Any other log not settled at its deadline is given up with an `A2C_DRAIN` warning, and its `check_phase` reports what the lanes still owe.
- **Clock stop.** A clock with no rising edge for `clock_stop_cycles` periods and a half has stopped. Its log settles if it is idle and not cut, and is given up otherwise. A settled log is watched again if its clock runs again; a given-up one is not. The steady period changes only when three intervals in a row agree within an eighth. Once a clock has one, neither a gated clock's gap nor a single runt pulse changes it, and a clock that slows by more than the stop limit in one step reads as stopped once. A clock gated in short bursts at uneven gaps may never have three agreeing intervals; until it does, its period is the shortest interval seen, and a runt in that time shortens its stop limit. Four rising edges whose three intervals agree set the period, so a burst of evenly spaced glitches can set a steady period of the glitch spacing. The real clock's next edge then reads as a stop unless `clock_stop_cycles` and a half exceeds the clock period divided by the glitch spacing. 2 or more covers runts near half the period.

A model lane whose master withdraws a request before the DUT lane has recorded the response it waits for, which the lane's monitor reports as `A2C_HOLD`, gets no ack for it. The push_ack, notify_ack, req_ack, pop_ack and Pro `lmmi` responders count no transaction for it and stop waiting for the record, so the drain does not wait on it. An `lmmi` request withdrawn after the model lane raised `lmmi_ready` leaves the response held, which `check_phase` reports as `A2C_REPLAY`.

A hand-written test that raises objections only in `main_phase()` drains too: UVM 1.2 calls the run phase's `phase_ready_to_end()` once the runtime phases have ended, which takes no time when the later ones hold no objection.

A `UVM_PASSIVE` agent can watch a paired-mode port beside the agent that drives it, on the same `vif` and `model_vif`, for example the agent of a reused block env inside a top env. It builds its monitors and `model_cmp` and no driver, so it sees neither a lane's death nor the drain's cut by itself. Left alone, its monitors would report the dead lane's open transfers as `A2C_PROTO` errors, and its `model_cmp` would report the pairs past a cut or a death as `A2C_MODEL_CMP` errors. The agents meet in `a2c_pin_registry`, one table per virtual interface type keyed by the virtual interface handle of each pin set, so the link needs no component path. The one condition is that the passive agent's `vif` and `model_vif` are the interface instances the active agent has: a second interface instance on the same nets, such as one a block env `bind`s into the block, is a different handle and does not match. In `connect_phase` a passive agent adds its `model_cmp` under `vif`, and a passive AXI agent also adds its monitor under `vif` and its `model_mon` under `model_vif`. The active agent marks the entry under its `vif` as its own. The active agent's replay log cuts and uncuts every `model_cmp` registered under its `vif`, and a paired-mode master that declares a lane dead (section 9.10) tells every monitor registered under that lane's pin set and every `model_cmp` registered under `vif`. In `end_of_elaboration_phase` a passive AXI or `lmmi` monitor takes the replay log of the active responder on its pin set, so it reports transfers left open after a cut as info, as the active agent's monitor does. With no such log the monitor keeps any `replay` a hand-written env gave it.

A passive paired-mode agent whose `vif` no active agent has marked reports it in `end_of_elaboration_phase` with one `UVM_LOW` `A2C_PASSIVE` info from the agent that names the port and points at its `cfg.vif`, and then runs as before. That is expected on a port no agent drives, such as an internal port of a top design. Where an active agent does drive the port, the info means the two agents have different interface instances, and the passive agent's `model_cmp` will report the pairs past a cut or a death as `A2C_MODEL_CMP` errors. The passive agents that report it are those that can learn of a cut or a death: the `A2C_DST` agents of the handshake families, memory and external_reg, and the req_ack, pop_ack, apb, Pro's `lmmi` and AXI agents in either role.

The registry is a global pool, the role `uvm_pool` plays in UVM, keyed by pin set. It is not a `uvm_pool`, because an associative array cannot take a virtual interface as its index: a virtual interface has `==` and no ordering. It is not analysis-port wiring either. A death and a cut are control events, not transactions, and a reused block env shares no component path with the top env through which to connect ports.

A hand-written paired-mode responder joins the drain by giving its `a2c_replay_log` a `clk_vif` and an `a2c_replay_lanes` implementation, as the built-in drivers do; the log registers itself with the drain at `start_of_simulation_phase`. A responder whose comparator holds pairs back at a cut implements `cut()` and `uncut()` on it. A passive agent's comparator is cut with the active agent's, so a factory override of a passive agent's `model_cmp` must implement them too. The base comparator's `cut()` stops the run with an `A2C_CFG` fatal; `a2c_in_order_comparator` has both, keyed by `key()` or not. Its `lane_starts()` and `lane_busy()` must change away from the rising edge of the log's `clk_vif`, at the falling edge or the drive point, as the built-in drivers do. The drain reads them at the rising edge. A driver that counts in an `@(posedge clk)` process races it, so the drain can end in that time step before the count moves and leave a false `A2C_REPLAY`.

| Member of `<block>_base_test` | Plusarg | Default |
| :--- | :--- | :--- |
| `drain_quiet_cycles` | `+a2c_drain_quiet_cycles=<n>` | `quiet_cycles` (1000) |
| `drain_deadline_cycles` | `+a2c_drain_deadline_cycles=<n>` | `output_deadline_cycles` (200000) |
| `drain_catchup_cycles` | `+a2c_drain_catchup_cycles=<n>` | each log's `drain_deadline_cycles` |
| `clock_stop_cycles` | `+a2c_clock_stop_cycles=<n>` | 1000 |
| `drain_cut_expected` | `+a2c_drain_cut_expected=1` | 0 |
| `lane_skew_cycles` | `+a2c_lane_skew_cycles=<n>` | the paired-mode master's own 200000; 0 turns the bound off |
| `lone_lane_cycles` | `+a2c_lone_lane_cycles=<n>` | the paired-mode master's own 200000; 0 turns the rule off |
| `joint_stall_cycles` | `+a2c_joint_stall_cycles=<n>` | the master's own 200000, in either mode; 0 turns the rule off |
| `model_throttle_cycles` | `+a2c_model_throttle_cycles=<n>` | the paired-mode master's own 1; 0 turns the rule off |
| `no_stimulus_expected` | `+a2c_no_stimulus_expected=1` | 0; set, it also sets `a2c_allow_no_pairs` on `env*` (section 9.12) |
| `run_timeout_cycles`, `run_timeout_floor_cycles`, `run_timeout_factor` | `+a2c_run_timeout_cycles=<n>`, `+a2c_run_timeout_floor_cycles=<n>`, `+a2c_run_timeout_factor=<n>` | a budget derived from the test's work; see "The run timeout" above |
| `rt_gap_cycles`, `rt_lag_cycles`, `rt_refusal_cycles` | `+a2c_rt_gap_cycles=<n>`, `+a2c_rt_lag_cycles=<n>`, `+a2c_rt_refusal_cycles=<n>` | -1, which sets nothing: every checker's rule stays off; see "Real-time checks" above |
| `rt_latency_cycles` | `+a2c_rt_latency_cycles=<n>` | -1; a checker left at 0 takes its lag bound as the starvation credit window |
| `rt_on_model` | `+a2c_rt_on_model=1` | -1; the checkers only measure on the model DUT |
| `expect_from_model` | `+a2c_expect_from_model=1` | 0; every output count is declared with `expect_count()`. Cleared in a run with one DUT. See "Completion from the model lane" above |

A test sets its own values in its constructor and the plusargs override them. The three drain cycle counts, `lane_skew_cycles`, `lone_lane_cycles`, `joint_stall_cycles` and `model_throttle_cycles` start at -1, which takes the default. The last four are not drain knobs. `lane_skew_cycles` bounds how many clocks one lane of a master in paired mode may trail the other before the master declares it dead, `lone_lane_cycles` how many clocks the one lane left after a death may go without progress, `joint_stall_cycles` how many clocks a lane may wait while no port anywhere makes a handshake, and `model_throttle_cycles` after how many clocks in a row of the model lane alone holding a master's next item back the master reports it (section 9.10). `build_phase` hands each to the env as `a2c_lane_skew_cycles`, `a2c_lone_lane_cycles`, `a2c_joint_stall_cycles` or `a2c_model_throttle_cycles` when it is 0 or more; left at -1 it sets nothing, and the master keeps its own default, as under a hand-written env. `no_stimulus_expected` is not a drain knob either: at `check_phase` a run whose input agents sent no item and whose output counters were declared no transaction raises `A2C_NO_STIMULUS`, as the scaffolded `<block>_smoke_test` does until its `run_body()` sends stimulus, unless the flag is set. On a block with an input besides its register bus, register writes alone leave the data path idle, so the check counts the other inputs only, through the base test's `data_stimulus_sent()`; on a block whose only input is its register bus, it counts that bus. The flag also sets `a2c_allow_no_pairs` on `env*`, since a run meant to send nothing compares nothing. The base test counts the items through `a2c_items_sent`: from each input agent's `sqr`, or, for a status input, which has no sequencer, the values its driver applied from `cfg.value` that differ from the one before, counting from the default 0. A test whose stimulus bypasses both also needs an `expect_count()` or the flag. An input agent with neither a sequencer of its item type nor a driver that counts (`a2c_items_driven`) is an `A2C_CFG` error. The warning says only what the base test counted; a paired-mode comparator or a check of the test's own may still have run. To give one log its own value, a test sets `a2c_drain_quiet_cycles`, `a2c_drain_deadline_cycles`, `a2c_drain_catchup_cycles`, `a2c_clock_stop_cycles` or `a2c_drain_cut_expected` on the log's path in its `build_phase`, after `super.build_phase()`. The log reads each as `int unsigned`, `int` or `uvm_config_int`, and the flag also as `bit`; `+uvm_set_config_int` on the command line works the same way. The type does not change which value wins. The log takes the entry `uvm_config_db` would pick if every entry had one type: the highest precedence, which in `build_phase` is the setter nearest the top, and of those the last set. So a hand-written env's `int` default does not override the base test's `int unsigned` values, and a later set for one port overrides an earlier blanket one. A winning entry of any other type, such as `longint unsigned` or `string`, is skipped with an `A2C_CFG` warning, and the knob takes the best entry of an accepted type, so the stray set costs only itself. The warning gives the value the knob takes. The drain reads these entries through `uvm_resource_pool`, not `uvm_config_db::get()`, so `+UVM_CONFIG_DB_TRACE` does not show its reads.

Section 9.17 lists the messages of the drain, the lane rules, the run timeout and the real-time checker, with what to change for each.

`<block>_fail_test extends <block>_smoke_test` is a self-checking negative test of the counters. After `super.run_body()` it calls `expect_count(missing_count)` on the first output counter, so that output owes more transactions than the DUT sends. `missing_count` defaults to 1 and `+a2c_fail_missing_count=<n>` sets it. An `a2c_error_demoter` turns each `A2C_TXN_COUNT` `UVM_ERROR` into `UVM_INFO` and counts it. In `report_phase` the test raises `A2C_FAIL_TEST` as a `UVM_ERROR` unless exactly one was demoted, the counter's lane ends exactly `missing_count` short, and no other `UVM_ERROR` or `UVM_FATAL` was raised. In paired mode the counter holds both lanes to the count, so the test expects one demoted `A2C_TXN_COUNT` per lane and each lane `missing_count` short. It sets `a2c_rt_off` on `env*`, which wins over the `rt_*` knobs, their plusargs and `set_limits()`, so a missing transaction never also fails a real-time rule. In a block with an input port it also raises `A2C_FAIL_TEST` when `data_stimulus_sent()` is 0, because a smoke test that sends nothing leaves the output short with a dead data path too; a smoke test that only programs registers sends nothing on the data path. The fail test clears `expect_from_model` and its config key `a2c_expect_from_model` after `super.build_phase()`, since in paired mode the model lane's first item would absorb the missing count, so the smoke test declares its counts as it does in a run with one DUT. A block with no counted output gets no fail test.

`<block>_model_mismatch_test extends <block>_smoke_test` is the self-checking negative test of the paired-mode compare. It calls `inject_mismatch(mismatch_at)` on the `model_cmp` of the first counted output's agent, so that pair reports a mismatch whatever its items hold. `mismatch_at` defaults to 1 and `+a2c_model_mismatch_at=<n>` sets it. An `a2c_error_demoter` demotes only the `A2C_MODEL_CMP` error whose text carries `(injected mismatch)`, so a real mismatch stays an error. In `report_phase` the test raises `A2C_MISMATCH_TEST` as a `UVM_ERROR` unless exactly one injected report was demoted, the comparator compared at least `mismatch_at` pairs, and nothing else raised a `UVM_ERROR` or `UVM_FATAL`. Outside paired mode it stops in `connect_phase` with an `A2C_CFG` `UVM_FATAL`. Only a block with a model and a counted output gets it.

`<block>_rt_fire_test extends <block>_smoke_test` proves the wiring of the env's real-time checkers. It sets `rt_lag_cycles` to 1, below the lag of any DUT that registers its output, so every output unit a checker pairs with an input unit misses its deadline once, and an `a2c_error_demoter` demotes and counts each `A2C_RT_DEADLINE`. It looks at the `a2c_rt_checker` components under `env` that are not off, and at `start_of_simulation_phase` sets their `max_reported` to the largest value, so every failure prints. In `report_phase` it raises `A2C_RT_FIRE` as a `UVM_ERROR` when there is no such checker, when one paired no unit or did not fail each unit it paired once (`units_checked()`, `failures_seen()`), or when the demoted count is not the units of the checkers that judge (`judges()`): none on the model DUT unless `rt_on_model` is set. A block with no counted output gets no rt-fire test. A block whose env holds no checker gets the test too, and it fails there.

`a2c_reg_test #(BASE)` is a block's register test, extended once as `<block>_reg_test` with the generated base test as `BASE`. It sets `no_stimulus_expected` and its `run_body()` starts `a2c_reg_access_seq` on `env.regmodel`. The sequence runs `uvm_reg_hw_reset_seq`, then an aliasing pass, then `uvm_reg_bit_bash_seq`. The aliasing pass writes each register whose fields are all `RW`, in a map that grants `RW`, in turn with the complement of the value it holds, and after each write reads back every register whose fields are all `RW` or `RO` and none volatile, the written one expecting its new value and the others the values they held. Neither UVM sequence writes one register and reads another, so the pass catches two registers that decode to one word, whatever their widths. A register with `NO_REG_TESTS` set is left out, as the UVM sequences leave it out. Its reads grow with the square of the number of registers it covers. A test with checks of its own overrides `run_body()` around `super.run_body()`.

The test package reaches the build through the manifest, as `A2C_UVM_TEST_SV_<top>`. A project that needs more SV files adds them by its own means.

### 9.7 Building and running

`USE_UVM=1` with `USE_XCELIUM=1` or `USE_VCS=1` includes `include/make/a2c-uvm.mk`. It stops make without one of the two, and with `VL_DUT=` empty. `VL_DUT` compiles the block's RTL into the snapshot, which every UVM snapshot needs, because the testbench module instantiates the RTL in its rtl branch.

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `UVM_TOP` | `A2C_UVM_DEFAULT_TOP_<HDL_TOP_MODULE>` | the testbench top's stem, `<block>_<variant>` or `<block>` |
| `UVM_DUT` | the first of `A2C_UVM_DUTS_<top>`: `model`, or `rtl` for a block with no model | the DUT the snapshot holds. `rtl` adds `+define+A2C_UVM_RTL_DUT`. `both` adds `+define+A2C_UVM_BOTH_DUT` and builds paired mode, the RTL beside the model as its reference (section 9.12). A block with no model has neither `model` nor `both` |
| `UVM_TEST` | empty | the `+UVM_TESTNAME` the run script adds when a run names none |
| `UVM_TOPOLOGIES` | `<UVM_TOP>:<each DUT of its block>` | what `uvm_snapshots` builds: space-separated `<top>:<dut>[,<dut>]` entries |
| `UVM_COV` | empty | `1` builds the snapshot for coverage and has each run write its own coverage database (section 9.16) |

`make gen` checks `UVM_TOP` and `UVM_DUT` against the manifest and names the valid values. Under `USE_UVM` the flow sets `VL_INST` empty, `DUT_TOPOLOGY` to `uvm_<UVM_TOP>_<UVM_DUT>` and `DUT_ELAB_ARGS` to `<block>_uvm --uvmDut <dut> --uvmTop <top>`. It adds `common/systemVerilog/uvm/a2c_uvm.f`, then `-F` of each builder layer list in `A2C_LAYER_UVM_F_FILES`, and the defines `A2C_UVM_PKG=<variant package>` and, for `rtl`, `A2C_UVM_RTL_DUT` or, for `both`, `A2C_UVM_BOTH_DUT` to the HDL arguments. It appends the variant package, the test package and the testbench module to `A2C_SV_FILES`, after `rtl.f`, and makes them, the `.sv` and `.svh` files of the UVM library, the agent packages, each layer list and each file a layer list names prerequisites of the snapshot. A layer list holds file paths only, relative to its own directory. The RTL side's files, those that `a2c.f`, the HDL hooks and `rtl.f` name and every `.sv` and `.svh` in their include directories, are prerequisites too, with the gaps section 10.4 lists. It adds `$(A2C_UVM_SRC_DIRS)` to the C++ sources, and on VCS `common/systemc/uvm/uvmVcsElabStub.cpp` too.

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
- Both: a seed of `random` is drawn once, by the script, so `sc_main` and the SV solver get the same value. The script adds `+a2c_seed=<seed>` when the run gives one, and `+a2c_rerun=cd <directory> && <script> <arguments>`, the command that repeats the run with the seed drawn. The base test prints them as `A2C_RERUN` (section 9.14).
- Both: under `WAVES=1` the run writes waves in the directory it starts from: `waves.shm` under Xcelium, `waves.fsdb` under VCS (section 9.14).

Xcelium's `-svseed` reads the same three forms as `std::stoul` with base 0, so the Xcelium script passes the value through. A malformed or over-32-bit `-svseed` value only warns there (`SVSEEDW`, seed 1). A probe on Xcelium 26.03 showed `010` giving seed 8, `0x1f` and `0X1F` giving 31, and `08`, `1f` and 4294967296 warning. `sc_main` still parses `--seed` itself, and stops with exit status 2 on a value with no leading digits. A seed never gives the same stimulus on both vendors.

A run names its testbench, DUT and top the way it does at elaboration. `dutRun.py` maps a test with `--uvmDut <dut> --uvmTop <top>` to `<base>_uvm_<top>_<dut>` and stops with an error when only one of the two is given. The config rejects a `--uvmDut` its block does not have and a `--uvmTop` that is not one of its block's stems, and the wrapper fails a run whose `--uvmDut` does not match the snapshot (section 9.8). From `examples/uvmMem/rundir`:

```
../../../dutRun.py build_xrun/run uvmMem_uvm --seed 7 --verbosity=low \
    --uvmTop uvmMem --uvmDut rtl +UVM_TESTNAME=uvmMem_smoke_test
```

A regression file builds with `make -j8 USE_UVM=1 USE_<VENDOR>=1 uvm_snapshots` and runs `../builder/dutRun.py build_xrun/run <block>_uvm` or `build/run <block>_uvm`, with `--uvmTop` in the shared arguments, `--uvmDut` per group and `+UVM_TESTNAME` per test entry. In a base example the runner is `../../../dutRun.py`. `examples/uvmMem/rundir/regr_uvmMem_uvm_xcelium.json` and `regr_uvmMem_uvm_vcs.json` are the reference. Each has three groups, `model_dut`, `rtl_dut` and `both_dut`, with `--uvmDut model`, `rtl` or `both` and the labels `mdl`, `hdl` and `both`; the `both_dut` group runs the paired-mode snapshot and adds `<block>_model_mismatch_test`. Each group runs a smoke, a random and a fail test, the random test three times with seed `random`, and `both_dut` runs the smoke and fail tests again with `+a2c_expect_from_model=1`. List the rule files in this order: `config/regrRules/uvm.json` by its relative path from the rundir, then any project rule file, then `default.json` and the vendor file. The JUnit report of `regrLauncher.py` keeps only the first failure, so the order decides which failure it shows. `uvm.json` ships in base, and projects reference it in place. It fails a run on a `UVM_ERROR` or `UVM_FATAL` report, a non-zero summary count, a log with no UVM report summary, or the `A2C_SEED_REPRO FAIL:` verdict of `seedRepro.py`.

#### Seed reproducibility

A test run twice with one seed on one simulator must give the same transactions on every port. `seedRepro.py`, beside `regrLauncher.py` in base and `../builder/seedRepro.py` from a project's rundir, checks it. It runs one command twice, echoes both runs' output to stdout as it arrives, each after an `A2C_SEED_REPRO run <n>: <command>` line, and ends with an `A2C_SEED_REPRO PASS:` or `A2C_SEED_REPRO FAIL:` line that names the reason. A run passes when it exits with status 0, prints a UVM report summary, and has no `UVM_ERROR` or `UVM_FATAL` report and no non-zero count of either, before or after the summary. It fails when it prints no `A2C_DIGEST` line, or when every digest it prints counts no transaction, because such digests match whatever the seed; one empty port among others is fine. It also fails when a port with `paired=1` reports both lanes with different item counts: its comparator pairs every item, so a correct run counts the same on both lanes, and a difference is the sign of a lane whose monitor feeds no digest. A port with `paired=0` is left out of this rule, since its lanes may count apart in a correct run. The command passes, with exit status 0, when both runs pass and the two runs' `A2C_DIGEST` lines are the same, in the same order.

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

The group's `timeout` is twice the file's, because each entry runs twice. Both runs' output lands in the launcher's one log for the entry, so the rule files check both, and the retention policy keeps or drops both. A `FAIL` verdict exits with status 1, and `uvm.json`'s `seed_repro_fail` filter matches its line, so the JUnit report names the reason, such as `[seed_repro_fail] seedRepro.py: the same seed gave different digests`. The filter is the last in `uvm.json`, so a run inside the entry that matched another `uvm.json` filter, a `UVM_ERROR` or `UVM_FATAL` report, a non-zero summary count or a missing summary, is named instead. It comes before every filter of `default.json` and the vendor file, so in a `seed_repro` entry the verdict outranks them: a run that died on a `Q_ASSERT`, a SystemC exception or a simulator error shows as the verdict's reason, such as `seedRepro.py: run 1 exited with status 1`, and the run's log holds the specific one. Only when both runs pass does the runner print each run's digest lines again as `A2C_SEED_REPRO run <n> A2C_DIGEST ...`, so the two can be compared in the log. Reproduction is per simulator. The same seed gives different stimulus on Xcelium and VCS, so a `seed_repro` entry never compares across them.

### 9.8 Completion and the verdict

The testbench module clears `uvm_root`'s `finish_on_completion`, so `run_test()` returns after the report phase. It then writes the `UVM_ERROR` plus `UVM_FATAL` count to `uvm_errors` and raises `uvm_done` one clock later. The wrapper's `uvm_watch` thread reads both pins, `rtl_dut` and `model_dut`: (0, 1) is the model snapshot, (1, 0) the rtl one and (1, 1) the both one. It fails the run with a reason through `errorCode::fail` when the count is not zero or the snapshot holds another DUT set than `--uvmDut` asks for, marks the run completed and casts the one end-of-test vote. Its `eot_thread` calls `sc_stop()`, because the testbench has no External to do it. The config's `final()` passes a completed run that nothing failed, and fails one where `uvm_done` never rose with `UVM testbench did not finish: uvm_done never rose`.

| Event | Verdict |
| :--- | :--- |
| `UVM_ERROR` | counted on `uvm_errors`; the wrapper fails the run with `UVM reported <n> UVM_ERROR/UVM_FATAL` |
| `UVM_FATAL` | `$finish` inside `run_test()`, so `uvm_done` never rises. Under Xcelium `sc_start` returns and `final()` fails the run. Under VCS the `$finish` exits through `main.cpp`'s `VcsSetExitFunc` handler, which fails the run with `simulation ended by $finish before the end of test` when nothing had set an exit code, and prints the recorded reason when something had. The handler acts from just before the zero-time `sc_start`, because a `UVM_FATAL` such as an unknown test name fires inside it |
| wrong snapshot | `--uvmDut <dut> does not match the snapshot: the run expects the <set>, and the SV testbench holds the <set>`, where each `<set>` is `model DUT`, `RTL DUT` or `model and RTL DUTs` |
| X or Z at an RTL port | section 9.4 |
| BFM contract break | the UVM config sets `bfmContractCheck::toUvm`, so the first break of each BFM check that section 9.11 lists, such as `SystemC stalled a backpressure: false producer`, waits in a queue. The testbench module takes the queue at every falling edge of the block's first clock through the DPI import `a2c_bfm_contract_break` (`common/systemc/bfmContractCheck.cpp`) and raises each break as an `A2C_BFM_CONTRACT` `UVM_ERROR`, so the UVM summary decides the run and a test can expect a break (below). A break still queued when `run_test()` returns fails the run from `final()` with `<n> BFM contract break(s) never reached UVM`. raw's missed-edge count is built warn-only and never queues, and the clock-paced report (section 9.11) is not a break and never queues. Other flows keep these checks as warnings, except `HDL lowered ready`, which fails the run in every flow (section 9.11) |
| `Q_ASSERT` | unchanged; the UVM report summary is missing, and `uvm.json` reports that too |

`try_sc_start` keeps a failure reason set during the run and appends the elapsed time to it. A passing run's summary is unchanged. `errorCode::fail` overwrites, so the summary shows the last failure recorded.

A test that provokes a break on purpose, such as an overrun of a `backpressure: false` input, expects it with `a2c_expected_error`, a component in `a2c_uvm_pkg`. Its fields `id`, `text` and `count` name the reports it expects: exactly `count` `UVM_ERROR`s with that ID whose message contains `text`, or any message when `text` is empty. It registers a `uvm_report_catcher` at `build_phase` that demotes the first `count` matches to `UVM_INFO`. A match beyond `count` stays a `UVM_ERROR`, and at `check_phase` any number other than `count` raises `A2C_EXPECTED_ERROR`, so a missing break fails the test as an extra one does. A break comes only from a BFM that exists, so a test sets `count` per DUT, for example 1 where the model runs and 0 on the RTL:

```systemverilog
bfm_break       = a2c_expected_error::type_id::create("bfm_break", this);   // build_phase
bfm_break.id    = "A2C_BFM_CONTRACT";
bfm_break.text  = "SystemC stalled a backpressure: false producer";
if (!uvm_config_db#(bit)::get(env, "", "a2c_model_dut", model_dut))        // connect_phase
    `uvm_error("A2C_CFG", "no a2c_model_dut config key")
bfm_break.count = (model_dut || env.dual_dut) ? 1 : 0;
```

`model_dut` is the `bit` config key `a2c_model_dut`, which the testbench module sets to 1 only when the model is the one DUT. The module sets it for `uvm_test_top.*`, so a test reads it through a child such as `env`. `env.dual_dut` is the env's copy of `a2c_dual_dut`, 1 when the run holds both DUTs.

The message starts with the BFM's instance path, so `text` can also pick one port's BFM.

The catcher counts only reports still at `UVM_ERROR` when it sees them, and keeps `UVM_LOG` on a report it demotes. Two `a2c_expected_error`s whose matches overlap therefore depend on order: the one whose catcher runs first takes the shared reports, and the other never counts them. Catchers run in the order `build_phase` registers them, which for siblings is the order of their names, so give the narrower one the earlier name.

### 9.9 Farm-only tests in base

Two tests need a four-state simulator with UVM and run only on the farm. Source the simulator setup, then run from any scratch directory:

| Command | Builds | Passes when |
| :--- | :--- | :--- |
| `common/systemVerilog/xcheck_test/run_xcheck_test.sh xcelium\|vcs [<tb.sv> <source>...]` | `xcheck_tb.sv` with the checker of each type in the script's `TYPES` into `./xcheck_<sim>`. `xz_count.c` stands in for `a2c_xz_fail` and counts each checker's reports. Given a testbench, the script builds it instead, after the sources that follow it, with the testbench file's stem as the top. A builder layer runs its own checker cases this way, for example Pro's `pro/common/systemVerilog/xcheck_test/lmmi_xcheck_tb.sv` | every case logs `XC_PASS`, and the number that pass equals `CASES` in `xcheck_tb.sv`. The cases cover qualified and unqualified X per type, every control signal, X before arming and during a later reset, a power-on X reset, one report per instance, the apb completion qualifiers, `rdata` only while `ack` for req_ack and pop_ack, memory `read_data` X after a read followed by a write of that address, a write elsewhere, a read, no access, or a reset, external_reg `wdata` only while `write` is non-zero, bound and unbound `tuser`, bound and unbound AXI ID and USER signals, and a reset released in delta cycles before the first edge |
| `common/systemVerilog/uvm/loopback/run_loopback.sh [--subset <name>] xcelium\|vcs [seed [<layer.f>...]]` | `a2c_uvm_loopback_tb.sv` with every agent package `a2c_uvm.f` lists and the `<type>_if.sv` beside each, into `./loopback_<sim>`. Each `<layer.f>` adds a builder layer's agent packages after `a2c_uvm.f`, the `<type>_if.sv` beside each, and the `*.sv` files in the `loopback/` directory beside the list, compiled after the testbench | every test logs `LB_PASS` with zero `UVM_ERROR` and `UVM_FATAL`. The tests are the classes each `*_lb_tests.svh` file registers with `` `uvm_component_utils `` under a name ending in `_test`. The script fails when a file registers none. With `--subset`, only the tests listed in `<name>.tests` run, and every loopback directory of the run, base's and each layer's, must hold that file; a listed name that no file registers fails the run. Then each `seed_repro_*` check runs `txn_digest_rv_test`, `txn_digest_er_test`, `txn_digest_axi_test`, `txn_digest_cut_test` or a test with no digest twice under `seedRepro.py` and must end with its verdict: the same seed matches; two seeds differ when the seed changes the data, only the timing, only the `external_reg` rdata levels, or only the AXI read data; two seeds on fixed stimulus fail; the same seed fails when one port's stream changes between the runs; a `paired=1` port whose lanes count different items fails, and a `paired=0` port whose lanes count different items passes, a status port or one whose in-order comparator a drain cut; and a test with no digest fails. Each check's log is `<check>.log` |

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

Base's checker test covers every base type, and Pro's `lmmi_xcheck_tb.sv` covers lmmi.

- `run_xcheck_test.sh` takes a testbench and the sources it needs. It builds the sources first and the testbench last, with the testbench file's stem as the top.
- `run_loopback.sh` takes the seed second and layer lists after it. The seed must come first: a list path in its place is read as the seed. The script never reads `A2C_LAYER_UVM_F_FILES`, because exporting that variable for it would make every later `make` in the same shell add Pro's list a second time. Pro's `a2cPro_uvm_loopback.sv` binds its interfaces into the testbench and runs the tests of `lmmi_lb_tests.svh`.

The loopback testbench includes every `*_lb_tests.svh` file in its directory: one per agent type, and one per base component or check, such as `no_backpressure_lb_tests.svh` and `a2c_expected_error_lb_tests.svh`. `run_loopback.sh` runs every `*_test` class those files register with `` `uvm_component_utils ``, plus each test a `// LB_TESTS` line names. The tests:

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
| `txn_count_*_test` | the counter's clean, missing, extra, unwaited, repeated, dropped and late cases; the two-lane counter of paired mode, each lane short or extra; a clock that stops, slows, pauses or runs a runt pulse |
| `txn_digest_*` (`a2c_txn_digest_lb_tests.svh`) | `txn_digest_test` feeds digests directly: the same items at the same times match, and a changed time, data value or order, or an extra side item, does not; a dual digest keeps its lanes apart; which comparators pair every item. `txn_digest_rv_test`, `txn_digest_er_test` and `txn_digest_axi_test` are for the `seed_repro_*` checks, which also run `txn_digest_cut_test` from `a2c_replay_drain_lb_tests.svh` and `rdy_vld_random_test`, a test with no digest |
| `expected_error_exact_test`, `expected_error_missing_test`, `expected_error_extra_test`, `expected_error_text_test` | `a2c_expected_error` with the expected count, one report short, one over, and a report with the ID but not the text, which stays a `UVM_ERROR`; each other count raises exactly one `A2C_EXPECTED_ERROR` |
| `expected_error_overlap_test` | two `a2c_expected_error`s whose matches overlap: the one whose catcher runs first takes the shared report, and the other counts only the report left at `UVM_ERROR` |
| `a2c_mem_model_test` | reads, writes and the three fill policies, unwritten words reading the same in any order, one `A2C_MEM` line per model |
| `lmmi_random_test`, `lmmi_reuse_test`, `lmmi_counter_test`, `lmmi_monitor_checks_test` (Pro) | as the other types |
| `model_cmp_*`, `status_cmp_*`, `midstream_guard_*`, `replay_log_*` (`a2c_model_cmp_lb_tests.svh`) | the paired-mode classes of section 9.12 on their own: match, mismatch, leftovers on either side, keyed order, injection, the report cap, cut and uncut, a dead lane; the three status policies; the guard's error and its `+a2c_predict_midstream` demotion; the replay log's record, replay and leftovers |
| `reg_read_*` (`a2c_reg_read_lb_tests.svh`) | register reads in paired mode. A read of a volatile register, of a register with one volatile field, or of a read-only memory while outputs are pending, with and without `+a2c_predict_midstream`, its compare demoted per read and no window opened, also with `inject_mismatch()` and across `cut()` and `uncut()`. Volatile reads when quiescent, after a lane death, and non-volatile, read-write memory or unmapped reads while pending. The skip list by address, `skip_reg()` with and without a map and `skip_mem()`, each also with a map that does not hold the register or memory, with the response and writes still compared and the `A2C_REG_SKIP` lines. The same reads through a register model and the apb agent's pins in paired mode and single mode. `a2c_reg_map` memories whose rows are narrower than their stride, written by burst and by row and read back over the pins, each row in its own bus words at its stride, with `get_mem_by_offset()` and `get_addresses()` on a byte-addressed and a word-addressed map. The same over a three-level model in paired mode and single mode, with two `a2c_reg_map` siblings and a memoryless child with a plain `uvm_reg_map` under the root: root-map lookups of every row word, `get_addresses()` through no map, the element's own map and the root map, the predictor's mirror of child registers, the guard and `a2c_reg_write_subscriber` naming child elements, and `skip_reg()` and `skip_mem()` of child elements. The `A2C_CFG` fatals of `a2c_reg_map`: `set_mem_stride()`'s two, a parent that is not an `a2c_reg_map`, a parent with another bus width or addressing, a guard and a subscriber given a child map, and overlapping strided memories and a register in a memory's unused row words. An `a2c_reg_map` under a matching `a2c_reg_map` is accepted. `a2c_child_block_catcher` in a three-level model demotes the `UVM/RSRC/NOREGEX` warning of each of the five blocks below the root to a `UVM_HIGH` info, and no other: a user resource with meta characters in its name still warns when it is set while the catcher is installed, and so does one named like a child block and set after. A second `install()` for one root and a `remove()` with no catcher are each an `A2C_CFG` fatal |
| `<type>_paired_test`, `<type>_paired_mismatch_test` and the other `<type>_paired_*` tests, every base type in both roles; `axi_paired_lb_tests.svh` for the AXI agents | two lanes of one interface type looped back, the same traffic compared on both and, where the type compares data, a mismatch forced on one lane; a lane that leads or trails; the responders' replay and drain; the AXI keyed compare and `reorder` with each lane leading in turn; lane deaths, lone lanes and passive agents; on `memory`, the model lane's credit, accesses made without it, two ports of one shared model, a model lane read that must return the DUT lane's word after another port rewrote it (`memory_paired_dst_rewrite_between_test`), the driver's held counts against the peer's, and a master's stall that a held memory read causes, under the lane skew rule and under the joint stall rule (`memory_paired_d1_stall_test`, `memory_paired_d1_joint_stall_test`) |
| `drain_*` (`a2c_replay_drain_lb_tests.svh`) | the end-of-test drain: settle, cut, re-cut, catch-up and clock stop, with deaths during each |
| `a2c_lane_watchdog_rules_test`, `joint_stall_*` (`a2c_lane_watchdog_lb_tests.svh`) | the lane skew, lone lane and joint stall rules, and which transfers count as progress. `<type>_paired_dst_watcher_test`, for push_ack, notify_ack, rdy_vld and axi4_stream: a passive `A2C_DST` agent on the port, whose `model_cmp` the master tells of the model lane's death |
| `paired_foreign_*`, `paired_contract_*` (`a2c_paired_contract_lb_tests.svh`) | agents that implement only `a2c_paired_agent`, compared through `a2c_paired_port`: a hand-written rdy_vld source; a source and a sink built on `a2c_lane_driver`, the sink with a replay log; a model-lane death that the port's `model_cmp` learns of, so the DUT lane's unpaired beats go unreported; and foreign monitors that never call `handshake()`, whose transfers the ports count while a push_ack master waits three times its `joint_stall_cycles`, and with the ports' `joint_watch` cleared count for nothing, so the wait raises `A2C_JOINT_STALL`. Each `paired_contract_*` test breaks one rule and expects its one `A2C_PAIRED_CONTRACT`: an agent that does not implement the interface, a null `lane_ap()`, one analysis port for both lanes, no watchdog, a one-lane watchdog, a master the env sets as `A2C_DST`, a watchdog never stepped or never configured, and a replay log with no `driver` or no `clk_vif` |
| `<type>_paired_throttle_test`, `<type>_paired_on_time_test`, `push_ack_paired_throttle_*`, `rdy_vld_paired_clock_paced_test`, `apb_paired_zero_wait_test`, `<type>_paired_same_clock_test` for push_ack, notify_ack, req_ack, pop_ack, rdy_vld and axi4_stream, `axi_read_paired_master_throttle_test`, `axi_write_paired_master_throttle_test`; Pro's `lmmi_paired_*throttle_test` and `lmmi_paired_on_time_test` | the model throttle rule on every master: a model lane one item late by the bound raises exactly one `A2C_MODEL_THROTTLE`, one a clock under the bound raises none, one late on every item raises one only, a DUT lane that is late counts nothing, and a model lane that keeps pace raises none under the default bound, with the held clocks counted exactly. Under the default bound a model lane one clock late on every rdy_vld item, as a model that waits on the clock between reads is, raises one, and two apb lanes that both raise `pready` in the first access phase raise none. Two ack-style lanes that both ack each request in its first clock, the DUT lane just after the master's drive point as a combinational `ack` does and the model lane one step before the falling edge as a src BFM does for a zero-time model, raise none and move one item per clock. Two rdy_vld or axi4_stream lanes whose model lane raises ready one step before the falling edge of each clock, as a src BFM does for a model whose last write a dst BFM completed at the sample point, also raise none and move one beat per clock. The loopback's lanes answer on their own scripts or random ready, not as an RTL and its model, so `lb_base_test` turns the rule off and only these tests turn it on. The lane skew and joint stall tests check the closing sentence on the trailing lane |
| `push_ack_dst_same_clock_test`, `notify_ack_dst_same_clock_test`, `push_ack_paired_dst_same_clock_test`, `rdy_vld_ready_pattern_test`, `push_ack_delay_pattern_test`, `a2c_rand_knobs_test` (`a2c_ready_policy_lb_tests.svh`) | `a2c_always_ready_policy` by factory override: every clock with the request high acks it, against a master that drives at its drive point; in paired mode the DUT lane acks in each request's clock, and the model lane in its own request's clock or, when it leads, in the clock the DUT lane acks; `a2c_pattern_ready_policy`'s `rdy` levels clock by clock and its ack delays transfer by transfer; `randomize()` keeping every default, an inline constraint replacing only the defaults it excludes, `c_valid` holding a range, and a factory-overridden config's own constraint |
| `rt_rv_*`, `rt_axis_*`, `rt_pa_*` (`a2c_rt_checker_lb_tests.svh`) | `a2c_rt_checker` and the monitors' flow counts on a configurable pipeline, and on push_ack with no DUT: each rule's failures, a lag at and below its bound, the stall and starvation credits, `set_limits()`, `a2c_rt_off`, an output on a second clock, and paired mode with a slow model lane or a slow DUT lane |
| `js_rv_*`, `js_axi_*` (`a2c_joint_stall_lb_tests.svh`) | the joint stall rule in single mode on a configurable pipeline: a DUT that stops taking input, one that is slow but keeps moving, a wait beside a moving port, an idle test, the bound at 0, two waiting ports, the run timeout's deferral to the rule and its leaving out a rule whose clock has stopped, and the run's end at the stall; and AXI read and write masters whose slave never returns R or B, held by the outstanding burst alone |
| `gen_base_*` (`a2c_gen_base_test_lb_tests.svh`) | the generated base test's knobs: the drain and lane rule settings, `A2C_NO_STIMULUS`, the run timeout's budget, deferral and phase handling, a single-mode joint stall ending the run (`gen_base_joint_end_*`), and `reset_dut()`, refused with `A2C_RESET` in paired mode and pulsing `clk`'s reset otherwise (`gen_base_reset_*`) |
| `lb_expect_from_model_*`, `lb_no_pairs_*` (`a2c_completion_lb_tests.svh`) | completion from the model lane: a paired-mode port with no declared count completes on the model lane's count, a DUT lane two short is two missing, and a single-lane counter with the key set is one `A2C_CFG`; a comparator that compared no pair is one `A2C_NO_PAIRS`, and none when waived |
| `lb_reset_held_test` (`a2c_reset_lb_tests.svh`) | a mid-run reset of `clk`'s domain while a master holds its item: a memory read in its gap and in its enable clock, an AXI read and an AXI write burst in their gaps, and an apb read in its setup phase. Each sequence ends within 50 clocks, the memory read with data 0, the bursts with no beats and the apb read with `slverr` set, and the pins at the reset show the point each reset hit |
| `lb_reset_paired_test` (`a2c_reset_lb_tests.svh`) | a mid-run reset of `clk`'s domain with `rdy_vld`, `push_ack` and an AXI read master in paired mode, each with items in flight, the push_ack replay log holding acks and the AXI model lane holding bursts: each comparator pairs exactly the items sent after the release, and nothing in flight is reported missing, extra or unpaired |

A test file adds tests that a macro defines with a line `// LB_TESTS <test>...`, because `run_loopback.sh` finds the others by their `` `uvm_component_utils `` lines.

The loopback does not run on Verilator, because 5.052 and master stop with an internal error on `typedef <agent>::item_t`.

These unit tests cover the generator and make side without a simulator:

- `test_error_uvm_blocks.py`, the validation;
- `test_uvm_register_view.py` and `test_uvm_pkg_regmodel.py`, the register view and the generated register model and env;
- `test_uvm_register_tree.py` and `test_uvm_pkg_regmodel_routed.py`, the instance tree of a hierarchical register model and the model generated from it;
- `test_seed_repro.py`, the verdicts of `seedRepro.py` over a stand-in simulator;
- `test_uvm_test_pkg.py`, the test package;
- `test_uvm_boundary_pins.py`, the pins, port maps, shells and generated files, on two variants and a block without a model, and in `check_vcs_shells` the order, count and defines of the VCS analysis steps;
- `test_build_manifest.py`, the manifest records;
- `test_dut_run.py`, the snapshot `dutRun.py` picks, including `--uvmDut` and `--uvmTop`;
- `test_uvm_agent_companions.py`, the agent and checker files;
- `test_hdl_wrapper_xcheck.py`, the checker instances;
- `test_regr_rules_uvm.py`, the `uvm.json` filters, the `seed_repro` verdict included;
- `test_raw_src_bfm_missed_edges.py`, the raw BFM's missed-edge warning;
- `test_bfm_backpressure_checks.py`, the rdy_vld and axi4_stream BFMs: the contract warnings, back-to-back throughput, delayed writes, reset, a src BFM that takes a beat only when its reader is back, and a dst BFM whose writer returns on the HDL's transfer edge. A transactional model moves one beat per clock and a clock-paced one one beat per two clocks, which alone gets the notice. A transactional writer behind a fixed one-clock `--delay` gets none, nor does a transactional relay into a randomly or always ready sink; the relay moves one beat per two clocks in one thread and one per clock in two. A model with room for three beats is handed three, a multicycle burst leaves the model when its first beat goes on the pins, and user ready control on a channel a src BFM writes asserts;
- `test_memory_bfms.py`, the memory BFMs' read timing, the src BFM's skipped-access count, the break queued for UVM and the run failed when UVM never takes it, the dst BFM holding each access for its credit, and dst BFMs keeping the model's program order across ports under a write order, with and without it, including a port behind a producer-shape thunker and a port on a slower clock;
- `test_uvm_model_credit.py`, the paired-mode credit pins, the testbench module's `a2c_credit_if` per credited port, the env's fetch and the wrapper's `setModelCredit()` call and its `setWriteOrder()` call only in a model-only run, on a copy of `examples/uvmMem`, and no credit pins on the same copy without a model;
- `test_axi_write_src_bfm_w_first.py`, `axi_write_src_bfm` holding `wready` low for a W beat that comes before its AW;
- `test_bfm_handshake_contract.py`, the held-request break of the `push_ack`, `req_ack`, `pop_ack`, `notify_ack` and `apb` src BFMs when the HDL drops or changes a request inside the model's call, and none when it holds it; the four ack-style src BFMs acking every request of a model that answers in zero time in its first clock, one request per clock, with the rdata on `req_ack` and `pop_ack`; an `apb` src BFM completing a posted write only after the model took it, and completing every transfer of a model that answers in zero time in its first access phase, writes and reads back to back; an `apb` dst BFM holding the model's next `request()` until the sample point before the edge that completes the posted write; the four ack-style dst BFMs completing each call at the sample point before the edge that takes the request, with the rdata of its ack, dropping the request at that edge under a timed delay that outlasts it, and keeping it on the pins, with the `HDL lowered ready` break, when `ack` falls after the sample point, or with no break when a reset asserts then; every `axi_read` and `axi_write` channel moving each beat on the HDL's transfer edge in both BFMs; the clock-paced report logged but never queued under UVM, with no report for a model that a memory BFM wakes; and a `rdy_vld` src BFM whose reader waits on the clock after each read holding `rdy` low one clock in two;
- `test_registered_fifo.py`, `registeredFifo` freeing a slot from the edge after a read, and at once with no BFM on its clock port, logged once by port in a run that has BFMs, and a two-thread model on it taking, dropping and sending exactly the beats the RTL `rdyVldFifo` does under an input that overruns it, where the same model on an `sc_fifo` takes a beat a clock early;
- `test_bfm_pin_timing.py`, outside UVM: an arbiter whose `ack` on a `req_ack` port falls when a `push_ack` port's request rises at the first port's sample point failing the run with `HDL lowered ready`, naming the first port and the second as the BFM port that drove a pin then; a multicycle `rdy_vld` dst BFM, an `axi_write` dst BFM carrying W bursts and a `memory_dst_bfm` driving a model call made in the low phase one step after the next rising edge, and one made in the high phase at once; a `push_ack` dst BFM raising its request at its own sample point against an `ack` that follows it combinationally, as a same-clock UVM responder's does, taking each request once at the next rising edge with no break; and `req_ack`, `pop_ack`, `memory` and `apb` dst BFMs whose read data follows another BFM's pin raised at their sample point failing the run with `HDL changed read data`, naming that BFM. Pro's `test_lmmi_bfm_contract.py` raises the same break for an `lmmi` slave that changes `lmmi_rdata` after the sample point;
- `test_port_transfer_size.py` and `test_uvm_max_transfer_bytes_flag.py`, the per-port transfer size and the agents that declare `max_transfer_bytes`;
- `test_watchdog_uvm_stall_check.py`, the SystemC watchdog's stall check turned off under UVM (section 9.11);
- `test_sv_string_select.py`, no `?:` between two string literals, bare or in `string'()`, in any SV file of base or in the SV the generators emit. VCS types such a `?:` as a packed vector, which `%s` pads with leading spaces; `a2c_select_str()` is the replacement. Pro's `test_uvm_sv_checks.py` applies it to the Pro layer;
- `test_uvm_sv_parse.py`, a Verilator parse of the UVM library, the loopback testbench and the generated UVM packages of `examples/uvmMem`, `uvmRegs` and `uvmReuse`, its leaf top and its root top, whose env compiles the leaf's variant packages first, and Pro's `test_uvm_sv_checks.py` of the Pro agent packages. It needs `UVM_HOME` set to an unpacked Accellera UVM 1.2 release, the directory whose `src/` holds `uvm_pkg.sv`, because the VCS and Xcelium copies encrypt files Verilator cannot read. `UVM_HOME` is the only place the release comes from: the build resolves no path of its own and the CI image carries no release, so without it the test prints a `SKIP:` line naming what did not run and passes, and the commit gate below is where the check runs. The parse finds syntax errors, undefined macros, missing includes and unknown package imports. The library's packages also get Verilator's full lint, which adds undeclared names, wrong argument counts and type mismatches. The loopback and the generated packages stop at the parse, because the lint rejects `::` through a typedef of a parameterized class's type member, which every generated env package uses and both simulators accept. A difference in how VCS and Xcelium treat legal SV, such as the string padding above, needs a simulator.

The UVM runs of `examples/uvmMem` need such a simulator too; its SystemC and Verilator runs are the `uvm-mem` pipeline target. The example is the end-to-end bench for a block with RTL and a model on UVM. Its DUT reads and writes one memory through two `memory` `src` ports, and its env shares one `a2c_mem_model` between them, so its paired-mode runs pass the credit pins through the shells, the wrapper and `memory_dst_bfm`. From its `rundir`, with the simulator setup sourced:

```
make regr_uvm_xcelium        # or regr_uvm_vcs
```

Each runs the smoke, random and fail tests on the model, the RTL and both, and `model_mismatch` on both. On both it also runs the smoke and fail tests with `+a2c_expect_from_model=1`, under which the smoke test declares no count, so the fail test also runs on a smoke test that takes its count from the model lane. The example sets `A2C_ROOT` to the base checkout. In a builder checkout whose layer sets the toolchain, pass `A2C_ROOT=<builder root> REPO_ROOT=<example>` to `make` so the layer's settings apply.

`examples/uvmRegs` is the end-to-end bench for a hierarchical register model. Its top `uvmRegs` owns no registers. It hosts a router whose slots hold two instances of one leaf at two variants, one at `addressMultiples: 2`, a leaf with `rw`, `ro` and `ext` registers, a `regAccess: ro` memory and a 12-bit `regType: memory` table on an 8-byte stride, a nested-router host and a passthrough container. Words pass from `in` through three of the leaves to `out`, so the output depends on the registers. `uvmRegs_smoke_test` programs every leaf by its instance path, streams words against a scoreboard that predicts from the model's mirror, and reads the count and the captured words back. `uvmRegs_reg_test` is an `a2c_reg_test` on the root block, then runs `uvm_reg_hw_reset_seq` on `uBridge.uDeep` alone, through its own map. `uvmRegs_mem_walk_test` runs `uvm_mem_walk_seq` on `uStat`, which walks the table at its stride. `uvmRegs_midstream_test`, on both only, writes `uWrap.uInner.tag` while words are due and passes only on exactly one `A2C_MIDSTREAM` naming it. Its SystemC and Verilator runs and RTL lint are the `uvm-regs` pipeline target. From its `rundir`, `make regr_uvm_xcelium` or `make regr_uvm_vcs` runs smoke, reg, mem_walk and fail on the model, the RTL and both, and `model_mismatch` and midstream on both. Its `rundir/regmodel.json` rule fails a run on any `UVM/RSRC/NOREGEX` warning, since uvmRegs creates no resource with meta characters in its name, so a child block warning that the generated root block's catcher missed fails the regression.

#### Before a commit

VCS and Xcelium differ in ways a parse cannot see: VCS prints a `?:` of string literals padded, its `uvm_resource_pool::lookup_name()` drops each entry that does not outrank the first match, it prints `%p` of a virtual interface as every signal where Xcelium prints a handle, and it gives every specialization of a parameterized class one struct type. Only a run on each finds the next one, but VCS licences are scarce, so no VCS run blocks a commit. A change to the UVM library, an agent package, the loopback or a UVM template passes, before it is committed:

1. `make unittest`, with `UVM_HOME` set so `test_uvm_sv_parse.py` runs, and Pro's `make unit-test`;
2. the full loopback with Pro on Xcelium.

The reduced loopback with Pro on VCS, `run_loopback.sh --subset reduced vcs <seed> $A2C_ROOT/pro/common/systemVerilog/uvm/a2cPro_uvm.f`, runs when a licence is free, before or after the commit. It needs one VCS licence and runs in under 20 minutes. A failure there is fixed in a later commit. The full loopback on VCS runs the same way. Use one seed for every loopback run of a change.

`reduced.tests` in each loopback directory lists the reduced loopback, chosen against a full run: every agent package in each of its roles, a test of every `*_lb_tests.svh` file, every library report call site that prints in the full loopback, and every branch the full loopback takes of an `a2c_select_str()` or `a2c_lane_name()` call. A new agent role, or a test that is the only one to print a library message, joins the list.

### 9.10 Agents

Every interface type with `uvmAgent: true` ships one agent package, `interfaces/<type>/<type>_uvm_pkg.sv`, or `builder/pro/interfaces/<type>/<type>_uvm_pkg.sv` for a Pro type. The 13 base types and Pro's `lmmi` carry the flag. A package holds `<type>_item`, `<type>_config`, the drivers, `<type>_monitor` with the analysis port `ap`, a sequencer, except for `status` and the `A2C_DST` drivers that choose nothing per transfer, and `<type>_agent`, which exports `item_t` and `config_t`. Every config extends `a2c_agent_config #(VIF_T)`, which holds `vif`, `model_vif` (null outside paired mode, section 9.12), `clk_vif`, `port_name`, `is_active` (default `UVM_ACTIVE`) and `role` (default `A2C_SRC`). The role is the side of the interface the agent plays, so an `A2C_SRC` agent drives a DUT `dst` port and an `A2C_DST` agent serves a DUT `src` port. A `UVM_PASSIVE` agent builds only its monitor.

Handshake and memory types have one `<type>_driver` that switches on the role. The AMBA types have `<type>_master_driver` for `A2C_SRC` and `<type>_slave_driver` for `A2C_DST`. Their package headers give the AMBA 5 names: Requester and Completer for APB, Manager and Subordinate for AXI. Every driver but `raw_driver` and `status_driver` extends `a2c_lane_driver`, described under "The lane driver base" below.

The pin-timing rule: drivers change pins 100 ps after a rising edge through `a2c_clk_if.drive_edge()`, and monitors sample at the falling edge through `sample_edge()`. The RTL changes boundary pins only between a rising edge and the next falling edge. The SystemC BFMs change them between a rising edge and the sample point, one time-resolution step before the falling edge, including at the sample point itself. A monitor therefore sees the value the next rising edge transfers. Four BFMs are exceptions. The `status` and `raw` dst BFMs drive each value the model writes at once, so under `--delay` their pins can change between edges. The `external_reg` dst BFM drives `wdata` and `write` one delta after the model's `reg_write_cmd()`, and Pro's `lmmi_src_bfm` raises `lmmi_ready` when the model's `reqReceive()` or `complete()` runs, in either phase of the clock. None of the four is tracked for the `HDL lowered ready` break (section 9.11). On rdy_vld, axi4_stream and push_ack every src driver raises valid without waiting for ready and holds it, with its data, until the transfer completes, as the interface definitions require.

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

Every item except `apb`, `raw` and `status` has a `rand` `gap` field, the idle clocks the src driver inserts first, with a soft default of 0. A `req_ack` or `pop_ack` item also has `delay`, the extra clocks the dst driver waits before `ack`. Neither takes part in `do_compare`. An agent stops at build with `A2C_CFG` when a delay minimum is above its maximum, when an AXI `_pct` knob, `max_outstanding`, `rdata_latency` or, with `burst` set, `burst_max` is 0, or when a width rule fails: the apb slave needs a `data_t` of whole bytes, and `axi_write` the strobe rule of the burst-limit section below.

#### The kinds of `A2C_DST` driver

- **Ack-only**, `push_ack` and `notify_ack`. The driver raises `ack` for one clock per transfer, after the delay its ready policy draws, which counts clocks from the request's own clock. The default policy draws it from `ack_delay_min` + 1 to `ack_delay_max` + 1, so the config's knobs count extra clocks after the driver samples the request, and with the defaults a transfer takes two clocks. At a delay of 0 the driver acks in the request's clock, as a combinational slave does: from its drive point to the sample point it holds `ack` up while the request is up, so a request the RTL raises at the rising edge, or a master raises at its drive point, has `ack` before the falling edge samples it. A SystemC dst BFM can raise its request at its own sample point, when the model's call reaches it there. The driver's `ack` then rises in that time step, after the BFM has read `ack`, so the BFM takes the request at the next rising edge, where `ack` is still high. The driver changes `ack` in a BFM's sample time step only in answer to that BFM's own request, so the BFM reads the same `ack` whatever order the simulator runs them in. `a2c_always_ready_policy` gives every transfer that delay. The driver draws each delay before its request, so a policy's draws run one transfer ahead.
- **Data responder**, `req_ack` and `pop_ack`. For each request it samples, the driver takes one item from `sqr` and drives `ack` and the item's `rdata` for one clock after the item's `delay`. The agent sets `<type>_responder_seq` as the `default_sequence` of `sqr.run_phase` through `uvm_config_db`. The default answers with random `rdata` and no delay, and a failed `randomize()` is `A2C_RAND`. A test replaces it with its own `default_sequence` set on `<agent>.sqr.run_phase` in `build_phase`, which wins because the test is higher in the hierarchy; the precedence holds only for sets made during `build_phase`. The other way is a factory override, which must name the port's specialization, `req_ack_responder_seq #(<data_t>, <rdata_t>)::type_id::set_type_override(...)` or `pop_ack_responder_seq #(<rdata_t>)`. The variant package declares no typedef for the responder, so the test spells the parameters itself. A replacement extends the same specialization and overrides `respond()`. `common/systemVerilog/uvm/loopback/req_ack_lb_tests.svh` shows both. `req_ack`'s sequencer is `req_ack_sequencer`. Its `uvm_tlm_analysis_fifo` `request_fifo` receives each request, data only, from the monitor's `req_ap`, and the default `body()` hands it to `respond()`, so a responder can compute `rdata` from the request. A replacement `body()` must take one request per response. The sequencer reports `A2C_RESPONDER` at `check_phase` when more than one is left. The earliest `ack` is the clock after the request, because the response comes from the sequence once the monitor has sampled the request, so no agent gives a DUT requester a same-clock `ack` on these two types.
- **Memory-backed**, `memory`, `lmmi` and the apb and AXI slaves. The driver serves each access from `cfg.mem`, an `a2c_mem_model`, which the agent creates when the test leaves it null. A `memory` read takes its word at the sample edge, before the rising edge applies a write, so a same-clock read and write of one address through two agents sharing a model return the old word, as `memory_dp` does. In paired mode the `memory` `A2C_DST` driver also drives `cfg.credit_vif`, which holds the model lane's accesses (section 9.12). The apb slave maps bus byte k to `paddr + k`, with no alignment, and writes every byte, because `apb_if` has no `pstrb`. An address in `error_ranges` gets `pslverr` or `SLVERR`, leaves the memory untouched and reads 0. An AXI write burst with any beat in a range writes nothing.
- **Level**, `external_reg`. The driver holds `rdata` at `cfg.value`. With `update_on_write` set it loads each write's `wdata` into `value`, so `rdata` changes one clock after the write, as a register flop does.

#### Constrained-random knobs and the ready policy

The timing knobs of every agent config are `rand`: `ready_pct`, `burst` and `burst_max`, `ack_delay_min` and `ack_delay_max`, `max_wait`, the AXI `_pct` knobs, `resp_delay_min` and `resp_delay_max`, `reorder` and `max_outstanding`, and Pro `lmmi`'s `ready_delay_min`, `ready_delay_max` and `rdata_latency`. So is every item's `gap`. Each class keeps its defaults as soft constraints in `c_default`, and in `c_valid` the rules that hold a range together: a minimum at most its maximum, a percentage at most 100, an AXI percentage at least 1. The generated env randomizes each agent config as it creates it, so with no constraint of a test's own every knob keeps its default, and a value a test assigns afterwards still wins. A test constrains knobs with `randomize() with {...}`: an agent config's in `connect_phase` or later, an item's in its sequence. A config class that a factory override puts in the env's place randomizes under its own constraints. A soft default gives way to a constraint that excludes it and holds otherwise, so `with { ready_pct inside {[30:60]}; }` draws from that range and `with { ready_pct inside {[50:100]}; }` returns 100. To draw over a range that holds the default, turn `c_default` off with `constraint_mode(0)` and constrain every knob of the class.

Every `A2C_DST` driver creates one `a2c_ready_policy` through the factory, as `<driver>.policy`, and takes from it each ready level and each response delay. `next_ready(channel, pct, hold_max)` returns a ready pin's level for the clock, and `next_delay(channel, min, max)` the clocks before a response. The driver passes the knobs on each call, so a config changed during the run applies from the next draw. The default calls `randomize()` under `c_ready`, a level of 1 on `pct` percent of draws, `c_hold`, 1 to `hold_max` clocks per level, and `c_delay`, `min` to `max`, which are the distributions the knobs describe. Each draw comes from the policy's own random stream, so a seed reproduces a run on one simulator (section 9.7). In paired mode the driver draws once and both lanes get the result: the same ready level, or the delay the DUT lane records for the model lane to replay. A channel names the pin a decision drives, so a driver with two ready pins draws them apart:

| Type | Ready channels | Delay channel and what it counts |
| :--- | :--- | :--- |
| `rdy_vld` | `rdy`, held for 1 to `burst_max` clocks with `burst` set | |
| `axi4_stream` | `tready` | |
| `apb` slave | | `pready`: wait clocks, 0 to `max_wait` |
| `push_ack`, `notify_ack` | | `ack`: clocks from the request's clock |
| `axi_read` slave | `arready` | `rvalid`: clocks before a burst's first beat |
| `axi_write` slave | `awready`, `wready` | `bvalid`: clocks before a burst's B |
| `lmmi` (Pro) | | `lmmi_ready`: clocks before `lmmi_ready` |

A test replaces the policy with a factory override before the agents build, of every driver's by type or of one driver's by instance path, and sets a subclass's fields in `connect_phase`. Two subclasses ship in `a2c_uvm_pkg`. `a2c_always_ready_policy` is ready on every clock and answers every response at its earliest, which for `push_ack` and `notify_ack` is the request's clock. `a2c_pattern_ready_policy` is a directed stall pattern: each channel steps through `ready_pattern` one clock per entry and through `delay_pattern` one response per entry, from the start again at the end, whatever the knobs say. A subclass that only changes a distribution overrides a constraint by name.

```systemverilog
class slow_sink_policy extends a2c_ready_policy;
    constraint c_ready { ready dist {1 := 1, 0 := 3}; }
    `uvm_object_utils(slow_sink_policy)
    function new(string name = "slow_sink_policy");
        super.new(name);
    endfunction
endclass

// In the test's build_phase, before super.build_phase() builds the env:
a2c_ready_policy::type_id::set_type_override(a2c_always_ready_policy::get_type());
a2c_ready_policy::type_id::set_inst_override(a2c_pattern_ready_policy::get_type(), "env.vout_agent.drv.policy", this);

// In connect_phase:
a2c_pattern_ready_policy p;
if (!$cast(p, env.vout_agent.drv.policy)) `uvm_fatal("TEST", "vout's policy is not the pattern")
p.ready_pattern = '{1, 0, 0, 1, 1};
```

The policy does not decide the AXI masters' `rready` and `bready`, the AXI slaves' `reorder` pick, or the `req_ack` and `pop_ack` responders' `delay`, which their responder sequence sets per item.

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
- **Sharing.** The env creates no model, so two ports of one memory keep separate models. To share one, create it in the `<block>_tb_env` subclass's `build_phase` after `super.build_phase(phase)`, fetch each port's config with `uvm_config_db#(<port>_config_t)::get(this, "<port>_agent", "cfg", cfg)`, and set `cfg.mem` on both. The env's `<port>_cfg` handles are locals of its `build_phase`, and the agents read their configs later in the build, so the objects set here are the ones the agents use. In paired mode each port's model lane waits for its credit, so a read through one port that the DUT lane makes after another port's write gets the written word on both lanes (section 9.12).

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

#### Lane deaths in paired-mode masters

Every `A2C_SRC` driver in paired mode that waits for each lane's own handshake puts each item on both lanes and moves on only when both are done: push_ack, notify_ack, req_ack, pop_ack, rdy_vld, axi4_stream, the apb master, Pro's `lmmi` and the AXI masters. A lane that stops answering would stop both lanes, so each of these masters bounds its lanes through `a2c_lane_watchdog`, with four rules. Each reads its knob from the `uvm_config_db` as `a2c_<knob>` at the start of the master's run phase, with a default of 200000 clocks for the first three and 2 for the model throttle rule, and 0 turns it off:

- **Skew**, `lane_skew_cycles`. One lane completed the item, or on AXI took a burst's AR, AW or W beat or completed the burst, and the other has not `lane_skew_cycles` clocks later. The master raises `A2C_SKEW` and declares the trailing lane dead.
- **Lone lane**, `lone_lane_cycles`. Once one lane is dead, the live lane goes `lone_lane_cycles` clocks in a row without progress while it has something to wait for. The master declares it dead too, with an `A2C_SKEW` that names `lone_lane_cycles` and calls the death a likely consequence of the first.
- **Joint stall**, `joint_stall_cycles`. Both lanes are live, at least one has something to wait for, and no lane of any port makes a handshake for `joint_stall_cycles` of the port's clocks in a row. The rule fires only when the whole environment has stopped: a port that waits a frame for a configuration word while the streams of the frame move, or a store-and-forward block that holds its input while it outputs, never stalls, however long it waits. The first master to reach the bound raises one `A2C_JOINT_STALL` for the run. It names every paired-mode port whose live lanes waited, a port with one lane dead included, and what each lane waited for, and says that no port made progress, so the cause may lie in the DUT, the model or the stimulus. Every paired-mode master then declares the live lanes of its port dead, so no second stall can follow. A port's `joint_stall_cycles` decides only whether that port can raise the stall: a port with it at 0 never raises it, but is named if it waits and loses its lanes like every other. While the skew bound is on, a lane that trails the other belongs to the skew rule, so the two rules never fire on one stall.
- **Model throttle**, `model_throttle_cycles`. Both lanes are live, the DUT lane is ready for the next item, or on AXI for the next AR, AW or W beat or a free outstanding slot, and the master holds it back only because the model lane is not, for `model_throttle_cycles` clocks in a row. The master raises one `A2C_MODEL_THROTTLE` for the port, and no lane dies. The model is untimed, so the RTL never waits on it: a model lane that holds the RTL's input back has shallower queuing than the RTL, or waits on the clock, and either is a model defect. The SystemC BFMs answer a model that answers in zero time on the clock an RTL with no wait states answers, `apb_src_bfm` included, and a model that reads and then writes in one thread keeps pace with RTL whose input ready follows its output ready (section 9.11), so a conforming model lane holds nothing back. The default bound is therefore 1: one clock of hold raises the error. In measured runs of SystemC models against their RTL, no master held anything back for the model lane. A model that waits on the clock between reads holds a stream master one clock per item (section 9.11), and the default bound reports it on the first item.

A lane with nothing to wait for counts as making progress, so an idle port never stalls. A dead lane never comes back. What a death does:

- **The dead lane freezes.** The master drives no new item on it. A request it had raised stays up with its payload until that handshake, as the protocols require, and then drops for good.
- **The live lane serves the sequence.** Every open and later item completes on the live lane. The response the sequence gets, `rdata` on req_ack and pop_ack, the read word on `lmmi`, `prdata` and `pslverr` on apb, comes from the DUT lane, or from the model lane once the DUT lane is dead. Once both lanes are dead, every open and later item completes at once, a response with what it was sent with.
- **The comparator and the passive agents learn of it.** A master whose agent has a `model_cmp` in the `A2C_SRC` role, req_ack, pop_ack, apb, `lmmi` and the AXI agents, tells it through `lane_dead()`. Every a2c master that owns a watchdog tells the passive agents on the port's pin sets through `a2c_pin_registry`, as the AXI subsection below describes, so a passive `A2C_DST` agent's `model_cmp` on a push_ack, notify_ack, rdy_vld or axi4_stream port learns of the death as one on a req_ack port does. The memory and external_reg masters own none, as below. The watchdog of an agent a2c does not provide tells only the `model_cmp` its `a2c_paired_port` hands it, since nothing joins that watchdog to the pin registry (section 9.10, "An agent a2c does not provide").
- **The drain keeps the death to name it** in later reports, with the clause the AXI subsection below describes.

The memory and external_reg `A2C_SRC` drivers put each access on both lanes in one clock and wait for no lane's handshake, so neither lane can trail, and status has no handshake. They declare no death.

The handshakes the joint stall rule counts, in one record, `a2c_joint_watch`, come from the monitors, one count per transfer a monitor sees, whatever the agent's role and lane count: a single-mode port, and a single-lane responder in a hand-written paired-mode env, count as a paired-mode port does. An `a2c_paired_port` counts each item either lane's monitor writes, so the monitors of an agent a2c does not provide count without calling `handshake()`; a transfer counted twice in one time step counts once, so an a2c monitor behind the port counts once. A monitor whose `a2c_agent_config` has `joint_watch` cleared, and a port with its own `joint_watch` cleared, count nothing. A transfer is a push_ack, notify_ack, req_ack or pop_ack ack, a rdy_vld or axi4_stream transfer, an apb transfer, a memory access, an external_reg write, an AXI AR, R beat, AW, W beat or B, and an `lmmi` request that ready takes or a read's `rdata_valid`. Status and raw have no handshake, and an external_reg `rdata` is a level, so none of them counts. A master's watchdog asks, on each clock its port waits, whether any monitor counted a handshake since it last asked. A handshake counted in the same time step is left to the next ask, whichever process ran first, so the stall fires on the same clock on every simulator. The count starts on the second clock the port waits after the last handshake, so a port that waits from the clock after it raises the stall `joint_stall_cycles` + 1 clocks after that handshake. A master that asks only in part of its protocol starts later: the apb master asks only in its access phase, so it raises the stall one clock later.

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

#### The joint stall rule in single mode

With one DUT (`UVM_DUT=rtl` or `model`) a master has one lane, so the skew and lone lane rules have nothing to compare, and the joint stall rule is the one that applies. It keeps the knob, the default, the count and the message of paired mode. It catches a DUT that stops taking input while the test still has items to send, which otherwise only the run timeout reports.

The rule counts only while a master holds an item, which means its lane waits for the DUT:

- A single-transfer master (push_ack, notify_ack, req_ack, pop_ack, rdy_vld, axi4_stream, apb and Pro's `lmmi`) holds an item from the drive point that raises its request until the item completes.
- An AXI master holds one while an AR, an AW or a W beat is on the bus, or a burst is outstanding.
- An item the sequence has started that the driver has not put on the pins yet is not held, whether it waits at the sequencer or in the driver's `gap` clocks. The DUT owes nothing for it, and those clocks are the test's own pacing.
- A responder, an `A2C_DST` driver, never holds one. A DUT that stops producing output is the output deadline's (section 9.6), and on a stream the real-time gap rule's. The memory and external_reg masters wait for no handshake and hold nothing either.

A handshake on any port restarts the count, so the stall fires `joint_stall_cycles` + 1 clocks after the last handshake anywhere, as in paired mode. The `A2C_JOINT_STALL` names each port that waited, as `in (uvm_test_top.env.in_agent.drv), waiting for the transfer of 'h5`. Its last sentence reads "With one DUT no lane dies, and the run ends here." in place of the paired-mode one about declaring lanes dead.

The stall then ends the run through the test's run timeout (section 9.6), the way the timeout ends it at its budget: the run phase and every running task phase end at once, each task phase that begins later ends as it begins, `extract_phase`, `check_phase` and `report_phase` run once, and no `A2C_RUN_TIMEOUT` follows. The end-of-test reports of what is missing name the joint stall rule as the end, as section 9.6 describes. A test that does not extend the generated base test has no run timeout, so its masters go on waiting, no port counts toward a second stall, and the message ends "With one DUT no lane dies, and with no run timeout to end the run the masters go on waiting." A budget of 0 turns off the run timeout's time limit, not the component, so the run still ends at the stall; a reported stall should not become a hang that only the UVM phase timeout ends, since that skips `check_phase`. If a fixed budget runs out in the same time step as the stall fires, the simulator's process order decides which ends the run, and the log may carry both `A2C_RUN_TIMEOUT` and `A2C_JOINT_STALL`; a derived budget defers past the stall, so this needs a fixed one. A derived budget defers to a joint stall that is counting when the budget is reached, and leaves it out when its port clock has stopped, as for the paired-mode rules (section 9.6).

#### AXI in paired mode

Each AXI agent drives both lanes and compares them through `model_cmp`, an `a2c_in_order_comparator` keyed by ID, so pairs are matched in order within an ID and the order across IDs is free.

| Role | Both lanes get | Compared | Not compared |
| :--- | :--- | :--- | :--- |
| master on a DUT `dst` port (`A2C_SRC`) | each AR, or AW and W, at one drive point, with each lane's own handshake and `max_outstanding` per lane. The sequence's response comes from the DUT lane, or from the model lane once the DUT lane is dead | R data and `rresp`, or `bresp`, per burst in order per ID | valid and ready timing, the order across IDs |
| slave on a DUT `src` port (`A2C_DST`) | one memory, `cfg.mem`. The DUT lane applies each burst, draws the delays and, with `reorder`, picks the next burst; the model lane answers the same burst by ID and arrival index once its own AR or AW is in, and waits otherwise | the AR bursts, or the AW bursts with their W data | none |

The model lane never chooses a burst, so both lanes answer in the DUT lane's order. At `check_phase` the slave reports two things as `A2C_REPLAY`:

- a pick the model lane holds whose AR it has not issued, or whose burst it has not ended. The error names the pick by ID and arrival index within the ID, and the model lane's own requests waiting behind it. A cut does not hide a held pick the cut keeps, and the replay log's error for the unreached cut then names the held pick as the cause instead of advising `drain_catchup_cycles`;
- bursts the model lane issued that the DUT lane never did, naming the first.

The slave's log joins the drain. A drain cut holds back the comparator's pairs after the cut, and the monitors report bursts left open after a cut as `UVM_INFO`.

**A model that keeps fewer requests outstanding than the DUT.** The model lane serves the DUT lane's picks in the DUT lane's order and never chooses, so the model must queue and arbitrate as the RTL does. A model that keeps fewer bursts outstanding than the DUT has a defect, and paired mode reports it. If the model's master sends the next AR or AW only after an earlier burst's response, the request for a pick the DUT lane reordered never comes, because the response the master waits for is behind the pick. The model lane stops, together with any agent that drives both lanes in step. The drain gives up or the catch-up runs out, and the slave reports the held pick and the requests behind it in an `A2C_REPLAY` error. Fix the model: issue each request ahead of its response, from a thread other than the one that takes the responses, and put a `synchLock` where those threads contend for shared state or a shared port. Setting `reorder` to 0 on the port is only a stopgap. The error goes away, and the port then checks none of the DUT's reordering.

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

#### The lane driver base

`a2c_lane_driver #(REQ, VIF_T, CFG_T, REC_T)` in `a2c_uvm_pkg` holds what the drivers share about their lanes. `REQ` is the item, `VIF_T` the virtual interface, `CFG_T` the config and `REC_T` what a responder's DUT lane records for its model lane. It has:

- `cfg`, the lanes `lane[]` and their count `lanes`, set in `connect_phase` from `cfg.vif` and `cfg.model_vif`, and the run phase's dispatch to `run_src()` on `A2C_SRC` and `run_dst()` on `A2C_DST`;
- for a master, `lane_master()` true by default on `A2C_SRC`: `wd`, the `a2c_lane_watchdog` created in `connect_phase` and configured with `cfg.clk_vif` at the start of the run phase, with the item loop of a single-transfer master in `run_src()`, the per-item wait in `wait_transfer()` and the dead lane's release in `release_dead()`;
- for a responder, `has_replay()` true by default on `A2C_DST`: `replay`, the `a2c_replay_log #(REC_T)` created in paired mode at build, and `run_responder()`, the request, wait, respond and drop cycle of the handshake responders, which records the DUT lane's response and replays it on the model lane;
- `lane_starts()`, `lane_done()`, `lane_busy()` and `lane_holding()` for the drain, from the counters `starts[]` and `done[]`;
- `join_lanes()` and `lane_replay()`, which implement `a2c_lane_joiner`, so an agent holds any lane driver by that one type whatever its `REC_T`. The agent calls `join_lanes()` in its `connect_phase`, which runs after the driver's, with its `model_cmp` and monitors. In paired mode it hands `wd` `model_cmp`, the monitors that implement `a2c_lane_watch` and both pin sets' watchers, and hands the replay log `model_cmp` and the DUT pin set's watchers. Either way the agent claims its DUT lane's pin set.

`a2c_lane_agent #(VIF_T)` holds an agent's share of the wiring. Its `connect_phase` calls `join_lanes()` on an active agent, and on a passive one `a2c_pin_registry #(VIF_T)::join_passive()`, which puts the monitors that implement `a2c_lane_watch` and the comparator into the pin sets' watchers. Its `end_of_elaboration_phase` raises the `A2C_PASSIVE` info, `note_unowned()`, for a passive agent whose `needs_owner()` holds when no active agent has claimed its DUT pin set. The agent supplies four hooks: `lane_cfg()`, `lane_joiner()`, its driver or null, `lane_monitor(l)`, and `lane_cmp()`, the comparator a death or a cut reaches. `needs_owner()` holds by default when `lane_cmp()` is not null. The memory agent narrows it to `A2C_DST`, as its master claims no pin set, and the external_reg `A2C_SRC` agent's `lane_cmp()` is null, as its rdata comparator takes no cut. The apb and AXI agents hold either of their drivers in one `uvm_driver` handle and give it to the base with one `$cast` to `a2c_lane_joiner`. Every agent with a lane driver, and Pro's `lmmi`, extends it. status and raw extend `uvm_agent`: their drivers are not lane drivers and their ports have no handshake, so no death or cut reaches a passive agent on them.

A protocol fills in the base's hooks: `raise_request()`, `drop_request()`, `request_held()`, `request_taken()`, `item_gap()`, `take_response()` and `return_response()` for the master's loop, and `request_seen()`, `request_withdrawn()`, `respond()`, `idle_response()`, `drive_response()` and `end_response()` for the responder's cycle. Every hook takes its lane as an `int`. The loops cannot work without `raise_request()`, `drop_request()`, `request_held()`, `request_taken()`, `request_seen()`, `respond()`, `idle_response()`, `drive_response()` and `end_response()`, so each ends the run with an `A2C_CFG` `UVM_FATAL` that names it when a loop calls it unoverridden. `run_responder()` serves the model lane from the replay log, and ends the run the same way in paired mode when `has_replay()` is 0. push_ack, notify_ack, req_ack and pop_ack use both loops. rdy_vld and axi4_stream use the master's loop and override `run_dst()`, as their sinks drive one ready level on both lanes and keep no replay log. The apb master keeps its own setup and access phases and uses the base's release, `drop_request()` and watchdog, and the apb slave uses the responder cycle. The `lmmi` master overrides `drop_request()` alone, for the base's release. memory, external_reg, `lmmi` and the AXI drivers keep their own run tasks, since their transfers are pipelined, have no handshake or take more than one step, and use the base's lanes, watchdog, replay log, counters and `join_lanes()`. The memory and external_reg drivers return 0 from `lane_master()`, as their masters cannot stall and declare no death.

#### An agent a2c does not provide

Paired mode needs lane-aware agents: one stimulus on both pin sets at one drive point, a handshake per lane, a watchdog on a master and a replay log on a responder. A UVM agent from elsewhere, such as a vendor VIP, has none of this. Its monitors can be reused unchanged, one per pin set. Its driver cannot: a closed VIP driver holds one pin set, steps no watchdog and feeds no replay log. A foreign agent in paired mode therefore needs a hand-written driver, most simply one built on `a2c_lane_driver` with the protocol's pin hooks, and takes part through this contract:

- The agent implements `a2c_paired_agent #(T)`. `lane_ap(l)` returns the analysis port of the monitor on lane `l`'s pin set, which writes one item per transfer, in transfer order, on the clock of the transfer; each lane has its own. `lane_watchdog()` returns an active master's `a2c_lane_watchdog`, built with 2 lanes by the end of `connect_phase`, and null otherwise. `lane_replay()` returns an active responder's `a2c_replay_log`, built by the end of `connect_phase` with `driver` and `clk_vif` set, and null otherwise. `lanes_in_lock_step()` returns 1 for a responder that drives both lanes alike on every clock, such as a sink that drives only a ready level, which needs neither.
- The master implements `a2c_lane_waits`, which the watchdog requires, and calls `wd.configure(clk_vif)` with the port's clock at the start of its run phase. On every clock it holds an item it either calls `step()`, after `begin_item()` at the item's drive point, which applies the skew, lone lane and joint stall rules and clears a dead lane's pending bit, or calls `progress()` and applies the rules itself: it bounds the skew between the lanes and declares the trailing lane dead with `declare_dead()`, and acts on the `A2C_LONE_STALL` and `A2C_BOTH_STALL` that `progress()` returns with `declare_lone()` and `declare_joint()`. It drives no new item on a lane the watchdog declares dead, and lets a request it had raised there complete. A replaying responder implements `a2c_replay_lanes` and follows the rules of `a2c_replay_log`. `a2c_lane_driver`'s master loop and responder cycle do all of this.
- The env builds an `a2c_paired_port #(T)`, sets its `agent` and `role` before `connect_phase`, and reads the comparison from its `model_cmp`. For an agent that keeps whether it is active in its own config, as many VIPs do, the env also calls `set_is_active()`; otherwise the port takes `agent.get_is_active()`. The port connects both lane ports to `model_cmp` and to a subscriber that calls `a2c_joint_watch::handshake()` for each item, so the agent's transfers count for the joint stall rule whether or not its monitors call it. For an agent inside the DUT the env clears the port's `joint_watch` before `connect_phase`, as the generated env clears `a2c_agent_config::joint_watch` on its internal passive agents, and the port leaves the subscriber out. It hands `model_cmp` to the watchdog and the replay log.

The port raises an `A2C_PAIRED_CONTRACT` error for each broken rule in the first phase that can see it. In `connect_phase`: an agent that does not implement the interface, a null `lane_ap()`, and one analysis port for both lanes, which would compare a lane with itself. At `end_of_elaboration_phase`, for an active agent: an `A2C_SRC` agent with no watchdog; an `A2C_DST` agent with neither a watchdog nor a replay log whose `lanes_in_lock_step()` is 0, which is how a master the env sets as `A2C_DST` shows; a watchdog with other than 2 lanes; and a replay log with no `driver` or `clk_vif`. At `check_phase`: a watchdog never configured, and one never stepped although `model_cmp` paired items.

Outside paired mode, with `UVM_DUT=rtl` or `model`, a foreign agent needs none of this: it drives and monitors its one pin set as any UVM agent does. With no `a2c_paired_port` to count its transfers, its monitor should call `a2c_joint_watch::handshake()` once per transfer, so that its traffic restarts the joint stall count of the a2c masters around it. The generated env builds only a2c agents, so a hand-written env builds the foreign agent and, in paired mode, its `a2c_paired_port`. In the loopback, `paired_foreign_agent_test` is a minimal hand-written rdy_vld source written to the contract, `paired_foreign_lane_driver_test` a source and a sink built on `a2c_lane_driver`, and each `paired_contract_*` test breaks one rule.

#### Checking outputs without the model

Paired mode compares the RTL with the model, so it catches a disagreement and misses an error both make. A bench therefore checks each output stream against the specification too, from the stimulus and never from the model: a scoreboard that computes the expected value, a contract-style check the bench writes, or an assertion. The check runs in every mode, and in paired mode on both lanes, so a model error shows as an independent failure on the model lane and not only as a mismatch. Base does not warn about an output with no such check: whether a check is complete is the bench's call.

#### Names and conventions

The agents use IEEE 1800.2 class roles and names: item, config, driver, monitor with `ap`, sequencer `sqr`, agent, `default_sequence`, `put_response()` with `set_id_info()`. Where they depart from that convention, section 9.13 lists the departure and its reason.

### 9.11 The SystemC side under UVM

With the model DUT, and in paired mode, the generated wrapper drives the pins through the SystemC BFMs in the DUT's swapped roles. Every BFM follows the pin-timing rule of 9.10.

The BFMs serve transactional models, here and in co-simulation. A transactional model calls its port again without waiting on the clock. Through each clock's high phase a `rdy_vld` or `axi4_stream` BFM drives the model's settled state: `rdy` or `tready` is high while the model has a `read()` outstanding, and `vld` or `tvalid` is high while it has a `write()` outstanding. A `write()` returns at the sample point, one time-resolution step before the falling edge, of the clock whose closing rising edge takes the beat: there `vld` and `rdy` are both high and no pin changes before that edge, so the transfer is certain. The model's next call therefore reaches its ports before the falling edge, and a model that reads one port and writes another in one thread moves a beat per clock, as RTL whose input ready follows its output ready does. Every AXI channel follows the same rule, as do the ack-style, `apb` and `lmmi` dst BFMs, and a `memory_dst_bfm` read completes at the sample point after its access edge. The BFM holds no beat of its own. The BFMs change their pins between a rising edge and the sample point, including at the sample point itself.

Sample-point completion has a precondition: on BFM ports, an HDL ready, ack or read data must not depend combinationally on a pin that another BFM drives. A model call that reaches a BFM at the sample point goes on its pins in that time step, as a send that follows a receive another BFM completed there does. RTL that breaks the precondition, such as an arbiter whose `ack` on one port falls when another port's request rises, then lowers a ready that a dst BFM has already read high and completed the model's call on. The RTL takes the request a clock later, possibly with other read data, and the model has already gone on. RTL whose read data follows such a pin changes it after the BFM handed it to the model, so the RTL transfers a value the model never received. The dst BFM reports either as a break below, which fails the run.

- `memory_dst_bfm` drives an access while the clock is high, or one step after the next rising edge if the model makes it while the clock is low, samples `read_data` at the sample point of the clock after the access edge, where it has settled, and completes the model's read there. Outside reset, `read_data` that differs at the next rising edge raises the `HDL changed read data` break below. A model that makes its next access in zero time has it on the pins before the falling edge, so back-to-back reads, and reads whose address comes from the last read's data, run at one per clock. Until it has measured a high phase the BFM completes a read at the rising edge after the access edge. A Verilated memory returns the same word as a UVM agent. In paired mode the wrapper gives it the port's credit and held pins, and it holds access n, the model blocked in `request()`, until the credit exceeds n (section 9.12). An access still held at the end of the simulation is logged at `LOG_IMPORTANT` with the credit it saw, which names a missed wake-up when the credit had released it. With a write order it holds an access until the earlier accesses on the other ports allow it, and logs an access still waiting at the end with the earlier access it waits for (section 9.12).
- `apb_src_bfm` takes each transfer at the rising edge that samples its setup phase, when APB has already fixed the address, direction and write data, and drives `pready` one time-resolution step after an edge by which the model has answered: a read's `request()` has returned, or the model's `reqReceive()` has taken a posted write. A model that answers in zero time completes each transfer in its first access phase, as a slave with no wait states does. Each edge the model has not answered by is a wait state, and an answer that comes between edges, as under `--delay`, is driven one step after the next edge.
- `push_ack_src_bfm`, `req_ack_src_bfm`, `pop_ack_src_bfm` and `notify_ack_src_bfm` take each request one time-resolution step before the falling edge of its first clock, where every source has settled its pins, and pass it into the model's blocking call there. They measure the clock's high phase at every falling edge to find that point. An answer the model gives while the clock is still high goes on `ack`, with `rdata` on `req_ack` and `pop_ack`, at once, so a model that answers in zero time completes each request on the rising edge after its first clock, one request per clock, as a destination whose `ack` follows the request combinationally does. An answer given later, as under `--delay`, is driven one step after the next rising edge. Before the first falling edge after construction the BFM takes no request.
- `memory_src_bfm`'s `request()` must not consume simulated time. An enabled edge that passes while it waits is never served. The BFM counts each one as a `bfmContractCheck` break, which a UVM run raises as `A2C_BFM_CONTRACT` (section 9.8).
- `rdy_vld_src_bfm` and `axi4_stream_src_bfm` sample whether the model's reader waits in `read()` one time-resolution step after a rising edge, once its zero-time work at that edge is done, and drive `rdy` or `tready` from it. They sample after each transfer and on every edge while `rdy` is low. A reader that calls `read()` later in the clock, up to the sample point, raises `rdy` then, so a model whose write a dst BFM completed at that sample point is ready for the next edge. A reader leaves `read()` only with a beat, so while `rdy` is high and nothing transfers they do not sample. The AXI BFMs drive every ready the HDL waits on the same way. A model that has taken a beat and has no room for the next therefore refuses the next edge, so the model's acceptance depth at the port is its own queuing, which paired mode compares with the RTL's (section 9.12). On a `backpressure: false` port that refusal is the break `SystemC stalled a backpressure: false producer`.
- `rdy_vld_dst_bfm` and `axi4_stream_dst_bfm` hold no beat of their own either. Each shows the value the model's writer offers on the pins at once while the clock is high, or one step after the next rising edge if the writer offers it while the clock is low. It reads the value from the channel at the sample point of the first clock whose `rdy` is high there, so the model's write returns before the edge that transfers the beat, as a write into the RTL's output register would leave the writer free for its next input in that clock. The AXI BFMs complete every model send the same way. If ready falls between that sample point and the edge, the BFM keeps the value on the pins until the HDL takes it, and outside reset raises the `HDL lowered ready` break (below). Until the BFM has measured a high phase, the write returns on the transfer edge. A multicycle `rdy_vld` channel carries bursts, so its BFM reads the burst when the first beat goes on the pins and the channel's ping-pong buffer holds the rest; that beat goes on them while the clock is high, as any other does. A W channel that carries bursts to `axi_write_dst_bfm` does the same.
- `push_ack_dst_bfm`, `req_ack_dst_bfm`, `pop_ack_dst_bfm`, `notify_ack_dst_bfm`, `apb_dst_bfm` and Pro's `lmmi_dst_bfm` drive the model's request while the clock is high, or one step after the next rising edge if the model makes it while the clock is low. Each completes the model's call at the sample point of the clock whose closing edge takes the request: where `ack`, `pready`, or for an LMMI write `lmmi_ready`, is high. An LMMI read completes at the sample point before its `lmmi_rdata_valid` edge. The BFM reads `rdata`, `prdata` or `lmmi_rdata` there, and outside reset raises the `HDL changed read data` break below if it differs at the edge. The request stays on the pins up to that edge. If ready falls before the edge, the BFM keeps the request on the pins until the HDL takes it, except that an LMMI read's request drops at its `lmmi_rdata_valid` edge regardless, and outside reset raises the same `HDL lowered ready` break. The channel's timed delay, which the completion waits out under `--delay`, runs in a thread of the BFM's own, so the request still drops at the edge and the HDL never takes it twice. `lmmi_dst_bfm` holds `lmmi_request` from a read's transfer to its `lmmi_rdata_valid` edge.
- The `HDL lowered ready after the sample point where the model's call completed` break of a dst BFM fails the run in every flow, co-simulation included: it sets the SystemC exit status (`errorCode`), and a UVM run also raises it as an `A2C_BFM_CONTRACT` `UVM_ERROR`. Its message names the BFM and the channel of its port, the sample point, and the BFM ports that drove a pin in that time step, the candidates for the combinational path, and says the RTL breaks the precondition above. The `HDL changed read data after the sample point where the model received it` break of the `req_ack`, `pop_ack`, `apb`, `lmmi` and `memory` dst BFMs fails the run the same way, with a message of the same form that gives the time the read data was sampled. The handshake and memory dst BFMs and the src BFMs that answer at the sample point are tracked. The `status`, `raw` and `external_reg` dst BFMs and Pro's `lmmi_src_bfm` are not, so a list that names none points at a pin one of those four drives or at one from outside the BFMs. A tracked BFM that drove a pin at the sample point is named even when it drives again at the rising edge that finds the break. The other `bfmContractCheck` breaks keep their severity, and the clock-paced report never fails a run.
- A model that reads one port and writes another in one thread moves one beat per clock. Its write returns at the sample point, it calls `read()` before the falling edge, and the src BFM raises `rdy` there. It needs no second thread or channel between the two to keep pace, and a model that adds one queues beats the RTL does not have (section 9.12).
- Where the RTL has a FIFO whose full flag is registered, as Pro's `rdyVldFifo`, the model uses `registeredFifo<T>` from `common/systemc/registeredFifo.h` in place of an `sc_fifo`. `write.rdy` of such a FIFO is `~full` from a count that a pop changes at its clock edge, so a slot freed by a read takes a write only from the next clock, and a write to a full FIFO waits even when a read completes in that clock. An `sc_fifo` frees the slot at once, so behind BFMs the model takes an input beat a clock before the RTL could and an input that overruns the FIFO drops different beats. The model's threads only call `read()` and `write()`. The constructor takes a name, the depth and one of the model's ports, the port in the FIFO's clock domain: the FIFO follows the clock of the BFM bound to that port's channel, which every BFM records. A slot read in a clock is free for writes from the next rising edge, and one read at a rising edge's own time from the edge after. An entry is readable at once, which matches the RTL when the writer writes on the edge that delivered its input, as a model fed by a src BFM does. With no BFM on that channel, as in a model-only or SystemC tandem run, a read frees its slot at once. In a run that has BFMs but none on that channel, as when the port given is not one a BFM serves, the FIFO logs that once at `LOG_IMPORTANT`, naming its port, and still runs untimed. The depth is the RTL's less any beats the model's threads hold outside the FIFO.
- A model that waits on the clock between reads is outside the contract. The blocking `read()` already spends the transfer edge, so such a model comes back one edge late and the port moves one beat per two clocks. In paired mode that model holds the RTL's input back one clock per item, which the master reports as `A2C_MODEL_THROTTLE` (section 9.10). A writer that waits on the clock between writes costs no clock behind a dst BFM, because its write returned before the edge.
- Under `--delay`, a write whose delay ends after the sample point of the clock in which the beat could first go on the pins goes on them one step after the next rising edge, so the late model costs a clock. A delay that ends by that sample point costs nothing, because the pins hold the previous beat until that clock: a write that returned at a sample point and is delayed one clock period is offered at the next sample point and still moves a beat per clock.
- The `rdy_vld` and `axi4_stream` BFMs record when, and from which process, the model called the port for each beat: the `read()`, or the `write()` before any timed delay. A call counts when it came on the first edge after the previous transfer, in that edge's own delta cycle or earlier, which is when a model that waits on the clock runs. A writer that waits on the clock calls `write()` on the transfer edge itself, so in practice the report names readers. After 32 counted beats in a row the BFM reports the port once: `port <port>: the model came back exactly one clock after each of 32 transfers in a row, so it waits on the clock between port calls and the port moves one beat per two clocks. A transactional model must not wait on clock edges: remove the wait from the model`. Every flow, UVM included, logs it at `LOG_IMPORTANT` and nothing more. It never fails a run: the model still runs, at the rate its own waits allow. The check that fails a paired-mode run for a model that slows the RTL's input is the model throttle rule.
- A model that another channel wakes with a delta notification runs a delta cycle after the edge and is not counted. A memory channel wakes its model with an immediate notification, so a model that a memory BFM wakes at the edge, waiting in `reqReceive()` for `memory_src_bfm` or in `request()` for `memory_dst_bfm`, calls its next port in the edge's own delta, paced by the HDL. A memory channel bound to a BFM records such a wake for the model's thread, and a port call from that thread in that delta is not counted. Because a write is stamped before its delay, a `--delay` never makes a transactional writer look clock-paced. A clock-paced model meets the count on its 33rd beat, and the run of 32 keeps a model whose own timed waits end on an edge now and then from reaching it.
- A reader on a channel a src BFM writes must not control `rdy` itself. The BFM drives `rdy` from whether the reader waits in `read()`, so `enable_user_ready_control()` on such a channel is a `Q_ASSERT`.
- `axi_write_src_bfm` holds `wready` low while its channel would wait for an address: a transactional receiver, a new burst and no address queued. A master that sends W before AW then holds the beat instead of losing it.
- `req_ack_dst_bfm` and `pop_ack_dst_bfm` drop the request for a clock between requests. The UVM src drivers may send requests back to back, and the src BFMs accept that.

The table gives, for every BFM, what it holds between the model's call and the pin handshake, and what it checks. "src" is the BFM whose HDL side sends or requests, "dst" the one whose model does. Each check is a `bfmContractCheck`: logged once with its time and counted to the end, and under UVM a contract break (section 9.8). A type with no check has the reason in the last column.

| BFM | Holds | Checks | Why nothing else can be lost |
| :-- | :-- | :-- | :-- |
| `rdy_vld`, `axi4_stream` src | nothing: `rdy` follows the model's outstanding `read()`, raised up to the sample point | `HDL transferred a beat the BFM did not sample`; `SystemC stalled a backpressure: false producer`; the clock-paced report | |
| `rdy_vld`, `axi4_stream` dst | nothing: the model's `write()` returns at the sample point before the HDL's transfer edge, once `vld` and `rdy` are high there; a multicycle `rdy_vld` burst is read when its first beat goes on the pins | `HDL stalled a backpressure: false interface`; `HDL lowered ready after the sample point where the model's call completed`, which fails the run; the clock-paced report | |
| `axi_read`, `axi_write` src and dst | nothing on any channel; a W channel that carries bursts to a cycle-mode dst BFM is read a burst at a time, as a multicycle `rdy_vld` burst is | `HDL lowered ready after the sample point where the model's call completed`, which fails the run | Each AXI channel is a `rdy_vld` channel with the `rdy_vld` BFMs' handshake. Where the HDL sends, the BFM raises ready only while the model waits to receive and lowers it before any call that can block, so a beat the HDL transfers is a beat the BFM takes on that edge. Where the model sends, the model's send returns at the sample point before the HDL's transfer edge, when that transfer is certain. AXI has no `backpressure: false` form, so no stall check applies |
| `push_ack`, `req_ack`, `pop_ack`, `notify_ack` src | nothing: the request goes into the model's blocking call one step before the falling edge of its first clock, and `ack` rises only after the model acks | `HDL dropped or changed a request between the edge the BFM took it and the edge it completed` | |
| `push_ack`, `req_ack`, `pop_ack`, `notify_ack` dst | nothing: the model's call returns at the sample point before the edge where the request and `ack` are both high | `HDL lowered ready after the sample point where the model's call completed`; on `req_ack` and `pop_ack`, `HDL changed read data after the sample point where the model received it`; each fails the run | |
| `apb` src | nothing: the BFM takes the transfer at the edge that samples its setup phase; a read's `request()` blocks until `complete()`; a write is posted, and `PREADY` waits until the model's `reqReceive()` has taken it | `HDL dropped or changed a request between the edge the BFM took it and the edge it completed`, with `PSEL` held from the setup phase | |
| `lmmi` src (Pro) | nothing: a read's `request()` blocks until `complete()`; a write is posted, and `lmmi_ready` waits until the model's `reqReceive()` has taken it | `HDL dropped or changed a request between the edge the BFM took it and the edge it completed` | |
| `apb` dst, `lmmi` dst (Pro) | nothing: the BFM shows the offered request and takes it with `reqReceive()` at the sample point before the edge that completes it, so a posted write holds the model's next `request()` | `HDL lowered ready after the sample point where the model's call completed`; on a read, `HDL changed read data after the sample point where the model received it`; each fails the run | |
| `memory` src | nothing: `request()` must not consume simulated time | `HDL made a memory access while SystemC was still serving the previous one` | |
| `memory` dst | an access waiting for its paired-mode credit or write order (bullets above) | `HDL changed read data after the sample point where the model received it`, which fails the run; an access still held at the end is logged | The memory interface has no backpressure: the HDL takes the access on the edge the BFM drives it |
| `raw` src | nothing | `SystemC had not taken the previous raw word at a clock edge`, built warn-only | |
| `raw` dst | the word on the pins | none | `raw` has no handshake. The pins hold the model's last word, the HDL samples them every edge, and the model's next `write()` blocks until after the edge, so every word is on the pins for at least one edge |
| `status` src and dst | the level on the pins | none | A status port carries a level, not transfers. The src BFM writes the pins' value at every edge, the dst BFM drives each value the model writes at once, and a change shorter than a clock is invisible to RTL too |
| `external_reg` src | nothing: each HDL write strobe is forwarded on its edge | none | Neither side can block, and the BFM forwards every strobe on the edge it sees it |
| `external_reg` dst | firmware writes queued in order, strobed one per two clocks | none | `reg_write_cmd()` never blocks and the interface has no backpressure, so the queue keeps every write in order. A reset empties it, as it clears the RTL register |

Tests and end-of-test voters live outside the DUT. The UVM testbench config never calls `set_test_names`, so a model that calls `register_test_name` or `ADD_TEST` exits with `the test list is empty`.

#### The SystemC watchdog

`sc_main` runs `watchDogHandler()` in every flow. Once every registered enabler has voted it on, its stall check fails the run with a `Q_ASSERT` if no model tickles it for one second of wall clock. Under UVM the test drives the DUT, so a model can idle while UVM waits, and the `Q_ASSERT` would end the run before the report phase. The UVM config's `createTestBench()` therefore sets `watchDog::stallCheckDisabledByUvm`, and the handler logs at startup, at every verbosity, that the check is off. The no-terminator check stays on.

The UVM checks that bound a stall instead depend on the DUT:

- Paired mode: the lane skew, lone lane and joint stall rules (section 9.10), then the output deadline, the drain and the run timeout (section 9.6).
- Single mode, `rtl` or `model`: the joint stall rule (section 9.10), the output deadline, once `run_body()` returns, and the run timeout (section 9.6). A DUT that stops taking input blocks `run_body()`. The joint stall rule reports it once no port moves and ends the run there.
- A test that does not extend `<block>_base_test` has neither the output deadline nor the run timeout.

A model whose tickles stand for internal progress that no port shows loses that check under UVM. Report the stall from the model with `errorCode::fail`, or expose the progress on a port the test checks.

#### Builder layers

A builder layer ships its agents through `A2C_LAYER_UVM_F_FILES`, a list of `-F` files of agent packages, each path relative to its list. Under `USE_UVM` the flow compiles them after `a2c_uvm.f`, which lists `a2c_clk_if.sv`, `a2c_credit_if.sv` and `a2c_uvm_pkg.sv` first, so a layer package can import `a2c_uvm_pkg`. Make reads each list with `$(file <)`, which needs GNU Make 4.2, and makes the lists and every file they name prerequisites of the snapshot. Pro adds `pro/common/systemVerilog/uvm/a2cPro_uvm.f` in `a2cPro.mk`, and its checkers through the `-y` line of `a2cPro.f` and `A2C_LAYER_VCS_LIB_SV_FILES`.

### 9.12 Paired mode: the model against the RTL

`UVM_DUT=both` builds one snapshot that holds the RTL and the model. The RTL, instance `dut`, is the DUT under test. The model runs beside it on the same stimulus and is the reference its outputs are compared with, port by port, in order. The tests, sequences and register model are the single-mode ones. The only selection a test sees is the env's `dual_dut`.

Each port has two pin sets, called lanes. The DUT lane is the port's interface, `cfg.vif`, wired to the RTL. The model lane is `<port>_model`, `cfg.model_vif`, wired through the testbench module's pins and the SystemC BFMs to the model. One agent per port drives and monitors both lanes, so `<port>_agent.sqr`, `<port>_agent.mon.ap` and `<port>_counter` keep their single-mode names. `mon` watches the DUT lane. With `model_vif` set the agent also builds `model_mon` on the model lane and, where the type compares something in that role, `model_cmp`, which takes `mon`'s items on `dut_export` and `model_mon`'s on `model_export`. With `model_vif` null the agent builds neither and draws no extra random numbers, so single mode and rtl runs keep their stimulus. The register predictor stays on the DUT lane's bus monitor, so register reads and the mirror test the RTL.

Paired mode passes no transaction through DPI. Both DUTs see the same values on the same cycles, and each lane completes on its own handshake, so the model does not see the RTL's exact input timing. That suits a block whose outputs depend on the order of its inputs and its registers. A block whose outputs depend on when its inputs arrive needs a transport that replays the RTL's input timing to the model, which is not built.

#### Lane rules

- **A master**, an `A2C_SRC` driver that starts transfers, puts the same values on both lanes at one drive point. Each lane completes on its own handshake, sampled at the falling edge, and drops its request at the next drive point. The next item starts when both lanes are done. The model is untimed and its BFMs answer it on the clock the RTL would, so the model lane is done no later than the DUT lane, and the RTL takes its input at its own pace: a model lane that holds the next item back is a model defect that the model throttle rule of section 9.10 reports as `A2C_MODEL_THROTTLE`. A model whose queuing matches the RTL's keeps pace without buffering of its own: one that reads and then writes in one thread keeps up with RTL whose input ready follows its output ready (section 9.11), so a channel or FIFO between threads added to keep pace is queuing the RTL does not have. A response the sequence gets back, such as `rdata`, `prdata` and `pslverr`, or an AXI burst's beats, comes from the DUT lane. Random values are drawn once per item or per clock, never per lane. The memory and external_reg masters put each access on both lanes on the same clock and wait for neither.
- **A ready level** the agent draws, such as `rdy` and `tready`, an AXI master's `rready` and `bready`, or an AXI slave's `arready`, `awready` and `wready`, is drawn once per clock and driven on both lanes.
- **A responder**, an `A2C_DST` driver that answers, serves both lanes from one model: one `cfg.mem` or one responder sequence. The DUT lane applies transaction n and records its response and the delay it drew in the driver's `a2c_replay_log`. The model lane replays the record in order, and when it reaches transaction n first it waits, by holding its ready or ack low, or on `memory` through its BFM's credit. The model lane never applies a transaction and never makes a decision. A choice such as which AXI burst a slave answers next is made by the DUT lane and replayed by the model lane, the way `synchLock::arb()` shares a decision in tandem, where the RTL is always the sender (`systemc-synchronization` skill, section 2).
- **A master's lanes are bounded** by the lane skew, lone lane, joint stall and model throttle rules of section 9.10. **A responder's model lane** is held at the end of the run phase by the drain of section 9.6 until it catches up. The run timeout of section 9.6 ends a run that none of these rules ends.

**The model must queue and arbitrate as the RTL does.** The model lane follows the DUT lane's responses and choices in the DUT lane's order. A model that keeps fewer requests outstanding than the RTL, or arbitrates differently, stalls, trails or differs on the model lane, and paired mode reports it as `A2C_REPLAY`, `A2C_SKEW`, `A2C_MODEL_THROTTLE` or `A2C_MODEL_CMP`. That is a defect of the model, not a limit of the flow. `A2C_MODEL_THROTTLE`, and `A2C_SKEW` and `A2C_JOINT_STALL` when the model lane trails, say so and say to fix the model. The AXI slaves' `A2C_REPLAY` error for a held pick says so and says how to fix the model (section 9.10, "AXI in paired mode").

**memory responders.** memory has no handshake to hold, so the model lane waits before its pins. The `A2C_DST` driver drives `cfg.credit_vif.credit`, the testbench module's `<port>_model_credit`, with the number of accesses the DUT lane has made, and the model's `memory_dst_bfm` holds its access n until the credit exceeds n, with `<port>_model_held` high while it waits. The credit changes at the drive point, so the model's access n reaches the pins at least one clock after the DUT lane's and finds its record: a read takes the DUT lane's word, and a write changes nothing. A read through one port that the RTL makes after another port's write therefore gets the written word on both lanes, as a tandem memory tee holds the model for the RTL. Every memory port the DUT drives is held this way. A model lane access made without credit, from a BFM that ignores the pins, is answered from `cfg.mem` and reported as one `A2C_REPLAY` error at `check_phase`. At `report_phase` the driver reports, as `A2C_CREDIT` at `UVM_MEDIUM`, the accesses the BFM held, counted by the rises of held, the sample edges at which held was high, and the accesses made without credit; `held_access_count()`, `held_clock_count()` and `uncredited_count()` return them for a test's own check.

- **Write order across ports, single mode.** A model's write is posted, so its later access through another memory port can reach the pins on the write's edge or before it, and a memory that serves both at one edge reads first. When the run holds the model alone, the UVM SystemC wrapper gives the `memory_dst_bfm`s of the DUT's memory ports, two or more of a type with `bfmWriteOrder: true`, one `memory_write_order`. Each memory channel stamps an access in the model's program order as `request()` starts, in the caller's thread. A producer-shape `memory_port_thunker` passes the stamp up through `observeRelayed()` as the child's `request()` starts, so a thunked port is stamped in the child's thread, not the thunker's, and the relay is not stamped again; the consumer shapes relay toward a completer and pass nothing, and Pro's `memory_port_tee` sits only in the generated `<block>Tandem` wrappers, which a UVM SystemC wrapper never holds, and merges two requesters that have no single program order. The BFM holds an access until the earlier accesses on the other ports allow it: a read is sampled after every earlier write, and a write is sampled after every earlier write and no earlier than every earlier read. On one clock the write may go once the read is on the pins, so it lands on the read's edge or later; on another clock it waits until the read has been sampled. A read whose BFM has not yet driven it, as while its port is in reset, holds the write either way. An access released by the edge of another clock waits for its own clock's next rising edge before it drives the pins, so they change only between its own rising edge and the sample point, including at the sample point itself, before the falling edge where the agent samples. Reads never hold reads. An access waits only for accesses issued before it, but the wait is not limited to one clock: an access issued behind a stream of posted writes on another port waits for each of them to be sampled, so every such access costs at least one clock, and a write behind a read on a slower clock waits for that clock's edge. Two model threads that issue accesses in one evaluation phase race: the stamps follow the order the kernel runs them, so the outcome can differ between the Accellera kernel in the model's SystemC testbench and the Xcelium or VCS kernel in a UVM run. An access still waiting at the end of the simulation is logged with the earlier access it waits for. In paired mode the model lane takes the RTL's words from the replay log, so the wrapper leaves the order off, and a BFM given both a credit and an order asserts at the end of elaboration.
- **Coverage boundary.** The model lane reads the RTL's words, so paired mode does not check that the model's own order of accesses across ports would read the same words from a memory of its own. Tandem has the same boundary. A single-mode run on the model DUT with a scoreboard covers it.
- **Input coupling.** The model is untimed and infinitely fast, so the RTL never waits on it. A held access blocks the model thread that makes it. If that thread makes the access at an earlier point in its input than the RTL, the RTL needs more input before the access than the model lane has taken, and the model lane takes no more until the access is released. Both lanes stop. The port's master reports `A2C_SKEW`, or the env `A2C_JOINT_STALL`, and the message names the memory access held for its credit and says to fix the model. This is a real ordering difference, not a limit of the master's lockstep: a write to that memory between the two points reaches one design and not the other. The fix is in the model, under the rule that the model queues and arbitrates as the RTL does. Make each access at the RTL's point in its input, buffering and queuing input as the RTL does, for example by taking input in a thread of its own or through a FIFO as deep as the RTL's, and use a `synchLock` where threads share the memory (`systemc-synchronization` skill). A memory access inside a register callback couples the register bus the same way; the generated register handler runs in its own thread.

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
| `memory` | either | each access, read data included on `A2C_SRC`, through `memory_comparator`, which holds a pair whose read word has X or Z; `A2C_DST`: the access stream, through `memory_access_comparator` | none |
| `external_reg` | `A2C_SRC` | `rdata` under the port's status policy, through `external_reg_comparator`, because the model's `rdata` trails a write by a clock more than the RTL's | intermediate `rdata` |
| `external_reg` | `A2C_DST` | the writes | none |
| `axi_read` | master | each burst's AR fields, beats, `rresp` and `ruser`, in order per ID | valid and ready timing, the order across IDs |
| `axi_read` | slave | the AR bursts, in order per ID | none |
| `axi_write` | master | each burst's AW fields, W beats, `bresp` and `buser`, in order per ID | channel timing, the order across IDs |
| `axi_write` | slave | the AW bursts with their W data and strobes, in order per ID | none |
| `lmmi` (Pro) | either | direction, offset and the word written or read; the word is left out on a read of an offset on the skip list | `A2C_SRC`: ready and `rdata_valid` timing |

#### Comparators

The comparator classes are in `common/systemVerilog/uvm/a2c_uvm_pkg.sv`:

- `a2c_comparator_base` holds what every comparator shares: `midstream_beats` (64), `max_reported` (10), `auto_stable` (1), `counted` (0), `allow_no_pairs` (0), `stable_point()`, `inject_mismatch()`, `get_pairs()`, `cut()`, `uncut()` and `lane_dead()`. The env's `comparators` list holds every agent's `model_cmp` as this type. A comparator that compared no pair by `check_phase` is an `A2C_NO_PAIRS` error, because its port went unchecked: a test that sends nothing through a port, or a port whose traffic never reached the model lane, would otherwise pass. A port meant to carry nothing sets `allow_no_pairs`, or the `bit` config key `a2c_allow_no_pairs` on its `model_cmp`. A comparator a lane death stopped is not reported, since the `A2C_SKEW` or `A2C_JOINT_STALL` error has already failed the run, nor is a status comparator under the `bounds` or `off` policy, which compares no pairs. A register bus comparator (`a2c_reg_comparator`, so `apb_comparator` and Pro's `lmmi_comparator`) is not reported either, because register traffic is optional and a test that never touches the bus leaves no datapath port unchecked. Nor is a memory port's comparator, `memory_comparator` on the `A2C_SRC` role and `memory_access_comparator` on the `A2C_DST` role: a memory port reaches a memory, through `memoryConnections`, or a register-mapped memory, through `registerConnections` with `regType: memory`, and a test may never access it. A generated test with `no_stimulus_expected` set waives every comparator below the env, through `a2c_allow_no_pairs` on `env*`. A test that sends no traffic through a datapath port on purpose, such as a register-only test, sets `a2c_allow_no_pairs` on that port's `model_cmp` in its test package's user span.
- `a2c_in_order_comparator #(T)` pairs the DUT lane's item n with the model lane's item n, in arrival order on each lane, and compares them with `T::compare()`. A mismatch is an `A2C_MODEL_CMP` `UVM_ERROR` naming the comparator and the pair, with both items printed, the time each item reached the comparator, and the fields that differ (section 9.14). After `max_reported` mismatches the rest are counted, and `check_phase` reports how many went unprinted. At `check_phase` items either lane left unpaired are `A2C_MODEL_CMP` errors, unless `counted` is set, which the env sets on a counted port because its counter already reports the shortfall or excess, or a lane is dead, because the `A2C_SKEW` or `A2C_JOINT_STALL` error that declared it dead has already failed the run and the comparison stopped at the death. A subclass that overrides `key()` pairs in order per key: the AXI comparators key by ID. `uvm_in_order_class_comparator` is not used, because it has no leftover check and none of these hooks.
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

The RTL pipelines a beat and the model does not, so a register write while data is in flight can take effect on a different beat in each. Paired-mode tests therefore change configuration only while the datapath is quiescent: program the registers, stream, wait for the outputs with `wait_for_outputs()`, and only then program again. `a2c_midstream_guard` enforces the rule. The env builds it in paired mode when the block has a register model, and feeds it from `a2c_reg_write_subscriber` on the DUT lane's bus monitor. The subscriber passes on every write the monitor sees, a memory write, an unmapped write and each bus word of a multi-word register included, because the predictor reports only writes that complete a whole register.

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

**The skip list.** Some reads cannot be compared at any time, such as a free-running counter. List them on the register bus comparator in the `<block>_tb_env` subclass, in `connect_phase` under `if (dual_dut)`. `model_cmp` exists only in paired mode, so without the `if` the default single-mode run stops on a null `model_cmp`. Here the register-bus port is `regs`:

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

The paired-mode messages, such as `A2C_MODEL_CMP`, `A2C_MIDSTREAM` and `A2C_NO_PAIRS`, are in the catalogue of section 9.17.

#### Names

The paired-mode names follow the agent conventions of section 9.10. Section 9.13 lists those that depart from common UVM practice, with the reasons.

### 9.13 Departures from UVM convention

This is the one list of the places where the flow departs from IEEE 1800.2 or from common UVM practice. Other sections refer to it and do not repeat it. Each row gives the convention, what the flow does instead and why. Where the reason is that the conventional form is not built yet, the row says so, and section 10.1 or 10.2 states what that leaves unverified or out of reach.

#### Testbench structure and the end of the test

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| A SystemVerilog top module owns the clocks and resets, calls `run_test()`, and the simulation ends at `$finish` | `sc_main` is the top. SystemC instantiates the testbench module as an HDL top, generates every clock and drives every reset. The module clears `finish_on_completion`, and reports completion and the error count to SystemC through the pins `uvm_done` and `uvm_errors`, which decide the run's exit status (section 9.8) | every arch2code testbench runs from `sc_main`, which holds the model, its BFMs and the exit code. One kernel runs the model and the RTL with no transaction transport through DPI |
| The testbench drives the clocks and resets, and the test asserts reset by driving the reset signal | SystemC generates every clock and drives every reset. A test asks for a reset with `reset_dut()` or `request_reset()`, and SystemC asserts every reset of the block at its clock's next rising edge and releases it `releaseCycles` edges after the request drops (section 9.6, "A reset during the test") | the model, its BFMs and the RTL run in one kernel from `sc_main`, and the SystemC side's clocks and resets drive both. A reset the testbench drove itself would reach the RTL and not the model's BFMs |
| After a mid-run reset the components return to their reset state through `phase.jump()` back to `reset_phase` or `pre_reset_phase`, and the runtime phases run again | each driver, monitor, counter, comparator, replay log and lane watchdog stays in `run_phase` and restarts its own run loop through `a2c_run_reset_aware()` at the first edge that samples its domain's reset asserted, keeping what it has checked so far (section 9.6) | the components and the base test run in `run_phase`, which a jump of the runtime schedule does not restart. A jump would also kill sequences blocked in the sequencer, and UVM 1.2's sequencer then takes the driver's next `get_next_item()` as a second call. A reset belongs to one clock domain, and each component watches its own port's clock; a jump restarts the whole schedule. The counters, comparators and lane watchdogs keep their history across the reset, the pairs compared and the lane deaths, which a restarted phase would have to save |
| A reset can be applied with any DUT | a reset during the test is refused in a run that holds the model: `reset_dut()` raises `A2C_RESET`, and the model and both snapshots tie `uvm_reset_req` low | the SystemC model has no mid-run reset, so the model lane cannot abandon its work as the RTL lane does (section 10.1) |
| A test overrides `run_phase` or the runtime phases, such as `reset_phase`, `configure_phase` and `main_phase`, and raises its own objections | the generated base test uses `run_phase` only and raises its one objection. A test puts its stimulus in `run_body()` (section 9.6). A hand-written test may still object in a runtime phase; the drain and the run timeout handle it | the base test owns the objection, the reset wait, the end-of-test wait and the work count the run timeout derives its budget from |
| The test ends when its sequences complete and the objections drop, often with a drain time or a scoreboard's empty check | the test declares each output's transaction count with `expect_count()`, and `wait_for_outputs()` waits for every count and then a quiet window (section 9.6) | the run must end when the DUT has delivered what the stimulus implies, and only the test knows how much that is. In paired mode, `expect_from_model` takes the count from the model lane instead (section 9.6, "Completion from the model lane") |
| `+UVM_TIMEOUT` or `uvm_top.set_timeout()` bounds the run in simulated time, and ends it with a `PH_TIMEOUT` `UVM_FATAL` | `a2c_run_timeout` counts clocks of the block's first clock against a budget derived from the declared work, raises one `A2C_RUN_TIMEOUT` `UVM_ERROR` and ends the task phases prematurely. UVM's timeout stays as a second limit (section 9.6) | a fatal skips `check_phase`, which reports what is missing. A budget in clocks does not depend on each project's clock period |
| A base test is a library class, and generated code and hand-written code live in separate files | the base test, with its knobs and their plusarg and `uvm_config_db` code, is generated into each block's test package, between markers in the file that holds the project's tests. The generated `<block>_fail_test`, `<block>_rt_fire_test` and `<block>_model_mismatch_test` extend the project's `<block>_smoke_test` (section 9.6) | the generated tests reuse the smoke test's stimulus, so each negative test proves its check on a run that sent traffic. Renaming the smoke test breaks them. Moving the knobs into a library class is not planned (section 10.2) |
| No virtual sequencer is required, but multi-agent stimulus usually runs as a virtual sequence | no virtual sequencer or virtual sequence is generated. A test starts sequences on each agent's `sqr` from `run_body()` | not built. A project adds a virtual sequence where ports need coordinating |
| The UVM library is an IEEE 1800.2 implementation | the flow runs Accellera UVM 1.2 on both vendors, `CDNS-1.2` and `uvm-1.2` (section 9.7). The library and the generated `examples/uvmRegs` bench also compile and elaborate against IEEE 1800.2-2020, Xcelium's `CDNS-IEEE-31`, with no deprecated API; nothing runs on it. The 1800.2-2017 kit, `CDNS-IEEE`, rejects the library, because it makes `uvm_comparer`'s `show_max` and `miscompares` local and the comparators read them. `uvm_phase::end_prematurely()` (IEEE 1800.2-2020 9.3.1.9.3), `uvm_resource_pool::lookup_regex()` and `get_highest_precedence()` (C.2.4.4.7, C.2.4.4.2) are in the standard. The `UVM/RSRC/NOREGEX` catcher is added only under UVM 1.2, the one library that raises that warning (section 9.5). `connect_in()`, `connect_out()` and `a2c_txn_digest::watch()` find a monitor's ports through the `uvm_port_component` UVM creates as each port's child, which the 1800.2 kits mark as specific to the Accellera implementation. The testbench module writes `uvm_root`'s `finish_on_completion` field, and `a2c_reg_map` reads the register map internals | the vendor-bundled UVM 1.2 libraries were the first target. The standard defines no port component, so it gives no way to reach a port from its owner by name. The lookup stays. The 1800.2 kits that Xcelium and VCS ship both carry the class. Running on 1800.2 is open (section 10.2). The documentation uses IEEE 1800.2 terms |

#### Pins and clocks

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| Interfaces carry four-state signals, and X or Z checks are SVA or monitor checks that report through UVM | the HDL wrapper's pins and the testbench module's pins are two-state `bit`. The `<type>_xcheck` modules inside the HDL wrapper check X and Z on the RTL side and fail the run through DPI and `errorCode::fail`, outside the UVM report summary (section 9.4) | the simulator shell binds the pins to two-state SystemC signals. The checkers sit on the RTL side of that boundary and run in every VCS and Xcelium run with an RTL DUT, UVM or not |
| Drivers and monitors time their pins with a clocking block | `a2c_clk_if` edge tasks: drivers change pins at the rising edge plus 100 ps, `DRIVE_SKEW`, and monitors sample at the falling edge | a clocking block in a shared clock interface cannot drive the signals of other interface instances, and a `#1` output skew is a whole period of a 1 ns clock. The skew is fixed, so `make db` rejects a `hasUvm` block with a clock period of 200 ps or less (section 9.1) |

#### Agents

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| Agents are master and slave, or initiator and target | roles `A2C_SRC` and `A2C_DST` | they match the interface modports and the SystemC BFM names |
| One driver class per role | one role-switched `<type>_driver` for the handshake and memory types | each role's code is short, as in `rdy_vld` |
| AMBA 5 terms: Requester and Completer for APB, Manager and Subordinate for AXI | master and slave for the AMBA driver classes; each package header gives the AMBA 5 terms | they match `apb_master_driver` and UVM 1.2-era VIPs |
| Every active agent has a sequencer | ack-only, memory-backed and level `A2C_DST` drivers have no sequencer | nothing is chosen per transaction |
| A driver extends `uvm_driver` | `status_driver` extends `uvm_component` | it holds a level from its config and takes no items |
| An agent exports its monitor's items through an agent-level analysis port, and has a sequencer class of its own | an agent exports no `ap`; a subscriber connects to `<agent>.mon.ap`, or in paired mode to `<agent>.model_mon.ap` for the model lane. Sequencers are plain `uvm_sequencer #(<item>)`, except `req_ack_sequencer`, which holds the request FIFO its responder reads | not built |
| Classes a test overrides through the factory have a type name | the agent classes of every type but `notify_ack`, which has no payload, and most of their items, drivers, monitors and sequences are parameterized by the port's types and registered with `uvm_component_param_utils` or `uvm_object_param_utils`, so they have no factory name. An override names the full specialization, as section 9.10 shows for the responder sequences | the payload types come from the port at each variant. The variant package gives each port's specializations a typedef, `<port>_agent_t` and `<port>_item_t` |
| One agent per pin set; a second DUT gets its own agents, and a layer above them coordinates the two | in paired mode one agent drives and monitors both pin sets of a port, its lanes. The drivers share the lane logic through `a2c_lane_driver`: one drive point for both lanes, a handshake per lane, the replay log of a responder and the lane watchdog of a master (sections 9.10 and 9.12) | both DUTs must see the same values on the same clocks with no DPI transport, and a responder's model lane must replay the DUT lane's decisions |
| Any UVM agent for a protocol, such as a vendor VIP, can drive the port | in paired mode only a lane-aware agent can: an a2c agent, or one that implements `a2c_paired_agent` with a hand-written driver, best built on `a2c_lane_driver`, and is compared through `a2c_paired_port` (section 9.10). A vendor VIP's monitors can be reused unchanged; its driver cannot. Outside paired mode any agent works | an agent of one pin set cannot keep two DUTs on one stimulus, bound one lane against the other, or replay a responder's decisions on the model lane |
| An agent extends `uvm_agent` and wires its own components in `connect_phase` | every agent whose driver is an `a2c_lane_driver`, and Pro's `lmmi`, extends `a2c_lane_agent`, which joins the agent's lanes to the pin registry in `connect_phase` and reports a passive agent no active one owns at `end_of_elaboration_phase`, from four hooks the agent supplies. status and raw extend `uvm_agent` | the paired-mode wiring between the agents of one port is the same for every protocol, and wiring it per agent is where it went wrong. status and raw have no lane driver and no handshake, so no death or cut reaches their passive agents |
| Timing choices, such as ready levels, delays and gaps, are `rand` fields or policy objects, constrained with `randomize() with {...}` | the config knobs and the item's `gap` are `rand`, and every `A2C_DST` driver takes its ready levels and delays from a factory-created `a2c_ready_policy` (section 9.10). Inside the ranges the knobs set, the AXI masters draw `rready` and `bready` and the AXI slaves the `reorder` pick with `$urandom_range()` | a per-beat constraint would call the solver for every beat, and the range knobs already bound each draw. The policy is built for `A2C_DST` drivers only, so a master's ready stays a percentage knob, and the reorder pick is not timing. Seeds reproduce on one simulator either way (section 9.7) |
| Item fields all take part in `compare()` | the item fields `gap` and `delay` are left out of `do_compare` | they are stimulus timing, not payload |
| A memory the testbench holds is a `uvm_mem` | `a2c_mem_model` for a memory the DUT reaches through a port; `uvm_mem` only for register-mapped memories | `uvm_mem` needs a register model and a map, and a memory behind a DUT port has neither |

#### Checking

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| Checking lives in scoreboards in the env that extend `uvm_scoreboard`, fed by a predictor | the paired-mode comparators, `model_cmp`, sit inside each agent and extend `uvm_component` through `a2c_comparator_base`. They compare the DUT lane with the model lane, so they need no predictor. A project's own scoreboards in `<block>_tb_env` follow the convention | each type knows what it can compare in each role, and a generated per-port scoreboard would need a new interface definition key. `uvm_scoreboard` adds no behaviour to `uvm_component` |
| `uvm_in_order_class_comparator` | `a2c_in_order_comparator` | it reports a mismatch as an error, reports items either lane left unpaired, and has the cut, death, midstream and injection hooks |
| A second DUT is a reference model, and its components carry a `ref_` prefix | lanes, the DUT lane and the model lane; the `model_` prefix: `model_vif`, `model_mon`, `model_cmp`, `<port>_model` | one agent drives two pin sets of one port, and "lane" names a pin set without implying a second agent. `model_` names what the lane holds and matches `UVM_DUT=model`; `ref_` would hide which DUT it is |
| A reactive responder computes each response from its own sequence | `a2c_replay_log`: the responder's DUT lane records each response and its model lane replays it | the model lane never makes a decision, as `synchLock` shares a decision in tandem with the RTL as the sender |
| A register that cannot be compared is excluded through the register model, by volatility or `set_compare(UVM_NO_CHECK)` | the skip list, an address list on `a2c_reg_comparator`, with `same_but_data()` comparing what a skipped read still checks | only an address list covers an unmapped address and `lmmi`, which has no register model |
| The env connects a monitor's `ap` to a subscriber's `analysis_export` in `connect_phase` | `a2c_rt_checker`'s `connect_in()` and `connect_out()` and `a2c_txn_digest::watch()` take the monitor component and find its ports among its children: `get_child("ap")` for the checker, every port component of the item type for the digest | the checker also reads the monitor's flow counts, `a2c_flow_counts`, and the digest hashes every analysis port of the monitor, so one call takes both. The lookup relies on the `uvm_port_component` that the Accellera implementation creates as each port's child, as the UVM library row above says |
| A component reads a setting with `uvm_config_db#(T)::get()` of one type | the drain, lane rule, real-time checker and run timeout knobs are read through `uvm_resource_pool`, accepting `int unsigned`, `int` and `uvm_config_int`, and `bit` for a flag, at the highest precedence (section 9.6). `+UVM_CONFIG_DB_TRACE` does not show these reads | a test, a hand-written env and `+uvm_set_config_int` set these knobs with different integer types, and a typed `get()` would silently miss every entry of another type |
| Shared state lives in objects that the env creates and hands down through `uvm_config_db`, or in a `uvm_pool` | the output counter list, the replay drain, the joint stall record with its one run timeout, the real-time checker list, `a2c_pin_registry` and the child block catcher table are static members of classes in `a2c_uvm_pkg` | the drain, the joint stall rule and the run timeout span the whole simulation, and the pin registry links agents that share no component path, keyed by virtual interface handle, which a `uvm_pool` cannot index. An env-scoped context is not built, so two envs in one simulation share one drain, one joint stall record and one run timeout (section 10.2) |

#### The register model

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| The register map is a `uvm_reg_map` | a block with a memory, and every map above one, is an `a2c_reg_map`, a `uvm_reg_map` subclass (section 9.5) | UVM 1.2 steps a memory by its own width in bus words, and the decoder steps it by a row stride sized for the widest variant |
| UVM's own warnings pass unchanged | a report catcher demotes the `UVM/RSRC/NOREGEX` warning for child register blocks to a `UVM_HIGH` info (section 9.5) | UVM 1.2 registers each child block under its dotted full name and warns once per child. IEEE 1800.2 drops that registration |
| A parent's register model holds its own classes | a parent holds a reused child's register block class from the child's variant package (section 9.15), and a root block locks the model only when it has no parent | one class serves the child's own bench and its parents', so a test or sequence written against it runs in both |
| Registers have HDL paths for backdoor access | the generated register model has front-door access only, with no HDL paths | not built. A test that needs backdoor access or a backdoor-based built-in sequence cannot run (section 10.2) |

#### Coverage

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| `UVM_CVR_FIELD_VALS` is sampled through `sample_values()`, which a test calls to record the mirrored field values at points it chooses | each register's `cg_vals` samples the fields from the data of every access, in the `sample()` override that `uvm_reg_predictor` calls (section 9.16) | every access the predictor sees is recorded without a call in each test. A test that wants the mirror sampled at chosen points adds its own covergroup |
| The test calls `uvm_reg::include_coverage()` before the register model is built | the generated env calls it with the `UVM_COV` setting, and a test's earlier call wins | coverage follows the one build switch, and a test can still choose the models |
| A component is created with `type_id::create()` | each agent creates its coverage subscriber through `a2c_coverage#(T)::create()`, which restores the creating thread's random state after the call | constructing a component draws from the creating thread's random generator, so a coverage build would otherwise draw other stimulus for the same seed than a build without coverage |
| An agent's coverage collector samples its monitor's items | the stream and request-acknowledge subscribers also read the monitor's flow counters, for the idle and stall or wait clocks of each transfer | handshake timing is not part of the item, and the counters are the ones the real-time checker already reads |

#### Reuse in a composed root

| Convention | What the flow does | Reason |
| :--- | :--- | :--- |
| A block's reusable verification code is a package of its own | it is the user span of the block's variant package (section 9.15) | SystemVerilog cannot parameterise a package, and the variant package is the one already compiled per variant without a macro |
| A parent watches a child's ports with an instance of the child's env in passive mode | the parent's env has its own passive agents on the connections between its children | a child env builds agents with the child's types and config keys, and the parent's connections carry the parent's own types, which a child env cannot bind |

### 9.14 Debugging a run

A failing regression entry leaves its log at `regr/<session>/runs/<group path>/<test>/run_<n>/<test>.log` (section 5.5). Work through it in this order:

1. Find the first `UVM_ERROR` or `UVM_FATAL` and look its ID up in section 9.17. The reports after it are often its consequences, and the end-of-test reports that follow a run timeout or a joint stall say so (section 9.6).
2. Repeat the run with the `A2C_RERUN` command printed beside that error.
3. Add verbosity or waves to the repeated run. With the same seed and snapshot the stimulus is the same.

The commands below run from `examples/uvmMem/rundir`.

#### Repeating the run

Every UVM test prints one `A2C_RERUN` `UVM_INFO` at `UVM_NONE` at `start_of_simulation_phase`, and the same line again just before the run's first `UVM_ERROR` or `UVM_FATAL`, so it sits beside the failure in the log:

```
UVM_INFO @ 0: reporter [A2C_RERUN] seed 3533507938: cd /proj/examples/uvmMem/rundir && build_xrun/run_uvm_uvmMem_rtl uvmMem_uvm --seed 3533507938 --verbosity=low --uvmTop uvmMem --uvmDut rtl +UVM_TESTNAME=uvmMem_random_test
```

The second print names the component that raised the error. The command is the run script and the arguments it got, with a seed of `random` replaced by the value the script drew, so pasting it into a shell repeats the run on the same snapshot. It runs the script directly, not through `dutRun.py`. Add plusargs or `WAVES_SCOPE` to it, or rebuild with `WAVES=1` first, to see more of the same run.

An error a test expects and demotes, through `a2c_expected_error` or `a2c_error_demoter`, prints no second line, since the base test registers the reporter after the build-time catchers. A run started without a run script, which has no `+a2c_rerun`, prints the plusargs the simulator received instead. `a2c_rerun` in `a2c_uvm_pkg` is the catcher that prints the line. A test that does not extend the generated base test calls `a2c_rerun::start()` from its own `start_of_simulation_phase`.

One regression entry runs again with a fixed seed through the launcher, which builds every snapshot first:

```
make regr_uvm_xcelium REGR_USER_OPTS="/both_dut/uvmMem_smoke_test --attr run.seed=42"
```

An entry that sets its own `seed`, such as uvmMem's random test with `"seed": "random"`, keeps it whatever `--attr` says; repeat that one from its `A2C_RERUN` line.

`seedRepro.py` checks that a seed reproduces. It runs the command twice and passes when both runs print the same `A2C_DIGEST` lines (section 9.7):

```
../../../seedRepro.py ../../../dutRun.py build_xrun/run uvmMem_uvm --seed 11 --verbosity=low \
    --uvmTop uvmMem --uvmDut both +UVM_TESTNAME=uvmMem_random_test
```

Its last line is `A2C_SEED_REPRO PASS: the digests match`, or `A2C_SEED_REPRO FAIL:` with the reason.

#### Waveforms

`WAVES=1` on the build makes the snapshot record waveforms in every run of it. Each vendor writes its own format:

| | Xcelium | VCS |
| :--- | :--- | :--- |
| Build | `-access +r` at elaboration | `-kdb -debug_access` at link and `VCS_DEBUG` defined (sections 1.2 and 3.4) |
| Run | the run script sources `include/make/a2c-waves-xrun.tcl`, which opens `waves.shm`, probes the scope with every level below it, then runs. The exit status is the simulation's | the UVM run script adds `+fsdbTrace +fsdbfile+waves.fsdb`, and the testbench module and the HDL wrapper call `$fsdbDumpvars` |
| File | `waves.shm`, in the directory the run starts from | `waves.fsdb`, in the directory the run starts from |
| Default scope | `sc_main`, the SystemC top, which holds the testbench module, the RTL, the SystemC model and its BFMs. SystemC ports and SV class objects are not probed, as xmsim warns | the UVM testbench module, `sc_main.<block instance>.tb_hdl`, which holds the RTL and the interfaces. SystemC objects are not dumped |
| `WAVES_SCOPE=<scope>` | probes that scope instead, such as `sc_main.uvmMem.tb_hdl.dut` for the RTL alone | dumps that SV instance instead, through `+a2c_waves_scope` |
| Viewer | `simvision waves.shm`; `simvisdbutil waves.shm -vcd -output waves.vcd` writes a VCD | `verdi -ssf waves.fsdb` |

On Xcelium:

```
make -j8 USE_UVM=1 USE_XCELIUM=1 UVM_DUT=both WAVES=1 all
../../../dutRun.py build_xrun/run uvmMem_uvm --seed 7 --verbosity=low --uvmTop uvmMem --uvmDut both \
    +UVM_TESTNAME=uvmMem_model_mismatch_test +a2c_model_mismatch_at=5
WAVES_SCOPE=sc_main.uvmMem.tb_hdl.dut build_xrun/run_uvm_uvmMem_both uvmMem_uvm --seed 7 --verbosity=low \
    --uvmTop uvmMem --uvmDut both +UVM_TESTNAME=uvmMem_smoke_test
simvision waves.shm
```

On VCS the same steps use the VCS targets and run scripts:

```
make -j8 USE_UVM=1 USE_VCS=1 UVM_DUT=both WAVES=1 all
../../../dutRun.py build/run uvmMem_uvm --seed 7 --verbosity=low --uvmTop uvmMem --uvmDut both \
    +UVM_TESTNAME=uvmMem_model_mismatch_test +a2c_model_mismatch_at=5
verdi -ssf waves.fsdb
```

Recording slows the run and its file grows with the run's length, so build with `WAVES=1` to debug a test, not for a regression. The build records `WAVES` with its options, so switching it rebuilds the snapshot. Each run overwrites the file in its directory, so two runs from one directory at once write over each other. Under VCS a non-UVM run has no run script, so it passes `+fsdbTrace` itself and the dump lands in `novas.fsdb` unless it also gives `+fsdbfile+<name>`.

#### Verbosity

The two sides of a run have separate verbosity controls:

- `--verbosity` sets the log level of the SystemC side: the model, its BFMs and the framework, as in every other flow. `--verbosity=low` keeps the logs short; raise it to follow the model.
- `+UVM_VERBOSITY=<level>` sets the UVM verbosity of every component, `UVM_MEDIUM` by default. The monitors log each transaction as `A2C_TXN` at `UVM_MEDIUM`, and the `raw` words and AXI beats at `UVM_HIGH` (section 9.10), so `UVM_HIGH` shows each beat.
- `+uvm_set_verbosity=<component path>,<id>,<level>,<phase>` sets one ID's verbosity on some components and leaves the rest of the log alone. `_ALL_` as the ID covers every ID. This pair keeps only the `out` port's transactions:

```
../../../dutRun.py build_xrun/run uvmMem_uvm --seed 7 --verbosity=low --uvmTop uvmMem --uvmDut rtl \
    +UVM_TESTNAME=uvmMem_smoke_test +UVM_VERBOSITY=UVM_LOW '+uvm_set_verbosity=uvm_test_top.env.out_agent.*,A2C_TXN,UVM_MEDIUM,run'
```

Both run scripts pass every argument that starts with `+` to the simulator, so plusargs go on the run script's or `dutRun.py`'s command line, or on a regression entry's `args+`. `--attr run.args+=<value>` splits its value on commas, so give a `+uvm_set_verbosity` through the regression file.

#### Reading an `A2C_MODEL_CMP` mismatch

A mismatch report names the comparator, the pair and, where the comparator keys its items, the key:

```
UVM_ERROR .../a2c_uvm_pkg.sv(785) @ 13000: uvm_test_top.env.raw_video_out_agent.model_cmp [A2C_MODEL_CMP] uvm_test_top.env.raw_video_out_agent.model_cmp: pair 5: DUT '{data:'{pixels:'ha090807}, frame:'{eol:'h0, sof:'h0, eof:'h0}}, model '{data:'{pixels:'ha090806}, frame:'{eol:'h0, sof:'h0, eof:'h0}}; DUT item sampled at 12500, model item at 10500; fields that differ, lhs DUT and rhs model: item.data: lhs = 'h50484038 : rhs = 'h50484030
```

- `pair <n>` counts the comparator's pairs from 1, in the order it compared them. On an in-order comparator the pair is the n-th item of each lane, or of each key.
- `sampled at` gives `$realtime` when each item reached the comparator, which is when the lane's monitor sampled the transaction and published it. It is printed in the units of the report's `@` time, the simulator's precision, ps in a bench built with `-timescale 1ns/1ps`. The `@` time is UVM's `$time`, rounded to whole time units, so in the example the DUT item sampled at 12.5 ns is reported `@ 13000`. Each lane has its own time because the two lanes run apart. Find the DUT lane's transaction on the port's interface at that time, and the model lane's on the `<port>_model` interface. A status comparator gives the time of each lane's latest value at the stable point.
- `fields that differ` lists each field of the item that differs as `<item name>.<field>`, with the DUT value as `lhs` and the model value as `rhs`, joined with `; `. A field with X or Z differs from one without. A struct field prints as its packed value, so `item.data` above holds the pixels and the frame markers together. The AXI items list beats as `data[<i>]`, `resp[<i>]` or `strb[<i>]` and a length difference as `beats`.

An unpaired-item report gives the first leftover item with its sample time, the time to start from when a lane stopped producing.

The field list comes from the item's `do_compare()`. Each base and Pro item passes every field it finds different to the comparer, with `comparer.compare_field("<field>", lhs, rhs, $bits(<field>))`, before it returns its verdict. The comparison and the verdict stay `===` on each field. A project item type that a comparator compares does the same for its fields to get a list, or uses the UVM field macros, which report fields through the comparer themselves. An item that does neither gives a report with no field list. A comparator that extends `a2c_comparator_base` and calls `check_pair()` itself gets the times by setting `pair_at[]` before the call, and the fields by comparing with `compare_items(dut, model)`.

#### From a pair to the waveform

`<block>_model_mismatch_test` injects a mismatch at a pair it chooses, so it shows the walk on a run that passes. In uvmMem's `both` run with `+a2c_model_mismatch_at=5`, the test demotes the report to an info:

```
UVM_INFO .../a2c_uvm_pkg.sv(943) @ 30000: uvm_test_top.env.out_agent.model_cmp [A2C_MODEL_CMP] expected, demoted to info: uvm_test_top.env.out_agent.model_cmp: pair 5 (injected mismatch): DUT '{word:'hbfb550b4}, model '{word:'hbfb550b4}; DUT item sampled at 29500, model item at 28500
```

1. Rebuild with `WAVES=1` and run the `A2C_RERUN` command. The stimulus is the same.
2. Take the port from the comparator's path: `out_agent` is port `out`. Its DUT lane is the interface `out` in the testbench module, `sc_main.uvmMem.tb_hdl.out` under Xcelium, and its model lane is `out_model` beside it.
3. Go to the DUT lane's time, 29500 ps. It is a falling edge of the port's clock, where the monitor sampled `out.vld` and `out.rdy` high with `out.data` at `'hbfb550b4`. The rising edge after it transfers the item.
4. Go to the model lane's time, 28500 ps, on `out_model`. The lanes run apart, so the times differ.
5. To confirm the pair, count the falling edges with valid and ready high on each lane since the reset release. On an in-order comparator the fifth is pair 5; on a keyed one, count per key.

#### When a check fires

**The real-time checker.** `A2C_RT_GAP`, `A2C_RT_DEADLINE` and `A2C_RT_REFUSAL` name the output, the unit and the bound.

1. Read the checker's `A2C_RT` summary at `check_phase`. It gives the worst lag, gap and refusal, each with its unit. A worst value just over its bound points at a bound set too tight. One far over it, or a unit that never completed, is a stall.
2. Repeat the run with the checkers off, to see whether anything else fails. `+uvm_set_config_int=uvm_test_top.env.*,a2c_rt_off,1` turns every checker under the env off, and a rule's plusarg at 0, such as `+a2c_rt_lag_cycles=0`, turns that rule off.
3. Open the waves at the first report's time. `A2C_RT_DEADLINE` gives when the anchor input unit ended, and `A2C_RT_GAP` the open unit's last beat.
4. If the design is right and the bound is wrong, change the bound in the test's constructor and say in a comment what the new value guarantees (section 9.6, "Wiring a checker into a project"). Do not loosen a bound in a regression entry to make a run pass.

**`A2C_MODEL_THROTTLE`.** A paired-mode master held its next item back because the model lane was not ready while the DUT lane was. That is a model defect: the model takes its input later than the RTL, through shallower queuing or by waiting on the clock (section 9.12, "Lane rules"). The message names the port and what the model lane waits for.

1. Search the run log for the clock-paced notice, `the model came back exactly one clock after each of 32 transfers in a row`. It names a port whose model waits on the clock between calls (section 9.11).
2. Otherwise compare the model's queuing on that port with the RTL's, such as a FIFO depth or a thread that does other work between reads.
3. Fix the model. `+a2c_model_throttle_cycles=0` turns the rule off, which shows whether other errors remain. It never belongs in a regression entry.

**`HDL lowered ready`.** An `A2C_BFM_CONTRACT` error whose text reads `HDL lowered ready after the sample point where the model's call completed`. It also fails the run on the SystemC side. The RTL lowered a ready, `ack` or `pready` after the BFM had read it high at the sample point and completed the model's call. The cause is a combinational path in the RTL from a pin that another BFM drives to that ready (section 9.11).

1. The message names the sample point and the BFM ports that drove a pin in that time step. Those pins are the candidates.
2. In the waves, find which of them changed in the time step in which the ready fell.
3. Fix the RTL: register the ready, or remove the path. The model is not at fault, and no knob turns the check off.

**`HDL changed read data`.** The same kind of error, whose text reads `HDL changed read data after the sample point where the model received it`. The BFM handed the model the `rdata`, `prdata`, `lmmi_rdata` or `read_data` on the pins at the sample point, and the pins held other data at the next rising edge, where the RTL transfers it. The cause is a combinational path from a pin another BFM drives to that read data. The message gives the time the read data was sampled and the candidate BFM ports, and the steps above apply, with the read data in place of the ready.

### 9.15 Reuse in a composed root

A root that composes child projects reuses the UVM code of each child block with `hasUvm`. Two things carry over: the child's register block class and the library the child keeps in its variant package.

#### Which children a top reuses

`projectCreate.deriveUvmReuse` walks each UVM top's instance tree with each instance's parameter values, resolved as for the register tree: the instance's variant, `containerParam`, `inheritContainerParam`. An instance of a `hasUvm` block reuses that block's standalone variant whose values equal the instance's. A block without params has one variantless package, which every instance reuses. An instance whose values match no standalone variant reuses nothing in that top: the parent generates its register classes as before, and `make db` prints an info line naming the top, the instance and the child. A block's tops all compile one list, the union of the matches over every top, so the test package, which serves every top, can name a child class wherever one top reuses it. It goes in `UVMNAMES[<block>]['tops'][<variant>]['reuse']`, one row per (block, variant), below-first. The manifest lists their variant package files in `A2C_UVM_REUSED_SV_<top>`, and `a2c-uvm.mk` compiles them before the top's own. Only the child's variant package enters the parent's build: not its test package, testbench module, SystemC wrapper or registrar. The child's own `make gen` writes the file and the parent never regenerates it, so generate each child before its parent. At `make db` the manifest stops with an error naming the child's project when a reused file of another project does not exist, and when a reused (block, variant) has no `uvmPkg` file in the child's file map.

Parent code names a child class with its package, `<child>_<variant>_uvm_pkg::<class>`, and never imports a child package with a wildcard: every variant package declares the same typedef names, `<port>_item_t` for example.

#### The register model

A reused instance in a hierarchical register model is a member of the child's register block class, `rand <child pkg>::<child>_reg_block <instance>;`, built with that class's `type_id::create()`. The parent generates no class for it or anything below it. An instance reuses a package only when every variant of the parent reuses the same one, because each variant package declares the same register block classes. Where the variants differ, the parent generates its own classes for that instance in every variant, and `make db` prints an info line naming it. Since a reused instance's subtree is the child's class, the parent generates no `<parent>_<path>_reg_block` class for anything in it, and hand code that names such a class stops compiling once the child is reused. A generated root register block calls `lock_model()`, and `check_overlaps_once()` where section 9.5 says so, only when `get_parent()` is null, so the same class is the root of the child's bench and a member of its parent's.

#### The library

Code the child's bench and a parent's bench share goes in the user span of the child's variant package (`// user package items here`): checks, scoreboards, sequences. It is compiled in both benches, so it imports no `` `A2C_UVM_PKG `` and names nothing of the test package. It can name the variant package's register block, item typedefs and localparams, and import `a2c_uvm_pkg`. A contract that reads the register mirror reads it through a register block handle the bench sets, which in a parent is the reused member of the parent's model. A block with several standalone variants keeps the library in one `.svh` that each variant package's span includes. The span compiles in a parent with the parent's include path and defines, and with the parent's `` `A2C_UVM_PKG ``, so it must depend on none of them: the parent's rundir puts the `.svh` directory on `EXTRA_HDL_INCDIRS` itself, as the child's does.

#### Connections between children

The env of a `hasUvm` block with children has a passive agent and a digest per connection between two of its children whose type has a UVM agent and is not a register bus. The agent is named `<channel>_agent`, where `<channel>` is the name the block's RTL gives the connection's interface instance. The testbench module publishes the RTL's own instance in the runs that hold the RTL: `dut.dut.<channel>` for a block without variants, and `dut.u_wrapper.dut.<channel>` for a variant top, whose wrapper holds the block as `u_wrapper`. The env builds these agents only in those runs: the model's connections are inside SystemC. Each agent samples on the connection's clock: its `clock:`, else the clock the source instance binds to its source port's clock domain. The env lists in a comment each connection it cannot watch, with the reason: a payload local to the block's module, which no package declares, a clock that is not one of the block's clock ports, or a channel with a boundary port's name. The agents have no counter, as nothing expects their traffic by default, and their transfers do not count as progress for the joint stall rule (section 9.10), since a child's traffic can go on while the boundary deadlocks. A test checks one by attaching its own subscriber to `<channel>_agent.mon.ap`, so a defect in one child fails first at that child's output connection.

`examples/uvmReuse` is the end-to-end bench. Its root `uvmReuseChain` holds two instances of the child project's parameterised leaf `uvmReuseLeaf`, which has a register and a configuration sequence, and a counter pair on a second clock. `uLeafA` reuses the leaf's w8 package in both tops; `uLeafB` matches w8 in v8 and w4 in v4, so its register classes are the root's own and both leaf packages compile in each top. The chain's test checks `out` against the chain of both leaves' contracts and the internal connection `mid` against `uLeafA`'s, and `uvmReuseChain_stall_test` deadlocks the boundary while the counter pair runs and passes only on one `A2C_JOINT_STALL`. Its SystemC and Verilator runs and RTL lint are the `uvm-reuse` pipeline target, and `make regr_uvm_xcelium` in each project's rundir runs its UVM regression.

### 9.16 Coverage

`UVM_COV=1` on the build collects three kinds of coverage, and `make uvm_cov_merge` merges the runs' databases into one report:

- **Agent coverage.** Each agent builds a coverage subscriber, `cov`, on its DUT lane's monitor.
- **Register coverage.** The generated register model covers each register's field values and each block's address map, sampled by the env's predictor.
- **Code coverage** of the RTL DUT: line or block, condition or expression, FSM, toggle and, under VCS, branch and assertion coverage, limited to the HDL top the testbench module holds.

Coverage is off by default. Without `UVM_COV` no covergroup is constructed, no coverage option reaches the simulator, and the simulator command lines, the run scripts and the run logs are those of a build that has no coverage code, apart from the source line numbers UVM prints. A `UVM_COV=1` build draws the same stimulus for a seed as the build without it; its run log adds only the simulator's coverage lines.

#### What each agent covers

| Agent | Subscriber | Covergroups, sampled once per item on the DUT lane |
| :--- | :--- | :--- |
| `rdy_vld`, `push_ack` | `a2c_flow_coverage` | `cg_flow`: `idle`, the clocks since the previous transfer, or since reset release, on which the source offered nothing; `stall`, the clocks the sink refused the offered beat; and the two crossed. Bins: 0, 1, 2-3, 4-15, 16 and more |
| `axi4_stream` | `axi4_stream_coverage` | `cg_flow` as above, and `cg_last`: whether the beat ends a packet |
| `pop_ack`, `req_ack` | `a2c_wait_coverage` | `cg_wait`: `idle`, the clocks with no request since the previous transfer; `ack_wait`, the clocks the request waited for its acknowledge; and the two crossed, with the bins of `cg_flow` |
| `apb`, `memory`, Pro `lmmi` | `<type>_coverage` | `cg_access`: read or write, the address in 16 equal ranges of `addr_t`, and the two crossed |
| `axi_read`, `axi_write` | `<type>_coverage` | `cg_burst`: burst length (1, 2, 3-4, 5-8, 9-16, 17-256 beats), size (one bin per size up to the data bus width, or the full width alone without `BYTE_LANES`), burst type, and length crossed with type, without the lengths WRAP and FIXED cannot take |
| `notify_ack`, `status`, `external_reg`, `raw` | none | see "What the flow does not cover" below |

Each subscriber extends `uvm_subscriber` of the agent's item and connects to `<agent>.mon.ap`. In paired mode that is the DUT lane, the RTL; the model lane, `model_mon`, is never sampled, so each transfer is counted once. The passive agents on the connections between a composed block's children (section 9.15) have no model lane and build their subscribers too, so a `UVM_COV=1` run of the RTL also covers the traffic between the children. The idle and wait counts come from the same monitor counters as the real-time checker (section 9.6). Every covergroup sets `option.per_instance` and is named after its component, such as `uvm_test_top.env.in_agent.cov.cg_flow`.

The agent config's `has_coverage` decides whether the agent builds `cov`. A `UVM_COV=1` build sets its default to 1, and a `has_coverage` bit set in `uvm_config_db` for the agent overrides it, so a test turns one agent off:

```systemverilog
uvm_config_db#(bit)::set(this, "env.side_agent", "has_coverage", 0);
```

#### Register coverage

The generated register model follows UVM's `build_coverage()` protocol. Each register class has `cg_vals`, one coverpoint per field over the field's bits, and constructs it when `has_coverage(UVM_CVR_FIELD_VALS)`. Each register block class with registers has `cg_map`, one bin per register offset crossed with read and write, without the write of a read-only register, and constructs it when `has_coverage(UVM_CVR_ADDR_MAP)`. Both override `sample()`, which `uvm_reg_predictor` calls for every bus access it predicts, so they record every access the register bus agent's monitor sees, including the ones a test makes without the register model.

The env calls `uvm_reg::include_coverage("*", a2c_uvm_pkg::a2c_reg_cov)` before it builds the model, and `regmodel.set_coverage(UVM_CVR_ALL)` after. `a2c_reg_cov` is `UVM_CVR_FIELD_VALS + UVM_CVR_ADDR_MAP` in a `UVM_COV=1` build and `UVM_NO_COVERAGE` otherwise. The first `include_coverage` setting wins, so a test that calls it in its `build_phase` before `super.build_phase()` chooses the models itself, for example `UVM_CVR_ADDR_MAP` alone. Memories keep `UVM_NO_COVERAGE`: `uvm_reg_predictor` does not sample memory accesses.

#### Building and running

`UVM_COV=1` needs `USE_UVM=1`. It adds `+define+A2C_UVM_COV` to the HDL arguments, the vendor options below to the elaboration, and coverage lines to the run script. The build records `UVM_COV` with its options, so switching it rebuilds the snapshot.

| | Xcelium | VCS |
| :--- | :--- | :--- |
| Elaboration, RTL in the snapshot (`rtl`, `both`) | `-coverage b:e:f:t:u -covdut <hdl top>` | `-cm line+cond+fsm+tgl+branch+assert -cm_hier <build>/vcs/run_<snapshot>.cm_hier`, a file holding `+moduletree <hdl top>` |
| Elaboration, `model` | `-coverage u`: the RTL is only an idle top | none: VCS collects covergroups without an option |
| Change the code metrics | `XRUN_COV_CODE`, default `b:e:f:t` | `VCS_COV_METRICS`, default `line+cond+fsm+tgl+branch+assert` |
| Replace the options | `XRUN_COV_OPTS` | `VCS_COV_OPTS` |
| Each run adds | `-covworkdir <dir>/cov -covscope <snapshot> -covtest <test>.<seed> -covoverwrite` | `-cm <metrics>` (not for `model`) `-cm_dir <dir>/cov/<snapshot>/<test>.<seed>.vdb -cm_name <test>.<seed>` |
| Run database | `<dir>/cov/<snapshot>/<test>.<seed>/`, beside the snapshot's model `icc_*.ucm` | `<dir>/cov/<snapshot>/<test>.<seed>.vdb`; the design is in `build/run_<snapshot>.simv.vdb` |

`<hdl top>` is the HDL top the manifest records for the UVM top as `A2C_UVM_HDL_TOP_<tb top>`, `<snapshot>` is `uvm_<top>_<dut>`, `<test>` is the run's `+UVM_TESTNAME`, or `notest`, and `<seed>` is the run's `--seed`; without one the name is `<test>` alone, and the next such run overwrites it. `<dir>` is `RL_RUN_DIR`, which `regrLauncher.py` sets to each run's `run_<n>` directory, or the directory the run starts from. Code coverage covers the HDL top and everything below it: the RTL, and in a `both` snapshot the RTL lane only, since the model is SystemC. simv hands its whole command line to `sc_main` (section 9.7), whose option parser skips `-cm`, `-cm_dir` and `-cm_name` with their values in a VCS build.

A regression collects coverage with `UVM_COV=1` appended to its build command, for example from `examples/uvmRegs/rundir`:

```
make regr_uvm_xcelium REGR_USER_OPTS="--attr build.command+=UVM_COV=1"
make USE_UVM=1 USE_XCELIUM=1 UVM_COV=1 uvm_cov_merge UVM_COV_RUNS=regr
```

#### Merging and reports

`make USE_UVM=1 USE_<VENDOR>=1 UVM_COV=1 uvm_cov_merge` finds every run database under `UVM_COV_RUNS`, default `.`, which holds the databases of runs started from the rundir and, under `regr/`, of every regression session, and writes to `UVM_COV_REPORT`, default `cov_report`:

| | Xcelium | VCS |
| :--- | :--- | :--- |
| Tool | `imc`, variable `IMC`. It ships with vManager, not Xcelium, so `IMC` may need the full path, such as `<vManager install>/Linux/bin/imc`. It takes an IMC licence | `urg -full64 +urg+lic+wait`, variable `URG`, which waits for a licence |
| Merge | `merge <runs> -out cov_report/merged -overwrite -initial_model union_all`, so runs of every snapshot merge | every run database with the design database of its snapshot, into `cov_report/merged.vdb` |
| Report | `summary.txt`, every metric by instance; `covergroups.txt`, every covergroup bin, with the register model's, which sit under no component; `html/` | `html/dashboard.txt`, `html/groups.txt` and the HTML pages |
| Log | `imc.log`, with the commands in `merge.tcl` | `urg.log` |

`make clean` removes `cov/` under the rundir and `cov_report`.

#### Adding coverage

A test adds or replaces covergroups through the factory: it extends the agent's subscriber, `<port>_agent_t::cov_t`, and overrides it before the env builds.

```systemverilog
class my_in_coverage extends dut_v0_uvm_pkg::in_agent_t::cov_t;
    covergroup cg_payload with function sample(dut_v0_uvm_pkg::in_item_t t);
        option.per_instance = 1;
        kind: coverpoint t.data.kind;
    endgroup
    `uvm_component_utils(my_in_coverage)
    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_payload = new();
    endfunction
    virtual function void write(dut_v0_uvm_pkg::in_item_t t);
        super.write(t);
        cg_payload.sample(t);
    endfunction
endclass

// In the test's build_phase, before super.build_phase():
dut_v0_uvm_pkg::in_agent_t::cov_t::type_id::set_inst_override(my_in_coverage::get_type(), "env.in_agent.cov", this);
```

A subscriber of a project's own connects to `<agent>.mon.ap` in the env's `connect_phase`, and is guarded with `` `ifdef A2C_UVM_COV `` to cost nothing in a build without coverage. A hand-written passive agent on the same pins as a generated one sets `has_coverage` to 0, or each transfer is covered twice. The agents create `cov` with `a2c_uvm_pkg::a2c_coverage#(T)::create()`, which restores the creating thread's random state afterwards: constructing a component seeds its random generator from that thread's, so otherwise a coverage build would draw other stimulus for the same seed (IEEE 1800 section 18.14.1). A project component created only for coverage uses the same call.

#### What the flow does not cover

- No coverage plan. Nothing in the YAML sets goals, weights or bins, and the report is not mapped to a verification plan. The bins are generic: address ranges are 16 equal slices of the address type, not the block's register map.
- No assertion or `cover property` in the interfaces or the HDL wrapper. VCS's `assert` metric counts only the RTL's own assertions.
- `notify_ack`, `status`, `external_reg` and `raw` agents have no subscriber: `notify_ack` and `status` carry no transfer worth binning, an `external_reg` port is covered through the register model, and `raw` has no transfer boundary.
- Error responses are not binned: `PSLVERR` on `apb` and the AXI `RRESP` and `BRESP`.
- Memories in the register model, and data values on stream ports.
- The SystemC model. Code coverage covers the RTL only; a `model` snapshot has agent and register coverage alone.

### 9.17 Messages

This is the one catalogue of the reports the library and the generated code raise. Each ID starts with `A2C_`. Other sections describe the checks and point here. A project's own IDs, such as uvmMem's `UVM_MEM_SB`, are the project's to document.

Read a failing run's first `UVM_ERROR` or `UVM_FATAL` first; section 9.14 says why and how to follow it.

| Id | Severity | Meaning | What to change |
| :--- | :--- | :--- | :--- |
| `A2C_BFM_CONTRACT` | `UVM_ERROR` | a SystemC BFM broke its contract with the model or the RTL, such as `SystemC stalled a backpressure: false producer` or `HDL lowered ready after the sample point where the model's call completed` (sections 9.8 and 9.11). The testbench module raises the first break of each check | the text names the BFM and its port. A stall break means the model or the RTL refused a `backpressure: false` port. `HDL lowered ready` means the RTL's ready depends combinationally on a pin another BFM drives (section 9.14, "When a check fires"). A test that provokes a break expects it with `a2c_expected_error` |
| `A2C_CFG` | `UVM_ERROR`; `UVM_FATAL` for wiring that stops the build, such as a missing agent config or an `a2c_reg_map` rule (section 9.5); `UVM_WARNING` for a knob set as an unread type | a log with `drain_deadline_cycles` below `drain_quiet_cycles`, or with no `clk_vif`; an input agent that `a2c_items_sent` cannot count; a drain knob, `a2c_lane_skew_cycles`, `a2c_lone_lane_cycles`, `a2c_joint_stall_cycles` or `a2c_model_throttle_cycles` whose winning `uvm_config_db` entry is not `int unsigned`, `int`, `uvm_config_int` or, for `a2c_drain_cut_expected`, `bit`; an `a2c_rt_checker` with no output, with a rule whose input or unit rule is missing, or with a monitor that has no flow counts; a counter with `a2c_expect_from_model` set and `dual` clear | raise the deadline or lower the window; give the driver's log its clock; set the knob as `int unsigned`, or the flag as `bit`, which the warning names; wire the checker as the error says; declare a single-lane counter's count with `expect_count()` |
| `A2C_CREDIT` | `UVM_INFO` at `UVM_MEDIUM` | at `report_phase`, a paired-mode `memory` responder's counts: the accesses its model's BFM held for credit, the sample edges at which held was high, and the accesses made without credit (section 9.12) | nothing; an access without credit is also an `A2C_REPLAY` error |
| `A2C_CUT` | `UVM_WARNING`; `UVM_INFO` when the cut dropped nothing or `drain_cut_expected` is set | the drain cut a port that never paused; the message gives the transactions left unchecked on each lane, and says whether the cut came at the deadline or on a re-cut's first clock | lower `drain_deadline_cycles` to cut sooner, end the stimulus before the drop, or set `drain_cut_expected` where the port is meant to stay busy to the end |
| `A2C_DIGEST` | `UVM_INFO` at `UVM_LOW` | at `report_phase`, one line per port and lane with the item count and a hash of every item (section 9.5) | nothing; `seedRepro.py` compares two runs' lines (section 9.7) |
| `A2C_DRAIN` | `UVM_WARNING` | a log neither settled nor still flowing at its deadline, or its clock stopped with a transaction open; the message says what kept it from settling | read the log's `A2C_REPLAY`. Raise `drain_deadline_cycles` only if the model lane is slow, not short |
| `A2C_EXPECTED_ERROR` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` when the count matched | at `check_phase`, an `a2c_expected_error` saw a number of matching errors other than its `count` (section 9.8) | too few means the provoked condition never happened; too many means it happened more often than the test expects |
| `A2C_FAIL_TEST` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` on a pass | `<block>_fail_test` did not see exactly the shortfall it causes, or its smoke test sent no stimulus (section 9.6) | read the other errors first. Until the smoke test sends stimulus, the fail test fails by design |
| `A2C_HOLD` | `UVM_ERROR` | a monitor saw a source drop or change a request, valid or payload before the handshake completed (section 9.10, "Monitor checks") | the side that drives the port broke the protocol: the RTL on a DUT `src` port, the agent or its sequence on a DUT `dst` port |
| `A2C_JOINT_STALL` | `UVM_ERROR` | no lane of any port made a handshake for `joint_stall_cycles` clocks of a master's port while a lane of it waited, in single or paired mode. Raised once per run; it names every port whose live lanes waited and what each lane waited for, each responder whose model lane waits, in the sentence `A2C_SKEW` gives, and the deaths declared before it. In paired mode the masters then declare the live lanes of every port dead, whatever each port's own `joint_stall_cycles`. In single mode no lane dies, and the run ends at the stall the way the run timeout ends it; in a test with no run timeout the masters go on waiting and count toward no second stall. In paired mode, when only model lanes wait, the message says so and adds the model-lane sentence of `A2C_SKEW`; when only DUT lanes wait, it says so and points at the RTL | the whole environment stopped, so the cause may lie in the DUT, the model or the stimulus: look for a deadlock between ports or an event nothing produces. When only model lanes wait, the RTL has finished and the model holds the run: fix the model. A memory access held for its credit is a model defect, as under `A2C_SKEW`. Raise `joint_stall_cycles` if the environment legitimately goes that long with no handshake anywhere |
| `A2C_MEM` | `UVM_INFO` at `UVM_LOW` | the first read of an unwritten word in an `a2c_mem_model`, with the fill it returned (section 9.10) | nothing; preload the model with `write()` where the fill matters |
| `A2C_MIDSTREAM` | `UVM_ERROR`; `UVM_INFO` under `+a2c_predict_midstream=1` | a register write, or a read of a volatile register or read-only memory, while outputs had transactions pending | move the access to after `wait_for_outputs()`, or skip the read's address on the register bus comparator |
| `A2C_MISMATCH_TEST` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` on a pass | `<block>_model_mismatch_test` did not see exactly one injected mismatch and nothing else (section 9.6) | read the other errors first; a comparator that compared fewer pairs than `mismatch_at` means the port received too little traffic |
| `A2C_MODEL_CMP` | `UVM_ERROR`; `UVM_INFO` at `UVM_NONE` for the line that says later mismatches are counted, and at `UVM_MEDIUM` for a comparison a lane death stopped | the model's output differs from the RTL's on a pair, a lane left items unpaired, or a status check failed | the RTL and the model disagree: find which matches the specification and fix the other. The message prints the pair index, both items, when each lane's monitor sampled its item, and the fields that differ (section 9.14). An unpaired report gives the first leftover item's sample time |
| `A2C_MODEL_CMP_MIDSTREAM` | `UVM_WARNING` | a mismatch inside a midstream window, or of a midstream read of a volatile register or read-only memory, under `+a2c_predict_midstream=1` | expected near a midstream write or read; remove the access or the plusarg to check those beats |
| `A2C_MODEL_THROTTLE` | `UVM_ERROR` | a paired-mode master held its next item, or on AXI its next address, W beat or outstanding slot, for `model_throttle_cycles` clocks in a row because the DUT lane was ready for it and the model lane was not (section 9.10). Raised once per port. The message names the port, the clocks of that hold, the knob and its plusarg, and what the model lane waits for, says that paired mode slowed the RTL's input to the model lane's pace so back-to-back input went untested, and ends with the model-lane sentence of `A2C_SKEW` | the model is untimed, so this is a model defect: it takes its input later than the RTL, through shallower queuing or by waiting on the clock. Fix the model to queue and buffer input as the RTL does. Raising `model_throttle_cycles` hides the defect |
| `A2C_PAIRED_CONTRACT` | `UVM_ERROR` | an agent compared through `a2c_paired_port` breaks the paired-mode contract (section 9.10, "An agent a2c does not provide") | implement the rule the message names |
| `A2C_NO_PAIRS` | `UVM_ERROR` | at `check_phase`, a comparator compared no pair of DUT and model items, so its port went unchecked | send traffic through the port, or set `a2c_allow_no_pairs` on the comparator where none is meant |
| `A2C_NO_STIMULUS` | `UVM_WARNING` | a generated test sent no transaction on any input, through an input agent's sequencer or a status input's `cfg.value`, and declared no transaction on any output counter; on a block with another input, the register bus does not count | send stimulus in `run_body()` and declare the outputs with `expect_count()`, or set `no_stimulus_expected` in a test meant to send nothing |
| `A2C_PASSIVE` | `UVM_INFO` at `UVM_LOW` | a passive paired-mode agent that can learn of a cut or a death found no active agent with its `cfg.vif` as its own, so it learns of neither on the port | nothing on a port no agent drives, such as an internal port of a top design. Where an active agent drives the port, give the passive agent that agent's interface instances |
| `A2C_PROTO` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` for an AXI or `lmmi` transfer left open on a dead lane or after a drain cut | a monitor saw a protocol rule broken, such as an `ack` with no request or `rlast` on the wrong beat, or transfers still open at the end of the run (section 9.10, "Monitor checks") | as for `A2C_HOLD` |
| `A2C_RAND` | `UVM_FATAL` | a `randomize()` failed: an agent config or a responder's response | the test's inline constraints conflict with each other or with the class's `c_valid` (section 9.10) |
| `A2C_REG` | `UVM_ERROR`; `UVM_FATAL` when the apb register adapter gets an item of another type | `write_reg()` or `a2c_reg_access_seq` got a bad status or read back a value other than the one expected (section 9.6) | the register named decodes wrongly, or another register shares its word |
| `A2C_REG_SKIP` | `UVM_INFO` at `UVM_LOW` | at `check_phase`, the reads each entry of a register bus comparator's skip list matched, one line per entry | nothing |
| `A2C_REPLAY` | `UVM_ERROR`; `UVM_FATAL` when a driver calls `replay()` with nothing recorded | at the end of the test a lane owes transactions: recorded responses the model lane never replayed, a model lane waiting for a response the DUT lane never recorded, a response or pick the model lane holds whose request it has not made, or a cut the lanes did not reach within `drain_catchup_cycles`. On `memory`, a model lane its BFM holds for credit is a model lane waiting for a record, and accesses the model lane made without credit are one more error at `check_phase`, with their count and the first of them. The fatal is a driver bug: the driver must check `can_replay()` first | a lane count mismatch is a design or model difference. A memory model lane held to the end is a model defect: the model made an access the RTL never made, or made it at an earlier point in its input than the RTL (section 9.12, input coupling). Memory accesses without credit mean the model's BFM ignores `<port>_model_credit`: it must hold access n until the credit exceeds n, as `memory_dst_bfm` does. A held AXI pick means the model keeps fewer requests outstanding than the RTL, which is a model defect (section 9.10). A held `lmmi` response means the model's master withdrew a request, which its monitor reports as `A2C_HOLD`. If the model lane is only slow after a cut, raise `drain_catchup_cycles` |
| `A2C_RERUN` | `UVM_INFO` at `UVM_NONE` | at `start_of_simulation_phase`, and again just before the run's first `UVM_ERROR` or `UVM_FATAL`: the seed and the command that repeats the run (section 9.14) | nothing; copy the command to reproduce the run |
| `A2C_RESET` | `UVM_ERROR` | `reset_dut()` was called in a run that holds the model, or on a block with no reset | reset only in a single-mode test on the RTL, `--uvmDut rtl` |
| `A2C_RESPONDER` | `UVM_ERROR` | at `check_phase`, a `req_ack` responder left more than one request in `request_fifo` (section 9.10) | a replacement responder's `body()` must take one request per response |
| `A2C_RT` | `UVM_INFO` at `UVM_LOW`; `UVM_ERROR` when failures went unprinted | the checker's summary at `check_phase`; the measure-only note on the model DUT; the count of failures beyond `max_reported` | read the summary's worst values to size the bounds |
| `A2C_RT_DEADLINE` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` when a reported unit ends late | output unit k had not ended `rt_lag_cycles` clocks after its anchor input unit ended, less the stall credit. Raised the clock the deadline is reached; the info at the unit's end gives how late it was | a late unit is a slow design, one with no info a hung one; compare the lag with the summary's first and worst |
| `A2C_RT_FIRE` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` on a pass | `<block>_rt_fire_test` found no real-time checker under `env`, a checker that paired no unit or did not fail each one, or a demoted `A2C_RT_DEADLINE` count other than the judged units (section 9.6) | wire a checker in the tb_env; a checker that paired no unit is missing its input or its unit rules |
| `A2C_RT_GAP` | `UVM_ERROR` | an open output unit went `rt_gap_cycles` clocks with no beat while its sink was ready, after the starvation credit. Raised once per unit; the message gives the unit's beats so far, its last beat, the raw idle and the credit | find the stall in the DUT; if the input caused it from further back than the window, raise `rt_latency_cycles` |
| `A2C_RT_REFUSAL` | `UVM_ERROR` | the DUT refused `rt_refusal_cycles` clocks of offered input within one input unit, not counting the clocks on which the sink stalled its output. Raised once per input unit | find why the DUT back-pressures its source |
| `A2C_RT_UNIT` | `UVM_ERROR` | an output unit ended before its anchor input unit had ended | the unit rules or the pairing (`in_units_per_out`, `out_units_per_in`, `anchor()`) do not match the design |
| `A2C_RUN_TIMEOUT` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` for a run that ended in time | the run phase of a generated test had not ended after its budget of clocks of the block's first clock, counted from its reset release. The budget is derived from the work the test declared, or fixed by `run_timeout_cycles` or `run_timeout.fix()`, and the message says which. Raised once; it gives the clocks per unit of declared work and names the ports whose masters wait and the objectors of the run phase and of each other running task phase. Those phases then end, and so does each task phase other than the run phase as it begins, so `check_phase` reports what is missing. An info at `UVM_NONE` names the progress rules a derived budget defers to, once, and another each phase ended as it began that held an objection. The info at `UVM_LOW` gives a passing run's length and budget, or says the run had no run timeout | read the ports and objectors it names and the `check_phase` reports after it. If the test is legitimately longer, raise `run_timeout_factor` or `run_timeout_floor_cycles`, or fix the budget with `run_timeout_cycles` or `run_timeout.fix()` |
| `A2C_SKEW` | `UVM_ERROR` | a master in paired mode declared a lane dead (section 9.10). The other lane completed the item, or on AXI took a burst's AR or AW, took one of its W beats, or completed it, and this lane had not `lane_skew_cycles` clocks later. Or this lane, alone since the other died, went `lone_lane_cycles` clocks without progress; that message calls the death a likely consequence of the first `A2C_SKEW`. A death declared earlier on another port, which may have stalled this one, is named in the clause described under the drain, right after "declares the <lane> lane dead". Before the sentence about the lane that serves from then on, one that starts "Responders whose model lane waits" names each `A2C_DST` driver whose model lane waits for a transaction the DUT lane has not made, with the transaction and since when. It marks a memory port's wait as "a memory access held for its credit", and one more sentence then says that the model makes that access at an earlier point in its input than the RTL and how to fix the model. The message names the item or burst, on AXI the channel, the dead lane, the knob that bounded it, and the lane that serves the sequence from then on. A skew death ends with a last sentence on the trailing lane: for the model lane, that the model is untimed and the RTL never waits on it, so a trailing model lane is a model defect, and to fix the model to queue, buffer and arbitrate input as the RTL does; for the DUT lane, that the model lane has finished, so the cause is in the RTL or the input it waits for. The master raises it once per lane | a lane that stopped answering is a design or model difference. A trailing model lane is a model defect, not a slow model to wait for: fix the model, since raising `lane_skew_cycles` only hides it. A memory access held for its credit is a model defect, which no knob fixes: the model makes the access at an earlier point in its input than the RTL. Fix the model as section 9.12, input coupling, describes. Read the first `A2C_SKEW` before the second, and raise `lone_lane_cycles` only if the live lane just stalls longer than it allows |
| `A2C_STALL` | `UVM_ERROR` | a `backpressure: false` port was stalled (section 9.10, "Monitor checks") | the sink of such a port must take every beat: fix the side that drives its ready |
| `A2C_STATUS` | `UVM_INFO` at `UVM_MEDIUM` | a status value logged under the `off` policy | nothing |
| `A2C_TXN` | `UVM_INFO` at `UVM_MEDIUM`; at `UVM_HIGH` for `raw` words and AXI beats | one line per transaction a monitor publishes, with its sample time in ns and the item (section 9.10) | nothing; select it with the verbosity plusargs (section 9.14) |
| `A2C_TXN_COUNT` | `UVM_ERROR`; `UVM_INFO` at `UVM_LOW` for the count received, and for a transaction that arrives after its shortfall was reported | an output counter was short of its expected count at the deadline, had more after the quiet window, or at `check_phase` held a count no wait covered. In paired mode it names the lane (section 9.5) | compare with the test's `expect_count()` calls. A short DUT lane is a DUT that stopped delivering. Read any `A2C_RUN_TIMEOUT` or `A2C_JOINT_STALL` before it |
| `A2C_UNCOMPARED` | `UVM_WARNING` | at `end_of_elaboration_phase`, a paired-mode `raw` output that nothing compares (section 10.1) | check the port on each lane with a project scoreboard, a contract-style check or an assertion |
| `A2C_XZ` | `UVM_ERROR` from a comparator or a monitor; a `$display` line, outside UVM, from an X/Z checker | one name for two checks. Under the `bounds` policy, a status value with X or Z (section 9.12); on a four-state boundary such as the loopback, an X or Z a monitor samples. In the generated testbench the `<type>_xcheck` modules print `A2C_XZ <time> <path>: <signal> is X or Z` and fail the run through `errorCode::fail` (section 9.4) | the side named drives an unknown value: find the signal the RTL leaves unset, or reset |

`A2C_SEED_REPRO` lines come from `seedRepro.py`, not from UVM (section 9.7).

## 10. Limits and open items

The four lists below do not overlap:

- 10.1, what the UVM flow does not verify. A verification plan covers these by other means.
- 10.2, limits of the framework: what a bench cannot do, or must work around.
- 10.3, paths that no base run has exercised.
- 10.4, build, tool and example items, which affect no verdict.

### 10.1 Not covered

The UVM flow does not verify the following. A plan that needs one of them covers it with a hand-written check, another flow or another tool, and does not count on this flow for it.

- **Reset of the model during a test.** The SystemC model, its channels and its BFMs have no mid-run reset, so a run that holds the model refuses `reset_dut()` with `A2C_RESET` (section 9.6, "A reset during the test"). Recovery after a reset is checked only on the RTL in single mode, by a project scoreboard or the counters, never against the model.
  The smallest addition that would allow it is a virtual `reset()` on `blockBase` that a model overrides to drop its state, a `clear()` on each channel, and a restart of each model thread through `sc_process_handle::reset()` when the reset asserts.
- **A reset of one clock domain alone.** `uvm_reset_req` is one pin, so a request asserts every reset of the block, each on its own clock. A reset of one domain while the others run, as a block with a separately reset interface sees, is not verified.
- **Reset timing.** SystemC asserts a requested reset at a rising edge of its clock and holds it for at least `releaseCycles` edges. An asynchronous assertion between edges, a short pulse, and a reset asserted while the clock is stopped are not generated.
- **Coverage closure.** `UVM_COV=1` collects generic agent, register and code coverage and merges it (section 9.16), but nothing ties it to a plan. The YAML sets no goals, bins or weights, and the agent bins know nothing of the design, such as which addresses are registers or which burst shapes the DUT must take.
  There is no assertion or `cover property` coverage of the interfaces, and no coverage of error responses, of register-mapped memories, of the `notify_ack`, `status`, `external_reg` and `raw` ports, or of the SystemC model's code. A closure argument needs project covergroups added through the factory (section 9.16) and a plan kept outside the flow.
- **Register reconfiguration under traffic.** In paired mode, configuration changes only while the datapath is quiescent: `a2c_midstream_guard` fails a register write, and a read of a volatile register or a read-only memory, while any output has transactions pending (section 9.12).
  So a design whose registers change under traffic, such as an interrupt status that software clears, a flow-control threshold or a DMA descriptor, is checked neither against the model nor against a contract. Only a single-mode run with a project scoreboard that samples the register state itself checks it.
- **Blocks whose outputs depend on input timing.** In paired mode both DUTs see the same values on the same clocks, but each lane completes on its own handshake, so the model does not see the RTL's exact input timing (section 9.12). A block whose outputs depend on when its inputs arrive, not only on their order, cannot be compared, because the transport that would replay the RTL's input timing to the model is not built. The model's timing is approximate, and the real-time checker only measures on the model DUT. Check such outputs against the specification on the RTL.
- **Ordering across ports.** Each port's comparator pairs that port's items in order, per ID on AXI (section 9.12). Nothing compares the relative order of transactions on two ports, such as an interrupt against the data that caused it, or a write on one memory port against a read on another. A project scoreboard that subscribes to both ports covers it.
  Paired mode also leaves unchecked whether the model's own order of accesses across memory ports would read the same words from a memory of its own, because the model lane reads the RTL's words (section 9.12, coverage boundary). A single-mode run on the model DUT with a scoreboard covers that.
- **raw outputs in paired mode.** The raw agent builds no comparator, and a raw output has no transaction counter, because raw has no transfer boundary. In paired mode a DUT raw output is monitored on both lanes and never compared, and its agent reports one `A2C_UNCOMPARED` `UVM_WARNING` naming the port at `end_of_elaboration_phase`, which does not fail the run. Against the model DUT the raw BFM is best effort (section 9.1). A raw output needs a project scoreboard, a contract-style check or an assertion on each lane.
- **Data-dependent output counts in single mode.** The generated base test ends when every output counter holds the count the test declared with `expect_count()` (section 9.6). In paired mode `expect_from_model` takes the count from the model lane. In single mode there is no model lane, so an output whose count depends on the data, such as a filter that drops items or a compressor, needs the test to compute the count from its stimulus.
  A DUT output of type `memory`, `apb`, `external_reg`, `status` or `raw` has no counter at all, and a run whose outputs have no declared count waits only for the quiet window. In paired mode each comparator must compare at least one pair (`A2C_NO_PAIRS`, section 9.12), so a port cannot go unchecked unnoticed. In single mode nothing checks how much a run compared.
- **Real-time and latency checks on request-response ports.** `a2c_rt_checker` works on `rdy_vld`, `axi4_stream` and `push_ack` ports, whose monitors count flow. `pop_ack`, `req_ack`, AXI, `memory` and Pro's `lmmi` have no real-time rule and no request-to-response latency bound (section 9.6).
- **The model's internal connections.** In a composed root, the passive agents on the connections between children watch the RTL only (section 9.15). The model's connections are inside SystemC, so in paired mode a defect localised to a child is found on the RTL lane alone. Comparing the model's internal connections needs SystemC taps, which do not exist.
- **Nested composition.** A grandparent's env watches the connections between its own children only. The connections inside a composed child are not watched from the grandparent, and the child's internal agents do not carry over.
- **Gate-level, SDF and power-aware simulation.** The flow compiles the RTL that `rtl.f` names under `-timescale 1ns/1ps`. Its make files have no SDF annotation, timing check, netlist, or UPF and CPF options, and the pin-timing rule needs every boundary pin to settle between a rising edge and the next falling edge (section 9.10). Plan gate-level, timing and low-power simulation in another flow.
- **Clock-domain crossing and clock changes.** SystemC generates each clock at its declared period. All clocks start together at time 0, with no jitter and no phase or frequency change during the run, and a test cannot change a clock's period or stop a clock mid-run. The pins are two-state, so no metastable or unknown value reaches the testbench, and the flow runs no structural CDC check. A multi-clock block's crossings are exercised only at the phase relationship the periods give. Use a CDC tool.

### 10.2 Framework limits

#### Kept as they are

These limits are known and are not planned to change, because what they would add is small next to their cost.

- **Base test knobs in each block's file.** The generated base test carries its knobs, about twenty, with their plusarg and `uvm_config_db` code, in each block's test package rather than in a library class. The generated tests share that file with the project's: the `footer` tests extend the project's `<block>_smoke_test`, so renaming that class breaks them (section 9.6).
- **One a2c env per simulation.** The output counter list, the replay drain, the joint stall record, the run timeout, the real-time checker list and the pin registry are static members in `a2c_uvm_pkg` (section 9.13). Two envs in one simulation share one drain, one joint stall record and one run timeout, and each env's watchdogs see the other's traffic. A composed root therefore reuses its children's packages, not their envs (section 9.15).
- **One regression file per simulator.** A project keeps a regression file for Xcelium and one for VCS, and lists each test once per DUT group in each (section 9.7). Adding a test is an edit per group and per file, and nothing checks that the files agree.
- **Register model width and access.** The generated register model has front-door access only and no HDL paths, so backdoor reads and writes, and the built-in sequences that need them, are not available. A register or memory row wider than 64 bits stops `make db` (section 9.1).
- **Overloaded names.** `A2C_XZ` names two checks: the X/Z checkers' `$display` line, which fails the run outside UVM (section 9.4), and the status comparator's error under the `bounds` policy (section 9.12). "Credit" names the real-time checker's starvation and hold credits (section 9.6) and the paired-mode memory credit (section 9.12), which are unrelated. `a2c_error_demoter` stays beside `a2c_expected_error`. It demotes every match and checks no count, so a test that uses it checks the count itself, as the generated negative tests do.
- **No automatic real-time checker wiring.** The YAML does not say which input feeds which output or what closes a unit, so base generates no `a2c_rt_checker`. A project wires each one in its `<block>_tb_env` (section 9.6, "Wiring a checker into a project"). Until it does, the generated `<block>_rt_fire_test` fails.
- **IEEE 1800.2-2017 kits.** The library does not compile on them, such as Xcelium's `CDNS-IEEE`, because they make `uvm_comparer`'s `show_max` and `miscompares` local and the comparators read them (section 9.13).

#### Other limits

- **Accellera UVM 1.2 only.** The flow runs UVM 1.2 on both vendors. The library and `examples/uvmRegs` compile and elaborate against Xcelium's IEEE 1800.2-2020 kit (section 9.13), and nothing has run on it. A move needs `set_finish_on_completion()` in the testbench module, a check of `a2c_reg_map`'s memory stride (section 9.5), and the loopback and the examples run on a 1800.2 kit.
- **Active-high resets.** Every reset is active-low. The YAML has no polarity key, and the SystemC wrapper, `a2c_clk_if` and the HDL wrapper assume low means asserted. A block whose RTL takes an active-high reset inverts it inside its own RTL top.
- **Clock periods of 200 ps or less.** Drivers change pins `DRIVE_SKEW`, 100 ps, after the rising edge, which must stay below half the clock period (`a2c_clk_if.sv`), so `make db` rejects such a clock on a `hasUvm` block (section 9.1). A bench that needs a faster clock cannot use the flow.
- **Register bus adapter.** Only `apb` ships a `<type>_reg_adapter`, so a block with a register model must have an `apb` register bus (section 9.1).
- **Clock slowdowns.** A clock that slows by more than `clock_stop_cycles` periods in one step reads as stopped once, to a waiting counter and to the paired-mode drain. Nothing tells a stop from a large step in frequency until the next edge, and a counter reports its shortfall then. In the drain, a log idle at that point settles and is watched again from the next edge. A log that is not idle, or is cut, is given up and never watched again, so the run can end with an `A2C_DRAIN` warning and an `A2C_REPLAY` error for what the model lane still owes, even if it would have caught up on the slower clock.
- **Multicycle `rdy_vld` buffering.** A multicycle `rdy_vld` dst BFM takes a whole burst from the model when its first beat goes on the pins, so the model's last `writeClocked()` of the burst returns before the HDL takes any of it. Such a port has up to a burst of buffering that the model does not declare. `test_bfm_backpressure_checks.py` pins this behaviour. The same holds in co-simulation.
- **The clock-paced notice.** It counts a model's port call only when it comes no later than the delta cycle of the BFM's own clock edge, and nothing else tells a wait on the clock from other wake-ups. A model that waits on a clock that rises a delta cycle later, such as a copy of the BFM's clock, gets no notice.
  The mirror case does get one, though it never fails a run: a transactional model between two BFMs whose clocks rise a delta cycle apart can be woken by the earlier BFM's channel no later than the later BFM's edge delta. Only a memory channel records a wake from a BFM, so a channel of another type that woke its model with an immediate notification from a process at the edge would be counted the same way; no base or Pro channel does. The same holds in co-simulation.
- **Draws outside the solver.** A bench whose sequences or tests draw item fields or gaps with `$urandom()` or `$urandom_range()`, as the uvmMem example's sequence does, cannot have those draws constrained by a derived test or a factory override. Each draw needs rewriting as `randomize() with {...}` on the item.
- **`axi4_stream` packet length.** An `axi4_stream` src agent can send a packet longer than the buffer of a multi-cycle model channel. Its items carry no `maxTransferSize` limit.
- **The memory next-access rule.** It passes an X `read_data` word whose next access writes the same address, even when the design used the X word (section 9.10).
- **The AXI burst limit counts bytes.** On a bus wider than a byte it is below the channel's beat capacity. On a 32-bit bus with `maxTransferSize` 256, INCR bursts stop at 64 beats.
- **AXI read interleaving.** The AXI slaves do not interleave R beats of different bursts, and `reorder` reorders whole bursts. The master and monitors accept interleaved R.
- **`id_unbound` AXI responses.** With `id_unbound` set, an AXI master's response carries ID 0, not the ID of the item it answers.
- **A model left waiting.** A UVM failure that leaves a model's end-of-test voter waiting hangs the run, because the run ends only when every voter has voted. Pass `--scTimeLimit <us>` on model-DUT benches.
- **Models that register tests.** A model that calls `register_test_name` or `ADD_TEST` exits under UVM, because the UVM testbench config lists no tests (section 9.11). Some base example models do, such as simple's producer and mixed's blockD, so those blocks cannot run as a model DUT under UVM.
- **Reuse in a composed root.**
  - Every top of a parent compiles each package any of its tops reuses (section 9.15). Two packages whose user spans declare the same class, such as the same library in two variant packages of one block, or two blocks' libraries that pick one name, register the same factory name. UVM 1.2 warns, and a factory override by name of those classes is ambiguous. An override by type works.
  - A child instance whose parameter values match none of its block's standalone variants reuses nothing in that top, and an instance whose match differs between the parent's variants reuses nothing in any (section 9.15). The parent generates its own register classes, so a class of the child's library that needs the child's register block class, such as a typed configuration sequence, cannot serve that instance. Code written against `uvm_reg` handles serves both.
  - A reused instance removes the parent's generated `<parent>_<path>_reg_block` classes for it and everything below it. Hand code that names one stops compiling.
- **Mid-run reset.**
  - A `req_ack` or `pop_ack` responder whose sequence has not answered a request by the reset answers the first request after it with that response.
  - A comparator restarts at a reset only when it has the port's clock. The a2c agents give `model_cmp` their `cfg.clk_vif`; an env that compares a foreign agent through `a2c_paired_port` sets `model_cmp.clk_vif` itself.
  - `request_reset()` called directly in a run that holds the model never returns, because that snapshot ties `uvm_reset_req` low, and the run timeout ends the run. `reset_dut()` refuses with `A2C_RESET` instead.

### 10.3 Paths no base run has exercised

- The status policies run only in the loopback. No base UVM example has a status output or an external_reg port.
- The VCS steps for a second `hasUvm` block in one project are checked by unit tests only. Each base UVM project has one `hasUvm` block.
- No base example has a `backpressure: false` input, so no base UVM run raises `A2C_BFM_CONTRACT`. The unit tests cover the queue and the generated testbench module, and the loopback covers `a2c_expected_error`; the end-to-end run is a project bench's.
- No base block bench draws a random ready level. The output agents of uvmMem and uvmRegs keep the default `ready_pct` of 100, and uvmReuse's stall test holds ready low.
- No base simulation has exercised the generated register model's multi-word path. Unit tests generate it.
- No base example has real RTL behind a `req_ack` or `pop_ack` port, or behind an AXI port. mixed declares req_ack ports only, pySocket's `dut.sv` drives nothing, and axiDemo's producer and consumer RTL are stubs. Only the loopback and scratch model-DUT benches have exercised these agents.
- The `notify_ack` `A2C_DST` driver has not run against RTL. The one base block with a notify_ack `src` port, mixed's blockA, cannot build a UVM bench (section 10.4).
- No base example runs a reset against RTL with request-response or AXI ports. The loopback resets `rdy_vld`, `push_ack` and an AXI read master with traffic in flight, and memory, AXI and apb masters each holding one item, and `examples/uvmReuse` resets its leaf's RTL in a single-mode run with a beat in flight (`uvmReuseLeaf_reset_test`).

### 10.4 Build, tool and example items

- Under Xcelium every uninstantiated HDL wrapper top is elaborated as an idle top-level. That is harmless at the tested size, but its memory cost on a large SoC is unmeasured.
- SystemC 3.0.1 is untested in both flows (VCS `-sysc=301` with a GCC 13 build, Xcelium `-sc_301`). The default `VCS_ELAB_OPTS` selects 2.3.4.
- The comment and `$(error)` text at `a2c-xrun.mk:8-13` say `XRUN_GCC_VERS` must match the compiler's libstdc++. For 26.03 that is inaccurate (section 2.2).
- Whether a later Xcelium bundling GCC 13 should be linked with it is untested.
- The Xcelium documentation reviewed during testing states that a snapshot records `LD_LIBRARY_PATH` and rejects a different value at simulation time. The builder does not record it. Keep `LD_LIBRARY_PATH` the same for the build and every run.
- An exported `XRUN_OPTS` or `VCS_LIB_SV_FILES`, or under `VCS_DEBUG` an exported `VLOGAN_OPTS` or `VCS_ELAB_OPTS`, is appended to again in each sub-make, so the builder's additions appear twice (section 3).
- A VCS or Xcelium snapshot's HDL prerequisites do not follow a nested `-f` or `-F` list, expand a `$VAR` in a list, or read an include directory whose name holds a `+`. An edit to a file reached only that way rebuilds nothing until `make clean`. Verilator's own dependency record covers it.
- The builder default `DUT_TOPOLOGIES` includes `verif:tandem`, which needs a builder layer that registers tandem blocks (section 1.3).
- Tandem: Pro's 1-in-2-out external_reg tee (`builder/pro/common/systemc/external_reg_port_tee.h`, `port_tee`) forwards a CPU write with `write()`, not `reg_write_cmd()`. A tandem dst model that waits in `read()` for CPU writes never sees one.
- A second `make USE_UVM=1 USE_VCS=1 uvm_snapshots` is not a no-op. The model, rtl and both snapshots share one `AN.DB` and one analysis-options stamp, and the rtl build adds `+define+A2C_UVM_RTL_DUT` and the both build `+define+A2C_UVM_BOTH_DUT`, so each build re-analyses after the one before. A no-op needs a per-DUT analysis library or a DUT selection without a define. Xcelium is not affected.
- The JUnit report of `regrLauncher.py` records only the first failure (`regrLauncher/report.py`), so the order of the rule files decides which failure it shows.
- An rtl-only (`hasMdl: false`) `hasVl` block's `<block>_hdl_sc_wrapper.h` imports `<ctx>_<block>.base`, which such a block never gets, so its C++ fails to compile in a `VL_DUT`, VCS or Xcelium build. The unit tests generate the files but never compile them.
- Example builds: Pro's lmmiDemo RTL does not elaborate on Xcelium, which rejects `$bits` of a hierarchical name in a typedef. The mixed example does not build on Xcelium (`URRNG` in blockB's `memory_dp.sv`), and its blockA RTL fails VCS elaboration (`ICPD`).
