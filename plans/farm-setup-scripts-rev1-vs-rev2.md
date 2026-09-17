# Farm setup scripts: revision 1 (installed) versus revision 2 (proposed)

Date: 2026-09-17. Scripts live in `/ldc/projects/qistor/setup` (owned by the tools owner account, read-only for users). Revision 1 was
installed on 2026-09-17 08:13 from the first proposal. Revision 2 is staged, complete and ready to copy, in
`/ldc/projects/qistor/users/atomlin/setup-proposed/` (eight scripts plus `README.txt`).

## 1. Why a second revision

Revision 1 added what the new VCS and Xcelium flows needed (`A2C_CLANG`, the Xcelium variables, licence servers) while the pro
makefile `builder/pro/include/make/a2cProEnv.mk` still carried the same values as `?=` defaults, plus older farm paths (Verilator root,
site tools prefix, patched SystemC headers, the per-OS Boost library).

Owner decision (2026-09-17): checked-in makefiles must not default to farm paths, licence servers or tool versions; defaults that
describe the standard development container stay in `builder/base`. The pro makefile now requires each farm value from the environment
and stops with an error naming the setup script when one is missing. Revision 2 of the scripts exports the values the makefile stopped
defaulting. **Until revision 2 is installed, a farm build of the current tree that sources only revision 1 stops at**
`a2cProEnv: A2C_TOOLS_LOCAL is not set - source /ldc/projects/qistor/setup/setup.bash`.

## 2. Variables by revision

| Variable | Rev 1 | Rev 2 | Consumer |
|---|---|---|---|
| `LDC_RHEL_ENV=1`, site `PATH`, `LD_LIBRARY_PATH`, `GIT_SSL_NO_VERIFY` | yes | yes | pro gate, OpenCV runtime |
| `A2C_CLANG` | yes | yes | pro: compiler for `USE_VCS`/`USE_XCELIUM` |
| `A2C_TOOLS_LOCAL` | no | **new** | pro: OpenCV include and library flags (`-I $A2C_TOOLS_LOCAL/include`, `-L $A2C_TOOLS_LOCAL/lib64`), VCS patched-header include |
| `VERILATOR_ROOT` | no (makefile default) | **new** | base Verilator flow |
| `VCS_HOME`, `SNPSLMD_LICENSE_FILE`, `SYSTEMC_LIBDIR`, `BOOST_INCLUDE`, `LD_BOOST`, `VG_GNU_PACKAGE`, gcc 13.2 on `PATH`, Verdi | yes | yes | base/pro VCS and plain flows |
| `SYSTEMC_INCLUDE` | stock VCS SystemC headers (pro overrode to the patched set) | **patched headers** `$A2C_TOOLS_LOCAL/include/vcs/systemc234` (pro no longer overrides) | base compile |
| `XCELIUM_ROOT`, `XCELIUM_TOOLS`, `XRUN_GCC_VERS=12.4`, `LM_LICENSE_FILE` | yes | yes | base/pro Xcelium flow |
| `XRUN_BOOST_LIBS` | no (makefile chose by OS) | **new**, chosen from `/etc/os-release`: RHEL 8 `libboost_program_options.so.1.66.0`, otherwise `.so.1.75.0` | pro/base Xcelium link |

Other differences: `xcelium.*` rev 2 drops two commented-out lines (`PATH`/`LD_LIBRARY_PATH` to the Xcelium tools) that rev 1 carried;
the flow calls `$XCELIUM_TOOLS/bin/xrun` directly and never needs them on `PATH`. The bash OS test runs in a subshell so sourcing leaves
no `/etc/os-release` variables (`NAME`, `VERSION_ID`, ...) in the user's shell. `setup.bash`/`setup.csh` are unchanged between revisions.

## 3. Verification of revision 2

Sourced directly from the staging directory in a clean shell (`env -i`, then `a2c_rhel_setup`, `vcs_systemc_gcc13`, `xcelium`):

| Check | RHEL 9.6 (`lrd-farm-rh9-66`) | RHEL 8.10 (`ldc-farm06`, LSF job 4933225) |
|---|---|---|
| `make clean && make db && make gen` | clean | clean |
| `make -j8 USE_VCS=1 all` + debayer verif run | `No error`, 91.4 s CPU | `No error` |
| `make -j8 USE_XCELIUM=1 all` + debayer verif run | `No error`, 70.9 s; Boost `.so.1.75.0` | `No error`; Boost `.so.1.66.0` chosen by the script |
| plain Verilator flow (`VL_DUT=1`, Clang wrapper) | `No error`, 32 s | not repeated |
| each required variable unset in turn | the pro error names the script | |

`grep -nE "/ldc|/tools/dist|virtlic|1725@|5280@|12\.4|1\.66|1\.75" builder/pro/include/make/*.mk` matches only `$(error ...)` text.

## 4. Install

Copy the eight files from `/ldc/projects/qistor/users/atomlin/setup-proposed/` over `/ldc/projects/qistor/setup/` (owner account), then
from a fresh shell: `source /ldc/projects/qistor/setup/setup.bash` and, in `debayer/rundir`, `make -j8 USE_VCS=1 all` and
`make -j8 USE_XCELIUM=1 all`. The pro makefile reports any missing variable by name.

## 5. Per-file differences, revision 1 to revision 2

