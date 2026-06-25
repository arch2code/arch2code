# Design Document: Parameterized Types and Variants

- **Branch:** `feature/116-parameterized-types`
- **Scope:** the `debayer` project plus the `builder` and `builder/base` engine submodules
- **Status of record:** implementation committed in branch history; `plan-*.md` files under `builder/base/plans/` are the design record
- **Date:** 2026-06-24
- **Audience:** arch2code framework maintainers and users authoring hardware modules with the framework

This document describes how the arch2code generator behaves **now**, on this branch, and how that differs from the previous (`main`) behavior. The emphasis throughout is on **user contracts and observable behavior**. The internal mechanics are organized into three independent sections — **Parsing**, **View Creation**, and **Templates** — matching the generator's three-stage pipeline. Every claim below was verified against the source on branch `HEAD`; file and line citations are provided, and a consolidated list of plan-versus-code discrepancies appears at the end.

---

## 1. Executive Summary

### 1.1 The problem

Before this branch, an arch2code block was sized exactly once, at project-global scope. The width and depth knobs that shaped a block (for example `BITS_PER_PIXEL_COLOR`, `PIXELS_PER_CLOCK`) lived in a shared constants file, and a block had exactly one concrete instantiation in the design. Building the same IP at a second width required forking the YAML.

### 1.2 The capability delivered

This branch introduces **one IP block instantiated many times at different widths or variants, from a single source of truth**. The canonical fixture `builder/base/examples/ip_test/` instantiates the `ip` block twice in one design — `uIp0` at `variant0` (8-bit) and `uIp1` at `variant1` (70-bit) — both generated from one block definition.

### 1.3 The new mental model

Users must internalize three ideas:

- **Variants are Configs.** Each declared variant maps one-to-one to a C++ `Config` policy struct and to one SystemVerilog parameter set. A parameterizable block is emitted once as a `template<typename Config>` class (C++) or a `#(parameter ...)` module (SV); differently-sized instances coexist as distinct template instantiations or parameter bindings.
- **IP-local parameter ownership.** The parameters that size an IP belong to that IP's root YAML file, not to a shared global file. Shared include files are forbidden from declaring `ipParameters`.
- **Worst-case sizing.** Because addresses and memory depths are allocated once across all variants, every parameterizable knob carries a worst-case bound (`maxValue` for constants, `maxBitwidth` for types), and the generator sizes invariant artifacts from that worst case.

### 1.4 Headline breaking changes

- A project must declare `yamlFormat: 2` or the build hard-stops.
- The project-wide `addressControl.yaml` is replaced by per-block `addressBlock:` and `registerPorts:` declarations plus address policy in `project.yaml`.
- `eval:` expressions are now a frozen SystemVerilog-subset language, not Python.
- Generated per-context include files are C++20 module-interface units (`.cppm`), not `.h`/`.cpp`.
- A single migration command, `make migrate`, performs all of the above conversions.

### 1.5 Scale of the change

The engine submodule `builder/base` changed approximately 860 files (about 64,500 insertions); `processYaml.py` alone grew by roughly 3,400 net lines, and `migrateAddressControl.py` (613 lines) is new. The consuming `debayer` project changed 170 files.

---

## 2. Pipeline Architecture at a Glance

The generator runs as a strict two-phase pipeline, with a SQLite database as the only channel between phases (an enforced engine rule). The three subject areas of this document map onto that pipeline:

```
 YAML (user source)
     │
     ▼
 ┌──────────────────────────────────────────────────────────┐
 │ projectCreate  (Phase 1)                                   │
 │                                                            │
 │  [§4 PARSING]                                              │
 │   migration gate (yamlFormat: 2)                           │
 │   schema-driven row parsing                                │
 │   eval expression parse (evalExpr.py, Pratt parser)        │
 │   value resolution (valueResolver.py)                      │
 │   → persists tables + canonical expression strings         │
 └──────────────────────────────────────────────────────────┘
     │ SQLite database
     ▼
 ┌──────────────────────────────────────────────────────────┐
 │ projectOpen  (Phase 2)                                     │
 │                                                            │
 │  [§5 VIEW CREATION]                                        │
 │   getBlockData / getContextData                            │
 │   per-block / per-context / per-variant projections        │
 │   config views, address-block view, thunker view,          │
 │   canonical eval view                                       │
 └──────────────────────────────────────────────────────────┘
     │ language-neutral views
     ▼
 ┌──────────────────────────────────────────────────────────┐
 │  [§6 TEMPLATES]                                            │
 │   templates/systemc/*.py   → C++ / SystemC                 │
 │   templates/systemVerilog/*.py → SV / RTL                  │
 │   select fields, apply language spelling, emit text        │
 └──────────────────────────────────────────────────────────┘
```

The ownership contract (engine `CLAUDE.md`): durable project truth is computed once in `projectCreate`; `projectOpen` view helpers perform only language-neutral reshaping of persisted truths; template utilities format already-supplied fields and never re-derive cross-object facts. The migration tooling sits beside this pipeline: it rewrites legacy YAML as text and never opens the database.

---

## 3. User Contracts and Behaviors

This section is the user-facing synthesis. It states what a person using arch2code must now write and do differently. The internal mechanics that implement each contract are cross-referenced to the later sections.

### 3.1 YAML authoring contract

#### `yamlFormat: 2` sentinel

Every `project.yaml` must declare `yamlFormat: 2` as a top-level field, or the generator hard-stops before parsing any YAML (`pysrc/processYaml.py:25`, `CURRENT_YAML_FORMAT = 2`; gate at `:4012`). Verified present at `arch/yaml/project.yaml:1` and `builder/base/examples/ip_test/arch/yaml/project.yaml:3`.

#### eval expressions: SystemVerilog subset, not Python

`eval:` strings are parsed by a frozen SystemVerilog constant-expression subset. The debayer migration shows the before-and-after directly:

```yaml
# before (Python)                                  after (SV subset)
VERTICAL_SIZE_LOG2: {eval: "($VERTICAL_SIZE-1).bit_length()"}  → {eval: "$clog2($VERTICAL_SIZE)"}
DEBAYER_OFFSET:     {eval: "($DEBAYER_DIMENSION - 1) // 2"}     → {eval: "($DEBAYER_DIMENSION - 1) / 2"}
ENTRIES_PER_LINE:   {eval: "$HORIZONTAL_SIZE // $PIXELS_PER_CLOCK"} → {eval: "$HORIZONTAL_SIZE / $PIXELS_PER_CLOCK"}
```

The rules: `.bit_length()` becomes `$clog2(...)`, floor division `//` becomes `/`. Already-SV expressions such as `(1 << $BITS_PER_PIXEL_COLOR) - 1` are unchanged. Real-valued evals (`/ 2.0`), `**`, comparisons, and ternary are out of grammar and must be hand-converted to literal `value:` entries. See §4.2 for the grammar and §4.3 for the converter.

#### Parameterizable types and `ipParameters`

`ipParameters:` is for the block's **root parameter constants** — the variant knobs named in `params:` and bound per variant. These **must live in the IP-root YAML file** (the same file as the block's `params:` endpoint), because that is how the generator identifies them as the variant-bound parameters. Each carries a required worst-case `maxValue` (`builder/base/examples/ip_test/arch/yaml/ip/ip.yaml:11`):

