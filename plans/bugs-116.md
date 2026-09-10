# Bug Register — #116 Parameterized Types and Composition

Status as of: 2026-08-04
Branch context: `feature/116-parameterized-types` in `builder/base` (HEAD `2b3f6d1`)

This is the defect register for the #116 release. It exists so that
[`plan-116-status-report.md`](./plan-116-status-report.md) stays a status index
and its executive overview stays usable as release-note source text: that
document states *what shipped*, this one states *what was broken*, and it links
back for each item.

Two classes of defect are recorded, and they must not be conflated:

- **Section 1 — release blockers found and fixed during this cycle (B1-B5).**
  Found by running acceptance for the 2026-08-04 status refresh. All five are
  fixed in the working tree and verified. None was caused by a review action
  item, though item 5's module work exposed three of them.
- **Section 2 — external bug reports under review (BUG 10, 12, 13).** Raised
  from ISP module parameterization work, reviewed here against the code. These
  are **not fixed**. Each entry states what was confirmed, what the originating
  report got wrong, and where the fix belongs.

**BUG 9 is deliberately not in this register.** The status-port tandem comparison
is a different category of problem: the tee code does what it was written to do,
and what is wrong is the premise that a status port presents a comparable sequence
of events at all. It needs a design decision and probably a prototype before any
code changes, so it has its own document —
[`bug-status-port-tandem-compare.md`](./bug-status-port-tandem-compare.md). This
register is for defects with determinate fixes.

Source documents for Section 2 live outside the repository, in the reporter's
home directory: `~/isp-parameterization-bug-report.md` (the index, BUG 1-9),
`~/bug-parameterized-types-lose-signedness.md` (BUG 10), and
`~/bug-lut-unsigned-saturate-and-coverage-gap.md` (BUG 12/13). BUG 1-7 are
recorded there as fixed; BUG 8 was fixed in this cycle by commit `de022a1`
(parameterized register reset values).

## Verification status of this register

Every claim in Section 1 was verified by execution: unit suites **87 of 87** in
25 s, and `make pipeline-test` exit code 0 with **38 `No error`** reports and zero
occurrences of `make: ***`, `Premature`, `Fatal`, `error:`, or `%Error` across
all 14 targets. Section 2 entries are read-only code reviews; no fix was
attempted and no build was run for them.

## Section 1 — Release blockers found and fixed 2026-08-04

Five defects were found by running the base acceptance suite at HEAD `2b3f6d1`.
All five are fixed in the working tree; none is committed, because
`builder/base` is a submodule the user stages. Each entry states the defect as
found and then the fix as landed.

