# Plan: File Ownership Classification (segment-role user-vs-generated rule)

## Status

- **Direction (reconciled 2026-07-24):** implemented migration classification
  and scaffold policy, with W4 clean-start recovery still open. Drafted
  2026-07-22 from an investigation of the live example suite
  (`examples/simple`, `examples/ip_test`, `examples/axi4sDemo`,
  `pro/examples/lmmiDemo`, the `debayer` product root, and the
  `unittest/fixtures/hier-layout` hierarchical fixture).
- **Status taxonomy:** W0-W3 landed in the `make migrate` pipeline; W4 remains
  design-only. Every classification row below is grounded
  in `builder/base/config/project.yaml` (`dirs` / `hierarchicalDirs` /
  `fileGeneration.fileMap`) plus an on-disk `GENERATED_CODE_BEGIN` marker scan
  of real files. No generator code is changed by this document.
- **Owner surface:** the migration sweeps in `pysrc/migrateIncludes.py` and
  `pysrc/migrateLayout.py` (both consume `pysrc/migrateCommon.py`), and the
  `newModule.py` / `newProject.py` scaffolders. Cross-references:
  `plan-yaml-migration.md` (three-phase `make migrate`),
  `plan-migration-tool.md` (historical `.cpp/.h`→templated-model conversion),
  `plan-decomp-functional-layout.md` (functional vs hierarchical layout).
- **Headline finding:** the architect's folder rule is directionally correct but
  must be re-keyed on the **fileMap segment role**, not a literal top-level
  directory (hierarchical layout nests the same segments under `<node>/`), and
  it needs three categories beyond "user" / "generated": authored-YAML **input**,
  **build-output**, and user-owned **build-config**. The `fw` split and the
  makefile handling are the two genuine special cases.
- **DECISION 2026-07-22 (architect) — makefile policy: SCAFFOLD-ONCE, NEVER
  TOUCH.** `newmodule` creates each wrapper makefile create-only; once it exists
  it is never overwritten and the user owns it fully thereafter. Clean-start
  never deletes makefiles (USER build-config). Rationale: matches `newModule`'s
  existing create-only stance, and the shared make logic already lives in
  `include/make/a2c-*.mk` that the thin wrappers `include`, so the wrappers
  rarely change. This resolves the Makefile open question below and unblocks
  W2/W4.
- **DECISION 2026-07-22 (architect) — migration classifies against a FROZEN
  LEGACY fileMap, not the live merge.** Snapshot the legacy base + pro fileMaps
  (`builder/base` main + `builder` main `config/project.yaml`) into the migration
  code and classify legacy files against that (overlaid with the project's own
  user `fileMap`). The live `mergeProjectConfig` reflects the current layout, not
  the layout that placed the legacy files, and base/pro overlays are not
  guaranteed reconstructable — the frozen map makes migration self-contained and
  drift-proof. Legacy is `functional`-only (verified: legacy base `project.yaml`
  has `dirs`+`fileMap`, no `hierarchicalDirs`). New work item W0; W1 gains a
  migration-vs-ongoing map-source split. See the Proposal subsection.
- **DECISION 2026-07-22 (architect) — annotate the frozen map with a per-entry
  `migrate:` disposition, embedded in the migrate tools.** Because the frozen map
  is our own copy, add a migration-only field (`delete`/`port`/`leave`/
  extensible) to each fileMap entry; the annotated map becomes the SINGLE
  migration dispatch table (superseding class-inference heuristics). The map +
  annotations are EMBEDDED directly in the migrate tools (not a separate data
  file). See the "Annotate the frozen map" Proposal subsection.
- **FEASIBILITY VALIDATED 2026-07-22 (read-only) — expand legacy map over the
  CURRENT DB.** Confirmed expansion needs the DB, so the sweep is a POST-stamp +
  POST-`make db` phase. Build a NEW enumerator on the map-agnostic primitives
  `expandNewModulePath`+`fileMapCondMatch` (do NOT reuse `createBuildManifest.create`
  with a swapped FILEMAP — its context branch reads the current-map `INCLUDEFILES`
  blob and would miss the legacy `include` orphans). Orphans = `{p ∈ L\C :
  exists ∧ _isGenerated}` minus `keep`. Legacy map = base⊕pro (captured); orphan
  surface = ext deltas `include {h,cpp}→cppm`, `blockBase h→cppm`,
  `block→blockModule`. New module `pysrc/migrateOrphans.py`; test = unittest
  fixture. Guards: legacy basePath missing from current segments; on-disk +
  `_isGenerated` neutralizes block/context drift.
