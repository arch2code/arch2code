# Plan: IP Project Composition (standalone IP projects)

## Status

- **State:** **UPDATE 2026-07-22 — C5 composition acceptance PASSED** (headline
  byte-identical parent address map G3/Q-C5 PASS, with the explicit caveat
  recorded in the C5 section below; fwIpMain Q-C11/G4, provider-override +
  duplicate-`projectName` negative, `projectName`-keyed SC+verilated
  registration, and distinct-type thunkers all PASS; cross-project eval Q-C12/G5
  DEFERRED). The earlier "implementation in progress" wording below is
  historical. Q-C10 `projectName` factory threading,
  C0a `CONTEXTOWNINGPROJECT`, per-project `PROJECTLAYOUT`, and the DB-driven
  generation ownership gate have landed. **COMPOSED BUILD IS GREEN ON A CLEAN
  CHILD-FIRST REBUILD (2026-07-21):** the ordinary `examples/ip_test` flow
  reports `No error`, and a clean child-first regeneration no longer removes
  `ipVariant1Config` and breaks the composed registrar. Registrar S3-H
  (parent-owned per-variant Config header) has LANDED and fixed that
  clean-rebuild SC blocker, so the earlier stale-committed-child-Config caveat
  no longer holds. The otherwise-tested base+pro suite is green (`pySocket`
  deferral excluded; the `mixed` registrar-orphan migration is now complete).
  The composed-build blocker was resolved by: `cpu` de-duplicated into a single
  `common`-owned generic APB master running firmware on the BSP
  `regRead32`/`regWrite32` seam (`ab75e9c`); `validateDeclaredPorts` scoped to
  instantiated blocks so a definitions-only project can own a `hasMdl` block it
  never instantiates (`91b69dc`) with zero-instance boundary ports synthesized
  from the definition (`ab75e9c`, unittest `test_zero_instance_ported_block.py`);
  cross-project plain-block registration emitting the child's owning
  `projectName` in `createInstance` (`4038204`); and the BSP register-access
  relocation pro→base at `common/systemc/bsp/` (`6791451`). Commit `6bbec76`
  then landed the `ipBridge` fixture refactor and owner-aware cross-project RTL
  directories; `6113562` made VL wrapper Makefiles consume
  `A2C_VL_WRAP_DIRS`. Provider-override acceptance is DONE (committed 37bad48 +
  test_provider_override.py green). **Reconciliation 2026-07-24:** explicit
  managed SV selection, composed/standalone VL, clangd/compdb, clean Config
  ownership, and C2/C5 acceptance are closed. Remaining work is C1's
  contract-document refresh and deferred/latent Q-C8 Role C/C2.5, Q-C12/G5,
  and the same-name collision fixture.
- **Code reality (reconciled against current source 2026-07-10).** **Q-C10
  is now IMPLEMENTED & validated:** the factory key is
  `Key{blockType, variant, projectName}`, threaded through
  `instanceFactory.{h,cpp}`, `watchDog.cpp`, `constructor.py`,
  `blockRegistrar.py`, `testbench.py`, `fileGen.py`,
  `module_hdl_wrapper.py`, and pro
  `classDeclTandem.py`/`constructorTandem.py`; the variant-fallback loop
  holds `projectName` fixed; behavior-neutral on monolithic (single
  `PROJECTNAME`), validated across all examples. The tb-top instantiation
  moved out of the user region into a GENERATED `createTbTop()` helper that
  threads `projectName` (replacing Q-C10's fragile per-project user-region
  hand-migration). **Q-C8 is PARTIAL:** the persisted
  `CONTEXTMODULEIDENTITY` field is added and the Role A C++ emitters are
  migrated (see [`proposal-qc8-identity-field.md`](./proposal-qc8-identity-field.md));
  Role C (SV package/module) is a settled composition prerequisite but remains
  implementation work. **Landed 2026-07-08:** (a) the temporary
  delegating factory overloads removed (the 5 non-`projectName`
  `registerBlock`/`createInstance` overloads dropped; full-suite
  gen/build/run `No error`); (b) **C0a ownership tag** — a new DB-backed
  config blob `CONTEXTOWNINGPROJECT` (context→owning `projectName`, keyed
  like `INCLUDENAME`, all-root on monolithic) built in `readRaw()`,
  persisted/reloaded beside its siblings, with the **Q-C8 dormant branch
  rewired** (`processYaml.py:3128`) to consult it — proven byte-identical
  (`diff -r`) and independently reviewed. **Also landed:** child-project
  detection, per-project `PROJECTLAYOUT`, owner-relative path expansion, and
  DB-driven generation skip gates in both the SystemC and SystemVerilog
  generators. `DIRS`/`FILEMAP` remain root globals; per-owner layout is carried
  by `PROJECTLAYOUT`. Authoritative child ownership is now landed; scaffold
  paths use owner layouts, and strict root-invoked scaffold skip semantics
  LANDED 2026-07-21 (ownership gate in `newModule.py`, mirroring the generation
  skip gates; no-op on monolithic, child-owned skipped in composed).
- **Cross-plan ordering.** This plan is the FOUNDATION in the composition
  workstream. See [`plan-composition-ordering.md`](./plan-composition-ordering.md)
  for the linear dependency chain, the single-owner-per-decision map, and
  the buildable-now-vs-gated table. This plan owns the determinism rule,
  `projectName` scoping, the factory key, the ownership gate, and the
  unblocking milestone (M-split, below). Shared-definitions owns the Q-C8
  identity contract and `proposal-qc8-identity-field.md` owns its implementation.
