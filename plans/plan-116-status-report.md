# Report: 116 Plan Hierarchy and Status

Status as of: 2026-07-27
Branch context: `feature/116-parameterized-types` in `builder/base`

This is the status index for the `plan-*.md` files under `builder/base`.
It states current status definitively; detailed execution records live in
the owning plans named below. A dated change log is kept at the end.

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
  Verilated wrappers.
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
- **One-command migration and regeneration.** `make migrate` now sequences YAML
  conversion, database creation, the frozen-map orphan sweep, create-once
  scaffolding, and regeneration. Generated legacy artifacts are removed
  deterministically, user-owned files are preserved or reported for an
  agent-driven port, and both functional and hierarchical layouts use the same
  ownership policy.
- **Cleaner registration and module boundaries.** Parameterized block classes,
  Base interfaces, and registrar trampolines use explicit C++20 module and
  per-assembler ownership. Registration is retained through a defined
  build-system contract, and reusable implementation trees do not carry
  consumer-specific registration anchors.
- **Migration and compatibility support.** The branch completes the unified
  YAML migration path, replaces project-wide address-control input with
  block-owned address declarations, adds hierarchical-layout migration support,
  and ports the in-tree examples to the current contracts.
- **Expanded verification.** Standalone and composed model flows reach clean
  end-of-test. Automated coverage includes parameterized declarations and
  expressions, register decode, ownership, layout, zero-instance blocks,
  provider overrides, build manifests, and parent-owned configuration emission.

For program planning, the 116 critical path is complete. The branch now
demonstrates the full standalone and composed SystemC/model path, explicit
managed SystemVerilog source selection, owner-qualified per-variant Verilated
tops, standalone and composed RTL co-simulation, cross-project clangd, and the
final registrar/config placement. Builds and migrations are reproducible from
YAML/DB ownership data without source-tree discovery, including clean
standalone and composed regeneration. Since the previous refresh, the branch
also landed the three-zone C++ module scaffold/migration, generated C++ module
map acceleration, and stricter project-scoped build-manifest handling. The
scan-all/parse-master logical file ownership, project-name ownership stamps,
canonical context stamping, and the `pySocket` migration are now committed as
well, alongside migration hardening, ISP-porting bugfixes, and cross-interface
boundary thunker support. These are post-critical-path robustness and
migration improvements, not a reopening of composition acceptance. The branch
remains **feature-complete for the planned reusable-IP composition and
verification workflow**.

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
| Owner-qualified language identity (Q-C8) | **Interim uniqueness gate complete; absolute owner qualification / SV Role C deferred as latent** | `proposal-qc8-identity-field.md` |
| Cross-level foreign-variant wrappers | **Complete against the architect-selected proof bar; hardening gaps deferred** | `plan-cross-level-variant-wrappers.md` |
| File ownership + one-command project migration | **Mechanical pipeline landed; parameterized `.cpp/.h`→`.cppm` user-code port remains agent-driven** | `plan-file-ownership-classification.md`, `rules/skills/migrate-project.md` |
| Canonical examples and layout cleanup | **Complete: `simple_ip`, `hierVlDemo`, and collapsed `ip_test` hierarchy landed** | `plan-simple-ip-example.md`, `plan-ip_test-dir-cleanup.md` |
| Three-section C++ block modules | **Complete in committed generator/example infrastructure; GMF and module-import user zones plus migration support landed** | `plan-block-module-3section.md` |
| Multi-copy project override / logical file ownership | **Committed in `e59ad94` with `test_project_scan.py` / `test_project_param.py`; `resolveContextKey` now requires an exact canonical key, retiring the basename fallback. Owner-plan sign-off pending** | `plan-projectoverride-file-ownership.md` |
| `pySocket` current-format migration | **Committed in `e59ad94` (26 files): YAML/address/include conversion, `.cppm` base and include modules, registrar output, and user-code port. Standalone model/VL acceptance not rerun here** | `plan-file-ownership-classification.md`, `plan-projectoverride-file-ownership.md` |
| Functional skills and agent guidance | **Updated: register decode, architecture/address placement, parameterization, RTL registers, and testbench guidance** | `rules/skills/`, `AGENTS.md.template`, `ARCH2CODE_AI_RULES.md` |

Branch-state caveat: the workstream code is committed in branch history
(the original range began at `ca0afec`; current HEAD is `1b58623`), but
`plans/` is ignored and no plan document is tracked in the `builder/base`
repository. "Complete" above refers to implementation state, not plan-file
tracking. As of 2026-07-28 the `builder/base` working tree is **clean**: the
S1/S2 scanner integration, project-mode `--project` stamping, and `pySocket`
migration previously carried as implemented-in-working-tree are now committed in
`e59ad94`. Rows describing those items as uncommitted have been corrected below;
their formal open/closed classification is left to the owning plans, since no
acceptance suite was rerun for this metrics refresh.