- **B1 — the end-of-test startup gate discarded an early explicit vote —
  FIXED.**
  `examples/nested` and `examples/helloWorld` complete every registered test and
  then abort on `Premature end of test detected`
  (`nestedConfig.cpp:76`, `helloWorldConfig.cpp:57`), which fails
  `make pipeline-test` at its second target. The cause is the startup gate added
  with the `a2c.endOfTest` module. `evaluateEndOfTest`
  (`common/systemc/endOfTest.cppm:74-81`) returns immediately while
  `startupComplete` is false, and it sets `hasBeenActive` only when it observes
  `endOfTestCounter < voters`. `sc_main` flips `startupComplete` after
  `simController::startupDelay`, which defaults to 100 ns
  (`common/systemc/simController.cpp:101`). A test that registers its voter and
  votes done inside that window is therefore evaluated once, at the startup
  flip, with the counter already equal to the voter count, so `hasBeenActive`
  never becomes true and end-of-test never latches. Fast, self-driving
  model-only examples hit this deterministically; `ip_test`, whose worker and
  firmware threads run past the startup delay, does not.
  **Fix:** activity is now recorded at vote time rather than inferred at
  evaluation time. `setEndOfTest` sets a `voteCast` flag unconditionally before
  the counter mutation and before the gate is consulted, `evaluateEndOfTest`
  latches on `voteCast && endOfTestCounter >= voters`, and the eval-time probe
  `if (endOfTestCounter < voters) hasBeenActive = true;` is deleted, with the
  member renamed `hasBeenActive` to `voteCast`. The gate itself and the single
  re-evaluation from `setStartupComplete()` are unchanged. Stated invariant: *a
  cast vote is the evidence that the test ran, and it is recorded when the vote
  happens, never inferred at evaluation time.* Recording activity on a *busy*
  vote would not have worked: a voter is busy implicitly by registration
  (`registerVoter()` raises `voters` without touching the counter) and
  `endOfTest::setEndOfTest` forwards only on a state change, so the entire vote
  history of the five failing examples is one `true` vote.
  **Semantic consequence to be aware of:** this is a strict relaxation of the
  guard. `voteCast` is implied wherever the old predicate permitted a latch, but
  it additionally permits one case the old code rejected — if every registered
  voter has voted done at the instant of the flip and a lazily-registered voter
  arrives afterwards, end-of-test now latches. Protection for that case now rests
  solely on `startupDelay` being long enough for firmware and runtime host
  threads to register, which is precisely what `scmain/main.cpp:259-267` says the
  delay is for, and which the old code covered only incidentally. `voteCast`
  still blocks the case the guard demonstrably protects: a project that never
  votes has `voters == 0`, making `endOfTestCounter >= voters` trivially true at
  the flip. The rejected alternative was sourcing independent activity evidence
  from `testController`; it preserves the stricter guard but couples end-of-test
  to the test registry and introduces a second notion of activity. **A known
  pre-existing weakness is unchanged in character:** the compound
  `voteCast && endOfTestCounter >= voters` read is not atomic as a whole, since
  these are separate `std::atomic` members, and end-of-test is voted from both
  SystemC threads and host worker and firmware threads.
- **B2 — a unit suite was failing and three suites were not wired into the
  serial runner — RESOLVED 2026-08-04.**
  `unittest/test_module_identity_uniqueness.py` failed 1 of 2 cases: it asserted
  the collision diagnostic contains `Module/package identity 'dupctx'`, while the
  project-qualified identity makes the message read
  `'module_identity_test_dupctx'`. The guard fires correctly and reports the
  qualified name, which is the name that actually collides in emitted output, so
  this was a stale test expectation of exactly the kind already corrected in
  `test_nested_ownership` and `test_foreign_key_lookup`. Fixed by deriving the
  expectation from `qualifyModuleIdentity` rather than a literal, following the
  `test_nested_ownership.py:371,385` precedent, so it cannot drift again; 2 of 2
  now pass and no non-test file changed.
  The registration gap was **three** suites, not two, and the exclusion was an
  omission rather than a decision — `test_module_identity_uniqueness.py` was
  added in `11be2e2`, which touched only the test file;
  `test_parameter_variant_block_param_identity.py` was added in `fd9ee1d`, which
  registered roughly twenty other new suites but skipped this one; and
  `test_error_nested_decoder_overflow.py` (review item 4's negative fixture,
  added in `14ce4c4`) was never registered in the serial runner at all and was
  only picked up implicitly by the parallel runner's globbing. The parallel
  runner's `EXCLUDE` array is removed, all three are registered in
  `run_all_tests.sh`, and both runners now select **87 of 87** present files with
  none dropped or duplicated. Both newly registered identity suites are
  classified ISOLATED on verified evidence (neither references `examples` at all;
  both create inputs via uniquely named `mkstemp` under the test directory), so
  the parallel runner's reader-versus-writer guarantee for `examples/` is
  unaffected. The parallel drop-guard count moved 84 to 87, which also silences a
  warning it would otherwise have printed on every run.
  Two pre-existing hygiene items were found and deliberately left alone: eleven
  gitignored `tmp*.db` files leaked into `unittest/` by some suite's failure path,
  and two leaked temp fixtures that were committed in `fd9ee1d`
  (`unittest/addrctl_arch_0ugcg0_g.yaml`,
  `unittest/addrctl_proj_xv1hd_h5_project.yaml`).