```yaml
ipParameters:
    constants:
        IP_DATA_WIDTH: { value: 70, maxValue: 128, desc: "Per-instance data width" }
        IP_MEM_DEPTH:  { value: 16, maxValue: 32,  desc: "Per-instance memory depth" }

types:                                          # regular section — the conventional home
    ipDataT: { width: IP_DATA_WIDTH, maxBitwidth: 128, desc: "IP data word, parameterizable" }
```

**Parameterizable types and derived constants should not normally be placed in `ipParameters`.** Parameterizability propagates from the referenced root parameter, so a type whose width is a parameter (such as `ipDataT` or a `pixel_t`) and a derived constant that references a parameter generate identically whether they sit in `ipParameters.types`/`ipParameters.constants` or in the regular `types:`/`constants:` sections. The convention — and what `design-parameterizable-blocks.md:37` recommends — is to keep them in the regular sections and let `ipParameters` hold only the root parameter constants. Such types and derived constants still require a worst-case bound (`maxBitwidth` on a literal-width type; `maxValue` auto-derived on a referencing constant) wherever they are declared.

> The `ip_test` fixture (`ip.yaml`) does place `ipDataT` under `ipParameters.types` to exercise the schema's *allowance* of that form. It is permitted, not the recommended norm.

#### Block `params:` and per-variant `parameters:` bindings

A block names the parameters it is sized by; values are bound per variant; an instance selects a variant:

```yaml
blocks:
  ip:
    params: [IP_DATA_WIDTH, IP_MEM_DEPTH, IP_NONCONST_DEPTH]
parameters:                                   # in ipVariants.yaml
  ip:
    - { variant: variant0, param: IP_DATA_WIDTH, value: 8 }
    - { variant: variant1, param: IP_DATA_WIDTH, value: 70 }
instances:                                    # in ip_top.yaml
  uIp0: { instanceType: ip, variant: variant0 }
  uIp1: { instanceType: ip, variant: variant1 }
```

Variant-binding identity is keyed by `(block, variant, param)`: two different blocks may both declare a parameter named `WIDTH` without collision. See §5.3.

#### `addressBlock:` / `registerPorts:` per-block schema

Address decode is declared on the blocks themselves, not in a project-wide file. A **router** block declares `addressBlock:`; a reusable-IP **leaf** declares `registerPorts:`; the two are mutually exclusive on a single block:

```yaml
blocks:
  apbDecode:                       # a router
    addressBlock:
      addressGroup: top
      addressIncrement: 0x01000000
      maxAddressSpaces: 16
      varType: addr_id_top
      enumPrefix: ADDR_ID_TOP_
      upstreamPort: apbReg
      registerDecoderPort: apbReg
  ip:                              # a reusable IP leaf
    registerPorts:
      regs: { interface: ipReg }
```

Project-wide address *policy* moves to top-level sections of `project.yaml`:

```yaml
instanceGroups:
    top: { varType: inst_top, enumPrefix: INST_TOP_ }
addressObjects:
    memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }
```

See §5.4 for how these declarations become decode and routing views.

#### Includes become C++20 modules

Generated per-context include files changed extension from `.h`/`.cpp` to `.cppm` module-interface units. Hand-written consumers must change `#include "<ctx>Includes.h"` to `import <module>;`. See §6.1 (SystemC templates).

### 3.2 Build and CLI contract

- **`make migrate`** — the single command that brings an existing project to `yamlFormat: 2`. It wraps `migrateYaml.py --write` (`builder/base/include/make/a2c-common.mk:135-136`) and is standalone: it rewrites YAML as text and never opens the database, because a pre-migration project cannot pass the gate.
- **`make gen` / `make db`** — unchanged entry points, but both now fire the `yamlFormat` hard-stop gate first.
- **`make newmodule`** — the scaffolding pass that creates skeleton implementation files for blocks (it runs `arch2code.py --newmodule`). It is **create-only**: it writes only files that do not yet exist and never overwrites or deletes — rewriting the `GENERATED_CODE` regions of existing files is `make gen`'s job. This create-only property is not new on this branch; it is called out here because the migration relies on it. After migration, recreating the new `.cppm` module-interface files is `make newmodule` (create the skeleton) followed by `make gen` (fill the generated regions). The branch did extend `newmodule` internally — it added `condAnd` file-map conditions and seeds a single-emission parameterizable testbench skeleton with the block's first declared variant (`pysrc/newModule.py`) — but neither change alters the create-only contract.
- **Never run `python arch2code.py` directly** — always use `make` targets. The migration tool is the sanctioned exception, invoked via `make migrate`.
- The standalone template-config files `config/cppConfig.yaml`, `config/svConfig.yaml`, and `config/docConfig.yaml` were **deleted**; the `templates:` map is now unified into `builder/base/config/project.yaml`. Projects that copied those files must remove them.

The gate's remediation message (`pysrc/processYaml.py:4026-4033`):

```
Project '<...>' is not migrated to yamlFormat: 2.
       Run the migration, then rebuild:
           make migrate
           make clean && make gen
```

### 3.3 Migration story

`migrateYaml.py` runs ordered, idempotent phases over the project's full YAML file set. The default invocation is a **dry-run** that prints a full report and changes nothing; `--write` (what `make migrate` passes) applies edits.

1. **Includes phase** — header-mode context includes migrate to `.cppm` modules; orphaned generated `<context>Includes.{h,cpp}` files (those carrying `GENERATED_CODE_BEGIN`) are deleted. This phase runs first on every invocation, even before the stamp short-circuit. User-code import rewrites are flagged `TODO_USER_IMPORT`.
2. **Phase A — eval Python to SV** — `CONVERTED` rows are rewritten in place; `NEEDS_MANUAL` rows (real-valued evals and similar) are reported, never rewritten, and block the stamp.
3. **Phase B — `addressControl` to per-block schema** — each live router becomes an `addressBlock:`; `instanceGroups:`/`addressObjects:` move to `project.yaml`; the `addressControl:` pointer is removed; `postProcess:` is normalized (`postParseRegister.py` to `postParseRegisterPorts.py`). Unresolvable items are flagged `TODO_INTERFACE_SCOPE`, `TODO_LEAF_REGISTER_PORTS`, or `TODO_ROUTER_RESOLUTION`.
4. **Phase C — stamp `yamlFormat: 2`** — written **only when** Phases A, B, and the includes phase leave no manual work. A project is never left partially stamped; a `--write` run that cannot stamp returns non-zero, so `make migrate` keeps failing until the project is genuinely clean.

**Step-by-step:** `make migrate` → read the report → resolve any `NEEDS_MANUAL`/`TODO_*` items → re-run `make migrate` until it stamps → `make clean && make gen`.

**Irreversibility.** The legacy paths are removed, not deprecated: the `addressControl.yaml` loader, `validateAddressControl`, and `config/postParseRegister.py` are deleted; Python-syntax eval acceptance is gone. Once a project is stamped and its legacy files are deleted, it builds only under format 2. New projects scaffold with the sentinel automatically.

### 3.4 Visible generated-artifact changes

