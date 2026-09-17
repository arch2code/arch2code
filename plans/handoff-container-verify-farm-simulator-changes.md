# Handoff: verify the farm simulator change set in the container environment

Written 2026-09-16 on the Lattice farm (RHEL 9.6 node) for an agent running in the `a2c-dev` container with the same working tree
mounted at `/work/ws/debayer`. Read this whole file first; then execute the checks in section 4 and report as in section 6.

## 1. What this change set is

The debayer/arch2code tree (repositories `debayer`, `builder`, `builder/base`, `builder/pro`, all with uncommitted changes) gained two
simulator flows next to the existing Verilator flow:

- `make USE_VCS=1 ...` builds one Synopsys VCS snapshot per DUT topology with the RTL elaborated natively by VCS.
- `make USE_XCELIUM=1 ...` does the same with Cadence Xcelium (`xrun`).
- The generator persists the HDL boundary pin widths per top at `make db` and, only under those two switches, `make gen` writes
  `.gen/vl/<top>.portmap` (VCS port map) and `.gen/vl/<top>_xcelium.h` (Xcelium foreign-module shell).
- Both flows share a topology list (`DUT_TOPOLOGIES` in `rundir/Makefile`), a dispatcher (`builder/dutRun.py`), regression session files
  (`rundir/regr_debayer_vcs.json`, `rundir/regr_debayer_xcelium.json`) and make targets (`regr_vcs`, `regr_xcelium`).

Full history and decisions: `builder/base/plans/plan-farm-simulators-vcs-xcelium.md` (sections 3.16, 3.18 to 3.29 and 3.33 are the
implementation record). Recipes and measurements: `builder/base/plans/farm-simulators-recipe-and-results.md`.

The container cannot run VCS or Xcelium. Its job is to prove that the Verilator flow, the generator, the unit tests and the examples are
unchanged or still correct in the container, with the container's Clang 20.1.8, and that nothing in the new flows leaks into a build that
does not ask for them.

## 2. Files changed (uncommitted; do not commit, do not revert)

builder/base:
- `include/make/a2c-common.mk`: `DEFAULT_BIN_DIR`/`XRUN_BIN_DIR`, `BIN_DIR` selection, boundary stamp (`VL_BOUNDARY_STAMP`) added to
  `GEN_DEPS` only when `USE_VCS` or `USE_XCELIUM` is set, `clean::` also removes `build_xrun` and simulator artefacts, `VCS_RUNDIR`/`XRUN_RUNDIR`.
- `include/make/a2c-systemc.mk`: `USE_VCS`/`USE_XCELIUM` blocks, `VL_DUT ?= 1` under either switch, `$(error)` when both are set,
  `DUT_TOPOLOGY`/`DUT_TOPOLOGIES`/`DUT_ELAB_ARGS`, `BIN = run_<topology>` under the switches (plain and Verilator keep `BIN = run`),
  `-MP` added to the four `-MMD` compile rules, `BUILD_FLAVOR` prefix, includes of the two new make files.
- `include/make/a2c-vcs.mk` (new), `include/make/a2c-xrun.mk` (new): the simulator flows; inert unless their switch is set.
- `templates/systemc/vlRegistrar.py`: guard `#if defined(VERILATOR) || defined(VCS_DUT) || defined(XCELIUM_DUT)`, per-top
  `using <top>_dut_t = ...` alias with a three-way `#if/#elif/#else`, `static_assert(<struct><Config>::_bitWidth == <persisted width>)`
  per payload pin of templated wrappers.