- **B3 — the committed example tree carried stale composed-child artifacts —
  FIXED.**
  The `a2c.endOfTest` migration and the module-preamble relocation regenerated
  only root-owned files, so `examples/ip_test/bridge` still shipped its previous
  form. Building composed `ip_test` failed with
  `imports must immediately follow the module declaration` at
  `bridge/model/bridgeDriver.cppm:22`, because the stale `moduleExport` region
  still emitted `using namespace ipBridge_ns;` ahead of the user import slot.
  Running the child project's own `make clean gen` fixes it and changes six
  files under `bridge/`. This is the committed-tree instance of the rule the
  migration skill already documents: a composed child must be regenerated in its
  own project, not through the parent.
  **Fix:** all 17 projects were swept — `make clean` then `make gen -j`,
  sequentially, each in its own project directory, children before parents.
  **Every stale file was in a composed child; every root-owned project was
  already current**, which is direct confirmation of the rule above. Ten further
  stale files were found beyond the six in `bridge/`: the module-preamble
  relocation had not reached `ip_test/common/cpu/model/cpu.cppm`,
  `simple_ip/common/cpu/model/cpu.cppm`, and the five
  `simple_ip/ip/model/ipStd*.cppm` and `ip.cppm` blocks; the `a2c.endOfTest`
  import had not reached `simple_ip/ip/tb/ip/{ipExternal,ipTestbench}.cpp`; and
  the parameterized register reset fix from `de022a1` had not reached
  `simple_ip/ip/rtl/ipRegs.sv`, which had no `ipCfg_rst` local parameter. The two
  testbench files gain a second `import a2c.endOfTest;` (one in the file
  preamble, one in the generated section); that duplication is already the
  committed form in root-owned equivalents such as
  `examples/nested/tb/nested/nestedExternal.cpp:1,8`, so the sweep makes children
  consistent rather than introducing anything new. Harmonizing that duplication
  is a template change and was deliberately left out of scope.
- **B4 — `make clean` from the project root left the object and dependency tree
  behind — FIXED.** The dependency files written by a previous build survive a
  clean and still name `common/systemc/endOfTest.h`, which this release deletes
  in favour of the module, so every affected example fails with
  `No rule to make target .../endOfTest.h`. The original diagnosis needed one
  correction: `make -C <project>/rundir clean` *did* remove `rundir/build`. The
  gap was `make clean` at the **project root**, which is what the base
  `Makefile` clean target invokes for every example, because `BIN_DIR` was
  defined only in `a2c-systemc.mk` and only `rundir/Makefile` includes that file.
  **Fix:** `BIN_DIR` moved to `include/make/a2c-common.mk` (which also owns
  `PROJECT_RUNDIR`, and which `a2c-systemc.mk` hard-errors without, so the
  variable cannot be undefined at any use site), and the shared `clean::` there
  now removes it alongside `GEN_BUILD_DIR`. The redundant removal in
  `a2c-systemc.mk` is dropped, leaving that rule to `simx.*` and `gcm.cache`.
  Verified: root clean and rundir clean both remove `rundir/build`, rebuild and
  run after clean succeed, and the `run-vl` targets that invoke `clean`
  internally all pass. `common/systemc/Makefile` is standalone with its own
  `./build` and is unaffected.
- **B5 — the firmware board-support relocation was not opted into by the
  `bridge` sub-project — FIXED.** Surfaced only once B3's regeneration let the
  build get further: `make -C examples/ip_test/bridge/rundir run` failed with
  `examples/ip_test/common/cpu/model/cpu.cppm:16:10: fatal error: 'modelComm.h'
  file not found`. This is a pre-existing consequence of the board-support
  package moving from `common/systemc/bsp` to `common/fw/bsp` in `7274b9c` and
  out of the default `A2C_SRC_DIRS`. Only `examples/ip_test/rundir/Makefile`
  received the `EXTRA_A2C_SRC_DIRS` opt-in; `bridge` needs it too, because
  including the common project puts `common/cpu/model/cpu.cppm` into bridge's
  compile closure. `ip_test/ip` has no common directories, which is why it never
  failed. **Fix:** the established opt-in is mirrored in
  `examples/ip_test/bridge/rundir/Makefile`. **Left open deliberately:** whether a
  standalone IP project should be compiling the parent's `cpu` block at all is a
  manifest and architecture question, not a build-flag question.


