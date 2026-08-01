# Plan — projectOverride & File Ownership Robustness

**Status: DRAFT / OPTIONS FOR ITERATION — no committed solution.**
Purpose: decide how a file's *identity* and *ownership* are established across
projects so that (a) cross-project builds attribute generation correctly and
(b) `projectOverride` — unifying **multiple physical copies of one logical IP** —
works without editing the copies. We want to either convince ourselves a derived
(projectName-equivalence) identity can work, or move to an explicit
projectName-scoped include reference.

Related: `plan-file-ownership-classification.md`,
`plan-cross-project-shared-definitions.md`, `plan-cross-project-block-resolution.md`,
`plan-ip-project-composition.md`.

---

## 1. Invariant rules (do not violate in any option)

1. **projectFile discovery closure is the definitive ownership label.** A file is
   owned by whichever `projectFiles:` + `include:` closure reaches it. Never
   inferred from disk location.
2. **Paths compare as the whole thing, or not at all.** No basename match, no
   directory-nesting / prefix rule for identity or ownership.
3. **`projectOverride` is the stress case.** It unifies one logical project
   reached via multiple physical copies / spellings.

## 2. Previously-rejected approaches (do not repeat)

- **Directory-prefix / disk-location ownership** (`fabs.startswith(providerDir+os.sep)`,
  "longest dir wins"). Added `894f101`, removed `4a57482`. Ownership must be the
  closure label, not disk layout.
- **Name-based cross-project fallback** `_lookupInChildProjects`. Added `894f101`,
  removed `c55b909`. Bypassed include scope.
- **`resolveContextKey` basename fallback** — `4c2138a`, "temporary". Still live
  (`processYaml.py:1017-1022`). To be retired.

## 3. Current mechanism (as-is)

- **Key form:** context/include/ownership keys are **root-relative lexical
  `relpath`** from the root project dir (`getFileList`, `processYaml.py:3953/3957/3966`).
  No `realpath`. Shared by `yamlContext`, `includeName`, `contextOwningProject`.
- **Ownership:** `_assignOwnership` reference-closure BFS — correct,
  order-independent. Obeys Rule 1.
- **projectOverride:** `_mergeOverrides` (`:3981-4001`), `_selectProvider`
  (`:4003-4024`), `providerFileAliases`. Reconciles **provider project files** by
  `projectName` + relative key; does **not** reconcile the non-provider shared
  design/include files reached *through* those providers → the schism point.
- **Runtime gate:** `resolveFileOwner` → `resolveContextKey`. The gen-vs-build
  **manifest split has landed**, so the gate is now a redundant backstop for
  generation.

## 4. Two separable sub-problems

- **P1 — cross-build stamp resolution.** Largely solved by the manifest split.
  Residual cleanup: `newModule.py:346` stamps per-project-top artifacts by
  basename — fix to full context key, then delete the `resolveContextKey`
  basename fallback. **This is folded into the engine (§10), not a separate
  precursor** — the engine rewrites the same resolution path, so doing it earlier
  is churn.
- **P2 — logical identity across physical copies.** The projectOverride core.
  This is where the identity model is decided.

## 5. Pinned scenario (the projectOverride target)

An ISP integrates N sub-blocks (like debayer), each a standalone sub-project that
**nests its own physical copy of `isp_shared`**. 8 sub-blocks → **8 physical
copies** of `isp_shared`, 8 tree locations. The integrating ISP wants to declare
**one** copy the master (or add a 9th canonical copy) and have **all** references
resolve to it — **without editing the 8 sub-projects**. Each sub-project also
parses standalone with a physical pointer to its own copy (as debayer does today).

**Consequence:** `realpath` identity is **ruled out** — 8 copies are 8 distinct
inodes; no path comparison can unify them without violating Rule 2. Identity must
be **logical**.

## 6. The logical key (common to both remaining options)

Both viable options converge on the same identity:

> **logical key = `(projectName, project-relative-path)`**

- `projectName` = the definitive ownership label (Rule 1), from the projectFile
  that discovered the file.
