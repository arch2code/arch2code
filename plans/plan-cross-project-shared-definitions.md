# Plan: Cross-Project Shared Definitions & Language-Level Identity

## Purpose of this document

**Status (reconciled 2026-07-24):** the selected Option-R/provider contract and
explicit managed SV selection are delivered. Q-C8 absolute owner
qualification/Role C and the D-SD8 Option-D duplicate-definition fixture remain
deferred; replace the provisional basename-based context-owner resolution
before attempting D-SD8.

Self-contained problem statement plus candidate solution options for **how a
definition that is shared across composed arch2code projects acquires a
language-level identity** (C++ module / namespace, SystemVerilog module /
package), and how sharing, duplication, accidental collision, and
explicit physical-provider selection behave when several projects are built
together. Written so a
fresh agent with no prior session context can pick it up. Created 2026-07-09
from a design session.

**Load first:** the `builder-base-development` skill (generator control flow:
`projectCreate` owns durable DB truth, `projectOpen` owns read-only views, the
DB is the single channel; no fallback defaults on contracted fields) and
`manage-build` (make targets; never run `arch2code.py` directly).

**Scope.** This document owns the **language-level identity of shared
definitions** and the selection of one physical provider when multiple project
copies claim the same logical identity. Adjacent facets are owned elsewhere and
only referenced here:

- Block-type resolution and file-ownership priority →
  [`plan-cross-project-block-resolution.md`](./plan-cross-project-block-resolution.md).
- Directory layout (`functional` / `hierarchical`) →
  [`plan-decomp-functional-layout.md`](./plan-decomp-functional-layout.md).
- The `projectName` factory key (runtime instance registration) → composition
  Q-C10 in [`plan-ip-project-composition.md`](./plan-ip-project-composition.md).
- General IP naming / parameterization and the Q-C8 identity field →
  [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md).

All code anchors were verified 2026-07-09; line numbers drift — confirm against
current source before editing.

## Background: definition lookup is solved; provider and language identity are not

Definition lookup inside the **database** is already unambiguous. Contexts are
keyed by path, references are explicit, and resolution is strictly scope-bounded:
`lookupInScope` (`pysrc/processYaml.py:6733`) walks only the referencing
context's include-chain closure (`yamlContext[context]`) plus the implicit
`_a2csystem` fallback, and returns `(None, None)` on a miss. There is **no
DB-wide resolution fallback**; `_lookupInGlobal` (`:6720`) is reached only for
schema validators that explicitly declare `scope: global`. Two identically
named definitions in two contexts are already distinct DB rows and each
resolves within its own scope.

Composition adds two separate concerns. During DB creation, several physical
project files may claim the same logical `projectName`; that ambiguity requires
an explicit hierarchical provider selection. After selection, the generated
language / build layer must give C++ modules, namespaces, and structs, and
SystemVerilog modules and packages collision-safe identities and compile exactly
the selected project graph.

## The settled frame (decided in session, 2026-07-09)

These are inputs to this document, decided or accepted during the design
session; they are recorded (not re-litigated) here:

- **`hierarchical` directory layout is the anchor.** Composition is designed
  against per-node subtrees, not the `functional` roots.
- **`include:` = scope; `projectFiles:` = boundary; ownership = derived.**
  `include:` declares what definitions are in a context's resolution scope.
  `projectFiles:` declares what a project processes (its boundary). Ownership is
  derived from the `projectFiles:` boundary tree, is **absolute** (a stable
  function of the owning project, identical whether that project is the build
  root or a referenced child), and controls three things: who generates a file,
  where its artifacts land, and its language identity. `include:` never assigns
  ownership. (Detailed in the block-resolution doc.)
- **Identity is by owner, never by name.** Two definitions are "the same" (one
  shared type) **only** when one is a reference to the other's owning project.
  Name equality across owners is coincidence and is always treated as distinct.
  Sharing is therefore **explicit** (single owner + reference) and is **never
  inferred from a matching name**. This is the invariant that makes "same name,
  actually different" safe.