## Disposition decided 2026-08-04

- **BUG 10 — FIXED 2026-08-04, with example coverage.** The generator fix is the
  one-token signedness selection; the substantive part of the work is the
  coverage, because the base and pro example suites are currently blind to the
  defect and the fix alone leaves every example byte-identical. Coverage is
  therefore two-level: a structural assertion on the emitted alias text (the
  emitter has no test coverage of any kind today) and an executed value-level
  assertion in an example fixture. The acceptance gate is that the new tests must
  **fail without the fix and pass with it** — a plain round-trip does not
  discriminate, for the reason recorded under BUG 10 below.
- **BUG 12 — no separate fix.** Its root cause is BUG 10. The `int64_t` casts
  already applied in `isp_lut/model/lut_core.cppm` and
  `isp_lsc/model/lsc_core.cppm` are correct workarounds and become redundant but
  harmless once BUG 10 lands; removing them is optional cleanup, not part of the
  fix.
- **BUG 13 — analysed to completion, not closeable from this tree.** The earlier
  rationale for sequencing it after BUG 10 (contention over the builder tree) no
  longer applies and is superseded: every file it needs to change is in
  `/work/ws/isp`, and out-of-tree code is neither to be modified nor executed. The
  analysis is finished and specified to the point of execution, including the
  reachability question the register had left open. It is a verification-methodology
  gap owned wholly by `isp_lut` and needs no builder change.
- **BUG 9 — split out to its own document for study and prototyping.** See
  [`bug-status-port-tandem-compare.md`](./bug-status-port-tandem-compare.md). It is
  a verification-harness design question rather than a defect with a known fix, it
  has no test harness in the repository at all, and a fixture has to be built
  before any candidate fix can even be evaluated.

The general principle applied here: **as each defect is addressed, coverage lands
with it in the examples.** BUG 10 is the cautionary case — a real generator defect
that the entire in-tree example corpus could not see.

## Section 2 — External bug reports reviewed 2026-08-04 (NOT fixed)

### BUG 10 — parameterizable types lose signedness — FIXED 2026-08-04

**Verdict: CONFIRMED. FIXED, with coverage. Owner: `builder/base` generator.**
Unusually for this series the originating report's file and line citations are
exact against the current tree. Source:
`~/bug-parameterized-types-lose-signedness.md`.

**Fix as landed:** `templates/systemc/includes.py:127` now selects
`containerType = 'int64_t' if value['isSigned'] else 'uint64_t'` for the scalar
parameterizable arm, keeping the fixed 64-bit container. `widthComment`
(`:119`) and the multi-word arm (`maxBitwidth > 64`) are unchanged — see the
deliberate-omission notes below.

**Coverage as landed** (two levels, both proven to fail without the fix):
- `unittest/test_param_type_signedness.py` (new, registered in both runners;
  suite count 87 -> 88) renders `includeTypes` and pins the exact emitted alias
  text for a signed scalar, an unsigned scalar, a signed non-parameterizable
  type, and a signed multi-word type. Its signed fixture has realwidth 8 and
  maxBitwidth 40, so the expected text also pins the container to the worst case
  rather than to `platformDataType`.
- `examples/ip_test/ip/yaml/ip.yaml` gains `ipSignedParamT`
  (`width: IP_MEM_DEPTH, isSigned: true`, derived `maxBitwidth` 32 against
  realwidth 16) and `ipSignedParamSt`, which `structContainsSignedTypes`
  classifies signed so the generated round-trip runs it with `signedPatterns` at
  all three sample points. The value-level discriminator is in
  `examples/ip_test/top/tb/ip_top/ip_topConfig.cpp` — unpack an all-ones pattern
  and assert `offset < 0` and `(offset >> 1) == offset`, neither of which holds
  for an unsigned container.