- **Origin:** 2026-06-25 working session. Split out from
  [`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md) so
  the cross-project composition mechanism is designed on its own; the
  registrar plan layers the per-assembler trampoline relocation on top of
  this boundary.
- **Precondition already settled:** each IP owns its own
  `ipParameters`/Config
  ([`plan-shared-vs-ip-boundary.md`](./plan-shared-vs-ip-boundary.md),
  Choice B). Shared YAML may define Config-consuming templates but may not
  bind a Config. That ownership rule is the right basis for treating an IP
  as an independently parameterized unit.

## Goal

Allow each IP to be its own standalone arch2code project — its own
`<ip>Project.yaml` and its own `arch/ base/ model/ rtl/ tb/ verif/
rundir/` — that is independently compilable and testable, and to let a
parent IP project *reference* a child IP project and instantiate it.

## Why this is new

Today a project is monolithic. `projectFiles:` includes YAML files
*within one project*; `dirs.root` resolves one project tree; the SQLite
DB is created once per project. There is no cross-project reference, no
shared/imported DB, and no build composition across project boundaries.
`examples/ip_test` is a single project that defines `ip`, `ipLeaf`,
`src`, `ip_top`, `ipBridge`, etc. together. Composition splits those into
independently owned projects.

## The IP Boundary

A child IP exposes a boundary across which the parent never sees the
child's *implementation*; it does, however, name the child's Base
template and the parent-owned per-variant Config.

- **Base header** (`<child>Base.h`) — the parent-facing template
  (`<child>Base<Config>`). The parent's container constructs the child
  through the factory by string key, then
  `dynamic_pointer_cast<<child>Base<ChildConfig>>` the result.
- **Per-variant Config struct (parent-owned)** — **correction from review
  C1:** the container TU is NOT config-free. `constructor.py:217-235`
  emits `dynamic_pointer_cast<{child}Base<{childPerVariantConfig}>>(...)`
  and the in-code comment requires the child's per-variant Config (else the
  cast returns `nullptr`). Confirmed in generated output
  (`ip_top.cpp:35-37`: `ipBase<ipVariant0Config>`). So the container must
  see the parent-owned per-variant Config struct (which lives in the
  registrar). The boundary is therefore **`<child>Base.h` + the
  parent-owned Config**, not "Base.h only."
- **The child's full implementation** (`<child>.h` block class, `<child>.cpp`
  member bodies) crosses into exactly one parent TU: the **trampoline**
  (registrar). The container does not see it.
- **Default config** — implicit in the child's `ipParameters` defaults
  (Q-C4); synthesized for the child's standalone build.

Encapsulation property (revised): the parent's container holds no symbol
reference to the child's *implementation*; it does reference
`<child>Base.h` and the parent-owned Config. Only the trampoline sees the
child's implementation.

## Worked Example: `ip_test` split into projects

`ip_test`'s real instance edges give both composition cases:

- `ip` is instantiated by **`ip_top`** (uIp0/uIp1) **and** **`ipBridge`**
  (uBridgeIp0/uBridgeIp1) → **shared IP**, referenced by multiple
  parents.
- `ipLeaf` is instantiated only by **`src`** (uLeaf) → **fully nested
  IP**, privately owned by one parent.
- `src` is itself both a parameterizable leaf and an assembler, so it is
  simultaneously a child IP (of `ip_top`) and a parent IP (of `ipLeaf`) —
  composition must nest to arbitrary depth.

### Case 1 — Fully nested IP (`ipLeaf` inside `src`)

The child project lives inside the parent's tree; the parent owns it
privately, and the child stays standalone-testable in its own `rundir/`.

```
src/                          (IP project)
  srcProject.yaml             references ./ipLeaf/ipLeafProject.yaml
  arch/ base/ model/ rtl/ tb/ rundir/
  registrar/                  (registrar plan) registers ipLeaf@variantLeaf0
  ipLeaf/                     nested child IP project (fully owned)
    ipLeafProject.yaml
    arch/ base/ model/ rtl/ tb/ rundir/   (ipLeaf builds/tests alone)
```

### Case 2 — Shared IP (`ip` used by `ip_top` and `ipBridge`)

The root and bridge each present a provider location for logical project `ip`.
The example uses a symlink to model the vendored Git-submodule path a real
standalone bridge would carry. Hierarchical overrides select exactly one
provider per build, while each assembler owns its own trampolines.

```
ip_test/
  ip/                         canonical projectName: ip provider
  ipProject.yaml
  arch/ base/ model/ rtl/ tb/ rundir/

  bridge/                     projectName: ipBridge
    ipBridgeProject.yaml
    ip -> ../ip               provider-location symlink
    registrar/                ip@variant0, ip@variant1
    rundir/                   standalone selects bridge/ip

  project.yaml                root override selects root ip
  registrar/                  ip@variant0, ip@variant1, src@variantSrc0
  rundir/                     composed build
  ...
```

Provider path identity is normalized without dereferencing symlinks. Bridge
standalone selects its nested path; root composition selects root `ip` and the
higher override wins. Removing the root override exposes the duplicate-
`projectName` error. The same logical `ip` identity is compiled once in either
effective graph.

## Reference Resolution and Build Discovery (worked through 2026-06-25)

This is the first composition sub-topic worked end to end.

### Reference via directory

The parent `<ip>Project.yaml` points to each child via a directory to the
child's project file. The child's own `dirs:` / `$root` then resolve the
child's YAML and generated directories — the parent does **not**
re-root the child's files under the parent tree. Each project keeps its
own `root`, `base`, `model`, `rtl`, `registrar`, etc.; the reference
simply makes a child's already-resolved directories visible to the
parent. Resolution is recursive: a referenced child may itself reference
grandchildren.

### Reference declaration: rely on existing project-file detection

The reference reuses the existing `projectFiles:` entry — a relative or
absolute path to the child's project file. **No new marker or syntax is
needed**: the parser already detects whether a `projectFiles:` entry is a
project file versus a regular YAML file.

- **How detection already works.** `createProjectConfig()`
  (`pysrc/processYaml.py:3097`) adds every top-level key of the project
  file to `self.ignoreSections`; section processing (≈ line 4778) skips
  any section in that set. So a nested project file's project-level
  sections (`dirs:`, `fileGeneration:`, `projectName:`, `topInstance:`,
  `systemFiles:`, `templates:`, …) are already recognized and skipped —
  its design sections are parsed, its project-level controls are ignored.
- **The change.** For a `projectFiles:` entry detected as a project file,
  stop discarding `dirs:` and `fileGeneration:` — **capture** them scoped
  to that child project, so that:
  - the child's directories are known to the build manifest (source /
    include / registrar dirs per child),
  - the child's generated and boundary files resolve under the child's
    own `$root`, not the parent's,
  - the parent generates only its own cross-boundary artifacts (the
    registrar trampolines), not the child's internals (ownership gate,
    Q-C9).

  This shifts `dirs:` / `fileGeneration:` from a single global record
  (today processed once from `self.proj`) to one **scoped per detected
  child project**, keyed by the owning project file. (Q-C1)

### Config across the boundary (Q-C4, confirmed 2026-06-25)

- **Default config is implicit (refinement 2026-06-25).** Each
  `ipParameter` already carries a default `value:`, so the child's default
  config is implicit in its own `ipParameters` — synthesized from those
  defaults for the standalone build rather than authored or placed as a
  separately-owned artifact. This removes the default-config *placement*
  question entirely: the only configs anyone *owns* are the parent's
  instanced ones; the default falls out of the IP's parameter definitions
  wherever the child is built.
  - **Migration note (review M4).** "Implicit" is a target, not the
    current state: today a concrete `<context>DefaultConfig` struct and a
    `<context>VariantConfig.h` are generated (e.g.
    `examples/ip_test/model/ip/ipVariantConfig.h`). Realizing the implicit
    default means changing that emission to synthesize the default from
    `ipParameters` defaults rather than emitting a standalone default
    struct; until then the artifact still exists.
- **Parent owns the specific configs it instances.** The consumer-selected
  variant config structs live in the parent's `registrar/`. The parent
  derives them from its own YAML bindings (for example `src` binds
  `ipLeaf@variantLeaf0` `LEAF_DATA_WIDTH = OUT0_DATA_WIDTH`), resolved by
  the existing eval/symbolic machinery from the full-parse DB.
- **Delivery to the child template.** The parent's registrar trampoline
  brings in the child block (module/header) and the parent-owned config
  struct, then instantiates `make_shared<child<parentChosenConfig>>(...)`.
  The config is a parent artifact passed as the template argument; the
  child's default is used only by the child's own standalone build.

**Determinism rule (load-bearing).** `instanceFactory::registerBlock`
does `getMap().emplace(Key{blockType, variant, projectName}, fn)` —
`std::map::emplace` is **first-wins and silently ignores a duplicate key
within one assembler-qualified key**. In monolithic `ip_test`, `ip_top`
contains `ipBridge`, and both instance `ip@variant0`/`variant1` under the
same `projectName`, so both registrars register the same
`(ip_model, variant0, ip_test)` key in one binary. This is safe **only if**
the config for a given `(child block, variant)` is deterministic within a
project, so every registrar's lambda and every owned config struct of the
same name are equivalent:

- If two assemblers in one project register the same `(block, variant,
  projectName)` with **different** derived configs, emplace-first-wins silently
  keeps one — a latent wrong-config bug — and the two same-named config structs
  in one binary are an ODR violation.
- Therefore a variant name must uniquely determine its config values within
  one project. A parent in that project that needs different values must use a
  distinct variant identity. Distinct projects may use the same local variant
  name because `projectName` qualifies both the factory key (Q-C10) and the
  generated language identity (Q-C8). The earlier registrar-plan phrasing
  "only one registrar registers a given key per build" is replaced by this
  rule.

**Load-bearing invariant (stated identically in dependent plans).** Config
is canonical per `(block, variant)` **within** a project; parent-ownership
of per-variant config manifests only **across** projects, via `projectName`.
The container does
`dynamic_pointer_cast<<child>Base<Config>>(createInstance(...))`, and under
`VL_DUT` the leaf-shared verilated wrapper derives from
`<child>Base<Config>`, so the container's and the wrapper's `Config` must be
the **same C++ type**. A C++20 module-exported struct is a distinct entity
from the same-named header struct, so per-parent-**distinct** config *types*
are correct **only when the parents are distinct projects** (distinct
`projectName`, which namespaces the type — Q-C8). On monolithic `ip_test`,
`ip_top` and `ipBridge` share `projectName=ip_test`, collide on `(ip,
variant0, ip_test)`, and the shared cast forces one canonical config; a
distinct per-parent config *module* would make one parent's cast return null
and break plain `make run`. This is why registrar S3-M/S6/S5 required the
split; S3-M/S6 have since LANDED (committed 2026-07-22) after M-split was
satisfied, leaving only S5. The S3-H parent-owned plain-header checkpoint preserves one
textual type at both cast/factory sites and is independently buildable (see
[`proposal-config-ownership-header-relocation.md`](./proposal-config-ownership-header-relocation.md),
M-split, and
[`plan-composition-ordering.md`](./plan-composition-ordering.md)).

### Factory qualification for same-variant reuse (Q-C10, implemented)

The fix is in the **instance factory**, not in YAML — YAML scoping already
keeps variant definitions distinct per IP. The implemented key is
`Key = {blockType, variant, projectName}` and `blockType` carries the IP name
(`ip_model`), so two *different* IPs sharing a variant name do not collide;
the unsafe case is the same `(blockType, variant, projectName)` registered with
*different*
configs. `plan-block-registration.md` already specified a `configTag`
third dimension for exactly this, but the current `Key` does not implement
it. Options:

- **F1 — Add `configTag` as a third Key dimension (recommended; lands the
  existing design).** `Key = {blockType, variant, configTag}`, where
  `configTag` is the stable config identity (the owning-IP-qualified
  config struct name). Registration and `createInstance` carry it; the
  per-instance binding (`registerInstance` / `getInstMap`) records it.
  Distinct configs under one variant become distinct keys — no silent
  first-wins. Matches the plan-block-registration intent directly.
- **F3 — Qualify by owning context.** Extend the existing instance map
  (`getInstMap`, qualifiedName → blockType) to carry
  `(blockType, variant, config)` per instance, so the hierarchical
  instance path disambiguates which parent's binding applies. No new
  public key dimension, but more change in the lookup path.
- **F2 — Fold config identity into the variant string**
  (`variant0#configTag`). No `Key` change, but stringly-typed and
  entangles with the variant-fallback logic. Not preferred.
- **F4 — No factory change; enforce determinism.** Keep
  `{blockType, variant}`, require `(block, variant) → one config` by a
  generation-time check, and treat identical re-registration as
  idempotent. Minimal, but disallows a parent overriding a variant to
  different values. Fallback only, since the direction is to qualify in
  the factory.

Recommendation: **F1** — it implements the `configTag` dimension already
specified in `plan-block-registration.md` and makes the parent-overridden
variant case explicit and safe.

**Decided 2026-06-25: third dimension is `projectName`.** `Key =
{blockType, variant, projectName}`.

**Reconciliation with `plan-block-registration.md` (review M1).** That
plan specified the third dimension as `configTag` = the child's
Config-name, with fallback scoped to the same configTag. `projectName`
**supersedes** that, it does not "implement it unchanged": within a
project `variant ≅ Config` already disambiguates configs
(`instanceFactory.h` comment), so a Config-name tag is redundant
*within* a project and — critically — does **not** disambiguate the
multi-assembler case this design targets. Two assemblers (`ip_top`,
`ipBridge`) instancing `ip@variant0` would share one Config-name
(`ipVariant0Config`) and still collide under a configTag key; under a
`projectName` key they get distinct keys. So `projectName` is the correct
disambiguator and `plan-block-registration.md`'s configTag is superseded
on this point.

Rationale: `project.yaml` already scopes the surface over which variant
definitions are shared (one project = one consistent set of
variant→config bindings, with its YAML context and hierarchy). So within
a project, `(blockType, variant)` is deterministic; across projects,
`projectName` disambiguates. Mechanics:

- The registrar that registers a child is owned by the assembling parent
  project, so it registers under the **parent's** `projectName`.
- The container `createInstance` call is emitted in the same parent
  project, so it passes the **same** `projectName` — registration and
  lookup agree with no extra plumbing.
- The same selected logical child block registered by two different assemblers
  (`ip_top` vs `ipBridge`) lands under distinct `projectName` keys, so
  both coexist and each carries that assembler's own config. The
  standalone child build registers under the child's own `projectName`.
- `projectName` is already persisted in project config, so it is
  available to both the registrar and container templates.

This also informs **Q-C8**: `projectName` is the natural basis for
IP-qualified C++ naming. Namespacing each project's generated config
structs (and modules) by `projectName` resolves the parallel ODR hazard —
`ip_top`'s and `ipBridge`'s same-named `ipVariant0Config` become distinct
project-namespaced types, which the trampolines instantiate independently.

The same `projectName`/`blockType` axis — NOT Q-C8, which is the
`includeName`/context axis — owns the **Verilated wrapper top-module /
`V*`-class design-unit name** (`<projectName>_<block>_<variant>_hdl_sv_wrapper`).
Q-C8 (`proposal-qc8-identity-field.md:79-81`) explicitly excludes block-keyed
module qualification. The wrapper top is the SV design-unit spelling of the
Q-C10 key and is emitted by registrar S6; Q-C8/Role C still owns the SV
package/type identities the wrapper references. See
[`plan-cross-level-variant-wrappers.md`](./plan-cross-level-variant-wrappers.md)
("Ownership of the wrapper top-module identity").

### Parse scope vs generation scope (worked 2026-06-25)

These are separate, and conflating them caused the earlier
flatten-vs-reference framing to look harder than it is.

- **Parse scope: full (decided).** The parent parses all child YAML so
  its DB holds the complete design picture. This is required for emitting
  trampolines (child block names, variants, parameter names, default
  config) and for the existing project-wide derivations (F2
  `isParameterizable` propagation, F3 worst-case address sizing) that
  already walk the whole block tree. The current `projectFiles:` flatten
  path already delivers full parse; it is the right behavior to keep.
- **Generation scope: parent-owned objects only (working decision).**
  Regenerating a referenced child's contained objects is redundant and
  risks clobbering: the child's model/rtl/base files are generated by the
  child's own project under the child's `$root`. The parent generates only
  objects it owns — which still includes the **cross-boundary artifacts**
  (registrar trampolines, consumer-selected child config), because those
  are keyed to the parent assembler block, not the child.
- **Mechanism: per-object ownership gate.** Tag each context/object with
  its owning project file (set when the reference loader captures the
  child's `dirs:` / `fileGeneration:`). The generation loop emits objects
  owned by the current project and skips those owned by a referenced
  child. The block-mode registrar emission is naturally parent-owned (it
  is keyed to the parent block that instantiates the child), so it
  survives the gate without special handling.
- **Residual uncertainty.** (a) Build ordering — the parent build
  consumes the child's already-generated files via the manifest, so the
  child must be generated before the parent builds; whether `make`
  encodes this as a prerequisite or the flow simply requires children
  generated first is open. (b) Whether any parent-side artifact derived
  from child data is missed by a pure ownership gate; the cross-boundary
  artifacts above are parent-owned, so none is expected, but C5's fixture
  must confirm. (Q-C9)

### Context keying vs language naming (collision hazard)

- **Parsing already keeps definitions distinct.** Contexts are keyed by
  path, so two projects with an identically-named YAML file
  (`shared_types.yaml`, `common.yaml`) are separate contexts; a
  basename-only `GENERATED_CODE_PARAM` is already reported as ambiguous.
- **The language layer is not automatically safe.** Generated module and
  namespace names derive from the file *stem*
  (`export module <stem>;`, `namespace <stem>_ns`). Two distinct IPs that
  each author a same-stem file emit the same module/namespace, which
  collides at C++/modules link time when both are composed into one
  parent. (Referencing the *same* child twice is fine — there is one
  definition, imported.)
- **Direction:** IP-qualified module/namespace/package naming so the
  language-level identity is unique per IP, not per file stem. This is
  the open work in
  [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md)
  and is a hard prerequisite for composing two IPs that share a file
  name. (Q-C8)

### Search-path problems

The include model is a flat `-I` per source directory. Composing several
projects puts many directories on one search path, so two same-basename
headers (for example two `<ip>Base.h` or two shared headers) silently
shadow each other — first on the path wins. Mitigations to evaluate:

- Include via an IP-qualified subpath (`#include "ip/ipBase.h"`) and add
  only the parent of the per-IP directory to the search path, so the IP
  segment disambiguates.
- Modules remove this for the block class and types (imported by module
  name, not found on the include path), but boundary **headers**
  (`<child>Base.h`) still resolve through `-I`; IP-qualified module names
  (above) plus IP-qualified header subpaths address both halves.

### Build-directory discovery (DB-emitted manifest)

Today the build hard-codes one `REPO_ROOT` and globs `base/model/fw/tb`.
Composition needs the build to discover an arbitrary set of referenced
project directories. The mechanism — consistent with the
DB-as-single-source-of-truth rule — is that **`projectCreate` emits a
build manifest as a `.mk` fragment** (decided 2026-06-25) that the
rundir Makefile includes, enumerating, for the parent and every
referenced child:

- source directories (for `*.cpp` globbing),
- include directories (for `-I`),
- registrar directories,
- module-dependency order (so `.cppm` precompile ordering is correct
  across project boundaries).

The existing `EXTRA_PRJ_SRC_DIRS` / `EXTRA_CPP_INCLUDES` hooks are the
seam; the manifest populates them (or a dedicated include). Because
clangd derives from `make -n`, this single change feeds both the real
build and clangd. A lighter interim is to hand-populate
`EXTRA_PRJ_SRC_DIRS` per parent, but that does not scale and is not the
target. (Q-C3)

### Shared definitions and provider copies (Q-C7, reconciled 2026-07-10)

This is a **user structuring decision; the framework supports both shapes.**
The authoritative contract is in
[`plan-cross-project-shared-definitions.md`](./plan-cross-project-shared-definitions.md):

- **Option R:** one selected logical project owner supplies one nominal
  identity to all consumers.
- **Option D:** each project owns a distinct local definition. Textually
  identical definitions remain nominally distinct; SystemC uses boundary
  thunkers and compatible packed RTL connects directly.
- **Multiple provider locations for one logical project:** duplicate
  `projectName` paths are an error unless hierarchical `projectOverrides`
  explicitly selects one. No content comparison or automatic dedup occurs.

The Q-C10 factory qualifier remains the **assembling parent's** `projectName`,
not the child IP's, so assembler registrations do not collide: `usb` instancing
`fifo` keys `(fifo_model, variantX, "usb")` and `audio` keys
`(fifo_model, variantX, "audio")`. Language identities are separately
owner-qualified as `projectName_localName`, and DB creation validates managed
name uniqueness.

### Address-space composition (Q-C5, largely solved 2026-06-25)

This composes through two existing mechanisms; no new address machinery
is expected.

- **Layered decode already nests.** A child IP's internal register/memory
  decode composes under the parent's decode hierarchy as a nested
  `apbDecode` router — the layered-decode path already handles this.
- **Hierarchy reachability excludes the child's testbench context.** A
  child's tb harness (its `<child>_tb`, its `cpu` model, its tb
  connections) is reachable only from the child's own `topInstance` in a
  standalone build. When a parent references the child, the **parent's**
  `topInstance` is the enumeration root, so the child's tb harness is
  never instanced, its connections are never made, and the parent uses
  its own `cpu`. In `ip_test` this is already the shape: `cpu` sits under
  `ip_top_tb`, not under `ip_top`; a grandparent instancing `ip_top`
  (not `ip_top_tb`) excludes `cpu`/tb automatically.
- **Only the root project's `topInstance` is authoritative.** Referenced
  children's `topInstance` (their tb root) is parsed but ignored for
  parent enumeration.

**Hardened by review G3 (must prove, not assert).** `calcAddresses`
(`processYaml.py:3278+`) computes per-block offsets **DB-wide**, keyed by
`blockKey`, with **no reachability/topInstance filter in the offset
computation**. So a child's parsed-but-uninstanced tb registers and `cpu`
get offsets computed. Whether they pollute the parent's *decode tree*
depends on a separate reachability/`addressGroup` filter at placement
time, which this plan asserted but did not cite. C5 acceptance must:
identify the actual placement-time reachability gate, and prove the
split-fixture parent address map is **byte-identical** to monolithic
`ip_test`. Treat as a hard verification gate.

## Open Questions

- **Q-C1 — Reference declaration. Parsing side resolved; generation side
  is new work (revised per review G2).** No new marker/syntax for parsing:
  project-file detection already exists as a side effect (project-level
  sections land in `ignoreSections` and are skipped; nested `projectFiles`
  are flattened into one pool). But that is *detection-by-side-effect*, not
  a classifier, and there is **no per-object owning-project field** today;
  `DIRS`/`FILEMAP`/`PROJECTNAME` are single globals
  (`processYaml.py:3058-3094`). So capturing per-child `dirs:` /
  `fileGeneration:` and gating generation by ownership is **foundational
  new work**, not a capture tweak: add a per-context owning-project tag,
  make `DIRS`/`FILEMAP` per-project-keyed, and make the file-driven gen
  dispatch honor ownership. See Q-C9.
- **Q-C2 — Parse vs generation scope.** Parse is **full** (decided): the
  parent parses all child YAML for a complete DB picture, so boundary
  metadata for trampolines and project-wide derivations are available.
  The open part is generation: confirm the per-object **ownership gate**
  (generate parent-owned objects only; skip referenced-child objects) and
  that the cross-boundary artifacts remain parent-owned. See Q-C9.
- **Q-C9 — Generation ownership + build ordering.** How is per-object
  ownership tagged and gated in the generation loop (new schema field +
  per-project `DIRS`/`FILEMAP`, per G2), and how is the
  child-generated-before-parent-built ordering handled (a `make`
  prerequisite via the manifest, or a flow requirement)? Confirm no
  parent-side child-derived artifact is missed by the gate.
- **Q-C11 — Firmware composition (gap, review G4).** A parent's firmware
  (`fw/src/fwIpMain.cpp` in `ip_test`) is inherently cross-boundary: it
  consumes child register base addresses (`BASE_ADDR_UIP0`,
  `REG_IP_IPLASTDATA`) and child-IP-generated FW constants
  (`IP_DATA_WIDTH_X2`, from `fw/include/ip/ipIncludesFW.h`). Neither plan
  addresses FW composition. Decide: which project owns the firmware main,
  how child per-context FW headers are discovered/included across the
  boundary under the flat `-I` model, and how generated register-base
  constants compose with the parent address map (depends on Q-C5/G3).
  **LARGELY SOLVED (2026-07-17).** In the composed `ip_test` that now
  builds+runs, `cpu` is a single `common`-owned generic APB master that runs
  firmware via the lmmiDemo `workerBase`/`workerFactory` pattern on the BSP
  `regRead32`/`regWrite32` seam (relocated pro→base at `common/systemc/bsp/`,
  `6791451`); `fwModelMain` + `fwIpMain` sit on that seam and child FW
  constants reach it via the full-parse DB and manifest `-I`. Commits `6791451`
  (BSP) + `ab75e9c` (common `cpu`). Remaining: prove byte-identical address
  composition (Q-C5/G3) once provider overrides are exercised.
- **Q-C12 — Cross-project symbolic eval (review G5).** `src` binds
  `ipLeaf@variantLeaf0 LEAF_DATA_WIDTH = OUT0_DATA_WIDTH` — child param
  bound to a parent param. `ValueResolver` is built over the whole DB
  today (`processYaml.py:3283`); under composition the symbol is defined
  in the child project and the value in the parent. C5 must reproduce this
  resolution with `src`/`ipLeaf` as separate projects and confirm the
  resolved value matches monolithic. Watch for single-project scoping
  assumptions in the resolver and `includeName` ambiguity (Q-C8).
- **Q-C3 — Build composition + discovery.** **Source composition**
  (decided), driven by a **DB-emitted `.mk` manifest**. Two review
  corrections:
  - **(G1) Reframe the manifest's job.** `.cppm` ordering is already
    automatic from `import`-line scanning in `a2c-systemc.mk` once files
    are discovered; the manifest should NOT "express order." The real gap
    is cross-project **module discovery + PCM target ownership**: a child
    `.cppm` outside `REPO_ROOT` is not globbed into `SC_GEN_FILES`/
    `CPP_MODULE_SRC` and `EXTRA_PRJ_SRC_DIRS` feeds only `-I`/`*.cpp`
    globbing, **not** the module set. Add a module-source seam
    (`EXTRA_CPP_MODULE_SRC` or extra `SC_GEN_FILES` roots) + per-project
    PCM rules. IP-qualified module names (Q-C8) are a prerequisite or
    same-stem child modules collide at link.
  - **(M5) Library composition is incompatible with current registration
    retention.** `A2C_REGISTRATION_RETAIN` only survives direct-`.o`
    linking, not static archives without `--whole-archive`
    (`instanceFactory.h:24-30`). The chosen source-composition direction
    is safe; a prebuilt-library variant would silently drop non-templated
    self-registration.
- **Q-C4 — Config across the boundary. CONFIRMED (2026-06-25).** Child
  owns its default config (standalone build); parent owns and generates
  the specific instanced configs in its `registrar/`, derived from its own
  bindings. See the worked-through section.
- **Q-C10 — Factory qualification for same-variant reuse. DECIDED
  (2026-06-25); PROVEN via proto (2026-06-25); IMPLEMENTED & VALIDATED
  (2026-07-07) — key is now `{blockType, variant, projectName}`.**
  Add a third Key dimension `Key = {blockType, variant, projectName}` (F1 with
  `configTag = projectName`). **This is the composition workstream's
  unblocker — see M-split below.**
  `project.yaml` scopes the shared variant-definition surface; the registrar
  and the container `createInstance` are co-located in the assembling project,
  so both use that project's `projectName`. Implements the `configTag`
  dimension from
  [`plan-block-registration.md`](./plan-block-registration.md). Factory
  change, not a YAML change.

  **Proto proof (2026-06-25):** `proto/model/test/test_projectname_factory_key.cpp`
  (`make step9`), built on the existing three-string-tuple
  `block_registration_factory.h` (whose variant-fallback already holds the
  third Key slot fixed), exercising that slot as `projectName`. Passes on
  clang and gcc, confirming:
  - **No collision.** `ip_top` and `ipBridge` both register
    `(ip_model, variant0)` under their own `projectName`; each `createInstance`
    resolves to its own config (`ipDefaultConfig` vs `ipFastConfig`) — distinct
    keys coexist in one binary.
  - **emplace first-wins is safe.** Re-registering the same
    `(blockType, variant, projectName)` with a different config is ignored and
    the first registration is kept; under the determinism rule the duplicate is
    equivalent, so the accepted-duplication case is benign.
  - **Variant fallback is scoped within `projectName`.** An unknown variant
    under `ip_top` falls back to `("", ip_top)`; the same unknown variant under
    `ipBridge` does **not** borrow `ip_top`'s fallback and throws.

  (Brief asked to reuse `test_cross_config_negative.cpp`, but that is a
  port-binding compile-fail test and cannot exercise a factory key; a dedicated
  positive test was written instead.)

  **Implementation (landed 2026-07-07):** the third Key dimension
  landed — `Key{blockType, variant, projectName}` threaded through
  `instanceFactory.{h,cpp}`, `watchDog.cpp`, `constructor.py`,
  `blockRegistrar.py`, `testbench.py`, `fileGen.py`, `module_hdl_wrapper.py`,
  and pro `classDeclTandem.py`/`constructorTandem.py`; the variant-fallback
  loop holds `projectName` fixed. Behavior-neutral on monolithic (one
  `PROJECTNAME`), validated across all examples. **Refinement:** the tb-top
  instantiation moved OUT of the user region into a GENERATED `createTbTop()`
  helper (`testbench.py` `sec_tb_config_class_template` + `fileGen.py`
  `tbConfigTemplate`) that threads `projectName` the standard way — this
  REPLACED Q-C10's fragile per-project user-region hand-migration (ip_test's
  two hand-added `"ip_test"` literals were reverted). **Cleanup DONE
  (2026-07-08):** the temporary delegating factory overloads were removed —
  the 5 non-`projectName` `registerBlock`/`createInstance` overloads dropped
  from `instanceFactory.{h,cpp}`; the API now terminates at the canonical
  4-arg `registerBlock` and 5-/6-arg `createInstance`; full base+pro suite
  gen/build/run `No error` (pySocket excluded — pre-existing deferral; the
  `mixed` registrar-orphan migration is now complete).
