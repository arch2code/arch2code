# Clock and reset branch PR review

## Full-branch review on 2026-09-26 at `1ce776d3`

**Request changes. The branch is not ready for a review-ready PR.** Nine functional defects and one test-coverage defect require changes. All 111 unit-suite scripts pass, but adversarial fixtures reproduce invalid generated code and incorrect simulation timing or reset selection.

- Branch: `feature/129-clock-followup`.
- Reviewed HEAD: `1ce776d3`.
- Comparison base: `origin/main` at `d7897c62d08c6d5846023bd13c8b96c204b6451a`.
- Scope: all 250 changed files, including Python derivation and views, schema, register routing, RTL, simulation wrappers, framework runtime, examples, tests, and documentation.
- Source paths are relative to `builder/base`; source line references refer to this HEAD.

This section supersedes the earlier verification limits and PR assessment below. Finding IDs remain stable. R1 through R4 remain open, R5 and R6 are confirmed inherited defects, and R7 through R12 record the additional findings from this pass.

### Current finding dispositions

| ID | Severity | Finding | Current result |
| --- | --- | --- | --- |
| R1 | P2 | Handler reset deferral misses name matching | Reproduced. A bus reset named `rst_n` rejects; the `rstB_n` control passes. |
| R2 | P2 | Port-domain agreement excludes connection maps | Reproduced. Leaf and containing wrapper select different clocks for the same interface. |
| R3 | P2 | Inferred bus name collides with register output | Reproduced. Database creation passes; generation crashes and merges APB/status identities. |
| R4 | P2 | Router BFMs ignore selected bus reset | Reproduced independently in views, generated bindings, and selected-reset RTL checks. |
| R5 | P2 | Dispatch loses qualified interface identity | Reproduced, but the offending dispatch and simple-name lookup also exist on the comparison base. Inherited defect. |
| R6 | P2 | Reused router-containing ancestor disconnects later occurrences | Reproduced, but declaration-only validation and first-match dispatch also exist on the comparison base. Inherited defect. |
| R7 | P2 | Renamed chained map loses the persisted port domain | New finding; generated middle wrapper uses the wrong clock. |
| R8 | P2 | Local selected reset is inaccessible to the BFM wrapper | New finding; generated SystemC references an undeclared signal. |
| R9 | P2 | Clock/reset namespace validation omits inferred interface ports | New finding; generated RTL has duplicate port identifiers. |
| R10 | P2 | Passthrough synthesis bypasses bus compatibility checks | New finding; accepted 32/64-bit mismatch produces truncating RTL. |
| R11 | P2 | Half-period rounding changes accepted clock frequencies | New finding; runtime probes confirm silent frequency changes, including a lockstep guard bypass. |
| R12 | P2 | `clkGen` passes with its divided clock stopped | Prior coverage warning promoted after a mutation test confirmed false success. |

R1 through R4 retain their detailed reproductions in the 2026-09-25 section. The ten change requests are R1 through R4 and R7 through R12. R5 and R6 should not be described as new branch regressions.

### Additional findings

#### R7. P2: Renamed chained connection maps discard the persisted domain

**Locations:** `pysrc/processYaml.py:3276-3279`, `3336-3340`.

For a `connectionMapPorts` row, the view passes the enclosing block's `portName` into a lookup scoped to the current block. The current block's persisted boundary domain is keyed by its own `instancePortName`. Different names cause the lookup to miss and silently return `defaultClock`.

Reproduction:

```text
outer.renamed -> mid.exposed -> leaf.data
                              declared clock: clkB
```

Database creation correctly persists `mid.exposed -> clkB`. Fresh generation nevertheless emits:

```cpp
exposed_bfm.clk(clkA);
exposed_bfm.rst_n(rstA_n);
```

The outer and leaf wrappers use `clkB/rstB_n`, and the RTL connects the interface directly through both levels. Changing only the outer boundary name to `exposed` makes the middle view select `clkB`.

**Impact:** Selecting the middle wrapper changes the interface's sampling and driving domain. Unlike R2, derivation is correct here; the read-only view loses the persisted result.

**Fix:** Look up the current block's own port identity. Do not substitute the default clock when a derived boundary requires a persisted domain row.

**Artifacts:** `/tmp/opencode/clock-review-extra/chain.yaml`, `extra.db`, `chain-control.db`, and `verif/vl_wrap/mid_hdl_sc_wrapper.h`.

#### R8. P2: BFM reset validation accepts an inaccessible local reset

**Locations:** `pysrc/clockTree.py:1215-1221`, `1707-1709`; `pysrc/processYaml.py:3293-3295`.

A container can select a child-driven local reset. BFM validation checks whether a reset is selected, but not whether the co-simulation wrapper can access it.

A fixture with `hasVl: true`, `resets: {}`, an internal reset producer, and a mapped data interface passes database creation and generation. Its reopened view reports no reset ports but assigns `localReset_n` to the interface. The generated header contains:

```cpp
data_bfm.rst_n(localReset_n);
```

