# Container verification report: farm simulator change set

Written 2026-09-16 in the `a2c-dev` container against the tree mounted at `/work/ws/debayer`, following
`handoff-container-verify-farm-simulator-changes.md`. All eight checks were executed. Nothing was edited, committed or
deleted beyond what `make clean` removes. `USE_VCS`/`USE_XCELIUM` appeared only in the `make -n` dry runs of check 2.

## Environment

- Container image: `a2c-dev:2.0`, hostname `debayer-dev`, Ubuntu 22.04.5 LTS, 96 CPUs.
- `clang++ --version`: `Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)`.
- `dot -V`: `graphviz version 2.43.0 (0)`. Python 3.10.12.
- `LDC_RHEL_ENV`, `USE_VCS`, `USE_XCELIUM`, `A2C_CLANG`, `VCS_HOME`, `XCELIUM_TOOLS` all unset.
- Before starting, the farm probe job (`rundir/rh8probe`, host ldc-farm06, last write 19:06 PDT) had reached `DONE`; no farm
  regression was active on the shared mount. Checks 1 to 5 and 8 (rundir) ran concurrently with checks 6 to 7 (builder/base);
  checks 6 and 7 ran sequentially.

## Results

| Check | Command | rc | Wall | Result |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `make clean && make db && make gen` (rundir) | 0 | 37 s | PASS. `git status --short` matches section 2 exactly; no other tracked file changed. |
| 2a | `ls /work/ws/debayer/.gen/vl` | 2 | <1 s | PASS. Directory absent, still absent at the end of the session. |
| 2b | `make -n gen \| grep -c vlBoundary` | 0 matches | 1 s | PASS. Prints 0. |
| 2c | `make -n USE_VCS=1 gen \| grep -c vlBoundary` | 2 | 2 s | DEVIATION. Prints 0. See below. |
| 2d | `make -n USE_VCS=1 USE_XCELIUM=1 all` | 2 | <1 s | PASS. `a2c-systemc.mk:48: *** USE_VCS and USE_XCELIUM are exclusive.  Stop.` |
| 3 | `make -j8 all`; `./build/run debayer --verbosity=low` | 0 / 0 | 40 s / 8 s | PASS. Ends `No error`. Compile lines carry `-MP`; 0 occurrences of `-DVCS`, `-DXCELIUM`, `-DVCS_DUT`, `-DXCELIUM_DUT` (checked in the captured build log, since `make -n all` is empty after a build). |
| 4 | `make -j8 VL_DUT=1 all`; three `--vlInst` runs | 0 / 0,0,0 | 67 s / 28 s, 37 s, 53 s | PASS. All three end `No error`. `-DVERILATOR` on the compile line. `static_assert` count 2 per registrar file with widths debayer 35/99, preprocess 35/323, interpolate 323/99. |
| 5 | `make regr` (regr_debayer.json) | 0 | 276 s (41 s build + 3 min 53 s launcher) | PASS. Launcher: `Run session completed succesfully (runs: 44, passed: 44, failed: 0, skipped: 0) [0:03:53]`. JUnit: `tests="44" failures="0" errors="0" skipped="0"`. No E549 in this run. Session: `rundir/regr/regr_debayer.atomlin.2026-16-09-192753.3272729`. |
| 6 | `unittest/run_all_tests_parallel.sh` | 0 | 166 s | PASS. 130 suites, 130 passed, no retry, no 10 s subprocess timeout. |
| 7 | `make clean && make -j4 -k pipeline-test` (builder/base) | 0 | 514 s | PASS, 26 of 26 targets (make -k rc 0). `diagram-and-doc` and `pySocket` both passed; see below. |
| 8a | `git diff -- examples/simple/verif/vl_wrap/simple_hdl_sc_wrapper.h` | 0 | - | PASS. Three-way `#if defined(VCS_DUT)` / `#elif defined(XCELIUM_DUT)` / `#else` include selection, the matching two-way `VCS_DUT || XCELIUM_DUT` guards on the `dut_hdl` member and constructor, and the reworded comment above the include. Byte-identical before and after check 7. |
| 8b | `head -60 registrar/debayerVlRegistrar.cpp` | 0 | - | PASS. Line 5 guard `#if defined(VERILATOR) \|\| defined(VCS_DUT) \|\| defined(XCELIUM_DUT)`; lines 19 to 24 three-way `using debayer_default_hdl_sv_wrapper_dut_t`; lines 26 to 27 `static_assert` on `video_bayer_t<...>::_bitWidth == 35` and `video_rgb_t<...>::_bitWidth == 99`. |