**Proof:** with the fix reverted the unit suite reports
`got: ... using signedParamT = uint64_t` and fails; `ip_test` builds and then
aborts at `[Q_ASSERT][checkSignedParameterizableField] signed parameterizable
field did not unpack negative`, *after* `test_ip_structs` has passed — direct
confirmation that the round-trip cannot see the defect. With the fix: unit suite
88 of 88, `make pipeline-test` exit 0 with 38 `No error` and zero occurrences of
`make: ***`, `Premature`, `Fatal`, `error:`, or `%Error`.

**The predicted zero blast radius is confirmed by query, not by inspection.**
Across all 17 base example projects and the one pro example, `ipSignedParamT`
is the *only* row with `isParameterizable=1 AND isSigned=1`, so the fix provably
cannot alter any other generated line. Every changed generated file is in
`examples/ip_test/ip/` and every changed line mentions `ipSignedParam*`.

In `includeTypes`
(`templates/systemc/includes.py:113-138`) the **parameterizable** branch
hardcodes the container type in an f-string (`:123` scalar, `:128` multi-word)
and never reads `isSigned`, then `continue`s at `:130`; the
non-parameterizable branch immediately below (`:131-138`) emits
`platformDataType`, which honours signedness correctly. These two lines are the
**only** sites in the generator that emit a parameterizable C++ type alias, so
the defect is one omission in one branch, not a missing capability. `isSigned`
is schema-backed and contracted (`config/schema.yaml:98`, a real boolean via
`pysrc/schema.py:1025-1026`), is already consumed at database-build time in the
same derivation that sets `isParameterizable` (`processYaml.py:7198` onward),
and the SystemVerilog emitter honours it unconditionally including for
parameterizable types
(`templates/systemVerilog/constantsTypesEnumsStructures.py:25-27`), so the
model-versus-RTL asymmetry is real.
- **The report's own suggested fix would introduce a new truncation defect.**
  `platformDataType` is derived from `realwidth`, the width at *default*
  parameter values (`processYaml.py:1119`, `:1130-1137`), whereas a
  parameterizable container must be sized by `maxBitwidth`, the worst case
  across variants. For `lsc_pixel_m_factor_t` those differ — 26 versus 34 — so
  substituting `platformDataType` would emit `int32_t` and silently truncate
  for any variant with `BITS_PER_PIXEL_COLOR > 6`. The fixed 64-bit container is
  correct; **only the signedness should become conditional**
  (`'int64_t' if value['isSigned'] else 'uint64_t'`). This adds no width
  restriction: a `W`-bit signed field in an `int64_t` is exact for all `W` up
  to and including 64, which is the branch's own guard.
- **Blast radius: nine types across three ISP modules**, and zero exposure in
  `builder/base/examples`, `builder/pro/examples`, or the debayer product —
  those trees declare both axes but never on the same type, so **the whole
  example suite is blind to this defect and regenerates byte-identical across
  the fix.** A new fixture is mandatory, not optional.
- **It is also a firmware-interface defect, which the report understates.**
  Four of the nine types back register or `regAccess` memory structures, so
  firmware headers present declared-signed register fields as `uint64_t`.
- **Why it is silent rather than loud.** Sign extension is emitted with a
  64-bit-wide mask and is *unconditional* on the parameterizable path, because
  the guard at `templates/systemc/structures.py:1025` tests
  `not isinstance(bitwidth, int)` and a parameterizable width is a symbolic
  string. The container therefore holds a correct full-width two's-complement
  pattern, so `pack`, `unpack`, `sc_pack`, `sc_unpack`, `prt`, `sc_trace`, and
  `operator==` all behave identically to the signed case. The only observable
  difference is the meaning of `>>`, `<`, `/`, and `%` applied to the alias.
  This is why `isp_ccm` is accidentally immune — it also never computes on the
  alias, casting into `sc_int<>` first — and why a green regression proves
  nothing.
