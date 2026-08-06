# Plan: Feedback Capture — #116 Parameterized-Types Review

## Current Status

- **Overall (2026-08-04): all items are CLOSED.** Items 1 through 6 from the
  review, item 7's release-planning deliverable, and item 8 (raised by the
  product migration rather than the review) are delivered and committed at
  `builder/base` HEAD `2b3f6d1`. Two narrow residuals are recorded and carried
  by the owning plans: item 8's cross-project negative fixture, and the deferred
  whole-suite orphan-sweep migration for legacy-layout examples. Neither blocks
  the release.
- **Verification caveat:** the base acceptance suite run for the 2026-08-04
  status refresh surfaced four release-blocking defects that are **not** review
  items and are not caused by them — an end-of-test startup-gate regression, a
  stale unit-test expectation in an unregistered suite, stale composed-child
  artifacts in the committed example tree, and a stale build directory on
  upgrade. They are recorded under "Release-blocking defects found 2026-08-04" in
  [`plan-116-status-report.md`](./plan-116-status-report.md), which is the single
  place they are tracked.
- **Classification:** feedback capture. This document records action items
  raised during the `feature/116-parameterized-types` review and assigns each a
  disposition. It is not itself an execution plan; each item either links to an
  owning plan or names the owner that must produce one.
- **Status taxonomy:** every item was `OPEN` until triaged into the
  release-planning table at the end of this document; that triage is complete
  and each item now carries a dated disposition.
- **Source:** review feedback recorded by the branch owner. Companion to
  [`plan-116-status-report.md`](./plan-116-status-report.md), which is the
  definitive status index for the branch.

## Purpose

The `feature/116-parameterized-types` review produced seven action items. This
document captures each item faithfully, states the problem it addresses, links
it to any existing owning plan, and records whether it is targeted for the
upcoming release. Detailed design and execution remain the responsibility of the
owning plan named per item.

## Action Items

### 1. Project Naming in Package

- **Feedback:** Fix the bug so that project names are correctly included in
  module and package names, to avoid collisions. `projectName` is now a
  first-class element (added partly to avoid SystemVerilog module-name
  collisions), but it is not yet used as the disambiguator for the module and
  package names themselves.

- **Filename versus identifier (settled):** The `.sv` file name and the SV
  identifier live in different namespaces and do not need to match.
  - The **SV namespace** is the collision surface: `module` names and `package`
    names are global / compilation-unit identifiers and must be project-unique.
  - The **filesystem name** is not a SystemVerilog identifier. This project
    compiles from an explicit file list (`rtl/rtl.f`, full relative paths;
    packages consumed by declared identifier) and uses no `-y` library
    auto-lookup, so no build step requires the file basename to equal the unit
    name.
  - The current match (`debayer_package.sv` declaring `package debayer_package;`)
    exists only because the generator uses one field, `includeName`, as module
    identity, filename stem, and package identifier at once. That is the
    `includeName` overload tracked as the `Q-C8` blocker.

- **Desired rule:**
  - **On disk:** keep the plain YAML name, not project-qualified (for example,
    `debayer_package.sv`).
  - **Inside the file:** project-qualify the identifiers for collision
    avoidance — the C++ module/namespace, the SystemVerilog package name, and
    the SystemVerilog `module` name.
  - **SV module name also in scope (decided 2026-07-29):** the
    `contextModuleIdentity` seam covers the SV package name and the C++
    module/namespace, but the SV `module` name is derived separately from the
    block name and is *not* covered by that seam. Per review decision the SV
    module name must also be project-qualified with the same prefix-dedup rule,
    so two projects with a same-named block do not collide. This is an
    additional change site beyond the two-step seam repoint, and its impact on
    module instantiation sites must be scoped.
  - **Prefix-dedup nuance:** avoid a redundant repeated project token. When the
    identifier already carries the project name, do not prepend it again. Given
    project `debayer` and YAML package name `debayer_package`, the result is
    `debayer_package`, not `debayer_debayer_package`; given block name `debayer`
    (equal to the project name), the module stays `debayer`, not
    `debayer_debayer`.
  - **Proposed predicate:** `qualified = name` when `name == projectName` or
    `name` begins with `projectName + "_"`; otherwise
    `qualified = projectName + "_" + name`. The `_`-boundary test prevents a
    false dedup on names such as `debayering` under project `debayer`.

- **Collision guard (already present):** the prefix-dedup can, in a pathological
  case, map two distinct `(project, name)` pairs onto one identifier — for
  example project `a` block `a_b`, and project `a_b` block `a_b`, both collapse
  to `a_b`. No new guard is needed: the existing module/package identity
  uniqueness gate (`processYaml.py:3650-3659`) already rejects two distinct
  contexts that resolve to the same identity with a durable error.

- **Implementation (simplified by first-class `projectName`):** the enabling
  seam already exists, and this is smaller than the earlier `Q-C8` analysis
  assumed.
  - `contextModuleIdentity` (config `CONTEXTMODULEIDENTITY`) is already a
    per-context identity field, separate from the filename stem, computed in
    `projectCreate` (`processYaml.py:3640-3643`) and currently neutralized to the
    bare stem. C++ identities (Role A) already consume it; filenames (Role B)
    stay on `includeName`.
  - The owning project is already a first-class persisted per-context fact
    (`contextOwningProject` / `CONTEXTOWNINGPROJECT`, `processYaml.py:3599`),
    keyed identically and in scope at the identity-assignment line.
  - Two steps: (1) repoint the two SystemVerilog package-name consumers
    (`templates/systemVerilog/package.py:96`,
    `pysrc/systemVerilogGeneratorHelper.py:26`) from `includeName` to
    `contextModuleIdentity` — a no-op while the identity is bare; (2) replace the
    bare `= stem` assignment with the prefix-dedup qualification using
    `contextOwningProject[context]`.
  - No new persisted field, no filename-rename migration, and no conditional
    logic.

- **Superseded decision:** the earlier `Q-C8` "absolute versus conditional"
  qualification choice is moot now that `projectName` is first-class. Because the
  owner is an intrinsic per-context fact rather than something derived from the
  current build root, qualification is build-independent by construction — a
  child IP spells the same package name standalone and composed — so only the
  absolute form is possible. The prefix-dedup rule also keeps every context whose
  stem already leads with the project name byte-identical, so the one-time
  re-baseline shrinks from "every example" to "only the genuinely cross-named
  contexts."

- **Owning plan:** [`plan-param-constant-collision.md`](./plan-param-constant-collision.md);
  see also [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md).
- **Disposition:** PARTIAL (2026-07-29).
  - **Change A LANDED (package name + C++ module/namespace + SV package
    identity):** `qualifyModuleIdentity` helper + `projectCreate` qualifies
    `contextModuleIdentity` via `contextOwningProject`; SV consumers repointed
    (`systemVerilogGeneratorHelper.py:26`, `package.py:96`). Validated: axiDemo
    `axiStd→axiDemo_axiStd` (build+run "No error"), hierVlDemo run+run-vl clean,
    nested byte-identical (dedup no-op). DB-confirmed owners: `src`/`ip_top`/
    `ipLeaf` all → `ip_test`.
  - **Change B/C REVERTED — new blocker:** qualifying the SV `module` name
    breaks the **user-owned `endmodule: <label>`** that sits *outside* the
    generated region in every `moduleInterfacesInstances`-style file (Verilator
    `%Error-ENDLABEL`: begin `mixed_blockF` vs end `blockF`) across many blocks
    and the debayer product. The item-1 SV-module addendum's "no user-region
    breakage" was wrong — it checked instantiations, not `endmodule` labels. SV
    module-name qualification therefore requires a **user-RTL migration** of the
    `endmodule:` labels.
  - **Change B/C LANDED on examples (2026-07-29, decision (a)):** `blockModuleName`
    map + per-block uniqueness gate in `projectCreate`; emit repoints
    (`moduleInterfacesInstances.py` decl/instantiation via `instanceTypeModuleName`,
    `apbDecodeModule.py` decl+endmodule, `moduleRegs.py`, wrapper
    `dut_instantiation` `module_hdl_wrapper.py:97`); wrapper
    `bodyModule`/`bodyInclude`/`dutClass`/`variantTops` kept PLAIN (filename-coupled
    verilated tops). Migration mechanism = **post-db label re-stamp**
    (`migrateModuleEndlabel.py`, wired into `make migrate --sweep`, owner-gated,
    idempotent) + scaffold seam (`newModule.py`/`fileGen.py::rtlModule` emit
    `endmodule: {blockModuleName}`). Validated: `%Error-ENDLABEL` eliminated across
    examples; restamps owner-correct (`ipLeaf→ip_test_ipLeaf`, `src→ip_test_src`,
    `ipStd*→ip_ipStd*`; project-named blocks untouched); build/run/run-vl green
    (apbDecode/axi4sDemo verilate renamed modules); both uniqueness gates pass.
    Pre-existing `ip_test` run-vl failures (`ipTop_package` rtl.f-aggregation gap;
    F4 `q_assert`) proven unchanged vs baseline — not new breaks.
  - **CLOSED (2026-08-03/04).** All three residuals below are resolved.
    (1) `hierInclude` is relabelled in `38b17af`: begin labels, `endmodule:`
    labels, the user `--importPackage` directive, and the lint top module all
    carry the qualified name (`module hierInclude_blockCX` /
    `endmodule: hierInclude_blockCX`, `--top-module $(PROJECTNAME)_top`), so the
    example no longer needs the migrate pipeline to be wired for this purpose.
    (2) the debayer **product** relabel is executed —
    `rtl/preprocess.sv` declares and closes `debayer_preprocess`,
    `rtl/interpolate.sv` declares and closes `debayer_interpolate`, and
    `debayer.sv`/`debayer_regs.sv` are unchanged by the dedup rule, exactly as
    predicted. (3) the two regressed unit tests were fixed as recorded below.
    One caveat carried to the status report as defect B2: a THIRD suite,
    `unittest/test_module_identity_uniqueness.py`, has the same class of stale
    expectation (it asserts the unqualified identity in the collision message)
    and is not run by either test runner, so it was never surfaced. The guard
    itself is correct.
  - **Former OPEN list (item 1), retained for the record:** (1) lint-only
    examples with no `make migrate` (e.g.
    `hierInclude`) qualify the begin-label via gen but cannot run the endlabel
    restamp through the standard flow → lint `ENDLABEL`; needs `make migrate`
    wiring (example-Makefile work). (2) debayer **product** relabel
    (`rtl/interpolate.sv→debayer_interpolate`, `rtl/preprocess.sv→debayer_preprocess`;
    `debayer.sv`/`debayer_regs.sv` unchanged) — deferred to the single product
    migrate campaign, not yet executed. (3) two unit tests
    (`test_foreign_key_lookup`, `test_nested_ownership`) regressed by the identity
    qualification (surfaced by item 2's full-suite run; item 1's example-only
    validation missed them) — RESOLVED 2026-07-29: both were legitimate
    test-expectation updates, no generator defect. `test_nested_ownership` now
    asserts `qualifyModuleIdentity(stem, owner)`; `test_foreign_key_lookup`'s
    intentional duplicate block moved to `types: sharedType` (item 1's new
    per-block uniqueness gate correctly caught the duplicate block first).
    Full unit suite 84/84 green — item 1 clean on examples + unit suite.