Farm references for comparison: regression 44 of 44 in 5 min 19 s at six jobs; unit tests 130 of 130; pipeline-test 24 of 26.

## Deviations from the expected results

### Check 2c: the VCS dry run stops at a parse-time guard

`make -n USE_VCS=1 gen` does not reach any recipe in an environment without VCS. First error line:

```
/work/ws/debayer/builder/include/make/a2c-vcs.mk:10: *** VCS_HOME is not set - load the VCS environment before building with USE_VCS.  Stop.
```

Cause: `a2c-vcs.mk` lines 9 to 11 contain `ifndef VCS_HOME` / `$(error ...)`, which fires while make parses the makefiles,
before `-n` has any effect. The handoff's expectation ("dry run only; VCS is not present") cannot hold as written.

Probe: with a dummy value the dry run behaves as the handoff expects, and nothing executes.

```
make -n USE_VCS=1 VCS_HOME=/nonexistent gen | grep -c vlBoundary   -> 1
(the line is: .../builder/arch2code.py --db /work/ws/debayer/debayer.db -r --vlBoundary)
ls .gen/vl                                                          -> still absent
```

The Xcelium switch has an equivalent parse-time guard: `make -n USE_XCELIUM=1 gen` stops with
`a2c-systemc.mk:60: *** XCELIUM_TOOLS is not set - point it at the Xcelium install's tools directory to build with USE_XCELIUM.  Stop.`
(and `a2c-xrun.mk:12` guards `XRUN_GCC_VERS`). The boundary gating itself is correct; only the handoff's check 2c wording needs
`VCS_HOME=<any>` added to the dry run, or the guard moved so that it fires from a recipe.

### Check 7: the two expected failures passed

- `diagram-and-doc`: the container's graphviz is 2.43.0, the version the golden SVG was drawn with. All `git diff --no-index`
  comparisons in the recipe (mixedDoc*.txt, mixedDiagram*.gv, nestedSt.svg, nestedDiagramDepth7.gv) produced no output; an
  independent diff of `examples/tests/out/nestedSt.svg` against the golden is byte-identical.
- `pySocket`: built, ran to `pySocket.py: done` and `No error`, then the RTL lint completed. No hang.
- The six `Error Number` blocks and six `make[1]: *** Deleting file` lines in the pipeline log all belong to asserted negative
  fixtures (`mtxBare`, `cpLayoutBad`, `inhLayoutBad`, `infPortBad`, `varUniqBad` twice), each followed by its expected `OK:` or
  rejection handling; none is a failure.

## Observations (not failures)

- `builder/base` shows ` D unittest/tmpy7kz9g0x.db-journal`, a tracked file not in the section 2 inventory. It was already
  deleted when this session started and was not touched here.
- `builder/base` has 85 modified files under `examples/` (bridge 7, ip 4, leaf 1, registrar 17, rtInh 12, rtl 2, src 2, top 9,
  verif 31); section 2 says 83. Not reconciled here (no pre-change baseline in the container).
- The three `plans/*.md` files, `dutRun.py`, `include/make/a2c-vcs.mk`, `include/make/a2c-xrun.mk` and `pysrc/vlBoundaryGen.py`
  are untracked in `builder/base`, as section 2 describes.

## Repository status at the end

`git -C /work/ws/debayer status --short` (unchanged from the start of the session):

