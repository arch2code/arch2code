# Arch2Code Generator Architecture

This document describes the concepts, data structures, stage boundaries,
resolution rules, project composition, parameterization, and artefact ownership
of the generator under `builder/base`. It is deliberately high level, with no
API reference or line numbers.

**Companion documents.** `config/SCHEMA_SPECIFICATION.md` is authoritative for
the schema system, key construction, and, critically, for **resolution
semantics**. Read its "Governing Invariants" section before forming any view
about how names resolve. `AGENTS.md` / `CLAUDE.md` in this directory are
authoritative for where a change belongs.

The central architectural constraints are:

- The **database is the only channel** between the two stages, and the **artefact
  file is a second input** carrying its own identity (§2, §7).
- Names resolve through an **ordered, two-hop include chain**, not globally and
  not transitively (§4).
- **`include:` grants visibility; `projectFiles:` grants ownership.** They are
  deliberately independent (§4, §5).
- A parameterized block is **one description realizing a family**, and its C++ and
  SystemVerilog forms must agree on resolved bit layout (§6).

---

## 1. What the generator is

A hardware design is authored as YAML — the Single Source of Truth. The generator
turns that description into SystemC models, SystemVerilog RTL, per-context type
and constant packages, per-variant configuration structs, testbenches,
verilated-wrapper glue, firmware headers, build manifests, and documentation.

Two properties shape the whole architecture:

- **Generated artefacts share files with hand-written code.** Most output files
  are part generated, part user-owned. The generator rewrites regions inside an
  existing file; it does not own the file.
- **Multiple independently authored projects compose into one build.** A design
  can instantiate blocks defined by projects it does not own, and each project
  must generate exactly its own artefacts, in its own tree, identically whether
  built standalone or as part of a parent.

Nearly everything difficult in this system follows from those two properties.

---

## 2. The pipeline and its seams

```
   YAML (SSoT)
       │
       ▼
 ┌──────────────┐
 │ projectCreate│   parse, validate, normalize, derive, persist
 └──────┬───────┘
        │  SQLite database  ◄── the only channel
        ▼
 ┌──────────────┐
 │ projectOpen  │   load read-only, build template-facing views
 └──────┬───────┘
        │  view dicts + persisted config
        ▼
 ┌──────────────┐
 │  renderer +  │   render text, rewrite generated regions only
 │  templates   │
 └──────┬───────┘
        │
        ▼
   artefacts on disk  ◄── which are ALSO an input (see §7)
```

Both stages are classes in `pysrc/processYaml.py`, dispatched from
`arch2code.py`: supplying `--yaml` and `--db` runs `projectCreate`; supplying
`--db` (with `--readonly`) runs `projectOpen`, after which independent post-open
dispatch branches may run: `--systemc`,
`--systemVerilogGenerator`, `--initialSystemVerilogPackagesGenerator`,
`--docgen`, `--newmodule`, `--diagram`, `--drawStructure`, `--flows`,
`--instancesWithBlockType`, `--blockContexts`. These are a sequence of
independent `if`s, not a mutually exclusive mode selection, so several can run in
one invocation. (`--newproject` is *not* one of them: it dispatches before any
database is opened.) Project makefiles wrap this as `make db` then `make gen`.

### Stage 1 — `projectCreate`: build the database

Responsible for everything that is true of the project as a whole and must be
computed once. Its driver is a linear sequence with no phase structure above
these steps:

1. **Bootstrap and project config** — delete and recreate the database; merge
   base ⊕ pro ⊕ user `project.yaml` into one effective configuration; resolve
   directory macros.
2. **Migration gate** — `_gateYamlFormat` is the sole detector of an un-migrated
   project. It runs before any address or eval processing, so a legacy project
   fails with a `make migrate` instruction instead of failing obscurely later.
3. **Schema load, layout, templates** — load and validate `config/schema.yaml`;
   resolve the address policy; build per-project directory layouts; expand and
   persist the `templates:` map.
4. **Discovery** — a side-effect-free scan-all pre-pass (`pysrc/projectScan.py`)
   walks the full `projectFiles:` / `include:` closure, folds `projectOverrides`,
   selects one master per duplicated project, and reconciles physically distinct
   copies onto it. Then `readRaw` reads the closure.
5. **Ownership** — each parsed context is labelled with its owning project.
6. **Parse** — `processYamls` processes files in include-dependency order,
   sections and rows in authored order, firing schema `_validate` foreign keys
   inline and `post(...)` hooks per row.
7. **Derivation passes** — address calculation; per-block config/parameterization
   election; foreign config headers; parameterized declaration sets; address
   enums; include-file resolution.
8. **External post-parse scripts** — `postProcess:` (register-bus distribution,
   variant sanity) and `createArtifacts:` (the build manifest).
9. **Final validation and persist** — port/interface compatibility barrier;
   module identity uniqueness; write the config blobs; commit and close.

**It must not** render text, choose language syntax, or know about C++ or
SystemVerilog spelling.

### Stage 2 — `projectOpen`: build views

