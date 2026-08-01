# Plan: Three-Section Block-Module Header

Status: proposed (2026-07-25). Awaiting review before implementation.

## Goal

Give parameterized block-module (`.cppm`) authors two correctly-zoned,
user-editable slots in the module header:

- a **GMF slot** for shared non-modular `#include`s (`endOfTest.h`,
  module-hostile libraries), and
- a **preamble slot** for body-only module `import`s.

This resolves a whole class of C++20 module-attachment bugs (a non-modular
shared header included in the module *purview* attaches its declarations to the
block module and then clashes with textual includes of the same header
elsewhere), and it unblocks the debayer build + regression.

## Problem (why the slots are needed)

A C++20 module unit has three zones, each with a distinct rule. Every piece of
user-injectable content has exactly one legal home:

| Content | Zone | Rule | Attaches to |
| --- | --- | --- | --- |
| Non-modular shared `#include` (`endOfTest.h`, OpenCV) | **GMF** (before `export module`) | includes/preprocessor only | **global module** |
| `export module X;` | boundary | after all includes, before all imports | — |
| `import` (base, context, sibling, body-only) | **preamble** (after `export module`, before first non-import) | all imports grouped here | (imported) |
| `using namespace`, class, definitions | **purview** (after imports) | anything | **module X** |

Today the generated block-module header is a **single** generated region
containing `module;` + GMF `#include`s + `export module` + imports. The only
user-editable spot is the gap *after* it, which is in the **purview** — so a
user forced to add `#include "endOfTest.h"` there attaches `endOfTestState` to
the block module. Any plain TU that both `import`s that block and textually
includes `endOfTest.h` (e.g. the tb-config via a generated `External.h`) then
sees the same entity attached two ways → hard error
(`declaration '…' attached to named module '…' cannot be attached to other
modules`). The `using namespace` relocation already landed
([[plan-cppm-module-scaffold-sections]] follow-on) is the purview-zone piece of
this same picture; this plan adds the GMF and preamble slots.

## Design — the three sections

Target layout for a parameterized block `.cppm`:

```
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
<generated GMF #includes>
// GENERATED_CODE_END
// user #includes here                    <- seeded user slot (GMF; global module)
// GENERATED_CODE_BEGIN --template=moduleExport
export module <block>.block;
import <block>.base;
<generated imports: context, foreign-config, sibling instance-base>
// GENERATED_CODE_END
// user imports here                      <- seeded user slot (preamble)
// GENERATED_CODE_BEGIN --template=classDecl
using namespace <ctx>_ns; ...             <- already relocated here (non-reg-handler)
export template<typename Config>
SC_MODULE(<block>) ...
```

- `moduleScaffold` section: GMF only (`module;` + `#include`s), ends **before**
  `export module`.
- `moduleExport` section (new): `export module` + all `import`s. For
  **reg-handlers** (which render via `blockRegs`, not `classDecl`), the context
  `using namespace` lines ride at the **tail of `moduleExport`** — replacing the
  current `isRegHandler` exception in the single header (D3).
- `classDecl` section: unchanged (usings at head + class).
- The two `// user … here` comments are seeded as initial **user-region**
  content by the scaffold, so they persist and guide.

## Locked decisions

- **D1 — existing-file upgrade (testing-phase pragmatic).** In-tree files
  (debayer + the `builder` examples) are upgraded by a marker restructure; the
  end state must be byte-identical to a fresh scaffold. The user rescaffolds
  their own separate test project. Only `.cppm` (module) files are affected. The
  migrate tool does the mechanical restructure; the migrating agent relocates any
  stray `import` lines (see Migration mechanic).
- **D2 — a new `migrateModuleHeader` phase** in the `make migrate` pipeline,
  alongside `migrateIncludes` (Option 1). It does the marker restructure and
  reports a per-file TODO for the agent's import relocation. Idempotent (a file
  already in 3-section form is a no-op).
- **D3 — reg-handlers are 100% generated**, so nothing to preserve; they
  regenerate/rescaffold, with usings at the `moduleExport` tail.

