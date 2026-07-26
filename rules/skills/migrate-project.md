---
name: migrate-project
description: Migrate an existing arch2code project to the current authoring format using `make migrate` (eval Python→SV, addressControl→per-block, include header→cppm modules, orphan sweep, scaffold, regenerate) and resolve every manual item the tool reports, including the agent-driven `.cpp/.h`→`.cppm` port of a parameterized block. Use whenever a project fails the projectCreate yamlFormat gate, still pins context includes to header mode, carries stale generated orphans, or the user asks to run/finish a project migration.
---
# Skill: Project Migration

This is the single operational guide for migrating an arch2code project. It
supplements the programmatic migration: the tool (`make migrate`) does every
mechanical edit, and this skill explains how to invoke it and resolve the items
it can only report.

## 1. Run the tool

```text
make migrate
```

`make migrate` is the single command — issue it once and everything happens. It
is idempotent: a fully migrated, orphan-free project is a no-op. The target is a
five-step pipeline. The first two steps halt the target on a non-zero exit, so an
unresolved yaml-stage item stops the run before the database is built. The sweep
(step 3) does **not** halt: it applies its deletes, then `newmodule` and `gen`
always run to rescaffold the purely-generated blocks, and only afterward is the
sweep's exit code re-raised — so a remaining agent-driven port (`TODO_PORT`)
leaves the tree scaffolded while `make migrate` still signals non-zero:

1. **`migrateYaml.py --write <project.yaml>`** — the text conversion + stamp.
   Standalone and text-only (it never opens the database); runs the three
   conversion phases below and, only when they leave no manual work, stamps
   `yamlFormat: 2`. A remaining manual item makes it exit non-zero, halting the
   pipeline **before** the database is built — resolve the items and re-run.
2. **`make db`** — builds the database from the now-stamped YAML (the yamlFormat
   gate passes).
3. **`migrateYaml.py --sweep --db <db>`** — the orphan sweep. This step opens the
   database **read-only**, removes the stale purely-generated orphans the form
   changes left behind (every delete marker-guarded by `GENERATED_CODE_BEGIN`,
   never `git`), and reports the files it cannot touch (`TODO_PORT`,
   `TODO_USER_INCLUDE`, `TODO_UNGENERATED_FILE`). It sweeps two ways, keyed on the
   embedded legacy file map. A **fully-generated segment** — one whose every legacy
   entry is `delete`, i.e. `base` and `vl_wrap` (and `registrar` on the
   hierarchical path, Section 7) — is cleared at the **directory** level: every
   marker-carrying source file found there is deleted, so alternate-extension or
   renamed orphans a per-file map expansion would miss (a pre-`.cppm`
   `<block>Base.h`, a model-only `<block>Tandem.*`, a stale `*_hdl_sc_wrapper.h`)
   are caught too. A **mixed segment** that also holds user code (`model`, `rtl`)
   keeps the per-file delete-by-map-expansion for its generated context files
   (`<context>Includes.{h,cpp}`, `<context>_package.sv`) and preserves the user
   code beside them; the `tb` segment is left untouched. `make newmodule` / `make
   gen` then recreate the cleared artifacts.
4. **`make newmodule`** — create-only; scaffolds the new-form files (for example
   the `<context>Includes.cppm` module interfaces). It runs after the sweep so
   the orphans are gone before regeneration.
5. **`make gen`** — fills the generated regions of the scaffolded files.

The text conversion (step 1) runs these phases over the project's YAML file set:

- **Phase A — eval Python→SV.** Rewrites Python-syntax `eval` strings into the
  frozen SV subset (for example `($X-1).bit_length()` → `$clog2($X)`).
- **Phase B — addressControl → per-block.** Emits `addressBlock:` on each
  resolved router, moves policy sections to `project.yaml`, normalizes
  `postProcess:`, removes the `addressControl:` pointer, and deletes the legacy
  `addressControl.yaml` when clean.
- **Includes — include header → cppm module.** Removes a legacy
  `fileGeneration.fileMap` `include` override (paired `.h`/`.cpp`) so the project
  inherits the base `cppm` module-interface definition, and deletes the orphaned
  generated `<context>Includes.{h,cpp}` files. The firmware
  `<context>IncludesFW.{h,cpp}` files are left in place (firmware headers remain
  header mode by design). This conversion is part of `yamlFormat: 2`; it runs
  before the stamp short-circuit so a project stamped before the phase existed
  still has its includes migrated.