Opens the database **read-only** (so parallel `make -j` generator invocations can
share it), loads every schema table into memory, reloads the config blobs,
reconstructs the authored hierarchy, and exposes **language-neutral views** to
templates.

**It must not** reparse YAML, re-merge project config, recompute project-wide
derivations, or make language-specific decisions. Its output is neutral currency:
a view says "this instance selects that variant descriptor"; the template decides
whether that spells a C++ template argument or a SystemVerilog parameter.

### Stage 3 — renderer and templates

`pysrc/renderer.py` is thin. Templates are Python modules exposing
`render(args, prj, data)`. They select fields, iterate, apply language-specific
formatting, and emit text.

### What crosses each seam — and why the database seam is strict

**The SQLite database is the only channel between stage 1 and stage 2.** No
Python object, closure, or in-memory graph survives. Two consequences dominate
the design:

- Any fact stage 3 needs must either be **persisted** (a schema table column, or
  a config blob) or **recomputable in `projectOpen` from persisted data**. There
  is no third option. When a derivation is expensive or its policy is subtle, the
  correct answer is to persist the *result*, not to re-run the derivation on the
  read side.
- The seam is crossed twice per build in opposite directions and by different
  code, so duplicate derivations on both sides can diverge.

Two kinds of thing cross it:

- **Schema tables** — the design data, defined by `config/schema.yaml`.
- **Config blobs** — non-schema project state. The set is data-dependent:
  `createProjectConfig` uppercases every top-level `project.yaml` section outside
  `{projectFiles, dirs, systemFiles, templates}` into a blob, so a user project
  adds its own. The explicitly-written ones include `TEMPLATES`, `DIRS`,
  `LAYOUT`, `PROJECTLAYOUT`, `FILEMAP`, `INCLUDEFILES`, `YAMLCONTEXT`,
  `INCLUDENAME`, `CONTEXTOWNINGPROJECT`, `CONTEXTNODEDIR`,
  `CONTEXTMODULEIDENTITY`, `BLOCKMODULENAME`, `TOPCONTEXT`,
  `REACHABLEINSTANCES`, `FOREIGNCONFIGHEADERS`, `BUILDMANIFEST`, `SCHEMA`,
  `A2CROOT`, `A2CPROJ`, `BASEYAMLPATH`; section-derived ones include
  `PROJECTNAME`, `FILEGENERATION`, `TOPINSTANCE`, `ADDRESSOBJECTS`,
  `INSTANCEGROUPS`, `POSTPROCESS`, `CREATEARTIFACTS`, `PROJECTOVERRIDES`,
  `YAMLFORMAT`.

There is also a **third input to stage 3 that does not come through the
database at all**: the target file itself. See §7.

---

## 3. The core data model

### The entity set

`config/schema.yaml` declares top-level authored sections, which become
top-level database tables. `enums` is a `_mapto` alias of `types`. Nested schema
nodes become nested tables. The database also contains `_config` and the
non-schema `blockParameterizedDecls` table. YAML dictionary groups such as
`_key:`, `_validate:`, and `ext:` are schema metadata, not tables.

Grouped by role:

**Definitions** (what things are)
- `constants` — named values. May be marked *parameterizable*, which is what
  makes them eligible to be design parameters.
- `types` — scalar types with a width, expressed directly or as `widthLog2` /
  `widthLog2minus1`, possibly evaluated from an expression.
- `enums` — enumerations, folded into `types`.
- `structures` — composite payloads: ordered fields of types, sub-structures, or
  arrays. Structures own bit layout.
- `specialStructures` — structures with framework-defined base behaviour.
- `encoders` — value encodings.
- `variables` — typed value declarations.

**Communication** (how things talk)
- `interface_defs` — reusable *protocol* definitions (apb, rdy/vld, push/ack,
  axi, status, memory…), each with signals, modports, modport groups, SystemC
  channel behaviour, and declared structure-typed parameters. These come from the
  framework `interfaces/` tree, not from user projects.
- `interfaces` — a *use* of a protocol with concrete structures bound to the
  protocol's structure parameters. This is the distinction that matters: an
  `interface_def` is `push_ack`; an `interface` is "push_ack carrying `videoSt`".

**Structure** (what the design is)
- `blocks` — design units. Carry generation flags (`hasMdl`, `hasRtl`, `hasVl`,
  `hasTb`), declared `params:`, declared `ports:`, register-bus ingress
  `registerPorts:`, an optional `addressBlock:` router declaration, and three
  columns filled by post-processing: `isParameterizable`, `defaultConfig`,
  `configContext`.
- `instances` — occurrences of a block inside a container block. Carry the
  selected `variant` and the container-inheritance flag
  `inheritContainerParam`.
- `connections` — point-to-point or multi-ended links on an interface, with
  `src` / `dst` / `ends`.
- `connectionMaps` — a container's own boundary port routed through to a child
  instance's port.

**Parameterization**
- `parameters` → `variants` → `params` — a three-level nesting. `parameters` is
  keyed by block; `variants` is the `(block, variant)` intermediate; the leaf
  `parametersvariantsparams` holds one row per `(block, variant, param)` binding.