That is the only occurrence of `localReset_n` in the header. The SV wrapper exposes only `clk`, so the internal reset does not reach SystemC. Exporting the reset as a block output supplies the missing port in the passing control.

**Impact:** Accepted input emits an undeclared identifier in the SystemC wrapper.

**Fix:** Require a wrapper-visible reset for each BFM during project creation, or implement an explicit observation mechanism. Selecting an internal RTL net is insufficient.

**Artifacts:** `/tmp/opencode/clock-review-extra/local.yaml`, `local/localreset.db`, `local/export-control.db`, and `local/verif/vl_wrap/wrap_hdl_sc_wrapper.h`.

#### R9. P2: Clock/reset name validation omits inferred interface ports

**Location:** `pysrc/clockTree.py:388-397`.

The namespace check includes declared `ports:`, `registerPorts:`, clocks, resets, and memories. It omits ports introduced by `connections` and `connectionMaps`.

A leaf declares clock `data`; a parent supplies `srcport: data` without a leaf `ports:` declaration. Database creation, scaffolding, and generation pass and emit:

```systemverilog
push_ack_if.src data,
input data, rst_n
```

Explicitly declaring the interface in `ports:` correctly rejects the same collision.

**Impact:** Accepted input generates duplicate module-port identifiers. The SystemC clock member also shadows the inherited interface port.

**Fix:** Include every inferred interface-port name in project-creation namespace validation.

**Artifacts:** `/tmp/opencode/clock-review-extra/collision.yaml` and `collision/rtl/leaf.sv`.

#### R10. P2: Passthrough synthesis bypasses register-interface compatibility checks

**Locations:** `config/postParseRegisterPorts.py:1162-1179`; downstream consumers at `pysrc/processYaml.py:2985-3001`, `3236-3239`.

The passthrough loop discards the resolved boundary interface and emits a map using the inner consumer's interface without checking compatibility. The view then treats the inner map as the wrapper's port declaration, overriding its authored boundary type.

Verified topology:

```text
router: apbReg, 32-bit data
  -> wrap.registerPorts.regs: apbReg, 32-bit data
      -> leaf.registerPorts.regs: wideReg, 64-bit data
```

Database creation and generation succeed. The wrapper view retains authored `apbReg/design.yaml` but emits `regs` as `wideReg/design.yaml`. Generated SystemC inserts a 32-to-64-bit thunker. Verilator reports `WIDTHTRUNC` when the handler assigns 64-bit `rd_data` to the actual 32-bit APB interface.

Moving the same leaf directly under the router correctly rejects the mismatch. A 32/32-bit passthrough control generates and lints cleanly.

**Impact:** Inserting a passthrough container bypasses required packed-width equivalence and permits truncating register-bus connectivity.

**Fix:** Validate both resolved interfaces at every synthesized passthrough hop and preserve the wrapper's authored interface in the view.

**Artifacts:** `/tmp/opencode/register-review-current/`, including generated `base/wrapBase.cppm`, `model/top.cppm`, and `rtl/leaf_regs.sv`.

#### R11. P2: Half-period rounding silently changes accepted clock frequencies

**Location:** `templates/systemc/module_hdl_wrapper.py:138-143`; downstream lockstep validation at `495-506`.

The wrapper computes `clk_half_(sc_time(period, unit) / 2)`. At the framework's default 1 ps SystemC resolution, odd-picosecond periods round their half-period upward, and the generator repeats that rounded interval indefinitely.

Fresh accepted/generated fixtures and a compiled probe using the current clock-generator body produced:

| Requested period | Observed half-period | Actual period |
| --- | --- | --- |
| 1 ps | 1 ps | 2 ps |
| 3 ps | 2 ps | 4 ps |
| 999 ps | 500 ps | 1000 ps |
| 1001 ps | 501 ps | 1002 ps |

Every free-running probe exited successfully. The 999 ps case also passed the lockstep guard, which sees the already-rounded 500 ps half-period. This is distinct from the original 500 ps/1.5 ns gated-clock finding, whose explicit rejection remains fixed.

**Impact:** Accepted timing silently changes frequencies and relative clock timing. Lockstep can accept a period it cannot represent exactly.

**Fix:** Check representability against the original requested period before rounding loses information. Support the required resolution or reject unrepresentable half-periods. Cover free-running and gated timing.

**Artifacts:** `/tmp/opencode/hardware-review-resolution.py`, `/tmp/opencode/hardware-review-head.mk`, and `/tmp/opencode/socket_clock_rereview`.

#### R12. P2: `clkGen` reports success when its generated clock is stopped

**Locations:** `examples/clkGen/tb/clkGen/clkGenExternal.cpp:35-44`; `examples/clkGen/tb/clkGen/clkGenConfig.cpp:40-47`, `56-61`.

The sole test completes after 500 ns without checking clock frequency, reset release, or consumer progress. Completion therefore measures the timer rather than DUT behavior.