- `project-relative-path` = the file's path relative to **its own project root**
  (the provider projectFile's dir), compared as a whole string within that
  project scope (Rule 2 — not cross-project disk nesting, not basename).

8 copies of `isp_shared/yaml/isp_types.yaml` all map to `(isp_shared,
yaml/isp_types.yaml)`. `projectOverride` declares which physical copy is the
**master root** backing that projectName (content read + artifact emission). This
is exactly a **generalization of the existing `providerFileAliases`** (which
already collapses provider *project files* by projectName+key) to *all* files
discovered through a provider.

The two options differ only in **how the logical key is obtained.**

### Option 1 — Derived (implicit): projectName-equivalence
- Keep bare includes; **no sub-project edits**. At discovery each file already
  arrives through a provider projectFile whose project declares `projectName` and
  whose root anchors the relative path — so `(projectName, projRelPath)` is
  **computable with no new syntax**. Copies sharing the key are equivalent;
  `projectOverride` picks the master.
- **Pros:** satisfies the hard "no sub-project modification" constraint; reuses/
  extends `providerFileAliases`; standalone sub-project builds unaffected.
- **Decisions it forces:**
  - **Content-divergence policy.** If the 8 copies differ (version skew),
    declaring one master makes it authoritative and discards the others. Decide:
    master-authoritative-by-design, or **detect divergence and warn/error** so
    skew is never silent. (Recommend at least a divergence error.)
  - **projectName uniqueness.** Two genuinely different projects must never share
    a projectName (false equivalence). Make it a validated invariant.

### Option 2 — Explicit: projectName-scoped include
- Include spelling carries the label: `isp_shared:yaml/isp_types.yaml` → the
  logical key directly.
- **Pros:** easier to **virtualize** — a reference need not have a physical copy
  vendored; it resolves against whatever `projectName` maps to. Explicit,
  debuggable, override-friendly.
- **Cons:** new include grammar + resolver; if *required*, it forces editing the
  8 sub-projects' includes (**violates** the no-edit constraint). Viable only as
  **additive/optional** on top of Option 1's derived engine.

## 7. They are layers, not alternatives

Option 1 is the **engine** (derive the logical key at discovery; dedup; override
picks master). Option 2 is an **optional explicit spelling** of the same key that
also unlocks virtualization (reference without vendoring). Build the engine
first; bare includes resolve via the derived key with **zero sub-project edits**;
add qualified-include syntax later as a virtualization convenience with no forced
migration.

## 8. Rule compliance

- **Rule 1:** ownership stays `projectName` from projectFile discovery. ✔
- **Rule 2:** identity is `(label, whole project-relative-path)`; projRelPath
  compared whole within project scope; ownership never inferred from
  cross-project disk nesting. ✔ (Distinct from the rejected dir-prefix approach,
  which used disk location to *infer ownership* — here disk location plays no part
  in ownership; the label does, and projRelPath is only the intra-project
  coordinate.)
- `realpath` not required (cannot help multi-copy). Basename gate retired via P1.

## 9. Mechanism sketch (Option 1 engine)

- At discovery (`readRaw` / `_selectProvider` / `getFileList`), tag each file with
  its logical key `(owningProjectName, projRelPathFromProviderRoot)` alongside the
  current physical relpath.
- Dedup contexts by logical key; `contextOwningProject` keyed by logical key →
  projectName.
- `projectOverride`: `projectName → master physical root`; the master's physical
  file backs the logical key.
- Generalize `providerFileAliases` from provider-project-files to *all*
  provider-discovered files.

## 9a. Parsing model implied by each option (decisive)

To derive `(projectName, projRelPath)` for the 8 copies and then resolve
`projectOverride`, Option 1 must **read the full reference closure — all 8
physical copies — before it can assign and reconcile.** Example: `ip1.yaml`
pulls `../isp_shared/yaml/isp_types.yaml` and `ip1`'s
`../isp_shared/prj/isp_sharedProject.yaml`; `ip2.yaml` pulls the *separate
physical* copies of the same two — and so on for all 8. Only after every copy is
read can equivalence be established and the master selected.

This gives two genuinely different parsing models. Note Model 1 reads in **two
tiers** — a cheap discovery scan over every copy, then a full parse of only the
resolved master:

- **Model 1 — scan-all, parse-master, reconcile-at-end (Option 1).**
  - *Tier 1 (every copy): discovery scan only* — extract `projectFiles` +
    `include:` (and each provider's `projectName` + root) to build the reference
    graph and derive each file's logical key. No semantic parse of types/
    structures/blocks.
  - *Reconcile:* dedup by logical key; apply `projectOverride` to select the
    master per `projectName`.
  - *Tier 2 (master only): full parse* of the one file each logical key resolved
    to, into the DB.
  - **Order-independent** — the natural extension of today's `_assignOwnership`
    (made order-independent, `4a57482`/`2c3ebd1`), so it sidesteps the
    discovery-before-project-file ordering issue.
  - **Cost is once-per-logical-file, not once-per-copy** — the heavy parse never
    scales with copy count; only the cheap scan does.
  - **Divergence detection** is *not* automatic (duplicates are never fully
    parsed), but is cheaply recoverable by **content-hashing each copy during the
    Tier-1 scan** and erroring/warning on a hash mismatch for one logical key.
  - **Requires every copy to exist** (to scan) — so it does *not* give
    virtualization (absent duplicates).

- **Model 2 — resolve-first, read-master-only (Option 2 explicit).** A qualified
  `isp_shared:...` reference + a known override map lets the parser resolve to the
  master root and read **only** that copy — the 7 duplicates need not be read (or
  even exist → true virtualization). **Cheaper**, but it requires the override to
  be known **before** includes are followed (fights the current
  discovery-before-project-file order the architect flagged), and it **forfeits
  automatic divergence detection** (the other copies are never read).

Model 1 is the smaller step from today and the safer default (only the master is
parsed; skew is caught via a scan-time hash). With the two-tier refinement, its
only remaining shortfall vs Model 2 is that copies must **exist** to be scanned —
so **virtualization (absent duplicates) is the sole distinctive payoff of
Model 2**, at the cost of the ordering shift and losing scan-time divergence
detection.

## 9b. Tier-1 scan cost — levers (reserve, do not pre-build)

If the Tier-1 discovery scan across all copies proves expensive, in priority
order:

1. **Do not use the ruamel round-trip parser for Tier-1.** ruamel's
   comment-preserving round-trip loader is heavy and is only needed for files we
   *fully parse and migrate* (the resolved master). The scan needs only
   `projectFiles`, `include:`, and `projectName` — a fast safe loader
   (`yaml.CSafeLoader`) or a targeted top-key extraction reads those reliably and
   far cheaper. This likely removes the cost before any parallelism is warranted.
2. **Parallelize the scan.** Tier-1 is embarrassingly parallel (independent
   per-file extraction) and the reconcile is already order-independent, so it is a
   clean fan-out. Today: threads help if I/O-bound (GIL released on read),
   `multiprocessing` for CPU-bound fan-out (serialization overhead). Free-threaded
   CPython (3.13t / 3.14 direction) would give true in-process thread parallelism
   for the CPU-bound parse, at the cost of a Python-version + complexity
   dependency.

**Guidance:** measure first; apply lever 1 before lever 2; treat true-parallelism
as a reserve lever, not a design driver (simplest-solution-first). The two-tier
model already caps full parsing to once-per-logical-file, so the scan is the only
per-copy cost and lever 1 alone likely suffices.

## E-stage status

- **E1 — ACCEPTED (observable).** `processYaml.py` +34/-0 (after comment
  cleanup): new `contextLogicalKey` dict + persisted `CONTEXTLOGICALKEY` blob,
  derived by `_deriveContextLogicalKey()` after `buildProjectLayout()`. Consumed
  by nobody; generation byte-identical (ip_test 205 / debayer 2337 files), unit
  suite exit 0. `projRelPath` anchored on the owning project's **`$root`**
  (`PROJECTLAYOUT[owner]['root']`) — CONFIRMED correct (reproduces
  `(common, yaml/shared_types.yaml)`; projectFile-dir would give `..`-laden
  paths). `builder-base-development` review: CLEAN on substance (contract-safe,
  correct placement, no behavior change); comment-only fixes (dropped plan-doc
  citations, condensed rationale) applied.

- **E2 CRUX (design note, must handle):** E1 anchors on `PROJECTLAYOUT[owner]
  ['root']`, which is keyed **by projectName — one root per name**. That is fine
  while each projectName has a single copy, but for the real multi-copy case (N
  distinct copies all named `isp_shared`) it cannot distinguish copies: a file in
  a non-selected copy, made relative to the single stored root, yields a
  `..`-laden `projRelPath` that would NOT match the master copy's key → no
  grouping. **E2 must derive `projRelPath` relative to each file's OWN physical
  copy root** (the provider instance it was discovered through), so distinct
  copies produce identical logical keys; then group by `(projectName,
  copy-local projRelPath)`, dedup, and let `projectOverride` pick which copy's
  physical file is the master (parsed/emitted). PROJECTLAYOUT being
  projectName-keyed is itself a multi-copy ambiguity E2 resolves via the master.

- **E2a — STOP-AND-REPORT (not landed); the E2 CRUX note above was
  UNDER-SCOPED.** Empirical finding (verified): re-anchoring `projRelPath` alone
  is necessary but far from sufficient. Root cause at `readRaw`
  (`processYaml.py:4064-4072`): when an ancestor override redirects a provider
  (`selectedKey != f`), the code records `providerFileAliases[f]=selectedKey` and
  **`continue`s WITHOUT scanning the redirected copy's own closure**. This is
  correct for the symlink/lexical-dedup case (the copy IS the master file) but
  breaks for genuinely distinct copies:
  - **Gap 1 — no per-copy root.** The copy's provider closure is never read, so
    `childProjectRaw`/`PROJECTLAYOUT` (projectName-keyed) hold only the master
    root; the copy's root (`bridge/common/prj/yaml`) is recorded nowhere.
  - **Gap 2 (decisive) — wrong owner.** The copy's design files
    (`shared_types.yaml`, `cpu.yaml`), reached only through the *including*
    project's `include:` edges, are attributed by `_assignOwnership` to the
    including project (`ipBridge`), NOT `common`. Their logical key derives as
    `(ipBridge, …)` and can never group with the master's `(common, …)`.
  - Verified red state: composed `make db` errors `Module/package identity 'cpu'
    used by two distinct contexts … 'common' and 'ipBridge'`.
  - **Real change required = the §9a Tier-1 scan-all**, not the re-anchoring the
    crux note described: SCAN (not parse) redirected copies' closures to record
    per-copy roots + enumerate members with copy-relative paths + **reattribute
    ownership to the copy's declaring `projectName`**, then group by
    `(projectName, copyRelPath)`, master-select via `projectOverride`, and
    generalize `providerFileAliases` so every non-master *member* (not just the
    provider file) aliases onto the master. Discovery-core: touches `readRaw`,
    `_assignOwnership`, a new per-copy membership/root structure, and the
    manifest/module-scan.
  - **Fixture wiring (clean part):** faithful multi-copy needs the bridge *design
    includes* repointed to the vendored copy (`../common/…`) AND the bridge-level
    `projectOverrides: common:` DROPPED (only the ROOT override unifies).
  - **Secondary (build-side):** the C++ module scan (`gen_cpp_module_map.py`,
    `a2c-systemc.mk`) dedups by lexical `normpath`, not `realpath`; once aliasing
    lands, the manifest must emit only master paths or the scan needs the same
    logical-key dedup. A stale `.gen/build.mk` listing copy paths can wedge even
    `make clean` — clear `.gen`.
  - **DECISION TO RATIFY (ownership axis):** the logical key's first element must
    be the DECLARING copy's `projectName` (`common`), not the resolved owner
    (`_assignOwnership` currently yields `ipBridge` for the copy). This makes
    **ownership reattribution in `_assignOwnership` in-scope for E2** — a real
    semantics change. Options: (1) full Tier-1 scan-all + reattribution (faithful
    to §5/§9a, discovery-core, recommended); (2) provider-only multi-copy fixture
    (narrower, does not validate the §5 "each sub-block drags its vendored copy
    via normal includes" scenario); (3) ratify the ownership axis before coding.

- **E2 IMPLEMENTATION PATH (chosen 2026-07-26, user ratified full scan-all +
  ownership reattribution).** Build the Tier-1 scan-all as a **dedicated
  standalone scanner class** (prototype-that-becomes-real), unit-tested in
  isolation, then integrate:
  - **S1** — standalone scanner class: fast-load (NOT ruamel) the FULL closure
    incl. redirected copies' own closures (which `readRaw` currently `continue`s
    past); emit the reconcile result: per-file logical key `(declaring
    projectName, copyRelPath)`, per-copy roots, logical-key groups, per-projectName
    master selection (from `projectOverride`), ownership-reattribution map, alias
    map (non-master member → master member), and per-file content hash. Unit-tested
    against multi-copy + single-copy/monolithic fixtures. NO live-path change.
  - **S2** — integrate the scanner into `readRaw`/`_assignOwnership` + manifest/
    module-scan (master-only paths); land Fixture A (distinct `bridge/common`
    copy, bridge design-includes repointed, bridge-level `projectOverrides:
    common:` dropped, root override = master); validate red→green + no-regression
    + suite.
  - **S3** — resolution/stamp cleanup: drop `resolveContextKey` basename fallback,
    `newModule.py:346` full-key stamp, stamp transition.
  - Ownership reattribution RATIFIED: logical-key first element = declaring
    `projectName`, scoped to redirected copies (single-copy parsing unchanged).

- **S1 — LANDED (standalone `pysrc/projectScan.py` `ProjectScanner`/`ScanResult`
  + `unittest/test_project_scan.py` + `fixtures/multi-copy/`, Suite 65; suite
  exit 0; `processYaml.py` untouched).** `builder-base-development` review:
  reconcile logic provably correct on fixtures; four-function reuse
  (`getFileList`/`_mergeOverrides`/`_isChildProjectFile`/`_referenceClosure`) is
  genuine single-source binding (strength). Review fixes APPLIED + VERIFIED
  (4/4 scanner tests pass; `processYaml.py` still +34/-0 untouched): stripped
  plan-stage comments; dropped unused `scan(inheritedOverrides=)` param; guard/
  diagnose a mis-targeted `projectOverrides` target (`_selectMasters`) instead of
  bare `KeyError`; friendly error on missing `dirs.root`; narrowed the
  "identical-keys" comment (the standalone scanner drops `getFileList`'s
  `dependencies` arg, so bare-basename `include:` entries would key differently).

- **S2 — LANDED + INDEPENDENTLY VERIFIED (2026-07-26).** `processYaml.py`
  +89/-57: deleted `_assignOwnership` + `_deriveContextLogicalKey` (single
  ownership implementation is now `_deriveOwnershipFromScan`, derived from
  `self.scanResult`); scanner pre-pass runs before `readRaw`; `readRaw`
  canonicalizes references onto masters via `aliasMemberToMaster` at dequeue AND
  on every `getFileList` result (result-level canonicalization is what fixes the
  include-chain circular-include error — dequeue-only left non-master keys in
  `yamlDependancies`). `_deriveOwnershipFromScan` REJECTS (printError+exit) any
  non-systemFile design context absent from the scan ownership (no silent
  default). `projectScan.py` +319: accumulates its own `yamlDependancies`
  (bare-basename key parity); BFS walks references in DECLARATION order (not set
  order) for deterministic bare-retention across PYTHONHASHSEED. Verified by me:
  both methods deleted + no dangling refs; byte-identical (only 4 ip_test yaml +
  the symlink changed, zero generated-file diffs across the sweep); scanner suite
  5/5 incl. new `test_bare_basename_include_key_parity` + `fixtures/bare-include/`;
  composed ip_test `make gen`+`make run` = "No error"; agent's full
  `run_all_tests.sh` exit 0 (Suite 61 gen-equivalence + Suite 65 scanner).
  `CONTEXTLOGICALKEY` no longer carries systemFiles entries (observable-only,
  unconsumed → output unaffected). Vestigial in `projectCreate` after the delete:
  `yamlReferences`/`rootReferences`/`providerFileAliases` (only the scanner's
  closure consumes that shape) — left populated to keep the change minimal;
  candidate S3 cleanup. **Fixture A landed**: `bridge/common` symlink → distinct
  physical copy (source+scaffold only, no generated files — the master-only
  manifest excludes it and Suite 61's glob gate would otherwise flag stale gen
  files); bridge includes repointed to `../common/...`; bridge-level
  `projectOverrides: common` DROPPED; root override selects the master. User
  staging TODO (not done by agent): `git rm` the old `bridge/common` symlink,
  `git add` the new copy.

- **CORRECTION (2026-07-26, user) — Fixture A was WRONG; reverting to symlinks.**
  Nested/multi-level `projectOverrides` are REQUIRED and every level must be
  buildable STANDALONE (bridge on its own) AND composed (top). Dropping the
  bridge-level `projectOverrides: common` in Fixture A removed the bridge's
  ability to unify its own copies → broke standalone bridge. The `ip_test/bridge`
  tree already EXISTS to exercise the nested-override case; the distinct-copy
  conversion was an unrequested addition. **DECISION: Option A** — revert Fixture A
  entirely (restore `bridge/common` symlink + bridge-level override + original
  yaml, via filesystem writes not `git restore`), keep symlinks (virtualization
  still deferred), and fix the SCANNER instead. Divergence/hash-difference
  coverage stays in the unit test (`multi-copy` fixture), NOT in ip_test.
  Key semantic read from live `_selectProvider` (4024): override-target validation
  is LENIENT (target must EXIST + DECLARE the projectName; NOT "discovered
  provider") — the S1 scanner guard was stricter than live and is what rejected
  the standalone bridge. Scanner fix (was review finding #4, now a REQUIRED bug
  fix): `_selectMasters` must reconcile the FULL inherited-override chain with
  highest-ancestor-wins (root depth 0), matching live, and use lenient target
  validation. End state after the fix: whole example suite byte-identical again
  (ip_test reverted to HEAD), scanner accepts the original symlink+nested-override
  fixture, standalone bridge + composed top both build. Dispatched to a corrected
  implementer. Review findings #1 (stale comment) + #3 (dead state) folded in; #2
  (CONTEXTLOGICALKEY persistence) kept as the accepted observable milestone (S3
  consumer). **LANDED + INDEPENDENTLY VERIFIED (2026-07-26):** fixture reverted
  byte-identical to HEAD (`git status examples/` = 0 changes); `bridge/common`
  symlink restored; edits confined to `processYaml.py` + `projectScan.py`;
  standalone `make -C examples/ip_test/bridge gen` EXIT 0 (was RED ValueError →
  GREEN); composed ip_test gen+run "No error"; all 10 buildable examples
  byte-identical; scanner suite 5/5; agent full suite exit 0. Scanner correction
  needed 3 coordinated changes (not just `_selectMasters`): `effectiveOverrides`
  (highest-ancestor-wins via `_mergeOverrides`), lenient target validation
  (mirrors live `_selectProvider` accept rule inline — not a direct call, since
  live uses printError/exit), and `scan()` override-target enqueue +
  `_assignOwnership` orphan-provider walk (the override target is named only by
  the override, never by a reference edge, so its closure must be seeded
  separately to be owned by its declaring projectName). `builder-base-development`
  review of this delta returned CHANGES-REQUESTED (5 findings); ALL ADDRESSED +
  VERIFIED: (1 HIGH) scan() now scans EVERY effectiveOverrides target via a
  post-drain pass over a shared `_drainQueue` so a globally-selected master is
  always a discovered provider (no `copyRoots` KeyError); the old inline
  lenient-accept branch became the invalid-target error path. (3) target
  acceptance goes through scan()'s single `_isChildProjectFile` provider gate
  (parity with live, no duplicated rule). (2) new `_foldEffective` tracks
  override declaring-depth and RAISES on conflicting same-depth sibling overrides
  (loud, not silent first-win). (4) `sorted(self._seen)`. (5) orphan-depth
  precedence comment. Two new scanner tests (cross-branch master discovery +
  conflict-fail-loud) with `unittest/fixtures/{cross-branch-override,
  conflict-override}/`. Re-verified by me: scanner suite 7/7; standalone bridge
  gen EXIT 0; composed ip_test gen EXIT 0 + run "No error"; all 10 examples
  byte-identical; agent full suite exit 0 (66 suites). **S2 CLOSED.**

- **S3-project — DECIDED + IN FLIGHT (2026-07-27, user directive).** Scope refined
  by a first-hand read: the ALWAYS-ON basename dependence is ONLY the project-mode
  artifact (rtl.f), which stamps `basename(topContext)` by construction
  (newModule.py:346). Context-mode files + SV packages stamp the FULL context key
  (exact-match in-build; basename fallback only in the cross-build-root case).
  Block-mode files never call `resolveContextKey`. **User directive:** project-mode
  must reference its owner by **projectName** (the logical label), not context —
  add a `--project` GENERATED_CODE_PARAM, stamp the owning projectName, resolve the
  owner directly from it (no context/basename), and RETIRE the rtl.f context hack.
  Dispatched: (1) `--project` in `textfileHelper.parseParam`; (2) newModule
  project-mode stamps `--project <PROJECTNAME>`; (3) `resolveFileOwner` returns
  `params.project` directly; (4) `systemVerilogGenerator` project branch derives
  `TOPCONTEXT` for render (owned file only — skip gate drops foreign); (5) migration
  re-stamps existing project-mode files; (6) assess whether the basename fallback
  then has any remaining consumer (context-mode cross-build-root) — remove if none,
  else report. Verify: only the rtl.f PARAM line changes, all else byte-identical;
  VL build honors the file list; full suite exit 0.
  **LANDED + INDEPENDENTLY VERIFIED (2026-07-27):** `--project` in
  `textfileHelper.parseParam`; `newModule` project-mode stamps `--project=<name>`
  (template `templates/fileGen/fileGen.py::rtlDotF_f`); `resolveFileOwner` first
  branch returns `params.project` validated against `projectLayout`;
  `systemVerilogGenerator` project branch derives `TOPCONTEXT`; migration
  `migrateProjectParam.restampProjectParam` wired into `migrateYaml.py:408` in the
  DB-backed `--sweep` phase (identifies project-mode files by fileMap `mode:project`,
  `_isGenerated`-guarded, idempotent). Verified: 13 example rtl.f files changed by
  EXACTLY one line each (`--context=X` → `--project=Y`), zero other diffs; composed
  ip_test gen+run "No error"; standalone bridge gen EXIT 0; VL builds link;
  `test_project_param.py` 4/4; agent full suite passed. `builder-base-development`
  review: S3-project LOGIC APPROVED ("functionally correct, no defect, would
  approve standalone") — reviewer confirmed owner-resolution branch/order,
  gate-guarantees-`params.project==PROJECTNAME`, byte-identical TOPCONTEXT view,
  migration (identification/placement-parity/idempotency/marker-guard/owner-only/
  sweep-safe), backward-compat, and basename retention. Findings: (1 HIGH, process
  only) the co-present S2 scan refactor is bundled in the working tree — a
  commit-SPLIT concern (S2 already reviewed in its own two gates), user's staging
  call, NOT a code change. (2 LOW) the `[TOPCONTEXT]`-for-any-`--project`-file
  render relies on there being exactly ONE `mode:project` fileMap entry (rtlDotF,
  config/project.yaml:201, top-context-rooted) — add a durable invariant comment
  (where TOPCONTEXT is set and/or the generator branch); OPEN, fold into next pass.
  (3 NIT) TOPCONTEXT-None safe by construction (definitions-only → no rtl.f
  scaffolded); reviewer says DO NOT add a guard. pySocket: reviewer confirms its
  topInstance block is defined in pySocket.yaml so TOPCONTEXT == its `--context`
  stamp → migrating it is byte-identical (genuine compat guard, safe to leave OR
  migrate).
  **KEY FINDING — basename fallback RETAINED (my earlier "maybe removable"
  hypothesis was WRONG).** Context-mode cross-build-root reads genuinely occur: in
  composed ip_test, ~9 in-tree context-mode files (e.g. `leaf/model/
  ipLeafIncludes.cppm`, `ipLeafVariantConfig.h`, `ipLeaf_package.sv`) carry a
  `--context` spelling relative to a REFERENCED CHILD's build root
  (`--context=../../ip/yaml/ipLeaf.yaml`) that differs from the composed build's
  yamlContext key (`../../leaf/yaml/ipLeaf.yaml`); they resolve ONLY via the
  basename fallback. S3-project removed the ONE project-mode (rtl.f) consumer of the
  fallback; the context-mode consumers remain. **S3-context — DECIDED + IN FLIGHT
  (2026-07-27, user directive "continue").** Design confirmed by the user: CONTEXT
  files carry BOTH `--project` (ownership) AND `--context` (render); PROJECT-mode
  files carry only `--project` (done). Scope (verified): the `--context` files are
  100% generated + disposable — the user-hosted seam (encoders, address headers
  e.g. regAddresses.h) is `--block`, NOT `--context`, so nothing with user content
  is touched; migration re-scaffolds/re-stamps them freely. Four stamp sites:
  fileMap `mode:context` `include`/`config`/`package` (newModule context scaffold)
  + the FW `<ctx>IncludesFW.h` (separate include-gen path; `includeFW` fileMap
  entry is COMMENTED OUT at project.yaml:194). Two `resolveContextKey` callers:
  `resolveFileOwner:881` (ownership — retired by `--project`, project-first branch)
  and `getContextData:1055` (render — needs the OWNED file's `--context` to
  EXACT-match the canonical `yamlContext` key). Today module vs fw stamp the same
  context with DIVERGENT spellings (`../../ip/yaml/ipLeaf.yaml` vs
  `ip/ipLeaf.yaml`) — so besides adding `--project`, the fix must NORMALIZE
  `--context` to the canonical key across all four sites (fw path is the suspect).
  Then DROP the basename fallback (reduce `resolveContextKey` to exact-match +
  unknown-context error) and PROVE it unreachable (composed ip_test + standalone
  bridge + each externalized child build green, byte-identical content). Migration
  per-project (owner-guarded, like `restampProjectParam`). Folds in S3-project
  review Finding 2 (single-top-context project-mode invariant comment). pySocket:
  migration re-stamps it (no longer left divergent).
  **LANDED + suite GREEN (2026-07-27).** Changed: `newModule.py` (context scaffold
  stamps `data['project']=contextOwningProject[context]` :475), `processYaml.py`
  (resolveFileOwner project-first branch; `resolveContextKey` basename fallback
  DELETED → exact-match + error only), `systemVerilogGenerator.py`,
  `templates/fileGen/fileGen.py` (PARAM template), `migrateYaml.py`+
  `migrateProjectParam.py` (re-stamp project+context+fw), 142 example stamp updates
  (--project added, --context normalized). Real-gen VERIFIED by me: simple +
  composed ip_test `make gen` EXIT 0 with basename gone; Suites 61 (regen all
  examples) + 63 (nested ownership: "context scaffolds carry --context +
  --project") PASS. Suite initially failed on TWO eval unit tests
  (`test_eval_canonical_view.py`, `test_eval_cpp_emit.py`) that hardcoded a BARE
  `getContextData(['ip'])` relying on the removed fallback — test-fixture issue,
  NOT a real path; FIXED (derive `ipCtx=prj.data['blocks'][getQualBlock('ip')]
  ['_context']`), full suite now exit 0 (verified). Stuck S3-context agent (looping
  on a stale sweep-wait; edits already complete) was TaskStop'd. `builder-base-
  development` review of the full delta IN FLIGHT (primary focus: is the normalized
  `--context` stamp GUARANTEED == render-time yamlContext key by construction across
  layouts?). Known review items: stale `resolveFileOwner` context-branch comment;
  `make migrate` now a hard prerequisite for old-form context stamps.
  **Review returned CHANGES-REQUESTED; PRIMARY CORRECTNESS PASSED BY CONSTRUCTION**
  (normalized --context == render key by identity in the owning build; migration +
  render gate owner-guarded; resolveContextKey reachability + migration completeness
  + invariant comment + --project threading all confirmed satisfactory).
  Consolidated fix pass IN FLIGHT (user confirmed): (A MEDIUM/real) owner-guard
  `newModule.context_create_from_template` (it iterated ALL INCLUDEFILES unfiltered
  → composed-build newmodule could scaffold a CHILD context with a parent-relative
  --context that the child build then fails to resolve with the fallback gone; fix
  = skip contexts where `contextOwningProject[ctx]!=PROJECTNAME`, matching the
  migration/render-gate); (B) reorder to `--project` BEFORE `--context` (user nit)
  via a SINGLE shared PARAM-tail helper used by BOTH `templates/fileGen/fileGen.py`
  and `migrateProjectParam._contextParamTail` (kills the lock-step drift hazard);
  (C) reword the stale resolveFileOwner context-branch comment; (D) REMOVE the
  orphaned `CONTEXTLOGICALKEY` (only written/persisted, NO getConfig consumer —
  S3 resolved ownership via --project not the logical key, so the E1 "observable
  only" blob is dead) + the dead `readRaw` shape-parallel writes
  (yamlReferences/providerFileAliases/rootReferences, proven no live
  `_referenceClosure` caller) — scanner's INTERNAL logical key stays. Re-verify:
  full suite exit 0, real gen + basename-unreachable, byte-identical except the
  reordered PARAM lines.
  **Consolidated fix ran; suite failed ONLY on synthetic Suite 63 (all real
  examples/Suite 61 PASS with the fixes).** Root cause = Fix A: the owner guard on
  `context_create_from_template` correctly stops the ROOT newmodule from scaffolding
  a CHILD-owned context, but Suite 63's `_gate_skip_proof` had the root create
  `childLeafIncludes.cppm`. **USER RESOLVED (2026-07-27):** owner-scoped create is
  CORRECT — "if a file has a fileMap it gets scaffolded; a project scaffolds only
  its own; lower-level projects newmodule their own stuff" ([[…newmodule_scaffolds_
  own_project_only]]). So Fix A STAYS; B/C/D stay; the FIXTURE is what was wrong.
  Dispatched: update `test_nested_ownership.py` so the CHILD's context files are
  scaffolded by a child-PROJECTNAME newmodule run (not the root), + fix the
  `_newmodule_no_token` docstring/PASS msg (root skips child BLOCKS **and
  CONTEXTS**). Re-verify full suite exit 0.

- **S3 COMPLETE — LANDED + INDEPENDENTLY VERIFIED (2026-07-27).** Consolidated
  fixes A/B/C/D all in; Suite 63 fixture fixed (child scaffolds its own contexts);
  full suite exit 0; `resolveContextKey` basename fallback removed and unreachable;
  `contextParamTail` is the single project-first PARAM-tail source; `CONTEXTLOGICALKEY`
  removed. Committed examples reordered to `--project`-first via the SURGICAL
  restamp-only path (NOT `--sweep`, which deletes legacy orphans on the pre-migration
  example trees): a driver calling `restampProjectParam`/`restampContextParam(write=True)`
  directly, per-project (per-subproject for composed ip_test/simple_ip), owner-guarded.
  Verified: 97 files changed, all `M`, one `GENERATED_CODE_PARAM` line each, zero
  deletions/additions, zero non-PARAM content lines, zero residual context-first stamps,
  suite green. See [[project_stamp_migration_inplace_not_rescaffold]]. Basename-hack
  retirement is DONE. (Separately, an unrelated deliverable this session:
  `unittest/run_all_tests_parallel.sh`, a safe parallel companion runner — see
  [[reference_parallel_unit_test_runner]].)

  Superseded options framing:

- **[SUPERSEDED for project-mode by the directive above] S3 — GATED ON USER DECISION (stamp-format migration).** `resolveContextKey`
  (processYaml.py:999) still has the rule-violating BASENAME fallback, and it is
  NOT purely redundant: `newModule.py:346` deliberately stamps
  `os.path.basename(topContext)` into the project-mode artifact (rtl.f)
  `GENERATED_CODE_PARAM`, and `resolveContextKey` matches that basename back. The
  durable fix (drop basename → logical-key resolution) is COUPLED: change the
  stamp to carry the stable logical key (projectName-qualified) AND change the
  resolver, AND transition every already-stamped generated file (old = build-root-
  relative / basename). Options to present: (A) lazy re-stamp on next gen (basename
  survives one transition pass then dropped); (B) one-shot `make migrate` re-stamp
  (cleanest end state, needs a migrate step); (C) defer (basename is now a
  redundant backstop for GEN after the manifest split; keep until a concrete
  cross-build-root case forces it). Non-urgent; do NOT auto-dispatch — real
  migration design decision, present to user.

- **[SUPERSEDED — resolved by the Option-A correction (revert + scanner nested-override fix); standalone bridge now builds] OPEN — standalone-bridge regression (Fixture B, out of S2 scope).**
  `make -C examples/ip_test/bridge gen` now FAILS in the scanner pre-pass: the
  standalone bridge still uses the un-migrated `ip` symlink+override pattern
  (projectFiles names the symlink path `bridge/ip`; `projectOverrides: ip` names
  the real `../../../ip`). The scanner is now authoritative and enforces the
  locked rule "an override target must be a discovered provider" (lexical keys,
  no realpath — the same rule `test_mistargeted_override_diagnostic` validates),
  so it rejects the symlink+override the old lenient `_selectProvider` tolerated.
  This is a DESIGN CONSEQUENCE, not a bug: symlink+override is no longer
  supported; distinct-copy is the migration target. Composed ip_test (the
  deliverable) is unaffected/green because the root discovers the real `ip` and
  the override target matches. Standalone bridge is not a top-level example and no
  unit suite builds it. Clean fix = migrate `ip` exactly as Fixture A migrated
  `common` (distinct `bridge/ip` copy + drop the ip override) — **Fixture B**,
  pending user go-ahead. Agent correctly STOPPED rather than exceed S2 scope.

- **S2 integration approach — SETTLED (2026-07-26, first-hand seam map).** The
  live `create()` order is: `getFileList(root)` → `readRaw()` (ruamel BFS;
  redirects ONLY provider files via `_selectProvider`, `continue`s without
  scanning the redirected copy — the E2a root cause; ends with
  `_assignOwnership()` → `contextOwningProject`) → `buildProjectLayout()` →
  `_deriveContextLogicalKey()` → … → persist `CONTEXTOWNINGPROJECT`/
  `CONTEXTLOGICALKEY` blobs. Integration, staged for per-step byte-identical
  verification:
  1. Make the scanner self-sufficient on keys: accumulate its OWN
     `yamlDependancies` during its BFS (mirroring `readRaw` lines ~4114-4117) and
     pass it into its `getFileList` calls; delete the requirement-#2 caveat
     comment. (Chicken-and-egg with live `yamlDependancies` — which is built
     DURING `readRaw` — is why the scanner builds its own over the same closure.)
  2. Run `ProjectScanner(projFile).scan()` as a PRE-pass in `create()` (Tier-1
     over all copies), hold `self.scanResult`. Side-effect-free ⇒ byte-identical.
  3. Generalize `readRaw`'s redirect to MEMBER level: before parsing a file,
     redirect any non-master member via `scanResult.aliasMemberToMaster` (not just
     provider files) so the generator parses master copies ONLY. Behavior changes
     only where a distinct copy exists (Fixture A); the 7 other examples stay
     byte-identical.
  4. Derive `contextOwningProject` from `scanResult.ownership`
     (`get(f, rootProjectName)` so system/root files fall to root) and
     `contextLogicalKey` from `scanResult.logicalKey`; DELETE the live
     `_assignOwnership` + `_deriveContextLogicalKey` (requirement #1). Byte-
     identical on all 8 (single-copy parity already asserted in the S1 test; the
     real proof is the 8-example regression).
  5. Fixture A: convert `examples/ip_test/bridge/common` symlink → a distinct real
     copy, repoint bridge design includes to `../common/...`, DROP the bridge-level
     `projectOverrides: common:` (only the ROOT override selects the master).
     Distinct copy pre-engine = duplicate-provider red; post-engine = green.
  Manifest + `gen_cpp_module_map.py` (dedups by lexical normpath) receive
  master-only paths as a consequence of parsing master-only.

- **HARD S2 REQUIREMENTS (from the S1 review — do NOT leave implicit):**
  1. **Retire the live duplicates.** S2 must make the live path DERIVE
     `contextOwningProject` and `contextLogicalKey` from `ScanResult` and RETIRE
     `processYaml.py::_assignOwnership` + `_deriveContextLogicalKey` — NOT keep
     the scanner's fork alongside the live ones (the scanner is a strict superset:
     file-keyed, multi-copy tolerant, tracks `owningProvider`). Two live ownership
     implementations is a divergence hazard and is disallowed.
  2. **Key identity at integration.** When integrated, the scanner must be fed the
     real `yamlDependancies` (as live `readRaw` passes to `getFileList`) so
     bare-basename `include:` entries key identically to the rest of the system
     (`includeName`/generated stamps). Verify key-parity on a fixture that has a
     basename-style dependency include.

## 10. Decisions

**Locked (2026-07-26):**
- **Parsing model = Model 1** (scan-all / parse-master, reconcile-at-end,
  order-independent). §9a.
- **No virtualization for now** — Option 2 (explicit `projectName:` include) is
  **deferred**; where a reference must resolve without a local copy, use a
  **symlink** as the interim substitute. Revisit qualified-include if/when true
  virtualization is needed.

**Locked (cont.):**
- **Divergence policy = WARN, non-blocking.** The Tier-1 hash compares copies for
  one logical key; a mismatch **warns** but never blocks and never forces a sync.
  Rationale: the `projectOverride`-selected master is authoritative and will
  legitimately diverge during "golden" development — a hard error would force
  constantly updating the unused copies. (If warnings prove noisy during golden
  dev, a later refinement can scope them to *non-selected copies disagreeing among
  themselves*, since that alone signals real cross-sub-project version skew.)
- **projectName global-uniqueness** = **already a requirement** (it anchors
  SystemVerilog package/namespace identity — duplicates break SV regardless).
  The Model 1 engine relies on this existing invariant for its equivalence key;
  it introduces nothing new. (If a clearer early db-time diagnostic is wanted,
  since the ownership engine now depends on it as an identity axis, that is a
  small optional add — not required.)
- **9th-copy master** declared via existing `projectOverride`
  (`projectName → master root`); no new canonical/master keyword.

**Locked (cont.):**
- **Fixture = extend `ip_test` in place (Option A).** ip_test today is only a
  *symlink-collapse* case (one physical `common`, reached via `bridge/common ->
  ../common`, same inode; `projectOverride` shape correct but deduping onto one
  copy). To become a faithful Model 1 fixture it needs a **genuinely distinct
  second physical copy** of `common` reached through a second sub-project closure,
  with the root `projectOverride: common:` designating one distinct copy as
  master and the others left unedited (still parse standalone). This change lands
  **together with the engine** (a distinct copy introduced pre-engine would break
  ip_test with a duplicate-provider collision — the intended red→green signal).

**Sequencing (revised):**
- **The former "P1" is FOLDED INTO the engine — not a separate precursor.** The
  engine rewrites `resolveContextKey`/`resolveFileOwner` (stamp → logical key)
  anyway, so retiring the basename fallback and fixing the `newModule.py:346`
  stamp to the full key are part of that one coherent keying change, done once.
  No urgency to do it earlier: the landed manifest split already stopped the
  basename gate from mattering for generation. Transition handled once inside the
  engine: existing basename-only `--context` stamps must be re-stamped (auto-heal
  on a clean gen if the `GENERATED_CODE_PARAM` line is rewritten, else a
  migration); the on-disk stamp stays the **physical** relpath key (the engine
  maps physical→logical internally).