**Storage and addressing**
- `registers`, `memories` — addressable objects owned by a block, typed by a
  structure, with a register type (`ro`/`rw`/`ext`/`memory`) and word count.
- `registerConnections`, `memoryConnections` — which instance reaches which
  register/memory block.

### The two identity axes

Every row carries two orthogonal identities, and conflating them is the most
common source of bugs:

1. **Storage key** — hierarchical, built by concatenating ancestor keys and the
   YAML anchor **with no separator** (`apb` + `src` + `inputs` = `apbsrcinputs`).
2. **Context qualification** — the storage key, one `/`, then the context string
   (usually a YAML file path, which may itself contain `/`).

Therefore: **a qualified key may contain several slashes, and you must never
recover its components by splitting on `/`.** The schema system provides
accessors for this; string surgery on keys is prohibited.

### The three shapes of the same data

The spec is explicit that these belong to different phases and must not be
interchanged:

| Phase | Shape | Indexed by |
|---|---|---|
| Parse (`projectCreate.data`) | context buckets | `[section][yamlFile][storageKey]` |
| Parse (`projectCreate.flatData`) | flat index, `flat` sections only | `[section][qualifiedStorageKey]` |
| SQLite | one relational table per schema node, name = concatenated path | — |
| Loaded (`projectOpen.data`) | flat by qualified key, **plus children attached under parents** | `[table][qualifiedKey]` |
| Loaded (`projectOpen.data_by_parent`) | secondary child index | `[table][qualifiedParentKey][anchor]` |

`flat` describes the parse-time index, **not** SQL layout.

### Invariants that hold the model together

- A block's identity is `(block, context)`; two projects may legitimately declare
  the same block name.
- An instance names its container and its type by name; nothing in an instance row
  is project-qualified. Cross-project instantiation looks exactly like local
  instantiation (§5).
- Structures own bit layout. Interface compatibility is decided by *packed form* —
  same protocol, same structure list, identical field widths and bit offsets at
  each position — and **never by field name**.
- Addresses are derived, never authored. Sizing uses worst-case widths for
  parameterizable objects.
- Every declared variant of a block binds every parameter the block declares.
  There is no default-fill.
- A block that names a parameterizable type must declare the `params:` that give
  it a Config. Emitting a reference to an undeclared Config and letting the C++
  compiler find it is not an accepted outcome.

### Project-qualified parameter bindings

The in-memory reconstruction `data['parameters'][block]['variants'][variant]['params'][param]`
is **projectName-blind**. In a composed build, two projects binding the same
`(block, variant, param)` collapse onto one entry, last load winning.
Identity-sensitive code must therefore use the flat leaf table
`parametersvariantsparams`, whose combo key carries the declaring `projectName`.

---

## 4. Resolution

**`config/SCHEMA_SPECIFICATION.md` "Governing Invariants" is authoritative for
resolution; what follows summarises it.**

### Scope-based, not global

A reference is resolved by walking the **include chain of the referring row's own
context file**, with the system context `_a2csystem` as an implicit final
fallback. The implementation is `lookupInScope(objType, context, name)`.

The include chain lives in `yamlContext`: a per-context ordered map. It is built
by seeding the context with itself, then for each **direct** include adding that
file followed by *its* direct includes.

**The chain is therefore flattened to exactly two levels, not transitively.**
`yamlDependancies` holds only direct includes, and nothing makes it transitive.
Since `lookupInScope` iterates exactly `yamlContext[context]` plus `_a2csystem`,
a definition three include levels away is unresolvable.

Order within the chain is depth-interleaved: `self, dep1, dep1's includes, dep2,
dep2's includes`. It is not breadth-first. Lookup returns the **first** match.

The consequences are the whole point:

- **Two rows in files that do not include each other are mutually invisible.**
  Same-named definitions in unrelated scopes are not a conflict and must not be
  reported as one.
- Because the chain is ordered, a name declared in the referring file **shadows**
  one reached through an include, and `dep1`'s own include shadows `dep2` — both
  silently.
- Because the chain is only two levels deep, transitive visibility is not
  something an author can rely on. A file that needs a definition must be able to
  reach it within two include hops.

`scope: global` exists, walks every loaded context, and reports duplicates as
errors. It discards include-chain isolation, so adding or retaining it requires
explicit architect signoff. An internal `_global` sentinel exists for
callers that must walk all contexts without duplicate diagnostics; the
`_global` validator exemptions are part of the resolution contract.

### Foreign keys and parse ordering

Schema `_validate: section:/field:` declares a foreign key, resolved inline
during parsing. The invariant is precise and frequently misread:

> **A successful foreign key proves that its target row was already parsed. It
> does not schedule parsing.**

Files are processed in include-dependency order; within a file, sections and rows
in authored order. A foreign key that resolves guarantees the matched target row
is complete, so a subsequent `_post` hook on the same row may rely on it. It
guarantees **nothing** about other rows in the target section.