- **DECISION 2026-07-22 (architect) — SINGLE-COMMAND migrate.** No separate
  `make migrate-orphans` target. `make migrate` orchestrates the whole pipeline in
  one command: text conversions + stamp (`migrateYaml.py --write`) → (only if
  stamped/clean) `make db` → orphan-sweep (invoke the `migrateOrphans.py` sweep as
  a step) → `make newmodule` (scaffold the current fileMap's new-form producers
  the legacy generator never emitted — `make gen` does NOT create missing files) →
  `make gen`. Gated by make's fail-on-nonzero: manual TODOs halt before
  db/sweep/newmodule/gen; the user resolves them and re-runs the same
  `make migrate`. An
  already-stamped project still proceeds to db→sweep→gen (so `make migrate` sweeps
  lingering orphans + regenerates even on a "migrated" project), and is a no-op on
  a fully-clean one.
- **DECISION 2026-07-22 (architect) — MAP-AS-DECIDER (supersedes L\C-as-decider).**
  The per-entry `migrate:` disposition IS the decision; the sweep dispatches on it
  (no computed `L\C`). `delete` (purely generated → wipe + regenerate): `include`,
  `blockBase`, `package`, `vlSvWrap`, `vlScWrap`, `tandem`, plus an explicit
  literal-delete list for files with NO fileMap entry — the F10 aggregator
  `vl_wrap.{cpp,h,sv}`. `port` (user code, future `.cpp/.h`→`.cppm`): `block`,
  `rtlModule`. `leave` (user tb): `testBench`/`tbConfig`/`tbExternal`. `_isGenerated`
  is a HARD guard only (never the decider); user-region entries MUST be port/leave
  because the marker cannot distinguish them from purely-generated. Now `make
  migrate` = delete-all-purely-generated + regenerate (clean-start), byte-identical
  after regen on a clean project.
- **`port` — conversion mechanism DEFERRED ("look into later"); preference is a
  SIMPLE MECHANICAL automation, not an agent (architect 2026-07-22).** For now the
  migrate TOOL only IDENTIFIES + REPORTS `port` targets (`TODO_PORT`: old-form user
  file present while the current map produces a different form) and NEVER converts
  or deletes a `port` file; `delete`/`leave` stay mechanical. The eventual
  `.cpp/.h`→`.cppm` conversion is HOPED to be a deterministic region-splice reusing
  the existing generated-vs-user region parsing (`codeText` already chops every
  in-place file into `GENERATED_CODE` regions vs user regions) — lift the user
  (ungenerated) sections from the old-form file, re-inject into the new-form
  `.cppm`'s user regions, plus the `#include`→`import` rewrite — with agent-driven
  execution only as a fallback if the mechanical splice proves insufficient.
  (Earlier framing as "agent-executed from this framework" is superseded by this
  preference.)
- **PROGRESS 2026-07-22 — migration-tooling Stage 2+1 landed (separate, related
  work).** The shared-util refactor (`pysrc/migrateCommon.py`) and correctness/
  hygiene fixes are done and green; the orphan-sweep that this classification
  serves was deliberately NOT implemented on the old marker-scan basis and is
  now W3 (rewire onto the W1 segment-role classifier).

## Problem / Motivation

Two migration/maintenance operations need a robust answer to "is this file the
user's or the generator's?":

- **Orphan sweep (`plan-yaml-migration.md` phase, `migrateIncludes.py`).** When
  a context include migrates from the old `.h/.cpp` shape to a `.cppm` module,
  the stale `<context>Includes.{h,cpp}` files must be deleted — but only if they
  are genuinely generated orphans, never if a user happens to own a same-named
  file.
- **Delete-purely-generated clean-start.** A robust "wipe everything the
  generator can rebuild, keep everything the user authored, then regenerate"
  recovery path. This has no clean implementation today.

The deferred **`.cpp/.h`→`.cppm` user-code conversion**
(`plan-migration-tool.md`, historical) is a third consumer: it must know which
files are user-owned so it lifts/re-injects their hand-written regions rather
than clobbering them.

