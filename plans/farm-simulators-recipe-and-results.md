# Recipe and results: the debayer SystemC/RTL regression under Verilator, VCS and Xcelium on the farm host

Standalone extract of `plan-farm-simulators-vcs-xcelium.md` (state of 2026-09-16: both simulator regressions pass 44 of 44; compile-switch review fixes applied, plan 3.27 and 3.28). It holds only what is needed to
reproduce the flows and the measurements taken; the experiment history and open design discussion stay in the plan.

## 1. Environment

- Hosts: RHEL 9.6 (glibc 2.34) and RHEL 8.10 (glibc 2.28) farm nodes, both verified for all three flows; NFS home. `source /ldc/projects/qistor/setup/setup.bash` sets `LDC_RHEL_ENV=1`,
  `VCS_HOME=/tools/dist/synopsys/VCS/W-2024.09-SP2` and puts the VCS_GNU GCC 13.2.0 on `PATH`.
- Python 3.10.13, PyYAML 6.0.3, Jinja2 3.1.6, GNU Make 4.3, Verilator 5.038 (`/ldc/projects/qistor/tools/bin/verilator`).
- Compiler for the C++20 module units: Clang 18.1.8, prebuilt, installed at `/ldc/projects/qistor/tools/share/llvm-18.1.8` (shared, read-only; owner decision 2026-09-16: Clang 18 stays because Clang 20.1.8 cannot run on the RHEL 8.10 farm nodes)
  (258 MB trimmed). GCC 13.2, GCC 14.2 and the site Clang 16 all fail on the module units.

  Install recipe (2026-09-15, run from a scratch directory; the full extraction is 7.1 GB, the trimmed install 258 MB):

```
curl -sSL -o llvm18.tar.xz https://github.com/llvm/llvm-project/releases/download/llvmorg-18.1.8/clang+llvm-18.1.8-x86_64-linux-gnu-ubuntu-18.04.tar.xz
tar -xJf llvm18.tar.xz
SRC=$PWD/clang+llvm-18.1.8-x86_64-linux-gnu-ubuntu-18.04
DST=/ldc/projects/qistor/tools/share/llvm-18.1.8   # final location (tools owner account); staged first under /ldc/projects/qistor/users/atomlin/tools
mkdir -p $DST/bin $DST/lib
cp -a $SRC/bin/clang-18 $SRC/bin/clang $SRC/bin/clang++ $DST/bin/
cp -a $SRC/lib/clang $DST/lib/                     # resource headers and runtimes (lib/clang/18)
$DST/bin/clang++ --version                          # clang version 18.1.8
$DST/bin/clang++ --gcc-install-dir=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0 \
    -std=c++23 -c probe.cpp -o /dev/null            # probe.cpp: #include <format> / <version>; must compile
```

Only the driver and its resource directory are needed: Clang is used with the GCC 13.2 headers and libraries (`--gcc-install-dir`), so
`lib/libclang*`, `lib/libLLVM*`, the other tools and the bundled libc++ were left out. The prebuilt binary needs glibc >= 2.27 (RHEL 9 has
2.34) and prints a harmless `libtinfo.so.5: no version information available` warning.
- Standard library: GCC 13.2's libstdc++ from `/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared`. Mandatory:
  VCS's `libsystemc.so` (`systemc234-gcc13`) needs its `GLIBCXX_3.4.30/3.4.32` symbols; Xcelium's runtime accepts them.
- SystemC for VCS: patched headers `/ldc/projects/qistor/tools/local/include/vcs/systemc234`, library `systemc234-gcc13/lib-linux64`
  (set by `builder/pro/include/make/a2cProEnv.mk`). SystemC 3.0.1 is available from VCS X-2025.06 onward and via Xcelium `-sc_301`;
  not yet adopted.
- Xcelium: `/tools/dist/cadence/XCELIUM/XCELIUMMAIN26.03.002` (bundled cdsgcc 9.3 and 12.4). The `xrun` on `PATH` is an LSF-submitting
  wrapper; the flow calls `tools/bin/xrun` directly and exports the site `LM_LICENSE_FILE`.
