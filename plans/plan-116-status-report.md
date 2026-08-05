# Report: 116 Plan Hierarchy and Status

Status as of: 2026-08-04
Branch context: `feature/116-parameterized-types` in `builder/base`
(HEAD `2b3f6d1`), with the matching `builder` pro overlay (HEAD `6b29e75`) and
the `debayer` product (HEAD `e9fc5ec`) as the integration vehicle.

This is the status index for the `plan-*.md` files under `builder/base`.
It states current status definitively; detailed execution records live in
the owning plans named below. A dated change log is kept at the end.

The `plans/` directory is now tracked in the `builder/base` repository
(committed 2026-08-01 in `b17a0fc`, 64 documents). Earlier revisions of this
report carried a caveat that no plan document was under version control; that
caveat is retired.

## Executive Overview

This branch expands Arch2Code to support reusable, independently buildable IP
projects that can be configured and composed into larger systems. The change set
connects parameterization, project ownership, build discovery, registration,
address generation, migration, and verification into one consistent workflow.

Key capabilities delivered:

- **Parameterized IP generation.** A block can define configurable widths,
  depths, types, structures, registers, and memories once in YAML. Arch2Code
  propagates those parameters consistently into SystemC models, SystemVerilog,
  register decode, firmware constants, testbench selection, and exact-width
  Verilated wrappers. Variants are declared once with their parameters nested
  beneath them, every variant must bind every parameter, and every declared
  variant receives its own named configuration structure.
- **Reusable standalone IP projects.** Reusable leaves and assembling IPs can
  live in their own project trees, build and test independently, and be
  referenced by parent projects. Verification covers standalone leaves,
  standalone assemblers, and composed roots.
- **Parent-selected variants without modifying the child.** A consuming project
  can select a child variant and own the resulting configuration artifact
  without placing consumer-specific configuration in the reusable child tree.
- **Deterministic cross-project ownership.** Project-qualified factory keys,
  authoritative file ownership, provider overrides, and active-root
  reachability prevent two projects from silently claiming the same generated
  artifact or runtime registration. Focused positive and negative tests cover
  provider selection and duplicate-provider diagnostics.
- **Composition-aware build and layout infrastructure.** Projects may use
  functional or hierarchical layouts. A generated build manifest supplies
  owner-correct SystemC, RTL, registrar, firmware, and wrapper paths across
  project boundaries instead of relying on one fixed project root.
- **Deterministic build automation.** Builds consume database-emitted C++ and
  SystemVerilog file lists instead of scanning source trees, generate one
  project-scoped `rtl.f`, and assign explicit Verilator file-to-top records with
  isolated build directories. `make newmodule` creates missing project artifacts
  and reference Makefiles without overwriting user-owned files; standalone and
  composed `compdb`/clangd flows use the same manifest as normal builds.
- **One-command migration and regeneration.** `make migrate` sequences YAML
  conversion, database creation, the frozen-map orphan sweep, create-once
  scaffolding, and regeneration. The conversion covers Python-to-SystemVerilog
  expression rewriting, project-wide address control to per-block declarations,
  include headers to C++ modules, the per-row-to-nested variant schema, and the
  database-backed re-stamps of `GENERATED_CODE_PARAM` lines and user-owned
  SystemVerilog `endmodule:` labels. Generated legacy artifacts are removed
  deterministically, user-owned files are preserved or reported for an
  agent-driven port, and both functional and hierarchical layouts use the same
  ownership policy.
- **Cleaner registration and module boundaries.** Every block implementation is
  a single C++20 module interface unit (`.cppm`), independent of whether the
  block is parameterized. Block classes, Base interfaces, framework services,
  and registrar trampolines use explicit C++20 module and per-assembler
  ownership. Registration is retained through a defined build-system contract,
  and reusable implementation trees do not carry consumer-specific registration
  anchors.
- **Collision-free generated identity across projects.** Generated C++ module
  and namespace names, SystemVerilog package names, and SystemVerilog module
  names are qualified by their owning project, with a prefix-dedup rule that
  leaves an identifier already leading with the project name unchanged. File
  names on disk keep the plain authored spelling. Two fail-fast database-time
  uniqueness gates reject any pair of contexts or blocks that would resolve to
  one identifier.
- **Migration and compatibility support.** The branch completes the unified
  YAML migration path, replaces project-wide address-control input with
  block-owned address declarations, adds hierarchical-layout migration support,
  and ports the in-tree examples to the current contracts.
- **Expanded verification.** Standalone and composed model and co-simulation
  flows reach clean end-of-test. Automated coverage includes parameterized
  declarations and expressions, register decode, address containment, ownership,
  layout, zero-instance blocks, provider overrides, build manifests,
  parent-owned configuration emission, variant completeness, container
  configuration inheritance, and generated-identity uniqueness.

## New In This Release Cycle

The following items landed between 2026-07-29 and 2026-08-04. They are the
outcome of the `feature/116-parameterized-types` review plus the `debayer`
product migration that exercised the result. All six review action items and
the one item the product migration added are now closed. Execution detail is
recorded in [`plan-116-review-feedback.md`](./plan-116-review-feedback.md).

- **Project-qualified generated identity (review item 1).** Generated C++
  module and namespace names, SystemVerilog package names, and SystemVerilog
  module names are now qualified by their owning project through one identity
  function, so two projects containing a same-named context or block no longer
  collide. File names keep the plain authored spelling. `make migrate`
  re-stamps the user-owned `endmodule:` labels that pair with the generated
  module declaration.
- **Variant declaration schema (review item 2).** A variant is declared once
  with its parameters nested beneath it, replacing the per-row form that
  repeated the variant label on every parameter. The nesting is expressed
  declaratively in the schema rather than reshaped in code. Every variant must
  bind every declared parameter of its block; an omission is a database-time
  error rather than a silent default. The retired per-row form is rejected with
  a durable message directing the user to `make migrate`, and the migration
  phase performs the rewrite mechanically.
- **One configuration structure per variant (review item 3).** Both previous
  deduplications are removed: a variant whose values equal the default, or
  equal a sibling variant, still receives its own variant-named configuration
  structure. A parameterized block therefore emits one default structure plus
  exactly one structure per declared variant, so the generated code shows which
  variants exist.
- **Nested address-decode containment validation (review item 4).** Database
  creation now proves that each nested decode footprint fits inside the window
  its parent router allocates. A nested decoder is judged by its routed
  footprint, and a routed register block by the space it actually decodes. A
  violation is a durable error naming the offending block and both spans.
- **Uniform C++20 block modules (review item 5).** Every block implementation
  is now a single module interface unit, independent of parameterization,
  replacing the paired implementation and header files. The migration performs
  the four-slot user-code transplant mechanically for the ordinary cases and
  reports the edge cases it deliberately declines to attempt.
- **Migration guide clarification (review item 6).** The `migrate-project`
  skill now separates automated phases from manual follow-up explicitly, and
  documents the variant-schema phase, the `endmodule:` label re-stamp, the
  redundant-preamble-import case, and the requirement to re-run migration in
  each composed child so its exported identifiers match what the parent now
  imports.
- **Container configuration inheritance (`inheritContainerParam`).** A
  contained-block instance may declare `inheritContainerParam: true` in place
  of a variant selector and is then typed with the container's active
  configuration, transitively. This makes a configuration-parameterized channel
  between two sibling children bind, which strict one-to-one per-block
  configuration otherwise prevents. Five preconditions are enforced at database
  time, including a same-owning-project restriction that preserves qualified
  identity.
- **Parameterized register reset values (defect fix).** A parameterized
  read/write register generated a reset of zero instead of its declared
  per-word default. The generated decoder now carries the declared reset values
  in a local parameter array and applies them on both the full-word and
  partial-word paths.
- **Framework services as modules.** `endOfTest` is now the `a2c.endOfTest`
  module rather than a header, which guarantees one shared singleton across
  module boundaries. Framework module interface units under the common
  SystemC directory are discovered automatically by the build. The firmware
  board-support package moved to its own directory and is no longer compiled
  into every SystemC target by default.
- **Expression evaluator coverage.** The shared constant-expression grammar
  gained relational, equality, and ternary-conditional operators, each with one
  identical SystemVerilog, C++, and C spelling so the emitters pass it through
  unchanged. The Python-to-SystemVerilog converter also re-spells C-style
  integer literals into the SystemVerilog based form.
- **Reachability-scoped SystemVerilog compile set.** The managed
  SystemVerilog file list is now restricted to the blocks reachable from the
  build's top instance, so a referenced child project's own standalone
  verification harness is no longer compiled into a parent build where its
  package is legitimately absent. This closes the last known hierarchical
  co-simulation file-list gap.
- **Cross-interface boundary thunker in production.** The boundary thunker now
  has its first product consumer: a parameterized device under test can be
  driven by non-parameterized testbench peers without re-typing the device
  under test, with field name, order, width, and offset parity machine-enforced
  at generation time.
- **Generator-architecture hygiene.** Wrapper-selection logic that had been
  placed in a `projectOpen` view was moved into the template utility layer,
  restoring the documented ownership split between database truth,
  language-neutral views, and language-specific rendering.

## Upgrade Path For Existing Projects