The current mechanism is **marker-scanning**: `migrateCommon._isGenerated(path)`
reads the whole file and tests for `GENERATED_CODE_BEGIN`
(`pysrc/migrateCommon.py:52`). `migrateIncludes.py` partitions delete candidates
with it (`staleFiles = [p for p in candidates if _isGenerated(p)]`,
`unguardedFiles = [... if not _isGenerated(p)]`, lines 124–125), and
`migrateLayout.py` uses it to decide "generated file moves to the node dir" vs
"hand-authored orphan moves to `prj/`" (lines 368, 375).

Marker-scanning is fragile and expensive:

- It reads and string-scans every candidate file.
- A **fully-user file** (no generated regions at all — e.g. `fw/src`
  firmware `.cpp`, a hand-written `sc_main`) is indistinguishable from a stale
  orphan by marker absence; today the code compensates with a name-glob
  pre-filter plus the marker check, and `migrateCommon.SOURCE_EXTS` narrows the
  walk to source extensions to avoid touching build scaffolding.
- It classifies **per file** when the real signal is **per location**: the
  generator places every artifact by `fileMap[*].basePath`, so a file's owning
  segment already encodes its ownership.

A folder/segment rule replaces a content scan with a path lookup that is
deterministic, cheap, and matches how the generator decides placement in the
first place.

## Proposal

Classify every file by the **fileMap segment role** of the directory it lives
in, not by scanning its contents and not by matching a literal top-level path.
The segment role is the `dirs`/`hierarchicalDirs` key (`base`, `model`, `rtl`,
`tb`, `vl_wrap`, `fwInc`, …) that `fileMap[*].basePath` references. This is
layout-agnostic: in `functional` mode the segment is a top-level directory
(`$root/model/<block>`); in `hierarchical` mode the same segment nests under the
node (`<node>/model/`) — see the taxonomy note below.

### The map used for MIGRATION classification is the FROZEN LEGACY map, not the live merge (decided 2026-07-22)

The effective fileMap the generator uses today is a MERGE of base + pro + user
(`mergeProjectConfig`). Two problems make that merge the wrong basis for
classifying a *legacy* project's files during migration:

- **It reflects the CURRENT (feature-branch) layout, not the layout that placed
  the legacy files.** A legacy file was emitted by the legacy fileMap; matching
  it against the new merged map (which added `hierarchicalDirs`, `mode: project`,
  `blockModule`, `blockVlRegistrar`, `vlSvWrapForeign`, `foreignConfig`, …) is
  where discovery misclassifies.
- **The base/pro overlays are not guaranteed to be reconstructable** in the legacy
  form at migration time — the migration must not depend on the current base/pro
  `project.yaml` still matching what the legacy files assume.

**Decision:** for MIGRATION classification, use a FROZEN snapshot of the LEGACY
base + pro fileMaps — captured from `builder/base` `main` `config/project.yaml`
and `builder` (a2cPro) `main` `config/project.yaml` — STORED IN the migration
code as a versioned resource, overlaid with the project's own on-disk user
`fileMap` (which the project being migrated carries). Verified capturable and
schema-compatible: both refs resolve; the legacy base `project.yaml` has standard
`dirs:` + `fileMap:` that the current loader parses, and — correctly — has **no
`hierarchicalDirs`** (legacy projects are all `functional`, so legacy
classification needs only the legacy *functional* `dirs`+`fileMap`; the
layout-agnostic keying above applies to the ONGOING/current-project use of the
classifier, e.g. clean-start on a current project, not to legacy migration).

This makes the migration self-contained and drift-proof: it classifies each
legacy file by the map that actually placed it, independent of how base/pro
evolve. The frozen map answers, per segment, "does this hold user code or pure
generator output," which is all the sweep/clean-start need.

### Annotate the frozen map with a per-entry `migrate:` disposition (decided 2026-07-22)

Because the frozen legacy map is OUR copy (it lives in the migration code, not in
the live generator fileMap), we can add a MIGRATION-ONLY field to each entry that
states, explicitly, how the migration should handle files of that type — instead
of inferring an action from a segment-role heuristic. Proposed field
`migrate:` with a small disposition vocabulary:

- **`delete`** — pure generator output; remove it (it is regenerated afterward).
  Covers the GENERATED-deletable segments (`base`, `registrar`, `vl_wrap`
  wrappers, `fwInc`) and marker-bearing orphans (e.g. `vl_wrap.{cpp,h}`).