## Branch Metrics

Metrics below cover the report's implementation range: the parent of
`ca0afec` (`1229582`) through current HEAD `1b58623`, 2026-06-11 through
2026-07-28. Commit counts use first-parent history so unrelated commits brought
in by merges are not presented as direct branch work; line and file counts are
the net tree diff across the endpoints, not cumulative per-commit churn.
Renamed paths are attributed to their source directory.

| Metric | Value |
|---|---:|
| First-parent commits | 88 |
| Merge commits on first-parent history | 2 |
| Non-merge first-parent commits | 86 |
| Non-merge first-parent commits carrying `#116` | 85 |
| All reachable commits, including merged side histories | 109 |
| Author identities across reachable commits | 3 |
| Paths changed | 1,198 |
| Files added / modified / deleted / renamed | 565 / 275 / 197 / 161 |
| Insertions | 58,072 |
| Deletions | 23,087 |
| Net lines | +34,985 |

The one non-merge first-parent commit whose subject does not carry `#116` is
`894f101`, which is typed `#166`; it is branch work despite the typo.

The first 11 first-parent commits (`ca0afec` through `5ff43e1`) close the
pre-composition work summarized in the 2026-06-23 entries. The following 77
first-parent commits carry the branch through project composition, layout,
ownership, provider selection, registrar relocation, migration, and example
cleanup. Major composition
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

Change volume is dominated by regenerated and reorganized examples:

| Top-level area | Paths | Insertions | Deletions |
|---|---:|---:|---:|
| `examples/` | 907 | 31,823 | 19,652 |
| `unittest/` | 162 | 11,230 | 382 |
| `pysrc/` | 26 | 7,815 | 953 |
| `templates/` | 26 | 1,775 | 941 |
| `rules/` | 14 | 1,449 | 195 |
| `config/` | 5 | 899 | 316 |
| `common/` | 19 | 691 | 54 |
| `interfaces/` | 17 | 520 | 173 |
| `include/` | 6 | 381 | 152 |

## Recorded Acceptance Runs

These are exact counts recorded by the dated owner-plan acceptance entries; no
new full regression was run solely for this documentation refresh:

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

No active item remains on the 116 composition/layout/registrar critical path.
The following active hardening plus deferred, conditional, or independent
backlog remains:

1. **Logical file ownership S3-context — committed, sign-off pending:** the
   S1/S2 scan-all/parse-master ownership, S3-project `--project` stamping, and
   the context-stamp pass are committed in `e59ad94`. `resolveContextKey` now
   exits on a non-canonical context name instead of reconciling by basename, so
   the fallback this item tracked is retired. What remains is owner-plan
   sign-off: no standalone/composed acceptance run was executed as part of the
   2026-07-28 metrics refresh.
2. **`pySocket` project migration / registrar S7:** the YAML/address/include
   conversion, `.cppm` base and include modules, registrar output, and user-code
   port are committed in `e59ad94`. The item stays open only pending a recorded
   pass of its standalone model/VL paths; the code is no longer uncommitted.
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
5. **Q-C8 absolute language identity / C2.5 — latent/deferred:** the fail-fast
   generated-name uniqueness gate is landed. Absolute
   `{owningProject}_{stem}` C++/SV linkage qualification, SV Role C, and
   C2.5 header-path disambiguation activate only when a real cross-project
   same-stem collision is introduced.
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

10. **#116 review action items — targeted for this release:** the review of
   `feature/116-parameterized-types` produced five substantive action items plus
   a documentation item, captured with implementation detail in
   [`plan-116-review-feedback.md`](./plan-116-review-feedback.md):
   project-name qualification of module/package identifiers (item 1), the
   nested-variant schema (item 2), always-emit variant-named config (item 3),
   nested address containment validation (item 4), full block-implementation
   module conversion (item 5), and migration-guide clarification (item 6). All
   are targeted for this release so users migrate once rather than repeatedly
   (items 2 and 5 both add migration surface). This supersedes the
   "latent/deferred" status of Q-C8 Role C in open item 5 above — item 1
   activates SV Role C qualification, simplified because `projectName` is now
   first-class — and the variant-config deferral in open item 9, since item 3
   requires per-variant Config emission.

The old `mixed` registrar-orphan deferral is closed. The earlier C2/L2b, C5/L5,
registrar S5, cross-project clangd, composed VL, and wrapper P2 items are also
closed and must not be carried forward as open work.

## Plan Hierarchy

### 1. Umbrella and control

- `plan-development-ordering.md` — active high-level control document and
  next-work index; points to the owner plans below.
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
  history is authoritative.
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