After the unmodified example passed, the divider output in a private copy was replaced with `assign clkDiv = 1'b0`. Rebuilding and running the whole-DUT target still exited 0:

```text
Completing test clkGenRunWindow
warning: clock 'clkDiv' produced no edge by end of run
No error
```

**Impact:** The pipeline example stays green when its central functionality is broken.

**Fix:** Make success depend on observed divided-clock timing, reset assertion/release, and consumer activity. Retain the stopped-clock mutation as evidence that the checks detect failure.

**Artifacts:** `/tmp/opencode/hardware-review-example-clkGen/` and the `clkgen-mutation` target in `/tmp/opencode/hardware-review-head.mk`.

### Verification and remaining concerns

The full unit suite ran in private clones through a make-wrapped serial runner covering every suite in each revision's `unittest/run_all_tests.sh`. Generator subprocesses used make targets.

| Revision | Suite scripts completed | Passed | Failed |
| --- | --- | --- | --- |
| HEAD `1ce776d3` | 111 | 111 | 0 |
| Comparison base `d7897c62` | 95 | 95 | 0 |

These counts are suite scripts, not individual assertions. Logs and per-suite results are in `/tmp/opencode/unit-review-head-final-logs/` and `/tmp/opencode/unit-review-main-final-logs/`, each with `results.json`.

Additional completed checks:

- All 20 existing `memory_reg_bridge` simulation configurations passed.
- All 58 clock/reset emission checks, 21 local-net checks, 47 register-decode checks, and 26 routing checks across 13 suites passed. These overlap the full unit suite and are not additional suite counts.
- Fresh private-copy generation, build, and simulation passed 14 example configurations: `simple` model and two partial RTL selections; `twoClk` model and six RTL selections; `clkGen` model and three RTL selections before mutation.
- Fixed 96-bit and parameterized 40-bit/16-bit handlers passed staged writes, readback, exact write counts, and reset-error/recovery checks.
- Selected-reset router behavior, `twoClk` whole-RTL APB traffic/error recovery, `clkGen` divider/reset/consumer behavior, and both changed IP/register-handler pairs passed targeted checks.
- Assertion-exit, watchdog, and test-completion suites passed against current framework sources.
- Fresh databases, reopened views, generated artifacts, lint failures, passing controls, runtime clock probes, and the stopped-clock mutation substantiate the findings above.

Remaining concerns:

- The inherited padding-read hang remains at `templates/systemVerilog/moduleRegs.py:805-822`. Offset `0xC` of a 96-bit row stalled for 200 cycles with no bridge request under both APB ready modes and both reset styles. The new bridge path copies the existing same-clock defect.
- Free-running to gated transitions can shorten one interval or create two delta-separated edges at one timestamp. Tested traces match `b828652b`; the current guard did not introduce this behavior.
- Changed BFM reset checks cover initial release, not general mid-transaction reset recovery. Startup checks do not prove runtime-reset behavior for every protocol.
- Full-branch `git diff --check d7897c62..1ce776d3` fails on trailing whitespace and extra EOF blank lines, predominantly in generated examples. The earlier passing check covered only `b828652b..HEAD`.