- **`port`** — user-owned content that must be carried over: preserve the file's
  user regions and, when the current fileMap emits this type in a DIFFERENT form
  or name, re-inject those regions into the new form. Covers USER-PRESERVE
  (`model`/`rtl`/`tb`, `fw/src`) and specifically the `.cpp/.h`→`.cppm`
  block-module conversion (③b).
- **`leave`** — never touched: authored-YAML INPUT (`arch/yaml`) and USER
  BUILD-CONFIG (makefiles, `.gitignore`).
- extensible ("or whatever the case needs") — e.g. a `move`/`relocate` for the
  functional→hierarchical layout relocation `migrateLayout` already performs, or
  a `recreate` (= delete-then-scaffold) if that ever needs to differ from
  `delete`.

This turns the annotated frozen map into the SINGLE dispatch table for the whole
migration: walk each legacy file, find the entry that placed it, act on its
`migrate:` field. It supersedes the "infer the class from the segment role"
mechanism (the four classes above become the disposition values), and it is
explicit and auditable per file type rather than heuristic. Two things it does
NOT cover and that still need a rule: paths with NO fileMap entry (`fw/src`,
build-output `obj_dir`/`rundir/build`) — handled by the existing `SKIP_DIRS` for
build-output and an explicit `fw/src`→`port` rule; and the disposition that
depends on more than the type (e.g. `.cpp/.h`→`.cppm` `port` applies only to
PARAMETERIZABLE blocks — non-param blocks stay `.cpp/.h`, so the `port` action
must be conditioned on the current entry's emitted form, not applied blindly).

### Segment classification table (verified)

Citations: `L##` = line in `builder/base/config/project.yaml`; marker counts are
`GENERATED_CODE_BEGIN` scans of `examples/simple` (plus `debayer` root for
`fw/src`).

| Segment role (dir key) | functional path | hierarchical (`hierarchicalDirs`) | fileMap entries (basePath) | Class | Evidence |
|---|---|---|---|---|---|
| `base` | `$root/base` (L64) | `base` (L95) | `blockBase` | **GENERATED — pure, safe to delete + regenerate** | `simple/base` 3/3 files carry markers |
| `registrar` | `$root/registrar` (L65) | `registrar` (L96) | `blockRegistrar`, `blockVlRegistrar`, `foreignConfig` | **GENERATED — pure** | `simple/registrar` 1/1 carries markers |
| `model` | `$root/model` (L66) | `model` (L97) | `block`, `blockModule`, `include`, `config` | **USER-PRESERVE — in-place (user code + generated regions)** | `simple/model` 7/7 carry markers; user body lives *outside* the markers |
| `rtl` | `$root/rtl` (L66-area) | `rtl` (L98) | `rtlModule`, `package`, `rtlDotF` | **USER-PRESERVE — in-place** | `simple/rtl` 5/7 carry markers (the 2 without are `Makefile` + `.gitignore`) |
| `tb` | `$root/tb` (L68) | `tb` (L99) | `testBench`, `tbConfig`, `tbExternal` | **USER-PRESERVE — in-place** | `simple/tb` 5/5 carry markers; user body outside markers |
| `vl_wrap` | `$root/verif/vl_wrap` (L67) | `verif` (flattened, L100) | `vlSvWrap`, `vlSvWrapBody`, `vlScWrap`, `vlSvWrapForeign` | **GENERATED source (wrappers), safe to delete + regenerate** | in `simple/verif`, only 2/74 files carry markers — the 2 generated wrappers; the rest is build output (see below) |
| `fwInc` | `$root/fw/include` (L69) | `fw` (flattened, L101) | `includeFW` (disabled in base project.yaml; active in newProject template) | **GENERATED — pure** | all `fw/include/*` carry markers (IncludesFW + RegAddresses) |

### Exceptions and additional categories the two-group rule misses

- **`fw` is split — this is the sharpest exception.** `fwInc` (=`fw/include`)
  is a fileMap segment and is fully generated. But `fw/src` is **user-owned**
  firmware source (`debayer/fw/src/fwDebayerMain.{cpp,h}` carry **no** markers)
  and is **not a fileMap segment at all** — it has no `dirs`/`fileMap` entry.
  `migrateLayout.py` already treats hand-authored `fw` entry files with no block
  YAML as project-scope orphans routed to `prj/fw/` (lines 39, 375–377), distinct
  from generated `fwInc` files. The rule must classify `fw/include` (generated)
  and `fw/src` (user) separately; "fw = generated" is wrong.
- **`verif` is mixed, not "fully generated."** The `vl_wrap` **source**
  (wrappers) is generated, but the `verif` tree also holds Verilator/library
  **build output** (`obj_dir`, `libsimplevl_s_wrap.a`, …) *and* a user-managed
  `verif/vl_wrap/Makefile`. "Delete `verif` and regenerate" would lose the
  makefile — the same wrinkle as everywhere else (see Makefile section).
- **`arch/yaml` — authored-YAML INPUT (a fourth class).** This is the single
  source of truth, not "generated" and not a code "user-preserve" segment; it is
  never swept and never regenerated. Mapped by `functionalDirectories["yaml"] =
  "arch/yaml"` (`newProject.py:18`) and `hierarchicalDirs.yaml: yaml` (L102).
  `arch/yaml/*.yaml` carry no markers.
- **`include` (=`include/make`) — user-owned BUILD-CONFIG.** Holds `shared.mk`
  and stays at the project root even in hierarchical mode: L105 comment "build
  config stays at project root (user-owned, not under prj/)". No markers.
- **`rundir` and `.gen` — BUILD-OUTPUT.** Both are in
  `migrateCommon.SKIP_DIRS = ("build", ".gen", "obj_dir", ".git", "rundir")`
  (line 20) and are never walked. `.gen/build.mk` is generator-emitted
  ("Generated by arch2code projectCreate … Do not edit",
  `createBuildManifest.py:15`). `rundir` also contains a user `Makefile` harness.
- **`prj/` — generated orphan container (hierarchical only).** L103 + L91–93:
  the container for generated orphan artifacts under a hierarchical node.
- **"USER-PRESERVE" segments still contain generated regions.** `model`, `rtl`,
  `tb` files are **in-place generated**: they carry `GENERATED_CODE` regions the
  generator rewrites, wrapped around hand-written user code. Folder
  classification says "never delete these files," but it does **not** mean "the
  generator never touches them" — the in-place render still rewrites their
  generated regions. This is the tension the `.cpp/.h`→`.cppm` conversion lives
  in (see Implications).

### Refined rule (four classes, keyed on segment role)

1. **GENERATED-deletable** — `base`, `registrar`, `vl_wrap`, `fwInc`. Whole file
   is generator output; safe to delete and regenerate. (`verif` build-output and
   `.gen`/`rundir`/`obj_dir` are deletable **build-output**, a sub-case.)
2. **USER-PRESERVE (in-place)** — `model`, `rtl`, `tb`, and `fw/src`. Never
   delete; generated regions inside are still rewritten in place.
3. **INPUT (authored YAML)** — `arch/yaml`. Never delete, never regenerate,
   never swept.
4. **USER BUILD-CONFIG** — `include/` (`shared.mk`) and the per-segment
   `Makefile`s. Never delete (see open question on user-modified scaffolds).

## Makefile approach

### What "make templates embedded in generator code" refers to today

The investigation refines the architect's phrasing. There is **no makefile body
embedded in generator Python** — a grep across `builder` for the wrapper bodies
(`REPO_ROOT = …`, `a2c-rtl.mk`, `A2C_VL_WRAP_DIRS`, `EXTRA_O3_CPP_SRC`) finds
them only in the committed example trees, never in a `.py`. The actual picture:

- **Shared make logic** lives in static, committed infra:
  `builder/base/include/make/a2c-{common,rtl,systemc,vl-wrap,agents,docker}.mk`.
  The per-segment makefiles are thin wrappers that `include` these.
- **Per-project / per-segment wrapper makefiles** — the top `Makefile`, and
  `rtl/Makefile`, `rundir/Makefile`, `verif/vl_wrap/Makefile`, plus
  `include/make/shared.mk` — are **hand-committed** in each example
  (`git ls-files examples/simple` lists all of them) and are **not** produced by
  `newProject.py` or `newModule.py`. `newProject.py` creates only the
  `project.yaml` (from an embedded triple-quoted `projectTemplate` string) and
  the block directories; it never writes a makefile. A brand-new project has
  **no mechanism** to obtain its wrapper makefiles except copying an example.
- **The one generator-emitted makefile** is `.gen/build.mk`
  (`createBuildManifest.py`), a variable dump marked "Do not edit" — build output,
  not a user file.

So "embedded in code" most accurately describes: (a) the wrapper makefiles exist
only as example artifacts with no scaffolding path, and (b) the closest thing to
an embedded scaffold template is `newProject.py`'s `projectTemplate` string (for
`project.yaml`, not makefiles). Either way, makefiles are today a
**classification special case**: `migrateCommon.py:22–24` explicitly calls out
"A file outside `SOURCE_EXTS` (Makefile, .f filelist, .gitignore) is build
scaffolding the user manages, not generated source, and is left untouched."