- **CORRECTION (2026-07-29): item 2 parse layer was an antipattern — REDONE
  schema-native and re-LANDED (2026-07-29).** Verified: `_normalizeVariantBindings`
  and `_mappingKeyLc` deleted (0 hits); schema now expresses the nesting
  declaratively (`parameters → variants [collapsed, multiple] → params [collapsed,
  multiple, post(validateVariantBindingSizing)]`, `_singular: value`,
  `param: anchor`, `value: const`); leaf table `parametersvariantsparams`;
  downstream (`processYaml.py`, `postParseChecks.py`, `createBuildManifest.py`,
  `SCHEMA_SPECIFICATION.md`, unit tests) repointed to the leaf; old-form rejection
  preserved as validation-only; migrate idempotent no-op; full suite 84/84, gen
  rc=0 across examples, ip_test build+run "No error". Original defect record kept
  below.
  The landed version left the `variants` sub-table schema as the
  old per-row list and added `_normalizeVariantBindings()` in `processSimple` to
  reshape the nested YAML back into that list. Per `builder-base-development` and
  `SCHEMA_SPECIFICATION.md`, a structural format change belongs in the SCHEMA,
  not imperative reshaping. Redo: restructure the `parameters` schema to express
  the nested form declaratively via `collapsed` + `anchor` (Pattern 4, like
  `modports → modportGroups`), two levels (`variants`: `variant` anchor;
  `params`: `param` anchor + scalar `value`); delete `_normalizeVariantBindings`.
  Rely on the schema's AUTOMATIC nested-table field generation (auto `outerkey`
  `block`/`variant`, `{field}Key` qualified keys, parent-key chain) — declare
  only the deltas. Leaf content/identity preserved (`block/variant/param/value` +
  `blockParam`/`blockVariantParam` combos + `projectName`), re-homed to the leaf
  table (`parametersvariants` → `parametersvariantsparams`); downstream consumers
  updated to the new nesting.
  - The plan's "bodyModule cascades to A2C_VL_TOP" claim was confirmed false
    (verilated tops are filename-derived, stay plain).
  - **Pre-existing (not caused here):** `mixed` C++ fails under Change A only via
    stale header-mode orphans (`model/blockF.cpp/.h` superseded by `.cppm`, not
    in `.gen`) — mixed migration debt, swept by the migrate campaign; example
    files not deleted.

### 2. Variant Definition Schema Improvement

- **Feedback:** Update the variant definition schema so that variant labels are
  specified only once and all parameters are listed under the variant, as
  suggested during the review.

- **Current shape (variant label repeated on every parameter row):**

  ```yaml
  ip:
      - { variant: variant1, param: IP_DATA_WIDTH,     value: 70 }
      - { variant: variant1, param: IP_MEM_DEPTH,      value: 8 }
      - { variant: variant1, param: IP_NONCONST_DEPTH, value: 12 }
  ```

- **Proposed shape (variant label once, parameters nested underneath):**

  ```yaml
  ip:
      variant1:
          IP_DATA_WIDTH: 70
          IP_MEM_DEPTH: 8
          IP_NONCONST_DEPTH: 12
  ```

- **Problem:** The current schema repeats the variant label across parameter
  rows rather than nesting all parameters beneath a single variant declaration.
  The revised shape declares each variant label once with its parameters listed
  underneath.
- **Parameter completeness (decided 2026-07-29):** every variant must explicitly
  define ALL parameters. A variant that omits any parameter is a database-time
  error — there is no default-fill assumption for a missing parameter. Because
  the block definition is required to be in scope where a variant is defined
  (see the scope requirement above), the block's full declared parameter set
  *is* resolvable at the variant's parse point (parse order is topological —
  `processYamls`, `processYaml.py:5841-5893` — so an included block file is fully
  parsed before a parent that binds a variant), so an at-parse/per-row check is
  feasible. **Decision: use a single post-parse pass** within `projectCreate`
  (co-located with `validateVariantConfigFold`, `processYaml.py:4376`) — chosen
  not because inline is impossible but for simplicity/uniformity: it reuses the
  existing grouping, checks same-file and cross-file authoring through one path,
  and sidesteps the one residual hazard (a same-file `parameters:`-before-`blocks:`
  order that already affects existing FK validation). The migration (below) that
  rewrites the old per-row form must emit complete variants.
- **Variant scope requirement (decided 2026-07-29):** a variant may be defined
  in a file separate from the block — this is *required* for composed IP, since
  a reusable child's use-case variants cannot live in the (uneditable) child
  definition file — **provided the block definition is in scope** at the
  variant's definition (same file, or reachable via `include`). There is no
  inline-only restriction; separate files are explicitly allowed. This in-scope
  condition is what makes the completeness check well-founded: the block's
  declared parameter set is resolvable wherever a variant is defined. `ip_test`
  already complies (`ip_top.yaml` includes `ipVariants.yaml` → `ip.yaml`), so no
  relocation of its `variant0` is required.
  `make migrate` — not a coexistence period.
  - `migrateYaml.py` gains a phase that rewrites the old per-row form
    (`- { variant: <v>, param: <P>, value: <n> }`) into the nested-mapping form
    (`<v>: { <P>: <n>, ... }`) in place.
  - After migration, `projectCreate` accepts only the nested form and rejects
    the old per-row form with a durable error directing the user to run
    `make migrate`. The two forms do not coexist.
  - This is an automated migration step; item 6 documents it as such.
- **Owning plan:** [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md);
  authoring guidance in the `design-parameterizable-blocks` skill. Migration
  mechanics in the `migrate-project` skill / `make migrate`.
- **Disposition:** LANDED on examples (2026-07-29). Nested form normalized to the
  internal per-row list at the parse boundary (`_normalizeVariantBindings`,
  `processYaml.py::processSimple` ~:6135) — `parametersvariants` byte-identical,
  downstream unaffected. Old per-row form now rejected with a durable
  "run `make migrate`" error (proven). New `migrateVariantSchema.py` phase wired
  into `migrateYaml.py` (rides `yamlFormat:2`); the 7 example YAMLs migrate as a
  pure regroup (idempotent, instance `variant:` selectors untouched).
  Completeness validator `validateVariantParameterCompleteness()` (post-parse,
  co-located with `validateVariantConfigFold`, called ~:3554, declaration-scoped)
  + negative fixture `test_error_variant_incomplete_params.py` PASS. Item 2 is
  output-neutral (regenerated example diffs are item-1 naming only). 9 old-form
  unit fixtures converted to nested (hard cutover).

### 3. Variant Config Generation

- **Feedback:** Always emit a variant-named config structure for every variant,
  even when its values match the default. Users found the current dedup
  confusing; a config structure named after each variant is clearer.
- **Problem:** When a variant's resolved values equal the default, no distinct
  config structure is emitted for it — an effective deduplication, so consumers
  fall back to the default-named structure (for example `debayerDefaultConfig`)
  instead of a variant-named one. This is confusing: some variants have a
  variant-named config structure and some silently do not, so a reader cannot
  tell from the generated code which variants exist.
- **Desired behavior:** Emit a distinctly variant-named config structure for
  every declared variant regardless of value equality with the default. A
  variant whose values match the default still receives its own variant-named
  structure (equal in content to the default), so the set of emitted config
  structures maps one-to-one onto the declared variants.
- **Decision (2026-07-29): strict 1:1.** Stop *both* folds in the config view —
  the default-fold *and* the sibling value-signature fold — so every declared
  variant gets its own variant-named structure. Two variants with identical
  values still each get a distinct named structure.
- **Interaction with item 2's completeness rule:** because every variant fully
  specifies all parameters (item 2 — no default-fill), each variant's config is
  fully explicit and independent.
- **Default config — resolved (2026-07-29):** the relevant axis is *has
  `ipParameters`* vs *has none*, not "variant vs non-variant use."
  - A block **with `ipParameters`** has an *implied default config* derived from
    the ipParameters' declared `value:`s, always emitted as a `<block>DefaultConfig`
    struct. This default is the baseline, not a fold — it is never suppressed.
  - Each declared variant is emitted 1:1 as its own `<block><Variant>Config`
    regardless of value equality (both folds stopped). So a parameterized block
    with variants `v0`/`v1` emits three structs: `DefaultConfig`, `V0Config`,
    `V1Config`.
  - A block **with no `ipParameters`** has no parameters, so no
    parameterized-config or variant question arises for it.
- **Owning plan:** [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md).
- **Disposition:** LANDED on examples (2026-07-29). Both folds removed in
  `_buildVariantConfigDescriptors` (`processYaml.py:~1613`) — every variant is
  now an independent canonical descriptor. `<stem>DefaultConfig` still emitted
  unconditionally (from `config.py::includeConfig`, independent of descriptors)
  → N+1 structs confirmed. New structs observed: mixed
  (`blockFVariant0Config`, `blockGGvariant0Config`), xif (`dutDutV0Config`,
  `srcSrcV0Config`, `sinkSinkV0Config`), ip_test (`srcVariantSrc0Config`).
  **xif TB hand-edit was NOT needed** — those Config references sit in
  GENERATED_CODE regions and re-rendered automatically (the hardening's
  user-region hazard was wrong). gen/run/run-vl green across base+pro (mixed C++
  blocked only by pre-existing `.cpp/.h`→`.cppm` orphan debt; ip_test run-vl
  pre-existing gap unchanged). **Product note:** on debayer product regen,
  `preprocess`/`interpolate` (block name ≠ context stem `debayer`) each gain
  their own `preprocessDefaultConfig`/`interpolateDefaultConfig`, re-typing their
  instances (the earlier "all three coincide" claim was wrong for the two
  siblings) — handled in the deferred product migrate.

### 4. Address Increment Validation

- **Feedback:** Add a check that a nested decoder's address footprint is
  contained within the higher-level decoder that routes to it, to prevent
  address-decode issues.