Selected reproduction commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/opencode/clock-review-extra/verify.py
make -C /tmp/opencode/register-review-current -j4 lint
make -C /tmp/opencode -f hardware-review-head.mk -j4 resolution
make -C /tmp/opencode -f hardware-review-head.mk -j4 clkgen-mutation
```

The first command asserts the observed bad views/artifacts and their controls. The lint command intentionally exposes the width mismatch. The mutation target intentionally demonstrates a broken DUT passing. Temporary fixtures may disappear or change and are not committed regression coverage.

The full example pipeline and tandem matrix, synthesis/STA, physical CDC/RDC analysis, and four-state simulation were not run. R4 has generated-binding and selected-reset RTL evidence, but no full SystemC wrapper simulation of that mismatched-reset fixture. R7 through R9 have database and emitted-artifact evidence; no additional elaboration/runtime result is claimed for them.

**PR recommendation:** Fix R1 through R4 and R7 through R12, add the adversarial cases to regression coverage, and rerun the suite and affected example/tandem paths. Green happy-path tests do not establish identity and domain consistency across inference, persisted data, and wrapper generation.

The review and verification left repository files unchanged. This report update preserves the earlier review text below.

## Rereview on 2026-09-25 at `1ce776d3`

**Request changes. Seven original findings are fixed; two are partially fixed.** The new register-boundary inference also introduces a confirmed naming regression. Three additional defects were confirmed in surrounding paths; these were not introduced by the latest fix commit.

Reviewed on 2026-09-25 after fetching `origin`. The checkout matched the pushed `feature/129-clock-followup` at `1ce776d3`. This pass reviewed the 56-file change from `b828652b`, tested the original findings, and exercised additional hierarchy, naming, reset-selection, and interface-scope cases. Source locations in this rereview section refer to `1ce776d3`.

### Original finding dispositions

| Original finding | Status | Verification |
| --- | --- | --- |
| 1. Router wrapper pin renaming | Fixed | Fresh generation preserves the router's declared ports. Wrapper and containing hierarchy pass Verilator lint. |
| 2. Silent lockstep clock distortion | Fixed by explicit restriction | Compiled current template body with the real socket scheduler rejects 500 ps and 1.5 ns periods with exit 1 in gated mode. Periods of 1, 2, 3, and 10 ns have exact edge spacing. Fractional periods still run correctly outside lockstep. |
| 3. Descendant resolution overwritten | Fixed | Conflicting hierarchy occurrences reject in both declaration orders, including reset-attribute conflicts. An agreeing control retains a 7 ns period and 11 reset-release cycles. |
| 4. Conflicting inferred port clocks | Partially fixed | Ordinary connection conflicts reject, but mixed `connections` and `connectionMaps` still give one physical interface inconsistent domains. See R2. |
| 5. Duplicate reset pins | Fixed | Two router reset ports mapped to one parent net retain distinct child pin names. Generated wrapper and hierarchy elaborate. |
| 6. Temporary handler reset binding | Partially fixed | The original `rstB_n` case passes; a bus reset named `rst_n` still undergoes premature validation. See R1. |
| 7. Memory-derived BFM reset validation | Fixed for reported path | Resetless memory accessors reject during database creation. A reset-bearing control emits a valid BFM binding. A resetless register accessor also rejects. |
| 8. Inconsistent passthrough boundaries | Fixed | Different router downstream names now converge on one inferred block boundary under the revised rules. Fresh generation and whole-hierarchy lint pass. |
| 9. Authored child-local interface ignored | Fixed for original case | Inner maps retain the child-local `ipReg` interface and `regs` boundary. Generation and whole-hierarchy lint pass. |

### Open findings

#### R1. P2: Handler reset deferral misses the name-match path

**Locations:** `pysrc/clockTree.py:919–938`, `956–978`. Continuation of original finding 6.

The new synthesized-handler exception applies only to the reset fallback branch. A reset literally named `rst_n` takes the earlier name-match branch and gets validated against the handler's temporary default clock.

```yaml
clocks:
    clkA: {default: true}
    clkB: {}
resets:
    rst_n: {clock: clkB}
registerPorts:
    apbReg: {interface: apbReg, clock: clkB}
```

Fresh `make db` rejects the generated handler because its temporary `clk` binds to `clkA`, while `rst_n` belongs to `clkB`. Renaming the reset to `rstB_n`, with corresponding bindings, makes the valid design pass.

**Impact:** Valid register-domain selection depends on reset spelling. The diagnostic asks users to repair a generator-owned binding.

**Fix:** Defer synthesized handler reset binding before name matching as well as fallback. Validate the final bus clock/reset pair after `_resolveRegisterHandlerBinds()`.

**Artifacts:** `/tmp/opencode/clock-register/project-rst-name.yaml`, `/tmp/opencode/hw129-review/named-reset/`.

#### R2. P2: Port-domain agreement excludes connection-map occurrences

**Locations:** `pysrc/clockTree.py:1301–1305`, `1393–1422`. Continuation of original finding 4.

The agreement map records ordinary connection endpoints only. Inside-out boundary derivation independently assigns an undeclared inner port its block default clock.

A freshly generated fixture has one leaf occurrence whose `out` port is inferred on `clkB` through an ordinary connection, and another occurrence whose `out` is passed directly through `wrap` by `connectionMaps`. Both clocks bind through the wrapper by identity.

```cpp
// Generated leaf wrapper
out_bfm.clk(clkB);
out_bfm.rst_n(rstB_n);