This release changes authored YAML, generated identifiers, and generated file
shapes. Existing projects must migrate; the changes were deliberately landed
together so that a project migrates once rather than repeatedly.

- Run `make migrate` in each project. In a composed design, run it in every
  child project bottom-up, including children that are already stamped
  `yamlFormat: 2`, because the parent now imports project-qualified identifiers
  that a stale child still exports under its bare name.
- Automated phases cover the variant-schema rewrite, address-control
  conversion, include-to-module conversion, Python-to-SystemVerilog expression
  conversion, the `GENERATED_CODE_PARAM` re-stamps, the user-owned
  `endmodule:` label re-stamp, the orphan sweep, create-once scaffolding, and
  regeneration.
- Manual follow-up is limited to the cases the tool reports: block
  implementations it declines to transplant automatically (parameterized
  blocks, module-hostile third-party libraries, non-boilerplate content in the
  preamble slot), and any hand-authored code that spells a generated identifier
  which is now project-qualified.
- Consumers that referenced a default-named configuration structure for a
  declared variant now reference that variant's own structure. Generated
  regions are re-rendered automatically; only hand-written references need
  attention.

For program planning, the 116 critical path is complete. The branch
demonstrates the full standalone and composed SystemC/model path, explicit
managed SystemVerilog source selection, owner-qualified per-variant Verilated
tops, standalone and composed RTL co-simulation, cross-project clangd, and the
final registrar/config placement. Builds and migrations are reproducible from
YAML and database ownership data without source-tree discovery, including clean
standalone and composed regeneration. The review action items above are
delivery hardening and authoring-surface corrections, not a reopening of
composition acceptance. The branch is **feature-complete for the planned
reusable-IP composition and verification workflow**, and the `debayer` product
now builds and runs through that workflow as a composed, parameterized,
hierarchical-layout project.

## Functional Skill Improvements

The branch updates user-facing skills so agents apply the delivered architecture
correctly instead of following obsolete manual patterns.

- **Register/memory decode design skill.** New `design-register-decode.md`
  replaces the old “manually write the decoder” model with the generated
  `addressBlock:` router and routed-leaf model. It documents the decoder-position
  decision rule, `registerPorts:` versus inferred top-down leaves, nested
  routers, the one upstream feed authored by hand, invariants, worked examples,
  and diagnostic recovery.
- **Architecture and address placement rules.** `design-architecture.md`,
  `architecture-yaml.md`, and `manage-address-space.md` now explain where
  routers and routed leaves belong, when a container may own registers, how
  nested decode works, and how generated files follow YAML-directory layout.
- **More precise parameterization rules.**
  `design-architecture.md`, `design-parameterizable-blocks.md`,
  and `architecture-yaml.md` now distinguish root variant parameters from
  derived parameterizable definitions and explain inherited worst-case bounds,
  variant bindings, and layout-aware generated identities.
- **Corrected RTL and verification guidance.** `rtl-registers.md`
  now limits user RTL to external-register storage and side effects because both
  router and block-level register handlers are generated.
  `verify-testbench.md` uses an in-tree current-format fixture for
  `--excludeInst`, and the agent routing templates direct architecture,
  register-decode, RTL-register, and testbench tasks to their authoritative
  skills.
- **Migration guidance separated into automated and manual steps** (review item
  6). `migrate-project.md` now documents the variant-schema rewrite phase, the
  user-owned `endmodule:` label re-stamp and why it is database-backed, the
  requirement to re-run migration in every composed child once cross-project
  identifiers are qualified, and how to resolve a redundant import left in the
  module preamble slot. `address-migration.md` and `manage-build.md` were
  reconciled to match.
- **Parameterizable authoring guidance refreshed.**
  `design-parameterizable-blocks.md` documents the nested variant declaration
  form, the all-parameters-per-variant completeness rule, and
  `inheritContainerParam` for a contained instance that must share its
  container's configuration.
- **SystemC module authoring guidance.** `systemc-core.md`, together with
  `rtl-to-systemc.md`, `systemc-to-rtl.md`, `systemc-interfaces.md`,
  `systemc-synchronization.md`, and `review-model.md`, now describes the single
  block module interface unit, its three zones, and which user slot legally
  hosts an `#include` versus an `import`.

## Current Status Summary

| Workstream | Status | Owning plan |
|---|---|---|
| Foundation / prototypes (P0, F1-F3, A1-A3) | Complete | `plan-development-ordering.md`, `plan-f2-f3-design.md` |
| Variant/config unification (Stages 1-11) | Complete | `plan-variant-config-unification.md` |
| Exact-width Verilated wrappers | Complete | `plan-canonical-verilated-wrappers.md` |
| Generated testbench variant selection | Complete | `plan-step-11-variant-aware-testbenches.md` |
| C1 / C2 parameterized declarations + SV emission | Complete | `plan-param-constant-collision.md` |
| C3 parameterized register decode | Complete | `plan-param-constant-collision.md`, `plan-parameterized-register-decode.md` |
| C4 symbolic eval | E4 complete; E5 complete (SystemC + firmware C); E6 **closed (descoped)** | `plan-eval-symbolic-emission.md` |
| Config header/template cleanup | Complete | `plan-config-policy-views.md` |
| Address-control refactor (Stages 1-8) | Complete | `plan-address-control-refactor.md`, `plan-address-control-test-coverage.md` |
| Unified YAML migration (`yamlFormat: 2`) | Complete | `plan-yaml-migration.md` |
| C++ module/template identity cleanup | Complete (WI6 closed — descoped 2026-06-23) | `plan-cppm-include-contract-cleanup.md` |
| Registration encapsulation cleanup | Complete (committed; Option δ, `force_link` retired) | `plan-registration-encapsulation-cleanup.md` |
| Parameterizable struct/eval test coverage | Complete (committed) | `plan-eval-symbolic-emission.md` |
| IP project composition foundation (C0-C5) | **Delivered / accepted; standalone and composed model+VL paths green; C1 contract-doc refresh remains** | `plan-ip-project-composition.md`, `plan-composition-ordering.md` |
| Cross-project ownership, provider selection, and reachability | **Complete for the selected-provider contract; Option-D collision hardening deferred** | `plan-cross-project-block-resolution.md`, `plan-cross-project-shared-definitions.md` |
| Project layout (`functional` / `hierarchical`) | **Complete: L1-L5 accepted** | `plan-decomp-functional-layout.md` |
| Reusable-IP registrar relocation | **Complete: S0-S6 landed; S5 is committed in the post-`c42b535` branch history** | `plan-reusable-ip-registrar.md`, `proposal-config-ownership-header-relocation.md` |
| Owner-qualified language identity (Q-C8 / review item 1) | **Complete.** Project qualification landed for the C++ module/namespace, the SystemVerilog package, and the SystemVerilog module name, with prefix-dedup, two uniqueness gates, and the `endmodule:` label migration. Examples and the `debayer` product are relabelled | `proposal-qc8-identity-field.md`, `plan-param-constant-collision.md`, `plan-116-review-feedback.md` |
| Nested variant declaration schema (review item 2) | **Complete.** Schema-native nesting (`parameters → variants → params`), leaf table `parametersvariantsparams`, completeness validator, old-form rejection, and `migrateVariantSchema.py` | `plan-ip-namespaces-and-parameterization.md`, `plan-116-review-feedback.md` |
| One configuration structure per variant (review item 3) | **Complete.** Default fold and sibling value-signature fold both removed; default plus one structure per declared variant | `plan-parameterizable-config-template.md`, `plan-116-review-feedback.md` |
| Nested address-decode containment validation (review item 4) | **Complete.** Database-time containment pass in `calcAddresses` plus negative fixture `test_error_nested_decoder_overflow.py` | `plan-address-control-refactor.md`, `plan-address-control-test-coverage.md` |
| Uniform C++20 block-implementation modules (review item 5) | **Complete.** Gate flipped to all `hasMdl` blocks; every in-tree base and pro block implementation converted; mechanized four-slot port with detect-and-flag edges | `plan-block-module-3section.md`, `plan-item5-port-mechanization-assessment.md` |
| Container configuration inheritance (`inheritContainerParam`) | **Complete for the same-project case.** Schema field, config-selection branch, five database-time preconditions, six unit tests, and the declared-variant HDL-wrapper follow-ons. Cross-project negative fixture deferred | `plan-parameterizable-config-template.md`, `plan-116-review-feedback.md` |
| Framework services as C++20 modules | **Complete.** `a2c.endOfTest` module replaces the header, framework `.cppm` auto-discovery in the build, firmware board-support package relocated | `plan-block-module-3section.md` |
| Expression-evaluator operator coverage | **Complete.** Relational, equality, and ternary operators plus C-style literal re-spelling in the Python-to-SystemVerilog converter | `plan-eval-symbolic-emission.md`, `plan-eval-python-to-sv-migration.md` |
| Hierarchical co-simulation file lists | **Complete.** Managed SystemVerilog compile set scoped to blocks reachable from the build top, matching the reachability-scoped `rtl.f` | `plan-decomp-functional-layout.md`, `plan-composition-ordering.md` |
| Tandem emission contract under parameterized types | **Specified** (`spec-tandem-parameterized-types.md`, normative); pro-side emitters aligned to the qualified block module name | `spec-tandem-parameterized-types.md` |
| Cross-level foreign-variant wrappers | **Complete against the architect-selected proof bar; hardening gaps deferred** | `plan-cross-level-variant-wrappers.md` |
| File ownership + one-command project migration | **Mechanical pipeline landed; parameterized `.cpp/.h`→`.cppm` user-code port remains agent-driven** | `plan-file-ownership-classification.md`, `rules/skills/migrate-project.md` |
| Canonical examples and layout cleanup | **Complete: `simple_ip`, `hierVlDemo`, and collapsed `ip_test` hierarchy landed** | `plan-simple-ip-example.md`, `plan-ip_test-dir-cleanup.md` |
| Three-section C++ block modules | **Complete in committed generator/example infrastructure; GMF and module-import user zones plus migration support landed** | `plan-block-module-3section.md` |
| Multi-copy project override / logical file ownership | **Committed in `e59ad94` with `test_project_scan.py` / `test_project_param.py`; `resolveContextKey` now requires an exact canonical key, retiring the basename fallback. Owner-plan sign-off pending** | `plan-projectoverride-file-ownership.md` |
| `pySocket` current-format migration | **Committed in `e59ad94` (26 files): YAML/address/include conversion, `.cppm` base and include modules, registrar output, and user-code port. Standalone model/VL acceptance not rerun here** | `plan-file-ownership-classification.md`, `plan-projectoverride-file-ownership.md` |
| Functional skills and agent guidance | **Updated: register decode, architecture/address placement, parameterization, migration, SystemC module authoring, RTL registers, and testbench guidance** | `rules/skills/`, `AGENTS.md.template`, `ARCH2CODE_AI_RULES.md` |
| `debayer` product integration | **Complete.** The product is migrated to hierarchical layout, composes the `isp_shared` definitions-only project, uses nested variant declarations and `inheritContainerParam`, carries qualified module names, and builds and runs green with an image-quality reference check | `plan-116-review-feedback.md` |