- **Containment rule (checked per nested slot; error if not met):**
  - **Nested decoder present:** validate against the nested decoder's routed
    footprint — its `addressIncrement × addressMultiples` (the increment alone
    would miss escapes). It must fit within the per-child increment that the
    higher-level decoder allocates to that slot, or error.
  - **No nested decoder:** validate against the decode space actually occupied by
    the nested register block. It must fit within the per-child increment that
    the higher-level decoder allocates to that slot, or error.
- **The two cases use different quantities:** a nested decoder is judged by its
  address increment (its routed footprint); a bare register block is judged by
  its decode space — the space actually decoded, not any larger nominal
  allocation. `ip_test` is the no-decoder case: a nested register block whose
  nominal space is larger than the parent's per-child window but whose decode
  space is small enough to fit, so it is valid. This is why the no-decoder check
  must be decode-space-based rather than nominal-space-based.
- **Placement:** database-time validation (address computation lives in
  `projectCreate`), reported as a durable error that names the offending nested
  block and both spans (allocated window versus decoded span). `ip_test` is the
  regression fixture for the fits-because-small-span case.
- **Owning plan:** [`plan-address-control-refactor.md`](./plan-address-control-refactor.md);
  test placement in [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md).
- **Disposition:** LANDED (2026-07-29) — nested-decoder containment pass added in
  `calcAddresses` (`processYaml.py:4372-4425`, guarded for projects with no
  `AddressGroups`); negative fixture `test_error_nested_decoder_overflow.py`
  (E4.1). Full base+pro suite `make gen` clean; all 42 address-control unit
  tests pass; `ip_test` model run green (exact-fit bridge accepted). NOTE: a
  pre-existing, unrelated `ip_test` `run-vl-src` `q_assert` (F4) was flagged —
  proven independent (byte-identical no-op: zero diff across ip_test after
  clean+gen) and tracked separately.

### 5. Module Conversion Standardization

- **Feedback:** Convert all block implementations to C++20 modules for
  consistency, regardless of parameterization, as the team preferred during the
  meeting.
- **Original decision (superseded):** convert only parameterized designs to
  modules. Because there were no parameterized designs in the wild at the time,
  this effectively converted no existing block implementation — only a
  newly-parameterized block would have been promoted.
- **Revised decision (team preference):** convert every block implementation
  (`.cpp` / `.h` → `.cppm`) to a module uniformly, independent of whether the
  block is parameterized.
- **Why now practical:** the original parameterized-only decision was made
  partly because full conversion was costly at the time. The migration tool has
  since improved (`make migrate` sequences the conversion, including the
  agent-driven `.cpp/.h` → `.cppm` port), so converting every block
  implementation is now practical where it previously was not — which is what
  makes the revised decision viable.
- **Impact:** this widens the conversion scope from "new parameterized blocks
  only" to "all block implementations," including existing non-parameterized
  in-the-wild blocks. That expands the migration surface — the agent-driven
  `.cpp/.h` → `.cppm` port — so item 6 must document this conversion as part of
  migration.
- **Owning plan:** [`plan-block-module-3section.md`](./plan-block-module-3section.md).
- **Disposition:** LANDED (2026-07-30, committed in `14ce4c4`; pro overlay in
  `7ee8fa3`). The `blockModule` gate is relaxed to all `hasMdl` blocks and every
  in-tree block implementation is a single `.cppm`: the paired `.cpp`/`.h` files
  are removed across all base examples and the pro `lmmiDemo`. The mechanized
  four-slot transplant carried the ordinary cases and flagged the edges it
  declines to attempt. Two follow-ons landed with it: the module-preamble import
  relocation (`b17a0fc`), which moves the generated `using namespace` out of the
  `moduleExport` region for non-register-handler blocks so the
  `// user imports here` slot is a legal preamble slot, and the migration of
  `endOfTest` to the `a2c.endOfTest` module (`7274b9c`) so a framework singleton
  is no longer a textual header in a module purview. Two consequences were
  recorded as status-report defects rather than item-5 residuals: the committed
  `ip_test/bridge` child was not regenerated onto the relocated preamble (B3),
  and the end-of-test startup gate added alongside the module regressed fast
  model-only examples (B1).
- **Original campaign plan (retained for the record):** GO (2026-07-29, reviewer
  green-light). Starts after item 2
  completes (sequential generator-editing on the shared `builder/base`
  submodule — no concurrent generator agents). Campaign plan:
  1. **Gate flip + pilot** on one simple non-parameterized single-block example
     — relax `config/project.yaml:139-140` (`blockModule` → `cond: {hasMdl: true}`,
     drop the `block` entry) and port that one block, to PROVE the flagged
     uncertainties (untemplated `--mode=module` `classDecl` path; exact fileMap
     form; reg-handler regenerate-not-port routing) BEFORE mass rollout.
  2. **HYBRID mechanized port (approved 2026-07-29).** Build a `codeText`-driven
     four-slot transplant into the migration (per
     `plan-item5-port-mechanization-assessment.md`): mechanically move the four
     user slots from `.h`/`.cpp` into the `.cppm` sections, drop boilerplate,
     rewrite `#include`→`import`. Mechanize the ~90% non-parameterized bulk;
     the mechanizer DETECTS-and-FLAGS the edges it should not attempt
     (parameterized/T2, module-hostile libraries e.g. OpenCV/pimpl, non-boilerplate
     slot-0 content, reg-handlers = regenerate-not-port), which stay agent-driven.
     Prove the mechanizer on the pilot block first, then roll out per example
     (~70 base across 12 examples + 2 pro `lmmiDemo`) with `make migrate` +
     `gen`/`run`/`run-vl` validation.
  3. **Product** (`apb_decode`, `cpu`) via the single product `make migrate`.
  The endlabel (item 1), variant-schema (item 2), and config (item 3) phases all
  compose into the one `make migrate`, so users migrate once.

### 6. Migration Guide Clarification

- **Feedback:** Review and clarify the migration guide so that users have
  explicit instructions and understand which steps are manual versus automated.
- **Problem:** The migration guide does not clearly separate automated steps
  (`make migrate`) from steps that require manual intervention, such as the
  agent-driven port and any schema changes introduced by item 2.
- **Owning plan:** the `migrate-project` skill and
  [`plan-yaml-migration.md`](./plan-yaml-migration.md).
- **Disposition:** LANDED (2026-07-30, committed in `3ee90d5` and `477d6c6`).
  `migrate-project.md` now states, per phase, what is automated and what is not:
  - the **variant-schema phase** is documented as standalone, text-only, scoped
    to `parameters:` sections, lossless, idempotent, and free of manual items
    (item 2's migration surface);
  - the **`endmodule:` label re-stamp** is documented with the reason it is
    database-backed and therefore reachable only through `make migrate`, plus the
    idempotence and owner-gating rules and the fact that a fully-generated RTL
    block carries no user end label (item 1's migration surface);
  - the **already-migrated child** case is documented explicitly: a child stamped
    `yamlFormat: 2` draws no `TODO_*` report, yet must still be re-migrated once
    the builder qualifies cross-project identifiers, because the parent imports
    the qualified name that a stale child still exports;
  - the **redundant preamble import** case is documented with the rule to remove
    rather than relocate, and why a stray `using namespace` makes the following
    generated imports illegal (item 5's migration surface);
  - `pysrc/migrateVariantSchema.py` and `pysrc/migrateModuleEndlabel.py` are
    listed in the phase-library reference.
  The `address-migration.md` and `manage-build.md` skills were reconciled in the
  same pass. What remains is not documentation: the `TODO_PORT` transplant for
  the cases the mechanizer declines, which is item 5's recorded scope.

### 7. Action Item Release Planning

- **Feedback:** Identify and communicate to the team which action items from the
  review will be tackled as part of the upcoming release and which will not.
- **Problem:** The release scope for the six items above is not yet decided or
  communicated.
- **Owning plan:** this document — the release-triage table below is the
  communication artifact.
- **Disposition:** DECIDED (2026-07-29) — all items target this release; see the
  release-triage table.

### 8. Contained-Block Config Inheritance (`inheritContainerParam`)

- **Origin:** surfaced by the debayer product migration (dogfooding items 3/5),
  not the original review. It is the resolution of the product note recorded on
  item 3's Disposition (siblings `preprocess`/`interpolate` gaining their own
  `preprocessDefaultConfig`/`interpolateDefaultConfig`).
- **Problem:** item 3's strict 1:1 per-block config means two sibling contained
  blocks that share one config context each get a distinctly *block*-named config
  struct (`preprocessDefaultConfig`, `interpolateDefaultConfig`) — byte-identical
  fields but distinct C++ types. A shared, Config-parameterized channel payload
  between them (`bayer_preprocess_stream_t<Config>`) then cannot bind: no single
  `Config` satisfies both the producer and consumer ports. This is the
  documented-unsupported Config-strict cross-block link (`classDecl.py:186-191`).
- **Design decision (2026-07-30):** an explicit, per-**instance** inheritance
  flag. A contained-block instance may declare `inheritContainerParam: true` **in
  place of** its `variant:` selector; that instance is then typed with the
  **container block's active config** (transitively — if the container is itself
  instantiated as variant `V1`, the child gets `<container>V1Config`), instead of
  the child's own descriptor/default config. The child block keeps its own
  `params:` and still emits its own `DefaultConfig` for standalone use.
  - **Preconditions (db-time errors):** the child's params must be a by-**name**
    subset of the container's; `variant:` and `inheritContainerParam:` are
    mutually exclusive; the container must be parameterized; the child must have
    params; and the container and child must be the **same owning project**
    (no cross-project inheritance for now).
  - **Values** come from the container's config; the child's own declared param
    values remain only its standalone defaults.
- **Why it honors items 1 and 3:** item 3 (per-block config for *independently*
  parameterized blocks) is untouched — an inheriting block still emits its own
  config; only the *contained instance's* Config selection changes. item 1
  (cross-project owner-qualified identity) is preserved by the same-project
  restriction. It is the C++ analogue of the SV parent→child param
  name-forwarding that already exists (`_resolveSvInstanceParams`,
  `.CHILD(PARENT)`), made explicit rather than implicit.
- **Mechanism (key insight):** a contained child renders inside the container's
  templated class scope, so inheritance reduces to spelling the container's own
  template symbol `Config` for that instance; C++ template instantiation resolves
  the concrete struct (including the transitive variant case) at the container's
  own instantiation site. No config value is plumbed.
- **Thunker orthogonality (confirmed):** thunkers are container-level members
  (`classDecl.py:200`, `constructor.py:206-259`) and key on cross-*interface*
  (protocol) ends; this feature is same-interface *config* unification. The two
  are orthogonal and both container-level, so inheritance removes the config
  mismatch without any thunker, and thunkers stay reserved for genuine protocol
  adaptation (no proliferation for the config case).
- **Implementation (~4 files):** (1) `schema.yaml:222` add
  `inheritContainerParam: optional(false)` to `instances`; (2)
  `processYaml.py:1466-1513` `_resolveInstanceConfigFields` inherit branch + a new
  contracted `inheritContainer` field on both returns; (3)
  `intf_gen_utils.py:435-445` `cpp_config_struct_name` returns `'Config'` when
  `inheritContainer`; (4) `postParseChecks.py` the five validations above. **No
  change** (verified) to `_resolveSvInstanceParams`, `_resolveConnectionConfigOverride`
  (both ends spell `Config`, `dst` tie-break moot), or thunkers. The subset check
  is **load-bearing** for the untouched SV path, so it must run in `projectCreate`.
  One invariant to re-confirm at implementation: nothing spells an inheriting
  instance's `Config` outside the container's templated scope.
- **Owning plan:** extends item 3 /
  [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md).
- **Disposition:** generator changes IMPLEMENTED (2026-07-30). Landed: the
  `instances.inheritContainerParam` schema field; the `_resolveInstanceConfigFields`
  inherit branch + contracted `inheritContainer` field on both returns;
  `cpp_config_struct_name` spelling `'Config'` for an inheriting instance; and the
  five preconditions (a subset, b variant-mutex, c container parameterized,
  d child has params, e same owning project) plus the top-instance guard, all in
  `calcBlockConfigInfo::validate_inherit_container_params` (relocated there from
  the initial `postParseChecks` home so they run once, off this pass's prebuilt
  maps, with no parse-timing or SQL concerns). Six unit tests
  (`unittest/test_inherit_container_param.py`: 1 positive + 5 negatives) green;
  `make db/gen -j` clean on `ip_test` and `simple_ip`. Documented in the
  `design-parameterizable-blocks` skill.
- **Debayer acceptance PASSED (2026-07-30):** `u_preprocess`/`u_interpolate`
  converted to `inheritContainerParam: true`; db-create clean (no validation
  fired); the `bayer_preprocess_stream` channel now binds — both siblings and the
  channel type on the container's `<Config>` (was the `preprocessDefaultConfig`
  vs `interpolateDefaultConfig` mismatch at `model/debayer.cppm`), and the
  container TU precompiles rc=0. Children still emit their own DefaultConfig for
  standalone use.
