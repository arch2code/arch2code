# Block Parameter / Constant Name Collision

Design discussion converging on a plan. Captures the problem, the
evidence, the current YAML and emitter behavior, and the chosen design
direction. Decided paths are stated as decisions; unresolved items are
called out as open questions.

## Status

- **Current handoff (reconciled 2026-07-24):** C1 and C2 are **committed and
  verified** per the logs below. C3 is **committed and verified** for
  C3.1-C3.8 and C3.R; **C3.6 static
  validation is now done** (2026-06-23) — its matrix is 11/11 PASS in
  `unittest/test_param_const_linkage.py`, so **C3 has no residual**. C4 is **superseded** as an
  owner here and is handed off to `plan-eval-symbolic-emission.md`: E4 and E5
  are complete/committed, including firmware C, and E6 is closed/descoped
  because all variants intentionally share the worst-case-sized address map.
- **Originating concern:** "We do not want parameters colliding with
  constants from a downstream language perspective. Constants in the
  same scope as the parameters could create problems."
- **What surfaced:** The collision is already biting `ip_test`. A TODO
  in the generated SV calls it out. There is also a latent parser-side
  bug for the unintentional-shadow case.
- **Design direction (2026-05-29, V1 + E1):**
  - **`ipParameters` stays.** It is processed early (the reason it
    exists — it solves the parse-ordering problem; see "Section
    ordering" below) and declares the externally exposed IP API
    parameters. Its constants are captured into a new **file-level dict**
    so the linkage to params can be validated.
  - **A block param *is* an `ipParameters`-defined constant**
    (same-name identity — today's overlap). This identity is
    **orthogonal to `isParameterizable`**: "is a param" (instancer-bound
    via `blockparams` + `parameters:` variants) is a separate concern
    from the `isParameterizable` emission flag.
  - **The overlap is required and checked for `ipParameters.constants`.**
    Every externally exposed `ipParameters` constant must be consumed by
    at least one block param (error on an orphaned `ipParameters` const).
    Multiple blocks may consume the same exposed parameter. Every block
    param must be backed by a same-name `ipParameters` const (pure params
    were dropped — see Q6 — so there is no unbacked block-param category).
  - **Derived/computed constants live in regular `constants:`**
    (e.g. `IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2`), with `eval` against
    the params. Their SV `eval` emission once inputs are module-scoped
    is a deferred issue (see Q4).
  - **Emission divergence on `isParameterizable`.** SV does not render
    `isParameterizable` elements in the package — they move to module
    scope (a language constraint: SV can't parameterize packages). C++
    keeps the templated + `using` scheme. User-facing SV and C++ code
    should look as similar as possible.
  - IP top-level YAML is conceptually the IP "API" (see next section),
    and `ipParameters` is part of that API surface; formalizing the
    convention is deferred to a future skill.
  - **Superseded:** the earlier embed-in-block / parse-twice /
    dual-materialization / V2-forbid-overlap direction is dropped (see
    the 2026-05-29 reversal entry in the iteration log).

## IP top-level YAML as the IP "API" (conceptual, future skill)

This framing informs the direction but is **not** part of this plan's
mechanics; it is captured here and intended to be formalized in a
future skill.

- The IP top-level YAML should be treated as the IP's **API**.
  Everything an IP *user* needs — the block(s), constants, types,
  structs, and interface definitions — is exposed here. It should be as
  self-contained as possible and omit implementation detail.
- A separate IP **implementation** YAML instantiates the lower-level
  instances and any other internal wiring, and `include`s this API
  YAML.
- `ipParameters` is part of the API surface: it declares the
  parameterizable constants an instancer sets, alongside the block,
  constant, type, struct, and interface definitions the IP exposes.

## SV constraint that forces the shape

SystemVerilog (IEEE 1800-2017) does not support parameterized packages.
A package declaration cannot take parameters and items inside a package
cannot reference per-instance module parameters. The package/module
split is fundamentally elaboration-time-fixed (package) vs
per-instance (module).

Concretely, this means:

- Any value that varies per block instance must live as a module
  `parameter` on the owning block. It cannot be a package `localparam`.
- Any typedef whose width depends on a per-instance value must be
  declared inside the module that owns the parameter — not in the
  package. SV typedefs in a package are sized once at package
  elaboration.
- Computed constants (`IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2`) whose
  inputs vary per instance must be computed inside the module as
  module-local `localparam`s, not as package localparams. (How the
  `eval` for these is emitted is deferred — see Q4.)

This is why parameterizable values must move out of the package and
into the owning module: it is the only end-state consistent with SV's
language model, and it drives the design direction in the Status
section.

### SV is the sentinel shape

SV is the most constrained of the supported output languages:

- No parameterized packages.
- Per-instance values can only live as module parameters.
- Typedef identity is per-scope; cross-module type sharing requires
  either a package symbol or an interface/class workaround.

C++ has no equivalent restriction — class templates parameterize
includes naturally, and the existing SystemC emission already uses
this. Because SV is the most constrained, **the YAML model has to
accommodate what SV can express**. Languages with looser constraints
can map onto a richer shape, but the YAML cannot oblige users to
write structures that SV cannot emit.

This is why the rest of this document treats SV emission decisions as
load-bearing constraints on the YAML model, while SystemC decisions
are mostly consequences.

## Problem statement

The YAML allows a name to appear simultaneously as:

1. A parameterizable constant (an entry under `ipParameters.constants`
   with `isParameterizable: True`), and
2. A block parameter (an entry in `blocks.B.params`).

Today these two declarations are treated by the parser as the *same
logical entity*: the constant provides the default value and worst-case
`maxValue`, and the block param provides the per-variant binding. The
overlap *is* the linkage. There is no other YAML construct that says
"these two are the same thing."

The convention does not declare itself as an invariant. The schema does
not enforce it. The parser does not validate it. The result is two
problems:

- **Downstream SV emission produces a name collision** (package
  `localparam` plus module `parameter`) which forces package-level types
  to a single fixed width even when per-variant module parameters want
  different widths.
- **The parser silently accepts unintentional overlap** between a block
  param and a non-parameterizable constant, producing wrong worst-case
  sizing in `calcAddresses`.

## Evidence

### The SV collision (the smoking gun)

`examples/ip_test/arch/yaml/ip.yaml` declares (excerpt):

```yaml
ipParameters:
    constants:
        IP_DATA_WIDTH:    { value: 70, maxValue: 128, ... }
        IP_MEM_DEPTH:     { value: 16, maxValue: 32, ... }
        IP_DATA_WIDTH_X2: { eval: "$IP_DATA_WIDTH * 2", ... }

blocks:
    ip:
        params: [IP_DATA_WIDTH, IP_MEM_DEPTH, IP_NONCONST_DEPTH]
```

Generated `examples/ip_test/rtl/ip_package.sv`:

```sv
package ip_package;
localparam int unsigned IP_DATA_WIDTH = 32'h0000_0046;   // = 70 (default)
localparam int unsigned IP_MEM_DEPTH = 32'h0000_0010;    // = 16 (default)
...
typedef logic[IP_DATA_WIDTH-1:0] ipDataT;
typedef logic[$clog2(IP_MEM_DEPTH)-1:0] ipMemAddrT;
typedef struct packed { ipDataT data; } ipMemSt;
...
```

Generated `examples/ip_test/rtl/ip.sv`:

```sv
module ip
import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
) (...);
```

Inside the `ip` module body both names exist:

- The package `localparam IP_DATA_WIDTH = 70` and the package-level
  `ipDataT` typedef sized to 70 bits.
- The module `parameter IP_DATA_WIDTH`, overridden per instantiation
  (e.g. `8` for variant0, `70` for variant1).

For any instance whose override differs from the package default, the
package-level type is *the wrong width* for that instance. The
generator already acknowledges this with a TODO inside `ip.sv`:

```sv
// TODO(SV parameterization): remove this field-wise widening once
// parameterizable package types become module-local types driven by
// this instance's IP_DATA_WIDTH parameter. Today ipDataSt/ipDataT
// come from ip_package at the max/default width, so variant0's
// narrower push_ack payload must be widened without moving marker.
```

The collision isn't a hypothetical — the SV emitter is actively
working around it with field-wise widening.

### The parser-side latent bug

`_resolveWordLinesConst`'s bare-name branch (`pysrc/processYaml.py:4884`):

```python
ctx = blockKey.split('/', 1)[1]
entry = self.data.get('constants', {}).get(ctx, {}).get(wl)
if entry is not None:
    return entry
if self.checkIsParam(blockName, wl, ctx):
    return None
printError(...)
```

This returns the constant entry **regardless of whether the constant is
parameterizable**. `calcAddresses` consumes it:

```python
if isParam and wlConst and wlConst['isParameterizable'] and wlConst['maxValue']:
    wordLines = wlConst['maxValue']
elif wlConst and wlConst['value'] is not None:
    wordLines = wlConst['value']
else:
    wordLines = self._resolveBlockParamMaxWordLines(...)
```

Consider a user YAML where the names accidentally collide and the
constant is *not* parameterizable:

```yaml
constants:
    DEPTH: { value: 16, desc: "memory depth" }   # NOT parameterizable

blocks:
    myBlock:
        params: [DEPTH]

parameters:
    myBlock:
        - { variant: v0, param: DEPTH, value: 24 }
        - { variant: v1, param: DEPTH, value: 32 }

memories:
    - { memory: myMem, block: myBlock, wordLines: DEPTH, ... }
```

The parser flow:

1. `wordLines: DEPTH` → `checkIsParam` returns True → `wordLinesKey = ""`.
2. `_resolveWordLinesConst` bare-name branch returns the constant
   `{value: 16, isParameterizable: False, maxValue: 0}`.
3. `calcAddresses` falls to the `elif wlConst['value'] is not None`
   branch → uses `16`.
4. The variant bindings (`24`, `32`) are **silently ignored for
   sizing**. Result: memory is under-allocated for both variants.

Nothing in the parser, schema, or post-parse passes refuses this YAML
today.

### How the SystemC emitter handles the overlap

For completeness: SystemC doesn't have the same collision shape as SV.
`examples/ip_test/model/ipConfig.h` (excerpt):

```cpp
template <> struct Config<Variant0> {
    static constexpr uint32_t IP_DATA_WIDTH = 8;
    static constexpr uint32_t IP_MEM_DEPTH = 16;
    static constexpr uint32_t IP_DATA_WIDTH_X2 = 140;
    static constexpr uint32_t IP_NONCONST_DEPTH = 24;
};
template <> struct Config<Variant1> {
    static constexpr uint32_t IP_DATA_WIDTH = 70;
    static constexpr uint32_t IP_MEM_DEPTH = 8;
    ...
};
```

Per-variant `Config` specializations collapse "block param" and
"parameterizable constant" into one C++ member each. The overlap
disappears because there's only one symbol per variant. Types use
`Config::IP_DATA_WIDTH` rather than a global; the variant the type is
instantiated under picks the right value. SystemC consumers do not see
the package-vs-module collision SV consumers see.

This is why the project ships today despite the SV collision: SystemC
is consistent across variants; SV is internally inconsistent but
shipped anyway with the TODO + field-wise widening.

## Current YAML model — what overlap means today

Three orthogonal categories share one namespace:

| Category | Declared in | Today's downstream artifact |
|---|---|---|
| A. Parameterizable constant with a backing param | `ipParameters.constants` AND `blocks.B.params` | SV: package `localparam` + module `parameter` (collision). SystemC: per-variant `Config` member. |
| B. Derived parameterizable constant | `ipParameters.constants` only | SV: package `localparam` (one global value, derived from defaults). SystemC: per-variant `Config` member (re-evaluated per variant). |
| C. Pure block param | `blocks.B.params` only | SV: module `parameter` (no default). SystemC: per-variant `Config` member. |
| D. Plain constant | `constants:` only | SV: package `localparam`. SystemC: shared include `const` (one definition; `includes.py::includeConstants` emits non-`isParameterizable` constants here and skips them from the per-variant `Config` structs). |

The linkage between (A)'s two declarations is **the name itself**. There
is no other YAML construct asserting "these are paired." Removing the
name overlap (or restricting it) requires giving the linkage a
first-class home somewhere.

## Design

### YAML model

`ipParameters` is retained as part of the IP top-level API surface. It
may contain more than constants (for example API-facing types), and its
sub-sections still flow through the normal `processSection` machinery.
The new linkage rule applies specifically to
`ipParameters.constants`.

The constants namespace divides as follows:

1. **Plain constants** stay in `constants:` — elaboration-time-fixed,
   globally visible, emitted as a package `localparam`.
2. **Param-backing constants** are declared in `ipParameters` and are
   the *only* place a block param's backing value may come from.
   These are the externally exposed parameters the IP user may set.
3. **Derived/computed constants** stay in `constants:` with `eval`
   against the params (e.g. `IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2`).
   Variant-aware recomputation and final SV emission for these values
   are deferred (see Q4).

A block param **is** an `ipParameters` constant of the same name
(today's overlap). The overlap is required and checked (see Parser). The
candidate shape — close to today's `ip.yaml`:

```yaml
ipParameters:                    # processed early; declares exposed IP API params
    constants:
        IP_DATA_WIDTH:     { value: 70, maxValue: 128, desc: ... }
        IP_MEM_DEPTH:      { value: 16, maxValue: 32,  desc: ... }
        IP_NONCONST_DEPTH: { value: 24, maxValue: 24,  desc: ... }  # was a pure param
    types:
        # API-facing parameterizable types may live here and follow normal
        # type processing; they are not part of the block-param consumed check.
        ipDataT:
            width: IP_DATA_WIDTH
            maxBitwidth: 128
            desc: ...

constants:                       # plain + derived/computed
    IP_REG_ADDR_WIDTH: { value: 32, desc: ... }
    IP_DATA_WIDTH_X2:  { eval: "$IP_DATA_WIDTH * 2", desc: ... }  # eval emission deferred (Q4)

blocks:
    ip:
        params: [IP_DATA_WIDTH, IP_MEM_DEPTH, IP_NONCONST_DEPTH]
```

Every param in `blocks.ip.params` has a same-name `ipParameters.constants`
entry (pure params are dropped — see Q6). Every `ipParameters.constants`
entry is consumed by one or more block params. Multiple blocks in the same
IP API may consume the same exposed parameter. The former pure param
`IP_NONCONST_DEPTH` is now a normal `ipParameters` constant.

### Parser

- **`ipParameters` processed early, captured in a file-level dict.**
  `_process_ipParameters` already routes its sub-sections through
  `processSection` and stamps `isParameterizable` per entry
  (`_ipParametersActive`, line 5934, with per-entry referent
  finalization at line 5946). Additionally, capture each `ipParameters`
  constant into a new **file-level dict** so the param linkage can be
  validated.
- **Overlap required and checked for constants, via a `_validate` linkage
  step.** Validate bidirectionally at the `ipParameters.constants` level:
  every `ipParameters` constant must be consumed by one or more block
  params (error on an orphaned `ipParameters` const), and every block
  param must be backed by a same-name `ipParameters` const. The validation
  is more than a name match — at file level it does two things:
  - **Resolves the qualified reference** from the block param to its
    backing const, for parse-time validation only. This reference is
    ephemeral parser state: it exists to detect and report linkage errors
    during `projectCreate` and is **not persisted**. The SV package
    discriminator (C3.1) does not consume it; `projectOpen` re-derives
    "block-param-backing vs eval-derived" through normal view creation off
    the persisted `blocksparams` and `constants` tables (see SV emitter).
  - **Asserts the backing const has `isParameterizable` set.** A block
    param backed by a non-parameterizable const is rejected here.

  Multiple blocks may consume the same parameter. Other `ipParameters`
  sub-sections are API-facing declarations and do not participate in the
  consumed-by-block validation.
- **Variant-bound sizing validation runs where the bindings are declared,
  not in the file-level linkage step.** The backing const's `maxValue` must
  be greater than or equal to the maximum over that param's `parameters:`
  variant bindings; worst-case sizing is then sourced from the const's
  `maxValue`. Without this assertion a const whose `maxValue` is set below
  its variant bindings reopens the silent under-allocation that latent
  issue #1 is meant to close. This check **cannot** sit in the API file's
  per-file step, because the `parameters:` variant bindings are an instance
  definition that may be authored in a different file (in `ip_test`,
  `ipVariants.yaml` `include`s `ip.yaml`, so no `parametersvariants` row for
  the block exists when `ip.yaml`'s section loop finishes). Instance
  definitions can only be validated where they are declared: this assertion
  is a `processSingleFile` step in the file that declares the `parameters:`
  bindings, where the included backing const (with its `maxValue`) and the
  local variant bindings are both known. It runs during parsing, ahead of
  `calcAddresses`, so under-sized `maxValue` is rejected before address
  sizing consumes it.
- **Consumed-scope validation runs per file.** The consumed check belongs
  immediately after a file has been parsed, as a `processSingleFile`
  step after its section loop completes. At that point the file-local
  `ipParameters.constants` dict and the file's `blocks.*.params` rows
  are both known, so orphaned exposed params and unbacked block params can
  be reported with the correct file scope. The check is one-directional
  orphan/backing detection within the file: it asserts that every
  `ipParameters` const declared in the file is consumed by a same-file
  block param, not that block params may only consume file-local params. A
  block definition is part of the IP API surface, so `ipParameters` and the
  consuming block declarations co-locate in the same (API) YAML; only
  instance instantiation lives in the implementation YAML. This is also
  consistent with the existing `_process_ipParameters` constraint that
  rejects `ipParameters` in a blockless shared include
  (`processYaml.py:5942`). Do not defer this to a later project-wide sweep
  unless a future cross-file API construct requires it.
- **Param identity is orthogonal to `isParameterizable`.** "Is a param"
  (instancer-bound via `blockparams` + `parameters:` variants) is
  tracked separately from the `isParameterizable` emission flag. Do not
  overload `isParameterizable` to mean "is a param."
- **`isParameterizable` is the load-bearing emission switch.** The SV
  package skips `isParameterizable` entries (they move to module scope);
  C++ keeps the templated form.
- **Latent under-allocation.** With the overlap required and checked, a
  block param always resolves to a parameterizable `ipParameters`
  constant, so the "non-parameterizable constant shadows a block param"
  case is rejected by validation rather than silently mis-sized. The
  `maxValue` ≥ variant-binding assertion (C1.2b, run where the bindings are
  declared) closes the second door (a backing const whose `maxValue` is set
  too low). Together these close
  latent issue #1; the old `_resolveWordLinesConst` shadow heuristic is no
  longer the load-bearing guard, so no separate fix to it is required.
- The `parametersvariants` binding references a block-param name, as
  today.

### View ownership (`getContextData` vs `getBlockData`)

The parser and post-processing should compute ownership facts once, then
surface them through the appropriate `projectOpen` views. This avoids
templates reverse-engineering the same relationships from both context
and block data.

- **`getContextData()` owns context/IP API declarations.** It surfaces
  the externally exposed `ipParameters` declarations, regular
  context-level constants/types/structures/enums, Config-header inputs,
  and context-level summaries needed by package/include/config emission.
- **`getBlockData()` owns block-local rendering facts.** It surfaces the
  params a block consumes, the Config descriptors and defaults relevant
  to that block, the parameterized types/structures/interfaces needed by
  its ports/registers/memories, and later the SV module-local
  declarations needed for that specific module.
- **Parameterized declaration selection bridges the two views; owner
  resolved (2026-06-02): a `projectCreate` post-parse derivation that
  persists the resolved per-block set.**
  Context data owns the full set of constants, types, and structures
  visible through the block's include contexts. Block data owns the
  subset that can be emitted locally: declarations whose parameter
  dependencies are satisfied by the parameters exposed on this block.
  The selection inputs are `(include contexts visible to the block,
  params available to the block)`, and the output is a block-local set of
  types/structures for module-local SV declaration. The set cannot be
  derived only from declarations used by memories, registers, and ports
  because parameterized declarations may be intended purely for user code.
  Rather than re-deriving this in `projectOpen`, the resolved set is
  computed once in `projectCreate` and persisted in a join table that
  `getBlockData()` reads with a single indexed query. See
  "Parameterized declaration set (C1.4 resolution)" below for the capture
  conclusion, derivation algorithm, and table.
- **Shared derivations get a single owner.** Cross-object facts such as
  "`ipParameters.constants` consumers", "which blocks consume this
  parameter", and "which parameterizable declarations are needed by this
  block" need an explicit owner. Template utilities should not walk
  `prj.data` to rediscover these relationships.

### Parameterized declaration set (C1.4 resolution)

This is the owner and mechanism for the per-block module-local
declaration set. Resolved 2026-06-02.

**Capture: no parser changes are needed for stage 1.** The type/struct →
parameter dependency graph is fully recoverable after parsing from columns
that already exist, verified against `ip_test.db`:

- Type → constant: `types.widthKey` / `widthLog2Key` / `widthLog2minus1Key`
  (e.g. `ipDataT.widthKey = IP_DATA_WIDTH/ip.yaml`).
- Struct → type / nested struct / array-size constant:
  `structuresvars.varTypeKey` / `subStructKey` / `arraySizeKey`.
- All keys are qualified `name/file`, so closure across include contexts is
  unambiguous; `isParameterizable` is already stored per type and struct.

The only edge discarded at parse is constant→constant (eval): the
`constants` table stores no `eval` string and no reference key. That edge
is needed only for variant-aware eval (C4) and is therefore deferred with
it. When a closure reaches a parameterizable constant that is not any
block's backing const, that is by definition an eval-derived constant; the
pass detects this and routes the dependent declaration to the
eval-coupled/deferred bucket without needing the missing edge.

**Derivation: a single post-parse pass**, slotted immediately after
`calcBlockConfigInfo()` (which has already set `blocks.isParameterizable`).
Inputs are all persisted: `blocksparams`, the `*Key` edges, the
`isParameterizable` flags, the C1.2 backing-const linkage, and
`yamlContext`.

1. **Classify constants** (global, once): a backing const (a block param,
   per the linkage) contributes its qualified key to a declaration's
   parameter set; a parameterizable-but-unbacked const is eval-derived and
   marks the dependent declaration eval-coupled; a non-parameterizable
   const contributes nothing.
2. **Per-declaration parameter set** (memoized, cycle-guarded transitive
   closure): types follow `width*Key`; structs union their vars'
   `varTypeKey` (recurse type), `subStructKey` (recurse struct), and
   `arraySizeKey` (constant). Output per parameterizable declaration is
   `paramSet` (backing-const keys) and `evalCoupled`. The existing
   `isParameterizable` flag must agree with "`paramSet` non-empty or
   `evalCoupled`"; a mismatch is asserted as a generator bug.
3. **Per-block selection**: for each block with `isParameterizable = 1`,
   include a parameterizable declaration when it is visible in
   `yamlContext[block._context]`, is not eval-coupled, and its `paramSet`
   is a subset of the block's param keys. Declarations with unsatisfied
   deps are omitted (they belong to a more-parameterized block);
   eval-coupled declarations are deferred to C4. Topologically order the
   included set (types before the structs that use them) and assign
   `orderIndex`.

`paramSet` stays in memory for the pass; it is not persisted, because the
C3.6 connection/interface validation (the non-parameterized-sub-block and
no-level-skipping checks) runs in the same pass off the same in-memory
structure.

The membership rule is the resolved Q8 stance (visible ∧ parameterizable ∧
satisfiable), which deliberately includes declarations used only by
hand-written user code. The accepted consequence: a parameterizable type
shared by several blocks is emitted module-local in each — correct for SV,
since each module sizes its own copy from its own parameter — at the cost
of an occasional unused local typedef where a block can satisfy a type it
never references. That is harmless and may be narrowed later if noisy.

**Storage: an explicit, non-schema derived table** (resolved 2026-06-02).
This is a new `projectCreate` → `projectOpen` communication channel,
distinct from the two existing ones: schema-backed tables (driven by
`config/schema.yaml`) and the DB-backed `config` object (pickled, used for
smaller-scale derived state). The per-block set is neither user-authored
nor small enough to want as a pickled blob queried by hand, so it is held
in a table that is created, indexed, populated, and queried **directly**,
outside the schema machinery:

- **Not declared in `config/schema.yaml`.** It is not user-derived data, so
  it does not belong to the schema contract and does not flow through
  `createTable` / `generateIndexes` / the `projectOpen` schema loader.
- **Created and indexed directly in `projectCreate`.** The derivation pass
  issues an explicit `CREATE TABLE`, then a bulk insert, then a
  `CREATE INDEX` on `blockKey` (creating the index after the bulk load
  keeps insertion cheap). The query case is block-usage, so `blockKey` is
  the indexed access path.
- **Queried directly in `projectOpen`.** `getBlockData()` issues
  `SELECT declKind, declKey, orderIndex FROM <table> WHERE blockKey = ?
  ORDER BY orderIndex` per block and joins to the existing
  `types`/`structures` rows for bodies. The table is not loaded wholesale
  into `prj.data`; it is queried on demand for the block being rendered.

Columns (keys and order only; emission bodies stay in the existing
`types`/`structures`/`structuresvars` tables):

| column | meaning |
|---|---|
| `blockKey` | owning parameterized block (indexed access path) |
| `declKind` | `type` or `structure` (`constant` reserved for C4) |
| `declKey` | qualified key into `types` / `structures` |
| `orderIndex` | emission order within the block |

`(blockKey, declKey)` is unique and may serve as the primary key; the
many-to-many relation is expressed by the same `declKey` appearing under
several `blockKey`s. The `declKind` discriminator lets eval-derived
constants fold in at C4 with no structural change. In stage 1 the table
holds only types and structures, because block params become module
`parameter`s straight from `blocksparams` (C3.3) and plain/eval constants
stay in the package.

**Efficiency:** the derivation builds the full row list in memory during
the closure pass, then performs a single `executemany` insert; the index
is created afterward. No per-row `INSERT` round-trips and no re-entry
through `processSimple`.

### Section ordering (resolved by keeping `ipParameters`)

Embedding params in `blocks` created a parse-ordering cycle:

```
block.params  →  types / structures  →  interface_defs / interfaces  →  block.ports
 (param consts)    (eval widths vs        (reference structures)         (reference
                    params)                                               interfaces)
```

- Sections are processed in **authored order, single forward pass**
  (`processSingleFile`: `for section, sectData in sections.items()`).
- Width `eval` is **parse-time** (`types`' `post(validateTypeWidth)`
  resolves via `_parserResolver`), so a type that evals `$IP_MEM_DEPTH`
  requires `IP_MEM_DEPTH` to already exist when `types` is processed.
- `block.ports` depends on `interfaces` → `structures`/`types` →
  param-constants. If params lived in `blocks` (authored last), the
  cycle would force multi-pass parsing.

**Resolution:** keep `ipParameters`. Authored before `types`/`blocks`,
it materializes the param-constants up front — exactly what it does
today — so a single forward pass works with no hoist and no deferred
eval. This is the decisive reason the embed-in-block direction was
dropped. (Q12 is thereby resolved.)

### Emitter constraint: reuse existing templates and sections

No new templates *and no new generated sections* are introduced for this
functionality. The new output goes into the existing generated regions:

- **C++ base class** (`--template=baseClassDecl`, e.g. `ipBase.h`):
  already declares the param constants (`const uint64_t IP_DATA_WIDTH;`
  …) and the interface ports (`push_ack_in< ipDataSt<Config> >
  ipDataIf;`) as bare-named members. The trailing-underscore storage and
  any base-side aliases extend this same region.
- **C++ derived class** (`--template=classDecl`, e.g. `ip.h`): the
  `using` type/constant re-imports and the user-facing reference aliases
  go here.
- **C++ constructor** (`--template=constructor --section=init`): the
  reference-alias initializers go in the existing init list.
- **SV module** (`--template=moduleInterfacesInstances`, e.g. `ip.sv`):
  the module-scope typedefs/structs/localparams go in the existing
  module region.
- **SV package** (`--template=package`): keeps only the
  non-`isParameterizable` symbols.

These are produced by extending the current templates (and the
`projectOpen` views that feed them), not by adding template files or new
`--section=` names. This applies to every emitter change below.

### SV emitter

- Package: emits non-`isParameterizable` constants and the types/structs
  that depend only on them. *(Superseded 2026-06-05: the package skips **all**
  `isParameterizable` declarations, including eval-derived parameterizable
  constants. The "keep eval-derived in the package until C4" sub-decision and
  the package-filter discriminator below are no longer in effect — the filter
  is simply `isParameterizable`. The discriminator note is retained only as
  history.)*
- Module: emits its own `params:` as module `parameter`s, and any
  types/structs that transitively depend on those as module-local
  typedefs declared inside the module. Computed (`eval`) constants whose
  inputs are module-scoped become module-local `localparam`s — but the
  `eval` emission is deferred (Q4).
- **Eval-derived constants are `isParameterizable` (verified).** The parser
  walks each `$TOKEN` in an `eval` string and stamps `isParameterizable`
  when any referent is parameterizable (`processYaml.py:4769`-`4817`).
  Confirmed against `ip_test.db`: `IP_DATA_WIDTH_X2` carries
  `isParameterizable = 1`, `maxValue = 256` (auto-derived `128 * 2`). A
  naive "skip all `isParameterizable` constants from the package" filter
  would therefore drop the eval value out of SV entirely while C4 is
  deferred, breaking any RTL that references it.
- **Package filter discriminator.** *(Superseded 2026-06-05 — history only.
  The package now skips every `isParameterizable` constant, so no
  block-param-backed vs eval-derived discriminator is needed at package time.)*
  Under the new scheme an eval-derived
  constant **cannot live in `ipParameters`**: nothing consumes it as a
  block param, so the per-file orphan/consumed check would reject it. It is
  therefore forced into `constants:`, where the consumed check does not
  apply. This makes the discriminator clean: a parameterizable constant
  that backs a block param (an `ipParameters` exposed param) moves to
  module scope; a parameterizable constant with **no** block-param backing
  is eval-derived, lives in `constants:`, and stays in the package until
  C4. C3.1 obtains this through normal `projectOpen` view creation —
  matching a parameterizable `constants` row against a same-name,
  same-scope `blocksparams` row — not through any reference carried over
  from the parser. This matters because the `constants` DB row stores no
  `eval` column (columns: `constant, constantKey, value, desc, maxValue,
  isParameterizable, valueType, _context`), so the emitter cannot
  rediscover "this was eval-derived" directly — the presence or absence of
  a `blocksparams` backing is the signal.
- Type/struct ownership rule: a type or struct is module-local if its
  width-deciding expression transitively references any
  `isParameterizable` value; otherwise it lives in the package.
- The `ip.sv` TODO ("remove this field-wise widening once
  parameterizable package types become module-local types") closes
  naturally once this lands.

### SystemC emitter

The per-variant `Config<Variant>` struct and templated types/structures
in the includes already implement the main C++ shape:

- Per-instance values are members of `Config<Variant>`, distinct per
  variant.
- Parameterizable types are template aliases parameterized by
  `Config` (e.g. `template<typename Config> using ipMemAddrT = ...`).
- Parameterizable structures are template structs that consume
  `Config`'s member values for their widths.
- Plain constants and plain types live in includes at the IP-root or
  shared level.
- Eval-derived parameterizable constants remain deferred. They may be
  stamped `isParameterizable`, but variant-aware re-evaluation and final
  C++/SV placement are handled with the broader eval work in Q4.

C++ class templates parameterize includes naturally, so the C++ shape
does not need a "module-local" vs "package" split. The same template
declaration in a shared include works for all variants because the
variant is supplied at instantiation time. The SystemC story is mostly
"consume the new YAML shape; the existing templated type/structure
emission pattern is already correct."

### Generated-artifact divergence is intentional, user-facing divergence should be minimized

Non-parameterized declarations are similar across emitters. The
parameterized ones land in different *generated* places because each
language has a different mechanism for "per-instance":

| YAML category | SV emission | C++ / SystemC emission |
|---|---|---|
| Plain constant (`constants:`) | package `localparam` | shared include `constexpr` / `inline constexpr` |
| Plain type (no parameter reference) | package `typedef` | shared include `using` alias |
| Plain structure (only plain types) | package `typedef struct packed` | shared include `struct` |
| Block parameter (`blocks.B.params` entry) | module `parameter` on B | `Config<Variant>::PARAM` member |
| Parameterized type (references a block param) | **module-scoped** `typedef` inside B | templated `using` alias in include, parameterized by `Config` |
| Parameterized structure (contains parameterized types) | **module-scoped** `typedef struct packed` inside B | templated `struct` in include, parameterized by `Config` |
| Computed constant (`eval` depending on params) | **module-scoped** `localparam` inside B (`eval` emission deferred — Q4) | `Config<Variant>::` member or `constexpr` derived from `Config` |

The YAML does not specify where things go per-emitter — it classifies
them as parameterized-or-not, and each emitter applies its own
convention. The "where it lives" column is an emitter property, not a
YAML property.

The asymmetry of work this implies:

- **SystemC emitter:** moderate — the existing templated-types-in-
  includes pattern is correct, but the user-facing code today exposes
  `Config::PARAM` and `someType<Config>` clutter that has no SV
  equivalent. To minimize cross-language user-facing divergence, the
  emitter should hide the template machinery behind class-local
  aliases (see next section).
- **SV emitter:** substantive — today emits parameterizable values as
  package localparams and parameterizable types as package typedefs.
  Both must move into the owning module. Derived values must be
  emitted as module-local localparams. Blocks that use parameterized
  types emit local declarations; cross-boundary channel adaptation is
  the remaining story (see Q9).

### Minimizing user-facing divergence (C++ class-local aliases)

Even though the *generated* artifacts diverge by language convention,
the **user-facing code** (what a designer reads and writes in
non-generated regions) can be made nearly identical across SV and C++
by hiding the C++ template machinery behind class-local aliases.

The mechanism: the generated templated base class establishes
`using` aliases and `static constexpr` aliases for every
parameterizable name it needs. The user-edited derived class
re-imports those names so they're directly visible without
`<Config>` or `Config::` qualification. Inside member function
bodies, the user writes bare names.

This applies **only to parameterized types and parameterizable
constants** — the ones carrying `<Config>` / `Config::`. A plain type
(no parameter reference) needs no alias and no `using` re-import: it is
already a bare name in a shared include and is referenced directly.
Same for a plain constant. The aliasing exists purely to strip the
template qualification that only parameterized names carry.

#### What's possible in C++

1. **Class-local type aliases hide `<Config>`.**

   ```cpp
   template<typename Config>
   class ipBase : public sc_module {
   public:
       using ipDataT     = ::ipDataT<Config>;
       using ipMemAddrT  = ::ipMemAddrT<Config>;
       using ipMemSt     = ::ipMemSt<Config>;
       // ...
   };
   ```

2. **Class-local constant aliases hide `Config::`.**

   ```cpp
   template<typename Config>
   class ipBase : public sc_module {
   public:
       static constexpr auto IP_DATA_WIDTH     = Config::IP_DATA_WIDTH;
       static constexpr auto IP_MEM_DEPTH      = Config::IP_MEM_DEPTH;
       static constexpr auto IP_NONCONST_DEPTH = Config::IP_NONCONST_DEPTH;
       // Derived values composed from the aliases above
       static constexpr auto IP_DATA_WIDTH_X2  = IP_DATA_WIDTH * 2;
   };
   ```

3. **The user-edited derived class re-imports the names.**

   C++ two-phase name lookup means names inherited from a templated
   base are *dependent* in the derived class and require
   re-importation or `this->` qualification. The generator emits the
   re-imports in a generated block at the top of the derived class so
   the user doesn't write them:

   ```cpp
   template<typename Config>
   class ip : public ipBase<Config> {
   public:
       // GENERATED_CODE_BEGIN --template=classDecl  (existing region)
       using typename ipBase<Config>::ipDataT;
       using typename ipBase<Config>::ipMemAddrT;
       using typename ipBase<Config>::ipMemSt;
       using ipBase<Config>::IP_DATA_WIDTH;
       using ipBase<Config>::IP_MEM_DEPTH;
       using ipBase<Config>::IP_NONCONST_DEPTH;
       using ipBase<Config>::IP_DATA_WIDTH_X2;
       // GENERATED_CODE_END

       // ... user code uses bare names ...
   };
   ```

#### Side-by-side: what the user sees and writes

**SV** (inside the module body; user-editable region):

```sv
module ip
import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
) (...);
    // GENERATED_CODE_BEGIN --template=moduleInterfacesInstances  (existing region)
    typedef logic[IP_DATA_WIDTH-1:0] ipDataT;
    typedef struct packed { ipDataT data; } ipMemSt;
    localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;
    // GENERATED_CODE_END

    ipDataT lastData;
    always_comb begin
        n_lastData = lastData;
        if (ipDataIf.push) begin
            n_lastData.data = ipDataIf.data.data;
            if (IP_DATA_WIDTH > 64) begin
                // ... wide-data handling
            end
        end
    end
endmodule
```

**SystemC** (inside the derived class; user-editable region):

```cpp
template<typename Config>
class ip : public ipBase<Config> {
public:
    // GENERATED_CODE_BEGIN --template=classDecl  (existing region)
    using typename ipBase<Config>::ipDataT;
    using typename ipBase<Config>::ipMemSt;
    using ipBase<Config>::IP_DATA_WIDTH;
    using ipBase<Config>::IP_DATA_WIDTH_X2;
    // Templated interface ports get an auto reference alias (see below)
    // so the user writes the bare name with no this->.
    push_ack_if<Config>& ipDataIf;   // bound to ipBase<Config>::ipDataIf_
    // GENERATED_CODE_END

    ipDataT lastData;
    void process() {
        auto n_lastData = lastData;
        if (ipDataIf.push) {
            n_lastData.data = ipDataIf.data.data;
            if (IP_DATA_WIDTH > 64) {
                // ... wide-data handling
            }
        }
        lastData = n_lastData;
    }
};
```

The shapes are very close. The C++ user writes:
- The same bare names for types (`ipDataT`, `ipMemSt`) and constants
  (`IP_DATA_WIDTH`, `IP_DATA_WIDTH_X2`).
- The same bare names for templated interface ports (`ipDataIf`, no
  `this->`), because the generator emits an auto reference alias for
  each templated inherited port — the trailing-underscore + reference
  pattern described in the next subsection. This is the adopted
  approach, not optional.
- `void process()` / method bodies instead of `always_comb` — a
  fundamental language difference, not a divergence cost.

Outside the user-facing code, the *generated* artifacts still
diverge: the SV emitter writes typedefs inside the module body, the
C++ emitter writes templated `using` aliases in a shared include. But
the user-edited code is symmetric.

#### Caveats

- **Inherited *data* members (e.g. templated interface ports)** would
  otherwise require `this->` (they are dependent names under C++
  two-phase lookup, unlike inherited types/static constants which are
  re-imported via `using`). The adopted fix is the auto reference alias
  — trailing-underscore storage in the base plus a reference member in
  the derived class — so the user writes the bare name. See "Hide
  `this->` via trailing-underscore + reference aliases" (Q11).
- **Cross-block type references.** If block A's code references a
  type owned by block B (e.g. a connection payload), the C++ side
  resolves through `Config` naturally (`Bblock<Config>::someType`)
  but the user-facing code wants a short name. The generator would
  emit a using alias for that cross-block type. SV handles block-local
  parameterized declarations by emitting them in each parameterized
  block that uses them; channel boundary adaptation remains Q9.
- **Generated boilerplate volume.** The base class declares one
  `using` / `static constexpr` per parameterizable name; the derived
  class re-imports each one. For a block with many parameterizable
  values that's a sizable generated block — but it's mechanical and
  hidden in `GENERATED_CODE_*` markers. Users don't write or
  maintain it.
- **Cross-class consumers** (free functions, helpers outside the
  class) — *moot (2026-05-29):* these do not exist. All user-facing
  code lives in the block's own class, so there is no consumer that
  needs the underlying `<Config>` / `Config::` forms.

#### Hide `this->` via trailing-underscore + reference aliases

The remaining C++-ism (`this->` for inherited non-static data
members) can be eliminated cleanly by adopting a naming convention
in the generated code:

- **Inherited storage** in the templated base class carries a
  trailing underscore (e.g. `ipDataIf_`). This is the *real* member
  — the `sc_in`, `sc_signal`, etc. that the SystemC kernel binds.
- **User-facing aliases** in the templated derived class drop the
  underscore (`ipDataIf`). Each alias is a reference member bound in
  the constructor initializer list to the corresponding underscored
  base member.

Because the names differ (`ipDataIf_` vs `ipDataIf`), there's no
member-shadowing-base-class warning. The two identifiers occupy
different name-lookup positions cleanly: the underscored name is
the storage, the non-underscored name is the user-facing handle.

Sketch:

```cpp
template<typename Config>
class ipBase : public sc_module {
public:
    // GENERATED_CODE_BEGIN --template=baseClassDecl  (existing region)
    // inherited storage carries a trailing underscore
    push_ack_if<Config>           ipDataIf_;
    apb_if<Config>                regs_;
    sc_signal<ipDataT<Config>>    lastData_;

    ipBase(sc_module_name name)
        : sc_module(name),
          ipDataIf_("ipDataIf"),     // user-facing SC name (no underscore)
          regs_("regs"),
          lastData_("lastData") {}
    // GENERATED_CODE_END

    // All other generated code that interacts with the base class
    // (regs handler wiring, top-level instantiation, etc.) uses the
    // underscored names directly.
};

template<typename Config>
class ip : public ipBase<Config> {
public:
    // GENERATED_CODE_BEGIN --template=classDecl  (existing region)
    using typename ipBase<Config>::ipDataT;
    using typename ipBase<Config>::ipMemSt;
    using ipBase<Config>::IP_DATA_WIDTH;
    // User-facing names (no underscore) bound to the inherited storage.
    push_ack_if<Config>&          ipDataIf;
    apb_if<Config>&               regs;
    sc_signal<ipDataT>&           lastData;
    // GENERATED_CODE_END

    ip(sc_module_name name)
        : ipBase<Config>(name),
          // GENERATED_CODE_BEGIN --template=constructor --section=init  (existing region)
          ipDataIf(ipBase<Config>::ipDataIf_),
          regs(ipBase<Config>::regs_),
          lastData(ipBase<Config>::lastData_)
          // GENERATED_CODE_END
    {}

    void process() {
        // User-facing code uses bare names; no this->, no shadow,
        // and the SC name in waves is still "ipDataIf" because the
        // base constructor passed that to the kernel.
        if (ipDataIf.push) {
            auto n = lastData;
            n.data = ipDataIf.data.data;
            lastData = n;
        }
    }
};
```

##### Why this works cleanly

- **No `-Wshadow` warning.** The base member is `ipDataIf_`, the
  derived reference is `ipDataIf`. Different identifiers, no
  shadowing.
- **SystemC kernel name is unaffected.** The `sc_in` / `sc_signal`
  constructor takes a string literal (`"ipDataIf"`) that becomes
  the kernel-visible name in waveform dumps, hierarchical names,
  and tracing. The C++ identifier (`ipDataIf_`) is independent.
  Users see the same name in debug output as in their code.
- **Generated code path is uniform.** Any other generated emitter
  that needs to interact with the base class (regs handler, top-
  level wiring, port binding) uses the underscored names. There's
  one rule: "internal generated code uses underscored names;
  user-facing aliases drop the underscore."
- **Reference cost is negligible.** A reference is at most one
  pointer at the implementation level and is typically elided by
  the compiler when the binding is visible at the call site.

##### Side-by-side, final shape

Same SV / SystemC comparison as the previous subsection, but with
the SystemC `this->` clutter actually eliminated:

**SV** (inside the module body; user-editable region):

```sv
ipDataT lastData;
always_comb begin
    n_lastData = lastData;
    if (ipDataIf.push) begin
        n_lastData.data = ipDataIf.data.data;
        if (IP_DATA_WIDTH > 64) begin
            // ...
        end
    end
end
```

**SystemC** (inside the derived class method body; user-editable region):

```cpp
ipDataT lastData_local;            // module-local sc_signal alias / register
void process() {
    auto n_lastData = lastData;
    if (ipDataIf.push) {
        n_lastData.data = ipDataIf.data.data;
        if (IP_DATA_WIDTH > 64) {
            // ...
        }
    }
    lastData = n_lastData;
}
```

The user code shapes are nearly identical. The remaining differences
are the unavoidable language ones (`void process()` vs `always_comb`;
assignment semantics on signals).

##### Scope of the underscore convention

*Resolved (2026-05-29): selective — templated ports only.* The
convention applies **only** to templated interface ports (the
`isParameterizable` ports). Membership is trivial to test: a port gets
the underscored-storage + reference-alias treatment iff it is
`isParameterizable`. Every other base-class member keeps its bare name.

Because templated ports are an entirely new feature (they do not exist
yet), scoping the convention to them produces **zero generator noise**
in existing output — no current generated member is renamed.

##### Constraints that justify this design

This trick only needs to apply to **inherited members in templated
classes that are user-exposed**. Two observations:

1. Non-parameterized types and constants don't need the alias
   pattern at all (no `<Config>` / `Config::` clutter; they're
   already bare names in includes).
2. All non-user-facing interaction with the base class is generated.
   The internal generated code can use whatever convention is
   convenient (underscored names work fine; they're not visible to
   end users).

Together these mean the convention only adds boilerplate where it
*replaces* user-visible asymmetry. There's no cost for non-templated
or non-user-facing paths.

#### Migration

The existing SystemC code in `ip_test` uses `Config::IP_MEM_DEPTH`
directly in user-facing code (e.g. `ip.cpp` line 33-49). Moving to
the class-local-alias pattern would change the user-visible style
across all SystemC examples — another migration cost on top of the
YAML restructuring.

### Migration

YAML migration is now small: `ipParameters` stays, and `blocks.B.params`
stays the existing name list. The new validation requires:
- moving derived/computed entries out of `ipParameters` into
  `constants:` because `ipParameters.constants` is reserved for
  externally exposed param-backing constants (e.g. `ip_test`'s
  `IP_DATA_WIDTH_X2`);
- keeping API-facing non-constant declarations, such as types, in
  `ipParameters` when they are part of the externally exposed IP API;
- declaring every block param in `ipParameters.constants` (e.g.
  `ip_test`'s `IP_NONCONST_DEPTH` gains an `ipParameters` entry with
  `value`/`maxValue`, where `maxValue` ≥ its worst-case variant binding);
  and
- the consumed-check passing: every `ipParameters.constants` entry has
  one or more consuming block params. Multiple blocks may consume the
  same exposed parameter.
The larger migration cost is in the emitters (SV module-scope rework,
SystemC user-facing aliasing), not the YAML.

## Execution plan

This execution plan is now **historical** for C1-C3 and current only for
the C3.6 residual. The stages below record the Q3 sequence
(YAML/parser → SystemC emission → SV emission), the implemented working
tree status, and the remaining static-validation handoff.

This supersedes the SV items **S1** and **S2** in
`plan-development-ordering.md`: S1 (omit parameterizable symbols from the
package) becomes part of stage **C3**; S2 (per-instance package generation)
is dropped in favor of module-local parameterized declarations.

### Progress

| ID | Status | Notes |
|----|--------|-------|
| **C1** | **done** | C1.1/C1.2/C1.2b/C1.4a/C1.5/C1.6 complete. The one remaining coverage item — eval-derived-const-referenced-in-RTL (the `evalCoupled` path) — is **deferred with C4** by decision (2026-06-04); the `evalCoupled` branch already implements the deferral (holds such decls out of the block-local set), so this is the intended end-state, not a gap. See "Implementation status (2026-06-03)" |
| **C2** | **done (2026-06-08)** | SystemC user-facing bare names achieved. **Design divergence from the C2.1/C2.2 sketch:** the `this->`-on-inherited-ports problem is solved by `using <Base>::<port>;` re-imports in the derived class (`classDecl.py`), **not** by the trailing-underscore storage + reference-member aliases the plan body sketched. A using-declaration on an inherited non-static data member is valid C++ and makes the bare name usable without `this->`, which is simpler than the underscore/reference scheme; baseClassDecl ports keep their plain names. C2.3 (class-local `using NAME = NAME<Config>;` type aliases + `static constexpr` param aliases) and C2.4 (regenerated `ip_test`) are as designed. Verified: `make clean && make db && make gen && make run` → `No error`; both variants (`uIp0` width 8, `uIp1` width 70) exercise the templated path and `ip.cpp` user code uses bare `ipDataIf`/`IP_DATA_WIDTH` (no `this->`/`Config::`). Residual `Config::` appears only in generated init-list/body regions (`constructor.py`), which is outside the user-facing-divergence goal |
| **C3** | **implemented in working tree** | SV: package filter + module-local `isParameterizable` symbols; cross-variant adapter (Q9 resolved). **C3.1 done (2026-06-05):** package skips every `isParameterizable` constant/type/struct (incl. eval-derived). **C3.2 done (2026-06-05):** general module-local path in `moduleInterfacesInstances.py` emits each parameterized block's `parameterizedDecls` as module-local typedefs/structs (`ip`/`ipLeaf`/`src`); `ip`/`ipLeaf`/`src`/`ipRegs` Verilator-elaborate cleanly. **C3.3 done (2026-06-05):** general-block module params + module-local decls verified — `ip_top` elaborates both `ip` parameter variants, `src`, `ipRegs`, and the `memory_dp` instances with zero errors. **C3.4 done (2026-06-05):** field-wise widening removed from `ip.sv`'s user region (direct `n_lastData = ipDataIf.data` now that module-local types size both sides; `src.out0`→`ip.ipDataIf` is a matched connection); `ip` lints clean in a matched harness. **C3.5 done (2026-06-05):** container declares non-param boundary types/structs/interfaces in YAML (`ip_top.yaml`); SV `ip_top` lints fully clean with no emitter change; added a producer (out) shape to `push_ack_port_thunker.h` so the symmetric two-thunker C++ path builds — `make run` `No error`. **2026-06-08:** producer shape + naming cleanup generalized to all six remaining thunkers (`rdy_vld`/`req_ack`/`apb`/`axi_read`/`axi_write`/`lmmi`); all seven compile via `proto/model` `make step7` (beyond `ip_test` needs, no generator change). **C3.8 + C3.7 done (2026-06-08):** The `regr_ip_test` regression first revealed `make all VL_DUT=1` did not build — the generated cosim wrappers referenced parameterized boundary structs (`ipDataSt`/`srcOut0St`/`srcOut1St`) that C3.1 removed from the package and made module-local, unresolvable at wrapper scope. **C3.8** fixed the wrapper template (`module_hdl_wrapper.py` now emits each variant's `parameterizedDecls` module-locally at wrapper scope), and **C3.7** then ran as the runtime gate: the regression hdl matrix was extended to 10 `--vlInst` targets (every Verilatable instance, incl. the nested Q10 bridge variants) and `make regr` is **11/11 PASS**. **Residual:** C3 remains incomplete only for C3.6 static validation; do not reopen completed C3.1-C3.5/C3.7/C3.8/C3.R work |
| **C4** | **superseded** | Variant-aware eval re-emission (Q4) is handed off to `plan-eval-symbolic-emission.md` as the active owner. Current handoff there: E4 **implemented in working tree**; E5 partially **implemented in working tree** with firmware C **deferred**; E6 **design only** if still in C4 scope |

#### Implementation status (2026-06-03)

Done and verified on branch `feature/116-parameterized-types` (`examples/ip_test`
`make db`+`make gen` green; generated `ipRegs.sv`/`ip_package.sv`/`ipConfig.h`
byte-identical to pre-validation baseline — parser-only, no emission change):

- **C1.1 done.** `_captureIpParametersConstants` records each `ipParameters.constants`
  entry into a per-file dict `self.ipParametersConstants[yamlFile][name]`
  (`name`, `context`, `constantKey`, `maxValue`). Called from
  `_process_ipParameters` after the `constants` sub-section is processed.
- **C1.2 done — but split per a design refinement (see below).** The linkage is
  now validated as **row-level validators plus a file-level orphan-only check**,
  not one file-level method.
  - *Row level* — `_post_validateBlockParamBacking`, a `post(validateBlockParamBacking)`
    on the block `params` sub-table: each param must resolve (via `lookupInScope`
    on `constants`) to a same-name constant that is `isParameterizable`. Rejects a
    pure/unbacked param and a param colliding with a plain non-parameterizable
    `constants:` entry.
  - *File level* — `_validateIpParametersLinkage` reduced to **orphan only**: every
    captured `ipParameters` constant must be consumed by ≥1 same-file block param
    (consumption read from `blocksparams.paramKey`). This empty-set detection is the
    one genuinely aggregate, `ipParameters`-unique fact, so it stays at file level.
  - *Design note:* a declarative `_validate: section: constants` on `param` is **not
    possible** — the schema FK framework only targets **flat** sections and
    `constants` is context-scoped (non-flat). Hence the lookup lives in the `post`.
    The `consumers` field from the C1.1 capture was dropped (orphan check derives
    consumption from `paramKey`).
- **C1.2b done — at row level.** `_post_validateVariantBindingSizing`, a
  `post(validateVariantBindingSizing)` on the `parameters.variants` sub-table:
  per binding row, the backing const's `maxValue` ≥ bound value. Backing located
  via the row's `blockParamKey` (qualified to the block's declaring file). Reports
  the exact binding row (e.g. `ipVariants.yaml:10`). Runs during parsing, ahead of
  `calcAddresses`.
- **C1.5 done.** `examples/ip_test/arch/yaml/ip.yaml`: `IP_DATA_WIDTH_X2` moved to
  `constants:` (eval-derived, no consumer); `IP_NONCONST_DEPTH` added under
  `ipParameters.constants` (`value: 24, maxValue: 24`); block-param comment updated.
- **Supporting fix (not a numbered item): flat-list line numbers.**
  `_scalarSeqItemLc` + updates to `processSubTable`'s scalar-list and
  `singleEntryList` branches recover each element's position from the parent
  `CommentedSeq` (`seq.lc.item(index)`), since ruamel attaches `lc` to collection
  nodes, not scalar leaves. Block-param errors now report a real line (e.g.
  `ip.yaml:169`) instead of `?`. Generic to all flat-list sections; `make gen`
  unchanged.

Negative cases verified to fire: orphan const, unbacked param, non-parameterizable
backing, variant binding exceeding `maxValue`.

- **C1.4a done.** `deriveParameterizedDeclSets()` runs immediately after
  `calcBlockConfigInfo()` in `projectCreate`. It recovers the type/struct →
  parameter dependency graph from the persisted `*Key` edges (`types.width*Key`;
  `structuresvars.varTypeKey`/`subStructKey`/`arraySizeKey`), classifies each
  referenced constant (backing → contributes its key to `paramSet`;
  parameterizable-but-unbacked → marks the declaration eval-coupled; plain →
  nothing), and computes a per-declaration `(paramSet, evalCoupled)` via a
  memoized, cycle-guarded closure (`typeInfo`/`structInfo`). It asserts the
  derived "`paramSet` non-empty or `evalCoupled`" agrees with the parser's
  `isParameterizable` per declaration (mismatch = hard generator-bug error).
  Per block with `isParameterizable = 1`, it selects parameterizable decls that
  are visible in `yamlContext[block._context]`, not eval-coupled, and whose
  `paramSet ⊆ block param keys`; topo-orders them (`_topoOrderParameterizedDecls`,
  types/sub-structs before the structs that use them) and assigns `orderIndex`.
  Persists to a **non-schema** table `blockParameterizedDecls`
  (`blockKey, declKind, declKey, orderIndex`): `DROP/CREATE TABLE`, single
  `executemany` bulk insert, then `CREATE INDEX` on `blockKey`. `getBlockData()`
  reads it via `getBDParameterizedDecls()` — a direct
  `WHERE blockKey = ? ORDER BY orderIndex` query joined to `self.data['types']` /
  `['structures']` for bodies, surfaced as `ret['parameterizedDecls']` (list of
  `{declKind, declKey, body}`); the table is never loaded into `prj.data`.
  Verified on migrated `ip_test`: `ip` → ipDataT, ipMemAddrT (types) then
  ipDataSt/ipCfgSt/ipMemSt/ipMemAddrSt/ipBurstSt (structs); `ipLeaf` and `src`
  likewise; eval-derived `IP_DATA_WIDTH_X2` has no dependent decl so nothing is
  eval-coupled yet; `ipRegs`/`ip_top` (parameterizable but no own params) select
  nothing. (**Superseded for `ipRegs` by C3.R, 2026-06-05:** the handler now
  inherits its parent's params and selects the parent's decl set —
  `ipDataT`/`ipMemAddrT`/`ipDataSt`/`ipCfgSt`/`ipMemSt`/`ipMemAddrSt`/`ipBurstSt`.)
  The agreement assertion was pre-checked against every current-schema
  example DB (`ip_test`, `simple`, `single_router_multi_reg`, `no_ip_simple`) —
  no mismatches. **`make gen` output is byte-identical with vs without C1.4a**
  (controlled regen diff over `rtl/model/base/include/verif/tb`), confirming the
  derivation is non-emitting at this stage; C3 consumes `parameterizedDecls`.

- **C1.6 unit tests done.** `unittest/test_param_const_linkage.py` (registered
  in `run_all_tests.sh` as Suite 18), 5 cases, all passing. Four negatives use
  the subprocess `arch2code.py` harness and assert a clean (traceback-free)
  failure with message substrings: orphan `ipParameters` constant; block param
  with no backing constant; block param backed by a non-parameterizable
  constant; variant binding exceeding the backing `maxValue`. **Finding:** the
  "backing const not marked `isParameterizable`" and "plain `constants:` name
  collision with a block param" done-when bullets are a single validation reached
  two ways (a block param resolving to a same-name non-parameterizable constant),
  so they are one test, not two. The positive case runs `projectCreate`
  in-process and asserts against the DB: one exposed param consumed by two blocks,
  and a parameterizable type + structure referenced **only by hand-written code**
  selected module-local for **both** consuming blocks (`sharedDataT` then
  `sharedDataSt`, `orderIndex` 0/1). This positive case covers two of the three
  `ip_test` coverage gaps (param-used-only-by-user-code and param-shared-by-two-
  blocks) directly in the unit fixture.

**C1 closed; one coverage item deferred with C4 (decision 2026-06-04).** The
`ip_test` expansion for an **eval-derived parameterizable constant referenced in
RTL** (e.g. a type whose width is `IP_DATA_WIDTH_X2`) is the only path that drives
`deriveParameterizedDeclSets`' `evalCoupled` branch and the C3.1 package
discriminator. Parameterized eval is a materially harder problem (variant-aware
re-evaluation, multi-block eval inputs, SV module-local `localparam` emission) and
is **deferred with C4**, so this coverage is deferred with it — not pending C1
work. The `evalCoupled` machinery already routes such declarations out of the
block-local set, which is the correct deferral behavior; when C4 is taken up, this
fixture case and a unit test for the `evalCoupled` path land together. The other
two coverage gaps (param-used-only-by-user-code, param-shared-by-two-blocks) are
covered by `test_param_const_linkage.py`.

**Caveat:** branch `HEAD` does not `make db` on its own (a pre-existing `src.yaml`
error from sibling staged WIP); validation was verified with the working-tree
changes applied. Generated baselines on the branch are stale, so verification used
an isolated migrated-vs-original diff rather than a committed baseline. Nothing is
staged/committed (`builder/base` is a submodule the user manages).

Test base: `examples/ip_test` — migrate YAML in C1, regenerate and verify
in C2/C3. **`ip_test` must be expanded**, because the current fixture does
not exercise several cases the design depends on:
- an eval-derived parameterizable constant **actually referenced in RTL**
  (today `IP_DATA_WIDTH_X2` is defined but unreferenced in `ip.sv`, so the
  C3.1 discriminator and the C4 deferral would go untested);
- a parameterized type used **only by user code** (not by any memory,
  register, or port), which the block-local declaration set must still
  emit;
- a single exposed param **consumed by two blocks** (shared-parameter
  positive case for the consumed-check).

### Atomic work items

| ID | Work item | Touches (generators) | Touches (hand-written / examples) |
|----|-----------|---------------------|-----------------------------------|
| **C1.1** | **DONE (2026-06-03).** Capture `ipParameters.constants` in a per-file dict while `processSingleFile` parses that file (name, context, `constantKey`, `maxValue`). `consumers` field dropped — orphan check derives consumption from `blocksparams.paramKey` | `pysrc/processYaml.py` | none |
| **C1.2** | **DONE (2026-06-03), restructured to row + file level.** Linkage is validated as: (row) `post(validateBlockParamBacking)` on block `params` — param resolves to a same-name `isParameterizable` constant (rejects unbacked param and plain-const collision); (file) `_validateIpParametersLinkage` reduced to **orphan only** — every `ipParameters` const consumed by ≥1 same-file block param. Note: a declarative `_validate` on `param` is impossible (FK framework targets only **flat** sections; `constants` is context-scoped), so the lookup is in the `post`. The "ephemeral param→const reference" / `blocksparams`⋈`constants` discriminator note still applies to C3.1 | `pysrc/processYaml.py` | none |
| **C1.2b** | **DONE (2026-06-03), at row level.** `post(validateVariantBindingSizing)` on `parameters.variants`: per binding row, the backing `ipParameters` const's `maxValue` ≥ that binding's value; backing located via the row's `blockParamKey`. Runs during parsing, ahead of `calcAddresses`. Reports the exact binding row. Closes the second door of latent issue #1 | `pysrc/processYaml.py` | none |
| ~~**C1.3**~~ | *Dropped.* The standalone `_resolveWordLinesConst` shadow fix is subsumed by C1.2: once the collision is rejected and sizing is sourced from the validated reference, the bare-name shadow branch is no longer the load-bearing guard, so "fixing" it would add an unreachable path | — | — |
| **C1.4** | *Resolved (2026-06-02).* Owner is a `projectCreate` post-parse derivation that persists the resolved per-block set. No parser changes for stage 1 (the type/struct→param graph is recoverable from persisted `*Key` edges); const→const eval edges deferred with C4. See "Parameterized declaration set (C1.4 resolution)" | — | — |
| **C1.4a** | **DONE (2026-06-03).** `deriveParameterizedDeclSets()` after `calcBlockConfigInfo()`: classify constants, per-declaration `(paramSet, evalCoupled)` via memoized cycle-guarded closure, agreement-assert against the parser's `isParameterizable`, select per block by visibility ∧ not-eval-coupled ∧ `paramSet ⊆ block params`, topo-order (`_topoOrderParameterizedDecls`). Persists into the **non-schema** table `blockParameterizedDecls` (`blockKey, declKind, declKey, orderIndex`): `CREATE TABLE`, single `executemany`, then `CREATE INDEX` on `blockKey`. `getBlockData()` reads it directly via `getBDParameterizedDecls()` (`WHERE blockKey = ? ORDER BY orderIndex`, joined to `types`/`structures`, surfaced as `ret['parameterizedDecls']`); table not loaded into `prj.data`. `make gen` byte-identical with/without. C3.6 validation (off in-memory `paramSet`) still rides this pass when implemented | `pysrc/processYaml.py` | none |
| **C1.5** | **DONE (2026-06-03).** Migrated `ip_test` YAML: `IP_DATA_WIDTH_X2` moved to `constants:`; `IP_NONCONST_DEPTH` added under `ipParameters.constants` (`value: 24, maxValue: 24`); block-param comment updated. API-facing `ipDataT` kept in `ipParameters.types` | none | `examples/ip_test/arch/yaml/ip.yaml` |
| **C1.6** | **DONE (2026-06-03).** `unittest/test_param_const_linkage.py` (Suite 18 in `run_all_tests.sh`), 5 cases passing: orphan `ipParameters` const, unbacked block param, non-parameterizable backing (this single validation is both "backing missing `isParameterizable`" and "plain-const/param collision"), variant binding `>` backing `maxValue`, and the positive shared-param-two-blocks case (asserted in-process incl. the `blockParameterizedDecls` decl set: shared parameterizable type+struct, user-code-only, module-local in both blocks). Remaining coverage gap: `ip_test` eval-derived-const-referenced-in-RTL (drives `evalCoupled`) | `unittest/` | none |
| **C2.1** | **SUPERSEDED / DONE-equivalent (2026-06-08).** Original sketch (trailing-underscore storage + underscore-free SC name) was **not** implemented. The `this->`-on-inherited-port problem is instead solved by C2.2's `using <Base>::<port>;` re-import, so baseClassDecl ports keep plain names and no underscore storage exists. No separate work item remains | `templates/systemc/baseClassDecl.py` | none |
| **C2.2** | **DONE (2026-06-08).** `classDecl` emits `using <Base>::<param>;` and `using <Base>::<port>;` (bare constants/ports, no `Config::`/`this->`) and `using typename <Base>::<type>;` (bare parameterized types). Reference-member aliases for ports were **not** needed — the using-declaration covers data members directly. `constructor` strips `<Config>` for out-of-line member refs via `bareParameterizedType` | `templates/systemc/classDecl.py`, `templates/systemc/constructor.py` | none |
| **C2.3** | **DONE (2026-06-08).** `baseClassDecl` emits class-local `static constexpr auto <param> = Config::<param>;` and `using <name> = <name><Config>;` for **all** templated types the block carries (uniform, per Q10) | `templates/systemc/baseClassDecl.py`, `templates/systemc/classDecl.py` | none |
| **C2.4** | **DONE (2026-06-08).** `ip_test` regenerated; `ip.cpp` user region uses bare `ipDataIf`/`IP_DATA_WIDTH`. `make run` → `No error` (both variants). Generated init-list/body still emit `Config::` (out of scope for the user-facing-divergence goal) | none | `examples/ip_test/model/`, `examples/ip_test/base/` |
| **C3.1** | **DONE (2026-06-05).** `package.py` skips every `isParameterizable` constant, type, enum, and structure from the package (they move to module scope; SV cannot parameterize packages). No discriminator view: each object already carries `isParameterizable`, so the template filters on `value['isParameterizable']` directly — no `projectOpen` helper, no `blocksparams`/`blockParameterizedDecls` lookup at package time. **Supersedes the earlier "keep eval-derived parameterizable constants in the package until C4" decision:** an eval-derived constant (e.g. `IP_DATA_WIDTH_X2`) is `isParameterizable=1` and is now also skipped. This is harmless today (no RTL references it) and consistent — C4 will emit such values module-local. Verified: `ip_package.sv`/`ipLeaf_package.sv`/`src_package.sv` drop all parameterizable constants/types/structs (incl. `IP_DATA_WIDTH_X2`); non-parameterizable items retained; container/shared packages (`ip_top`/`ipBridge`/`shared_types`) byte-identical. Suite 18 5/5 | `templates/systemVerilog/package.py` | none |
| **C3.2** | **DONE (2026-06-05).** Consume the C1.4 block-local declaration set to emit module-local typedefs/structs for each parameterized block. `moduleInterfacesInstances.py` emits `data['parameterizedDecls']` (empty for non-parameterized blocks/containers) as module-local typedefs/structs right after the port list, sized from the block's module parameters — the same set the package omits (C3.1). The type/struct SV spelling is shared via `package.parameterizedDeclLines()`, which `moduleRegs.section_param_decls` now also calls (reg-handler slice output byte-identical — C3.R preserved). Verified: `ip`/`ipLeaf`/`src` gain their module-local decls; `ip`/`ipLeaf`/`src`/`ipRegs` Verilator-elaborate with no type-resolution errors. The residual `ip_top.sv` errors (container channels typed with child `srcOut0St`/`srcOut1St`) are the Q8/Q9 container-channel boundary — C3.5, not C3.2. Suite 18 5/5. **localparams (eval-derived) remain package-skipped and deferred to C4.** | `templates/systemVerilog/moduleInterfacesInstances.py`, `templates/systemVerilog/moduleRegs.py`, `templates/systemVerilog/package.py` | none |
| **C3.3** | **DONE (2026-06-05).** Emit module `parameter`s from `blocks.*.params` (existing) plus module-local parameterized types/structs used by ports, memories, registers. The general-block slice rides the C3.2 `parameterizedDecls` path (`moduleInterfacesInstances.py`) and the existing parameter emission; the reg-handler slice is C3.R (handler inherits parent params via `postParseRegisterPorts.py`, emits them, parent forwards them on `uIpRegs`). **Verified (Verilator lint-only):** `ip_top` instantiates `ip` twice with distinct parameter sets (`uIp0` width 8 / depths 16,24; `uIp1` width 70 / depths 8,12), plus `src`, `ipRegs` (param-forwarded), and three `memory_dp` instances sized by module parameters — all elaborate with zero errors. The only residual errors are the `ip_top` container-channel `data_t(srcOut0St/srcOut1St)` typing (`ip_top.sv:18-19`), which is the Q8/Q9 boundary owned by **C3.5**, not C3.3. The `ip.sv` field-wise widening workaround removal is **C3.4** | `templates/systemVerilog/moduleInterfacesInstances.py`, `templates/systemVerilog/moduleRegs.py`, `config/postParseRegister*.py` | none |
| **C3.4** | **DONE (2026-06-05).** Regenerated `ip_test` RTL (generated regions already current post-C3.2/C3.3) and removed the field-wise widening workaround in `ip.sv`'s user region. With module-local `ipDataSt`/`ipDataT` now sizing both sides from the instance's `IP_DATA_WIDTH`, the `if (ipDataIf.push)` body collapses from `n_lastData='0; n_lastData.marker=…; n_lastData.data=ipDataT'(…)` to a direct `n_lastData = ipDataIf.data`. The `src.out0`→`ip.ipDataIf` connection is a **matched** parameterized connection — `srcOut0St` and `ipDataSt` are both `{marker, data}` with equal per-variant width (variant0: 1+8) — so no adapter is needed, confirming Q9's "matched connections need no widening." Verified: `ip` Verilator-elaborates clean (`--lint-only`) in a matched harness supplying the module params and a bit-compatible payload type; the edit is preserved across `make gen` (user region). The SystemC model builds and runs (`No error`). Full `ip_top` elaboration remains gated on **C3.5**: the container declares `push_ack_if #(.data_t(srcOut0St))` / `srcOut1St`, and those parameterizable structs left `src_package` at C3.1, so `ip_top.sv` cannot resolve them until the Q9 container-channel boundary type lands. **Note (updated 2026-06-05):** the reg handler (`ipRegs.sv`) is regenerated in its variant-correct shape; its `ipRegs` package collision is cleared by C3.1. | none | `examples/ip_test/rtl/` |
| **C3.5** | **DONE (2026-06-05).** Implemented the Q9-resolved policy. **Resolution differed from the original file list (user decision 2026-06-05): no `intf_gen_utils`/SV-template change and no auto-synthesized types were needed.** The principle: a container that bridges two parameterized instances **declares its own non-parameterized boundary types/structs/interfaces in YAML** (not generator-synthesized) that width-match each connected variant; both instances stay parameterized. (1) **SV** — `ip_top.yaml` now declares `boundaryMarkerT`/`srcOut0BoundaryT`/`srcOut1BoundaryT` + `srcOut0BoundarySt`/`srcOut1BoundarySt` + `srcOut0BoundaryIf`/`srcOut1BoundaryIf`, and the `uSrc→uIp0/uIp1` connections point at the boundary interfaces. The channel is then `push_ack_if #(.data_t(srcOut0BoundarySt))` (concrete, in `ip_top_package`), and the generic `.src`/`.dst` ports bind directly — **full `ip_top` Verilator lint clean with no SV emitter change** (the template already types channels from the connection's YAML interface). (2) **C++** — both connection ends now differ from the non-param channel interface, so `getBDCrossInterfaceBinds` emits **two** thunkers per connection (producer `uSrc→channel`, consumer `channel→uIp`) with **no generator change** (the annotator is already symmetric over ends). The existing `push_ack_port_thunker` only supported a **consumer** (`push_ack_in`) downstream port; added a **producer (out) construction shape** (`push_ack_out_if<UpT>&` + `push_ack_out<DownT>&`, with `thunkOut()` reversing the data flow child→channel). Because `push_ack_channel` is both `in_if` and `out_if` and the child port's `in`/`out` type disambiguates overload resolution, the container's existing wiring `(name, channel, instance->port, name())` resolves to the right constructor — **no `constructor.py`/`classDecl.py` change**. Verified: `make run` reports `No error`; `uIp0`/`uIp1` receive `0xa5`/`0x2a…5a` marker 1 through the two-thunker chain (data + marker survive both adaptations). The C3.4 matched-connection widening removal stands. **Status update (2026-06-08): producer shape generalized across the thunker family.** The `push_ack` producer-shape prototype was first cleaned up for naming consistency (symmetric `thunkIn()`/`thunkOut()`; members `m_up_in_iface`/`m_up_out_iface`/`m_down_channel`; ctor param `block_`; `upInIface`/`upOutIface`), then the same cleanup **and** the producer (out) construction shape were extended to all six remaining thunkers — `rdy_vld`, `req_ack`, `apb`, `axi_read`, `axi_write`, `lmmi` — so the whole family is symmetric for future cross-variant containers. Each `thunkOut()` mirrors its `thunkIn()` by swapping the consumer object (`m_down_channel`), the producer object (`m_up_out_iface`), and the Up/Down conversion direction, adapted per protocol handshake. All seven thunkers compile-instantiate clean via the proto smoke test (`proto/model` `make step7`, which explicitly instantiates every thunker). This generalization is **beyond `ip_test`'s needs** (which require only the `push_ack` producer shape) and introduces **no `ip_test`/generator change**; the six additional headers are submodule edits left unstaged. **Remaining: C3.6** (validation matrix + informative endpoint-parameterization errors). | `interfaces/push_ack/push_ack_port_thunker.h` (producer shape); `examples/ip_test/arch/yaml/ip_top.yaml` (container boundary decls) | `examples/ip_test/rtl/`, `examples/ip_test/model/` |
| **C3.6** | **DONE (2026-06-23).** Static endpoint validation + matrix. `deriveParameterizedDeclSets()` runs `_validateParameterizedConnectionEndpoints()` off the in-memory `paramSet`: for every parameterizable connection it unions the backing params of the interface's parameterizable payload structures and requires each endpoint instance's block (`connectionsends` → `instanceTypeKey`) to supply them, else a fatal, traceback-free error naming the interface, the connection `src -> dst`, the endpoint instance/block, and the missing param(s), with the reason distinguishing an unparameterized block from one parameterized on the wrong param. This encodes the no-level-skipping rule (a block reached through a parameterized interface must itself carry the backing param so the payload sizes in its own module scope). Matrix in `unittest/test_param_const_linkage.py` (7→11 cells): negatives for dst-unparameterized, dst-parameterized-wrong-param (second reason branch), and src-short (both ends checked); positives for both-endpoints-parameterized, a plain interface between plain blocks (no over-fire), and the C3.5 cross-variant non-parameterized boundary channel (skipped, per-leg adaptation is runtime). 11/11 PASS. Negative cases are `unittest` fixtures per direction. Independent of C3.7 | `pysrc/processYaml.py`, `unittest/test_param_const_linkage.py` | targeted test YAML |
| **C3.7** | **DONE (2026-06-08).** Cross-language cosim acceptance for the parameterized boundary — runtime functional verification, distinct from C3.6's static parser validation. With C3.8's wrapper fix landed, the `regr_ip_test` regression now builds and runs green: `make regr` → build phase `make -j all VL_DUT=1` Verilates clean (build session 0:00:25), run session **11/11 PASS, 0 failed**. The `hdl_tests` matrix was extended from 4 to 10 `--vlInst` targets covering every Verilatable instance under `ip_top`: `cosim` (`ip_top`), `boundary` (`uSrc`), `narrow_le64` (`uIp0`, label `param`), `wide_gt64` (`uIp1`, `param`/`wide`), plus the six remaining — `apb_decode` (`uAPBDecode`), `bridge` (`uBridge`), `bridge_driver` (`uBridgeDriver`), `bridge_apb_decode` (`uBridge.uBridgeAPBDecode`), and the nested cross-interface bridge variants `bridge_narrow_le64` (`uBridge.uBridgeIp0`, `param`/`bridge`) and `bridge_wide_gt64` (`uBridge.uBridgeIp1`, `param`/`bridge`/`wide`). Both the narrow (≤64) and wide (>64, width 70) parameterized `ip` variants run green through the model-side thunker into the Verilated SV module, at both the top push_ack boundary and the Q10 cross-interface bridge. This is the end-to-end acceptance gate for the C3 emission chain (C3.2/C3.3/C3.4/C3.5/C3.R), previously signed off only via Verilator lint/elaboration + a model/model `make run`; a Verilated *parameterized* block driven through the boundary is now demonstrated functional. **Note:** the wide `>64` path is covered by the regression's `wide_gt64`/`bridge_wide_gt64` entries, so the originally-planned dedicated `run-vl-ip1` rundir Makefile target was **not** added — the regression JSON supersedes the per-target need. Depends on C3.5 (done) **and C3.8 (done)**; independent of C3.6 | `examples/ip_test/rundir/regr_ip_test.json` | `examples/ip_test/` |
| **C3.8** | **DONE (2026-06-08).** Fixed the cosim wrapper emission for parameterized blocks. `templates/systemVerilog/module_hdl_wrapper.py` now emits each variant's `parameterizedDecls` (module-local typedefs/structs, the same C1.4a/C3.2 set) at wrapper scope, sized by the variant's concrete parameters via a wrapper-scope `localparam`, before the boundary interface declarations — mirroring the in-module emission C3.2 added. Verified in the regenerated wrappers: `ip_variant0`/`ip_variant1`/`src_variantSrc0`/`ipLeaf_variantLeaf0` now declare `ipDataT`/`ipDataSt` (etc.) module-locally (e.g. `ip_variant1`: `localparam IP_DATA_WIDTH = 70;` → `typedef … ipDataT` → `push_ack_if #(.data_t(ipDataSt)) ipDataIf();`), so `import <block>_package::*` no longer needs the parameterizable structs the C3.1 package move removed. The SystemC-side wrapper (`*_hdl_sc_wrapper.h`) needed no analogous change. **Done-condition met:** `make -j all VL_DUT=1` Verilates `ip_variant0`/`ip_variant1`/`src_variantSrc0` with no `Param 'data_t' … isn't a type` / `isn't const` errors, and the `regr_ip_test` regression reaches and passes the run phase (build session done 0:00:25). Depends on C3.5 (done); unblocked C3.7. *Discovered 2026-06-08 by the `regr_ip_test` regression; fixed same day.* (Original task: ~~Fix the cosim wrapper emission for parameterized blocks (blocks C3.7).~~ The Verilator build (`make all VL_DUT=1`) fails because the generated per-variant cosim wrappers (`module_hdl_wrapper` output — `verif/vl_wrap/ip_variant0_hdl_sv_wrapper.sv`, `ip_variant1_…`, `src_variantSrc0_…`) declare the boundary interface using the parameterized boundary struct at **wrapper scope**: `push_ack_if #(.data_t(ipDataSt)) ipDataIf();`. C3.1 moved `ipDataSt`/`srcOut0St`/`srcOut1St` out of `<block>_package` and made them **module-local**, so the wrapper's `import <block>_package::*` cannot resolve them — Verilator reports `Param 'data_t' of 'ipDataIf' ... isn't a type` / `'ipDataSt' isn't const`. The wrapper is variant-specific and already hard-codes the variant's concrete parameter values on the `dut #(.IP_DATA_WIDTH(8)…)` line, so the fix is to emit that block's `parameterizedDecls` (the same C1.4a/C3.2 module-local typedefs/structs), sized by the variant's concrete parameter values, at wrapper scope before the interface declarations — mirroring the module-local emission C3.2 added inside the module itself. Confirm whether the SystemC-side wrapper (`templates/systemc/module_hdl_wrapper.py` → `*_hdl_sc_wrapper.h`) needs the analogous treatment. **Done when** `make all VL_DUT=1` Verilates `ip_variant0`/`ip_variant1`/`src_variantSrc0` clean and the C3.7 regression reaches the run phase. Depends on C3.5 (done); blocks C3.7.*) | `templates/systemVerilog/module_hdl_wrapper.py` | `examples/ip_test/verif/vl_wrap/` (regenerated) |
| **C3.R** | **DONE (2026-06-05). Parameterize the auto-synthesized register handler** so the C3.1 package move does not break it — the reg-handler slice of C3.2/C3.3, scoped and validated by `plan-parameterized-register-decode.md` (hand-written proto `proto/rtl/rtl/reg_decode_mparam.sv`, `make step5`). (1) `synthesiseRegHandler` gives the handler its parent's `params` (`parentParams` from `blocksparams`), so it emits module parameters and `deriveParameterizedDeclSets` selects the parent's decls for it. (2) `moduleInterfacesInstances.py` forwards the parent's params on the reg-handler instance (`uIpRegs #(.IP_DATA_WIDTH(IP_DATA_WIDTH), ...)`). (3) `moduleRegs.py` emits the inherited params, the module-local parameterized typedefs (`parameterizedDecls`), and a `generate`-guarded variant-aware word decode (`$bits`-based width, per-word flops/`_rword` arrays elaborated away for narrow variants) while the worst-case address footprint stays fixed (byte-identical `REG_*`). **Behavior change for ALL reg blocks (user decision, diverges from the proto):** the bus is never stalled and `pslverr` is never asserted — unmapped/ro/absent accesses ACK, unmapped reads return 0. Non-parameterizable registers keep the simple fixed-word shape. **Package collision cleared by C3.1 (done 2026-06-05);** full `ip_test` compile now gated on C3.2/C3.3 (`ip.sv` module-local decls) | `config/postParseRegister.py`, `config/postParseRegisterPorts.py`, `templates/systemVerilog/moduleInterfacesInstances.py`, `templates/systemVerilog/moduleRegs.py` | `examples/ip_test/rtl/ipRegs.sv`, `ip.sv` |

### Dependencies

```
C1.1 -> C1.2 -> C1.6
C1.2 -> C1.5
C1.1 -> C1.2b
C1.1 -> C1.4 -> C1.4a
C1.* (complete) -> C2.*
C1.* (complete) -> C3.*
C3.1 -> C3.2 -> C3.3 -> C3.4
C3.R (reg-handler slice of C3.2/C3.3) DONE; full ip_test compile still -> C3.1
C3.5 (Q9 resolved; SV adapter parallel to the SystemC thunker)
C3.5 -> C3.6 (static validation matrix)
C3.5 -> C3.8 -> C3.7 (C3.8 fixes the cosim wrapper build that C3.7 depends on)
C3.5 -> C3.7 (runtime cosim acceptance; independent of C3.6; gated on C3.8 build)
C4 deferred; do not gate C1–C3
```

C2 and C3 are independent of each other once C1 is done; either order is
allowed. C3.2 has a concrete ownership rule (Q8): each parameterized block
that uses a parameterized type emits the needed local declaration. Q9 is
resolved: matched connections need no widening, deliberate cross-variant
`connectionMaps` adapt via a per-connection SV adapter parallel to the
SystemC thunker, and mismatched endpoint parameterization is a C3.6
validation error. C3.5 is therefore no longer blocked on an open design
question — it is implementation. C3.6 locks the rules down with positive
and negative tests across the relevant permutations and informative
endpoint-parameterization error messages.

### Done-when (verification)

**C1 complete when:**

- `make db` on `examples/ip_test` fails on: orphan `ipParameters` const,
  block param without `ipParameters.constants` backing, backing const not
  marked `isParameterizable`, backing const `maxValue` below a variant
  binding, and a plain `constants:` name collision with a block param.
- `make db` succeeds on migrated `ip.yaml`.
- `make gen` output is **unchanged** from pre-C1 for SV and SystemC
  (parser-only stage).
- C1.6 unit tests pass.

**C2 complete when:**

- Regenerated `ip_test` model/base build (`make` in `examples/ip_test/rundir`).
- User-facing block code can use bare port/type/constant names for
  templated symbols (no `this->` on templated ports; minimized `Config::`
  per Q10 decision).
- No change required to SV RTL in this stage.

The C3 deliverables split into a self-contained part that closes within
this plan and a boundary part that bottoms out in Q9 (still open). Do not
treat C3 as failed because the Q9-blocked part is incomplete.

**C3 (self-contained) complete when:**

- Regenerated `ip_package.sv` contains **no** `isParameterizable` constants,
  types, or structs at package scope. (Superseded 2026-06-05: eval-derived
  parameterizable constants are also skipped — they are `isParameterizable` —
  not kept in the package; see C3.1 and the 2026-06-05 log entry.)
  **DONE via C3.1 (2026-06-05).**
- Regenerated `ip.sv` declares module-local types sized from module
  `parameter`s for blocks whose parameterized declarations are
  self-contained (no cross-instance width mismatch). **DONE via C3.2
  (2026-06-05):** `ip.sv`/`ipLeaf.sv`/`src.sv` declare their `parameterizedDecls`
  module-local right after the port list; `ip`/`ipLeaf`/`src`/`ipRegs`
  Verilator-elaborate with no type-resolution errors. The earlier
  `Expecting a data type: 'ipDataSt'` failure is cleared. (Full `ip_top`
  elaboration still blocks on the C3.5 container-channel boundary.)
- Regenerated `ipRegs.sv` (the auto-synthesized register handler) is
  variant-correct: inherited params, module-local parameterized typedefs,
  `generate`-guarded variant word decode, fixed worst-case address map.
  **DONE via C3.R** (`plan-parameterized-register-decode.md`); its package-type
  collision is cleared by C3.1 (done 2026-06-05).
- `ip_test` RTL sim/lint path still passes for the self-contained blocks.
  *(Status 2026-06-05: SystemC model builds and runs — `No error`; the
  self-contained parameterized leaves `ip`/`ipLeaf`/`src`/`ipRegs` now
  Verilator-elaborate cleanly after C3.2. Full-design RTL co-sim from `ip_top`
  is gated on the C3.5 container-channel boundary — `ip_top.sv` still types its
  `out0`/`out1` channels with the child `src` block's `srcOut0St`/`srcOut1St`,
  which left the package at C3.1 and need the Q9 non-templated boundary type.)*

**C3 (cross-variant boundary part) status (Q9 resolved):** C3.4/C3.5,
C3.6, C3.7, C3.8, and C3.R are **implemented in working tree** and verified
as logged below. C3 has no remaining work; the validation bullets below
are the C3.6 criteria, now satisfied (see the 2026-06-23 log entry).

- **DONE (C3.4 + C3.5, 2026-06-05).** The field-wise widening TODO in `ip.sv`
  is removed: matched parameterized connections size both sides identically by
  construction (no widening). The cross-boundary case is handled by a
  container-declared non-parameterized boundary interface/struct (YAML, not a
  package max-width struct): SV binds the generic ports to it directly (no SV
  adapter needed), and C++ adapts each end via the `push_ack_port_thunker`
  (consumer shape pre-existing; producer "out" shape added in C3.5).
- Validation errors, with informative messages, when a parameterized
  interface connects an endpoint (parent port or child block) that lacks
  the parameterization needed to match the interface — naming the
  interface, the endpoint, and the missing parameter(s). This subsumes the
  no-level-skipping rule (a param cannot be reached one level down by
  skipping a level).
- Positive and negative tests cover parameterized vs non-parameterized
  parent/sub-block/interface/channel combinations.

**C3.8 (cosim wrapper emission fix) — DONE 2026-06-08:**

- ✅ `make -j all VL_DUT=1` Verilates the per-variant cosim wrappers
  (`ip_variant0`, `ip_variant1`, `src_variantSrc0`) with no
  `Param 'data_t' … isn't a type` / `isn't const` errors.
- ✅ The wrappers source the parameterized boundary types module-locally
  (sized by each variant's concrete parameters via a wrapper-scope
  `localparam`), not from `<block>_package`, consistent with the C3.1
  package move and C3.2's module-local emission.
- ✅ The `regr_ip_test` regression progresses past the build phase into the
  run phase (the runtime result is then C3.7's gate, not C3.8's).

**C3.7 (cross-language cosim acceptance) — DONE 2026-06-08:**

- ✅ The narrow parameterized `ip` variant0 instance (`--vlInst ip_top.uIp0`),
  driven through the model-side thunker boundary, runs green with the
  payload/marker integrity asserts holding across the SystemC↔SV boundary.
- ✅ The wide variant1 (`--vlInst ip_top.uIp1`, width 70 — the `> 64` path)
  runs green; the wide payload survives the boundary intact. Covered as the
  regression `wide_gt64`/`bridge_wide_gt64` entries rather than a dedicated
  `run-vl-ip1` Makefile target.
- ✅ The hdl matrix was extended to all 10 Verilatable instances under
  `ip_top` (incl. the nested Q10 cross-interface bridge variants
  `uBridge.uBridgeIp0`/`uBridgeIp1`); `make regr` reports **11/11 PASS**.
- This is runtime functional verification, distinct from C3.6's static parser
  validation; it is the end-to-end acceptance gate for the C3 emission chain
  (C3.2/C3.3/C3.4/C3.5/C3.R), previously signed off only via Verilator
  lint/elaboration and a model/model `make run`.

**C4 (superseded here / active owner elsewhere):** variant-aware eval for
parameterized `constants:` with `eval` is tracked in
`plan-eval-symbolic-emission.md`. Current handoff: E4 is **implemented
in working tree**, E5 is partially **implemented in working tree** with
firmware C **deferred**, and E6 remains **design only** if still in C4
scope.

### Relationship to `plan-development-ordering.md`

| Ordering doc | This plan |
|--------------|-----------|
| F1–F3, A1–A3 | Prerequisite — assumed **done** |
| T1–T7, M1–M5 | Prerequisite for C2 — assumed **in progress / done** on branch |
| **S1** | Absorbed into **C3.1** |
| **S2** | **Dropped** — use module-local types, not per-instance packages |
| T9 | Independent — factory registration not part of C1–C3 |

## Latent issues this document is tracking

1. **Silent under-allocation when a non-parameterizable constant shadows
   a block param.** Demonstrated above; not detected by any current
   check. *Resolved by the required-and-checked overlap (2026-05-29): a
   block param must be backed by a parameterizable `ipParameters`
   constant, so a non-parameterizable shadow is rejected by validation
   rather than silently mis-sized. A second door — a backing const whose
   `maxValue` is set below its variant bindings — is closed by the C1.2b
   `maxValue` ≥ variant-binding assertion, run as a per-file step in the
   file that declares the `parameters:` bindings.*
2. **SV package types at wrong width for non-default variants.**
   Documented by the `ip.sv` TODO; worked around with field-wise
   widening. *Resolution path (C3 + Q9, 2026-06-02): parameterizable types
   move to module scope sized from the module's own parameters, so matched
   connections are correct by construction; deliberate cross-variant
   connections adapt via the per-connection thunker/adapter rather than a
   package max-width type. The widening TODO closes in C3.5.*
3. **No first-class YAML declaration of the
   parameterizable-constant ↔ block-param linkage.** The relationship
   exists by name coincidence only. *Resolved by the design: the
   same-name overlap is required and checked bidirectionally, with
   `ipParameters` constants captured in a file-level dict to drive the
   one-or-more-consumer check.*
4. **The shadow lookup in `_resolveWordLinesConst` is load-bearing for
   correct sizing but is not documented as such**, making it a tempting
   target for "simplification" that would break `ip_test`. *Superseded by
   C1.2 (2026-05-29): once linkage is validated and sizing is sourced from
   the stored param→const reference, the bare-name shadow branch is no
   longer load-bearing, so C1.3 (a standalone fix to it) is dropped.*
5. **A hand-written `isParameterizable: true` on a plain `constants:`
   entry with no `eval` and no backing block param is not rejected.** Such
   an entry is parameterizable with no per-instance source, which is
   meaningless under the design's rules, and it would slip through the
   C3.1 package discriminator as if it were eval-derived. *Deferred
   (2026-05-29): noted but intentionally not handled now. Closing it would
   be a C1.2 rejection rule; until then the discriminator assumes the only
   parameterizable non-backed constants are eval-derived.*

## Decisions to make

Decided items are marked *Resolved*; genuinely open items are marked
*Open* and state the remaining choice.

**Q1. Is the param/constant overlap intentional or accidental?**  
*Resolved (2026-05-29):* Intentional and required. A block param **is**
an `ipParameters`-defined constant of the same name. The overlap is the
linkage and is validated (see Q2). It is no longer treated as
accidental.

**Q2. Where does the
parameterizable-constant ↔ block-param linkage live?**  
*Resolved (2026-05-29):* In the same-name overlap, made explicit and
checked by a parser `_validate` step. `ipParameters` is processed early
and its constants are captured into a file-level dict. Validation is a
consumed-by-block relationship: every `ipParameters.constants` entry must
be consumed by one or more block params (error on an orphan), and every
block param must be backed by an `ipParameters` const of the same name
(pure params dropped — see Q6). The file-level `_validate` step also
asserts the backing const carries `isParameterizable` and resolves the
qualified param→const reference for parse-time validation only — that
reference is ephemeral parser state for error detection and is not
persisted. The `maxValue` ≥ worst-case variant-binding check is **not** part
of this file-level step: the `parameters:` variant bindings are an instance
definition that may be authored in a different file, so that assertion runs
where the bindings are declared (a `processSingleFile` step in that file,
ahead of `calcAddresses` — see C1.2b). The SV emitter (C3.1) tells a
block-param-backing parameterizable const apart from an eval-derived one
through normal `projectOpen` view creation (`blocksparams` joined to
`constants`), since the `constants` DB row does not persist the `eval`
expression.
Multiple blocks may consume the same exposed parameter. The param identity
is orthogonal to the `isParameterizable` emission flag.

**Q3. How is the work sequenced?**  
*Resolved (2026-05-29):* Three stages — **C1** YAML/parser, **C2**
SystemC emission, **C3** SV emission. See **Execution plan** for work
IDs, file touch lists, dependencies, and done-when criteria. C2 and C3
are independent once C1 is complete. C3.2 uses the Q8 rule that only
parameterized blocks emit parameterized local declarations; C3.5 is now
implementation (Q9 resolved): the SV cross-variant adapter parallel to the
SystemC port-thunker, with matched connections needing no widening.

**Q4. What about computed constants that depend on params (the `eval`
case, e.g. `IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2`)?**  
*Decided in shape; eval handling deferred (2026-05-29):* There is **no
separate `derived:` concept**. These are ordinary `constants:` entries
with `eval`, stamped `isParameterizable` exactly as today when their
inputs are parameterizable. *Verified (2026-05-29):* the stamping does
fire — `processYaml.py:4769`-`4817` walks each `$TOKEN` and sets
`isParameterizable` plus an auto-derived `maxValue`; `ip_test.db` shows
`IP_DATA_WIDTH_X2` as `isParameterizable=1, maxValue=256`. The
consequence for C3: ~~the package filter must **not** blanket-skip
`isParameterizable` constants, or it would drop the eval value out of SV
while this work is deferred.~~ *(Superseded 2026-06-05: C3.1 does blanket-skip
all `isParameterizable` constants, including eval-derived ones. This is
harmless because no RTL references `IP_DATA_WIDTH_X2` today, and it is the
consistent end-state — C4 emits these module-local. The discriminator described
next is no longer needed.)* Such a constant cannot live in `ipParameters`
(no block param consumes it, so the orphan check rejects it there); it is
forced into `constants:`. ~~C3.1 keeps eval-derived parameterizable
constants in the package — discriminated by the absence of a block-param
backing, equivalently by living in `constants:` rather than being an
`ipParameters` exposed param — until this lands.~~ The deferred problem is purely *eval
emission* in SV: once a computed constant's inputs are module-scoped
per-instance values, it must be emitted as a module-local `localparam`
(re-evaluated per instance) rather than a single package value. The SV
emission strategy for `eval` under module scope is the deferred issue.
In C++, the target shape is a `Config<Variant>` member or `constexpr`
derived from `Config`, but variant-aware re-evaluation remains deferred
with the rest of this eval work. Open sub-point: if a computed value's
inputs come from parameters in multiple blocks, no single SV module can
compute it — that case needs a rule, but is deferred with the rest of
eval handling.

**Q5. Where may a block param's backing constant be declared?**  
*Resolved (2026-05-29):* Only in `ipParameters`. A param's
parameterizable backing constant lives there (same name as the param). A
plain `constants:` entry must not share a name with a block param.

**Q6. What is the YAML shape, and how is it parsed?**  
*Resolved (2026-05-29):* `ipParameters` is retained and authored before
`types`/`blocks` (see the candidate YAML under "Design → YAML model").
It is processed by the existing `_process_ipParameters` handler;
additionally its constants are captured into a file-level dict, and the
bidirectional consumed-check (Q2) runs. `blocks.B.params` stays the
existing flat name list (no new schema, no parse-twice, no embedding).
**Externally configurable pure block params are dropped**: every such
block param must be declared in `ipParameters.constants` (same name).
Today's `IP_NONCONST_DEPTH` becomes a normal `ipParameters` constant
with a `value`/`maxValue`, and its worst-case wordLines sizing comes
from that entry. The Q2 check requires one or more consumers for every
`ipParameters.constants` entry; shared exposed parameters are legal.

**Q7. What is the migration story for existing user YAML and
existing user-edited C++?**  
*Resolved for templated ports / SC aliasing (2026-05-29):* The
templated-ports feature is entirely new code. There are **no migration
issues** for it — the only churn is within this branch as it lands.
Existing generated output is untouched because templated ports do not
exist yet (the trailing-underscore convention applies only to them).

*Tentative for the YAML side (new-code framing, 2026-05-28):* this work
is treated as new code. There's no contract to preserve existing
user-edited SystemC source files in their current shape; existing
arch2code examples (e.g. `ip_test`) will be re-generated to the new
style. Decisions still open:
- YAML side: hard break with example migration, or soft break (warn
  for one release, then hard-error)?
- A migration tool that transforms old YAML to the new shape is
  optional. Worth doing only if there are user projects outside the
  examples that would be impractical to migrate by hand.
- Existing SystemC user code in examples gets regenerated under the
  new naming convention (bare-name aliases instead of
  `Config::PARAM` / `<Config>` clutter). User-editable regions get
  re-styled; generated regions get regenerated.

**Q8. What about types and structures that depend on parameterizable
values today?**  
*Resolved with Q9 coupling (2026-05-29):* A parameterized type or
structure can only be emitted inside a block module that is itself
parameterized. Any parameterized block that uses a parameterized type or
structure emits its own module-local declaration for that type/structure
inside the block module. There is no cross-module typedef sharing for
parameterized declarations; package scope keeps only non-parameterized
symbols.

Detection remains the existing `isParameterizable` propagation: a type
or structure is parameter-dependent when its width, array size, or field
dependencies transitively reference an `isParameterizable` value.
The block-local list is selected from the constants, types, and
structures visible through the block's include contexts, filtered to
declarations whose parameter dependencies are satisfied by the
parameters available on this block. It is not enough to scan only the
types/structs/constants referenced by memories, registers, ports, or
connections: a parameterized declaration may exist only for user code,
and future parameterized `eval` support will add more dependency paths.
C1 must therefore decide whether this set is computed and persisted in
`projectCreate` or assembled in `projectOpen` from persisted dependency
facts. Whichever owner is chosen, `getBlockData()` consumes the result
as a block-local view input. Declarations whose dependencies are not
satisfied by the block's params cannot be emitted in that block; the
design must either parameterize the block or route through a
non-parameterized boundary shape.

Instance containers do not use a child block's parameterized typedef as
the channel type. They create separate non-templated channel/interface
types for the channel instance; boundary adaptation between that channel
shape and the child block's module-local type is Q9. If a sub-block
needs direct access to a parameterized type or structure, that sub-block
must itself be parameterized; otherwise it can only interact through a
non-parameterized boundary/channel shape.

This is a validation rule, not just an emission preference: if a
sub-block has a connection defined with a parameterized interface and
that connection requires the sub-block to see the parameterized
type/structure directly, the sub-block must be parameterized. A
non-parameterized sub-block in that position is an error.

**Q9. What is the interaction with `connectionMaps` / cross-block
interfaces that carry parameterizable structs?**  
*Resolved (2026-06-02).* A parameterized interface implies a
parameterized parent **and** a parameterized child: both endpoints must
carry the parameterization needed to match the interface's parameterized
types. This is a validation rule:

- **Both endpoints must match the interface's parameterization.** If a
  parameterized interface connects an endpoint (parent port or child
  block) that lacks the parameterization required to realize the
  interface's parameterized type, that is an error. The error message must
  be informative enough to debug it directly — naming the interface, the
  endpoint block, and the parameter(s) the endpoint fails to supply, so
  the user knows which block needs which parameterization.
- **Matched connections need no widening.** When both endpoints are
  parameterized to match, the module-local parameterized types on each
  side have identical widths by construction, so there is no field-wise
  widening at the boundary. The `ip.sv` widening TODO closes for these
  matched connections.
- **Deliberate cross-variant connections use the port-thunker, not package
  widening.** When a container connects two children of different variants
  (different parameterizations on each leg, e.g. `ipBridge`), each leg's
  interface matches its own child's variant and the existing port-thunker
  mechanism adapts the payloads between them (already implemented in
  SystemC via `intf_gen_utils` + `constructor`/`classDecl`; the SV
  equivalent adapter is the residual implementation in C3.5). This is an
  explicit per-connection adapter, not a package-scope max-width type.

Net effect: Q9 is no longer an open design question. The remaining work is
implementation — the SV adapter parallel to the SystemC thunker (C3.5) and
the positive/negative validation matrix over parameterized vs
non-parameterized parent / child / interface / channel permutations
(C3.6), with informative endpoint-parameterization errors.

**Q10. How aggressive should the C++ class-local aliasing be?**  
*Resolved (2026-06-02): alias all templated items identified.* Every
templated item a block carries (its `isParameterizable` types,
structures, constants, and ports) gets the class-local alias / `using`
re-import — uniform, not usage-filtered. This avoids tracking which
parameterizable names the user-facing code happens to reference and keeps
the generated surface predictable. If the resulting boilerplate becomes a
problem in practice, narrowing to only-what's-used can be revisited later.
- ~~Aliasing for cross-block types~~ — *moot (2026-05-29).*
  Cross-class consumers do not exist, so there is no cross-block alias
  case to handle. A block's user-facing code only references its own
  parameterizable types/constants.

**Q11. Adopt the trailing-underscore + reference-alias pattern to
eliminate `this->` entirely?**  
*Resolved — adopt (2026-05-29).* Templated interface ports get the auto
reference alias so the user writes the bare name (`ipDataIf.push`, not
`this->ipDataIf.push`). The pattern is described under "Hide `this->`
via trailing-underscore + reference aliases" and is reflected in the
canonical SystemC side-by-side example. Cost (new code, no compatibility
impact):
- One trailing-underscore declaration per inherited base member
  (replacing the bare-name declaration).
- One reference declaration per user-facing alias in the derived
  class.
- One constructor initializer per user-facing alias.

Because this is new code (no existing user code to migrate; existing
arch2code examples will be re-generated to the new style), the
boilerplate has no compatibility cost. Sub-decisions resolved
(2026-05-29):
- **Scope of the underscore convention** — *selective: templated ports
  only.* The trailing-underscore convention applies **only** to
  templated interface ports, which are themselves all-new (they do not
  exist yet), so this adds **zero generator noise** to existing output.
  Membership is trivial to determine: a port is templated iff it is
  `isParameterizable`. All other base members keep their bare names.
- **Cross-block alias handling** — *moot.* Cross-class consumers do not
  exist, so a derived class never needs to alias another block's
  member. The pattern is confined to a block's own templated ports.

Note: types, structs, and interfaces already inherit the
`isParameterizable` attribute, so the machinery to decide which ports
are templated is already present in the model.

**Q12. How is the param→types→interfaces→ports ordering cycle resolved
without multi-pass parsing?**  
*Resolved (2026-05-29):* By keeping `ipParameters`. Authored before
`types`/`blocks`, it materializes the param-constants up front (its
original purpose), so a single forward pass works with no hoist and no
deferred eval. This is the decisive reason the embed-in-block direction
was dropped. See "Design → Section ordering."

## Iteration log

This section captures decisions and open questions as the discussion
evolves.

### 2026-05-28 — initial framing

Captured the SV collision, the parser latent bug, the four
categories, and the V1-V4 / E1-E3 option grid. No decisions yet.

### 2026-05-28 — leading direction settled to V2 + E1

User input:

> Considering the SV shape, we will likely want to end up with module
> parameters fed via instancing with module-scoped const/types/and
> structs - I think that SV does not accept parameterized packages —
> unless I'm mistaken. The module params are intended to be the block
> level params. We likely do not want name collision here with const.

SV-package-non-parameterization confirmed (IEEE 1800-2017). E2 and E3
ruled out as long-term destinations. E1 + V2 recorded as the leading
direction with the caveat that "likely" means leading, not committed.

Doc updated to:
- Add the "SV constraint that forces the shape" section.
- Mark V2 + E1 as the leading row in the interaction table.
- Sketch the YAML, parser, SV emitter, and SystemC implications under
  "Implications of the V2 + E1 direction."
- Add Q6 (YAML shape detail), Q7 (migration story), Q8 (parameter-
  dependent types), Q9 (cross-block parameterized structs).
- Tentatively answer Q1, Q2, Q4, Q5 against V2 + E1 (marked as
  "tentative" pending final commitment).

Still open: Q3 (sequencing), Q6, Q7, Q8, Q9. The sequencing question
is the next decision blocker.

### 2026-05-28 — output shape, SV-as-sentinel, intentional divergence

User input:

> I want to iterate on the output shape a little, as there is potential
> for divergence between SV and SystemC, and it is desirable to
> minimize this. The C++ config struct and templated structures and
> types is a good path, and the C++ structure and type object are
> naturally more complex due to the size mapping issues. The SV shape
> is the sentinel shape, and the limitation of packages being
> parameterizable is going to inform this. It seems for SV we will
> likely need module scoped types, and structures derived from the
> parameters. Eventually this will include calculated consts. This
> probably means that SV and C++ will diverge some, and the contents
> of the includes/packages will need to diverge. SV will have module
> scope definitions and C++ will have parameterized include
> (modules). All non-parameterized types and constants will be
> similar, but the location of the parameterized ones will differ.

Captured in doc:
- New subsection "SV is the sentinel shape" under "SV constraint that
  forces the shape." Explicitly states SV is the most constrained
  emitter and the YAML model has to accommodate what SV can express.
- New subsection "Cross-emitter divergence is intentional" with a
  category-by-emitter table showing where each YAML category emits in
  SV vs C++. Non-parameterized rows are similar across emitters; the
  parameterized rows differ by language convention (SV: module-scope;
  C++: templated include).
- Expanded "SystemC emitter" implications to acknowledge the existing
  templated-types-in-includes pattern is already correct.
- Noted the asymmetry of work: SystemC emitter is minor; SV emitter is
  substantive.
- Q4 refined: derived parameterizable consts go module-local in SV
  (with "eventually" qualifier — likely deferred past initial
  migration); C++ already has its convention.
- Q8 / Q9 reframed as the hardest open problem, especially cross-
  module type sharing in SV (parameterized typedefs can't go through a
  package, and SV lacks a clean cross-module typedef-sharing mechanism).

Still open: Q3 (sequencing), Q6 (YAML shape detail), Q7 (migration
story), Q8 (cross-module parameterized types in SV), Q9
(cross-instance parameterized structs in connections). Q8 and Q9 are
now the deepest open problems; sequencing depends partly on how
ambitious we are about resolving them.

### 2026-05-28 — minimize user-facing divergence via C++ class-local aliases

User input:

> Thinking further, we want the code for both implementations to look
> as similar as possible — so that users looking at both
> implementations see similar shape. I am wondering if in C++ we can
> hide some of the templating noise. We could have class level
> typedefs that alias to the more complex templated types and maybe
> something similar for the templated consts. Is this possible?

Answer: yes. The C++ pattern is class-local `using` aliases for
templated types and `static constexpr auto` aliases for `Config::`
constants. The user-edited derived class re-imports them via `using`
declarations so member function bodies can use bare names. The only
residual C++-ism is `this->` for inherited data members.

Captured in doc:
- Renamed "Cross-emitter divergence is intentional" to "Generated-
  artifact divergence is intentional, user-facing divergence should
  be minimized." Reframed the work asymmetry to call out that SystemC
  emitter changes are moderate (not minor) because the user-facing
  style changes.
- New subsection "Minimizing user-facing divergence (C++ class-local
  aliases)" covering:
  - The base-class-aliases + derived-class-re-imports pattern.
  - A SV / SystemC side-by-side showing nearly identical user-facing
    shape under the pattern.
  - Caveats: `this->` for non-static inherited members, cross-block
    type references, generated boilerplate volume, helpers outside
    the class scope.
  - Migration cost: existing SystemC examples (`ip_test`) would need
    re-styling.
- New Q10 on how aggressive to be with C++ aliasing (alias only what
  the block uses vs everything; cross-block type aliasing strategy).

Still open: Q3, Q6, Q7, Q8, Q9, Q10. Q8 / Q9 (cross-module
parameterized types/structs in SV) remain the deepest open problems.

### 2026-05-28 — shadowing reference members to hide `this->`

User input:

> For C++ can we create class local auto pointer or references
> initialized in the constructor to hide the this-> stuff?

Answer: yes. The pattern is to declare reference members in the
derived class with the **same names** as the inherited members,
bound in the constructor initializer list. C++ name lookup finds the
derived reference before climbing to the base, so unqualified use in
member function bodies resolves to the reference and `this->`
disappears. The references are aliases (one pointer at the
implementation level, often elided), so the runtime cost is small.

Captured in doc:
- New subsection "Optional: hide `this->` via shadowing reference
  members" under "Minimizing user-facing divergence." Includes a
  worked example showing the base class with data members, the
  derived class with same-named reference members + initializer
  list, and the user-facing body using bare names.
- Trade-offs listed (then revised in the next iteration log entry):
  - Pro: closes the last visible C++-ism; SV and SystemC
    user-facing code becomes naming-uniform.
  - Pro: SystemC kernel semantics work transparently (references
    alias inherited objects).
  - Con: more generated boilerplate (one reference + one
    initializer per inherited member the user might touch).
  - Con: derived-shadowing-base is an uncommon pattern with a
    learning cost for anyone debugging the generated layer.
  - Caveat: compiler `-Wshadow` warnings will fire on the
    shadowing.
- "Caveats" subsection updated to reframe `this->` as the default
  C++-ism rather than "unavoidable."
- New Q11 on whether to adopt the pattern.

Still open: Q3, Q6, Q7, Q8, Q9, Q10, Q11. Q8 / Q9 remain the
deepest open problems. Q10 / Q11 are the C++-side aesthetic
decisions; orthogonal to Q8 / Q9.

### 2026-05-28 — refine to trailing-underscore + reference alias, no shadowing

User input:

> As this is all for new code, we already know that this all only
> applies for templated interfaces. We could use a qualifier in the
> base class — e.g. trailing _ for templated interfaces — and all
> the other users of the base class is all generated code. Anywhere
> we need to expose the port to users we use the reference trick,
> and all the internal generated code just deals with it.

Cleaner refinement of the previous iteration. The base class storage
members carry a trailing underscore (`ipDataIf_`); the derived class
declares reference aliases without the underscore (`ipDataIf`).
Different identifiers, no name shadowing, no `-Wshadow` warning.
Internal generated code uses the underscored names; user-facing
code in the derived class uses bare names. The trick applies only
to inherited members in templated classes that get exposed to user
code.

Captured in doc:
- Renamed "Optional: hide `this->` via shadowing reference members"
  to "Hide `this->` via trailing-underscore + reference aliases."
  Worked example updated to show `ipDataIf_` in base, `ipDataIf` as
  derived reference.
- New "Why this works cleanly" subsection covering:
  - No shadow warning (different identifiers).
  - SystemC kernel name unaffected (the SC name string passed to
    the base constructor is `"ipDataIf"` — no underscore —
    regardless of the C++ identifier).
  - Uniform internal-code rule: "underscore = storage; no
    underscore = user-facing alias."
  - Reference cost negligible.
- New "Scope of the underscore convention" subsection laying out
  uniform-vs-selective application; uniform is the likely default.
- New "Constraints that justify this design" subsection capturing
  the user's observation that the trick only applies to user-exposed
  templated inherited members — non-parameterized stuff doesn't
  need it, and internal generated code doesn't care about
  underscores.
- Q7 (migration) revised with the "new code" framing: no contract
  to preserve existing SystemC user-edited source style; examples
  get regenerated under the new naming convention.
- Q11 updated: leaning toward adopting the trailing-underscore
  pattern; sub-decisions on uniform-vs-selective scope and
  cross-block alias handling.

Still open: Q3, Q6, Q7, Q8, Q9, Q10. Q11 is now "leaning yes."
Q8 / Q9 (cross-module parameterized types/structs in SV) remain
the deepest open problems.

### 2026-05-29 — IP-as-API framing, remove ipParameters, dual materialization

User input:

> Conceptually the IP top level yaml should be considered as the IP
> 'API'. This means any structures, types or interfaces should all be
> exposed here. It should be as self contained as possible and omit as
> much implementation details as possible. A likely shape would include
> block, const, types, structs and interfaces defines that are needed by
> the ip user yaml. There is likely a ip implementation yaml that
> instantiates lower level instances and any other stuff includes this
> 'api' yaml as well. We will likely want to create a skill that captures
> intent and shape at a later point. I think the cleanest fix is probably
> to remove ipParams and embed this info into the block definition —
> similar but different to the example. I am thinking that some of the
> behaviour is similar to today. The params will still become 'constants'
> from a yaml processing perspective — but in the c++ module and SV
> package they will diverge. SV will not render isParameterizable
> elements in the package. These will move to be module specific in SV.
> C++ will stick with the templated + using scheme already fleshed out.
> The user facing schematics are important here the goal being that the
> code looks as similar as possible.

Clarifications gathered:
- Internal model is **dual materialization**: a block param creates both
  a `blockparams` row (as today) and a `constants` entry processed as a
  constant. Exact schema expression is undecided.
- The IP API-yaml vs implementation-yaml split is **future skill
  guidance**, not part of this plan's mechanics.
- The shadow-lookup / under-allocation latent bug likely dissolves
  because the param and its constant become the same thing; flagged as
  needing more thought.

Captured in doc:
- Status leading direction rewritten: `ipParameters` removed, param
  metadata embeds in the block definition, dual-materialization internal
  model, emission diverges on `isParameterizable` (SV package skips them;
  C++ keeps templated + `using`).
- New section "IP top-level YAML as the IP 'API' (conceptual, future
  skill)" capturing the API/impl framing without committing mechanics.
- Parser section rewritten: dual materialization replaces the earlier
  "shadow lookup goes away / stamping becomes unnecessary" sketch.
  `isParameterizable` is explicitly reinstated as load-bearing.
- Q2 refined: linkage disappears user-facing but becomes a
  materialization rule internally.
- Q6 updated: `ipParameters` removal decided; the dual-entry schema
  expression is now the central undecided schema question.
- Latent issue #1 annotated as likely-resolved-by-construction (needs
  more thought).

Still open: Q3, Q6 (esp. dual-entry schema expression), Q7, Q8, Q9, Q10.
Q11 leaning yes. Q8 / Q9 remain the deepest open problems.

### 2026-05-29 — block `params:` reuses the constants schema

User input:

> I want the params section in block to look exactly like a constants
> section - we will reuse the constants schema. After consts handling -
> with isParameterizable set (similar to how we handled ipParameters) we
> will then add the appropriate params. Still need some thought on how we
> iterate on this - as it might want to be entry at a time. But this is
> the general direction.

This answers the central dual-entry schema question from the prior
iteration. The block `params:` section is authored in exactly the
constants shape and reuses the constants schema — no new schema. It is
processed through the constants pipeline with `isParameterizable`
stamped (the same `_ipParametersActive` mechanism `ipParameters` uses in
`_process_ipParameters`, `processYaml.py:5934`), then the `blockparams`
entries are added.

Grounding in existing code: `_process_ipParameters` flips
`_ipParametersActive = True` and routes each sub-section through
`processSection` so per-entry handlers stamp `isParameterizable=True` as
each entry is processed (line 5934). The comment at line 5946 notes the
stamping is done entry-at-a-time on purpose, "preserving finalized
referents when later entries reference them" — which is exactly the
iteration-granularity concern the user flagged.

Captured in doc:
- Status internal-model bullet updated: block `params:` reuses the
  constants schema; processed as constants with `isParameterizable`
  stamping, then `blockparams` added.
- Parser section updated with the reuse-constants-schema mechanism, the
  `_ipParametersActive` grounding, and a new bullet calling out
  iteration granularity (whole-section vs entry-at-a-time) as the open
  mechanical question.
- Q6 dual-entry item marked decided-in-direction (reuse constants
  schema); new sub-item added for iteration granularity (leaning
  entry-at-a-time, not settled).

Still open: Q3, Q6 (iteration granularity), Q7, Q8, Q9, Q10. Q11
leaning yes. Q8 / Q9 remain the deepest open problems.

### 2026-05-29 — cleanup: remove options, drop `derived:`, params are constants

User input:

> lets clean up the plan. where we have defined path - lets remove
> options. If items are not resolved, clarify the option. Remove the
> derived: section, these should just be in the constant section.
> Resolving the 'eval' handling is still a deferred issue. Params are
> purely constants that are exposed for the instancer to set. We will use
> isParameterizable for everything else - as currently implemented.

Cleanup pass, not a new design decision. Changes:
- Removed the `Categories of "fix"` section entirely (V1–V4 / E1–E3
  options and the interaction table). The decided path now lives in the
  Status and `Design` sections; the option history is preserved only in
  this log.
- Renamed "Implications of the V2 + E1 direction" to `Design` and
  dropped the "exploratory; nothing committed" hedging.
- **Removed the `derived:` concept.** Computed values are ordinary
  `constants:` entries with `eval`, stamped `isParameterizable` as
  today. The candidate YAML, the SV-emitter section, and the divergence
  table were updated to drop `derived:`.
- **`eval` handling is explicitly deferred** (Status + Q4): the open
  problem is how a computed constant whose inputs are module-scoped
  per-instance values is emitted in SV (module-local `localparam`,
  re-evaluated per instance).
- **Params reframed as "constants exposed for the instancer to set"**:
  authored in the constants shape, reusing the constants schema; the
  only new construct is the block `params:` section. Everything else
  parameterizable uses `isParameterizable` exactly as implemented today.
- Marked Q1, Q2, Q5 *Resolved*; Q4 and Q6 *Decided in shape* with the
  remaining open bits (eval handling; iteration granularity) called out.
  Q3 rewritten without the dead V1 near-term-tightening option.
- Latent issue #3 annotated as resolved by the design.

Still open: Q3 (sequencing), Q4 (eval emission, deferred), Q6
(iteration granularity), Q7, Q8, Q9, Q10. Q11 leaning yes. Q8 / Q9
remain the deepest open problems.

### 2026-05-29 — params parsing: parse twice, custom blockparams handler

User input:

> review the plan a remove references to discards decision options. I
> think for params parsing we should probably just parse twice. First
> with constants schema, then with param schema. For now - lets just use
> the param schema.yaml exactly as is and add a custom section handler
> for blocksparams. I dont think adding schema abstraction for this makes
> sense at the moment.

Settles the parsing mechanism for the block `params:` section. A custom
section handler (analogous to `_process_ipParameters`) parses the
section content twice: first through the constants schema (materializing
`isParameterizable` constants via `_ipParametersActive`), then through
the existing param schema, used exactly as-is (materializing the
`blockparams` entries). No new schema and no schema abstraction for the
embedded-param shape now.

Grounding: today `blocks.B.params` is a flat list of names
(`config/schema.yaml:251`, `param: key`), and `parameters:` binds
variants against the derived `blocksparams` table
(`config/schema.yaml:291-314`). The second parse reuses that existing
param schema; the first parse adds the constants materialization.

Captured in doc:
- Status param bullet rewritten to the parse-twice + custom-handler
  mechanism; the stale iteration-granularity note removed.
- Parser section rewritten: the dual-materialization bullet is now the
  parse-twice handler; the separate iteration-granularity bullet is
  folded in (parse-twice supersedes whole-section-vs-entry-at-a-time
  because the constants pass already finalizes referents per entry).
- Q6 retitled "...and how is it parsed?" and updated to the parse-twice
  decision; the iteration-granularity open item is closed.
- Confirmed the body carries no discarded-option references (V1–V4 /
  E1–E3 and the shadowing-reference approach survive only in this log).

Still open: Q3 (sequencing), Q4 (eval emission, deferred), Q7, Q8, Q9,
Q10. Q11 leaning yes. Q8 / Q9 remain the deepest open problems.

### 2026-05-29 — parse-ordering cycle (params before types) surfaced

User input:

> Ok, we still potentially have an ordering problem that we need to
> resolve. blocks contains params and ports. ports reference interfaces,
> which may depend on parameterized values. This ordering problem is
> partially what ipParameters solved originally. Multi pass parsing is
> definitely something I want to avoid if possible.

Grounding confirmed in code: sections are processed in authored order in
a single forward pass (`processSingleFile`,
`for section, sectData in sections.items()`), and width `eval` is
parse-time (the `types` `post(validateTypeWidth)` handler resolves via
`_parserResolver`). In `ip.yaml`, `ipParameters` is authored first so
`IP_MEM_DEPTH` exists before `types: ipMemAddrT { widthLog2minus1:
IP_MEM_DEPTH }` is processed. Embedding params in `blocks` (which is
authored last because ports reference interfaces) breaks that ordering.

Captured in doc:
- New "Design → Section ordering / single-pass constraint" subsection
  laying out the cycle (block.params → types/structures → interfaces →
  block.ports), the parse-time-eval fact, and three candidate
  resolutions (hoist param-constants pass / defer eval to post-parse /
  keep an early top-level params section). Hoist is leaning.
- Parser section gets an ordering-constraint bullet pointing to it.
- New Q12 (the current blocker), and a note that it constrains the
  parse-twice decision: pass 1 (constants) must run early; pass 2
  (blockparams) runs during normal block processing.

Still open: Q3, Q4 (deferred), Q7, Q8, Q9, Q10, Q12 (current blocker).
Q11 leaning yes. Q8 / Q9 remain the deepest emission problems; Q12 is
the deepest parsing problem.

### 2026-05-29 — reversal: keep `ipParameters` (V1 + E1), required+checked overlap

User input:

> I am questioning my decision to eliminate ipParameters. I think the
> change is that when we process ipParameters - I also want to capture
> any constants defined here in a new file level dict and ensure that
> any const defined here IS consumed by params and generate error if its
> not. This is going to a major change to the current plan direction.

Plus clarifications: a block param *is* an `ipParameters`-defined
constant (same-name overlap), orthogonal to `isParameterizable`; the
overlap scheme is unchanged but required and checked for
`ipParameters.constants`; derived/computed consts move to regular
`constants:`; a param's backing parameterizable const may come from
`ipParameters.constants` only. Other `ipParameters` sub-sections remain
available for externally exposed API declarations.

This **reverses** the embed-in-block / parse-twice / dual-materialization
/ V2-forbid-overlap direction. The plan now lands on **V1 + E1**: keep
the overlap, validate it strictly, and let emission divergence
(`isParameterizable` → module scope, a SV language constraint) fix the
collision.

The decisive reason for the reversal is the parse-ordering cycle
(former Q12): `ipParameters` exists to materialize param-constants
before `types`/`blocks` in a single forward pass. Removing it
reintroduced the cycle and forced a hoist or deferred eval; keeping it
avoids both.

Captured in doc:
- Status rewritten to the V1 + E1 direction; superseded note added.
- Design → YAML model rewritten: `ipParameters` retained (param-backing
  consts only), plain/derived consts in `constants:`, param = same-name
  `ipParameters` const.
- Design → Parser rewritten: early `ipParameters` processing + new
  file-level dict + bidirectional consumed-check; param identity
  orthogonal to `isParameterizable`.
- Design → "Section ordering" updated to show keeping `ipParameters`
  resolves the cycle (Q12 closed).
- Q1 (overlap intentional/required), Q2 (linkage = validated overlap),
  Q5 (backing const only in `ipParameters`), Q6 (no parse-twice; open
  sub-question on pure params) rewritten. Q12 resolved.
- Latent issues #1 and #3 re-annotated; Migration subsection reduced to
  a small YAML change plus the emitter rework.

Still open: Q3 (sequencing), Q4 (eval emission, deferred), Q6 (pure
params allowed?), Q7, Q8, Q9, Q10. Q11 leaning yes. Q8 / Q9 (cross-module
parameterized types/structs in SV) are again the deepest open problems
now that the parsing/ordering question is resolved.

### 2026-05-29 — drop pure params; plain types need no `using`

Two clarifications:

> a plain type does not need a using reference. I am not sure I
> understand the use case for pure block param. What does it mean?

- **Plain types/constants:** the C++ class-local aliasing applies only
  to parameterized types and parameterizable constants (the ones
  carrying `<Config>` / `Config::`). A plain type needs no alias and no
  `using` re-import — it is a bare include name referenced directly.
  Added an explicit note in "Minimizing user-facing divergence."
- **Pure block param** was explained as `ip_test`'s `IP_NONCONST_DEPTH`:
  a param with no backing constant anywhere, existing only as a
  `blocks.params` name plus per-variant bindings, used solely for
  worst-case wordLines sizing (a deliberate test artifact). Decision:
  **drop the externally configurable pure-param category.** Every
  externally configurable param must be declared in
  `ipParameters.constants`; `IP_NONCONST_DEPTH` becomes a normal
  `ipParameters` constant. The Q2 check is a one-or-more-consumer
  relationship, not strict 1:1.

Captured in doc: Q6 resolved (pure params dropped); Q2 tightened to
require at least one block-param consumer; the candidate YAML and
migration note updated to show `IP_NONCONST_DEPTH` as an
`ipParameters` constant.

Still open: Q3 (sequencing), Q4 (eval emission, deferred), Q7, Q8, Q9,
Q10. Q11 leaning yes. Q8 / Q9 remain the deepest open problems.

### 2026-05-29 — constraint: reuse existing templates (no new templates)

User input:

> one note - I dont want to create new templates for this functionality,
> the existing templates should capture the new output

Captured as a hard constraint. The SV module-scope rework and the C++
class-local aliasing must be produced by extending the existing
templates (and the `projectOpen` views that feed them), not by adding
new template files. Added an "Emitter constraint: reuse existing
templates" subsection in Design (before SV emitter) and it applies to
all emitter-side work (Q3, Q8, Q9, Q10, Q11).

### 2026-05-29 — keep the auto reference for templated interface ports

User input:

> make sure we still have the auto reference for the templated interface
> ports the user example still has the this->

The canonical SystemC side-by-side example still showed
`this->ipDataIf`, and the surrounding text wrongly called `this->`
unavoidable. Fixed:
- The example now uses the auto reference alias: a `member-aliases`
  generated block declares `push_ack_if<Config>& ipDataIf;` bound to the
  base's `ipDataIf_`, and the body uses bare `ipDataIf` (no `this->`).
- The "what the user writes" bullet and the Caveats bullet are reframed:
  templated interface ports use the generated auto reference alias; this
  is the adopted approach, not optional.
- Q11 promoted from "leaning yes" to "Resolved — adopt." The
  uniform-vs-selective underscore scope and cross-block alias handling
  remain open sub-decisions.

### 2026-05-29 — reuse existing generated sections, no new section names

User input:

> one note - I dont want to create new templates for this functionality,
> the existing templates should capture the new output
>
> no i mean we already have sections to put additional entries in, use those

The examples invented new `--section=` names (`type-imports`,
`member-aliases`, `member-alias-init`, `module-types`). Those are not
real generated sections. Inspected the generated files to confirm the
existing regions:

- `--template=baseClassDecl` (`base/ipBase.h`) already declares the param
  constants (`const uint64_t IP_DATA_WIDTH;` …) and the interface ports
  (`push_ack_in< ipDataSt<Config> > ipDataIf;`) as bare-named members,
  initialized from `Config::` in the base constructor init list.
- `--template=classDecl` (`model/ip.h`) is the derived class region.
- `--template=constructor --section=init` is the derived constructor init
  list.
- `--template=moduleInterfacesInstances` (`rtl/ip.sv`) is the SV module
  region; `--template=package` is the SV package.

Captured in doc:
- "Emitter constraint" subsection renamed to "reuse existing templates
  *and sections*" and now enumerates the real generated regions each new
  output lands in (no new templates, no new `--section=` names).
- All example code blocks updated to mark the existing regions
  (`baseClassDecl` / `classDecl` / `constructor:init` for C++,
  `moduleInterfacesInstances` for SV) instead of the invented sections.

### 2026-05-29 — sequencing + underscore-scope sub-decisions resolved

User input:

> cross class consumers do not exist. The underscore convention shall
> only be used for templated ports - there will be zero generator noise
> from this as templated ports do not exist yet. It is simple to manage
> - isParameterizable. The templated ports feature is all new code -
> there is no migration issues - except for in this branch. We will do
> this a step at a time, deal with yaml and parser changes. Handle sc
> and sv emission a step at a time. All the types, structs, interfaces
> already inherit the isParameterizable attribute.

Resolutions captured in doc:
- **Q3 (sequencing) → Resolved.** Staged one step at a time: (1) YAML +
  parser (capture + consumed-check), (2) SystemC emission, (3) SV
  emission. The emission steps are independent; both add zero churn to
  existing output because templated ports are new.
- **Q7 (migration) → Resolved for templated ports / SC aliasing.** All
  new code, no migration issues except churn within this branch.
- **Q10 cross-block aliasing bullet → moot.** Cross-class consumers do
  not exist.
- **Q11 sub-decisions → resolved.** Underscore convention is *selective:
  templated ports only*, keyed off `isParameterizable`; zero generator
  noise since templated ports don't exist yet. Cross-block alias
  handling is moot. Added the note that types/structs/interfaces already
  inherit `isParameterizable`, so the templated-port membership test is
  already available.

Still open: Q4 (SV eval emission, deferred), Q8, Q9 (cross-module /
cross-instance parameterized types & structs in SV — the deepest open
problems), and the one remaining Q10 bullet (alias-only-what's-used vs
alias-everything).

### 2026-05-29 — API scope, shared consumers, eval deferral, view ownership

User input:

> I dont see an issue with ipParameters being more than constants. The
> rule is - if something is declared an ipParameter constant then all
> consts must be referenced by blocks - can be more than one, and
> multiple blocks can consume the same parameter. Eval of
> parameterized constants are deferred. ipParameters shall only contain
> parameters that are exposed externally. When we tackle SV emission we
> will handle the isParameterizable package and module issues together.
> We should probably think more about how getBlockData and
> getContextData work as there is some now overlap of roles.

Clarifications captured in doc:
- `ipParameters` remains a general IP API-surface container; it may
  contain API-facing non-constant declarations. The consumed-by-block
  validation applies specifically to `ipParameters.constants`.
- The consumed check is one-or-more, not strict 1:1. An
  `ipParameters.constants` entry must have at least one consuming block
  param, and multiple blocks may consume the same exposed parameter.
- Eval-derived parameterizable constants remain deferred. The current
  plan records the target C++/SV shape but does not try to solve
  variant-aware eval recomputation in the parser/YAML stage.
- SV package filtering and module-local emission are treated as one SV
  emission effort, not split into independent partial fixes.
- A new "View ownership (`getContextData` vs `getBlockData`)" section
  defines context/IP API declarations as context-view owned, block-local
  rendering facts as block-view owned, and shared cross-object
  derivations as owned by `projectCreate` or a narrow `projectOpen`
  helper.

### 2026-05-29 — Q8 resolved: block-local SV parameterized declarations

User input:

> any block having a parameterized type will need a local declaration.
> It is expected that instance containers will have a separate
> non-templated type that is used to create the channel instance.

Resolution captured in doc:
- **Q8 → Resolved with Q9 coupling.** A parameterized declaration can
  only be emitted in a parameterized block. Any parameterized block that
  uses a parameterized type or structure emits its own module-local
  declaration. There is no cross-module typedef sharing for
  parameterized declarations.
- Instance containers use separate non-templated channel/interface
  types for channel instances; adapting between the container channel
  shape and child module-local type is now the remaining Q9 problem.
- If a sub-block needs direct access to a parameterized type/structure,
  it also needs to be parameterized.
- The block-local declaration set is a projection from context-visible
  constants/types/structures through the block's include contexts,
  filtered by the parameters exposed on that block. This is the bridge
  between context-owned declarations and block-owned SV local emission.
- The owner of that projection is not yet settled. It may belong in
  `projectCreate` because the set is non-trivial: declarations may be
  for user code only (not referenced by memories/registers/ports), and
  future parameterized `eval` will add more dependency paths. C1.4 makes
  this an explicit ownership decision before implementation.
- Execution plan C3.2 is no longer blocked on Q8. C3.5 remains blocked
  on Q9's propagation and boundary/channel adaptation policy.

### 2026-05-29 — parameterized-interface validation matrix

User input:

> so if a sub block has a connection that is defined with parameterized
> interface but the sub block is not parameterized that is an error. We
> will need to ensure we have positive and negative test cases for the
> permutations and combinations

Resolution captured in doc:
- A non-parameterized sub-block connected through a parameterized
  interface that requires direct access to parameterized types is a
  validation error.
- C3.6 adds a positive/negative validation matrix covering
  parameterized and non-parameterized parent, sub-block, interface, and
  channel ownership permutations.

### 2026-05-29 — consumed-scope check runs per parsed file

User input:

> regarding consumed scope checking. I think this check should be done
> after parsing each file as a step in processSingleFile

Resolution captured in doc:
- `ipParameters.constants` consumed-scope validation is a per-file
  `processSingleFile` post-section step, not a late project-wide sweep.
- The check runs after the file's authored sections have been processed,
  when the file-local `ipParameters.constants` entries and
  `blocks.*.params` rows are known.
- Execution items C1.1 and C1.2 now explicitly capture the per-file dict
  and run the consumed check from `processSingleFile`.

### 2026-06-02 — C1.4 resolved: projectCreate-owned post-parse derivation, no parse capture

Two design questions were settled by inspecting the live `ip_test.db`
schema and rows.

- **Capture.** The type/struct → parameter dependency graph is recoverable
  after parsing from already-persisted qualified `*Key` columns
  (`types.width*Key`, `structuresvars.varTypeKey`/`subStructKey`/
  `arraySizeKey`) plus the `isParameterizable` flags. The only edge not
  persisted is constant→constant (eval), since `constants` stores no `eval`
  string; that edge is needed only for C4 and is deferred with it.
  Conclusion: **no parser changes for stage 1.**
- **Owner and storage.** The per-block set is computed once by a
  `projectCreate` post-parse pass (after `calcBlockConfigInfo()`) and held
  in an **explicit non-schema table** — a deliberate third
  `projectCreate` → `projectOpen` channel alongside schema tables and the
  pickled `config` object, chosen because this derived data is neither
  user-authored nor small enough for a hand-queried pickle. The pass issues
  a direct `CREATE TABLE`, a single `executemany` bulk insert, and a
  `CREATE INDEX` on `blockKey`; `getBlockData()` queries it directly per
  block (`WHERE blockKey = ?`) rather than loading it into `prj.data`.
  `paramSet` stays in-memory because C3.6 validation runs in the same pass.

Captured in doc:
- New "Parameterized declaration set (C1.4 resolution)" subsection under
  View ownership, with the capture conclusion, the three-step derivation,
  the membership rule (resolved Q8 stance) and its accepted unused-typedef
  tradeoff, and the join-table schema.
- View-ownership "Parameterized declaration selection" bullet rewritten
  from "owner still a design decision" to the resolved owner.
- Progress/execution: C1.4 marked *Resolved*; C1.4a rewritten as the
  implementation of the post-parse derivation and the join table.

### 2026-06-02 — Q9 and Q10 resolved

- **Q9 → Resolved.** A parameterized interface implies a parameterized
  parent and child; both endpoints must carry the parameterization needed
  to match the interface, else it is an error with an informative message
  (naming interface, endpoint, missing parameter). Matched connections need
  no field-wise widening (widths match by construction). Deliberate
  cross-variant `connectionMaps` adapt via a per-connection adapter — the
  existing SystemC port-thunker, with an SV equivalent as the residual C3.5
  implementation — not a package max-width struct. Q9 is no longer an open
  design question; C3.5 becomes implementation and C3.6 the validation
  matrix. Updated the Q9 entry, C3.5/C3.6, the C3 done-when, the
  dependencies block, the Q3 note, and the C3 progress row.
- **Q10 → Resolved: alias all templated items.** The C++ class-local
  aliasing is uniform over every templated item a block carries, not
  usage-filtered; revisit only if boilerplate becomes a problem. Updated
  the Q10 entry and C2.3.

This leaves Q4/C4 (variant-aware eval emission) and latent issue #5 as the
only deferred items; C1, C2, and C3 have no open design questions on their
critical paths.

### 2026-06-03 — review feedback: validation timing, reference lifetime, stale note

Worked through external review feedback against the live code and
`ip_test.db`. Resolutions:

- **Param→const reference is parser-ephemeral, not a durable channel.** The
  file-level dict captured during parsing exists only to detect and report
  linkage errors in `projectCreate`; it is not persisted. The SV package
  discriminator (C3.1) re-derives "block-param-backing vs eval-derived"
  through normal `projectOpen` view creation off the persisted
  `blocksparams` and `constants` tables. Corrected the Parser `_validate`
  bullet, the SV-emitter package-filter discriminator, C1.2, and Q2, which
  had over-claimed the reference as "durable" and "consumed by C3.1."
- **Variant-bound sizing check split out of the file-level linkage step.**
  The file-level step validates only that every declared `ipParameters`
  const is consumed by a block param. The `maxValue` ≥ max-variant-binding
  assertion cannot run there because `parameters:` variant bindings are an
  instance definition that may be authored in a separate file (verified:
  `ipVariants.yaml` `include`s `ip.yaml`, so no `parametersvariants` row
  exists when `ip.yaml`'s section loop finishes). Added **C1.2b**: a
  `processSingleFile` step in the file that declares the bindings, run ahead
  of `calcAddresses`. Updated the Parser bullets, C1.2, Q2, latent issue #1.
- **Package-filter wording (item 4) → no prose change (Reading B).** The
  apparent inconsistency is the unmigrated fixture: an `eval` constant
  (`IP_DATA_WIDTH_X2`) must not live in `ipParameters`. The C1.5 YAML
  migration moving it to `constants:` is the fix; the discriminator follows.
- **Latent issue #5 → remains deferred** per direction.
- **Stale note (item 6) → fixed.** "Current YAML model" table row D wrongly
  stated plain constants become per-variant `Config` members; verified
  against `includes.py::includeConstants` that they are emitted as shared
  include `const`s and skipped from the `Config` structs. Corrected row D.

### 2026-06-04 — C1.4a + C1.6 landed; parameterized eval deferred

- **C1.4a implemented and verified.** `deriveParameterizedDeclSets()` +
  `getBDParameterizedDecls()` + the non-schema `blockParameterizedDecls` table,
  per the "Parameterized declaration set (C1.4 resolution)" section. `make gen`
  byte-identical with vs without the pass (controlled regen diff); the
  isParameterizable agreement assertion pre-checked clean against every
  current-schema example DB.
- **C1.6 unit tests landed.** `unittest/test_param_const_linkage.py` (Suite 18),
  5 cases. Recorded the finding that "non-parameterizable backing" and
  "plain-const/param collision" are one validation, not two.
- **Parameterized eval deferred (user decision).** Parameterized eval is a
  materially harder problem (variant-aware re-evaluation, multi-block eval inputs,
  SV module-local `localparam` emission) and stays deferred with **C4**. The lone
  remaining C1 coverage item — an eval-derived constant referenced in RTL, the
  only driver of the `evalCoupled` branch — is therefore deferred with C4, not
  pending C1 work. The `evalCoupled` machinery already holds such declarations
  out of the block-local set (the correct deferral behavior); the fixture case and
  a unit test for that path land when C4 is taken up. **C1 is closed** for its
  in-scope deliverables. Next available work is C2 (SystemC) or C3 (SV), which are
  independent of each other.

### 2026-06-04 — orphan check relocated to a post-parse sweep (C1.2 fix)

- **Defect.** `_validateIpParametersLinkage` ran at the tail of
  `processSingleFile`, i.e. once per `processSingleFile` invocation. That method
  is re-entered mid-parse for synthesized `{types, constants}` subsets of the
  **same** file (encoder expansion at `processYaml.py:5473`; address-enum
  injection at `:3695`). On the encoder re-entry the file's `ipParameters`
  constants are already captured but the consuming `blocks:` section is not yet
  parsed, so the check saw zero consumers and falsely errored
  ("`ipParameters` constant … is not consumed by any block param"), aborting the
  build via `logError`.
- **Fix (Option 2).** The check is now a single project-wide post-parse sweep:
  the tail call was removed from `processSingleFile`, `_validateIpParametersLinkage`
  takes no argument and iterates every file in `self.ipParametersConstants` after
  `processYamls()` completes (called from `projectCreate`). Per-file semantics are
  unchanged — each file's captured constants are still checked against that same
  file's `blocksparams.paramKey`.
- **Supersedes wording elsewhere in this doc.** The earlier descriptions of the
  orphan check as running "per parsed file" and being "idempotent across repeated
  `processSingleFile` calls" (C1.2 row, the 2026-05-29 "consumed-scope check runs
  per parsed file" entry, and the Implementation-status bullet) are superseded by
  this single post-parse sweep; idempotency is moot because the check now runs
  exactly once. No emission change; the row-level validators
  (`_post_validateBlockParamBacking`, `_post_validateVariantBindingSizing`) and the
  capture scaffolding (`_captureIpParametersConstants` / `self.ipParametersConstants`,
  which remains required because `isParameterizable` is a broader set than the
  `ipParameters`-declared set) are unchanged.
- **Verification.** Full `unittest` suite result is identical before and after the
  change (the only failure, `T4.3`, is pre-existing and unrelated, reproducing on
  the pre-edit baseline). Change is unstaged in the working tree; `builder/base`
  staging remains user-managed.

### 2026-06-05 — C3.1 landed: SV package skips `isParameterizable` declarations

First emission change of the C3 stage; `make gen` is no longer byte-identical
for the parameterized contexts (intended).

- **Implementation.** `package.py` skips every `isParameterizable` constant,
  type, enum, and structure (`if value['isParameterizable']: continue`). Every
  object already carries `isParameterizable`, so the template needs no
  discriminator view, no `projectOpen` helper, and no `blocksparams` /
  `blockParameterizedDecls` lookup at package time. (An earlier attempt added a
  `getModuleLocalDeclKeys()` view + a `getContextData` field to keep eval-derived
  constants in the package; that view was removed as unnecessary on user
  direction — see the decision below.)
- **Decision — skip eval-derived too, supersedes the prior "keep in package"
  plan.** An eval-derived parameterizable constant (`IP_DATA_WIDTH_X2`) is
  `isParameterizable=1` and is now skipped from the package along with the
  block-param-backed ones. This reverses the earlier Q4 / SV-emitter / C3
  done-when wording that kept eval-derived constants in the package at
  worst/default value until C4. Rationale: it is harmless today (no RTL
  references `IP_DATA_WIDTH_X2`) and is the consistent end-state — C4 emits such
  values module-local. The C3.1 package filter therefore needs no special case
  for eval-derived constants and no way to tell them apart from block-param
  constants; both are simply `isParameterizable`.
- **Verification.** Regenerated against the existing `ip_test.db`:
  `ip_package.sv` drops `IP_DATA_WIDTH`/`IP_MEM_DEPTH`/`IP_NONCONST_DEPTH`/
  `IP_DATA_WIDTH_X2` and `ipDataT`/`ipMemAddrT`/`ipDataSt`/`ipCfgSt`/`ipMemSt`/
  `ipMemAddrSt`/`ipBurstSt`; `ipLeaf`/`src` packages drop their analogues; all
  non-parameterizable items retained; `ip_top`/`ipBridge`/`shared_types`
  packages byte-identical. Unit Suite 18 passes 5/5.
- **Build/run state after C3.1 (verified 2026-06-05):**
  - **SystemC model fully builds and runs.** `make gen` + `make all` + `make
    run` complete; the simulation runs to completion and reports `No error`.
    C3.1 does not touch this path (the model consumes C++ includes, not the SV
    package).
  - **RTL / Verilator co-sim does not build yet (expected gating, not a
    regression).** `make all VL_DUT=1` fails in Verilator on `ip.sv`:
    `Expecting a data type: 'ipDataSt'` (ip.sv:67), `Can't find definition of
    variable: 'ipDataT'` (ip.sv:80), plus implicit-signal warnings for
    `ipCfgSt`/`ipDataSt`/`ipMemSt`/`ipMemAddrSt`. C3.1 correctly removed these
    parameterizable types from the package, but `ip.sv` does not yet declare
    them module-local. The reg handler `ipRegs.sv` is already module-local via
    C3.R, so the failure is confined to `ip.sv`.
- **C3.2/C3.3 general module-local path for `ip.sv` is DONE (2026-06-05).** The
  module-local typedefs/structs and module parameters are emitted for the
  general parameterized block; Verilator elaborates `ip_top` instantiating both
  `ip` parameter variants, `src`, `ipRegs`, and the sized `memory_dp` instances
  with zero errors. The only residual elaboration errors are the `ip_top`
  container-channel `data_t(srcOut0St/srcOut1St)` refs (the Q8/Q9 boundary).
- **Next items:** C3.4 (remove the `ip.sv` field-wise widening workaround and
  full RTL regen) and C3.5 (the container-channel adapter that resolves the
  remaining `ip_top` errors), after which full `ip_test` RTL co-sim is
  verifiable.
- Nothing staged/committed (`builder/base` is a user-managed submodule).

### 2026-06-08 — C3.6 split: static validation vs runtime cosim acceptance (C3.7 added)

User input: the validation matrix should also confirm the thunkers between
SystemC and SV work as expected — instantiate a parameterized `ip` block in
verification (cosim) mode and check functionality — and asked whether that
belongs in C3.6 or a separate step.

Resolution captured in doc:
- **C3.6 stays as static parser validation** (the connection/interface
  parameterization matrix + informative endpoint errors), with negative cases
  as `unittest` fixtures (user direction: negative tests belong in unittest
  fixtures).
- **C3.7 added** for the runtime cross-language acceptance check, kept separate
  because it differs in kind: a different verification mode (build + Verilate +
  simulate + scoreboard vs `make db` rejecting YAML), a different thing under
  test (the emitted RTL + thunker boundary at runtime vs the parser), and a
  genuine open gap (the cross-variant boundary was signed off only via Verilator
  lint/elaboration + a model/model `make run`; a Verilated *parameterized* block
  driven through the thunker boundary has not been demonstrated functional). The
  cosim infrastructure already exists (`verif/vl_wrap`, `run-vl`/`run-vl-ip0`);
  C3.7 confirms `run-vl-ip0` green and adds a wide-variant `run-vl-ip1` target.
- C3.6 and C3.7 are independent; both depend only on C3.5 (done).

### 2026-06-08 — C3.8 opened: cosim wrapper build break blocks C3.7

A comprehensive `ip_test` regression (`regr_ip_test.json`, run via a new
`regr` make target in `examples/ip_test/rundir/Makefile`, with a copied
`default.json` ruleset) was authored as the vehicle for C3.7. Its matrix is
a model/model baseline plus Verilator `verif` cosim of the whole `ip_top`,
`uSrc`, `uIp0` (variant0, ≤64), and `uIp1` (variant1, width 70, >64). Tandem
was intentionally excluded — no `pro/` is present, so `A2CPRO` is undefined
and `simController.cpp` asserts tandem unsupported; `--vlType` defaults to
`verif`, which is what the existing `run-vl-*` targets already use.

Running it exposed that **C3.7's stated premise was wrong**: `make all
VL_DUT=1` does not build. The generated cosim wrappers
(`module_hdl_wrapper`) instantiate the boundary interface as
`push_ack_if #(.data_t(ipDataSt))` at wrapper scope, but C3.1 removed
`ipDataSt`/`srcOut0St`/`srcOut1St` from `<block>_package` and made them
module-local, so the wrapper's package import cannot resolve them
(Verilator: `Param 'data_t' … isn't a type`). The Verilated parameterized
boundary had never actually compiled — only `--lint-only` on the modules
themselves and a model/model `make run` had been exercised.

Resolution captured in doc: **C3.8 added**, depends on C3.5, blocks C3.7.
The wrapper template must emit the block's `parameterizedDecls`
module-locally (sized by the variant's concrete parameters, which the
wrapper already hard-codes on the `dut #(…)` line), mirroring C3.2's
module-local emission, instead of relying on the package. C3.7 then reverts
to its runtime functional role once the build is green.

### 2026-06-08 — C3.8 fixed and C3.7 closed (regression 11/11 PASS)

C3.8's wrapper-emission fix landed: `templates/systemVerilog/module_hdl_wrapper.py`
now emits each variant's `parameterizedDecls` (module-local typedefs/structs)
at wrapper scope, sized by a wrapper-scope `localparam` from the variant's
concrete parameters, before the boundary interface declarations. The
regenerated wrappers confirm it — e.g. `ip_variant1_hdl_sv_wrapper.sv` carries
`localparam IP_DATA_WIDTH = 70;` → `typedef … ipDataT;` → `ipDataSt` →
`push_ack_if #(.data_t(ipDataSt)) ipDataIf();`, so the package import no longer
needs the parameterizable structs C3.1 moved out. The SystemC-side wrapper
(`*_hdl_sc_wrapper.h`) needed no analogous change.

With the build green, C3.7 ran as the runtime gate. The `regr_ip_test`
`hdl_tests` matrix was extended from 4 to 10 `--vlInst` targets to cover every
Verilatable instance under `ip_top` (user decision: add all remaining,
including nested): the original `cosim`/`boundary`/`narrow_le64`/`wide_gt64`,
plus `apb_decode` (`uAPBDecode`), `bridge` (`uBridge`), `bridge_driver`
(`uBridgeDriver`), `bridge_apb_decode` (`uBridge.uBridgeAPBDecode`), and the
nested Q10 cross-interface bridge variants `bridge_narrow_le64`
(`uBridge.uBridgeIp0`) and `bridge_wide_gt64` (`uBridge.uBridgeIp1`). Labels
follow the existing scheme: `param` for parameterized `ip` variants, `wide`
for the `>64` path, and a new selectable `bridge` label across the `uBridge`
subtree. `make regr`: build session 0:00:25, run session **11/11 PASS, 0
failed**. The dedicated `run-vl-ip1` Makefile target was not added — the
regression's `wide_gt64`/`bridge_wide_gt64` entries cover the `>64` path and
supersede the per-target need. C3.7 and C3.8 are **DONE**; C3.6 (static
validation matrix) was subsequently closed 2026-06-23, so C3 has no residual.

### 2026-06-23 — C3.6 closed: endpoint validation matrix filled

The C3.6 static validator (`_validateParameterizedConnectionEndpoints`, run
inside `deriveParameterizedDeclSets()` off the in-memory `paramSet`) was
already present and committed with a minimal positive/negative pair. C3.6 was
closed by filling out the validation matrix the plan calls for, all as
`unittest` fixtures in `test_param_const_linkage.py` (7 → 11 cells):

- **Negative — dst parameterized on the wrong param.** The consumer is
  parameterized but carries an unrelated backing param, so it is
  parameterizable yet still cannot size the payload. Exercises the second
  error-reason branch (`does not declare the required parameter(s)`), which the
  pre-existing dst-unparameterized negative did not reach.
- **Negative — src endpoint short.** The shortfall is placed on the producer
  (src) end, with the consumer carrying the param so it is not an orphan. Shows
  both connection ends are validated, not only the consumer.
- **Positive — plain interface between plain blocks.** A non-parameterizable
  connection must skip endpoint validation; guards against the validator
  over-firing.
- **Positive — C3.5 cross-variant non-parameterized boundary channel.** Two
  parameterized blocks bound to different variants (WIDTH 8 vs 16) bridged by a
  non-parameterized boundary interface: the channel is not parameterizable, so
  validation is skipped and the build succeeds, the per-leg payload adaptation
  being a runtime concern (covered functionally by C3.7).

`make`-driven: each fixture runs a real `arch2code.py` projectCreate and asserts
the failure message (or success) end-to-end. 11/11 PASS. No change to the
validator logic was needed. C3 now has no residual.

## Related documents

- `plan-development-ordering.md` — broader modules/Config ordering; **S1/S2**
  superseded by this plan's **C3** (see Execution plan).
- `plan-constants-flat-lookup.md` — wordLines helpers lifecycle
  cleanup. That plan deliberately preserves today's shadow lookup
  behavior; whatever we decide here changes the picture for that
  plan's "What stays" section.
- `plan-foreign-key-lookup.md` — establishes the `lookupInScope`
  primitive that the constant-vs-param collision validator would use to
  walk a block's include chain.
- `plan-schema-controlled-flat-data.md` — establishes the "don't
  preemptively mark flat" guardrail. Not directly relevant to this
  discussion but cited for context on the broader project conventions.

## #116 Review Follow-Up — Item 1: Project-Name Qualification of Module/Package Identifiers (Execution, 2026-07-29)

Execution hardening of `plan-116-review-feedback.md` item 1. Keep the
on-disk filename plain (unqualified), but project-qualify the **C++
module identity** and the **SystemVerilog package identifier**, with a
prefix-dedup that keeps every context whose stem already leads with its
owning project byte-identical. SV **module** names are unaffected (they
derive from the block name, not the context identity — see change sites).

### Change sites (verified 2026-07-29, current line numbers)

1. **`pysrc/processYaml.py::projectCreate`, lines 3640-3643** — the
   `contextModuleIdentity` assignment, currently neutralized to the bare
   stem:

   ```python
   self.contextModuleIdentity = {}
   for context, stem in self.includeName.items():
       self.contextModuleIdentity[context] = stem
   ```

   Replace the bare `= stem` with the prefix-dedup qualification using
   `self.contextOwningProject[context]` (persisted first-class per-context
   fact set at line 3599, `CONTEXTOWNINGPROJECT`, keyed identically to
   `includeName` and in scope here). No new persisted field.

2. **`templates/systemVerilog/package.py`, line 96** (Role C consumer):

   ```python
   packageName = prj.includeName[data['context'][0]] + '_package'
   ```

   Repoint `prj.includeName[...]` → `prj.contextModuleIdentity[...]`
   (`+ '_package'` unchanged). No-op while the identity is bare.

3. **`pysrc/systemVerilogGeneratorHelper.py`, line 26** (Role C consumer,
   in `importPackages`):

   ```python
   packageName = prj.includeName[context] + '_package'
   ```

   Same repoint `prj.includeName[context]` → `prj.contextModuleIdentity[context]`.

4. **`pysrc/processYaml.py::projectCreate`, lines 3649-3661** — the
   existing module/package identity uniqueness gate. **No change**; it
   already rejects two distinct contexts resolving to the same identity
   with a durable error, which covers the pathological collapse case
   (project `a` block `a_b` vs project `a_b` block `a_b`). No new guard.

Do the SV repoints (2, 3) first — a pure no-op while the identity is bare
— then the qualify (1). C++ Role A already consumes `contextModuleIdentity`,
so no C++-side edit is needed.

### Dedup predicate (pseudocode)

The qualification is applied to the **stem** (`includeName` value); SV then
appends `_package` to the result, and C++ spells the result directly as the
module/namespace name.

```
def qualify(stem, projectName):
    if stem == projectName or stem.startswith(projectName + "_"):
        return stem                       # already leads with project → no dedup
    return projectName + "_" + stem       # otherwise prepend

# self.contextModuleIdentity[context] = qualify(stem, self.contextOwningProject[context])
```

The `+ "_"` boundary is load-bearing: it prevents a false dedup of
`debayering` under project `debayer`, and — as the cross-example list below
shows — it **does** re-qualify camelCase-concatenated stems such as
`hierIncludeB` under project `hierInclude` (no `_` boundary), which is
intended.

### Cross-example impact (read-only survey of `builder/base/examples`)

Impact axis is the **context stem vs its owning `projectName`**. A context
CHANGES iff its stem neither equals nor leads with `projectName + "_"`. The
same set changes in both languages (SV package name = `identity + "_package"`;
C++ module/namespace = `identity`); SV **module** names do not change.

**Byte-identical (no change) — the common single-project cases, confirmed:**
`apbDecode` (`apbDecode`), `axi4sDemo` (`axi4sDemo`, `axi4sDemo_tb`),
`helloWorld` (`helloWorld_tb`), `inAndOut` (`inAndOut`), `nested`
(`nested`), `pySocket` (`pySocket`, `pySocket_tb`), `simple` (`simple`),
`xif` (`xif`). Each sole design context equals its project, and every
`<project>_tb` context leads with `<project>_`, so dedup holds them fixed.

**Contexts that CHANGE** (old identifier → new; SV package appends
`_package`):

| Example (project) | Context stem | New identity | Note |
|---|---|---|---|
| axiDemo (`axiDemo`) | `axiStd` | `axiDemo_axiStd` | shared AXI-std types context |
| hierInclude (`hierInclude`) | `hierIncludeTop` | `hierInclude_hierIncludeTop` | camelCase, no `_` boundary |
| hierInclude (`hierInclude`) | `hierIncludeNestedTop` | `hierInclude_hierIncludeNestedTop` | " |
| hierInclude (`hierInclude`) | `hierIncludeB` | `hierInclude_hierIncludeB` | " |
| hierInclude (`hierInclude`) | `hierIncludeBInclude` | `hierInclude_hierIncludeBInclude` | " |
| hierInclude (`hierInclude`) | `hierIncludeC` | `hierInclude_hierIncludeC` | " |
| hierInclude (`hierInclude`) | `hierIncludeCInclude` | `hierInclude_hierIncludeCInclude` | " |
| hierVlDemo (`hierVlDemo`) | `hierVlSharedTypes` | `hierVlDemo_hierVlSharedTypes` | shared-types context |
| mixed (`mixed`) | `mixedBlockC` | `mixed_mixedBlockC` | camelCase, no `_` boundary |
| mixed (`mixed`) | `mixedInclude` | `mixed_mixedInclude` | " |
| mixed (`mixed`) | `mixedNestedInclude` | `mixed_mixedNestedInclude` | " |
| simple_ip (`common`) | `shared_types` | `common_shared_types` | cross-project shared types |
| simple_ip (`ip`) | `ipTop` | `ip_ipTop` | camelCase, no `_` boundary |
| ip_test (`common`) | `shared_types` | `common_shared_types` | cross-project shared types |
| ip_test (`ip`) | `ipTop` | `ip_ipTop` | camelCase, no `_` boundary |
| ip_test (`ip_test`) | `src` | `ip_test_src` | owner assumed `ip_test` — confirm |
| ip_test (`ip_test`) | `ip_top` | `ip_test_ip_top` | `ip_top`↛`ip_test_`; confirm owner |
| ip_test (`ip`?/`ip_test`?) | `ipLeaf` | `ip_ipLeaf` **or** `ip_test_ipLeaf` | **owner uncertain — confirm** |

Uncertainty flagged: `ip_test` owner assignments (`src`, `ip_top`,
`ipLeaf`) are inferred from directory/composition memory, not read from
the DB. At execution, confirm each against `CONTEXTOWNINGPROJECT` (dump the
persisted per-context map) before trusting the new-identity column. The
`ip`/`ipBridge`/`common`/`simple_ip` roots and every single-project row
above are high-confidence.

**Not affected (verified):** `mixedEncoderPackage` (file
`mixed/rtl/mixedEncoder_package.sv`) is a **hand-authored** encoder in the
`mixed` context (EXTRA-seam); its `package mixedEncoderPackage;` line sits
outside the generated region and never passes through the
`includeName + '_package'` consumers, so the repoint does not touch it. Its
in-file `import mixed_package::*;` stays (`mixed` == project).

### User-code / import touchpoints

Every import of a renamed identifier found in the suite lives inside a
`GENERATED_CODE_BEGIN/END` region and is emitted by the generator itself:

- SV `import <ctx>_package::*;` — produced by `importPackages`
  (`systemVerilogGeneratorHelper.py`), present in dependent package files,
  block RTL, and `*_hdl_sv_wrapper.sv`. Example: `axiDemo_package.sv:7
  import axiStd_package::*;` and ~10 `import shared_types_package::*;` sites
  across `ip_test` — all generated regions.
- C++ `import <ctx>;` — produced by the `--template=headers` region, e.g.
  `axiDemoIncludes.cppm:16 import axiStd;` — a generated region.

Because the consumers are repointed at the same seam that emits these
imports, `make gen` rewrites both the declaration and every import of a
renamed identity in lockstep. **No hand-authored user-region reference to a
renamed package/module was found** in the example suite, so the re-baseline
is mechanical (regenerate + commit changed generated files), not a manual
edit sweep. `rtl.f` lists file paths, not package identifiers, so it is
unaffected.

### Migration implications

- **No filename-rename migration.** On-disk `.sv`/`.cppm` basenames stay on
  the plain stem; only the in-file identifier changes. No `migrateYaml.py`
  phase and no user-authored YAML change are required for item 1.
- **One-time generated re-baseline** limited to the CHANGE table above.
  Users of the affected examples (and any real project with a cross-named
  context) regenerate and commit the churned generated regions. Single-
  project projects whose contexts equal/lead with the project name see zero
  diff.
- **Cross-project stability is the design payoff:** because the identity is
  qualified by the intrinsic `contextOwningProject`, not the current build
  root, a child IP (`ip`, `common`) spells the same package/module name
  standalone and when composed into `ip_test` — closing the build-dependent
  qualification concern from the superseded Q-C8 analysis.

### Validation plan

1. **No-op checkpoint:** apply only change sites 2 and 3 (SV repoint to the
   still-bare identity), then `make -j gen` across the full base+pro suite;
   expect a **zero diff** in all generated SV.
2. **Qualify:** apply change site 1, then `make -j clean gen run` across the
   full base+pro example suite (see the `feedback_validate_across_all_examples`
   convention — ip_test alone is insufficient). Use `-j` (also exercises the
   concurrent verilated `--Mdir` path).
3. **Confirm the change set** equals the CHANGE table: the only churned
   package/module identifiers are the rows above; every byte-identical
   example shows no diff.
4. **Uniqueness gate:** confirm lines 3649-3661 still pass for the whole
   suite (no two contexts collapse to one identity under qualification).
5. **Cosim:** `make -j run-vl` on the VL-capable examples (`ip_test`,
   `apbDecode`, `axi4sDemo`) to confirm the renamed packages still elaborate
   and import correctly across the model/RTL boundary.
6. **Owner confirmation:** before step 2, dump `CONTEXTOWNINGPROJECT` for
   `ip_test` and reconcile the three flagged rows (`src`, `ip_top`,
   `ipLeaf`).

#### Scope extension (2026-07-29): SV `module` name qualification

Reviewer decision: the SystemVerilog **`module` name is also in scope**, with
the same prefix-dedup predicate and the owner sourced from
`CONTEXTOWNINGPROJECT` (resolved through the block's `_context`).

**Module-emit sites (all converge on the block name):**
- Declaration: `pysrc/systemVerilogGeneratorHelper.py::moduleDeclaration`
  (lines 6-7, returns `module {b}`), called with `data['blockName']` at
  `templates/systemVerilog/moduleInterfacesInstances.py:15` and
  `templates/systemVerilog/apbDecodeModule.py:32`.
- `endmodule`: `apbDecodeModule.py:148` (`endmodule: {data['blockName']}`);
  `templates/systemVerilog/moduleRegs.py:93` (`modulename=data['blockName']`,
  rendered at `:757`/`:848`).
- **Instantiation:** `moduleInterfacesInstances.py:99` emits
  `f"{value['instanceType']}{inst_params}{value['instance']} ("` — the
  instantiated module name is `value['instanceType']`, from the
  `data['subBlockInstances']` view.
- HDL wrapper: `pysrc/processYaml.py:1383` builds
  `bodyModule = f'{blockName}{wrapTail}'`, consumed by
  `module_hdl_wrapper.py:124/181/240`, and cascades to `dutClass = V{bodyModule}`
  (`processYaml.py:1399`), `HDL_TOP_MODULE`, and the `A2C_VL_TOP_<block>`
  verilated-top map.

**Design — emit-only field, never overload the lookup key.**
`blockName`/`instanceType` are **internal keys**, not just labels:
`moduleInterfacesInstances.py:18` does `prj.getQualBlock(data['blockName'])`
and connection resolution keys off them. Qualifying them in place would break
lookups. So, mirroring the filename-stem-vs-`contextModuleIdentity` split,
add an **emit-only** identity:
- `projectCreate` derivation (new, block-keyed, analogous to
  `contextModuleIdentity` at `:3640-3643`):
  `blockModuleName[blockKey] = qualify(blockName, contextOwningProject[block._context])`,
  persisted.
- `getBlockData()` surfaces `data['blockModuleName']`; the
  `subBlockInstances` view surfaces `value['instanceTypeModuleName']` = the
  qualified name of the *instantiated* block, looked up through the same map;
  `bodyModule` is built from `blockModuleName`.
- Repoint the emit sites (declaration, `endmodule`, instantiation,
  `bodyModule`) to the new field; `blockName`/`instanceType` stay plain for
  lookups.

**Instantiation-consistency finding.** Declaration, `endmodule`,
instantiation (`instanceTypeModuleName`), HDL-wrapper `bodyModule`, and the
verilated `dutClass`/`HDL_TOP_MODULE`/`A2C_VL_TOP` map **all resolve the
module spelling from the one `blockModuleName` map** (the instantiation reads
the instantiated block's own entry). Consistency is therefore guaranteed by
construction: a rename of block B updates B's declaration and every parent's
`instanceType`-site in lockstep on `make gen`. A survey of the example suite
found **no hand-authored/user-region SV that instantiates a block by literal
module name** — every instantiation is inside a `GENERATED_CODE` region — so
there is no manual instantiation-site breakage to repair; the re-baseline is
mechanical.

**Uniqueness gap (flag).** The existing gate at
`processYaml.py:3649-3661` guards **context** identities only, not block
module names. Qualification can in principle collapse two blocks (project `a`
block `b_c` vs project `a_b` block `c` → both `a_b_c`). A **parallel
per-`blockModuleName` uniqueness gate** should be added alongside site 1;
without it a block-name collapse would silently clobber generated modules.

**Cross-example module-name impact.** Module name = block name; it CHANGES
unless the block name equals or leads with `owningProject + "_"`. This is a
**much larger re-baseline than the package rename** — most blocks are
generically named and do not lead with their project:

- **Byte-identical (survive):** blocks named exactly after their project —
  `apbDecode`, `axiDemo`, `mixed`, `nested`, `pySocket`, `simple`,
  `simple_ip`, `ip`, `ipBridge`, `hierVlDemo`, `inAndOut` — plus
  `<project>_`-prefixed blocks such as **`debayer_regs`** (leads `debayer_`).
- **CHANGE (the majority):** in the **debayer product**, `interpolate` →
  `debayer_interpolate` and `preprocess` → `debayer_preprocess` (only
  `debayer` and `debayer_regs` are byte-identical — the product is **not**
  fully unchanged). Across the example suite: `blockA`/`blockB`/`blockC`
  (+`X`/`Y`/`Z`), `blockD`, `blockF`, `blockG`, `blockGLeaf`, `blockARegs`,
  `blockBRegs`, `blockGRegs`, `consumer`, `producer`, `dataGen`, `dut`,
  `sink`, `src`, `top`, `cpu`, `threeCs`, `someRapper`, `bridgeApbDecode`,
  `bridgeDriver`, `ipLeaf`, `ipRegs`, `ipStdDecode`/`ipStdDriver`/
  `ipStdMaster`/`ipStdTop` — each qualifies to `<owningProject>_<block>`.
  `<block>_hdl_sv_wrapper` names inherit the change via `bodyModule`.

**Validation delta.** Extend step 2/3 of the plan above: the churned set now
includes every renamed **module** (declaration + all instantiations +
wrappers + verilated tops), not only packages. Step 5 (`make -j run-vl`) is
now load-bearing — it proves the renamed DUT modules still elaborate,
instantiate, and match `HDL_TOP_MODULE`/`A2C_VL_TOP` across the tandem
boundary. Add a step to confirm the new per-block uniqueness gate passes.

Builds/edits to generator code are out of scope for this document; this
section is the execution contract for the implementer.

### Execution outcome (2026-07-29) — corrections from implementation

Item 1 was executed against this section. Findings below correct two wrong
claims above and record two blockers discovered while implementing.

**A. Package name + C++ module/namespace identity — LANDED, sound.**
`qualifyModuleIdentity(name, projectName)` (prefix dedup) added; projectCreate
qualifies `contextModuleIdentity` with `contextOwningProject[context]`; the two
SV package consumers (`templates/systemVerilog/package.py`,
`pysrc/systemVerilogGeneratorHelper.py::importPackages`) repointed to
`contextModuleIdentity`. C++ Role A already consumed the seam (headers.py,
structures.py, moduleScaffold.py, intf_gen_utils `cpp_context_include_lines`),
so declaration and every importer rename in lockstep. Proven: `axiDemo`
(`axiStd → axiDemo_axiStd`) and `hierVlDemo` (`hierVlSharedTypes →
hierVlDemo_hierVlSharedTypes`) build + run + run-vl "No error"; `nested`
(byte-identical) shows a **zero diff** (dedup no-op confirmed).
Caveat: the `mixed` example carries pre-existing **stale header-mode orphans**
(`model/blockF.cpp` / `blockF.h`, not in the `.gen` graph, superseded by
`blockF.cppm`) that still get compiled; they hard-code `import mixedBlockC` and
break under the rename. This is mixed-example migration debt (orphan sweep), not
a generator defect — but full-suite `make run` is not green until mixed's
orphans are removed.

**Owners — CONFIRMED from CONTEXTOWNINGPROJECT (ip_test.db), replacing the
inferred rows above:** `src.yaml → ip_test`, `top/ip_top.yaml → ip_test`, and
`leaf/ipLeaf.yaml → **ip_test**` (NOT `ip`). So in the composed build the
package identities are `ip_test_src`, `ip_test_ip_top`, `ip_test_ipLeaf`.
`ip`/`ipBridge`/`common` roots as stated.

**B. SV module-name qualification — BLOCKED, reverted.** Two corrections:

1. *The "bodyModule cascades to A2C_VL_TOP" claim is WRONG.* `A2C_VL_TOP_<block>`
   / `A2C_VL_TOPS` / `HDL_TOP_MODULE` derive from the **filename basename**
   (`config/createBuildManifest.py`, `os.path.basename(filePath)`), never from
   `svWrapper['bodyModule']`. For a non-parameterizable block the wrapper body
   module IS the verilated top and its name must equal the plain filename;
   qualifying `bodyModule` (and `dutClass = V{bodyModule}`, `bodyInclude`)
   desyncs it from the plain `--top-module`. So `bodyModule` / `variantTops` /
   `foreignVariantTops` MUST stay plain. Corrected Change-B scope was therefore:
   qualify only the design-block module identity (declaration, endmodule,
   parent instantiation, and `module_hdl_wrapper.py::dut_instantiation` line 97),
   keeping all wrapper/verilated-top names plain.

2. *Corrected scope hits a user-owned line the plan missed:* the SystemVerilog
   **`endmodule: <label>`** in every `moduleInterfacesInstances`-style RTL file
   (leaf and hierarchical — `blockF.sv`, `blockG.sv`, `blockA.sv`, `cpu.sv`,
   `threeCs.sv`, … and the debayer product's `interpolate.sv`/`preprocess.sv`) is
   scaffolded (`templates/fileGen/fileGen.py::rtlModule`) **outside** the
   generated region — USER-OWNED. `gen` never rewrites it, so qualifying the
   generated `module <name>` begin-label leaves the user `endmodule: <plainname>`
   stale → Verilator `%Error-ENDLABEL`. (Fully-generated RTL — `moduleRegs` /
   `apbDecodeModule` — closes its module INSIDE the region, so its endmodule is
   generator-owned and already tracks the rename.)

**Reviewer decision (2026-07-29): PROCEED with SV module-name qualification; a
migration reconciles the user `endmodule:` label, folded into `make migrate`.**

**Chosen migration mechanism — Option 1 (post-db label re-stamp).** A new
`--sweep`-phase step (`pysrc/migrateModuleEndlabel.py::restampModuleEndlabel`,
wired into `migrateYaml.py --sweep` after the project/context re-stamps) reads
the qualified `blockModuleName` from the DB and rewrites each owned RTL block
file's user-region `endmodule: <label>` to the qualified name.
- *Why post-db:* the qualified name is `qualify(blockName, owningProject)`, and
  the owner (`contextOwningProject`) exists only after `make db`. A pre-db text
  phase cannot compute it — confirmed.
- *Why Option 1 over Option 2 (generator owns the endmodule):* Option 2 needs a
  SECOND trailing generated region after the user module body in every RTL file
  (the begin-region cannot span the user body to reach `endmodule`), i.e. a
  structural scaffold change plus a migration that inserts the trailing region
  and deletes the user label in every file. Option 1 changes one user line and
  reuses the existing `--sweep` restamp machinery; it is strictly simpler and is
  consistent with how package/context identities already re-baseline on an owner
  change. Idempotent (a file already carrying the qualified label is a no-op);
  files whose endmodule is generator-owned (inside a region) or unlabelled are
  left untouched; owner-gated so a composed build never rewrites a child's file.
- *New files:* the scaffold is fixed at the same seam — `fileGen.py::rtlModule`
  emits `endmodule: <blockModuleName>` and `newModule.py` surfaces
  `blockModuleName` on the per-block scaffold `data` — so a freshly created block
  never reintroduces the mismatch.

**Generator edit sites (B/C re-applied, corrected scope):**
`processYaml.py` `blockModuleName` map + per-block uniqueness gate (projectCreate),
`BLOCKMODULENAME` load (projectOpen), `ret['blockModuleName']` +
`instanceTypeModuleName` on the block/instance views; emit repoints in
`moduleInterfacesInstances.py` (:15 decl, :99 instantiation), `apbDecodeModule.py`
(:32 decl, :148 endmodule), `moduleRegs.py` (:93 modulename), and
`module_hdl_wrapper.py::dut_instantiation` (:97). Wrapper `bodyModule` /
`bodyInclude` / `dutClass` / `variantTops` / `foreignVariantTops` kept PLAIN.

**Net:** Change A landed. Changes B + C re-applied with the corrected scope.
The `endmodule:` reconciliation is Option 1, wired into `make migrate`.

### Migration implementation + example validation (2026-07-29)

New module `pysrc/migrateModuleEndlabel.py` (`restampModuleEndlabel` +
`renderModuleEndlabelReport`), invoked from `migrateYaml.py --sweep` after the
project/context re-stamps. Scaffold seam fixed for new files:
`newModule.py` puts `blockModuleName` on the per-block scaffold `data`;
`fileGen.py::rtlModule` emits `endmodule: {blockModuleName}`.

**Validated (migrate → build/run/run-vl):**
- ENDLABEL eliminated everywhere it was expected: mixed, apbDecode, axi4sDemo,
  ip_test (composed), simple_ip, simple, nested, helloWorld — all 0 `%Error-ENDLABEL`.
- Endlabel restamps matched DB-confirmed owners, e.g. ip: `ipStd*→ip_ipStd*`;
  ip_test: `ipLeaf→ip_test_ipLeaf`, `src→ip_test_src`, `ip_top→ip_test_ip_top`;
  mixed: `blockA→mixed_blockA` … (regs/apbDecode generator-owned + `mixed`/
  `debayer`-style project-named blocks correctly left untouched).
- Build+run "No error": axiDemo, hierVlDemo (run-vl), axi4sDemo (run-vl),
  nested, helloWorld, simple, simple_ip (all child projects migrated),
  pro/lmmiDemo (run-vl), ip_test composed MODEL run, ip standalone MODEL run.
- Uniqueness gates (context + per-block module) passed across every db build.

**Pre-existing issues (NOT regressions; confirmed against committed baseline):**
- ip_test composed `run-vl`: `ipTop_package not found` — the composed
  `top/rtl/rtl.f` never aggregates the child `ip`'s `ipTop_package.sv` (git HEAD
  shows the same list minus the qualified name); plus F4 `q_assert`
  (`unregistered block type ip_verif`, a factory key this change never touches).
  Both match the "ip_test composed flip incomplete" known state.
- mixed C++ + pySocket C++: pending agent-driven `.cpp/.h`→`.cppm` port
  (`TODO_PORT` / header-mode leftovers), independent of this change.

**Legacy-example gap (needs a decision):** lint-only legacy examples with no
`make migrate` target (e.g. `hierInclude`, files under `systemVerilog/`) qualify
their begin-labels via `gen` but cannot invoke the endlabel migration through the
standard flow, so their lint hits ENDLABEL. `restampModuleEndlabel` DOES handle
their files correctly (verified by a direct `migrateYaml.py --sweep` dry-run:
`top→hierInclude_top`, `blockA→hierInclude_blockA`, …). They need `make migrate`
wiring (running a raw `--sweep` alone is destructive — it deletes orphans without
the follow-on `newmodule`+`gen`). `inAndOut` lint stayed green (no renaming leaf
modules). This is example-Makefile wiring, not a migration-logic defect.

### debayer product RTL enumeration (relabel targets; NOT executed)

Same migration on the debayer product (`projectName: debayer`) would relabel the
USER `endmodule:` of exactly:
- `rtl/interpolate.sv`: `endmodule : interpolate` → `endmodule : debayer_interpolate`
- `rtl/preprocess.sv`:  `endmodule: preprocess`   → `endmodule: debayer_preprocess`
`rtl/debayer.sv` (== project) and `rtl/debayer_regs.sv` (leads `debayer_`, and
generator-owned endmodule) are unchanged. Run as a separate confirmed product
migration step.