- **The existing round-trip test cannot catch it.** `_roundTripHelperLines`
  (`structures.py:1476-1530`) compares pack against unpack and against the raw
  bits but never inspects a field's *value*, and both paths sign-extend
  identically into whichever container is emitted, so the assertions pass with
  either type. A test that merely round-trips a negative value through a signed
  parameterizable type would pass before *and* after the fix. Closing this
  needs a structural assertion on the emitted alias text — `includeTypes` has
  **no test coverage of any kind** today and `isSigned` appears nowhere in
  `unittest/` — plus, if a runtime assertion is wanted, a value-level check
  such as unpack-from-all-ones comparing less than zero.
- **Separate latent defect found alongside — STILL OPEN, deliberately not fixed.**
  Multi-word signed types (`maxBitwidth > 64`) receive no sign extension in
  *either* branch, because `get_sign_extension_code` is called only from the
  single-word arms (`templates/systemc/structures.py:930`, `:1172`). No affected
  type exceeds 34 bits, so it is latent. This is also why the multi-word arm of
  `includeTypes` was left emitting `uint64_t word[N]`: that shape has no
  arithmetic operators, so signedness is unobservable on it, and emitting
  `int64_t word[N]` would advertise signed support that the missing sign
  extension does not deliver.
- **Ownership:** the one-token change is template-side under
  `builder/base/CLAUDE.md`, since it derives nothing new and selects a C++
  spelling from a contracted boolean, exactly as the adjacent SystemVerilog
  emitter does. A consistency alternative — a sibling `projectOpen` view field
  computed from `maxBitwidth` — would also let the template stop computing
  `(maxBitwidth + 63) // 64` at `includes.py:126`. That is a view-contract
  change and is the user's decision.

### BUG 12 — LUT unsigned saturate

**Verdict: CONFIRMED. Not fixed at source. Owner: same generator defect as BUG 10,
with a product-code exposure in `isp_lut`.** Source:
`~/bug-lut-unsigned-saturate-and-coverage-gap.md`.

The report's arithmetic and its stated owning layer are correct; its explanation
for the missing compiler diagnostic is wrong, and the truth is worse.

- **Regression proven by history, not inference.** At committed `HEAD`
  `isp_lut/model/lutIncludes.cppm:40` read `typedef int32_t lut_slope_t; // [18]`.
  In the working tree the same type is
  `template<typename Config> using lut_slope_t = uint64_t`. Signedness was
  honoured while the width was a literal and lost the moment the width became
  parameter-dependent — which is BUG 10's branch, confirmed in code rather than
  assumed from the report.
- **The generator layer contradicts itself, which pins ownership.** The alias
  emitter drops signedness while the *structure* template still emits sign
  extension for the same field (`lutIncludes.cppm:422-425`). The database knows
  the type is signed; only the alias emission discards it.
- **Concrete failing case, verified numerically** at the model default variant
  (`LUT_ACCUM_WIDTH=10`, `LUT_OFFSET_WIDTH=8`,
  `LUT_SLOPE_FRACTIONAL_WIDTH=10`, `MAX_PIXEL_VALUE=255`, per
  `model/lutVariantConfig.h:17-26`): for a 10-bit signed accumulator of `-1`, `-3`,
  or a wrapped `-386`, the pre-fix model returns **255** where both the RTL
  (`rtl/lut_core.sv:271-276`) and the testbench golden
  (`model/rgb_img_writer_impl.cpp:96-97`) return **0**. That is a 255-count error
  per affected pixel per channel. Mechanism: `sign_extend` returns `int32_t`, the
  negative result converts to `uint64_t` as a 64-bit sign-extended pattern, so
  `accum < 0` is unreachable and the `accum > 255` arm is taken.