- Boost: the site static Boost in `/ldc/projects/qistor/tools/local/lib` is non-PIC. The plain and VCS flows link it with `-no-pie`;
  the Xcelium flow uses the OS's shared Boost (`a2cProEnv.mk` picks 1.75 on RHEL 9, 1.66 on RHEL 8 from `/etc/os-release`) and header-only stacktrace.
- Farm setup scripts: `source /ldc/projects/qistor/setup/setup.bash` (installed 2026-09-17: exports `A2C_CLANG`, the Xcelium variables and licence servers as well as the VCS/SystemC/GCC 13 environment; verified in a clean shell with both simulator flows).
- LSF: this Claude session is an interactive LSF job on an RHEL 9 node; simulators run as direct processes on that node. To reach RHEL 8.10 nodes use `lshosts -o "hname ostype"` and `bsub -m <host>` (resource selects do not filter here).
- Licences (`/lsc/ldp/bin/lmstat`, 2026-09-15): `VCSRuntime_Net` 3 issued at `1725@ldc-virtlic01`; `Xcelium_Single_Core` 651 issued,
  617 in use at query time, at `5280@lrd-virtlic-ha-01b`. Every VCS binary, including the model-only one, is a `simv` and takes a seat.

## 2. Recipes

All commands run from `debayer/rundir` after the one-time setup. `make clean && make db && make gen` is required after switching
between the container and the host, and after generator changes. `USE_VCS=1` and `USE_XCELIUM=1` imply `VL_DUT=1` (pass an empty
`VL_DUT=` for a model-only simulator binary) and are the only modes in which `make gen` writes the per-top boundary files under
`.gen/vl` (`<top>.portmap` for VCS, `<top>_xcelium.h` for Xcelium); a plain or Verilator build never creates them.

```
source /ldc/projects/qistor/setup/setup.bash
CLANG18=/ldc/projects/qistor/tools/share/llvm-18.1.8/bin/clang++
GCC13=/tools/dist/synopsys/VCS_GNU/X-2025.06/linux64/gcc-13.2.0_64-shared/lib/gcc/x86_64-centos-linux/13.2.0
cd debayer/rundir
make clean && make db && make gen
```

### 2.1 Plain SystemC model, no simulator

```
make -j8 USE_GCC= CXX="$CLANG18 --gcc-install-dir=$GCC13 -fno-pie -no-pie"
./build/run debayer --verbosity=medium
```

### 2.2 Verilator on the host (reference flow)

```
CL="$CLANG18 --gcc-install-dir=$GCC13 -fno-pie -no-pie"
make -j8 VL_DUT=1 USE_GCC= CXX="$CL" BIN_DIR=$PWD/build_vl all      # 52 s wall, 3 min 21 s CPU
./build_vl/run debayer --verbosity=low --vlInst debayer --vlType verif
```

The verilated library is compiled by the GCC 13.2 on `PATH`, the same libstdc++ as the Clang objects.

### 2.3 VCS, model-only DUT

```
make USE_VCS=1 VL_DUT= -j8 all                  # pro sets Clang 18 (A2C_CLANG) and the GCC 13 headers
./build/run debayer --verbosity=medium
```

### 2.4 VCS, RTL in the loop: one snapshot per DUT topology

VCS discovers the SystemC/HDL topology once per output binary (`-syscelab` arguments) and reuses it on relink, so every
`(vlInst, vlType, vlTandem)` combination is its own snapshot `build/run_<inst>_<type>[_tandem]` (instance path kept verbatim, dots included). One compile
serves every snapshot; only the 15 to 20 s link is per topology. The run command line is the same as under Verilator.

