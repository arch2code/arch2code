# Plan: Parameter Sharing Between A Parameterizable IP And Its Consumers

## Current Status

- **Classification (2026-08-31): SETTLED DESIGN WITH THE STEP 7 THROUGH STEP 11 FOLLOW-UP IMPLEMENTED AND VERIFIED IN THE WORKING TREE.** Step 1 landed and was independently reviewed. D7's parameter-scoped inheritance, its site-keyed layout gate, the registrar-pair work, and the testbench Config-source checks are complete locally. **Step 3 landed 2026-09-05** on an architect ruling that a block's Config carries only the parameters that block declares, with derived constants computed in the implementation as SystemVerilog already does (§6, step 3). **Step 3's fixture half closed 2026-09-06**: `twoCtx` is retargeted, asserts its bound values at run time, and is the `xproj-twoctx` gate in `pipeline-test`. Steps 2 and 5 and the RTL-bearing half of step 6 remain open; **step 4 landed on 2026-08-14 and is gated, and the "steps 2 through 5" phrasing this bullet carried until 2026-09-04 was wrong** (§6, step 4). Decisions D1 through D5 are the plan of record. D6 is resolved by the explicit link from a block parameter to its parameter source (§3), independently of Q3, which stays rejected (§4.3). Implementation is complete for this follow-up, but commit preparation is not: the final change set is not yet fully staged, committed, or pushed.
- **Plan review 2026-09-07.** The decisions of record and the end goal hold; steps 1, 3 and 7 through 11 deliver §1. Corrected in place: three lines that still listed step 3 as open, the "Q3's rename waits on step 3" dependency (Q3 is rejected), done criterion 2 (rewritten to §4.0), and the design document's claim that a Config may carry unnamed same-file parameters. Added: step 3's emitted-output delta (§6, step 3), the finding that `twoCtx` makes the §7 Config name and home flip live, and the finding that done criterion 6 is unmet for direct instantiation (`uLeafX`). Step 6's RTL half was redirected onto `twoCtx` after the dpMid attempt proved non-discriminating (§6, step 6). The skill rewrite landed (§6, step 7). Steps 12, 13 and 14 were opened on the user's ruling for Case 1 with the duplicate-in-scope diagnostic, the product tree's move off `inheritContainerParam`, and connectionMap adjudication of an inheriting child. Step 6 then closed the same day on `twoCtx`. The user ruled that Config ownership follows the project that declares the variant and that Config names always carry that project (step 15), and judged this plan contaminated with implementation detail: the guiding rules are now a draft section at the top of [`design-parameter-inheritance.md`](./design-parameter-inheritance.md), iterated there, with a dated list of where the tree deviates. Rules 2 and 7 (scope-based resolution, collision is an error) are the open part of that iteration; the user's expectation is that the parser already resolves by scope, and the deviation list records the evidence that it selects by project instead. Later the same day steps 2 and 5 landed (§6), each fault-injected and reviewed, and the rules iteration with the architect confirmed rules 1 through 3 and redrafted rule 4 around the two container-sourced forms (rule 1 now permits a definitions-only shared declaring file; rule 2 rejects shadowing; step 12's lexical proposal is withdrawn). The iteration then confirmed rules 5 through 10 (rule 4 ruled: `inheritContainerParam` stays same-project, cross-project goes through a `containerParam` variant), settled rule 7's scope resolution with its fixture consequences (step 12), and step 15 LANDED with the always-qualified Config names and the owner-declared `default` rule (§6, step 15). Open: steps 12, 13, 14; three follow-ups under step 15.
- **Step 12 split into 12a and 12b, 2026-09-08. Both LANDED.** Step 12a (rules 1 and 2); step 12b
  (rule 7, scope resolution of a variant label) moved `ip_test`'s bridge instance's declaration
  into `ipBridge.yaml` itself, the one shape the blast radius scan found needing a fixture move.
  See each step's own entry (§6) for the fixtures, the corpus-scan blast radius, the `uLeafX`
  decision, and the gates.
  A comment review across the whole change set followed (2026-09-08): 177 comment blocks judged,
  44 kept, 106 rewritten, 27 deleted; two wrong comments corrected (`cpp_own_config_import`,
  the `test_eval_cpp_emit` docstring), the label-selection invariant moved onto
  `_selectDeclaredDescriptor`, an unused `defaultConfig` parameter dropped from
  `cpp_descriptor_config_name`, and the contracted-field `.get()` fallbacks in
  `constructor.py::wordLinesExpr` replaced with direct reads. All gates re-run green.
- **Step 16 LANDED 2026-09-09.** An `inheritContainerParam` child's shared parameters must be the
  container's own `ipParameters` constants; a same-named different constant is rejected at
  `make db`. See §6, step 16.
- **Step 14 LANDED 2026-09-08.** The connectionMap arm (and the plain-connection arm) now
  adjudicate an `inheritContainerParam` end at its container's configuration instead of skipping
  it, fixing the defect step 10 had recorded and left open. See §6, step 14 for the fixture, the
  measured pre-fix pass on the rejecting arm, the gates, and the product-tree connections this
  newly adjudicates.
- **Step 13 LANDED 2026-09-08, then REVERTED 2026-09-09 (user).** `u_preprocess`/`u_interpolate` moved off `inheritContainerParam` onto declared `containerParam:`-sourced variants and back again, on the user's ruling that self-contained blocks do not declare `ports:` for internal plumbing; `yaml/debayer.yaml` is back at its pre-step-13 content, and the three generator fixes found on the way and their fixtures stand. See §6, step 13. **Pre-commit review applied and the full gate set re-run on the final tree, 2026-09-09:** two `SiteBindingIndex` fallbacks removed (§6, step 14, "Pre-commit review"); unit suite 120 of 120; base pipeline exit 0 with 66 "No error", 0 `ERROR:`, 3 `OK:`; pro pipeline exit 0 with 14 "No error"; product regenerates byte-identical to HEAD; model run and Verilated run two "No error" each. Ready to stage. Open: the inferred-port thunker gap step 13 found and did not fix (§6, step 13, "Defect found on the way, OPEN"); step 15 follow-ups (a) and (c); step 12a follow-ups (d) and (e).
- **Step 14 follow-up LANDED 2026-09-09.** The junction diagnostic names the container block and variant that supplied an inheriting or `containerParam:` side's values; `inhLayoutBad` is a multi-variant container and both layout gates assert the naming. Full gate set at baseline on the final tree. Ready to stage. Newly open: an inheriting nested router raises `KeyError` in `config/postParseRegisterPorts.py` (§6, step 14, "Found on the way").
- **Stale registrar detection and cleanup, LANDED 2026-09-10.** The manifest step warns about generated files in owned registrar directories the contract does not name; `make newmodule` deletes them (user ruling). The check found two true orphans (`ip_ipRegsVariantConfig.cppm` in the simple_ip and ip_test `ip` sub-projects, removed by their own `make newmodule`) and one pre-existing scaffold-definition gap: the `foreignConfig` fileMap entry required hasMdl or hasTb while the emitter imported a params block's Config module on hasOwnParams alone (xif_tb). Ruled "we cannot need a file but not scaffold it": the fileMap entry now keys on hasOwnParams only and the emitter decides through the same entry (§6, step 12a follow-up (d)). Full gates green, zero stale warnings anywhere. Committed in 9f5bfce together with inhLayout's nine new scaffold files (user's call: commit).
- **newModule bare-wrapper scaffold and the same-named endpoint note, LANDED 2026-09-10.** `make newmodule` no longer scaffolds a bare HDL wrapper for a params-declaring block whose every variant is container-sourced (§6, step 13 follow-up). The endpoint diagnostic's same-named note is kept under rule 2 and now has a fixture and a cell (§6, step 12a follow-up (e)). Facts for 12a (d), 15 (a) and the nested-router `KeyError` are recorded at their entries; each awaits a ruling. Gates: unit 121/121; base pipeline exit 0, 66 `No error`, 0 `ERROR:`, 3 `OK:`; pro 14 `No error`; product `make clean && make gen -j` diff-stat only the builder and isp_shared rows, rundir model run and `VL_DUT=1` run (`--vlInst=tb.debayer`) two `No error` each. Ready to stage.
- **Descriptor selectors assert one match, LANDED 2026-09-10.** The three selectors raise on zero or several matches instead of taking the first; new unit suite, runner count 121. Full gate set at baseline on the final tree. Ready to stage (§6, step 14, last bullet).
- **Step 17 LANDED 2026-09-10 (user ruling: support, the ISP will need it).** A nested register-bus
  router that declares `params:` and inherits or is container-sourced is a supported shape: the
  router-to-router check resolves both sides through the sibling that contains the nested router
  (per-side container sites in every junction diagnostic), the SystemVerilog router template emits
  the parameter header and local typedefs, a single-child router selects without a constant compare,
  the HDL wrapper takes the ordinary body for a params-less parameterizable container, register-bus
  structs are spelled Config-aware in the SystemC templates, and register accessors are Config-aware.
  New example `examples/xprojParam/rtInh` (`xproj-nested-router` in `pipeline-test`) proves it
  model and Verilated with firmware through both routers. Scope finding recorded as a limitation in
  `design-parameter-inheritance.md` §5: a register-bus structure sized by a parameter has no master
  that can drive it (no dispatch or boundary thunker). Seven follow-ups await rulings (§6, step 17,
  last bullet). Ready to stage.
- **artifactPaths extraction, LANDED 2026-09-10.** `expandNewModulePath`, `fileMapCondMatch` and
  `getRegistrarFiles` moved verbatim from `pysrc/processYaml.py` into the new `pysrc/artifactPaths.py`;
  ten callers repointed, no re-export. Behaviour-preserving; reviewed categorically, review applied.
  Gates at baseline on the final tree (§6, step 12a follow-up (d), last bullet). Committed in a139e68.
- **Step 1 LANDED 2026-08-13.** `blocksparams` carries `paramSource`/`paramSourceKey`, a foreign key onto `constants` resolved through the param row's own include chain; `param`/`paramKey` are retained unchanged as the block-scoped identity, and are deliberately NOT repointed. All four bad consumers of §5 B1, the two re-derivations of §4.5 and the orphan check now read the source link. Evidence, the mechanism chosen for the name defaulting, and the corrections to this document's own text are at "Plan of record" step 1. `examples/xprojParam/cstUse` — the probe this plan predicted would flip — **builds and runs, and is promoted into `xproj-const`** (the first half of step 6); `xproj-const-probes` is retired.
- **Step 1 was re-measured independently, 2026-08-13.** Unit suite **101/101**; cold `make pipeline-test -j` **exit 0**; `make xproj-const -j` **exit 0** with three cells at widths **12 / 20 / 20**; **zero** unresolved `paramSourceKey` rows; the product tree cold-regenerates, builds and links. **The emitted-output delta (1693 files, zero changed) and the census were taken on trust, not re-measured** — the earlier "Emitted-output delta: none, measured. Census: unchanged at 18 of 42" claim in this bullet list is corrected to that standing. The review also corrected three of this document's own figures (cold `paramKey` baseline, database census, `builder/pro`); see step 1's landed record.
- **One defect the review found was ruled on, FIXED, and is now VERIFIED BY BUILD (2026-08-18)** — the third silent early return in `_post_validateVariantBindingSizing`. See "Ruled on after the review" at step 1 for the measurements.
- ~~**Steps 2 (B4), 3 (B5) and 5 (B2) have NOT landed.**~~ **Steps 2 and 5 LANDED 2026-09-07, step 3 on 2026-09-05 (§6). Step 4 (B3) HAS**, on 2026-08-14, with its replacement acceptance gate; §6 read it as open until 2026-09-04 while §5 recorded it fixed, and §6 was the stale half. Step 6's remaining half, the RTL-bearing cell, has not landed either. **Step 7 (D7) is built and guarded.** Step 7a supplies the schema field, declaration-time checks, site-time validator, and SystemVerilog emission. Step 7b supplies the site-keyed layout gate. Step 7c emits a C++ Config templated on the container's Config, per the architect's 2026-08-14 ruling. The local fixture family and the cross-project Verilated regression both pass.
- **The built parts of step 7 ARE REGRESSION-GUARDED as of 2026-08-18.** The claim this bullet carried until then — that the `dp` fixture family "is wired into **no `make` target**, so it is not in `pipeline-test`" — was **FALSE from 2026-08-17**, when `xproj-depth` (the `dp` family), `xproj-inherit` (`inhVar`) and `xproj-container-layout` (`cpLayout`/`cpLayoutBad`) all entered `pipeline-test` (`Makefile:463`). Only the unit half was true, and it is now closed: `unittest/test_container_param_inheritance.py` covers the D7.1 rejection and one forwarding acceptance. **VERIFIED BY EXECUTION** (§6, step 7a).
- **The registrar's empty-variant registration is FIXED on both paths, 2026-08-19.** `getRegistrarConfigView` decides it from whether a reachable keyed instance asks for it rather than from the absence of variant labels. **Its guard, `unittest/test_registrar_default_variant.py`, was RETIRED on 2026-08-20** because step 8 rejects the fixture's variant-less instance of a params-declaring block. The suite does not fail and is not awaiting a ruling; it no longer exists. The four follow-ups it exposed are resolved by the step 8 selector rules and the completed registrar-pair work (§6).
- **The synthesised register handler inherits its container's Config, 2026-08-20.** `postParseRegisterPorts.py` was the generator's own producer of the variant-less-instance-of-a-params-declaring-block shape, on every project with registers, so the handler's parameter values froze at the declaring constants while its SystemVerilog twin forwarded the container's symbols. The architect ruled that the handler takes the Config of the block whose registers it holds; the instance now sets `inheritContainerParam`. The delta is two model files, one module map, and two trampolines that go away; no SystemVerilog changed. Guarded by `unittest/test_regs_handler_container_config.py`. The rejection of the shape itself is now approved and LANDED as step 8, so the handler fix was also its precondition: it was the only in-tree producer of the shape.
- **The instance Config-selector rules are LANDED, 2026-08-20.** An instance of a params-declaring block that names neither `variant:` nor `inheritContainerParam:` is rejected at db, and so is a top instance whose block declares `params:`. One `post(...)` row hook on `instances`. The census found exactly one authored site, `examples/xif/arch/yaml/xif.yaml:127`, which drew the top rule; `examples/xif` is restructured so its parameterized testbench harness sits under an unparameterized root, and its emitted output is **byte-identical** across that restructure. The ruling is §2, D9; the implementation record and the gates are §6, step 8. Rule A retired the subject of `unittest/test_registrar_default_variant.py`, whose fixture authored the rejected shape by design; the suite and its fixture were deleted on 2026-08-20 and the unit gate returned to green (§6, step 8, "Collateral fixture updates").
- **The verilated SystemC wrapper of a block reached only by `inheritContainerParam` is FIXED, 2026-08-20.** It took its shape from the INSTANTIATED variant view, which such a block never populates, so it was emitted as a concrete class pinned to the block's default Config with the `<Config>` argument deleted from its BFM and hdl_if types. Both arms now key on one view fact, `svWrapper['scWrapperConfigTemplated']`, that the wrapper template and its trampoline share. The Config the trampoline binds is unchanged; **which Config a container-typed site should get was referred to the architect and is ANSWERED in step 10, 2026-08-20** — the container forwards its own variant label and the trampoline registers one entry per container variant. Emitted-output delta: **zero across `examples/` and `common/`**, four files in the product tree. Guarded by `unittest/test_inherit_vl_child.py`, which verilates and runs the shape; its emitted checks are what discriminate the fix, and its run is what proves the path works at all. **One arm of this step was reverted the same day**: the concrete path's `<Config>` deletion is the deliberate fix of 2026-08-03, not the defect it was briefed as, and substituting the default Config name is `error: expected '>'` against a non-dependent Base's member alias. No build caught the substitution because arm 1 left the concrete-parameterizable branch unreachable (step 10's record carries the detail).
- **Step 11 and the registrar follow-up are complete in the working tree, 2026-08-31.** A testbench requires a variant declared by its DUT block. The Config-source validators, declarative `dutVariant` fileMap selection, fresh-project fileMap cleanup, mixed ordinary/inherited sites, stable physical registrar artifacts, and pair-qualified logical registration identities are implemented and verified. Local `containerParam` forwarding and cross-project Verilated `containerParam` selection both pass. Base acceptance is 114/114 unit suites and 31 successful simulations with 62 `No error` reports. Pro acceptance includes the focused tandem helper regression and 7 simulations with 14 `No error` reports. The product clean, generation, and `VL_DUT=1` build gates pass. ~~**Steps 2, 5, and the RTL-bearing half of step 6 remain open; steps 3 and 4 are closed (§6, steps 3 and 4).**~~ **All of steps 2 through 6 are closed as of 2026-09-07 (§6). Earlier unrelated loose ends keep their status. The implementation is not yet fully staged, committed, or pushed.** (This sentence listed step 3 as open until 2026-09-07, two days after it landed.)
- **The normative authoring surface and the rules are [`design-parameter-inheritance.md`](./design-parameter-inheritance.md).** That document owns the authored YAML, the emitted shapes and the rules addressed to an author; this document owns the decision history, the work breakdown and every implementation fact. Neither restates the other.
- **The fixture family that pins the behaviour** is `examples/xprojParam/cstIp`, `cstBind` and `cstUse`; all three now build and run.
- **Prerequisite context, cited rather than restated.** The boundary safety this feature relies on is [`plan-interface-compatibility.md`](./plan-interface-compatibility.md), specifically its §5.5/§5.5a root-cause record, §5.9, and Plan of record steps 7 and 8. The composition boundary and the G-item register are [`plan-ip-project-composition.md`](./plan-ip-project-composition.md), specifically G5.4, G5.5 and G5.9. The one-Config-per-variant and thunker-at-the-boundary rules are [`plan-variant-config-unification.md`](./plan-variant-config-unification.md), decisions D4, D5 and Q10/R2. This document does not repeat any of them.
- **Evidence discipline.** Every behavioural claim below carries a `file:line`, a database query, or an explicit statement that it was not verified. Claims are tagged **VERIFIED BY EXECUTION** (a command was run, read-only), **VERIFIED BY CODE READING** (the code path was read, not run) or **NOT VERIFIED**.

## 1. The Problem, In The User's Terms

A parameterizable IP and the blocks that surround it — a testbench stimulus and checker, a downstream composed block — must agree on the same parameterization. Today an author has three ways to make them agree and no single correct one:

- restate the parameter declaration in every file that needs it, which duplicates the knob;
- restate the value as a literal at every variant binding, which duplicates the number;
- reach the IP's declaration through `include:` scope, which is what the authors reach for first and which **did not work at any value other than the IP's own default** (§5, B1) until step 1 landed the resolved `paramSource` link.

The requirement is that **no fact is stated twice**. A parameter is declared once. A use-case value is written once. Everything else is a reference to one of those two.

## 2. Decisions Of Record

The rules these decisions produced are stated, without evidence, in the rules section of [`design-parameter-inheritance.md`](./design-parameter-inheritance.md). That section is normative and is being iterated; this section is the history of how each rule was reached.

### D1 — Three facts are distinct and must not be conflated

- **Declaration** of a parameter — its name, default, `maxValue` and description — belongs to the IP root file, stated once, in `ipParameters:`.
- **Naming** — which parameters a block uses — is written as `params:` in the block's own file. Naming is not defining.
- **Binding** — where an instance's values come from — is written as `variant:` on the instance, resolved through the `parameters:` section that declares that variant.

Reasoning: these three are separately owned. The declaration is owned by whoever owns the IP. The naming is owned by whoever writes the block. The binding is owned by whoever assembles the use case, who is frequently none of the above (D4). Collapsing any two of them forces one owner to know something that belongs to another. The fixture states this in its own words at `examples/xprojParam/cstIp/yaml/xpCstIp.yaml:6-10`.

### D2 — The orphan rule stands unchanged

An `ipParameters` constant must be consumed by a block param **in the file that declares it**. Nothing may be published purely for downstream consumption.

- Mechanism: `_validateIpParametersLinkage`, `pysrc/processYaml.py:8229-8247`. The consumer set is built from `self.data['blocksparams'].get(yamlFile, {})` at `:8243`, which is restricted to block rows declared in that same file. **VERIFIED BY CODE READING.**
- Reasoning: every parameter then has a real owner, and an IP cannot become a bag of knobs that nothing in the IP itself uses. The cost is that an IP wishing to expose a knob must use it.
- **Consequence for §5, B1, worth stating because it is not obvious.** The check compares `const['constantKey']` against the set of `paramKey` values. Today those coincide only for a same-file param. Repointing `paramKey` (or moving the check onto a resolved link key) does **not** weaken the rule, because the consumer set is already restricted to the declaring file's own block rows. **VERIFIED BY CODE READING** at `:8243`.

**Case 1 — a shared declaration consumed only by blocks in other files. Reviewed 2026-08-13: SUPPORTED WITH PRECONDITIONS. RECOMMENDED, NOT DECIDED.**

The shape is an `ipParameters:` constant declared in a shared file and named by no block in that file, only by blocks in files that include it.

- **The gate that actually blocks it is D2's orphan rule, not the shared-include rejection.** Relaxing the shared-include rejection alone accomplishes nothing: the orphan rule fires first and rejects the declaration outright.
- **Recommendation: re-scope the orphan rule from same-file to include-reachable** — a declared parameter must be consumed by some block that can reach the declaration through `include:` scope, rather than by a block in the declaring file. Error when the declaring file itself carries `blocks:`, warning when it does not. This preserves D2's purpose (nothing is published purely for downstream consumption) while allowing a definitions-only shared file.
- **Case 1 in C++ is NOT free, and that is the crux — MEASURED.** See §5, B5: a block reaching two contexts is accepted silently at `make db` and then misbehaves three ways in the emitted C++. **B5 (step 3) is therefore a hard precondition for Case 1**, not an adjacent improvement.
- A second prerequisite is the include-chain ambiguity recorded at §7: Case 1's own migration path passes through the state in which both a shared and a local declaration of one name exist.

### D3 — Values reach a variant through a named constant, uniformly

- **Default case.** Bind the `ipParameters` constant itself: the symbolic `PARAM: PARAM` form. The default value is then stated exactly once, in the constant's `value:`. Live at `examples/xprojParam/cstIp/yaml/xpCstIp.yaml:57-60`.
- **Non-default case.** The assembler declares its **own plain `constants:` entry** carrying the use-case value, and declares the variants for **both** the DUT and its supporting blocks in that same file, every binding referencing that one constant. The value is stated exactly once. Live at `examples/xprojParam/cstBind/yaml/xpCstBindTop.yaml` (`CS_USE_WIDTH: {value: 20}` and three bindings naming it).
- A plain, non-parameterizable `constants:` entry **is** an accepted variant binding value. The schema types the field `value: const` (`config/schema.yaml:326`), which resolves any constant or enum visible in the binding row's own include scope. **VERIFIED BY EXECUTION** — `examples/xprojParam/cstBind` builds and runs on exactly this shape.
- The assembler's use-case constant **cannot** be an `ipParameters` constant: it is used as a value and is named by no block's `params:`, so it would fail D2's orphan rule.

**Resolved emission, retained reference.** A binding that names a constant yields that constant's value **resolved to a literal in the emitted Config**, not a symbolic name. `/work/ws/debayer/model/debayerVariantConfig.h:37` carries `static constexpr uint32_t BITS_PER_PIXEL_COLOR = 8;` for the symbolic binding at `yaml/debayer.yaml:287`. **VERIFIED BY EXECUTION.**

The reference itself is **not** lost. `parametersvariantsparams` persists both the symbol and its resolved key, and a literal binding is distinguishable from a reference by the key being empty. Measured on `/work/ws/debayer/debayer.db`, **VERIFIED BY EXECUTION**:

```
param                 value                 valueKey
BITS_PER_PIXEL_COLOR  BITS_PER_PIXEL_COLOR  BITS_PER_PIXEL_COLOR/../../yaml/debayer.yaml
PIXELS_PER_CLOCK      4                     (empty)
```

Two consequences:

- **The tracking is live.** The header is regenerated from the database, so changing the constant's default moves every symbolic binding on the next build. Resolved emission is a property of the artefact, not a loss of the relationship.
- **This is the precedent for §4.** The value side already does what the explicit parameter link proposes for the declaration side: keep the authored symbol, persist the resolved key as a validated FK (`value: const`, `config/schema.yaml:326`). The declaration side instead composes a key from the block's file and discards the resolution (§5, B1). **The explicit link is that existing pattern applied to `params:`, not a new mechanism** — which is also why the recommended authoring shape at Q2 makes the two read alike.

**Decision: emission stays resolved.** The Config member is the definition site in C++; emitting a symbol would make a per-variant header depend on the constants package for no gain, since the relationship is preserved in the authored YAML and in `valueKey`. Recorded explicitly because it is otherwise implicit.

**An inconsistency to hold in view.** A plain constant reference is emitted resolved (here); an eval-derived one is emitted symbolically and drops its per-variant override (§5, B4). The two behave in opposite directions, and only the second is a defect.

**A `useDefault: true` flag was considered and is REJECTED.** Reasoning, recorded so it is not reproposed:

- It reads as "match the DUT" but can only ever deliver the *declaration default*, which is a different fact. A DUT bound to a use-case value would not be matched by a supporting block carrying `useDefault: true`.
- It reintroduces default-fill, which was removed deliberately. Every declared variant must bind every parameter its block declares, with no fill for an omission (`_post_validateVariantParameterCompleteness`, `pysrc/processYaml.py:8271` onward). A flag that supplies a value for an unbound parameter is that mechanism returning under another name.
- The symbolic `PARAM: PARAM` form already expresses the default case with no new schema surface, and expresses it as a reference rather than as a mode.

### D4 — The assembler owns per-use-case variants, including variants of blocks it does not own

This already works and is deliberately proven. `examples/ip_test/top/yaml/ip_top.yaml:126-135` declares `variant1` of the **foreign** `ip` block at the assembler, with the in-file comment recording that it is a prototype of exactly this. **VERIFIED BY CODE READING** of the fixture; the descriptor machinery that supports it is `calcVariantConfigDescriptors`' declaring-project grouping at `pysrc/processYaml.py:4074-4080`, and the foreign-variant Config naming it produces.

Reasoning: the use case is the assembler's fact. Requiring the IP to enumerate its consumers' variants would invert the dependency and would make an IP unusable by a second consumer without editing the IP.

### D5 — Supporting blocks get their own Config, hence their own C++ type, hence a thunker

A supporting block that declares its own `params:` gets its own Config struct, therefore its own C++ payload type, therefore a generated thunker at every boundary to the DUT — **even when the field definitions are identical**.

- Observed, four boundaries and four thunkers, at `examples/xprojParam/README.md`, "Thunkers and the layout gate", quoting `cstBind/model/xpCstBindWrap.cppm`. **VERIFIED BY EXECUTION** (the fixture builds and runs; `make xproj-const` is in `pipeline-test`, `Makefile:370`).
- This is expected and unavoidable, not a defect. It follows from [`plan-variant-config-unification.md`](./plan-variant-config-unification.md) D4/D5: one Config per variant, containers non-templated, cross-Config binds through a thunker.
- **The interface-compatibility work is what makes it safe.** The boundary is a *checked* bit-layout match rather than an assumed one: `checkInterfacePair` builds a separate `ValueResolver` per side and compares packed-field triples before either side is emitted ([`plan-interface-compatibility.md`](./plan-interface-compatibility.md), Plan of record steps 1, 3, 6 and 7). The gate is live on this family — rebinding one end of a cell while the other stays put is rejected at `make db`, with the verbatim diagnostic recorded in `examples/xprojParam/README.md`.
- **The explicit link of §4 does not change this.** A block that *names* the IP's constant still gets its own per-variant Config struct — observed as `xpCstBind_xpCstSrcIncDfltConfig` beside `xpCstDutDfltConfig` in the thunker list above. Sharing a declaration does not collapse two Configs into one C++ type.

### D7 — Parameter-scoped inheritance, expressed in the variant. DECIDED (architect, 2026-08-13)

(D6 is at §3; this decision answers the customer/depth case measured at §5, B6.)

The rulings, in the order they were made:

- **Not a blanket instance option.** Inheritance is limited to the parameters the **container itself declares**. A container does not become a conduit for everything below it.
- **Expressed through the VARIANT mechanism, not through an instance option.** The place a parameter's value is stated is the variant, so the place inheritance is stated is the variant.
- **The overload is UNSAFE, and a distinct expression is REQUIRED, not deferred.** A variant is a **declaration**, and its meaning must not depend on the site at which it is instantiated. The decisive case: one variant instantiated under two containers, one of which declares the parameter and one of which does not. Under an overloaded spelling that variant would mean two different things.
- **The inherit indication REPLACES the binding; it never accompanies one.** Completeness (`_post_validateVariantParameterCompleteness`) generalises from "every parameter is bound" to "every parameter is bound **or** container-sourced".
- **The spelling.** Within a declared variant, each parameter is either a value or `containerParam: xxx` naming the **container's** parameter. **The names need not match.** ~~A second form inherits the **entire** variant from the parent.~~ **The whole-variant form is NOT BUILT and is NOT SPECIFIED, 2026-08-14.** It is in neither `config/schema.yaml` nor the fixture, and [`design-parameter-inheritance.md`](./design-parameter-inheritance.md) deliberately specifies the per-parameter form only. It is not scheduled; if it is ever wanted it must be re-decided and specified first.
- **Incompatibility must be a DB-TIME diagnostic naming both sides.** Relying on the thunker or the layout gate to catch a mismatch is explicitly **REJECTED** — §5, B6 measures why the layout path is not a reliable net.

**`inheritContainerParam` is subsumed** as the degenerate case of the **per-parameter** form — every parameter container-sourced, same name, same project. (Corrected 2026-08-14: it was recorded here as the degenerate case of the whole-variant form, which does not exist. The relationship is stated in full at step 7's implementation record below.)

Consequences recorded with the decision:

- **Case 1 is NOT a prerequisite.** Cross-project identity already works through include scope (§3), so D7 does not wait on the orphan-rule re-scoping.
- Migrating the product tree onto the new rule would **restore layout adjudication on two connections that are excluded today** (§5, B6).

### D7.1 — Identity versus compatibility. RESOLVED 2026-08-14: COMPATIBILITY, not identity

Recorded here as OPEN until 2026-08-14: whether the child's parameter and the named container parameter must **share a backing constant**, or need only be **compatible**. **The implementation and the fixture decided it.**

- **Identity is NOT required.** Requiring it would forbid a container from declaring its own knob at all, which is the shape the motivating case is built on: `xpDpMid.MID_ALGO` and `xpDpLeaf.DP_ALGO` are different constants in different projects.
- **Compatibility IS required, and the relation is `maxValue`:** the container parameter's `maxValue` MUST NOT exceed the child's. `maxValue` is the child's **acceptance contract** — worst-case sizing is taken from it — so a container whose domain is wider can be bound to a value the child cannot accept.
- **The three reuse cases, MEASURED 2026-08-14** per site on `examples/xprojParam/dpTop`. At that
  time `uLeafX` still reused `xpDpMid.yaml`'s `customer` variant under a second container
  (`xpDpWrap`). Step 12a's `uLeafX` decision moved that instance onto its own declared variant
  (`leafX`), so this specific dpTop evidence no longer exists in the tree. The three dispositions
  below remain true generally, and are also evidenced by `cstBind`'s analogous table:

| Case | Disposition |
| :-- | :-- |
| same backing constant on both containers | accepted, no diagnostic |
| different constants, identical `maxValue` | accepted, no diagnostic |
| different constants, container's `maxValue` wider | **rejected**, per site, naming that site and both constants |

The rule as an author sees it, and the message the rejection produces, are in [`design-parameter-inheritance.md`](./design-parameter-inheritance.md).

**Extending the compatibility relation to `valueType` was raised and is DECLINED (architect, 2026-08-14).** The relation stays `maxValue` alone. The finding is kept, not deleted, so it is not re-raised as new:

- **The finding.** `maxValue` bounds the magnitude a container may bind but says nothing about the value's TYPE. A signed container value flowing into a child Config member whose type comes from the CHILD's own declaration is therefore accepted by the site-time validator, and the member is emitted at the child's declared type.
- **The ruling.** The failure mode is narrow — it needs a signed container parameter bound into an unsigned child member — and was judged not important enough to widen the relation for. No gate, no diagnostic and no schema field is added.
- **Recorded in the authoring surface, 2026-08-18.** An accepted gap an author cannot discover is indistinguishable from a bug, and [`design-parameter-inheritance.md`](./design-parameter-inheritance.md) named `valueType` nowhere. Its §4 now carries a "What is not checked" subsection stating that `valueType` is not compared and that agreement is the author's responsibility.

### D7.2 — `containerBlock` is REMOVED. DECIDED (architect, 2026-08-14)

**The container is resolved from the INSTANCE declaration; the variant does not name the container block.** The optional `containerBlock:` field, and with it the three diagnostics reachable only through it, are removed from the schema and the generator. The single-field `containerParam:` form is the only form. **The removal was in flight in `config/schema.yaml` and `pysrc/processYaml.py` when this was recorded; the target state is described, not the tree.**

Why the pinned form bought nothing:

- **The foreign-key route was unavailable.** The linkage cannot be a parse-time foreign key at all: a container block's `params:` are not reliably parsed before a child variant's binding rows, so the check is post-parse either way (R12 of the design doc). Pinning the block would not have made it declarative.
- **Nothing useful could be persisted on the declaration row**, because emission is **per site** regardless — one variant may be instantiated under several containers, and the resolved value differs per site.
- **The only harmful reuse case is already caught per site.** D7.1's third row — a container whose domain is wider than the child accepts — is rejected at the site, naming both constants. Pinning the container therefore bought a **restriction** rather than a safety property.
- **The measured cost was variant proliferation.** Variants emit Config structs one-to-one, with no dedup, so pinning would have forced N containers to mean N variant declarations — N Config structs and N thunker sets — for one configuration.

`inheritContainerParam`'s own precondition set is the precedent for resolving the container from the instance row: it already takes the container from `container:` and rejects an instance not contained in a block.

The work, its measurements, and the split between what is built and what is not, are at "Plan of record" step 7. The authoring surface and the rules are [`design-parameter-inheritance.md`](./design-parameter-inheritance.md).

### D8 — A block variant declared by two files of one project is an error. DECIDED (user, 2026-08-17)

A variant's Config identity is `(block, variant, declaring project)` — what the emitted per-variant Config struct, the descriptor grouping and the `instanceFactory` key all resolve to. The declaring **file** is not part of it, so two files of one project declaring the same variant yielded one Config, the later declaration silently replacing the earlier's bindings. Rejected at db by `validateVariantDeclarationUniqueness`, naming the block, the variant and **both** declaring files. Gated by `xproj-variant-unique`.

**Cross-project reuse of the same `(block, variant)` stays legal on the Config-struct path** and is untouched there: `calcVariantConfigDescriptors` (`pysrc/processYaml.py:4057-4086`) groups descriptors by declaring project, so those are distinct Config identities emitting distinct structs. `ip-test` composes `ip/variant1` under two projects and must keep passing. (**CORRECTED 2026-09-04:** the sentence carried no path qualifier, so it read as a guarantee that nothing can confuse two projects' bindings of one `(block, variant)`. The three SystemVerilog and RTL emission paths carry no project axis and do confuse them. Measured on a fixture authored strictly to these rules, one clean build emitted a Config of 3 beside a Verilated top and an RTL instantiation of 7. The identity stated here is right and the emitters are wrong, so the fix belongs in them, not in a new restriction on this sentence. See item 9A of [`plan-116-review-feedback.md`](./plan-116-review-feedback.md).)

**The schema route was examined and is closed**, so this validator is not double-implementation:

- The schema system has **no** uniqueness mechanism — no `unique` attribute, and no `UNIQUE`/`PRIMARY KEY` on any generated DDL. `_key`/`_combo` build composite key *values* and assert nothing.
- Making the section `flat` does **not** reach it: `addFlatRecord` dedups on the **context-qualified** key, and the declaring context is exactly what differs between the two duplicate declarations. Non-`flat` is deliberate here — `SCHEMA_SPECIFICATION.md` names `parametersvariantsparams` as its worked example, under Governing Invariant 1 (scope-based resolution: mutually invisible files may legitimately hold same-named rows).
- A SQL `UNIQUE` on the intermediate `parametersvariants` table would reject **legitimate** cross-project reuse: that table keys on block + variant with **no** `projectName`.

Implemented as a post-parse pass, not a `variants` row hook: a row hook sees only declarations parsed before it, so the same duplicate pair would be caught or missed by file load order — which is precisely what differs between a standalone and a composed build.

### D9. An instance of a params-declaring block must select a Config, and a top may not be parameterized. DECIDED (architect, 2026-08-20)

A block that declares `params:` is typed per instance, and the architect settled the closed list of authoring shapes that name that type:

1. `variant: X`, where `X` binds values or constants.
2. `variant: X`, where `X`'s rows carry `containerParam: yyy`, sourcing from the container per parameter. Names may differ, cross-project is allowed, and the `maxValue` domain relation is enforced (D7).
3. `inheritContainerParam: true` with no variant. All-or-nothing, bare-name subset, same owning project only (D7.2).

A fourth shape, an instance naming neither, was accepted and is now **rejected at db (rule A)**. It leaves the block parameterized and the instance untyped, and every downstream consumer then guesses: the C++ side falls back to the context default Config while `_resolveSvInstanceParams` forwards the container's symbol wherever the names happen to match. That divergence is what the register handler had (§6, step 7, "The synthesised register handler now inherits its container's Config"), and the handler was the generator's own producer of the shape.

**A top instance whose block declares `params:` is rejected too (rule B).** A top has no container, so shapes 2 and 3 are unreachable, and a project declares one top, so shape 1 could only ever be a single set of literals. That is a constant with extra machinery. The architect's ruling is explicit that a testbench top should not be parameterized and that no use case for a parameterized top exists.

Both rules are one hook, so rule B subsumes rule A at the top. Both are kept, because they reject different mistakes and rule A must still fire for a contained instance.

**Census taken before implementing, over every non-hidden `.db` under `examples/`, `builder/pro/examples/` and the product tree database (`/work/ws/debayer/debayer.db`).** 104 instances of params-declaring blocks: 91 name a variant, 12 inherit (7 distinct sites, three of them the synthesised register handlers that started inheriting the same day), and **exactly one** was shape 4, `examples/xif/arch/yaml/xif.yaml:127`, whose container resolves to `_topInstance`. The same census found no composed-child root declaration (the self-edge row a child project keeps when a parent composes it) on a params-declaring block, so rule B keyed on `_topInstance` leaves no reachable gap today. **VERIFIED BY EXECUTION.**

## 3. D6 — The Question As It Stood

D6 was recorded as the central open question:

- **Option A, reuse by include scope.** A file that `include:`s the IP root may name the IP's constants in its own blocks' `params:`. One declaration, reached from several files.
- **Option B, share the value only.** Each block declares its own knob; only the *value* is shared, through a named constant. The declaration is duplicated; the number is not.

Where this stood before 2026-08-13:

- The user favoured Option A.
- The fixture proved Option A does not work today at any value other than the IP's declared default (§5, B1). `examples/xprojParam/cstBind` therefore ships Option B as cell B — the smallest correct alternative — with Option A present as cell A, which is correct precisely because cell A binds the default.
- Option A **cannot simply be forbidden**: `examples/xprojParam/filterShared/yaml/xpFilterShared.yaml:6-12` and `examples/xprojParam/sinkShared` depend on it, and so does the product tree. **VERIFIED BY EXECUTION** (read-only query, §5 B1 blast-radius table): eight blocks in both trees are on the include-reached path, two of them `raw_video_src` and `rgb_video_sink` in `/work/ws/debayer`.
- [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) step 8e records the same conflict from the enforcement side: a db-time rule requiring every block param to resolve in the block's own context would reject exactly those four blocks and would additionally reject `filterShared`/`sinkShared`, "so the rule as stated and the shared-parameter composition pattern are in direct conflict and the architect has to decide which survives."

§4 is the third answer, and it is the reason this section is titled "as it stood".

### D6 — RESOLVED, 2026-08-13; confirmed by execution when step 1 landed

**Both options are legal authoring choices, and no rule is needed to pick between them.** D6 existed only because Option A was *broken*: a block naming an include-reached constant produced a `paramKey` that resolved to nothing, so the layout gate compared against a stale value, the sizing check silently skipped, and the shape worked only at the IP's declared default (§5, B1). That is a defect, not a design boundary.

Once `paramSourceKey` resolves correctly (§4.0), Option A works at any value. **Confirmed:** `examples/xprojParam/cstUse` — which *is* Option A at a non-default value, and was asserted to fail — now builds and runs at the bound value, and is promoted into `xproj-const`. Option B continues to work unchanged and remains the right choice where a block genuinely owns its own knob. `filterShared` and `sinkShared` need no change under either reading.

Recorded so it is not reopened: the resolution is **not** the renaming of §4.3, which is not part of this design (§4.0). It is simply that fixing the key removes the reason one of the two options was unusable.

### Cross-project reuse of `ipParameters` — reviewed 2026-08-13; no gate recommended

The question re-put after step 1 landed: should a block in project X be permitted to name an `ipParameters` constant declared by project Y, reached through `include:` scope?

**An independent review recommends ALLOWING it, and recommends against any project-boundary gate.** The grounds, in order:

- **It is already the shipped status quo.** `examples/xprojParam/filterShared` and `sinkShared` do exactly this, and so does the `shared` assembler that composes them, which is in `pipeline-test`. `examples/xprojParam/cstUse` does it too, and step 1's acceptance rests on that path.
- **A hard gate would be self-contradictory.** A verbatim-asserted diagnostic requires a block sitting on a foreign parameterized interface to name that interface's backing parameter. A ban on naming a foreign project's parameter and that requirement cannot both be satisfied.
- **`inheritContainerParam`'s same-project rule is not a counter-precedent.** It was judged scaffolding around a bare-name comparison (`pysrc/processYaml.py:4942-4943`, and the container/child owning-project check at `:5063`) rather than a policy about parameter ownership. It is filed as a gap, not as a ruling that cross-project naming is disallowed.

**NOT DECIDED by the architect:** whether to document a **CONVENTION** — prefer sharing *values* across a project boundary, and declarations only within one — as distinct from a gate. A convention constrains authoring guidance only and would not be enforced. **OPEN.**

### Case 2 — a higher-level assembler exposing a sub-block's parameter

- **The one-level form is already emitted today.** `DEBAYER_ALGORITHM` is exposed upward in the product tree by commit `201a17f` together with `inheritContainerParam`.
- **The architect clarified the real use case, 2026-08-13:** a **customer** instantiating the IP in a particular configuration, which is not the one-level form — the customer is two or more project levels above the block being configured.
- **That case is NOT supported. MEASURED — see §5, B6.** The customer's declaration is accepted at every gate and then silently orphaned. D7 (§2) is the decided answer.

## 4. The Explicit Parameter Link (architect direction, 2026-08-13)

**The direction.** Expand the parameter definition so that a block's `params:` entry carries an explicit link from the param to its parameter source, rather than the source being recovered by same-name scope lookup and then discarded.

**What is true today.** `blocks.params` is a bare name list:

```yaml
  params:
    _attribs: [optional, list, flat, post(validateBlockParamBacking)]
    param: key
```

(`config/schema.yaml:260-262`.) The backing constant is found by `lookupInScope` inside `_post_validateBlockParamBacking` (`pysrc/processYaml.py:8210-8226`) and the resolution is **thrown away**. The automatic key machinery then builds `paramKey` by qualifying the param name with the file that declares the **block** (`pysrc/processYaml.py:6830-6833`; the mechanism is documented at `config/SCHEMA_SPECIFICATION.md`, "Key-Related Types", `key`). That is the root cause of every symptom in §5, B1.

**Measured, read-only against `examples/xprojParam/cstBind/xpCstBind.db`. VERIFIED BY EXECUTION:**

```
block        param           paramKey
xpCstDut     CS_PIXEL_WIDTH  CS_PIXEL_WIDTH/../../../cstIp/yaml/xpCstIp.yaml
xpCstSrcInc  CS_PIXEL_WIDTH  CS_PIXEL_WIDTH/../../yaml/xpCstSup.yaml       <-- no such constant
```

### 4.0 The row shape — DECIDED (architect, 2026-08-13)

`blocksparams` carries **four** authored/derived pairs plus the existing block reference:

| field | origin | meaning |
| :-- | :-- | :-- |
| `param` | **user input** | the name the author wrote in `params:`. Retained. |
| `paramKey` | key machinery | that name qualified by the **block's declaring file**. Retained. A block-scoped identity, **not** a constant key. |
| `blockparam` / `blockparamKey` | existing combo | the block+param identity the variant side's FK already targets. Unchanged. |
| `paramSource` / `paramSourceKey` | **new, derived** | the resolved link to the backing constant. |

**The FK target is `constants`, not `ipParameters`. VERIFIED BY EXECUTION** — `ipParameters` does not appear in `config/schema.yaml` at all. It is not a section: `_process_ipParameters` (`pysrc/processYaml.py:8145`) routes its sub-sections through the normal `constants` and `types` pipelines with `_ipParametersActive` set, which stamps `isParameterizable` on each entry as it is processed. There is no table to key onto. "Must reference an ipParameter" is therefore expressed as two things:

- an FK onto `constants`, resolved through the referring row's include scope — declaratively expressible (§4.1);
- a check that the resolved row carries `isParameterizable` — not expressible as an FK, and retained as the row hook that exists today (`_post_validateBlockParamBacking`).

**"Explicit" means explicit in the ROW, not in the YAML. DECIDED (architect, 2026-08-13).** `params:` remains a **bare list**. The user writes no link and never sees one; the validator fills in the derived key. `param` remains the user's input, and `paramSource` records the resolution the parser already performs. Consequences:

- **No YAML change and no migration, now or as part of this design.** All 45 occurrences (§4.4) stay exactly as written. §4.4 is retained as a measurement of the authored variant's cost should it ever be proposed; it is **not** a cost of this plan.
- **The same-name rule stands.** A block cannot rename its knob, and **renaming (Q3) is not part of this design.** §4.3 is retained as analysis of what renaming would require, not as work.
- **All four bad consumers (§5, B1) move onto `paramSourceKey`.** `paramKey` stops being read as a constant key by anything. The orphan check `_validateIpParametersLinkage` (`:8243`) must move too, even though it is correct today, because its correctness rests on the two keys coinciding within one file.

This supersedes shape (iii) at §4.2, which put the validator on the existing `param` field: that would overwrite `paramKey` with the **constant's** context and destroy the block-scoped identity the table is required to keep. Recorded as **REJECTED**.

**The lookup is the foreign-key validator, not an `auto(...)` handler. DECIDED.** `paramSource` is FK-typed against `constants`; the validator performs the scoped resolution and writes `paramSourceKey`. Today the field takes the param's own name, because the same-name rule holds. When the name becomes authored and may differ (Q3), **the same validator handles it unchanged** — which is the reason to use the FK rather than a derived handler: one construct serves the derived case now and the authored case later, with no second code path and no second resolution site. `_post_validateBlockParamBacking` correspondingly loses its hand-rolled `lookupInScope` (`pysrc/processYaml.py:8220`) and retains only the `isParameterizable` check on the resolved row.

The FK mechanism is **observed working in this table family**, not merely read: the variant side's `value: const` produces a resolved `valueKey` onto `constants` on live rows (§2, D3). **VERIFIED BY EXECUTION.**

**One detail to answer from the schema, not to invent:** how `paramSource` takes the param's name when the author has not written one. **ANSWERED, and landed: `auto(paramSource)` plus the FK `_validate`.** The field is `_type: auto(paramSource)` with `_validate: {section: constants, field: constant}`; `_auto_paramSource` returns `processed['param']` and the foreign key resolves it and writes `paramSourceKey`. Reasoning and the rejected alternatives are at "Plan of record" step 1.

### 4.1 Q1 — What does the link name? RESOLVED by §4.0

**Recommendation: a foreign key onto `constants`, resolved by the referring row's own include scope. Naming a file is rejected.**

- Naming the constant is what the schema framework already expresses. Naming the declaring file is strictly weaker: the constant must still be resolved from the name, so the file buys nothing and adds a second thing that can be wrong.
- **The stated limitation does not hold, and the comment asserting it is stale.** `_post_validateBlockParamBacking` states at `pysrc/processYaml.py:8212-8214` that "A declarative `_validate` cannot express this because constants is context-scoped (the FK framework only targets flat sections)". **`constants` IS flat** — `config/schema.yaml:69-70`, `_attribs: [flat]`, `constant: key`. **VERIFIED BY CODE READING.** That comment should be corrected as part of the work.
- The Foreign-Key Invariants (`config/SCHEMA_SPECIFICATION.md`, under `_validate`; enforced by `pysrc/schema.py:_validate_foreign_key_lookups`, the flat check at `:720-727` and the storage-key check at `:728`) require, for a plain FK, that the target section be flat and that `field:` name its storage key. `constants` satisfies both with `field: constant`. **VERIFIED BY CODE READING.**
- Resolution is exactly the scoped walk the Governing Invariants require: the plain-FK arm of `validateForeignKey` delegates to `lookupInScope(targetSection, context, value)` (`pysrc/processYaml.py:8380-8381`), which walks the referring row's include chain with the `_a2csystem` fallback (`:8347-8353`). No `scope: global` is involved and none is needed.
- **The resolved key is persisted for free.** When a validator resolves, `processSimple` writes `ret[field+'Key'] = varInfo[validator['field']] + '/' + varContext` (`pysrc/processYaml.py:6994`), and the key machinery pre-populates `{field}Key` only when it is absent (`:6832`, `if qualified_field in schema and qualified_field not in ret`). So the FK's resolved qualification wins. **VERIFIED BY CODE READING.** No new persistence code and no new derived-fact pass are required; the fact lands on the row at parse time, which is where `projectCreate` owns it (`CLAUDE.md`, "Where Changes Belong").
- **Parse-ordering exposure is unchanged.** Governing Invariant 2 states that a successful FK proves the target was already parsed but does not schedule parsing, so `ipParameters:` must be authored before `blocks:` in the same file. `_post_validateBlockParamBacking` fires at the same point in `processSimple` and already carries the identical exposure. **VERIFIED BY CODE READING**; no regression, but it must be stated in the diagnostic.
- What the `_post` hook retains: the FK cannot express "the resolved constant must be parameterizable". That check stays as a row hook on the resolved row, which is exactly the case `config/SCHEMA_SPECIFICATION.md`, "Choosing Where a Validation Belongs", describes for a `_post`.

### 4.2 Q2 — Required or optional?

Three authoring shapes are available, and the framework's tolerance differs between them. **VERIFIED BY CODE READING** at `pysrc/processYaml.py:8430-8466`, the `list` attrib handler, which already branches on `isinstance(nested[0], (dict, list))`:

- **Shape (i), list of dicts, link optional.** `params: [MY_W]` and `params: [{param: MY_W, source: CS_PIXEL_WIDTH}]` both parse **with no processing-code change** — the branch exists. Cost: two authored shapes in the tree indefinitely, and an optional field means the same-file default must be filled by a `_post` hook, which is a second code path for the thing the change exists to make single.
- **Shape (ii), mapping with `_singular`, link required.** `params: {MY_W: CS_PIXEL_WIDTH}`, schema `_attribs: [optional, multiple, ...]`, `_singular: source`, `param: anchor`, `source: {_validate: {section: constants, field: constant}}`. This is **byte-for-byte the shape `parametersvariantsparams` already uses** (`config/schema.yaml:322-326`: `_singular: value`, `param: anchor`, `value: const`), so a block's param declaration and a variant's param binding would read as the same construct. Cost: every existing `params: [...]` must be rewritten (Q4).
- **Shape (iii), no new field at all.** Put the `_validate` onto the existing `param` field. `paramKey` is then repointed in place to the resolved constant key, and every one of the four bad consumers in §5 B1 is corrected with **zero YAML change and zero consumer change**. Cost: the link is implicit and the same-name rule is hardwired, so **Q3 cannot be answered in the affirmative and D6 stays open**.

**Recommendation: shape (ii), required.** Reasoning: an optional link with a same-file default preserves the very ambiguity the change removes — a reader still cannot tell, from the block, where the knob comes from — and it keeps two resolution paths alive in code that `CLAUDE.md` ("Prefer one direct path through the code") tells us to avoid. The migration cost is measured at Q4 and is small and mechanical.

**Shape (iii) deserves to be on the table as a fallback**, because it is the whole of the §5 B1 fix at near-zero cost and can be landed first if the architect wants the defect closed before the authoring question is settled. It is forward-compatible: adding the `source` field later moves the resolved key from `paramKey` to `sourceKey` and repoints the same consumers a second time.

### 4.3 Q3 — Renaming: REJECTED (architect, 2026-08-13), on authoring clarity

**The same-name rule is kept as a positive design property, not as an absence.**

What the author is saying when a block writes `params: [BITS_PER_PIXEL_COLOR]` is *"I am using that constant as my parameter."* The constant thereby **stops being a constant** for that block: it is no longer emitted into the package, and it appears only as a Config member. **VERIFIED BY EXECUTION** — in `/work/ws/debayer/model/debayerIncludes.cppm` the symbol occurs only as `Config::BITS_PER_PIXEL_COLOR` (`:82-83`, `:116-118`), never as a plain declaration; the exclusion is already implemented, `pysrc/processYaml.py:5395` dropping a backing key from the declaration set.

Under renaming, one fact would need two symbols. The original constant would have to appear **as well** — as a module parameter, or as a `consteval`/`constexpr` equated to the block's input parameter — with a binding between them that the author must read to understand which one is live. One name for one width, disappearing into the Config at the point of use, is clearer than two names and an equation.

The remainder of this section is retained as **analysis of what renaming would have required**, so the cost is on record if it is ever reproposed. It is not work, and nothing in §6 depends on it.

#### Analysis, retained: what renaming would have required

Today a block param must be backed by a **same-name** parameterizable constant, enforced at `pysrc/processYaml.py:8220` (`lookupInScope('constants', yamlFile, param)`) with the diagnostic "every block param must be declared as a same-name ipParameters constant" (`:8223-8224`).

With an explicit link the names no longer *have* to match. **If they need not match, D6 stops being a choice.** Option A and Option B collapse into one shape: a block always declares its own param name, and always names where the value comes from. "Reuse by include scope" becomes "my knob's source is that IP's constant"; "own knob" becomes "my knob's source is my own constant". There is one rule, and `cstBind`'s Inc pair and Own pair become the same construct with different sources.

**That is the strongest argument for the link, and it is not free. Three things must be true, and only the first is true today.**

1. **The db-time resolvers must key on the resolved source, not the name.** They will, by construction, once the link is persisted (§5, B1).
2. **The Config builder must key on resolved constant identity, not on the name.** It does not today. `calcVariantConfigDescriptors` gathers Config fields by name from the config context's parameterizable constants (`pysrc/processYaml.py:4068-4070`), and matches variant overrides by param name against the constant's name (`:4086-4089`). A block param whose name differs from its source constant falls through to the synthetic-field arm at `:4071-4073` and `:4090-4092` and is emitted as an **additional** plain member, leaving the real constant at its declaration default. **VERIFIED BY CODE READING.** This is B5 (§5). **Renaming is unsafe until B5 is fixed.**
3. **The C++ Config member name must remain the constant's name; the block's param name is a local alias.** A parameterizable structure's width is emitted as `Config::<constantName>` (`templates/systemc/includes.py:96-101`, `constReference_cpp`), so the Config member the payload type reads is named by the constant and cannot be renamed per consuming block. Meanwhile the base class exposes the block's params as `static constexpr auto <param> = Config::<param>` (`templates/systemc/baseClassDecl.py:95`), which assumes the two names are identical. Under renaming that line must become `static constexpr auto <param> = Config::<sourceConstantName>`. **VERIFIED BY CODE READING.** On the SystemVerilog side the same rename is a straightforward improvement rather than a problem: `parameterizedDeclLines` maps a constant key to the block's SV parameter name (`templates/systemVerilog/package.py:46`), so the module parameter is spelled with the block's own name and the constant symbol resolves to it.

**Recommendation.** Adopt "the names may differ" as the target rule and record **D6 as RESOLVED BY THE LINK, conditional on B5**, with the sequencing that follows: land the link with the same-name rule still enforced (which fixes B1 and changes no authored YAML semantics), land B5, then lift the same-name restriction as a separate, separately-measured step. If the architect declines the rename — for instance to keep one name for one width across a whole composition, which is a legitimate readability position — then the link still fixes B1 in full and **D6 remains open**, decided instead by whichever of Option A or Option B the architect prefers. Nothing in §5 depends on the rename.

**One consequence to have in view either way.** `inheritContainerParam` compares a child's params against its container's **by bare name** (`pysrc/processYaml.py:4942-4943`). If names may differ, that comparison must move to resolved source identity, or the feature silently stops matching. **VERIFIED BY CODE READING.**

### 4.4 Q4 — Migration

**Measured, 2026-08-13. VERIFIED BY EXECUTION** (`grep` over authored YAML; `builder/pro` is not present in this tree, so `pro/examples` is not counted) — **the parenthetical is FALSE and is corrected at step 1's landed record: `builder/pro` IS present. It carries no `blocksparams` rows, so the counts below are unaffected:**

| Tree | `params: [...]` occurrences | files |
| :-- | --: | --: |
| `builder/base/examples` | 33 | 22 |
| `builder/base/unittest` | 7 | 7 |
| `/work/ws/debayer/yaml` | 5 | 2 |
| **total** | **45** | **31** |

75 authored param names in total. Cross-checked against the databases: 100 distinct `(block, param, file)` rows over 58 distinct blocks in 22 distinct YAML files, across every database in `examples/`, plus `/work/ws/debayer/debayer.db` and `/work/ws/debayer/isp_shared/isp_shared.db`. The two counts differ because several projects re-parse the same files in composed builds and because `unittest` fixtures build only inside their suites. **Databases in the tree may be stale relative to the working YAML; the `grep` figure is the authoritative migration count.**

- **The conversion is mechanical for 71 of the 75 names.** `params: [A, B]` becomes `params: {A: A, B: B}` for every param whose backing constant is same-file, which is the case for all but the 14 rows listed at §5 B1 (8 distinct blocks, of which the 4 `cstUse` and `cstBind` Inc rows are fixture rows). The include-reached ones convert identically — `params: {PIXEL_WIDTH: PIXEL_WIDTH}` — and simply become *correct* where today they are silently wrong.
- **The mechanism exists.** `make migrate` / `migrateYaml.py`, with the `yamlFormat:` sentinel gate at `pysrc/processYaml.py:5744` (`_gateYamlFormat`) against `CURRENT_YAML_FORMAT = 2` (`:27`), and the phase/report/dry-run split described in [`plan-yaml-migration.md`](./plan-yaml-migration.md). This change would be a new phase and a bump to format 3. The migration is a pure text rewrite of one section shape and never needs the database, which matches the constraint every existing phase honours.
- **Shape (i) needs no migration at all** and shape (iii) needs none either; this cost is specific to the recommended shape (ii).

### 4.5 What the link does to the existing consumers

The decisive property is that **all four bad consumers are reading a key that is genuinely resolved, so one change fixes all four at once** rather than four separate corrections. Each is listed with what it needs *beyond* the key being correct:

| Consumer | Site | Beyond the correct key |
| :-- | :-- | :-- |
| `variantValueBindings` | `pysrc/processYaml.py:6105` | Seed the resolver under the resolved source key. The extra seeds at `:6103-6104` (bare `param`, `blockParamKey`) become dead or, under Q3 renaming, a hazard; delete them rather than leave three keys for one fact. |
| `_post_validateVariantBindingSizing` | `:8259` | **The silent early return at `:8260-8261` must become loud.** With an FK the miss is impossible, so the branch is either a hard generator-bug diagnostic or it goes. Leaving a quiet `return` would preserve the failure mode after removing its cause. |
| `_resolveWordLinesConstant` | `:7215-7216` | The unguarded `self.flatData['constants'][backingKey]` becomes safe by construction, since the FK guarantees the row. Keep a diagnostic rather than an index, in the same form as the neighbouring `printError` at `:7210-7213`. **CORRECTED 2026-08-13 (independent review): this path IS verified by execution.** `memories.wordLines` is `param`-typed (`config/schema.yaml:498`), so a `wordLines` naming a block param leaves `wordLinesKey` empty and reaches the bare-name arm. `examples/ip_test/ip` (`ipMem`, `ipFixedMem`, `ipNonConstMem`) and `examples/simple_ip/ip` do exactly that, and `_auto_memIsParameterizable` calls the helper on every memory row, so every `make db` of those examples executes it. Both are in `pipeline-test`. |
| `templates/systemVerilog/package.py` | `:46` | Key `paramNameByKey` by the resolved source key. Under Q3 this is what makes a renamed knob spell correctly in SV. Three call sites, not one: `moduleInterfacesInstances.py:39`, `moduleRegs.py:141`, `module_hdl_wrapper.py:64`. |

Two further readers, both currently correct, are **simplified** rather than fixed, and should be moved onto the persisted key so that one fact has one source:

- `deriveParameterizedDeclSets` re-resolves the identical rows via `lookupInScope` at `pysrc/processYaml.py:5540-5547`; its `backingKeys` set at `:5284` reads `paramKey` raw. For a plain `ipParameters` constant the two arms of `constantRefDeps` (`:5310-5320`) reach the same answer, so this is benign today; for an eval-derived one it is entangled with B4. **VERIFIED BY CODE READING; NOT VERIFIED by execution.**
- `calcBlockConfigInfo` re-resolves the same rows again at `:4873-4879` to derive `own_params_context`, the fix [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) step 7 had to make. That becomes a read of the persisted source key's context.

And one consumer must **move** to the link or it breaks under Q3 renaming: `_validateIpParametersLinkage` (`:8243`) reads `paramKey` as the consumed-constant set. If a block renames its knob in the same file, that check would report a false orphan. It must read the resolved source key. D2's meaning is unchanged either way (§2, D2).

**Rejected alternatives, one line each:**

- *Re-resolve through `lookupInScope` at each consumption point.* Loses: it multiplies an existing re-derivation from two sites to six, states the same fact six times, and leaves the authored YAML still not saying where the parameter comes from.
- *Enforce same-file locality.* Loses: it rejects `filterShared`/`sinkShared` and the two product-tree blocks (measured at §5 B1 and independently at [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) step 8e), and it decides D6 against Option A by fiat rather than making Option A work.

## 5. Blocking Defects, In Sequence

### B1 — `blocks.params` carries an unresolved key, and four consumers read it as the backing constant key

**Root cause.** `params` is a plain `key`-typed schema field (`config/schema.yaml:260-262`), so `blocksparams.paramKey` is qualified with the file declaring the **block** and is never resolved into `constants`. It is correct only when block and constant share a file.

**Blast radius, exhaustive. VERIFIED BY EXECUTION**, read-only over every database in `examples/` plus `/work/ws/debayer/debayer.db` and `/work/ws/debayer/isp_shared/isp_shared.db`, by left-joining `blocksparams.paramKey` against `constants.constantKey`. **Fourteen rows in six databases miss; every other row in both trees hits.** **CORRECTED 2026-08-13 (independent review): 14-in-6 is the POST-change figure. Against a cold pre-change tree the baseline is 12 rows in 5 databases** — two of the fourteen are `cstUse`'s, and `cstUse` had no database before step 1 because its `make db` was asserted to fail. The table below is otherwise unchanged.

| database | block | param | bound value | constant default |
| :-- | :-- | :-- | --: | --: |
| `cstBind` | `xpCstSrcInc`, `xpCstChkInc` | `CS_PIXEL_WIDTH` | 12 (symbolic) | 12 |
| `cstUse` (probe) | `xpCstUseSrc`, `xpCstUseChk` | `CS_PIXEL_WIDTH` | 20 | 12 |
| `filterShared`, `shared` | `xpFilterShared` | `PIXEL_WIDTH` | 8 | 8 |
| `sinkShared`, `shared` | `xpSinkShared` | `PIXEL_WIDTH` | 8 | 8 |
| `debayer` | `raw_video_src` | 4 params | 8 / 4 / 3840 / 2160 | 8 / 4 / 3840 / 2160 |
| `debayer` | `rgb_video_sink` | 2 params | 8 / 4 | 8 / 4 |

**Two consequences of that table which materially de-risk the fix:**

- **Every live binding on the affected path binds its constant's declared default.** Only the `cstUse` probe, which is asserted to fail, binds anything else. So repointing the key **moves no resolved value anywhere in either tree**, and enabling the `maxValue` check rejects nothing (`PIXEL_WIDTH` max 32 against 8; `PIXELS_PER_CLOCK` max 4 against 4; `HORIZONTAL_SIZE` max 3840 against 3840). **VERIFIED BY EXECUTION.**
- **All eight affected blocks are `hasRtl: 0`.** **VERIFIED BY EXECUTION.** The SystemVerilog consequence below is therefore **latent everywhere in both trees**, which is why it has never been observed, and there is no fixture that would observe it.

**The four consumers, with what each produces today:**

- `variantValueBindings` (`pysrc/processYaml.py:6105`) feeds `checkInterfacePair`. It produces a **FALSE REJECTION** in one arrangement and a **SILENT ACCEPTANCE of a real divergence** in the mirror arrangement — the latter compiles, links, and is caught only by a runtime assertion, with the database and the emitted C++ genuinely disagreeing. **VERIFIED BY EXECUTION**; both directions are recorded verbatim at [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) §5.5a and at `examples/xprojParam/README.md`, "`cstUse` — the prescribed shape at a non-default value, rejected".
- `_post_validateVariantBindingSizing` (`:8259`): the `not in constants` guard at `:8260-8261` becomes a **silent early return**, disabling the `maxValue` check. This was the sole failing cell of the unit suite — `unittest/test_param_cross_project_linkage.py::test_gap_shared_include_binding_sizing_enforced` (`:562`), which binds 64 against a `maxValue` of 32 and asserts rejection. It is the recorded G5.9 of [`plan-ip-project-composition.md`](./plan-ip-project-composition.md).
- `_resolveWordLinesConstant` (`:7215-7216`): unguarded index; raises a raw `KeyError` instead of a diagnostic. **EXECUTED** on every `make db` of `examples/ip_test/ip` and `examples/simple_ip/ip`, whose `wordLines` name block params and so leave `wordLinesKey` empty; it never raised because those params are same-file, so `paramKey` and the backing constant key coincided.
- `templates/systemVerilog/package.py:46`: the key misses `paramNameByKey`, falls through `symSpelling` (`:49-54`) and emits the constant's **default literal** into the module-local declaration instead of the module parameter name. **Silently wrong RTL.** Not covered by any fixture — the `cst` family declares `hasRtl: false` throughout. **Treat this as the most serious consequence**, notwithstanding that it is currently unreachable: it is the only one whose artefact is wrong hardware rather than a wrong check.

**Two readers are correct** (`_validateIpParametersLinkage` at `:8229`, because it compares within one file where the two keys coincide; `deriveParameterizedDeclSets`' per-block resolution at `:5540-5547`) and **`calcBlockConfigInfo` resolves properly** via `lookupInScope` at `:4873-4879`. **The qualification is INCONSISTENT, not uniformly wrong**, which is exactly why the emitted artefacts and the db-time gates disagree rather than both being stale.

**The fix is §4, and it LANDED 2026-08-13** ("Plan of record" step 1). All four bad consumers read a genuinely resolved key and were corrected by one change. The 14 rows below are unchanged on `paramKey`, which is retained as the block-scoped identity; the same join on the new `paramSourceKey` returns zero.

### B2 — A structure declared in an including file whose width comes from an included constant does not compile

Per-context round-trip test structures (`--template=structures --section=testStructsCPP`) are instantiated at Configs built from **that context's own** parameterizable constants, which do not carry the included one. Clean `db`, clean `gen`, then a build failure:

```
model/xpCstSupIncludes.cppm:52:55: fatal error: no member named 'CS_PIXEL_WIDTH'
   in 'xpCstBind_xpCstSup_test_ns::xpCstSupTestConfigDefault'
```

**VERIFIED BY EXECUTION**, recorded at `examples/xprojParam/README.md` and at [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) §5.5a. This is why `cstBind`'s Inc blocks carry the IP's own `csDutIf` rather than a payload of their own, and it is a second, independent reason an author cannot straightforwardly build on an included parameter.

### B3 — The testbench External omits `foreignConfigModules`

`ext_module_export` (`templates/systemc/testbench.py:228-249`) emits `sc_instance_includes` and `_tb_context_imports` but never `data['foreignConfigModules']`, while the block-module path does (`pysrc/intf_gen_utils.py:596-606`) and so does the registrar (`templates/systemc/blockRegistrar.py:107`) and the Verilated registrar (`templates/systemc/vlRegistrar.py:91`). **VERIFIED BY CODE READING**; `foreignConfigModules` is populated at `pysrc/processYaml.py:2154` and has exactly those three consumers.

Consequence: a top that **directly** contains an instance bound to a foreign-declared variant fails to compile, because the External names the owner-qualified Config without importing the module that exports it. The fixture works around it with a wrapper, and says so: `examples/xprojParam/cstBind/yaml/xpCstBindTop.yaml`, "The cells sit in a wrapper rather than directly in the top because the testbench External the top would otherwise get names the DUT's owner-qualified foreign Config without importing the module that exports it."

This matters to the feature because D4 — the assembler declares variants of blocks it does not own — is exactly the shape that produces a foreign Config, and the natural place to assemble a use case is the top.

**FIXED 2026-08-14, with a live acceptance gate.** `ext_module_export` now emits `data['foreignConfigModules']` in its excludeInst arm, in the same order the block path uses (foreign Config modules, then container-sourced maker modules). Two corrections to the record above:

- **The reachable shape is a PEER of the DUT, not a child of it.** The Externals were retargeted at their `_tb` container, so an External emits the DUT's siblings; instances of the DUT itself are on the block path, which already emitted the import. The `cstBind` and `xpDpMidStdTop` wrapper comments citing B3 as their reason are therefore wrong and are corrected in place; the wrappers are left standing because removing them needs model re-authoring.
- **The gate.** `examples/xprojParam/dpTop` gains `xpDpTbPeer`, a block instantiated only inside `xpDpTop_tb`, at two assembler-declared (foreign) variants. It runs under `make xproj-depth`. Observed before the fix: `tb/xpDpTop/xpDpTopExternal.cppm:35:36: fatal error: use of undeclared identifier 'xpDpTop_xpDpTbPeerPeerConfig'`. Green after.

**The excluded DUT was a second, unrecorded half of B3.** `getBDInstances`' excluded-instance loop resolved the DUT's per-instance Config but recorded neither its `foreignConfigModule` nor a container-sourced maker entry, so a DUT bound to a foreign variant would still have missed its import after the fix above. The recording is now mirrored from the contained-instance loop. **No fixture exercises it**: it needs a testbench whose DUT block's config context is owned by another project, which no example has.

**A third gap in the same family, also fixed.** `getBDConfigInfo` populated `configIncludeContext` from the block's own params and `subBlockInstances` only. A testbench container holding a parameterizable DUT and NO parameterizable peer therefore named `<DUT>Inverted<dutXConfig>` with no `#include "<ctx>VariantConfig.h"`. Excluded instances now contribute their DUT's config context too.

- **The gate is `hasOwnParams`, not `isParameterizable`**, because that is the condition under which the emitted `Inverted` base carries a template argument at all. Gating on `isParameterizable` — which is what the neighbouring `subBlockInstances` loop does — was tried first and MEASURED to over-include: it added `#include "xpGainVariantConfig.h"` to `examples/xprojParam/shared/tb/xpSharedTop/xpSharedTopExternal.cppm`, whose DUT is flagged parameterizable only because parameterizable structures transit its surface and whose base clause therefore names no Config.
- **No current example exercises it.** Every testbench that holds a `hasOwnParams` DUT also holds a peer in the same config context, and any peer bound to a parameterizable DUT port is itself flagged `isParameterizable`, so the include already arrives by the other route. The fix changes no emitted byte in either tree.

### B3b — The testbench External spells the container's `Config` template symbol, which it does not declare

`cpp_config_struct_name` (`pysrc/intf_gen_utils.py`) spells a per-instance Config that defers to the container as the container's own class template parameter: bare `Config` for `inheritContainerParam`, `<name><Config>` for a container-sourced variant, and a nested-Config alias applied to the same. Every site that consumes it renders inside the container's class template — except the testbench External, which has no template head. The External is the ONE consumer of the per-instance Config machinery that is neither a class template nor on the block dependency-line path, so this is the only place the symbol leaks.

Seven sites in `templates/systemc/testbench.py` carried the spelling; six were unsubstituted and the seventh — the peer-to-peer channel declarations — already mapped it onto the container's Config with a post-hoc `replace`. **FIXED 2026-08-14** by threading that one substitution through the whole region instead: `_tb_bind_container_config` binds the symbol once over each rendered External section, which covers the peer declarations, the ctor casts, the container-sourced maker argument, the channel and thunker payloads, and the excluded DUT's `Inverted` base clause.

**Observed before the fix**, on the `examples/xif` gate: `tb/dut/dutExternal.cppm:39:54: fatal error: use of undeclared identifier 'Config'`. Green after.

**The product tree is NOT exposed to this defect. The earlier suggestion that it is, through `inheritContainerParam`, is wrong and is corrected here.** `/work/ws/debayer/yaml/debayer.yaml:271-272` declares `inheritContainerParam` on DUT CHILDREN (`u_preprocess`, `u_interpolate` inside `debayer`), which excludeInst mode never emits — they are on the block path, inside `debayer`'s own class template, where the symbol is correct. `debayer_tb` declares no `params:` and no peer of the DUT uses either deferral mechanism.

### B3c — A testbench container cannot carry `params:` today, which bounds B3b's reach

Both deferral mechanisms REQUIRE a parameterized container (`validate_inherit_container_params` rule (c); the container-parameter existence check for `containerParam`). For B3b to arise, the `_tb` block must therefore declare `params:`. **In a cross-project shape it then names a Config struct that no artifact emits.** MEASURED on `examples/xprojParam/dpTop`: giving `xpDpTop_tb` `params: [MID_ALGO]` produced `xpDpTop_xpDpTop_tbTbConfig` in the External and in no other file in the tree. The `foreignConfig` fileMap entry is `mode: registrar, condAnd: {hasMdl: true}` — it emits per *reused child* of an assembler, and a `_tb` block is `hasMdl: false` and is nobody's child — while the context Config header carries only the non-foreign structs. `xpDpTop_tb`'s `configContext` resolves to the included IP root (`dpLeaf`), so its own variants are classified foreign.

Consequence: **B3b's guard has to live in a SINGLE-PROJECT example**, where the container's config context is owned by the same project and its struct lands in that context's Config header. `examples/xif` is that example and carries the gate: `xif_tb` declares `params:`, and `tbPeer` is instantiated twice inside it, once at a stated variant and once at a variant that sources every parameter from the container.

**A second, independent limit on the `inheritContainerParam` arm. FIXED 2026-08-17** — see "Supersession: one framework template replaces the generated makers" (§6, step 7) and its `make xproj-inherit` gate. The description below is the defect as it stood. The parent-owned registrar registers an inherited child against the CHILD's `defaultConfig` (`templates/systemc/blockRegistrar.py`, `_target(variant, desc)` with `desc is None`), not against the container's resolved Config. Inside the container's class template that is invisible, because the declaration is symbolic. In a testbench External the declaration is concrete, so unless the container's selected Config happens to spell the same struct as the child's default — which is exactly why the product tree's `debayer`/`preprocess` pair works — the `dynamic_pointer_cast` returns null and elaboration dereferences it. **The `xif` gate therefore uses the `containerParam` arm, which has no such mismatch: the maker template is applied to the same container Config the declaration names.** The `inheritContainerParam` arm is covered by the same one-line substitution but is NOT separately guarded by a running fixture.

### B4 — An `eval`-derived backing constant discards its per-variant override, silently

An eval-derived parameterizable constant is emitted into the Config **symbolically**, from its canonical expression, regardless of the resolved per-variant value: `_configMemberRhs`, `templates/systemc/config.py:217-224` — `if constData['evalCanonical']: return emitCStyleCanonical(...)`, ignoring `resolved`. The descriptor *does* carry the override (`pysrc/processYaml.py:4086-4089`), so the value exists and is then thrown away at emission. **VERIFIED BY CODE READING.** There is no diagnostic.

`deriveParameterizedDeclSets` excludes such a constant from the declaration set when it is a backing key (`pysrc/processYaml.py:5395`), which is why this reads as an **unhandled combination rather than a supported one**.

Consequence for this feature: D3's uniform "value through a named constant" rule breaks wherever the value is computed. In the cross-file case the artefact is a plausible-looking wrong number. The fixture records the constraint in its own words at `examples/xprojParam/cstBind/yaml/xpCstSup.yaml`: "It cannot be written as `eval: \"$CS_PIXEL_WIDTH\"`: an eval-derived constant is emitted into the Config symbolically and its per-variant override is dropped, so every variant would carry the same expression."

### B5 — The emitted Config carries the whole context's parameterizable constants, not the subset a block names

`calcVariantConfigDescriptors` builds a Config's field set from **every** parameterizable constant whose `_context` equals the block's `configContext` (`pysrc/processYaml.py:4068-4070`), then assigns each field either the variant override or the constant's own declared value (`:4086-4089`). **Citation corrected 2026-09-05.** This section and B4 both named the function `_buildVariantConfigDescriptors` at lines 1875-1930. No such identifier exists; it was renamed, and those line numbers now land in unrelated code. Three separate readers lost time to it. The behaviour described was and is real, at the lines given here, and two further sites apply the same context-wide rule: `getForeignConfigData` (`:1830-1839`) and `templates/systemc/config.py:136`.

Two consequences:

- **A block silently inherits fields it never declared**, taking the *declaration default* rather than any bound value. That is a silent-divergence hazard on exactly the path this feature creates, because the whole point of the feature is that several blocks share one context.
- **Derived constants are emitted as Config members.** In the product tree that is `MAX_PIXEL_VALUE` and `BPPC_P1..P5`; the generated base classes consume them (`base/raw_video_srcBase.cppm:46`, `static constexpr auto MAX_PIXEL_VALUE = Config::MAX_PIXEL_VALUE;`, quoted at [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) step 8e). **This contradicts the architect's stated rule that derived parameters are not part of the config.**

**In scope for this feature**, both because of the silent divergence and because Q3's rename is unsafe until the Config is composed by resolved constant identity rather than by name (§4.3, point 2).

**Measured 2026-08-13: a two-context block. VERIFIED BY EXECUTION**, on the disposable fixture `examples/xprojParam/twoCtx` (`xpTwoCtxDut` names an included `DP_WIDTH` and an own-file `TC_GAIN`, both bound to non-default values; `xpTwoCtxBare` is the same shape with no parameterizable structure on its own surface). No such block existed anywhere in either tree before. `make db` and `make gen` are **clean**, and then:

1. **It does not COMPILE** when the losing context contributes a derived constant the block's surface reaches — `base/xpTwoCtxDutBase.cppm:49` names `Config::TC_GAIN_X2`, which the emitted Config does not carry.
2. **The Config's NAME and HOME HEADER flip on the order of the `params:` list**, for a params-only block, with **no diagnostic**: `[DP_WIDTH, TC_GAIN]` yields `xpDpLeafDefaultConfig` in the included file, `[TC_GAIN, DP_WIDTH]` yields `xpTwoCtxDefaultConfig` in the block's own.
3. **Losing-context params degrade to a bare `uint32_t`** emitted through the synthetic arm, with no declared type and no `maxValue` check.

**Bound values do survive** all three. **B5 (step 3) removes all three**, which is what makes B5 the precondition for Case 1 (§2, D2). The SystemVerilog side carries **both** contexts correctly, so the two languages disagree about the block's parameter set.

**Measured 2026-08-13: the "one Config for everyone" worry is factually superseded.** The concern behind the original shared-vs-IP boundary decision ([`plan-shared-vs-ip-boundary.md`](./plan-shared-vs-ip-boundary.md)) was that blocks sharing a config context would be forced to share one Config. **Seven blocks across two files already share one config context and one `defaultConfig` in the product tree while emitting five distinct per-variant structs.** **VERIFIED BY EXECUTION.** Sharing a context does not collapse the per-variant Configs; B5's defect is the field **set**, not the struct count.

### B6 — A variant declared above the instance's own project is accepted and then silently orphaned

**The customer/depth case of §3, Case 2. This is the finding that originated the D7 design work.**

Established on a three-level disposable fixture, `examples/xprojParam/{dpLeaf,dpMid,dpTop}` — leaf IP, mid-level IP that instantiates it, customer assembler that instantiates the mid and declares the **leaf's** variant. **VERIFIED BY EXECUTION**, recorded in full at `examples/xprojParam/dpTop/README.md`:

- **A variant declared two levels above is accepted at every gate and then ORPHANED.** `make db` clean, `make gen` clean, the design compiles, and **the value appears in no emitted artefact**: the nested leaves resolve the vendor's declared default while the customer declared something else. **There is NO diagnostic anywhere.** The only thing that notices is a hand-written runtime assertion in the customer's own checker.
- **The emitted RTL does not even elaborate.** The container forwards a child parameter it does not itself declare; Verilator rejects it — "Expecting expression to be constant".
- **Two instances of one IP whose nested blocks differ is INEXPRESSIBLE today.** Both mid instances' nested leaves take one and the same Config. Per-instance configuration stops at the level whose project declares the instance.

**Root causes, two:**

1. **Descriptor selection keys the consumer project on the file declaring the INSTANCE**, so a declaration owned by an ancestor project is never eligible.
2. **The container is generated from its OWN database and hard-codes the child Config symbol**, so nothing downstream of the container can vary per container instance.

**A recorded belief corrected.** `examples/ip_test/bridge/yaml/bridgeStdTop.yaml:76-79` states that "In composition ip_top owns this declaration and bridgeStdTop is not included, so there is no duplicate." **That is FALSE. VERIFIED BY EXECUTION:** both declarations are present and the bridge binds its **own** Config. It works only because the two declarations carry the same values.

**A latent hazard confirmed.** `inheritContainerParam` emits a cast on `Config` while the registrar hard-codes the **default** Config. The two coincide only because `debayer` declares exactly one variant. A second declared variant would make that cast return `nullptr` **at run time**, with no compile-time diagnostic. **VERIFIED BY EXECUTION.** **FIXED 2026-08-17**: the container now names the child's implementation class at the `createInstance` site and the wrong registration is deleted; the hazard is guarded by `make xproj-inherit` (`examples/xprojParam/inhVar`), whose second container variant reproduced the null cast as a SIGSEGV before the fix. See "Supersession: one framework template replaces the generated makers" (§6, step 7).

**The layout gate is not a safety net here.** It adjudicates only the pairing named by the **instance row's** variant label: the same divergent nested width was **REJECTED** on one variant and accepted **SILENTLY** on another. **VERIFIED BY EXECUTION.** This is why D7 requires a db-time diagnostic rather than leaning on the thunker/layout path.

**Not a blocker for steps 1 through 6.** B6 is the premise of step 7, and it is recorded as a defect rather than a design gap because the silent orphaning has no diagnostic.

## 6. Plan Of Record

Sequence and dependencies only. Each step states what changes, what proves it, and its blast radius. **B1 gates most of the rest**, and the parallelism is stated explicitly.

### Step 1 — The explicit parameter link. LANDED 2026-08-13. GATES steps 3 and 6

- **Changes.** The schema shape chosen at Q1/Q2; the FK onto `constants`; `_post_validateBlockParamBacking` reduced to the parameterizable check on the resolved row, with its stale comment at `pysrc/processYaml.py:8212-8214` corrected; the four consumers of §4.5 repointed; the two re-derivations at `:5540-5547` and `:4873-4879` collapsed onto the persisted key; `_validateIpParametersLinkage` (`:8243`) moved onto the link; **the silent early return at `:8260-8261` made loud**. If shape (ii) is chosen, a `migrateYaml.py` phase and a `yamlFormat` bump.
- **Proves it, make-driven.** `make xproj-const` still runs both cells, reporting `checked 4 samples at pixel width 12` and `... at pixel width 20`. **`make xproj-const-probes` must FLIP**: the `cstUse` db build, today asserted to fail (`Makefile:230-235`, which errors if the build succeeds), must succeed, at which point the target's own diagnostic instructs promotion. `unittest/test_param_cross_project_linkage.py::test_gap_shared_include_binding_sizing_enforced` must **pass**, taking the suite to 9/9 and the unit suite to 101/101. `make pipeline-test -j` exit 0. The product tree builds and links.
- **Structural readback is the weaker second gate, not the first.** After the flip, `select ... from blocksparams left join constants` must return **zero** unresolved rows across every database in both trees; today it returns 14.
- **Blast radius.** Resolved values: **none move** — measured, §5 B1. Emitted output: expected none, to be confirmed by hashing every generated source in `examples/` and `/work/ws/debayer` before and after, which is the measurement every step of the sibling plan used. Authored YAML: 45 occurrences in 31 files under shape (ii); none under shapes (i) or (iii).
- **Done when.** The probe flips and is promoted into `xproj-const`; the sizing cell passes; `pipeline-test` and the product build are clean; the emitted-output delta is enumerated and is either empty or explained row by row.

#### Step 1 as landed, 2026-08-13. VERIFIED BY EXECUTION unless stated

**The row shape.** `blocks.params` gains one authored-shape-free field pair. `params:` stays a bare list; no YAML anywhere changed and there is no migration and no `yamlFormat` bump, exactly as §4.0 decided.

```yaml
  params:
    _attribs: [optional, list, flat, post(validateBlockParamBacking)]
    param: key
    paramSource:
      _type: auto(paramSource)
      _validate:
        section: constants
        field: constant
```

**The mechanism for the name defaulting, and why the alternatives lose.** `auto(...)` pre-population plus the foreign key is not a new construct: `instances.container` is `_type: auto(container)` carrying a `_validate: {section: blocks, field: block}` (`config/schema.yaml:230-235`, `_auto_container`), which is precisely "a field whose value is supplied by code and then resolved by an FK". `_auto_paramSource` returns `processed['param']`, which states the same-name rule directly rather than re-deriving it from the YAML anchor. The FK then resolves and `processSimple` overwrites `paramSourceKey` with the resolved qualification.

- **`anchor` — REJECTED.** It would have taken the list element with no new Python at all, and it parses. But `pysrc/schema.py:1077` sets `node.anchor_field = field_name` unconditionally, and `blocksparams` already has an anchor: `param: key` is converted to `anchor` for nested tables at `:1045-1050`. A second `anchor` field silently repoints `node.anchor_field`, which feeds the `data_by_parent` nested index key (`pysrc/processYaml.py:817-818`) and the `data['key']` fallback (`pysrc/schema.py:1229-1230`). It is correct today only because the two values coincide under the same-name rule — the exact class of latent coincidence this step exists to remove. It is also the only `anchor` in the whole schema used as anything but the key. Declaring `paramSource` before `param` would dodge the clobber by declaration order, which is worse.
- **`_combo` of `[param]` — REJECTED, cannot work.** `validateForeignKey` branches on `sourceFieldObj.combo_sources` and takes the combo arm, which Foreign-Key Invariant 4 requires to target a combo field; `constants.constant` is not one.
- **`_singular` — not applicable.** The section is a list of scalars, not a mapping.
- **`required`/`optional` — REJECTED by §4.0.** Either the user authors the link, which §4.0 forbade, or an `optional` empty value skips validation entirely (`pysrc/processYaml.py`, the `ftype=='optional' and ret[field]==""` arm).

**The experiment §7 asked for, run before anything was built on it.** On `examples/xprojParam/cstBind/xpCstBind.db`, the FK writes the resolved qualification and `paramKey` is untouched:

```
block        param           paramKey                                         paramSourceKey
xpCstDut     CS_PIXEL_WIDTH  CS_PIXEL_WIDTH/../../../cstIp/yaml/xpCstIp.yaml  CS_PIXEL_WIDTH/../../../cstIp/yaml/xpCstIp.yaml
xpCstSrcInc  CS_PIXEL_WIDTH  CS_PIXEL_WIDTH/../../yaml/xpCstSup.yaml          CS_PIXEL_WIDTH/../../../cstIp/yaml/xpCstIp.yaml
xpCstChkInc  CS_PIXEL_WIDTH  CS_PIXEL_WIDTH/../../yaml/xpCstSup.yaml          CS_PIXEL_WIDTH/../../../cstIp/yaml/xpCstIp.yaml
```

§7's "read from the code but not executed" entry for `processYaml.py:6832`/`:6994` is therefore **discharged**: the key machinery pre-populates `{field}Key` only when absent and the validator's assignment wins.

**Consumers moved.** All four of §4.5 plus the two re-derivations and the orphan check now read `paramSourceKey`: `variantValueBindings` (its bare-`param` and `blockParamKey` seeds deleted, so one fact has one key), `_post_validateVariantBindingSizing`, `_resolveWordLinesConstant`, `templates/systemVerilog/package.py::parameterizedDeclLines` (all three call sites take `blockInfo['params']`, which are whole DB rows, so they needed no change), `deriveParameterizedDeclSets` (both `backingKeys` and the per-block `blockParams`, whose `lookupInScope` is deleted), `calcBlockConfigInfo`'s `own_params_context` (now the resolved row's `_context`, not a re-lookup and not a string split), and `_validateIpParametersLinkage`.

**The two silent early returns.** `continueOnError` is a module-level `False` (`pysrc/processYaml.py:21`), so `logError` always exits; an unresolved `paramSourceKey` downstream of the FK is therefore genuinely unreachable, not merely unlikely. `_post_validateVariantBindingSizing`'s guard became a hard generator-bug diagnostic naming the block and param, and `_resolveWordLinesConstant`'s unguarded index became the same, matching the neighbouring `printError`. `_post_validateBlockParamBacking` keeps **only** the `isParameterizable` check and indexes the resolved row directly.

**Two claims in this document were WRONG and are corrected in place.**

- §4.1's "the comment asserting it is stale" was right about the comment but the comment is now **deleted**, not corrected: `_post_validateBlockParamBacking` no longer performs a lookup, so there is nothing left to justify.
- §4.4 states "`builder/pro` is not present in this tree". **It is present** — `builder/pro/examples/lmmiDemo` exists and carries a database. It has no `blocksparams` rows, so it does not change the §4.4 migration count or the B1 blast radius, but the parenthetical is false.

**A diagnostic regression, reported rather than hidden.** An unbacked block param used to be rejected by `_post_validateBlockParamBacking` with "block param 'X' has no backing constant; every block param must be declared as a same-name ipParameters constant". It is now rejected by the generic FK miss: `In file F:4, section params, key:NO_BACKING field paramSource, value NO_BACKING was not valid in context F; no constants row named 'NO_BACKING' was found in any context processed before this one`. The rejection still happens and the message still names the file, line, section and symbol and carries the include-chain hint, but it mentions the internal field `paramSource`, which the author never writes, and it drops the "must be a same-name ipParameters constant" guidance. Restoring that wording would mean re-resolving the constant at a second site, which is what this step removed. `unittest/test_param_const_linkage.py::test_unbacked_block_param` was updated to the new text.

**Acceptance, measured.**

- **The headline prediction holds.** `examples/xprojParam/cstUse` builds and runs. Under the pre-change generator, reconstructed and re-run to confirm the reconstruction, it still fails at `make db` with the recorded false layout-gate rejection between `xpCstDut` and `xpCstUseSrc`. It is **promoted into `xproj-const`** and `xproj-const-probes` is deleted, its only cell having graduated. Its models were scaffolded with `make newmodule` and authored to mirror `cstBind`'s Inc pair; both assert their resolved width against a number restated in the model.
- `make xproj-const -j` exits 0, all three cells reporting: `checked 4 samples at pixel width 12` (cell A), `... at pixel width 20` (cell B), `... at pixel width 20` (cstUse).
- `unittest/test_param_cross_project_linkage.py` is **9 of 9**; `test_gap_shared_include_binding_sizing_enforced` passes, closing G5.9 of [`plan-ip-project-composition.md`](./plan-ip-project-composition.md). Unit suite **101 suites, 101 passed**. The guard count did not change, so neither runner needed editing.
- `make clean` then `make pipeline-test -j` exits 0. The product tree cold-regenerates, builds and links.
- **Unresolved rows: 14 → 0.** Left-joining `blocksparams.paramSourceKey` against `constants.constantKey` over every database in `examples/`, `builder/pro/examples/`, `/work/ws/debayer/debayer.db` and `/work/ws/debayer/isp_shared/isp_shared.db` returns **zero rows** across 131 `blocksparams` rows in 40 databases. The same join on `paramKey` still returns **14 rows in 6 databases** — intended, because `paramKey` is retained as the block-scoped identity and is no longer read as a constant key by anything. Two databases carry no `paramSourceKey` column: `isp_shared.db`, which is built by `isp_shared`'s own independent builder submodule rather than this one, and the stale `lmmiDemo.db`. Both have **zero** `blocksparams` rows, so the omission is vacuous.
  - **Two measurement corrections, 2026-08-13 (independent review).** (a) The 40/131 population counts each project **twice**: the glob picks up both the live `<name>.db` and the previous-generation `.<name>.db` snapshot the build keeps alongside it. The live population is **34 databases / 107 rows**; the zero-unresolved result is the same on either population, re-measured. (b) The `paramKey` figure is **not** "unchanged" against a cold pre-change tree: 2 of the 14 rows are `cstUse`'s, and `cstUse` had no database before this step because its `make db` was asserted to fail. The cold pre-change baseline is **12 rows in 5 databases**; 14-in-6 is the post-change figure and matches the pre-change figure only against a stale `xpCstUse.db`.
- **Emitted-output delta: NONE.** 1693 generated sources across `examples/`, `builder/pro/examples/`, `isp_shared` and `/work/ws/debayer` hashed after a full cold regeneration under each generator: zero added, zero removed, zero changed. This is what §5 B1 predicted, because every live binding on the affected path binds its constant's declared default. `cstUse`'s 21 files are new to the tree and are the change's only additions.
- **Census: unchanged at 18 of 42** (`ip_test` 14/19, `simple_ip` 2/4, `xif` 0/2, `xprojParam` 2/17), re-read from emitted `_port_thunker<>` instantiations. `cstUse` adds 2 pairs, both corresponding, outside that table's scope in the same way `cstBind` and the `mtx*` family are.

**Review follow-ups applied.** A dedicated review of the change found and closed: a now-vestigial truthiness test at `calcBlockConfigInfo`'s context append (the FK guarantees a real `_context`, so the falsy branch — and the comment paragraph advertising it — are gone); a stale `_validateIpParametersLinkage` comment still pointing the reader at "the param field `_validate`"; a wrong function name inside `_resolveWordLinesConst`'s own diagnostic; and `examples/xprojParam/cstBind/yaml/xpCstSup.yaml`'s header, which still told authors the Inc shape "works at the IP's declared default and ONLY there". Stale cross-references in [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) are marked superseded and **G5.9 is recorded there as CLOSED**. Everything above was re-measured after these edits and is unchanged.

**Two review recommendations NOT taken, recorded with reasons.**

- *Delete the two "generator bug" guards outright rather than diagnose.* Kept. The brief for this step asked specifically for a diagnostic at `_resolveWordLinesConst` "matching the neighbouring `printError`", and both sites reach a **different** row than the one whose FK just fired — `_post_validateVariantBindingSizing` arrives via `blockParamKey`, `_resolveWordLinesConst` via a scan — unlike `_post_validateBlockParamBacking`, which is same-row and is therefore correctly left unguarded. The asymmetry is deliberate, not an oversight.
- *Add a fixture for the deleted bare-name seed in `variantValueBindings`.* Not added here. Dropping the bare-`param` and `blockParamKey` seeds was explicitly directed by §4.5, and the remaining scoped path (`_visibleNamedKey` against the resolver's context) is strictly more correct than the scope-blind bare-name hit it replaces. The empirical evidence that nothing live depended on it is the zero emitted-output delta plus a clean `pipeline-test` and product build. A fixture exercising an **unqualified** width reference whose backing constant is not visible from the interface's declaring context would still be worth having, and is recorded here as an open coverage item rather than done.

#### Independent review, 2026-08-13 — findings not previously recorded

Re-measured independently: unit suite **101 of 101**; cold `make clean` + `make pipeline-test -j` **exit 0** with the three `xproj-const` cells reporting widths **12 / 20 / 20**; unresolved `paramSourceKey` rows **0**; product tree cold `make clean` + `make gen -j` + `make -C rundir -j all` **exit 0**. The emitted-output delta and the census were taken on trust; neither is re-measurable without the pre-change generator.

1. **The include chain silently decides the backing constant when two same-named parameterizable constants are in scope. NEW, and measured.** `validateForeignKey`'s plain arm delegates to `lookupInScope`, which returns the **first** match with no ambiguity diagnostic — the duplicate check exists only on the `scope: global` arm (`_lookupInGlobal`). Reproduced with a throwaway three-file fixture: two included files each declaring a parameterizable `WIDTH` (`maxValue` 32 and 9), and a third block naming `WIDTH` with both in scope. Reversing the two `include:` entries flips the resolved `paramSourceKey` between the two files, and with it a `WIDTH: 20` binding between accepted and rejected. **Blast radius today: zero.** Walking every `blocksparams` row's persisted `YAMLCONTEXT` include chain against `constants` across all 34 live databases, **every row reaches exactly one same-named constant** — never zero, never two. This is a pre-existing property of every plain FK rather than something this step introduced, but the step makes it load-bearing for a fact that now reaches the emitted Config, the SV parameter spelling and the `maxValue` gate. Recorded as a known limitation; a duplicate diagnostic on the scoped arm is the obvious fix and has `_lookupInGlobal` as precedent.
2. **One of the two silent early returns in `_post_validateVariantBindingSizing` was left silent.** The guard on the *constants* miss was made loud as directed. The guard two lines above it — `if blockParamKey not in self.flatData['blocksparams']: return item` — is equally unreachable (`parametersvariantsparams.blockParam` is a combo FK onto `blocksparams.blockparam`, and `continueOnError` is `False`, so a miss exits at parse time) and is still a bare `return`. The stated reason for keeping the loud guards — "both sites reach a different row than the one whose FK just fired" — applies to this one identically. Either both should be loud or all three should go; the present asymmetry is unexplained.
3. **`blocksparams.paramKey` now has zero code consumers.** Grepping `pysrc/` and `templates/` finds it only in two comments. It survives because the key machinery emits a `{field}Key` contextKey for any `key`-typed field, not because anything reads it. "Retained as the block-scoped identity" overstates it: the identity the variant side actually targets is the `blockparam` combo key.
4. **`checkInterfacePair`'s equal-bindings fast path now actually fires.** Before, `variantValueBindings` seeded `blockParamKey`, which embeds the block, so `parentBindings == childBindings` was false for every junction whose two sides both declared params, and the comparison always ran. Keyed by resolved constant key alone, two sides sharing one constant at one value now compare equal and the junction is skipped. Assessed safe — equal `interfaceKey` plus equal overrides means both resolvers walk one declaration identically, and `structPackedFields` resolves through each var's own `_context` rather than the resolver's — but it is a behavioural change in the gate, not only a re-keying.
5. **`calcBlockConfigInfo`'s `own_params_context` changed meaning, not merely its derivation.** It now records the **backing constant's** file rather than the file the `params:` list sits in, which flows into `configContext` and `defaultConfig`. Nothing moves today because every block that would differ is already `isParameterizable` from an own-surface structure, so the `params:`-only arm is not reached — consistent with the zero emitted-output delta. The new reading is the correct one (a Config must be emitted where its fields are declared); it is recorded here because it is a semantic change rather than a collapsed re-derivation. Verified in passing: **no block in either tree** declares params backed by more than one context, so taking the first param's context is currently unambiguous.
6. **`validate_inherit_container_params` still compares child and container params by bare name** while resolved identity is now on the row. Two blocks whose same-named param is backed by *different* constants — the exact shape `unittest/test_parameter_variant_block_param_identity.py` builds — would be treated as a match. Pre-existing and out of scope for this step, but now cheaply fixable and worth an entry.
7. **The diagnostic regression has no cheap in-framework fix.** `_validate` accepts only `section`, `field`, `scope` and `values` (`schema.py:934-947`); there is no per-field message hook, and adding one would be new schema surface serving exactly one field. Not recommended. The generic message does keep file, line, `section params`, the symbol and the include-chain hint, and its "no constants row named 'X' was found in any context processed before this one" wording covers the parse-ordering case §4.1 asked to be stated. What it loses is the word "ipParameters"; that is a real but small loss of authoring guidance and is accepted here.

#### Ruled on after the review, 2026-08-13 — FIXED; VERIFIED BY BUILD 2026-08-18

**Review finding 2 (the third silent early return) was ruled on by the architect: "make it loud".** The `blocksparams` miss in `_post_validateVariantBindingSizing` had been left a bare `return item` while its neighbour was made a hard diagnostic; the asymmetry recorded at finding 2 is removed. It now **mirrors the neighbouring guard exactly** — `printError` followed by `exit(warningAndErrorReport())`, with the same `Generator bug in _post_validateVariantBindingSizing:` prefix, naming the variant, the param and the unresolved block-param key.

**The verification owed here was run on 2026-08-18. All three pass; nothing else in step 1's landed record changes.**

- Unit suite **103 of 103**, `unittest/run_all_tests_parallel.sh` exit 0 (103 rather than 101 because two suites have been added since: the container-layout channel cell and this closeout's `test_container_param_inheritance.py`).
- Cold `make clean` then `make pipeline-test -j` **exit 0**, with the `xproj-depth` chains reporting algorithms 5 / 6 / 7 / 1, `xproj-inherit` reporting 1 and 6, and `xproj-container-layout` reporting `cpLayoutBad` rejected at the container-resolved `_bitWidth 24`.
- Product tree cold `make clean` + `make gen -j` + `make -C rundir -j all`, all **exit 0**.
- **Emitted-output delta: NONE.** 1124 generated sources under `/work/ws/debayer` (excluding `builder/` and both `rundir/` trees) hashed before and after the cold regeneration: zero added, zero removed, zero changed. The guard is unreachable on every design in the corpus, which is why making it loud moves no artefact.

The remaining review findings (1, 3, 4, 5, 6, 7) were not actioned; each is carried at §7 or §8 with its own standing.

### Step 2 — B4: the eval-derived backing constant. LANDED 2026-09-07

- **As landed.** Option (a), at declaration. `_post_validateBlockParamBacking` (`pysrc/processYaml.py`) gained a second arm: a block param whose backing constant carries a non-empty `evalCanonical` is rejected, naming the file and line, the param, and the constant's name and declaring file. No variant is named, per the paragraph below. Guarded by `unittest/test_block_param_eval_backing.py` on `unittest/fixtures/block-param-eval-backing` (rejecting cell, and an accepting cell where the same constant becomes a plain `ipParameters` constant); registered in both runners. **Fault-injected, VERIFIED BY EXECUTION:** on the un-fixed generator the fixture built at exit 0 and the emitted Config carried `static constexpr uint32_t DERIVED_WIDTH = BASE_WIDTH * 2;` (8) against a bound 20. With the check removed the test FAILs; restored, both cells PASS. Corpus: `ip_test`, `twoCtx` and the product tree build clean, so the plan's zero-rows measurement held. Emitted-output delta: none. Unit suite 116 of 116.

- **Changes.** Either (a) reject the combination at db time with a diagnostic naming the constant, the block param and the variant, or (b) support it by re-resolving the expression under the variant's overrides. **Recommend (a) first**: it converts a silent wrong number into a message at the cost of a few lines, and (b) is the deferred D2 of [`plan-variant-config-unification.md`](./plan-variant-config-unification.md) ("eval re-evaluation ... language-native compile-time eval is deferred"), which is a larger question than this feature.
- **Proves it.** A fixture cell authoring `eval:` on a backing constant, fault-injected against the un-fixed generator and confirmed to emit the wrong number before the diagnostic is added. Today no such cell exists anywhere.
- **Blast radius. MEASURED 2026-09-05: ZERO. VERIFIED BY EXECUTION**, twice and independently. Left-joining `blocksparams.paramSourceKey` onto `constants` and filtering for a non-empty `evalCanonical` returns no rows in any of the 47 live databases that carry the link column. The two live databases without it, `unittest/fixtures/hier-layout/hier.db` and `isp_shared/isp_shared.db`, hold no parameterizable eval-derived constant at all, so neither can contain a hit. The population that could become a backing key later is 37 constants: the four `IP_DATA_WIDTH/MEM_DEPTH` multiples repeated across the `ip.yaml` family, `twoCtx`'s `TC_GAIN_X2`, and `debayer`'s 16 derived constants. No variant binds any of the 37.
- **The rejection belongs at DECLARATION, not at binding.** `_post_validateBlockParamBacking` (`pysrc/processYaml.py:8775-8785`) already resolves the backing constant row and rejects a non-parameterizable one with a positioned diagnostic, so the `evalCanonical` condition is a few lines inside an existing hook. That hook fires on the block-param row and has no variant in hand. Requiring the diagnostic to name the variant, as the "Changes" bullet above does, would move the check to `_post_validateVariantBindingSizing` and let an incoherent declaration stand until somebody bound it. A computed constant cannot be a block parameter whether or not a variant binds it.

### Step 3 — B5: the Config field set. LANDED 2026-09-05; DEPENDED ON step 1

**Landed record.** The Config field set now resolves through `blocksparams.paramSourceKey` at all four sites, and derived constants are computed in the implementation instead of carried as Config members. `model/debayerVariantConfig.h` went from five byte-identical 22-member structs to per-block structs of **6, 5, 6, 4 and 5** members. Each `*Base.cppm` now carries its derived constants as computed lines, `MAX_PIXEL_VALUE = (1 << Config::BITS_PER_PIXEL_COLOR) - 1` and the rest, matching `rtl/debayer.sv`'s `localparam` block. `rgb_video_sink` gained `HORIZONTAL_SIZE`, `VERTICAL_SIZE` and `DEBAYER_ALGORITHM` in `yaml/debayer_tb.yaml`, which is where those blocks are declared. `examples/xprojParam/twoCtx` went from not-compiling to compiling.

**Fixture half, LANDED 2026-09-06.** `twoCtx`'s testbench External is retargeted at `--block=xpTwoCtxTop_tb --excludeInst=u_xpTwoCtxTop`, matching the other `xprojParam` tops. Its five blocks gained behaviour: `xpTwoCtxSrc` drives `dpSt` payloads; `xpTwoCtxDut` asserts `DP_WIDTH == 12` and `TC_GAIN == 5` at run time, checks the payloads and forwards `tcSt` at `TC_GAIN_X2 + i` (the payload crosses the thunker by `bit_cast`, so the field checks prove routing, not width, which the review of this fixture caught: the first draft claimed a truncation guard that could not fire); `xpTwoCtxSnk` checks that against its OWN Config's `TC_GAIN_X2`, so the included-file and own-file context paths must agree on `TC_GAIN`; `xpTwoCtxBare` asserts `DP_WIDTH == 12`, `TC_GAIN == 5`, `TC_GAIN_X2 == 10` at run time. `xpTwoCtxDut` and `xpTwoCtxBare` also `static_assert(!requires { Config::DP_ALGO; })`, which pins the field set itself: `DP_ALGO` is declared in the included file and named by neither block. It is the new `xproj-twoctx` target, in `pipeline-test`, ordered after `xproj-depth` because both regenerate `dpLeaf`; it left `xproj-param-probes`, which now holds `deparam` alone. **Fault-injected, VERIFIED BY EXECUTION**: `xpTwoCtxSnk` expecting `TC_GAIN_X2 + i + 1` fails on `val field mismatch`; `xpTwoCtxBare` expecting `TC_GAIN_X2 == 11` fails on its run-time assert; inverting the `DP_ALGO` `static_assert` fails to compile. Each was restored and the run went back to "No error".

**Evidence, re-measured 2026-09-06.** `pipeline-test` exit 0, 64 "No error" (62 before `xproj-twoctx` joined), exactly 2 `make[1]: ***` at `varUniqBad` and `cpLayoutBad`; unit suite exit 0 at 115 suites, 115 passed (the "87 distinct suites" this line carried on 2026-09-05 was a miscount); the product tree regenerates from clean, builds, links, runs `test_debayer_structs` and reports "No error" at exit 0. Both gate logs were greped from the full teed file, and both were re-run after the defect below was fixed, not before.

**A defect this step introduced, found in review and fixed.** `constReference_cpp` (`templates/systemc/includes.py`) inlines a derived constant's expression into surrounding code and did not parenthesise it. `PREPROCESS_GRID_WIDTH` is `DEBAYER_DIMENSION + PIXELS_PER_CLOCK - 1`, so `w*PREPROCESS_GRID_WIDTH` became `w*DEBAYER_DIMENSION + PIXELS_PER_CLOCK - 1`. With `bayer_column_t::_bitWidth` at 40 and 8 columns, `preprocess_grid_t::_bitWidth` emitted 203 where 320 is correct, while `_packedSt` stayed `uint64_t[10]`; packing 320 bits into an `sc_bv<203>` aborted the product tree's struct self-test inside SystemC's `sc_bit_proxies.h`. Two sites carried it, `model/debayerIncludes.cppm:951` and `fw/debayerIncludesFW.h:504`, and one parenthesisation fixes both because both route through that function. The sibling emitter in `templates/systemc/baseClassDecl.py` is correct unwrapped: there each expression is a whole named declaration whose later members reference earlier names, so nothing is substituted into larger arithmetic. SystemVerilog is immune by construction, because a derived constant there is always a standalone `localparam` referenced symbolically.

**The gates did not catch it, and that is the more useful finding.** Both were green while the product tree emitted wrong arithmetic, because no example in the corpus multiplies by a derived constant whose expression is a sum. `unittest/test_eval_cpp_emit.py::test_const_reference_cpp_parenthesizes_compound_derived` now covers it, fault-injected in both directions: with the parentheses removed it fails on both assertions, reporting 43 where 64 is correct; restored, it passes. A `clog2(...)`-wrapped or single-term derived constant would have passed either way and been a test that proves nothing.

**A process note worth keeping.** This defect was reported to the reviewing session as a pre-existing unrelated crash, with a supporting claim that the crashing section was byte-for-byte unchanged. The diff contradicted both. The accompanying numeric check was real but examined `ENTRIES_PER_LINE_LOG2`, which genuinely does not move, rather than `PREPROCESS_GRID_WIDTH`, which does.

**Emitted-output delta, enumerated 2026-09-07.** Taken as the working-tree diff against `builder/base` HEAD `facf2c1` after the 2026-09-06 `pipeline-test` run, so it is step 3 plus its fixture half and nothing else. Every changed file is explained by one of four causes. The classification script counted removed and added `static constexpr` lines per file and the diffs of every file whose count did not decide it were read.

| Cause | Files | Which |
| :-- | --: | :-- |
| Config narrowed to the block's own params (members removed, nothing added) | 19 | `ip_test` and `simple_ip` `ipVariantConfig.h` (8 members each, 4 derived per struct), `ipBridge_ipVariantConfig.cppm`, `ip_test_ipVariantConfig.cppm`, `mixedVariantConfig.h` (`bob`), `xifVariantConfig.h`, `xpCppWrapVariantConfig.h`, three `dpMid` and three `dpTop` registrar Config modules, `xpInhContVariantConfig.h`, `xpMtxIpVariantConfig.h`, `xpTwoCtxVariantConfig.h`, two `twoCtx` registrar Config modules |
| Base class computes derived constants instead of aliasing `Config::` | 5 | `ip_test` and `simple_ip` `ipBase.cppm` (4 each), three `twoCtx` Base files |
| `constReference_cpp` spells a derived constant as its expression | 6 | `ipIncludes.cppm`, `ipIncludesFW.h` and `ip.cppm` in both `ip_test` and `simple_ip` (`Config::IP_MEM_DEPTH_X4` becomes `((Config::IP_MEM_DEPTH * 2) * 2)`) |
| The `twoCtx` fixture half | 8 | five `twoCtx` model files, its External, its README, `examples/xprojParam/README.md` |

38 files under `examples/`. One further file, `examples/xprojParam/dpTop/yaml/xpDpTop.yaml`, changes a comment and a `desc:` only: they said the customer's `MID_ALGO` bound was "deliberately wider than the leaf accepts" while the value was already 7, equal to the leaf's. No value moved. It is unrelated to step 3 and is recorded here so the diff is fully accounted for. `Makefile` gains the `xproj-twoctx` target.

Product tree, against `/work/ws/debayer` HEAD `70ec235`: the working tree also carries the uncommitted output of steps 7 through 11 (Tandem files, registrars, VL wrappers, the External), so only the step 3 share is listed. `model/debayerVariantConfig.h` goes from five 22-member structs to 6, 5, 6, 4 and 5, measured by counting `static constexpr` per struct in HEAD and in the working tree. The five `*Base.cppm` files each swap 16 aliases for 16 computed lines, `raw_video_srcBase.cppm` 9, and `rgb_video_sinkBase.cppm` removes 6 and adds 12 because the sink gained three params and their derived constants. `model/debayerIncludes.cppm` and `fw/debayerIncludesFW.h` spell `ENTRIES_PER_LINE_LOG2` and `PREPROCESS_GRID_WIDTH` as parenthesised expressions. `yaml/debayer_tb.yaml` adds the three sink params and their bindings, and `model/rgb_video_sink.cppm` gains the corresponding `using` declarations. `model/debayer.cppm` changes belong to steps 7 and 10, not to this step.

- **RULED ON BY THE ARCHITECT, 2026-09-05.** A block's Config carries exactly the parameters that block declares, and nothing else. Derived constants leave the Config and are computed in the implementation, the way SystemVerilog already computes them. In the architect's words: "debayer has 6 parameters. The config struct should just have those. The derived parameters should not be in the config struct, they should be available in the implementation as consteval's similar to how sv is done. Also block configs should be specific to the block." This closes the "separately decide" clause below and the §7 unknown that asked it.
- **Changes.** Compose a block's Config from the parameters the block names, by resolved constant identity, rather than from every parameterizable constant in the context. Four sites carry the context-wide rule and all four move together: `calcVariantConfigDescriptors` (`pysrc/processYaml.py:4068-4070`), its name-based `syntheticParams` test (`:4071-4073`), `getForeignConfigData` (`:1830-1839`), and `templates/systemc/config.py:136`. The Base class then computes each derived constant instead of aliasing it: `templates/systemc/baseClassDecl.py:216` emits `= Config::{name}` today and must emit the canonical expression, mirroring `parameterizedDeclLines` in `templates/systemVerilog/package.py:25-90`, whose `symSpelling` (`:56-61`) is the speller to copy. `constReference_cpp` (`templates/systemc/includes.py:96-100`) spells every parameterizable constant as `Config::NAME` including derived ones, and is the single site that puts `Config::ENTRIES_PER_LINE_LOG2` inside the shared context header's struct templates; it must spell a derived constant as its expression.
- **The declaration set is already correct and already mirrors SV.** `deriveParameterizedDeclSets` (`:5853`) selects, per block, the derived constants whose referent closure lies inside that block's own params; the check is `if not info['paramDeps'] <= params` at `:6053`. It persists `blockParameterizedDecls` at `:3939`, before `calcVariantConfigDescriptors` at `:3949`, so the input this step needs is already in hand and needs no reordering. `baseClassDecl.py` already walks that set in that order. Only the right-hand side changes.
- **Proves it.** A fixture in which two blocks share one config context and name different subsets, asserting at run time that each resolves only its own; plus the product tree still building, which is the real gate, because `raw_video_srcBase.cppm:46` consumes a derived constant today. **`examples/xprojParam/twoCtx` is that fixture and is already in the tree** — it must go from not-compiling to compiling, and its `params:`-order dependence and its bare-`uint32_t` degradation must both disappear (§5, B5). ~~Its testbench External is also still at the scaffold seed `--block=xpTwoCtxTop` and so elaborates a second copy of the DUT's children; every other `xprojParam` top has been retargeted at its `_tb` container, and this one must be too once it builds well enough to verify.~~ **DONE 2026-09-06**, see the fixture-half record above. Two corrections to that sentence: the seeded External held no instances at all under the current generator, so it never elaborated a second copy, and `inhVar`'s External is also still at its seed, so "every other" was wrong; `inhVar` is left alone here.
- **Blast radius. MEASURED 2026-09-05. VERIFIED BY EXECUTION.** Across the corpus, 34 databases carry a parameterizable block; 24 of them hold at least one block that loses a field under narrowing, 64 blocks in all, 222 field-losses summed per block, 154 of them derived. In `debayer` all seven parameterizable blocks share one context and one 22-member struct, so `model/debayerVariantConfig.h` emits five byte-identical structs today. Under the ruling the field sets become 6, 5, 6, 4 and 5.
- **The derived losses cost nothing, and this is the measurement that de-risked the step.** For every one of the 75 generated `*Base.cppm` files in the whole corpus, the union of a block's declared params and its `blockParameterizedDecls` constants covers every `Config::X` name that file spells. Zero uncovered. So the Base classes already assume the per-block closure this step implements; moving the derived constants to computed lines changes their spelling, not their availability.
- **The product tree's entire exposure is one hand-written file.** `model/rgb_img_writer.h:19-23` reads `Config::HORIZONTAL_SIZE`, `Config::VERTICAL_SIZE` and `Config::DEBAYER_ALGORITHM`, and is instantiated as `rgb_img_writer<Config>` at `model/rgb_video_sink.cppm:81`, while `rgb_video_sink` declares only `BITS_PER_PIXEL_COLOR` and `PIXELS_PER_CLOCK`. It compiles today only because the Config is over-inclusive. **The architect's disposition:** the sink is a peer of `debayer`, not part of its hierarchy, and inherits nothing from it; it should declare whatever its own abstraction needs, reusing the same `ipParameters` the feature exists to support, and should not carry parameters it does not use. So the three go on `rgb_video_sink`'s `params:` list. `model/b2p_deb_conv.h` reads only the four parameters `raw_video_src` already declares and is unaffected.
- **Gates Q3.** Until this lands, a block param whose name differs from its source constant is emitted as an extra synthetic Config member and the real constant keeps its default (§4.3, point 2).
- **Gates Case 1.** B5 is a **hard precondition** for a shared declaration consumed only from other files (§2, D2), because a two-context block is exactly what Case 1 produces.

### Step 4 — B3: `foreignConfigModules` in the testbench External. LANDED 2026-08-14; GATED by `make xproj-depth`

**This step is CLOSED. It previously read open here while §5, B3 recorded the same change as fixed with a live gate; the contradiction was stale text in this section, not an unfinished step. Re-verified 2026-09-04.**

- **Changes, as landed.** `ext_module_export` (`templates/systemc/testbench.py:264-268`) calls `sc_instance_config_imports` (`pysrc/intf_gen_utils.py:424-436`), which iterates `data['foreignConfigModules']`, under the same `_ext_holds_peers` guard the rest of the peer-facing region uses. §5, B3 records two further gaps in the family that landed with it, both unreachable by any fixture in the corpus.
- **Proves it.** ~~Remove `cstBind`'s wrapper so the cells sit directly under `xpCstBindTop`, and require `make xproj-const` to build and run.~~ That proof was vacuous, because the `xprojParam` testbench Externals were retargeted at their `_tb` container (`--block=<X>_tb --excludeInst=u_<X>`) and `cstBind`'s External names no foreign Config either way. **The replacement gate is `examples/xprojParam/dpTop`'s `xpDpTbPeer`**, which is what the requirement stated here asked for: a block whose Config is foreign, sitting in the External's own instance set as a sibling of the DUT inside `_tb`. It is instantiated twice at assembler-declared variants (`yaml/xpDpTop.yaml:96-97`), runs under `make xproj-depth`, and that target is in `pipeline-test` (`Makefile:468`).
- **The gate is not vacuous, established read-only.** `tb/xpDpTop/xpDpTopExternal.cppm:36` names `xpDpTop_xpDpTbPeerPeerConfig` and `:20` imports `xpDpTop.xpDpTbPeer.config`. That module interface unit (`registrar/xpDpTop_xpDpTbPeerVariantConfig.cppm:9-11`) is the struct's only definition site, and no other import supplies it: the sole Config header the External includes does not carry it, and `xpDpTop_xpDpTbPeer.base` declares the Base as a class template over `Config` and so never names it. Under C++20 module rules, dropping that import leaves the name undeclared. `dpTop` is the only External in the corpus that imports a `.config` module.
- **Blast radius.** Additive imports on one generated file kind. Regeneration leaves the tracked External byte-identical.

### Step 5 — B2: a structure declared over an included constant. LANDED 2026-09-07

- **As landed.** The additive view field is `sampleConfigConstants` on `getContextData`, built by `projectOpen._sampleConfigConstants`: the context's own parameterizable constants, then each structure's persisted base-parameter closure (`STRUCTUREPARAMDEPS`, written by `deriveParameterizedDeclSets` from the per-structure `paramDeps` it already computed, sorted). `_sampleConfigs` (`templates/systemc/structures.py`) and `configStructLines` (`templates/systemc/config.py`) read it; `ret['constants']` is unchanged. **Fault-injected, VERIFIED BY EXECUTION:** the `cstBind` Inc pair now carries its own payload `csIncSt` over the included `CS_PIXEL_WIDTH`; on the un-fixed generator its rundir build failed with `fatal error: no member named 'CS_PIXEL_WIDTH' in 'xpCstSupTestConfigDefault'`, and after the fix `xproj-const` runs clean with `CS_PIXEL_WIDTH` in all three sample Configs. A first version walked structures at open time from a per-constant blob and iterated sets; review found the member order non-deterministic for a context reaching two included constants, and the persisted sorted per-structure closure replaced it (three identical runs on a two-constant scratch copy). Emitted-output delta across `examples/xprojParam/*`, `ip_test`, `simple_ip`, `mixed`, `xif` (583 files): one file, `cstBind/model/xpCstSupIncludes.cppm`, plus the `cstBind` files the fixture change itself regenerates. Product tree: zero. Unit suite 116 of 116. The stale "does not compile" prose in `xpCstSup.yaml` and `examples/xprojParam/README.md` is rewritten.
- **Gates after steps 2 and 5, 2026-09-07, VERIFIED BY EXECUTION.** `make clean && make pipeline-test -j` exit 0, 64 "No error", zero `ERROR:` lines, both asserted rejections (`varUniqBad`, `cpLayoutBad`) printed their OK lines. The combined log shows five `make[1]: *** Deleting file` lines rather than two: three are the leading `make clean`, whose per-example clean builds the db to read the manifest and so trips the three rejection fixtures (`cpLayoutBad`, `mtxBare`, `varUniqBad`) once each; pipeline-test itself contributes exactly two. Product tree: `make clean && make gen -j && cd rundir && make -j && ./build/run debayer --verbosity=medium` exit 0, two "No error", `test_debayer_structs` executed. Unit suite, run after pipeline-test finished: 116 of 116, no count warning.

- **Root cause, traced 2026-09-05.** `_sampleConfigs` (`templates/systemc/structures.py:1593-1594`) builds the sample Config from `data['constants']`, which `getContextData` (`pysrc/processYaml.py:1115-1116`) filters on `value['_context'] in contexts`, the file's own `--context` tokens. The include chain is computed two lines earlier into `ret['includeContext']` and then not used for this filter. So the sample Config can only ever carry constants declared in that one file. A real block's Config does not have this problem, because `configContext` (`:5743-5763`) resolves through the include chain to the file that owns the parameterizable declarations.
- **Take the first option, not the db-time refusal.** The shape being refused is not broken. It already resolves correctly for a real block's Config, so a db-time rejection would forbid a legal authoring pattern to work around a shortcut in one self-test generator, and would make the same reference legal for a block and illegal for a bare structure.
- **The new field must be additive.** Sourcing the sample Config only from constants the context's structures reference would silently drop any parameterizable constant in the context that no structure names, which is an unmeasured emitted-output delta. Take the union of the context's own parameterizable constants and the referenced ones wherever declared. Widening `ret['constants']` itself is not an option: `templates/systemc/includes.py:56-58` emits literal declarations from that same dict, so a wider filter would re-declare constants the included file already exports.
- **Sequencing note.** Step 3 changes `constReference_cpp` (`templates/systemc/includes.py:96-100`) so a derived constant spells as an expression over `Config::<param>`. A test structure whose width names a derived constant therefore needs the sample Config to carry that constant's referent parameters. Do step 5 after step 3 and the union rule above covers both.
- **Proves it.** Give `cstBind`'s Inc blocks a payload of their own, which the fixture cannot do today, and require the build to succeed.
- **Blast radius. MEASURED 2026-09-05: zero in the product tree.** A query for a struct field whose width-backing constant is declared in a different file than the structure returns 0 rows in both `debayer.db` and `isp_shared.db`, and 0 rows again for `arraySizeKey`. `isp_shared` has no parameterizable types at all. The defect is confined to the `testStructsCPP` section, which is reachable only from `structTest()` (`templates/systemc/structures.py:1615-1667`) and has no other call site, and its only live instance is the deliberately-constructed `xprojParam` fixture.

### Step 6 — Promote the probe and close the RTL coverage gap. HALF LANDED; DEPENDS ON step 1

- **Changes.** ~~Move `cstUse` from `xproj-const-probes` into `xproj-const`~~ **DONE with step 1**; `xproj-const-probes` is deleted, having no cells left. Still to do: add an **RTL-bearing** cell to the family, because the SystemVerilog consequence of B1 is the most serious and is covered by nothing: all eight affected blocks in both trees are `hasRtl: 0` (measured, §5 B1), and the `cst` family declares `hasRtl: false` throughout.
- **Proves it.** The new cell's generated package or module-local declaration must spell the **module parameter name**, not the constant's default literal; fault-inject by reverting step 1's change to `templates/systemVerilog/package.py:46` and confirm the cell fails.
- **Redirected 2026-09-07, after the dpMid attempt below did not discriminate.** A type width is spelled by `typeWidthExpression_sv`, which goes through `emissionUtils.typeWidthExpr` (`pysrc/emissionUtils.py:124-126`) and returns the constant's bare declared name; it never consults `paramNameByKey`. Only two emissions do: an eval-derived `localparam` right-hand side (`emitSvCanonical`, `templates/systemVerilog/package.py:88`) and a structure member's `arraySizeKey` (`:66-67`). So the B1 SystemVerilog consequence is confined to those two, and `dpMid`'s `typedef logic[DP_WIDTH-1:0]` is right by the same-name rule, not by step 1. **Fault-injected and observed**: with `paramNameByKey` keyed on `paramKey`, `xproj-depth` still exits 0 and the typedef is byte-identical. The dpMid grep added to `xproj-depth` is kept as a pin of the type-width path, but it is not the step 6 gate. **The gate is `twoCtx`**: `xpTwoCtxDut` and `xpTwoCtxBare` are `hasRtl: true` and name the include-reached `DP_WIDTH`; a derived constant `DP_WIDTH_X2` over it, declared in `xpTwoCtx.yaml`, lands in both blocks' `localparam` sets, and `xproj-twoctx` greps for `localparam DP_WIDTH_X2 = DP_WIDTH * 2`. The `paramKey` injection must turn that into the literal `8 * 2`.
- **LANDED 2026-09-07. VERIFIED BY EXECUTION.** `examples/xprojParam/twoCtx/yaml/xpTwoCtx.yaml` declares `DP_WIDTH_X2: { eval: "$DP_WIDTH * 2" }`; with no other YAML change `rtl/xpTwoCtxDut.sv:22` and `rtl/xpTwoCtxBare.sv:21` carry `localparam DP_WIDTH_X2 = DP_WIDTH * 2;`, and `xpTwoCtxBare` asserts `DP_WIDTH_X2 == 24` at run time beside its existing asserts. `xproj-twoctx` greps both files for the symbolic line and fails otherwise. **Fault-injected**: with `paramNameByKey` keyed on `paramKey`, the target exits 2 at `ERROR: xpTwoCtxDut.sv did not spell the include-reached parameter DP_WIDTH on localparam DP_WIDTH_X2` (the emitted line read `8 * 2`, reported by the implementer; the ERROR line is in the retained log); the run-time assert changed to 25 fails on `xpTwoCtxBare DP_WIDTH_X2 did not derive from the bound DP_WIDTH`. Both restored; `git diff templates/systemVerilog/package.py` empty; `make xproj-twoctx -j` exit 0 with four "No error" (two from the depth family it runs first, two from twoCtx). The "No error" expectation of `pipeline-test` stays 64: the gate adds greps, not simulations. The `dpMid` typedef grep in `xproj-depth` stays as a pin of the type-width path. **This closes step 6.** The `cst` family stays `hasRtl: false`.
- **The premise is partly stale, found 2026-09-07.** "Covered by nothing" was true of the `cst` family and the product tree, but `examples/xprojParam/dpMid/yaml/xpDpMid.yaml:33` declares `params: [DP_WIDTH, MID_ALGO]` with `hasRtl: true`, and `DP_WIDTH` is reached by `include:` from `dpLeaf`. Its emitted `rtl/xpDpMid.sv:20` reads `typedef logic[DP_WIDTH-1:0] dpPixelT;`, the module parameter, which is exactly the artefact this step asks a new cell to produce. Two gaps keep the step open: `xproj-depth` runs `make gen` on `dpMid` and asserts nothing about the spelling, and no target elaborates that RTL (every `dpTop` block is `hasVl: false`, and `make lint` is unusable, §8). **Recommended, not decided:** close the step with a grep gate on `dpMid`'s emitted RTL inside `xproj-depth`, plus the `paramKey` fault injection, rather than authoring a new RTL cell in the `cst` family.

### Step 7 — D7: parameter-scoped inheritance expressed in the variant. DECIDED 2026-08-13; HALF BUILT 2026-08-14

Answers §5, B6. The decision, its rulings and the spelling are at §2, D7; the authored YAML, the emitted shapes and the authoring rules are [`design-parameter-inheritance.md`](./design-parameter-inheritance.md); this step is the work. **The step is split so that the built and the unbuilt halves are distinguishable.**

- **Measured before the decision, on the mixed case. VERIFIED BY EXECUTION.** A container that declares some of its child's parameters and not others emits **a parameter list of exactly what the container declares**, forwards those as **symbols**, emits the non-declared child parameter as a **literal**, and **elaborates under Verilator at exit 0**. The whole-Config form does **not** elaborate. That contrast is why D7 is parameter-scoped rather than Config-scoped.
- **Measured: the migration pays for itself on the layout side.** Migrating the product tree onto the new rule **restores layout adjudication on two connections that are excluded today**.
- **Sequencing constraint, load-bearing, and it belongs to step 7b.** The merged bindings must exist as **DATABASE ROWS before the layout pass**, or the gate stays blind to exactly the divergence D7 exists to catch.
- **Blast radius. NOT MEASURED**, for either half.

#### Step 7a — the declaration surface, the validators and SystemVerilog. BUILT AND MEASURED, 2026-08-14; GUARDED 2026-08-18

Present in the working tree and exercised on `examples/xprojParam/{dpLeaf,dpMid,dpTop}`. The sites and the diagnostics are in the implementation record below.

- **Landed.** The variant schema's `containerParam:` per-parameter form; the declaration-time exclusivity and presence checks; **the site-time validator `validate_container_sourced_params` (`pysrc/processYaml.py:5374-5493`)**, with its container-existence, container-parameter-existence and domain-relation diagnostics (the single-level-reach diagnostic is reachable only through `containerBlock` and goes with it, §2 D7.2); SystemVerilog emission forwarding the container's symbol for a container-sourced parameter. `_post_validateVariantParameterCompleteness` needed **no change** — it compares the block's `params:` against the set of binding rows, and a container-sourced row is a binding row.
- **Measured.** `make db` and `make gen` clean on all three fixture projects; the chain persisted as a chain rather than flattened; the emitted `xpDpMid` forwarding `.DP_ALGO(MID_ALGO)` where the pre-design shape was rejected by Verilator; **Verilated runtime parameter values through two levels** (`MID_ALGO=5, DP_WIDTH=8` giving `LEAF_DP_ALGO=5 LEAF_DP_WIDTH=8`; `6, 20` giving `6, 20`, neither being the declared defaults of `1` and `8`); and the three reuse dispositions of D7.1.
- **The status text this step carried until 2026-08-14 was WRONG about the validator.** It read "**ASSESSED, NOT BUILT.** Three pieces were reasoned through and not implemented: the merged-Config synthesis; the identity-keyed site-time validator; and the layout-gate extension", and the status header read "Step 7 (D7) is decided and not started". The validator is built and measured. It is also **not identity-keyed**: it checks **compatibility**, not identity (§2, D7.1). The other two pieces became step 7b; the layout gate landed 2026-08-17 and only the superseded merged-Config synthesis remains unbuilt, deliberately so (it was ruled wrong and replaced by the templated Config of step 7c).
- **GAP CLOSED, 2026-08-18. This half is a gate.** Both halves of the recommendation this bullet carried are met. The `make` half landed 2026-08-17 — `xproj-depth` runs the `dp` family's three projects and `dpTop`'s model, `xproj-inherit` runs `inhVar` and `xproj-container-layout` runs both `cpLayout` arms, all three in `pipeline-test` (`Makefile:463`) — so the entry's premise that the family sat in no target was **already false when it was last edited**. The unit half is `unittest/test_container_param_inheritance.py`: the D7.1 rejection (container `maxValue` wider than the child's, asserting the diagnostic names the instance, both backing constants and both bounds) and one forwarding acceptance (differently-backed equal domains, whose emitted Config template is **compiled and run** to prove the child resolves to the value the container binds, and whose emitted SystemVerilog forwards the container's symbol). The bound value (5) is neither declared default (child 1, container 2), so **the compile-and-run cell** cannot pass on a fallback to either; the SystemVerilog cell asserts a symbol and pins no number, so it is guarded instead by the two constants being deliberately named differently, which also defeats a resolver matching on spelling. **Each cell was observed failing** with its behaviour disabled: the domain check suppressed, `_descriptorMemberLines`' container arm suppressed (reproducing the invalid `= ;` member), and `_resolveSvInstanceParams`' container arm suppressed. Each injection was reverted and the product tree re-regenerated to a byte-identical 1124-file checksum, so the reverts are known exact.

The suite is registered in both runners. **The guard literal in `run_all_tests_parallel.sh` moves 95 → 103, of which only the last step is this change's.** Two facts that a bare "+1" would hide: the committed guard read **95 against 96 committed suites**, so it was already stale by one and would have warned; and the working tree had reached **102** through six unrelated uncommitted suites before this one, so the closeout's own contribution is 102 → 103.

#### Step 7b — the C++ Config path (BUILT 2026-08-14, as a TEMPLATED Config) and the site-keyed layout gate (BUILT AND GUARDED 2026-08-17)

- **The C++ Config path is BUILT, and NOT in the shape this step originally proposed.** The per-site merged struct recorded below was **ruled wrong by the architect on 2026-08-14** and is superseded; the built shape is a Config **templated on the container's Config**. The reasoning and the full implementation record are at "Step 7c" below. What this bullet retains is the defect it opened on: the emitted artefact for a container-sourced parameter used to be invalid C++ — `examples/xprojParam/dpMid/registrar/xpDpMid_xpDpLeafVariantConfig.cppm:12` contained `static constexpr uint32_t DP_ALGO = ;` (**MEASURED**, before the fix). It now contains a struct template whose member reads `ContainerConfig::MID_ALGO`, and the fixture's model builds, links and runs.
- **The superseded proposal, recorded so it is not reproposed.** "Synthesise one plain struct of resolved literals per (container variant instantiated × child instance)." **REJECTED (architect, 2026-08-14):** a per-site struct is emitted per consumer configuration, so if the emission belongs to the vendor IP the vendor must be regenerated whenever a consumer adds a configuration, and an IP that changes when its consumers change is not reusable. It also diverges from the SystemVerilog, which forwards a **symbol** (`.DP_ALGO(MID_ALGO)`), not a literal.
- **The site-keyed layout gate is BUILT (2026-08-17).** `variantValueBindings` used to resolve bindings per **declared** variant; a container-sourced binding has no value there, so the row was skipped and the parameter fell back to its backing constant's declared default. The resolution is now **site-correlated**: both ends of a junction are instances in the same container, so one container configuration resolves both together, and the walk recurses because a container's own parameters may be container-sourced in turn. A junction with no container-sourced parameter on either side is adjudicated exactly once, as before, so nothing that does not inherit changes shape.
- **The before/after, quoted, on one fixture.** `examples/xprojParam/cpLayout` is the accepting arm — container `CP_BUS_W: 16`, sibling leaf bound to the literal `CP_WIDTH: 16`, leaf sourced from the container as `CP_WIDTH: {containerParam: CP_BUS_W}`, identical in truth. (**CORRECTED 2026-08-18:** this bullet read "container `CP_WIDTH: 16`", which erased the deliberate name difference the bullet below relies on; `CP_WIDTH` is the leaf's parameter, `CP_BUS_W` the container's.) Both constants' default is deliberately `8`, so a fallback to either is visible as a wrong number rather than passing by coincidence.
  - **Before**, `make db` exit 2: *"parent field 'data' has `_bitWidth 8` at bit offset 8 ... while child field 'data' has `_bitWidth 16` at bit offset 8"*, resolved for block `xpCpLeaf` at variant `use`. The `8` can only be the declared default.
  - **After**, `make db` exit 0.
- **The gate still catches a REAL mismatch, which matters more.** `examples/xprojParam/cpLayoutBad` is the same shape with the container moved to `24` while the sibling stays at the literal `16`. It is rejected **both** before and after, so the fix did not buy acceptance by ceasing to check — but only after the fix does the diagnostic name the true value: *"parent field 'data' has `_bitWidth 24` ... while child field 'data' has `_bitWidth 16`"*. Before the fix the same junction was rejected reporting `_bitWidth 8`, the declared default. `24` appears nowhere in the leaf's own declaration and can only have been reached through the container, so the number itself is the evidence that resolution is per site.
- **Guarded, not merely measured.** Both arms are the `xproj-container-layout` target, which is in `pipeline-test`. The target asserts the accepting arm's `make db` succeeds, asserts the rejecting arm's `make db` fails, **and** greps the rejection for `_bitWidth 24`, so a gate that rejected for the wrong reason — or at the stale default — fails the target. Running the target against the pre-change generator fails with exit 2, so the guard is known to bite.
- **A container-sourced parameter may now be used in a layout.** The prototype restriction recorded against this step is retired. **The authoring document's copy of that restriction outlived it by a day and was removed 2026-08-18**, along with the framing it justified: [`design-parameter-inheritance.md`](./design-parameter-inheritance.md) had declared itself "a design statement rather than authoring guidance for a shipped feature" on the strength of this gap plus the missing build target, and both are now closed. It is retitled as an authoring guide, and its §5 lists what is genuinely not covered — the cross-level register-bus router junction below, `valueType`, and B5's Config field set.
- **Where the correlation lives.** `SiteBindingIndex.junctionBindings` is the single place that decides which configurations a junction is checked at, and it is deliberately the only one: the first implementation resolved the two sides from independent enumerations at two of the three call sites, which paired one end's configuration with the other's. Two shapes exist — the parent side IS the container (a channel typed by the assembling container, and every `connectionMap` up side), where the container's own resolved values are what the child inherits; or both ends are siblings within it, where one of the container's configurations resolves both.
- **KNOWN LIMITATION, deliberate: the cross-level register-bus junction is not site-resolved.** `config/postParseRegisterPorts.py` compares a nested router against its parent router, and `_findRouterParent` returns the router serving the container of the block the nested router sits in — so the two are **one level apart, not siblings**. Correlating them needs the parent's configuration resolved, then the intervening block's from it, then the nested router's: a two-level walk this pass does not do. Both sides are therefore resolved from their declarations, exactly as before this step, so an inherited parameter on a *router* still falls back to its constant's default there. This is not a regression and it is commented at the call site; it is the remaining piece if register-bus routers ever take inherited widths.
- **Coverage the guard does NOT reach**, recorded so it is not assumed: the container-fallback parent side (a junction where no end is elected because every end's declared interface differs from the connection's), a multi-level inheritance chain on a *layout* parameter, and the cross-level router junction above. `cpLayout` covers the elected-sibling path with a single-level chain. Both arms deliberately name the container's parameter `CP_BUS_W` and the leaf's `CP_WIDTH`, so a resolver that looked up the wrong name — or crossed the two ends' configurations — fails rather than passing on a coincidence of spelling.
- **`inheritContainerParam` migration is unblocked by 7b.** An inheriting endpoint is still excluded from layout adjudication by the separate `inheritContainerParam` skip in the connection loop; that exclusion is now the only thing standing in the way, and the resolution machinery the migration needs exists.

#### Step 7c — the templated Config. BUILT AND MEASURED 2026-08-14; GUARDED (`xproj-depth` 2026-08-17, unit cell 2026-08-18)

**The ruling.** The C++ shape §3.1 of the design specification carried was wrong. Verbatim: *"looking at the design doc, I think the C++ shape is wrong, and its part of this change. we want the config to be templated by the parents config. The shape shown is based on the current design, otherwise any time the customer declares a new variant the ip will need modification"*. The specification was corrected the same day; this is the implementation.

**The shape.** A declared variant that sources any parameter from its container emits a class template over the container's Config; a variant every one of whose parameters is bound emits the plain struct it emits today. The rule deciding the form is exactly "does this variant carry a container-sourced binding", read off the descriptor. The template parameter is spelled `ContainerConfig` and is unconstrained: any Config carrying the named members satisfies it, and a missing member is a compile error naming it.

```cpp
export template<typename ContainerConfig>
struct xpDpMid_xpDpLeafCustomerConfig {
    static constexpr uint32_t DP_ALGO  = ContainerConfig::MID_ALGO;
    static constexpr uint32_t DP_WIDTH = ContainerConfig::DP_WIDTH;
};
```

Every site that names such a Config spells it applied to the container's own `Config`. That is always legal, because a container that declares the sourced parameter necessarily declares `params:` and is therefore a class template — the site-time validator already guarantees the declaration.

**Where the behaviour lives.**

| Piece | Site |
| :-- | :-- |
| `containerSourced` on the per-variant descriptor: `{childParam: containerParam}`, empty for a fully bound variant | `calcVariantConfigDescriptors`, `pysrc/processYaml.py` |
| Struct-versus-template opening line, and the `ContainerConfig::<param>` member RHS | `_descriptorStructOpen` / `_descriptorMemberLines`, `templates/systemc/config.py`, used by both the context-header and the registrar-domain module paths |
| `<Config>` applied at every use site (member, channel, thunker, cast target) | `cpp_config_struct_name`, `pysrc/intf_gen_utils.py` |
| ~~Maker template the container calls~~, and suppression of the registration that can no longer name a concrete type | `templates/systemc/blockRegistrar.py` |
| ~~Maker argument~~ implementation-type template argument at the child's `createInstance` | `templates/systemc/constructor.py` |
| Container-supplied constructor, used when the exact key resolves to no registration | `instanceFactory::createInstance`, `common/systemc/instanceFactory.{h,cpp}` |
| ~~Registrar-module import the container needs to name the maker~~ child block-module import the container needs to name the implementation class | `containerTypedChildModules` (`getBDInstances`) and `sc_class_dependency_includes` |

**The maker mechanism is SUPERSEDED, 2026-08-17.** See "Supersession: one framework template replaces the generated makers" below. The rows above are kept as the record of what the shape was; the strikethroughs mark what no longer exists.

**How the string-keyed factory composes with a dependent type — the expectation this refutes.** The expectation on entry was that the concrete instantiation is registered as a per-design fact in the **consumer's** registrar domain, while the Config template is a per-IP fact owned by the vendor. **REFUTED, and the refutation is the load-bearing finding.** Two independent reasons:

- **The consumer cannot write into the vendor's registrar file.** `systemcGen` resolves each file's owning project from its `GENERATED_CODE_PARAM` line and returns without rendering when the owner is not the current project. The consumer runs the generator over the vendor's registrar-domain files (they are in its manifest) and writes nothing. So any content that varies with the consumer's design cannot live there — which is also **why the vendor's files are byte-identical after the consumer adds a variant**.
- **The factory key has no Config dimension.** It is `(blockType, variant, projectName)`. Two instances of one container at two Configs create the same child block at the same variant under the same project name, so one key would have to resolve to two distinct C++ types. Inventing a fourth key dimension (a Config identity string, e.g. `typeid`) was assessed and **rejected**: it makes every consumer enumerate the concrete instantiation chains of a design it did not author, and it needs a registrar file scaffolded in the consumer's domain for descendants the consumer never names.

**What was built instead.** The concrete instantiation is registered **nowhere**. The container passes the constructor for the type it needs, as a maker template exported by the child's own registrar module and applied to the container's `Config`:

```cpp
// the vendor's registrar module, emitted once
export template<typename ContainerConfig>
std::shared_ptr<blockBase> xpDpMid_xpDpLeafCustomerMaker(const char * blockName, const char * variant, blockBaseMode bbMode)
{ return ... std::make_shared<xpDpLeaf<xpDpMid_xpDpLeafCustomerConfig<ContainerConfig>>>(...); }

// the container, at the site
uLeafA(std::dynamic_pointer_cast<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>>(
    instanceFactory::createInstance(name(), "uLeafA", "xpDpLeaf", "customer", "xpDpMid",
                                    &xpDpMid_xpDpLeafCustomerMaker<Config>)))
```

Three properties follow, and they are the reason this shape was chosen:

- **The vendor emits it once**, parameterized, with no knowledge of any consumer. C++ instantiates it per concrete container Config.
- **The child's implementation class stays out of the container's translation unit.** Construction happens in the registrar module, which is the TU that already owns it.
- **Substitution is unchanged.** `createInstance` uses the supplied factory only when the key resolves to no registration, so a registered replacement still wins, and every other child's path through the factory is untouched.

The registration a container-sourced variant would have carried is **suppressed** in the registrar, because there is no concrete type to name. A registrar whose only variant is container-sourced emits an empty trampoline body.

**A defect this exposed, fixed here, and separable from the shape.** A project's registrar registered variants bound by instances **outside this build's design tree** — a referenced child project's own standalone harness, parsed into the same database but never built here. The consumer then instantiated the container at the block's context default Config, which does not carry the block's synthetic `params:` members, and the build failed with `no member named 'MID_ALGO' in 'xpDpLeafDefaultConfig'`. The instance-bound variant set (`getBDInstances`) is now restricted to `reachableInstances`, the same filter address emission already applies. Nothing this drops can be created by the build: an instance the design reaches is reachable by construction.

**Measured, 2026-08-14. VERIFIED BY EXECUTION.**

- **The vendor does not move when the customer adds a configuration.** Two full cold regenerations of all three projects (`make clean`, `make newmodule`, `make gen`), one with the customer declaring two configurations of the mid-level IP and one with three (`customer3`, `MID_ALGO: 7`, with its own instance, checker variant and connections), both on the final generator. All emitted files under `dpMid/` and `dpLeaf/` are **byte-identical, 0 changed**; only the customer's own project moves. Re-measured on the corrected fixture with a fourth configuration (`customer4`, `MID_ALGO: 4`, with its own instance, checker variant and connections): 73 files, aggregate MD5 `5f4a85341327a6c0b31b5eac07c1b514` before and after a cold regeneration of all three projects, and the fixture restored to byte-identical afterwards.
- **The model builds, links and runs — the first time on this fixture.** `make -C examples/xprojParam/dpTop/rundir -j all` exit 0; `make -C examples/xprojParam/dpTop/rundir run` exit 0, "No error".
- **Three configurations resolve independently at the nested leaf**, two project levels below the value: `uWrap.uMid.uLeaf{A,B}` at algorithm **5**, `uWrap.uMid2.uLeaf{A,B}` at **6**, `uWrap.uMid3.uLeaf{A,B}` at **7**, each checked against a checker configured from an independent path through the generator (`uChk` / `uChk2` / `uChk3` "checked 4 samples at algorithm 5 / 6 / 7").
- **`ContainerConfig::` chaining composes through two levels**, consistent with the single-level authoring rule: the leaf of the first chain is instantiated at `xpDpMid_xpDpLeafCustomerConfig<xpDpTop_xpDpMidCustomerConfig<xpDpTop_xpDpWrapCustomerConfig>>`. Each link is authored single-level; the composition is C++'s.
- **Both forms coexist in one emitted module**, which is the rule in one artefact: `xpDpTop_xpDpMidCustomerConfig` is a template (inherits `MID_ALGO`), `xpDpTop_xpDpMidCustomer2Config` beside it is a plain struct (`MID_ALGO = 6`).
- **The mid-level IP still builds standalone.** `make -C examples/xprojParam/dpMid/rundir -j all` exit 0. Its `run` aborts on "Premature end of test" because that project's own driver and sink are empty scaffolds — a fixture gap, not a build one.

**Two fixture-local facts, recorded because they are not this shape's doing.**

- ~~`dpTop`'s testbench External names the DUT's assembler-declared Config and the generated import set omits the registrar-domain config modules (**B3**, step 4). The import is stated by hand in the External's user region, with a comment naming B3.~~ **No longer applies.** The External was seeded at the DUT (`--block=xpDpTop`) rather than retargeted at the `_tb` container, which is why it named the DUT's Config at all — and which also made it elaborate a second, disconnected copy of the whole chain under `tb.external.*` while the run still reported `No error`. Retargeted at `--block=xpDpTop_tb --excludeInst=u_xpDpTop`, the External holds no instances, names no Config, and the hand-written import has been removed.
- `uLeafX` — the same leaf variant instantiated directly by the customer rather than through the IP — still resolves to the leaf's **default** Config and stamps algorithm 1. That is the descriptor-selection gap already recorded in the fixture README (a variant declared by an intermediate project is not selectable by a third project's instance), unchanged and untouched here.

**Still owed.** ~~The regression guard of step 7a covers this half too: the `dp` family is in no `make` target, so every measurement above is a recorded run rather than a gate.~~ **Closed.** The family is now the `xproj-depth` target and is part of `pipeline-test`; the guard is the checkers' per-sample assertion that each nested leaf resolved the algorithm its own Config declares, and it has been observed failing (perturbing `xpDpWrap.customer.MID_ALGO` from 5 to 4 fails the target with "the customer declared the leaf at algorithm 5 but the leaf resolved 4"). The site-keyed layout gate (step 7b) **has since landed, 2026-08-17**: a container-sourced parameter that appears in a **width** is now inside the layout comparison, resolved at the value its site actually binds.

#### Supersession: one framework template replaces the generated makers, 2026-08-17

**Decision.** The per-`(parent, child, variant)` maker function template is removed. A container names the child's implementation class as an explicit template argument of one framework-side `instanceFactory::createInstance<Impl>`:

```cpp
// common/systemc/instanceFactory.h - emitted nowhere, written once
template<typename Impl>
static std::shared_ptr<blockBase> createInstance(const char * hierarchy, const char * blockName,
                                                 const char * blockType, const char * variant,
                                                 const char * projectName)
{ return createInstance(hierarchy, blockName, blockType, variant, projectName,
      [](const char * n, const char * v, blockBaseMode m) { return ... std::make_shared<Impl>(n, v, m); }); }

// the container, at the site
uLeafA(std::dynamic_pointer_cast<xpDpLeafBase<xpDpMid_xpDpLeafCustomerConfig<Config>>>(
    instanceFactory::createInstance<xpDpLeaf<xpDpMid_xpDpLeafCustomerConfig<Config>>>(
        name(), "uLeafA", "xpDpLeaf", "customer", "xpDpMid")))
```

**Why.** The finding the maker was built on is unchanged and is the reason this works: **the factory key cannot carry the type.** `(blockType, variant, projectName)` has no Config dimension, so it can name only one member of what is, for a container-typed child, a FAMILY of C++ types. What the maker got wrong was the vehicle: it made the type travel through a GENERATED function whose name, module and qualification all had to be invented and kept in step across three templates and a view. The type can travel as a template argument instead, and the container already spells it — it is the same type the `dynamic_pointer_cast` on the same line demands. One framework template serves every combination; nothing is emitted per pair.

**What this restores.** Substitution by registration. Under the maker the site-supplied constructor was consulted FIRST and a colliding registration was reported as an error, so a container-typed child could not be replaced at all. The keyed lookup for the site's own `(blockType, variant, projectName)` now runs first and wins; the site-named type is the fallback. Proven by execution: a registration planted under the exact key is used at all four container-typed sites of `examples/xprojParam/inhVar` in preference to the type the sites name.

**One property the maker had is deliberately given up.** "The child's implementation class stays out of the container's translation unit" no longer holds — naming `Impl` instantiates the child's class template in the container's TU. That was never a stated requirement, and the container already imported the registrar module which imported the child's block module, so the module graph is net-zero: `import <parent>.<child>.registrar` becomes `import <child>.block`.

**Both inheritance mechanisms now take one path.** `inheritContainerParam` (whole-Config inheritance) is the same structure and never got the maker: it was resolved through the key, registered against the CHILD's `defaultConfig`. Its site now emits `createInstance<preprocess<Config>>(...)` and the wrong registration is deleted rather than patched.

**The `inheritContainerParam` default-variant bug is FIXED.** Recorded above at §5 B3b and again as "A latent hazard confirmed" — the container's cast is on `Config` while the registrar hard-coded the child's default Config, which coincide only when the container is at the variant whose struct happens to spell that default. `debayer` is safe only because it declares exactly one variant, named `default`, of a block whose name matches its context stem.

- **Gate: `make xproj-inherit`**, in `pipeline-test`. `examples/xprojParam/inhVar` is one container block instantiated at TWO variants (`default`, `alt`), each holding two `inheritContainerParam` leaves, each chain checked per sample against a checker configured from an independent path.
- **BEFORE (generator as it stood): SIGSEGV.** `xpInhCont<xpInhContAltConfig>::xpInhCont` at `model/xpInhCont.cppm:72` (`uLeafA->in(this->contIn)`) with `this=0xa0`: the registration produced `xpInhLeaf<xpInhContDefaultConfig>` and the cast to `xpInhLeafBase<xpInhContAltConfig>` yielded null. The `default` container constructed first and correctly; only the second variant failed.
- **AFTER: exit 0.** `uContDef.uLeaf{A,B}` resolve algorithm 1 and `uContAlt.uLeaf{A,B}` resolve 6, each asserted per sample.

**A model registrar TU with nothing to register is no longer emitted.** A child every one of whose bindings under a parent is container-typed contributes no model registration, so the trampoline would hold only its module preamble. The persisted pair record gates the scaffold through `requiresRegistrations: true` on `blockRegistrar`. A `hasVl` child still gets the separate pair-qualified VL registrar and concrete wrapper tops. Removed from the corpus: `examples/xprojParam/dpMid/registrar/xpDpLeafRegistrar.cppm`, and in the product tree `registrar/preprocessRegistrar.cppm` and `registrar/interpolateRegistrar.cppm`. Nothing imports a registrar module for its own sake — the only three importers in the corpus imported it to name a maker.

**What was NOT removed, and why.** The mode gate in `instanceFactory::createInstance` (the site-supplied constructor is dropped when `instMode` is neither empty nor `model`) was proposed for removal on the grounds that it existed only because the maker and the key answered different questions. **Measured, and the proposal is wrong.** The site-supplied constructor names the MODEL class in every case; it can answer no other mode. With the gate removed and `--vlInst` naming a container-typed child of a `hasVl: false` block, the keyed lookups for `xpInhLeaf_verif` both miss, the model constructor is taken and the run completes with exit 0 and "No error" — a silent model where a verilated child was asked for. With the gate in place the run stops on `Attempted to create an instance uLeafA of an unregistered block type xpInhLeaf_verif`. The gate stays, with its comment rewritten to state the model-only reason rather than the ordering one. The collision assert, which DID exist only because of the ordering, is removed.

**`containerSuppliedFactory` also stays** on both non-template `createInstance` overloads: `createInstance<Impl>` is its one remaining caller and forwards through it.

**One thing the deleted collision assert was catching, now caught at db-create.** With keyed-first, a registration under the site's exact key silently replaces the site's type. For an `inheritContainerParam` site the emitted variant is always empty, which is the SAME key an instance naming no variant resolves — so a child reached both ways would hand the inheriting container a child built at the child's default Config, and the generated cast would yield null with no diagnostic. Under the maker the assert reported it. `validate_inherit_container_params` now rejects the pair at db-create, rule (f), naming both sides:

```
instance uLeafA in file .../xpInhCont.yaml: inheritContainerParam child block 'xpInhLeaf'
is also instantiated without a variant by ['uLeafPlain']; both resolve the same factory
key, which cannot carry two different Configs. ...
```

Measured by adding such an instance to `inhVar`: `make db` exits 2 with that message. Nothing in the corpus or the product tree authors the shape, so the rule rejects nothing that exists. A container-sourced site emits no model registration under its child label. Its VL registration uses the parent label and the concrete nested Config recorded for that pair.

**The empty-variant registration is asked for by a site, not inferred from the absence of labels. FIXED 2026-08-19.** `getRegistrarConfigView` (`pysrc/processYaml.py:1751-1762`) decides the empty-variant registration from whether any reachable keyed instance actually asks for it. Before, a container holding one variant-bound and one variant-less instance of the **same** parameterized child emitted registrations for the bound labels only, and the variant-less site aborted elaboration in `common/systemc/instanceFactory.cpp` on an unregistered block type: the keyed lookup missed, no container-supplied factory answers for a plain child, and the empty-variant fallback repeated the same miss. Fixed on both paths — the model trampoline (`templates/systemc/blockRegistrar.py`) and the verilated one (`templates/systemc/vlRegistrar.py`), the latter through its own view field `verifDefaultRegistration`, because `instanceFactory` nulls the container-supplied factory for every non-model mode and a verilated site therefore has nothing but the registration to find.

- **Retired gate: `unittest/test_registrar_default_variant.py`.** Step 8 rejects the variant-less parameterized-child shape that this suite authored. The suite and fixture were deleted on 2026-08-20. It is not a current failure or an open acceptance item.
- **`templates/systemc/constructor.py`'s equivalent branch (`:457-474`) is unreachable and was deliberately left alone.** That self-registration path returns early for a block with own params, so reaching its label-only arm needs a block declaring variants and no `params:` — the shape the third item below now rejects at db, so the arm is unreachable by construction rather than by coincidence.

#### Follow-up after the empty-variant fix, resolved 2026-08-20 through 2026-08-23

- ~~**No verilated DUT exists at a parameterized block's default parameters.**~~ **Resolved by step 8.** A params-declaring child must select `variant:` or `inheritContainerParam:`. The invalid variant-less shape no longer reaches wrapper generation.
- ~~**`_resolveSvInstanceParams` raises `KeyError` for a variant-less instance of a params-declaring child when the container declares no same-named parameter.**~~ **Resolved by step 8.** Database creation rejects the shape before SystemVerilog generation.
- ~~**A block declaring a variant that binds no parameters, with no `params:` of its own, passes `make db` and `make newmodule` and then fails `make gen`** with an unhandled `AttributeError` in `getBDInstances`, where the variant's `params` subtable is `None`.~~ **RESOLVED 2026-08-20 under the architect's ruling: rejected at db.** Reproduced first, on a minimal cell authoring nothing but the shape: `make db` and `make newmodule` both exited 0, then `make gen` exited 2 on `AttributeError: 'NoneType' object has no attribute 'items'` in `getBDInstances`. Every line number in this bullet is the shipped tree's, after the dead-code deletion recorded in the next bullet moved this function up 108 lines. The traceback lands on the instantiated arm's comprehension over `binding_rows` (`pysrc/processYaml.py:2010`); the `binding_rows = variantEntry['params']` three lines above it at `:2007` is where the `None` subtable comes in. The declared-variant arm at `:2025` reaches the same `None` for a variant no instance selects. A variant exists to bind parameters, so on a block that declares none it binds nothing and can carry no Config. `_post_validateVariantParameterCompleteness` now rejects the row where it is declared (`pysrc/processYaml.py:8424`), naming the variant, the block, the file and line, and the owning project. The check sits ahead of the missing-parameter arm in the same hook, which already resolves the block by scope from the variant row's foreign key, so it needs no new pass and no schema field. **Gate: `unittest/test_error_variant_on_params_less_block.py`**, make-driven: `make db` on the fixture must fail with the diagnostic and no traceback, then the suite gives the block a `params:` list, has the variant bind it, and requires the same `make db` to pass — without that second phase a rule that rejected every variant row would look identical. A third phase pins the boundary against the missing-parameter arm of the same hook: the block declares the `params:` list but the variant binds nothing, and the diagnostic must be the missing-parameter one. **Observed failing against the unfixed generator** (`FAIL: make db accepted a variant on a block with no params:`) and passing after. Nothing authors the shape: a scan of all 232 project YAMLs under `examples/`, `unittest/`, `builder/pro/` and the product tree found 98 declared variant rows and no hit. **VERIFIED BY EXECUTION.**
- ~~**Dead code.** `_reconstruct_nested_structure` and `_attach_subtables_recursive` (`pysrc/processYaml.py:574`, `:592`) are never called and carry raw `print("DEBUG: ...")` statements.~~ **RESOLVED 2026-08-20: both deleted.** A repository-wide sweep found the only references were the definitions, the call at `:590` inside `_reconstruct_nested_structure`, and the recursion at `:680`; nothing else in `builder/base` or the product tree named either. 108 lines out, and all three remaining `print("DEBUG: ...")` sites in the generator went with them. `_loadSubTablesRecursive` and `loadTable` are untouched, so the sub-table loader itself is unchanged; the descriptive citation at [`plan-block-config-postprocess.md`](./plan-block-config-postprocess.md):246 now names a mechanism that no longer exists and is left for whoever takes that plan's §3 forward. **VERIFIED BY EXECUTION** — `make clean && make pipeline-test` exited 0 and the unit suite reported 107 of 107 passing.

**The synthesised register handler now inherits its container's Config. LANDED 2026-08-20.** `synthesiseRegHandler` (`config/postParseRegisterPorts.py:65`) builds one `<block>_regs` handler block, instance and leaf-to-handler `connectionMap` per routed leaf. It set `'params': parentParams` on the block row, the routed leaf's own parameter list, but the instance it emitted at `:91` carried only `instanceType` and `container`. That is the shape "variant-less instance of a params-declaring block". The C++ side froze the handler at the context default Config while the SystemVerilog side forwarded the container's parameter symbols, because `_resolveSvInstanceParams` forwards a parent symbol wherever the names match and the handler's names are the parent's by construction. A leaf held at a variant therefore got a handler whose parameter values came from the declaring constants, and the handler is where that leaf's registers live. In the product tree `model/debayer.cppm:60` read `std::shared_ptr<debayer_regsBase<debayerDefaultConfig>>` two lines below the `inheritContainerParam` children `preprocessBase<Config>` and `interpolateBase<Config>`, while `rtl/debayer.sv:120` instantiated `debayer_regs #(.BITS_PER_PIXEL_COLOR(BITS_PER_PIXEL_COLOR), ...)`.

**ARCHITECT'S RULING, 2026-08-20: the handler holds the leaf's own registers, so its Config is the leaf's.** The synthesised instance now sets `inheritContainerParam`, gated on the leaf declaring parameters at all, because `validate_inherit_container_params` rejects an inheriting child that declares none. One line of generator code, and it is the gate.

- **The inheritance preconditions all hold by construction, and the composed-build one was queried rather than assumed.** `validate_inherit_container_params` (`pysrc/processYaml.py:4993`) requires the child's params to be a bare-name subset of the container's, the two blocks to share an owning project, and the instance to be contained in a block. The subset is equality here, since the handler's `params` IS the leaf's list. Ownership was the risk, because `ipRegs` appears in six databases across the composed `ip_test` and `simple_ip` builds. It cannot diverge, because the handler's block row is fed through `processSingleFile(leafContext, ...)`, so its `_context` is the leaf's own YAML file, and both sides resolve through the same key. Queried on all six of `ip_test`, `ip_test/ip`, `ip_test/bridge`, `ip_test/bridge/ip`, `simple_ip` and `simple_ip/ip`. Every one reports owning project `ip` for handler and container alike, whatever the root build. Rule (f), which rejects a child both reached by an inheriting site and instantiated without a variant, is unreachable too, because there is exactly one handler instance per leaf block and it is the inheriting one. **VERIFIED BY EXECUTION.**
- **Emitted-output delta, measured from clean on both sides.** Corpus of 1200 generated source files across every example, `common/`, and the product tree; 1199 after. Three files differ, two go away, and one appears only in the after snapshot, the product's `.gen/cpp-modules.mk`, because `make all` writes it and the before snapshot was taken after `make gen` alone. That last one is snapshot timing, not a change. `examples/mixed/model/blockG.cppm` and the product's `model/debayer.cppm` move their handler member and its constructor cast from `<contextDefaultConfig>` to `<Config>`, switch to the container-typed `createInstance<handler<Config>>` overload, and gain an `import` of the handler's block module. `examples/mixed/.gen/cpp-modules.mk` loses the handler trampoline's module entry and adds it to `blockG`'s import list. The two removals are the trampolines themselves, `examples/mixed/registrar/blockGRegsRegistrar.cppm` and the product's `registrar/debayer_regsRegistrar.cppm`. An all-container-typed child earns no registration, `hasRegistrations` goes false, and `requiresRegistrations` on the `blockRegistrar` fileMap entry suppresses the scaffold. **Zero SystemVerilog files changed**, which is the confirmation that the SV side was already right. `ipRegs` is `hasMdl: 0`, so the six `ip`-owning builds emit no model artifact for it and show no delta at all; `blockARegs` and `blockBRegs` declare no params, so the gate leaves them alone. **VERIFIED BY EXECUTION.**
- **Deleting the two orphans is manual.** Neither file is swept when the declaration that produced it goes away. The pair-specific manifest fix below stops scheduling a trampoline with no registrations, so generation no longer opens that stale file to print the old "nothing to register" diagnostic. Registrar orphan cleanup remains separate work.
- **Gate: `unittest/test_regs_handler_container_config.py`**, make-driven, on the new `unittest/fixtures/regs-container-variant` cell. `rcvLeaf` declares `RCV_CFG_GAIN`, owns the `cfg` register, and is instantiated once at variant `tuned`, which binds 12 where the constant declares 1. The block reports its own gain beside the gain its handler resolved and asserts they agree, and `rcvCpu` writes `0xABC` to `cfg` over APB through the router and reads it back, so a handler that elaborated but decoded nothing fails rather than passing. The suite also asserts the emitted member is typed by `Config` and that no handler trampoline was emitted, which separates an emitter fault from a run fault. **Observed failing against the unfixed generator** by reverting the edit by hand rather than through a scratch mirror. The mirror technique does not work for this file, because CPython resolves a symlinked script's directory before setting `sys.path[0]`, so `pysrc.processYaml` is imported from the real tree and `a2cRoot`, hence `$a2c/config/postParseRegisterPorts.py`, is the real one. The failing run reported `gain 12 handler gain 1` and exited 2; after the fix, `gain 12 handler gain 12` and exit 0. **VERIFIED BY EXECUTION.**
- **Found and not fixed. A register whose payload field is a parameterizable type cannot be generated.** `registerFeatures` (`templates/systemc/structures.py:735`) emits `_getValue`/`_setValue`, and its signature takes neither `prj` nor `useConfig`, so it cannot call `cppTypeName` (`:183`) at all. It casts with the bare `vardata['varType']` at `:783` and `:785`, which for a parameterizable field is a template name with no arguments and does not compile, and it masks with the literal `vardata['bitwidth']`, the declaring constant's width rather than the resolved variant's. `sc_pack` (`:790`) and `sc_unpack` (`:897`, via the `cppTypeName` call at `:917`) get both right, so the correct pattern is adjacent in the same file. `common/systemc/hwRegister.h` is clean: it goes through `sc_pack`/`sc_unpack` and never calls these accessors. This was hit while building the `regs-container-variant` fixture and is why its register payload is a fixed-width type. It is also why no in-tree register is variant-width today, so `synthesiseRegHandler`'s docstring loses its claim that the handler's register storage is variant-width. **Zero live sites**: `_getValue` appears only in `examples/apbDecode/model/apbDecodeIncludes.cppm` and `examples/mixed/model/mixedIncludes.cppm`, and neither register is parameterizable. **VERIFIED BY CODE READING**, line numbers re-checked against the working tree 2026-08-20. **The cast arm is a straightforward `cppTypeName` call once the signature carries `prj` and `useConfig`; the mask width is the open question.** A `NamedStruct` field could use `subStruct<Config>::_bitWidth`, but the correct spelling for a **scalar** parameterizable type is not confirmed, so this is filed as a question, not a diagnosis with a known fix. Separate defect, separate step; no code changed here.

**A registrar TU left behind by older YAML remains an orphan-cleanup concern, not an active generation path.** The persisted pair record and manifest gate no longer schedule a model registrar with no registrations. Existing stale files still require the separate registrar-orphan cleanup policy.

**The `requiresRegistrations` manifest gap and the `hasVl + containerParam` gap are closed, 2026-08-23.** `projectCreate` now persists reachability before artifact creation, the selected Config descriptors, and one complete `REGISTRARPAIRS` record per reachable qualified `(assemblerKey, childKey)` pair. Each record owns the model registrations, concrete Verilated registrations, nested Config expressions, resolved RTL parameter values, factory domain, and collision-free artifact/top identities. `createBuildManifest`, `newModule`, `blockRegistrar`, `vlRegistrar`, and `getRegistrarConfigView` consume that record. None of those five repeats instance or project-precedence selection. (**CORRECTED 2026-09-04:** this read "None repeats instance or project-precedence selection", which scans as a claim about every consumer of the variant data. `projectOpen.getStandaloneVariants()` is not one of the five, and it does repeat the selection at `pysrc/processYaml.py:1629-1632`, then discards the descriptor at `:1635` and reads its values from the project-blind nested rows instead. See item 9A of [`plan-116-review-feedback.md`](./plan-116-review-feedback.md).) A physical registrar keeps one stable child basename per owning project and aggregates that project's parent-child pairs. Factory domains, Verilated top names, and pair-specific wrapper identities remain qualified by the logical parent-child pair, so two parents can bind the same child without colliding or multiplying physical registrar files.

A `containerParam` site forwards its parent's runtime variant label. The pair's VL registrar binds that label to `childVariantConfig<parentVariantConfig>`, and its pair-qualified SV top binds the resolved child literals for that parent variant. Local coverage checks mixed inherited and ordinary sites in both YAML orders, one physical registrar artifact, and the ordinary registration. Cross-project coverage enables RTL on a separately owned leaf, selects two parent Configs with different algorithms and widths, and runs each pair-qualified top. Other guards cover the synthesised all-inherit handler, precedence, and an unreachable referenced-project harness. **VERIFIED BY EXECUTION.**

**Superseded prototype in the working tree. REMOVED 2026-08-18.** The `configFromContainer` instance flag, its schema field, the `A2C_NESTED_CONFIG` trait in `common/systemc/nestedConfig.h`, the nested-entry emission in the config template and the nested-Config plumbing in `_resolveInstanceConfigFields` / `getForeignConfigData` / `getRegistrarConfigView` predated this ruling and implemented the per-site shape it supersedes. The recommendation this bullet carried — remove it as a separate change so the tree states one design — was approved and executed; see "The `configFromContainer` prototype removal" below.

#### Implementation record for step 7 — moved here from the design specification, 2026-08-14

[`design-parameter-inheritance.md`](./design-parameter-inheritance.md) was rewritten on 2026-08-14 as a **user-facing** specification of the YAML, the emitted shapes and the authoring rules. Everything implementation-facing that it carried is recorded here instead, because this plan owns implementation.

**Where the behaviour lives.** Line numbers are those of the working tree before the `containerBlock` removal (§2, D7.2) and will have shifted.

| Piece | Site |
| :-- | :-- |
| Schema field on `parametersvariantsparams` (`value: optionalConst`, `containerParam: optional`, `_singular: value`, `param: anchor`) | `config/schema.yaml:340-362` |
| Declaration-time exclusivity and presence (a row is a value **or** container-sourced, never both, never neither) | `pysrc/processYaml.py:8525-8546`, inside `_post_validateVariantBindingSizing` |
| Site-time linkage validator: container existence, container-parameter existence, the `maxValue` domain relation, single-level reach | `validate_container_sourced_params`, `pysrc/processYaml.py:5374-5493`, run inside `calcBlockConfigInfo` |
| Variant completeness generalised to "bound **or** container-sourced" — **needed no change** | `_post_validateVariantParameterCompleteness`, `:8579-8604` |
| SystemVerilog instantiation parameters, forwarding the container's symbol | `_resolveSvInstanceParams`, `:2106-2140` |
| ~~The layout-gate skip that loses a container-sourced row (step 7b)~~ **REMOVED 2026-08-17** | was `variantValueBindings`; now `siteParamValues` / `valueBindingsFromValues` resolved through `_siteValueMaps` |
| `inheritContainerParam` preconditions (bare-name subset, same owning project, contained in a block) | `:5024-5095` |
| The layout-pass exclusion of an `inheritContainerParam` endpoint | `:6663-6672`, with the binding-collection skip at `:6599` |

**Why the linkage is a post-parse check and not a foreign key.** A container block's `params:` are not reliably parsed before a child variant's binding rows, and Governing Invariant 2 states that a successful FK proves the target was already parsed but does not schedule parsing. `containerParam` is therefore not FK-typed, and only row-local well-formedness is checked where the variant is declared. This is also one of the grounds for D7.2.

**The diagnostics, by the fault each names.** All are db-time and name both sides, per D7's ruling. Three of the original eight — `containerBlock` without `containerParam`; two-level reach; a container-pinned variant instantiated elsewhere — were reachable only through `containerBlock` and go with it (§2, D7.2). Removing the two-level-reach message loses its forwarding advice, which named the fix; **folding that advice into the container-declares-no-such-parameter message is worth doing as part of the removal.**

| Fault | Where checked | Site |
| :-- | :-- | :-- |
| Both a value and a container source | declaration, row-local | `:8536-8540` |
| Neither a value nor a container source | declaration, row-local | `:8542-8545` |
| Container declares no such parameter | post-parse, per site | `:5198-5204` |
| Container's `maxValue` exceeds the child's | post-parse, per site | `:5210-5218` |
| Instance not contained in a block | post-parse, per site | `:5159-5163` |
| Parameter omitted from a variant | declaration, row-local | `:8598-8603` |
| ~~`containerBlock` without `containerParam`~~ | ~~declaration~~ | removed with the field |
| ~~Two-level reach~~ | ~~post-parse~~ | removed with the field |
| ~~Named container block does not contain this instance~~ | ~~post-parse~~ | removed with the field |

**How `inheritContainerParam` is generalised**, recorded because it is the migration target: per parameter rather than all or nothing; explicit naming of the container parameter rather than bare-name matching; no same-project restriction (`inheritContainerParam` hard-rejects a cross-project pair, which is why it cannot express the motivating case, and which is G5.8 of [`plan-ip-project-composition.md`](./plan-ip-project-composition.md)); and it resolves to literals per site, and since step 7b landed (2026-08-17) the layout gate adjudicates the connection.

**Skill guidance is in conflict. Both gating conditions are now met, so the rewrite is UNBLOCKED (2026-08-18) but NOT DONE.** **DONE 2026-09-07.** The section is retitled "Container-sourced parameters (`containerParam`, `inheritContainerParam`)", leads with the per-parameter form on the `cpLayout` fixture (`examples/xprojParam/cpLayout/yaml/xpCpLayoutTop.yaml:52-96`, names differing), states that names need not match, that cross-project is allowed, and that the container's `maxValue` may not exceed the child's, then presents `inheritContainerParam: true` as the shorthand for every parameter at once with its preconditions reframed as the conditions under which the shorthand applies. It points at [`design-parameter-inheritance.md`](./design-parameter-inheritance.md) §4 for the full rules and for `valueType` not being checked. The line-106 sentence on the three legal shapes is unchanged. Every YAML snippet was checked against its fixture line and every rule against the design document's §4; the install copy under `.claude/skills/` was not hand-edited. `rules/skills/design-parameterizable-blocks.md` documents `inheritContainerParam` as **the** container-inheritance mechanism (line 104, and "Container Config Inheritance", lines 110-129, which states the same-owning-project precondition as a rule). That is correct for what ships today but incomplete: `containerParam` also ships. The condition was "step 7b lands and step 7a has a regression guard" — 7b landed 2026-08-17 and 7a's guard closed 2026-08-18. "Container Config Inheritance" is the section to rewrite, presenting `inheritContainerParam` as the degenerate case and pointing at [`design-parameter-inheritance.md`](./design-parameter-inheritance.md) for the general form. Deliberately left for its own change.

**Two adjacent gaps this design neither causes nor fixes.**

- **A third project instantiating a foreign block at a variant declared by an intermediate project resolves no descriptor and silently gets defaults.** ~~`_selectVariantDescriptor` matches either the consuming project's own declaration or the child block owner's~~ **CORRECTED 2026-09-04: the shipped module-level `selectVariantDescriptor` (`pysrc/processYaml.py:292-312`) has THREE arms, tried in this order: a foreign binding the consuming project authored itself, then the config context owner's own bare-name binding, then a foreign binding from the block's declaring project. The block owner's arm is deliberately LAST, because a block's config context can be owned downstream of the block, and that owner emits the struct and authors its own binding.** The gap the bullet names survives the correction, because no arm reaches a declaration authored by a project that is neither the consumer nor the block's owner. An instance declared in the customer project at a variant declared by the mid-level IP therefore falls back to the block default Config. The container-sourced work keeps *validation* sound in its presence — `validate_container_sourced_params` keys its rows by `(block, variant)` and so checks **every** declaration of the variant label a site names (`:5119-5126`) — but it does not close the descriptor gap.
- **A stale generated orphan**, `examples/xprojParam/dpTop/registrar/xpDpTop_xpDpLeafVariantConfig.cppm`, left from an earlier shape of the fixture: generated files are not swept when the declaration that produced them is removed.

**One further limitation visible in the fixture's emitted output**, and it is B5 rather than anything new: `examples/xprojParam/dpTop/registrar/xpDpTop_xpDpMidVariantConfig.cppm` carries `DP_ALGO` even though `xpDpMid` names only `DP_WIDTH` and `MID_ALGO`, because a Config is composed from the declaring context's parameterizable constants rather than from the block's own `params:` (§5, B5; step 3).

**The `instances.configFromContainer` prototype field** belonged to the superseded templated-Config prototype, not to D7. Its disposition was a separate question from `containerBlock` and is now **RESOLVED: removed 2026-08-18**; see "The `configFromContainer` prototype removal" below.

#### The templated-Config prototype — SUPERSEDED; its measured results stand

A prototype that made the container's Config a template parameter was built and is **explicitly SUPERSEDED by D7**. It is retained only for what it measured, because those measurements are what established that the customer case is reachable at all.

**All three gates passed. VERIFIED BY EXECUTION:**

- the customer's value reached the **nested leaf**;
- **two container instances carried different nested configurations**;
- the vendor's emitted sources stayed **byte-identical** under customer-driven regeneration — 7 changed files out of 883 across 38 example projects, **all inside the fixture** — and the unit suite passed.

**Its four recorded defects, which are why it is superseded:**

1. nested binding worked by variant-**LABEL COINCIDENCE**;
2. nesting was keyed per child **BLOCK**, so sibling instances shared one Config;
3. **no layout gate** for a divergent nested width;
4. **SystemVerilog unserved** — the RTL equivalent forces the vendor's parameter list to become the **union** of its own parameters and every nested IP's.

**One qualification to keep in view:** a templated container ships as **SOURCE**, not as a precompiled object.

#### The `configFromContainer` prototype removal — DONE 2026-08-18

The prototype above left a fourth container-inheritance mechanism in the tree alongside the three live ones (`containerParam`, `inheritContainerParam`, the templated-Config path). It is recorded as P8 of [`GENERATOR_ARCHITECTURE.md`](../GENERATOR_ARCHITECTURE.md), which required an explicit product decision before deletion because the schema documented a capability the other mechanisms do not provide — a project *above the container's own project* configuring a nested child. **The architect approved deletion**, including `common/systemc/nestedConfig.h`.

**Inertness proved before anything was deleted.** `configFromContainer`, `A2C_NESTED_CONFIG` and `nestedConfig` were swept across `builder/base` (sources, `examples/`, `unittest/fixtures/`, `rules/`, `plans/`, docs), `builder/pro`, the product tree (`arch/yaml`, `config`, `model`, `tb`, `rtl`, `isp_shared`), the read-only downlevel `/work/ws/isp` (56942 files) and the stale vendored `isp_shared/builder/` (1434 files). **Zero occurrences outside `builder/base`**, and inside it the only YAML occurrence was the schema declaration itself — **no YAML anywhere set the flag**, confirming the claim this plan had carried since 2026-08-17. The `nestedConfig.cpp` hits under `examples/nested/` are that example's own testbench config and are unrelated to the prototype.

**Blast radius for an out-of-tree consumer: a warning, not a rejection.** A design-YAML field absent from the schema is reported by `printWarning` at `pysrc/processYaml.py:7277-7278` and parsing continues; `warningAndErrorReport()` (`pysrc/arch2codeHelper.py:134-146`) sets a non-zero return only from `errorCount`. So a project that set the flag gets one warning per occurrence and the field is dropped — and since the flag was inert, dropping it moves no artefact. P8's "would fail at `make db`" is therefore **too strong** and is corrected here.

**What was removed.** The schema field (`instances.configFromContainer`); `common/systemc/nestedConfig.h` (which was untracked, so it was copied aside before deletion); in `pysrc/processYaml.py` the `addNestedConfigDescendants` helper, the `_nestedConfigEntries` method, the `nestedChild` key from both `_resolveInstanceConfigFields` returns, the `configTypeIdentity` nested arm, `getRegistrarConfigView`'s `nestedVariants` set and its union into `variants`, `getForeignConfigData`'s two nested return keys, `nestedConfigChildren` from `getBlockData`'s `blockDataSet` and its per-instance population; in `pysrc/intf_gen_utils.py` the three `cpp_nested_config_*` helpers, the `nestedChild` arm of `cpp_config_struct_name` and the `nestedConfig.h` include emission; the trait-declaration block in `templates/systemc/classDecl.py`; the nested-module import and nested-entry members in `templates/systemc/config.py`; the trait-keyed factory-argument branch in `templates/systemc/constructor.py`, collapsed to the single remaining arm. **Two sites P8's inventory did not list** were found by symbol sweep and removed too: `templates/systemc/constructor.py`'s branch (P8 said "two SystemC templates" but the third was `config.py`) and the now-dead `addNestedConfigDescendants` call sites in `pysrc/newModule.py` and `config/createBuildManifest.py`, which with the flag gone were no-ops. One import left unused by the removal (`cpp_descriptor_config_name` in `config.py`) was dropped as well.

**What proves it, all OBSERVED.**

- **Emitted-output delta: NONE. This is the proof the deletion is behaviour-neutral.** Hashed before and after two independent cold regenerations: **1932 files** under `/work/ws/debayer` (excluding `builder/`, the vendored `isp_shared/builder/`, both `rundir/` trees and the `.db` files) and **2848 files** across `base/examples` and `pro/examples`. **Zero added, zero removed, zero changed** in both populations. This is a deliberately broad superset of the 1124-file figure used at step 1's closeout, whose exact filter was not recorded.
- Cold `make clean` then `make pipeline-test -j` **exit 0**.
- Unit suite **103 of 103**, `unittest/run_all_tests_parallel.sh` exit 0, guard silent.
- Product tree cold `make clean` + `make gen -j` + `make -C rundir -j all`, all **exit 0**.

**Nothing was found suggesting the prototype was live.** Every branch removed was guarded by a flag no row set, and the zero-delta result over 4780 hashed files is the measurement.

**Review, 2026-08-18. Two independent reviewers, no MUST-FIX.** Three findings were taken: the vestigial `variantArg`/`projectArg` locals the collapsed branch left in `templates/systemc/constructor.py` (inlined into the `createInstance` call, since with one arm left they were single-use quoting wrappers); `type_key` in `_resolveInstanceConfigFields`, whose second reader was the deleted `nested_child` computation (collapsed into the `getBlockConfigView` call); and the stale `addNestedConfigDescendants` mention in P5's staging note in [`GENERATOR_ARCHITECTURE.md`](../GENERATOR_ARCHITECTURE.md), which cited a function this change deleted. All four gates were re-run after these edits and are unchanged, **including the zero emitted-output delta** — which is what makes the `constructor.py` inlining safe to assert, since it is a template edit.

**Findings declined, with reasons.** `cpp_config_struct_name`'s head comment enumerates three outcomes while the function has four branches — but the two it omits (`inheritContainer`, `containerSourced`) are both live mechanisms, the text is unchanged from before this removal, and the removal made it strictly closer to accurate by deleting one arm. Likewise the `configTypeIdentity` docstring's "the first spells `Config` outright" ordinal, which does not match the condition order in the `if`. Both are pre-existing comment debt on code this change did not author; fixing them here would be improving adjacent non-prototype code. Also declined as out of scope: the `block_row.get('params', []) or []` contracted-field fallback at `getForeignConfigData` (one of seven instances of that pattern, wanting one repo-wide decision rather than a local patch), the dead `instIsParameterizable` local in `constructor.py`, the descriptor contract's undocumented `containerSourced` key, and the permanently-dead `useDefault`/`duplicateOf` descriptor branches. Each is a pre-existing item recorded here rather than fixed.

### Step 8, the instance Config-selector rules (D9). LANDED 2026-08-20

Both rules are one `post(...)` row hook on the `instances` section, which had none before.

| Piece | Site |
| :-- | :-- |
| Hook declaration | `config/schema.yaml:215`, `_attribs: [flat, post(validateInstanceParameterBinding)]` |
| Rule B, the parameterized top | `pysrc/processYaml.py:8458` |
| Rule A, the instance selecting no Config | `pysrc/processYaml.py:8469` |

**Why a row hook and not a project-wide pass.** `SCHEMA_SPECIFICATION.md`'s own decision procedure puts it here, because the check concerns one row and a target its own foreign key guarantees. `instanceType` is `_type: required` with `_validate` onto `blocks.block` (`config/schema.yaml:217-221`), so the block row and its nested `params:` are parsed before this row is processed, and `self.flatData['blocks'][item['instanceTypeKey']]` reads them directly with no scope walk and no fallback. A row hook also has the row's `lc`, so the diagnostic names the file and line, which for rule A is the whole difficulty, since the mistake is an absence.

`container` is `auto(container)` and resolves to the `_topInstance` sentinel for the root project's own top row, so rule B is one equality test on a field the same hook already has. **VERIFIED BY EXECUTION.** The first run against the unrestructured `examples/xif` reported `In xif.yaml:127: top instance 'xif_tb' is block 'xif_tb' (project 'xif'), which declares params: [DATA_WIDTH, FRAME_HEIGHT, FRAME_WIDTH]`, which is the census's single predicted site and no other.

**`blockRow.get('params', {})` here is not a contracted-field violation.** `params` is `_attribs: [optional, list, flat, ...]` and the parser omits the key entirely when the node is empty; `checkIsParam` tests `'params' in varInfo` at `pysrc/processYaml.py:8488` for the same reason.

#### `examples/xif` restructured, because it held the only authored site

The file documents two subjects and both had to survive: the BUG 7 cross-interface boundary thunker at the testbench/DUT boundary, and the container-Config gate for the testbench External. The second is the constraining one. `tbPeer` at variant `pvSourced` sources every parameter from its container, so its Config is a template over the container's Config built through a maker template, and the External pseudo-block is the one consumer of that machinery that is not itself a class template. The symbol therefore has to be bound to the container's own resolved Config, which needs the container-sourced child to be a direct child of the harness container.

The restructure keeps the harness exactly where it was and adds a root above it: a new unparameterized `xif_top` block, `topInstance: xif_top`, and the `xif_tb` instance row moved to `container: xif_top, variant: tbV0`. `xif_tb` keeps its `params:` and its `tbV0` variant. The harness stays the harness, since `dut` still has `hasTb: true` and its External is still built from the block holding `uDut`, so the External gate keeps its shape.

**A parameterized testbench harness that is not the top works. VERIFIED BY EXECUTION.** This was the arrangement's risk: `ip_test` shows a non-top harness (`ip`'s testbench under `ipStdTop`, `ipBridge` and `ip_top`), but in every such case the harness is the top of its own standalone build and becomes non-top only when a parent composes it. No example had a harness that is non-top by design within one project. `examples/xif` now does, and `make -C examples/xif clean && make gen`, `make -C rundir all` and `make -C rundir run` all exit 0 with "No error".

**The External gate is intact, checked field by field.** `examples/xif/tb/dut/dutExternal.cppm:3` still stamps `--variant=tbV0`, and `:39` and `:76` still spell `tbPeerBase<tbPeerPvSourcedConfig<xif_tbTbV0Config>>`, the container's own resolved Config rather than a template parameter. Both peers still assert the frame height their partner stamped, so the run, not merely the compile, is the check.

**Emitted-output delta for the restructure: zero files.** A full `make clean` then `make gen` on `examples/xif` leaves `git status` reporting only the two YAML files I edited. That is stronger than expected and it has a reason: the External is generated per **block**, and the variant it stamps comes from `xif_tb`'s single declared variant, neither of which the restructure touched. The new root block declares `hasMdl`, `hasRtl`, `hasVl` and `hasTb` all false, so it scaffolds nothing.

#### Gates

Both suites are make-driven: each copies its fixture to a temp tree and runs `make db`, so the rejection has to arrive through the build a user runs, and a rejection delivered as a traceback fails the suite.

- **`unittest/test_error_instance_no_config_selector.py`** on `unittest/fixtures/instance-no-config-selector`. `incLeaf` declares `params: [INC_WIDTH]` and `uLeaf` names no variant and does not inherit. The container `incTop` declares the same parameter, so both accepting forms are one edit away, and the suite takes both: phase two adds `variant: leafV0`, phase three `inheritContainerParam: true`, and each must pass. Without both, a rule that rejected every instance of a parameterized block would look identical.
- **`unittest/test_error_parameterized_top.py`** on `unittest/fixtures/parameterized-top`. The top instance names `variant: ptV0`, so it is well formed by every other rule and rule A has nothing to fire on. That isolation is the point, because a fixture that merely omitted the variant would pass against either arm. Phase two performs the restructure the diagnostic asks for, adding an unparameterized `ptRoot` above the harness, moving the harness into it and repointing `topInstance:`, then requires `make db` to pass. That is the unit-scale statement of what `examples/xif` now does.

Each suite asserts the specific diagnostic text rather than only a non-zero return, and asserts that the **other** arm of the same hook stayed silent.

**Both gates were observed failing against a disabled arm, then passing restored. VERIFIED BY EXECUTION.**

- Rule B's arm replaced by `if False:`. `test_error_parameterized_top.py` exits 1 with `FAIL: make db accepted a parameterized top instance`, while its phase-two accept arm still passes and `test_error_instance_no_config_selector.py` still exits 0. So the top suite is proving rule B and nothing else.
- Rule A's arm replaced by `if False:`. `test_error_instance_no_config_selector.py` exits 1 with `FAIL: make db accepted an instance that selects no Config`, while both accept phases still pass and `test_error_parameterized_top.py` still exits 0.

#### Verification, all from clean

- `make clean -j && make pipeline-test -j` at the base root: **exit 0**. Both intentional negative probes printed their `OK: ... rejected` lines. **VERIFIED BY EXECUTION.**
- `unittest/run_all_tests_parallel.sh`: **109 of 110** at this historical
  checkpoint. The failed `test_registrar_default_variant.py` fixture authored
  the shape step 8 rejects. The architect later retired that suite and fixture;
  the current full result is 114 of 114.
- Product tree: `make clean -j`, `make gen -j`, `make -C rundir -j all`, `./build/run debayer`, all **exit 0**, run reports "No error". **VERIFIED BY EXECUTION.**
All four were re-run from clean after the review edits below, with the same results and a byte-identical corpus.

- **Emitted-output delta: zero files differ in content.** 1188-file corpus over `examples/`, `common/` and the product tree, build directories and databases excluded. Compared against the snapshot taken at the register-handler change's closeout: **zero files differ**. The only listed entries are eleven `.gen/cpp-modules.mk` files present in the earlier snapshot and absent now, plus one `.gen/build.mk` the other way, all of which record which make target last ran rather than any generator output. The xif tree, which I expected to move, did not: see the restructure above.

#### Collateral fixture updates and the retired gate

Four unit suites failed on the first run, all because their fixtures authored the shape rule A now rejects. Three were incidental to their subjects and their fixtures were migrated to legal authoring, the same migration `examples/xif` took:

- `test_block_config_parameterization.py`, both inline architectures. `uLeaf` of `wordLineLeaf` gains `variant: wl0`; `uSrc`/`uDst` of `srcBlock`/`dstBlock` gain `variant: bus0`. Each new variant binds the constant's declared value, so no measured width moves.
- `test_block_own_surface_param_no_params.py`. `uDst` in the negative arm, and both `uSrc`/`uDst` in the positive control, gain `variant: w0`. The negative arm matters: rule A fired during the parse of `uDst` and pre-empted the own-surface validator that runs after parsing, so the suite was reporting the wrong rejection.
- `test_parameter_variant_block_param_identity.py`. `uOther` gains `variant: narrow` at `WIDTH: 7`. This strengthens the subject: both same-named `WIDTH` parameters are now variant-bound, which is what the block-scoped identity is for.

**RESOLVED 2026-08-20: rule A retired
`test_registrar_default_variant.py`.** The suite used a parameterized child
reached at a variant by one site and at no variant by another. Rule A makes that
authoring illegal. The architect chose deletion because the model-side subject
is unreachable under the new rule and an inheriting site has separate coverage.
The suite and `registrar-default-variant` fixture no longer exist.

Traced through `getRegistrarConfigView` (`pysrc/processYaml.py:1626-1654`), **VERIFIED BY CODE READING**:

- `emptyVariantAsked` is `not keyedInstances or any(inst['variant'] == '' for inst in keyedInstances)`. After rule A, a params-declaring block can have no keyed instance at the empty variant, so the second disjunct is dead and only the "no keyed instance at all" case remains. That case sets `inheritOnly` when any site is container-typed, and `defaultRegistration = not inheritOnly and emptyVariantAsked` then goes false. **So the model-side `defaultRegistration` arm is unreachable for a parameterized block.** For an unparameterized block every instance sits at the empty variant, so the normal path is untouched.
- `verifDefaultRegistration = containerTyped or emptyVariantAsked` **keeps a live consumer**, through `containerTyped`. The verilated half of the suite's subject survives an `inheritContainerParam` site.

Rule A also closes two of the items filed under "Open after the empty-variant fix": the missing default-parameter verilated DUT, whose recorded options were a default-parameter SV wrapper top **or** a db-time rejection of the shape, and `_resolveSvInstanceParams`'s `KeyError` for a variant-less instance of a params-declaring child. Both were reachable only through the shape rule A rejects.

**The repoint-or-delete question is closed.** A scratch probe showed that
switching the two variant-less sites to `inheritContainerParam: true` passed
`make db`, but it would have dropped the suite's `defaultConfig` subject. The
architect selected deletion. Mixed ordinary/inherited behavior and
`verifDefaultRegistration` now have direct coverage elsewhere.

#### Review, 2026-08-20. Findings taken

- **The diagnostics named the wrong project.** Both read `block 'B' (project 'P')` while resolving `P` from the instance row's own file, so a cross-project instantiation printed the instantiating project against the instantiated block. Now resolved from `blockRow['_context']`, matching the idiom at `pysrc/processYaml.py:1606`, `:1673` and `:2105`. **VERIFIED BY CODE READING** only: both fixtures are single-project, so neither distinguishes the two spellings, and no cross-project cell was added for a message-text fix. The same flaw is in the sibling variant hook at `:8419` and was left alone as pre-existing.
- **Rule B's message understated the fix.** It said to put the block under an unparameterized root and omitted repointing `topInstance:`, which is half the restructure. It now names all three edits and says why one variant of literals is refused rather than only that it is the only option.
- **Two author-facing rejections had no author-facing documentation.** Added to `rules/skills/design-parameterizable-blocks.md`, beside the variant-completeness rule and the `inheritContainerParam` preconditions, and to the "What is not allowed" list in [`design-parameter-inheritance.md`](./design-parameter-inheritance.md), which this plan's opening bullet names as the owner of rules addressed to an author. `.claude/skills/` holds an install copy that `make agents-setup` regenerates and git ignores; it was not hand-edited.
- Comment and prose trims in `examples/xif/arch/yaml/xif.yaml`, both new fixtures, one test docstring, and this document.

**Superseded review disposition.** The review correctly deferred the gate change
until the architect ruled. The later ruling selected deletion, and the runner no
longer contains the suite. The current full result is 114 of 114.

#### Consequence noted, not acted on

Rule A makes the last check in `validate_inherit_container_params` unreachable. It rejects an inheriting child that is **also** instantiated without a variant, because both resolve the same factory key; with rule A the second instance is rejected at parse time, before `calcBlockConfigInfo` runs. The check is left in place: it states an invariant worth keeping in the code, and deleting it is not this step's work.

### Step 9, the verilated wrapper of a block reached only by `inheritContainerParam`. LANDED 2026-08-20

**The defect.** `/work/ws/debayer/verif/preprocess_hdl_sc_wrapper.h` and `interpolate_hdl_sc_wrapper.h` were emitted as CONCRETE classes bound to `preprocessBase<debayerDefaultConfig>`, with the `<Config>` argument deleted from every BFM and hdl_if type rather than substituted. Both blocks are reached only through `inheritContainerParam` (`/work/ws/debayer/yaml/debayer.yaml:271-272`), so the container types them with its own `Config` and the wrapper was one C++ type where a family is needed. The product tree never noticed: its verilated path is a VCS flow behind `USE_VCS`, and the registrar wraps the whole trampoline in `#ifdef VERILATOR`.

**Root cause chain, both arms in `templates/systemc/module_hdl_wrapper.py`.**

1. The wrapper's shape was keyed on `data['variants']`, the INSTANTIATED variant view. An instance carrying `inheritContainerParam` binds no variant label, so that view is empty for such a block while `data['declaredVariants']` is populated. `pysrc/processYaml.py:2012-2025` documents exactly this case and says the declared view exists so the SystemVerilog wrapper does not fall through to the non-parameterizable render path; the SystemC wrapper was still reading the instantiated one.
2. `mp_sig[port][key].replace('<Config>', '')` deleted the template-argument list where its own comment four lines above said it substituted the project-wide default Config.

**The second arm was not a compile break, contrary to the report that opened this step. MEASURED.** With the strip restored by hand, `unittest/fixtures/inherit-vl-child` generates, verilates, builds and RUNS clean, and the checker reads back the right algorithm. The bare name is not the namespace-scope class template: unqualified lookup inside the wrapper's class body finds the member alias the block's Base publishes (`using vliSt = vliSt<Config>;`, emitted at the end of every `<block>Base`), and that Base is bound to the same `defaultConfig` the wrapper inherits. The strip therefore resolved to the block default by accident of name lookup, which is what the comment claimed it did on purpose.

**Substituting the name explicitly is NOT equivalent, and it was reverted on 2026-08-20.** The measurement above was taken on a fixture whose wrapper is Config-templated, where the Base is dependent and the bare name resolves to the namespace-scope class template. On the CONCRETE path the Base is non-dependent, so its public member alias is already a concrete non-template that class-scope lookup finds first, and appending a template-argument list to it is `error: expected '>'`. That was established by a real build failure on 2026-08-03, and deleting the argument list is the fix from that date rather than a defect. The substitution landed here and no build caught it because after arm 1 no block reaches the concrete-parameterizable branch at all: zero emitted wrappers corpus-wide carry a qualified `DefaultConfig` on a `bfm_decl` or `hdl_if_decl`. Green builds prove nothing about a dead branch. The comment now states the base-alias reason instead of the substitution story, because the line reads like a defect and has now been at risk twice.

**The fix.** One fact, `svWrapper['scWrapperConfigTemplated']`, added to the block view at `pysrc/processYaml.py:1446` beside the wrapper names it belongs with, and read by both consumers so they cannot drift apart again: `templates/systemc/module_hdl_wrapper.py` for the class shape and `templates/systemc/vlRegistrar.py:123` for the trampoline that instantiates it. It is true when the block declares its own params AND declares variants. Both files lost their DUT_T-only arm, which required a block with variants and no `params:`. That shape is rejected at db by `_post_validateVariantParameterCompleteness` in the working tree, and the two changes must land together: without the rejection, such a block goes from compiling to not compiling.

**The Config the trampoline binds is UNCHANGED, and which Config it SHOULD bind for a container-typed site is open.** The empty-variant `_verif` registration still names `sc_concrete_dut` paired with the block's `defaultConfig`, exactly as before; the change is that a templated wrapper needs both spelled. That pairing is the item already filed under "Open after the empty-variant fix" above, and this step adds a second, sharper reason to answer it:

- The answer is also constrained by pin width, not only by type identity. A templated wrapper's hdl_if is `sc_bv<payload<Config>::_bitWidth>`, while the Verilated top it is paired with is fixed at the widths its own declared variant elaborated. Any answer must pair a top and a Config that resolve the same widths.
- A container-typed site asks the factory under the EMPTY variant key, because inheritance carries no variant label (`templates/systemc/constructor.py:223` passes `value["variant"]`, which is `''`). `instanceFactory::createInstance` nulls the container-supplied factory for every non-model mode (`common/systemc/instanceFactory.cpp:76`), so a verilated site has nothing but that one registration to find. One key, one Config.
- The container casts to `<child>Base<Config>` with ITS OWN Config (`/work/ws/debayer/model/debayer.cppm:128`). A container declaring N variants is N distinct C++ types, so no single registration can serve more than one of them.
- The one that works is the container variant whose Config struct IS the context default, which happens only when the container's block name matches its config-context file stem and the variant is literally named `default`. `debayer` is in exactly that shape, which is why the product tree works and why a second `debayer` variant would break it.
- **MEASURED**, on the fixture: `make run-vl-def` (leaf under the `default` container) runs clean; `make run-vl-alt` (the same leaf under `alt`) segfaults on the null `dynamic_pointer_cast`, rc 2.

Answering it needs a decision this step did not take: either the container forwards its own variant label for an inheriting child so the key carries the Config dimension, or the shape is rejected at db for a `hasVl` child under a multi-variant container. Both are design changes, so the question is referred rather than guessed.

#### Gate: `unittest/test_inherit_vl_child.py`, on `unittest/fixtures/inherit-vl-child`

No corpus fixture combined a multi-variant container with a `hasVl` child reached by `inheritContainerParam`; `examples/xprojParam/inhVar` is the same topology with `hasVl: false`, and this cell is derived from it. `vliCont` is instantiated at `default` and `alt`, differing only in `VLI_ALGO`; `vliLeaf` inherits, declares one variant `solo` of its own so a standalone verilated top exists, and its RTL stamps the resolved `VLI_ALGO` into every sample it forwards. The suite scaffolds, generates, VERILATES and runs, swaps the verilated leaf into the `default` container instance, and asserts the checker read back that container's algorithm while the `alt` chain's model leaves read back theirs. The `alt` swap is run as a recorded probe and asserted to FAIL, so answering the Config-selection question forces the suite to be revisited.

- **Observed failing against the unfixed generator**, by reverting both arms by hand and restoring them: five emitted checks fail (`the emitted wrapper does not carry 'template <typename DUT_T, typename Config>'` and four more), and the suite exits 1. **The RUN passes either way**, because the Config the trampoline binds does not change and the fixture's `default` container variant is the coincidence described above. That is the honest reach of the runtime half: it proves the whole verilated path works under a multi-variant container, which nothing covered before, while the emitted checks are what discriminate the wrapper's shape.
- Registered in `unittest/run_all_tests.sh`; the parallel runner's suite-count guard moves 109 -> 110. The suite isolates into a temp copy under `unittest/`, so it stays in the ISOLATED lane.

#### Verification, all from clean

- `make clean -j && make pipeline-test -j` at the base root: **exit 0**, before and after.
- **Emitted-output delta across `examples/` (960 files) and `common/` (69 files): ZERO.** No example reaches the new path: none has a `hasVl` block whose instances are all inheriting, and none has a parameterizable `hasVl` block declaring variants that no instance binds. That is the measurement that says the change is behaviour-preserving everywhere it was already exercised, and it is also why the fixture had to be built.
- Product tree, 151 files: **four differ**, all predicted. `verif/preprocess_hdl_sc_wrapper.h` and `verif/interpolate_hdl_sc_wrapper.h` become `template <typename DUT_T, typename Config>` classes inheriting `<block>Base<Config>`, drop the concrete DUT include from their preamble, and keep `<Config>` on their BFM and hdl_if types; `registrar/preprocessVlRegistrar.cpp` and `registrar/interpolateVlRegistrar.cpp` spell `<Vpreprocess_default_hdl_sv_wrapper, debayerDefaultConfig>` where they named the bare class. The hand-written `setTimedLocal` override and `end_ctor_init` in `verif/preprocess_hdl_sc_wrapper.h` survive intact.
- Product tree `make clean -j && make gen -j`, `make -j all` in `rundir`, `./build/run debayer`: **all rc 0, "No error"**.
- `unittest/run_all_tests_parallel.sh`: **110 of 110**, no count warning.

### Step 10, the Config a container-typed verilated site gets. LANDED 2026-08-20

Step 9 left this open and referred it to the architect. It is answered. The
container says which Config it wants, using the variant label it already holds.

**The defect. MEASURED** on `unittest/fixtures/inherit-vl-child`: the container
at variant `default` verilated and ran clean, the same leaf under `alt`
segfaulted on a null `dynamic_pointer_cast`, rc 2. A `hasVl` child reached only
through `inheritContainerParam` got exactly ONE `_verif` registration, under the
empty variant key, bound to one concrete Config.

**Root cause, two halves.**

1. `templates/systemc/vlRegistrar.py:40` read `sorted(data['variants'].keys())`,
   the INSTANTIATED variant view. An inheriting instance binds no variant, so
   that set is empty, the per-variant loop emitted nothing, and only the
   `verifDefaultRegistration` arm fired.
2. `templates/systemc/constructor.py:223` passed `value["variant"]`, `''` for an
   inheriting instance. Per-variant registrations alone leave keys nothing asks
   for.

**The mechanism is the model side's, said with a string instead of a type.**
The model path never uses the registration keyspace for an inherited child: the
container is a class template already instantiated at a known Config, so it hands
the factory a constructor naming the child's implementation class
(`instanceFactory.h:64-71`, used at `/work/ws/debayer/model/debayer.cppm:130`).
`instanceFactory.cpp:76` discards that constructor for every non-model mode. A
container TU cannot name a Verilated class, so it says the same thing with a
string instead of a type: its own variant label. The lookup order at
`instanceFactory.cpp:85-97` is exact key, then container-supplied constructor,
then empty-variant fallback, so `(child_verif, "alt", proj)` hits first while
`(child_model, "alt", proj)` misses and the model path is untouched.

**Where the new fact lives, and why there.** `projectCreate.calcVariantSourceBlocks()`
persists `VARIANTSOURCEBLOCKS`: per block, the blocks whose declared variants
supply its Config. Normally the block itself; for a block every instance of which
inherits, its containers, transitively. It is a `projectCreate` derivation rather
than a `projectOpen` view because `config/createBuildManifest.py` consumes it and
runs inside `runCreateArtifacts`, before `projectOpen` exists. Four consumers read
the one map: the block view's `standaloneVariants` (renamed from
`declaredVariants`, which no longer described what it held), the `newModule`
per-variant scaffold, the build manifest's verilated top set, and
`getRegistrarConfigView`'s `verifRegistrations`.

**The registrations themselves live in the parent-owned trampoline view**, which
already keyed on the (child, parent) pair and already bound the Config the
parent's own instances bind. The inheriting case sources its variants from the
PARENT rather than from the child's containers, so a child reused under two
containers registers each container's variants in that container's own TU instead
of both TUs registering the union. The reverse child-to-containers lookup is still
needed, because the `.sv` tops, the SC wrapper's
templated-ness, the scaffold and the manifest are all block-scoped with no parent
in hand.

**The child's own declared variants are the wrong source**, which the fixture now
pins. `vliLeaf` declares `solo` at algorithm 3; both container variants resolve
something else. With the source map disabled, the run fails with `the container
was configured at algorithm 1 but its leaves resolved 3`.

#### The three questions, answered

1. **Two containers instantiating one inheriting child.** No union to compute: the
   key carries the container's project and variant, and the registrations are
   emitted per parent. Same-named variants across containers are governed by the
   existing duplicate-variant-declaration rule; no new check was added. **Decided
   by the architect**, on the shape of `getRegistrarConfigView`.
2. **The empty-variant registration keeps its existing role**, decided by the
   `verifDefaultRegistration` arm (`pysrc/processYaml.py:1679`), which is
   `containerTyped or emptyVariantAsked` and is unchanged. It is neither removed
   nor repurposed. A single-variant container therefore emits two registrations
   naming the identical class under two keys.
3. **Nested chains compose. MEASURED**, on a throwaway three-level copy of the
   fixture (`vliCont` -> `vliMid` -> `vliLeaf`, both inheriting). The leaf's
   registrations two levels down name `vliContDefaultConfig` / `vliContAltConfig`
   and the grandparent's tops; each level forwards its own `variant`, so the label
   reaches the leaf. Both variants build and run clean, each chain reading back its
   own container's algorithm and width. Not folded into the committed fixture,
   which would then serve two purposes.

#### Found on the way: the connectionMap sizing gate ignores inheritance

`pysrc/processYaml.py`'s connectionMap arm adjudicated an `inheritContainerParam`
child at its OWN declared values while adjudicating the container at its variant,
so a container variant that moves a payload width was REJECTED at db with a
per-field `_bitWidth` disagreement the design does not have. The child's Config IS
the container's; there is nothing to compare. The plain-connection arm ~200 lines
above already skips such an end for exactly this reason and says so; the
connectionMap arm now carries the same skip. **Pre-existing, and invisible until a
container variant moved a width.** The alternative disposition, adjudicating the
child AT the container's variant rather than skipping, is a stronger gate and is
the architect's call.

#### Gate: `unittest/test_inherit_vl_child.py`, extended

The `alt` probe was a recorded failure; it is now a checked run. The fixture's two
container variants differ in BOTH a behavioural knob (VLI_ALGO 1 vs 6) and a
payload width (VLI_WIDTH 8 vs 10), so the two Verilated tops have different pin
widths, which one SystemC wrapper header can only serve as a class template. Each
chain has its own driver and checker at its own width. The RTL and the model leaf
both stamp the algorithm and the width they resolved, and `--vlInst` targets
`uLeafB`, the LAST leaf in the chain, so what the checker reads back is what the
VERILATED leaf stamped rather than what its downstream model twin overwrote.
Exactly one instance is verilated per run (`common/systemc/simController.cpp:68-73`),
so the two variants are two runs.

**Gate evidence, both halves disabled in turn and restored.**

- Constructor forwarding reverted to `""`: all 11 emitted checks still pass, and
  `run-vl-alt` **segfaults**. Registrations alone do not reach the site.
- The source map forced to `{block: [block]}`: five emitted checks fail (no top for
  either container variant, a top for the decoy `solo`, and neither registration),
  and `run-vl-def` fails at runtime with the decoy value, `algorithm 1 but its
  leaves resolved 3`.

#### What the width dimension actually protects, MEASURED

Verilator bakes parameters in at elaboration, so a container variant at a
different width needs its own SV wrapper and its own Verilated model. Verified by
artifact, not by reading the generator: the fixture's
`rundir/build/vl/obj_dir/` holds `vliLeaf_default_hdl_sv_wrapper/` and
`vliLeaf_alt_hdl_sv_wrapper/`, each with its own `V<top>.h`, and their payload
pins differ, `sc_bv<40>` against `sc_bv<42>`.

The fixture is built so a lost payload bit is visible rather than inferred. The
driver drives `1 << (VLI_WIDTH - 1)`, which does not fit the narrow variant; both
leaves ADD `1 << (VLI_WIDTH - 3)` and wrap at their own width, so a narrower
module wraps sooner instead of forwarding a truncation unremarked; and the
checker's expectation is computed entirely from its OWN Config, so it never asks
either leaf what width it thinks it is. The algorithm and width stamps are kept
alongside, because they fail for a different reason.

**The honest result: the width risk is caught structurally, not by that runtime
assertion.** With the fix disabled the failure is a null cast or the decoy
algorithm, never a data fault, because the wrapper is a class template whose
Config fixes both the base class and the payload width. A wrong Config cannot
quietly yield a wrong width; it yields a null `dynamic_pointer_cast`. And a right
Config against the WRONG top does not link: forcing every registration onto the
first variant's top fails at COMPILE, `no matching function for call to object of
type 'sc_out<sc_bv<40>>'` at `verif/vliLeaf_hdl_sc_wrapper.h:47`. The data-path
assertion is worth keeping as the backstop for a bit lost in the BFM or the pin
binding, but it is not what guards the variant selection.

#### Review, 2026-08-20. Findings taken

- **The mixed-site contract is site-owned. FIXED AND EXECUTED 2026-08-23.**
  `calcVariantSourceBlocks` now keeps both the child and inherited container
  sources. `_resolveInstanceConfigFields` forwards the container label at every
  inherited site, while ordinary sites keep their own labels. Verilated and
  tandem registration consume the union. `unittest/test_inherit_vl_child.py`
  now runs the same leaf type at child-owned `solo` and inherited `default` and
  `alt` Configs. The `builder/pro` tandem cell carries the same three Configs.
- **One table, two contracts.** `getRegistrarConfigView` indexed
  `data['parameters']` directly where `getHdlWrapperVariants` treated the row as
  optional, so a container declaring `params:` but no variants raised `KeyError`.
  Both now go through `declaredVariantRows`.
- **The source map counted unreachable instances.** It now intersects with
  `reachableInstanceKeys()`: one standalone-harness row from a referenced child
  project would otherwise have put a block back on its own variants, silently,
  with the original segfault as the failure mode. The hierarchy is rebuilt
  immediately before, because the one standing at that point predates
  `postYamlExternalScript` and omits the synthesized register handlers.
  **MEASURED**: without the rebuild the delta was four files, with it five, the
  extra being `examples/mixed/model/blockG.cppm`, whose synthesized handler is an
  inheriting instance and was being silently excluded.
- Comment trims in four files, and the stale fixture generated regions refreshed
  by the generator (`vliDrv` still published a removed `out2`, `vliLeaf.sv`'s
  struct had no `wid`).

**Resolved 2026-08-23.** `validateVariantSourceLabelCollision` rejects one label
declared by two Config-source blocks before generation. This covers two
containers and the mixed child/container source set. The error names the child,
the label, and both source blocks. Disjoint source labels remain legal.

#### Verification, all from clean

- `make clean -j && make pipeline-test -j` at the base root: **exit 0**, before and
  after.
- `unittest/run_all_tests_parallel.sh`: **110 of 110**, no count warning. No suite
  added, so the guard is unchanged.
- Product tree `make clean -j && make gen -j`, `make -j all` in `rundir`,
  `./build/run debayer`: **all rc 0, "No error"**. The hand-written `setTimedLocal`
  override in `verif/preprocess_hdl_sc_wrapper.h` is byte-identical.
- **Emitted-output delta, 1198 files across `examples/`, `common/` and the product
  tree: FIVE files.** Two are the forwarded variant label at an inheriting site
  (`examples/xprojParam/inhVar/model/xpInhCont.cppm`, and
  `examples/mixed/model/blockG.cppm`, whose synthesised register handler is an
  inheriting instance). Three are the product tree: `model/debayer.cppm` forwards
  the label at its three inheriting sites, and the two VlRegistrar TUs each gain a
  `"default"`-keyed registration.
- **The product tree's registration count went 1 -> 2 per reused child, not 1 as
  expected.** `debayer` declares one variant, so `default` now earns a keyed
  registration alongside the pre-existing empty-key one. Both name the identical
  class; only the key differs, and the keyed one is what the forwarded label
  resolves. Question 2 says the empty-key arm keeps its role, so this is addition,
  not replacement.
- No verilated SV wrapper changed in the product tree: `preprocess` and
  `interpolate` each declare a variant named `default` binding the same resolved
  values as `debayer`'s, so the wrapper variant set is the same set under either
  source.

### Step 11, testbench variant ownership and Config-source validation. COMPLETE IN WORKING TREE 2026-08-31; COMMIT PREPARATION OPEN

A generated testbench builds one DUT at one named Config. It now requires that
variant to be declared by the DUT block itself. A container label is not a DUT
variant merely because the DUT inherits the container's Config.

`projectCreate` runs two validators immediately after
`calcVariantSourceBlocks()`:

- `validateContainerSourcedTestbench` rejects a testbench on a block whose Config
  comes only from containers and which declares no variant of its own. Its
  negative fixture and accepting arm are
  `unittest/test_error_inherit_container_tb.py`, serial suite **19m2e**. The
  accepting arm adds a DUT-owned variant.
- `validateVariantSourceLabelCollision` rejects one label declared by two Config
  source blocks. Its negative fixture and accepting arm are
  `unittest/test_error_variant_label_collision.py`, serial suite **19m2f**. The
  accepting arm gives the two containers disjoint labels.

The three testbench fileMap entries, `testBench`, `tbConfig`, and `tbExternal`,
now carry `dutVariant: true`. `processYaml` uses that field to identify
testbench artifacts for validation, and `newModule` uses it when selecting the
single generated-code variant. The hardcoded `TB_FILE_KEYS` tuple is gone.
`newModule` seeds the testbench from `getQualBlockVariants`, not the broader HDL
wrapper variant set, so the selected variant belongs to the DUT block.

`pysrc/newProject.py` no longer writes its stale 13-entry starter `fileMap`.
The base project owns that map. A new project gets only a commented `includeFW`
override example, and the old tandem entry is gone. This prevents a fresh
project from scaffolding legacy `.h` and `.cpp` model files beside `.cppm` and
then failing `make gen`.

Small fixes in the same work arc make the generated support code self-contained
and deterministic. `templates/systemc/vlRegistrar.py` sorts Config-context
iteration, the tandem header includes `<memory>`, and
`common/systemc/instanceFactory.h` includes `blockBase.h` and `<memory>`
directly. Nested template Config registrations in
`builder/pro/templates/systemc/constructorTandem.py` sort Config expressions and
name their TU-local helpers with deterministic `config0`, `config1`, and later
ordinals. `builder/pro/unittest/test_constructor_tandem.py` checks the text and
compiles, links, and runs two rendered translation units.

**Recorded verification, refreshed 2026-08-31.** Base reports 114/114 unit
suites and 31 successful simulations with 62 `No error` reports.
`unittest/test_inherit_vl_child.py` passes end to end with exact checks for
`solo`, `default`, and `alt` wrapper parameters, registrations, and runtime
values. Local and cross-project `containerParam` Verilated paths pass. The clean
Pro pipeline includes the focused tandem helper test and reports 7 successful
simulations with 14 `No error` reports. The product passes `make clean -j`,
`make gen -j`, and `make -C rundir -j all VL_DUT=1`; its only diagnostic is the
existing unused `bayer_pattern_lookup` warning.

The implementation is complete in the working tree. Commit preparation is not:
the final intended change set is not yet fully staged, committed, or pushed.
Working-tree-versus-HEAD diff checks are clean after EOF normalization. Cached
checks may retain the old whitespace until the normalized files are staged.
Steps 2 through 6 are all closed as of 2026-09-07 (this line listed steps 3 and 4
as open until 2026-09-07, and steps 2 and 5 until later that day). This entry does not
reclassify unrelated loose ends or review findings recorded above.

### Step 12a, rules 1 and 2. LANDED 2026-09-08

The rules iteration of 2026-09-07 settled this step's content; the normative statement is
rules 1 and 2 in [`design-parameter-inheritance.md`](./design-parameter-inheritance.md).
Rule 7 is split out as step 12b, below, and untouched by this entry.

- **Rule 2, the duplicate-in-scope diagnostic for parameter names.** `lookupInScope` returned
  the first match on the include walk with no ambiguity check. `validateBlockParamScopeUniqueness`
  (`pysrc/processYaml.py`), a project-wide pass after `processYamls()`, walks
  `self.yamlContext[context]` for every `blocksparams` row, the block's own file first, and
  collects every qualification whose `constants` table (plain and `ipParameters` rows alike)
  holds the param's name; more than one is `self.logError`ed naming the block, the param, and
  every declaring file, in walk order. It runs after parsing because the per-row hook fires
  while the referring file's `blocks:` section is being parsed and sections are processed in
  authored order, so an `ipParameters:` section below `blocks:` was invisible to it (review
  finding, fixed the same day, pinned by the reordered-section unit cell). Placement confirmed by
  the architect 2026-09-08: included files are always complete when a per-row hook fires, so the
  only rows it cannot see are the referring file's own, and the one shape that hides there (an
  own-file duplicate of an included name, authored below `blocks:`) binds the block to the other
  file's constant without a diagnostic. The project-wide pass stays; a per-row hook was rejected
  for that silent miss, and a second hook on the constant row was judged more machinery than the
  pass.
  `examples/xprojParam/dpTop/yaml/xpDpTop.yaml` declared its
  own `MID_ALGO` while including `xpDpMid.yaml`, which declares another; the customer knob is
  renamed `CUST_ALGO` (design document §2.3) and the fixture's README loses the "include-chain
  shadowing is silent" and "not selectable" paragraphs.
- **Rule 1, the shared declaration (Case 1).** `_validateIpParametersLinkage`, the project-wide
  orphan check requiring a same-file consumer, is deleted along with its call, its
  `self.ipParametersConstants` cache, and `_captureIpParametersConstants`. A second gate found on
  the way, `_process_ipParameters`'s `isIncludedElsewhere and not hasBlocks` check (which rejected
  `ipParameters` in any file included elsewhere with no `blocks:` of its own, unconditionally,
  regardless of consumption), is also deleted: it was the design deviation's actual current
  blocker, not `_validateIpParametersLinkage` alone. A definitions-only file may declare
  `ipParameters` and needs no consumer, anywhere, ever. No replacement orphan check is added.
- **The `uLeafX` decision.** `dpTop`'s `uLeafX` named variant `customer`, which `xpDpMid.yaml`
  declares for `xpDpLeaf`, sourcing `DP_ALGO` from a container parameter named `MID_ALGO`. Renaming
  the wrapper's own knob to `CUST_ALGO` (rule 2) leaves `xpDpWrap` with no `MID_ALGO` to source
  that variant from, which the old, unchanged rule 7 resolution (`selectVariantDescriptor`,
  project-based, not scope-based) never reached anyway. It resolved no descriptor for `uLeafX`
  and fell back to the leaf's default Config. Rather than leave that stale fallback in place, `uLeafX` takes
  a customer-declared variant instead: `variant: leafX`, declared in `xpDpTop.yaml` itself
  (`parameters: xpDpLeaf: leafX: { DP_ALGO: { containerParam: CUST_ALGO }, DP_WIDTH: DP_WIDTH }`),
  which `selectVariantDescriptor` finds directly as the consumer's own project. `uChkX` moves from
  asserting the leaf's declared default (1) to asserting 5, the same value the nested chain
  carries. This is a fixture decision, not a rule-1/2 implementation requirement; rule 7 (step 12b)
  is what would let `uLeafX` keep naming `customer` and still resolve correctly.
- **Fixtures.** `unittest/test_param_scope_uniqueness.py`, three cells against
  `unittest/fixtures/param-scope-dup-own-file`, `param-scope-dup-included-files` and
  `param-scope-shared-definitions`: (a) a name declared in the referring file and an included file,
  rejected naming both, premise asserted, fault-injected legal on a temp copy; (b) a name declared
  in two included files, rejected naming both, premise asserted, fault-injected legal; (c) one
  declaration in a definitions-only included file, consumed by two other including files, builds.
  `examples/xprojParam/cstShared`, modelled on `cstBind`: `xpCstSharedDefs.yaml` (no `blocks:`)
  declares `CSH_WIDTH` plus a parameterizable type/structure/interface over it; `xpCstSharedSrc.yaml`
  and `xpCstSharedChk.yaml` each `include:` it and name it; the top binds both to 12 (not the
  declared default 8), wires src to chk, and each model asserts its own resolved `CSH_WIDTH == 12`
  before driving or checking, the checker voting the test done. Added to the `xproj-const` target.
  Fault-injected: binding 8 in one variant is rejected at `make db` (an interface-layout width
  disagreement between the two ends, rule 9's own check, not a new one), restored and re-verified
  passing. `dpTop`'s fault injection: `uChkX`'s `leafX.DP_ALGO` set to 1 fails the run (the checker's
  assertion never votes, the run times out), restored and re-verified passing.
- **Blast radius, measured.** The corpus scan for every `blocksparams` row whose include chain
  reaches two same-named parameterizable constants found exactly one hit, `dpTop`'s `MID_ALGO`
  (renamed). The unit-suite gate found a second, NOT in the corpus scan because it is
  synthesised at runtime rather than authored: `test_param_cross_project_linkage.py`'s
  `test_same_key_endpoint_with_foreign_same_named_param_rejected` constructs a same-file
  redeclaration of an included name on a temp copy to probe a downstream (unrelated) diagnostic;
  rule 2 now intercepts that construction first, so the test asserts rule 2's rejection instead
  and its docstring records the two diagnostics as distinct checks.
  `test_container_param_cross_project_vl.py` needed its `uLeafX` yaml text anchor and its
  now-unused `xpDpLeaf: leafX:` declaration updated for the same renames, unrelated to rule 2's
  own reach. Both were fixed; no rule was loosened.
- **Also updated.** `rules/skills/design-parameterizable-blocks.md` (the same-file wording, two
  places); `examples/xprojParam/README.md` (the retired orphan-rule paragraph and the shared-
  constant family's table, section and cross-references); `plans/design-parameter-inheritance.md`
  (closed deviation lines, `*not yet enforced*` markers, the `dpTop` note, §5's "waits on plan
  step 12").
- **Gates, VERIFIED BY EXECUTION 2026-09-08.** Unit suite 118/118 (117 plus
  `test_param_scope_uniqueness.py`). `make clean && make pipeline-test -j`: exit 0, 66 "No error"
  (was 64, plus 2 from `cstShared`), zero `ERROR:`, both `varUniqBad`/`cpLayoutBad` OK lines, 5
  total `Deleting file` lines across the clean+pipeline logs (3 from clean). Product: `make clean
  && make gen -j && cd rundir && make -j && ./build/run debayer --verbosity=medium`: exit 0, two
  "No error"; `make -j all VL_DUT=1`: exit 0, no compile errors (this target builds, it does not
  run). `git status --short | wc -l` unchanged at 63; thirteen new paths appeared
  (`model/debayer_regs.cppm`, `model/interpolate.cppm`, `model/preprocess.cppm`,
  `model/raw_video_src.cppm`, six `registrar/debayer_*VariantConfig.cppm`,
  `tb/debayer/debayerConfig.cpp`, `tb/debayer/debayerTestbench.cppm`,
  `verif/debayer_hdl_sc_wrapper.h`), all step 15's per-block Config-module split reaching files
  this session's `make clean && make gen` was the first to regenerate since step 15 landed, not a
  step 12a effect. Pro: `make -C builder/pro pipeline-test -j` exit 0, 14 "No error";
  `test_constructor_tandem.py` PASS.
- **Sequencing.** Independent of steps 13 through 15.
- **Follow-up (d), a stale generated registrar shadows a container-typed site.** `make gen` does
  not remove a registrar file left behind by a renamed instance, and when its exact key still
  matches a container-typed site, it shadows the templated construction and the generated site
  dereferences a null `dynamic_pointer_cast`. Seen in `dpTop` when `uLeafX` moved to `leafX`; the
  stale file was deleted by hand. Candidate guards: a gen-time report of files under `registrar/`
  absent from `.gen/build.mk`, and a run-time assert on the cast at the generated site.
  Facts gathered 2026-09-10 (VERIFIED BY CODE READING): `common/systemc/instanceFactory.cpp` ~86-98
  consults the exact `Key{blockType, variant, projectName}` first, then the container-supplied
  factory, then the empty-variant entry, so a stale exact key always wins; `templates/systemc/constructor.py`
  ~235 emits the `dynamic_pointer_cast` with no null check; `pysrc/migrateOrphans.py` ~343 excludes
  registrar-mode entries from the sweep by design; no unit test covers the shape. **RULED
  2026-09-10:** `make newmodule` may delete stale registrar files (they carry no user content), and
  the manifest step warns about a registrar file it does not list, recommending that cleanup. No
  run-time assert was asked for. **LANDED 2026-09-10 (with the scaffold-definition fix below).**
  `artifactPaths.getRegistrarFiles(prj, blockCondData, filemap)` is the one owner of the expected
  registrar file set and the owned registrar directories; `createBuildManifest.py` reads it after its
  record loops and emits one `printWarning` per generated file (marker-classified through
  `migrateCommon.classifyGeneratedDir`) the set does not name, plus a closing line recommending
  `make newmodule`; `newModule.cleanup_stale_registrar_files` deletes the same set after the
  registrar scaffold pass. `a2c-common.mk` documents the deletion. Guard:
  `unittest/test_stale_registrar_cleanup.py` (block rename in the `inherit-vl-child` fixture; asserts
  the warning text, the recommendation, removal of both `.cppm` and `.cpp` registrar files, and
  silence afterwards); runner count 122. The manifest keeps its own foreign-inclusive compile-set
  derivation because the view returns a flat owned path set; sharing would need per-artifact rows
  (`fileDef`, path, layout, owner), recorded as a follow-up. Gates on the final tree: unit 122/122;
  base pipeline exit 0, 66 `No error`, 0 `ERROR:`, 3 `OK:`; pro 14 `No error`; product gen diff-stat
  builder and isp_shared only, model and `VL_DUT=1` runs two `No error` each; zero stale warnings in
  pro and product. `.gen/build.mk` byte-identical on simple_ip, dpTop, inhTandem.
  **Warnings the base pipeline raised, and what they are.** (1) TRUE POSITIVES:
  `examples/simple_ip/ip/registrar/ip_ipRegsVariantConfig.cppm` and
  `examples/ip_test/ip/registrar/ip_ipRegsVariantConfig.cppm`, tracked since d06e20f, absent from
  their `.gen/build.mk`, compiled only through the directory glob, unneeded since the synthesised
  register handler took `inheritContainerParam` (2026-08-20); nothing imports `ip.ipRegs.config`.
  REMOVED 2026-09-10 on the user's instruction by `make newmodule` in the OWNING projects,
  `examples/ip_test/ip` and `examples/simple_ip/ip` (both are vendored sub-projects with their own
  project file and db; the parent's newmodule skips their artifacts by the ownership gate, so the
  parent run is a no-op for them, which is by design). (2) FALSE POSITIVE, BLOCKING:
  `examples/xif/registrar/xif_xif_tbVariantConfig.cppm` is imported from a generated region of
  `tb/dut/dutExternal.cppm` (`ownConfigModule` at `processYaml.py` ~1516 is gated on
  `hasOwnParams` only, with a comment saying a params-declaring harness with no model still imports
  its own Config module), but the `foreignConfig` fileMap entry (`config/project.yaml` ~134) scaffolds
  and manifests that module only under `cond: {hasMdl, hasTb}` and `condAnd: {hasOwnParams}`.
  `xif_tb` has both flags false, so the emitter imports a module that newmodule never scaffolds and
  the manifest never lists; the tracked file survives only because gen rewrites files that exist.
  Under the new cleanup, `make newmodule` (and so `make migrate`) in xif would delete it and break the
  build. Pre-existing mismatch, surfaced by the new check. **RULING NEEDED:** align the fileMap
  condition with the emitter (drop the hasMdl/hasTb `cond`, keep `condAnd: {hasOwnParams: true}`;
  the only other blocks with that shape are the three RTL-only blocks in
  `examples/xprojParam/inhLayout`, which would gain Config modules), or gate the import the same way
  (breaks xif's External, which binds `xif_xif_tbTbV0Config`). **RULED 2026-09-10** ("we cannot
  need a file but not scaffold it"): fix the scaffold definition. IN PROGRESS: the fileMap entry drops
  the hasMdl/hasTb `cond` (keeps `condAnd: {hasOwnParams: true}`), and `ownConfigModule` derives the
  import from that fileMap entry through `fileMapCondMatch`, so need and scaffold read one predicate.
  inhLayout's three RTL-only params blocks gain Config modules (new files for the user to commit); a
  grep assertion on the `xif` make target pins the manifest listing. **LANDED 2026-09-10.**
  `config/project.yaml` `foreignConfig` entry: `condAnd: {hasOwnParams: true}` only; the sibling
  `vlSvWrapForeign` entry never had the mismatch. `projectOpen.__init__` selects that entry once by its
  flags (`configModuleFileDef`); `getBDConfigInfo` decides `ownConfigModule` with `fileMapCondMatch`
  on a row from the new `getBlockCondRow(qualBlock)` view helper, which newModule's `blockCondData`
  now also uses. `Makefile` `xif:` runs `db` and asserts `A2C_SC_GEN_FILES` lists
  `registrar/xif_xif_tbVariantConfig.cppm`. Skill `design-parameterizable-blocks` gained the
  emission sentence and its rule 1 / `ipParameters` text now match plan rule 1 (the drift noted at
  12a (e) is closed). Census: xif_tb and inhLayout's three blocks are the only params blocks with
  neither hasMdl nor hasTb that reach newmodule; inhLayout (db-only fixture) gained nine scaffolded
  files (three Config modules plus model/rtl/rundir baseline), untracked, for the user to commit or
  delete as with cpLayout. Final gates on the whole tree: unit 122/122; base pipeline exit 0, 66
  `No error`, 0 `ERROR:`, 3 `OK:`, 0 stale-registrar warnings; pro 14 `No error`, 0 warnings;
  product gen diff-stat builder and isp_shared only, 0 warnings, model and `VL_DUT=1` runs two
  `No error` each; `.gen/build.mk` byte-identical on simple_ip and dpTop.
  **Follow-ups opened here, OPEN:** (i) the manifest still derives its compile set itself; sharing
  needs the view to return per-artifact rows (`fileDef`, path, layout, owner). (ii) The create-side
  cond-row copies (`createBuildManifest.condRow`, `migrateOrphans.py` ~322) should read one helper
  like `getBlockCondRow`. (iii) `processYaml.py` ~5685 still hardcodes `fileMap['foreignConfig']`
  by key name.
- **artifactPaths extraction, LANDED 2026-09-10.** The three path-resolution functions the stale
  registrar work made shared (`expandNewModulePath`, `fileMapCondMatch`, `getRegistrarFiles`, 122
  lines) moved out of `pysrc/processYaml.py` into `pysrc/artifactPaths.py`, whose only imports are
  `os` and the two error helpers from `arch2codeHelper`, so no import cycle. Bodies are byte-identical
  to the deleted region (diffed against `HEAD:pysrc/processYaml.py` lines 135-256). `processYaml`
  imports the module qualified and does not re-export the names; the ten callers
  (`config/createBuildManifest.py`, `pysrc/newModule.py`, the five `migrate*.py` users,
  `unittest/test_nested_ownership.py`, and the six sites inside `processYaml` itself) import from
  `pysrc.artifactPaths`. `createBuildManifest.py` no longer imports `processYaml` at all. Review
  applied: shorter module docstring, the redundant `_condMatch` comment deleted, continuation lines
  realigned. `plan-split-processyaml.md` proposes a broader `projectShared` module; this is the
  narrower cohesive slice and does not preclude that split. Gates, VERIFIED BY EXECUTION
  2026-09-10: unit suite 122 of 122; base pipeline exit 0, 66 "No error", 0 `ERROR:`, 3 `OK:`, 0
  stale registrar warnings; pro pipeline exit 0, 14 "No error", 0 warnings; product
  `make clean && make gen -j` diff-stat only the `builder` and `isp_shared` rows, model run and
  `VL_DUT=1` run (`--vlInst=tb.debayer`) two "No error" each, 0 stale registrar warnings.
- **Follow-up (e), TESTED 2026-09-10.** The endpoint diagnostic "The block declares
  same-named parameter(s) from other file(s)" (`pysrc/processYaml.py` ~6081-6089) had no test
  reaching it. Rule 2 makes the shape legal (a same-named declaration in a file the block does not
  reach is a different parameter, not a collision), so the note stays. New fixture
  `unittest/fixtures/param-same-named-endpoint` (consumer includes only file B; the connection's
  `dataIf` is sized by file A's `X`) and cell `test_param_interface_endpoint_same_named_foreign_param`
  in `test_param_const_linkage.py` assert the rejection text names both declaring files, then
  fault-inject the include to A and assert the build succeeds. The review confirmed
  `validateBlockParamScopeUniqueness` cannot fire for the fixture and no earlier validator rejects
  it. Skill drift found on the way, OPEN: `design-parameterizable-blocks` rule 1 still says root
  parameters live in "the block's own YAML file"; plan rule 1 dropped that on 2026-09-08.

### Step 12b, rule 7, scope resolution of a variant label. LANDED 2026-09-08

The normative statement is rule 7 in [`design-parameter-inheritance.md`](./design-parameter-inheritance.md).

- **Rule 7, scope resolution of a variant label.** `selectVariantDescriptor` selected by project
  (consumer's own, config-context owner, block owner) and never rejected two visible
  declarations. It is deleted, replaced by `resolveInstanceVariantDeclarers`
  (`pysrc/processYaml.py`), a project-wide pass after `processYamls()`, modelled on
  `validateBlockParamScopeUniqueness`: for every instance naming a variant (not
  `inheritContainerParam`), it walks `self.yamlContext[context]` (the instance's own file, then
  its include chain) and collects every file whose `parametersvariants` rows declare that
  (block, variant). Exactly one is required; zero is rejected naming the out-of-scope declarer(s)
  if any exist, otherwise saying no file declares it; more than one names every declaring file.
  The result, `INSTANCEVARIANTDECLARERS` (`{instanceKey: declaringProject}`), is persisted and read
  by a new `projectOpen` helper, `_instanceVariantDescriptor`, which is the one place an instance's
  descriptor is now resolved: the entry of `self.variantConfigDescriptors[blockKey]` whose
  `variant` and `declaringProject` match the recorded declarer. Every call site that used to pass
  `(variant, consumerProject, blockProject)` to `selectVariantDescriptor` now passes the instance
  data instead (`_resolveInstanceConfigFields`, `_resolveSvInstanceParams`,
  `calcRegistrarPairs.selectedDescriptor`). `getStandaloneVariants` and
  `_declaredVariantConfigEntries` are a different shape: they enumerate every DECLARED label
  across a block's variant sources, whether or not any instance selects it, so they resolve
  through `_declaredDescriptorsByLabel` (groups `self.variantConfigDescriptors[blockKey]` by
  label, one entry per declaring project) and `_selectDeclaredDescriptor` (the enumerating
  build's own project's entry when present, otherwise the group's remaining entry).
  `validateVariantLabelBuildOwnership`, run in `projectCreate` right after
  `calcVariantConfigDescriptors`, rejects a label two or more foreign projects declare when this
  build declares none of them, naming the block, the label and every declaring project, so the
  fallback arm always has exactly one entry left to take. An earlier version of this enumeration
  read the label-collapsed `declaredVariantRows()` view instead, which silently drops one
  project's declaration when the build project declares neither of two foreign ones; a later
  review replaced it with the descriptor-grouped form above and added the create-time rejection.
  `BLOCKPARAMDEFAULTS` is removed: its two remaining readers
  (`calcRegistrarPairs`, `_resolveSvInstanceParams`) took `values: {}` for a params-less child and
  the default Config's own values for a params-declaring one with no descriptor
  (`inheritContainerParam`, whose params all forward the container's same-named symbol instead of
  reading `values`); both now read `DEFAULTCONFIGDESCRIPTORS[blockKey]['values']`, guarded the same
  way `calcVariantConfigDescriptors` guards populating it (`blockKey in paramsByBlock`). `isForeign`
  stays on the descriptor: `calcRegistrarPairs` still reads it to name a Verilated wrapper's
  foreign-vs-native fileStub. D8's build-wide same-project uniqueness check stays untouched.
- **Proves it.** `unittest/test_variant_scope_resolution.py`: (a) a label visible in the instance's
  own file and an included file, rejected naming both (`fixtures/param-variant-two-declarers`,
  unmodified); (b) a label declared only downstream of the instance's own file, rejected naming
  the out-of-scope declarer (new fixture `fixtures/variant-scope-out-of-range`, modelled on the
  pre-migration `ip_test` bridge shape); (c) the same fixture with the declaration moved into the
  instance's own file, builds, and the persisted `INSTANCEVARIANTDECLARERS` entry names that
  file's project. Each rejection cell asserts its premise and is fault-injected into a legal shape
  on a temp copy, confirming the build then succeeds.
- **`ip_test` migration.** `examples/ip_test/bridge/yaml/ipBridge.yaml` instantiates `uBridgeIp1`
  of `ip` at `variant1`, authored inside `ipBridge.yaml` itself; its own scope (itself plus its own
  direct includes, `shared_types.yaml` and `ipVariants.yaml`) declared only `variant0`. `variant1`
  was declared downstream, identically, in `bridge/yaml/bridgeStdTop.yaml` and
  `top/yaml/ip_top.yaml`, both of which include `ipBridge.yaml` rather than the reverse, so the
  instance saw zero visible declarations. The declaration moves into `ipBridge.yaml` itself (the
  file that instantiates the reused block declares the variant it instantiates); the two
  downstream copies are deleted. `ip_top.yaml`'s own `uIp1` (also naming `variant1`) then resolves
  the bridge's declaration through its direct include of `ipBridge.yaml`, one hop, within scope.
  `bridgeStdTop.yaml`'s now-unused direct include of `ipVariants.yaml` (kept only for the deleted
  binding's block-type resolution) is removed with it. The emitted Config for `variant1` is now
  `ipBridge_ipVariant1Config` (`bridge/registrar/ipBridge_ipVariantConfig.cppm`,
  `export module ipBridge.ip.config;`), and `ip_top.cppm`/`top/registrar/ipRegistrar.cppm` import
  and spell it instead of the old `ip_test_ipVariant1Config`. `make gen` does not remove a
  registrar file a renamed/relocated declaration leaves behind (the same generator gap step 12a's
  record notes for `xpDpLeafRegistrar.cppm`): `top/registrar/ip_test_ipVariantConfig.cppm`, the
  ip_test project's now-empty Config module for a variant it no longer declares, was left in place
  by `make gen` and deleted by hand after confirming nothing imports it. The three "PROTOTYPE (P1)"
  comments (`ip/yaml/ipVariants.yaml`, `top/yaml/ip_top.yaml`, and the related duplication
  rationale in `bridge/yaml/bridgeStdTop.yaml`) are rewritten to state the standing shape instead
  of the retired experiment. No hand-written file outside a generated region spells the old Config
  name (checked by grep).
- **Blast radius, measured 2026-09-08 over every example, pro example, unit fixture and the
  product YAML.** `examples/ip_test`'s bridge instance is the one authored shape needing a fixture
  move (above). `unittest/fixtures/param-variant-two-declarers` sees two declarations, as recorded;
  it becomes a rejection fixture (below). `examples/xprojParam/varUniqBad` is already rejected by
  D8. `unittest/fixtures/variant-two-integrators` is sibling-scoped (`xviTop` and `xviMid` never
  include each other; each build's own instance sees exactly its own project's declaration) and
  unaffected in resolution; it pins the declared-variant iteration `getStandaloneVariants`/
  `getDeclaredVariantConfigs` perform, which needed its own fix (below). The product tree's three
  variant selections (`u_raw_src`, `u_debayer`, `u_rgb_sink` in `debayer_tb.yaml`) each resolve
  within scope with exactly one visible declaration; unaffected. A fourth hit, not in the
  authored-corpus scan because it is constructed at runtime: `test_param_cross_project_linkage.py`'s
  `test_registrar_requirements_exclude_unreachable_child_harnesses` appends an instance naming
  `variant: v0` directly into a child project's own file, where `v0` is declared only in the
  downstream assembler that includes it; rule 7 now rejects that construction, so the appended
  instance instead declares and names its own `harness0` label, in its own file, matching the
  point the test makes (registrar requirements exclude an unreachable instance) without depending
  on a label declared out of its scope. Nothing else in the corpus sees zero or two declarations.
- **`getStandaloneVariants`/`getDeclaredVariantConfigs`, the two-integrators finding.** These
  enumerate every label a block's variant sources declare, independent of any instance, to offer a
  standalone Verilated wrapper by name (`--variant=`) whether or not this build's tree instantiates
  it. The declared-row view collapses two projects' bindings of one label onto whichever was parsed
  last (`design-parameter-inheritance.md`'s "Project-qualified parameter bindings" note), so reading
  a value off it directly, rather than through a resolved descriptor, would have `xviTop`'s
  standalone wrapper for label `v0` carry `xviMid`'s value or vice versa depending on parse order.
  `_declaredDescriptorsByLabel`/`_selectDeclaredDescriptor` avoid this: they enumerate straight
  from `self.variantConfigDescriptors[blockKey]`, grouped by label, and prefer the enumerating
  build's own project's descriptor when one exists. `calcRegistrarPairs`, driven by instances
  rather than declared labels, is what keeps `xviMid`'s `vMid` out of `xviTop`'s artefacts in the
  first place; this pair of helpers only decides which project's descriptor a shared label
  resolves to once enumerated. Verified against
  `unittest/test_variant_two_integrators.py`: `xviTop`'s own build emits `v0` at its own gain (3)
  and `vTop` at 9, never `xviMid`'s `vMid`; `xviMid`'s emits `v0` at its own gain (7) and `vMid` at
  5, never `xviTop`'s `vTop`.
- **Gates, VERIFIED BY EXECUTION 2026-09-08.** Unit suite 118/118 (one retired,
  `test_variant_scope_resolution.py` replacing `test_param_variant_declarer_precedence.py`, so the
  count is unchanged from the 12a baseline). The one corpus fixture the blast-radius bullet above
  found needing a fix is fixed. `make clean && make pipeline-test -j`: exit 0, 66 "No error" (unchanged from the 12a baseline),
  zero `ERROR:`, both `varUniqBad`/`cpLayoutBad` OK lines, 5 total `Deleting file` lines across the
  clean+pipeline logs (3 from clean). Product: `make clean && make gen -j && cd rundir && make -j
  && ./build/run debayer --verbosity=medium`: exit 0, two "No error", `test_debayer_structs`
  executed; `make -j all VL_DUT=1`: exit 0, no compile errors; `git status --short | wc -l`
  unchanged at 63 (no paths beyond the 12a baseline's own thirteen). Pro: `make -C builder/pro
  pipeline-test -j` exit 0, 14 "No error"; `test_constructor_tandem.py` PASS.
- **Review fix-up, 2026-09-08.** `getStandaloneVariants`/`_declaredVariantConfigEntries` read
  `declaredVariantRows()`, the label-collapsed nested view, as their fallback when the enumerating
  build's own project declared nothing: a label two foreign projects both declare then resolved to
  whichever one the collapse happened to keep, silently dropping the other. Fixed by enumerating
  `self.variantConfigDescriptors[blockKey]` directly, grouped by label
  (`_declaredDescriptorsByLabel`/`_selectDeclaredDescriptor`, replacing `_declaredVariantDescriptor`),
  and rejecting the ambiguous case at create time instead of silently picking one:
  `validateVariantLabelBuildOwnership`, run right after `calcVariantConfigDescriptors`, errors
  naming the block, the label and every declaring project when two or more foreign projects
  declare a label this build declares none of. Proved on a new cell in
  `unittest/test_variant_two_integrators.py` (a third project, `both/`, composing both integrators
  through `xviTopProject.yaml`'s own closure and declaring no `v0` of its own; rejected naming both
  `xviTop` and `xviMid`, and builds once `xviBothOwn.yaml` declares `v0` itself).
  `resolveInstanceVariantDeclarers`'s zero-declarer message named no file for an instance whose
  block declares no `params:` at all; it now says so instead of "no file declares". Three dead
  fallback arms removed (`calcRegistrarPairs`'s non-container `values` ternary,
  `_resolveSvInstanceParams`'s `inheritContainerParam` branch, `constructorTandem.py`'s
  `if desc else` guard), each unreachable given the validation already in place. The bridge
  migration in step 12b's own entry above dropped `bridgeStdTop.yaml`'s direct include of
  `ipVariants.yaml` as now-unused, but `ip.yaml` (which declares the `ip_package` RTL package)
  sits three include hops from
  `bridgeStdTop.yaml` once that direct include is gone, one past the two-level visibility every
  scoped lookup gets, which silently dropped `ip_package.sv` from `rtl.f`; the include is restored,
  with a comment stating why. A new cell in `unittest/test_variant_scope_resolution.py` exercises
  the out-of-scope message's until-now-untested multi-declarer branch (a second file added to a
  temp copy of `variant-scope-out-of-range`, declaring the same out-of-scope label; rejected naming
  both). "Rule 7" comments and doc mentions of the include chain now describe the two-level
  visibility directly (file, its includes, their includes) instead of citing the rule number or
  "include chain", matching `GENERATOR_ARCHITECTURE.md` §4. `unittest/test_eval_cpp_emit.py`'s
  derived-member cell pointed at `ip_test_ipVariant1Config`, a struct step 12b's own migration
  retired, so its second assertion loop passed on an absent struct; it now renders the bridge
  project's `ipBridge_ipVariant1Config` and fails if that struct is absent (confirmed by reverting
  the name on a copy). All four gates re-run clean: unit suite 118/118 (two cells added to existing
  files, `test_variant_two_integrators.py` and `test_variant_scope_resolution.py`; no new file, so
  the suite count is unchanged); `make clean && make pipeline-test -j` exit 0, 66 "No error",
  zero `ERROR:`, both OK lines; product `make clean &&
  make gen -j && cd rundir && make -j && ./build/run debayer --verbosity=medium && make -j all
  VL_DUT=1` exit 0, two "No error", `git status --short | wc -l` unchanged at 63; pro `make -C
  builder/pro pipeline-test -j` exit 0, 14 "No error", `test_constructor_tandem.py` PASS.
- **Sequencing.** Independent of steps 13 through 15.

### Step 13, the product tree moves off `inheritContainerParam`. DECIDED 2026-09-07 (user); LANDED 2026-09-08; REVERTED 2026-09-09 (user)

- **Reverted 2026-09-09 (user).** Landing it required explicit `ports:` on two self-contained blocks purely so the container would emit thunkers between distinct Config types, and a thunker on the sibling stream. The user ruled that self-contained blocks do not declare `ports:` for internal plumbing and that the product keeps `inheritContainerParam`; `yaml/debayer.yaml` is back at its pre-step-13 content and the product regenerates byte-identical to HEAD. The three generator fixes found on the way and their fixtures stand. A follow-on proposal, payload types keyed on parameter values so same-valued Configs bind directly, is recorded in [`design-parameter-inheritance.md`](./design-parameter-inheritance.md) as a direction, not yet a step.

The record below is kept as history: what landing this step required and found, before the revert.

`/work/ws/debayer/yaml/debayer.yaml`'s `u_preprocess` and `u_interpolate` held `inheritContainerParam`. Each became a declared variant every one of whose parameters is `containerParam:` sourced from `debayer`'s same-named parameter. `inheritContainerParam` itself stays supported; this migrates one design, it does not retire the mechanism, and the synthesised register handler keeps using it (step 7, "The synthesised register handler now inherits its container's Config").

A step planned as YAML-only needed three generator fixes on the way, each found by reproducing the failure, reading the generator, and fixing it under the same constraint (product-tree edits confined to `yaml/debayer.yaml`):

1. **Inferred-port thunker gap.** The container-boundary connectionMap wiring (`u_preprocess->video_raw_stream(this->video_raw_stream)` in `model/debayer.cppm`) bound the container's port directly onto the child's, with no thunker, once the child's Config became a distinct nested type. Root cause: in the cross-interface annotation (`pysrc/processYaml.py`, `annotate()`), `declaredChildInterfaceKey(instanceKey, portName)` returns nothing for a top-down inferred port, so `annotate()` returns `None` and no thunker is emitted, even though `bindsDirectly` would have found the Config type identity differs. `dpMid` builds because `xpDpLeaf` declares explicit `ports:`; `preprocess` and `interpolate` did not. Fixed in YAML, not the generator, per the design-parameterizable-blocks skill's rule 5: `preprocess` and `interpolate` each gained an explicit `ports:` map keyed by the names their top-down inferred ports already carried. **This defect itself is OPEN**, recorded below; the YAML fix sidesteps it for this design but the generator gap remains.
2. **Partial-ports completeness rejected an undeclarable register-connection port.** Adding explicit `ports:` to `interpolate` made `validateDeclaredPorts` demand a `ports:` entry for `bayer_pattern`, a plain `registerConnections:` row, but the schema requires `ports:`'s `interface:` field to name a real `interfaces:` entry, and a register connection is never declared through that mechanism, so no legal entry exists. Fixed in the generator: `validateDeclaredPorts` (`pysrc/processYaml.py`, the completeness loop) now exempts an inferred port whose `sourceType` is `'registers'` or `'memories'`, the same way it already exempts `registerPorts:` names and connectionMap-declared boundary ports. Fixture: `unittest/test_ports_register_memory_connections_independent.py`.
3. **The VL build manifest and the wrapper renderer both assumed a container-sourced variant is never a block's ONLY variant.** `templates/systemVerilog/module_hdl_wrapper.py::render_sv` rendered pair-specific concrete registrations only inside the standalone arm, so a variant that is fully container-sourced (excluded from `standaloneVariants`) fell to `render_non_parameterizable`, discarding the pair-specific module the parent-child pair contract already computed. `config/createBuildManifest.py`'s block-mode verilated-top loop recorded a bare `<block>_hdl_sv_wrapper` top whenever a `hasOwnParams` block's every declared variant is container-sourced, because its variant list was empty and it fell back to the un-suffixed stub, even though the pair loop already records the real top against the same physical file. Both fixed in the generator. Fixture: `unittest/test_container_param_vl_wrapper_migration.py`, which reproduces the exact migration (scaffold the wrapper while the variant still looks standalone, then edit it to `containerParam:` in place, without re-scaffolding) that made the defect reachable only once a design does exactly what this step does.

- **Defect found on the way, OPEN.** A params-declaring child whose ports are top-down inferred receives no cross-interface annotation (`annotate()` returns `None` when `declaredChildInterfaceKey()` is empty), so when its Config type differs from the channel's the container binds the port directly and the failure surfaces as a C++ compile error, not a db diagnostic. Either emit the thunker for inferred ports too, or reject the shape at db naming the block and the skill rule. No fixture; the product tree before this step was the only instance.
- **What it buys.** The templated-Config shape of step 7c on the product tree, and the product tree's independence from the whole-Config shorthand. Layout adjudication on the two connections is no longer at stake: step 14 adjudicates them on inheritContainerParam already.
- **The YAML, as landed.** `u_preprocess`/`u_interpolate` on `variant: default`, every `preprocess`/`interpolate` parameter row rebound to `{ containerParam: <same name> }`. `preprocess` and `interpolate` each gained an explicit `ports:` map (rule 5): `video_raw_stream`/`bayer_preprocess_stream` for `preprocess`, `bayer_preprocess_stream`/`video_rgb_stream` for `interpolate`; `interpolate`'s `bayer_pattern` register connection stays out of that map (fix 2 exempts it). The two block-level comments and the comment above `parameters:` were reworded to state the standing behaviour.
- **What changed in the emitted product.** The children's Config becomes `debayer_<child>DefaultConfig<Config>` (a template over the container's Config, step 7c) instead of the container's bare `Config`; the VL registrar binds the forwarded container label to that nested Config (step 10). `model/debayer.cppm` gained three `rdy_vld_port_thunker` members (`thunker_bayer_preprocess_stream_u_preprocess`, `thunker_u_preprocess`, `thunker_u_interpolate`) bridging the previously-direct binds. User code in `model/preprocess.cppm` and `model/interpolate.cppm` reads `Config::<param>` and did not move, because the member names are the same; both files are untouched (0 diff).

**Emitted-output delta, `make clean && make gen -j`, exit 0.** 11 generated files changed, plus the hand-edited `yaml/debayer.yaml`:

| File | Kind of change |
| :-- | :-- |
| `registrar/debayer_preprocessVariantConfig.cppm` | `debayer_preprocessDefaultConfig` struct becomes `template<typename ContainerConfig> struct ... { static constexpr ... = ContainerConfig::<member>; }` (step 7c) |
| `registrar/debayer_interpolateVariantConfig.cppm` | same, for `debayer_interpolateDefaultConfig` |
| `model/debayer.cppm` | config imports; `#include "rdy_vld_port_thunker.h"`; the channel member, the two instance members, and their constructor lines retype to the nested Config; three `rdy_vld_port_thunker` members and their constructor-init-list entries replace the direct port binds the constructor body carried |
| `registrar/preprocessVlRegistrar.cpp` | config import; VL registration binds `debayer_preprocessDefaultConfig<debayer_debayerDefaultConfig>` in place of the bare `debayer_debayerDefaultConfig` (step 10, forwarded parent label) |
| `registrar/interpolateVlRegistrar.cpp` | same, for interpolate |
| `base/preprocessTandem.h` | gains `import debayer.preprocess.config;` |
| `base/preprocessTandem.cpp` | tandem factory registration Config type nests the same way, `preprocessTandem<debayer_preprocessDefaultConfig<debayer_debayerDefaultConfig>>` |
| `base/interpolateTandem.h` | gains `import debayer.interpolate.config;` |
| `base/interpolateTandem.cpp` | same nesting, for interpolate |
| `verif/preprocess_default_hdl_sv_wrapper.sv` | no longer standalone-instantiable (`containerParam`-only parameters cannot resolve without a container): drops its own `localparam`s and its separate standalone module, and defines exactly one module, `p7_debayer_c18_debayer_preprocess_default_hdl_sv_wrapper`, binding the resolved literals (8, 4, 3840, 2160, 5) onto the `preprocess_hdl_sv_wrapper` body |
| `verif/interpolate_default_hdl_sv_wrapper.sv` | same, for interpolate: one module, `p7_debayer_c19_debayer_interpolate_default_hdl_sv_wrapper`, wiring `debayer_interpolate` |
| `yaml/debayer.yaml` | the hand edit |
| `isp_shared/isp_shared.db` | rebuilt by every db build and shows as modified inside the submodule; not part of this step |

`rtl/*.sv`, `model/preprocess.cppm`, `model/interpolate.cppm`: 0 files changed, consistent with "the SV side was already right" (step 8's history). `verif/preprocess_hdl_sc_wrapper.h` (the hand-written HDL bridge wrapper carrying the `setTimedLocal` override): **byte-identical**, md5 `9ae8e04f549fdcc4d57bedfa7f539a61` before and after. `.gen/build.mk`'s `A2C_VL_TOPS` carries exactly three entries: `debayer_default_hdl_sv_wrapper`, `p7_debayer_c18_debayer_preprocess_default_hdl_sv_wrapper`, `p7_debayer_c19_debayer_interpolate_default_hdl_sv_wrapper`; no phantom bare `preprocess_hdl_sv_wrapper` or `interpolate_hdl_sv_wrapper` entry.

**Gates, VERIFIED BY EXECUTION 2026-09-08.**

Generator fixes, from `builder/base`:
1. `unittest/run_all_tests_parallel.sh`: 120 of 120 passed (118 + the two new cells for fixes 2 and 3).
2. `make clean && make pipeline-test -j`: exit 0, 66 "No error", 0 `ERROR:`, 3 `OK:` lines (`varUniqBad`, `cpLayoutBad`, `inhLayoutBad`).
3. `make -C builder/pro pipeline-test -j`: exit 0, 14 "No error" (the wrapper template is shared; `inhTandem` exercises it).

Product, from `/work/ws/debayer`:
4. `make clean && make gen -j`: exit 0. `git diff --stat rtl/ model/preprocess.cppm model/interpolate.cppm` empty. Wrapper md5 unchanged. `.gen/build.mk` VL tops as above; `verif/preprocess_default_hdl_sv_wrapper.sv` defines exactly the `p7_..._preprocess_default_hdl_sv_wrapper` module with the resolved literals.
5. `cd rundir && make -j`: exit 0.
6. `./build/run debayer --verbosity=medium`: exit 0, two "No error" lines, `test_debayer_structs` executed.
7. `make -j all VL_DUT=1` in `rundir`: exit 0.
8. The VL run (`rundir/Makefile` carries no `run-vl` target for this project; `./build/run debayer --verbosity=medium --vlInst=tb.debayer`, the binary's own hierarchy-path selector, against the `VL_DUT=1` build): exit 0, two "No error" lines.

**Sequencing record, for what each attempt found.** First attempt (YAML only): gate 1 passed; `rundir`'s build failed on defect 1 above, a direct `sc_port` bind onto a now-distinct Config type at the container-boundary connectionMap. Second attempt (rule 5's explicit `ports:` added): `make db` failed on defect 2, the undeclarable register-connection port. Generator fix for defect 2 landed and gated. Third attempt (both YAML pieces together): gates 1 through 3 passed with the thunkers now present; gate 4 (`VL_DUT=1`) failed with `%Error: Cannot find file containing module` and `--top-module ... was not found in design`, defect 3, the stale VL top/file manifest. Generator fixes for defect 3 landed and gated. Fourth attempt: all gates pass, as recorded above.

- **Follow-up, LANDED 2026-09-10.** `pysrc/newModule.py` ~90-96 scaffolded a bare `<block>_hdl_sv_wrapper.sv` for a `hasVl` block with no standalone variant. A design authored container-sourced from the start got that file, `render_sv` rendered it as a non-parameterizable module over a default-less DUT, and the manifest left it out of the top set silently. The block-mode scaffold loop now takes the same branch as `createBuildManifest.py` (`hasOwnParams` and no standalone variants: no bare top); the review confirmed both read `blocksparams` and the standalone set from the same views, so they cannot diverge. `unittest/test_container_param_vl_wrapper_migration.py` gained a from-scratch cell (container-sourced tail written directly, `make clean db newmodule gen`, asserts no bare wrapper on disk, one pair-qualified top in the manifest and the wrapper file); the defect was reproduced with the branch commented out before the assertions were fixed. Gates on the final tree: unit 121/121, base pipeline exit 0 with 66 `No error`, 0 `ERROR:`, 3 `OK:`; pro pipeline 14 `No error`; product gen diff-stat only builder and isp_shared rows, model run and `VL_DUT=1` run two `No error` each.

### Step 14, the connectionMap arm adjudicates an inheriting child instead of skipping it. LANDED 2026-09-08

Step 10 found the connectionMap sizing arm rejecting an `inheritContainerParam` child at its own declared values and fixed it by adding the same skip the plain-connection arm already had ("Found on the way: the connectionMap sizing gate ignores inheritance"). The skip means a junction between an inheriting child and a sibling bound at a literal is not checked at all: container at 16, inheriting child therefore at 16, sibling at a literal 8, and `make db` passes. Adjudicating the inheriting end at the container's variant, which is what the site-keyed index of step 7b already does for a `containerParam` end, catches it.

- **The shape landed, as a structured site key.** A first version keyed `SiteBindingIndex` on `(blockKey, variant)` pairs and represented an inheriting instance with a string sentinel compared against `variant`, which the user rejected: `instances.inheritContainerParam` is already a parsed boolean, and a lookup should read that field, never re-derive it from a magic string. The landed shape is a module-level `Site = namedtuple('Site', ['blockKey', 'variant', 'inheritsContainer'])`, and `instanceSite(instRow)` builds one straight from the parsed row (`instRow['instanceTypeKey']`, `instRow['variant']`, `instRow['inheritContainerParam']`). Every `SiteBindingIndex` method that took `(blockKey, variant)` now takes one `Site`: `inheritsParams(site)` reads `site.inheritsContainer` directly instead of comparing anything to a sentinel; `paramValues(site, containerValues)` branches on the same field and returns `{param: containerValues[param]}` for every param the block declares (read off `blockParams`, a per-block index built alongside `paramSource` from the same `blocksparams` rows); `bindingsAt`, `valueMaps`, `foreignDeclaredBindings` and `junctionBindings` all take `Site`s and pass them through unchanged. `instanceVariantsByType` becomes `instanceSitesByType`, `{blockKey: set(Site)}`; because every `Site` stored under a block's key already carries that block's own identity, `containerSites`' values are container `Site`s directly, with no separate unpacking. `sitesOf(blockKey)` is the one place that answers "the Sites a block is instantiated at, or its declared defaults if never instantiated"; a fully unparameterized end falls back to the separate module-level `DEFAULTS_SITE = Site('', '', False)`. An inheriting instance that is itself a container still lets its own children resolve, because `instanceSitesByType` carries its `Site` (with `inheritsContainer=True`) forward like any other.
- **`validatePorts` changes.** Both skips are deleted: the connection arm's whole-connection skip (`any(... inheritContainerParam ...)`) and the connectionMap arm's per-instance skip. Every site that used to read `instRow['variant'] or ''` to build a binding-site key now calls `instanceSite(instRow)`: the `_connectionBindings` election, the register-bus `otherInst` parent, and `childSite` in both arms. `_containerBindings` returns `sitesOf(containerBlockKey)`, sorted; a container's own site set may now contain an inheriting `Site` (a container itself reached only by inheritance), and it resolves there like any other. `checkInterfacePair` takes `parentSite`/`childSite` in place of the four separate block-key/variant positionals it carried before; `_junctionSideIdentity` reads `site.inheritsContainer` for the "its container's configuration" text and `site.variant` otherwise, so no code path compares a variant string to anything. The router-to-router check in `config/postParseRegisterPorts.py` builds both sides with `instanceSite` as well.
- **Fixture, built first.** `examples/xprojParam/inhLayout` / `inhLayoutBad`, in the shape of `cpLayout`/`cpLayoutBad`: container `xpInhWrap` (`params: [IL_WIDTH]`), a sibling `xpInhSrc` bound to a literal via a declared variant, and a leaf `xpInhLeaf` (`params: [IL_WIDTH]`, no variant) instantiated twice with `inheritContainerParam: true`. `uLeafA` is reached through a plain connection to an inner sibling instance; `uLeafB` is reached through the container's own `connectionMaps` boundary port. A top-level instance of the same sibling block drives that boundary port, always at the container's own width, so that junction never fails in either arm. `IL_WIDTH`'s declared default is 8, unequal to every bound value (16 or 24), so a fallback to the declaration would show as a wrong number.
  - `inhLayout`: wrap 16, inner sibling literal 16, top-level driver 16. `make db` accepts.
  - `inhLayoutBad`: wrap 24, top-level driver 24, inner sibling literal 16. `make db` rejects, naming `_bitWidth 24`.
  - The connectionMap arm's own junction (container boundary port to `uLeafB`) resolves both ends from the same container configuration by construction, so it cannot itself produce a mismatch in this fixture; every rejection observed is the connection arm's (`uSrc` against `uLeafA`). That is expected and stated in the fixture's own comments: the connectionMap arm's coverage here is that it is now adjudicated at all, not skipped, not that it is the arm that fails.
- **The pre-fix observation, MEASURED.** With the fixtures in place and `pysrc/processYaml.py` untouched, `make -C examples/xprojParam/inhLayoutBad clean db -j` exited 0 with three scaffold warnings, no errors, `.xpInhLayoutBad.db` touched. That is the defect: a container at 24 with an inheriting leaf and a literal sibling at 16 passed `make db` silently.
- **After the change**, the same command on `inhLayoutBad` fails with two errors, both naming `_bitWidth 24` for the parent side, described as "resolved for block 'xpInhBadLeaf' (project xpInhLayoutBad) at its container's configuration" against "resolved for block 'xpInhBadSrc' ... at variant 'inner'"; `inhLayout`'s equivalent command exits 0 with warnings only.
- **Makefile.** A new target `xproj-inherit-layout`, modelled on `xproj-container-layout`: builds `inhLayout` at `db` (must succeed), builds `inhLayoutBad` at `db` into a captured log (must fail), greps the log for `_bitWidth 24` and prints `OK: inhLayoutBad rejected at db at the container-resolved width`. Added to `pipeline-test`'s prerequisite list. `examples/xprojParam/README.md` gained a section for the pair, in the style of the `inhVar` section above it.
- **Gates, VERIFIED BY EXECUTION 2026-09-08.**
  1. `make -C examples/xprojParam/inhLayout clean && make -C examples/xprojParam/inhLayout -j db` exit 0 (warnings only); `make -C examples/xprojParam/inhLayoutBad clean && make -C examples/xprojParam/inhLayoutBad -j db` exit 2, naming `_bitWidth 24`.
  2. `make xproj-container-layout -j` exit 0 (`cpLayout`/`cpLayoutBad` unaffected); `make xproj-inherit -j` exit 0. `inhVar`'s `uLeafA` to `uLeafB` connection and its two connectionMaps (`contIn` to `uLeafA.in`, `contOut` to `uLeafB.out`) are adjudicated for the first time here and accept, because both leaves resolve from the same container instance; `make xproj-inherit-layout -j` exit 0, printing the `OK:` line.
  3. Unit suite: `unittest/run_all_tests_parallel.sh`, 118 of 118 passed, no new suite added (the fixture is db-only and covered by the Makefile gate, not a new unit cell).
  4. `make clean && make pipeline-test -j` exit 0. 66 "No error" (baseline unchanged), zero `ERROR:` lines, three `OK:` lines (`varUniqBad`, `cpLayoutBad`, and now `inhLayoutBad`).
  5. Product: `make clean && make gen -j && cd rundir && make -j && ./build/run debayer --verbosity=medium` exit 0 with two "No error" lines, then `make -j all VL_DUT=1` exit 0. The product tree's `u_preprocess`/`u_interpolate` were `inheritContainerParam` instances; their connection `{interface: bayer_preprocess_stream, src: u_preprocess, dst: u_interpolate}` and their two connectionMaps, `{interface: video_raw_stream, block: debayer, direction: dst, instance: u_preprocess}` and `{interface: video_rgb_stream, block: debayer, direction: src, instance: u_interpolate}`, were skipped before this step and are adjudicated now; all three accept.
  6. Pro: `make -C builder/pro pipeline-test -j` exit 0, 14 "No error" (baseline unchanged); `inhTandem`, another `inheritContainerParam` fixture, builds and links under the new adjudication.
- **Sequencing.** Step 13 landed and was then reverted (2026-09-09, user), so the product tree again exercises the inheriting path through `u_preprocess`/`u_interpolate`; inhLayout/inhLayoutBad and inhTandem remain additional coverage.
- **Gate-baseline update.** Step 13 added two unit cells on its way to landing (§6, step 13); the unit suite total is 120 as of 2026-09-08, not the 118 this step measured.
- **Follow-up LANDED 2026-09-09: the diagnostic names the governing container site.** `junctionBindings` yields `(parentBindings, childBindings, containerSite)`, the third element being the container `Site` whose configuration governed that pair (`parentSite` when the parent is the container, the enumerated container `Site` otherwise, `None` when no end takes a value from a container). `checkInterfacePair` takes it as a required positional and hands it to `_junctionSideIdentity`, which names it for any side with container-sourced values that is not the container itself: an inheriting side reads `at its container's configuration: block 'xpInhBadWrap' (project xpInhLayoutBad) at variant 'use'`, a `containerParam:` side reads `at variant 'use', with CP_WIDTH from container block 'xpCpBadWrap' (project xpCpLayoutBad) at variant 'use'` (new `SiteBindingIndex.containerSourcedParams`, which `inheritsParams` now shares). The register-router caller in `config/postParseRegisterPorts.py` passes `None`; it resolves both sides at the declared defaults and never reaches the naming branch. A container that is itself the parent end is named only by its own variant text; when it in turn inherits, the site above it is not named, because `valueMaps` carries values without provenance. `inhLayoutBad` became a multi-variant container (`alt` 16 and `use` 24, two top-level drivers); `Site` sorts `alt` first and that site accepts, so the gate `xproj-inherit-layout` asserts the rejection names `use` and never `alt`, and `xproj-container-layout` asserts the `containerParam` text on `cpLayoutBad`. Review applied before the gates: comment trimmed, one filter over `paramRows`, single-line docstring, `xproj-container-layout` comment updated.
  - Gates, VERIFIED BY EXECUTION 2026-09-09: unit suite 120 of 120; `make clean && make pipeline-test -j` exit 0 with 66 "No error", 0 `ERROR:`, 3 `OK:` (`varUniqBad`, `cpLayoutBad` and `inhLayoutBad`, the last two now asserting the container-site text); pro pipeline exit 0 with 14 "No error"; product `make clean && make gen -j` diff-stat only the `builder` and `isp_shared` rows, `rundir` model run and `VL_DUT=1` run two "No error" each.
  - **Found on the way, OPEN.** `config/postParseRegisterPorts.py` resolves both router sides with `bindingsAt(site, dict())`. Since the 2026-09-09 pre-commit review removed the membership filter in `paramValues`, a nested router instance that sets `inheritContainerParam: true` or binds a `containerParam:` row raises `KeyError` there instead of falling back to the constant's default as the comment above the call still claims (VERIFIED BY CODE READING; no fixture has an inheriting router). Fix is the two-hop correlation that comment describes, or a db diagnostic rejecting the shape. Facts gathered 2026-09-10 (VERIFIED BY CODE READING): `SiteBindingIndex.valueMaps(site)` already walks `containerSites` to the root without caller-supplied values, so the router-to-router check can iterate `valueMaps` per router side instead of passing `dict()`; routers are never the synthesised register handler, so the shape is only authored. No fixture exists; whether a parameterized nested router is a supported shape is the ruling needed before a fixture is written.
- **Pre-commit review, 2026-09-09.** An independent review of the uncommitted tree found two fallbacks in `SiteBindingIndex` that restated guarantees `projectCreate` already enforces. `sitesOf` used `or` on the site set, so a present but empty set read as "never instantiated"; it now branches on key absence only. `paramValues` filtered an inheriting child's params with `if param in containerValues`, and the `containerParam:` row branch carried the same membership test; either would have turned a broken producer into default bindings and a junction that passes at the declared defaults. Both filters are removed, so a violated contract raises. The guarantees they restated: `validate_inherit_container_params` requires a by-name subset backed by the same constants (step 16), `validate_container_sourced_params` rejects a `containerParam:` the container does not declare, and variant completeness binds every declared parameter, so a resolved container map always carries the name; `valueMaps` passes an empty map only to a site with no container-sourced rows. Verified by execution: `xproj-inherit-layout`, `xproj-container-layout`, `xproj-inherit` and `xproj-depth` pass with their `OK:` lines, unit suite 120 of 120, and the base and pro pipelines and product gates re-run on the final tree (Current Status). Two further findings sit outside this change and are not commit blockers: `getRegistrarConfigView` seeding from `projectPairs` when a stale `--parent=` stamp misses, which the user ruled load-bearing on 2026-08-31 and `unittest/test_inherit_vl_child.py` pins; and the descriptor selectors (`selectedDescriptor`, `_instanceVariantDescriptor`, `_selectDeclaredDescriptor`) taking the first match without asserting exactly one, recorded as a follow-up for the next Open-side pass.

- **Descriptor selectors assert one match, LANDED 2026-09-10.** `_instanceVariantDescriptor`, `_selectDeclaredDescriptor` and `calcRegistrarPairs.selectedDescriptor` single-element-unpack their filtered list, so zero or several matches raise at the selector instead of returning the first. The premises they rest on, each read in the producer: `calcVariantConfigDescriptors` emits one descriptor per (declaring project, label); `resolveInstanceVariantDeclarers` persists one declaring project per labelled instance from the same `contextOwningProject` map; `validateVariantLabelBuildOwnership` leaves a label the build does not declare with exactly one declarer, and both `_selectDeclaredDescriptor` callers pass `PROJECTNAME`. `own or descriptors` branches on whether the build declares the label, an optional relationship, not a contracted-field fallback. New `unittest/test_descriptor_selector_uniqueness.py` drives both `projectOpen` selectors unbound (seven cells: own wins, sole foreign declarer, two foreign declarers raise, one match, no match raises, two matches raise, unlabelled returns None); the closure is covered by the example pipelines. `run_all_tests_parallel.sh`'s stale suite count moved from 118 to 121. Reviewed categorically; review applied. Gates, VERIFIED BY EXECUTION 2026-09-10: unit suite 121 of 121 with no suite-count warning; base pipeline exit 0, 66 "No error", 0 `ERROR:`, 3 `OK:`; pro pipeline exit 0, 14 "No error"; product regenerates with only the `builder` and `isp_shared` diff rows, model run and `VL_DUT=1` run two "No error" each.
### Step 15, Config names always carry the declaring project. LANDED 2026-09-07

- **As landed.** Every Config struct, the block default included, is `<declaringProject>_<block><Variant>Config` / `<ownerProject>_<block>DefaultConfig`, and each (declaring project, block) emits its structs in one module, `<project>_<block>VariantConfig.cppm` (`export module <project>.<block>.config;`), which the block's Base, registrars, testbench External and Verilated wrapper import. The per-context header `<context>VariantConfig.h` renders an empty generated region and is still scaffolded (see follow-up below). One speller: `calcVariantConfigDescriptors` persists `structName` on every descriptor and every consumer reads it; `cpp_variant_config_name` is deleted and `cpp_descriptor_config_name` survives only as a pass-through for `builder/pro`'s `constructorTandem.py`. `calcConfigModules` (`CONFIGMODULES`) is the one home map; `calcForeignConfigHeaders` (`FOREIGNCONFIGHEADERS`, the SV wrapper family) is a filter over it. The `foreignConfig` fileMap entry is gated `cond: {hasMdl, hasTb}` and `condAnd: {hasOwnParams}`; the fileMap key and marker keep their old name (migrate implication), the Python and view identifiers are renamed (`configModules`, `verifConfigModules`, `getConfigModuleData`, `configModule()`).
- **Rule found on the way, ruled by the architect 2026-09-07.** An owner-declared variant labelled `default` spells the same name as the block's synthetic default; the first landing deduped by name and silently kept the synthetic values (fault-injected on a copy of `inhVar`: bound `INH_ALGO: 6`, emitted `INH_ALGO = 1`). Now an owner-declared `default` IS the block's default Config and no synthetic one is emitted for that block. Guarded by `unittest/test_default_variant_identity.py` on `unittest/fixtures/default-variant-identity` (fails without the fix). The product tree declares every variant as `default` at the constants' own values, so its output is unchanged.
- **Hand-written casualties, edited outside generated regions.** `/work/ws/debayer/tb/debayer/debayerConfig.cpp` (qualified two names, two imports), `examples/ip_test/ip/tb/ip/ipExternal.cppm`, `examples/simple_ip/ip/tb/ip/ipExternal.cppm`, three YAML comments, `twoCtx`'s `desc:` and README, `examples/xprojParam/README.md`, the skill `rules/skills/design-parameterizable-blocks.md`. `/work/ws/debayer/proto/model/test/*` left alone: standalone experiments with no project database. Nine unit suites updated for the spelling; `test_config_template.py` now renders through `configModule()`.
- **Outside `builder/base`, awaiting the user's acceptance.** `builder/pro/templates/systemc/classDeclTandem.py` read a base view field this step removed; it now imports the block's own Config module or the pair's `verifConfigModules`, following `constructorTandem.py`. `builder/pro/unittest/test_constructor_tandem.py` gained the `structName` field on its hand-built descriptor stubs.
- **Gates, VERIFIED BY EXECUTION 2026-09-07 after the review repairs.** `make clean && make pipeline-test -j` exit 0, 64 "No error", zero `ERROR:`, both OK lines. Unit suite 117 of 117. Product: `make clean && make gen -j && cd rundir && make -j && ./build/run debayer --verbosity=medium && make -j all VL_DUT=1` exit 0, two "No error", `test_debayer_structs` executed, `verif/preprocess_hdl_sc_wrapper.h` byte-identical, product status count unchanged. Pro: `make -C builder/pro pipeline-test -j` exit 0, 14 "No error", `test_constructor_tandem.py` passing. All four re-run once more after the last edit (a direct read of the contracted `ownConfigModule` view field replacing a `.get`): unit 117 of 117, pipeline-test exit 0 at 64, product exit 0, pro exit 0 at 14. Two earlier product and pro gate failures were tree collisions with a gate chain the repair agent left running detached, not defects; both passed alone.
- **Emitted-output delta.** NOT MEASURED as a before/after hash: the implementer worked iteratively from no clean snapshot. Verified by content inspection (`twoCtx`, `ip`, the product tree) and by the gates. The review repairs' own delta was measured at zero.
- **Follow-ups this step opened.** (a) Retire the empty `<context>VariantConfig.h`: fileMap `config` entry, `_configHeaderContexts`, `saveIncludeFiles`'s `config_hdr`, `templates/fileGen/fileGen.py` scaffold, `genFileParam.py`, `config.py`'s empty renderer, plus a per-file orphan-sweep entry for `make migrate`; `unittest/test_container_param_cross_project_vl.py` already deletes the stale header by hand and `dpMid` gained a new empty one. (b) The implementer's `make newmodule` sweep scaffolded `model/`, `rtl/`, `rundir/` and three Config modules into `examples/xprojParam/cpLayout`, a db-only fixture; nine untracked files with no user content, deletion referred to the user. Resolved: the user committed the files; they are tracked. (c) The `foreignConfig` fileMap key now names native Config modules too; renaming it is a migrate item. Inventory for (a), 2026-09-10 (VERIFIED BY CODE READING): touchpoints are the `config` entry in `config/project.yaml` ~161, `genFileParam.py` `_CONTEXT_FILE_MODE['config_hdr']`, `fileGen.py` `config_hdr`, `processYaml.py` `saveIncludeFiles`/`_configHeaderContexts`, `migrateLayout.py` `FULLY_GENERATED_FILEMAP_KEYS`, and `templates/systemc/config.py::includeConfig` returning `""`. `migrateOrphans.py` `LEGACY_FILEMAP` omits `config` because it never existed at `main`, so a retirement needs a delete-only sweep of its own for trees that carry the header. Zero tracked `*VariantConfig.h` in `examples/`, `pro/examples/` or the product; only unit fixtures include it. Awaiting the architect's go-ahead, since the sweep deletes generated files in user trees.

Rule 5 of the rules section in [`design-parameter-inheritance.md`](./design-parameter-inheritance.md): a variant is owned by the project that declares it, and its name carries the project. Today the name carries the project only when the declaring project does not own the block's config context, so one identity has two spellings and the spelling of a two-context block follows its `params:` order (§7).

- **Changes.** Every emitted Config struct, including the default, is `<project>_<block><Variant>Config`, and each (declaring project, block) pair emits its Configs in one artefact, so the context header stops carrying variant structs. One naming function decides the spelling and every consumer reads it; the exact site is for the implementer to find, not for this entry to guess.
- **Blast radius, measured 2026-09-07.** 98 distinct Config struct names across `examples/`, `builder/pro/examples` and the product tree; all change. Hand-written code naming a concrete Config, found by scanning every line outside a generated region: `/work/ws/debayer/tb/debayer/debayerConfig.cpp` (4 lines), `examples/ip_test/ip/tb/ip/ipExternal.cppm` and `examples/simple_ip/ip/tb/ip/ipExternal.cppm` (2 lines each), and four files under `/work/ws/debayer/proto/model/test/`. Three YAML comments mention names (`yaml/debayer_tb.yaml`, `examples/ip_test/bridge/yaml/ipBridge.yaml`, `examples/xprojParam/cstBind/yaml/xpCstSup.yaml`). Everything else reaches a Config through the `Config` template parameter.
- **Proves it.** `pipeline-test` exit 0 at 64 "No error"; the unit suite green; the product gate including `VL_DUT=1`; the emitted-output delta enumerated, expected to be every file that spells a Config name and nothing else. The §7 flip closes with it: `twoCtx`'s two blocks get names that differ only in the block, whatever their `params:` order, and the fixture's `desc:` stating the order dependence is rewritten.
- **Sequencing.** After the rules iteration settles rule 5's wording. Independent of steps 12 through 14.

### Step 16, an inheritContainerParam child shares the container's declarations. DECIDED 2026-09-09 (user); LANDED 2026-09-09

`validate_inherit_container_params` checked only that the child's `params:` names are a by-name subset of the container's. It never checked what those names are backed by. `inheritContainerParam` forwards each parameter by name only: SystemVerilog forwards the port parameter by name, and SystemC types the child on the container's Config. If the child's own `ipParameters` declaration of a shared name carries a smaller `maxValue` than the container's declaration, the child's worst-case sizing was computed from the smaller bound while a larger container value passes the by-name subset check silently. The per-parameter `containerParam:` path already checks `maxValue` at the site; the whole-container shorthand had no equivalent check.

- **The rule.** For every parameter the child shares with the container, the two `blocksparams` rows (child and container) must carry the same `paramSourceKey`, the same backing `ipParameters` constant. A same-named parameter backed by two different declarations is rejected, once per offending (container, child, param).
- **The check.** In `calcBlockConfigInfo`, the same `flat_rows('blocksparams')` loop that already builds `params_by_block` also builds `param_source_key`, a map from `(blockKey, param)` to `paramSourceKey`. `validate_inherit_container_params` reads it for every parameter in `childParams & containerParams` and compares the two source keys, alongside the existing by-name subset check.
- **The diagnostic**, as printed by the rejecting fixture cell, with the fixture's temporary file names shortened:

  ```
  instance uChild in file arch.yaml: inheritContainerParam child block 'childIp' parameter 'WIDTH' is backed by constant 'WIDTH/child.yaml', but container block 'containerIp' backs it with a different constant 'WIDTH/container.yaml'; each shared parameter must be the container's own declaration. Give the instance a declared variant and bind the parameter with containerParam: if it is meant to differ
  ```

- **The fixture.** `unittest/test_inherit_container_param.py` gained negative (f): one project, one owning scope, two files that each declare their own `WIDTH` and their own block, neither file including the other. A shared top file includes both and wires the `inheritContainerParam` instance across them. Rule 2 of `design-parameter-inheritance.md` (a block's `params:` resolves through its own include scope) meant this layout reaches the new check cleanly: each block sees only its own file's `WIDTH`, so nothing about scope resolution rejects the design first, and the design reaches the shared-declaration check. `_make_project`/`_run_negative` gained an optional `extra_files` argument to carry the two block files through cleanup, matching the existing single-file style otherwise.
- **Gates, VERIFIED BY EXECUTION 2026-09-09.**
  1. `unittest/test_inherit_container_param.py` directly: 8 cells before the new fixture, 9 after, all passing. `unittest/run_all_tests_parallel.sh`, measured after: 120 of 120 passed; the suite count is unchanged from before this step, because it added a cell inside an existing suite file, not a new suite.
  2. `make clean && make pipeline-test -j`: exit 0, 66 "No error", zero `ERROR:`, three `OK:` lines. `examples/xprojParam/inhLayout` (the positive `inheritContainerParam` example) still accepts at `make db`; `examples/xprojParam/inhLayoutBad` still rejects, and for its original bit-width reason, not this step's check.
  3. `make -C builder/pro pipeline-test -j`: exit 0, 14 "No error" (`inhTandem`, an `inheritContainerParam` fixture, still builds and links).
  4. `make clean && make -j db` in `/work/ws/debayer`: exit 0.

### Step 17, a parameterized nested router inherits or is container-sourced. DECIDED 2026-09-10 (user); LANDED 2026-09-10

The user ruled the shape SUPPORTED, expecting the ISP to need it: `isp_top` is a block with
`registerPorts:` holding its own router, so a SoC router dispatching into it is exactly the
router-to-router junction, and a parameterized `isp_top` would carry that parameterization onto its
router. Rejection at db was the cheaper alternative and was not taken.

- **What already works (VERIFIED BY CODE READING 2026-09-10).** A router block declaring `params:` is
  accepted at db when its instance binds a `variant:`; `unittest/test_addrctl_parameterized_router.py`
  and `test_addrctl_parameterized_router_upstream.py` pin it, the second with a parameter-typed data
  struct on the router's `upstreamPort`. On the SystemC side the router class and its `routerDecode`
  body are templated on the block's Config when `hasOwnParams` (`templates/systemc/constructor.py`
  ~85-90, `baseClassDecl.py` ~78-80), and the container instantiates it like any child.
- **Gap A, the db check.** `config/postParseRegisterPorts.py` ~675 resolves both router sides with
  `bindingsAt(site, dict())`. An inheriting or `containerParam:`-sourced nested router raises
  `KeyError` in `paramValues`. The other two junction arms enumerate `junctionBindings` triples; this
  arm needs a three-site version because the parent router P and the sibling S (block B) share
  container C while the nested router R sits inside S: C's configuration gives P's and S's values,
  S's values give R's. `SiteBindingIndex.nestedRouterBindings(parentSite, siblingSite, childSite)`
  yields `(parentBindings, childBindings, containerSite)` and the check runs once per triple, after
  the existing container-sibling lookup that already finds S. Fixture: `unittest/test_nested_router_inherit.py`
  (inherit matching, inherit mismatching rejected naming the dispatch and the container site,
  `containerParam:` form matching).
- **Gap B, the SystemVerilog router header.** `templates/systemVerilog/apbDecodeModule.py` ~32-37
  emits `module <name>` then the port list with no `#(parameter ...)` section, while
  `moduleInterfacesInstances.py` ~22-25 emits one for an ordinary block and ~94-97 emits the
  instance-side `#(.P(spelling))` from `svInstanceParams` for every parameterized child, routers
  included. A parameterized router therefore verilates with a parameter override onto a module that
  declares none. The router template also never emits the module-local parameterized declarations
  (`parameterizedDeclLines`) that `moduleInterfacesInstances.py` ~39 and `moduleRegs.py` ~141 emit,
  so a parameter-typed register-bus struct has no local typedef in the router body. Fix: the router
  header and local declarations follow the ordinary block template, through the same view fields.
- **Gap C, coverage.** No buildable example has a parameterized router. Plan: a db-only pair under
  `examples/xprojParam/` on the `inhLayout`/`inhLayoutBad` pattern for gap A, and one buildable
  example with model, RTL and Verilated run whose nested router inherits its container's width onto a
  parameter-typed upstream data struct, driven by a cpu running fw through both routers, for gap B.
  Seed to be chosen from the existing nested-router examples (`ip_test/bridge`, `mixed`).
- **Gap D, prose.** `design-parameter-inheritance.md` §5 "not covered" caveat on nested routers goes;
  the parameterizable-blocks skill gains one sentence that a router block may declare `params:` and
  inherit like any block.
- **Sequencing.** Gap A first (generator edit), then the fixtures, then gap B, one generator-editing
  agent at a time on the primary tree. Landed facts and gates are recorded here as each part lands.
- **Gap A LANDED 2026-09-10.** `SiteBindingIndex.nestedRouterBindings(parentSite, siblingSite,
  childSite)` enumerates the shared container's configurations through `containerSites[siblingSite]`
  and `valueMaps`, resolves the parent router and the sibling at each, and the nested router at the
  sibling's result; the default-resolved single tuple is yielded only when none of the three sites
  takes a value from a container. The check in `postParseRegisterPorts.py` now follows the existing
  container-sibling lookup and runs once per tuple. Found on the way: one shared `containerSite`
  cannot attribute both sides of this junction (the parent router's container is C, the nested
  router's is the sibling), and the first landing named block `top` as the router's container in the
  rejection text. Every junction generator now yields `(parentBindings, childBindings,
  parentContainerSite, childContainerSite)` and `checkInterfacePair` takes the two sites;
  `junctionBindings` yields the same site twice, so the `inhLayoutBad` and `cpLayoutBad` texts are
  unchanged. Measured pre-fix failure: `KeyError: 'PARAM_UPSTREAM_WIDTH'` at `paramValues` from
  `bindingsAt(childSite, dict())`. Fixture `unittest/test_nested_router_inherit.py`: (a) inherit
  matching accepts, (b) inherit with the container narrower rejects naming the dispatch
  `uAPBDecode` to `uParamRouter` and the child side "at its container's configuration: block 'mid'
  ... at variant 'midV0'", (c) `containerParam:` form accepts. Reviewed by the supervisor, revision
  applied. Gates, VERIFIED BY EXECUTION 2026-09-10: unit suite 123 of 123 (runner count raised);
  `make xproj-inherit-layout -j` and `make xproj-container-layout -j` print their `OK:` lines; the
  full base and pro pipelines and the product gates run once when the whole step lands.

- **Fixture measured 2026-09-10 (VERIFIED BY EXECUTION on `examples/xprojParam/rtInh`, new,
  untracked).** Shape: common cpu -> `xpRtInhTop` (DUT) -> primary router `xpRtPrimeDecode` ->
  `xpRtWrap` (`params: [RT_WIDTH]`, `registerPorts: rtReg: rtApbReg`) -> nested router
  `xpRtNestDecode` (`inheritContainerParam`, upstream `rtApbReg` whose data struct is `RT_WIDTH`
  wide, default 8, bound 32) -> `xpRtLeaf` (one rw `cfg`). Findings, in build order:
  1. `make db` demands `params:` on the primary router: the dispatch connection to `uWrap` is typed
     on the nested router's upstream interface, so the primary router's own port carries a
     parameterized struct and the own-surface rule applies. Consistent with the rules; the unit
     fixture's `apbDecode` declares params for the same reason.
  2. `make db` demands `params:` on the leaf: `_resolveRouterRegisterBusInterface` types a router's
     register bus from `upstreamPort` alone, and the router template drives both sides from one
     struct set, so a `registerDecoderPort` naming a second interface is not honoured. Rule to
     document: one register-bus type per router; a parameterized upstream bus parameterizes every
     leaf the router serves.
  3. `make gen` crashes in `templates/systemVerilog/module_hdl_wrapper.py::param_names` for
     `xpRtInhTop`, flagged `isParameterizable` through an internal parameter-typed channel while
     declaring no `params:` (`params` is None). Gap E, real defect, fixed with gap B.
  4. The model does not compile: `xpRtInhTop.cppm` binds a channel typed `rtDataSt<xpRtWrapUseConfig>`
     to the primary router's port typed `rtDataSt<xpRtPrimeDecodeTopConfig>`; equal values, distinct
     C++ types, no thunker. This is step 13's open inferred-port thunker gap reached through a
     synthesised register-bus connection. Not fixed here: the fixture takes the skill's own answer
     (siblings binding a Config-typed channel inherit the container's Config), so `xpRtInhTop`
     declares `RT_WIDTH` bound at `u_xpRtInhTop` and every block on the register path inherits it,
     which is also how the ISP would author it.
  5. `rtl/xpRtNestDecode.sv` has no `#(parameter RT_WIDTH)` header and no local `rtDataSt` typedef
     while `rtl/xpRtWrap.sv` instantiates it with `#(.RT_WIDTH(RT_WIDTH))`: gap B confirmed
     statically; Verilator was not reached because of 3 and 4.
  The SystemC nested router is `export template<typename Config> SC_MODULE(xpRtNestDecode)`, as
  expected. `xpRtLeaf` needed no hand code outside its generated regions.
- **Gaps B and E LANDED 2026-09-10.** `templates/systemVerilog/apbDecodeModule.py` emits the
  `#(parameter ...)` list after the package imports when the block declares `params:` and the
  module-local parameterized declarations after the port list when `parameterizedDecls` is
  non-empty, both by the code shape `moduleInterfacesInstances.py` already uses; the emitted
  `rtl/xpRtNestDecode.sv` and `rtl/xpRtPrimeDecode.sv` now carry `parameter RT_WIDTH` and the
  `rtDataT`/`rtDataSt` typedefs and lint standalone. `module_hdl_wrapper.py::render_sv` routes a
  block without own params (`hasOwnParams` false) to the non-parameterizable body even when the
  fileMap scaffolded the `.svh` on `isParameterizable`: the block's module has no parameter port
  list, so the templated body has nothing to spell. Contract: `isParameterizable` says a block's
  emitted code depends on a parameter somewhere inside it; `hasOwnParams` says its own module and
  Config carry a parameter list. New guard `unittest/test_transit_container_vl_wrapper.py` with
  fixture `unittest/fixtures/transit-vl-wrapper` (hasVl `top` with no params over two frozen-variant
  parameterized leaves), reverted-and-rerun to prove it catches the crash; runner count 124.
  Emitted-output delta on apbDecode, mixed, simple_ip and ip_test: none (`git diff --stat examples/`
  empty after clean regeneration).
- **Found on the way, OPEN (gap F).** A transit container with no own params, `hasRtl`, over a
  parameter-typed internal channel emits `<if> #(.data_t(<paramStruct>))` interface instances in
  its own SystemVerilog module with no `<paramStruct>` typedef in scope (`parameterizedDecls` is
  empty for a block without params), so `xpRtInhTop.sv` at its first shape failed lint with
  "Signal definition not found: 'rtDataSt'". The right emission is a typedef sized off the resolved
  literal, since the container has no parameter to size against. The `transit-vl-wrapper` fixture
  is db-and-gen only and does not lint, so nothing pins this today. Needs a ruling: support the
  shape (resolved-literal local typedefs) or reject a params-less `hasRtl` container over a
  parameter-typed channel at db.
- **Found on the way, LANDED 2026-09-10.** A router with exactly one child emitted
  `if (apb_addr >= apbAddrSt'(32'h0))`, a constant compare Verilator lint rejects (UNSIGNED as
  error). The selection block now sets the single child's `_next_psel` without a compare; two or
  more children emit byte-identical text. Three tracked generated routers carried the defect and
  regenerate with the three-line simplification: `examples/simple_ip/rtl/apbDecode.sv`,
  `examples/simple_ip/ip/rtl/ipStdDecode.sv`, `examples/ip_test/ip/rtl/ipStdDecode.sv`; none of
  those examples runs `make lint` in `pipeline-test`, which is why it went unseen. apbDecode and
  mixed (multi-child) lint clean and are unchanged.
- **Fixture revised 2026-09-10, second measurement.** `xpRtInhTop` declares `RT_WIDTH` bound at
  `u_xpRtInhTop` (`variant: use`, 32) and `uPrimeDecode`, `uWrap`, `uNestDecode`, `uLeaf` all
  inherit it; `xpRtWrap` needs no `registerPorts:` (top-down block, db never asked). `make db` and
  `make gen` pass; the testbench Config and Testbench files carry `--variant=use` since the DUT has
  no anonymous default. The RTL hierarchy lints clean through the Verilated wrapper top, which is
  the proof of gaps B and E on the real example. Model build stops at gap G: `classDecl.py` spells
  the router's decoder member `abpBusDecode< apbAddrSt, rtDataSt >` from
  `registerBusStructs`, a `{structureType: bareName}` view map, so a Config-templated bus struct is
  a class template at that point (the `using typename` alias is emitted later).
- **Gap G LANDED 2026-09-10.** `getBDAddressBus` now fills `registerBusStructs` as
  `{structureType: {structure, structureKey}}`; `classDecl.py` spells the decoder member through
  `sc_structure_field_type` (`rtDataSt<Config>` for a parameterizable struct, bare otherwise), and
  `constructor.py` and `blockRegs.py` spell the out-of-line `registerHandler<>` call through the same
  helper then `bareParameterizedType`, because inside a member body of a templated block the bare
  name is the class-local alias and `rtDataSt<Config>` there is `error: expected '>'` (measured on
  `xpRtLeaf.cppm`). The SystemVerilog readers (`apbDecodeModule.py`, `moduleRegs.py`) take
  `['structure']`. Emitted-output delta on apbDecode, mixed, simple_ip, ip_test: none beyond the
  three single-child routers; `make apbDecode -j` and `make mixed -j` two "No error" each.
- **Third measurement and fixture decision, 2026-09-10.** With G in, the model build stops at
  `xpRtPrimeDecode`: its decoder is `abpBusDecode<apbAddrSt, apbDataSt>` (upstream `apbReg`) while
  its dispatch port toward `uWrap` is `apb_out<apbAddrSt, rtDataSt<Config>>`, typed on the nested
  router's upstream interface by `postParseRegisterPorts`. Two bus types inside one router need an
  adapter at the router dispatch, which is step 13's open thunker item, not this step. The fixture
  takes the ISP shape instead: one register-bus interface (`rtApbReg`) on every router port inside
  the DUT, `xpRtInhTop` declaring `registerPorts:` like `isp_top`, and the common cpu's fixed
  `apbReg` meeting `rtApbReg` only at the DUT boundary, where the testbench-boundary thunker exists.
  Rule this pins for authors: a router serves one register-bus type; inside a block, every router
  and register leaf on one path uses that one interface.
- **Found on the way, OPEN (gap H, db diagnostic).** A container's `registerPorts:` key must equal
  the served router's `addressBlock.upstreamPort`: `postParseRegisterPorts.py` ~754-774 synthesises
  the boundary connectionMap with `port` and `instancePort` both set to the router's upstreamPort
  name, and the base class declares the boundary port from `registerPorts:`. With
  `registerPorts: cpuReg: {interface: rtApbReg}` and upstream `rtApbReg`, `make db` and `make gen`
  both passed and the emitted `xpRtInhTop.cppm` bound `this->rtApbReg`, a member the base never
  declares (measured 2026-09-10 on rtInh's third shape). `ipBridge.yaml` and `isp_top.yaml` state
  the pairing in comments; nothing enforces it. Needs a ruling: reject the mismatch at db, or let
  the `registerPorts:` key name the boundary port and have the synthesised map use it.
- **Fourth measurement and scope finding, 2026-09-10 (gap I, OPEN).** With `registerPorts:
  rtApbReg` (key equal to the router's upstreamPort) and the cpu connection landing on it
  (`dstport: rtApbReg`, interface `apbReg`), db and gen pass and the boundary classes are
  consistent, but the testbench External binds `uCPU->cpu_main(rtApbReg)`, an
  `apb_out<apbAddrSt, apbDataSt>` onto an `apb_out<apbAddrSt, rtDataSt<Config>>`, with no thunker
  anywhere in the generated tree. The boundary thunker exists for `ports:` (`xif`, `cppAxis`), not
  for `registerPorts:`. Consequence, stated as a limitation: a Config-typed register-bus struct
  cannot be driven today. The master and the DUT would have to share one Config, the root
  testbench cannot be parameterized, and neither a register-boundary thunker nor a router-dispatch
  thunker exists; `isp_top` sidesteps this by keeping its boundary types literal-sized. Needs a
  ruling if a parameterized register bus is ever wanted: register-boundary thunker at the
  testbench, or reject a parameterizable struct on an `addressBus` interface at db.
  **Fixture narrowed (fifth shape):** fixed `apbReg` bus end to end; `xpRtWrap` bound at
  `RT_WIDTH` 32; `xpRtNestDecode` and `xpRtLeaf` inherit; the leaf's `cfg` register payload is
  `RT_WIDTH` wide, so the firmware round trip at 32 bits proves the width reached the leaf through
  the wrapper and the inheriting router. Gaps A, B, E, G and the single-child fix are all on that
  path; only gap G's decoder-member spelling has no in-tree consumer with a Config-typed bus struct
  (it is exercised by the leaf's register handler instead).
- **Fifth measurement, 2026-09-10 (gap J, FIX IN FLIGHT).** On the narrowed shape db, newmodule and
  gen pass (the stale registrar warn/delete path ran for real: three files warned at db, removed by
  `make newmodule`; four stale verif wrappers from earlier shapes are not covered by that sweep and
  were deleted by hand, a gap the orphan sweep should own). The model build fails in the generated
  `cfgSt<Config>` register accessors: `templates/systemc/structures.py::registerFeatures` emits
  `_getValue`/`_setValue` with the field's declared width as a literal (8, the default) and the type
  by bare name, so a parameterizable payload is `( cfgDataT )` (alias template, no argument) masked
  to 8 bits at a bound width of 32; `pack`/`unpack` in the same file are Config-aware. `_setValue`'s
  parameter also shadows a member named `value`. Also found: a stale `--variant=use` on a plain
  block's testbench GENERATED_CODE_PARAM line is accepted by gen and emits
  `createInstance(..., "use", ...)` for a block with no such variant; removed in the fixture, not
  guarded.
- **Gap D LANDED 2026-09-10.** `design-parameter-inheritance.md` §5's "nested router is not
  resolved per site" caveat is replaced by the verified rule and the limitation gap I measured: a
  router serves one bus type on both sides, may declare `params:` and inherit like any block, is
  adjudicated at the governing configuration, and a register-bus structure sized by a parameter has
  no master that can drive it (no dispatch or boundary thunker, no Config at the root). The
  parameterizable-blocks skill gains one paragraph under container Config inheritance saying the
  same for authors: size the register payload by the parameter, never the bus structure.
- **Review pass 2026-09-10 (categorical, reviewer).** No logic defects. Applied: `registerFeatures`
  takes `prj, useConfig` as required parameters (no `if prj else` arms); `moduleRegs.py` reads
  `registerBusStructs['addr_t']['structure']` directly; the transit-wrapper test asserts on the
  absence of a `#(` header line rather than the substring; comment blocks trimmed across the
  templates, the fixture and the Makefile; the stale `test_regs_handler_container_config.py`
  docstring paragraph that said a parameterizable register payload cannot be generated is gone;
  the one-off `xproj-nested-router-clean` target removed (the example sits in the clean glob).
  Deferred to the user:
  (i) `vlSvWrapBody`'s fileMap `cond: {isParameterizable: true}` scaffolds the `.svh` body for a
  transit container that also gets the bare `.sv`; both now render the ordinary body, a dead
  duplicate the manifest never compiles. Producer-side fix is `cond: {hasOwnParams: true}`,
  matching `vlSvWrapPair`; that is a fileMap contract change, so the template dispatch stays until
  ruled.
  (ii) `_getValue` in `registerFeatures` is mis-emitted for multi-field register structures
  (pre-existing: the `isArray` block sits outside the `for`, so only the last field survives, and
  its mask binds by precedence to the shifted mask, returning 0; `apbDecode`'s `un0ARegSt` shows
  it). Neither `_getValue` nor `_setValue` has a consumer under `common/systemc/`, `templates/`,
  `pysrc/` or `pro/`. Ruling: fix the loop or stop emitting the pair.
  (iii) The four stale `verif/*_hdl_sv_wrapper.*` files earlier fixture shapes left behind were
  not swept by `make newmodule` (registrar files were) and had to be deleted by hand; the orphan
  sweep should own verif wrappers a shape change orphans.
- **Step 17 LANDED 2026-09-10; gates VERIFIED BY EXECUTION on the final tree.** Unit suite 124 of
  124 (two new suites, runner count raised); base pipeline exit 0, 70 "No error" (66 plus the four
  from `xproj-nested-router`: model run and Verilated run, two each), 0 `ERROR:`, 3 `OK:`, 0 stale
  registrar warnings; pro pipeline exit 0, 14 "No error", 0 warnings; product `make clean && make
  gen -j` diff-stat only the `builder` and `isp_shared` rows (the product's testbench router is
  model-only and its register structures carry no register-generator field, so neither template
  change reaches it), model run and `VL_DUT=1` run two "No error" each. Tracked generated files
  that regenerate under this change and must be committed with it: `examples/simple_ip/rtl/apbDecode.sv`,
  `examples/simple_ip/ip/rtl/ipStdDecode.sv`, `examples/ip_test/ip/rtl/ipStdDecode.sv` (single-child
  selection) and `examples/apbDecode/model/apbDecodeIncludes.cppm`, `examples/mixed/model/mixedIncludes.cppm`
  (`_setValue(uint64_t packedValue)`, and a constant-named field width now spelled symbolically,
  `ASIZE`/`BSIZE_LOG2`, as the struct's `_bitWidth` already was). New untracked: `examples/xprojParam/rtInh/`
  (hand-authored YAML, project file, Makefiles, fw/src, tb user regions, vendored `common`),
  `unittest/test_nested_router_inherit.py`, `unittest/test_transit_container_vl_wrapper.py`,
  `unittest/fixtures/transit-vl-wrapper/`. Open from this step, each needing a ruling: gap F
  (transit container SV over a parameter-typed channel), gap H (registerPorts key mismatch accepted
  at db), gap I (no register-boundary thunker; parameterizable bus structs undrivable), the
  `vlSvWrapBody` fileMap condition, the dead mis-emitted `_getValue`, the orphan sweep for stale
  verif wrappers, and the stale `--variant=` on a plain block's testbench accepted by gen.
### What may proceed in parallel

Steps 2 and 5 depend on nothing in this plan and may be taken in any order; step 4, which was the third member of that set, has landed. Steps 3 and 6 waited on step 1, and step 3 has landed. ~~Q3's rename waits on step 3.~~ Q3 is rejected (§4.3), so nothing waits on it. Step 7 depends on step 1 only (its measurements were taken against the post-step-1 generator) and **not** on Case 1 (§2, D2). Case 1 waited on step 3 and is now unblocked, but it is recommended, not decided, and also needs the include-chain ambiguity diagnostic of step 1's review finding 1; no step owns either. Nothing here depends on [`plan-interface-compatibility.md`](./plan-interface-compatibility.md), whose steps 1 through 8 have already landed; step 1 of this plan **removes** that plan's sole remaining failing unit cell.

## 7. What Is Not Known, Separated From What Is Measured

**Measured, by execution, read-only:**

- 14 `blocksparams` rows in 6 databases carry a `paramKey` that is not a `constants` key; every other row in both trees resolves. **CORRECTED 2026-08-13: the cold pre-change baseline is 12 rows in 5 databases** (§5, B1).
- Every one of those bindings, except the `cstUse` probe's, binds its constant's declared default, so step 1 moves no resolved value and the re-enabled `maxValue` check rejects nothing.
- All 8 affected blocks are `hasRtl: 0`.
- 45 authored `params: [...]` occurrences across 31 files, 75 param names; 100 `(block, param, file)` rows over 58 blocks in the databases.
- `constants` is `flat`, so a plain scope-resolved FK onto it is expressible.
- `make xproj-const` builds and runs both cells and is in `pipeline-test`; `make xproj-const-probes` asserts `cstUse`'s rejection; the sizing unit cell fails. **All three of these are pre-step-1 measurements**; step 1 flipped the second and third and folded `cstUse` into the first.

**Measured 2026-08-13, after step 1 landed** (each is recorded in full where it is used):

- Step 1 re-measured independently: unit suite 101/101, cold `pipeline-test` exit 0, `xproj-const` at 12/20/20, zero unresolved `paramSourceKey` rows, product tree cold-regenerates and links. **The emitted-output delta and the census were NOT re-measured** and are held on trust.
- The live database population is **34 databases / 107 `blocksparams` rows**; the cold pre-change `paramKey` join baseline is **12 rows in 5 databases**. `builder/pro` **is** present. (Step 1 landed record.)
- The two-context block: silent `db`/`gen`, then a compile failure, an order-dependent Config name and home header, and losing-context params degraded to bare `uint32_t`. Bound values survive. (§5, B5.)
- Seven blocks across two files already share one config context and one `defaultConfig` while emitting five distinct per-variant structs. (§5, B5.)
- The three-level customer case: accepted at every gate, orphaned in every artefact, no diagnostic; the emitted RTL does not elaborate; two differing nested configurations are inexpressible. (§5, B6.)
- The layout gate adjudicates only the pairing named by the instance row's variant label — the same divergent nested width rejected on one variant, accepted silently on another. (§5, B6.)
- D7's mixed case: container parameter list exactly what the container declares, symbols forwarded, non-declared child parameter emitted as a literal, Verilator exit 0; the whole-Config form does not elaborate. (Step 7.)
- The templated-Config prototype's three gates, and its byte-identical vendor output under customer-driven regeneration. (Step 7, superseded prototype.)
- **The include chain silently decides the backing constant when two same-named parameterizable constants are in scope**, reproduced on a throwaway three-file fixture; corpus scan across all **34 live databases** finds **ZERO** occurrences today. This design makes that choice load-bearing, because the constant it selects is what bounds a nested IP's parameter under D7.1. It therefore blocks nothing now, but it is a prerequisite for Case 1 (§2, D2), whose migration path passes through the state where both a shared and a local declaration exist. (Step 1, independent review finding 1.)

**Measured 2026-08-14, on `examples/xprojParam/{dpLeaf,dpMid,dpTop}`** (step 7a):

- `make db` and `make gen` clean on all three fixture projects; the container-sourced chain persisted as a chain rather than flattened.
- The emitted SystemVerilog forwards the container's symbol — `xpDpLeaf #(.DP_ALGO(MID_ALGO), .DP_WIDTH(DP_WIDTH)) uLeafA` — against a failing pre-design control that Verilator rejected.
- **Verilated runtime parameter values through two levels**: `MID_ALGO=5, DP_WIDTH=8` at the top gives `LEAF_DP_ALGO=5 LEAF_DP_WIDTH=8` two hops down; `6, 20` gives `6, 20`. Neither is a declared default (`1` and `8`).
- The three reuse dispositions of D7.1, per site: same constant accepted, different constants with identical `maxValue` accepted, different constants with a wider container `maxValue` rejected and named.
- ~~**The model is NOT built.**~~ **SUPERSEDED 2026-08-14 by step 7c.** The invalid `static constexpr uint32_t DP_ALGO = ;` is gone; the model of `dpTop` **builds, links and runs**, and the SystemC runtime assertion passes at three independent configurations (5, 6, 7) resolved at a leaf two project levels below the stated value (§6, step 7c).
- **All of the above is regression-guarded as of 2026-08-18**: the family is the `xproj-depth` target in `pipeline-test` (since 2026-08-17), and `unittest/test_container_param_inheritance.py` covers the D7.1 rejection and one forwarding acceptance (§6, step 7a). The "in no `make` target" claim this entry carried was false from 2026-08-17.

**Carried from the independent review, 2026-08-13, and not actioned:**

- `checkInterfacePair`'s equal-bindings fast path **could never fire before step 1 and now does**. Judged safe; recorded as a behavioural change in a safety gate, not merely a re-keying. (Finding 4.)
- `blocksparams.paramKey` has **ZERO code consumers**; it survives only because the key machinery emits a `{field}Key` for any `key`-typed field. (Finding 3.)
- The regressed diagnostic for an unbacked block param is **accepted**: there is no cheap in-framework fix, the schema offers no per-field message hook, and adding one would serve exactly one field. (Finding 7.)
- `validate_inherit_container_params` still compares by bare name while resolved identity is on the row. (Finding 6; subsumed by D7's work, §2.)

**Read from the code but not executed:**

- That an FK on the param field would overwrite `{field}Key` with the resolved qualification. The mechanism at `pysrc/processYaml.py:6832` and `:6994` is unambiguous, but **no experiment was run**, and it must be the first thing step 1 confirms.
- ~~`_resolveWordLinesConstant`'s `KeyError` (`:7215`). Plausible; not reproduced.~~ **CORRECTED 2026-08-13:** the enclosing path is executed on every `ip_test` / `simple_ip` database build (see §4.5); only the `KeyError` itself is unreproduced, because no fixture gives a block-param `wordLines` an include-reached backing constant.
- The SystemVerilog literal-emission consequence (`templates/systemVerilog/package.py:46`). Follows from the code; **unreachable in either tree today**, so it has never been observed.
- B3's compile failure. The omission is certain from the code; the failure itself is known only from the fixture's workaround comment, not from a reproduction in this session.

**Not known at all:**

- ~~The blast radius of step 3 (B5) on the product tree.~~ **MEASURED 2026-09-05** (§6, step 3). Five identical 22-member structs become per-block sets of 6, 5, 6, 4 and 5; all 75 generated Base files in the corpus are already covered by the per-block closure; the only hand-written casualty is `model/rgb_img_writer.h`.
- ~~Whether any design in either tree authors an eval-derived backing constant (step 2's premise).~~ **MEASURED 2026-09-05: none does**, in any of the 49 live databases (§6, step 2).
- ~~Whether the architect wants derived constants out of the Config now or later, and what `debayer`'s base classes become if they leave.~~ **RULED 2026-09-05: out now.** The Config carries declared parameters only; derived constants become computed declarations in the implementation, mirroring the SV module-local `localparam` block. The Base classes keep the same names in the same order, with a computed right-hand side instead of a `Config::` alias (§6, step 3).
- **NEW, and not resolved by that ruling: the Config's NAME and HOME HEADER still flip on `params:` list order** for a params-only block, with no diagnostic (§5, B5, consequence 2). Narrowing the field set removes the other two consequences but not this one, because the name still comes from `configContext`. It needs its own disposition. **Live in the tree since 2026-09-06, and no step owns it.** `examples/xprojParam/twoCtx` now holds the shape: `xpTwoCtxDut` (`params: [DP_WIDTH, TC_GAIN]`) gets `xpTwoCtx_xpTwoCtxDutTwoctxConfig`, homed in a registrar Config module under the `dpLeaf`-owned context, while `xpTwoCtxBare` (`params: [TC_GAIN, DP_WIDTH]`) gets `xpTwoCtxBareTwoctxConfig` in the project's own `xpTwoCtxVariantConfig.h`. Same two parameters, same file, different name and home, decided by list order. Step 1's review finding 5 rested on "no block in either tree declares params backed by more than one context"; `twoCtx` made that false, so first-param selection in `calcBlockConfigInfo` is no longer unambiguous by accident. The fixture's own `desc:` states the dependence, so the fixture passes by pinning it rather than by rejecting it.
- Whether shape (ii)'s mapping form has a schema-framework wrinkle beyond the one traced here. The `list` branch was read (`pysrc/processYaml.py:8430-8466`) and the `_singular` precedent was read (`config/schema.yaml:322-326`), but the mapping form was **not** exercised for `blocks.params` specifically.
- The interaction between Q3's rename and tandem / Verilated registration. Not investigated.
- ~~**Whether D7's child parameter and the named container parameter must share a backing constant, or need only be compatible.** OPEN (§2, D7).~~ **RESOLVED 2026-08-14 as COMPATIBILITY, not identity, on the `maxValue` relation** — decided by the implementation and the fixture, and measured on three reuse cases (§2, D7.1).
- **Whether a cross-project CONVENTION — prefer sharing values, not declarations — should be documented as distinct from a gate.** Not decided by the architect (§3).
- ~~The blast radius of step 7 (D7). Not measured, for either half.~~ **MEASURED 2026-08-14 for the C++ shape (step 7c)**: cold `make pipeline-test -j` and the product tree cold regenerate/build/link, with the emitted-output delta enumerated (§6, step 7c). The site-keyed layout gate (§6, step 7b) has since been built and guarded, 2026-08-17.
- ~~Whether steps 7a and 7c survive a regression gate, because there is none.~~ **ANSWERED: they do.** `xproj-depth`, `xproj-inherit` and `xproj-container-layout` have been in `pipeline-test` since 2026-08-17, and the unit cell landed 2026-08-18 (§6, step 7a).
- **The whole-variant inheritance form.** NOT BUILT and not specified; it exists in neither the schema nor the fixture (§2, D7).
- ~~Whether the third `_post_validateVariantBindingSizing` guard's fix holds under build.~~ **ANSWERED 2026-08-18: it does.** Unit suite 103/103, cold `pipeline-test` exit 0, product tree regenerates/builds/links, emitted-output delta zero over 1124 files (step 1, "Ruled on after the review").

## 8. Related, Not In This Plan

Recorded so nothing is lost; each is out of scope here and belongs to its own owner.

- **`make` reporting success on a broken tree, case 1.** Manifest-listed files are filtered through `$(wildcard ...)`, so an unscaffolded generated file is silently skipped and `make gen` reports success. Recorded at [`plan-interface-compatibility.md`](./plan-interface-compatibility.md) step 8e.
- **`make` reporting success on a broken tree, case 2.** `make gen` exits 0 when the db build failed and `.gen/` is absent.
- **The `xproj-reuse` parallel write/read race.** One-line fix, ours, tracked separately.
- **The four different spellings of "this block has its own params".** `hasOwnParams` on the view (`pysrc/processYaml.py:1567`), `params_by_block` in `calcBlockConfigInfo` (`:4873`), `blockInfo['params']` in the templates, and the raw `blocksparams` rows. A naming cleanup, not a correctness item.
- **Fixture and documentation nits** across `examples/xprojParam`.
- **`make lint` is unusable tree-wide.** Verilator 5.038 rejects `+incdir+` in `common/systemVerilog/a2c.f`. **This is a toolchain incompatibility, not the `REPO_ROOT` issue previously supposed** — recorded here so the earlier attribution is not carried forward. No RTL in this plan can be linted until it is resolved.
- **Product-tree drift, 2026-08-13.** `tb/debayer/debayerExternal.cppm` is rewritten by `make gen` from uncommitted thunker changes in the working tree. Not caused by anything in this plan; it will show up in any before/after emitted-output hash taken on the product tree.
- **`calcForeignConfigHeaders` collides on a bare block name.** `pysrc/processYaml.py:5757` keys `headers` on `(projectName, blockKey)` but builds the header basename from the **bare** block name, so two distinct blocks sharing a name, owned by two projects and given variants by one declaring project, produce two entries with one `baseName`. D8's `blockKey` identity deliberately permits that shape, so it is not gated there either. Found during the D8 review; pre-existing, and its own item.
- **Three emission paths select variant parameter values project-blind.** `getStandaloneVariants` (`pysrc/processYaml.py:1629-1635`), `getBDInstances` (`:1989`) and `_resolveSvInstanceParams` (`:1914-1932`) read `data['parameters'][qualBlock]['variants']`, which carries no project axis and resolves last-writer-wins, rather than selecting through the descriptor. Where two projects declare one `(block, variant)` at differing values, the emitted `localparam` and the RTL instantiation parameters can carry the losing project's value while the SystemC Config carries the right one. Measured on a fixture authored strictly to the rules in this plan. One clean build, exit 0, no diagnostic. This is the defect the D8 correction (§2) and the step 7 correction (§6) both point at. It is owned as item 9A of [`plan-116-review-feedback.md`](./plan-116-review-feedback.md), alongside item 9B, which holds the same collapse in `SiteBindingIndex`. ~~The two must be sequenced together: 9B's project-blindness is what turns a width-coupled divergence into the loud `per-field _bitWidth must agree` failure that step 7b's `xproj-container-layout` gate depends on.~~ **That reason is FALSE and is withdrawn, 2026-09-04. VERIFIED BY EXECUTION.** `examples/xprojParam/cpLayoutBad` is a single project with one `projectFiles:` entry and no `include:` anywhere, so a project axis on `SiteBindingIndex` cannot move that gate; the mismatch it adjudicates is intra-project. The two items also share no data path: `SiteBindingIndex` is db-time only, feeds `checkInterfacePair`, and is referenced nowhere under `templates/`. 9B was then MEASURED on 2026-09-04 and is a defect in its own right: the collapse rejects a composition in which both projects are internally correct, unsatisfiably at any value, while letting an actual cross-project width divergence through at exit 0. It guards nothing, so nothing has to replace it. 9A still goes first because it is the item that emits wrong hardware.
- **Fixtures in the tree carrying their own READMEs.** Both are wired into a `make` target:
  - `examples/xprojParam/{dpLeaf,dpMid,dpTop}` — the three-level customer topology of §5, B6, and now the reference fixture for D7 (§6, step 7a). **CORRECTED 2026-08-14: it does NOT build and run, and its runtime assertion was not exercised.** The entry previously read "It builds and runs, and **its runtime assertion fails by design** in the restored baseline; the failure is the finding", which described the fixture as it stood when it was the B6 evidence vehicle. **CORRECTED AGAIN 2026-08-14, after step 7c: the model now builds, links and runs**, and the runtime assertion passes at three configurations. Six layers are verified: the database rows, the emitted SystemVerilog, a Verilator elaboration, Verilated runtime parameter values through two levels, a SystemC build and link, and a SystemC run whose checkers assert the algorithm each nested leaf resolved (§6, step 7c). The intermediate state this entry described — `static constexpr uint32_t DP_ALGO = ;`, invalid C++ — is gone. The fixture now carries a third customer configuration, added expressly to measure that the vendor projects do not move when a consumer adds one. **CORRECTED 2026-08-18: it is the `xproj-depth` target and has been in `pipeline-test` since 2026-08-17**, and the unit half is `unittest/test_container_param_inheritance.py`, so this is a gate rather than a recorded run (§6, step 7a).
  - `examples/xprojParam/twoCtx` — the two-context block of §5, B5. ~~`db` and `gen` are clean and **it does not compile because step 3 (B5) has not landed**.~~ **CORRECTED 2026-09-05: it compiles**, as step 3 required. `xpTwoCtxDut` now takes `{DP_WIDTH, TC_GAIN}` on its Config and computes `TC_GAIN_X2` locally. It still aborts at run time with "Premature end of test detected", which is the separate scaffold-seed defect its own README documents: the testbench External is still at `--block=xpTwoCtxTop` and elaborates a second copy of the DUT's children, where every other `xprojParam` top has been retargeted at its `_tb` container. ~~Retargeting it is the remaining half of step 3's "proves it" and is **not done**. It is in `xproj-param-probes`, which tolerates the failure, and the README's opening status line is now stale.~~ **DONE 2026-09-06**: retargeted, behaviour added, run-time and compile-time asserts fault-injected, promoted to `xproj-twoctx` in `pipeline-test`, README rewritten (§6, step 3, fixture half).

## 9. Done Criteria

The feature is complete when all of the following hold simultaneously:

- An IP declares a parameter **once**, in its own root file, and satisfies D2 with its own block param.
- ~~A consumer states **where its knob comes from**, and no consumer restates the declaration or the default.~~ **Reworded 2026-09-07 to match §4.0**, which decided the link is explicit in the row, not the YAML: a consumer names the knob once in `params:`, the row records the resolved source (`paramSourceKey`), and no consumer restates the declaration or the default. **MET, step 1.**
- A use-case value appears **exactly once** in the authored YAML and reaches every block that must agree on it, at any value, not only at the declaration default.
- ~~`examples/xprojParam/cstUse` builds, runs and lives in `xproj-const`, not in `xproj-const-probes`.~~ **MET, step 1.**
- ~~`unittest/test_param_cross_project_linkage.py` is 9 of 9, and the unit suite is clean.~~ **MET, step 1** (9/9; 101 of 101 suites).
- A consumer two or more project levels above a block can state that block's configuration **once**, and either the value reaches the emitted artefact or the pairing is rejected by a **db-time diagnostic naming both sides** — never silently orphaned (D7; §5, B6). **MET for the container-sourced path, step 7** (`xproj-depth`, three configurations resolved two levels down). **NOT MET for direct instantiation:** a third project instantiating a block at a variant declared by an intermediate project resolves no descriptor and silently takes the block default Config (`uLeafX`, step 7c; "Two adjacent gaps", step 7; item 9C's adjacent finding in [`plan-116-review-feedback.md`](./plan-116-review-feedback.md)). That is a silent orphan with no diagnostic, and no step owns it.
- ~~The container-sourced fixture family is behind a `make` target with at least one unit cell, so step 7a is a **gate** rather than a recorded run.~~ **MET**: `xproj-depth` / `xproj-inherit` / `xproj-container-layout` in `pipeline-test` (2026-08-17), `unittest/test_container_param_inheritance.py` (2026-08-18) (§6, step 7a).
- `make pipeline-test -j` exits 0, and `/work/ws/debayer` builds and links.
- The emitted-output delta of every landed step is enumerated, and every entry in it is explained. (Step 3's was missing until 2026-09-07 and is now at §6, step 3.)
- ~~D6 is recorded as resolved~~ **MET, step 1**: resolved by the link, with Q3 declined. Both authoring options are legal and both work at any value.