- **Two HDL-wrapper follow-ons the acceptance surfaced (both landed + reviewed):**
  a `hasVl` leaf instantiated *only* via `inheritContainerParam` has an empty
  *instantiated*-variant view, which broke the SV leaf wrappers that keyed off it.
  Fix = source from the block's DECLARED variants/params instead:
  (1) `module_hdl_wrapper.py::param_names` reads the block's declared `params`
  (the source `parameterized_decls` already uses), not the first instantiated
  variant — fixed the `.svh` DUT-wrapper `StopIteration`; (2) a new projectOpen
  `declaredVariants` view field (resolved binding values, same shape as the
  instantiated `variants`) feeds the `.sv` per-variant trampoline dispatch +
  `render_trampoline`, fixing a *silent* misrender (a declared-but-uninstantiated
  variant had fallen through to `render_non_parameterizable`, emitting a broken
  parameterless `.sv`). Both proven byte-identical across the whole base+pro
  wrapper corpus; the inheriting-leaf `.sv` now binds resolved literals and
  elaborates in Verilator rc=0.
- **Still open:** the (e) cross-project negative fixture, deferred because it
  needs a composed multi-project fixture rather than a single-file unit fixture;
  and the debayer composed *build* remains blocked on the unrelated product-code
  items #1b (rgb_video_sink import purview) and #3 (`b2p_deb_conv`
  `bayer_pattern_t`), which are user-owned and out of scope for this feature.

## Release-Triage Table

The following table is the item-7 deliverable.

**Decision (2026-07-29):** all items below are targeted for **this release**.
Landing them together avoids forcing users through multiple migrations — items 2
and 5 both add migration surface, and splitting them across releases would make
users run `make migrate` more than once. Execution is therefore in scope now.

| # | Item | Type | Owning Plan | Target | Status |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | Project naming in package | Bug fix | plan-param-constant-collision | This release | **CLOSED** 2026-08-03 |
| 2 | Variant definition schema | Schema change | plan-ip-namespaces-and-parameterization | This release | **CLOSED** 2026-07-29 |
| 3 | Variant config generation | Correctness | plan-parameterizable-config-template | This release | **CLOSED** 2026-07-29 |
| 4 | Address increment validation | New validation | plan-address-control-refactor | This release | **CLOSED** 2026-07-29 |
| 5 | Module conversion standardization | Consistency | plan-block-module-3section | This release | **CLOSED** 2026-07-30 |
| 6 | Migration guide clarification | Documentation | migrate-project skill | This release | **CLOSED** 2026-07-30 |
| 8 | Contained-block config inheritance | New capability | plan-parameterizable-config-template | This release | **CLOSED** 2026-07-30 (cross-project negative fixture deferred) |

Item 7 is this table. Item 8 was raised by the product migration rather than the
review and is listed here because it shares the release and the migration
surface.

## Change Log

- 2026-07-29: Document created; captured seven review action items and linked
  each to an owning plan. Release targets remain to be decided (item 7).
- 2026-07-29: Elaborated items 1–5 with reviewer detail — identifier-versus-
  filename split and prefix-dedup rule for item 1 (simplified by first-class
  `projectName`; the old `Q-C8` absolute-versus-conditional decision is
  superseded); nested-variant schema example and hard-cutover migration for
  item 2; always-emit variant-named config for item 3; decoder-increment versus
  decode-space containment rule with the `ip_test` no-decoder case for item 4;
  and full block-implementation module conversion for item 5. Items 6 and 7
  unchanged.
- 2026-07-29: Release decision — all items target this release (single migration
  for users; items 2 and 5 both add migration surface). Status-report Open Items
  updated with a cross-reference that supersedes the Q-C8 Role C and
  variant-config deferrals. Execution begun via the owning plans.
- 2026-07-29: Item 4 LANDED (nested-decoder containment check + negative
  fixture; full suite gen clean, address unit tests pass; pre-existing unrelated
  ip_test run-vl-src q_assert flagged separately). Added item-2 parameter-
  completeness rule (every variant defines all parameters; no default-fill) and
  item-1 SV module-name qualification scope. Sequencing continues: item 1 next,
  then item 3, then the items 2+5 migration campaign (paused for go-ahead).
- 2026-07-29: Item 5 campaign progress — Phase A porter (`migrateBlockModulePort.py`,
  `migrate --port`, four-slot codeText transplant) + gate flip proven on
  `examples/simple`; module-mode context-import generator gap CLOSED in
  `templates/systemc/classDecl.py` (re-emits base interface-context imports, deduped,
  no-op for already-converted blocks) and porter trimmed to pure four-slot. Stage B-1
  running: reg-handlers AND decoders are 100% generated → delete-rescaffold-generate
  (NOT transplant/flag), proven on `mixed` + `apbDecode`. Rollout is staged per user;
  product (debayer) migration held for explicit confirm.
- 2026-07-29: Code-quality review of #116 `processYaml.py` additions (read-only,
  builder-base-development). Decisions: (T1) extract the inline module-identity block
  `__init__:3620-3695` into `deriveModuleIdentities()` — mechanical, queued behind B-1;
  (T2a) DELETE the `processSimple` old-form rejection guard `:6116-6121` entirely — the
  yamlFormat:2 migration fully handles conversion and stale old-form is just bad YAML
  for the regular error path; NO special-case error in the parser (user decision);
  remove any unit test asserting the bespoke message; (T3) INITIAL "no change" verdict
  was WRONG and reversed after a scope-mechanism trace (see below).
- 2026-07-29: T3 REVERSED then LANDED. Trace established validation is SCOPE-BASED
  (`lookupInScope` walks the include chain) and the `parameters.block` FK checker forces
  block-parsed-before-variant, so the block's params are complete at the variant row.
  `validateVariantConfigFold` iterated ALL context buckets globally (scope-BLIND) →
  false positives across mutually-invisible same-project scopes → an incorrect anti-pattern,
  not a needed guard. FINAL (user-directed): (a) MOVE completeness to a variant-row `_post`
  `_post_validateVariantParameterCompleteness` on `parametersvariants`; (b) REMOVE
  `validateVariantConfigFold`; (c) NO split-rejection — a split variant now fails completeness
  naturally. Root cause of the repeated wrong turns captured in `SCHEMA_SPECIFICATION.md`
  new sections (Governing Invariants, `_post` contract, `flat`, Foreign-Key Invariants,
  "Choosing Where a Validation Belongs"). T1/T2a/T3 all LANDED + validated: gen rc=0 across
  variant examples, negative fixture passes from the `_post`, suite 81/84 (3 = B-2 gate-flip
  debt). Config-emission scope-verification PASSED (no consumer relied on fold uniqueness).
- 2026-07-30: Stage B-2 example rollout run; guard held (0 `TODO_PORT_UNPLACED`). Surfaced 4
  defects (see `project_item5_module_port_hybrid` memory): D1 nested sibling `#include`→`import`
  gap (CLEAR-BUG), D4 hierVlDemo stale include-guard not recognized (CLEAR-BUG), D3 xif redundant
  user-region import closing the preamble (pre-existing, data/`migrateModuleHeader` fix), D2
  `TODO_PORT_NO_CPPM` = intentional cross-project boundary, operational bottom-up migrate (no code
  fix). Fix agent running; debayer product migration held until suite clean.
- 2026-07-30: Code-quality item (T4) — HOIST the singular-to-dict conversion. `processSimple`'s
  `:6061-6063` conversion is invisible to callers, so `_constants` re-inspects the raw `item` with
  `isinstance(item, dict)` guards (`:6363`, `:6377`, `:6402`) for a shape that cannot occur
  (`constants` is `flat`, NOT `_singular`). User direction: make it clean (option B). PLAN: extract
  the conversion into a helper keyed by `context+section` vs `schema.data['singular']`; call it at
  the two scalar entry points — top-level dispatch `:6015` and `processSubTable` `nested.items()`
  `:7746`; REMOVE it from `processSimple` so "`item` is a dict" is a hard precondition; delete the
  `_constants` guards, read the dict directly. Verify full unit suite + example gen (DB unchanged).
  QUEUED behind the running porter-fix agent (shared submodule — no concurrent parser edits).
  REFINEMENT (user): the helper's non-singular non-dict fall-through IS a malformed-YAML case —
  today it crashes opaquely at `:6067` `for field in item` (TypeError on a scalar). So the helper
  must convert-if-singular ELSE emit a clean YAML error via the existing path (cf. `:6086-6088`),
  making the dict precondition real and replacing the opaque crash with a proper diagnostic.
  Implementation must first confirm no section legitimately relies on the silent fall-through.
  UPDATE 2026-07-30: Phase-1 gate FIRED — premise violated. Collapsed nested sub-tables pass
  LISTS through `processSimple` legitimately (e.g. `modportGroups` `inputs: [pready,prdata,pslverr]`
  via `:7746` with `outer != None`; the `:6067` field loop is guarded by `if outer == None` and the
  collapsed `groups` singleEntryList consumes the list). A blanket top-of-`processSimple` dict
  precondition breaks `make db` (ip_test exit 2 vs 0). So the fall-through is malformed ONLY at the
  top-level dispatch (`outer == None`), NOT in the nested collapsed path. NARROWER DESIGN (agreed
  approach): coerce singular at `:7746` only (both `_singular` sections — `signals.signalType`,
  `parameters.variants.params.value` — flow there; NO no-op top-level coercion); put the dict
  precondition ONLY inside the existing `if outer == None:` block; drop `_constants` guards
  (constants is top-level/`outer==None`, dict-ness still guaranteed). Awaiting user confirm.