- **Q-C5 — Address / register spaces across the boundary. LARGELY SOLVED
  (2026-06-25).** Composes via existing layered `apbDecode` nesting plus
  hierarchy reachability (which excludes the child's tb/`cpu` context).
  See the worked-through section; remaining work is a C5-fixture
  confirmation that uninstanced child tb objects do not pollute the
  parent's address map or generation.
- **Q-C6 — clangd across projects. CONFIRMED for the composed root
  (2026-07-21).** `make compdb` + `make clangd` in `examples/ip_test/rundir`
  produce an 80-entry `compile_commands.json` in which child-owned files
  (under `ip/`, `bridge/`, `common/`) have their own compile entries, each
  already carrying the child include roots (`ip/model/ip`, `ip/base/ip`,
  `ip/registrar/ip`, `ip/fw/include/ip`, plus the `bridge/*`/`common/*`
  equivalents) with no extra path logic in `gen_compile_commands.py`; `.clangd`
  mirrors the same roots globally. A concrete parent->child include resolves:
  `model/top/ip_top.h` -> `ipVariantConfig.h` (physically
  `ip/model/ip/ipVariantConfig.h`), whose directory is on the compiling unit's
  `-I` list. Standalone sub-project `make compdb` (in `ip/rundir`,
  `bridge/rundir`) is deferred behind the `vl_wrap`/F10 retirement — see C3.
- **Q-C7 — Sharing/provider identity. RECONCILED (2026-07-10).** Options R
  (one nominal owner) and D (project-local distinct types) both work.
  Duplicate provider paths claiming one `projectName` require hierarchical
  `projectOverrides`; no content dedup occurs. The factory qualifier is the
  assembler's `projectName`; language identity is independently owner-qualified.
  See the worked-through section and shared-definitions D-SD1–D-SD3.
- **Q-C8 — Owner-qualified language naming. PARTIAL IMPLEMENTATION; CONTRACT
  SETTLED (2026-07-10).**
  Module / namespace / package
  names (and generated config structs) must be unique per IP, not per file
  stem, so two IPs that share a YAML file name — or two assemblers owning a
  same-named config — can compose without a C++/modules/ODR collision.
  Basis and spelling: **`projectName_localName`**, from the absolute owning
  project. Owned by
  [`plan-cross-project-shared-definitions.md`](./plan-cross-project-shared-definitions.md)
  D-SD4/D-SD6; a hard prerequisite for composing such IPs. Includes matching
  include-path disambiguation (IP-qualified header subpaths).
  **Landed (per [`proposal-qc8-identity-field.md`](./proposal-qc8-identity-field.md)):**
  a new persisted config field `CONTEXTMODULEIDENTITY` (view
  `contextModuleIdentity`) separating language linkage identity from physical
  filename identity; Role A C++ emitters partially migrated and
  `contextIncludeName` removed. **Role C is required** and lands with explicit
  managed SV file lists. **Pending:** compute the absolute identity from
  `CONTEXTOWNINGPROJECT`, migrate remaining Role A/C consumers, and validate
  managed-name uniqueness.

## Review Findings (2026-06-25, sub-agent adversarial pass)

Both plans were reviewed against the working-tree code. Verified-sound:
the parsing premises (project-file keys already ignorable, full parse,
context-keyed-by-path), the `emplace` first-wins motivation, the current
`{blockType, variant}` key + variant fallback, `blockType` carrying the
IP suffix, `createProjectConfig`/`ignoreSections`, single-global
`DIRS`/`FILEMAP`, module names from file stem, clangd-follows-`make -n`,
the `EXTRA_*` seams, intra-project `.cppm` ordering, single-purpose
`vl_wrap.cpp`, and the `ip_test` hierarchy facts.

Findings folded into this plan and the registrar plan:

| ID | Finding | Disposition |
|---|---|---|
| **C1** | Container references the child's per-variant Config (`dynamic_pointer_cast<<child>Base<Config>>`), so "parent sees only Base.h" is false. | Boundary section corrected (Base.h **+** parent-owned Config); registrar plan corrected. |
| **C2** | Modules linkage is unproven; block class is not in the module; T9 open. (`proto/` is **not** gone — tracked on `feature/116-parameterized-types`, restored 2026-06-25 at `/work/ws/debayer/proto`.) | Registrar plan modules section demoted to UNPROVEN; S0 **extends** the existing `proto/model/test/block_registration_*` + `.cppm` material rather than rebuilding. |
| **C3/C4** | `projectName` "agrees for free" only on the SC model path; verilated/tandem/tb need explicit threading; key change touches every call site; fallback loop must become projectName-aware. | Captured in Q-C10 mechanics + registrar S6; **note:** projectName is a per-project literal baked into each project's own registrar+container, which is consistent because a container only creates instances its own registrar registered (resolves the deeper standalone-vs-parent worry). |
| **G1** | `.mk` "module order" is the wrong instrument; real gap is cross-project module discovery + PCM ownership. | Q-C3 reframed. |
| **G2** | Generation-ownership gate is new foundational work, not a capture tweak (no per-object owning-project field; gen loop file-driven; globals). | Q-C1/Q-C9 revised. |
| **G3** | `calcAddresses` is DB-wide with no reachability filter in offset computation. | Q-C5 hardened; C5 must prove byte-identical parent map. |
| **G4** | FW composition (`fwIpMain` consuming child register bases + FW constants) unaddressed. | New Q-C11; C5 acceptance gate. |
| **G5** | Cross-project symbolic eval unverified. | New Q-C12; C5 acceptance gate. |
| **G6** | `vl_wrap.h` split + hard-coded `CPP_SRC` reference must move with the verilated relocation. | Registrar S6 surface extended. |
| **M1** | `configTag = projectName` supersedes (not implements) plan-block-registration's Config-name configTag. | Q-C10 reconciliation added. |
| **M2/M4/M5** | Stale "key unchanged"; default-config still a real artifact; library composition breaks archive self-registration. | Fixed in registrar relationship; Q-C4 migration note; Q-C3 archive caveat. |

## Work Items

### M-split — The unblocking milestone (owner: this plan)

The single concrete gate that lets the registrar plan's S3-M / S6 / S5
proceed. **S3-M/S6 have since LANDED (committed 2026-07-22); only S5 remains.**
Two parts:

1. **Implement Q-C10 — DONE (2026-07-07).** Added `projectName`
   as the third factory-key
   dimension (`Key{blockType, variant, projectName}`, F1). Threaded through
   `registerBlock` / `createInstance` at every call site (SC model,
   verilated, tandem, tb — the "agrees for free" reasoning covers only the
   SC model path, review C3/C4), and the variant-fallback loop is now
   `projectName`-aware. Behavior-neutral on monolithic `ip_test` (one
   `projectName` per project) and validated across all examples; the
   dimension the split needs is installed. The temporary delegating factory
   overloads were removed 2026-07-08.
2. **Canonical composed fixture — shape reconciled 2026-07-10.** Split the
   **real `examples/ip_test` in place** (not a
   throwaway fixture; the committed monolithic `ip_test` in git history is
   the behavioral C5 baseline). Externalize **`ip`** and **`ipBridge`**
   as their own projects nested under `examples/ip_test/` (each with its own
   project file, fake standalone harness, and `rundir/`); `ip_top` stays the
   root project and references them via `projectFiles:`. Keep
   `src`/`ipLeaf`/`cpu`/`fwIpMain`
   **inside `ip_top`** — this holds the `src→ipLeaf`
   `LEAF_DATA_WIDTH=OUT0_DATA_WIDTH` binding intra-project so cross-project
   eval (Q-C12) does not fire. The shared-`ip` edge is the target: `ip_top`
   instances `ip` (`uIp0/uIp1`) and `ipBridge` instances `ip`
   (`uBridgeIp0/uBridgeIp1`) → two assemblers under distinct `projectName`s,
   so a per-parent-distinct config *module* (registrar S3-M) becomes
   correct. `fwIpMain` stays `ip_top`-owned, reaching `ip`'s FW header via
   the C2 manifest `-I` (Q-C11 via include-dirs + full-parse constants).
   **Both `ip` and `ipBridge` must be separately buildable/testable.**
   The canonical target uses the committed `bridge/ip -> ../ip` symlink,
   modeling the bridge's vendored Git-submodule copy without duplicating
   source. Both paths declare `projectName: ip`; bridge selects its symlinked
   provider standalone and root selects root `ip` in composition. Path identity
   is normalized without symlink dereference; the root override supersedes the
   bridge override.
   Address
   (Q-C5) and FW (Q-C11) become cross-project but are validation gates
   (full-parse + manifest), not new machinery. The **full** target
   (splitting `src`/`ipLeaf`, cross-project eval, address byte-identical
   proof) remains C5. Owner-qualified SV Role C and explicit managed SV file
   lists are required, not deferred. Implementation
   phases: 0 restructure → 1 classifier+owner-propagation → 2 `PROJECTLAYOUT`
   → 3 ownership gate → 4 cross-project manifest + build/run. **Phases 1–3
   DONE + reviewed (2026-07-08).** **ABSOLUTE-OWNERSHIP invariant** (learned
   in Phase 3): both the generation gate and the C++ module identity must be a
   stable function of the file's OWNING project, computed identically no matter
   which project is the current build root — never relative to `== current
   root`. So the gate is **DB-driven** (`projectOpen.resolveFileOwner` reads
   `CONTEXTOWNINGPROJECT`; skip when owner != running `PROJECTNAME`; applied in
   `systemcGen.py` + `systemVerilogGenerator.py`; no `--project` file stamp).
   The settled identity contract is also absolute:
   `projectName_localName` from the owning project in standalone and composed
   views. Remaining bare-stem emitters are implementation gaps, not an accepted
   mode. A relative gate/identity breaks the standalone-buildable child
   (`export module ip_ip;` standalone vs a differently-qualified import in a parent → link
   break; unstamped child files regenerated by the parent).
   **Phase 0+4 status (2026-07-09):** ip_test split in place; `ip` builds+runs
   standalone and `ip_top` `db`+`gen` + ownership gate are green, but the
   composed `ip_top` BUILD is blocked by cross-project block resolution +
   ownership (a parent must `include:` the child's design file to resolve its
   block type, which steals ownership from the child). Gap #1 (owner-relative
   moduleDir) is DONE but gated by this. Full problem statement, candidate
   model and implementation sequence are in
   [`plan-cross-project-block-resolution.md`](./plan-cross-project-block-resolution.md)
   — the active document for finishing the composed build.
   **Phase 0+4 UPDATE (2026-07-17): composed `ip_top` build+run is now GREEN.**
   The composed multi-project `ip_test` builds and runs (`No error`), full suite
   green. Resolution landed via `cpu` de-duplication into a `common`-owned
   generic APB master (`ab75e9c`), definitions-only `hasMdl` ownership
   (`91b69dc` + `ab75e9c`), cross-project plain-block registration in
   `createInstance` (`4038204`), and the BSP relocation to `common/systemc/bsp/`
   (`6791451`) — rather than the originally-designed `validateForeignKey`
   fallback. Q-C11 FW composition is satisfied: the `common`-owned `cpu`
   consumes child FW via the BSP `regRead32`/`regWrite32` seam and full-parse
   constants. Commit `6bbec76` adds the final fixture stimulus refactor and
   owner-aware RTL directory emission; `6113562` wires VL wrapper Makefiles to
   the manifest. Explicit managed SV files,
   full VL/clangd validation, and a runnable standalone `ipBridge` remain
   (provider negative-path acceptance is DONE — committed 37bad48 +
   test_provider_override.py green).
   **Provider-override acceptance proven 2026-07-21** (read-only fixture toggle,
   reverted; db is untracked). Positive path: the committed root `ip` override
   yields a composed `ip_test` db/build/run green with one `ip` provider.
   Negative path: removing BOTH the root and bridge `ip` overrides triggers the
   duplicate-provider error naming both paths (root real-tree +
   symlinked `bridge/ip`); removing only the root override does NOT, because the
   bridge's own override (`ipBridgeProject.yaml`) normalizes its symlinked
   reference onto the same real-tree `ipProject` independently, leaving one
   coherent provider. Behavior is correct; the root `project.yaml` comment was
   corrected accordingly. This closes the provider negative-path acceptance
   item, now committed as a fixture+test (committed 37bad48 +
   test_provider_override.py green — positive and negative paths, wired into
   run_all_tests.sh); the other C2/M-split gates (explicit managed SV, VL,
   clangd, Q-C8) remain open.