// Generated containing wrapper
out_bfm.clk(clkA);
out_bfm.rst_n(rstA_n);
```

The RTL directly connects `.out(out)` with no domain conversion. Database creation and generation nevertheless succeed.

**Impact:** Verification samples the same interface on different clocks depending on whether the leaf or its containing wrapper is selected.

**Fix:** Establish one block-port domain across every port-producing relationship, then use it for boundary derivation and persisted views.

**Artifacts:** `/tmp/opencode/clock-ports/design.yaml`, generated wrappers under `/tmp/opencode/clock-ports/verif/vl_wrap/`.

#### R3. P2: Inherited bus names collide with register-output channels

**Locations:** `config/postParseRegisterPorts.py:863–865`, `914–915`. Confirmed regression in the latest fix.

A wrapper declares `registerPorts: {cfgA: {interface: apbReg}}`. Its plain inner leaf owns register `cfgA` and relies on inference. The new inference gives the leaf and handler a bus port named `cfgA`, colliding with the generated register-output port and internal status channel.

`make db` and `make newmodule` pass. `make gen` crashes in `processYaml.py:3192` with `KeyError: 'interfaceKey'`. The partially generated handler has already merged different protocols:

```systemverilog
apb_if.dst cfgA,
// Missing status_if.src cfgA
assign cfgA.data = cfgA_reg;
```

The identical fixture generates and lints when only the register-port pass is replaced by its `b828652b` version. A HEAD control with boundary name `regs` also passes. This isolation used the old pass, not a full old-commit build.

**Impact:** Previously working input now crashes generation and merges an APB port with a status port.

**Fix:** Resolve inferred bus names against leaf and handler generated namespaces. Keep bus and register-output identities distinct. At minimum, reject unavoidable collisions during project creation rather than merging protocols.

**Artifacts:** Failure `/tmp/opencode/regports-rereview-4oqk06ta`; old-pass control `/tmp/opencode/regports-rereview-bu16vugl`; renamed-boundary control `/tmp/opencode/regports-rereview-6e4ozw0m`.

#### R4. P2: Router BFMs ignore the explicitly selected bus reset

**Locations:** `pysrc/processYaml.py:3283–3295`, `templates/systemc/module_hdl_wrapper.py:255–256`. Predates the latest fix.

A router selects `addressBlock.reset: regBus_n`, while its clock's default reset is `regDefault_n`. Its generated RTL flops use `regBus_n`, but both upstream and downstream APB BFMs bind to `regDefault_n`. The router view has `registerBusPort: None`, so the special reset selection does not reach those BFMs.

**Impact:** With the default reset held asserted and the selected bus reset released, the router operates but its BFMs remain blocked on an unrelated reset.

**Proof:** Generated BFM bindings and reopened views show the mismatch. A targeted RTL test routes reads, propagates errors, and recovers using the selected bus reset while the default reset remains low, under both reset styles. A full SystemC wrapper simulation was not run for this case.

**Fix:** Stamp every router bus port with its own `busClockPort/busResetPort`. Cover both upstream and downstream ports without changing the clock's general default reset.

**Artifacts:** `/tmp/opencode/hw129-review/router_tb.sv`, `/tmp/opencode/hw129-review/probe_view.py`, generated `decode_hdl_sc_wrapper.h`.

#### R5. P2: Dispatch can substitute a shadowing interface

**Locations:** `config/postParseRegisterPorts.py:979–983`, `998–1002`; `pysrc/processYaml.py:3514–3521`. Predates the latest fix.

A router and leaf resolve `apbReg/shared.yaml` with 32-bit data. Their instances are declared in `top.yaml`, which defines another `apbReg` using a different 16-bit `badDataSt`. Dispatch discards the resolved interface context and emits the simple name into the instance context.

Fresh generation produces a router-to-leaf connection using `apbReg/top.yaml` and a leaf-to-handler map using `apbReg/shared.yaml`. The address-bus view also selects by simple name. The handler references `badDataSt` while importing only the shared package. Verilator fails with `Can't find typedef/interface: 'badDataSt'`.

**Fix:** Validate the resolved router interface in every dispatch emission context. Preserve qualified interface identity through register-bus views and derive structures from that exact row.

**Artifacts:** Failure `/tmp/opencode/regports-rereview-r3wc32y5`; old-pass comparison `/tmp/opencode/regports-rereview-mjib81xa`; control `/tmp/opencode/regports-rereview-cv3cfqct`.

#### R6. P2: Reusing a router-containing block leaves later occurrences disconnected

**Locations:** `config/postParseRegisterPorts.py:1071–1079`, with declaration-only router instance validation at `125–150`. Predates the latest fix.

Instantiate a container `mid` twice, with one declared nested router inside `mid`. The router restriction counts declarations rather than hierarchy occurrences. Dispatch synthesis then stops at the first matching container instance.

Database creation and generation succeed, but the second container instance omits its APB interface connection. Whole-hierarchy lint reports an unconnected `apbReg` interface. The single-container control passes.

**Fix:** Enforce the documented router multi-instance restriction across hierarchy occurrences, including reused ancestors, during database creation.

**Artifact:** `/tmp/opencode/hw129-review/reuse/`.

### Hardware warnings and verification

- The inherited fixed-width padding-read hang remains at `templates/systemVerilog/moduleRegs.py:805–822`. Fresh generated RTL stalls on offset `0xC` of a 96-bit row for 200 cycles with no bridge request. Reproduced for both APB ready modes and both synchronous and asynchronous reset builds.
- Free-run-to-gated transitions can produce a shortened half-cycle or two delta-separated edges at one timestamp. Traces matched `b828652b` for all 12 tested supported-period/transition combinations, so this is not a regression from the new guard.
- The previous `clkGen` scoreboard, socket reset responsibility, and watchdog-policy warnings remain. They were not promoted to new implementation findings.

Checks performed for this rereview:

- All checks in `test_clock_reset_emission.py`, `test_register_decode_clock.py`, and `test_clock_domains.py` passed with generator subprocesses routed through temporary make adapters.
- 26 existing routing checks across 13 suites passed. The separate 47 register-decode clock checks also passed and overlap the suite named above.
- Fresh generation, reopened database views, and Verilator elaboration covered the original router/passthrough failures and adversarial controls.
- Generated handlers passed staged writes, readback, exact memory-write counts, and memory-held-reset error tests.
- Both changed IP RTL pairs elaborated through their checked-in variant wrappers.
- Compiled socket probes checked unsupported-period rejection, valid gated timing, fractional free-running timing, ACK pauses, and transition traces against the old body. The probe bodies were checked against the templates byte-for-byte.
- `git diff --check b828652b..HEAD` passed.