### Proposal

Have `newmodule`/project scaffolding write **default / reference makefiles as
real files** — the thin wrapper bodies that examples commit by hand today (top
`Makefile`, `rtl/Makefile`, `rundir/Makefile`, `verif/vl_wrap/Makefile`,
`include/make/shared.mk`) — even though they contain **no** `GENERATED_CODE`
regions. The reference bodies already exist as the example wrappers; they become
the scaffold source ("ref versions").

**Benefit:** makefiles become ordinary scaffolded files under the USER
build-config class. The clean-start path can then delete a GENERATED-deletable
segment and have the scaffolder re-create the reference makefile
deterministically, instead of the sweep needing a Makefile-shaped special case
and instead of new projects having to copy makefiles from an example by hand.

**How a user-modified scaffolded makefile is treated — DECIDED (architect,
2026-07-22): scaffold-once, never touch.** `newmodule` writes each wrapper
makefile create-only; once present it is never overwritten and the user owns it
fully. Clean-start never deletes makefiles (they are USER build-config). This
matches `newModule`'s create-only stance, and because the shared make logic lives
in `include/make/a2c-*.mk` that the thin wrappers only `include`, the wrapper
bodies rarely need to change. The alternatives (managed header region + user
tail; checksum-against-reference divergence warning) were considered and NOT
chosen — they add machinery for a body that seldom changes.