Schema validation itself enforces what `validateForeignKey` may assume: a plain
foreign key's target section must be `flat` and its `field:` must name the
target's storage key; a combo foreign key's target must be a combo over
identical sources. Violations are schema bugs that fail fast.

### Where a validation belongs

Decide in this order, stop at the first that fits:

1. Fixed value set → schema `_validate: values:`.
2. A reference this row names directly → schema `_validate: section:/field:`.
3. One row, cross-checked against something a foreign key cannot express → a
   `post(...)` hook on that section. Fires once per row, at the tail of row
   processing (children already populated), **in the row's own file scope**. It
   must resolve references via `lookupInScope` and must not iterate other context
   buckets.
4. Inherently aggregate, with no row to hook → a project-wide pass in
   `projectCreate` after `processYamls()`. The canonical example is
   `_validateIpParametersLinkage`. Such a pass must still resolve each reference
   in its own scope; treating all buckets as one namespace produces false
   positives across mutually invisible scopes.

### What `include:` does — and the three slots

A project file and a design file may each reference other files, through three
slots with **different meanings**:

| Slot | Parses the file? | Contributes to include scope? | May open a child project? |
|---|---|---|---|
| `systemFiles:` | yes, into `_a2csystem` | no | no |
| `projectFiles:` | yes | **no** | **yes** |
| `include:` | yes | **yes** | no |

So `include:` is the **definition-scope** mechanism and the only one: it is what
makes a name resolvable. `projectFiles:` is **discovery and ownership only** and
never participates in name resolution. Referencing a project file from
`include:` is a fatal authoring error: "a project file provides nothing to
`include:` scoping".

### How ownership is determined

Ownership answers "which project generates this file", and it is a **label from
the discovery closure**, never inferred from disk location.

- Path identity is the **whole root-relative lexical context key**. No basename
  matching, no directory-prefix matching, no `realpath` dereference. Symlinked
  copies stay lexically distinct on purpose.
- A referenced file is a **child project** only if its content carries the full
  sentinel set `projectName` + `dirs` + `fileGeneration`, *and* it arrived via the
  `projectFiles:` slot.
- The scan-all pre-pass assigns ownership: the root closure belongs to the root
  project, and for a file reachable through several providers **the deepest
  closure wins, equal depth broken lexically on the provider path.**
- `projectCreate` then records the result as `contextOwningProject`, persisted as
  `CONTEXTOWNINGPROJECT`. A design context absent from the scan closure is a hard
  error and does not default to the root.

---

## 5. Project composition

### The author's contract

To instantiate a block another project defines, an author writes **two** things
in **two** different files:

```yaml
# my project file — discovery + ownership boundary
projectFiles:
    - ../../../theirIp/prj/yaml/theirIpProject.yaml
    - ../../yaml/myDesign.yaml
```
```yaml
# my design file — definition scope, so the block name resolves
include:
    - ../../theirIp/yaml/theirIp.yaml

instances:
    uTheirs: { container: myWrapper, instanceType: theirBlock, variant: fast }
```

Nothing in the instance row is project-qualified. That is the design intent:
composition is invisible at the point of use.

### `projectOverrides:` and nesting

When one `projectName` is reachable by more than one lexically distinct path,
an ancestor declares which physical file provides that name:

```yaml
projectOverrides:
    isp_shared: ../../canonical/isp_shared/prj/yaml/ispSharedProject.yaml
```

Semantics:

- It selects a **provider file for a project name**. It does not override design
  content, parameters, or blocks.
- **Highest applicable ancestor wins.** A descendant's entry never displaces an
  ancestor's. Multi-level nesting is supported: a child project's override is
  honoured when no shallower ancestor overrides that name.
- Two **non-dominating declarers at the same depth** selecting different targets
  for one name is a loud failure, not a silent pick.
- Paths normalize **lexically** against the declaring project file.
- Reconciliation is **member-level**: every file discovered through a
  non-master copy is aliased onto the corresponding master file, not just the
  provider project file.
- Copy divergence is reported as a **non-blocking warning**, and only when
  non-master copies disagree with *each other* — the signal of genuine version
  skew. Comparison is comment- and key-order-insensitive.

Without an override, a second lexically distinct path claiming an
already-claimed `projectName` is a fatal duplicate-provider error naming the fix.

### Definitions-only ("common") projects

There is **no flag**. A project is definitions-only by consequence: it declares
no instances, so it omits `topInstance`. `topInstance` is required **iff** the
project declares instances, and that is checked after parsing so the failure is
clear at database creation.

Downstream, a definitions-only project emits no `rtl.f` (`TOPCONTEXT` is `None`),
and the instance-, hierarchy-, and address-driven passes iterate an empty table
as natural no-ops. Such a project may still own blocks with models it never
instantiates; boundary ports for a zero-instance block are synthesized from the
declaration.

The `common` projects in `examples/ip_test` and `examples/simple_ip` are the
worked examples: shared constants, types, structures, interfaces, plus the
generic `cpu` block, generating their package / include / firmware artefacts.
Note that `builder/base/common/` is *not* a project — it is the framework runtime
source tree.