Referenced from layout L5 and registrar S3. (M-split has since been satisfied
and registrar S3-M/S6 LANDED 2026-07-22; S3.2a — parent-qualified `.cppm`
registrar module, config canonical in header — was the correct monolithic
checkpoint until then.)

### C0 — Reference + resolver design

**Status (updated 2026-07-17): ownership foundation LANDED.** The
per-object ownership tag is now a persisted DB-backed config blob
`CONTEXTOWNINGPROJECT` = `{context → owning projectName}`, keyed identically
to `INCLUDENAME`, built in `readRaw()` and reloaded in `projectOpen` beside
its sibling blobs. On monolithic every context maps to the root
`PROJECTNAME`, so it is byte-identical no-op (proven by `diff -r` on generated
output + independent review); the Q-C8 dormant identity branch
(`processYaml.py:3128`) was rewired from the `= projectName` tautology to
consult this map. The user approved the config-blob method (not a
`schema.yaml` column) on 2026-07-08. Child-project detection, per-project
`PROJECTLAYOUT`, authoritative ownership, owner-relative path expansion,
reachable-instance filtering, and both SystemC/SystemVerilog generation gates
are now landed. Strict root-invoked scaffold skip semantics LANDED 2026-07-21
(ownership gate in `newModule.py`, mirroring the generation skip gates).

