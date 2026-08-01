# Plan: Cross-Project Block Resolution & Ownership (composed-build blocker)

## Purpose of this document

Historical problem statement and execution record for cross-project block
resolution/ownership. **Reconciled 2026-07-24: this plan's contract residuals
are closed.** The `projectFiles:`-only lookup was closed will-not-implement,
strict scaffold ownership landed, provider positive/negative acceptance passed,
and C2/L2b/C5/L5 subsequently closed.
Written so a fresh agent with no prior session context can pick it up and
iterate. Created 2026-07-09.

**COMPOSED-RUN BLOCKER RESOLVED 2026-07-17; CONTRACT PARTIAL.** Composed multi-project
`examples/ip_test` now **builds AND runs** (`make clean gen run` = `No error`,
full base+pro suite green; `mixed`/`pySocket` deferrals excluded). The blocker
was resolved by a different mechanism than the "Settled model" `readRaw` /
`validateForeignKey` ownership sequence below:
- **`cpu` duplicate-basename clobber removed** by de-duplicating `cpu` into a
  single `common`-owned generic APB master (Option R), commit `ab75e9c`.
- **Definitions-only project owns a `hasMdl` block it never instantiates:**
  `validateDeclaredPorts` scoped to instantiated blocks (`91b69dc`), plus
  zero-instance boundary ports synthesized from the definition in
  `getBlockData`/`getBDDefinitionPorts` (`ab75e9c`, unittest
  `test_zero_instance_ported_block.py`).
- **Cross-project PLAIN-block registration ("Option B"):** the container emits
  each plain cross-project child's owning `projectName` in `createInstance`
  (derived `createInstanceProjectName` view field, emitted by
  `constructor.py`/`testbench.py`); parameterizable children stay
  assembler-scoped. Commit `4038204`.
- **BSP register-access relocated pro→base** at `common/systemc/bsp/`
  (`6791451`), enabling the `common` `cpu` firmware seam.

Also committed: authoritative order-independent ownership/provider redirection
and router reachability (`894f101`/`88d7520`); the real-child fixture and
provider link `bridge/ip -> ../ip`; owner-aware RTL paths and the final fixture
refactor (`6bbec76`); and VL wrapper manifest-variable consumption (`6113562`).

The former standalone-`ipBridge` gap is closed: `bridgeStdTop.hasTb` is enabled
and the later S5/L5 acceptance validates standalone model+VL and compdb.
Provider-override negative-path acceptance is DONE (committed `37bad48` +
`test_provider_override.py` green).