### How file ownership decides who generates what

Ownership is enforced at **three** gates, all resolving a file to an owning
project and returning early when it is not the running project:

- **Generation** — `systemcGen` and `systemVerilogGenerator` each call
  `resolveFileOwner` and skip foreign-owned files.
- **Scaffolding** — `newModule` mirrors the gate at each of its write sites.
- **Build manifest** — regeneration targets are owned-only, while compile sets
  and directories stay foreign-inclusive, so foreign artefacts compile without
  being regenerated.

Ownership also selects **placement**: `PROJECTLAYOUT` holds one layout per owning
project, each resolved against that project's own `dirs.root`. A parent build
therefore writes only its own tree.

Standalone and composed generation must leave every file owned by a nested
project byte-identical. A parent may instantiate a nested project's Config
templates at a new configuration, but it must not re-emit the nested project's
files.

Crucially, ownership is not merely a skip flag. It is an **identity axis inside
composite keys**: address groups are keyed `(owningProject, group)`, foreign
Config headers `(owningProject, child)`, the SystemC instance factory
`Key{blockType, variant, projectName}`, and per-variant Config semantic identity
`(projectName, block, variant)`.

### The reference-depth trap

Because ownership is "deepest provider closure wins, lexical tiebreak", an
assembler **must not** list a sub-project at the same closure depth as another
sub-project that includes it. Doing so attributes the shared context to whichever
provider sorts last, which **renames its generated module** and makes the build
unresolvable.

---

## 6. Parameterization

A parameterized block is one design description that realizes as a family of
concrete hardware configurations: differing widths, depths, payload shapes,
register sizes, and algorithm selectors.

### Declaration: `ipParameters` and `params:`

Three facts are deliberately **separated and separately owned**, and conflating
them is the most common authoring error:

| Fact | Written as | Owned by |
|---|---|---|
| **Declaration** | `ipParameters:` in the IP root — name, default `value`, `maxValue`, description | the IP owner |
| **Naming** | `params: [...]` on a block | whoever writes the block |
| **Binding** | a variant, stating where a value comes from | the assembler — frequently neither of the above |

**Declaration.** `ipParameters:` is a custom YAML section (not a schema table of
its own). Its child sections — `constants`, `types`, and `_mapto` aliases — are
processed through their normal schemas and then **marked parameterizable**.
Parameterizability then propagates transitively: a type whose width names a
parameterizable constant becomes parameterizable, and so on through structures,
interfaces, registers, memories, and connections. The affected schema sections
carry an `isParameterizable` column as a result.

`ipParameters:` is invalid in a shared include file, meaning one that another
file includes and that declares no `blocks:`, because "parameter bounds are tied
to the IP root". A declaration therefore lives in a file that declares blocks.

**Naming.** A block opts in by naming the constants it consumes:

```yaml
blocks:
    myFilter:
        params: [PIXEL_WIDTH, TAP_COUNT]
```

Two properties follow, and both matter:

- **A block param's name *is* the constant's name.** The backing link is derived
  from the param's own name and then resolved as a foreign key through this
  row's include chain. There is no aliasing or renaming at a parameter boundary,
  and therefore no positional binding — parameters match by name only. A
  parameter's *identity* is the file that declares it, so two same-named
  constants in two files are two different parameters.
- Its backing constant must be *parameterizable*; a plain constant is invalid
  (`validateBlockParamBacking`).
- **Naming is not declaring.** Any block that can reach the declaration through
  `include:` may name it, including a block in another project.

The aggregate rule is enforced separately: `_validateIpParametersLinkage`
requires every exposed `ipParameters` constant to be consumed by a block param in
the **same file** as the declaration. An upstream project therefore cannot
publish a parameter purely for downstream projects to `include:`; it must consume
its own knob.

### Variants and bindings

A **variant** is a named, complete assignment of a block's parameters:

```yaml
parameters:
    myFilter:
        hd:  { PIXEL_WIDTH: 10, TAP_COUNT: 5 }
        sd:  { PIXEL_WIDTH: 8,  TAP_COUNT: 3 }
```