- **`<context>VariantConfig.h`** — a **new** generated per-context Config-policy header. No per-context Config header existed on `main`; this artifact is introduced by the branch. During the branch's own development it was first named `<context>Config.h` and then renamed to `<context>VariantConfig.h` to avoid colliding with the testbench-generated `<block>Config.cpp`; that rename was an intra-branch change, not a rename of anything that shipped on `main`. (The only `*_config.h` files on `main` are the unrelated pre-existing snake_case `raw_video_src_config.h` / `rgb_video_sink_config.h`.)
- **Per-variant Config structs** — one `struct` of `static constexpr` members per variant in that header; the anonymous/default variant is `<block>DefaultConfig`.
- **Deleted include artifacts** — the SystemC `model/*Includes.{h,cpp}` are deleted and replaced by `.cppm` modules.
- **Variant-aware testbench selection** — standalone testbench artifacts carry a file-level directive `// GENERATED_CODE_PARAM --block=ip --variant=variant0`. `--variant=` chooses an existing Config/factory key; it is not a runtime knob and does not fan out files (one `<block>Testbench.*` regardless of variant count). The default is the **first variant in declaration order**.
- **Per-variant Verilated SV wrappers** — the monolithic `<block>_hdl_sv_wrapper.sv` is replaced by a canonical include body (`.svh`) plus tiny per-variant `.sv` trampolines.

> **Clarification on RTL packages.** The SystemVerilog packages `rtl/debayer_package.sv` and `rtl/isp_types_package.sv` were **not deleted** — both exist at branch `HEAD` (verified via `git ls-tree`). Their *parameterizable contents* were relocated into module scope; the packages now carry only non-parameterizable items. See §6.2.6.

### 3.5 Skills and documentation contract

The repo-root `AGENTS.md` was rewritten into a skill-routing table that `CLAUDE.md` and `GEMINI.md` now symlink to, with the mandatory rule: "Before editing, you must load the project skill that matches the task." The user-facing skills most relevant to this branch:

| Skill (`builder/base/rules/skills/`) | Governs |
| :-- | :-- |
| `migrate-project.md` | The end-to-end `make migrate` workflow and resolving manual TODOs |
| `address-migration.md` | Phase B reference: `addressControl.yaml` → per-block `addressBlock:`/`registerPorts:` |
| `design-register-decode.md` | Greenfield decode hierarchy: router vs routed leaf, decode decision rule |
| `manage-address-space.md` | `project.yaml` address policy and FW-header generation |
| `manage-build.md` | `make` targets, `newmodule`, the no-direct-python rule |
| `run-tandem.md` (pro) | Tandem verification for leaf blocks |

### 3.6 Breaking changes and back-compatibility summary

| Area | Before | After (this branch) | Back-compat |
| :-- | :-- | :-- | :-- |
| Project format | implicit (format 1) | `yamlFormat: 2` required | None — hard-stop gate; run `make migrate` |
| Address control | project-wide `addressControl.yaml` | per-block `addressBlock:`/`registerPorts:` + `project.yaml` policy | None — loader and validator deleted |
| `postParseRegister.py` | user `postProcess:` entry | `postParseRegisterPorts.py`, defaulted by base config | drop user override |
| `eval:` syntax | Python (`.bit_length()`, `//`, `/2.0`) | SV subset (`$clog2`, `/`) | auto-converted except real/`**`/comparison |
| Generated includes | `<ctx>Includes.{h,cpp}` | `<ctx>Includes.cppm` (C++20 module) | consumers: `#include` → `import` |
| Config header | (none existed) | new `<ctx>VariantConfig.h` per-context Config-policy header | None — purely additive; no user action |
| Template-config files | `config/{cpp,sv,doc}Config.yaml` | unified into `project.yaml` | delete copies |
| IP parameter location | shared constants file | `ipParameters` in IP-root file only | move params |
| Division semantics (eval) | Python floor `//` | SV/C++ truncate-toward-zero `/` | differs for negative operands only |

---

## 4. Parsing

### 4.1 Overview

Parsing is a `projectCreate`-time front end that turns user YAML into the SQLite database. The layers, in order:

1. **Migration gate.** `projectCreate` calls `_gateYamlFormat()` first (`pysrc/processYaml.py:4012`). A project must carry `yamlFormat: 2` or the build hard-stops before any YAML is parsed.
2. **Schema-driven row parsing.** Each YAML file is walked against `config/schema.yaml` (loaded by `pysrc/schema.py`). Field types (`const`, `param`, `eval`, `auto`, foreign-key validators) drive ingestion.
3. **Expression parsing.** For `eval` fields, the value string is parsed once into a language-neutral IR by `pysrc/evalExpr.py`, with bare `$symbols` resolved to qualified keys through `ValueResolver` (`pysrc/valueResolver.py`).
4. **Value resolution.** `ValueResolver` resolves symbol references to integers against context-keyed parse-time data and the qualified flat index, honoring per-instance overrides.
5. **Persistence.** The canonical serialization is stored in `constants.evalCanonical`; numeric results (`value`, `maxValue`) are stored as ordinary columns. `projectOpen` re-exposes these without re-parsing or re-evaluating.

### 4.2 Expression parser and evaluator (`evalExpr.py`)

`evalExpr.py` is a standalone, project-neutral module owning the tokenizer, an in-house precedence-climbing (Pratt) parser, the IR node classes, the numeric evaluator, and the canonical serializer (`evalExpr.py:1-20`). It knows nothing about `ValueResolver` or project data — symbol qualification and value lookup are injected as callbacks.

**What an eval expression is.** In YAML a constant's `value:` field is an `eval` field (`config/schema.yaml:73`). The user may write a literal value or `eval: "<expr>"`. The expression language is a **frozen integer SystemVerilog constant-expression subset**, not Python.

**IR nodes** (frozen dataclasses, `evalExpr.py:32-60`): `Num(value, base)`, `Sym(key)`, `Unary(op, operand)`, `Bin(op, lhs, rhs)`, `Clog2(operand)`.

**Grammar and literals.**
- Unsized decimal (`255`, `4_095`) and SV based literals: `8'hFF`, `'hFF`, `'b1010`, `12'd4095`, signed `'shFF`, with `_` separators (`evalExpr.py:183-246`).
- Octal is normalized to base-16 at parse time (`evalExpr.py:244`), since C has no clean octal spelling.
- The authored radix is recorded on `Num.base` (10/16/2) for re-spelling; the authored bit-width is discarded (the IR models unbounded integers).
- **Rejected at parse:** real literals and scientific notation (`evalExpr.py:205-206`), C-style `0x`/`0o`/`0b` prefixes (`:202-204`), `x`/`z`/`?` digits (`:233-234`), and bare `<`/`>` (only `<<`/`>>` are valid; `:124-135`).

**Operators and precedence** (`evalExpr.py:76-83`; unary `{+, -, ~}`). Higher binds tighter, all binary operators left-associative:

```
|:1   ^:2   &:3   <<,>>:4   +,-:5   *,/,%:6
```

`$clog2(...)` is the sole function. Excluded by design: `**`, `~^`/`^~`, arithmetic shifts, ternary, relational/logical, `$bits` — so every retained operator has a one-to-one SV and C++ spelling.

**Symbol forms** (`evalExpr.py:331-346`):
- `$NAME` — bare; the parser calls `qualify(NAME)` to obtain the `name/context` key, folding unresolved-symbol validation into parsing.
- `${name/context}` — already-qualified; parsed straight to `Sym(key)`. This is the canonical/reload form (needed because `/` is the division operator, so qualified keys are wrapped in `${...}`).