```
# one topology
make USE_VCS=1 -j8 all                                                 # build/run_debayer_verif
make USE_VCS=1 VL_TANDEM=1 -j8 all                                     # build/run_debayer_verif_tandem
make USE_VCS=1 VL_INST=debayer.u_preprocess -j8 all                    # build/run_debayer.u_preprocess_verif
./build/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif

# every regression topology at once (VCS_TOPOLOGIES in rundir/Makefile, <inst>:verif[:tandem] entries)
make -j8 USE_VCS=1 vcs_snapshots               # build/run_model plus six verif snapshots, links sequential (shared AN.DB/csrc)

# dispatcher: picks the snapshot from the test's own arguments, exec, no simulation overhead
../builder/dutRun.py build/run debayer --verbosity=low --vlInst debayer.u_interpolate --vlType verif --vlTandem
```

- `build/run_model` (linked with the testbench name only) serves every test that instantiates no RTL: plain model, model/model tandem,
  delay, with or without `--vlInst`. Verified with no topology warning and `No error`.
- `VCS_DEBUG=1` adds `-kdb -debug_access` and enables `$fsdbDumpvars`; default links carry no `-race -kdb -debug_access`.
- Each VCS log carries eight harmless `Warning-[RT_UO] Unsupported option` lines, one per a2c option. `-suppress=RT_UO` cannot be used:
  first on the command line it suppresses nothing, last it is rejected by the a2c option parser.
- One VCS build or regression at a time per rundir: two concurrent builds share `csrc` and `AN.DB` and a failed link removes both.
- A failed link removes `csrc`, `AN.DB` and the analysis stamps so the next build redoes the analysis.

### 2.5 VCS regression

`rundir/regr_debayer_vcs.json` holds the same 44 tests and labels as `regr_debayer.json` with `jobs: 3`, build command
`make -j8 USE_VCS=1 vcs_snapshots` (timeout 900 s), run command `../builder/dutRun.py build/run debayer --verbosity=low`
(timeout 900 s) and rules `default.json` plus `vcs.json` (`Error-[code]` and `Fatal-[code]` lines).

```
make regr_vcs                                  # regrLauncher.py --build regr_debayer_vcs.json
make regr_vcs REGR_USER_OPTS="--labels hdl,tandem"
# results: regr/<session>/test-reports/junit.xml, per-test logs under regr/<session>/runs/
```

The job count must not exceed the three runtime licences: a `simv` beyond that queues for a licence and times out.

### 2.6 Xcelium, RTL in the loop

```
make USE_XCELIUM=1 [VL_TANDEM=1] [VL_INST=<inst>] -j8 all   # snapshot xcelium_<topology>.d, run script build_xrun/run_<topology>
./build_xrun/run_debayer_verif debayer --verbosity=low --vlInst debayer --vlType verif

# every regression topology at once (DUT_TOPOLOGIES in rundir/Makefile, <inst>:<type>[:tandem]); elaborations run in parallel
make -j8 USE_XCELIUM=1 xrun_snapshots          # build_xrun/run_model plus one script per entry
../builder/dutRun.py build_xrun/run debayer --verbosity=low --vlInst debayer.u_interpolate --vlType verif --vlTandem
```

The Xcelium flow's default output directory is `build_xrun` (`XRUN_BIN_DIR` in `a2c-common.mk`, `clean` covers it), so its snapshots
coexist with the VCS ones in `build/`. Objects are compiled once; each topology is an elaboration of 1 to 3.5 minutes.

- The run script turns every argument into `+systemc_args+<arg>` and executes `xrun -R -xmlibdirname <snapshot> -64bit -nolog`; it
  exports the `LM_LICENSE_FILE` captured at build time.
- Xcelium fixes the whole SystemC object set in the snapshot, not only the HDL binding: a model/model tandem test constructs a second
  model instance, so it needs its own `run_<inst>_model_tandem` snapshot (VCS serves those tests from `run_model`). The dispatcher maps
  `--vlType model --vlTandem --vlInst X` to `<base>_X_model_tandem` for both flows and `DUT_TOPOLOGIES` lists `<inst>:model:tandem`; the
  VCS build gains three short links. Any option that changes the constructed SystemC hierarchy needs a snapshot under Xcelium. `-top` must
  not be given.