- **`projectName` is the logical project identity and must be unique in the
  effective composed graph.** A short name such as `common` is sufficient; the
  user is responsible for choosing project names that do not collide. If DB
  creation discovers multiple physical providers declaring the same
  `projectName`, it reports all providers and fails unless an applicable
  ancestor `projectOverrides` selection chooses one. No content comparison,
  hashing, revision matching, or inferred equivalence is performed.
- **Provider overrides are hierarchical.** An ancestor may select the physical
  provider for a logical `projectName` throughout its subtree; a higher
  ancestor's selection wins over a lower one. If sibling branches contain
  overrides for the same project, their common ancestor must make the unifying
  selection even when both branches happen to name the same provider. This
  preserves standalone subtree choices while making the composed root
  deterministic.
- **SV resolution uses explicit generated file lists.** `-y` search order is
  not part of project identity or provider selection. The effective project
  graph determines the exact files compiled, and each selected physical
  provider appears once.
- **Qualification uses a single underscore.** A managed generated identity is
  spelled directly from its owning project and local name, for example
  `common_shared_types_package`. Arch2code does not escape or sanitize unusual
  user names; users are responsible for choosing language-compatible names.
  `projectCreate` must nevertheless reject collisions between managed generated
  identities so every managed module/package name is unique.

## Worked example

The canonical fixture is `examples/ip_test`, split into root `ip_test`, reusable
leaf `ip`, and reusable assembler `ipBridge`. `ip` is instanced by `ip_test`
directly (`uIp0`/`uIp1`) and by `ipBridge`
(`uBridgeIp0`/`uBridgeIp1`); `ipBridge` is itself instanced by `ip_test`.

The canonical target deliberately presents two provider paths for logical
project `projectName: ip`:

```
examples/ip_test/ip/                         # root provider
examples/ip_test/bridge/ip -> ../ip          # committed provider-location symlink
```

The symlink models the vendored Git-submodule copy a real standalone
`ipBridge` project would carry without duplicating the example's source files.
It is committed. Provider selection is exercised by the composed build; the
negative-path acceptance test (remove the root override and diagnose both
providers) remains open.
Provider identity is the normalized authored path without `realpath`/symlink
dereference, so the DB sees two provider locations. `ipBridge` selects
`bridge/ip` when built standalone; root `ip_test` selects root `ip`, and that
higher override wins in the composed build. The manifest compiles only the
selected provider. Removing the root override is the canonical duplicate-
project error case.

The current fixture extracts `shared_types` and `cpu` into the referenced
`common` project, so `common` and selected `ip` exercise Option R. The planned
duplicate-definition Option D acceptance fixture is not present; it remains
gated on robust context-owner resolution and owner-qualified language identity.

### C++ manifestation

`ip` emits its block/Base/types as modules under an identity derived from the
owning project. `apbReg`'s payload structs emit as C++ structs/typedefs. The
container casts `dynamic_pointer_cast<ipBase<Config>>(...)`, so the container's
`Config` and the verilated wrapper's `Config` must be the **same C++ type**.

- **Shared by reference (one selected owner):** one `ip` module and Base type.
  Both parents instantiate the same selected implementation; casts are direct.
- **Duplicated (per-project copies):** `ip_top::apbReg` and `bridge::apbReg`
  are **distinct C++ types** even if structurally identical (C++ is nominally
  typed). They coexist only because they are in different namespaces/modules,
  and a cross-project bind between them requires the existing SystemC thunker
  to repack the payload.

C++ has a scoping construct (namespace / C++20 module), so owner-qualification
can hide in the scope and the **filename is independent** of the module name.

### SystemVerilog manifestation

arch2code feeds SV to Verilator by **library search**, not an explicit resolved
list. `common/systemVerilog/a2c.f` and each project's generated `rtl/rtl.f`
carry:

```
+libext+.sv
+incdir+.
-y .
apbDecode_package.sv      # packages listed explicitly
```

`+libext+.sv` with `-y <dir>` means: an instantiation of an undefined module
`M` is resolved by searching the `-y` directories for a file named **`M.sv`**.
Two consequences:

- **Filename is coupled to module name** in this flow (the file holding
  `module M` must be `M.sv` to be found).
- **Module and package names are a single flat, global namespace at
  elaboration.** SystemVerilog has **no scoping construct** equivalent to a C++
  namespace or module. Two `module ip`, or two `package apbReg_package`, cannot
  coexist in one elaboration.

