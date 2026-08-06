# Proposal: Parent-Owned Per-Variant Config Header in the Registrar Domain

## Status

- **COMPLETE / committed (reconciled 2026-07-24).** The original
  pre-implementation decision and proof record below is historical. General
  S3-H implementation landed in `52be673`; S3-M later moved the header form
  into the registrar config module without changing parent ownership.
- **Registrar-domain shape (architect decision 2026-07-20):** preserve the
  parent/assembler ownership and placement already decided by
  `plan-reusable-ip-registrar.md` and adopted by
  `plan-decomp-functional-layout.md`. The decoupled checkpoint changes only the
  emission form (plain header rather than module export), not the artifact's
  owner or functional domain.
- The header and its Config identity are owner-qualified from the start. It is
  not a functional-layout-only or bare-name interim.
- **Implementation stop CLEARED (2026-07-20):** all eight "Pre-implementation
  stop gates" are CLOSED, and the mandatory VL proof PASSED and was independently
  re-verified. In fixture `examples/ip_test/bridge`, a disposable owner-qualified
  `ipBridge_ipVariant1Config` (bridge-owned files only; ip child tree and all
  `GENERATED_CODE` regions untouched) drove both a clean standard-flow MODEL run
  (`uBridgeIp1` = `ip<ipBridge_ipVariant1Config>`) and a `VL_DUT` run (`uBridgeIp1`
  = verilated `ip_hdl_sc_wrapper<VipBridge_ip_variant1_hdl_sv_wrapper,
  ipBridge_ipVariant1Config>`) to `No error`, with a non-null cast and real data
  ACKed through the replaced foreign child in both. variant1 resolved values
  (authoritative from the bridge DB): IP_DATA_WIDTH=70, IP_MEM_DEPTH=8,
  IP_NONCONST_DEPTH=12.
- **General implementation COMPLETE and independently verified (2026-07-21),
  committed as `52be673`.** Nine generator files changed (`config/schema.yaml`,
  `config/project.yaml`, `config/createBuildManifest.py`, `pysrc/processYaml.py`,
  `pysrc/intf_gen_utils.py`, `pysrc/newModule.py`, `templates/systemc/config.py`,
  `templates/systemc/blockRegistrar.py`, `templates/fileGen/fileGen.py`);
  `ip_test` gains 6 retargeted outputs + 2 owner-qualified headers
  (`bridge/registrar/bridge/ipBridge_ipVariantConfig.h`,
  `registrar/top/ip_test_ipVariantConfig.h`); one test updated
  (`unittest/test_eval_cpp_emit.py`). Reviewer: no blockers; the MAJOR DRY finding
  (foreign-classification duplicated in the manifest) fixed via one persisted
  `projectCreate` fact `FOREIGNCONFIGHEADERS` consumed by both manifest and
  scaffold, plus three cheap cleanups. Verified by me: composed `ip_test` clean
  rebuild `No error`; whole applicable suite (base 6 + pro `lmmiDemo`)
  byte-identical; child `ip` tree and all `GENERATED_CODE` regions untouched; no
  VL/module-export/`hasTb`/`hasVl` touched. The lone S3-H test regression
  (`test_config_struct_symbolic_per_variant`) fixed to the owner-qualified
  location (3/4, symbolic preserved). All other failing unit tests confirmed
  PRE-EXISTING on branch HEAD via safe working-tree baseline revert.