- **Module header — single region → GMF + moduleExport.** Restructures every
  block-module `.cppm` (one carrying a `moduleScaffold --section=blockModuleHeader`
  region) from the legacy single header region into the three-section form:
  GMF-only `blockModuleHeader`, a new `moduleExport` region owning `export module`
  + the imports, and two seeded user slots (`// user #includes here` in the GMF
  zone, `// user imports here` in the preamble). It inserts the `moduleExport`
  region and the `// user imports here` slot just before the class region
  (`classDecl`, or `blockRegs --section=header` for a reg-handler); the next
  `gen` refills `blockModuleHeader` to GMF-only and populates `moduleExport`. The
  old user gap between the header and class regions ends up in the GMF zone, so an
  existing `#include "endOfTest.h"` there lands in the GMF slot automatically. It
  manipulates markers only — every span below the class region is untouched. Part
  of `yamlFormat: 2`, idempotent (a file already carrying a `moduleExport` region
  is a no-op), and, like the includes phase, runs before the stamp short-circuit.

Because a stamped-but-orphan-carrying project exits step 1 with zero, the
pipeline still proceeds to sweep, scaffold, and regenerate it — so `make migrate`
finishes the job on a partially migrated tree, not only a pristine one.

## 2. Read the report

Applied edits are listed under `applied:`. Items the tool cannot complete are
listed under `manual TODO:` as:

```text
<file>:<line>  <KIND>  <message>
```

Resolve every reported item, complete the recreation steps below when the
includes or block-port work applies, then re-run `make migrate` to confirm a
clean report.

### Manual-TODO kinds

| Tool report `KIND` | Emitted by | Meaning | Resolve with |
| --- | --- | --- | --- |
| `TODO_ROUTER_RESOLUTION` | address phase | An `AddressGroups` row's router cannot be resolved. | `address-migration` skill, Step 3 |
| `TODO_INTERFACE_SCOPE` | address phase | A router has no `addressBus: true` interface in its load-time scope. | `address-migration` skill, Step 2 |
| `TODO_LEAF_REGISTER_PORTS` | address phase | A routed leaf needs `registerPorts:`. | `address-migration` skill, `registerPorts:` note (Migration Diagnostics) |
| `TODO_USER_IMPORT` | includes phase | Hand-written user code `#include`s a migrated context header. | Section 4 below |
| `TODO_MODULE_IMPORT` | module-header phase | A hand-added `import` line was left in the old header→class gap, which the restructure moved into the GMF zone (before `export module`) where imports are illegal. Never moved by the tool. | Section 4a below |
| eval `NEEDS_MANUAL` | eval phase | A real-valued eval (e.g. `$DWORD / 2.0`) cannot be expressed in the SV subset. | Replace the `eval:` with a literal `value:` (hand decision). |
| `TODO_PORT` | orphan sweep | An old-form user `.cpp`/`.h` pair that the current map now produces in a different form — a block that was parameterized so its artifact is a single `.cppm`. Never deleted by the sweep. | Section 6 below (agent-driven port) |
| `TODO_USER_INCLUDE` | orphan sweep | Hand-written user code `#include`s a generated header the sweep deleted. Same fix as `TODO_USER_IMPORT`. | Section 4 below |
| `TODO_UNGENERATED_FILE` | orphan sweep, includes phase, or layout migration | A file that carries no `GENERATED_CODE_BEGIN` marker and either matches a per-file delete-target name **or** sits inside a wholesale-cleared fully-generated segment (`base`, `vl_wrap`). Skipped and reported, **never deleted**. | Inspect it: it is user-owned (hand-move/keep) or a generated file whose marker was lost (regenerate). |
| `TODO_MISSING_BASEPATH` | orphan sweep | A legacy file-map `basePath` is absent from the current layout, so that entry is skipped. | Rare; confirm the layout is expected. No file action is needed if the path genuinely no longer exists, but the item keeps the sweep's report non-clean, so `make migrate` still exits non-zero until the stale entry no longer applies. |
| `TODO_UNSUPPORTED_LAYOUT` | orphan sweep | A context owner uses the hierarchical layout, which the sweep does not walk. | Complete the format migration in functional layout, then migrate to hierarchical (Section 7). |

