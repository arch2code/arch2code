# Plan: Unified YAML Migration to `yamlFormat: 2`

Status: **Gate LANDED (2026-06-18); Phase A + Phase B core libraries LANDED;
unified `migrateYaml.py` orchestrator + `make migrate` target + Phase C stamp
LANDED (2026-06-18). In-tree stamping sweep wave 1 (2026-06-19): `axi4sDemo`,
`mixed`, and the debayer product stamped and `make gen`-verified. Waves 2-3
(2026-06-19) DONE: `apbDecode`, `hierInclude`, `simple`, the `builder/pro`
`lmmiDemo`, and (wave 3) `axiDemo`, `inAndOut`, `nested`, `helloWorld` are
stamped and verified, and the `builder/migrateYaml.py` symlink is added so `make
migrate` works in the pro layout. After wave 3 every in-tree example and pro
project is stamped (see "Stamping In-Tree Projects" → "Sweep status"). The
`unittest/` fixtures were audited 2026-06-19 and found already migrated (the
sentinel is supplied uniformly via `_addrctl_helpers` and the inline-project
fixtures; gate-failure and converter suites omit it by design — see "Remaining"
→ `unittest/` entry). New-project scaffolding was completed 2026-06-19
(`newProject.py` now emits `yamlFormat: 2` and drops the retired
`addressControl:` line — see "New-Project Scaffolding"). The skill re-frame of
`address-migration.md` was completed 2026-06-19 (see "Re-framing
`address-migration.md` as the Fallback"). All planned work is landed; the lone
converter-side follow-up (the `TODO_LEAF_REGISTER_PORTS` "Step 6.2" pointer) is
RESOLVED (2026-06-23) — see that section.**
Reconciled 2026-06-18 with two landed prerequisites: the eval Python→SV core
(`pysrc/evalPyToSv.py`, exercised by Suite 19h `test_eval_py_to_sv.py`) is
committed, and the `addressControl` legacy path was retired early (refactor
Stage 8, 2026-06-12).

Landed 2026-06-18 (sequencing step 3): the `projectCreate` gate and the
`CURRENT_YAML_FORMAT = 2` constant in `pysrc/processYaml.py`
(`projectCreate._gateYamlFormat`), the in-tree stamping of every migrated
project and unittest fixture with `yamlFormat: 2`, and the gate's own suite
(`unittest/test_gate_yaml_format.py`, Suite 19i — absent / mismatched /
present branches). The gate replaced the bare Stage-8 `addressControl:`
hard-stop. Un-migrated examples (`mixed`, `axi4sDemo`) are deliberately left
unstamped so the gate rejects them until `make migrate` exists.

Landed (sequencing step 2, Phase B core): `pysrc/migrateAddressControl.py` —
the standalone `addressControl.yaml` → per-block `addressBlock:` converter
(`migrateAddressControlInProject(projectYamlPath, write=False)`), exercised by
Suite 19j `test_migrate_address_control.py` (wired after the gate suite 19i). It
reads the on-disk legacy YAML as text (PyYAML values + `yaml.compose` marks for
line numbers and verbatim value capture), never opens the database, and mirrors
`evalPyToSv`'s report/dry-run/`write` split. Automated: `addressBlock:` emission
on the resolved router (verbatim field copy incl. hex), dormant-group drop,
`InstanceGroups:`/`AddressObjects:` move to `project.yaml`, `addressControl:`
pointer removal, `postProcess:` normalization (`postParseRegister.py` →
`postParseRegisterPorts.py` + base-dup strip), and legacy-file deletion when
clean. Report-only (delegated to `address-migration.md`, word-for-word
diagnostics): interface-scope placement (Step 2), routed-leaf `registerPorts:`
authoring (Steps 4/6.2), and ambiguous/missing router resolution (Step 3). When
the manual-TODO list is non-empty it does not delete the legacy file and reports
`clean = False` so the orchestrator will not stamp.

Landed 2026-06-18 (sequencing step 2, remainder): the unified `migrateYaml.py`
CLI (top-level sibling of `arch2code.py`, `migrateYaml.py [--write]
<project.yaml>`), the `make migrate` target (in
`include/make/a2c-common.mk`, wrapping `$(A2C_ROOT)/migrateYaml.py --write
$(A2C_PRJ_YAML)`), and the Phase C stamp inside the tool. The orchestrator is
standalone (never opens the database): it loads project.yaml as text, reuses
Phase B's `_projectFileSet` for file-set discovery, runs Phase A
(`convertEvalsInFile`) on each project file and Phase B
(`migrateAddressControlInProject`), and stamps `yamlFormat: 2` only when Phase A
has no NEEDS_MANUAL rows and Phase B reports `clean`. Default is dry-run; a
project already carrying `yamlFormat: 2` short-circuits to "already migrated". A
`--write` run that cannot stamp (manual work remains) prints the BLOCKED
checklist and returns non-zero so `make migrate` signals the project is not yet
buildable. Exercised by Suite 19k `test_migrate_yaml.py` (wired after 19j),
which runs the orchestrator end-to-end over synthetic temp projects.

Note on re-running a partially-migrated project: Phase B removes the
`addressControl:` pointer on the surfacing run even when it leaves
interface-scope / leaf-`registerPorts:` TODOs (it keeps the pointer only for
unresolved-router TODOs). The orchestrator correctly refuses to stamp on that
surfacing run; a blind re-run before the manual TODOs are authored would then
see no pointer, report Phase B clean, and stamp — at which point `make gen`'s
post-parse diagnostics enforce the missing `registerPorts:`. This is Phase B's
landed idempotency contract, not an orchestrator behavior.

Skill re-frame and new-project scaffolding both LANDED 2026-06-19. No
design-only work remains in this plan.
Owner: follows the C4 symbolic-eval work and the `addressControl` refactor.

## Goal

Deliver a single, copy-pasteable migration command that brings an existing
arch2code project's user YAML up to the current authoring format, and a
generator gate that refuses to build an un-migrated project until that command
has been run.

The current format (`yamlFormat: 2`) requires:

1. **`eval` strings in the SystemVerilog subset**, not Python. The legacy
   Python idioms (`($X-1).bit_length()`, floor `//`, real `/ 2.0`) do not parse
   under the frozen SV-subset grammar that the eval pipeline now uses.
2. **Per-block address control** (`addressBlock:` on routers, `registerPorts:`
   on routed leaves, address-policy sections on `project.yaml`), not the
   project-wide `addressControl.yaml` / `addressControl:` schema.

A migrated project carries a single top-level `yamlFormat: 2` field in its
`project.yaml`. `projectCreate` reads this field first and stops with a clear,
copy-pasteable remediation command when it is absent.

## Relationship to Existing Plans

This plan is the **umbrella** that ties two already-designed migrations together
behind one command and one version sentinel. It does not re-derive their
mechanics; it sequences them, adds the cross-cutting sentinel/gate, and turns
the address migration into a tool-plus-skill-fallback pair.

| Document | Relevance |
| -------- | --------- |
| [`plan-eval-python-to-sv-migration.md`](./plan-eval-python-to-sv-migration.md) | E1.5 Python→SV `eval` converter (`pysrc/evalPyToSv.py` core + CLI). Design complete, **deferred**, no code. This plan un-defers its **core library** and folds its CLI into the unified command. |
| [`plan-eval-symbolic-emission.md`](./plan-eval-symbolic-emission.md) | E0–E5 eval pipeline. **E2 is DONE**, so SV-subset eval strings build correctly today; the "build goes red until E2" caveat from the E1.5 plan no longer applies. |
| [`plan-address-control-refactor.md`](./plan-address-control-refactor.md) | The per-block `addressBlock:` / `registerPorts:` schema (Stages 1–7 landed). Stage 8 (legacy-path retirement) is **complete** (2026-06-12): the in-generator `addressControl.yaml` loader, `validateAddressControl`, and `postParseRegister.py` are already removed. |
| `.claude/skills/address-migration.md` | Skill that drives the address migration by hand today. This plan re-frames it as the **fallback** for cases the automated converter flags. |
| [`plan-migration-tool.md`](./plan-migration-tool.md) | Scope sketch for the **C++/SV code** parameterization migration. Different artifact set; not part of this plan. |

## Locked Decisions (this session, 2026-06-11)

- **Gate behavior.** When `project.yaml` has no `yamlFormat: 2`, `projectCreate`
  stops and prints a specific command the user can paste to run the converter.
  Absent sentinel is a hard stop, not a warning.
- **One unified command.** A single entry point orchestrates the eval pass, the
  address pass, the legacy-file deletion, and the stamp. There is no separate
  per-concern CLI for the user to discover.
- **Address migration is automated where mechanical, skill-driven where not.**
  The tool converts every case it can resolve unambiguously and emits a
  structured report of the cases it cannot. `address-migration.md` becomes the
  fallback reference that explains how to fix each flagged case by hand,
  written so an AI agent can follow it.
- **One sentinel per project, stamped only when clean.** `yamlFormat: 2` is a
  single top-level field in `project.yaml`, written only after the whole project
  is format-2 clean (no Python-syntax `eval` rows remain and no `addressControl:`
  pointer remains). A project is never left partially stamped.

## Amendment 2026-06-18 — no dual-support; the sentinel is the sole detector

The original "support both spellings during a migration window" decision — the
basis for the now-removed "the legacy loader must remain" text — predates two
changes that have since landed and made it obsolete:

- The `eval` pipeline moved to the frozen SV-subset grammar (E0–E5 committed).
  Python-syntax `eval` strings no longer parse, so there is no dual-accepting
  eval loader to keep alive.
- The `addressControl` legacy path was retired early (refactor Stage 8,
  2026-06-12): the in-generator `addressControl.yaml` loader,
  `validateAddressControl`, and `postParseRegister.py` are deleted. There is no
  legacy address loader left to keep available.

Consequently the generator no longer accepts legacy input at all. The single
remaining detector of an un-migrated project is **the absence of the
`yamlFormat` sentinel**, checked by the `projectCreate` gate. An un-migrated
project is stopped at the gate, before any address or `eval` processing — it is
not parsed by a surviving legacy loader. The gate **replaces** the bare Stage-8
`addressControl:` hard-stop (`processYaml.py:5297`), which is simplified away
once the gate lands so a single remediation surface remains.

The migration tool does not depend on the removed loader: `migrateYaml.py` is
standalone and reads the on-disk `addressControl.yaml` as text (Phase B), so a
pre-migration project's file is still present on disk for the converter even
though the generator no longer loads it.

## The Sentinel and the Gate

### Sentinel

A single top-level field in the project's `project.yaml`:

```yaml
# project.yaml
yamlFormat: 2
```

- Absent is treated as the pre-migration state (legacy / format 1).
- The generator owns the current value as a constant, for example
  `CURRENT_YAML_FORMAT = 2` in `pysrc/processYaml.py`.

### Gate

Add an early check in `pysrc/processYaml.py::projectCreate`, before any legacy
`addressControl:` loading or `eval` parsing, that reads `yamlFormat` from the
merged project config:

- **Present and equal to `CURRENT_YAML_FORMAT`** — proceed normally.
- **Absent** — stop with a fatal, actionable message naming the exact command,
  for example:

  ```text
  ERROR: project '<name>' is not migrated to yamlFormat: 2.
         Run the migration, then rebuild:

             make migrate
             make clean && make gen

         (make migrate wraps: python3 $A2C/migrateYaml.py --write <project.yaml>)
  ```

- **Present but not equal** (for example a future `3`, or a malformed value) —
  stop with a distinct message stating the generator's expected version. This
  branch is minimal; it exists so a forward/garbled value fails loudly rather
  than silently passing the `!= absent` check.

The gate is the single detector of an un-migrated project. The legacy
`addressControl.yaml` loader and `postParseRegister.py` are already deleted
(`plan-address-control-refactor.md` Stage 8, complete 2026-06-12), so there is
no dual-acceptance path behind the gate: an un-migrated project is stopped at
the gate before any address or `eval` processing, not parsed by a surviving
legacy loader. The gate **replaces** the bare Stage-8 `addressControl:`
hard-stop at `processYaml.py:5297`; that error is simplified away when the gate
lands so a single remediation surface remains. The converter does not need the
removed loader — `migrateYaml.py` reads the on-disk `addressControl.yaml` as
text (Phase B).

The command the gate names should be a project **make target** (`make migrate`),
consistent with the project rule that the generator is driven through `make`,
never `python arch2code.py` directly. The make target wraps the standalone
`migrateYaml.py`.

## The Unified Command

A standalone top-level CLI, `migrateYaml.py`, a sibling of `arch2code.py` (and,
like it, not invoked directly by users — wrapped by `make migrate`). It is
standalone on purpose: a pre-migration project cannot pass the `projectCreate`
gate, so the migrator must run **without** opening the database. It reads and
rewrites YAML text directly (PyYAML for values, line-capturing loader for
targeted write-back), exactly as the E1.5 design already specifies for the eval
pass.

```
migrateYaml.py [--write] <project.yaml>
```

- **Default is dry-run.** Without `--write`, print the full report (eval
  conversions, address conversions, and every manual-fix item) and change
  nothing. `--write` applies the edits.
- **Idempotent.** Re-running a migrated project is a no-op: SV-valid evals are
  skipped, an already-present `addressBlock:` / absent `addressControl:` is
  skipped, and a present `yamlFormat: 2` short-circuits to "already migrated".

The command runs three ordered phases over the project's YAML file set
(discovered from `project.yaml` plus its `include:` chain):

### Phase A — `eval` Python→SV

Reuse the E1.5 core library `pysrc/evalPyToSv.py` (`convertExpr`) verbatim. For
each `eval` row: `ALREADY_SV` rows are skipped, `CONVERTED` rows are rewritten
with targeted text replace (only the changed spans), and `NEEDS_MANUAL` rows
(real-literal evals such as `$DWORD / 2.0`) are reported, never rewritten. The
standalone `migrateEvalExpr.py` CLI from the E1.5 plan is **superseded** by this
unified command; its core library is retained and reused unchanged.

Because **E2 is done**, a project whose evals are converted to `$clog2(...)`
builds under the current generator. The E1.5 plan's "write these edits with/after
the E2 cutover" sequencing constraint is satisfied and no longer gates this work.

### Phase B — `addressControl` → per-block schema (automated, with skill fallback)

A new core library `pysrc/migrateAddressControl.py` performs the mechanical
conversion and reports everything it cannot resolve.

**Automated (the tool rewrites these):**

- Read the legacy `addressControl.yaml`: `AddressGroups`, `RegisterBusInterface`,
  `InstanceGroups`, `AddressObjects`.
- For each **live** `AddressGroups` row (one that names a `decoderInstance`, or
  is referenced by an instance's `addressGroup:`), emit an `addressBlock:` field
  on the router block resolved from `decoderInstance`. Copy `addressGroup`,
  `addressIncrement`, `maxAddressSpaces`, `varType`, `enumPrefix`. Drop the
  retired fields `primaryDecode`, `varTypeContext`, `decoderInstance`. Set
  `upstreamPort` and `registerDecoderPort` from the legacy
  `RegisterBusInterface` value.
- **Drop dormant groups** — an `AddressGroups` row with no `decoderInstance` and
  no referencing instance is removed, not converted (matches the skill's Step 1
  rule).
- Move `InstanceGroups:` → `project.yaml` `instanceGroups:` and `AddressObjects:`
  → `project.yaml` `addressObjects:`, carrying **every active** row (including
  router-unrelated rows such as `blocks:`).
- Remove the `addressControl:` pointer from `project.yaml`.
- Normalize a project `postProcess:` override:
  - **Rewrite any reference to the legacy `config/postParseRegister.py` into the
    new `config/postParseRegisterPorts.py`** (the Stage 4 script). The legacy
    script name never survives migration.
  - Strip entries that only duplicate base scripts (the base config owns the
    canonical list; see skill Step 5). The converted `postParseRegisterPorts.py`
    is itself dropped if it duplicates a base entry, so a project that only
    overrode the register pass ends with no `postProcess:` block.
  - A block left with genuinely project-specific entries keeps them and is
    reported for review.
- **Delete `addressControl.yaml`** once no remaining `addressControl:` pointer or
  direct reference to the file exists.

**Delegated to the skill (the tool detects, reports, and points at the fix):**

- **Interface scope placement (skill Step 2).** For each router, check whether an
  `addressBus: true` interface and its supporting types/structures are already
  visible through that router file's existing `include:` chain. If not, the tool
  **cannot** safely relocate the interface (this requires reasoning about the
  include graph). It reports the router, the file, and a pointer to skill Step 2.
- **Leaf `registerPorts:` authoring (skill Steps 4 / 6.2).** The new schema needs
  every routed leaf to declare `registerPorts:` backed by a leaf-scoped
  register-bus interface. Choosing that interface and its scope is a judgment
  call; the tool reports each routed leaf that lacks `registerPorts:` and points
  at the relevant skill step rather than guessing an interface.
- **Ambiguous or missing router resolution.** If `decoderInstance` resolves to
  zero or multiple router block types, or two live groups resolve to the same
  router, the tool reports the conflict (matching the post-parse pass's own
  diagnostics) instead of authoring an `addressBlock:`.

The report groups items by `file:line`, separating "applied" edits from a
"manual TODO" checklist; each manual item names both sides of the relationship
and the skill step that resolves it. When the manual TODO list is non-empty, the
tool does **not** delete `addressControl.yaml` and does **not** proceed to the
stamp — the project is not yet format-2 clean.

### Phase C — Stamp

Only when Phase A has no remaining `NEEDS_MANUAL` rows blocking the build (real
evals are reported but, per the E1.5 design, must be hand-converted to a literal
`value:` before the project is clean) and Phase B has an empty manual-TODO list
and has removed the `addressControl:` pointer, write the single top-level
`yamlFormat: 2` into `project.yaml`. If either phase left manual work, print the
checklist and exit **without** stamping, so the gate keeps failing until the
project is genuinely clean.

## Re-framing `address-migration.md` as the Fallback

**DONE (2026-06-19).** `rules/skills/address-migration.md` was re-framed to
position the automated tool first and itself as the fallback:

- Added a lead "Run `make migrate` first" section that describes the tool's
  automated edits, the `<file>:<line>  <KIND>  <message>` manual-TODO format, and
  a mapping table from each report `KIND` (`TODO_ROUTER_RESOLUTION`,
  `TODO_INTERFACE_SCOPE`, `TODO_LEAF_REGISTER_PORTS`) to the step that resolves
  it. Step numbering (1–7) was left unchanged so the converter's literal
  `see address-migration.md Step 3` / `Step 4` message pointers still land.
- Annotated Steps 2, 3, and 4 with a **Tool report item** note quoting the exact
  converter message strings for `TODO_INTERFACE_SCOPE`, `TODO_ROUTER_RESOLUTION`,
  and `TODO_LEAF_REGISTER_PORTS` respectively.
- The diagnostics section is kept and now opens by stating it shares vocabulary
  with the tool's `manual TODO:` messages word for word.
- Added a References entry for `make migrate` / `migrateYaml.py` /
  `migrateAddressControl.py`.

Carried follow-up — RESOLVED (2026-06-23). The `TODO_LEAF_REGISTER_PORTS`
message previously pointed at "Step 4 (and Step 6.2)", but the skill has no Step
6.2 and Step 4 is the policy-section step. The message
(`migrateAddressControl._routedLeaves` emit, and the constant comment at the
head of the module) now points directly at "the registerPorts: note under
Migration Diagnostics in address-migration.md". The skill was reconciled in
lockstep: the stale "Tool report item" annotation under Step 4 was removed
(Step 4 is purely the policy-section step again) and the converter-message quote
was relocated to the `registerPorts:` note in Migration Diagnostics, where the
message now lands. The two routing tables (`address-migration.md` "Manual-TODO
kinds" and `migrate-project.md`) and Suite 19j
(`test_migrate_address_control.py`, which now asserts "Migration Diagnostics"
rather than "Step 4" in the leaf message) were updated to match.

## Stamping In-Tree Projects

The gate breaks **every** in-tree project until stamped. The migration must
stamp them all in one pass of this plan:

### Sweep status (2026-06-19)

Wave 1 stamped the three legacy/product projects below. Wave 2 (same day)
stamped the scoped examples (`apbDecode`, `hierInclude`, `simple`) and the
`builder/pro` `lmmiDemo`. Wave 3 (same day) stamped four more examples found in
the wave-2 final sweep (`axiDemo`, `inAndOut`, `nested`, `helloWorld`). After
wave 3 every in-tree example and pro project is stamped; `unittest/` fixtures
remain pending.

- **`examples/ip_test`** — already `yamlFormat: 2` (pre-stamped); `make gen`
  passes. Used as the gold reference for the nested-router (`addressBlock:`) and
  routed-leaf (`registerPorts:`) patterns.
- **`examples/axi4sDemo`** — **stamped and verified.** Dry-run clean (no manual
  TODO); `make migrate` dropped the dormant `top` group, removed the pointer,
  moved policy sections, normalized `postProcess:`, deleted the legacy
  `addressControl.yaml`, and stamped. `make clean && make gen` passes.
- **`examples/mixed`** — **stamped and verified.** Manual TODOs resolved by hand:
  the real-valued eval `REAL_HALF = "$DWORD / 2.0"` became the literal
  `value: 16.0`, and the legacy `ip1` address group (referenced by `uBlockD` /
  `uBlockF0` but with no decoder) was **dropped** per owner decision — its
  `addressGroup:`/`addressMultiples:` were removed so it falls dormant. `blockA`
  / `blockB` are top-down leaves needing no `registerPorts:`. `make clean &&
  make gen` passes after the clean-start regeneration below.
- **The debayer product `arch/yaml`** — **stamped and verified.** Seven
  Python-syntax evals converted, `addressBlock:` emitted on `apb_decode`, policy
  moved, `postProcess:` normalized away. The lone `registerPorts:` TODO on the
  top-down leaf `debayer` is advisory (it infers its bus from the router). `make
  clean && make gen` passes with no further work.

#### Wave 2 (2026-06-19)

- **`examples/hierInclude`** — **stamped and verified, clean.** No evals; all
  three `AddressGroups` rows (`top`, `ip1`, `ip2`) were dormant and dropped, the
  pointer was removed, policy moved, and the legacy `hierIncludeAddress.yaml`
  deleted — one-run stamp. `make -C arch` (db/gate) passes; SV regeneration
  produces byte-identical output (no `.sv` changed).
- **`examples/apbDecode`** — **stamped and verified.** Two evals converted to
  `$clog2(...)`; `addressBlock:` emitted on router `apbDecode`; pointer removed;
  `postProcess:` (sole `postParseRegister.py` → `postParseRegisterPorts.py`, a
  base dup) normalized away; `AddressObjects:` moved. The two
  `TODO_LEAF_REGISTER_PORTS` on `blockA`/`blockB` are advisory (single-instance
  top-down leaves), so the **two-run dance** stamped: run 1 surfaced the TODOs
  and removed the pointer, run 2 saw no pointer → Phase B clean → stamped. `make
  -C arch` (db/post-parse) then **passed with no error**, confirming the leaves
  need no `registerPorts:`. `model`/`systemVerilog` `gen` pass. Legacy
  `apbDecodeAddress.yaml` is orphaned-but-harmless (expected per the routed-leaf
  finding below).
- **`examples/simple`** — **stamped and hand-resolved.** One eval converted. The
  group `top` was a referenced-group-with-no-router (`RegisterBusInterface:
  None`, no `decoderInstance`, no router block, no register-bus interface at
  all) — a design decision. Per owner decision (mirroring `mixed`/`ip1`),
  `addressGroup: top` was removed from all six instances (`u_producer`, `u_pipe`,
  `u_consumer`, `u_in_out0/1`, `u_simple`), keeping `instGroup: allInstances`;
  the group then fell dormant and was dropped, the pointer removed, policy moved,
  and `config/address.yaml` deleted — one-run stamp. A second hand fix was
  needed for the converter postProcess bug (see Findings). `make -C examples/simple
  db` (gate/post-parse) passes. `simple` has no subdir Makefiles in this
  checkout, so there is no `make gen` path for its committed generated files; the
  db build is the authoritative check.
- **The `builder/pro` `lmmiDemo`** — **stamped and verified via `make migrate`,
  clean.** Applied through the documented `make migrate` from `rundir` (the new
  `builder/migrateYaml.py` symlink now resolves `$(A2C_ROOT)/migrateYaml.py`).
  One eval converted, dormant `top` dropped, pointer removed, `postProcess:`
  (`postParseRegister.py` + `postParseChecks.py`, both base dups) normalized
  away, policy moved, legacy `addressControl.yaml` deleted — one-run stamp.
  `make clean && make gen` passes (the lone warning — missing
  `lmmiDemoIncludes.cppm` → run `--newmodule` — is pre-existing and unrelated).

### Findings from the sweep (carry into the remaining work)

- **Orphaned legacy file for projects with routed leaves.** The converter only
  deletes the legacy `addressControl.yaml` on the surfacing run when the project
  is *clean*, but `migrateAddressControl._routedLeaves` reports a
  `TODO_LEAF_REGISTER_PORTS` for **every** routed leaf unconditionally (it cannot
  tell reusable-IP from top-down). So any project with a routed leaf is never
  clean on the surfacing run, the pointer is removed but the legacy file is not
  deleted, and the stamping re-run early-returns (no pointer) without deleting.
  Result: `examples/mixed/arch/yaml/exampleAddress.yaml` and
  `arch/yaml/config/addressControl.yaml` remain on disk, orphaned but harmless
  (nothing references them). Deciding whether to teach the converter to delete
  the file once only advisory leaf TODOs remain is a follow-up.
- **`make migrate` wiring for the pro/product layout — RESOLVED (2026-06-19).**
  The product's `A2C_ROOT` is `builder/` (the pro wrapper that symlinks
  `arch2code.py`, `config`, `templates`, … into `base/`); it had **no
  `builder/migrateYaml.py` symlink**, so `make migrate` resolved to a
  non-existent path (wave 1 migrated the product by invoking
  `builder/base/migrateYaml.py` directly). Wave 2 added the
  `builder/migrateYaml.py -> base/migrateYaml.py` symlink (mirroring the existing
  `arch2code.py` / `regrLauncher.py` symlinks). Verified end-to-end: `make
  migrate` from `lmmiDemo/rundir` resolves `$(A2C_ROOT)/migrateYaml.py` and
  stamps. `builder/` is a submodule; the symlink is left **unstaged** for the
  user to commit.
- **Converter bug — `_rewritePostProcess` orphans the trailing entry when an
  earlier `postProcess:` entry is commented out (RESOLVED 2026-06-19).** Fixed:
  the item loop now spans the whole block — consuming interleaved comment/blank
  lines instead of breaking on them — and terminates at the next top-level
  construct or EOF, tracking `contentEnd` so trailing blank separators are never
  swallowed (kept or removed). Suite 19j gained `test_commented_first_entry_no_orphan`
  (simple shape → block removed, parses, no orphan) and
  `test_mixed_keep_with_interleaved_comment` (base dup + comment dropped,
  project-specific entry kept). Original defect description below. In
  `migrateAddressControl._rewritePostProcess`, the item-collection loop stops at
  the first line after `postProcess:` that does not `lstrip().startswith("- ")`.
  `examples/simple` had a commented-out first entry:

  ```yaml
  postProcess:
    #- $a2c/config/postParseRegister.py
    - $a2c/config/postParseChecks.py
  ```

  The comment line halted collection at **zero** items, so the converter removed
  only the `postProcess:` key line and **orphaned** the real
  `- postParseChecks.py` into structurally invalid YAML (a sequence item under
  `fileGeneration:` with no owning key). The dry-run misleadingly reported
  "removed postProcess: override (only base-script duplicates remained)". Worked
  around by hand-deleting the two orphaned lines (the sole real entry was a base
  dup, so the correct end state is no `postProcess:` block). **Recommended fix:**
  have the item loop skip blank/comment lines within the block (continue rather
  than break) so interleaved comments do not truncate collection, and extend
  Suite 19j with a commented-entry fixture. Only `simple` hit this in the sweep;
  `lmmiDemo`'s contiguous `postProcess:` migrated correctly.
- **Generator guard fix surfaced by `mixed`.** A non-parameterized register-handler
  block (`blockARegs`) has `params: None`, and
  `templates/systemVerilog/moduleRegs.py::section_param_decls` called
  `parameterizedDeclLines` unconditionally, crashing on `None` (the two other
  callers guard with `if data['parameterizedDecls']:`). Added the same guard.
  `ip_test` did not expose this because its leaf is parameterized.

### Clean-start regeneration of stale generated files (warned, opt-in)

A project that could not be regenerated before migration (it was blocked at the
gate) can carry **stale generated-section directives** that predate template
moves. `examples/mixed/model/mixedConfig.h` carried
`--template=includes --section=config` from before the E5 `config` section moved
out of `includes.py` into `systemc/config.py`; `make gen` then fails with
`Unknown section 'config' for template 'includes'`.

Because `make gen` regenerates existing files **in place** (it reads each file's
embedded directive) and does **not** create missing files, the fix is a
clean-start regeneration:

1. **Warn the user** — this deletes generated artifacts. Restrict deletion to
   **fully-generated files only** (`*Config.h`, `*Includes*`, `*Base.h`, …), never
   user-implementation files (`model/*.cpp`, partially-generated `.h`) which carry
   hand-written code in their non-generated regions.
2. Delete the stale generated file(s).
3. `make newmodule` — recreates the file scaffold with the **current** FILEMAP
   template directive (e.g. `--template=config`).
4. `make gen` — fills in the generated content.

This is an opt-in step in the migration *procedure*, not part of the standalone
`migrateYaml.py` tool (which stays text-only and never opens the database or runs
the generator).
### Remaining (pending)

- **Scoped examples + `builder/pro` projects — DONE (2026-06-19).** `apbDecode`,
  `hierInclude`, `simple`, and `lmmiDemo` are stamped and verified (see Sweep
  status → Wave 2).
- **Additional un-migrated examples (discovered in the wave-2 final sweep) —
  DONE (2026-06-19, wave 3).** A grep for `addressControl:` / missing
  `yamlFormat:` across `examples/*` and `../pro/examples/*` surfaced **four more**
  in-tree example projects the gate also rejected, outside the stated wave-2
  scope: `examples/axiDemo`, `examples/inAndOut`, `examples/nested`, and
  `examples/helloWorld`. None uses legacy address control — axiDemo/inAndOut/
  nested carry an explicit `addressControl: null` line (parsed as None, so Phase
  B is a no-op) and helloWorld has no `addressControl:` at all. All four were
  **clean one-run stamps**: only `nested` needed eval conversion (five
  `($X-1).bit_length()` → `$clog2($X)`); the rest needed only the sentinel.
  Verified: `make -C arch` (db/gate) passes for all four; model gen passes
  (axiDemo, nested, helloWorld); SV regen passes (axiDemo `.gen_file`, inAndOut
  `lint`). **Caveat resolved:** the leftover `addressControl: null` key is
  **harmless** — `make db` accepts it under the post-Stage-8 generator. The three
  dead `addressControl: null` lines (and their two-line explanatory comments)
  were nonetheless removed by hand from axiDemo/inAndOut/nested as cleanup, since
  the key references a retired concept; `make db` re-verified clean for all three
  after removal. After wave 3, **every** in-tree example and pro project is
  stamped.
- **`unittest/` fixtures that build mock YAML in-process via `projectCreate` —
  DONE (2026-06-19, verified).** Audited all 67 `unittest/test_*.py` files; the
  sentinel was already applied uniformly rather than per-test, so no edits were
  required:
  - The 40 addrctl-style fixtures inherit the sentinel from a single source —
    `_addrctl_helpers.make_project` defaults `yaml_format=2` (and threads
    `yaml_format=None` for the gate-failure cases).
  - The inline-project fixtures (`test_error_*`, `test_foreign_key_lookup`,
    `test_param_const_linkage`, `test_parameter_variant_block_param_identity`,
    `test_thunker_view`) already author `yamlFormat: 2` in their temp
    `project.yaml`.
  - The eval-emission fixtures (`test_eval_sv_emit`, `test_eval_cpp_emit`,
    `test_eval_canonical_view`) consume the on-disk pre-stamped
    `examples/ip_test` project, so they pass the gate via that file.
  - Deliberate omissions (correct by design): `test_gate_yaml_format` (asserts
    the gate's failure message) and the converter suites
    `test_migrate_address_control` / `test_migrate_yaml` (operate on
    pre-migration legacy input).
  - Verified empirically: the five gate-sensitive suites
    (`test_error_leaf_no_serving_router`, `test_eval_sv_emit`,
    `test_eval_cpp_emit`, `test_eval_canonical_view`, `test_gate_yaml_format`)
    all pass.

## New-Project Scaffolding

A freshly authored new-schema project would also be blocked by the gate until
stamped. Update project scaffolding (`setup-project` / the new-project make path)
to write `yamlFormat: 2` into the generated `project.yaml` by default, so new
projects are born format-2.

**DONE (2026-06-19).** `pysrc/newProject.py::projectTemplate` now emits
`yamlFormat: 2` as the first project field, so a scaffolded project passes the
`projectCreate` gate without manual editing. The same edit also removed the
retired `addressControl: {{data.addressControlFile}}` line (and the now-unused
`addressControlFile` key from the render `data` dict) — the scaffold no longer
references the legacy address-control schema removed in refactor Stage 8.
Verified by rendering the template and asserting the sentinel is present and no
`addressControl` text or unrendered template variable remains; gate acceptance
of `yamlFormat: 2` is covered by Suite 19i (`test_gate_yaml_format`).

## Sequencing and Dependencies

1. **Un-defer the E1.5 core** (`pysrc/evalPyToSv.py`) — required by Phase A.
   **Already landed** (committed, with Suite 19h `test_eval_py_to_sv.py`). The
   E1.5 CLI is not built; the unified CLI replaces it.
2. **Build `migrateAddressControl.py`** (Phase B) and the unified
   `migrateYaml.py` orchestrator + `make migrate` target. **DONE 2026-06-18** —
   the Phase B core library landed earlier (Suite 19j
   `test_migrate_address_control.py`); the orchestrator, the `make migrate`
   target, and the Phase C stamp landed with Suite 19k `test_migrate_yaml.py`.
3. **Add the gate** to `projectCreate` and the `CURRENT_YAML_FORMAT` constant.
   Land the gate **after** the in-tree fixtures and examples are stamped (or in
   the same change), or the whole test suite and every example build breaks at
   once. **DONE 2026-06-18** — gate, constant, in-tree stamping, and Suite 19i
   landed in one change; the only residual red suites are the pre-existing C4
   parameterized-eval failures (`test_error_parameterizable`, T4.3, TT.4, TT.5),
   unrelated to the gate.
4. **Re-frame the skill** and update scaffolding. **DONE 2026-06-19** — the
   `address-migration.md` re-frame and the `newProject.py` scaffolding sentinel
   both landed (see their sections above).

`make migrate` (steps 1–2) and the skill re-frame are independent of the gate
(step 3). The gate is the last switch thrown, gated on every in-tree project
being stamped first.

`plan-address-control-refactor.md` Stage 8 (deleting `postParseRegister.py` and
the `addressControl.yaml` loader) is **already complete** (2026-06-12), so this
plan no longer carries a "legacy loader must survive" constraint. The generator
accepts only the new schema; the gate's job is to stop an un-migrated project
with an actionable `make migrate` message rather than letting it fail obscurely
in downstream processing. The converter reads the on-disk `addressControl.yaml`
as text and does not rely on the removed in-generator loader.

## Testing

Following the project's "tests must execute functionality" preference and the
existing `unittest/` conventions:

- **Phase A** — reuse / port the E1.5 converter tests (per-rule string
  conversion, numeric-equivalence, idempotency, file round-trip).
- **Phase B** — `convertExpr`-style unit cases over a small legacy
  `addressControl.yaml` fixture: assert the emitted `addressBlock:` body,
  dropped dormant groups, moved policy sections, removed `addressControl:`
  pointer, and the manual-TODO report for the interface-scope and leaf-
  `registerPorts:` cases. Assert the tool does **not** stamp or delete when the
  manual list is non-empty.
- **Gate** — an in-process `projectCreate` over a fixture lacking `yamlFormat`
  asserts the fatal message contains the `make migrate` command; a fixture with
  `yamlFormat: 2` builds; a fixture with a wrong value hits the distinct
  version-mismatch message.
- **End-to-end** — `make migrate` then `make clean && make gen` on `ip_test`
  succeeds and leaves generated output byte-identical to the pre-stamp snapshot
  (the only change is `yamlFormat: 2` in `project.yaml`).

Wire new suites into `unittest/run_all_tests.sh` after the existing eval suites
(19c–19g). The Phase B suite is **landed** as Suite 19j
(`test_migrate_address_control.py`), wired after the gate suite 19i; it executes
the converter over synthetic temp legacy projects per the assertions above.

## Out of Scope / Deferred

- **Stage 8 legacy-path retirement** (deleting `postParseRegister.py` and the
  `addressControl.yaml` loader) — **complete** (2026-06-12); no longer part of
  this plan's scope.
- **Real-eval → literal conversion** — reported, hand-converted (E1.5 rule).
- **C++/SV code parameterization migration** — `plan-migration-tool.md`.
- **Multi-`registerPorts:`, protocol-changer, multi-instance routers** — out of
  scope per the address refactor plan.

## Resolved

- **Tool/target names (2026-06-11, agreed).** The unified CLI is
  `migrateYaml.py` (sibling of `arch2code.py`), wrapped by the `make migrate`
  target. The address-conversion core library is `pysrc/migrateAddressControl.py`
  and the eval core library is the reused E1.5 `pysrc/evalPyToSv.py`.
- **Gate placement (2026-06-11, agreed).** The `yamlFormat` gate runs only in
  `projectCreate` (database build), not in `projectOpen` (read-only generator
  passes are already past a successful create), so one create-time check covers
  the whole build.
- **`postProcess:` handling (2026-06-11, agreed).** A project `postProcess:`
  reference to the legacy `config/postParseRegister.py` is **rewritten** to the
  new `config/postParseRegisterPorts.py`, not dropped; base-script duplicates
  (including the converted entry, if it duplicates a base entry) are then
  stripped. See Phase B.

## Update 2026-08-04 — two migration phases added; review item 6 closed

Two phases were added to `make migrate` for the #116 review items, both riding the
existing `yamlFormat: 2` sentinel:

- **Variant schema (`pysrc/migrateVariantSchema.py`).** Rewrites each
  `parameters:` block entry from the retired per-row list
  (`- {variant: v, param: P, value: n}`) into the nested mapping form
  (`v: {P: n}`). Standalone and text-only, scoped to `parameters:` sections so
  instance `variant:` selectors are never touched, lossless — it groups rows by
  variant in first-seen order — idempotent, and it produces no manual TODOs.
  Owner: `plan-ip-namespaces-and-parameterization.md` (review item 2).
- **Module end-label re-stamp (`pysrc/migrateModuleEndlabel.py`).** Rewrites each
  RTL block module's user-owned `endmodule: <label>` to the project-qualified
  `blockModuleName`. This one is **database-backed** and therefore part of
  `migrateYaml.py --sweep` rather than the text-conversion phase, for the same
  reason as `migrateProjectParam`: the qualified name comes from
  `BLOCKMODULENAME` / `qualifyModuleIdentity`, the same identity function the
  generator uses, not from string manipulation. Owner-gated so a composed build
  never rewrites a referenced child's file, and idempotent. A fully generated RTL
  block that closes its module inside a generated region carries no user end label
  and is left untouched. The scaffold seam was updated in lockstep
  (`newModule.py` / `fileGen.py::rtlModule` emit `endmodule: {blockModuleName}`).
  Owner: `plan-param-constant-collision.md` (review item 1).

**Review item 6 (migration guide clarification) is closed here and in the
`migrate-project` skill.** The skill now separates automated from manual per
phase and documents both new phases, plus two cases that had caused real
failures:

- **An already-`yamlFormat: 2` child still needs its own run** when the builder
  has begun qualifying cross-project identifiers. `TODO_UNMIGRATED_SUBPROJECT`
  fires only on an *unstamped* child, so an already-migrated one draws no report —
  but the parent now imports `<owner>_<ctx>` while the stale child still exports
  the bare name and keys its `-fmodule-file` entries bare, and the composed build
  fails with `module '<owner>_<ctx>' not found`, which no `TODO_*` catches.
- **A redundant import in the preamble user slot must be removed, not
  relocated.** When the generated `classDecl` region already re-emits a context
  `import` and its paired `using namespace`, a hand-written copy of that pair in
  the preamble slot is redundant, and the stray `using namespace` closes the
  module preamble so the generated imports that follow become an illegal
  import-after-declaration. Only a body-only import the generated region does not
  re-emit must stay.

The 2026-08-04 acceptance run confirmed the practical consequence of the first
case at scale: every stale generated artifact found in the committed example tree
was in a composed CHILD project, and every root-owned project was already
current.