- **Naming/dependency cleanup applied and independently verified (2026-07-21,
  output-neutral).** `processYaml` no longer imports `intf_gen_utils` (verified: no
  matches); the sanitization primitive `sanitizeModuleToken` now lives in
  `processYaml` and `intf_gen_utils.cpp_module_name` imports it FROM core (correct
  direction, no cycle). The foreign-Config header basename is fileMap-derived via
  `expandNewModulePath` (same `baseName` path as `config_hdr`); the hardcoded
  `cpp_variant_config_header_name` is deleted. All per-variant Config struct-name
  spelling moved to the template layer (`cpp_variant_config_name`, bare +
  owner-qualified from the view's neutral `isForeign`); the projectOpen views carry
  neutral identity, no struct-name strings in core. Generator set is now 13 files
  (adds `templates/systemc/classDecl.py`, `constructor.py`, `module_hdl_wrapper.py`,
  `testbench.py`). Verified by me: composed `ip_test` build+run `No error`; whole
  base+pro suite byte-identical; `ip_test` generated output = exactly the S3-H set
  (6 retargeted + 2 owner-qualified headers), no drift; eval test still 3/4.
- **Comment-durability pass + `configSel`→`configSelection` rename applied
  (2026-07-21, both output-neutral, independently verified).** Comments state
  current behavior durably (no prior-state/contrast framing, no plan tags); the
  neutral config-selection identifiers are spelled out (`configSelection`;
  resolver functions `resolveInstanceConfig`/`resolveConnectionConfig`), guarding
  `_resolveInstanceConfigFields`/`_selectVariantDescriptor`. Both verified
  byte-identical across the suite + `ip_test`.
- Grounded in a read-only design pass; mechanism claims are cited to current
  source but are **not yet build-verified**.
- This refines the "config-ownership is coupled to S6/S5 and gated"
  framing in [`plan-composition-ordering.md`](./plan-composition-ordering.md),
  [`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md) (S3-config),
  and [`plan-cross-level-variant-wrappers.md`](./plan-cross-level-variant-wrappers.md)
  (P2(e)); those owner plans now distinguish the independent S3-H header
  checkpoint from the gated S3-M/S6/S5 module/VL end state.

## Problem

Composed `examples/ip_test` fails a clean build:
`bridge/registrar/bridge/ipRegistrar.cppm:25: use of undeclared identifier 'ipVariant1Config'`.

`variant1` of the reusable leaf `ip` is DECLARED by the assembling projects
(`ip_top`/root `ip_test`; `bridge`/`ipBridge`), not by the child `ip` project.
The per-variant `Config` struct is emitted only into the child `ip` context
(`ip/model/ip/ipVariantConfig.h`, `--context=ip/ip.yaml`), which on a clean regen
holds only `ipVariant0Config`. The assembler-owned registrars/containers
reference `ip<ipVariant1Config>`, so the symbol is absent.

## Key concept — two independent axes

The plans gate config-ownership with S6/S5 as one coupled change. That conflates
two separable axes:

- **(i) Which project EMITS the struct** — emission is keyed on the block's
  child-owned `configContext`, so the assembler never produces `ipVariant1Config`.
  **This is the entire cause of the blocker.**
- **(ii) Header struct vs C++20 module export** — a module-exported struct is a
  distinct entity from the same-named header struct, so moving config into a
  registrar module makes `dynamic_pointer_cast<ipBase<ipVariant1Config>>` return
  null. This is the real S3-M/S6/S5 coupling.

The blocker is entirely axis (i). This proposal fixes (i) as a **header
relocation** — untouching (ii), so it stays independent of S6/S5.

## Recommended approach — owner-qualified registrar-domain header

Emit each foreign-declared variant's `Config` struct into a plain header in the
declaring parent/assembler's **`registrar` domain**, beside the registrar that
instantiates the generic child. The header, Config type, and include spelling
are owner-qualified. The parent container and parent-owned registrar consume
that header; the reusable child implementation does not include or otherwise
depend on an outer project's concrete Config.

Placement uses the existing registrar-mode layout seam:

```
functional:   registrar/<assembler>/<owner-qualified-child>VariantConfig.h
hierarchical: <assembler>/registrar/<owner-qualified-child>VariantConfig.h
```

The later S3 module form folds this header into the adjacent registrar module
without changing ownership or functional domain.

Why owner-qualified from the start (not bare-name interim):
- **B7/N7 identity.** `ip_test`'s and `ipBridge`'s `variant1` configs become
  DISTINCT C++ types (`ipTest_ipVariant1Config` vs `ipBridge_ipVariant1Config`),
  so no cross-project language-identity collision under in-tree nesting.
- **Unconditional ODR.** Distinct types remove the earlier "ODR-safe only
  because values are identical" caveat entirely; correctness no longer depends
  on value coincidence.
- **No reshape later.** A bare name now → qualified later would change every cast
  site; qualifying up front avoids that.
- **No outward child dependency.** Only parent-owned artifacts include the
  concrete header. The imported child remains `child<Config>` and is agnostic to
  where each consumer defines `Config`.

Preserved properties:
- **Preserves the cast** (avoids axis ii): the struct stays a header struct
  textually included by both the cast site and the factory registration within
  one project.
- **Honors the invariant:** within one project `(block, variant) → one Config`;
  distinct per-project configs are correct only across distinct `projectName`s.
- **Same-project byte-identical:** when a variant's declaring project
  equals the block's `configContext` owner (always single-project), the bare
  name and existing header are kept (F5), so output is unchanged.

### Coupling verdict — independent of S6/S5; prerequisites = ownership key + naming
- **Independent of S6/S5.** The struct stays header-attached (not a module
  export), so the module-vs-header cast-breakage axis that gates S3-M/S6/S5
  (`plan-composition-ordering.md:104-108`; `plan-reusable-ip-registrar.md:814-824`)
  is untouched. This is the decoupled SC-path portion of P2(e).
- **Prerequisites:** preserve declaration identity as
  `(declaringProject, qualifiedBlock, variant)` and add an owner-qualified
  per-variant Config naming helper. These depend on the **landed** Q-C10
  `projectName` axis (via `CONTEXTOWNINGPROJECT` + the variant row `_context`);
  they must **not** reuse Q-C8's `CONTEXTMODULEIDENTITY` (wrong axis) and do
  **not** need Q-C8 SV Role C (this is the C++/SC path only).

## How it works today (cited)

- **Struct name is BLOCK-derived, not context-stem.** `_buildVariantConfigDescriptors`
  (`pysrc/processYaml.py:1431`) builds the per-variant name as
  `f'{block_name}{Variant}Config'` (`:1540-1542`) → `ipVariant1Config`;
  `templates/systemc/config.py:86` emits it verbatim from the descriptor's
  `configName`. Only the shared **default** is context-stem-derived
  (`<contextStem>DefaultConfig`, `config.py:63`). So the owner qualifier attaches
  in `_buildVariantConfigDescriptors`, not the default path.
- Descriptor variant set comes from `self.data['parameters'][qualBlock]['variants']`
  (`:1470`); members from the block's `configContext` constants (`:1465`,
  `:1491-1497`). `configContext = contexts[0]` (`calcBlockConfigInfo`, `:4200/:4216`)
  — for `ip`, `ip/ip.yaml`.
- The current `config` artifact is context-mode under `model`
  (`config/project.yaml:163`). It remains the home of child-owned defaults and
  same-project canonical variants. It is **not** reused for foreign,
  consumer-selected variants.
- Registrar placement already flows through the layout seam: registrar-mode
  artifacts use the assembler block's `dir` and the assembler context's owning
  project layout (`config/createBuildManifest.py:89-114`). The ownership gate
  resolves `--parent` through the parent block context
  (`processYaml.py:840-855`).
- **Declaring-project attribution is available:** each parsed variant row carries
  `_context`, and `contextOwningProject[row['_context']]` resolves the logical
  declaring project without path parsing. However, the current schema key
  (`block`, `variant`, `param`; `config/schema.yaml:314-318`) does not preserve
  two projects' declarations of the same local variant in one composed DB. The
  project dimension must be added before descriptor construction.
- **Current include spelling is bare basename:** container and registrar sites
  include `ipVariantConfig.h`. The new registrar-domain header uses an
  owner-qualified basename so the existing manifest's exact registrar
  directories can remain the `-I` surface without search-order ambiguity.

## Proposed change set (by ownership layer)

**Schema + projectCreate (durable truth)**
- Extend the variant-binding identity so declarations remain distinct by
  `(declaringProject, qualifiedBlock, variant, param)`. Do not attach ownership
  after the current `(block, variant, param)` rows have already collapsed.
- projectCreate owns the `projectName` identity axis and the fold validation:
  that all member rows fold to one declaring project/context, form a complete
  binding, and satisfy the within-project invariant that `(block, variant)` has
  exactly one Config. Descriptor CONSTRUCTION itself stays a projectOpen view
  (`_buildVariantConfigDescriptors`, `:1431`), now grouped by
  `(declaringProject, qualifiedBlock, variant)` rather than `qualBlock` alone —
  do not move descriptor building into projectCreate.
- Each descriptor carries `declaringContext`, `declaringProject`,
  `configName`, `headerName`, and complete per-member emission metadata:
  effective value, `valueType`, `maxValue`, `evalCanonical`, resolved
  non-member symbol spellings, and synthetic block-param metadata.
- Keep same-project canonical descriptors on the existing context-mode `config`
  path. Surface foreign descriptors as parent-owned registrar artifacts.

**fileMap + artifact creation**
- Add a dedicated registrar-mode Config-header entry under `basePath:
  registrar`; do **not** reuse the context-mode `config` entry. It emits one
  owner-qualified header for the declaration-owning parent/child pair. Other
  consumers of the same `(project, block, variant)` point to that canonical
  header rather than emitting another definition.
- Derive its directory through the same assembler-dir + assembler-owner layout
  seam as `blockRegistrar`. Derive its basename from persisted owner/parent/
  child identity, not from filesystem strings.
- `make newmodule` scaffolds the new generated header before generation, and the
  build manifest records its registrar directory through the existing
  registrar-mode iteration.

**projectOpen (language-neutral view)**
- Add an assembler-aware Config-artifact view keyed by
  `(declaringProject, qualified declaring parent, qualified child)`, with
  entries keyed by variant and carrying consuming-instance sets, selected
  provider, owner-qualified type/header identities, and physical output path.
- Construct registrar block data with the `--parent` identity available before
  include/config view assembly. The leaf registrar must receive headers for the
  rendered child's own selected foreign variants; parent containers receive
  headers for foreign variants selected by their child instances.
- Keep same-project descriptors under the block's existing `configContext`.

**Template / render helper**
- Add `cpp_variant_config_name(projectName, blockName, variant)` to
  `pysrc/intf_gen_utils.py` (spelling only; single-underscore `projectName_local`
  per D-SD4/D-SD6, mirroring the precedent `cpp_registrar_module_name`
  `:383-390`).
- Add the corresponding owner/parent-qualified header-name helper. It formats
  persisted identity only; it does not infer ownership from paths.
- Reuse the Config struct-line emitter against the complete descriptor, but
  render foreign descriptors into the new registrar header rather than the
  context header.
- `blockRegistrar.py` and container class-declaration emission consume the
  header basename and Config name supplied by the assembler-aware view.

## Required Verilator/S6 contract before S3-H implementation

S3-H may land before S6, but its data contract, Config identity, and physical
artifact must already be consumable by S6 without another ownership or naming
reshape. The following is the required end-to-end contract; S6 owns its
implementation.

### Artifact ownership and type flow

For one foreign binding `(assemblerProject, childBlock, variant)`:

```
parent container
  dynamic_pointer_cast<childBase<OwnerConfig>>
                         ^
                         |
parent SC registrar -----+---- includes S3-H header
  make_shared<child<OwnerConfig>>
                         ^
                         |
parent VL registrar -----+---- includes the SAME S3-H header
  make_shared<child_hdl_sc_wrapper<VQualifiedTop, OwnerConfig>>
```

- `OwnerConfig` is the one project-canonical
  `(projectName, block, variant)` type emitted by S3-H. SC and VL paths must
  consume the exact same descriptor and header identity; S6 must not rebuild,
  copy, alias to a different struct, or infer a Config from a wrapper filename.
- The child-owned `<child>_hdl_sc_wrapper.h` remains a generic class template on
  `<DUT_T, Config>`. It does not include a parent Config header, emit
  assembler-specific aliases, or bake a parent `projectName` into registration.
- The child-owned canonical SV body (`<child>_hdl_sv_wrapper.svh`) remains
  generic and default-less. It does not acquire consumer ownership.

### Parent-owned wrapper artifacts

For every foreign variant declared and instantiated by an immediate assembler,
S6 emits the artifacts below. Before retiring the aggregator, the same
parent-owned registration mechanism must also cover same-project/default
parameterized variants, non-parameterizable `hasVl` children, the active
top-level DUT, and standalone testbench DUTs. Cross-project plain children must
retain the factory-project selection already used by container lookup; they
must not be blindly re-keyed to the assembler project.

1. An assembler-owned SV trampoline with an owner-qualified design-unit name:
   `<projectName>_<child>_<variant>_hdl_sv_wrapper`. Its physical filename may
   remain layout-local, but no build step may recover the top name from that
   filename. It includes the selected child provider's canonical `.svh` body and
   binds the resolved parameter literals from the same project-qualified
   variant descriptor used by S3-H.
2. A parent-owned `<child>VlRegistrar.cpp` in the same registrar domain as the
   SC registrar and S3-H header. It is an ordinary `.cpp`, not a C++ module:
   it exports no API and must textually include the Verilator-generated `V*.h`,
   generic child SC-wrapper header, and S3-H Config header.
3. A direct factory registration under
   `Key{"<child>_verif", variant, assemblerProjectName}` whose lambda constructs
   `child_hdl_sc_wrapper<VQualifiedTop, OwnerConfig>`.

The whole VL registrar file is guarded by `#ifdef VERILATOR`, including its
Verilator-header includes. Registrar directories are already ordinary model
source directories, so the file compiles as an empty TU in model-only builds
and becomes active in the host C++ compile under `VL_DUT=1`; current
`a2c-systemc.mk` defines `VERILATOR` for that host pass, while `VL_DUT` is only
passed to Verilator's own invocation. No second source-discovery path is needed.
The registration static uses the same retention mechanism as other generated
factory registrars.

### Generic-wrapper cleanup

S6 removes assembler-specific responsibilities from
`templates/systemc/module_hdl_wrapper.py` and the generated generic child
header:

- no nested/static factory registration carrying the child project's
  `projectName`;
- no per-variant concrete Config typedefs or explicit specializations;
- no concrete Config-header includes;
- only the reusable `child_hdl_sc_wrapper<DUT_T, Config>` class template,
  Base import, BFM/interface plumbing, and DUT connection remain.

The assembler-owned VL registrar is the sole owner of aliases (if a local alias
improves readability) and `_verif` registration.

### Build-manifest and Verilator make contract

The current `a2c-vl-wrap.mk` derives a Verilator top and object target from the
physical `.sv` filename (`:35,55-59`). That is invalid once the design-unit is
owner-qualified but the physical filename is not. Before S6 renderer work:

- Persist a language-neutral managed-wrapper record containing assembler
  project, child provider, variant, physical SV file, qualified top,
  canonical-body include directory, generated `V<top>.h` name, and expected
  archive/object identity.
- Emit explicit file→top records in `.gen/build.mk`; do not encode ownership by
  splitting filenames or paths in make.
- Generate one Verilator rule per record using the explicit `--top <qualified>`
  value. Object/header/library dependencies derive from the top field, not the
  source basename.
- Give each record a distinct Verilator output directory (`--Mdir`) or prove a
  serialized shared-directory contract. Parallel `make -j` invocations must not
  write concurrently into one `obj_dir`.
- Archive only the objects produced by those records; remove the broad
  `obj_dir/V*_hdl_sv_wrapper*.o` collection.
- Add an explicit `A2C_VL_BUILD_DIR` (or equivalent manifest fact) and use it
  for recursive `vlwrap`/`clean` invocations and library search. Do not retain
  hard-coded `$(REPO_ROOT)/verif/vl_wrap`.
- Retire `vl_wrap.h` and `vl_wrap.cpp` after their include aggregation and
  registration move into per-assembler VL registrars. The Verilator build
  directory/library remains project-scoped; the C++ registration aggregator
  has no residual role.

Q-C8/SV Role C still owns the qualified package/type identities referenced by
the canonical body. S6/Q-C10 owns the wrapper top, `V*` class, Config selection,
factory key, and assembler registration. The managed-wrapper record carries
both axes explicitly.

### Generation and provider ordering

- Child-owned canonical `.svh`, RTL, packages, and generic SC wrapper are
  generated by the selected child provider first.
- Parent-owned S3-H header, SV trampoline, and VL registrar are generated only
  by the declaring assembler project.
- A parent build must not regenerate or modify the child provider tree.
- A declaration in an ancestor project cannot serve a nested assembler; the
  instance, declaration, Config header, SV top, and VL registrar must agree on
  the immediate assembler `projectName`.

### Mandatory pre-implementation proof

Before implementing the general generator change, use `make newmodule` to
scaffold any required fixture artifacts, then build a disposable or
fixture-local proof with one owner-qualified foreign variant that manually
exercises the final shape outside generated regions:

1. S3-H parent Config header beside the SC registrar.
2. Owner-qualified SV top over the child `.svh`.
3. Guarded parent `VlRegistrar.cpp` constructing the generic child wrapper with
   the S3-H type.
4. Explicit source→top Verilator invocation (no filename-derived top).
5. Parent container replacement through the normal
   `(blockType, variant, projectName)` factory lookup.

Watch during the proof and the `unittest/` parse run: the `variants` table is
`collapsed`, so the computed `auto(projectName)` key-member's interaction with
collapsed-table grouping and the byte-identical fold is the least-proven
mechanism and must be exercised explicitly (a two-projects-same-local-variant
case).

The proof must pass both model and `VL_DUT` runs before schema, renderer, or
makefile implementation begins. It must demonstrate a non-null cast and
exercise data through the replaced foreign child, not merely compile a wrapper
or replace the whole top.

## Pre-implementation stop gates

The following decisions remain open after the document-set review and must be
closed before the proof or implementation begins:

1. **S3-M canonical declaration unit — CLOSED (architect, 2026-07-20).** The
   S3-M end-state is a dedicated canonical config MODULE per `(owningProject,
   child)` — the S3-H header folded in place into a module interface unit at the
   same location. Every parent registrar module `import`s that one unit; none
   re-declares it, so there is a single module-attached entity and the
   `dynamic_pointer_cast` stays valid. Config leaves the `-I` surface (imported,
   not included), satisfying B6. This is a slight divergence in FORM from N3's
   "config-as-registrar-module-export" wording but meets its goal; the N3 text in
   `plan-decomp-functional-layout.md` is reconciled to "dedicated config module
   imported by the registrar." S3-H (header at the per-`(project, child)`
   location) forecloses nothing here. Still gated behind M-split/S6.
2. **Exact schema key — CLOSED (architect, 2026-07-20).** Add a `projectName`
   field to the `variants` section typed `auto(...)`, whose `_auto_` function
   returns `contextOwningProject[yamlFile]`. This is parse-time safe:
   `_assignOwnership` populates the map at the end of `readRaw` (`:3825/:3849`)
   before `processYamls` (`:3264`) runs the section auto-fields. Declare it
   before `blockVariantParam` and add `projectName` to `blockVariantParam._key`,
   so the row key becomes `(block, variant, param, projectName)`; `_context` is
   NOT a key field. Config descriptors group rows by
   `(projectName, qualBlock, variant)`. Same-project declarations in two contexts
   fold onto one identity and must be validated byte-identical (fatal on
   conflict), enforcing the within-project one-Config invariant. On monolithic
   builds every row's `projectName` is the root `PROJECTNAME`, so the added key
   dimension is uniform and output stays byte-identical.
3. **Artifact enumeration mode — CLOSED (architect, 2026-07-20).** Extend the
   existing registrar mode with a foreign-Config header entry rather than adding
   a new mode: it rides the registrar layout seam and `--parent` flow for
   placement. Note the existing registrar enumeration
   (`createBuildManifest.py:89-114`) is per-`(assembler-block, child)`; collapsing
   to per-`(owningProject, child)` with the union of variants is new dedup logic,
   and when ONE project has two distinct assembler blocks of the same child a
   canonical physical home must be chosen (OPEN general-implementation item; not a
   proof blocker — ip_test's two assemblers are distinct projects, so the dedup is
   a no-op there). `projectOverride:` covers one child reused at many homes, not
   two distinct parents in one project. Granularity is one owner-qualified header per
   `(owningProject, child)`, aggregating the union of that project's foreign
   variants of that child across all its assemblers (a per-assembler-block header
   would redefine the identical `<projectName>_<block><Variant>Config` struct
   twice on one include path — an ODR violation, since a variant is unique WITHIN
   a project) (reuses the current multi-struct config-header emission; fewest
   artifacts and includes — chosen for generator simplicity). The enumeration key
   is `(owningProject, child, variant, provider)` so the later S6 SV top and
   `VlRegistrar.cpp` can be added as sibling entries without reshaping the
   enumeration; only the Config header is built now. The foreign-versus-
   same-project filter is computed in a projectOpen view; same-project and
   default variants remain on the context-mode `config` path (F5).
4. **Physical parent identity — CLOSED (architect, 2026-07-20).** Identity is the
   owning `projectName` (Q-C10 axis), not the assembler block. The header basename
   is `projectName`-qualified (`<projectName>_<child>VariantConfig.h`), so across
   projects both the qualifier and the registrar directory differ (no collision),
   and within a project the canonical `(owningProject, child)` header carries the
   union of variants (one correct emission, since a variant is unique within a
   project). The same IP reused at multiple homes in the tree is collapsed to one
   canonical provider by `projectOverride:` (existing mechanism), so there is no
   multi-home physical-clobber case to pin; no new directory machinery is added.
5. **Complete aggregator replacement — CLOSED (architect, 2026-07-20).** Each
   per-assembler `VlRegistrar.cpp` owns `_verif` registration for every category
   that assembler instantiates: foreign parameterized variants,
   same-project/default parameterized children, plain non-parameterized `hasVl`
   children, the active top DUT (root project is the assembler), standalone TB
   DUTs (the testbench is the assembler), and tandem. The registrar emits the
   line, but the `Key{blockType, variant, projectName}` uses the OWNING project
   for cross-project plain children (the existing `createInstanceProjectName`
   selection) and the assembler project for parameterized variants. This retires
   `vl_wrap.h/.cpp` entirely (F10). Scope note: this is the S6 target; the S3-H
   proof exercises only the foreign parameterized path and does not require the
   aggregator gone. OPEN (S6): a plain/owning-keyed child instantiated by two
   assemblers in one build would have both assemblers' registrars emit the same
   `Key{child, variant, owningProject}` — cross-assembler de-duplication of the
   identical owning key is unspecified and must be resolved before the aggregator
   is retired.
6. **Executable Verilator record — CLOSED (architect, 2026-07-20).** Each
   file→top record gets a distinct `--Mdir` (per-top output directory), so
   `make -j` never writes concurrently into one `obj_dir`. The top name comes
   from the explicit record in `.gen/build.mk`, NOT from `$(notdir <sv-stem>)`
   (`a2c-vl-wrap.mk:56`). Each record names its generated `V<top>.h`, its object
   set, and its Mdir; the library archives only the recorded objects, dropping
   the `obj_dir/V*_hdl_sv_wrapper*.o` wildcard (`:58-59`). Object/header/library
   dependencies derive from the top field, not the source basename. The
   single-entry `A2C_VL_WRAP_ENTRY` (`createBuildManifest.py:142`,
   `a2c-systemc.mk:140`) is replaced by the set of per-assembler
   `VlRegistrar.cpp` files; an explicit `A2C_VL_BUILD_DIR` manifest fact drives
   recursive `vlwrap`/`clean` and library search in place of hard-coded
   `verif/vl_wrap`.
7. **Final default Config home — CLOSED (architect, 2026-07-20).** For S3-H,
   child defaults and same-project canonical variants stay in the block's
   `configContext` header (context-mode `config` entry), byte-identical (F5);
   S3-H relocates only foreign assembler-declared variants, so the migration
   boundary is exactly the foreign/same-project split. Whether defaults later
   move into a registrar module is an S3-M/S5 decision and is deferred; a header
   folds into an adjacent module in place later, so S3-H forecloses nothing.
8. **Naming responsibility — CLOSED (architect, 2026-07-20).** Composition/Q-C10
   owns the persisted semantic identity `(projectName, block, variant)`
   (`projectName` from the Gate #2 auto-field via `CONTEXTOWNINGPROJECT`);
   `CONTEXTMODULEIDENTITY` is explicitly not the storage key. Shared-definitions
   (D-SD4/D-SD6) plus the Q-C8 implementation own the legal C++ spelling and
   generated-name uniqueness validation. The F7 helper
   `cpp_variant_config_name(projectName, blockName, variant)` goes in
   `intf_gen_utils.py`, mirroring `cpp_registrar_module_name` (`:383`), spelling
   only. The `plan-composition-ordering.md` owner-map is updated to state this
   split before any helper is added.

## Relationship to `plan-decomp-functional-layout.md`

- **Ownership and placement agree (N3/N8).** The foreign Config remains a
  parent-owned consumer artifact in the parent node's `registrar` domain. Only
  its emission form differs from N3's module target.
- **Placement rides the registrar seam.** The same fileMap mode and
  `expandNewModulePath` inputs as `blockRegistrar` produce
  `registrar/<assembler>/...` in functional mode and
  `<assembler>/registrar/...` in hierarchical mode.
- **B6 satisfied without an include overlay.** The generated build manifest
  already contributes exact registrar directories to `A2C_SC_SRC_DIRS`; an
  owner/parent-qualified header basename prevents same-basename search-order
  ambiguity. The inner child has no outward header dependency.
- **B7/N7 satisfied.** Owner-qualified struct identity on the Q-C10 axis
  prevents the language-identity collision the hierarchical split does NOT fix on
  its own (layout plan B7, `:690-710`; N7).
- **Divergence from the adopted END-STATE form is limited to emission form.** The
  layout plan's directory picture ADOPTS config-as-registrar-**module**-export
  (N3 `:523-542`, B6) as the target, to take the config off the `-I` surface.
  This proposal keeps the same owner and registrar location but uses an adjacent
  **header** to stay decoupled from S6/S5. The module-export form remains the
  still-gated S3 end-state and can replace the header in place.

## Architect decisions

- **F1 — header struct, not module export.** Preserves the cast; stays decoupled
  from S6/S5.
- **F2 — physical home:** an owner/parent-qualified header beside the
  parent-owned child registrar. Functional:
  `registrar/<assembler>/...VariantConfig.h`; hierarchical:
  `<assembler>/registrar/...VariantConfig.h`.
- **F3 — dedicated registrar-mode foreign-Config artifact.** The existing
  context-mode `config` remains unchanged for defaults and same-project
  canonical variants.
- **F4 — FLIPPED to owner-qualified.** Emit the per-variant struct
  `<projectName>_<block><Variant>Config` on the Q-C10 axis. The bare-name /
  "ODR-safe only if values match" position is withdrawn; distinct-project
  `variant1` types are distinct by construction.
- **F5 — scope:** owner-qualify and relocate only **foreign** (assembler-declared)
  variants; leave each block's `variant0`/default in the block's `configContext`
  header with its existing bare name, so child/monolithic output stays
  byte-identical.
- **F6 — VL implementation remains S6, but its contract is mandatory here.**
  S3-H implementation cannot begin until the pre-implementation
  Config/type/factory/top/manifest proof above passes. S6/Q-C10 owns the wrapper
  top and registration; Q-C8 owns referenced SV package/type identities.
- **F7 (new) — naming-scheme prerequisite.** Add `cpp_variant_config_name` before
  renderer work; it depends only on landed Q-C10 `projectName` and must not reuse
  Q-C8 `CONTEXTMODULEIDENTITY` or require SV Role C.
- **F8 — no project-qualified include overlay.** Owner-qualified header
  basenames plus exact registrar directories from the manifest are sufficient;
  no child implementation includes an outer Config.
- **F9 — VL registrar is a guarded `.cpp`, not `.cppm`.** It exports nothing,
  consumes textual Verilator/generated headers, compiles empty without
  `VERILATOR`, and directly owns `_verif` factory registration.
- **F10 — no VL C++ aggregator.** S6 retires `vl_wrap.h/.cpp`; the project-scoped
  Verilator build directory and library remain, driven by explicit manifest
  file→top records.

## Blast radius & validation

- Byte-identical: projects with no cross-project variant declarations. Existing
  defaults and same-project canonical variants retain their current header,
  name, and include.
- Expected divergence: standalone or composed consumers that declare a foreign
  variant gain an owner-qualified registrar Config header plus qualified
  Config/include spellings.
- Validate: standalone `ip` (`variant0`-only header unchanged, `No error`);
  standalone `ipBridge` (a bridge-owned qualified header defines
  `ipBridge_ipVariant1Config`, its registrar includes it and compiles); composed
  `ip_test` (`make clean db gen make run` → `No error`). Regenerate the full
  suite and diff (expected diffs: new declaring-project owner-qualified config
  headers + retargeted qualified `#include`s + qualified cast/registration
  spellings). Also validate two projects declaring the same local
  `(block,variant)` in one DB, incomplete/mixed-owner bindings, the leaf
  registrar include path, synthetic params, eval-derived members, duplicate
  context/header basenames, and second-generation byte identity.
  `mixed`/`pySocket` exclusions apply. Run the `unittest/` parse set.
- Before implementation, pass the mandatory VL proof above. Final acceptance
  additionally requires standalone `ip`, standalone `ipBridge`, and composed
  `ip_test` under model, `VL_DUT`, and tandem configurations; direct root and
  nested bridge `ip@variant1` replacement; distinct same-local-name variants in
  two projects; exact factory `projectName`; clean child-first regeneration;
  explicit manifest file→top entries; no stale child Config/wrapper artifact;
  and model-only builds with every guarded VL registrar inactive.

## Critical files (if approved)

- `pysrc/processYaml.py`
- `config/schema.yaml`
- `pysrc/intf_gen_utils.py` (new `cpp_variant_config_name`)
- `templates/systemc/config.py`
- `templates/systemc/blockRegistrar.py`
- `templates/systemc/vlRegistrar.py` (new guarded S6 registrar template)
- `templates/systemc/module_hdl_wrapper.py` (S6 generic-wrapper cleanup)
- `templates/systemVerilog/module_hdl_wrapper.py` (S6 parent top/body split)
- `config/project.yaml`
- `config/createBuildManifest.py`
- `pysrc/newModule.py`
- `pysrc/systemcGen.py`
- `pysrc/systemVerilogGenerator.py`
- `include/make/a2c-systemc.mk`
- `include/make/a2c-vl-wrap.mk`