The address-control kinds are documented in depth in the `address-migration`
skill; each converter message points at the resolving step or note named in the
table above. The sweep only ever **deletes** purely-generated orphans; every
user-owned file it encounters is reported, not touched.

## 3. Wire user-hosted generated-region files into the build

After migration the build enumerates generated source from the DB-derived
manifest (`A2C_SC_GEN_FILES` / `A2C_SV_GEN_FILES`, emitted by
`config/createBuildManifest.py` and consumed wildcard-filtered by
`a2c-common.mk`), replacing the old build-time `find … grep GENERATED_CODE_`
scan. The manifest lists **only** files arch2code scaffolds whole through the
fileMap, so a **user-hosted generated-region file** — a host whose name and
segment are user-authored while arch2code injects only its generated sections —
is no longer auto-discovered. Left unwired, it silently drops out of **both**
generation and compilation.

Identify them: a file that carries `GENERATED_CODE_BEGIN` markers yet is **not**
scaffolded by any fileMap entry (`make newmodule` never creates it). The common
cases are the address headers emitted through the `includes` template
(`regAddresses.h`, `axi4sRegAddresses.h`) and the encoder units emitted through
the encoder templates (`mixedEncoders.h`, `mixedEncoder_package.sv`). Wire each
one onto the matching seam in the project's `include/make/shared.mk`, above the
`include … a2c-common.mk` line — SystemC/C++ hosts (`.h`/`.cpp`/`.cppm`) on
`EXTRA_SC_GEN_FILES`, SystemVerilog hosts (`.sv`/`.svh`) on `EXTRA_SV_GEN_FILES`:

```make
# User-hosted generated-region files: arch2code injects generated sections into
# these user-authored hosts (address defines via the includes template, encoder
# units via the encoder templates). Not fileMap-scaffolded, so they ride the
# EXTRA_ generation seam.
EXTRA_SC_GEN_FILES = $(REPO_ROOT)/model/regAddresses.h
EXTRA_SV_GEN_FILES = $(REPO_ROOT)/rtl/mixedEncoder_package.sv
```

The seam layers onto the manifest baseline: listed files stamp for regeneration
and compile alongside the scaffolded set. The stock examples show the pattern —
`examples/{apbDecode,simple_ip,ip_test}` wire a `regAddresses.h`, `axi4sDemo` and
`hierVlDemo` wire an `axi4sRegAddresses.h`, and `mixed` wires both an encoder
header and its `_package.sv`. The `manage-build` skill covers the make targets
that regenerate and compile the wired files.

### Sweep the retired vl build tree

The whole-design Verilator build now lives under `rundir/build/vl`
(`A2C_VL_BUILD_DIR = $(BIN_DIR)/vl`, driven by
`include/make/a2c-vl-build-entry.mk`); the old per-project `prj/verif/` build
`Makefile` is retired and is no longer relocated by any migration step. When
migrating an existing project, delete any stale `prj/verif/` vl-build `Makefile`
and its `obj_dir` / built lib so they do not shadow the new build location.

## 4. Finish an includes (header → cppm) migration

When the report shows an `Includes` phase that applied edits, the project moved
from paired-header context includes to C++20 module interfaces. Whether the
`.cppm` interfaces already exist depends on the report: a `TODO_USER_IMPORT` from
the includes phase keeps `yamlFormat: 2` un-stamped, which makes step 1 exit
non-zero and halts the pipeline **before** `make db`/`newmodule`/`gen` — so the
`<context>Includes.cppm` files are **not** yet recreated. Fix the import sites
below first, then re-run `make migrate`: on the clean second pass step 1 stamps
and the pipeline continues, so `make newmodule` scaffolds the missing
`<context>Includes.cppm` and `make gen` fills them. The remaining work is
hand-written code and stale build state:

1. **Fix `TODO_USER_IMPORT` / `TODO_USER_INCLUDE` sites.** A hand-written source
   file that does:

   ```cpp
   #include "<context>Includes.h"
   ```

   must instead import the module. Read the exact module name and namespace from
   the top of the generated `<context>Includes.cppm` — `export module <module>;`
   and `export namespace <module>_ns` — rather than deriving them from the
   filename; the module name need not equal the file stem. In the common case it
   is the context stem without the `Includes` suffix, so a file that included
   `axi4sDemo_tbIncludes.h` becomes:

   ```cpp
   import axi4sDemo_tb;
   using namespace axi4sDemo_tb_ns;
   ```

   Generated files (those carrying `GENERATED_CODE_BEGIN`) are skipped wholesale
   by the scanner and **not** reported — `make gen` rewrites the include in their
   *generated* regions into an `import` automatically. Two caveats: an include a
   user placed in a *user* region of a generated file is neither reported nor
   rewritten (move it by hand), and the scanner matches only the quoted form
   `#include "..."` — an angle-bracket `#include <...>` is not detected. Only
   user-authored files need this edit.

2. **Clear stale build artifacts.** A prior header-mode build leaves `.d`
   dependency files that reference the deleted `.h`. The example `clean` target
   removes only the database and `.gen`, not the rundir build tree, so a stale
   `.d` can break the next build with `No rule to make target ...Includes.h`.
   Remove the rundir build tree before rebuilding:

   ```text
   rm -rf <project>/rundir/build
   ```

3. **Verify.** Rebuild and run the project's normal targets (for example
   `make -C <project>/rundir all run`). A clean build and run confirms the
   migration.

## 4a. Relocate a stray module import (`TODO_MODULE_IMPORT`)

The module-header restructure moves the old user gap (between the legacy header
region and the class region) into the **GMF zone**, before `export module`. A
non-modular `#include` there is correct — it attaches to the global module. A
hand-added **`import`** there is not: C++20 forbids an import before the module
declaration (clang: `imports must immediately follow the module declaration`).
The tool reports each such line as `TODO_MODULE_IMPORT` and never moves it.

Fix it by hand: cut the `import <name>;` line out of the GMF gap (between the
`blockModuleHeader` `GENERATED_CODE_END` and the `moduleExport`
`GENERATED_CODE_BEGIN`) and paste it into the `// user imports here` slot (the
gap between the `moduleExport` `GENERATED_CODE_END` and the class region's
`GENERATED_CODE_BEGIN`). That slot is the module preamble, where imports are
legal. Order within the slot: every `import` first, then any `using namespace`.
Do **not** paste inside a generated region. Re-run `make migrate` to confirm the
`TODO_MODULE_IMPORT` is gone.

## 5. Adopt the generated `createTbTop()` helper

The testbench top is instantiated through a generated helper. `make gen` emits,
into the `tbConfig` generated region of each testbench's `<block>Config.cpp`,

```cpp
std::shared_ptr<blockBase> createTbTop(void)
{ return instanceFactory::createInstance("", "tb", "<block>Testbench", "", "<project>"); }
```

so the factory `createInstance` — including the `projectName` factory key that
must match the tb-top registration — is regenerated on every `make gen`. The
project rule is that this `createInstance` for the tb-top **is generated** (lives
inside `createTbTop`), and is **never** hand-written in a user region.

A testbench predating the helper instantiates the tb-top by hand in the **user
body** of `createTestBench()`:

```cpp
// user region — pre-helper form
std::shared_ptr<blockBase> tb =
    instanceFactory::createInstance("", "tb", "<block>Testbench", "");
```

`make gen` recreates the generated half (it emits `createTbTop`) but never
rewrites the user body, and the tool flags **no** TODO for this — so fix the call
site by hand. Replace the raw `createInstance` with a call to the helper:

```cpp
// user region — after
std::shared_ptr<blockBase> tb = createTbTop();
```

This is the only edit: the factory call now sits in the generated `createTbTop`,
and the user code just calls it, so the emitted `projectName` key stays correct
across regenerations.

## 6. Port a parameterized block (`.cpp`/`.h` → `.cppm`)