#### a2c_rhel_setup.bash
```diff
@@ -5,3 +5,8 @@
 
 # Compiler for the arch2code C++20 module units on the farm (RHEL 8.10 and 9.6): the pro makefiles read A2C_CLANG.
 export A2C_CLANG=/ldc/projects/qistor/tools/share/llvm-18.1.8/bin/clang++
+
+# Site tools prefix and Verilator install the pro makefiles read (A2C_TOOLS_LOCAL, VERILATOR_ROOT); the makefiles
+# carry no farm defaults for either.
+export A2C_TOOLS_LOCAL=/ldc/projects/qistor/tools/local
+export VERILATOR_ROOT=/ldc/projects/qistor/tools/share/verilator
```

#### vcs_systemc_gcc13.bash
```diff
@@ -3,7 +3,9 @@
 
 PATH=${VCS_HOME}/bin:${PATH}
 
-export SYSTEMC_INCLUDE=${VCS_HOME}/etc/systemc/accellera_install/systemc234-gcc13/include
+# OpenCV and the stock VCS SystemC collide on int64/uint64 types; use the site's patched SystemC
+# headers instead (the pro makefiles no longer override SYSTEMC_INCLUDE themselves).
+export SYSTEMC_INCLUDE=/ldc/projects/qistor/tools/local/include/vcs/systemc234
 export SYSTEMC_LIBDIR=${VCS_HOME}/etc/systemc/accellera_install/systemc234-gcc13/lib-linux64
 
 LD_LIBRARY_PATH=${SYSTEMC_LIBDIR}:${LD_LIBRARY_PATH}
```

#### xcelium.bash
```diff
@@ -5,5 +5,9 @@
 export XRUN_GCC_VERS=12.4
 export LM_LICENSE_FILE=1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b:29000@ldc-hw-eda:1725@ldc-virtlic01:5280@lrd-virtlic-rh8-01:5280@lrd-virtlic-ha-01a:5280@lrd-virtlic-ha-01b:5056@lrd-virtlic-rh8-01
 
-#export PATH=${XCELIUM_ROOT}/tools/bin:${PATH}
-#export LD_LIBRARY_PATH=${XCELIUM_ROOT}/tools/lib:${XCELIUM_ROOT}/tools/lib64:${LD_LIBRARY_PATH}
+# The site Boost is static and not PIC, so xrun's shared-library link takes the OS-provided shared
+# library instead (RHEL8 ships 1.66, RHEL9 ships 1.75; the site headers used to compile are 1.74).
+case $(. /etc/os-release && echo "${VERSION_ID%%.*}") in
+  8) export XRUN_BOOST_LIBS=/usr/lib64/libboost_program_options.so.1.66.0 ;;
+  *) export XRUN_BOOST_LIBS=/usr/lib64/libboost_program_options.so.1.75.0 ;;
+esac
```

#### a2c_rhel_setup.csh
```diff
@@ -5,3 +5,8 @@
 
 # Compiler for the arch2code C++20 module units on the farm (RHEL 8.10 and 9.6): the pro makefiles read A2C_CLANG.
 setenv A2C_CLANG /ldc/projects/qistor/tools/share/llvm-18.1.8/bin/clang++
+
+# Site tools prefix and Verilator install the pro makefiles read (A2C_TOOLS_LOCAL, VERILATOR_ROOT); the makefiles
+# carry no farm defaults for either.
+setenv A2C_TOOLS_LOCAL /ldc/projects/qistor/tools/local
+setenv VERILATOR_ROOT /ldc/projects/qistor/tools/share/verilator
```

#### vcs_systemc_gcc13.csh
```diff
@@ -3,7 +3,9 @@
 
 setenv PATH ${VCS_HOME}/bin:${PATH}
 
-setenv SYSTEMC_INCLUDE ${VCS_HOME}/etc/systemc/accellera_install/systemc234-gcc13/include
+# OpenCV and the stock VCS SystemC collide on int64/uint64 types; use the site's patched SystemC
+# headers instead (the pro makefiles no longer override SYSTEMC_INCLUDE themselves).
+setenv SYSTEMC_INCLUDE /ldc/projects/qistor/tools/local/include/vcs/systemc234
 setenv SYSTEMC_LIBDIR ${VCS_HOME}/etc/systemc/accellera_install/systemc234-gcc13/lib-linux64
 
 setenv LD_LIBRARY_PATH ${SYSTEMC_LIBDIR}:${LD_LIBRARY_PATH}
```

#### xcelium.csh
```diff
@@ -5,5 +5,11 @@
 setenv XRUN_GCC_VERS 12.4
 setenv LM_LICENSE_FILE 1717@lrd-virtlic-rh8-01:1717@lrd-virtlic-ha-01a:1717@lrd-virtlic-ha-01b:29000@ldc-hw-eda:1725@ldc-virtlic01:5280@lrd-virtlic-rh8-01:5280@lrd-virtlic-ha-01a:5280@lrd-virtlic-ha-01b:5056@lrd-virtlic-rh8-01
 
-#setenv PATH ${XCELIUM_ROOT}/tools/bin:${PATH}
-#setenv LD_LIBRARY_PATH ${XCELIUM_ROOT}/tools/lib:${XCELIUM_ROOT}/tools/lib64:${LD_LIBRARY_PATH}
+# The site Boost is static and not PIC, so xrun's shared-library link takes the OS-provided shared
+# library instead (RHEL8 ships 1.66, RHEL9 ships 1.75; the site headers used to compile are 1.74).
+set osmajor = `sed -n 's/^VERSION_ID="\([0-9]*\).*/\1/p' /etc/os-release`
+if ( "$osmajor" == "8" ) then
+  setenv XRUN_BOOST_LIBS /usr/lib64/libboost_program_options.so.1.66.0
+else
+  setenv XRUN_BOOST_LIBS /usr/lib64/libboost_program_options.so.1.75.0
+endif
```