- 2026-07-30: B-2 defect fixes LANDED + verified. Item-5 mechanized port now clean suite-wide
  (D1 sibling-include→import, D4 structural guard, D3 xif data-only, D2 common/cpu bottom-up);
  zero critical TODOs. Two residuals, neither an item-5 porter bug: mixed/blockF = tolerated
  parameterized hand-port edge (debayer will hit same); pySocket = pre-existing orphaned-user-
  include (non-block helper includes now-gone base .h; migrateIncludes/orphan concern). Pending
  before debayer: T4 hoist (now unblocked), porter code review, 3 gate-flip unit tests.
- 2026-07-30: External review of #116 changes — 4 findings, all CONFIRMED by adversarial re-verify
  (tried to refute each). NEW item T5 (fix scope TBD by user):
  - A (High) cross-project variant-config loss: descriptor builder reads collapsed `data_by_parent`
    nesting (`processYaml.py:1660`,`:1703`) keyed by `(block,variant)`+bare `param` (no projectName),
    so composed same-`(block,variant)` bindings overwrite → `getBlockConfigView` emits Config for one
    project while FOREIGNCONFIGHEADERS (`:4732`, leaf table w/ projectName) still scaffolds a header
    for the other → missing Config type / wrong values. Collapse is at TWO levels (variant key AND
    param anchor); reviewer's "qualify intermediate key" is INCOMPLETE. FIX: build descriptors from
    leaf table `parametersvariantsparams` grouped by projectName (mirror `:4732`). Gap in items 2/3.
  - B (High) SystemC `.cppm` module names not project-qualified: `moduleScaffold.py:88,127` use
    `cpp_block_module_name(data["blockName"])` (plain blockName); `blockModuleName` (`:3677`) is
    SV-only; SV gate `:3681-3698` has no C++ analogue. Item 5 made every block a `.cppm` → two
    same-named composed blocks emit duplicate `export module ip.block;` → hard C++20 build break.
    FIX: route persisted qualified identity into C++ module name + add C++ uniqueness gate. Gap
    opened by items 1+5.
  - C (Medium, latent) `qualifyModuleIdentity` (`:94-104`) does not sanitize projectName → `my-project`
    yields illegal SV `module my-project_ip`; C++/variant/foreign paths already sanitize (`:1399`,`:4745`);
    no projectName charset validation. FIX: sanitize in qualifyModuleIdentity, dedup sanitized-vs-sanitized.
  - D (Low, harmless today) `:1877-1879` `... if variantEntry else {}` masks a postParseChecks-guaranteed
    relationship. FIX: index directly.
  - test_nested_ownership KeyError 'block' = KNOWN gate-flip debt (pending unit-test fix), not new.
- 2026-07-30: T4 LANDED as-is (user approved; narrower design already in `processYaml.py`, verified
  equivalence + zero regressions). User approved full remaining order: T5 (A+B+C+D) → pySocket
  orphan-include → 3 gate-flip unit tests → full green verify → debayer. Executing sequentially.
- 2026-07-30: T5 A/C/D LANDED + verified (all in `processYaml.py`): A builds variant descriptors
  from leaf `parametersvariantsparams` grouped by projectName (collision-proven: both projects'
  Configs now emit; single-project byte-identical); C sanitizes projectName in qualifyModuleIdentity;
  D direct-indexes the variant entry. Suite gen green; unit 81/84 (known gate-flip debt only).
  T5-B STOPPED at gate — scope larger than a single chokepoint: `cpp_block_module_name`/`cpp_base_
  module_name` take a bare name, so ~10 emit/import sites must each source the persisted qualified
  token (self/export moduleScaffold:88,127; sub-block intf_gen_utils:268; self intf_gen_utils:528;
  module_hdl_wrapper:184; testbench:103,289,379; blockRegistrar:112; porter migrateBlockModulePort:545),
  PLUS a new subBlockTypes view field (for testbench:289), PLUS updating the porter's already-emitted
  (non-generated-region) sibling imports or builds break. NO new C++ gate needed (`.block`/`.base`
  are 1:1 with already-gated blockModuleName). B only bites composed builds with same-named blocks.
  DECISION: user chose DO B NOW, with a HARD CONSTRAINT — the project qualifier must NOT reach the
  logging infrastructure at log init. Confirmed safe: logging uses the sc_module INSTANCE name
  (`this->name()`, `constructor.py:458`) + a "block" verbosity string; NO logging code uses the
  module-name formatters, so B (which only rethreads `cpp_block_module_name`/`cpp_base_module_name`
  inputs) structurally cannot leak. B must NOT touch sc_module instance names, `log_` init, or
  addBlock/setLogging/blockVerbosity/logPrint 'block' args. B in progress.
- 2026-07-30: T5-B LANDED + verified where tree builds (hierVlDemo/xif/axi4sDemo green; composed
  same-name proof rootProj_sharedLeaf vs childProj_sharedLeaf PASSED; logging constraint honored —
  no log identifier uses qualified name; test_cpp_module_map 6/6). blockModuleName always prepends
  owning project (deduped). Sites: moduleScaffold:88/127, intf_gen_utils:268/528, module_hdl_wrapper:184,
  testbench:103/289/379, blockRegistrar:112, migrateBlockModulePort:545; +view fields subBlockTypes
  blockModuleName (:1950) & excluded instInfo instanceTypeModuleName (:2005); nested/testBlock.cppm:20
  sibling import hand-updated.
  BLOCKER (surfaced, NOT T5/B): fresh `make clean && make db` fails on ~8 examples —
  `constant 'X': maxValue must be > 0 when parameterizable` (apbDecode ASIZE is a PLAIN constant, so
  the parameterized-eval WIP is mis-flagging plain constants). Committed validation `processYaml.py:6494`;
  uncommitted WIP `rawMaxValue = ret['maxValue']` (beyond the landed T4 diff; not mine). Blocks full-suite
  verify + pySocket + unit tests + debayer. Awaiting user: pause vs read-only investigate the mis-flag.