The orphan sweep reports `TODO_PORT` when a block was **parameterized** — its
YAML now declares its own `params:` — so the current file map produces a single
`<block>.cppm` module interface in place of the legacy `<block>.h` + `<block>.cpp`
pair. Those old files still hold the block's hand-written code, so the sweep
leaves them untouched and reports them. A block left non-parameterized keeps its
`.cpp`/`.h` form and is never reported.

A synthesized `<block>_regs` handler is a special case: it is generated wholesale
through the `blockRegs` template and holds **no** user code (its only
non-generated span is an empty member placeholder). So if a legacy
`<block>_regs.h`/`.cpp` pair is flagged `TODO_PORT`, it is a
regenerate-not-port case — delete the legacy pair and let `make gen` recreate the
`.cppm`. Do **not** run the four-slot procedure below on it: a reg-handler has no
user slots to carry over.

`make migrate` performs mechanical **format** conversion only; it does **not**
parameterize a block, and it does not attempt this port. The port is
**agent-driven** and is two transformations. Do them in the order below —
**T2 (templatize) first, then T1 (move)**; the labels are historical, the
sequence is what matters:

### T2 — templatize the user code (do this first, in place on the legacy files)

The block is now a class template on `Config`, so its hand-written code must be
made template-correct **before** it is moved. This step requires understanding
the code — it is not a text substitution:

- Prefix every out-of-line definition with `template<typename Config>` and
  rewrite `<block>::` to `<block><Config>::`.
- Qualify dependent return/member types. The in-tree convention brings inherited
  types into scope with an in-class `using typename <block>Base<Config>::acc32_t;`
  declaration, then writes out-of-line definitions in the trailing-return form —
  e.g. rewrite a leading `acc32_t <block>::f(...)` to
  `auto <block><Config>::f(...) -> acc32_t`.
- Reach inherited base members through `this->` (or the matching `using`
  declaration) where the compiler now treats them as dependent names.
- Switch a user `#include` of a now-module dependency to the matching `import`,
  minding the name form: a parameterized sibling **block** becomes
  `import <sibling>.block;` (block module names are dotted), while a migrated
  **context** header becomes `import <context>;` (bare stem). A sibling block that
  was **not** parameterized is still `.h`/`.cpp`, not a module — leave its
  `#include` alone.

If the block cannot be made template-correct, the parameterization itself is
wrong — fix that before porting.

### T1 — move the user regions into the single `.cppm` (mechanical)

The pipeline scaffolds `<block>.cppm` with empty user regions via `make
newmodule` + `make gen`, which run even while ports remain — so after `make
migrate` the `.cppm` already exists and is ready to port into, and the
purely-generated blocks the sweep deleted are rescaffolded (`make migrate` still
exits non-zero to signal the pending ports). The legacy
files and the new `.cppm` carry the same
generated-section markers, so every stretch of user code sits between the same
two markers (or after the last one) in both, and transplants by that anchor. A
block has **four** user slots, and all four must move — do not treat the `.cpp`
as only "out-of-line methods":

- **Class body** (from `<block>.h`): the members after the `--template=classDecl`
  `GENERATED_CODE_END` and before the class-closing `};` → the same slot in the
  `.cppm` (after its `classDecl` `GENERATED_CODE_END`, before `};`).
- **Constructor init list** (from `<block>.cpp`): the user init-list entries
  (e.g. `,m_bayer_pattern_reg(...)`) between the `--template=constructor
  --section=init` `GENERATED_CODE_END` and the `--section=body`
  `GENERATED_CODE_BEGIN` → the same between-markers slot in the `.cppm`.
- **Constructor body** (from `<block>.cpp`): the user statements after the
  `--section=body` `GENERATED_CODE_END` and before the constructor's closing
  `};` — this includes the essential `SC_THREAD(...)` registrations and any
  `static_assert` — → after the same marker in the `.cppm`, before the `};`.
- **Out-of-line definitions** (from `<block>.cpp`): everything after the
  constructor's closing `};` to end of file → the tail of the `.cppm`.

