# Proposal: Q-C8 Identity Field — Separating Language Identity from Filenames

Status: **C++ Role A partially implemented; SV Role C DEFERRED as LATENT
(architect, 2026-07-21); contract settled 2026-07-10.** The Section 5 Role A
edit list has
been applied for Role A: `CONTEXTMODULEIDENTITY` (view `contextModuleIdentity`)
is added in `projectCreate`/`projectOpen`/`getContextData`, the Role A emitters
(`intf_gen_utils`, `moduleScaffold`, `structures`, `headers`) read it, and
`contextIncludeName` was removed. **Known pending:** compute the absolute value
from each context's owning `projectName`, migrate every managed C++ and SV
linkage consumer, and validate generated-name uniqueness.

**Role C deferral (architect, 2026-07-21).** SV Role C (owner-qualified SV
package / C++ module identity) is **DEFERRED as LATENT, not "required now".**
The neutral seam `contextModuleIdentity` already exists (computed in
`projectCreate`, currently neutralized to the bare stem; C++ Role A already
consumes it, SV package names still read raw `includeName`), so **no new field
or rename is needed** to land Role C later. The current/target composed fixture
has globally-unique context stems, so no identity collision exists; landing
Absolute owner-qualification now would re-baseline every example's C++ module
and SV package names for zero current benefit. If a real cross-project same-stem
collision ever appears, the structural fix is Role C with the **Absolute** rule
`{owningProject}_{stem}` — this is the settled spelling if Role C is landed
(build-independent, so text-stable standalone vs composed; the required
property). The "Conditional" variant is rejected (build-dependent, breaks
composed builds). **Interim fail-fast uniqueness gate LANDED** (working tree, being
committed): in `projectCreate`, right after `CONTEXTMODULEIDENTITY` is built, it
rejects two DISTINCT contexts resolving to the same module/package identity with
a durable, plan-tag-free error ("...give one context a distinct includeName");
permanent test `unittest/test_module_identity_uniqueness.py`; full unit suite
green; emission-neutral (byte-identical). **Orthogonality note:**
`projectOverride` resolves same-`projectName` PROVIDER selection and is
orthogonal to this gate, which guards two distinct contexts with different
`projectName`s colliding on identity (e.g. two `foo.yaml` → both `foo_package`);
`projectOverride` never engages there. The gate is a belt-and-suspenders; Role C
(Absolute) would eliminate the cross-project case structurally.

Owner axis is Q-C8 (see
[`plan-cross-project-shared-definitions.md`](./plan-cross-project-shared-definitions.md)
D-SD4/D-SD6 and [`plan-composition-ordering.md`](./plan-composition-ordering.md)).

**Scope note (2026-07-17) — the composed-build landing did NOT need
owner-qualified identity for the plain cross-project case.** Cross-project
plain-block registration ("Option B", commit `4038204`) resolves the
specific plain-block cross-project registration by emitting each plain child's owning
`projectName` into `createInstance` — it preserves the `projectName` factory
disambiguation **without** relying on owner-qualified C++/SV names. So this
proposal's owner-qualified-identity work is NOT a prerequisite for the plain
cross-project fixture case that now builds+runs. This does not weaken Q-C8's
general collision-safety contract: the generated-name hazard remains for the
parameterizable registrar, same-named language units across projects, and two
IPs authoring a same-stem YAML context (SV Role C). Role A C++ / Role C SV
completion is unchanged by this arc.

## 0. Contract-layer correction (read first)