Runtime timing checks can be repeated with:

```bash
make -C /tmp/opencode -f clock-review.mk -j4 socket_clock_rereview socket_clock_baseline
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/opencode/socket_clock_rereview_check.py
make -C /tmp/opencode/hw129-review -j2 lint-wrapper lint-router
```

Temporary fixtures may change during further investigation or disappear during cleanup. The original section's reproduction commands describe historical artifacts, not guaranteed current failing cases.

The full regression suite, full SystemC/tandem matrix, synthesis, physical CDC/RDC checks, and four-state simulation were not run. No implementation files were changed by the rereview; only this report was updated.

## Original review at `b828652b`

The following preserves the original findings and evidence. Their current dispositions are listed above.

### Original verdict and scope

**Request changes before opening the PR.** The review found nine actionable defects, including generated RTL that cannot elaborate and simulations that silently use incorrect clocks.

- Review date: 2026-09-25.
- Branch: `feature/129-clock-followup`.
- Reviewed HEAD: `b828652b15e415a17fccef428284f18848853b2e`.
- Comparison base: `origin/main` at `d7897c62d08c6d5846023bd13c8b96c204b6451a`.
- Scope: full branch diff, with independent Python, hardware, simulation-wrapper, and register-routing reviews.
- Review method: adversarial review against `builder-base-development`, Python review guidance, and the clock/reset design contracts.

All source paths and line numbers below refer to the original reviewed HEAD and are relative to `builder/base`. The original review did not modify implementation files. All nine findings were open at that review.

## Actionable findings

### 1. P1: Renaming a router's clock/reset breaks its Verilator wrapper

**Locations:** `templates/systemVerilog/module_hdl_wrapper.py:118`, `templates/systemVerilog/apbDecodeModule.py:42–48`.

A router with `hasVl: true` can map its implicit `clk/rst_n` onto container signals such as `busClk/busRst_n`. The router generator renames the actual module ports, but the wrapper still connects their original names:

```systemverilog
// Generated router declaration
input busClk, busRst_n

// Generated wrapper instantiation
.clk(clk),
.rst_n(rst_n)
```

Database creation and generation succeed. Verilator then reports `PINNOTFOUND` for both connections.

**Impact:** Supported domain renaming breaks standalone router co-simulation and tandem elaboration.

**Suggested fix:** Establish one DUT-port identity contract in the view. Emit wrapper bindings such as `.busClk(clk)` and `.busRst_n(rst_n)`, while preserving the wrapper's SystemC-facing boundary.

Both the Python and hardware reviews independently reproduced this.

### 2. P1: Socket lockstep silently changes sub-nanosecond clock frequencies

**Location:** `templates/systemc/module_hdl_wrapper.py:495–500`.

The clock generator receives notifications every 500 ps and toggles at most once per notification. A valid clock with a 500 ps period needs an edge every 250 ps, which this implementation cannot produce.

A compiled SystemC probe using the actual socket scheduling code produced:

```text
fast edge 0 s
fast edge 500 ps
fast edge 1 ns
fast edge 1500 ps
```

**Impact:** A declared 2 GHz clock runs at 1 GHz. Other half-periods that are not multiples of 500 ps suffer quantization, changing clock ratios and crossing behavior.

**Suggested fix:** Make gated time advancement account for actual clock-edge deadlines. Repeated `sig.write()` calls within one update phase will not solve this, because those writes collapse into one update.

### 3. P2: Reused containers overwrite descendant clock resolutions

**Location:** `pysrc/clockTree.py:2665–2690`.

`_resolveAllInstances()` walks hierarchy occurrences but stores results by declaration-level `instanceKey`. When a container block appears twice, its descendant instance keys repeat. The second traversal overwrites the first.

Reproduction:

```text
uWrapA -> 7 ns clock
  uLeaf
uWrapB -> 9 ns clock
  uLeaf
```

The `hasVl` leaf declares no explicit period. Database creation should reject the ambiguous standalone timing under V21. Instead, it succeeds and selects **9 ns**. Reversing the wrapper declarations selects **7 ns**.

**Impact:** Standalone timing depends on declaration order. Reset attribute resolution has the same information loss.

**Suggested fix:** Preserve all hierarchy-occurrence resolutions and validate agreement before selecting standalone attributes.

### 4. P2: The same inferred port can acquire conflicting clocks across instances

**Location:** `pysrc/processYaml.py:3253–3259`.

Two instances of one block can assign the same top-down port to different block-local clocks through their connections. Validation checks the endpoints individually but never establishes a single domain for the shared block port.

The view subsequently deduplicates the port and chooses one instance:

```python
instanceKey = next(iter(portRow['instance']))
```

A fixture assigning `out` to `clkA` on one instance and `clkB` on another generates successfully. Reversing connection order changes the generated BFM binding between `clkA/rstA_n` and `clkB/rstB_n`.

**Impact:** A single generated wrapper silently samples or drives an interface on the wrong domain for one instance.

**Suggested fix:** During `projectCreate`, validate agreement by block and port using resolved block-local clocks. Persist that domain instead of choosing an instance in the view.

### 5. P2: Reset fan-in creates duplicate named router pins

**Location:** `pysrc/clockTree.py:574–580`.

For router/handler instances, the emitted reset-pin rename is selected by equality of the parent net, rather than identity of the child reset port.

If a router has two resets and both bind to `busRst_n`, generation produces:

```systemverilog
.busRst_n(busRst_n),
.busRst_n(busRst_n)
```

The second declared reset port remains unconnected.

**Impact:** The containing RTL hierarchy fails elaboration, independently of the wrapper defect in finding 1.

**Proof:** Verilator reports a duplicate `busRst_n` connection and a missing `rstExtra_n` pin.

**Suggested fix:** Rename only the selected child bus-reset port, using `name == child.busResetPort`. Apply the identity-based rule to clock-pin handling too.

### 6. P2: Temporary handler bindings reject a valid resetless datapath

**Locations:** `pysrc/clockTree.py:947–953`, `2249–2253`.

A leaf can validly declare:

- Default datapath clock `clkA`, without a reset.
- Register clock `clkB`, with `rstB_n`.
- Its register port on `clkB`.

The initial binding pass treats the synthesized register handler as an implicit `clk/rst_n` child. It binds to default `clkA` and demands a reset before the later register-handler pass can move it to `clkB/rstB_n`.

**Proof:** `make db` rejects this fixture. Adding an unused reset on `clkA` makes it pass.

**Impact:** Valid multi-clock register leaves are rejected. The diagnostic suggests modifying the generator-owned handler.

**Suggested fix:** Resolve synthesized handlers directly onto their final bus domain before reset-binding validation.

### 7. P2: Memory-derived BFM ports bypass reset validation

**Locations:** `templates/systemc/module_hdl_wrapper.py:255–256`, `pysrc/processYaml.py:3271–3287`.

A `hasVl` leaf with `resets: {}` can obtain its interface through a parent-owned memory's `memoryConnections` row. This port category escapes the reset validation applied to ordinary BFM ports.

Database creation and generation succeed, emitting:

```cpp
tbl_bfm.clk(clk);
tbl_bfm.rst_n(None);
```

**Impact:** The generated SystemC wrapper cannot compile.

**Suggested fix:** Validate every port category that emits a BFM during project creation, including memory-derived ports. Reject the missing reset there. A template fallback would hide the broken producer contract.

### 8. P2: Reused passthrough blocks get inconsistent register-bus boundaries

**Locations:** `config/postParseRegisterPorts.py:885–888`, `1056–1060`.

Instantiate one router-less wrapper under two routers whose `registerDecoderPort` names differ. When the wrapper has no explicit `registerPorts:`, dispatch chooses each router's name independently, but the wrapper's internal boundary map uses only the first serving router.

The generated wrapper declares both `apbReg` and `customDecoder`, while its inner leaf connects only to `apbReg`.

**Proof:** Database creation and generation succeed; RTL lint fails with missing interface connections. Making the two router port names agree passes lint.

**Impact:** Accepted YAML produces an unelaboratable hierarchy.

**Suggested fix:** Validate a single inferred boundary binding across all instances of a passthrough block. Reject conflicting inference and require an explicit `registerPorts:` boundary.

### 9. P2: Passthrough inference ignores an authored child-local interface

**Locations:** `config/postParseRegisterPorts.py:755–758`, `1061–1074`.

A reusable wrapper in `child.yaml` declares a register boundary using its own `ipReg` interface. Its inner register-owning leaf relies on inference. An outer router in `parent.yaml` uses a compatible `apbReg` interface.

The recursive serving-router lookup imports the outer router's interface into the child's generated connection map, bypassing the wrapper's authored boundary.

**Proof:** `make db` fails with:

```text
value apbReg was not valid in context child.yaml
but is defined in parent.yaml
```

Explicitly repeating `ipReg` on the inner leaf makes generation pass.

**Impact:** A reusable wrapper cannot infer its internal register connection from its own declared boundary.

**Suggested fix:** Propagate the nearest authored passthrough boundary's interface inward. Resolve handler port naming separately from interface ownership.

## Python architecture assessment

**FAIL: The branch needs producer-contract fixes before approval.**

The strongest issues are concrete data-model failures:

- Hierarchy occurrences collapse into declaration-level keys.
- Port deduplication happens before cross-instance domain agreement is established.
- Emitted router pin identity differs between consumers.
- Reset validation does not cover every generated BFM source.
- Register passthrough inference crosses an authored interface boundary.

