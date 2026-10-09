# VCS and Xcelium integration specification

This document specifies how Arch2Code builds and runs a project under Synopsys VCS and Cadence Xcelium, and what a site must install and set to bring both flows up. It covers the make interface, the generated files, the environment, and the known failure modes. The make targets and hooks are summarised here. The full hook table and the general build workflow are in the `manage-build` skill (`rules/skills/manage-build.md`), and the regression file format is in `run-regression-tests` (`rules/skills/run-regression-tests.md`).

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
| `VERILATOR` | `VL_DUT` with neither switch | the Verilator flow, including `--vlTrace` VCD tracing |
| `VCS_DEBUG` (SystemVerilog) | `VCS_DEBUG=1` | the HDL wrapper calls `$fsdbDumpvars` when the run passes `+fsdbTrace` |

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

A missing snapshot exits with `dutRun: no snapshot <binary> for arguments ...`. A regression file keeps one run command, for example `../builder/dutRun.py build/run <testbench>` for VCS and `../builder/dutRun.py build_xrun/run <testbench>` for Xcelium.

### 1.5 Generated boundary files

The RTL top of each DUT is the generated HDL verification wrapper (`<block>[_<variant>]_hdl_sv_wrapper`). Owner-qualified foreign tops (`<stub>_<label>_hdl_sv_wrapper`) and pair tops (`p<n>_<parentSv>_c<m>_<childSv>_<label>_hdl_sv_wrapper`) are tops too (`specs/spec-verilated-wrappers.md` §2). A top's pins are flat `bit` and `bit [N-1:0]` ports. Each top binds literal parameter values, so its widths are fixed, but they are written as parameter expressions (`specs/spec-verilated-wrappers.md` §5), which neither `vlogan -sc_model` nor a hand-written foreign module can size. So the generator evaluates them.

- `make db` evaluates the width of every parameterizable structure and type at each top's parameter values and stores them in the database.
- `make gen` runs `arch2code.py --vlBoundary` only when `USE_VCS` or `USE_XCELIUM` is set and the manifest lists HDL tops (`A2C_VL_TOPS`). It writes two whole files per top under `.gen/vl/`, with no user region:

| File | Consumer | Content |
| :--- | :--- | :--- |
| `.gen/vl/<top>.portmap` | `vlogan -sc_model <top> -sc_portmap` | one line per pin: `<pin> <width> bit bool` or `<pin> <width> bitvector sc_bv` |
| `.gen/vl/<top>_xcelium.h` | the registrar under `XCELIUM_DUT` | `class <top> : public xmsc_foreign_module` with one `sc_in<...>` or `sc_out<...>` per pin, typed `bool` or `sc_bv<W>`, and `hdl_name()` returning `<top>` |

- The VCS SystemC shells themselves (`<top>.h`) are written by `vlogan` into `$(VCS_RUNDIR)/csrc/sysc/include`.

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
| `VCS_ELAB_OPTS` | optional | `-sysc=234 -ignore initial_driver_checks` | `vcs` elaboration options | |
| `VCS_DEBUG` | optional | unset | `1` adds `-kdb -debug_access` to the link and `+define+VCS_DEBUG` to `vlogan`, for FSDB dumps with `+fsdbTrace` at run time | `1` |
| `VCS_LIB_SV_FILES` | optional | every `interfaces/*/*_if.sv` and `common/systemVerilog/*.sv` except `flops.sv` | units `vlogan` analyses explicitly because it does not search `-y` directories | |
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
| `XRUN_OPTS` | optional | `-64bit -sv -sysc -sc_main -timescale 1ns/1ps -warn_multiple_driver` | snapshot build options. `-gcc_vers $(XRUN_GCC_VERS)` is appended | |
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

1. `vlogan $(VLOGAN_OPTS) $(EXTRA_VLOGAN_OPTS) -F a2c.f <HDL hooks> -F rtl.f <RTL modules> $(VCS_LIB_SV_FILES) +incdir+<wrapper dirs>`, in `VCS_RUNDIR`, log `vlogan_rtl.log`.
2. Per HDL top: `vlogan ... -sc_model <top> -sc_portmap .gen/vl/<top>.portmap <wrapper.sv>`, log `vlogan_<top>.log`. The shells land in `csrc/sysc/include/<top>.h`, which the registrar objects include. `-sc_model` takes one source file per call and the calls share `AN.DB`, so they run in sequence.
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

A builder layer adds its own arguments through `A2C_LAYER_CXX_FLAGS`, `A2C_LAYER_CPP_INCLUDES`, `A2C_LAYER_LD_FLAGS` (which also reach the `xrun` link as `-Wld,`), `A2C_LAYER_HDL_F_FILES` and `A2C_LAYER_VCS_LIB_SV_FILES`. Their position relative to the builder and project arguments is in `manage-build`.

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
| Xcelium `*E,MULAXX` from `flops.sv` | `A2C_RESET_NONE` or `FPGA_INIT_FLOPS` pairs `initial` with `always_ff` | keep `-warn_multiple_driver`, which the default `XRUN_OPTS` carries, in any `XRUN_OPTS` override |
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

Harmless warnings: Xcelium `*W,SCK910` on `sc_start(0)`, `SPDUSD` and `LIBNOU` for unused include and library directories from `a2c.f`, and the `MULAXXW` cap message.

### 7.3 Behaviour to know

- Under Xcelium, `sc_main` runs twice: once under xmelab during the snapshot build, up to the first `sc_start`, and again under xmsim for each run. Code before `sc_start` runs in both, so side effects such as file writes happen at build time too.
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

## 9. Open items

- Under Xcelium every uninstantiated HDL wrapper top is elaborated as an idle top-level. That is harmless at the tested size, but its memory cost on a large SoC is unmeasured.
- SystemC 3.0.1 is untested in both flows (VCS `-sysc=301` with a GCC 13 build, Xcelium `-sc_301`). The default `VCS_ELAB_OPTS` selects 2.3.4.
- The comment and `$(error)` text at `a2c-xrun.mk:8-13` say `XRUN_GCC_VERS` must match the compiler's libstdc++. For 26.03 that is inaccurate (section 2.2).
- Whether a later Xcelium bundling GCC 13 should be linked with it is untested.
- The Xcelium documentation reviewed during testing states that a snapshot records `LD_LIBRARY_PATH` and rejects a different value at simulation time. The builder does not record it. Keep `LD_LIBRARY_PATH` the same for the build and every run.
- An exported `XRUN_OPTS` or `VCS_LIB_SV_FILES`, or under `VCS_DEBUG` an exported `VLOGAN_OPTS` or `VCS_ELAB_OPTS`, is appended to again in each sub-make, so the builder's additions appear twice (section 3).
- The builder default `DUT_TOPOLOGIES` includes `verif:tandem`, which needs a builder layer that registers tandem blocks (section 1.3).