- **Completeness is mandatory.** Every declared variant binds every parameter the
  block declares; there is no default-fill
  (`validateVariantParameterCompleteness`, a per-row `post` hook resolving the
  block in the row's own scope).
- **Emission is N+1.** The generator emits one baseline
  `<stem>DefaultConfig` plus one `<block><Variant>Config` per declared variant.
  Variants with identical values still receive distinct variant-named structs.
- A binding is **either** a literal `value` **or** container-sourced
  (`containerParam:`), never both; the singular shorthand `<param>: <scalar>`
  routes to `value`.
- Sizing is checked against the backing constant's `maxValue`, because address
  allocation uses worst-case widths (`validateVariantBindingSizing`).
- The leaf binding row's key carries the declaring `projectName`, so two
  assembler projects declaring the same local `(block, variant)` survive as
  distinct Config identities in one composed database.

Values flow into widths and layouts through the expression evaluator
`pysrc/evalExpr.py`, which owns a **frozen integer SystemVerilog
constant-expression subset** — every retained operator has an identical
SV/C++/C spelling, so emitters pass it through unchanged. It is project-neutral:
symbol qualification and value lookup are injected as callbacks. Each expression
is parsed once and evaluated up to twice — with declared values, and, if any
referenced symbol is parameterizable, again with `maxValue` for the worst case.
The canonical expression string is persisted, and symbolic emission for each
target language happens later (`emissionUtils`, and the SV package template).

`pysrc/valueResolver.py` is the parse-time arbiter of what a reference means and
of active-versus-worst-case, including the packed-field spans that the interface
compatibility gate compares.

`pysrc/evalPyToSv.py` is **one-time migration tooling**, not part of emission: it
rewrites legacy Python `eval:` strings in YAML into the SV subset, using Python's
own `ast` as the front end and applying targeted text spans so untouched text
stays byte-identical. It refuses two cases rather than guessing:
`real`-typed evals, and `//` floor division (which floors toward −∞ where SV `/`
truncates toward zero, so a blind rewrite would silently corrupt the ceiling
idiom `-(-a//b)`).

### The two container-inheritance mechanisms

Both answer "this child's configuration comes from its container", at different
granularities. They are **not** interchangeable.

**`containerParam:` — per parameter.** In a variant binding, one parameter is
sourced from a named parameter of whichever block contains the instance:

```yaml
parameters:
    myLeaf:
        inherited: { PIXEL_WIDTH: { containerParam: BUS_WIDTH } }
```

Properties:

- **The container is never named by the binding.** It is taken from the instance
  row at each site, so one variant means different concrete values in different
  containers. No `containerBlock:` field exists.
- **Names need not match.** `DP_ALGO: { containerParam: MID_ALGO }` is ordinary.
- **Inheritance is single level**, because that is what the hardware model
  permits: an SV parameter reaches a nested module only through a container that
  declares it. Multi-level configuration is a chain of single-level links, each
  intervening level declaring the parameter it forwards. A container is never a
  conduit for everything beneath it.
- **The relation is compatibility, not identity**: the container parameter's
  `maxValue` must not exceed the child's, because `maxValue` is the child's
  acceptance contract. The relation does not compare `valueType`.
- **It crosses project boundaries freely.** The container's and child's parameters
  may be different constants owned by different projects.
- **`containerParam` cannot be a foreign key**: a container block's `params:` are
  not reliably parsed before a child's binding rows, so the linkage is validated
  by a post-parse pass. The parse-time check is limited to row-local
  well-formedness.

**`inheritContainerParam` — the whole Config.** An instance flag, used *in place
of* `variant:`, declaring that the child is typed with its **container's entire
Config**. Because a contained child renders inside the container's templated class
scope, this reduces to spelling the container's own `Config` symbol at that
instance, and C++ template instantiation resolves the concrete struct at the
container's instantiation site — including transitively. No configuration value is
plumbed. Database creation enforces that the child's params are a **by-name
subset** of the container's and that **container and child have the same owning
project**.

Such an instance binds **no variant label**: it is one member of a type family a
registration key cannot select from, so its container names the class at the site
and it reaches no factory registration. A consequence worth knowing: HDL-wrapper
views must therefore source from a block's **declared** variants and params, not
its instantiated set, or a declared-but-uninstantiated variant silently renders as
a broken parameterless module.

**The two are not interchangeable, and the difference that matters most is
composition:** `inheritContainerParam` **cannot cross a project boundary**;
`containerParam` can. That asymmetry is precisely why the per-parameter form had
to exist for cross-project cases. The per-parameter form subsumes the whole-Config
form as its degenerate case (every parameter container-sourced, same names, same
project), but the whole-Config form remains the right choice where it applies.

### From YAML to two languages that must agree

A pervasive distinction governs this: **`hasOwnParams` versus
`isParameterizable`.** A block that declares its own `params:` becomes a class
template / parameterized module. A block that is parameterizable only because
parameterizable structures *transit its surface* (a container) is emitted
**non-templated**. A block with a parameterizable structure on its *own* surface
but no own params is invalid because it has no `Config` to instantiate the type
with.

The same parameterized block becomes:

- **C++** — a class template. The parameter set becomes a **Config struct**: one
  per declared variant, emitted in the block's *config context* (the file where
  its parameterizable declarations live, which is not necessarily its declaring
  file), in a header `<context>VariantConfig.h`. Members are
  `static constexpr`, with the C++ type chosen from `max(value, maxValue)`, so a
  worst-case-wide parameter gets a 64-bit field even when its current value is
  small. (`maxBitwidth` is a separate worst-case sizing input, used for
  parameterizable types and structures.) A container-sourced variant emits a **struct template
  over the container's Config** rather than a plain struct. A block's
  `defaultConfig` names the struct used when no variant override applies. A parent
  instantiating a child must name the child's per-variant Config, because the
  container's `dynamic_pointer_cast<childBase<childConfig>>` returns `nullptr`
  otherwise — the container translation unit is deliberately **not** config-free.
  Eval-derived constants are emitted **symbolically**, not frozen to literals, so
  `WIDTH_X2 = WIDTH * 2` recomputes inside each struct from that struct's own
  `WIDTH` — which is what makes deferring per-variant eval re-resolution sound.