- 2026-07-30: BLOCKER ROOT-CAUSED + FIXED (user OK'd revert). `schema.py:1024` stores an `optional(N)`
  parenthetical default as a STRING ("0"), so `ret['maxValue']` for a constant w/o maxValue is the
  string "0"; the WIP line `rawMaxValue = ret['maxValue']` (beyond the reviewed T4 diff) made
  `userMaxProvided = "0" not in (0,None,'')` TRUE → flips directParam → plain constants (apbDecode
  ASIZE) mis-flagged parameterizable → `:6495` ">0" error. FIX: reverted `:6407` to
  `rawMaxValue = item.get('maxValue', 0)` (int-0 default; item is always a dict here). Fresh db-create
  now PASSES on apbDecode (plain) AND ip_test (real ipParameters) — string-"0" bug was the sole cause.
  Running full unit suite to confirm 81/84 baseline restored, then resume order (T5/B review → pySocket
  → 3 unit tests → full verify → debayer).
- 2026-07-30: T5 A/B REVIEW clean (both SOUND; B logging non-leak confirmed; A single-project byte-identical;
  only unreachable theoretical risks + a pre-existing `.get()` fallback). pySocket FIXED — determination
  pySocket-SPECIFIC (unresolved migrate TODO; migrateOrphans sweep already flags dangling `<block>Base.h`
  user includes as TODO_USER_INCLUDE, so debayer user files ALREADY protected). Fix = 2 pySocket user files
  (import pySocket.base after textual includes; +projectName arg on registerBlock/createInstance). pySocket
  builds + runs clean. New LSP diagnostics (module-not-found across dataGen/cpu/blockGLeaf/xif_dut/pySocket
  .base, blockBRegs extraneous brace, dutInverted, cpu shared_ptr) assessed as mixed post-B regen state +
  C++20-module-LSP-in-isolation (no .pcm) — NOT authoritative; capstone full clean rebuild in progress to
  confirm/expose. Capstone also fixes the 3 gate-flip unit tests + runs full unit suite. Then debayer.
- 2026-07-30: CAPSTONE VERIFY done. Full clean rebuild GREEN suite-wide (simple/apbDecode/axiDemo/
  axi4sDemo/helloWorld/hierVlDemo/nested/pySocket/xif + composed simple_ip/ip_test); ZERO TODO_PORT_UNPLACED;
  B qualified names consistent (build-green proof). ALL LSP diagnostics = FALSE-POSITIVES cleared on clean
  rebuild (incl. cross-project cpu→common_cpu.base; blockBRegs brace = stale legacy file, live .cppm fine;
  dutInverted/cpu shared_ptr = pre-rebuild cascade). Unit suite 83/84. test_nested_ownership + test_layout_nested
  FIXED. TWO items remain (neither a regression/generator defect): (1) test_layout_hierarchical RED — stale
  hier-layout FIXTURE (override pins retired `block` .h/.cpp + `blockBase_hdr` gone; masks Unknown-section
  crash via committed stale files); fix = fixture surgery (override→inherit base .cppm, delete committed stale
  .cpp/.h/*Base.h, regen golden); generator correctly rejects it. (2) mixed/blockF TODO_PORT_PARAM = known
  parameterized hand-port edge (debayer will need same technique). Awaiting user: hier fixture fix now vs defer;
  green-light debayer.
- 2026-07-30: User chose FIX-NOW hier fixture, HOLD debayer. hier-layout fixture FIXED: removed stale
  `block`/`blockBase` fileMap override entries (now inherits base `.cppm`), deleted 9 stale git-tracked
  GENERATED pre-flip `.cpp/.h/*Base.h` fixture artifacts (core/leaf), regen golden = clean `.cpp/.h`→`.cppm`
  flip. Unit suite 84/84. Deletions verified scoped + git-tracked (recoverable); harness security flag was a
  false alarm given the explicit Fix-now authorization. #116 REVIEW-FEEDBACK COMPLETE — all 7 items + T5
  review findings A/B/C/D + maxValue fix + pySocket + 3 unit tests landed & verified (suite green suite-wide,
  84/84, zero TODO_PORT_UNPLACED, all LSP diagnostics false-positive). DEBAYER product migration = remaining
  separately-gated step, ON HOLD per user; mixed/blockF param hand-port technique still to establish (debayer).
- 2026-07-30: User green-lit DEBAYER — discovery shows product already yamlFormat:2 + hierarchical +
  includes/module-header done; 5 param blocks + reg-handler + OpenCV/pimpl edges (raw_video_src, rgb_video_sink)
  already `.cppm`; NO remaining param hand-port edges. Remaining narrow work (execution agent running): migrate
  debayer; apb_decode DELETE-RESCAFFOLD (decoder, verified no user code); cpu 4-slot AUTO-PORT (non-param; real
  code in all 4 slots + GMF includes asyncEvent/workerThread/modelComm — no-loss diff-verify before deleting
  legacy); add EXTRA_PRJ_SRC_DIRS(fw/src) + EXTRA_SC_GEN_FILES(fw/debayerRegAddresses.h) to include/make/shared.mk;
  re-migrate clean + build. isp_shared (types-only submodule, already migrated) NOT re-migrated (skip unless build
  demands). User-owned files untouched: b2p_deb_conv*, rgb_img_writer*, *_config.h, fw/src/*.
- 2026-07-30: DEBAYER product-side ports DONE + no-loss-verified (apb_decode delete-rescaffold, cpu 4-slot,
  make seam EXTRA_SC_GEN_FILES=fw/debayerRegAddresses.h; clean port report). BUT build BLOCKED:
  `module 'isp_shared_shared_types' not found` — regenerated debayer imports QUALIFIED context names
  (isp_shared_isp_types) while isp_shared exports BARE (isp_types); -fmodule-file keys bare; debayer
  user-region hand-import bare vs generated-region qualified (internal disagreement). ROOT CAUSE = my
  execution-agent SKIPPED isp_shared migrate (wrong). USER CORRECTION: migrate rule is SUB-PROJECTS FIRST —
  isp_shared's own migrate run re-emits its qualified context-module identity for cross-project consumers;
  skipping a seemingly-already-migrated sub-project breaks cross-project module-name consistency. CORRECTED
  PLAN: migrate isp_shared FIRST, then re-migrate/rebuild debayer, + any debayer-side key/hand-import fix the
  in-flight diagnosis identifies. Executing once the read-only diagnosis (reading isp_shared/debayer) returns
  (no concurrent --write on trees it is reading). LESSON: never skip a sub-project's migrate even if it looks
  already-migrated — sub-projects-first is required for cross-project qualified-module-name consistency.
- 2026-07-30: SKILL REFRESH decided (user: ALL 11, AFTER debayer). Canonical source = `builder/base/rules/skills/*.md`
  (+ `builder/pro/rules/skills/` for run-tandem); `.claude/.gemini/.opencode/.agents/.cursor` are GENERATED via
  `make agents-setup`/`cursor-setup` — edit source only, then re-deploy. 11 stale skills: (1 Critical) systemc-core —
  Module Structure still two-file .h/.cpp → single templated `<block>.cppm` (moduleScaffold blockModuleHeader/
  moduleExport/classDecl regions; `template<typename Config> SC_MODULE ... public <block>Base<Config>`). (2 High)
  migrate-project — add the two wired-but-undocumented phases: variant-schema migration (migrateVariantSchema.py,
  per-row→nested, in yamlFormat:2) + module-endlabel restamp (migrateModuleEndlabel.py, in --sweep). (3 High)
  design-parameterizable-blocks — old flat per-row variant list → nested `variant: {PARAM: val}`; completeness rule
  (bind ALL params, no default-fill); always-emit Default+per-variant Config. (4 High) review-model — .h/.cpp/*Base.h/
  *Includes.h → .cppm regions. (5-6 Med) systemc-interfaces, systemc-synchronization — ".h/.cpp after GENERATED_CODE_END"
  → .cppm user regions. (7-8 Med) rtl-to-systemc, systemc-to-rtl — model .cpp → .cppm, *Base.h→*Base.cppm (rtl-to-systemc
  *_types.h = verify-then-fix). (9 Med-Low) manage-build — newmodule scaffolds .cppm model skeleton (gate blockModule
  cond:hasMdl); add .cppm to impl-file list. (10 Low) design-register-decode — add nested-decoder containment check (item4).
  (11 Low) address-migration — <block>Base.h → .cppm. NO change: design-architecture, setup-project, systemc-patterns,
  verify-testbench, verify-cosimulation, all 6 RTL skills, manage-address-space, run-tandem, run-regression-tests, debug.
  Item-1 qualified names = conditional dedup → no identifier rewrites, at most a one-line caveat. builder is user-managed
  submodule (no stage/commit).
- 2026-07-30: SKILL REFRESH DONE — all 11 updated in canonical `builder/base/rules/skills/` + redeployed via
  `make agents-setup`/`cursor-setup` to .claude/.gemini/.opencode/.agents/.cursor (spot-checked). systemc-core
  single-.cppm rewrite; migrate-project +variant-schema/+endlabel phases; design-parameterizable-blocks nested
  variant+completeness+config; review-model + 6 .h/.cpp→.cppm rewords; design-register-decode containment row;
  address-migration Base.h→.cppm. VERIFIED: no generated `*_types.h` exists (only a hand POC), rtl-to-systemc
  reworded to import-from-*Includes.cppm. No stage/commit. Debayer cross-project fix still running.
- 2026-07-30: migrate-project skill GAP closed — it explained sub-projects-first (Section 1 "Composed builds")
  but only around the yamlFormat:2 stamp gate (TODO_UNMIGRATED_SUBPROJECT fires only on UNstamped children).
  Added a note: an already-yamlFormat:2 child STILL needs its own regen when the builder qualifies cross-project
  names (contextModuleIdentity→<owner>_<ctx>) — else stale bare exports vs parent's qualified imports →
  `module '<owner>_<ctx>' not found`, which no TODO catches (the exact debayer/isp_shared bug). Redeployed via
  agents-setup/cursor-setup; note verified present in all 5 deployed trees (.claude/.gemini/.opencode/.agents/.cursor).
  PROCESS: any canonical-skill edit needs a follow-up agents-setup/cursor-setup or deployed copies go stale.
- 2026-07-30: DEBAYER cross-project blocker RESOLVED. Root cause was builder-version SKEW: debayer builder
  7fd14fe qualifies contextModuleIdentity; isp_shared builder ca46116 (older #116) NEUTRALIZED qualification →
  bare exports. Earlier "regenerate isp_shared" failed because isp_shared's OWN builder was the non-qualifying
  one. USER aligned both submodules' builders to 7fd14fe. Then: regenerated isp_shared (make clean+gen; migrate
  hit stale-db BLOCKMODULENAME, clean+gen is the fallback) → now exports isp_shared_isp_types/isp_shared_shared_types;
  debayer user-region bare imports already removed. Module graph now qualified-consistent end-to-end (.gen/cpp-modules.mk
  providers + -fmodule-file keys all qualified; zero bare). `module not found` GONE.
  DEBAYER BUILD still not linked — 3 NEW downstream errors surfaced by dogfooding (past module resolution):
  (1) GENERATOR/migration — preamble import-ordering: generated classDecl `import debayer; import isp_shared_isp_types;`
      lands AFTER a user-region `using namespace debayer_ns;` (illegal) in preprocess/interpolate/rgb_video_sink.cppm;
      known module-preamble-placement class ([[project_module_preamble_import_placement]]).
  (2) GENERATOR — variant-config type mismatch: debayer.cppm:130 channel typed bayer_preprocess_stream_t<interpolateDefaultConfig>
      vs preprocess port's <preprocessDefaultConfig>; per-block Config resolved from wrong block on a cross-block channel.
  (3) USER-CODE (pre-existing, not migration) — b2p_deb_conv.h:31 bayer_pattern_t vs vreader.h enum bayer_pattern_e.
  #1/#2 = #116 generator fixes; #3 = product code. Awaiting user direction on scope.
- 2026-07-30: DIAGNOSIS of #1/#2. #1 NOT a generator bug — stale REDUNDANT user-region `import debayer;`+
  `using namespace debayer_ns;` in the preamble gap of preprocess/interpolate/rgb_video_sink.cppm; classDecl
  re-emits both, so the stray `using` strands the generated imports (xif clean-gap proves generator correct).
  Same class as xif-D3; recurs = the systemic user-region-redundant-import gap. USER DECISION: fix the 3 files
  (remove redundant lines) + COVER IN SKILL (migrate-project 4a: redundant gap import that classDecl re-emits →
  REMOVE not relocate); do NOT complicate migrate code (no migrateModuleHeader dedup machinery). (In progress.)
  #2 = documented-UNSUPPORTED pattern (classDecl.py:186-191): item-3 gives preprocess/interpolate DISTINCT
  DefaultConfig types (byte-identical fields, distinct C++ types) → the Config-parameterized channel payload
  between them cannot bind (no single Config satisfies both ports). `_resolveConnectionConfigOverride`
  processYaml.py:1615 dst tie-break picks consumer config = minor mis-direction, NOT the fix. USER DECISION:
  wants preprocess+interpolate to SHARE one config, BUT tread carefully — VERIFY practicality first, honor the
  spirit of item-3 (always-emit per-block config), EVALUATE what shared-config means before implementing.
  → read-only evaluation queued after #1. #3 (b2p_deb_conv bayer_pattern_t) stays product-code for user.
- 2026-07-30: #2 DESIGN DIRECTION chosen (user): EXPLICIT shared parameterization via a CONTAINED BLOCK
  INHERITING ITS PARENT's parameterization (Option B, intent-based — NOT structural dedup A). Shared config =
  the parent's own named config (debayerDefaultConfig), so no coincidental-identity/neutral-naming corner cases.
  Model: item-3 per-block Default+variant configs UNCHANGED (standalone identity); when a contained block inherits,
  parent instantiates it as childBase<parentConfig> not childBase<childDefaultConfig> → co-contained children share
  parent config → shared-payload channels bind; the :1615 dst tie-break becomes moot. Cross-project keeps qualified/
  distinct (item-1). OPEN iteration points: (1) declaration site — child-opt-in vs instance/containment-level (lean
  instance-level, block advertises eligibility); (2) param compat — strict by-name subset child⊆parent, db-time error
  else (no silent mapping) vs mapping escape hatch; (3) variants — parent variant propagates (debayerV0→children V0),
  inherited child hides own variants; (4) BOUNDARY case — contained child from ANOTHER project: does inheritance
  cross the boundary (parent-config type crosses, owner-qualified) or is cross-project containment excluded. Read-only
  mechanism analysis (a57018fd749d993ef) grounding feasibility (existing propagation? where child Config chosen).
  NOT implementing #2 until model settled with user. Iterating.
- 2026-07-30: #2 mechanism analysis CORRECTS the premise. Blocks ALREADY co-parameterized: share one
  configContext (debayer.yaml), all `defaultConfig`=`debayerDefaultConfig`. Bind breaks on a 2nd axis: per-variant
  struct name is BLOCK-name-derived (`cpp_variant_config_name` = {block}{Variant}Config); every instance binds
  variant `default`, so item-3's no-fold emits preprocessDefaultConfig/interpolateDefaultConfig distinct instead of
  the shared debayerDefaultConfig. Pre-item-3 a values-equal-default variant folded → shared → bind worked. NO
  parent→child Config propagation exists / not expressible in YAML → inheritance is NET-NEW. Boundary discriminator
  = `isForeign` (contextOwningProject vs declaringProject, processYaml.py:1682-1690); orthogonal to qualifyModuleIdentity.
  THREE option shapes (small→large): (1) re-enable same-project default-fold (few lines in _buildVariantConfigDescriptors,
  isForeign=False + values==context-default → useDefault=True) — but WALKS BACK item-3's explicit stop-the-folds
  (default-fold + sibling value-sig fold per [[project_variant_config_model]]); (2) ALIAS middle — keep item-3 per-block
  NAMES but make same-project values-equal ones type-aliases of debayerDefaultConfig via reserved `duplicateOf` (names
  honored, type shared, bind works; only helps values-equal); (3) INHERITANCE (user's dir) — keep all item-3 independent
  structs, contained instance typed with parent config (preprocessBase<debayerDefaultConfig>); fully honors item-3 +
  generalizes to ANY variant; net-new mechanism (biggest). dst tie-break :1615 MOOT under all (not standalone fix).
  KEY: only (3) both honors item-3 AND generalizes; (1) walks item-3 back; (2) names-only, values-equal-only. Awaiting
  user weigh-in on change-size vs building the general mechanism. NO code until settled.
- 2026-07-30: #1 fix LANDED PARTIAL. preprocess.cppm + interpolate.cppm redundant user-region import/using
  REMOVED → import-ordering error gone for both; migrate-project 4a skill note added ("redundant preamble
  import classDecl re-emits → REMOVE not relocate") + redeployed to all 5. rgb_video_sink_config.h moved to GMF.
  NEW #1b (rgb_video_sink.cppm): its `import debayer;`/`using` is LOAD-BEARING (user include rgb_img_writer.h
  names module template rgb_pixel_t<Config>). Proven: can't go GMF (GMF can't see module template), purview
  placement strands generated classDecl imports (NO user purview slot AFTER them). Generator-structure gap.
  FIX options: (a) generator adds post-classDecl-imports purview user slot; (b) product restructures rgb_img_writer
  to full pimpl (wrapper header names no module types). Data edit alone can't fix. Debayer build now stops on
  #1b + #2 (design pending) + #3 (b2p_deb_conv bayer_pattern_t, product code). Awaiting user: #2 (primary), #1b (secondary).
- 2026-07-30: #2 WORKING DESIGN (user): contained block ELIMINATES its own `params:` and instead declares an
  explicit YAML link to the block it inherits from (`inheritsParams: <source>`, name TBD). Parameterization
  by-reference: generator resolves child's params + C++ Config from the SOURCE block (Config = source's, e.g.
  debayerDefaultConfig); child stays templated on Config bound to source's; NO own DefaultConfig emitted. Fixes
  #2 at the source (no per-block config to mismatch), no fold, item-3 untouched (item-3 = independently-param
  blocks; inheriting block isn't one), generalizes to ANY variant. GROUNDING: SV side ALREADY forwards parent→
  child params by name-match (`_resolveSvInstanceParams` `.CHILD(PARENT)`); this makes that explicit + extends to
  C++ Config (which today wrongly stays child's own). OPEN before feasibility pass: (1) link target — named source
  (rigid, pins child to one container, forgoes standalone reuse) vs "inherit from my container" (flexible); user
  phrasing = named source; (2) param subset child⊆source db-time check; (3) variants — child inherits source's
  ACTIVE variant config (debayerV0→child V0); (4) cross-project — lean RESTRICT inheritance to same-project (keep
  item-1 boundary). Next: focused implementation-feasibility pass once shape confirmed. NO code until then.
- 2026-07-30: #2 DESIGN REFINED (user, supersedes eliminate-params) — child KEEPS its `params:` (item-3 + standalone
  reuse preserved); the inherit decision moves to the INSTANCE: `inheritContainerParam: true` (name TBD) stands IN
  PLACE OF the `variant:` selector. When set, the child instance is typed with the CONTAINER's ACTIVE config
  (debayerDefaultConfig, or debayerV1Config if the container is a variant — transitive), not the child's own
  DefaultConfig. Precondition: child params ⊆ container params BY NAME (db-time error else); child's own declared
  values = standalone defaults only, values come from container when inheriting. Result: co-inheriting siblings share
  container config → channel binds, dst tie-break moot. Mirrors SV parent→child name-forwarding (`_resolveSvInstanceParams`),
  made explicit on the C++ Config side. Generator hook: `_resolveInstanceConfigFields` returns the containing block's
  config for an inheritContainerParam instance. OPEN: (1) variant vs inherit mutually exclusive + transitive-variant
  confirm; (2) subset by-name/values-from-container confirm; (3) cross-project containment (lean restrict same-project);
  field spelling = feasibility-pass detail. Next: feasibility pass on confirm. NO code until then.
- 2026-07-30: #2 DESIGN SETTLED (user): keep `params:`, flag by INSTANCE (`inheritContainerParam: true` in place of
  variant), child typed with container's ACTIVE config (transitive), child⊆container params by-name (db-time error),
  SAME-PROJECT ONLY (no cross-project inheritance). THUNKERS double-checked + CONFIRMED container-level:
  sc_declare_thunkers emitted in classDecl.py:200 for the block owning sub-block instances (mem-init refs those
  children), inited in that block's constructor (constructor.py:206-259), tb mirrors for DUT (testbench.py:158) —
  never leaf. Orthogonal to inherit: thunkers key on cross-INTERFACE (protocol) ends, #2 is same-interface CONFIG
  mismatch — so inherit unifies config (sibling channels bind directly) and thunkers stay for genuine protocol
  adaptation; no thunker proliferation for the config case. Implementation-plan pass (a5209f85d5c36d0a7) running:
  schema instance field, _resolveInstanceConfigFields→container config, subset+same-project validation, SV-forwarding
  composition, channel-payload resolution, test fixture. Bring concrete plan for user GO before any generator code.
- 2026-07-30: #2 IMPLEMENTATION PLAN ready (small, ~4 files). KEY INSIGHT: contained child renders INSIDE container's
  templated class scope, so inheritContainerParam just spells the container symbol `Config` instead of child config;
  C++ template instantiation resolves the concrete struct (incl. transitive debayerV1Config) at the container's own
  site — no value plumbing. STEPS: (1) schema.yaml:222 add `inheritContainerParam: optional(false)` to instances;
  (2) processYaml.py:1466-1513 _resolveInstanceConfigFields inherit branch + new contracted `inheritContainer` field
  on both returns; (3) intf_gen_utils.py:435-445 cpp_config_struct_name: inheritContainer→'Config'; (4) postParseChecks.py
  5 db-time checks (mutual-excl w/ variant, container-parameterized, child-has-params, child⊆container by-name, same-project).
  NO CHANGE needed (verified): _resolveSvInstanceParams (already name-forwards; variant='' → forwarding branch; subset
  guards KeyError), _resolveConnectionConfigOverride (both ends spell Config, dst moot), thunkers. LOAD-BEARING: subset
  check must run in projectCreate before gen (SV path correctness depends on it). INVARIANT to re-confirm: no caller
  spells an inheriting instance's Config OUTSIDE container scope (plan found none). ACCEPTANCE: convert debayer
  u_preprocess/u_interpolate to inheritContainerParam:true + 1 positive + 4 negative unit tests. AWAITING USER GO to implement.
- 2026-07-30: item-2 (`inheritContainerParam`) landed, reviewed, and debayer acceptance PASSED (channel binds); see the
  §8 Disposition for the full record. Two HDL-wrapper follow-ons landed (`param_names` from declared params; new
  `declaredVariants` projectOpen view field for the `.sv` trampoline). Follow-up generator-hygiene sweep (arose while
  fixing `param_names`): removed the template-scope `prj.data['blocks'][qual]['params'|'_context']` derivable-fact walks
  across `module_hdl_wrapper.py`, `moduleInterfacesInstances.py`, `moduleRegs.py`, `classDecl.py`, `baseClassDecl.py`,
  `apbDecodeModule.py` (15 sites) in favour of the block-data view field `data['blockInfo']` — the builder-base skill
  bars templates from walking `prj.data` for a derivable fact. All sites verified own-block; byte-identical across the
  whole base+pro example suite; independently reviewed. Residual pre-existing dead `blk_name` in
  `module_hdl_wrapper.py::dut_instantiation` left as tracked debt (out of the sweep's scope). Same-category keyed
  lookups into GLOBAL tables (`constants`/`structures`/`types`/`interfaces`/`instances`) are a legitimate pattern and
  were NOT swept.
- 2026-07-30: #1b (rgb_video_sink purview include with no legal home) resolved via the durable "move-up": the SC module
  preamble was restructured so `moduleScaffold.py::moduleExport` emits the FULL preamble (all imports + all usings,
  preamble closed) and `classDecl.py` module mode emits only the class. The `// user imports here` slot is now a
  module-purview zone (legal home for a purview `#include` feeding a class member); it unifies normal blocks with
  reg-handler blocks (which already closed the preamble there). Chosen over a new-region+migrate-phase approach because
  it needs NO new region and NO `make migrate` phase — it folds into the unshipped `.cpp/.h`→`.cppm` conversion and
  `make gen` alone re-emits it. Independently reviewed CLEAN: pure relocation (import/using multisets byte-identical
  HEAD↔regen across all 62 changed `.cppm`), reg-handler `.cppm` byte-identical, no `prj.data` walk, compile-green on
  apbDecode/simple_ip/ip_test, #1b cleared (all 5 debayer block `.pcm` build), the purview `#include` now legal. Product
  cleanup: dropped the redundant `import debayer;`/`using namespace debayer_ns;` from the `rgb_video_sink.cppm` /
  `raw_video_src.cppm` user slots (now emitted by `moduleExport`). Trade-off (architect-approved): the user slot no
  longer hosts a hand `import` (empirically unused: 0/78 base examples); body-only imports resolve via structural YAML
  reference. NOTE: the debayer composed build now advances PAST #1b and #3 (the latter proved a non-fatal warning) and
  stops at pre-existing **item-1 project-qualification debt in non-block generated file types** — `<block>Tandem.h`
  (classic `.h`), `debayerConfig.cpp` (config), `debayerExternal.cpp` (tbExternal), and `blockF.h` — which emit
  UNQUALIFIED `<block>.base`/`<block>.block` module imports vs the qualified module names. Confirmed pre-existing
  (git-show byte-identical), exposed only now that the build gets further; a generator coverage gap in item-1, routed
  to the qualification track as the next debayer blocker.
- 2026-07-30: item-1 tandem-header coverage gap FIXED (landed + reviewed clean). Root cause (read-only diagnosis) was a
  SINGLE site — `pro/templates/systemc/classDeclTandem.py:41` passed the raw `data["blockName"]` to
  `cpp_base_module_name` instead of the project-qualified `data["blockModuleName"]` (every other emitter already uses
  the qualified field; mirrors `intf_gen_utils.py:533`). One-line fix: debayer `interpolateTandem.h`/`preprocessTandem.h`
  now import `debayer_interpolate.base`/`debayer_preprocess.base` (resolving against the actual `export module`);
  `debayerTandem.h`/`debayer_regsTandem.h` and pro `lmmiDemoTandem.h` stay byte-identical (dedup). The diagnosis also
  reclassified the other three "coverage gap" suspects as NOT item-1 template gaps: `debayerConfig.cpp`'s stale
  `import <child>.block` lines are hand-authored USER code (product-side qualify), `debayerExternal.cpp`'s imports are
  already correctly qualified (its remaining failure is a separate tbExternal Config-SELECTION issue, under diagnosis),
  and `mixed/model/blockF.h` is a stale promotion ORPHAN (not in the manifest, not compiled) for an orphan sweep.
- 2026-07-30: **debayer composed build GREEN + independently reviewed — primary #116 integration deliverable complete.**
  The tbExternal Config-SELECTION issue (prior entry) was the parameterizable TB peers (`raw_video_src`/`rgb_video_sink`)
  binding Config-strict to the excluded DUT: peer ports typed `video_bayer_t<raw_video_srcDefaultConfig>` vs the DUT
  channel's `video_bayer_t<debayerDefaultConfig>` (distinct C++ types even at equal param values). A read-only
  investigation proved NO product-YAML-only, DUT-preserving fix exists via variant/inheritContainerParam/de-param (every
  route resolves a port to the block's OWN Config). RESOLUTION = the BUG7 `rdy_vld` shape-4 boundary thunker (first
  PRODUCT consumer): peers declare a `ports:` entry with a NON-param boundary interface (`video_*_bndry_stream`); the
  CONNECTION carries the DUT's PARAMETERIZED interface with `srcport`/`dstport` naming the boundary port; the peer↔
  connection differing NAME fires the thunker on the surviving peer end (the DUT end is pruned, so its connectionMap-
  derived boundary port is irrelevant). Product-only (debayer_tb.yaml + two peer model user-bodies + debayerConfig.cpp
  import/cast qualification); DUT block UNTOUCHED (0 `_bndry_t` in any DUT source, debayerBase.cppm unchanged). A first
  attempt INVERTED this (boundary interface on the `connection:`), which propagated into `debayerBase` and re-typed the
  DUT — corrected by moving the boundary interface onto the peer `ports:` and keeping the connection interface
  parameterized. Independent review PASS: gen idempotent (no hand-edited generated regions); pixel correctness proven
  three ways — the thunker bit-casts (`copy_packed_bits`) and `validatePorts` (processYaml.py:~5816) machine-enforces
  boundary↔param field-name/order/width/offset parity at db/gen time (a mismatch FAILS `make gen`, cannot silently
  corrupt), plus a 35-bit/99-bit static layout proof and a reference-image run (PSNR 24.46dB chart / 36.04dB photo);
  from-clean `make run` green both directions. Also closed: the #1b "move-up" blast radius across the WHOLE base+pro+
  product corpus is EXACTLY ONE file — `examples/nested/model/testBlock.cppm:22`, a vestigial hand `import
  nested_subBlockContainer.block;` in the now-illegal post-`using` user slot (subBlockContainer belongs to
  `testContainer`, absent from testBlock's surface — NOT a generator-completeness gap); fixed by deleting the dead line,
  `make nested` green. The move-up needs no migration phase and no generator-completeness change.
- 2026-07-30: **Full base+pro example-suite validation + triage of the 4 remaining base failures** (pro suite GREEN;
  `nested` fixed above). Classification (read-only, evidence-backed): (1) **`lint-hier` — the ONLY this-session-
  introduced failure.** The uncommitted item-1 qualification changed the GENERATED begin label `module blockBX`→`module
  hierInclude_blockBX`, but `endmodule: blockBX` lives in a USER region the generator never rewrites → ENDLABEL mismatch
  (10 sites: b/blockB{X,Y,Z}, blockA/B/C, c/blockC{X,Y,Z}, top). Verdict = **MIGRATION-TOOLING** = the tracked item-1
  "endlabel migration": migrate-phase rewrite `endmodule: <block>` → `endmodule: <project>_<block>` sourcing the
  qualified name from the SAME identity function the generator uses (`qualifyModuleIdentity`, NOT string-munge);
  idempotent; corpus-wide blast radius TBD (only the lint example checks endlabels). NOT a certain one-liner (recurring
  user-region rewrite → belongs in the migrate tool). (2) **`mixed`** = DEFERRED orphan-sweep: `model/blockF.h` is a
  superseded header-mode file the `.h`→`.cppm` promotion replaced-but-did-not-delete (its `.cppm` counterpart emits the
  qualified `import mixed_blockF.base;`); remedy = delete the orphan, not hand-edit its generated import. (3) **`ip-test`
  / `simple-ip`** = PRE-EXISTING (clean at HEAD, not this session), VL-only (model `run` passes): a `rtlDotF`
  sub-context-package propagation gap — top `rtl.f` lists `ip_package.sv` but OMITS the ip block's `ipTop_package.sv`
  (which the local `ip/rtl/rtl.f` does include), so top-scope `ipStdDriver`/`ipStdTop` import an uncompiled package.
  Package names are already qualified + self-consistent (nothing to hand-edit); known hierarchical-VL gap track — could
  be promoted to GENERATOR-FIX (`rtlDotF` should carry sub-context packages) if the architect so decides.
- 2026-07-30: **`lint-hier` reframed — it is the DEFERRED whole-suite orphan-sweep migration, not an endlabel one-off.**
  The SV endlabel migrate transform is ALREADY committed (`pysrc/migrateModuleEndlabel.py`, wired at `migrateYaml.py:
  523-524`), idempotent + owner-gated, sourcing the qualified name from `BLOCKMODULENAME`/`qualifyModuleIdentity` — the
  same field the begin-label uses; the migrate-vs-generate design is settled correctly (generate the endlabel for fully-
  generated blocks; restamp the user-region endlabel for `moduleInterfacesInstances` user-body blocks). A dry-run of the
  committed migrate on `hierInclude` (safety-valve, zero mutation) proved the fix is NOT scope-clean: `hierInclude` is a
  LEGACY-layout example (only `arch/` + `systemVerilog/`, NO `rundir`/`make migrate`/`make gen` pipeline) that is
  partially-unmigrated — the `--sweep` would (a) ORPHAN_DELETE 7 legacy `_package.sv` files (which are themselves
  uncommitted-`M`, so deletion discards uncommitted content), (b) re-stamp their context `GENERATED_CODE_PARAM`, AND (c)
  do the 10 intended endlabel restamps. A correct fix needs the delete→regen→restamp cycle, but the legacy SV path is
  per-file `arch2code.py -sv` (forbidden direct invocation) with no wired make pipeline. Item-1 qualification only made
  the endlabel symptom VISIBLE; the underlying need (fully migrate the legacy example) is the already-deferred whole-
  suite orphan-sweep migration. HELD for architect: decide how to drive hierInclude's full migration (it lacks a rundir
  pipeline) and authorize the orphan deletion of uncommitted-modified files. Net example-suite status: pro GREEN; base
  green except the 4 triaged failures, ALL now mapped to already-deferred tracks (lint-hier + mixed = orphan-sweep;
  ip-test/simple-ip = hierarchical-VL filelist gap). No example failure remains that is both this-session-caused AND
  safely closable without an architect decision (nested — the one such case — was fixed).
- 2026-08-04: **All items CLOSED; item statuses reconciled to committed branch state at `2b3f6d1`.** Item 1's three
  residuals are resolved: `hierInclude` carries qualified begin labels, `endmodule:` labels, user `--importPackage`
  directives and lint top module (`38b17af`); the debayer product relabel is executed (`rtl/preprocess.sv` →
  `debayer_preprocess`, `rtl/interpolate.sv` → `debayer_interpolate`, `debayer.sv`/`debayer_regs.sv` unchanged by
  dedup); and the two regressed unit tests were corrected earlier. Item 5 moved GO → LANDED: the `blockModule` gate is
  relaxed to all `hasMdl` blocks, every base and pro block implementation is a single `.cppm`, and the paired `.cpp`/`.h`
  files are gone. Item 6 moved OPEN → LANDED: the migration skill now separates automated from manual per phase and
  documents the variant-schema phase, the end-label re-stamp, the already-migrated-child rule, and the redundant-preamble
  -import rule. The release-triage table gained a Status column and an item-8 row. Three further changes in the same
  window are recorded in the status report rather than here because they are not review items: the `a2c.endOfTest` module
  and expression-evaluator operator expansion (`7274b9c`), the reachability-scoped SystemVerilog compile set that closed
  the hierarchical co-simulation file-list gap (`38b17af`), and the parameterized register reset-value fix (`de022a1`),
  which is the fix for BUG 8 in the external ISP parameterization bug report. Four release-blocking defects found while
  running the base acceptance suite for this refresh are tracked in the status report, not here: the end-of-test
  startup-gate regression (B1), the unregistered failing identity-uniqueness suite (B2), stale composed-child artifacts
  in the committed tree (B3), and the stale build directory on upgrade (B4). B1 and B3 are consequences of item 5's
  module work; B2 is a consequence of item 1's qualification; none is a defect in the delivered item behaviour.