Branch-state caveat: the workstream code is committed in branch history
(the original range began at `ca0afec`; current HEAD is `2b3f6d1`), and
`plans/` is now tracked as well. "Complete" above refers to implementation
state. The `builder/base` working tree was clean at HEAD `2b3f6d1` before this
refresh. The formal open/closed classification of each row remains with the
owning plans named in the same row.

## Branch Metrics

Metrics below cover the report's implementation range: the parent of
`ca0afec` (`1229582`) through current HEAD `2b3f6d1`, 2026-06-11 through
2026-08-04. Commit counts use first-parent history so unrelated commits brought
in by merges are not presented as direct branch work; line and file counts are
the net tree diff across the endpoints, not cumulative per-commit churn.
Renamed paths are attributed to their source directory.

| Metric | Value |
|---|---:|
| First-parent commits | 101 |
| Merge commits on first-parent history | 4 |
| Non-merge first-parent commits | 97 |
| Non-merge first-parent commits carrying `#116` | 93 |
| All reachable commits, including merged side histories | 125 |
| Author identities across reachable commits | 3 |
| Paths changed | 1,311 |
| Files added / modified / deleted / renamed | 630 / 242 / 273 / 166 |
| Insertions | 101,292 |
| Deletions | 26,552 |
| Net lines | +74,740 |
| Unit-test suites in `unittest/` | 88 |
| Base examples | 16 |

Two figures need context. Insertions grew by roughly 43,000 lines relative to
the previous refresh mostly because `plans/` became tracked: the 64 plan and
research documents account for 37,689 of those lines and contain no product
code. Four non-merge first-parent commits do not carry `#116` in the subject:
`894f101` is typed `#166` (a typo, and it is branch work), and the three
commits `38b17af`, `7274b9c`, and `59b7329` carry descriptive subjects instead
of the issue tag.

The first 11 first-parent commits (`ca0afec` through `5ff43e1`) close the
pre-composition work summarized in the 2026-06-23 entries. The following 77
first-parent commits carry the branch through project composition, layout,
ownership, provider selection, registrar relocation, migration, and example
cleanup. The final 13 commits (`14ce4c4` through `2b3f6d1`) deliver the review
action items and the product integration. Major composition
milestones include:

- `5810dd5` — introduce `projectName` into the instance-factory path.
- `a6907fb` through `929caa4` — project data/layout, ownership foundations, and
  the split `ip_test` fixture.
- `894f101` / `88d7520` — authoritative nested-project/provider ownership and
  active-root reachability.
- `6791451`, `91b69dc`, `ab75e9c`, `4038204` — BSP/common ownership,
  definitions-only blocks, zero-instance ports, and cross-project plain-block
  registration that make the composed model run green.
- `6bbec76` / `6113562` — bridge fixture/owner-aware RTL paths and VL manifest
  directory consumption.
- `0b3a699` / `37bad48` — runnable standalone `ipBridge` model harness and
  provider-override positive/negative coverage.
- `52be673` — project-qualified variant identity and S3-H parent-owned foreign
  Config headers.
- `c377962` / `cbea09a` — manifest/example coverage and closure of the `mixed`
  registrar-orphan deferral.
- `d7f65b6` / `7cb32f3` / `c42b535` — config-module ownership, foreign
  Verilated wrappers, explicit file-to-top records, and `vl_wrap` retirement.
- `731b196` through `a50f12c` — standalone compdb and project-mode `rtl.f`
  closure, completing registrar S5 and the standalone model/VL matrix.
- `59f4fd7` through `4acd77e`, then `a09c0db` / `281beba` / `03e43fd` /
  `a0ec705` —
  the one-command migration pipeline, frozen-map orphan sweep, create-once
  build scaffolds, and migration hardening.
- `43b5b2e` through `dd75dd8` — hierarchical-layout fixes and the canonical
  `ip_test` directory collapse.
- `d7d73cb` / `4e4dc54` — `simple_ip`/`hierVlDemo`, explicit generated-file
  discovery, and removal of C++ source scanning from the build.
- `6ca55e1` — nested register-handler coverage and a functional `mixed`
  model/RTL test harness.
- `1b22c95` / `33d0095` / `e2002d8` — channel include cleanup, module-purview
  `using` placement, and the three-section GMF/module-export/class scaffold with
  migration support.
- `e503ccb` / `0fec076` / `f07ae17` — database-emitted C++ module mapping,
  layout-aware directory correction, and strictly project-scoped manifest
  consumption.
- `e59ad94` — project-scan ownership landing: the multi-copy fixture tree,
  `test_project_scan.py` / `test_project_param.py`, and the `pySocket`
  current-format conversion all move from working tree to branch history.
- `1494898` / `b5aca65` — migration hardening (`migrateSubProjects.py`,
  address/include/orphan/layout passes) with the matching skill refresh.
- `fcff7c6` — bugfixes surfaced by ISP porting across the build manifest,
  eval-to-SV conversion, register handlers, and structure emission.
- `1b58623` — cross-interface boundary thunker support on testbench externals,
  plus the new `xif` example exercising it.

Review-cycle milestones (2026-07-29 through 2026-08-04):

- `14ce4c4` — the combined review-item landing: project-qualified identity,
  the schema-native nested variant form and its completeness validator, strict
  one-to-one variant configuration, nested address containment with its negative
  fixture, and the conversion of every block implementation to a single `.cppm`.
- `3ee90d5` — skill refresh for migration, parameterizable authoring, SystemC
  module authoring, and model review.
- `477d6c6` — `inheritContainerParam`: schema field, configuration-selection
  branch, five database-time preconditions, and `test_inherit_container_param.py`.
- `b17a0fc` / `5565acd` — `plans/` placed under version control (64 documents),
  the module-preamble import relocation in the SystemC templates, and the
  normative tandem emission specification.
- `bc81ff2` — standalone `make` invocation fix for the agent-rules target.
- `38b17af` — reachability-scoped managed SystemVerilog compile set, stable
  hierarchy node identifiers for diagrams and documents, qualified `endmodule:`
  labels and user import packages in `hierInclude`, deletion of the superseded
  `mixed` block header orphan, and `VL_DUT` propagation into the co-simulation
  run targets.
- `7274b9c` / `59b7329` / `b523777` — `endOfTest` migrated to the
  `a2c.endOfTest` module with a single shared singleton and a framework
  startup gate, firmware board-support package relocated, relational, equality,
  and ternary operators added to the expression evaluator, and the examples
  rebuilt onto the module.
- `6a9330c` / `2b3f6d1` — concrete Verilated-top selection for a non-templated
  wrapper, then relocation of that selection from the `projectOpen` view into
  the template utility layer to restore the ownership split.
- `de022a1` — parameterized read/write registers carry their declared reset
  values into the generated multi-word decoder instead of resetting to zero.

Change volume is dominated by plan documents plus regenerated and reorganized
examples:

| Top-level area | Paths | Insertions | Deletions |
|---|---:|---:|---:|
| `examples/` | 942 | 34,890 | 22,703 |
| `plans/` | 64 | 37,689 | 0 |
| `unittest/` | 160 | 11,478 | 512 |
| `pysrc/` | 30 | 9,285 | 977 |
| `templates/` | 26 | 1,894 | 984 |
| `rules/` | 20 | 1,594 | 242 |
| `config/` | 7 | 1,146 | 404 |
| `common/` | 23 | 827 | 135 |
| `interfaces/` | 17 | 520 | 173 |
| `include/` | 6 | 401 | 153 |