**The Pratt parser** (`evalExpr.py:249-328`): `_expr(minPrec)` does precedence climbing — it parses a unary atom, then while the next operator's precedence is at least `minPrec` it consumes the operator and recurses at `PRECEDENCE[op] + 1` to enforce left-associativity. Parentheses are consumed and discarded; grouping survives only as tree shape.

**Canonical serialization** (`unparse`, `evalExpr.py:378-405`): symbols become `${key}`, literals are emitted in unsized SV based form per authored radix, operators single-space-padded, parentheses re-inserted from precedence. The invariant `parse(unparse(node)) == node` holds.

**Evaluation** (`evaluate(node, resolve)`, `evalExpr.py:438-493`) follows SV/C++ integer semantics, not Python:
- `/` truncates toward zero (`_truncDiv`, `:430-435`), not Python floor `//`.
- `%` follows the truncated quotient.
- divide/modulo-by-zero, negative shift counts, and `$clog2` of values ≤ 0 all raise `EvalEvalError`.
- `Num.base` is presentation-only and ignored in evaluation.

`symbolKeys(node)` (`:408-422`) returns the set of referenced qualified keys for parameterizable-dependency detection without evaluating.

**Integration in `processYaml.py`** — parse once, evaluate up to twice:
- Parse at ingestion (`:5040-5042`). `EvalParseError` becomes a user diagnostic; the field defaults to 0 to avoid cascades.
- **Active value** (`:5049-5052`) via `evaluate(node, resolve=value)`.
- `unparse(node)` persisted to `evalCanonical` (`:5062`).
- **Worst-case maxValue** (`:5202-5227`): if any referenced symbol is parameterizable, the constant is "derived-parameterizable" and the same tree is re-evaluated with `resolve=maxValue`.

This single eval path replaces the older regex-substitute-then-Python-`eval()` mechanism, removing the arbitrary-code-execution surface.

### 4.3 Python-to-SV expression migration (`evalPyToSv.py`)

**Why.** Legacy `eval:` strings were authored in Python and do not parse under the frozen SV grammar (`evalPyToSv.py:1-22`).

**What it converts** (`convertExpr`, `:68-112`), three outcomes:
- `ALREADY_SV` — input already parses under `evalExpr.parse` (the skip gate; makes it idempotent and minimal-diff).
- `CONVERTED` — two rewrites only: `($X - 1).bit_length()` → `$clog2($X)`; general `e.bit_length()` → `$clog2(e + 1)`; and floor `//` → `/`.
- `NEEDS_MANUAL` — out-of-grammar constructs (real literals, `**`, non-`bit_length` calls, booleans), left untouched with a reason.

**How.** The front end is Python's own `ast`: `$` is placeheld to `_` (both width 1, so column offsets are preserved), then targeted text-replace spans are applied right-to-left so spacing, parens, and comments stay byte-identical. A self-check re-parses the output through `evalExpr.parse`; failure is internal and never written.

**Where invoked.** This is Phase A of the unified migration (`migrateYaml.py:111-112`). The standalone `migrateEvalExpr.py` CLI from the original plan was superseded and never built.

### 4.4 Schema changes (`schema.py` / `config/schema.yaml`)

- **`flat` attribute** (`schema.py:105`, set at `:518-519`, exported at `:1240`): a `flat` section gets a `flatData[section][qualifiedKey]` index maintained during parse, distinct from the scoped store. `constants` is now `flat` (`schema.yaml:70`), which underpins the eval pipeline's qualified lookup.
- **`evalCanonical` field on `constants`** (`schema.yaml:72`): stores `unparse(node)` for eval rows, empty otherwise. Generator-owned, not user-authored.
- **`value: eval`** (`schema.yaml:73`) triggers expression parsing. **`maxValue: optional(0)`** and **`isParameterizable: optional(false)`** (`:75-76`) form the parameterizable-constant contract: an `ipParameters` constant must carry a positive `maxValue`; a derived eval constant must not carry a hand-written `maxValue`.
- **Foreign-key invariants** enforced at schema load (`schema.py:652-746`): plain-FK targets must be `flat` and name the storage key; combo-FK source/target combos must match component-wise; every `flat` section must have a populated qualified storage key. These make lookup total functions.
- **`addressBlock:` / `registerPorts:`** are the per-block address-control fields that replaced project-wide `addressControl.yaml`, produced by migration and consumed by the post-parse register-decode passes.

### 4.5 Value resolution (`valueResolver.py`)

`ValueResolver` is a parse-time helper bound to a file context (`valueResolver.py:7-10`), created per-file (`processYaml.py:4750`) and nulled at the end of each parse phase.

- **Constants and enums.** `lookupNamedRow(key, label)` (`:31-44`) dereferences an already-qualified key in `flatData['constants']`, falling back to `qualEnums`. `lookupVisibleRow` (`:46-78`) resolves a bare name by walking the include chain (`global` searches all contexts).
- **Qualified overrides / flat lookup.** `qualifyKey(ref, context, fatal)` (`:169-215`) qualifies foreign-key columns and eval symbols: numeric values return `''` (literals carry no symbol); bare names resolve to `name/context`; unknowns hard-fail or return `None`.
- **Active versus max resolution.** `value(ref)` → `_resolveActiveValue` (`:109-161`) honors per-instance variant overrides. `maxValue(key)` → `_resolveMaxValue` (`:149-167`) returns a parameterizable referent's worst-case bound. Width and struct helpers each choose active or max via a `use_max` flag.

### 4.6 Migration tooling (`yamlFormat: 2`)

`make migrate` wraps `migrateYaml.py --write` (`include/make/a2c-common.mk:135-136`). `migrateYaml.py` never opens the database — it reads and rewrites YAML as text only. The three ordered phases (includes, eval Python→SV, addressControl→per-block) and the conditional stamp (Phase C) are described from the user's perspective in §3.3. The hard-stop gate (`_gateYamlFormat`, `processYaml.py:4012-4040`) prints distinct messages for an un-migrated project versus a version mismatch, both exiting non-zero.

### 4.7 Verification

| Behavior | Test |
| --- | --- |
| Tokenizer/parser: literals, bases, symbol forms, precedence, associativity, unary, parens, `$clog2`, rejections | `unittest/test_eval_expr_parser.py` |
| `unparse` canonical form and round-trip; `symbolKeys` | `test_eval_expr_parser.py` |
| Evaluator: operator values, truncating division/modulo, by-zero, negative shift, non-positive `$clog2` | `unittest/test_eval_expr_evaluator.py` |
| Python→SV conversion rules, numeric equivalence, idempotency | `unittest/test_eval_py_to_sv.py` |
| `evalCanonical` persisted and surfaced without re-evaluation | `unittest/test_eval_canonical_view.py` |
| Block-param ↔ ipParameters linkage, name-collision rejection, variant binding exceeding `maxValue` | `unittest/test_param_const_linkage.py` |
| Parameterizable-constant negative cases | `unittest/test_error_parameterizable.py` |
| `yamlFormat` gate (absent / mismatch / present) | `unittest/test_gate_yaml_format.py` |
| Migration orchestrator (clean→stamp, blocked, dry-run, short-circuit) | `unittest/test_migrate_yaml.py` |
| Address-control migration (`addressBlock:` emission, policy move, TODOs) | `unittest/test_migrate_address_control.py` |
| Includes migration (override removal, orphan deletion, user-import TODO) | `unittest/test_migrate_includes.py` |

---

## 5. View Creation