## Migration mechanic (the tool/agent split)

The generator template change is a prerequisite: `moduleScaffold` starts
generating **GMF-only**, and `moduleExport` is a new section. With that in place:

**Tool (`migrateModuleHeader`, the basics):** for each module-form block
`.cppm`, insert the missing region — replace
`// GENERATED_CODE_BEGIN --template=classDecl` with
`[moduleExport BEGIN/END]` + `// user imports here` + the original `classDecl`
marker. On the next `gen`, the old single header region is refilled to GMF-only
and the export/imports populate `moduleExport`.

A neat consequence: the old user gap (between the old header and `classDecl`)
ends up **before** `moduleExport` — i.e. in the GMF zone — so an existing
`#include "endOfTest.h"` there lands in the GMF slot automatically.

**Agent (the judgment):** the only content needing a hand touch is any hand-added
**`import`** line left in that old gap (now in the GMF zone), which must move down
to the `// user imports here` slot — imports before `export module` are illegal.
The tool reports this as `TODO_MODULE_IMPORT` per affected file, mirroring
`TODO_USER_IMPORT` from the includes phase.

## Implementation phases (each verified before the next)

1. **Generator split** — `templates/systemc/moduleScaffold.py`
   (two render sections: GMF-only `blockModuleHeader` + new `moduleExport`),
   `templates/fileGen/fileGen.py` (dispatch the new section for block-module and
   reg-handler-module scaffolds; seed the two `// user … here` slot comments).
   Reg-handler usings move to the `moduleExport` tail. `classDecl` untouched.
2. **`migrateModuleHeader` phase** — `pysrc/migrateModuleHeader.py`, wired into
   `migrateYaml.py` next to `migrateIncludes`; the marker restructure +
   `TODO_MODULE_IMPORT` reporting. Update `rules/skills/migrate-project.md`
   (new phase, new TODO kind).
3. **Suite validation (atomic with 1–2)** — regenerate/migrate + build/run the
   base and pro example suite; run `unittest/run_all_tests.sh`, updating any
   golden/emit expectations that encode the old single-header layout (bucket-A,
   never weaken). Run the whole runner (do not kill it under a short timeout —
   [[reference_unit_suite_regen_flake]]).
4. **Debayer (out-of-tree)** — after the suite is green: migrate/rescaffold its 6
   block `.cppm`, confirm `endOfTest.h` sits in the GMF slot for
   `raw_video_src`/`rgb_video_sink`, relocate any stray gap imports, build, and
   run the regression (`run-regression-tests`).

## Blast radius (13 module-form block `.cppm`)

- Examples (7): `ip_test` (`ip`, `ipLeaf`, `src`), `mixed` (`blockF`, `blockG`,
  `blockGRegs`), `simple_ip` (`ip`).
- Debayer (6): `debayer`, `debayer_regs`, `interpolate`, `preprocess`,
  `raw_video_src`, `rgb_video_sink`.
- Reg-handlers: `debayer_regs`, `blockGRegs`.

## Risks

- **User-code loss in migration** — mitigated: the header region is fully
  generated; the tool only manipulates markers; everything below `classDecl` is
  untouched. The single judgment step (import relocation) is agent-driven and
  reported.
- **Golden/emit test churn** — expected; bucket-A expectation updates only.
- **Reg-handler correctness** — usings must sit after imports, before the class;
  covered by the `moduleExport`-tail placement.
- **Composition with in-flight work** — must be idempotent and compose with the
  in-progress debayer `.cpp/.h → .cppm` migration and the block-module promotion
  ([[project_block_module_cppm_promotion]]).

## Relationship to existing plans

- Extends [[plan-cppm-module-scaffold-sections]] (the block-module `.cppm`
  section model) and the committed using-namespace relocation (the purview-zone
  piece).
- Reuses the phase pattern from the includes migration
  ([[plan-migration-tool]] / `migrateIncludes.py`) and the `make migrate`
  pipeline ([[plan-yaml-migration]]).