Cases:

- **Shared by reference (one owner):** the explicit manifest contains one
  owner-qualified module and package, for example `ip_ip` and
  `common_shared_types_package`. Every consumer uses those same definitions;
  nothing collides.
- **Duplicated:** each project-local copy has a distinct owner-qualified name,
  for example `ip_test_shared_types_package` and
  `ipBridge_shared_types_package`. The package typedefs are distinct identities,
  but structurally equivalent packed RTL payloads connect directly as signals.
  `validatePorts()` remains responsible for checking compatible protocol,
  width, and field layout. No RTL thunker or conversion hardware is required.
- **Multiple provider locations for one logical project:** root `ip` and
  symlinked `bridge/ip` both declare `projectName: ip`. They must not be
  compiled twice and are not compared for equality. `readRaw` fails until the
  applicable hierarchy selects one provider through `projectOverrides`; the
  explicit manifest then contains only the selected provider.

**The `-y` mechanism is insufficient for composed builds.** It predates the
generation of the `.f` files and makes physical search-path order choose among
same-named modules. Composed builds therefore use **explicit generated file
lists**. This decouples filenames from module names and, more importantly,
makes the DB-resolved effective project graph authoritative for the exact
compiled set. The **flat-namespace constraint remains**: module and package
names must still be globally unique per elaboration, so all generated SV design
units require owner-qualified names such as `projectName_localName`.

## Why the two languages differ (the asymmetry that drives the options)

| Aspect | C++ | SystemVerilog |
|---|---|---|
| Scoping construct | namespace / C++20 module | **none** (flat global names) |
| Owner-qualification | hides in the namespace/module | must be baked into the real name |
| Filename vs identity | independent | independent under required explicit file lists |
| Two unqualified same-named things | coexist in different namespaces | collide |

The SV side is the harder one. Q-C8 Role C implementation has not landed, but
its contract is no longer deferred: composition requires owner qualification of
every managed generated SV module and package. A shared definition has one
qualified owner identity; project-local copies have distinct qualified
identities.

## Definition taxonomy (what drives the per-definition choice)

- **Project-private** — used only inside one project; its own boundary owns it;
  no cross-project concern.
- **Shared, pervasive-crossing** — reaches many project boundaries (e.g. the
  `apbReg` register bus). Usually wants a single identity. Project-local copies
  require a SystemC thunk at every crossing, although equivalent packed RTL
  payloads remain direct signal connections.
- **Shared, rare-crossing** — shared among a few projects but seldom or never
  crosses a boundary as a bound type. Duplication is tolerable here.

**Crossing-pervasiveness heuristic:** pervasive crossing usually favors a
single shared project; rare / no crossing makes per-project duplication more
tolerable. This is guidance only. Arch2code does not infer sharing or
automatically extract definitions—the user decides when local definitions
should be pulled into a shared project.

## Solution options

### Option R — Shared by reference (single canonical owner)

The definition lives in **one owning project** (for `shared_types`, its own
IP-like project placed at the dominator of its consumers, referenced
*downward*, never reached up into). Every consumer references that one owner, so
there is one canonical identity.

- **C++:** one namespace/module; direct binds and casts; filename free.
- **SV:** one owner-qualified module / package, selected once by the explicit
  manifest; byte-identical to monolithic direct binds.
- **Provider resolution:** the diamond (`ip` via `ip_top` and via `ipBridge`)
  collapses to one entry when both references resolve to the same selected
  physical provider. Multiple physical providers declaring the same
  `projectName` are an error by default, not candidates for automatic
  de-duplication. An ancestor `projectOverrides` declaration must explicitly
  select one; compatibility and version correctness are the user's
  responsibility. The selected provider's dirs are `-I`'d / compiled once.
- **Requires:** reference resolution; a generate-before-build ordering for the
  owner; hierarchical provider resolution; and an explicit manifest of the
  effective project graph.