### 5.1 Overview

After parsing, `projectOpen` exposes **views** — language-neutral projections of the persisted database assembled on demand for one rendering context (a block, or a YAML context), shaped so a template can iterate and emit text without re-walking `prj.data` across blocks, instances, and connections. The two top-level entry points:

- `getBlockData(qualBlock, ...)` (`processYaml.py:1056`) — the per-block view; a pipeline of `getBD*` sub-builders, each attaching one facet (instances, registers/memories, address decode, connections, ports, includes, config info, parameterized declarations, address-block view).
- `getContextData(contexts, dataTypeMapping)` (`processYaml.py:875`) — the per-context view consumed by the constants/types/enums and Config-header emitters.

Every view function named below is **new on this branch** — `git show main:pysrc/processYaml.py` contains none of them.

### 5.2 Config views

**`getBlockConfigView(qualBlock)`** (`processYaml.py:1155`) is a memoized per-block bundle of four fields read from the persisted block row: `isParameterizable`, `hasOwnParams`, `defaultConfig`, `variantConfigs`. It is an internal helper; templates consume the equivalent fields surfaced on the block/context views.

**`_buildVariantConfigDescriptors(qualBlock, ...)`** (`:1262`) is where parameterized types resolve to concrete per-variant values:
- The variant set derives from `data['instances']` (`:1301-1307`) — only **instance-bound** variants get a Config; an uninstantiated parameterizable block produces no Config.
- The Config struct's fields are the parameterizable constants of the block's canonical config context (`config_context = block_row['configContext']`).
- **Eval re-resolution under variant overrides is deferred** (`:1336-1338`): eval-derived constants keep their default-resolved value in the descriptor; the symbolic emission (§6.1.2) recomputes them per Config struct.
- **Intra-block dedup**: variants whose resolved value signature is byte-identical fold onto one canonical struct via `duplicateOf` (`:1392-1410`). The context-default `<context>DefaultConfig` is seeded as canonical so all-default bindings collapse onto the shared default, keeping direct cross-block channel binds well-typed.

**`getContextConfigView(contexts)`** (`:1009`) is a single-pass context-level view returning `variantConfigs` (aggregated per-block descriptors) and `blockParamSynthetic` (the member-type contract for block params with no backing parameterizable constant). The `context`-prefixed result names (`contextVariantConfigs`, `contextBlockParamSynthetic`) avoid shadowing during SV generation's view merge.

**`_resolveInstanceConfigFields`** (`:1181`) resolves per-instance Config typing for children, returning `configName`, `configArg` (the `<X>` template suffix), and flags. A documented limitation (`:1190-1195`): a Config-strict link from a multi-variant parent to a parameterized child is unsupported — use a single-variant child, a Config-agnostic interface, or a thunker bind.

### 5.3 Variant resolution and block-param identity

A *variant* is a named (or anonymous) binding of a parameterizable block's params to concrete values. Resolution: instances declare `variant:`; `parameters:` rows bind `(variant, param) → value`; the view layer reads these via `getQualBlockVariants` and `_buildVariantConfigDescriptors`.

**Block-param identity** is the contract that the same bare param name on two different blocks resolves independently. `parametersvariants` rows carry a `blockParamKey` foreign key to the specific block's `blocksparams` row. `test_parameter_variant_block_param_identity.py` locks this: two blocks each declare `WIDTH`; the target block's variant row resolves to the target's param key, never the sibling's. Parameterizable types resolve symbolically at the HDL boundary, not to a fixed integer in the view.

### 5.4 Address-block view

This is the largest user-facing change. On `main`, decode views were built by reading the project-wide `addressControl.yaml` blob. On this branch that table is dissolved into per-block declarations (Stage 8 retired the legacy path; the new schema is the only accepted input).

- **`getBDAddressDecode(ret)`** (`:1640`) determines router-ness purely from the block's own `addressBlock:` field — `isApbRouter` is `True` only when the block authors `addressBlock:`. It surfaces `addressGroupData`, `addressGroup`, `containerBlock`, and `instanceWithRegApb`.
- **`getBDAddressBlockView(ret)`** (`:2416`) is deliberately tiny: for a router it copies `blockRow['addressBlock']`; non-routers get nothing.
- **`getBDAddressBus(ret)`** (`:2428`) populates `registerBusInterface`, `registerBusPort`, and `registerBusStructs` for any router or decoder.
- **`_registerBusInterfacePort(ret)`** (`:2341`) is the unified resolver and embodies the central principle: `registerPorts:` is a **parse-time construct that projectOpen never reads**. Three resolved-design paths: router (port from `addressBlock['upstreamPort']`), synthesized handler (reads the leaf-to-handler `connectionMap`), and routed leaf (reads the same map, filtered to `addressBus: true`).

`test_addrctl_ip_test_view.py` confirms routers `apbDecode`/`bridgeApbDecode` resolve `registerBusInterface == 'apbReg'`, the leaf `ip` is not a router and resolves its own scoped `ipReg` on port `regs`, and a primary router serves both direct leaves and a nested router subtree.

**Internal note.** The `addressControl`/`AddressGroups` symbols still exist inside `projectCreate` for address-counter allocation and the `ADDRESS_CONFIG` blob, but they are now **synthesized internally** from per-block `addressBlock:` declarations plus `project.yaml` policy — not read from a user `addressControl.yaml`.

### 5.5 Thunker view

`buildThunkerView` (`:2004`, a closure inside `getBDCrossInterfaceBinds`) builds a language-neutral description of the per-protocol *thunker* that bridges a **cross-interface bind** — a connection whose parent interface differs from the child block's bottom-up declared port interface (including different per-variant Config types on each side).

- It is driven by `interface_defs`: it reads the protocol's `sc_channel.type` and the `parameters` whose `datatype == 'struct'`. **A protocol with no struct parameters produces no thunker** (`:2021-2022`).
- It emits `payloads` for both parent and child sides, ordered by side then declared parameter order.

It is produced inside `getBDCrossInterfaceBinds(ret)` (`:1914`), which walks connections, connection ports, and connection maps. `test_thunker_view.py` locks payload order and channel type per protocol (`rdy_vld`, `req_ack`, `push_ack`, `apb`) and confirms `notify_ack` (no struct params) produces no cross-interface ends.

### 5.6 Canonical eval view

The canonical eval view is the contract that an eval-derived constant's expression reaches generators as a **persisted canonical string**, with no parsing or numeric evaluation at open/view time. `projectCreate` persists `evalExpr.unparse(node)` into `constants.evalCanonical`; the canonical form uses fully-qualified `${name/context}` symbols, so it is context-independent on reload. `test_eval_canonical_view.py` runs the real `ip_test` pipeline with `evalExpr.parse`/`evaluate` replaced by traps and asserts the context view surfaces `IP_DATA_WIDTH_X2`'s canonical `${IP_DATA_WIDTH/ip/ip.yaml} * 2` and value `140` verbatim — failing if any parse/evaluate fires at open.

### 5.7 Cross-interface register check and boundary signals

The cross-interface compatibility gate is `validatePorts` (`:4485`) in `projectCreate` — it writes nothing back. It requires same `interfaceType`, same `structures` paired by `structureType`, and exact per-field `_bitWidth`/offset under the bound variant. Synthesized binds (`_context == '_global'`) are exempt.