Q-C1 is resolved (rely on existing project-file detection). Concretely:
the child project file is already detected (its project-level sections are
in `ignoreSections`); the work is to **capture** its `dirs:` /
`fileGeneration:` scoped per project instead of discarding them, so the
child's contexts/files resolve under the child's own `$root`. Keep parse
full (Q-C2). Add a per-object ownership tag so the generation loop emits
parent-owned objects only and skips referenced-child objects
(cross-boundary artifacts stay parent-owned, Q-C9). The `DIRS` / fileMap
handling in `projectCreate` (today processed once from `self.proj`)
becomes per-detected-child-project. Prototype resolution on an
`ip_test`-derived fixture without changing the child's generation output.
This per-project directory record is the direct input to the C2 build
manifest.

### C1 — Boundary artifact contract

Pin the child boundary as the child Base module plus the parent-owned
per-variant Config required by the container's `dynamic_pointer_cast`. The
child implementation remains hidden except in the parent-owned registrar
trampoline.

### C2 — Build composition + DB-emitted manifest — IN PROGRESS

The DB manifest now supplies owner-correct child SystemC source/include/module
paths, and the composed model builds/runs. Commit `6bbec76` adds owner-aware RTL
directories to the context view and generated `rtl.f`; `6113562` makes every
example VL wrapper Makefile consume `A2C_VL_WRAP_DIRS`.