- Uninstantiated HDL wrappers are elaborated as idle top-levels (harmless for debayer, a memory concern at SoC scale).

### 2.7 Xcelium regression

`rundir/regr_debayer_xcelium.json`: the same 44 tests, `jobs: 6`, build `make -j8 USE_XCELIUM=1 xrun_snapshots` (1200 s), run
`/usr/bin/time -f CPU_TIME_USER=%U ../builder/dutRun.py build_xrun/run debayer --verbosity=low` (900 s, so each log carries the user CPU
time), rules `default.json` plus `xcelium.json` (`*E,CODE` and `*F,CODE` lines from xrun, xmelab and xmsim).

```
make regr_xcelium                              # regrLauncher.py --build regr_debayer_xcelium.json
```

The `Xcelium_Single_Core` pool is large and shared; six jobs saw no licence error with 17 free seats.

## 3. Data

All measurements on the same farm host, 2026-09-15, `--verbosity=low`, user CPU seconds unless stated. The host was shared between the
VCS regression, the Verilator baseline and other builds during the measurements.

### 3.1 Single tests, three simulators

| Test (synthetic data) | Verilator | VCS | Xcelium |
|---|---|---|---|
| model only, no RTL | 8.7 | 12.2 | 10.6 |
| debayer verif | 30.8 | 91.0 | 69.7 |
| debayer verif tandem | 40.7 | 108.2 | 84.1 |
| debayer.u_preprocess verif | 56.3 | 87.4 | 114.2 |

- Combined-tree check after all generator and make changes landed (19:00): VCS debayer verif 93.9 s, Xcelium 70.1 s, both `No error`,
  both from the generated `.gen/vl` boundary files.
- Pure SystemC: the VCS kernel costs about 1.4x the plain SystemC 2.3.4 build.
- RTL in the loop, whole design: VCS about 3x and Xcelium about 2.3x Verilator. Verilator compiles the RTL to C++; the a2c flow adds
  nothing per cycle beyond the simulator's own SystemC/HDL boundary.
- VCS link options matter: the prototype linked with `-race -kdb -debug_access` took 208 s on the debayer verif test; default options
  92.6 s; `-kdb -debug_access` alone 90.4 s. The 2.3x came from `-race`.

### 3.2 Whole regression, 44 tests

| Flow | Result | Jobs | Limit on jobs | Wall time | Total user CPU |
|---|---|---|---|---|---|
| Verilator | 44 / 44 pass | 6 | cores only | 5 min 19 s | 23 min 53 s |
| VCS | 44 / 44 pass | 3 | 3 `VCSRuntime_Net` licences | 19 min 20 s, plus 2 min 54 s snapshot build | 50 min 00 s |
| Xcelium | 44 / 44 pass | 6 | free seats of the 651-seat shared `Xcelium_Single_Core` pool | 9 min 40 s, plus 3 min 49 s snapshot build (parallel elaborations) | 43 min 21 s |

- VCS at eight jobs: 39 of 44, run 18 min 51 s. The five `model_tests/tandem` tests sat in `Queuing for License` for their full 900 s
  timeout; nothing functional failed.
- VCS JUnit of the passing run: `tests="44" failures="0" errors="0" time="3021.45"`.

### 3.3 VCS snapshot build times

| Step | Wall time |
|---|---|
| `make USE_VCS=1 VL_DUT=1 -j8 all`, cold compile plus one link | 48.6 to 49 s |
| Incremental rebuild, one link | 16 s |
| Relink after a topology change | 15 to 20 s |
| `vcs_snapshots`, seven links on current objects | 2 min 07 s to 2 min 17 s |
| `vcs_snapshots` after `make db gen` regenerated sources | 2 min 33 s to 2 min 54 s |

### 3.4 Xcelium snapshot build times (prototype flow, `BIN_DIR=$PWD/build_xrun`)