The load-bearing branch (resolved 2026-06-12): `registerPorts:` is part of the declared-port surface, so the check consults the **union `ports: ∪ registerPorts:`** (`:4579-4583`). `test_register_ports_independent_of_ports.py` locks the independence: a leaf may declare a partial `ports:` map plus a `registerPorts:`, and the partial-`ports:` completeness check skips the register-bus port. `test_boundary_signals.py` confirms the view supplies symbolic widths for parameterizable payloads and fixed widths for the register bus, so the HDL/Verilated boundary matches the resolved struct width.

### 5.8 Verification

| Behavior | Test |
| --- | --- |
| Canonical eval string reaches context view, no open-time eval | `test_eval_canonical_view.py` |
| Thunker payload order / channel type; no thunker for struct-less protocol | `test_thunker_view.py` |
| Block parameterization inheritance | `test_block_config_parameterization.py` |
| Config struct emission (maxValue width selection) | `test_config_template.py` |
| HDL boundary symbolic vs fixed widths | `test_boundary_signals.py` |
| `registerPorts:` independent of partial `ports:` | `test_register_ports_independent_of_ports.py` |
| Block-param identity across same-named params | `test_parameter_variant_block_param_identity.py` |
| Migrated `ip_test` decode views; parameterized nested router | `test_addrctl_ip_test_view.py`, `test_addrctl_parameterized_router.py` |
| Topology matrix (routers, leaves, multi-level, fanout, top-down inference) | ~25 `test_addrctl_*.py` |

---

## 6. Templates

Templates are the emission stage. A template's `render(args, prj, data)` returns text for a single `GENERATED_CODE_BEGIN ... END` region; views supply all derived facts, and templates select fields and apply language spelling only.

### 6.1 SystemC templates

#### 6.1.1 Overview and template-to-file mapping

| Template module (`builder/base/templates/systemc/`) | Emits | Per |
| --- | --- | --- |
| `config.py` | `<context>VariantConfig.h` Config structs | context |
| `includes.py` | `<ctx>Includes.cppm` / FW header constants, types, enums, addresses | context |
| `structures.py` | packed struct definitions + struct round-trip test harness | context |
| `moduleScaffold.py` | C++20 module preamble | context (`.cppm`) |
| `headers.py` | `import`/`using namespace` (cppm) or `#include` (hdr) | context |
| `baseClassDecl.py` | `<block>Base` / `Inverted` / `Channels` companion classes | block |
| `classDecl.py` | `SC_MODULE(<block>)` class declaration | block |
| `constructor.py` | constructor init/body + factory-registration anchors | block |
| `blockRegs.py` | register-handler block class | block |
| `blockRegistrar.py` | `<block>Registrar.cpp` trampoline TU (parameterizable blocks) | block |
| `module_hdl_wrapper.py` | `<block>_hdl_sc_wrapper.h` + `vl_wrap.cpp` registrations | block / project |
| `testbench.py` | `<block>Testbench`, `<block>External`, `<block>Config` | block |

The central concept is **variant ≅ Config**: every parameterizable leaf block is emitted once as `template<typename Config> class B`, and each variant maps one-to-one to a per-variant Config policy struct. A pervasive distinction is **`hasOwnParams` versus `isParameterizable`**: a block that declares its own `params:` becomes a class template; a container that is parameterizable only because parameterizable structures transit its surface (for example `ip_top`) is emitted as a non-templated class (`classDecl.py:25`, `constructor.py:63`, `blockRegs.py:124`, `module_hdl_wrapper.py:28,41`).

#### 6.1.2 Parameterizable Config struct, VariantConfig header, and symbolic eval emission

`config.py` emits the Config policy structs into `<context>VariantConfig.h` (named via the `fileMap` entry `config: { name: "VariantConfig", ... }` at `config/project.yaml:112`). It emits a legacy `<contextStem>DefaultConfig` struct plus one struct per variant from `data['contextVariantConfigs']`. Each member is `static constexpr <type> NAME = <rhs>;`; the C++ type is chosen from `maxValue`/`maxBitwidth` so a worst-case-wide parameter gets a 64-bit field even when its current value is small.

**Symbolic eval emission (E5).** An eval-derived parameterizable constant is not frozen to a literal — its RHS comes from `emitCStyleCanonical(evalCanonical, symSpelling)` → `emissionUtils.emitExpr(..., C)`. A referent that is itself a struct member stays symbolic by bare name; any other referent is spelled from its persisted value as a literal. Result (`examples/ip_test/model/ip/ipVariantConfig.h`):

```cpp
static constexpr uint32_t IP_DATA_WIDTH    = 8;
static constexpr uint32_t IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;     // symbolic — recomputes per struct
static constexpr uint32_t IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;  // chains through sibling
```

So `ipVariant0Config::IP_DATA_WIDTH_X2` evaluates to 16 from that struct's own `IP_DATA_WIDTH = 8`, with no per-variant generator rerun.

**Firmware C emission** (`includes.py::includeConstants`): FW headers have no Config struct, so eval-derived parameterizable constants are emitted as flat consts whose RHS is the canonical expression re-spelled in C. A referent that is itself an emitted FW eval-constant stays symbolic; a block param is spelled from its persisted default. Result (`ipIncludesFW.h`): `const uint32_t IP_DATA_WIDTH_X2 = 70 * 2;` then `IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;`.

#### 6.1.3 Module / cppm scaffold and includes contract

Context includes migrated from textual `.h` headers to C++20 module-interface units (`.cppm`):
- `moduleScaffold.py::moduleHeader` emits the global-module preamble (`module;`, the `#include`s, then `export module <name>;`). The module name comes from a project-owned view field, not a filename split.
- `headers.py::_include_context_modules` emits, in cppm mode, an `import <module>;` block followed by a separate `using namespace <ns>;` block (C++20 requires all imports precede other declarations).

#### 6.1.4 HDL/Verilated SystemC wrapper bridge

`module_hdl_wrapper.py` emits `<block>_hdl_sc_wrapper.h`. For a block with own params and variants, the wrapper class is `template <typename DUT_T, typename Config>` inheriting `<block>Base<Config>`. The **HDL boundary is fixed-width and must match the resolved Verilated SV pin**: the SC-side bridge type for a parameterized payload is `sc_bv<<Struct><Config>::_bitWidth>`, while fixed signals (APB) stay literal-width. Result (`ip_hdl_sc_wrapper.h`):

```cpp
push_ack_dst_bfm<ipDataSt<Config>, sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_bfm;
apb_dst_bfm<ipRegAddrSt, ipRegDataSt, sc_bv<32>, sc_bv<32>> regs_bfm;   // APB stays fixed 32-bit
```

#### 6.1.5 Block registration encapsulation (Option δ)

`force_link` is fully retired — `grep force_link templates/systemc/` returns nothing. Two registration shapes coexist:
- **Non-templated blocks** self-register via a namespace-scope static marked `A2C_REGISTRATION_RETAIN` (defined as `[[gnu::used, gnu::retain]]`, `common/systemc/instanceFactory.h:32`). The retain attribute survives `--gc-sections`; archive-packaged builds must link with `--whole-archive` (build-system contract).
- **Parameterized blocks** defer registration to a per-block trampoline TU `<block>Registrar.cpp` (`blockRegistrar.py`), which emits one `instanceFactory::registerBlock("<block>_model", lambda, "<variant>")` per `(blockType, variant)`. The block's own `.cpp` emits `[[gnu::used]]` instantiation anchors. The `addParam`/`getParam` runtime table is decommissioned — constructors read `Config::*` directly.