## Recorded Acceptance Runs

### Executed for this refresh (2026-08-04)

Unlike previous refreshes, this one ran acceptance rather than only citing
owner-plan records. Results are stated exactly as observed at HEAD `2b3f6d1`.

- **Unit suites: 88 of 88 pass**, 25-42 s wall clock depending on machine load,
  via `unittest/run_all_tests_parallel.sh`. The first run of this refresh covered
  every `test_*.py` file present and passed 87 of 87; the eighty-eighth is
  `test_param_type_signedness.py`, added with the BUG 10 fix. The pre-fix run was
  85 of 85 selected out of 87 present; the two unselected suites plus one further
  unregistered suite were defect B2, and after that fix both runners select all.
- **Generation across every base example is clean.** `test_build_manifest.py`
  performs an in-place `make clean/db/gen` on all 16 base examples and passes,
  and the `builder/base` working tree stayed clean through it, so generation is
  byte-idempotent at HEAD.
- **Base example execution suite: all 14 targets pass.** Before the fixes,
  `make pipeline-test` failed at `nested`, `helloWorld`, `mixed`, `apbDecode`, and
  `axiDemo`, every one with the identical `Premature end of test detected`
  assertion — one cause, five symptoms (defect B1). After the five fixes the suite
  was re-run from clean and independently re-verified: exit code 0, **38
  `No error` reports**, and zero occurrences of `make: ***`, `Premature`,
  `Fatal`, `error:`, or `%Error` across the 4,558-line log. Coverage includes
  `diagram-and-doc` golden comparison, model runs for `nested`, `helloWorld`,
  `mixed`, `pySocket`, `apbDecode`, `axiDemo`, Verilator co-simulation for
  `axi4sDemo`, `hierVlDemo`, composed `ip_test` (root model plus four co-simulated
  instances), standalone `ip` and `bridge` (model and co-simulation each), and
  `simple_ip` (model and co-simulation), plus `rtl lint` for `mixed`, `pySocket`,
  `apbDecode`, `axiDemo`, `hierInclude`, and `inAndOut`.
- **Generation is idempotent and the suite is side-effect free.** After the full
  suite, the only modified files in `builder/base` are the 23 belonging to the
  five fixes and the plan documents. The suite performs in-place generation across
  every example and left no other change, so the committed tree and a freshly
  generated tree agree byte for byte.
- **Two invocation hazards were confirmed and are worth recording.** A top-level
  `make -j pipeline-test` is unsafe: several targets share the `mixed` database
  and race in `projectOpen`, producing `Invalid config item ... not found`
  followed by `KeyError: 'instances'`. Inner recursive makes already use `-j`, so
  the top-level target must run serially. Separately, an example directory
  regenerated with `make clean gen -j` in one invocation does not guarantee
  `clean` before `gen`; the two must be separate invocations.

### Recorded by owner plans

These are exact counts recorded by the dated owner-plan acceptance entries and
were not re-executed for this refresh:

- **8/8 L5 executions:** standalone `ip` model+VL (2), standalone `ipBridge`
  model+VL (2), and composed `ip_test` model + VL-src/ip0/ip1 (4), all
  `No error` on 2026-07-22.
- **2/2 focused foreign-variant VL paths** (`uIp1`, `uBridge.uBridgeIp1`) reached
  `No error`; **13/13 wrappers** were byte-identical after clean regeneration.
- **8/8 composed hierarchical VL executions** reached `No error` after the
  2026-07-23 `ip_test` directory collapse.
- **2/2 `simple_ip` execution gates** (model and composed VL) reached
  `No error`; firmware register readback also passed.
- **8/8 focused address-migration tests** pass for the committed rerun cleanup
  in `a0ec705`.
- **Three-section module infrastructure:** the committed `e2002d8` generator
  split and migration phase cover all in-tree parameterized block modules;
  `e503ccb` adds focused C++ module-map tests and the full runner integration.
- **Logical ownership S2:** scanner suite **7/7**, standalone
  `ipBridge` generation, composed `ip_test` generation/run (`No error`), all 10
  buildable examples byte-identical, and the full **66-suite** runner pass are
  recorded in `plan-projectoverride-file-ownership.md`. These runs predate the
  `e59ad94` commit of the same work and were not repeated after it.
- **Project-mode owner stamps:** `test_project_param.py` **4/4**,
  standalone bridge generation, composed `ip_test` generation/run, and linked
  VL builds pass; exactly 13 `rtl.f` files change from `--context` to
  `--project`. The suite count has since grown from 82 to 84 files with
  `test_project_scan.py` and `test_project_param.py` now committed.

## Open Items

No active item remains on the 116 composition, layout, registrar, or review
action-item critical path. Defect detail lives in the separate bug register
[`bugs-116.md`](./bugs-116.md); this section carries only status and pointers.

### Release-blocking defects found and fixed 2026-08-04

Five defects (B1-B5) were found by running acceptance for this refresh and are
all fixed in the working tree and verified. They are recorded, with full
diagnosis and fix detail, in [`bugs-116.md`](./bugs-116.md) Section 1:

| | Defect | Fix |
|---|---|---|
| B1 | End-of-test startup gate discarded a vote cast inside `startupDelay`, aborting five examples with `Premature end of test detected` | Activity recorded at vote time (`voteCast`) instead of inferred at evaluation time |
| B2 | One unit suite failing on a stale expectation; three suites unregistered in the serial runner | Expectation derived from `qualifyModuleIdentity`; all three registered; both runners now select 87 of 87 |
| B3 | Sixteen stale generated artifacts in the committed example tree, every one in a composed child | All 17 projects regenerated, children before parents |
| B4 | `clean` from a project root left `rundir/build`, so dependency files naming the deleted `endOfTest.h` broke the next build | `BIN_DIR` moved to `a2c-common.mk` so the shared `clean` owns it |
| B5 | Firmware board-support relocation not opted into by the `bridge` sub-project | `EXTRA_A2C_SRC_DIRS` mirrored in its Makefile |

None was caused by a review action item, though item 5's module work exposed B1,
B3, and B5. B1's fix is a deliberate strict relaxation of the startup guard; its
semantic consequence is recorded with the defect.

### Deferred, conditional, and independent backlog

1. **Logical file ownership S3-context — committed, sign-off pending:** the
   S1/S2 scan-all/parse-master ownership, S3-project `--project` stamping, and
   the context-stamp pass are committed in `e59ad94`. `resolveContextKey` now
   exits on a non-canonical context name instead of reconciling by basename, so
   the fallback this item tracked is retired. What remains is owner-plan
   sign-off: no standalone/composed acceptance run was executed as part of the
   2026-07-28 metrics refresh.
2. **`pySocket` project migration / registrar S7:** the YAML/address/include
   conversion, `.cppm` base and include modules, registrar output, and user-code
   port are committed in `e59ad94`. The `pySocket` target passes in the
   2026-08-04 base suite run, which satisfies the model half of the recorded-pass
   condition; the VL half is still not separately recorded. One residual was
   found while verifying: `examples/pySocket/model/pySocketIncludes.cpp` and
   `.h` are header-mode leftovers from `#107`, superseded and unreferenced — the
   design imports `pySocket_tb`, and `pySocket_tbIncludes.cppm` is the live
   module — so they are unswept orphans rather than an active header-mode
   context. They belong to the orphan-sweep backlog, not to this item's
   acceptance.
3. **Parameterized user-code migration:** `make migrate` now performs the
   mechanical text conversion, DB build, frozen-map orphan sweep, create-once
   scaffolding, and regeneration. When a parameterized legacy block must move
   from `.cpp/.h` to `.cppm`, the tool deliberately reports `TODO_PORT`; the
   region-preserving port remains agent-driven. A general current-format
   clean-start/recovery operation (file-ownership W4) is also future work.
4. **C1 boundary-artifact contract refresh:** keep the documented child
   boundary explicitly aligned to the child Base module plus parent-owned
   per-variant Config. The delivered fixtures satisfy this shape, but the
   composition owner index still marks the contract-refresh task open.
5. **Q-C8 absolute language identity — CLOSED (2026-07-30):** review item 1
   delivered the absolute `{owningProject}_{stem}` qualification for the C++
   module and namespace, the SystemVerilog package, and the SystemVerilog module
   name, with prefix-dedup and two uniqueness gates. This item is no longer
   latent and must not be carried forward as open work. Only **C2.5 header-path
   disambiguation** remains deferred, and it activates only if two projects ever
   ship generated headers with the same basename on one include path.
6. **Option-D collision hardening — deferred, now unblocked:** the stated
   precondition is met, since `e59ad94` retired the provisional basename-based
   `resolveContextKey` ownership resolution. Adding the duplicate-definition
   D-SD8 fixture remains outstanding and separate. The current Option-R fixture
   was never blocked.
7. **Cross-level wrapper hardening — deferred by architect:** declaration-owner
   negative validation, fixture-declaration ownership cleanup, and a consolidated
   `projectOpen` wrapper view (P2 Gaps 1/3/4). P2 itself is accepted against the
   selected proof bar.