LANDED (2026-07-21): strict newmodule/fileGen scaffold skip semantics (#2).
`newModule.py` gates all three scaffold write sites on ownership
(`contextOwningProject == PROJECTNAME`), mirroring the generation skip gates;
byte-identical no-op on monolithic examples, child-owned blocks skipped on the
composed `ip_test` root. `fileGen.py` needed no change (render-only).

CLOSED (architect, 2026-07-21): the original `projectFiles:`-only
`validateForeignKey` fallback will NOT be implemented. It would conflate two
deliberately independent concepts — `include:` governs definition scope (visible
symbols / compiled context) while `projectFiles:` governs ownership/discovery
only — silently widening compilation scope and adding a second resolution path
to `validateForeignKey`, against generator discipline. It is not a correctness
gap: composed builds are green because parents explicitly `include:` the child
design YAML for scope. `include:` remains the cross-project definition-scope
contract, orthogonal to `projectFiles:`. Parent contexts still include child
design YAML for definition scope. The remainder of this document is a
design/history record, not the current execution sequence.

**Load first:** the `builder-base-development` skill (generator control flow:
`projectCreate` owns durable DB truth, `projectOpen` owns read-only views, the
DB is the single channel between them; no fallback defaults on contracted
fields; no unused flexibility; pause+ask on data-contract/core-semantic
changes). Also `manage-build` (make targets; never run `arch2code.py`
directly). Read `plans/plan-ip-project-composition.md` (FOUNDATION; owns the
reference model, boundary contract C1, ownership gate Q-C9) and
`plans/plan-composition-ordering.md` (cross-plan index).

All code anchors below were verified ~2026-07-08; line numbers drift — confirm
against current `pysrc/processYaml.py` before editing.

## Background: what already works (do NOT redo)

The IP-composition workstream lets each IP be its own arch2code project and a
parent project reference+instantiate a child. Landed + committed this session,
each reviewed:

- **Q-C10** — factory key is `{blockType, variant, projectName}`
  (`common/systemc/instanceFactory.h`); delegating overloads removed.
- **C0a** — DB config blob `CONTEXTOWNINGPROJECT` = `dict(context -> owning
  projectName)`, built in `readRaw()`, reloaded in `projectOpen`. It is
  **absolute**: the owner is the declared `projectName`, identical whether that
  project is the current build root or a referenced child.
- **PROJECTLAYOUT** — DB config blob `dict(projectName -> layoutConfig)`; each
  object's generated files resolve under its OWNING project's `$root` via
  `expandNewModulePath()` (`processYaml.py:~83`), threaded through
  `newModule.py` + `config/createBuildManifest.py`.
- **Ownership gate (DB-driven, absolute)** — `projectOpen.resolveFileOwner()`
  resolves a file's owner from `CONTEXTOWNINGPROJECT`; `systemcGen.py` and
  `systemVerilogGenerator.py` skip a file when its owner != the running
  `PROJECTNAME`. Owner-qualified language identity is now a settled composition
  prerequisite (`projectName_localName`); its remaining implementation is owned
  by the shared-definitions/Q-C8 plans.
- **Gap #1 (owner-relative moduleDir) — DONE and committed.** In
  `processSingleFile` (functional branch, ~5124-5140) a child object's
  `moduleDir` is now computed relative to the OWNING project's yaml base
  (`self.childProjectRaw[owner]['projectFileDir']`) instead of the root's
  `g.yamlBasePath`. It is a **no-op until child files are actually
  child-owned**. Authoritative ownership now makes this active in composed
  projects.

**The canonical fixture:** `examples/ip_test` has root project `ip_test`, a
standalone reusable `ip/` project, and a reusable assembler
`bridge/` (`projectName: ipBridge`). The canonical target includes
`bridge/ip -> ../ip`, a committed symlink modeling the vendored `ip` Git
submodule a real bridge repository would carry. Both
provider paths declare `projectName: ip`: `ipBridge` selects its nested path
standalone, root `ip_test` selects root `ip`, and its higher override wins in
composition. Provider paths are normalized without dereferencing symlinks.

The shared-`ip` edge remains the functional point: `ip_test` instances `ip`
(`uIp0/uIp1`) and `ipBridge` instances `ip`
(`uBridgeIp0/uBridgeIp1`)—two assemblers of one selected logical child under
distinct assembler `projectName`s. `src`/`ipLeaf`/`fwIpMain` stay inside
`ip_test`; `cpu` is a single `common`-owned generic APB master.

**Green today:** `ip` builds+runs standalone; composed `ip_top` builds+runs and
the ownership gate leaves child files byte-identical. `ipBridge` builds but is
not runnable because `bridgeStdTop` has no testbench registration.

## Historical problem (pre-2026-07-17)

The original composed **build** failed (`ipIncludesFW.h file not found`) because
the child's real source/include dirs never reach the parent build manifest.
Root cause chain:

1. **Cross-project block-type resolution is include-chain-only.**
   `validateForeignKey` (`processYaml.py:~5483`, error text ~5499 "add the
   defining file to the include: chain") resolves an `instanceType` (e.g. the
   `ip` block referenced by `ip_top`) ONLY through the referencing file's
   `include:` chain. A `projectFiles`-referenced child's blocks are in the DB
   (full parse) but not on the parent context's include chain, so resolution
   fails unless the parent `include:`s the child's design file.

2. **`include:` forces ROOT ownership.** To satisfy (1) the fixture parents
   `include:` the child design files (`ip_top.yaml` includes
   `.../ip/arch/yaml/ip/ipVariants.yaml` and
   `.../bridge/arch/yaml/bridge/ipBridge.yaml`). In `readRaw()`'s ownership BFS
   (`processYaml.py:~3538-3579`, `newFiles.insert(0, ...)` + first-read-wins
   `if f not in self.yamlAllFiles`), the root-owned `include:` reaches those
   files BEFORE the child `projectFiles` closure does, so **`ip_test` (root)
   claims ownership** of `ip.yaml`/`ipVariants.yaml`/`ipBridge.yaml`.

3. **Consequence.** Because the child design files are root-owned,
   `CONTEXTOWNINGPROJECT[ip context] == "ip_test"` (not `"ip"`). Gap #1's
   moduleDir fix only fires for child-owned contexts, so it never fires; the
   manifest emits wrong child paths (e.g. `examples/ip/arch/yaml/ip`,
   `examples/ip_test/ip/arch/yaml/ip`) instead of
   `examples/ip_test/ip/model/ip`, `.../ip/fw/include/ip`; the child dirs never
   reach the parent build.

A "design-only child YAML" workaround (`ipDesign.yaml`/`ipBridgeDesign.yaml`,
listed in the root `project.yaml` `projectFiles:` before `top/ip_top.yaml`) was
tried to force child-first ownership, but the BFS `insert(0)` ordering means a
sibling root `include:` still wins. The workaround should be **removed** as part
of the fix.

## Interdependent cluster (the composed build needs all of these)

| # | Issue | Location | Status |
|---|---|---|---|
| 1 | Child moduleDir anchored to root yaml base | `processYaml.py::processSingleFile` ~5124 | **DONE** |
| 4 | Cross-project block resolution + ownership priority | `validateForeignKey`; `readRaw` | **PARTIAL / RUN-UNBLOCKED** — authoritative ownership/provider redirection landed and composed run is green; `projectFiles:`-only FK fallback will not be implemented (decision 2026-07-21); `include:` is the scope contract |
| 3 | Router/address selection must ignore parsed child harnesses outside the active top | `config/postParseRegisterPorts.py`, `REACHABLEINSTANCES` | **LANDED** (`88d7520`) |
| 2 | `make newmodule`/`fileGen` scaffold ownership | `pysrc/newModule.py` / `templates/fileGen/fileGen.py` | **LANDED (2026-07-21)** — owner-relative paths landed, and `newModule.py` skips non-owned blocks (`contextOwningProject == PROJECTNAME`, mirroring the generation gates); no-op on monolithic, child-owned skipped in composed; `fileGen.py` unchanged |

The old `ipBridge` standalone generator crash is no longer the observed
failure. It now builds/links; `make run` fails because `bridgeStdTop` is
`hasTb: false` and therefore has no testbench registration.

## Original settled model (partially implemented)

**1. Reference — `projectFiles:` only.** A parent references a child solely by
listing `<child>Project.yaml` in `projectFiles:`; it does NOT `include:` the
child's design YAML.

**2. Resolution — cross-project fallback in `validateForeignKey`.** Resolve an
`instanceType`/block reference first through the referencing file's include
chain (intra-project, unchanged); if not found, fall back to blocks provided by
any `projectFiles`-referenced child project. A `projectFiles` reference makes
the child's blocks resolvable in the parent.

**3. Ownership — declared-child-ownership-wins.** A file within a child
project's `projectFiles` closure is owned by that child, regardless of any
parent `include:` that also reaches it. `readRaw` ownership becomes
authoritative for child closures; a sibling `include:` is a visibility
mechanism, never an ownership claim. (Removes reliance on BFS ordering.)

**4. Generation — unchanged (already built).** Ownership gate skips child-owned
files in the parent build; child generates its own; parent generates its own +
registrar trampolines; parent owns the per-variant config it instantiates,
child owns its default.

**5. Provider override — handled in `readRaw`.** On encountering a project file,
resolve the highest applicable ancestor's `projectOverrides` entry before
reading that project's design closure. Override paths are absolute or relative
to the declaring project file; the selected file must declare the requested
`projectName`. `readRaw` owns missing-target, cycle, name-mismatch, duplicate-
provider, and sibling-override errors. Normalization is lexical and must not
dereference symlinks.

Current result: design-only project shims are gone, child ownership and paths
are correct, and the composed build proceeds. Parent contexts still include
child design YAML for scope because item 2's cross-project FK fallback was not
implemented. The plan must either retain that fallback as an explicit future
contract or formally accept `include:` for visibility.

## Decisions

- **D1 — Block visibility across the reference: all child blocks.** A
  `projectFiles:` child reference makes all blocks in that child's project
  closure resolvable. A public/export subset would require new schema and is
  deferred beyond this composition milestone.
- **D2 — `include:` policy: permissive but never ownership-transferring.**
  Parents do not need child design files in their include chains. If authored,
  such an include affects scope only; the child project boundary remains the
  authoritative owner.
- **D3 — Ownership priority: authoritative in `readRaw`.** Declared project
  closures establish ownership independently of traversal order; no post-parse
  ownership repair or root/shared special case is added.
- **D4 — Router reachability.** `_findPrimaryRouter` and related address
  selection operate on the active root project's `topInstance`-reachable graph.
  Parsed standalone child harnesses therefore cannot compete in a parent build.
- **D5 — Shared definitions.** Settled in
  `plan-cross-project-shared-definitions.md`: project-local copies (Option D)
  and a referenced canonical project (Option R) are both legal. Ownership is
  never inferred from equal names or contents.

## Acceptance criteria

- **Monolithic byte-identical (hard gate):** `make clean && make gen` (+ build/
  run) for apbDecode, axiDemo, axi4sDemo, lmmiDemo (pro) all "No error", output
  byte-identical. (Exclude `mixed`, `pySocket` — pre-existing deferrals.)
- **`ip` standalone:** `examples/ip_test/ip/rundir` → gen+build+run "No error".
- **`ipBridge` standalone: PARTIAL.** `examples/ip_test/bridge/rundir` selects
  `bridge/ip` and builds/links. Run acceptance is NOT MET: `bridgeStdTop` is
  `hasTb: false`, so `make run` reports `TestBench bridgeStdTop not found`.
- **`ip_top` composed model: MET 2026-07-17.** `examples/ip_test/rundir` →
  `make db && make gen` succeed with the ownership gate leaving child files
  byte-identical; the manifest carries correct child paths; and `make run`
  reaches "No error" — the shared-`ip` accepted-duplication links in one binary
  (two `ip@variant0` registrations under distinct `projectName` keys) and
  registration resolves. (Achieved via `cpu` de-dup, definitions-only ownership,
  and plain-block registration; see the RESOLVED note at the top.)
- **Hierarchical override:** root and bridge overrides for `projectName: ip`
  are both parsed; the root selection wins and only root `ip` is emitted in the
  composed manifests. Removing the root override produces a detailed error
  listing root `ip/.../ipProject.yaml` and symlinked
  `bridge/ip/.../ipProject.yaml`.
- **Fixture boundary: PARTIAL.** No design-only child project shims remain and
  parents reference real child project files. Parent contexts still include
  child design YAML for definition scope.
- Parsing/layout unittests pass (`unittest/test_nested_ownership.py`,
  `test_contextkey_validation.py`, `test_config_template.py`,
  `test_layout_selector.py`, `test_layout_hierarchical.py`,
  `test_nested_loading.py`). Isolate known pre-existing failures
  (`test_build_manifest` on `mixed`; `test_layout_nested`/`test_migrate_layout`
  `.cppm` golden drift).

## Constraints & working notes

- `builder/base` is a submodule; do NOT stage/commit (user manages). Never
  `git stash`. `make clean`/`make gen` are freely runnable to verify.
- Every generator change must be byte-identical on the monolithic example
  suite and independently reviewed (the workstream's discipline).
- Do NOT introduce `.get(k, default)` fallbacks on contracted fields; resolve
  owner/base/context via the established contracts (`CONTEXTOWNINGPROJECT`,
  `childProjectRaw`, `resolveContextKey`, `resolveFileOwner`).
- Current sequence: make `ipBridge` runnable. Provider positive and negative
  acceptance is DONE (committed 37bad48 + test_provider_override.py green).
  Strict scaffold skip semantics are RESOLVED — LANDED
  2026-07-21 (ownership gate in `newModule.py`). The
  `projectFiles:`-only FK contract decision is MADE — will not implement
  (2026-07-21); `include:` remains the scope contract. Ownership, pathing,
  reachability, and the composed model run are already landed.

## Key file/line pointers (verify against current code)

- `pysrc/processYaml.py`: `validateForeignKey` (include-chain-only resolution);
  `_mergeOverrides` / `_selectProvider` / `readRaw`; authoritative
  `_assignOwnership`; `childProjectRaw`; `processSingleFile` owner-relative
  moduleDir (Gap #1);
  `expandNewModulePath` ~83; `resolveFileOwner`/`resolveContextKey` (added this
  session; grep for them).
- `pysrc/systemcGen.py` (~39) and `pysrc/systemVerilogGenerator.py` (~50):
  DB-driven ownership gate.
- `config/createBuildManifest.py`: emits `A2C_SC_SRC_DIRS` etc.
- `config/postParseRegisterPorts.py::_findPrimaryRouter`: #3.
- `pysrc/newModule.py`, `templates/fileGen/fileGen.py`: #2 scaffold path.
- Fixture: `examples/ip_test/{arch/yaml/project.yaml, arch/yaml/top/ip_top.yaml,
  ip/, bridge/}`.

## Related

- `plans/plan-cross-project-shared-definitions.md` (sibling facet: language-level
  identity of shared definitions — C++ module/namespace vs SV module/package,
  Options R/D, hierarchical provider selection, explicit managed SV files).
- `plans/plan-ip-project-composition.md` (FOUNDATION; C1 boundary contract,
  Q-C9 ownership gate, Q-C5/G3 address, Q-C11 FW, Q-C12 eval).
- `plans/plan-composition-ordering.md` (cross-plan index / M-split milestone).