#### 6.1.6 Variant-aware testbenches

`testbench.py` emits one TB artifact family per block regardless of variant count. `--variant` is purely a generated-code parameter selecting the Config type and factory variant string inside the single artifact. `_tb_selection` reads the file-level `GENERATED_CODE_PARAM --variant=...`, resolves it to `{configName, factoryVariant}`, and builds the `Config` only when `hasOwnParams`. The DUT default is the first declared variant.

#### 6.1.7 Verification

- `unittest/test_config_template.py` — Config field types selected by `maxValue`; `clog2.h` included unconditionally.
- `unittest/test_eval_cpp_emit.py` — C-style canonical translation; symbolic per-variant Config emission; FW flat-const symbolic emission.
- `unittest/test_block_config_parameterization.py` — `calcBlockConfigInfo()` parameterizable propagation.
- End-to-end: `examples/ip_test` (`make gen`/run, `VL_DUT=1`, `make regr` 11/11, "No error").

### 6.2 SystemVerilog templates

#### 6.2.1 Overview and template-to-file mapping

| Template (`builder/base/templates/systemVerilog/`) | Emits | Example output |
| --- | --- | --- |
| `package.py` | one `<context>_package` per context | `rtl/isp_types_package.sv`, `rtl/debayer_package.sv` |
| `constantsTypesEnumsStructures.py` | inline constants/types/structs in a non-package context | — |
| `moduleInterfacesInstances.py` | a container/leaf module body | `rtl/debayer.sv` |
| `moduleRegs.py` | the auto-synthesized register-handler module | `rtl/debayer_regs.sv`, `ip/ipRegs.sv` |
| `apbDecodeModule.py` | the address-decode router module | `top/apbDecode.sv` |
| `module_hdl_wrapper.py` | canonical `.svh` body + per-variant `.sv` trampolines | `ip_hdl_sv_wrapper.svh`, `ip_variant0_hdl_sv_wrapper.sv` |
| `rtldotf.py` | the `rtl.f` filelist | `rtl/rtl.f` |

**Package versus module-local split (the core C3 change).** SystemVerilog cannot parameterize a package, so every `isParameterizable` constant, type, enum, and structure moved out of the package and into the owning module (or wrapper) scope, declared from that module's parameters. The package now carries only non-parameterizable items. The module-local declaration set is produced once by `projectCreate.deriveParameterizedDeclSets()` and surfaced as `data['parameterizedDecls']`.

#### 6.2.2 Parameterized modules

`moduleInterfacesInstances.py:21-26` emits a `#( ... )` parameter list, one `parameter <NAME>` per row — **default-less** (no `= <pkg>::<NAME>` fallback). Module-local declarations follow the port list, produced by the shared helper `package.parameterizedDeclLines()` (`package.py:26-88`), ordered by `orderIndex` (eval-derived localparams first, then types/sub-structs before structs that use them).

The **symbol-spelling rule** (`package.py:53-58`): a symbol that is one of the block's own params stays symbolic; a symbol already emitted as an earlier localparam is spelled by that localparam; any other symbol is spelled from its persisted value as a literal.

**Instance parameter forwarding** (`moduleInterfacesInstances.py:88-99`): if a child's param matches one of the parent block's own params, it forwards the parent symbol; otherwise it emits the child's variant-bound literal.

#### 6.2.3 Parameterized types/structs/constants (eval → SV localparam)

Eval-derived parameterizable constants emit as module-local `localparam`s whose RHS is translated from the persisted `evalCanonical` string via `package.emitSvCanonical` → `emissionUtils.emitExpr(..., SV)`. Operators pass through one-to-one, `$clog2` stays `$clog2`, and `Num` re-spells in its authored unsized SV base. Result (`examples/ip_test/rtl/ip/ip.sv:21-24`):

```systemverilog
localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;
localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
typedef logic[IP_DATA_WIDTH_X4-1:0] ipDerivedWidthT;
```

The package render filters these out (`package.py:107-186`): every loop body `continue`s on `isParameterizable`.

#### 6.2.4 Parameterized register decode

`moduleRegs.py` makes the auto-synthesized register handler variant-correct (C3.R). The handler inherits its parent block's params, emits them as module parameters, and emits the parent's `parameterizedDecls` module-local. The parent forwards its params on the handler instance (`rtl/debayer.sv:110`).

**Per-variant word-count design.** A register is parameterizable iff its storage struct is. Storage is the variant-width module-local struct; the **APB address footprint stays at the worst-case word count** (address constants are byte-identical across variants). For each potential word, the data flop and 32-bit read view are wrapped in a `generate ... if (<W> > 32*gi) ...` ladder with `<W> = $bits(<struct>)`. Absent words are elaborated away and read `'0`. Verified in `ip/ipRegs.sv:74-93` and `:114-144`.

**Behavior change for all register blocks** (a deliberate user decision diverging from the proto): the bus is never stalled and `pslverr` is never asserted — `assign apbReg.pslverr = 1'b0;`; unmapped/read-only/absent accesses ACK, unmapped reads return 0. (The proto `reg_decode_mparam.sv` still asserts `pslverr` with `32'hBADD_C0DE`; the generator intentionally does not match it — see the "Reg-decode RTL/model divergence is intended" project record.)

`apbDecodeModule.py` (the router) is not parameterized; it routes by address offset with flopped `prdata`/`pready`/`pslverr`. Per-variant word counts are entirely a `moduleRegs` concern.

#### 6.2.5 Verilated wrapper SV side

`module_hdl_wrapper.py` emits, for a parameterizable block, two pieces:
1. **Canonical body** (`<block>_hdl_sv_wrapper.svh`) — include-only, default-less parameters, eval-derived port-width constants declared as `localparam` in the parameter port list, DUT instantiated with parameters passed by name. Verified: `ip_hdl_sv_wrapper.svh` with `input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data` and fixed `[31:0]` APB ports.
2. **Per-variant trampoline** (`<block>_<variant>_hdl_sv_wrapper.sv`) — includes the `.svh`, binds the variant's concrete values as `localparam`s, wires every flattened port through by name. Verified: `ip_variant0_hdl_sv_wrapper.sv` (`localparam IP_DATA_WIDTH = 8`, resolving the data port to 9 bits).

The flattened port widths are exact to the active per-variant width, matching the SystemC `sc_bv<...::_bitWidth>` bridge ABI. Non-parameterizable blocks take a single self-contained `.sv`.

#### 6.2.6 Emitted-RTL walkthrough and the package question

The SV packages `rtl/debayer_package.sv` and `rtl/isp_types_package.sv` exist on both `main` and `HEAD` (verified). What changed is that their **parameterizable contents were relocated into module scope**:

- `git diff main...HEAD -- rtl/isp_types_package.sv` removes `BITS_PER_PIXEL_COLOR`, `MAX_PIXEL_VALUE`, `PIXELS_PER_CLOCK`, `HORIZONTAL_SIZE`, `VERTICAL_SIZE`, `VERTICAL_SIZE_LOG2`, `pixel_t`, and the structs `rgb_pixel_t`, `bayer_pixels_per_clock_t`, `rgb_pixels_per_clock_t`, `video_bayer_t`, `video_rgb_t`. The package retains only non-parameterizable items (`eol_t`/`sof_t`/`eof_t`, `bayer_pattern_t`, `color_t`, `video_frame_t`).
- `git diff main...HEAD -- rtl/debayer.sv` shows the receiving side: `debayer` gains a `#(parameter BITS_PER_PIXEL_COLOR, PIXELS_PER_CLOCK, HORIZONTAL_SIZE, VERTICAL_SIZE)` header, the relocated localparams/typedefs/structs reappear module-local and symbolic (`rtl/debayer.sv:24-88`), and `u_preprocess`/`u_interpolate` get literal bindings (they carry explicit `variant: default`) while `u_debayer_regs` gets symbolic forwarding (the reg-handler inherits parent params).

**Why the relocation:** SV cannot parameterize a package; once a single source must elaborate at multiple bitwidths in one design, the parameterizable types must be sized from module parameters, which only module scope can express. The package stays byte-stable across variants.

#### 6.2.7 Verification

- `unittest/test_eval_sv_emit.py` — `emitSvCanonical` translation; `localparam` emitted symbolic per module (not the frozen worst-case literal); ordered before typedefs; excluded from the package; chained constants; foreign-param closure exclusion.
- `unittest/test_eval_py_to_sv.py` — the Python→SV eval converter.
- `unittest/test_boundary_signals.py` — `ipDataIf_data` spells `(IP_DATA_WIDTH + 1)` (9/71 bits), APB stays 32-bit.
- Build/runtime gates: `examples/ip_test` `make gen`/run, `make all VL_DUT=1`, `make regr` 11/11.
- Hand-written protos lock the shapes: `proto/rtl/rtl/reg_decode_mparam.sv`, `interpolate_flat_exact_wrapper.sv`, `interpolate_mparam.sv`, `preprocess_mparam.sv`.

---

## 7. Consolidated Discrepancies and Caveats

The following are points where the plan documents diverge from the committed code, or where naming may surprise a reader. They are recorded so future readers trust the code over stale plan prose.

1. **Plans are status records, not always current code.** `plan-eval-symbolic-emission.md` lists E1.5 (`evalPyToSv.py`) as "DEFERRED" in one table, but the code is landed and exercised. The code is authoritative. `plan-116-status-report.md:28-31` cautions that "Complete" refers to committed implementation, not to the (untracked) plan files themselves.
2. **`addressControl` is not fully removed from the codebase, only from the input/view-read path.** The `self.addressControl`/`AddressGroups` symbols persist inside `projectCreate` for address-counter allocation and the `ADDRESS_CONFIG` blob; they are now synthesized internally from per-block `addressBlock:` plus `project.yaml` policy. The legacy *reading* path that existed on `main` is removed.
3. **`getBlockData` comment about an `ADDRESS_CONFIG` fallback for routers without an authored `addressBlock` is stale** relative to the post-Stage-8 code, where every router authors `addressBlock:`.
4. **RTL packages were not deleted.** Earlier framing (including the initial diff-stat read, which showed `50 -`/`31 -` line changes) suggested `debayer_package.sv`/`isp_types_package.sv` were removed. They exist at `HEAD`; only their parameterizable contents moved to module scope. The actual deletions are the SystemC `model/*Includes.{h,cpp}` (now `.cppm`), `tb/debayer/test_structs.{cpp,h}`, the monolithic `*_hdl_sv_wrapper.sv` (now `.svh` + per-variant `.sv`), the AI-rules files (now symlinks to `AGENTS.md`), and the engine files `config/{cpp,sv,doc}Config.yaml` and `config/postParseRegister.py`.
5. **Generated SV parameters are default-less.** `plan-sv-parameterization.md` and the protos show parameters defaulting from the package (`= isp_types_package::BITS_PER_PIXEL_COLOR`). The shipped emitter emits default-less parameters and always instantiates with explicit overrides; the package-default escape hatch was not used.
6. **Proto-versus-generator `pslverr`.** The reg-decode proto asserts `pslverr` and returns `0xBADD_C0DE` on unmapped access; the shipped `moduleRegs.py` intentionally ties `pslverr` to 0 and returns 0. This is a deliberate divergence, not a defect.
7. **Stale narrative comments.** `blockRegistrar.py` (lines 26-29) and `classDecl.py` (lines 101-105) still reference an "active force-link function"; that machinery was retired under Option δ and emits nothing. `structures.py` carries a stale `# TODO: handle variable size parameters`; the wrapper path already handles parameterizable widths.
8. **Several plans are historical/superseded** — `plan-parameterizable-config-template.md` (names a non-existent `configPolicy.py`; describes a one-Config-per-instance model that was superseded by `plan-variant-config-unification.md`), `plan-migration-tool.md` (a separate hand-written C++/SV migration scope, not the YAML migration), and `plan-ip-test-example.md`. There is no `plan-ip-namespaces-and-parameterization.md`. Cite these only for design rationale.
9. **`ipDefaultConfig` default value.** The generated `ipVariantConfig.h` sets `ipDefaultConfig::IP_DATA_WIDTH = 70`, mirroring the `ipParameters` `value: 70` rather than the variant0 value (8). This is internally consistent but can surprise a reader who expects "default = variant0."
10. **`constantsTypesEnumsStructures.py` has no `isParameterizable` filter** (unlike `package.py`); it is used for non-package contexts and is not on the parameterized path, so it is untouched by C3.

---

## 8. Appendix

### 8.1 Key source files

| Area | File |
| --- | --- |
| Expression parser/evaluator | `builder/base/pysrc/evalExpr.py` |
| Python→SV converter | `builder/base/pysrc/evalPyToSv.py` |
| Expression emission (C/SV) | `builder/base/pysrc/emissionUtils.py` |
| Schema | `builder/base/pysrc/schema.py`, `builder/base/config/schema.yaml` |
| Value resolution | `builder/base/pysrc/valueResolver.py` |
| Views + parse orchestration | `builder/base/pysrc/processYaml.py` |
| Address migration | `builder/base/pysrc/migrateAddressControl.py` |
| Includes migration | `builder/base/pysrc/migrateIncludes.py` |
| Migration driver | `builder/base/migrateYaml.py` |
| SystemC templates | `builder/base/templates/systemc/*.py` |
| SystemVerilog templates | `builder/base/templates/systemVerilog/*.py` |
| Canonical fixture | `builder/base/examples/ip_test/` |

### 8.2 Glossary

- **Variant** — a named binding of a block's parameters to concrete values.
- **Config** — the C++ policy struct (one per variant) that supplies a templated block's parameter constants.
- **Parameterizable** — an item whose width/depth depends on a parameter; carries a worst-case bound (`maxValue`/`maxBitwidth`).
- **`hasOwnParams`** — a block declares its own `params:` (becomes a class template / parameterized module).
- **`isParameterizable` (container)** — parameterizable only because parameterizable structures transit its surface (emitted non-templated).
- **Router** — a block declaring `addressBlock:`; decodes and routes register traffic.
- **Routed leaf** — a register-owning leaf; a reusable IP declares `registerPorts:`, a top-down leaf infers from the serving router.
- **Thunker** — a per-protocol bridge generated for a cross-interface bind where parent and child interfaces (or Config types) differ.
- **Canonical eval string** — the persisted, fully-qualified serialization of an eval expression (`evalCanonical`), surfaced to generators without re-parsing.