## #116 Review Follow-Up — Item 5: Full Block-Implementation Module Conversion (Execution, 2026-07-29)

Item 5 of [[plan-116-review-feedback]] supersedes the original
"convert only parameterized designs" decision. The team now wants **every**
block implementation (`.cpp`/`.h` → single `.cppm` C++20 module) converted
uniformly, independent of parameterization. This section hardens that into an
execution plan. It shares the SINGLE `yamlFormat: 2` migration with Item 2
(nested variant schema) so users run `make migrate` once.

### Gating change site (the whole generator-side change)

The predicate that restricts `.cppm` promotion to parameterized blocks is the
`hasOwnParams` split between two mutually-exclusive fileMap entries in
`config/project.yaml`:

- `config/project.yaml:139` — `block`: `ext: {hdr: h, src: cpp}`,
  `cond: {hasMdl: true}`, `condAnd: {hasOwnParams: false}`, `mode: block` →
  the classic `.h`/`.cpp` pair (non-templated blocks).
- `config/project.yaml:140` — `blockModule`: `ext: {cppm: cppm}`,
  `cond: {hasOwnParams: true}`, `condAnd: {hasMdl: true}`, `mode: block` →
  the single `.cppm` module interface (templated blocks).

**Change:** relax `blockModule` to `cond: {hasMdl: true}` (drop the
`hasOwnParams: true` gate) and remove the `block` `.h`/`.cpp` entry so every
block with a model emits the single `.cppm`. This fileMap flip is essentially
the entire emission-side change, because the rendering machinery already
handles the non-parameterized module class:

- `templates/systemc/classDecl.py:91-95` already branches on `hasOwnParams`:
  `if hasOwnParams:` emits `export template<typename Config> SC_MODULE(...)`,
  the `else` emits a plain `export SC_MODULE(...)` — the untemplated module
  class path already exists.
- `block_hdr` (`templates/fileGen/fileGen.py:134`, scaffolds `--template=classDecl`
  + `--template=constructor`) and `blockModule_cppm`
  (`templates/fileGen/fileGen.py:169`, same two sections plus the
  `moduleScaffold --section=blockModuleHeader` / `moduleExport` header regions
  and the `--mode=module` PARAM flag) scaffold the **same** class/constructor
  sections. Promotion just re-routes a block from the first scaffold to the
  second.
- The `blockBase` `.cppm` already proves the base-module machinery renders both
  forms: a non-param base is emitted untemplated today
  (`examples/simple/base/producerBase.cppm`: `export class producerBase`) vs the
  templated `examples/ip_test/leaf/base/ipLeafBase.cppm`.

`hasOwnParams` is the block's own `params:` relationship (not a stored block-row
field); it is materialized for fileMap `cond` evaluation at
`pysrc/newModule.py:45` (`row['hasOwnParams'] = ... getBlockConfigView(...)['hasOwnParams']`)
and documented at `pysrc/migrateOrphans.py:272-273`.

**Reg-handler consequence:** removing the `block` entry also re-routes
non-param reg-handlers (today `block_hdr`→`blockRegs_hdr`) to
`blockRegsModule_cppm` (`fileGen.py:199`). This is consistent with the Blast
Radius list above, which already carries `debayer_regs` and `blockGRegs` as
module-form reg-handlers. Confirm no non-param reg-handler depends on the
`.h`/`.cpp` form before removing the entry.

### Migration mechanics (automated vs agent-driven)

**Automated — no orphan-sweep code change is required.** The legacy embedded
fileMap already carries the block entry as a port disposition with no param
split: `pysrc/migrateOrphans.py:107` — `block` → `cond: {hasMdl: True}`,
`migrate: MIGRATE_PORT`. The port detector
(`pysrc/migrateOrphans.py:501-508`) computes `portOldForm` (every block
`.h`/`.cpp`) minus `currentForm` (the current merged map). Today a non-param
block's `.h`/`.cpp` is still in `currentForm` (via the `block` entry), so no
`TODO_PORT` fires. **Once the gate flip makes the current map produce `.cppm`
for every block, the `.h`/`.cpp` fall out of `currentForm` and `TODO_PORT`
fires automatically for every non-parameterized block.** The gate flip alone
extends the sweep's per-block port reporting to the full block set; the sweep
never transforms or deletes a port file (`migrateOrphans.py:434-440`).