**Explicit managed SV module file list LANDED (2026-07-21)** — C2 item 1 (and
the module-selection portion of D-SD7). `config/createBuildManifest.py` emits a
new `A2C_SV_FILES` var enumerating managed `rtlModule` `.sv` files (`role=='sv'`;
excludes context packages and `vl_wrap` wrappers), mirroring
`A2C_CPP_MODULE_FILES`; the Verilator lint (`a2c-rtl.mk`) and cosim
(`a2c-vl-wrap.mk`) commands consume `$(A2C_SV_FILES)`, and
`templates/systemVerilog/rtldotf.py` no longer emits `-y` for managed modules
(fixed a2c libs via `a2c.f` and user `-y` remain). The redundant top-module
`.sv` was dropped from `RTL_SRC_FILES`. Validated: code review CLEAN; full
base+composed suite builds/runs/lints green; generated SystemC byte-identical;
real Verilated cosim proven green on `axi4sDemo` (`--vlInst axi4sDemo`) and all
four `apbDecode` instances — both exercised the new `A2C_SV_FILES`/no-`-y` path.
**LANDED 2026-07-22 (S6/F10):** the Verilator file->top record (explicit
`-top` per wrapper, replacing filename-derived top in `a2c-vl-wrap.mk`) and the
`vl_wrap.h/.cpp` aggregator retirement (F10) — i.e., D-SD7 for the WRAPPER
surface.