## Implications for the migration tooling

- **Orphan sweep (③a / `migrateIncludes.py`) simplifies.** The stale-file
  partition (`_isGenerated` vs not, lines 124–125) becomes "does this candidate
  live in a GENERATED-deletable segment?" — a path lookup instead of a
  whole-file marker scan. The name-glob pre-filter plus `SOURCE_EXTS` walk
  narrowing can fold into the segment classifier. Marker-scanning can remain as a
  belt-and-suspenders assertion, but it is no longer the primary signal.
- **Delete-purely-generated clean-start becomes expressible.** "Delete every
  GENERATED-deletable segment (`base`, `registrar`, `vl_wrap`, `fwInc`) plus
  build-output (`.gen`, `rundir/build`, `obj_dir`), keep INPUT + USER-PRESERVE +
  BUILD-CONFIG, then regenerate" is a direct consequence of the class table —
  once makefiles are scaffolded files rather than a special case.
- **Tension with the `.cpp/.h`→`.cppm` conversion.** Folder classification puts
  `model`/`rtl`/`tb` in USER-PRESERVE ("never delete"), but the conversion
  **mutates those very files** — it must lift the user's hand-written regions out
  of the old-form `.h/.cpp`, delete/replace the file shape, and re-inject the
  user regions into the new `.cppm`. Folder classification answers "whose file is
  it" (the user's — preserve the content); it does **not** license leaving the
  file untouched. The conversion still needs the in-place region lift/re-inject
  machinery. Capture: **segment class = who owns the bytes; it does not mean the
  generator never rewrites the file.**

## Open Questions / Risks

- **Hierarchical vs functional keying.** The rule must key on the `dirs`/
  `hierarchicalDirs` segment role, resolved through the persisted `PROJECTLAYOUT`
  (the same contract `createBuildManifest.py` uses), so a segment classifies
  identically whether it sits at `$root/model` (functional) or `<node>/model`
  (hierarchical, `plan-decomp-functional-layout.md`). Risk: the flattened
  segments (`vl_wrap`→`verif`, `fwInc`→`fw`) and the project-scope dirs (`yaml`,
  `prj`, `rundir`, `include`) must be resolved via the layout config, not a raw
  path prefix match, or hierarchical `<node>/verif` vs functional
  `$root/verif/vl_wrap` will misclassify.