8. **Cross-project symbolic-eval fixture — deferred:** Q-C12/G5 remains
   unexercised because `src`/`ipLeaf` stay root-owned; current evaluation and
   address-map acceptance are green.
9. **Independent cleanup/design backlog:** the behavior-preserving
   `processYaml.py` split, authored YAML namespace/import semantics, and the
   `wordLines` resolver-lifecycle cleanup remain design-only. Also deferred are
   implicit-default-Config emission (M4), variant-config D2/templated
   `prt()`/D10, register-bus leaf-handler/protocol-changer guidance, and the
   firmware-decode skill rewrite. The pre-existing `test_build_manifest`
   failure shared by `hierVlDemo` remains tracked outside the composition arc
   as issue #22. Commit `33d0095` broadens the SV discovery root from
   `verif/vl_wrap` to `verif` and may address that failure, but no recorded
   `hierVlDemo` PASS closes the issue yet. None is required for the delivered
   116 workflow.

10. **#116 review action items — CLOSED (2026-07-30):** all six review action
   items and the seventh item that the product migration added
   (`inheritContainerParam`) are delivered; execution detail is in
   [`plan-116-review-feedback.md`](./plan-116-review-feedback.md). Two residuals
   from that work remain, both narrow:
   - the `inheritContainerParam` **cross-project negative fixture**, deferred
     because it needs a composed multi-project fixture rather than a single-file
     unit fixture; the precondition it would prove is implemented and enforced;
   - the deferred **whole-suite orphan-sweep migration** for legacy-layout
     examples. The `hierInclude` symptom that surfaced it is resolved
     (`38b17af` qualified its begin labels, end labels, user import packages, and
     lint top module), and the superseded `mixed` block header orphan was
     deleted in the same commit, so no example failure is attributable to this
     item any longer. The generic clean-start operation it belongs to is
     file-ownership W4, tracked in item 3 above.
11. **Externally reported defects — see the bug register:** BUG 10
   (parameterizable types lose signedness) was a real generator defect that the
   entire example suite was blind to; it is **FIXED**, and it ships with both a new
   unit suite pinning the emitted alias and an executed example fixture, each shown
   to fail without the fix. BUG 12 (LUT unsigned saturate) needed no separate fix,
   since BUG 10 was its root cause. BUG 13 (LUT regression coverage gap) is
   **analysed to an executable specification but not closeable from this tree**,
   because every file it changes is in `/work/ws/isp`. One finding is deliberately
   left open: signed parameterizable types wider than 64 bits get no sign
   extension, latent because no such type exists today. Full analysis, including
   what each originating report got wrong, is in
   [`bugs-116.md`](./bugs-116.md) Section 2.
12. **Status-port comparison under tandem — open design question, own document:**
   a status port has no transaction on either side, so the per-notification
   comparison the tee performs is unsound in principle rather than merely
   mistuned, and `status_port_tee.h` is instantiated by zero examples in the
   repository. This is a verification-harness design problem needing study and
   probably a prototype, not a defect with a determinate fix, so it is tracked
   separately in
   [`bug-status-port-tandem-compare.md`](./bug-status-port-tandem-compare.md)
   rather than in the bug register.

## Plan Hierarchy

### 1. Umbrella and control

- `plan-development-ordering.md` — active high-level control document and
  next-work index; points to the owner plans below.
- `bugs-116.md` — defect register for this release. Section 1 holds the five
  release blockers found and fixed while verifying the 2026-08-04 refresh;
  Section 2 holds the reviewed external bug reports (BUG 10, 12, 13) that are
  confirmed but not fixed. Defect detail belongs there, not in this status index.
- `bug-status-port-tandem-compare.md` — open investigation into what a status-port
  comparison under tandem should mean. Kept separate from the bug register because
  it needs a design decision and a prototype before any code change, and because
  no in-tree harness exercises the code in question.
- `plan-ip-namespaces-and-parameterization.md` — original umbrella plan
  (historical context).

### 2. Foundation and prototype (complete)

- `plan-p0-proof-of-concept.md`, `plan-p0-rtl-proof-of-concept.md` —
  completed prototype records.
- `plan-f2-f3-design.md` — supersedes the F2/F3 portions of
  `plan-foundation-address-decode.md`.
- `plan-foundation-address-decode.md` — phase context for F1-F3 / A1-A3.
- `plan-ip-test-example.md` — defines the `ip_test` fixture.

### 3. Config template and registration (complete)

- `plan-variant-config-unification.md` — authoritative variant/config
  index (Stages 1-11; absorbs `plan-block-registration.md` Step 10).
- `plan-step-11-variant-aware-testbenches.md` — generated testbench
  variant selection.
- `plan-canonical-verilated-wrappers.md` — exact-width Verilated wrappers.
- `plan-config-policy-views.md` — Config header/view cleanup.
- `plan-parameterizable-config-template.md`,
  `plan-cppm-module-scaffold-sections.md`, `plan-block-config-postprocess.md`,
  `plan-block-registration.md` — earlier design records for this layer.

### 4. SV parameterization and register decode

- `plan-sv-parameterization.md` — strategy decision record (module-local
  params/types plus package defaults).
- `plan-param-constant-collision.md` — C1-C4 collision work. C1/C2
  complete; C3 complete; C4 handed to the eval plan.
- `plan-parameterized-register-decode.md` — C3.R register-handler record.

### 5. Symbolic eval and YAML migration

- `plan-eval-symbolic-emission.md` — completed C4 execution record. E4 complete;
  E5 complete (SystemC plus firmware C, the latter exercised by the `ip_test`
  `fw/` tree); E6 closed (descoped — worst-case address sizing makes addresses
  variant-invariant).
- `plan-eval-python-to-sv-migration.md` — E1.5 converter design; the core
  (`pysrc/evalPyToSv.py`) is committed and consumed by the YAML migration.
- `plan-yaml-migration.md` — unified migration behind `yamlFormat: 2`:
  `migrateYaml.py` + `make migrate`, eval Python→SV, addressControl→
  addressBlock, and project stamping. Landed; the converter diagnostic
  follow-up was resolved 2026-06-23.

### 6. Address-control refactor (complete)

- `plan-address-control-refactor.md` — move from project-wide
  `addressControl.yaml` to per-block `addressBlock:` / `registerPorts:`.
  Stages 1-6 committed; Stage 7 coverage complete; Stage 8 legacy
  retirement complete (`postParseRegister.py` deleted, legacy loader
  removed; new schema is the only accepted input).
- `plan-address-control-test-coverage.md` — Stage 7 coverage; checklist
  fully committed, no rows open.

### 7. IP composition, layout, identity, and registrar (delivered)

- `plan-composition-ordering.md` — authoritative composition dependency and
  ownership index. Its later 2026-07-22 entries retire the critical path:
  C2/L2b, C5/L5, registrar S0-S6, and wrapper P2 are accepted.
- `plan-ip-project-composition.md` — composition foundation. Q-C10, ownership
  truth, project layout, generation gates, owner-aware SC/RTL discovery, and
  standalone/composed model and RTL execution have landed.
- `plan-cross-project-block-resolution.md` — complete for the selected-provider
  contract. `projectFiles:`-only lookup was explicitly closed
  will-not-implement, strict scaffold ownership landed, and provider selection
  has focused positive/negative coverage.
- `plan-cross-project-shared-definitions.md` — Option R/D and hierarchical
  provider contracts are settled; explicit managed SV selection landed.
  Absolute Q-C8 qualification and the Option-D fixture are deferred.
- `plan-decomp-functional-layout.md` — L1-L5 complete/accepted.
- `plan-reusable-ip-registrar.md` — S0-S6 complete. S5's formerly-staged
  project-mode scaffolding and standalone closure are committed after
  `c42b535`.
- `proposal-config-ownership-header-relocation.md` — S3-H implementation
  record. General implementation and cleanup are committed as `52be673`;
  parent-owned foreign Config headers remove the stale-child-Config dependency.
- `proposal-qc8-identity-field.md` — Q-C8 seam and uniqueness gate landed;
  absolute qualification / Role C deferred as latent.
- `plan-cross-level-variant-wrappers.md` — Direction A and P2 complete against
  the proof-only acceptance bar; Gaps 1/3/4 are deferred hardening.
- `plan-projectoverride-file-ownership.md` — post-acceptance multi-copy
  ownership hardening. The scan-all/parse-master engine (S1/S2), project-mode
  `--project` stamp, canonical context-mode stamping, and basename-fallback
  retirement are committed in `e59ad94`; owner-plan sign-off is outstanding.

### 8. Migration, examples, cleanup, and backlog

- `plan-file-ownership-classification.md` — status reconciled 2026-07-24. The
  frozen-map `delete`/`port`/`leave` dispatch, orphan sweep, create-once
  makefile scaffolding, and one-command `make migrate` pipeline landed in the
  2026-07-22 through 2026-07-24 commits. `TODO_PORT` remains intentionally
  agent-driven; the first full in-tree `pySocket` port is committed in
  `e59ad94`. Generic W4 clean-start remains future work.