The constructor-body and out-of-line slots are one contiguous region in the file
(both follow the `--section=body` `GENERATED_CODE_END`, split only by the
constructor's `};`); move the whole region so neither half is lost.

Never paste inside a `GENERATED_CODE_BEGIN`/`END` region. Drop the legacy
boilerplate the module form replaces: the `#ifndef` guard, `#include
"systemc.h"`, and the `#include "<block>.h"` at the top of the old `.cpp`.

### Restore body-only context imports

The generated `.cppm` header emits only `import` lines — `import <block>.base;`
plus a context `import` for every context the block's **generated surface**
structurally references (registers, memories, ports, connections). The matching
`using namespace <ctx>_ns;` lines are emitted at the **head of the
`--template=classDecl` region**, not in the header, so the header always ends
import-only. The generated set does **not** cover a context type or constant used
only in the implementation **body** (e.g. `bayer_pattern_reg_t`,
`NUM_LINE_BUFFERS`) — the generator has no structural reference to key on, so that
import is the migrating agent's job. If the build reports `must be imported from
module '<ctx>'` or `use of undeclared identifier`, add `import <ctx>;` (and
`using namespace <ctx>_ns;` unless that context is already covered by the
generated usings) for each such context.

Put them in the non-generated purview gap between the module-header
`GENERATED_CODE_END` and the `--template=classDecl` `GENERATED_CODE_BEGIN` — that
region is module purview and survives `make gen`. Because the header ends
import-only, that gap always sits inside an open module preamble, so a hand-added
`import` there is always valid (any generated `using namespace` sits later, at the
classDecl head). Order within the gap: every `import` first, then any
`using namespace` (and before any declaration-introducing `#include`); C++20
requires all import-declarations to precede the first non-import declaration
(clang: `imports must immediately follow the module declaration`). Do **not**
paste the `import` inside a generated region.

### Finish the port

Once `<block>.cppm` holds the ported code, delete the now-superseded legacy
`<block>.h` and `<block>.cpp` (the sweep never deletes them — `port`-disposition
entries are excluded from its delete set by construction), then re-run `make gen`
and build. Re-run `make migrate` to confirm the `TODO_PORT` is gone.

### When a block pulls a module-hostile library

Some libraries cannot be safely included in a module **purview** — notably ones
that pull SIMD-intrinsic or precompiled headers (e.g. OpenCV). Their headers
attach to the named module and clash with the global module, producing errors
like `declaration of '<sym>' in the global module follows declaration in module
<block>.block`; global-module-fragment hoisting does not reliably fix it.

This is project-specific and a design decision, not a mechanical port step — the
migrating agent works out the right approach for the block. In general, keep the
library out of the module purview: confine its use to a plain, separately-compiled
`.cpp` (global module) behind an opaque/pimpl interface so the parameterized
template names no library types, or leave the block non-parameterized (`.cpp/.h`,
no module) if parameterization is not essential.

## 7. (Opt-in) Migrate to hierarchical layout

The functional → hierarchical layout migration is a **separate, opt-in step**,
not part of the `make migrate` chain above and **not** gated by the
`yamlFormat: 2` stamp. A project stays valid in functional layout forever; this
step runs only when the project has chosen the hierarchical layout but its tree
is still laid out functionally on disk.

**Order matters — migrate to format-2 *while still functional*, then opt in.**
Run `make migrate` **first, before adding any `layout:` key**, so the project
reaches `yamlFormat: 2` in functional layout. Do not opt into hierarchical before
`make migrate`: its orphan sweep does not walk a hierarchical context owner and
would report `TODO_UNSUPPORTED_LAYOUT` and stop. Only after `make migrate` is
clean, **opt in** by hand-adding `layout: hierarchical` under `fileGeneration:` in
the project YAML (the base default is `functional`) — that declaration is what
makes the project a migration candidate. Then run:

```text
make migrate-hierarchical
```

`make migrate-hierarchical` wraps `migrateYaml.py --to-hierarchical --write
<project.yaml>`. Unlike `make migrate`, it is a single standalone step: it only
relocates the tree (it never builds the database, sweeps orphans, or
regenerates), and it is idempotent — re-running a migrated project is a no-op.
There is no `make` dry-run target; run `migrateYaml.py --to-hierarchical
<project.yaml>` directly (without `--write`) for a dry run that prints the full
move/delete/rewrite map and changes nothing. Because it does not regenerate, you
finish it by hand (see "Finish the migration" below).

### When it runs

The step is a no-op unless the project is a migration candidate:

- **Not opted in** — `fileGeneration.layout` is `functional` (the default). The
  report says nothing to do.
- **Already hierarchical** — the project file already sits under
  `<prj>/<yaml>/`. The report says nothing to do.
- **Candidate** — `fileGeneration.layout: hierarchical` is declared but the tree
  is still functional. Relocation runs.

Because relocation moves files where the unconditional phases edit content in
place, it **presupposes the project is already `yamlFormat: 2`**. A candidate
that opts into hierarchical before being format-2 clean is reported as
`TODO_NOT_FORMAT2` and nothing is moved: run `make migrate` first, then
`make migrate-hierarchical`.

### Composed / nested-provider projects

`make migrate-hierarchical` auto-converts a **genuinely independent** sub-project
— its own `project.yaml`, no other provider nested in-tree — cleanly. Run the
dry-run first and confirm it reports **zero escaping moves and zero manual
items** before applying.

A project that **nests providers** — a parent composing child projects in-tree
via vendored symlinks or cross-project references (a composition root, or a
bridge that vendors another IP) — needs **manual** handling: automatic
relocation would try to move sibling/provider files that live outside the
migrated project's own tree ("escaping moves"). Convert **leaf-first** — migrate
the independent child sub-projects before the nesting parent — so the parent's
re-pointed references resolve. For the parent:

1. Re-point cross-project references at the children's **new** post-migration
   locations (`prj/yaml` + per-node `<node>/yaml`).
2. Apply the relocation. There is **no** "drop escaping moves" switch:
   `--to-hierarchical --write` applies every safe move/delete and reports each
   out-of-tree reference as `TODO_UNREWRITABLE_PATH`, leaving it in place. The
   write is **not** transactional — the safe moves are applied even when it exits
   non-zero, and it cannot roll back (a mid-sequence destination clash can leave
   the tree half-moved). So re-point the references (step 1) first and confirm a
   clean dry-run **before** writing.
3. Hand-fix any `TODO_UNREWRITABLE_PATH` reference whose relative-path depth
   changed.

Two invariants:

- In-tree nesting requires the **parent** to be `hierarchical`; a `functional`
  parent may only compose children as external siblings.
- A child project file must be referenced via `projectFiles:`, never `include:`
  (a db-time guard enforces this — a project file provides nothing to `include:`
  scoping).

File ownership across a composition follows the **projectFile reference
closure** — the deepest project file whose `projectFiles:`/`include:` closure
reaches a file owns it — not directory location, so relocation never changes
ownership.

### What it moves

For an unblocked candidate the tool relocates the tree, preserving user content
byte-for-byte:

- **Authored YAML.** `arch/yaml/<decomp>/*.yaml` → `<decomp>/yaml/*.yaml`. A
  block with no decomposition subdir (`decomp=""`) maps to the **project-root
  node** (`yaml/*.yaml` at the project root); no node directory is synthesized.
- **Project file** → `prj/yaml/<projectName>Project.yaml`; **integration
  orphans** (`fwIpMain`, `sc_main`, and the `vl_wrap` aggregator sources
  `vl_wrap.{cpp,h,sv}` / `vl_dummy.sv`) → `prj/fw/` / `prj/verif/` (flattened). No
  vl-build `Makefile` is relocated: the whole-design Verilator build is make
  infrastructure under `rundir/build/vl` (`A2C_VL_BUILD_DIR`, driven by
  `a2c-vl-build-entry.mk`), not a per-project file — sweep any stale
  `prj/verif/` build `Makefile`/`obj_dir` (Section 3). **Build-config `include/`
  and `rundir/` stay at the project root** — they are user-owned entry points,
  not `prj/` orphans. The only
  harness change is the `A2C_PRJ_YAML` line in the root `include/make/shared.mk`,
  which the tool re-points at the moved project file
  (`$(REPO_ROOT)/prj/yaml/<projectName>Project.yaml`); every other
  `$(REPO_ROOT)/include/make/...` reference keeps working unchanged.
- **Source.** The same directory-level wholesale clear applies here. A
  **fully-generated segment** — one whose every fileMap entry is whole-file
  generated: `base`, `registrar`, `vl_wrap` — is cleared at the **directory**
  level: every marker-carrying file is **deleted** (guarded by
  `GENERATED_CODE_BEGIN`), so alternate-extension or renamed orphans a per-file
  name match would miss go with it, and all are recreated at the hierarchical
  location by `make newmodule` / `make gen`. A **mixed/user segment** (`model`,
  `rtl`, `tb`, `fwInc`) is classified per file: its recognized generated source
  (`Includes`, `_package`) is deleted the same marker-guarded way, while every
  other source (user-editable, or an unrecognized/custom fileMap type) **moves**
  byte-preserving so its user regions are never lost. A project-scope orphan
  (`sc_main`, `vl_dummy`, the retired `vl_wrap.*` aggregator) is moved into `prj/`
  regardless of segment. A non-marker file inside a fully-generated segment is
  reported (`TODO_UNGENERATED_FILE`) and left in place — never deleted, never
  moved.
- **Relative references.** Relative `include:` / `projectFiles:` directives and
  relative `#include` / `` `include `` paths inside **user regions** are
  re-rooted through the new `yaml/` levels. Generated regions are left for
  `make gen` to refresh; `$macro` and absolute paths are left alone.

### Read the report

`renderLayoutReport` prints the move/delete/rewrite map under either `DRY-RUN`
(no `--write`) or `APPLIED` (`--write`). Manual items are listed for hand fixup
using the same `<file>:<line>  <KIND>  <message>` format as the other phases:

| Tool report `KIND` | Meaning | Resolve with |
| --- | --- | --- |
| `TODO_NOT_FORMAT2` | Hierarchical opted in before the project is `yamlFormat: 2`. Nothing is moved. | Run `make migrate` first, then `make migrate-hierarchical`. |
| `TODO_UNGENERATED_FILE` | A source file matches a fully-generated name but carries no `GENERATED_CODE_BEGIN` marker. Left in place, **never deleted**. | Inspect the file: hand-move it to its hierarchical location, or add the marker if it should be generated. |
| `TODO_UNREWRITABLE_PATH` | A relative `include:` / `projectFiles:` reference (or an authored YAML) resolves outside the migrated tree. Left byte-for-byte. | Re-point the reference by hand after the move. |

### Finish the migration

The deleted fully-generated source is recreated at the hierarchical location:

```text
make clean      # rebuild the database from the relocated project.yaml
make newmodule  # create the generated modules at the hierarchical location
make gen        # fill the generated regions
```

As in Section 4, a prior build leaves `.d` dependency files that reference the
old paths; remove the rundir build tree (`rm -rf <project>/rundir/build`) before
rebuilding. Then rebuild and run the project's normal targets to confirm the
migration, and resolve any manual item the report listed.

## References

- `make migrate` / `migrateYaml.py` — the unified orchestrator.
- `make migrate-hierarchical` / `migrateYaml.py --to-hierarchical` — the opt-in
  layout migration (`pysrc/migrateLayout.py`).
- `pysrc/evalPyToSv.py` (Phase A), `pysrc/migrateAddressControl.py` (Phase B),
  `pysrc/migrateIncludes.py` (Includes phase), `pysrc/migrateModuleHeader.py`
  (Module-header phase) — the text-conversion phase libraries.
- `pysrc/migrateOrphans.py` — the orphan sweep (`migrateYaml.py --sweep`): the
  embedded legacy file map, its `delete`/`port`/`leave` dispositions, and the
  `TODO_PORT` / `TODO_USER_INCLUDE` / `TODO_UNGENERATED_FILE` reports.
- `config/createBuildManifest.py` / `include/make/a2c-common.mk` — the DB-derived
  generated-file manifest (`A2C_SC_GEN_FILES` / `A2C_SV_GEN_FILES`) and the
  `EXTRA_S{C,V}_GEN_FILES` user-extension seam (Section 3).
- `include/make/a2c-vl-build-entry.mk` — the whole-design Verilator build entry,
  built under `rundir/build/vl` (`A2C_VL_BUILD_DIR`).
- `address-migration` skill — the in-depth reference for the address-control
  manual-TODO kinds.
- `manage-build` skill — `make` targets (`db`, `gen`, `newmodule`, `clean`).