Remaining C2 closure: none of the wrapper items above — composed VL is now
GREEN (composed `ip_test` `VL_DUT` run: uSrc/uIp0/uIp1 all `No error`, the
foreign `ip_test_ipVariant1Config` cast non-null), and cross-project clangd is
confirmed for the composed root (C3). The accepted-duplication shared case
links in the composed model run.

**Branch-health note.** `apbDecode` Verilated cosim is now fully green after an
RTL/model parity fix (`rtl/blockA.sv` user region reproduces the model
`blockA::LocalRegAccess()` startup state — `blockATable1[5]` seed + `extA`
power-up — so the read-only CPU test passes on real RTL; example fix, not a
generator change).

### C2.5 — Search-path disambiguation

Resolve same-basename header shadowing across composed projects (Q-C8):
IP-qualified header subpaths and per-IP include roots, coordinated with
the IP-qualified module/namespace naming.

### C3 — clangd across projects — CONFIRMED (composed root, 2026-07-21)

Because clangd derives from `make -n`, the C2 manifest feeds it directly. The
acceptance — `gen_compile_commands.py` resolves the referenced child
`model/`/`base/`/`registrar/` directories with no extra path logic — is **MET**
for the composed `ip_test` root: `make compdb` + `make clangd` in
`examples/ip_test/rundir` emit an 80-entry `compile_commands.json` where
child-owned files carry the child include roots (`ip/model/ip`, `ip/base/ip`,
`ip/registrar/ip`, `ip/fw/include/ip`, plus `bridge/*`/`common/*`) and `.clangd`
mirrors them globally; the `model/top/ip_top.h` -> `ipVariantConfig.h`
(`ip/model/ip/ipVariantConfig.h`) parent->child include resolves off the
compiling unit's `-I` list.

Standalone sub-project `make compdb` (in `ip/rundir`, `bridge/rundir`) currently
**FAILS**, but not in compdb/clangd/`gen_compile_commands.py`: it fails at
compdb's VL dry-run capture pass (`make -n -B all VL_DUT=1`) because the child
projects lack generated `verif/vl_wrap/vl_wrap.cpp` (a pre-existing standalone
VL-scaffolding gap; the composed root has its copy). The children's MODEL pass
succeeds with correct include roots, so the C++ compile database is fully
derivable once the VL blocker clears. **DECISION (architect, 2026-07-21):** the
standalone sub-project compdb fix is **DEFERRED behind the `vl_wrap` aggregator
retirement (F10)**, which removes the `verif/vl_wrap/vl_wrap.o`/`.cpp`
dependency that is the actual blocker; fixing compdb's VL capture beforehand
would be reworked.

### C4 — Address-space composition

Resolve Q-C5: how a referenced child's register/memory spaces map into a
parent address group.

### C5 — Canonical fixture: standalone and composed `ip_test` — PASSED/ACCEPTED (2026-07-22)

**UPDATE 2026-07-22 — C5 composition acceptance PASSED, with an explicit caveat
recorded below.** The headline gate — a byte-identical parent address map
(G3/Q-C5) — PASSES. Findings:

- **Placement-time reachability gates (identified in code).**
  `templates/systemc/includes.py:181` (the FW/SC `BASE_ADDR_*` map) and
  `config/postParseRegisterPorts.py:307` (the apbDecode router decode tree) are
  both keyed on `reachableInstanceKeys()`. `calcAddresses`
  (`pysrc/processYaml.py`) computes offsets DB-wide with no filter, so these two
  gates are precisely what excludes the parsed-but-unreachable child harness from
  the parent map (proven by a DB offset table: the bridge standalone harness
  `uBridgeDriver`/`uCpu` have `container=bridgeStdTop` → excluded, while the
  `ip_top`-container design copies are included).