- `plan-block-module-3section.md` — its header still says proposed, but the
  generator split, `moduleExport` section, migration tool, example updates, and
  supporting build work are committed in `33d0095`/`e2002d8`; current branch
  history is authoritative. Extended by review item 5: the `blockModule` gate is
  now all `hasMdl` blocks, the generated `using namespace` moved out of the
  `moduleExport` region for non-register-handler blocks so the preamble user slot
  is legal (`b17a0fc`), and `endOfTest` became the `a2c.endOfTest` module
  (`7274b9c`) so a framework singleton is no longer a header in a module purview.
- `plan-item5-port-mechanization-assessment.md` — read-only feasibility
  assessment of mechanizing the `.cpp/.h` → `.cppm` user-region transplant over
  the `codeText` region splitter. Its hybrid recommendation was adopted and
  executed as review item 5.
- `spec-tandem-parameterized-types.md` — normative descriptive specification of
  the tandem wrapper emission contract under parameterized types, written to be
  portable across generator implementations. Tandem is pro-only and base contains
  no tandem artifact, so its worked examples are derived renderings anchored on
  base blocks rather than copied output; Section 5.0 states what is real.
- `plan-simple-ip-example.md` — complete and committed; model/VL/firmware gates
  green.
- `plan-ip_test-dir-cleanup.md` — complete and committed; the primary
  hierarchical tree is collapsed and the old vehicle removed.

- `plan-cppm-include-contract-cleanup.md` — template identity cleanup;
  complete (commit `1c09e53` plus the 2026-06-23 WI6 descope).
- `plan-registration-encapsulation-cleanup.md` — committed; Option δ selected,
  `force_link` retired (retain attribute +
  build-system contract), validated by the δ/tandem proto matrix.
- `plan-migration-tool.md` — historical C++/SV migration scope sketch,
  superseded by the current migration pipeline and agent-driven port workflow.
- `plan-split-processyaml.md` — open design-only mechanical refactor; it is not
  on the composition critical path.
- `plan-constants-flat-lookup.md` — open design-only `wordLines`
  resolver-lifecycle cleanup.
- `plan-foreign-key-lookup.md`, `plan-value-resolver-refactor.md`, and
  `plan-register-bus-cross-interface-check.md` — status headers reconciled to
  the landed implementations and focused tests; not active 116 work.
- `plan-schema-controlled-flat-data.md` — historical.
- `plan-shared-vs-ip-boundary.md` — deferred authored namespace/import design.
- `firmware_decode_skill_fix_plan.md` — open draft documentation/skill work;
  its baseline evaluation and canonical skill rewrite remain.
- `review-staged-python-changes.md` — historical review record. Its foreign-key
  finding is superseded by the committed lookup/schema refactor; its
  `busWidth = 4` cleanup remains separately deferred.

## Reconciliation Notes

The stale owner-plan status blocks identified by the original audit were
reconciled on 2026-07-24. The 2026-07-27 refresh additionally records the
committed three-section module/build work and the active
`plan-projectoverride-file-ownership.md` working-tree stages. Historical
checkpoint prose remains where it records the sequence, but is labeled
historical/superseded. In particular:

- composition control/owner plans now close Q-C9, C2/C5, L2b/L5, S0-S6,
  standalone compdb, and P2 while retaining C1/C2.5 and deferred hardening;
- parameterization, eval, registration, and address plans now close C3.6,
  E5/E6, Option delta, and Stage 7;
- file ownership now records W0-W3 landed and W4 open; and
- foreign-key, ValueResolver, and register-bus plans now point at their landed
  implementations instead of claiming design-only status.

## Status Taxonomy

- **Design only:** no code written.
- **Implemented in working tree:** code exists locally, not committed.
- **Committed:** present in branch history.
- **Verified:** an exact command or regression passed.
- **Deferred:** intentionally out of current scope, with the owning plan named.
- **Superseded / Historical:** kept for context; not implementation instructions.

## Change Log

- **2026-06-11 — Plan-document cleanup.** Seven documentation batches
  normalized the plan hierarchy: established `plan-variant-config-unification.md`
  as the variant/config index, closed the C1-C4 status handoff, reconciled
  address-control Stage 7 wording, normalized completed follow-ups, marked
  historical/superseded design docs, and classified the cleanup backlog.
  Documentation-only; no generator/test/example changes.
- **2026-06-22 — Status refresh.** Folded in commits `ca0afec` (parameterized
  eval), `9c9af64` (legacy YAML removal / Stage 8), `10124ad` (address
  migration), `fdf3569` + `ed84522` (example migration/porting), and
  `1c09e53` (file include cleanup). Net effect: unified YAML migration,
  address-control Stage 7 coverage, and Stage 8 retirement moved to complete;
  C++ identity cleanup moved to implemented-in-working-tree with the WI6
  residual; owner plans (`plan-development-ordering.md`,
  `plan-cppm-include-contract-cleanup.md`, `plan-address-control-refactor.md`,
  `plan-eval-symbolic-emission.md`, `plan-eval-python-to-sv-migration.md`)
  reconciled to match. C3.6, eval E5-firmware/E6, and registration
  encapsulation remain open. Verified against branch state; not committed
  (submodule — user manages staging).
- **2026-06-23 — Branch advance, no status change.** Two commits since the
  prior refresh: `53456ed` (port the `apbDecode` example to the new layout —
  `arch/yaml/` + `base/` dirs, cppm modules, `rtl/` + `rundir/`; continues
  the example migration/porting folded in for `fdf3569`/`ed84522`) and
  `3fb5b86` (test hygiene for `unittest/test_eval_sv_emit.py`: drop partial
  databases/temp trees on fixture failure, move `g.db`/`g.cur` reset into
  `finally`). Both are verification/porting hardening within the YAML
  migration and C4 eval workstreams; neither opens or closes a tracked row,
  and the six Open Items are unchanged. Committed range caveat advanced to
  `3fb5b86`.
- **2026-06-23 — Symbolic eval E6 closed (descoped).** Confirmed that C4
  does not require per-variant address-affecting evals: `calcAddresses`
  sizes parameterizable address objects to their worst case
  (`maxBitwidth` / `maxValue`), so offsets and decoded ranges are identical
  across variants and all variants share one address map. Per-variant
  address evaluation would break that shared map rather than improve it, so
  E6 is closed with no code or fixture work. Open Items drop from six to
  five; owner `plan-eval-symbolic-emission.md` reconciled. Documentation
  only.
- **2026-06-23 — Registration encapsulation cleanup resolved (Option δ).**
  The `force_link` follow-up is closed. Option δ selected over the α
  fallback: a portable `A2C_REGISTRATION_RETAIN`
  (`[[gnu::used, gnu::retain]]`) attribute on each self-registering
  static plus an explicit `--whole-archive` build-system contract for
  archive packaging. The generator no longer emits any `force_link`
  declaration/definition/call (`instanceFactory.h` macro;
  `constructor.py`, `baseClassDecl.py`, `testbench.py`, `blockRegs.py`,
  `fileGen.py`). Validated by the δ proto matrix
  (`proto/model/test/delta_matrix.sh`) on clang 20 + gcc 13 — direct-`.o`
  and modules PASS, archive-no-flag FAILs as expected, `--whole-archive`
  / `-Wl,-u` recover — and by a tandem-shaped proto (wrapper builds
  `_verif` + non-templated `_model` via the factory, no `force_link`;
  PASS direct-`.o` clang+gcc and modules clang). All eight `examples/*`
  regenerate with zero `force_link` and build/run. Decision + full table
  recorded in `research-block-registration-options.md` (2026-06-23
  addendum); Option 6a / Open Question 11 marked retired/resolved;
  `plan-block-registration.md` "Force-Link Function" marked historical.
  Open Items drop from five to four. A live `debayer` tandem run remains
  blocked by the unrelated WI6 cppm-include-contract gap, not by δ.
  Implemented in working tree; not committed (submodule — user manages
  staging).
- **2026-06-23 — Branch advance: registration δ committed + parameterizable
  struct tests.** Three commits since `3fb5b86`. `3994d1a` (trampoline
  cleanup) commits the Option δ registration-encapsulation work: the portable
  `A2C_REGISTRATION_RETAIN` (`[[gnu::used, gnu::retain]]`) attribute is added to
  `common/systemc/instanceFactory.h` and every `force_link`
  declaration/definition/call is removed from the generated base headers, model
  `.cpp`, and testbench/config `.cpp` across all `examples/*` (verified zero
  `force_link` references remain under `examples/`). `b4c4cae` (test structs for
  params) reworks SystemC struct round-trip test generation to the
  non-templated Option C shape — a shared `roundTrip<T>` helper plus
  deterministic Default/Mid/Max sample-point Configs (`<stem>TestConfig<Role>`,
  variant-independent, derived only from the ipParameter `value`/`maxValue`) —
  adds `config.configStructLines`, a memset fix in `sc_unpack` for
  exact-multiple-of-64 Config widths, and the new `unittest/test_eval_cpp_emit.py`
  exercising E5 symbolic eval-derived Config emission on the `ip_test` vehicle.
  `5ff43e1` (add test structs) regenerates the example `.cppm` includes with the
  new test infrastructure. Net effect: the registration-encapsulation row and
  the new parameterizable-struct/eval-test row move to committed; the four Open
  Items are unchanged (the δ follow-up was already closed in the prior entry,
  and WI6 / C3.6 / E5-firmware / YAML-converter remain open). Committed range
  caveat advanced to `5ff43e1`. The committed E5 test coverage hardens the
  symbolic-emission half of Open Item 2; the deferred firmware-C half is
  unaffected. Documentation only; plan docs untracked (submodule — user manages
  staging).