| Topology | Snapshot | Run CPU |
|---|---|---|
| debayer verif | 1 min 16 s, plus 36 s compile | 69.7 s |
| debayer verif tandem | 1 min 28 s | 84.1 s |
| debayer.u_preprocess verif | 3 min 32 s (host busy) | 114.9 s |

### 3.5 Per-test user CPU, Verilator versus VCS

Each cell: synthetic data; 1920x1080 data. Format `Verilator / VCS (ratio)`. Model tandem tests without a VCS figure were the ones lost to
licence queuing in the eight-job pass.

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 31.5 / 91.0 (2.9x); 8.1 / 17.4 (2.1x) | 102.7 / 165.2 (1.6x); 25.8 / 35.5 (1.4x) | 56.5 / 87.4 (1.5x); 14.3 / 20.4 (1.4x) |
| hdl delay | 72.2 / 227.8 (3.2x); 18.5 / 56.5 (3.1x) | 130.5 / 292.0 (2.2x); 33.3 / 72.6 (2.2x) | 80.3 / 179.4 (2.2x); 20.3 / 43.8 (2.2x) |
| hdl tandem | 41.1 / 108.2 (2.6x); 10.5 / 21.8 (2.1x) | 119.7 / 223.0 (1.9x); 30.0 / 51.9 (1.7x) | 61.5 / 97.5 (1.6x); 15.7 / 22.7 (1.4x) |
| hdl tandem_delay | 83.5 / 240.0 (2.9x); 21.6 / 61.2 (2.8x) | 137.8 / 303.0 (2.2x); 35.0 / 75.4 (2.2x) | 86.2 / 189.7 (2.2x); 22.0 / 46.0 (2.1x) |
| model delay | 10.0 / 16.0 (1.6x); 2.8 / 4.3 (1.6x) | 10.5 / 16.2 (1.5x); 2.9 / 4.5 (1.6x) | 10.1 / 15.4 (1.5x); 2.8 / 4.2 (1.5x) |
| model tandem | 17.1 / -; 4.5 / 6.4 (1.4x) | 15.8 / -; 4.1 / - | 14.1 / -; 3.8 / - |
| model tandem_delay | 18.4 / 28.1 (1.5x); 4.8 / 7.4 (1.5x) | 17.1 / 23.7 (1.4x); 4.5 / 6.3 (1.4x) | 15.4 / 24.6 (1.6x); 4.0 / 6.6 (1.6x) |
| model basic (debayer) | 8.9 / 12.2 (1.4x); 2.5 / 3.4 (1.4x) | | |

Reading: VCS costs 1.6x (interpolate, model-side work dominates) to 3.2x (whole design with delay, RTL dominates) Verilator with RTL in
the loop, and a steady 1.4x to 1.6x on pure SystemC.

### 3.6 Per-test user CPU, Xcelium regression (44 of 44 pass, six jobs)

Each cell: synthetic data; 1920x1080 data. Model tandem tests run on their own `run_<inst>_model_tandem` snapshots.

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 70.7; 15.7 | 159.4; 38.6 | 114.2; 28.1 |
| hdl delay | 142.6; 36.1 | 235.4; 59.0 | 179.2; 45.0 |
| hdl tandem | 85.4; 19.7 | 199.4; 49.7 | 126.7; 30.8 |
| hdl tandem_delay | 162.2; 40.5 | 248.7; 62.5 | 193.1; 48.0 |
| model delay | 11.5; 3.3 | 11.9; 3.4 | 11.8; 3.4 |
| model tandem | 19.1; 5.1 | 17.7; 4.9 | 16.2; 4.5 |
| model tandem_delay | 20.2; 5.5 | 18.6; 5.1 | 17.5; 4.8 |
| model basic (debayer) | 10.6; 3.0 | | |

Reading: RTL tests cost 1.2x to 2.3x Verilator (interpolate 1.5x, whole design 2.3x) and about 0.8x VCS; model tests about 1.2x plain
SystemC. Totals: RTL tests 39 min 51 s, model tests 3 min 18 s.

### 3.7 Per-test wall time, VCS regression at three jobs (all PASS)