- **Split reorganization is byte-neutral.** The pre-split monolithic
  `regAddresses.h` is a 100% (`R100`) rename with byte-identical content across
  commits `16da8ca`/`53456ed`.
- **The single delta vs monolithic** (`BASE_ADDR_UBRIDGEDRIVER` removed) is an
  INTENTIONAL documented design refactor (`6bbec76`,
  `examples/ip_test/arch/yaml/top/ip_top.yaml:109`), not address-map pollution.
- **CAVEAT (recorded, not glossed):** No same-design monolithic-vs-composed
  historical byte-diff exists, because every monolithic baseline predates the
  ipBridge refactor; the byte-identical claim is therefore established as (a)
  split-reorganization byte-identity (`16da8ca` ≡ `53456ed`) PLUS (b) a
  self-consistency proof for the current composed map (fwIpMain's asserted
  `BASE_ADDR_*`/`REG_*` values exactly match the composed `regAddresses.h` and
  the composed run passes) — NOT a single same-design monolithic-vs-composed
  diff.

Other C5 gates: fwIpMain across the boundary (Q-C11/G4) PASS; provider override
plus the duplicate-`projectName` negative PASS (committed `37bad48` +
`test_provider_override.py`); `projectName`-keyed SC + verilated registration
PASS; thunkers for distinct SC boundary types with packed RTL directly connected
PASS (`examples/ip_test/model/top/ip_top.h:65-74`). Cross-project eval Q-C12
(G5) is DEFERRED — `src`/`ipLeaf` remain root-owned nodes (not split into
separate projects). No gaps.

Make `examples/ip_test` the user-facing composition reference:

```
ip_test/
├── ip/                         # canonical projectName: ip provider
└── bridge/                     # projectName: ipBridge
    └── ip -> ../ip             # simulates vendored/submodule ip provider
```

- `ip` is the canonical reusable leaf. Its fake harness supplies local
  stimulus, an APB master, and a primary decode shell; its block-level External
  is generated from that harness container with the DUT excluded.
- `ipBridge` is the canonical reusable assembler. Its committed fake harness supplies
  stimulus and an outer primary decoder so the production
  `bridgeApbDecode` remains nested, matching composed topology.
  `bridgeStdTop.hasTb: true`; later S3-H/S3-M/S5/S6 and L5 acceptance close
  clean Config relocation and standalone/composed VL.
- Bridge standalone selects `bridge/ip`; root composition selects root `ip`.
  The root override wins. Without it, DB creation reports both provider paths.
- Design-only project shims are removed and parents reference real child
  project files. Parent contexts still include child design YAML for definition
  scope; the planned `projectFiles:`-only FK fallback is CLOSED as
  will-not-implement (architect, 2026-07-21). `include:` governs definition scope
  and `projectFiles:` governs ownership/discovery only; letting `projectFiles:`
  resolve a foreign key would conflate the two and silently widen compilation
  scope. `include:` remains the cross-project definition-scope contract,
  orthogonal to `projectFiles:`.
- `common` and selected `ip` exercise Option R. A genuine duplicate-definition
  Option D fixture remains future work.
- Owner-aware RTL output paths and explicit managed SV selection are committed.
  Owner-qualified SV Role C remains latent/deferred until a same-stem collision.

The `ip` child and standalone `ipBridge` model harnesses are runnable. The
composed root is green on a clean child-first rebuild — registrar S3-H has
LANDED and removed the stale-child-Config dependency; composed VL_DUT is now
GREEN (registrar S3-M/S6/F10 LANDED 2026-07-22) and the remaining identity
gate (Q-C8 SV Role C) is latent/deferred (provider-override acceptance is DONE — committed
37bad48 + test_provider_override.py green).
Acceptance gates (disposition UPDATE 2026-07-22):

- **PASS (with caveat above)** — parent address map **byte-identical** to
  monolithic `ip_test` (G3/Q-C5),
- **DEFERRED** — cross-project eval `LEAF_DATA_WIDTH = OUT0_DATA_WIDTH` resolves
  to the monolithic value if/when `src`/`ipLeaf` are split (G5/Q-C12);
  `src`/`ipLeaf` remain root-owned nodes,
- **PASS** — the parent firmware (`fwIpMain`) builds against child FW headers
  across the boundary (G4/Q-C11),
- **PASS** — no `force_link`/registration loss; `projectName`-keyed registration
  resolves for SC, verilated, and tandem,
- **PASS** — root and bridge overrides select the expected provider and only
  that provider appears in each effective manifest,
- **PASS** — removing the root override yields a detailed duplicate-`projectName`
  error (committed `37bad48` + `test_provider_override.py`),
- **PASS** — local distinct SystemC boundary types use thunkers while packed RTL
  remains directly connected (`examples/ip_test/model/top/ip_top.h:65-74`).

This is the acceptance vehicle for the registrar plan's S5/S6 and layout L5.

## Relationship to Other Plans

- **`plan-reusable-ip-registrar.md`** — the dependent plan. The
  per-assembler `registrar/` and the trampoline that crosses this boundary
  are owned there; that plan assumes the boundary and reference mechanism
  defined here.
- **`plan-shared-vs-ip-boundary.md`** — the settled `ipParameters`
  ownership rule that makes per-IP parameterization sound (Choice B).
- **`plan-cross-level-variant-wrappers.md`** — the HDL-wrapper analog of
  the cross-project ownership boundary. When a higher-level project declares
  an ADDITIONAL variant of a reusable sub-component, the per-variant Verilated
  SV wrapper (and SC typedef / `V*` / factory registration) is owned and
  emitted by the immediate ASSEMBLING project into its own
  `verif/vl_wrap/<sub>/` tree,
  `` `include``ing the sub-project-owned canonical `.svh` body — the same
  assembler-owned trampoline shape this plan applies to the SC registrar.
  Direction A's P1 no longer depends on a stale child-owned Config: registrar
  S3-H has LANDED and resolved that SC blocker. Registrar S3-M/S6 have since
  LANDED (committed 2026-07-22); P2 now remains coupled to registrar S5. Its
  Q-C8 SV Role C dependency is LATENT/DEFERRED (uniqueness gate covers the
  collision hazard), NOT a live gate. Its P3
  reconciliation is settled: packages continue to follow shared-definitions
  Option R/D ownership, while each assembler owns its concrete variant
  wrapper/Config/registration. Managed identities are qualified along two axes
  by their actual owner: Q-C8 (Role C) for the `includeName`/context package+type
  identities, and the Q-C10 `projectName` axis (emitted by registrar S6) for the
  blockType-axis wrapper-top and Config identities — Q-C8 does NOT own the
  wrapper module name (see the Q-C10 note above).
- **`plan-ip-namespaces-and-parameterization.md`** — IP namespace /
  packaging context.
- **`plan-composition-ordering.md`** — the authoritative cross-plan index
  for this workstream (dependency chain, owner map, invariant,
  buildable-vs-gated table). This plan is its FOUNDATION.
- **`plan-decomp-functional-layout.md`** — the directory-axis plan; its
  L2b/L5 depend on this plan's C2 and M-split.
- **`plan-development-ordering.md`** — high-level branch index; item 8 and
  its owner map point here and to the cross-plan index.

## Done Criteria

- `<ip>Project.yaml` reference declaration and resolver defined and
  prototyped (Q-C1/Q-C2).
- Build composition model chosen and working (Q-C3): a parent builds and
  runs a referenced child, including the shared-IP duplication case.
- A child IP builds and tests standalone in its own `rundir/`.
- The `ip_test` composition fixture (C5) builds and runs in both the
  nested and shared configurations.
- clangd resolves cross-project symbols (Q-C6). **SATISFIED** for the composed
  root and standalone sub-projects; F10 and `731b196` closed the former compdb
  blocker.
- Address-space composition resolved (Q-C5).