- **SystemVerilog** — a parameterized module. Because SV cannot parameterize a
  package, every parameterizable constant, type, enum, and structure moves **out
  of the package and into module scope**, declared from the module's parameters;
  the package keeps only non-parameterizable items and stays byte-stable across
  variants. That module-local declaration set, with its dependency ordering, is
  derived once by `deriveParameterizedDeclSets` and persisted. Per-variant
  verilation uses a canonical include-only wrapper *body* plus a small per-variant
  trampoline that binds concrete values.

They must agree on **resolved bit layout**, and the compatibility barrier
(`validatePorts` and its helpers) is what enforces it: identical protocol,
identical structure list, identical field widths and bit offsets under the bound
variant. Field names are never compared.

Two boundary rules are easy to get wrong:

- **The HDL bridge emits a resolved bit-vector, not a struct** — and which width
  depends on the payload. A *parameterizable* payload structure bridges as
  `sc_bv<Struct<Config>::_bitWidth>`, tracking the variant. A *non-parameterizable*
  structure, and any `hdlparams`-derived signal such as the APB register bus,
  bridges at a **literal fixed width**. The fixed-width branch is intentional and
  applies on both sides; it is not a fallback.
- **A standalone per-variant wrapper binds resolved literals**, not parent
  symbols, because it is a top module with no enclosing scope to resolve a symbol
  in. The canonical wrapper *body* is parameterized and shared; the small
  per-variant trampoline that includes it supplies concrete `localparam`s, and
  that is what makes the SystemC and Verilated pin widths equal.

### Where a channel's Config comes from

When a channel payload is parameterizable, something must supply the Config it is
typed at. There are exactly three possibilities, and the design enumerates them:

1. **The container's own class template parameter** — the container lists the
   parameter in `params:`, so it is a template and the channel spells
   `payload<Config>`, resolved at the container's instantiation site.
2. **An unadapted end elects it** — an end whose declared port shares the
   connection's interface binds directly and types the channel with its own
   variant Config. The price is that the channel's configuration is no longer
   independent of that endpoint's.
3. **Nothing** — fails at `make db` with a diagnostic naming the channel, both
   ends, and the two available fixes.

---

## 7. Artefact generation and file ownership

### `fileMap` — the artefact catalogue

`fileGeneration.fileMap` in `project.yaml` (base ⊕ pro ⊕ user, key-level merge)
declares every **kind** of artefact.

Each entry declares:

- **`mode`** — the iteration domain: `block` (one per design block), `context`
  (one per authored YAML file), `registrar` (one per assembler × instantiated
  child), or `project` (exactly one).
- **`name`** and **`ext`** — filename suffix and logical→real extension map. The
  logical extension key is load-bearing: it keys both `INCLUDEFILES` and the
  PARAM-line mode table.
- **`basePath`** — a *segment key* into `dirs:` / `hierarchicalDirs:`, never a
  literal path. Segments map to toolchain groups via `buildGroups`
  (`sc` / `sv` / `vl`).
- **`cond`** (OR) / **`condAnd`** (AND) — a predicate over the block's flags
  (`hasMdl`, `hasRtl`, `hasVl`, `hasTb`, `isParameterizable`, `hasOwnParams`,
  `smartInclude`).
- Modifiers — `blockDir`, `variant` (one file per declared variant),
  `foreignConfig` (owner-qualified; only the declaring assembler emits),
  `requiresRegistrations` (suppress an empty trampoline).

Layout is either `functional` (`$root/<segment>/<decomp>`) or `hierarchical`
(`<node>/<segment>`), selected **per project file**, so a nested project uses its
own setting. Four keys — `yaml`, `prj`, `rundir`, `include` — are layout
*conventions*, not fileMap segments.

### Generated regions, user regions, and the crucial asymmetry

Region handling lives entirely in `pysrc/textfileHelper.py` (`codeText`), not in
the renderer. Three marker forms:

- `GENERATED_CODE_PARAM <args>` — one per file, file-level.
- `GENERATED_CODE_BEGIN <command>` — opens a region; the trailing text is parsed
  as a command line (`--template=`, `--section=`, `--handler=`).
- `GENERATED_CODE_END` — closes it.

On read, `codeText` accumulates everything outside regions verbatim — **including
the marker lines themselves** — and discards region bodies. On write it
interleaves preserved text with freshly rendered bodies, and writes only if the
bytes changed.

Two consequences follow structurally, not by policy:

- **The generator can never touch user code.** Preservation is a property of
  read/write symmetry.
- **`make gen` can never rewrite a marker or PARAM line**, because those are
  user-side bytes. Changing the stamp vocabulary therefore *requires* a migration
  phase; there is no self-healing path.