- **CORRECTION to the report — the compiler safety net is not merely switched off,
  it is structurally unavailable.** Verified by control compile (GCC 13.1, scratch
  files only): `a < 0` on a **non-dependent** `uint64_t` *does* warn
  (`-Wtype-limits`, enabled through `-Wextra` at
  `include/make/a2c-systemc.mk:44`), and `-Wno-sign-compare`
  (`a2c-systemc.mk:175`) does **not** suppress it — that flag governs
  signed/unsigned comparisons, not `x < 0`. But the identical comparison on a
  **template-dependent** alias, which is exactly how these types are spelled
  (`model/lut_core.cppm:78`), produces **no warning at all**, with or without the
  flag. So the diagnostic is unavailable for every `Config`-parameterized type in
  every module, and flag hygiene cannot recover it. Only fixing the alias emission
  can.
- **The applied `int64_t` change in `isp_lut/model/lut_core.cppm:369-392` is a
  correct workaround, not the fix.** The same workaround already exists in
  `isp_lsc/model/lsc_core.cppm:313-336`, which confirms the cross-module
  footprint. Once BUG 10 is fixed at source these explicit casts become redundant
  but remain harmless.

### BUG 13 — LUT regression coverage gap

**Verdict: CONFIRMED and materially worse than reported. Owner: `isp_lut`
verification methodology; no builder change required.**

The report's two central characterisations of the suite are both wrong, and three
corrections make the gap larger rather than smaller.

- **Confirmed as reported:** `rundir/regr_lut.json` passes `--lut_cfg` on exactly
  two entries, both under `model_tests/basic`. Every other entry inherits
  `--lut_cfg 0` (`tb/lut/lutConfig.cpp:48`), driving `REG_LUT_ENABLE = 0`
  (`model/fw/fwModelMain.cpp:37-39`), and the model gates the entire arithmetic
  block on `if (enable_v_.enable)` (`model/lut_core.cppm:304`).
- **Correction 1 — `model_tests/basic` performs no value check whatsoever.** The
  golden LUT reference is computed (`model/rgb_img_writer_impl.cpp:72-153`) but its
  only consumer is `createDiffImage`, which writes a PNG and asserts nothing
  (`:241-246`). The only assertions on that path are frame geometry and
  end-of-test. `rundir/Makefile` `clean::` then deletes the PNGs. So the two runs
  that *do* enable the LUT verify nothing about arithmetic values — not against
  RTL, and not against the golden either.
- **Correction 2 — half the "tandem" groups cannot detect model-versus-RTL
  divergence at all.** `model_tests/tandem` and `model_tests/tandem_delay` use
  `--vlType model --vlTandem`, which is model/model tandem. Only
  `hdl_tests/tandem` and `hdl_tests/tandem_delay` compare RTL against model.
- **Correction 3 —** `--lut_cfg 16` is `generateDisabledInversion` with
  `enable = false` (`tb/lut/lutTestConfigs.h:296-303`), not a selectable enabled
  inversion. Only `--lut_cfg 10` is.
- **Actual coverage: LUT arithmetic has never been compared against any reference,
  in any configuration.** Value-checking runs total **8**
  (`hdl_tests/tandem` plus `hdl_tests/tandem_delay`, two tests each across `lut`
  and `lut_core`), and **all 8 run `--lut_cfg 0`, pure bypass**. Sign extension,
  `frac * slope`, the arithmetic right shift, the 10-bit accumulator truncation,
  offset addition, and saturation are all unverified. A `32/32` pass is therefore
  consistent with the arithmetic being arbitrarily wrong.
- **Does BUG 13 explain BUG 12 escaping? Yes, over-determinedly** — two
  independent sufficient conditions: no RTL/model comparison run enables the LUT,
  and the runs that enable it assert nothing. Enabling the *existing* inversion
  vector would not have caught BUG 12 either: `generateInversion`
  (`tb/lut/lutTestConfigs.h:116-133`) yields a minimum accumulator of `+3`.
- **A further divergence class not in the report:** the 10-bit accumulator can
  overflow upward and wrap negative (offset 255 plus 383 gives 638, wrapping to
  −386). RTL and the fixed model both return 0, but the golden returns 255 because
  `rgb_img_writer_impl.cpp:96` computes in `int16_t` with **no accumulator
  truncation**. The golden is not a faithful reference at the overflow corner.
  Reported as apparently unreachable today with moderate confidence only; the firm
  implication is that aggressive new vectors must be validated through tandem, not
  through the golden, until `genLUTReference` models the accumulator width.