`includeName` / `INCLUDENAME` is **not** a `schema.yaml` table field. It is
persisted through the DB-backed `config` object. Per `builder/base/CLAUDE.md`
("non-schema project state is persisted through the DB-backed `config`
object"), the governing contract for this change is the
`projectCreate`/`projectOpen` config-ownership rules in `CLAUDE.md`, **not** the
table/field grammar in `SCHEMA_SPECIFICATION.md`. `SCHEMA_SPECIFICATION.md`
becomes controlling only if the user prefers to promote this identity into a
schema table (not recommended — see Open Questions).

## 1. Problem Statement

Q-C8 requires the C++ module/namespace identity of a generated context to be
qualified by `projectName`, so two IPs that author a same-stem YAML file (e.g.
two `shared_types.yaml`) do not emit the same C++ module/namespace and collide
at link/ODR time when composed into one parent
(`plan-ip-project-composition.md` lines 360-378, 590-598;
`plan-ip-namespaces-and-parameterization.md` Section 3).

The blocker: a single persisted value, `includeName`, is overloaded across
three roles. Qualifying it in place also renames generated files and SV
packages, which breaks the build. The three roles, each confirmed against the
working tree:

- **Role A — C++ module and namespace identity**
  - Set in `pysrc/processYaml.py::readRaw` lines 3411-3414 (from YAML
    `includeName:` else file basename stem).
  - Persisted as config blob `INCLUDENAME` at `processYaml.py:3103`.
  - Loaded in `projectOpen` at `processYaml.py:420`.
  - Exposed by `getContextData` at `processYaml.py:1066`
    (`contextIncludeName`).
  - Consumed for C++ spelling in `pysrc/intf_gen_utils.py`: `cpp_module_name`
    (358), `cpp_namespace_name` (392), `cpp_test_namespace_name` (395),
    `cpp_context_include_lines` (406-408), `wrap_module_namespace` (494),
    `wrap_module_test_namespace` (500); and templates
    `moduleScaffold.py:28`, `structures.py:1585`, `headers.py:46-47`.
- **Role B — physical filename stem (must stay UNqualified)**
  - `processYaml.py::saveIncludeFiles` lines 4154, 4163 →
    `expandNewModulePath` line 106 (`fileName = f"{moduleFileStub}{fileStub}"`).
    Names every generated `*Includes.cppm` / `*VariantConfig.h`, etc.
- **Role C — SystemVerilog package/design-unit name (must be qualified)**
  - `templates/systemVerilog/package.py:96` and
    `pysrc/systemVerilogGeneratorHelper.py:26`
    (`packageName = includeName + '_package'`).

### Drift / scope corrections found during verification

- `cpp_block_module_name` / `cpp_base_module_name`
  (`intf_gen_utils.py` 364-381) take `blockName`, **not** `includeName`, and
  are out of scope for this field (block/base module qualification is a
  separate axis, already keyed by `blockType`). That blockType axis — including
  the Verilated wrapper top-module / `V*`-class name
  `<projectName>_<block>_<variant>_hdl_sv_wrapper` — is owned by composition
  **Q-C10** (`projectName`) and emitted by registrar **S6**, not by this field.
- `cpp_registrar_module_name` (383-390) already takes `projectName` explicitly;
  unrelated to `includeName`.
- `pysrc/newModule.py:137-146` uses the block name as the file stub; does not
  read `includeName`; unaffected.

## 2. Proposed Data-Contract Change

Introduce a new persisted `config` blob carrying the Q-C8-qualified C++
identity, leaving `includeName` untouched as the raw stem for Roles B and C.

- **New field:** per-context dict keyed identically to `includeName`.
  Proposed config key `CONTEXTMODULEIDENTITY`; in-memory attribute
  `self.contextModuleIdentity`.
- **Computed (`projectCreate`):** right after the `includeName` map is
  populated, near `processYaml.py:3103`. Durable, computed-once project fact.
- **Persisted:** `self.config.setConfig('CONTEXTMODULEIDENTITY',
  self.contextModuleIdentity, bin=True)` — mirrors `INCLUDENAME`.
- **Loaded (`projectOpen`):** `self.contextModuleIdentity =
  self.config.getConfig('CONTEXTMODULEIDENTITY')`, adjacent to line 420.
- **Exposed (view):** `getContextData` adds
  `ret['contextModuleIdentity'] = self.contextModuleIdentity[context]` next to
  `contextIncludeName` (line 1066).
- **Value formula:** `f"{owningProjectName}_{includeName[ctx]}"` for every
  managed context, independent of which project is the current build root.
  The direct single underscore is the settled user-facing spelling. Arch2code
  does not escape unusual names, but DB creation rejects collisions among
  managed generated identities.

### Role assignment after the change

- **Role A** reads the new field (the Section 1 Role A consumers switch from
  `includeName`/`contextIncludeName` to `contextModuleIdentity`).
- **Role B** keeps reading `includeName` — no change; filenames stay
  unqualified.
- **Role C** reads the new owner-qualified field for package/design-unit
  spelling. Physical filenames continue to use Role B's raw `includeName`;
  explicit SV manifests remove filename/module-name coupling.

## 3. Decision Point: Which Field Carries the Qualified Value (correctness-driven)

The deciding principle is **correctness (one meaning per field), not churn.**

### The correct seam is by concern, not by language

- **Filesystem/authoring identity (Role B — filenames).** Directory-scoped
  (`$root`, per-child under C0a); already disambiguated by path; must stay
  **unqualified**.
- **Language linkage identity (Role A AND Role C).** A C++ module/namespace
  name and a SystemVerilog **package** name are both entries in a **global
  linkage namespace**. Two composed IPs each emitting `isp_types` (C++ module)
  or `isp_types_package` (SV package) collide identically. **Correctness
  correction:** the SV package (Role C) is a linkage identity and belongs with
  Role A, NOT with Role B. The qualified identity must therefore drive the SV
  package name too, else Q-C8 leaves an SV-side collision unfixed under
  composition. Role C is a settled composition prerequisite; only its code
  landing remains open.

### Which field holds the qualified value

- **Option 1 (RECOMMENDED, on correctness):** `includeName` keeps its true,
  original meaning — the raw authored context stem (YAML `includeName:` or file
  basename, `processYaml.py:3411-3414`), serving Role B only. A new,
  honestly-named field carries the qualified linkage identity for Roles A (and
  C). Each field then has exactly one meaning.
- **Option 2 (rejected, on correctness):** redefining `includeName` to hold a
  `projectName`-qualified token silently changes the meaning of an existing
  contract field out from under every reader; a field named `includeName`
  holding `myproj.isp_types` is misleading. This corrupts an existing field's
  meaning — the *less* correct choice, independent of edit count.

That Option 1 is also less churn is incidental; the reason to choose it is
meaning-preservation and one-meaning-per-field.

### Layer (correctness)

The field is derived, computed-once, project-wide **naming** truth, not design
data. Per `CLAUDE.md`, non-schema project state belongs in the DB-backed
`config` object; `schema.yaml` tables are for design entities. The `config`
layer (parallel to `INCLUDENAME`) is therefore the **correct** home; promoting
to a schema table would misclassify a naming derivation as design data.

## 4. Migration and Compatibility

The old monolithic byte-identical no-op was useful while qualification was
dormant, but it is not the final contract. Language identity is absolute: the
same owning project emits the same identity whether built standalone or as a
referenced child.

- **All projects:** `contextModuleIdentity[ctx] =
  owningProjectName + "_" + includeName[ctx]`.
- **Standalone vs composed:** both consult `CONTEXTOWNINGPROJECT`, so child
  identity is unchanged when a parent opens the child.
- **Files:** raw names and owner-relative directories remain independent of
  linkage identity.
- **Migration gate:** legacy examples may change generated language names when
  the absolute contract activates. Validate behavior rather than preserving
  obsolete bare-stem output.

## 5. Exact Edit List (Role A partial landed 2026-07-07)

1. `processYaml.py` `projectCreate` ~3103: compute `self.contextModuleIdentity`
   and `setConfig('CONTEXTMODULEIDENTITY', ..., bin=True)`.
2. `processYaml.py` `projectOpen` ~420: load `CONTEXTMODULEIDENTITY`.
3. `processYaml.py` `getContextData` ~1066: add `contextModuleIdentity` view
   field.
4. `intf_gen_utils.py`: switch Role A helpers — `cpp_context_include_lines`
   (406-408) to `prj.contextModuleIdentity[context]`; `wrap_module_namespace`
   (494) and `wrap_module_test_namespace` (500) to
   `data['contextModuleIdentity']`. `cpp_module_name`/`cpp_namespace_name`/
   `cpp_test_namespace_name` remain dumb sanitizers (unchanged).
5. `templates/systemc/moduleScaffold.py:28`:
   `export module {cpp_module_name(data["contextModuleIdentity"])};`.
6. `templates/systemc/structures.py:1585`:
   `using namespace {cpp_namespace_name(data["contextModuleIdentity"])}`.
7. `templates/systemc/headers.py:46-47`: build `import`/`using namespace` from
   `prj.contextModuleIdentity[name]`.
8. Keep `saveIncludeFiles` (4154, 4163) and `expandNewModulePath` (106) on raw
   Role B names. Switch `package.py` (96),
   `systemVerilogGeneratorHelper.py` (26), and managed SV module/reference
   emitters to the owner-qualified identity.
9. Add DB validation that all managed generated module/package identities are
   unique.
10. Rebuild standalone `ip`, standalone `ipBridge`, and composed `ip_test`;
    verify the selected child's identity is identical in all three views and
    managed SV manifests are explicit.

## 6. Decisions settled

**Settled by the user:**
- **Which field / layer:** Option 1 (new field holds the qualified linkage
  identity; `includeName` stays the raw stem) in the `config` blob layer —
  chosen on correctness (one meaning per field; naming derivation is not design
  data).
- **Qualification:** derive every managed context identity from its absolute
  owning project as `projectName_localName`; there is no foreign/current branch.
- **`contextIncludeName` disposition:** **remove** it after Role A migrates
  (no non-Role-A consumer found).

**Role C (SV package/module) scope — DEFERRED as LATENT (architect,
2026-07-21).**
- Investigation confirmed the SV package IS a linkage identity that WOULD
  collide under composition: generated SV compiles as one flat Verilator unit
  (`include/make/a2c-rtl.mk:41`, all packages in a single `rtl.f`) with no
  `library`/`config`/`--lib` namespacing; two IPs sharing a stem both emit
  `<stem>_package` → duplicate-package error.
- The composition design is settled: **if** Role C is landed, owner-qualify
  every managed SV module and package with the Absolute rule
  `{owningProject}_{stem}`, and compile managed RTL from explicit generated file
  lists. User-added and fixed arch2code-library `-y` entries may remain.
- Role C is **not required now.** The neutral seam `contextModuleIdentity`
  already exists (bare-stem-neutralized), so no new field/rename is needed to
  land it; the current/target composed fixture has globally-unique context
  stems, so no collision exists and qualifying now would re-baseline every
  example for zero benefit. An **interim fail-fast uniqueness gate** in
  `projectCreate` (permanent test `unittest/test_module_identity_uniqueness.py`)
  rejects two distinct contexts colliding on identity. Role C becomes active
  work only if a real cross-project same-stem collision appears.
- **New field name: `contextModuleIdentity` (config `CONTEXTMODULEIDENTITY`)**,
  language-neutral linkage scope.