### `GENERATED_CODE_PARAM` — the file's self-description

The database records *what* exists. The file records *which* database object it is
a rendering of. The PARAM line carries `--block`, `--context`, `--parent`,
`--variant`, `--project`, `--mode`, `--scope`, `--hierarchy`, `--inst`,
`--excludeInst`, `--importPackages`.

It is written by exactly two producers — the scaffold templates
(`templates/fileGen/fileGen.py`) and the migration re-stamp
(`pysrc/migrateProjectParam.py`) — which share helper code
(`pysrc/genFileParam.py`) so a re-stamped line is byte-identical to a fresh
scaffold. It is read on every `make gen`, merged into every region's arguments,
and consumed by the ownership gate.

The gate's branch order is **load-bearing**: `--project` first, then `--parent`
(a registrar trampoline is assembler-owned), then `--block`, then `--context`;
absent all of them, `None`, meaning "always generate". The reason is composition:
context keys are build-root-relative, so a child's standalone build stamps a
child-relative `--context` spelling a parent build cannot resolve. `--project` is
the only token that lets a parent recognise and skip a child-owned file.
Context-key resolution demands an **exact** match and exits with a `make migrate`
instruction otherwise.

Nothing outside the file maps a path back to a database identity. A stale or
corrupt stamp is therefore unrecoverable by inference, so stamp identity
failures are hard errors and migration must re-stamp the file.

### Scaffold-once versus regenerated

Three distinct write disciplines:

| Discipline | Who | Behaviour |
|---|---|---|
| **Create-only** | `newModule` fileMap writers | Write whole file incl. stamp and empty regions; skip if it exists **unless `--overwrite`** |
| **Scaffold-once** | `newModule` `scaffold_create` | Skip if it exists, **ignoring `--overwrite` entirely**; no markers; `gen` never touches them; absent from the manifest |
| **Regenerate in place** | `systemcGen`, `systemVerilogGenerator` | Never create; open existing, rewrite region bodies only |

So: **`make gen` does not create files; `make newmodule` does not fill them.**

File classes are keyed on **segment role**, not literal directory (so the rule is
identical in both layouts). Migration derives wholesale-clean eligibility from
the frozen legacy map, where the wholesale-clean set is `{base, vl_wrap}`:

1. **GENERATED-deletable** — `base`, `registrar`, `vl_wrap`, `fwInc`.
2. **USER-PRESERVE in place** — `model`, `rtl`, `tb`, plus `fw/src`. Never
   deleted; generated regions inside *are* still rewritten.
3. **INPUT** — `arch/yaml`. Never touched.
4. **USER BUILD-CONFIG** — `include/`, per-segment makefiles. Never deleted.

Segment class answers "who owns the bytes"; it does **not** mean the generator
never rewrites the file. Named exceptions: `fw` is split (`fw/include` generated,
`fw/src` user-owned and not a segment at all); `verif` is mixed.

### The build manifest

`config/createBuildManifest.py` runs inside `projectCreate` (via
`createArtifacts:`) and emits `.gen/build.mk` plus a `BUILDMANIFEST` blob: source
directories, generated file lists, module files, verilated tops, and the
per-project `rtl.f`. It re-walks the merged `fileMap` using the *same* placement
primitives as `newModule`, explicitly so the manifest cannot drift from what is
actually emitted. Regeneration targets are owned-only; compile sets are
foreign-inclusive. Makefile consumption wraps the lists in `$(wildcard ...)`
deliberately: the manifest lists **intent**, and a not-yet-scaffolded file must
not be a missing prerequisite. `EXTRA_SC_GEN_FILES` / `EXTRA_SV_GEN_FILES` are
the documented seam for the user-hosted files carrying generated regions that no
fileMap entry expresses. The rule is fileMap first, seam only for what falls
outside it. `examples/mixed` and its encoder units are the seam's only user in
base or pro.

### Migration

Migration exists because artefacts are a **second source of truth** that the
database cannot rewrite. `migrateYaml.py` orchestrates:
eval Python→SV, `addressControl.yaml`→per-block `addressBlock:`, include
header→`.cppm` module, variant schema reshape, sub-project recursion, orphan
sweep, PARAM re-stamps, module end-label re-stamp, testbench restructuring, and
the `.cpp/.h`→`.cppm` user-code transplant.

A single top-level `yamlFormat: 2` sentinel in `project.yaml` gates the whole
project, and `projectCreate` hard-stops without it. The sentinel is **coarse** —
whole-project, not per-phase. Several phases therefore run *before* the
already-stamped short-circuit. Exit statuses distinguish clean /
manual-work-remains / blocked, and
`make migrate` chains text phases → `db` → sweep → `newmodule` → tb port → `gen`
→ module port, an order dictated by the create/fill split above.

Migration must know about ownership (so a composed build does not delete or
re-stamp a child's artefacts), about stamps (whose vocabulary it is changing),
and about user regions (which it transplants rather than regenerates).