Each cell: synthetic data; 1920x1080 data, minutes:seconds as reported by the launcher.

| Group | debayer | interpolate | preprocess |
|---|---|---|---|
| hdl default | 1:32; 0:18 | 2:44; 0:35 | 1:27; 0:21 |
| hdl delay | 3:46; 0:57 | 4:58; 1:14 | 3:01; 0:44 |
| hdl tandem | 1:48; 0:21 | 3:41; 0:52 | 1:39; 0:23 |
| hdl tandem_delay | 4:08; 1:04 | 5:07; 1:16 | 3:16; 0:48 |
| model delay | 0:16; 0:04 | 0:16; 0:05 | 0:16; 0:04 |
| model tandem | 0:25; 0:07 | 0:21; 0:06 | 0:22; 0:06 |
| model tandem_delay | 0:29; 0:08 | 0:24; 0:07 | 0:25; 0:07 |
| model basic (debayer) | 0:12; 0:04 | | |

- Sum of the 24 RTL tests 47 min 05 s, of the 20 model tests 3 min 47 s. Longest test 5 min 07 s against the 900 s timeout.
- At three seats the RTL tests set the 19 min 20 s wall time.

## 4. Flow pieces (unstaged in the working trees)

- `builder/base/include/make/a2c-vcs.mk`: VCS analysis, per-top `-sc_model` shells, `-syscelab` topology stamp, per-topology link,
  `VCS_TOPOLOGIES` and `vcs_snapshots`, `VCS_DEBUG`, `clean::`.
- `builder/base/include/make/a2c-xrun.mk`: Xcelium equivalent with `xcelium_<topology>.d` snapshots and generated run scripts.
- `builder/base/include/make/a2c-systemc.mk`: `USE_VCS` and `USE_XCELIUM` blocks, `BIN = run_<topology>` under `VL_DUT`, build flavour stamp.
- `builder/base/dutRun.py` (plus `builder/dutRun.py` symlink): the snapshot dispatcher for both simulators (`<base>_<topology>` from the test's `--vlInst/--vlType/--vlTandem`; the instance path is kept verbatim so distinct paths never share a snapshot).
- Generator: boundary pin widths persisted at `make db`; `.gen/vl/<top>.portmap` (VCS) and `.gen/vl/<top>_xcelium.h` (Xcelium) written by
  `make gen` only under `USE_VCS=1` or `USE_XCELIUM=1`; registrars carry `static_assert`s on the persisted widths under every flow.
- `builder/pro/include/make/a2cProEnv.mk`: Clang 18 path, GCC 13 headers, `-gdwarf-4`, Xcelium install and licence variables.
- debayer: `rundir/Makefile` (`VCS_TOPOLOGIES`, `regr_vcs`), `rundir/regr_debayer_vcs.json`, `rundir/vcs.json`.

## 5. Known items

- Xcelium elaborates the HDL wrappers a topology does not use as idle top-levels: harmless for debayer, a memory question at SoC scale.
- `USE_VCS=1` with `USE_XCELIUM=1`, or `USE_GCC=1` with either, is rejected by make. `make clean` removes both `build` and `build_xrun` and every simulator artefact in the rundir whatever the switches.
- Examples: `simple` never reaches end of test in any DUT flow. (`hierVlDemo`/`axi4sDemo` had 2-state nets that Xcelium rejects; fixed, both now run under Xcelium.)
- Under Xcelium every command-line option that changes the constructed SystemC hierarchy needs its own snapshot (today: model/model tandem).
- Pro RTL library: `rdyVldBurstFifo.sv` parameter type syntax (vlogan `Error-[SE]`), `a2cPro.f` lacks `+libext+.sv`, `flops.sv` FPGA
  macros trip Xcelium `MULAXX` (demoted with `-warn_multiple_driver`).
- Leftovers in `rundir` from the measurements: `build_vl/`, `build_xrun/`, `xcelium_*.d`, `xrun_*.log`, `regr_debayer_vlbase.json`, the
  `regr/` session directories.
