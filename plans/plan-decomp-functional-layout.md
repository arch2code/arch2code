# Plan: Project Layout Mode (`functional` / `hierarchical`)

## Status

- **State:** **L1 + L2a + L3 landed; L4 T4.1–T4.7 COMPLETE (2026-07-06):**
  T4.6's five Gap-1 follow-on items landed + verified, and the T4.6 sign-off is
  done — `examples/nested` converted to hierarchical in place (zero manual
  harness fixup) with a committed structural golden + guard test; L4 is finished
  pending the user committing the `nested` conversion. **UPDATE 2026-07-22 —
  L2b/C2 CLOSED/ACCEPTED and L5 full nested composition acceptance PASSED.**
  The composed SystemC paths/build, owner-aware cross-project RTL paths
  (`6bbec76`), and VL wrapper consumption of `A2C_VL_WRAP_DIRS` (`6113562`)
  landed; the previously-remaining L2b items are now all satisfied — explicit
  managed SV module file lists via the S6 explicit file->top records, active-
  project VL entry/source closure and standalone (S5), and cross-project clangd
  (S4) — and L5 is the acceptance vehicle and it PASSED. L5 ran the full matrix
  on the split `examples/ip_test` (`ip`/`ipBridge`/`common`) fixture under
  `make -j`: standalone `ip` (model+VL), standalone `ipBridge` (model+VL), and
  composed `ip_test` (model + VL-src/ip0/ip1) all report `No error`; evidence
  checks all PASS (provider override precedence with the `bridge/ip` symlink not
  dereferenced and 0 physical `bridge/ip/` leaks in the root manifest, N7
  distinct parent-qualified identities, N8 one-selected-child-file-set,
  standalone-vs-composed scope, no `vl_wrap` reintroduced); `common` is
  correctly a definitions/support project with no `run` target; no code gaps.
  Created 2026-06-29.
  - **L1 (mode-aware path composition)** — done: `fileGeneration.layout`
    selector, normalized layout-keyed config, mode-aware `dir` derivation and
    seam join order; `functional` output byte-identical across all `examples/`
    (regression gate green), `hierarchical` green-field fixture matches the
    committed structural golden.
  - **L2a (single-project hierarchical build, ungated)** — done (T2a.1–T2a.4):
    `projectCreate.buildManifest` emits `.gen/build.mk`; rundir makefiles consume
    it (fixed-root globs deleted); the green-field fixture
    (`unittest/fixtures/hier-layout/`) builds and runs its block-level tb to clean
    end-of-test from its own `rundir/`, and `make clangd`/`compdb` cover its
    source set. Functional examples unaffected (byte-identical gate green).
  - **L3 (registrar reconcile)** — done: `plan-reusable-ip-registrar.md`
    records the decided `hierarchical` axis (header "UNBLOCKED 2026-06-30").
    L3 settles *where* parent-owned registrar/config artifacts sit. Architect
    reconciliation 2026-07-20 splits S3 by emission form: the independent
    S3-H checkpoint (LANDED, committed 2026-07-21) emits an owner-qualified
    Config header beside the registrar;
    the later S3-M registrar-module export remains coupled to S6/S5 and gated on
    composition **M-split** (distinct `projectName`s — the load-bearing
    invariant). "Layout-unblocked" ≠ "composition-ungated"; see
    [`plan-composition-ordering.md`](./plan-composition-ordering.md).
  - **L4 (opt-in migration)** — design done; residuals resolved (Q-L4a separate
    `--to-hierarchical` invocation; Q-L4b no synthesized node). **T4.1 (trigger +
    idempotence) done:** `pysrc/migrateLayout.py` + `migrateYaml.py
    --to-hierarchical` + `make migrate-hierarchical`, three-state classifier,
    stamp untouched, `test_migrate_layout.py`. **T4.2 (relocation map) done
    (2026-06-30):** `migrateLayout._buildRelocationMap` attaches a `moves`/`deletes`
    map (authored-YAML decomp→`<node>/yaml/`, project file→`prj/yaml/`, build
    config→`prj/include/`, orphans→`prj/{verif,fw}`, marker-guarded generated
    deletes) to the report; `renderLayoutReport` prints it; DRY-RUN only (no
    writes). Verified on temp copies of `nested` + `hierInclude` and a synthetic
    orphan fixture; live trees + non-layout migrate path unchanged. **T4.3 (apply
    relocation) done (2026-06-30):** `migrateLayout._applyRelocationMap` executes
    the map under `write=True` (marker-guarded deletes, byte-preserving
    `shutil.move` with a no-overwrite guard, only-if-empty dir prune); the layout
    flip is a no-op precondition (a candidate already declares hierarchical), so
    no selector edit is written; `renderLayoutReport` prints `APPLIED` under
    `--write`. Acceptance met on temp copies of `hierInclude` (green-field shape)
    + the synthetic orphan/guard fixture, idempotent re-run, live trees
    untouched. **T4.4 (relative-path re-rooting + fileMap-driven classification)
    done (2026-06-30):** file classification now uses the merged fileMap
    (`processYaml.mergeProjectConfig`, the create-time base/pro/user merge,
    factored out of `projectCreate.__init__` as the shared seam): a recognized
    fully-generated file type (`blockBase`, `blockRegistrar`, `include`, `config`,
    `package`, `vlSvWrap`, `vlSvWrapBody`, `vlScWrap`) is deleted+recreated, every
    other/unrecognized source MOVES byte-preserving to `<node>/<hierarchicalDir>/`
    (node from the authored-YAML decomposition, stripping any blockDir level), so
    user content is never lost. After apply, `include:`/`projectFiles:` entries
    and user-region source includes are re-rooted through the new levels via
    `yaml.compose` byte-offset splices (comments/quoting preserved); a reference
    resolving outside the migrated tree — or an authored YAML pulled in from
    outside the root — is reported `TODO_UNREWRITABLE_PATH`, never mangled.
    Covered by `test_migrate_layout.py` (hierInclude include/projectFiles re-root
    + module-`.sv` move + package delete, synthetic classification/orphan fixture,
    user-region source rewrite, escaping-include report, byte-preservation,
    idempotence); `nested`/hierInclude create+gen byte-identical after the
    `mergeProjectConfig` refactor; live trees + non-layout migrate path unchanged.
  - **L4 T4.5 (report + wiring)** — done (2026-07-06): `LayoutReport`
    dataclass (`migrateLayout.py`), `renderLayoutReport` +
    `--to-hierarchical` arg (`migrateYaml.py`), `make migrate-hierarchical`
    target (`a2c-common.mk`); the invocation returns before the unconditional
    phases so it stays out of `stampEligible`. Verified by
    `test_migrate_layout.py` (green).
  - **L4 T4.7 (skill doc)** — done (2026-07-06): `rules/skills/migrate-project.md`
    gained a "(Opt-in) Migrate to hierarchical layout" section (command,
    classifier states, move/delete map, the three manual-TODO codes, and the
    `make clean && make newmodule && make gen` finish step).
  - **L4 T4.6 (validation)** — validated end-to-end on `nested` (builds/runs to
    "No error" after migrate → harness fixup → `newmodule` → `gen` → `run`);
    experiment reverted. **Gap 1 resolved (2026-07-06):** leave `include/` (and
    `rundir/`) at the project root — the `prj/include/` move was tidiness-only
    and caused the entire harness-breakage class; `prj/` now holds only
    generated project-scope orphans + the project file. Residual harness edit
    is a single deterministic `A2C_PRJ_YAML` line. Gap 2 (`newmodule` before
    `gen`) is documented. **All five follow-on code/fixture items landed +
    verified (2026-07-06)** — migrateLayout `include/`-stays + auto `A2C_PRJ_YAML`
    re-point, config `include` convention, fixture + golden, skill note; the
    in-place `nested` re-validation builds/runs to "No error" with zero manual
    harness fixup (see T4.6).
  - **Remaining:** L4 COMPLETE. **UPDATE 2026-07-22 — L2b/C2 CLOSED/ACCEPTED
    and L5 PASSED/ACCEPTED** (full nested composition acceptance on the split
    `ip_test` fixture; see the State note above). Nothing remains in this
    milestone set.
  The layout-axis pause on
  [`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md) is
  **resolved**: `hierarchical` is settled and S2/S3.2a shipped the interim
  registrar layout. S3-H is LANDED (committed 2026-07-21); registrar S3-M/S6/S5
  remain gated for the separate reason of composition **M-split** (distinct
  `projectName`s). **UPDATE 2026-07-22 —** L2b composition C2 work is now closed
  and L5 (the full split `ip_test` fixture, also the composition C5 acceptance
  vehicle) PASSED. Ordering across the workstream plans
  lives in
  [`plan-composition-ordering.md`](./plan-composition-ordering.md).
- **Origin:** 2026-06-29 working session. While working the reusable-IP
  registrar plan the user observed that the current root layout is
  **`functional`** (functional roots `arch/ model/ rtl/ base/ ...`
  with the yaml decomposition mirrored inside each), which suits a
  top-down project but obstructs the multi-project nested/embedded-IP
  scenario the reuse work targets. The user's direction: **both
  arrangements must be supported**, expressed through the `dirs:` /
  `fileMap` mechanism.

## The Two Arrangements

A generated file's directory is the composition of two axes:

- **Functional axis** — the kind of artifact (`model`, `rtl`, `base`,
  `registrar`, `verif/vl_wrap`, `tb`, `fw/include`). Today this is a
  `dirs:` key referenced by each `fileMap` entry's `basePath`.
- **Decomposition axis** — the block's position in the architecture
  hierarchy, derived from the directory of the block's defining YAML
  (the context/`yamlDir`). Examples in `ip_test`: `ip`, `src`, `bridge`,
  `top`, `common`.

**`functional` (today).** Functional axis is outer, decomposition
axis is inner:

```
$root/model/ip/ip.cpp
$root/rtl/ip/ip.sv
$root/base/ip/ipBase.h
$root/registrar/top/ipRegistrar.cpp
$root/fw/include/ip/ipIncludesFW.h
```

**`hierarchical` (proposed).** Decomposition axis is outer,
functional axis is inner — every artifact for one block sits under one
subtree:

```
$root/ip/model/ip.cpp
$root/ip/rtl/ip.sv
$root/ip/base/ipBase.h
$root/top/registrar/ipRegistrar.cpp
$root/ip/fw/include/ipIncludesFW.h
```

## Why This Matters (the finding that prompted the plan)

The two in-flight plans have **already diverged** on this axis, and the
divergence is load-bearing, not cosmetic:

- **The composition plan is implicitly `hierarchical` at the IP
  boundary.** A standalone IP project is drawn as a decomposition node
  holding every functional directory
  (`ip/ arch/ base/ model/ rtl/ tb/ rundir/`,
  [`plan-ip-project-composition.md`](./plan-ip-project-composition.md)
  lines 105–118); a nested child is embedded as a contiguous subtree
  (`src/ipLeaf/{arch,base,model,rtl,tb}`, lines 89–97); and the registrar
  is drawn **under** the IP node (`src/registrar/`, `ip_top/registrar/`,
  `ipBridge/registrar/`).
- **The registrar plan and the landed S2 work use the `functional`
  layout.** S2 placed the registrar at
  `registrar/<assembler-yaml-dir>/<child>Registrar.cpp`,
  "mirroring the yaml dir tree the way `base/` does"; the on-disk result
  is `registrar/{bridge,top,src}`.

So the same artifact — the registrar — is `<assembler>/registrar/` in one
plan and `registrar/<assembler>/` in the other. They cannot both be the
target. Two consequences force a decision now:

- **The nested-child case forces a hybrid tree under `functional`.**
  If intra-project layout stays `functional` but the composition plan
  embeds `ipLeaf/` as a `hierarchical` subtree inside `src/`, a
  single tree carries both conventions at once (`src/model/...` beside
  `src/ipLeaf/model/...`). The only escapes are to make the layout
  uniform or to forbid in-tree nesting (external siblings only).
- **The `hierarchical` mode erases the block-to-IP seam.** The registrar
  plan's principle is "no special-casing of top vs IP vs leaf; ownership
  follows instantiation at every level." A `hierarchical` subtree
  gives that a structural counterpart: an in-project block and a
  referenced standalone IP become structurally identical, so promoting a
  block to a reusable IP is a directory move, not a scatter-gather
  refactor across seven functional roots. This is the user's "directly
  and simply embedded."

## Embedding Asymmetry (decided 2026-06-29)

A referenced child project occupies **one contiguous subtree** — it has
its own `$root` holding all its functional directories. This makes
embedding asymmetric:

- **A `hierarchical` parent can embed any child in-tree.** It already
  organizes its space as one subtree per node, so a child project slots in
  as another node subtree (`$root/<child>/...`); the child's internal
  layout is self-contained and invisible to the parent.
- **A `functional` parent cannot embed in-tree.** It organizes its space
  as one subtree per function with blocks scattered inside, so there is no
  node-subtree slot for a self-contained child project. A `functional`
  parent therefore references children only as **external siblings**, not
  nested.

Rule: **in-tree nesting requires the parent to be `hierarchical`.**
Each project file declares its own mode and owns its subtree; nesting only
changes where the child's `$root` resolves.

## Mode Names (decided 2026-06-29)

The project file selects the layout via `fileGeneration.layout:`, whose
value names the outer/major axis:

- **`functional`** (default; today's behavior) — functional axis outer,
  decomposition axis inner (`$root/model/ip/...`). A `functional` project
  references children only as external siblings (see Embedding
  Asymmetry).
- **`hierarchical`** — decomposition axis outer, functional axis inner
  (`$root/ip/model/...`). A `hierarchical` project can embed child
  projects in-tree as node subtrees.

Chosen for native fit with the project's existing vocabulary:
`config/project.yaml` already calls `dirs:`/`fileGeneration:` the
"functional layout" and states the tree "mirrors the architecture
hierarchy."

**The two modes are not co-equal capabilities.** `functional` is kept for
**back-compat and no-regression** — it is the only mode existing projects
(and the live `debayer` tree) use today, and it cannot embed children
in-tree (Embedding Asymmetry). `hierarchical` is the **strategic target**:
it is the *only* mode that delivers the reuse/composition goal that
motivates this plan, so realizing the benefit on any existing project
requires migrating it to `hierarchical` (Q-L4). Read "both modes
supported" as "functional retained as legacy, hierarchical is where the
work is heading," not as two interchangeable options.

## Worked Example: Self-Contained Nested IP (`ipLeaf` in `src`)

The load-bearing case is a **complete, standalone-buildable IP project
nested inside a parent**. It exercises every nesting concern at once, so
the layout is designed against it rather than against the flat single
project. `ipLeaf` is the chosen vehicle: it has its own parameter
(`LEAF_DATA_WIDTH`, default 4), its own type/struct, a private no-FW
memory (`ipLeafMem`), no children of its own, and it is instantiated only
by `src` at `variantLeaf0` with `LEAF_DATA_WIDTH = OUT0_DATA_WIDTH`
(parent parameter bound to child parameter). It is therefore both fully
reusable and the deepest nesting in `ip_test`
(`ip_top` → `src` → `ipLeaf`).

### Addressing in `hierarchical` mode — no node naming

The generator does **not** name or derive a "node" in `hierarchical` mode.
The **user provides the directory structure**, nesting directories however
they wish and placing each block's YAML in a **`yaml/` subdirectory** of
the node (where `yaml` is the authored-segment name from `dirs:`, not a
hard-coded literal). The **directory that contains the `yaml/` subdir *is*
that block's node** — derived from the parsed YAML file's own location
(`yamlDir`, `processYaml.py:4805`), not from a scan — and the generator's
only job is to **create the functional directories** (`model/`, `rtl/`,
`base/`, `fw/`, `tb/`, `registrar/`, `verif/`) as siblings of `yaml/`.

Consequences:

- **No central `arch/yaml/` tree and no generator-assigned node name.**
  Authored YAML lives in `<node>/yaml/`; the generated functional dirs sit
  beside it. Path composition is
  `<node> / <funcSegment> / <file>`, where `<node>` is the parent of the
  `yaml/` directory of the parsed block YAML (the file the project pulled
  in via `projectFiles:`/`include:`).
- **Granularity and grouping are pure authoring choices.** Putting two
  blocks' YAML in one `yaml/` groups them in one node; giving a block its
  own `<dir>/yaml/` makes it independently embeddable. The generator
  imposes nothing.
- **A node is not a project — and neither is found by scanning.** A
  **node** (decomposition) is the directory a parsed block-YAML file sits
  in (its `yamlDir`); the generator anchors that block's functional dirs
  there. A **project** (a unique, independently-buildable thing) is
  whatever a **project file** names. Both are resolved from
  **references and parsed file locations, never from directory-name
  scanning** (see "The `prj/` directory" below). Node identity comes from
  the YAML the project file already pulled in via `projectFiles:` /
  `include:`; project identity comes from the project-file **path** handed
  to the build or named by a parent.
- **A nested child project is just a referenced project whose root
  resolves inside the parent tree.** The parent names the child by path in
  `projectFiles:`; the child's own `dirs.root` (relative to the child
  project file) puts its artifacts under `<parent>/<child>/...`. Embedding
  is a path, not a marker — nothing else changes.

### The `prj/` directory — referenced container, abstracted name

`prj/` is **not a discovery token**; nothing globs for it. Its whole role
is to be the **container for the project root's own artifacts** — the
things that belong to the project as a whole rather than to any one block.
Two properties, both already true of the code today:

- **The project is referenced by its project-file path, not discovered.**
  The build is handed the path to the project file (today `A2C_PRJ_YAML`);
  a parent names a child by path in `projectFiles:`. The parser `chdir`s to
  the project file's directory and resolves `dirs.root` **relative to that
  file** (`processYaml.py:2987–2988`, `:3062` — *"relative to project
  file"*). So the **project root is derived from the project-file path**.
  No marker directory is scanned to find a project; the only input is the
  path you already supply.
- **The container name is abstracted into `dirs:`.** `prj` is a **`dirs:`
  segment** (a `$prj` macro, by convention `$root/prj`, overridable), the
  same kind of entry as `model`/`base`. The project-scope artifacts that
  have no block YAML — `fwIpMain`, `sc_main`, the `vl_wrap` aggregator,
  build `include/`, and the project file itself — are emitted there by
  anchoring their `basePath` on `$prj` instead of `$root/<funcSegment>`.
  Rename the segment in config and nothing else cares; the literal string
  `prj` appears in **no** discovery or build glob.

Consequences of being reference-based (this supersedes the earlier
name-heuristic framing):

- **No reserved-name hazard for projects.** Because a project is located
  by the path you pass, no directory name is magic for *finding* it; the
  container may be named anything (`prj` is just the default `dirs:` value).
- **Authored vs generated segments are config names, not scan tokens.**
  The authored-YAML segment (`yaml`) and the functional segments
  (`model rtl base fw tb registrar verif`) are explicit entries in the
  selected layout's directory set. They describe *where the generator
  writes*, and never drive project discovery.
- **Directories are derived; files within them may be searched.** The
  *directory tree* is not discovered — node dirs come from the
  `projectFiles:`/`include:` tree and functional dirs from the segment
  list, so `projectCreate` knows every directory by derivation (no
  dir-finding glob like today's `find_cpp_source_directories`). *Within* a
  known directory, files **may** still be searched (`wildcard $(dir)/*.cpp`),
  because a dir can hold **user-authored / user-templated files beyond the
  generated "known files"** that the generator does not track. The rule is
  therefore **directory list from YAML, files found by search within it**.
  The authored *YAML* input set is the one thing needing no search at all —
  it is the include-tree closure (derived) and is what triggers DB rebuild,
  replacing `YAML_FILES = $(shell find …)`.

### Standalone `ipLeaf` project (built alone)

```
ipLeaf/                              project root (has prj/)
  rundir/                            ← run `make` here (first place people go)
  prj/   yaml/    ipLeafProject.yaml      ← project file (projectName: ipLeaf;
         include/ make/shared.mk            layout: hierarchical; topInstance: ipLeaf_tb)
         verif/   sc_main.cpp               ← verilated simulation entry (per-build)
  yaml/    ipLeaf.yaml  ipLeaf_tb.yaml    ← user-authored YAML (block + block-level tb)
  base/    ipLeafBase.cppm               ┐ (Base promoted to a module — B6)
  model/   ipLeaf.cppm  ...              │ generator-created functional dirs,
  rtl/     ipLeaf.sv  ipLeaf_package.sv  │ siblings of yaml/
  fw/      ipLeafIncludesFW.{h,cpp}      │ (types only; ipLeafMem has no FW access)
  tb/      ipLeaf/ipLeafTestbench.{h,cpp}┘ (block-level tb; tb config self-registers)
  registrar/  ipLeafRegistrar.cppm         ← module: EXPORTS ipLeaf's default Config;
                                            registration static (not exported)
```

`ipLeaf/` is a **project** (it has a `prj/`, so it builds standalone) and
also the single block node (its `yaml/` is at the root). `rundir/` sits at
the project root (the first place people go); the project file, build
config (`include/`), and verilated `sc_main` live under `prj/`; the block
YAML in `yaml/`; the generator created the functional dirs beside it. The
`registrar/` holds **ipLeaf's own default config** and registers it, so
ipLeaf is instantiable standalone (and its block-level tb runnable).

### Canonical `ip_test` project tree

The earlier `ipLeaf` tree remains a useful generic layout example, but the
composition acceptance fixture is now focused on three logical projects:
`ip_test` (root), `ip` (reusable leaf), and `ipBridge` (reusable assembler).
`src` and `ipLeaf` remain root-owned nodes for this milestone.

```
ip_test/                              PROJECT: ip_test
  rundir/
  prj/yaml/ip_testProject.yaml        references ./ip and ./bridge
  top/ ...                            root integration + root-owned registrars
  src/ ...                            root-owned node (contains ipLeaf)
  common/ ...                         root-local Option-D boundary definitions

  ip/                                 PROJECT: ip; canonical provider
    rundir/  prj/yaml/ipProject.yaml
    yaml/ ...  base/ model/ rtl/ fw/ tb/ verif/ registrar/

  bridge/                             PROJECT: ipBridge
    rundir/  prj/yaml/ipBridgeProject.yaml
    yaml/ ...  base/ model/ rtl/ fw/ tb/ verif/ registrar/
    common/ ...                       bridge-local Option-D boundary definitions
    ip -> ../ip                       provider-location symlink
```

Bridge standalone selects `bridge/ip`; root composition selects root `ip`, and
the root override supersedes the bridge override. The symlink models a vendored
Git submodule without copying the fixture's source. Provider normalization must
preserve the authored path rather than dereference the symlink.

Root-owned `top/registrar/ipRegistrar.cppm` and
bridge-owned `bridge/registrar/ipRegistrar.cppm` coexist because registrations
use distinct assembling `projectName` keys. The child `ip` implementation and
default standalone registrar remain owned by logical project `ip`. Each
project's `rundir/`, build config, generated source roots, and fake harness are
active only when that project is the build root.

### Nested Issues (the checklist this example must resolve)

Several are owned by the composition plan; listed here as the
**directory-structure expression** each one takes, with cross-references.

- **N1 — Child `$root` resolution.** `ipLeaf`'s `dirs.root` resolves
  relative to its project file `src/ipLeaf/prj/yaml/ipLeafProject.yaml`, so
  all child artifacts sit under `src/ipLeaf/`. The parent does not re-root
  the child (composition Q-C1).
- **N2 — Per-project layout mode.** `ipLeaf`'s own project file declares
  its `layout:`; the parent never imposes one. The parent project
  (`ip_test`) must be `hierarchical` to embed the child in-tree; a
  `functional` parent could only reference `ipLeaf` as an external sibling
  (Embedding Asymmetry, Q-L1).
- **N3 — Config stays in the parent registrar domain; emission form is
  staged.** Ownership and placement do not depend on whether Config is a header
  or module export. The S3-H checkpoint emits each foreign consumer-selected
  Config as an owner-qualified plain header beside the consumer node's
  registrar (`src/registrar/` binds `ipLeaf@variantLeaf0`), included by the
  parent container and SC registrar; the generic `ipLeaf` implementation has no
  outward dependency. The S3-M target folds that adjacent header in place into a
  DEDICATED config module per `(owningProject, child)` at the same location; the
  parent registrar module(s) and container `import` that one unit (registration
  remains a non-exported static). This is the canonical-declaration-unit decision
  (architect 2026-07-20, Option A): a single module-attached entity per
  `(projectName, block, variant)` keeps the `dynamic_pointer_cast` valid, and
  config leaves the `-I` surface (B6). The config is its own module rather than
  being folded into `<child>Registrar.cppm`, since the Config is shared by all
  same-project parents and must not be re-exported through an elected primary
  parent. Child-owned defaults and same-project canonical variants retain their
  existing context header until their own module-form migration. The types
  coexist under distinct `(block, variant, projectName)` keys (registrar plan S3;
  composition Q-C4/Q-C10).
- **N4 — Run scope, not compile exclusion.** A child's `tb/`, driver/`cpu`,
  and default `registrar/` are **not excluded** from a parent build — they
  self-register into the tb/instance factories and become **selectable by
  name** through the shared `sc_main`. What differs per run is which tb /
  `topInstance` is selected (and thus which instances/addresses are
  enumerated), a runtime choice, not a compile-time exclusion
  (composition Q-C5). A child's block-level tb stays runnable even when the
  child is embedded.
- **N5 — Build discovery of nested dirs.** The parent build compiles and
  `-I`s the child's functional dirs (`model/ rtl/ base/ fw/`, and `tb/` +
  `registrar/` to keep the block-level tb available). The one
  per-build-unique thing is the **verilated** entry — exactly one project
  `verif/.../sc_main.cpp` and one `vl_wrap` aggregator (the active
  project's). The DB-emitted manifest enumerates the set from parsed facts
  (Q-L2; composition Q-C3).
- **N6 — YAML reference + full parse + cross-project eval.** `ip_test`
  references the `ipLeaf` project via `projectFiles` (its project file),
  parses the child YAML fully, and must resolve `LEAF_DATA_WIDTH =
  OUT0_DATA_WIDTH` across the boundary to the same value as monolithic
  (composition Q-C12). Relative cross-node includes re-root through the
  `yaml/` level.
- **N7 — Naming / namespace / include collisions.** Same basenames in
  different directories are allowed; the hazard is a **language-visible
  identity** collision (C++ module name, exported namespace/type/config name,
  SV package name, residual header include spelling, or build PCM/object target
  name), not the filename itself. Child-owned reusable artifacts qualify by
  the child's `projectName`, so the child's module names and include spelling
  are identical standalone and nested. Parent-scoped artifact identities
  (registrar modules, Config-header basenames, verilated registrar TUs, build
  targets) qualify by owning `projectName` + persisted parent/assembler context
  + child block + artifact kind. The Config **type** follows the separate
  canonicality invariant `(projectName, block, variant)`: two assemblers in one
  project consuming the same variant share one type and point to the one
  declaration-owning header. Do **not** derive either identity from raw
  filesystem nesting; use the same persisted ownership/context facts that drive
  registrar emission. This
  lets `top/registrar/ipRegistrar.cppm` and `bridge/registrar/ipRegistrar.cppm`
  coexist even though they share a basename (B6/B7; composition Q-C8).
- **N8 — Generation ownership boundary; location ≠ owner.** The `src`
  node's functional dirs are owned and regenerated by `ip_test`;
  `src/ipLeaf/*` regenerates only under the `ipLeaf` project; `ip_test`
  skips child-owned objects but keeps the cross-boundary registrar it owns
  in the `src` node (composition Q-C9). **Critical inversion vs
  `functional`:** in `functional` a functional root maps cleanly to one
  owner, so directory location *implies* the owner. In `hierarchical` that
  no longer holds — `src/registrar/ipLeafRegistrar.cppm` is owned by
  `ip_test` while `src/ipLeaf/` two levels away is owned by the `ipLeaf`
  project, and both sit inside the same `src/` subtree. Ownership is
  determined by **which project's parse reached the object** (the
  per-context owning-project tag, composition Q-C9), **not** by where the
  file lands. Any "regenerate this directory" logic that keys on path
  instead of the ownership tag will clobber child-owned files; this is the
  most likely source of cross-project generation bugs and must be tested by
  the L5 fixture.
- **N9 — Address-space composition.** `ipLeaf`'s private memory composes
  under `src`'s (and thence `top`'s) decode hierarchy; the child's tb
  registers are excluded by reachability (composition Q-C5).

### Choices resolved by this example

- **Project vs node + orphans' home — DECIDED.** A **project** is the
  thing a **project file** names; it is located by the project-file
  **path** the build/parent supplies, and its root is `dirs.root` resolved
  relative to that file (not by scanning for a marker). A **node** is the
  directory a parsed block-YAML file sits in (decomposition only). The
  **`prj/` container** holds the project file plus the project's
  integration artifacts with no block YAML — `fwIpMain`, the `vl_wrap`
  aggregator, `sc_main`, build `include/` — anchored on the abstracted
  `$prj` `dirs:` segment (`prj/fw/`, `prj/verif/`, `prj/include/`,
  `prj/yaml/<name>Project.yaml`). The container name is config, not a
  discovery token (see "The `prj/` directory"). Only independently-built
  roots carry a project file; ordinary nodes do not. In the canonical example
  the projects are `ip_test` (root), `ip` (reusable leaf), and `ipBridge`
  (reusable assembler); `bridge/ip` is a provider-location symlink, not a
  fourth logical project. `common`, `src`, and `top` remain plain nodes (Q-L3).
> **Scope note (ownership).** The next two items are **module-emission
> decisions, not layout-axis decisions**. They are **owned by**
> [`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md)
> (its M3/T6 block-class promotion and S3 config relocation) and are
> **adopted here, not decided here**, only because the worked example must
> show concrete file extensions. If the registrar plan changes the
> emission form, this section follows it — the single authoritative record
> of the `ext` flips lives in that plan's Generator Surface, not in two
> places. They are restated here for the directory picture; do not treat
> this plan as their decision site.

- **Base promoted to a module — ADOPTED from registrar plan M3/T6.**
  `<child>Base` is emitted as a module unit (`<child>Base.cppm`), so the
  parent container imports the owner-qualified boundary
  (`import <projectName>_<child>_base;`) instead of
  `#include "<child>Base.h"`. The cross-project boundary becomes the **Base
  module + the parent-owned Config**, fully off the `-I` search path
  (dissolves the C++ part of B6). The `blockBase` fileMap flips `ext` from
  `h` to `cppm`. **Emission form is whole-project, not per-artifact:** the
  modules build (clang) emits block class, types, and Base all as modules —
  there is no header to fall back to; a toolchain that cannot consume
  SystemC modules (gcc-13) instead emits the *entire* C++ surface
  header-visible (registrar mechanism (b)), consistently. There is no
  "Base-as-header inside a modules build" state. (Decision owned by the
  registrar plan; this plan only requires that *whatever* boundary form it
  picks is import-by-module-name so the `-I` shadowing in B6 dissolves.)
- **Variant Config in the registrar domain — staged target from registrar plan
  S3 — S3-H LANDED (committed 2026-07-21), S3-M not yet landed.** S3-H first emits an owner-qualified plain header beside
  the parent registrar, preserving one textual type at the container and SC
  factory sites without making the child include outward. After composition
  M-split unlocks S3-M, the registrar
  (`<child>Registrar.cppm`) **exports** the per-variant Config
  struct(s); the container `import`s the registrar module to obtain the
  Config it casts to (`<child>Base<Config>`), instead of
  `#include "<child>VariantConfig.h"`. This removes the config header from
  the `-I` surface (B6). Because this is a **parent-owned** artifact, the
  registrar module and exported Config namespace/name are parent-qualified
  (owning project + parent/assembler context + child + artifact kind), not
  merely child- or file-stem-qualified. The **registration trampoline is
  *not* exported** — `registerBlock(...)` is a link-time static initializer
  (Option-δ retain + direct-`.o`); nothing imports it, so it stays
  module-internal. The registrar module **privately `import`s** the child
  implementation (`<child>.block`) to instantiate `<child><Config>` but does
  **not** re-export it, so a container importing the registrar sees the
  Config and not the implementation — preserving the encapsulation boundary.
  The `blockRegistrar` fileMap flips `ext` `cpp`→`cppm`. S3-H and S3-M are
  decisions owned by the registrar plan; they are restated here only for the
  directory picture.
- **Node naming and granularity — moot.** With no generator-assigned node
  name, directory names and grouping are entirely the user's authoring
  choice (which `<dir>/yaml/` they place a block in). The example's names
  (`ipLeaf`, `src`, `ip`, `bridge`, `top`) and its grouping of non-IP
  helpers (`apbDecode`, `cpu`, `bridgeDriver`) with their assembler are
  illustrative, not generator policy.

## Build Model and Issues

Per-project `rundir/` (at the project root) and `prj/include/` make each
project independently buildable; nesting several projects in one tree
creates build hazards that must be designed for. The organizing idea is the
**active project** — the one whose `rundir/` you build in — but note (from
the verified mechanism below) that this is mostly about *runtime selection
and the verilated entry*, not blanket compile-time exclusion.

### Verified mechanism — one shared model main, many tbs by name

The model binary's entry is the **shared** `common/scmain/main.cpp`, not a
per-project main. Every compiled testbench/config self-registers into
`testBenchConfigFactory` (e.g. `ip_topConfig`, `ipConfig`), and `sc_main`
selects one **by name at runtime** (`createTestBench(testBenchName)`).
Consequences:

- **Block-level tbs are available.** A child's tb compiled into a parent
  build simply registers and becomes runnable by name — there is **no
  duplicate `main()`** on the model path and no reason to exclude it.
- **Default + consumer configs coexist.** An IP's own default (its
  `registrar/`) and the consumer-selected variants (consumer-node
  `registrar/`) all register under distinct `(block, variant, projectName)`
  keys and are selected at runtime.
- **The per-build-unique artifact is the verilated entry** — the project
  `verif/.../sc_main.cpp` (a real `sc_main`) plus the `vl_wrap` aggregator.
  Exactly one of these belongs in a binary: the active project's.

### What "active project" actually governs

- The active project's **Verilator build directory/library and managed top
  set** (plus a real Verilated `sc_main` if that separate entry is retained).
  S6 retires the `vl_wrap.h/.cpp` C++ registration aggregator.
- The integration **firmware** main (`fwIpMain`) and the default run
  selection (`topInstance` / address-map root).
- The `rundir/` you build in and the `prj/include/` build config that
  governs flags/toolchain.
- It does **not** require excluding child `tb/`/`registrar/` from the model
  build; those are compiled and runtime-selected.

### `verif/` has two distinct roles — read this once

`verif` is both a per-node functional segment *and* a `prj/` segment, so it
appears at two levels with different contents. To avoid conflation across
N5/B10/Q-L3:

- **`<node>/verif/`** (per-node, decomposed) — the per-block verilated
  wrappers (`vl_wrap` per-block units), decomposed to their owning node by
  registrar S6. There is one per node that has verilated blocks; all of
  them are compiled into a composed build.
- **`prj/verif/`** (per-project, one active) — the project-wide Verilator build
  directory/library and explicit managed-top records, plus a real Verilated
  `sc_main` if retained by that flow. S6 retires `vl_wrap.h/.cpp`; registration
  lives in guarded parent `registrar/*VlRegistrar.cpp` files. Exactly one
  project's Verilator build output is linked per binary — the active project's.
  This is the single real exclusion the manifest encodes (B1/B10).

Same split applies to `fw`: per-node `<node>/fw/` holds generated FW
headers; `prj/fw/` holds the integration `fwIpMain` (the project orphan).

### The directory tree is derived; files are found within it

Principle: **the build does not discover the directory structure — it
derives it — but it does search for files within the derived directories.**
The split matters because a directory can hold user-authored or
user-templated files the generator never emitted and does not track.

- **Directories come from YAML, by derivation.** Node dirs are the
  locations in the `projectFiles:`/`include:` tree; functional dirs are
  those nodes crossed with the segment list. `projectCreate` therefore
  knows every source / include / registrar directory by composition —
  replacing today's *directory* search (`find_cpp_source_directories`) and
  the fixed functional-root globs (`PRJ_SRC_DIRS`, `SC_GEN_FILES`).
- **Files within a directory are found by search.** Within each known dir
  the build still globs `*.cpp` / `*.sv` (e.g. `wildcard $(dir)/*.cpp`), so
  **user files beyond the generated "known files" are picked up**. This is
  search **scoped to derived dirs**, not discovery of the tree.
- **The directory list (and the rest of the build tree) is a generated
  output.** `projectCreate` emits a `.mk` enumerating, for the active
  project and every referenced child: the source / include / registrar
  dirs, the module set, the project-file path, and the single active
  verilated entry. The `rundir/` Makefile **includes** it and wildcards
  files within each listed dir. The same generated facts feed clangd
  (composition Q-C3).
- **YAML inputs need no search.** The DB-rebuild dependency list is the
  include-tree closure (derived), replacing `YAML_FILES = $(shell find …)`.

So what is removed is the *directory* discovery (`find_cpp_source_directories`,
the fixed `PRJ_SRC_DIRS`/`SC_GEN_FILES` roots, the hard-coded `vl_wrap.cpp`
line) — replaced by the derived dir list — while the **per-dir file
wildcard stays**. This is nesting-depth agnostic and encodes the one real
exclusion (pick a single verilated entry). The literal directory names
(`prj`, `model`, …) live only in the generator's `dirs:` config, never in a
build-time *tree* search.

### Build issues (the checklist this model must resolve)

- **B1 — Verilated `sc_main` / `vl_wrap` is per-build-unique.** The model
  main is shared a2c (no duplicate-main hazard), but the verilated
  `verif/.../sc_main.cpp` and the `vl_wrap` aggregator are per-project; a
  composed build must pick exactly the active project's. (Folds with B10.)
- **B2 — Registration coexistence, not leakage.** Compiling child tbs and
  default-config registrars is fine: they self-register and are selected by
  name. The requirement is unique keys (`projectName` dimension) so
  same-named registrations do not collide (composition Q-C10), not
  excluding the dirs (corrects the earlier "harness leakage" framing; see
  N4/N5).
- **B3 — `REPO_ROOT` / rundir anchor.** `REPO_ROOT` is the active project
  root, computed from the root-level `rundir/`. Today's single `REPO_ROOT`
  + functional-root glob is replaced by manifest-driven multi-dir discovery
  (Q-L2).
- **B4 — Cross-project `.cppm` discovery + PCM ownership.** A child
  `.cppm` outside the active project's own tree must still be discovered,
  precompiled, and have per-project PCM targets; import-scan ordering stays
  automatic once the file set is discovered (composition Q-C3/G1).
- **B5 — Generate-before-build ordering.** A parent build consumes child
  generated files, so children must be generated first — a `make`
  prerequisite via the manifest, or a flow requirement
  (composition Q-C9).
- **B6 — Include search-path shadowing (residual non-module headers).**
  **Resolved by the registrar plan's Base-as-module promotion** (M3/T6,
  adopted above — owned there, not here). With the block class, context
  types, **and** `<child>Base` all imported by module name, the C++ model
  boundary leaves the `-I` path entirely, so its same-basename shadowing
  dissolves. The **modules-vs-header-visible choice
  is a whole-emission mode, not a per-artifact mix** (see the resolved
  choice below): a modules build has no Base/class header to fall back to; a gcc-13
  build emits the *entire* surface header-visible (registrar mechanism
  (b)), consistently. At the S3-M end state the variant **Config** is no longer
  a header either — it is a **module export of the registrar** — so
  the residual `-I` shadowing comes only from headers that are **not
  modules at all**, independent of the toolchain: the **firmware headers**
  (`fw/include/*.h`, consumed by the firmware build, the `fwIpMain`
  cross-project case — composition Q-C11) and any hand-authored header. For
  child-owned headers, the B6 end-state contract is a **project-qualified
  subpath** plus an owner-root include mapping. The current manifest does not
  yet emit a parent-of-project `-I` or logical-project overlay, so that remains
  composition Q-C8/C2 work rather than a landed mechanism. For parent-owned residual headers
  (if any remain after registrar-module export), use the same owner
  qualifier as the parent-owned module identity: owning project +
  parent/assembler context + child + artifact kind. In a whole-project
  header-visible (gcc-13) build, the same scheme also covers the reverted
  C++ headers. During S3-H, the parent-owned Config header is a deliberate
  additional residual: it lives beside the registrar and uses an
  owner/parent-qualified basename, while the manifest contributes that exact
  registrar directory to `-I`. It disappears from the `-I` surface when S3-M
  folds it into the registrar module. Owned by composition Q-C8 and registrar
  S3.
- **B7 — Module / namespace collisions.** Generated module/namespace names
  must not derive from the file stem alone: two independently-authored projects
  sharing `common.yaml` or `fifo.yaml` would collide. **The hierarchical
  directory split does not fix this**—language identity is independent of
  filesystem path. Managed context/module/package identities use the absolute
  owning project with direct single-underscore spelling
  (`projectName_localName`), as settled by shared-definitions D-SD4/D-SD6.
  That qualifier is path-independent, so a child's identity is identical
  standalone and nested. Parent-scoped registrar/header/build artifacts qualify
  by **owning project + parent/assembler identity + child + artifact kind**;
  the Config type itself remains canonical by
  `(projectName, block, variant)`. The parent/assembler identity is the
  persisted context/ownership fact already used by registrar generation, not a
  raw directory string. Thus
  same-basename files such as `top/registrar/ipRegistrar.cppm` and
  `bridge/registrar/ipRegistrar.cppm` are fine as long as their exported
  module/namespace identities and project-canonical Config references do not
  collide. Multiple provider paths claiming
  the same `projectName` are resolved explicitly by hierarchical
  `projectOverrides`; no content comparison is performed. Hard prerequisite
  owned by `plan-cross-project-shared-definitions.md`; this
  plan contributes the path-independence requirement, parent-qualified
  registrar/config identity, and the owner-qualified residual-header scheme
  (B6).
- **B8 — Registrar duplication.** The shared `ip` registers the same
  `(block, variant)` from two trampolines (`top/registrar/`,
  `bridge/registrar/`) in one binary; `emplace` is first-wins and safe
  under the determinism rule, disambiguated by the `projectName` key
  (composition Q-C10).
- **B9 — Build-config isolation.** Each project's `prj/include/` may carry
  different flags/toolchain. The **active** project's `include/` governs
  the build; child `include/` must not be pulled in. The manifest
  contributes child *sources*, never child build config.
- **B10 — Verilator aggregation per build.** Each project's `rundir/` has
  its own `obj_dir`; only the active project's `verif/.../sc_main.cpp` +
  `vl_wrap` aggregator are used. The hard-coded
  `CPP_SRC += verif/vl_wrap/vl_wrap.cpp` must become manifest-driven
  (registrar S6 / composition G6). This is the concrete form of B1.
- **B11 — rundir isolation.** Each project's root-level `rundir/` is
  independent, gitignored build output; a child's `rundir/` is dormant in a
  parent build, with no cross-contamination.
- **B12 — clangd + nested-config ambiguity.** Derived from `make -n` of
  the active project, so the manifest feeds it directly; cross-project
  symbols resolve through the same include dirs (Q-L5; composition Q-C6).
  This is likely a low-risk generated-artifact issue rather than a layout
  blocker: these files are not expected to be checked in, and users
  typically create them from the outermost active project they are editing.
  Confirm the clangd target follows that usage — one active-project
  `compile_commands.json` covering the composed set — and document that
  embedded child standalone configs should not be treated as source truth
  for an outer composed edit session.
- **B13 — Managed SV discovery is explicit.** Generated manifests enumerate
  every arch2code-managed SV module/package from the effective provider graph;
  directory wildcards and `-y` remain only for user-added or fixed arch2code
  libraries. Layout supplies paths but never selects a managed definition by
  search order.

B1–B3 and B9–B11 are introduced by *this* plan (hierarchical layout +
per-project `rundir/`/`prj/include/` + the verilated-entry selection);
B4–B8 and B12 are owned by the composition plan and listed here for the
build picture.

## The Seam (and what else moves with it)

Generation-time path composition is **one function**:
`processYaml.expandNewModulePath` (`pysrc/processYaml.py:78`). It is the
only place the two axes are joined *for emitted files*, and it is shared
by every emission consumer:

- `newModule.py:161` (block mode),
- `newModule.py:216` (registrar mode),
- `processYaml.py:4012` (`projectCreate` context-file enumeration).

Its current body composes `functional`:

```python
basePathAbs  = dirMacros[basePathKey]              # e.g. $root/model
moduleDirAbs = join(basePathAbs, moduleDir)        # moduleDir = decomposition path ("ip")
if blockDir: moduleDirAbs = join(moduleDirAbs, module)
filePath     = join(moduleDirAbs, moduleFileStub + fileStub)
```

Flipping the join order here flips the layout for every emitted file at
once — that part is genuinely a single point of change. But the claim
"one seam, nothing else to keep in sync" is **too strong**; two other
pieces are mode-dependent and must move with it:

- **The seam's *input* is mode-dependent (a `projectCreate` change).**
  All three callers pass `moduleDir = prj.data['blocks'][<block>]['dir']`
  (block mode and the registrar's assembler dir). In `functional` that
  `dir` is a path **relative to `arch/yaml/`** that the seam re-roots
  under `$root/<funcSegment>`; in `hierarchical` it must be the node's
  **own directory** (the parent of `<node>/yaml/`). That value is
  computed and persisted during `projectCreate`, not inside
  `expandNewModulePath`. So the seam body and the `dir` derivation in
  `projectCreate` are **one logical change in two places**; the seam
  alone is not sufficient.
- **Build/manifest discovery is a *second* resolver.** The makefiles glob
  fixed roots independently of the seam: `a2c-common.mk` globs
  `find -L $(REPO_ROOT)/arch/yaml/` and pins
  `A2C_PRJ_YAML = $(REPO_ROOT)/arch/yaml/project.yaml`; `a2c-systemc.mk`
  globs `$(REPO_ROOT)/{base,model,registrar,fw,tb}` into `PRJ_SRC_DIRS`
  and hard-codes `CPP_SRC += $(REPO_ROOT)/verif/vl_wrap/vl_wrap.cpp`.
  None of this passes through `expandNewModulePath`, so it does **not**
  flip for free. The replacement is the composition plan's DB-emitted
  manifest (Q-L2): single-project and composed SystemC discovery,
  owner-aware RTL directories, and VL wrapper manifest-variable consumption
  are now landed; full L2b acceptance remains.

Net: the **generation** half (seam body + `projectCreate` `dir`
derivation) is self-contained and can land alone with byte-identical
`functional` output (work item L1). The **build/discovery** half is a
separate resolver implemented incrementally through the composition manifest
(work item L2). Line
references above will drift as files change — treat the symbol names
(`expandNewModulePath`, `PRJ_SRC_DIRS`, the `vl_wrap.cpp` `CPP_SRC` line)
as the stable anchors, not the line numbers.

## Recommended Mechanism

Express both modes with **explicit layout-keyed directory sets** selected by
`fileGeneration.layout`, but keep that extra layer in the **internal
project representation**, not in the user-authored project-file surface. Do
not derive one layout from another by stripping or rewriting path strings.

The user-visible project YAML surface remains the existing one: projects keep
authoring `dirs:` and `fileMap` as they do today, with only the new
`fileGeneration.layout` selector added (default `functional`). During
`projectCreate`, the **default merge/normalization step** builds the internal
layout-keyed representation from the merged defaults + user overrides, and
generators/build views consume the selected layout from that normalized shape.

- `fileMap` entries keep referencing stable semantic keys (`model`, `rtl`,
  `base`, `registrar`, `vlWrap`, `tb`, `fwInc`, ...). The selected layout
  supplies the concrete path for each key. The keys are shared; the values
  are layout-specific.
- **`functional`:** `path = <selected model/rtl/... path> / <decomp> [/ block] / file`,
  where `<decomp>` is the block YAML's directory **relative to the central
  `arch/yaml/` root** (today's behavior; identical output).
- **`hierarchical`:** `path = <dir containing the block YAML> / <selected model/rtl/... segment> [/ block] / file`.
  `<decomp>` is the YAML's **own user-chosen directory**, and the selected
  functional segment is created beside the YAML. There is no central
  `arch/yaml/` and no node naming.

The only real difference is the anchor: `functional` re-roots the YAML's
relative decomposition under a shared functional root; `hierarchical`
emits the functional segment in place, at the YAML's own location. The
composition function plus a layout selector covers both, using the selected
layout's explicit directory values. Three things become mode-aware in
lockstep (see "The Seam"): `expandNewModulePath` (the join order),
the `projectCreate` `blocks[...]['dir']` derivation (what the seam receives
as the decomposition anchor), and the build/glob discovery (replaced by the
composition manifest, Q-L2).

Note this also shifts **where YAML lives**: `functional` centralizes it
under `arch/yaml/<decomp>/`; `hierarchical` distributes it into the node
directories, co-located with the generated functional dirs. That
relocation is the substance of the opt-in Q-L4 migration.

## Open Questions

- **Q-L1 — Selector scope. DECIDED (2026-06-29): per project file.** Each
  `<ip>Project.yaml` selects its own layout mode. When a nested project
  file is discovered during YAML parsing, **that project's own setting
  determines its subtree**; the parent does not impose its layout on the
  child. The mode tag rides the per-context owning-project record that the
  composition plan's Q-C9 ownership gate already introduces (no separate
  carrier needed). Mode names decided (see "Mode Names").
- **Q-L2 — Build tree (directory list) as a generated artifact.** Today
  the build *discovers directories* by glob (`find_cpp_source_directories`
  over fixed roots → `PRJ_SRC_DIRS`/`SC_GEN_FILES`), globs the YAML dep
  list (`YAML_FILES = $(shell find …)`), and hard-codes the `vl_wrap.cpp`
  line. The **directory discovery and the fixed roots go away**:
  `projectCreate` derives the directory set from the `projectFiles:`/
  `include:` tree crossed with the functional segments and **emits it as a
  generated `.mk`** (dirs, module set, project-file path, active verilated
  entry). The makefile then **wildcards files within each derived dir**
  (`wildcard $(dir)/*.cpp`), so user-authored files beyond the generated
  set are still compiled — file search is **scoped to derived dirs**, not
  used to find the tree. The YAML dep list is the include-tree closure
  (derived), not a glob. This (a) reaches nested project implementation
  dirs and (b) selects exactly the **active project's verilated entry**.
  The model main is shared a2c and tbs are runtime-selected, so child
  `tb/`/`registrar/` are compiled, not excluded (see Build Model, B1/B2).
  Shared with the composition plan's manifest (its Q-C3) — same seam, no
  second ad-hoc discovery path.
- **Q-L3 — Non-decomposed / flat functional areas. RESOLVED
  (2026-06-29; amended 2026-07-06 — `include/` stays at root).**
  **Generated** project-scope artifacts with no block YAML (the `vl_wrap`
  aggregator, `sc_main`, `fwIpMain`) plus the project file live in the
  **`prj/` container**, the project root's own artifact home, named by the
  abstracted `$prj` `dirs:` segment (`prj/fw/`, `prj/verif/`,
  `prj/yaml/<name>Project.yaml`). `prj/` is **referenced via the project-file
  path, not discovered** (see "The `prj/` directory"); its literal name is
  config and appears in no glob. A plain node is just a directory holding
  parsed block YAML; `common` is an ordinary node. The `vl_wrap` per-block
  wrappers are decomposed to their owning node by registrar S6; only the
  residual project-wide aggregator lands in `prj/`.
  - **User-owned root exemptions (amended 2026-07-06).** Build config
    `include/` and `rundir/` do **not** move into `prj/`; they stay at the
    project root, alongside the root `Makefile`. Rationale: these are the
    stable, human-facing, conventionally-rooted entry points (the whole a2c
    ecosystem references `$(REPO_ROOT)/include/make/shared.mk` and runs from
    `rundir/`), the same class as the already-decided `rundir/`-at-root
    exemption. Keeping `include/` at root is what **retires migration Gap 1**
    (T4.6): the bootstrap Makefiles' `include $(REPO_ROOT)/include/make/...`
    references — five of them in `debayer`, plus a silent `-include` — never
    break, so no scaffolding scan / build-gate is needed. The split is thus
    **`prj/` = generated project-scope guts + the project file; root =
    user-owned config/entry (`include/`, `rundir/`, `Makefile`) + decomposition
    nodes**. Build-config isolation for the composed case (B9) is delivered by
    the manifest ("contributes child sources, never child build config"), not
    by `prj/` placement, so nothing functional is lost by leaving `include/`
    at root.
- **Q-L4 — Migration. DECIDED (2026-06-30): opt-in per project, not
  forced by a format bump.** Existing projects remain valid in
  `functional`; only projects that choose the `hierarchical` layout run the
  migration through the existing `make migrate` / `yamlFormat:2` machinery
  (not a manual sweep). Some in-tree examples and reusable-IP fixtures will
  opt in, but there is no global requirement that every project adopt
  hierarchical dirs. **This is higher-risk than the generator change — it is
  not just a file move:**
  - **It relocates authored YAML**, not just generated output:
    `arch/yaml/<decomp>/*.yaml` → distributed `<node>/yaml/*.yaml`, and it
    must introduce `prj/` and move the integration orphans
    (`fwIpMain`, `sc_main`, the `vl_wrap` aggregator) into `prj/`.
  - **It must rewrite relative cross-node `include:` directives.** N6 notes
    that hierarchical "relative cross-node includes re-root through the
    `yaml/` level" — so every relative include between authored YAML files
    changes spelling when the files move. Mechanical correctness of that
    rewrite (and of any relative path inside user regions of `.cpp`/`.cppm`
    that reaches a sibling functional dir) is the **hard part** and the
    main migration risk; it touches user-authored content, not just
    generated regions. The migration phase must prove these rewrites are
    safe (or report the ones it cannot rewrite for manual fixup), the way
    `migrateYaml` already reports manual items.
  - **Existing projects do not yet have generated registrars.** Registrar
    placement still matters for green-field hierarchical fixtures and for
    the registrar plan, but it is not the main compatibility burden for
    migrating today's trees. The main non-YAML changes are module-facing:
    module unit locations, module/import spelling, PCM/object naming, and
    any header-visible fallback emitted by the whole-project non-modules
    mode.
  - **Pure generated implementation files are not the delicate case.**
    Files with no user-owned content (for example generated Base/module
    artifacts) can be recreated in the new location through the normal
    `make newmodule` / generation flow instead of being carefully moved.
    Migration must be careful only for files that carry user content:
    authored YAML, user regions in `.cpp`/`.h`/`.cppm`/`.sv`, hand-authored
    support files, and relative paths inside those files.
  - **Sequencing:** because migration edits user files, it should land
    *after* L1 (generation) and L2 (build) are proven on a green-field
    `hierarchical` fixture, so the migration is validated against a known-good
    target shape rather than co-developed with the mechanism.
- **Q-L5 — clangd. LOW RISK / confirm behavior.** The generated `.clangd`
  `-I` list is derived from the same directory facts; confirm it follows the
  seam automatically once `expandNewModulePath` and the manifest are
  mode-aware (no separate path logic). The earlier nested-config concern is
  probably not a real migration blocker: `.clangd` / `compile_commands.json`
  are generated local artifacts, not expected to be checked in, and users
  typically create them from the outermost active project level. The rule to
  confirm is simple: the active project's clangd generation covers the
  composed source set; embedded child standalone configs are regenerated only
  when working on that child as the active project.
- **Q-L6 — Config schema for the selector + scheme-specific defaults.
  DECIDED (2026-06-30): same user surface, internal layout-keyed defaults,
  no string-derived paths.** The project file sets
  **`fileGeneration.layout: functional | hierarchical`**, defaulting to
  `functional` in `builder/base/config/project.yaml` (no regression for
  existing projects). Apart from that selector, user project files keep the
  exact existing authoring surface: `dirs:` and `fileMap` stay where they
  are today. The extra layout-keyed layer is a normalized internal project
  representation created by `projectCreate`, not something users must author
  in their project files. The base config must still ship good defaults for
  **both** schemes, because they differ:
  - **Shared (scheme-independent):** the `fileMap` block definitions
    (`name`/`ext`/`cond`/`mode`) and the functional-segment identities
    (`model rtl base fw verif tb registrar`).
  - **functional placement:** segments rooted at `$root/<…>`, including the
    multi-level tails `verif/vl_wrap` and `fw/include`; YAML under
    `arch/yaml/`; `rundir/` at root.
  - **hierarchical placement:** node-relative segments, with the
    multi-level tails **flattened** (`vl_wrap`→`verif`, `fwInc`→`fw`);
    authored YAML in `<node>/yaml/`; project marked by `prj/` (project file
    in `prj/yaml/`); **build config `include/` and `rundir/` stay at the
    project root** (amended 2026-07-06, Q-L3) — they are user-owned entry
    points, not `prj/` orphans. `prj/` holds only the generated project-scope
    orphans (`prj/fw/`, `prj/verif/`) + the project file (`prj/yaml/`).
  - **Mechanism:** keep the user-authored `fileMap` entries keyed by
    artifact role and keep user-authored `dirs:` as the compatibility
    surface. The implementation change is in how defaults are merged: in
    `projectCreate`, merge the existing user surface with the base defaults,
    normalize that merged result into an internal layout-keyed directory
    representation, and select the set named by `fileGeneration.layout` for
    downstream generators/build views. Do **not** derive the hierarchical
    values by stripping `$root` or otherwise manipulating the functional
    strings; if two layouts have different values, they are represented as
    different internal config values and selected directly in code.
- **Q-L7 — Default for *new* projects. DECIDED (2026-06-30):
  `hierarchical`.** This is distinct from the base-config default: Q-L6 keeps
  the merged config default at `functional` so *existing* projects do not
  regress when they lack the selector. Brand-new projects scaffolded by
  `newProject.py` should explicitly set `fileGeneration.layout:
  hierarchical`, because `hierarchical` is the strategic target (see Mode
  Names) and the only mode that composes. Existing projects remain
  `functional` unless they opt in via Q-L4 migration.

## Generator Surface

- **`pysrc/processYaml.py::expandNewModulePath` + the `projectCreate`
  `blocks[...]['dir']` derivation** — add the `hierarchical` join order in
  the seam, selected by the Q-L1 mode, **and** make the persisted `dir`
  the node's own directory in `hierarchical` (vs `arch/yaml/`-relative in
  `functional`); the seam receives that value, so the two change together
  (see "The Seam"). `functional`-mode output must stay byte-identical to
  today.
- **`fileGeneration:` config (`config/project.yaml`)** — add the
  `layout: functional | hierarchical` selector (Q-L1), default `functional`
  (no regression). Preserve the existing user-authored `dirs:`/`fileMap`
  surface; the change is in `projectCreate`'s default merge/normalization,
  which turns the merged defaults + user overrides into an internal
  layout-keyed directory representation selected directly by `layout:`
  (functional roots vs hierarchical node-relative segments, flattened
  `verif`/`fw` tails, `yaml`/`prj`/`rundir` conventions) per Q-L6. No layout
  path is derived by stripping or rewriting another layout's strings. **The
  `ext` flips below are owned by the registrar plan (M3/T6, S3), not by this
  plan** — they land with that plan and are listed here only so the layout
  config stays consistent: `blockBase` `ext` `h`→`cppm` (Base-as-module,
  B6); `blockRegistrar` `ext` `cpp`→`cppm`; S3-H adds a registrar-mode foreign
  Config header, and S3-M folds that header into a dedicated config module
  imported by the registrar (Option A, 2026-07-20).
  The context-mode `config` entry remains for child-owned defaults and
  same-project canonical variants until their separately authorized migration.
  This plan's *own* user-visible config surface is just the
  `layout:` selector; the explicit layout-keyed directory defaults are an
  internal normalized config shape (Q-L6).
- **Build tree (dir list) as a generated `.mk`** — emit the **directory
  set** from `projectCreate` (Q-L2), shared with the composition manifest
  seam. It supplies, by derivation, the source/include/registrar **dirs**,
  the module set, and the YAML dep list — so the fixed-root **directory**
  globs (`find_cpp_source_directories` → `PRJ_SRC_DIRS`/`SC_GEN_FILES`),
  the `YAML_FILES = $(shell find …)` line, and the hard-coded
  `CPP_SRC += …/vl_wrap.cpp` line are **deleted**. Per-dir **file** globs
  (`wildcard $(dir)/*.cpp`) **stay**, so user files beyond the generated
  set in each derived dir are still picked up. The build still
  **references the project-file path** (`A2C_PRJ_YAML`); re-point it at the
  project file's new location (`$prj/yaml/<name>Project.yaml`) — a path
  change, not a discovery change.
- **`pysrc/newProject.py` / `pysrc/newModule.py`** — scaffold
  `hierarchical` by default for new projects (Q-L7) by explicitly writing
  `fileGeneration.layout: hierarchical`, while preserving `functional` for
  existing projects that omit the selector. In `hierarchical`, author block
  YAML into `<node>/yaml/`, and for a buildable project create a root-level
  `rundir/` plus a `prj/` marker holding the project file (`prj/yaml/`),
  build config (`prj/include/`), and the integration orphans (`fwIpMain`,
  `vl_wrap` aggregator, verilated `sc_main`) in `prj/fw/` and `prj/verif/`.
  Each project gets its own root `rundir/` + `prj/include/`; only the
  active project's verilated entry is linked per build.
- **Migration (`migrateYaml` / `make migrate`)** — an opt-in phase that
  relocates an existing `functional` tree to `hierarchical` when that
  project selects the layout (Q-L4). Today's projects do not yet have
  generated registrars, so the migration burden is primarily authored YAML
  relocation, relative-include rewrites, and module/import/path references
  inside files with user-owned content. Pure generated implementation
  artifacts can be deleted and recreated through `make newmodule` /
  generation in the new location.

## Relationship to Other Plans

- **`plan-reusable-ip-registrar.md`** — layout axis reconciled.
  S2's `functional` `registrar/<assembler>/` layout is the concrete
  instance of the contradiction this plan resolves. Once the axis is
  decided, S3 (config relocation) and S6 (verilated trampoline) inherit
  it; S2 may need its `basePath`/layout reconciled. **The Base-as-module
  and registrar-exports-Config decisions (B6, N3) are owned by *that* plan
  (M3/T6, S3), not this one** — this plan only adopts them for the worked
  example and requires that the chosen boundary form be import-by-module so
  the B6 `-I` shadowing dissolves. Keep the authoritative `ext`-flip record
  in the registrar plan to avoid two divergent decision sites.
- **`plan-ip-project-composition.md`** — its standalone-IP and
  nested-child layouts are `hierarchical`; this plan provides the
  intra-project mechanism that makes the in-project block and the
  referenced IP structurally identical. The per-context owning-project
  record introduced by its Q-C9 ownership gate is the natural carrier for
  a per-reference layout selector (Q-L1).
- **`plan-development-ordering.md`** — high-level index; add this plan to
  its owner map and re-sequence the registrar plan behind it.

## Work Items

**Historical landability split.** L1/L2a/L3/L4 described below have landed.
L2b is now active rather than blocked:

- **L1 is independently shippable.** Mode-aware path composition (seam +
  `dir` derivation) needs nothing from the composition plan. Its
  acceptance is byte-identical `functional` output plus a correctly
  inverted `hierarchical` tree — both checkable by inspecting generated
  files, no composed build required. Land it first; it de-risks everything
  else and cannot regress existing projects.
- **L2a is complete; L2b is CLOSED/ACCEPTED (UPDATE 2026-07-22).** The DB
  manifest drives composed SystemC directories; owner-aware RTL paths, VL
  wrapper manifest consumption, explicit SV files (S6 file->top records),
  clangd (S4), and full VL acceptance all landed.
- **L4 is complete.**

**UPDATE 2026-07-22 —** the critical path is fully retired for this plan:
composition C2/L2b is closed and L5 (the acceptance vehicle) PASSED. Registrar
S3-M/S5/S6 have since LANDED (M-split satisfied). S3-H LANDED (committed
2026-07-21). The historical wording below is retained for the record.

### L0 — Selector scope — DECIDED (2026-06-29)

Per project file (Q-L1): each `<ip>Project.yaml` sets
`fileGeneration.layout: functional | hierarchical`; a discovered nested
project file uses its own setting for its subtree. The mode tag rides the
composition plan's per-context owning-project record (Q-C9). No further
design work; L1 onward implements it.

### L1 — Mode-aware path composition (independently landable)

Implement the `hierarchical` join order in `expandNewModulePath` **and**
the mode-aware `projectCreate` `blocks[...]['dir']` derivation, behind the
L0 selector. **No build-system dependency.** Acceptance:
- `functional` output **byte-identical** to today across all `examples/`
  (regression gate), and
- `hierarchical` produces the inverted tree for a chosen fixture, checked
  against a **structural golden** (an expected `find`-sorted file-path
  listing committed with the fixture) so a layout regression is caught by
  diff, not only when a later build breaks.

### L2 — Build + clangd discovery, verilated-entry selection — CLOSED/ACCEPTED (2026-07-22)

L2a is complete. For L2b, the manifest reaches referenced-child SystemC
implementation directories and the composed model builds/runs. Commit
`6bbec76` emits owner-aware RTL directories; `6113562` makes VL wrapper
Makefiles consume `A2C_VL_WRAP_DIRS`. **UPDATE 2026-07-22 — L2b CLOSED:** the
previously-remaining items are all satisfied — explicit managed SV module file
lists (S6 explicit file->top records), active-project VL entry/source closure
and standalone (S5), cross-project clangd (S4) — and the full hierarchical
composed acceptance vehicle (L5) PASSED.

### L3 — Reconcile registrar plan

Re-point registrar S2's layout to the decided axis; unblock S3/S6 on the
chosen mechanism.

### L4 — Opt-in migration (lands last; edits user files)

Provide the `make migrate` phase that relocates an existing `functional`
tree to `hierarchical` only when that project selects the layout (Q-L4),
including the relative-include rewrite and any module/import/path references
inside files with user-owned content. Pure generated implementation files are
recreated through `make newmodule` / generation rather than carefully
migrated. Migrate only the in-tree examples/fixtures that opt in to
hierarchical layout. Sequenced after L1/L2 so it is validated against a
proven green-field target shape. Report any include it cannot rewrite for
manual fixup (the `migrateYaml` manual-item convention).

### L5 — Canonical nested composition fixture (acceptance vehicle; needs L2) — PASSED/ACCEPTED (2026-07-22)

**UPDATE 2026-07-22 — L5 full nested composition acceptance PASSED.** The full
matrix ran on the split `examples/ip_test` (`ip`/`ipBridge`/`common`) fixture
under `make -j`: standalone `ip` (model+VL), standalone `ipBridge` (model+VL),
and composed `ip_test` (model + VL-src/ip0/ip1) all report `No error`. Evidence
checks all PASS: provider override precedence (root selects root `ip`; the
symlink `bridge/ip` is not dereferenced; 0 physical `bridge/ip/` leaks in the
root manifest), N7 distinct parent-qualified identities (distinct config modules
`bridge/registrar/bridge/ipBridge_ipVariantConfig.cppm` vs
`registrar/top/ip_test_ipVariantConfig.cppm`; owner-qualified SV wrapper tops),
N8 one-selected-child-file-set in manifests, standalone-vs-composed scope, and
no `vl_wrap` reintroduced. `common` is correctly a definitions/support project
(no `run` target). No code gaps.

Build the composition plan's C5 example. Root `ip_test`, reusable leaf `ip`,
and reusable assembler `ipBridge` each have independent project/rundir scope;
both child projects must build and test standalone. The committed
`bridge/ip -> ../ip` symlink models the vendored Git-submodule location a
standalone bridge would carry. Provider identity preserves the normalized authored path
without dereferencing the symlink. Bridge selects that path standalone; root
selects root `ip` and its higher override wins when composed.

This fixture proves YAML-co-located addressing, project-vs-node discovery,
parent-owned registrars, provider override precedence, one selected child file
set in manifests, standalone-vs-composed build scope, and explicit managed SV
discovery. A later `src`/`ipLeaf` project split may additionally exercise
cross-project eval; it is not required to establish the canonical
`ip`/`ipBridge` harness pattern.

## Done Criteria

Grouped by dependency so a partial landing (L1 alone) has a clear,
checkable bar.

**Landable now (L1; no composition dependency):**

- Selector scope (Q-L1) implemented; `layout:` selectable per project file.
- `functional` output **byte-identical** to today (no regression for
  existing top-down projects).
- A `hierarchical` fixture's generated tree matches a committed
  **structural golden** (expected `find`-sorted path listing), proving the
  inverted layout independent of any build.

**Gated on the composition manifest (L2+):**

- A `hierarchical` `ip_test`-derived fixture builds, runs, and resolves in
  clangd from the active project's generated config, with one IP's full
  surface under a single subtree (B12).
- **The self-contained nested `ipLeaf` builds and runs both standalone
  (its own root `rundir/`) and embedded under `src`/`top`. `ipLeaf/`
  carries only its own default config in its `registrar/`; the
  consumer-selected variant lives in `src/registrar/` (N1–N9 resolved).**
- **Build composition works: each project has its own root `rundir/` +
  `prj/include/`; a parent build pulls child implementation sources, keeps
  child block-level tbs runnable by name, and links exactly the active
  project's verilated `sc_main` + `vl_wrap` aggregator (B1–B3, B9–B11).**
- N7 is proven with a collision fixture: same-stem child-owned artifacts across
  two projects use child-`projectName` identities, and same-child parent-owned
  registrar/config artifacts under two assembler contexts use distinct
  parent-qualified module/namespace/include/build identities.
- Generation ownership is enforced by the owning-project tag, **not** by
  path: a parent regeneration does not clobber child-owned files in a
  shared subtree (N8).

**Cross-plan:**

- The registrar plan's layout (S2) reconciled with the decided axis; S3-H is
  LANDED (committed 2026-07-21), while S3-M/S6 are unblocked **on the layout axis
  only** and stay gated on composition M-split (the `ext` flips remain owned by
  that plan). See
  [`plan-composition-ordering.md`](./plan-composition-ordering.md).
- The composition plan's nested-child case is representable under the
  decided selector scope (or in-tree nesting is explicitly deferred to
  external siblings, recorded as a decision).
- Opt-in migration (Q-L4) relocates an existing selected tree **including
  relative includes** and user-content module/import/path references, with
  unrewritable cases reported for manual fixup; pure generated
  implementation artifacts are recreated rather than hand-migrated.

## Execution Plan (todos)

Created 2026-06-30. This section refines the milestone-level Work Items into
ordered, individually-acceptable todos for the **near-term landable slice
only**. This execution-plan introduction is historical: L4 is complete, and
(UPDATE 2026-07-22) L2b is now CLOSED/ACCEPTED with L5 full nested acceptance
PASSED.

**L2 is now split** (decided 2026-06-30): the original single L2 work item is
superseded by **L2a** (single-project `hierarchical` build, **not** gated on
the composition manifest) and **L2b** (composed/nested build, now active with
the composition plan's C2 manifest). L2a derives its dir list from one project's
own `projectFiles:`/`include:` closure and is the parent-only portion of the
eventual composition manifest, so it is incremental toward L2b, not throwaway.

Historical critical path:
**T0.\* → L1 (T1.\*) → L2a (T2a.\*)**, with **L3** in parallel. Current
remaining path: **none — L2b/composition C2 CLOSED and L5 PASSED (UPDATE
2026-07-22)**; L4 is complete.

### Phase 0 — Pre-work (no production code change; de-risks L1)

- **T0.1 — `functional` byte-identical regression harness.** Build a script
  that captures a **pre-L1 generation snapshot of the current working tree**,
  then regenerates after L1 with `layout: functional` and diffs the generated
  file sets and contents across `examples/`. This is the safety net for the
  riskiest L1 change (the config normalization, T1.2) and must exist and
  capture its baseline **before** any normalization lands.
  - *Baseline definition (reference-state caveat).* The baseline is the
    generation output of the working tree as-is, **not** a pristine committed
    reference. This matters because `examples/ip_test` is **mid-migration**
    (registrar plan / M3/T6: `.cpp`/`.h` retired, `.cppm` added, `registrar/`
    introduced) and there is **no full saved buildable copy** — only the
    6-file `unittest/fixtures/block-module-migration/before/` partial
    snapshot. Verified 2026-06-30: `make clean && make db && make gen` on
    `ip_test` succeeds (exit 0, full file set emitted), so it **generates
    deterministically** and is safe to include in the byte-identical gate.
    The gate proves **generation-equivalence**, not build success.
  - *Acceptance:* harness reports zero diff for `layout: functional` across
    `examples/` (baseline established); ready to gate T1.2/T1.6.

- **T0.2 — Pin the decomposition `dir` blast radius.** Enumerate every
  producer and consumer of the decomposition `dir` value the seam re-roots
  (`includeData['dir']` at `processYaml.py:4012`, the `self.yamlDir` write at
  `:4809`, and the `moduleDir`/`assemblerDir` computed for
  `newModule.py:161`/`:216`). Confirm `expandNewModulePath` is the **only**
  join site and that no other code consumes `dir` assuming `functional`
  semantics.
  - *Acceptance:* a short written inventory (in this plan or a code comment)
    listing producers/consumers and confirming the single join site. No code
    change.

- **T0.3 — Design the Q-L6 internal layout-keyed representation.** Produce the
  concrete internal data shape that `projectCreate` normalizes the merged
  defaults plus user overrides into: how each `fileMap` role key maps to a
  per-layout path value, and how the `hierarchical` specifics are encoded —
  the flattened tails (`vl_wrap`→`verif`, `fwInc`→`fw`) and the
  `yaml`/`prj`/`rundir` conventions. The same segment record must also carry
  the segment's build group (`sc`, `sv`, `vl`, or none), so later manifest
  logic consumes a directory/segment contract instead of inferring build
  behavior from `basePath` strings. Paths must be distinct internal values per
  layout, never derived by string-stripping the other layout (Q-L6).
  - *Acceptance:* documented internal shape agreed before T1.2 begins. This is
    the one remaining design residual that gates implementation.

### Phase 1 — L1: Mode-aware path composition (independently landable)

- **T1.1 — Add the `fileGeneration.layout` selector.** Add
  `layout: functional | hierarchical` to `config/project.yaml`, default
  `functional`, with validation in `projectCreate` (Q-L1/Q-L6). No behavior
  change yet. The mode tag rides the per-context owning-project record
  (composition Q-C9).
  - *Acceptance:* selector parsed and validated; default-`functional`
    projects produce identical output (T0.1 green).

- **T1.2 — Implement the normalized internal representation (highest risk).**
  In `projectCreate`, merge user `dirs:`/`fileMap` with base defaults and
  normalize into the T0.3 layout-keyed shape; select the set named by
  `layout:`. `functional` values must reproduce today's directories exactly.
  - *Acceptance:* T0.1 harness reports zero diff for `functional` across all
    `examples/`. This is guarded by T0.1 because the refactor sits on the
    `functional` path too.

- **T1.3 — Make the `dir` derivation mode-aware.** Per T0.2, derive the
  decomposition anchor as the node's own directory (parent of `<node>/yaml/`)
  in `hierarchical`, versus the `arch/yaml/`-relative path in `functional`.
  - *Acceptance:* `functional` unchanged (T0.1); `hierarchical` yields
    node-own anchors.

- **T1.4 — Flip the seam join order; anchor `prj/` orphans.** Add the
  `hierarchical` join order in `expandNewModulePath`, selected by mode. Anchor
  the project-scope orphans (`fwIpMain`, `sc_main`, the `vl_wrap` aggregator)
  on the `$prj` segment for `hierarchical`. This is **generation-side only**;
  orphan *discovery* is deferred to L2a (Finding 6 of the 2026-06-30 review).
  - *Acceptance:* emitted paths invert correctly; orphans land under `prj/`.

- **T1.5 — Green-field `hierarchical` fixture + structural golden.** Author a
  green-field `hierarchical` fixture and commit a structural golden (an
  expected `find`-sorted file-path listing) alongside it.
  - *Acceptance:* fixture generates; golden committed.

- **T1.6 — L1 acceptance gate.** Run T0.1 (functional byte-identical across
  `examples/`) and diff the fixture tree against the T1.5 golden.
  - *Acceptance:* both clean. **L1 done.**

### Phase 2 — L2a: Single-project hierarchical build (ungated)

- **T2a.1 — Emit a per-project derived dir-list `.mk`. — DONE.** From a single
  project's own `projectFiles:`/`include:` closure crossed with the functional
  segments, emit a `.mk` enumerating source/include/registrar dirs, the module
  set, the project-file path, and the single verilated entry (Q-L2). No
  cross-project machinery; this is the parent-only portion of the future
  composition manifest.
  - *Acceptance:* `.mk` emitted for both modes; dir set for `functional`
    fixtures matches today's globbed set. **Met:** a late `createArtifacts` hook
    (`config/createBuildManifest.py`, after `saveIncludeFiles()`) emits
    `.gen/build.mk`; `unittest/test_build_manifest.py` confirms the derived dir
    set reproduces the glob set across all 8 examples (orphans excepted).

- **T2a.1a — Move manifest build grouping into the segment contract. — DONE.** Replace
  any hard-coded `basePath`→manifest-role table with metadata on the normalized
  layout/file-generation segment record: `fileMap[*].basePath` selects the
  segment, and the segment's `buildGroup` determines whether its emitted dirs
  contribute to `A2C_SC_SRC_DIRS`, `A2C_SV_SRC_DIRS`, `A2C_VL_WRAP_DIRS`, or no
  build manifest group. This keeps directory layout, artifact placement, and
  build consumption linked through the same abstraction, and avoids adding a
  second ad-hoc taxonomy in `processYaml.py`.
  - *Acceptance:* the manifest hook reads build grouping from the normalized
    segment data; adding a new build-participating `basePath` requires updating
    the segment definition, not a private `_MANIFEST_ROLE_BY_BASEPATH` map.
    **Met:** `fileGeneration.buildGroups` is normalized into each `LAYOUT`
    segment record; `config/createBuildManifest.py` consumes
    `segment['buildGroup']` through the late `createArtifacts` hook.

- **T2a.2 — Rewrite the rundir makefiles to consume the `.mk`. — DONE.** Include
  the derived `.mk` and `wildcard` files within each derived dir; **delete** the
  fixed-root directory globs (`find_cpp_source_directories` over
  `PRJ_SRC_DIRS`/`SC_GEN_FILES` roots), the `YAML_FILES = $(shell find …)`
  line, and the hard-coded `CPP_SRC += …/vl_wrap.cpp` line. Keep the per-dir
  file wildcards. Re-point `A2C_PRJ_YAML` to `$prj/yaml/<name>Project.yaml`
  (a path change, not a discovery change).
  - *Acceptance:* existing `functional` examples still build and run (the
    derived `.mk` reproduces their dir set — regression surface). **Met:**
    `a2c-common.mk`/`a2c-systemc.mk` consume the manifest; functional examples
    build/run and the byte-identical gate is green.

- **T2a.3 — Build/run the green-field hierarchical fixture. — DONE (2026-06-30).**
  From its own root `rundir/`, the single hierarchical project builds, runs, and
  runs its block-level tb by name. Confirm `functional` projects are unaffected.
  - *Acceptance:* hierarchical fixture builds + runs; `functional` unchanged.
    **Met:** committed build harness (`prj/include/make/shared.mk`, root
    `Makefile`, `rundir/Makefile`); the fixture's DUT `core` runs a
    `gen → u_leaf0 → u_leaf1 → gen` loop (a `gen` block with both `dOut`/`dIn`
    via `srcport`/`dstport`, two `leaf` pass-through stages), self-driving to
    clean end-of-test; `make run core` reports "No error". The block tb uses
    external mode (`--block=hier_tb --excludeInst=u_core`, empty external).
    Structural golden regenerated (21 generated-only paths; the build harness
    under `prj/include/` is excluded by `test_layout_hierarchical.py`). Functional
    byte-identical gate green across all 8 examples.

- **T2a.4 — Confirm clangd for the single active project. — DONE (2026-06-30).**
  Verify the generated `.clangd`/`compile_commands.json` for the one active
  project covers its source set, following the seam automatically (Q-L5, low risk).
  - *Acceptance:* clangd resolves the fixture's symbols. **Met:** `make
    compdb`/`clangd` emit a `compile_commands.json` + `.clangd` covering the
    fixture's sources across both nodes (core + leaf), with `-I` for every
    manifest-derived dir. Fixed a pre-existing model-only `compdb` break (the
    forced `VL_DUT=1` pass recursed into a non-existent `verif/vl_wrap`; affected
    `helloWorld`/`nested` identically): the VL pass is now guarded on
    `A2C_VL_WRAP_DIRS` (the authoritative has-VL signal), so VL projects still
    capture VL flags while no-VL projects build the compdb from the model pass
    alone. **L2a done.**

### Phase 3 — L3: Ratify the layout decision into the registrar plan (immediate)

- **T3.1 — Reconcile and unblock the registrar plan.** The layout axis is
  already decided (`hierarchical`). Record it in
  `plan-reusable-ip-registrar.md`, reconcile S2's `functional`
  `basePath`/layout note against the decided axis, and unblock S3 (config
  relocation) and S6 (verilated trampoline) **on the layout axis** — they
  stay gated on composition M-split (see
  [`plan-composition-ordering.md`](./plan-composition-ordering.md)). `ext`
  flip status (reconciled 2026-07-10): both `blockRegistrar` `cpp`→`cppm`
  (S3.2a — the registrar is now a parent-qualified `.cppm` module) and
  `blockBase` `h`→`cppm` have landed. Both flips are owned by the registrar
  plan. Documentation/coordination only; no code in this plan.
  - *Acceptance:* registrar plan records the decision; S3/S6 marked
    layout-unblocked (composition-gated).

### Phase 4 — L4: Opt-in functional→hierarchical migration (design)

Entry condition **met** (2026-06-30): L1 and L2a are proven on the green-field
fixture, so a known-good `hierarchical` target shape exists to migrate *toward*.
This section is the **design + todo breakdown** for L4. Both design residuals
were resolved 2026-06-30 (Q-L4a/Q-L4b below), so the todos are unblocked.

**How L4 differs from the three landed phases (decides where it plugs in).**
The eval (Phase A), address (Phase B), and includes phases are **unconditional
and part of `yamlFormat: 2`**: they run on every `make migrate`, are idempotent,
and a manual TODO in any of them blocks the `yamlFormat: 2` stamp
(`migrateYaml.py::stampEligible`). L4 is different in two load-bearing ways:

- **It is opt-in, not part of the format stamp (Q-L4).** A project stays valid
  in `functional` forever; L4 runs **only** for a project that has chosen
  `hierarchical`. So its trigger is a **declared-vs-on-disk mismatch**: the
  project file sets `fileGeneration.layout: hierarchical` but the tree is still
  functional (YAML under `arch/yaml/`, no `prj/`). Idempotent: once relocated,
  it is a no-op. It must **not** gate the `yamlFormat: 2` stamp — a
  `functional` project that never opts in must still stamp clean.
- **It moves files; the other phases edit content in place.** This forces an
  **ordering** rule: relocation must run **after** eval/address/includes/stamp,
  because those phases locate and rewrite YAML *by path*, and relocation
  invalidates those paths. **Decided (Q-L4a):** a **separate invocation**
  (`migrateYaml.py --to-hierarchical` / a distinct `make` target) that
  presupposes the project is already `yamlFormat: 2`, **not** a fifth step
  folded into the unconditional `migrateProject` chain.

**The mechanical transform (functional → hierarchical), per the worked example
and Q-L6 placement rules.** Reuses the phase pattern of `migrateIncludes.py`:
standalone, text-only, never opens the DB; PyYAML `safe_load` for values +
`yaml.compose` for line/col marks; a `Report` with `applied` (mechanical) /
`manual` (TODO) lists; deletion guarded by the `GENERATED_CODE_BEGIN` marker so
a name-matched user file is never removed.

1. **Relocate authored YAML** `arch/yaml/<decomp>/*.yaml` → `<decomp>/yaml/*.yaml`
   (functional dirs are then recreated beside each `yaml/` by generation). A
   block with **no decomposition subdir** (`arch/yaml/*.yaml`, decomp="") maps to
   the **project-root node** — `yaml/<block>.yaml` and the functional dirs at the
   project root — exactly the standalone `ipLeaf` / green-field `leaf` shape. No
   node directory is synthesized (Q-L4b).
2. **Move the project file** to `prj/yaml/<name>Project.yaml`; **move build
   config** `include/` → `prj/include/`; **move integration orphans**
   (`fwIpMain`, `sc_main`, the `vl_wrap` aggregator) → `prj/fw/`, `prj/verif/`.
   `rundir/` stays at the project root.
3. **Set `fileGeneration.layout: hierarchical`** in the project file (and
   re-point `A2C_PRJ_YAML` consumers to `$prj/yaml/...`, already a path change
   per T2a.2).
4. **Delete generated functional source** (the `base/ model/ rtl/ fw/ tb/ verif/`
   decomposition subtrees), marker-guarded; recreated in the hierarchical
   location by `make newmodule`/`make gen` (plan: pure generated artifacts are
   the *non*-delicate case, recreated not hand-moved).
5. **Rewrite relative cross-node `include:` directives** — *the hard part*. An
   `include: ../common/shared_types.yaml` in `arch/yaml/top/ip_top.yaml`, once
   both files move to `top/yaml/` and `common/yaml/`, must re-root through the
   new `yaml/` levels (→ `../../common/yaml/shared_types.yaml`). Same for any
   relative path inside **user regions** of `.cpp/.cppm/.sv` that reaches a
   sibling functional dir. Unrewritable cases are **reported for manual fixup**
   (the existing manual-TODO convention), never silently rewritten.

**Todos:**

- **T4.1 — Trigger + idempotence (separate `--to-hierarchical` invocation,
  Q-L4a). — DONE (2026-06-30).** Detect the opt-in mismatch (declared
  `hierarchical` + on-disk `functional`); no-op once migrated; presuppose
  `yamlFormat: 2`. *Acceptance:* a `functional` project and an already-migrated
  `hierarchical` project are both no-ops; the `yamlFormat: 2` stamp is
  unaffected. **Met:** `pysrc/migrateLayout.py` classifies the project into
  `LAYOUT_FUNCTIONAL` / `LAYOUT_ALREADY_HIERARCHICAL` / `LAYOUT_NEEDS_MIGRATION`
  text-only (no DB), via a path-based on-disk detector (project file under
  `<prj>/<yaml>/`); `migrateYaml.py --to-hierarchical` (and `make
  migrate-hierarchical`) runs it as a separate invocation that returns before the
  unconditional phases, so the stamp is untouched; not-yet-`yamlFormat: 2` opt-in
  is reported as a `TODO_NOT_FORMAT2` blocker (exit 1). Covered by
  `unittest/test_migrate_layout.py` (registered in `run_all_tests.sh`); relocation
  itself remains T4.2/T4.3.
- **T4.2 — Relocation map. — DONE (2026-06-30).** Compute each authored YAML's
  destination (`<decomp>/yaml/`, or the **project-root node** for decomp="" blocks
  per Q-L4b — no synthesized node), the `prj/` destinations for project
  file/orphans/build config, and the generated-source delete set. *Acceptance:* a
  dry-run prints the full move/delete map for `nested` and `hierInclude` with no
  writes. **Met:** `migrateLayout._buildRelocationMap` attaches a `moves` /
  `deletes` map (text-only, no DB) to the `LayoutReport` for an unblocked
  candidate; `migrateYaml.renderLayoutReport` prints it. The functional central
  yaml root is the project file's own directory, so each authored YAML's decomp is
  its dir relative to that root and lands in `<root>/<decomp>/yaml/`; the project
  file goes to `prj/yaml/<projectName>Project.yaml`, build-config `include/` to
  `prj/include/`, and project-scope orphans (`sc_main`/`vl_wrap` → `prj/verif/`,
  `fwIpMain` → `prj/fw/`, keyed by role basename) **move** rather than delete.
  Generated source under the project's own declared `dirs:` segments is deleted,
  marker-guarded by `GENERATED_CODE_BEGIN` (a name-matched source file lacking the
  marker is reported `TODO_UNGENERATED_FILE`, never deleted). Dry-run only — writes
  nothing (verified byte-for-byte). Covered by `unittest/test_migrate_layout.py`
  (`test_decomposed_example_map` on a temp-copied `hierInclude`, plus
  `test_orphan_and_guard_map` on a synthetic fixture exercising orphans /
  build-config / marker guard). Real `nested`, the green-field fixture, and the
  non-layout `make migrate` path stay no-op. *Note (per user 2026-06-30):* the
  `vl_wrap` aggregator is currently not scaffolded by `make newmodule` and
  probably should be; T4.2 treats it as a project-scope orphan that moves. The
  move-vs-delete precedence for a marker-carrying orphan is settled here (orphans
  always move); revisit if newmodule starts creating it.
- **T4.3 — Apply relocation + layout flip. — DONE (2026-06-30).** Execute the
  move/delete map, marker-guarding every delete. *Acceptance:* tree matches the
  green-field hierarchical shape; user-content files preserved. **Met:**
  `migrateLayout._applyRelocationMap` (run from `migrateLayoutInProject` under
  `write=True`) executes the T4.2 map exactly — removes the marker-guarded
  generated-source deletes, relocates every `Move` byte-preserving
  (`_applyMove`: `makedirs` the destination parent + `shutil.move`; refuses to
  overwrite a pre-existing destination rather than risk data loss), then prunes
  the emptied source dirs (`_pruneEmptyDirs`/`_pruneUp`: only-if-empty, walking
  up toward but never removing the project root, so a dir still holding a
  user/unguarded/non-source file is kept). **Layout flip is a no-op precondition,
  not an edit:** `migrateLayoutInProject` reaches the map only when the project
  already declares `fileGeneration.layout: hierarchical` (the opt-in trigger), so
  there is nothing to flip; T4.3 writes no selector edit. A candidate with only a
  `TODO_UNGENERATED_FILE` manual item still applies its safe moves/deletes and
  leaves the flagged file in place. `migrateYaml.renderLayoutReport` now prints
  `APPLIED` under `--write`. Covered by `unittest/test_migrate_layout.py`
  (`test_apply_decomposed` on a temp-copied `hierInclude`: authored YAML →
  `<node>/yaml/`, project file → `prj/yaml/`, generated `.sv` gone, non-source
  scaffolding preserved, emptied `systemVerilog/{b,c}` pruned, moved bytes
  identical, re-run is `LAYOUT_ALREADY_HIERARCHICAL`; `test_apply_orphan_and_guard`
  on the synthetic fixture: orphans → `prj/{verif,fw}` byte-preserved, build config
  → `prj/include/`, `vl_wrap` moved not deleted, unguarded source kept + its dir
  not pruned, idempotent re-run). Live `nested`/green-field/non-layout paths stay
  no-op and untouched. **The relative cross-node `include:`/`projectFiles:` and
  user-region path rewrites remain T4.4** — a bare T4.3 tree is structurally
  hierarchical but its includes still point at the pre-move locations (bar is
  structural, not a build).
- **T4.4 — Relative cross-node include rewrite + manual reporting. — DONE
  (2026-06-30).** Re-root relative `include:` directives and user-region relative
  paths through the new `yaml/` levels; report unrewritable cases. *Acceptance:*
  `hierInclude`'s 4 cross-node includes re-root correctly; intentionally-
  unrewritable case is reported, not mangled. **Met:** two blocking issues found
  during T4.3 were resolved with the user first. (1) *Deleting generated source
  destroys user regions* — resolved by classifying files with the **merged
  fileMap** (via `processYaml.mergeProjectConfig`, the create-time base/pro/user
  merge extracted from `projectCreate.__init__` into a shared, DB-free seam):
  only recognized fully-generated file types (`blockBase`, `blockRegistrar`,
  `include`, `config`, `package`, `vlSvWrap`, `vlSvWrapBody`, `vlScWrap`) are
  deleted+recreated; every other or unrecognized/custom fileMap type MOVES
  byte-preserving (the safe default), with the hierarchical node taken from the
  authored-YAML decomposition (stripping any blockDir subdir) and the segment dir
  from `hierarchicalDirs`. (2) *`projectFiles:` breaks too* — T4.4 owns re-rooting
  it. The rewrite (`migrateLayout._planPathRewrites`/`_applyPathRewrites`) plans
  edits from the pre-move files (byte-preserved offsets stay valid on the
  relocated copies), splices only the scalar value via `yaml.compose` marks
  (comments/quoting preserved), and runs after `_applyRelocationMap` under
  `--write`. `include:`/`projectFiles:` relative entries and user-region source
  `#include`/`` `include `` are re-rooted; `$macro`/absolute are left; a reference
  resolving outside the migrated tree, or an authored YAML reached from outside
  the project root, is reported `TODO_UNREWRITABLE_PATH` and left byte-for-byte.
  Covered by `test_migrate_layout.py` (registered in `run_all_tests.sh`):
  `hierInclude` 4-reference re-root + module-`.sv` move + `*_package.sv` delete,
  a synthetic classification/orphan fixture (fully-generated delete vs
  user-editable move, root-node stays, sub-node relocates, unguarded name-match
  reported), a dedicated user-region source rewrite, and the escaping-include
  report — all asserting byte-preservation, parse, and idempotence. Verified:
  `nested`+`hierInclude` `make db`/`gen` byte-identical after the
  `mergeProjectConfig` refactor; `--to-hierarchical` dry-run on live `nested` and
  the green-field fixture stays no-op; live `examples/`+`fixtures/` and the
  non-layout `make migrate` path unchanged.
- **T4.5 — Report + wiring. — DONE (2026-07-06).** Add the `LayoutReport`
  dataclass and wire the separate invocation; keep it **out of**
  `stampEligible`. *Acceptance:* report renders applied/manual like the other
  phases. **Met:** `LayoutReport` (frozen-plus-mutable dataclass in
  `pysrc/migrateLayout.py`) carries `applied`/`manual` plus the
  `moves`/`deletes`/rewrite maps; `migrateYaml.renderLayoutReport` prints it
  (DRY-RUN / APPLIED); the `--to-hierarchical` arg and `make
  migrate-hierarchical` target run `migrateLayoutInProject` as a separate
  invocation that returns before the unconditional `migrateProject` phases, so
  `stampEligible` is untouched. Verified green by `test_migrate_layout.py`.
- **T4.6 — Validation. — VALIDATED end-to-end on `nested`; two gaps found,
  one decision open (2026-07-06).** Migrate, then `make clean && make gen &&
  make run` (and block-tb run) on the migrated tree; structural-compare
  against a committed golden. *Acceptance:* migrated `nested` and `hierInclude`
  build + run to "No error" from their `rundir/`.
  - **Proven:** an in-place migration of `examples/nested` (declared
    `layout: hierarchical`, then `migrateYaml.py --to-hierarchical --write`)
    builds and runs to **"No error"** from its `rundir/`. The experiment was
    reverted; `examples/nested` is unchanged. The working sequence is
    **migrate → harness fixup → `make newmodule` → `make gen` → `make run`.**
  - **Gap 1 — bootstrap build harness breakage. RESOLVED (2026-07-06):
    leave `include/` at the project root; do not move it into `prj/`.**
    Original problem: `migrateLayout.py:108` deliberately treats
    `Makefile`/`.f`/`.gitignore` as user-managed scaffolding and leaves them
    untouched, but it moved `include/make/shared.mk` into `prj/include/`, so
    every `include $(REPO_ROOT)/include/make/shared.mk` in the bootstrap
    Makefiles broke (two in the examples, **five** in `debayer` — see blast
    radius below). **Resolution:** the `include/` move was for tidiness only
    and is not load-bearing (build-config isolation is manifest-driven, B9),
    so `include/` (and `rundir/`) stay at the project root as user-owned entry
    points (Q-L3 amended). This retires the gap: the harness `include`
    references never break, so no scaffolding scan / auto-rewrite / build-gate
    is needed — options (a)/(b)/(c) below are all mooted. The **only** residual
    harness edit is `A2C_PRJ_YAML`, because the *project file* still moves to
    `prj/yaml/`; that is a single deterministic line the migration can write
    into the (now un-moved, root) `shared.mk` from the known relocation map.
    - **Real out-of-tree project (debayer) blast radius — verified 2026-07-06.**
      The gap is not specific to in-tree examples; a real project hits it
      harder. Examples resolve `A2C_ROOT` via `git rev-parse` (they *are* the
      builder/base repo); debayer resolves `REPO_ROOT` via `git rev-parse` and
      sets `A2C_ROOT = $(REPO_ROOT)/builder`. Either way `REPO_ROOT` is the
      project root and `include/` relocates to `prj/include/`, so
      `$(REPO_ROOT)/include/make/shared.mk` breaks identically — but debayer has
      **five** scaffolding files that include it (`Makefile`, `rundir/Makefile`,
      `rtl/Makefile`, `verif/vl_wrap/Makefile`, `docker/Makefile`) vs the
      example's two, **plus** a project-owned `-include
      $(REPO_ROOT)/include/make/systemc.mk` (a second `include/make/` file the
      examples lack), **plus** the same `A2C_PRJ_YAML`-default break, **plus**
      verilated `verif/vl_wrap` orphan relocation (L2b territory the model-only
      `nested` never exercised). This blast radius — five Makefiles plus a
      silent `-include`, none reliably detectable by static scan (variable
      indirection + soft `-include` skip) — is precisely **why the resolution
      is to not move `include/` at all** rather than to detect/rewrite the
      references. Keeping `include/` at root makes all of these references stay
      valid unchanged.
  - **Gap 2 — `make gen` alone does not recreate deleted generated files;
    `make newmodule` is required first.** The migration deletes the generated
    `base/*Base.h`, `*Includes.cppm`, `*_package.sv`; `make gen` did **not**
    recreate them (build failed on a missing `consumerBase.h`), but
    `make newmodule` scaffolds them at the hierarchical location (skipping
    existing user files), after which `make gen`/`make run` succeed. This
    matches the plan's "recreated by `make newmodule`/`make gen`" wording;
    the skill (T4.7) documents `make clean && make newmodule && make gen`.
  - **`hierInclude` acceptance corrected:** `hierInclude` is generate-only
    (no `rundir`/`model`), so its bar is "migrate + `make gen` clean", not
    "build + run". The include-rewrite itself is already covered by
    `test_migrate_layout.py`.
  - **Follow-on code/fixture work from the Gap-1 resolution (leave `include/`
    at root) — DONE (2026-07-06):**
    1. **DONE.** `pysrc/migrateLayout.py` — dropped the `include/`→`prj/include/`
       relocation (removed the `MOVE_BUILD_CONFIG` kind + step-2b sweep + the
       now-unused `_filesUnder`); `BUILD_CONFIG_DIR` is retained only to locate
       the root harness. `include/` and `rundir/` no longer move.
    2. **DONE.** `pysrc/migrateLayout.py` — `_planHarnessEdit`/`_applyHarnessEdits`
       (new `HarnessEdit` row + `report.harnessEdits`) write the single
       deterministic `A2C_PRJ_YAML = $(REPO_ROOT)/prj/yaml/<name>Project.yaml`
       line into the (root, un-moved) `include/make/shared.mk`, derived from the
       project-file move — replacing an existing assignment or inserting before
       the first makefile `include` so it wins over a2c-common.mk's `?=`. A
       project with a bespoke harness (no conventional `shared.mk`, e.g.
       `hierInclude`) is left untouched (empty harness-edits list), keeping the
       clean-vehicle "no manual items" invariant. `migrateYaml.renderLayoutReport`
       prints the harness-edits section.
    3. **DONE.** `config/project.yaml` — added `include: $root/include` to
       `hierarchicalDirs` and promoted `include` to a project-scope convention
       (`processYaml.LAYOUT_CONVENTION_KEYS`, both mode conventions +
       `LAYOUT['include']`), so the normalized layout records build config at the
       project root (parallel to `rundir`), not under `prj/`.
    4. **DONE.** Green-field fixture (`unittest/fixtures/hier-layout/`) — moved
       `prj/include/make/shared.mk` back to root `include/make/shared.mk`,
       re-pointed the root `Makefile` + `rundir/Makefile` to
       `$(REPO_ROOT)/include/make/shared.mk`, and updated
       `test_layout_hierarchical.py`'s harness exclusion. The structural golden is
       unchanged (21 paths — moving `include/` does not alter generated source),
       re-verified green.
    5. **DONE.** Skill (`migrate-project.md`) — dropped the `prj/include/`
       mention; notes `include/`/`rundir/` stay at root and only `A2C_PRJ_YAML`
       changes (every other `$(REPO_ROOT)/include/make/...` reference keeps
       working).
    - **Verification (2026-07-06):** `test_migrate_layout.py`,
      `test_layout_hierarchical.py`, `test_build_manifest.py` green;
      `test_config_template.py`/`test_migrate_yaml.py`/`test_migrate_includes.py`/
      `test_gate_yaml_format.py` green; the functional byte-identical gate across
      `examples/` PASS (pre-edit baseline vs candidate IDENTICAL for every
      example). In-place `nested` re-validation: `migrate-hierarchical` now leaves
      `include/` at root and auto-writes only the `A2C_PRJ_YAML` line — **zero
      manual harness fixup** — then `make newmodule` → `make gen` → `make run`
      builds and runs to **"No error"** from `rundir/`. Experiment reverted;
      `examples/nested` clean vs HEAD.
  - **T4.6 sign-off — DONE (2026-07-06): `examples/nested` converted to
    hierarchical in place.** The user chose `nested` (the real build+run example)
    as the committed sign-off vehicle. `make migrate-hierarchical` relocated it
    (authored YAML → `yaml/`, project file → `prj/yaml/nestedProject.yaml`, fw
    flattened to `fw/`, `arch/` pruned) with **zero manual harness fixup** —
    `include/` and both makefiles (`Makefile`, `rundir/Makefile`) were untouched;
    only the auto-written `A2C_PRJ_YAML` line changed. `make newmodule` → `gen` →
    `run` reaches **"No error"**. A committed structural golden
    (`examples/nested/expected_tree.golden`, 63 paths) + guard test
    (`unittest/test_layout_nested.py`, registered in `run_all_tests.sh`) lock the
    hierarchical file set; `nested` is removed from the functional byte-identical
    gate (now in its SKIP list) and `test_migrate_layout.py`'s functional-example
    reference was repointed to `examples/simple`. Being flat (single root node),
    `nested`'s functional segments coincide with the root, so `test_build_manifest`
    still passes. **Committing the converted tree + golden is the user's task**
    (builder/base is a user-managed submodule); everything is staged in the
    working tree, green, and left unstaged.
- **T4.7 — Skill update.** Update `migrate-project.md` with the hierarchical
  opt-in flow and the manual include/import fixups it can emit.

**Resolved design residuals (2026-06-30):**

- **Q-L4a — Invocation surface. DECIDED.** A separate `--to-hierarchical`
  invocation (its own `make` target) that presupposes `yamlFormat: 2` and runs
  after the unconditional phases — not a fifth step inside `migrateProject`. Keeps
  ordering and stamp coupling clean.
- **Q-L4b — Top-level (decomp="") block. DECIDED: follow the existing design;
  add no structure where none exists.** A block with no decomposition subdir maps
  to the **project-root node** (`yaml/<block>.yaml` + functional dirs at the
  project root), mirroring the standalone `ipLeaf` / green-field `leaf` shape. No
  node directory is synthesized and no node is named. A project with no
  decomposition nodes migrates with no nodes.

**Validation-vehicle note (flagged 2026-06-30).** `nested` (chosen vehicle) is a
**single flat `nested.yaml`, no `include:` directives, no decomposition
subdirs** — it exercises relocation + `prj/` + orphan move + layout flip, but
**not** the cross-node include rewrite (T4.4), which is L4's main risk. Add
**`hierInclude`** (8 YAML files, 2 subdirs, 4 files with `include:`) as the
include-rewrite vehicle so T4.4 is actually covered; keep `nested` as the
single-node smoke test.

### Remaining milestones

- **L2b — Composed/nested build: CLOSED/ACCEPTED (UPDATE 2026-07-22).** C0a,
  authoritative ownership, SystemC/SV generation gates, child SystemC
  discovery, owner-aware RTL directories, and VL manifest-variable consumption
  had landed; the previously-remaining items are now all satisfied — explicit
  managed SV files (S6 file->top records), active-project VL entry/source
  closure and standalone (S5), cross-project clangd (S4), and full hierarchical
  composed acceptance via L5 (B4–B13; composition Q-C3/Q-C9).

- **L4 — Opt-in migration. Entry condition MET (2026-06-30); promoted to
  "Phase 4 — L4" todos above.** Design + todo breakdown done; T4.3 onward gated
  on residuals Q-L4a (invocation surface) and Q-L4b (decomp="" node default).

- **L5 — Nested self-contained fixture (`ip_test`-derived acceptance):
  PASSED/ACCEPTED (UPDATE 2026-07-22).** Full matrix green under `make -j`
  (standalone `ip` model+VL, standalone `ipBridge` model+VL, composed `ip_test`
  model + VL-src/ip0/ip1, all `No error`); all evidence checks PASS; no code
  gaps.
  *Entry condition:* L2b. Builds and runs canonical `ip` and `ipBridge`
  standalone, then composes both under root `ip_test`. The symlinked
  `bridge/ip` provider and hierarchical root/bridge overrides exercise nested
  path ownership without copying source. It proves the C5 provider, manifest,
  registrar, harness, and explicit-managed-SV contracts. A later
  `src`/`ipLeaf` split may extend L5 with cross-project eval; it is not required
  for the canonical composition example. This is not a prerequisite for
  L1/L2a, whose primary acceptance vehicle remains the green-field
  `hierarchical` fixture (T1.5/T2a.3).

### Open design residual blocking implementation

- **T0.3 (Q-L6 internal shape) is the only design item that must be settled
  before T1.2 can begin.** Everything else in Phase 0/1 is discovery or
  mechanical. T0.1 and T0.2 can proceed immediately and in parallel.