- `templates/systemc/module_hdl_wrapper.py`, `templates/systemVerilog/module_hdl_wrapper.py`: three-way DUT header/class selection;
  `$fsdbDumpvars` under `` `ifdef VCS_DEBUG``.
- `pysrc/processYaml.py`: `calcVlTops` persists `VLTOPS`; `projectOpen.hdlParamWidths`, `getVlTopBoundaryPins`; registrar pair fields
  `vcsDutClass/vcsDutHeader/xceliumDutClass/xceliumDutHeader`; svWrapper view fields.
- `pysrc/vlBoundaryGen.py` (new), `arch2code.py` (`--vlBoundary`), `config/createBuildManifest.py` (`A2C_VL_PORTMAP_<top>` under `.gen/vl`,
  `A2C_VL_GEN_INC`), `pysrc/intf_gen_utils.py` (`sc_concrete_dut` carries the Xcelium header; inline width lookups replaced),
  `pysrc/valueResolver.py` (public `structureWidth()`).
- `common/scmain/main.cpp` (`#ifdef VCS`/`#ifdef XCELIUM` blocks only), `common/systemc/simController.cpp` (`#ifndef VCS` removed around
  the `--vl*` options), `common/systemc/hwMemory.h` (lambda instead of `sc_core::sc_bind`; same behaviour).
- `dutRun.py` (new dispatcher), `unittest/test_inherit_vl_child.py`, `unittest/test_transit_surface_classification.py` (expectations
  follow the `<top>_dut_t` alias and the new view keys), regenerated `examples/*/{registrar,verif}` outputs (83 files).

builder (superproject): `dutRun.py -> base/dutRun.py` symlink (untracked).
builder/pro: `include/make/a2cProEnv.mk`, `include/make/a2cPro.mk` (farm-only paths, all inside `ifdef LDC_RHEL_ENV`; the container does
not set `LDC_RHEL_ENV`, so this whole file body is skipped there).
debayer: `rundir/Makefile` (`DUT_TOPOLOGIES` before the include, `regr_vcs`, `regr_xcelium`, old VCS block removed), `.gitignore`
(rundir simulator artefacts), regenerated `registrar/*VlRegistrar.cpp` and `verif/*_hdl_sv_wrapper.svh`, untracked
`rundir/regr_debayer_vcs.json`, `rundir/regr_debayer_xcelium.json`, `rundir/regr_debayer_vlbase.json`, `rundir/vcs.json`,
`rundir/xcelium.json`.

## 3. Before you start (container specifics)

- The tree was last built on the farm host, whose absolute paths (`/home/atomlin/ws/debayer/...`) are recorded in `.gen/build.mk`,
  the databases and the object dependency files. In the container the tree is at `/work/ws/debayer`. Run `make clean` in
  `rundir` first, and in every example rundir you touch (the base `make clean` at `builder/base` cleans all examples), otherwise
  `make db` fails with `No rule to make target '/home/atomlin/ws/...'`.
- Expect `rundir/` to contain farm leftovers you should ignore: `build_vl/`, `build_xrun/`, `xcelium_*.d/`, `xrun*.history`, `regr/`
  session directories, `rh8probe/`, `vc_hdrs.h`. `make clean` removes the build trees and simulator artefacts; leave the rest.
- Compiler in the container: Clang 20.1.8 (the default `clang++`). Do not set `USE_VCS`, `USE_XCELIUM`, `A2C_CLANG` or `LDC_RHEL_ENV`.
- Never run `python arch2code.py` directly; use make targets. Do not edit generated regions. Do not commit.

## 4. Checks

Run from `/work/ws/debayer/rundir` unless stated. Record rc, wall time and the result tail of each.

1. Clean regeneration: `make clean && make db && make gen`. Then `git -C /work/ws/debayer status --short` must show only the files in
   section 2 (no new modifications from regeneration; if `make gen` changes any tracked file beyond the listed ones, report the diff).
2. Boundary artefacts are switch-gated: after step 1, `ls /work/ws/debayer/.gen/vl` must fail (directory absent), and
   `make -n gen | grep -c vlBoundary` must print 0. `make -n USE_VCS=1 VCS_HOME=/nonexistent gen | grep -c vlBoundary` must print 1
   (dry run only, nothing is executed; the dummy `VCS_HOME` satisfies the parse-time guard in `a2c-vcs.mk` that otherwise stops make
   before `-n` applies; `USE_XCELIUM` has the same kind of guard on `XCELIUM_TOOLS` and `XRUN_GCC_VERS`). `make -n USE_VCS=1 USE_XCELIUM=1 all` must fail with `USE_VCS and USE_XCELIUM are exclusive`.