- **2026-06-23 — Symbolic eval E5 firmware C closed.** The firmware-C half of
  E5 is no longer deferred: commit `3994d1a` adds a generated `fw/` tree to
  `ip_test` (per-context FW headers `*IncludesFW.h/.cpp` plus a hand-authored
  `fw/src/fwIpMain.cpp/.h`) that exercises parameterizable eval-derived
  constants in firmware headers — exactly the fixture the deferral was waiting
  on. `examples/ip_test/fw/include/ip/ipIncludesFW.h` emits the eval-derived
  constants into the flat FW constants section with the eval operator structure
  preserved and base parameterizable members frozen to their worst-case literal
  (firmware has no per-variant Config): `IP_DATA_WIDTH_X2 = 70 * 2`,
  `IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2`, and the matching
  `IP_MEM_DEPTH_X2/X4` chain; `fwIpMain.cpp` consumes `IP_DATA_WIDTH_X2` as a
  real reader. C4's E5 row moves to complete (SystemC + firmware C); Open Items
  drop from four to three (C3.6, WI6, YAML-converter follow-up remain). Owner
  `plan-eval-symbolic-emission.md` reconciled. Committed; not "Verified" here —
  no fw build/run was executed as part of this status update. Documentation
  only; plan docs untracked (submodule — user manages staging).