**Agent-driven — the per-block consolidation** (migrate-project skill §6). For
each `TODO_PORT`, the pipeline has already scaffolded `<block>.cppm` with empty
user slots (`make newmodule` + `make gen` run even while ports remain). The
agent transplants the user code from the legacy pair into the `.cppm` by marker
anchor, then `git rm`s the old `.h`/`.cpp` and re-runs `make gen`.

- **Item 5 simplification:** non-parameterized blocks **skip T2 (templatize)
  entirely** — there is no `template<typename Config>` head, no dependent-type
  qualification, no `this->`/`using typename` rewrite. The port is purely the
  mechanical **T1 region move** plus switching any `#include` of a *now-module*
  sibling to `import <sibling>.block;` (only where that sibling actually became
  a module — a still-`.h`/`.cpp` sibling keeps its `#include`). This is far
  lighter than the parameterized-block port.
- **Reg-handlers are regenerate-not-port:** a `<block>_regs` pair holds no user
  code — delete the legacy pair and let `make gen` recreate the `.cppm`; do not
  run the slot procedure.

### Region-preservation requirements

The legacy `.h`/`.cpp` and the scaffolded `.cppm` share identical
generated-section markers, so every user span sits between the same two markers
in both and transplants by anchor. `blockModule_cppm` provides **four** empty
user slots (`fileGen.py:179-187`), and **all four must move** — a missed slot is
silent user-code loss:

1. **Class body** — members after the `--template=classDecl` `GENERATED_CODE_END`
   and before the class-closing `};` (from `<block>.h`).
2. **Constructor init list** — between `--template=constructor --section=init`
   END and `--section=body` BEGIN (from `<block>.cpp`).
3. **Constructor body** — after `--section=body` `GENERATED_CODE_END` (from
   `<block>.cpp`).
4. **Out-of-line method definitions / trailing user code** below the constructor
   (from `<block>.cpp`).

The tool only manipulates markers and reports; every user span is preserved by
construction. The 3-section slots this plan adds (GMF `// user #includes here`,
preamble `// user imports here`) are where module-hostile includes
(`endOfTest.h`) and any relocated `import` lines land.

### Cross-example scope (the migration workload — largest surface)

Non-parameterized block-implementation `.h`/`.cpp` pairs to consolidate into a
single `.cppm`, per example (read-only survey, 2026-07-29). Blocks already in
module form (parameterized) are **excluded**.

| Example (base) | Non-param blocks to port | Count |
| --- | --- | --- |
| `apbDecode` | apbDecode, cpu, blockA, blockB, someRapper | 5 |
| `axi4sDemo` | axi4sDemo, axi4s_m_drv, axi4s_s_drv | 3 |
| `axiDemo` | axiDemo, consumer, producer | 3 |
| `helloWorld` | consumer, producer, helloWorld | 3 |
| `hierVlDemo` | axi4s_m_drv, axi4s_s_drv, hierVlDemo | 3 |
| `ip_test` | cpu(common), apbDecode+ip_top(top), ipStdDecode/Driver/Master/Top(ip), bridgeApbDecode/bridgeDriver/bridgeStdTop/ipBridge(bridge) | 11 |
| `mixed` | apbDecode, blockA, blockB, blockBRegs, blockC, blockD, blockGLeaf, cpu, mixed, threeCs | 10 |
| `nested` | consumer, firstBlock, lastBlock, nested, nestedL1–L6, producer, secondBlock, secondSubA, secondSubB, subBlock, subBlockContainer, testBlock, testContainer | 18 |
| `pySocket` | dut, pySocket, pySocket_tb | 3 |
| `simple` | simple, producer, consumer | 3 |
| `simple_ip` | simple_ip, dataGen, apbDecode, ipStdDecode/Driver/Master/Top(ip), cpu(common) | 8 |
| `xif` | — (dut, sink, src already module-form) | 0 |
| **Base subtotal** | | **70** |