3. Plain model: `make -j8 all && ./build/run debayer --verbosity=low` ends with `No error`. Confirm a compile line carries `-MP` and
   no `-DVCS`, `-DXCELIUM`, `-DVCS_DUT`, `-DXCELIUM_DUT` (`make -n all | grep -c -- -DVCS` prints 0).
4. Verilator RTL: `make -j8 VL_DUT=1 all`, then
   `./build/run debayer --verbosity=low --vlInst debayer --vlType verif` (about 30 s CPU, `No error`),
   `./build/run debayer --verbosity=low --vlInst debayer --vlType verif --vlTandem`,
   `./build/run debayer --verbosity=low --vlInst debayer.u_preprocess --vlType verif`. Confirm the registrar objects compiled with the
   `static_assert` lines present (`grep -c static_assert /work/ws/debayer/registrar/*VlRegistrar.cpp` prints 2 for each of the three files:
   35- and 99-bit payloads for debayer, 35 and 323 for preprocess, 323 and 99 for interpolate) and
   that `-DVERILATOR` is on the compile line.
5. Full Verilator regression: `make regr` (session file `regr_debayer.json`, 44 tests, `-j8`). Expect 44 pass. Report the launcher
   summary line and the JUnit totals from `regr/<session>/test-reports/junit.xml`. Farm reference: 44 of 44, 5 min 19 s wall at six jobs.
6. Unit tests: `cd /work/ws/debayer/builder/base/unittest && ./run_all_tests_parallel.sh`. Expect 130 suites, 130 pass (farm: 130 of 130,
   two suites occasionally hit a fixed 10 s subprocess timeout under heavy load and pass on the runner's retry; report if that happens).
7. Examples: `cd /work/ws/debayer/builder/base && make clean && make -j4 -k pipeline-test`. Farm result: 24 of 26 targets pass; the two
   expected failures are `diagram-and-doc` (golden SVG drawn with graphviz 2.43; report the container's `dot -V` and whether the golden
   matches there) and `pySocket` (on the farm the site Python lacked `libffi.so.6`; in the container it may pass; if it hangs, kill it
   after two minutes and report). Any other failure is a finding.
8. Generated-text spot check: `git -C /work/ws/debayer/builder/base diff -- examples/simple/verif/vl_wrap/simple_hdl_sc_wrapper.h` should show
   the three-way `#if defined(VCS_DUT)` / `#elif defined(XCELIUM_DUT)` / `#else` selection and nothing else; `head -60
   /work/ws/debayer/registrar/debayerVlRegistrar.cpp` should show the guard, the `using debayer_default_hdl_sv_wrapper_dut_t` alias and a
   `static_assert` for the 35- and 99-bit payloads.

## 5. What not to do

- Do not try to install or emulate VCS or Xcelium; `USE_VCS`/`USE_XCELIUM` appear here only in dry runs.
- Do not change generator, template or make files. If a check fails, capture the first error, the command and the relevant diff, and
  report; the farm side owns the fix.
- Do not delete the untracked rundir JSON files or `builder/dutRun.py`; they are part of the change set awaiting `git add`.
- Do not run `make clean` on the farm side of a shared mount while a farm regression is running (ask if unsure; the farm session can be
  mid-regression).

## 6. Report format

Write the report to `builder/base/plans/handoff-container-verify-report.md` (new file; the farm side integrates it into the plan) with:
container image/tag and `clang++ --version`; a table of checks 1 to 8 with rc, wall time and result; every deviation from the expected
result with the first error line; the `git status --short` of each repository at the end; the leftover files you created. Keep it factual.