- **2026-06-23 — C++ identity cleanup WI6 closed (descoped).** The last
  residual of the template identity cleanup is resolved. `config.py`'s
  per-context `<context>DefaultConfig` name was kept on the `contextStem`
  derivation rather than routed to a new `getContextData()` field, because the
  persisted `blocks.defaultConfig` column cannot be cleanly consumed per
  render: `calcBlockConfigInfo()` keys it off a block's `contexts[0]` (the
  first parameterizing context, not the block's `_context`, and not persisted),
  and constant-only config contexts (real, per `_configHeaderContexts()`) have
  parameterizable constants but no primary block to read from. The only real
  defect was the template's incomplete sanitization: it mapped `-`→`_` but not
  `.`→`_`, so a context stem containing `.` could emit a struct name that drifts
  from the type consumer blocks reference. Fixed by aligning `config.py` to
  `calcBlockConfigInfo()`'s `.replace('-', '_').replace('.', '_')`. No view or
  schema/contract change. Open Items drop from three to two (C3.6 and the
  YAML-converter follow-up remain). Owners `plan-cppm-include-contract-cleanup.md`
  (WI6 + Open Question #3 marked resolved) and `plan-development-ordering.md`
  (Next-Work item 6) reconciled. Code change is the one-line `config.py`
  normalization; plan docs untracked (submodule — user manages staging).
- **2026-06-23 — C3.6 static validation matrix closed.** The C3.6 endpoint
  validator (`_validateParameterizedConnectionEndpoints`, run inside
  `deriveParameterizedDeclSets()` in `pysrc/processYaml.py` off the in-memory
  `paramSet`) was already present; C3.6 is closed by filling the validation
  matrix it calls for in `unittest/test_param_const_linkage.py` (7 → 11 cells):
  negatives for a dst endpoint parameterized on the wrong backing param (the
  second error-reason branch) and a src-side shortfall (both ends checked), plus
  positives for a plain interface between plain blocks (no over-firing) and the
  C3.5 cross-variant non-parameterized boundary channel (validation correctly
  skipped). Each fixture runs a real `arch2code.py` projectCreate end-to-end;
  **11/11 PASS** (verified). No validator-logic change was needed. C3 has no
  residual. Open Items drop from two to one (only the YAML-converter follow-up
  remains). Owner `plan-param-constant-collision.md` reconciled (C3.6 marked
  DONE 2026-06-23). Plan docs untracked (submodule — user manages staging).
- **2026-06-23 — Unified YAML migration converter follow-up resolved.** The last
  Open Item is closed. The `TODO_LEAF_REGISTER_PORTS` message emitted by
  `pysrc/migrateAddressControl.py` (`_routedLeaves` emit + the constant comment)
  pointed at "address-migration.md Step 4 (and Step 6.2)", a step that does not
  exist (the skill runs Steps 1–7; Step 4 is the policy-section step). The
  message now points directly at "the registerPorts: note under Migration
  Diagnostics in address-migration.md". The skill was reconciled in lockstep: the
  stale "Tool report item" annotation under Step 4 was removed and the
  converter-message quote relocated to the `registerPorts:` note in Migration
  Diagnostics; both routing tables (`address-migration.md`, `migrate-project.md`)
  were repointed. Suite 19j `test_migrate_address_control.py` now asserts
  "Migration Diagnostics" rather than "Step 4" in the leaf TODO message. Open
  Items drop from one to zero. Owner `plan-yaml-migration.md` reconciled
  (carried follow-up marked RESOLVED). Plan docs untracked (submodule — user
  manages staging).
- **2026-07-17 — IP composition arc: composed `ip_test` builds AND runs.**
  Composed multi-project `examples/ip_test`
  `make clean gen run` now reaches `No error`, with the full base+pro suite
  green (`mixed`/`pySocket` pre-existing deferrals excluded). Commits: `6791451`
  (BSP register-access `regRdWr`/`modelComm`/`fwlog` relocated pro→base at
  `common/systemc/bsp/`), `91b69dc` (`validateDeclaredPorts` scoped to
  instantiated blocks → a definitions-only project may own a `hasMdl` block it
  never instantiates), `ab75e9c` (zero-instance block boundary-port synthesis
  from the definition + `cpu` de-duplicated into a single `common`-owned generic
  APB master running firmware on the BSP seam; unittest
  `test_zero_instance_ported_block.py`), and `4038204` (cross-project plain-block
  registration — container emits the child's owning `projectName` in
  `createInstance`). Commit `6bbec76` then lands the `bridgeDriver` relocation,
  `ip_top`→`uBridge`-from-`uSrc` rewire, and owner-aware RTL directories;
  `6113562` wires VL wrapper Makefiles to `A2C_VL_WRAP_DIRS`. This closes the
  composed-model run blocker but not the broader C2/L2b, Q-C8, provider,
  registrar, or VL acceptance work. Earlier commits `894f101` and `88d7520`
  supply authoritative ownership/provider redirection and active-root router
  reachability respectively.
- **2026-07-17 — Standalone bridge and provider-contract coverage.** Commit
  `0b3a699` makes `bridgeStdTop` a runnable standalone `ipBridge` model harness
  and carries the foreign-variant prototype fixture. Commit `37bad48` adds a
  focused provider-override fixture and test: the positive case proves the root
  override selects exactly one provider, and the negative case proves removing
  it fails with both provider paths and the `projectOverrides` recovery in the
  diagnostic. Some owner plans still carry pre-commit wording that calls these
  two items open; current branch history is authoritative for this report.
- **2026-07-21 — Foreign Config ownership S3-H landed.** Commit `52be673`
  implements project-qualified variant declaration identity and parent-owned
  foreign Config headers in the registrar domain. The parent container and SC
  registrar now consume the same owner-qualified Config type; a clean
  child-first rebuild no longer depends on stale `ipVariant1Config` output in
  the reusable child. The composed `ip_test` model flow reaches `No error`.
  This closes the cross-level wrapper P1 SC-path blocker, but does not complete
  P2 or the gated S3-M/S6/S5 module/VL end state. Commit `c377962` extends
  manifest/example coverage, and `cbea09a` removes the obsolete `mixed`
  registrar orphan and closes that test deferral. Current HEAD is `cbea09a`;
  `plans/` remains ignored and user-managed.
- **2026-07-22 — Registrar S3-M / S6 / F10 landed (coupled config-module +
  verilated relocation).** Three commits complete the coupled registrar end
  state above S3-H: `d7f65b6` (S3-M) folds each parent-owned foreign Config
  header into a canonical config MODULE interface unit (`.cppm`) per
  `(owningProject, child)` that the container and SC registrar `import` (struct
  names unchanged, so no cast site moved); `7cb32f3` (S6) emits owner-qualified
  per-variant SV wrapper tops `<projectName>_<child>_<variant>_hdl_sv_wrapper`
  with explicit per-top `file->top` manifest records driving `a2c-vl-wrap.mk`
  (distinct `--Mdir` per top; gate #6 closed) plus per-assembler guarded
  `VlRegistrar.cpp` registration keeping the container cast non-null under
  `VL_DUT`; `c42b535` (F10) retires the `vl_wrap.h/.cpp` aggregator suite-wide.
  Composed `ip_test` `VL_DUT` is GREEN (uSrc/uIp0/uIp1 all `No error`). Gate #5
  (cross-assembler owning-key dedup) was DROPPED — `emplace` is first-wins so a
  duplicate `_verif` registration is harmlessly ignored; no fixture exercises
  it. Registrar S5 (standalone-TB module config home), cross-level wrapper P2,
  and the F10-unblocked sub-project `compdb` remain open. Current HEAD is
  `c42b535`; `plans/` remains ignored and user-managed.
- **2026-07-24 — Branch and plan reconciliation through `a0ec705`.** Twenty
  first-parent commits after `c42b535` close registrar S5/standalone compdb,
  hierarchical-layout and `rtl.f` placement, the canonical `ip_test` collapse,
  `simple_ip`/`hierVlDemo`, generated-file discovery without C++ source
  scanning, and the one-command migration/orphan-sweep/scaffold pipeline.
  Recomputed branch metrics cover 76 first-parent commits (74 non-merge
  `#116` commits), 1,085 changed paths, +51,550/-22,510 lines. The former
  C2/L2b, C5/L5, S5, composed-VL/clangd, and wrapper-P2 rows are closed.
  Remaining work is explicitly classified as deferred/conditional or
  independent cleanup: `pySocket`, `TODO_PORT` user-code ports, latent Q-C8,
  C1 contract refresh, Option-D collision hardening, wrapper Gaps 1/3/4,
  Q-C12/G5, W4 clean-start, `processYaml.py` splitting, authored namespaces,
  firmware-decode guidance, and `wordLines` cleanup.
  No full regression was rerun for this documentation-only refresh; the report
  records the exact acceptance counts from the dated owner plans plus the
  focused 8/8 address-migration result attached to the final commit. The stale
  status blocks in the composition, registrar, parameterization, eval, address,
  migration, and Python-cleanup owner plans were reconciled in the same
  documentation pass. The executive summary now also records the user-facing
  functional skill work: generated register-decode architecture,
  address/layout placement, parameterization, RTL-register, and testbench
  guidance.
- **2026-07-27 — Module/build commits plus logical-ownership working tree.**
  Seven first-parent commits advance HEAD to `f07ae17`: nested register-handler
  coverage in `mixed`, channel/include cleanup, three-zone block modules and
  their migration phase, faster DB-emitted C++ module maps, layout corrections,
  and project-scoped manifest consumption. Recomputed committed-range metrics
  are 83 first-parent commits (81 non-merge commits, 80 carrying `#116`), 1,110 changed
  paths, and +52,180/-22,797 lines. The working tree is intentionally reported
  separately: `plan-projectoverride-file-ownership.md` records independently
  verified S1/S2 scan-all/parse-master ownership and S3-project `--project`
  stamps, while S3-context canonical stamping is still active; the first full
  `pySocket` current-format/user-code port is also present but uncommitted. No
  new regression was run solely for this documentation refresh; acceptance
  counts above are the exact results recorded by the owning plan.
- **2026-07-28 — Metrics recomputed against HEAD `1b58623`; working tree now
  clean.** Five first-parent commits land after `f07ae17`: `e59ad94` (project
  scan ownership, multi-copy fixture tree, `test_project_scan.py` /
  `test_project_param.py`, and the `pySocket` conversion), `b5aca65` and
  `1494898` (migration hardening plus `migrateSubProjects.py` and the skill
  refresh), `fcff7c6` (bugfixes surfaced by ISP porting), and `1b58623`
  (cross-interface boundary thunker on testbench externals, with the new `xif`
  example). Recomputed committed-range metrics are 88 first-parent commits (86
  non-merge, 85 carrying `#116`; `894f101` is branch work typed `#166`), 109
  reachable commits, 1,198 changed paths, and +58,072/-23,087 lines. Unit-test
  suites go 82 → 84 and the example count 15 → 16. The prior refresh's
  separately reported working-tree state is retired: the `builder/base` working
  tree is clean and the S1/S2 ownership, project-mode stamping, and `pySocket`
  work it described are committed in `e59ad94`, which also retires the
  `resolveContextKey` basename fallback and so unblocks the deferred Option-D
  precondition. Open Items 1, 2, and 6 and the two matching status rows were
  corrected to state committed fact rather than working-tree state; their formal
  open/closed classification is unchanged and remains with the owning plans,
  because this refresh verified git history only and reran no acceptance suite.
  All figures in the previous refresh were re-verified against the repository
  and reproduced exactly at `f07ae17` before being recomputed.
- **2026-08-04 — Review-cycle refresh; acceptance executed; four release blockers
  found.** Thirteen first-parent commits land after `1b58623`, advancing HEAD to
  `2b3f6d1`, and they close every one of the review action items: `14ce4c4`
  (project-qualified identity, schema-native nested variants with a completeness
  validator, strict one-to-one variant configuration, nested address containment,
  and all block implementations converted to `.cppm`), `3ee90d5` (skill refresh),
  `477d6c6` (`inheritContainerParam`), `b17a0fc` (plans placed under version
  control, module-preamble import relocation) and `5565acd` (tandem emission
  specification), `bc81ff2` (standalone make fix), `38b17af` (reachability-scoped
  managed SystemVerilog compile set, stable hierarchy node identifiers,
  `hierInclude` relabelling, `mixed` orphan deletion, `VL_DUT` propagation),
  `7274b9c` / `59b7329` / `b523777` (`a2c.endOfTest` module, firmware
  board-support relocation, relational/equality/ternary evaluator operators,
  examples rebuilt), `6a9330c` / `2b3f6d1` (concrete Verilated-top selection,
  then its relocation out of the `projectOpen` view into the template utility
  layer), and `de022a1` (parameterized register reset values, which is also the
  fix for BUG 8 in the external ISP parameterization bug report). Recomputed
  metrics are 101 first-parent commits (97 non-merge, 93 carrying `#116`), 125
  reachable commits, 1,311 changed paths, and +101,292/-26,552 lines; roughly
  37,700 of those insertions are the newly tracked `plans/` documents and contain
  no product code. Unit suites go 84 → 87 files and examples stay at 16.
  Q-C8 and the whole review-item block are closed and must not be carried forward
  as open work.
  This refresh **executed acceptance** rather than only citing owner-plan
  records, which is a departure from the previous four refreshes, and it found
  **five release-blocking defects** that the review items did not cause but that
  their work exposed: B1, the end-of-test startup gate discarding an early
  explicit vote, which aborted five base examples with `Premature end of test
  detected` and was the single cause of every example failure observed; B2, a
  failing identity-uniqueness suite that neither test runner executed, plus two
  further unregistered suites — one of them review item 4's own negative fixture;
  B3, stale composed-child artifacts in the committed example tree, sixteen files
  in total and every one of them in a composed child rather than a root-owned
  project; B4, a surviving build directory whose dependency files name the
  deleted `endOfTest.h`, caused by `BIN_DIR` being defined only in
  `a2c-systemc.mk` so a project-root `clean` did not own it; and B5, the firmware
  board-support relocation not opted into by the `bridge` sub-project, which
  compiles the common project's `cpu` block. **All five are fixed in the working
  tree** and none is committed, since `builder/base` is a submodule the user
  stages. The B1 fix is a deliberate strict relaxation of the startup guard and
  its semantic consequence is recorded with the defect. **Post-fix acceptance was
  re-run and independently verified: unit suites 87 of 87 in 25 s — the first run
  covering every present suite — and `make pipeline-test` exit code 0 with 38
  `No error` reports and zero failure markers of any kind across all 14 targets,
  leaving no tree change beyond the fixes themselves.**
  Two invocation hazards are now recorded because both cost real diagnosis time:
  a top-level `make -j pipeline-test` races on the shared `mixed` database and
  fails with `Invalid config item ... not found` then `KeyError: 'instances'`, so
  that target must run serially while inner makes use `-j`; and
  `make clean gen -j` in one invocation does not guarantee `clean` before `gen`.
  **Defect detail was then moved out of this report into a separate register,
  `bugs-116.md`**, on the same date and at the user's direction: a status index
  states what shipped, the register states what was broken. That register also
  absorbed the reviews of four externally reported defects — BUG 9, 10, 12, and
  13 — which are confirmed against the code but not fixed, and which this report
  now references from a single Open Items entry rather than describing inline.
- **2026-08-04 (later, same day) — BUG 10 fixed with coverage; BUG 13 analysed to
  a specification.** `templates/systemc/includes.py::includeTypes` now selects
  `int64_t` or `uint64_t` from the declared `isSigned` on the parameterizable
  scalar arm, which previously hardcoded `uint64_t` and so silently contradicted
  both the YAML declaration and the SystemVerilog emitter. The container stays
  fixed 64-bit deliberately, because a parameterizable type must hold its worst
  case across variants, and that reasoning is now a durable comment in the
  template rather than only a plan note. Coverage landed with the fix at two
  levels, since the entire example corpus was previously blind to the defect: a
  new `unittest/test_param_type_signedness.py` pins the emitted alias text for
  four cases, and a signed parameterizable fixture in `examples/ip_test` asserts
  at runtime that the field unpacks negative and shifts arithmetically. Both were
  shown to **fail with the fix reverted and pass with it applied**, which was the
  acceptance gate; a plain pack/unpack round-trip passes either way and therefore
  could not have guarded it. **Unit suites are now 88 of 88** and
  `make pipeline-test` remains exit code 0 with 38 `No error` reports. The one
  finding deliberately left open is the multi-word arm: signed types wider than 64
  bits receive no sign extension at all, latent today because no such type exists,
  and recorded in the register rather than fixed. BUG 13 was investigated to
  completion in parallel but **cannot be closed from this tree** — every artefact
  it changes lives in `/work/ws/isp`, which is out of tree. The register now
  carries the settled reachability analysis it previously lacked.