- **Is default-to-bypass correct? Two different defaults, two different answers.**
  The *hardware register* default is correct and must not change
  (`yaml/lut.yaml:203`, matched by the RTL reset at `rtl/lut_regs.sv:94`) because
  the LUT memories are uninitialised at reset. The *testbench option* default is
  the actual problem: `tb/lut/lutConfig.cpp:48` makes a functionally disabled DUT
  the default for any test that does not opt in, so under-coverage is the path of
  least resistance and is invisible in the pass count. Recommended remedy is to
  leave the default alone and make `--lut_cfg` explicit on every regression entry,
  so a bypass run is always a deliberate declaration.
- **Minimum to close.** One new vector plus one JSON entry would have caught
  BUG 12: append a steep-inverse vector to `lutTestConfigs[]` and add it under
  `hdl_tests/tandem → lut_core`. Four entries make the datapath genuinely
  verified: gamma at both `lut` and `lut_core`, the existing inversion
  (`--lut_cfg 10`) for negative slope, product, and arithmetic shift, and the new
  steep-inverse vector as the only one reaching a negative accumulator. Beyond the
  minimum: mirror all four into `hdl_tests/tandem_delay`, make `--lut_cfg`
  explicit everywhere, and add a real value assertion against the golden — but
  only after `genLUTReference` models the accumulator truncation, or it will
  produce false failures.

**Reachability of the proposed vector — settled 2026-08-04 by independent
read-only inspection.** The register previously specified the steep-inverse vector
without confirming that any existing stimulus reaches the negative-accumulator
points. It does.

- `synthetic_data` fills every channel with `i % 256`
  (`model/b2p_rgb_conv_impl.cpp:36-43`), so pixel values 253, 254 and 255 are all
  present in the frame. Those decompose to LUT address 63 with fractional parts 1,
  2 and 3 — exactly the points the vector needs. No new stimulus is required.
- Recomputed accumulator at address 63 with `offset = 0`, `slope = -1024`:
  `frac ∈ {1,2,3}` gives `accum ∈ {-1,-2,-3}`, three negative cases. `slope` is
  representable — `LUT_SLOPE_WIDTH = 18` signed holds -1024 comfortably.
- Selector arithmetic confirmed: `tb/lut/lutConfig.cpp:100` indexes
  `lutTestConfigs[lut_cfg_index - 1]`, so the option is 1-based over a 16-entry
  array (`tb/lut/lutTestConfigs.h:309-326`). An appended generator is `--lut_cfg 17`.
- Sharpens Correction 1: `has_ref` is set only by `setRGBReference`
  (`model/rgb_img_writer_impl.cpp:63`), which runs only under `--rgb_file`. Of the
  two LUT-enabled runs, `synthetic_gamma` therefore does not even *compute* the
  golden; only `testdata_gamma` reaches `genLUTReference`, and then discards it.

**Blocked on scope, not on analysis.** Every artefact BUG 13 requires changing —
`rundir/regr_lut.json`, `tb/lut/lutTestConfigs.h` — lives in `/work/ws/isp`, which
is outside this tree. Under the standing instruction not to modify or execute
out-of-tree code, BUG 13 cannot be closed from here. The specification above is
complete enough to be executed in the `isp` workspace without further analysis;
the accumulator-truncation caveat on `genLUTReference` still governs, so new
vectors must be validated through `hdl_tests/tandem`, not against the golden.

**Cross-cutting note.** The escape of BUG 12 required both defects. BUG 10 made
the code wrong and made the compiler structurally unable to report it; BUG 13 made
the runtime unable to report it either. Fixing BUG 10 alone removes this instance
but leaves `isp_lut` arithmetic unverified against RTL. Fixing BUG 13 alone leaves
every other parameterized signed type in every other module silently unsigned.