- **User-modified scaffolded makefiles. RESOLVED (2026-07-22): scaffold-once,
  never touch** (create-only, never overwritten, never swept). See Makefile
  section.
- **Frozen legacy-fileMap resource — storage form RESOLVED (2026-07-22): embed
  it directly in the migrate tools** (an embedded literal in the migration code,
  not a separate committed data file). Still open: whether the pro overlay is
  always present (a base-only product) or must be conditional; and whether more
  than one legacy format ever existed (if the legacy `dirs`/`fileMap` shape changed across the pre-migration
  history, a single frozen snapshot may not classify every project — decide
  whether one snapshot suffices or the resource needs a small version set). Also:
  confirm the current loader consumes the legacy map cleanly (no reliance on
  feature-branch-only fields like `hierarchicalDirs`/`mode: project`).
- **`fw` split resists a one-line rule.** `fw/include` (generated) and `fw/src`
  (user, not a fileMap segment) share a parent `fw/`. The classifier must
  descend to the segment, and `fw/src` must be recognized as USER-PRESERVE
  despite having no fileMap entry.
- **`verif` is mixed.** Generated wrapper source + Verilator build output + a
  user makefile under one tree. Clean-start must delete the generated + build
  parts while preserving/scaffolding the makefile.
- **Is `base` truly free of user content?** Evidence says yes (100% marker
  coverage in `simple/base`), and CLAUDE.md forbids editing generated regions;
  but the class rests on the invariant that nothing user-authored is ever placed
  in `base`/`registrar`/`vl_wrap`/`fwInc`. Worth a validator assertion.
- **Back-compat for existing projects.** Existing projects have **hand-authored**
  wrapper makefiles already committed. Introducing reference scaffolding must not
  clobber a project's customized makefile — scaffolding has to be create-only /
  divergence-aware, consistent with `newModule`'s existing create-only stance.

## Work Items

- **W0 — DONE. Capture + ANNOTATE the frozen legacy fileMap resource.** Snapshot
  `builder/base` `main` `config/project.yaml` (legacy base) and `builder` (a2cPro)
  `main` `config/project.yaml` (legacy pro) and EMBED them directly in the
  migrate tools (an embedded literal in the migration code — decided 2026-07-22,
  NOT a separate committed data file). Then ADD a per-entry `migrate:` disposition
  (`delete`/`port`/`leave`/extensible) to each fileMap entry — this is a
  migration-only field on our frozen copy, not on the live generator fileMap.
  Legacy is `functional`-only (no `hierarchicalDirs`). This annotated map is the
  migration dispatch table. Prerequisite for W1.
- **W1 — DONE. Disposition dispatch (replaces the segment-role classifier for
  migration).** Map each legacy file to the frozen-map entry that placed it and
  act on that entry's `migrate:` field (`delete`/`port`/`leave`). Add the rules
  for paths with no fileMap entry (`SKIP_DIRS` build-output; explicit
  `fw/src`→`port`) and condition `port` form-conversion on the CURRENT entry's
  emitted form (`.cpp/.h`→`.cppm` only for parameterizable blocks). ONGOING/
  current-project operations (clean-start on an already-current project) instead
  use the live `PROJECTLAYOUT` + merged `fileMap` segment roles, layout-agnostic.
  Lives beside `migrateCommon.py`.
- **W2 — DONE. `newmodule` reference-makefile scaffolding.** Scaffold the wrapper
  makefiles (top, `rtl/`, `rundir/`, `verif/vl_wrap/`, `include/make/shared.mk`)
  as create-only reference files sourced from the current example bodies.
  User-modification policy RESOLVED (scaffold-once, never touch), so clean-start
  simply never deletes makefiles.
- **W3 — DONE in the revised `migrateOrphans.py` pipeline. Rewire the orphan
  sweep (③a).** Replace the `_isGenerated` marker-scan
  partition in `migrateIncludes.py` (and the generated-vs-orphan decision in
  `migrateLayout.py`) with the W1 classifier; keep marker-scan as an optional
  assertion, not the primary signal.
- **W4 — OPEN / design only. Clean-start recovery target.** A "delete GENERATED-deletable +
  build-output, preserve the rest, regenerate" operation built on W1 (+ W2 so
  makefiles survive/re-scaffold).
</content>