- **Standalone:** the owner builds standalone with its full artifact set; a
  consumer that references it declares a resolvable dependency (the "build the
  library first" model).

### Option D — Duplication (per-project copies reconciled at boundaries)

Each project carries its own copy of the definition under its own
owner-qualified identity; where two copies meet at a boundary they are
reconciled according to the target language.

- **Thunker facts (verified):** `projectCreate.validatePorts()` performs the
  structural equivalence check; the view pass `getBDCrossInterfaceBinds`
  (`processYaml.py:2041`) / `buildThunkerView` (`:2131`) records already-valid
  binds; `intf_gen_utils.py` `sc_declare_thunkers` (`:723`) emits a
  `<channelType>_port_thunker` that repacks between the two structurally-
  equivalent-but-distinct payload types. It fires at `ports:` connections and
  register-bus (`registerPorts:`) child binds — exactly the IP boundary.
- **C++:** owner-namespaced copies coexist; each cross-project bind gets a
  thunk (a repack member).
- **SV:** modules and packages carry owner-qualified names because of the flat
  namespace. Structurally equivalent packed payloads connect directly through
  the standard parameterized interfaces as bits; no RTL thunker or conversion
  hardware is needed. Q-C8 Role C naming is required pending implementation.
- **Cost / caveats:** N source or identity copies to keep in sync; structural
  drift is caught by `validatePorts` **only at connected boundaries**, and
  **semantic** drift (same layout, different meaning) is never caught; a
  SystemC thunk repacks each crossing while RTL remains a direct connection.
  Maintaining the copies and model thunks makes Option D better suited to
  rare-crossing definitions.

### Migration from D to R

Both options are supported architectural states; Option D is not an error or a
temporary compatibility mode. It lets independently developed projects keep
their own owner-qualified definitions and compose safely. When users decide
that several local definitions should have one nominal identity, they migrate
explicitly:

1. Create an independent shared project (for example `projectName: common`)
   owning the definitions.
2. Change consumers to reference that project instead of their project-local
   copies.
3. Migrate consumers incrementally if desired. During the mixed state, local
   and shared identities coexist; SystemC uses boundary thunkers and compatible
   packed RTL remains directly connected.
4. Once all consumers reference `common`, the definition has one canonical
   identity and the boundary thunkers for it disappear.

`projectOverrides` serves the related but distinct physical-provider problem:
after `common` is an independent logical project, a composed tree may contain
several vendored copies of it. The override selects which one supplies the
single `common` identity. It does not infer that embedded project-local
definitions are equivalent or extract them automatically.

### Requirement E1 — replace `-y` library search with generated explicit file lists

Because the `.f` files are already generated and the generator has full
file-level information, module resolution moves from `-y` filename search to an
**explicit generated file list**. This decouples the SV filename from the
module name and makes the DB-selected provider graph, rather than search order,
control the exact compiled set. Each selected project is emitted once. The
**flat-namespace constraint is unaffected**—owner qualification is still
required for modules and packages. All arch2code-managed project RTL is listed
explicitly. Users may still add `-y` directories for unmanaged sources. Fixed
arch2code system libraries may remain under `-y`; converting those libraries is
not a composition prerequisite.

### Requirement E2 — hierarchical physical-provider overrides

It is normal for a Git tree to contain multiple vendored/submodule copies of a
dependency, for example one `common` beneath each component. When `readRaw`
discovers multiple project-file paths declaring the same `projectName`, it
reports the duplicate providers and fails. The user resolves
the ambiguity by selecting one physical provider at an applicable ancestor:

```yaml
projectOverrides:
  common: ./common/commonProject.yaml
```

The selection redirects references to `common` throughout that ancestor's
subtree. The override path is absolute or resolved relative to the project file
that declares it; it is a standalone `projectName`-to-location mapping and may
introduce a provider not otherwise named by that project's `projectFiles`.
When `readRaw` encounters a project with that `projectName`, it discards that
physical project file and redirects to the selected provider. The selected
provider must declare the same `projectName`.

A higher ancestor selection supersedes a descendant selection. If two sibling
branches contain overrides for the same `projectName`, their common ancestor
must also select the provider, even if the sibling paths resolve to the same
location. “Top level” therefore means the highest applicable ancestor in the
current composition, not necessarily the repository root.

`readRaw` owns redirect resolution and the detailed errors for missing targets,
cycles, project-name mismatch, duplicate providers without an applicable
override, and sibling overrides without a common-ancestor selection. Repeated
references to the same normalized project-file path are one physical provider;
different normalized authored paths are different providers. Path normalization
must not dereference symlinks: the canonical fixture's `ip/` and `bridge/ip`
paths intentionally identify two provider locations even though the latter is
a symlink to the former. No content or filesystem identity comparison is
performed. The override is the user's assertion that the selected provider is
the one the composition should use.

### Underpinning U1 — owner-qualified language identity (Q-C8)

All of the above rest on the generated language identity being an **absolute,
owner-qualified** function of the owning project. The implementation still has
bare-stem seams, but the contract is settled: `contextModuleIdentity` must use
the owner-qualified identity. Bare stems are unsafe the moment two projects
share a file stem for unrelated definitions — the "same name, actually
different" hazard. The logical `projectName` is also the stable key used by
explicit provider resolution and the generated manifests. Owner-qualified
identity is therefore a **prerequisite for collision safety in every model**,
not only for duplication. Its C++ half (Role A) has landed; the SV half (Role C)
remains implementation work, not an open design decision. The language spelling
uses a direct single-underscore composition
(`projectName_localName`); `projectCreate` validates uniqueness of the managed
result rather than escaping or sanitizing user names.

## Known limitation — ownership-gate context resolution (provisional, must close)

**Status: provisional fix landed 2026-07-10; robust replacement deferred and
REQUIRED before the D-SD8 duplicate-basename fixture lands.**

**Update 2026-07-17.** The composed `ip_test` build+run is now green, but the
`cpu` duplicate-basename clobber that blocked the composed *run* was resolved by
**de-duplication, not by the robust replacement below**: `cpu` was extracted
into a single `common`-owned generic APB master (the D-SD5 "extract into a
referenced shared project" / Option R path), commit `ab75e9c`. This removed the
only live duplicate-basename collision, so the provisional basename-match fix
still holds. The robust `resolveContextKey` replacement remains **deferred** and
is still REQUIRED before a genuine D-SD8 duplicate-definition fixture (two
project-local `shared_types.yaml`) can land — that fixture is not present.

Commit `6bbec76` also moved generated cross-project RTL paths from authored YAML
directories to each context owner's RTL output directory. Commit `6113562`
makes VL wrapper Makefiles consume `A2C_VL_WRAP_DIRS`. These are C2/L2b
discovery progress, not D-SD7 completion: generated `rtl.f` still uses `-y` for
managed modules, so explicit managed SV module lists and full VL validation
remain open.

### Symptom that was fixed

Composed `examples/ip_test` `make gen` aborted in the generator ownership gate
(`systemcGen.py` / `systemVerilogGenerator.py` → `resolveFileOwner` →
`resolveContextKey`, `pysrc/processYaml.py`). A `GENERATED_CODE_PARAM` context
spelling is written relative to the build root that generated the file. A file
generated by a referenced child project's own standalone build therefore carries
a child-root-relative spelling (e.g. `bridge/ipBridge.yaml`) that does not equal
the composed build's key for the same physical context
(`../../bridge/arch/yaml/bridge/ipBridge.yaml`). `resolveContextKey` matched only
an exact key or a bare basename, so the directory-prefixed foreign spelling
resolved to nothing and the gate exited before it could read
`contextOwningProject` and skip the child-owned file.

### Provisional fix (what is in the tree now)

`resolveContextKey` now canonicalizes the incoming name by **filename basename**
before matching against the basenames of the known `yamlContext` keys. This is
resolution-only: single-project builds always hit the exact-key match and are
byte-identical, and the composed build now identifies each child-owned file's
absolute owner via `contextOwningProject` and skips it.

### Why this is provisional, not robust

The mechanism assumes **every context file has a globally unique basename in the
composed database.** A file's basename is stable across build roots, so the
fragility is collision, never instability:

- **Direct conflict with Option D (D-SD5/D-SD8).** Project-local duplicate
  definitions (root and `bridge` each owning a `shared_types.yaml`) create two
  composed keys with basename `shared_types.yaml` under different owners. A
  child-owned file naming that context matches both keys and trips the ambiguity
  guard — a hard, fail-loud build break. The provisional fix works today only
  because the current fixture collapsed to a single `common/shared_types.yaml`.
- **False-positive ambiguity within one owner.** Two same-basename context files
  in different subdirectories of one project make a foreign param ambiguous even
  though both candidates share the same owner and the skip decision is identical.
- **Silent mis-ownership (low probability, high severity).** Normally every owned
  context is parsed into the composed database, so collisions fail loud. If a
  child's own context is absent while a same-basename foreign context is present
  (for example a provider-override loser whose generated files remain on disk and
  are still walked by gen), a foreign file could resolve to the wrong single
  owner and be regenerated/clobbered instead of skipped.
- **Keyed on filename, not on the settled identity.** U1 expresses stable
  identity as owning `projectName` + `includeName`; this mechanism keys on the
  physical filename basename instead.

### Robust replacement (deferred)

Resolve owner without passing through a filename:

- Resolve the param to an absolute filesystem path using the owning provider's
  project-file directory (`childProjectRaw[...].projectFileDir`), then match
  against the absolute paths of the composed context keys; or
- Resolve the generated file's owner by physical containment in the provider
  directory trees — the same logic `_assignOwnership` already uses at database
  creation.

Both are collision-proof under Option D because duplicate copies occupy distinct
absolute paths. Both require persisting the provider directory map (currently a
`projectCreate`-only structure) into `projectOpen`, which is a **data-contract
addition** and must be confirmed with the user before implementation. Closing
this item is a prerequisite for the D-SD8 duplicate-definition fixture.

## Related separable issue (not owned here)

Reachability filtering is now landed: `REACHABLEINSTANCES` restricts router and
address processing to the active root hierarchy, so parsed standalone child
harnesses do not compete for primary-router selection. Final address-map
equivalence remains a C5/Q-C5 acceptance item.

## Recommendation

- **Both Option R and Option D are supported.** Option D permits safe,
  owner-qualified local definitions; Option R gives definitions one explicit
  canonical identity. A pervasive definition such as
  `shared_types` / `apbReg` is a strong candidate for its own referenced project
  at its consumers' dominator, but extracting it is the user's responsibility.
- **Duplication (Option D) is legal.** Project-local copies remain distinct even
  when textually identical. SystemC uses the existing,
  `validatePorts`-checked thunker at crossings; structurally equivalent packed
  RTL interfaces connect directly.
- **Require E1** (explicit SV file lists); library-search order is not a
  composition mechanism.
- **Require E2** (hierarchical `projectOverrides`) to resolve multiple physical
  providers explicitly, with no automatic content de-duplication.
- **Promote Underpinning U1** (owner-qualified identity, including SV Role C) to
  a hard prerequisite of the composition work.

## Decisions settled 2026-07-10

- **D-SD1 — Sharing model.** Sharing is explicit through one project owner and
  references. Local duplication is legal and remains nominally distinct;
  arch2code never infers sharing from equal names or contents.
- **D-SD2 — SV resolution.** Generated explicit file lists are required;
  composed RTL does not use `-y` search order to select modules.
  **IMPLEMENTED (2026-07-21):** managed SV module selection is now explicit via
  the manifest `A2C_SV_FILES` var, and `rtldotf.py` no longer emits `-y` for
  managed modules (fixed a2c libs + user `-y` remain).
- **D-SD3 — Physical-provider resolution.** `projectOverrides` selects one
  physical provider for a logical `projectName`, scoped hierarchically with the
  highest applicable ancestor winning. Paths are absolute or relative to the
  declaring project file, the selected provider must declare the matching
  `projectName`, and sibling override branches require a common-ancestor
  selection. Redirects and all related errors are handled in `readRaw`.
  Provider-path normalization is lexical and does not dereference symlinks.
- **D-SD4 — Q-C8 promotion.** Owner-qualified language identity, including SV
  modules and packages, is a prerequisite.
  **DEFERRED as LATENT (architect, 2026-07-21):** the SV/C++ identity seam
  `contextModuleIdentity` already exists (bare-stem-neutralized; C++ Role A
  consumes it), so owner-qualification (SV Role C) needs no new field/rename and
  lands only if a real cross-project same-stem collision appears. An interim
  fail-fast uniqueness gate in `projectCreate` (test
  `unittest/test_module_identity_uniqueness.py`) covers the hazard meanwhile.
- **D-SD5 — `shared_types` disposition.** Local copies may remain in separate
  projects and coexist under owner-qualified identities. Users who require one
  nominal identity must extract the definitions into a referenced shared
  project; arch2code does not do this automatically.
- **D-SD6 — Generated-name spelling.** Use direct single-underscore
  qualification (`projectName_localName`). Users own language-compatible naming;
  arch2code does not encode unusual names, but DB creation rejects collisions
  among all managed generated identities.
  **DEFERRED as LATENT (architect, 2026-07-21):** the qualification itself is
  deferred; `contextModuleIdentity` remains the bare stem for now, and the
  Absolute `{owningProject}_{stem}` spelling is the settled rule if/when Role C
  lands. The collision-rejection half is what LANDED as the interim uniqueness
  gate in `projectCreate` (2026-07-21).
- **D-SD7 — Managed SV file resolution.** All arch2code-managed project RTL is
  explicit in generated manifests. User `-y` entries remain allowed; fixed
  arch2code libraries may continue using `-y`.
  **PARTIALLY IMPLEMENTED (2026-07-21):** managed module `.sv` files are now
  explicit in the manifest (`A2C_SV_FILES`, consumed by lint + cosim; no `-y`
  for managed modules). The managed WRAPPER file->top records (explicit `-top`
  per wrapper, replacing the filename-derived top in `a2c-vl-wrap.mk`) and the
  `vl_wrap.h/.cpp` aggregator retirement remain S6-gated.
- **D-SD8 — Canonical fixture.** The `ip_test` target contains root `ip` plus
  committed `bridge/ip -> ../ip`. Bridge and root
  overrides select their respective provider paths, with root winning in
  composition. The current `common` and selected `ip` projects exercise R; a
  genuine duplicate-definition Option D fixture remains future acceptance work.

## Key file / line pointers (verify against current code)

- `pysrc/processYaml.py`: `lookupInScope` ~6733 / `_lookupInGlobal` ~6720
  (scoped resolution, no DB-wide fallback); `getBDCrossInterfaceBinds` ~2041 /
  `buildThunkerView` ~2131 (thunker view); `_mergeOverrides` /
  `_selectProvider` / `readRaw` plus authoritative `_assignOwnership`;
  `CONTEXTOWNINGPROJECT`; `contextModuleIdentity`
  (bare-stem, Q-C8 seam); `calcAddresses` (DB-wide, no reachability filter);
  `resolveFileOwner` / `resolveContextKey` (ownership-gate context resolution;
  provisional basename match — see "Known limitation" above); the ownership gate
  itself in `systemcGen.py` and `systemVerilogGenerator.py`.
- `pysrc/intf_gen_utils.py`: `sc_declare_thunkers` ~723,
  `sc_thunker_protocols` ~753, `_thunker_member_type` ~697.
- `common/systemVerilog/a2c.f` (`+libext+.sv`, `-y <dir>`); per-project
  generated `rtl/rtl.f` (explicit package list); `include/make/a2c-rtl.mk:41`
  and `include/make/a2c-vl-wrap.mk` (Verilator invocation).
- `config/postParseRegisterPorts.py::_findPrimaryRouter` and related passes
  consume active-root reachability.

## Related

- [`plan-cross-project-block-resolution.md`](./plan-cross-project-block-resolution.md)
  — block-type resolution + file-ownership priority (the sibling blocker).
- [`plan-ip-project-composition.md`](./plan-ip-project-composition.md) —
  composition FOUNDATION (Q-C7 shared/vendored, Q-C8 identity, Q-C10 factory
  key).
- [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md)
  — authored YAML namespace/parameterization design; composition linkage
  identity is owned here.
- [`plan-decomp-functional-layout.md`](./plan-decomp-functional-layout.md) —
  `hierarchical` layout (B6/B7 language-identity build notes).
- [`plan-composition-ordering.md`](./plan-composition-ordering.md) — cross-plan
  index.