```
 M .gitignore
 M builder
 M isp_shared
 M registrar/debayerVlRegistrar.cpp
 M registrar/interpolateVlRegistrar.cpp
 M registrar/preprocessVlRegistrar.cpp
 M rundir/Makefile
 M verif/debayer_hdl_sv_wrapper.svh
 M verif/interpolate_hdl_sv_wrapper.svh
 M verif/preprocess_hdl_sv_wrapper.svh
?? agent-prompt-report-since-2026-05-01.md
?? apb_register_decode_lessons.md
?? branch-116-review-report.md
?? claude_session_summary_may.md
?? docs/windows-environment-assessment.md
?? opencode-agent-report-since-2026-05-01.md
?? output_rgb_image.png
?? presentations/
?? regression-e549-investigation.md
?? rundir/build_vl/
?? rundir/regr_debayer_vcs.json
?? rundir/regr_debayer_vlbase.json
?? rundir/regr_debayer_xcelium.json
?? rundir/rh8probe/
?? rundir/vcs.json
?? rundir/xcelium.json
?? skills-assessment-report.md
?? usage-reports/
```

`git -C /work/ws/debayer/builder status --short`:

```
 m base
 M pro/include/make/a2cPro.mk
 M pro/include/make/a2cProEnv.mk
?? dutRun.py
```

`git -C /work/ws/debayer/builder/base status --short`, entries outside `examples/` (plus 85 ` M examples/...` entries):

```
 M arch2code.py
 M common/scmain/main.cpp
 M common/systemc/hwMemory.h
 M common/systemc/simController.cpp
 M config/createBuildManifest.py
 M include/make/a2c-common.mk
 M include/make/a2c-systemc.mk
 M pysrc/intf_gen_utils.py
 M pysrc/processYaml.py
 M pysrc/valueResolver.py
 M templates/systemVerilog/module_hdl_wrapper.py
 M templates/systemc/module_hdl_wrapper.py
 M templates/systemc/vlRegistrar.py
 M unittest/test_inherit_vl_child.py
 M unittest/test_transit_surface_classification.py
 D unittest/tmpy7kz9g0x.db-journal
?? dutRun.py
?? include/make/a2c-vcs.mk
?? include/make/a2c-xrun.mk
?? plans/farm-simulators-recipe-and-results.md
?? plans/handoff-container-verify-farm-simulator-changes.md
?? plans/handoff-container-verify-report.md
?? plans/plan-farm-simulators-vcs-xcelium.md
?? pysrc/vlBoundaryGen.py
```

`git -C /work/ws/debayer/builder/pro status --short`:

```
 m ../base
 M include/make/a2cPro.mk
 M include/make/a2cProEnv.mk
?? ../dutRun.py
```

## Files created by this session

- In the tree: this report; the regression session directory `rundir/regr/regr_debayer.atomlin.2026-16-09-192753.3272729`;
  ordinary build outputs under `rundir/build`, `.gen`, the databases, and the example rundirs (all `make clean` products, and
  `.gen/build.mk` now records `/work/ws/debayer` paths instead of the farm paths).
- Outside the tree, session scratchpad `/tmp/claude-19778/-work-ws-debayer/3c76ad51-8ef6-4b0f-8439-aa0a681c46ce/scratchpad/`:
  step logs `step1_gen.log`, `step1_gitstatus.log`, `step2_boundary.log`, `step3_make_all.log`, `step3_run.log`, `step3_flags.log`,
  `step4_make_vl.log`, `step4_run1_verif.log`, `step4_run2_tandem.log`, `step4_run3_preprocess.log`, `step4_asserts.log`,
  `step5_regr.log`, `step8_registrar_head.log`, `step_final_gitstatus.log`, `step6_unittests.log`, `step7_pipeline.log`,
  `step8a_before.diff`, `step8a_after.diff`, `agentA_results.md`, `agentB_results.md`.
- Also in `/tmp` directly: `mkn_gen.log`, `mkn_gen_vcs.log`, `mkn_both.log`, `mkn_all_post.log`, `dverilator_line.txt`, `step3_start`.