These fixes belong primarily in `projectCreate` derivation/validation and shared `projectOpen` views. Adding defaults, compatibility lookups, or template-side recovery would conceal the failures.

The review did not establish additional actionable defects in the `schema.py` or `valueResolver.py` changes.

## Independent hardware assessment

- **PASS:** All 20 existing `memory_reg_bridge` simulation configurations passed, covering reset styles, clock ratios/phases, reset recovery, and CDC-jitter injection.
- **PASS:** Generated 96-bit memory-handler tests passed staged writes, readback, exact write counts, and memory-held-reset error responses in both APB ready modes.
- **PASS:** Targeted `twoClk` simulations passed readback, partial-row accumulation, error propagation, and recovery under synchronous and asynchronous reset builds.
- **PASS:** Targeted `clkGen` RTL simulations checked divided-clock operation, reset assertion, synchronized release, and consumer restart.
- **FAIL:** Router pin generation and wrapper timing have the defects above.

### Additional warnings

1. **Inherited APB padding-read hang.** At `templates/systemVerilog/moduleRegs.py:810–824`, a 96-bit row has a 16-byte stride, but reading padding offset `0xC` matches no word case. The generated handler leaves `pready=0` and issues no bridge request. This remained stuck for 200 bus cycles in both APB ready modes. The new bridged path copies an existing same-clock defect.
2. **The checked-in `clkGen` test is not a functional scoreboard.** Its external test completes after 500 ns, and its leaf models are empty scaffolds. A green example sweep alone does not prove the clock/reset chain.
3. **Lockstep reset pulse responsibility needs explicit documentation.** Socket reset counts use a fixed 1 ns timebase, so a short pulse can miss a slow synchronous domain. This follows the explicit partner-owned reset contract and is not counted as an implementation blocker. See `plans/spec-clock-reset-requirements.md:723–730`, `783–791`, and `989–992`.
4. **The new watchdog imposes a wall-time termination policy.** Delayed voter registration or future force-and-stop completion can be preempted after the grace period. This matches the accepted watchdog plan, so it is a compatibility concern rather than an implementation defect. See `plans/plan-tb-external-terminator.md:131–154` and `186–190`.

Hardware checklist: **4 PASS, 2 FAIL categories, 4 WARN**.

## Verification and reproduction artifacts

The findings were checked with make-driven generation, reopened database views, actual generated artifacts, Verilator elaboration, and compiled SystemC probes.

Temporary reproduction artifacts were retained under `/tmp/opencode` at review time. They are local artifacts, not committed regression fixtures, and may not survive environment cleanup.

```bash
make -C /tmp/opencode/hw129-review -j2 lint-wrapper lint-router
make -C /tmp/opencode -f clock-review.mk -j8 check
```

The lint command intentionally reproduces the router failures.

Additional artifact locations:

| Finding | Reproduction artifact |
| --- | --- |
| 1 | `/tmp/opencode/clock-router`, `/tmp/opencode/hw129-review` |
| 2 | `/tmp/opencode/clock-review.mk`, `/tmp/opencode/socket_clock_review.cpp` |
| 3 | `/tmp/opencode/clock-review/design.yaml`, `/tmp/opencode/clock-review/probe.py` |
| 4 | `/tmp/opencode/clock-ports/design.yaml`, `/tmp/opencode/clock-ports/probe.py` |
| 5 | `/tmp/opencode/hw129-review` |
| 6 | `/tmp/opencode/clock-register/design.yaml` |
| 7 | `/tmp/opencode/verif/leaf_hdl_sc_wrapper.h`, `/tmp/opencode/review-checks.py` |
| 8 | `/tmp/opencode/regports-review-1ajw3w6t`, passing control `/tmp/opencode/regports-review-4ufv_bwq` |
| 9 | `/tmp/opencode/regports-review-l3kydhg9`, passing control `/tmp/opencode/regports-review-_e1fg72u` |
| Padding-read warning | `/tmp/opencode/hw129-review/handler_tb.sv` |

The register-passthrough reproduction driver is `/tmp/opencode/regports_review.py`. It routes database creation and generation through project make targets.

Additional checks reported by the independent reviews:

- All 14 schema-only cases in `test_project_scope.run_schema_cases()` passed.
- 26 cases across 13 register-routing suites passed, covering passthrough chains, reuse, address-group diagnostics, unserved consumers, nested-router rejection, router register/memory ownership, authored handlers, and explicit port names.
- A `Q_ASSERT` after timed `sc_start()` reached the summary path and preserved exit status 1. The suspected assertion-exit regression was excluded.

## Limits and PR recommendation

The full regression suite and full SystemC/tandem example matrix were not run. Physical CDC/RDC analysis, synthesis/STA, and four-state simulation remain unverified. The passing bridge simulations do not establish physical metastability or bundled-data timing guarantees.

**PR recommendation:** Fix the nine findings, then rerun the full suite with these adversarial cases added. The existing happy-path tests miss the identity, reuse, and inference failures that dominate this review.