| Example (pro) | Non-param blocks to port | Count |
| --- | --- | --- |
| `lmmiDemo` | lmmiDemo, lmmi_m_drv | 2 |

**Debayer product (out-of-tree, blast-radius):** `apb_decode`, `cpu` still
classic `.cpp`/`.h` (the other 6 — debayer, debayer_regs, interpolate,
preprocess, raw_video_src, rgb_video_sink — are already `.cppm`). = **2**.

**Total ≈ 74 blocks (~148 `.h`/`.cpp` files → ~74 `.cppm`).** Already
module-form and out of scope: `ip_test` ip/ipLeaf/src, `mixed`
blockF/blockG/blockGRegs, `simple_ip` ip, `xif` dut/sink/src, debayer's 6.
Stale duplicate orphans (e.g. `mixed/model/blockF.cpp`+`.h` sitting beside
`blockF.cppm`) are removed by the sweep's delete/orphan path, **not** ported.

### Coordination with Item 2's migration

- Item 2 adds a `migrateYaml.py` text phase (per-row variant → nested mapping).
  Item 5 adds **no new migrate phase** — its effect is entirely the one-time
  fileMap gate flip, picked up by the **existing** orphan-sweep `TODO_PORT`
  machinery. The gate flip must be committed at/before the migration so the
  sweep reports the ports.
- Both land in the SAME `yamlFormat: 2` migration; a user runs `make migrate`
  once and resolves item-2 schema rewrites (automated) and item-5 `TODO_PORT`
  block consolidations (agent-driven) in one pass. Item 6 (migration-guide
  clarification) documents this combined surface.

### Validation plan (base + pro suite, then debayer)

Per the "validate across all examples" and "subagent builds use `-j`" rules:

1. Land the `config/project.yaml` gate flip (drop `blockModule` `hasOwnParams`
   gate; remove the `block` `.h`/`.cpp` entry).
2. For each base + pro example: `make migrate` → resolve every `TODO_PORT`
   (agent-driven four-slot consolidation for normal blocks; delete +
   regenerate for reg-handlers) → `make clean && make gen -j && make run -j`;
   `make run-vl` where the example has verilated blocks.
3. `unittest/run_all_tests.sh` (do not kill under a short timeout); update
   bucket-A golden/emit expectations that encode the old `.h`/`.cpp` block form
   (never weaken). Retry regen/Verilator flakes once from clean before
   diagnosing.
4. Debayer last (out-of-tree): port `apb_decode` + `cpu`, build, run the
   regression.

### Risks / open uncertainties

- **User-code loss (largest risk):** ~74 blocks × four slots. The four-slot
  transplant must be complete; the reg-handler regenerate-not-port case must be
  distinguished from a real port (empty-member placeholder is the tell).
- **Latent untemplated-module path:** the `classDecl.py` untemplated branch is
  exercised today only in **header** mode; a plain non-param `SC_MODULE` in
  `--mode=module` (GMF/moduleExport slots, module attachment) is first exercised
  here. Needs a build proof on the first ported example before scaling out.
  *(Uncertainty — flagged.)*
- **Import/build-graph churn:** registrar/VlRegistrar TUs and any importer that
  `#include`s `<block>.h` must switch to `import <block>.block;`. Interacts
  directly with this plan's GMF/moduleExport slots (module-hostile includes).
- **Final fileMap form:** whether to delete the `block` entry outright vs
  neutralize it, and whether removing it forces every non-param reg-handler to
  module form cleanly, needs confirmation on the first mixed/reg-handler
  example. *(Uncertainty — flagged.)*
- **Count drift:** the ~74 figure may shift by a few as stale duplicate orphans
  (blockF-style) are classified as delete vs port during the actual sweep.
