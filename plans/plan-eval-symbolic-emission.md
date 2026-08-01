# Plan: Symbolic Eval — Parse, Evaluate, Emit, Persist

Date: 2026-06-09 (status reconciled 2026-07-24)
Status: **complete for the selected scope** — E4 is committed for SV localparam emission and
block-local dependency closure; E5 **complete** (SystemC C++ half
2026-06-11; firmware C half 2026-06-23): the FW `includes` constants
section now emits eval-derived parameterizable constants symbolically via
`emitCStyleCanonical`, and `ip_test`'s firmware consumes one
(`IP_DATA_WIDTH_X2`) with `make gen`/build/run green — see E5; E6
variant-aware address evaluation is
**closed (descoped)**: `calcAddresses` sizes parameterizable address
objects to their worst case, so all variants share one address map and
per-variant address evaluation is neither needed nor desirable (see E6).
The E1.5 Python→SV converter (`pysrc/evalPyToSv.py`) is committed and
is exercised by the unified YAML migration path (Suite 19h). The old standalone
CLI ownership wording in `plan-eval-python-to-sv-migration.md` is superseded by
`migrateYaml.py` / `make migrate`.
Source: [`research-eval-symbolic-emission.md`](./research-eval-symbolic-emission.md).
Owner: C4 (`plan-param-constant-collision.md`).

This plan turns the recorded research decisions into a staged
implementation. The research doc froze the inputs: the authoring language
is an **integer SystemVerilog constant-expression subset**, the grammar is fixed
(SystemVerilog integer literals, arithmetic `+ - * / %`, bitwise `& | ^ ~`, logical shifts
`<< >>`, `$clog2`, `$symbol` references, parentheses), and the parser is an
**in-house precedence-climbing (Pratt) parser** with no external
dependency. This plan does not re-open those decisions; it is organized
around the **use cases** the parsed representation must serve.

## Goal

Replace the current parse-time `eval()`-of-substituted-string mechanism
for integer constants with a single pipeline: parse each integer `eval`
expression once into a
language-neutral **object tree (IR)**, then drive every consumer — numeric
evaluation and per-language emission — off that one tree, and persist it
for reload by generators.

## Core Design Principle: One Pipeline, Not Two

There is **one** eval representation for **all integer** `eval` constants,
parameterizable or not. The parser/IR/evaluator replaces the regex
substitution plus `eval()` for every integer eval constant; the language
emitters additionally fire only for the parameterizable ones. This is a
single direct path (per the builder-base rules — no parallel APIs, no
`eval()` fallback) and it removes the arbitrary-code-execution surface of
the current `eval()` calls as a side effect.

`valueType: real` with `eval` is **not supported in this pipeline**. Real
SystemVerilog constant expressions are a separate typed expression domain
(real literals, real division, invalid real `%`, and target-language type
policy). For this C4 work, real-valued constants must be literal values,
not `eval` expressions.

## Use Cases

The IR exists to serve four concrete consumers. Each is anchored to the
current code it replaces or extends.

### UC1 — Parse user input into an object tree

Input: the user-authored integer SV-subset expression string (today the
`eval:` field). Output: an IR tree of nodes (`Num`, `Sym`, `Unary`, `Bin`,
`Clog2`). Replaces the regex tokenizing in `processYaml.py:4895` and the
discard of the expression after evaluation.

- `$symbol` references resolve to constants/enums through the existing
  include-chain scope rules (`ValueResolver`, `valueResolver.py`); the IR
  stores the qualified symbol key so reload needs no re-scoping.
- Real literals and `valueType: real` eval expressions are rejected at
  create time. They are out of scope for this integer symbolic-eval
  pipeline.
- Integer literals are **SystemVerilog** integer literals: unsized decimal
  (`123`) and SV based literals, sized or unsized, in any base
  (`8'hFF`, `'hFF`, `12'd4095`, `'b1010`), with `_` digit separators
  permitted. C-style `0x` / `0o` / `0b` prefixes are **not** accepted — the
  authoring language is SV, so literals are spelled in SV. `x` / `z` digits
  are rejected: they have no integer value to evaluate.
- Out-of-grammar input is rejected by the parser with a user-tone error,
  replacing the `eval()` try/except at `processYaml.py:4910`-`4918`.

### UC2 — Evaluate at create time (the two existing eval sites)

The evaluator is `evaluate(node, resolve) -> int`, mirroring SV
constant semantics (notably integer `/` truncating toward zero, **not**
Python floor `//` — see Resolved Decisions). It is called with different
symbol-value resolvers to serve the two evaluations the generator already does
today:

- **UC2a — active value.** Replaces `eval(myVal, {}, {})` at
  `processYaml.py:4911`. Symbol resolver returns each referent's resolved
  `value`. Result stored as the constant's `value`.
- **UC2b — worst-case maxValue.** Replaces `eval(substituted, {}, {})` at
  `processYaml.py:5077`. Symbol resolver returns each referent's `maxValue`
  if parameterizable, else `value`. Result stored as `maxValue`.
- **UC2c — address generation.** `calcAddresses` (`processYaml.py:3159`)
  runs in `projectCreate` and consumes resolved integer values. Where an
  `eval` constant feeds an address computation, the same evaluator
  resolves it. Address objects are sized to their **worst case** across
  variants (`maxBitwidth` / `maxValue`), so addresses are variant-invariant
  by construction and there is no per-variant address evaluation (see E6,
  closed). This is why the evaluator must be a create-time facility, not an
  emit-time one.

### UC3 — Emit to target languages

A per-language walk of the same IR, fed by `projectOpen` for generators.

- **SV emitter** — near-identity: operators and `$clog2` pass through;
  `$symbol` is re-spelled to the module-scoped parameter name; a `Num` is
  spelled in its authored base — decimal as-is, otherwise the unsized SV
  based form (`'hFF`, `'b1010`). Produces a module-local
  `localparam` for an eval-derived parameterizable constant (the deferred
  C4 emission; today these are package-skipped — see
  `plan-param-constant-collision.md` C3.1 / Q4).
- **C++/SystemC emitter** — `$clog2` -> `clog2` (existing precedent,
  `includes.py:85`), `$symbol` → scoped spelling (e.g. `Config::NAME`); a
  `Num` is spelled in its authored base — decimal as-is, hex as `0x..`,
  binary as `0b..`. (Octal is normalized to hex at parse, so no octal case
  reaches the emitter.) Because `**`, `~^`, and `^~` are excluded, every
  retained
  operator has a one-to-one C++ spelling, so no operator special-casing is
  required.
- **Firmware C** — follows the **C++ emission rules** (operators, `clog2`,
  and literals are already largely identical). No separate FW back end: it
  reuses the C-style emission walk, differing only in the `symSpelling` it
  is given (FW header naming rather than `Config::`).

### UC4 — Persist efficiently and reload

The SQLite DB is the only channel between `projectCreate` and
`projectOpen`. The canonical expression string must survive that boundary
so the template-layer emitter APIs can reconstruct the same tree the
evaluator used in `projectCreate`.

`projectOpen` and downstream templates do **not** numerically evaluate
eval expressions. `projectOpen` also does not need to rebuild the IR as a
view object: it exposes the trusted `evalCanonical` string as ordinary
view data. Template-layer emitter APIs accept that canonical string, parse
it internally, and translate it to target-language text. Any concrete
integer result needed by a view or template must already have been
computed in `projectCreate` and persisted as normal schema/config data
(`value`, `maxValue`, address data, or a future persisted per-variant
value).

**Recommended approach: persist a canonical serialization of the IR with
qualified symbols.** The stored string is **not** the
user's verbatim input: it is `unparse(node)`, in which every symbol is
written in fully qualified form so the stored expression is
context-independent. Add one text column to the `constants` table holding
this canonical string for eval rows and the empty string for non-eval rows;
`projectOpen` exposes non-empty values through the relevant view helper for
the template emitter APIs. Rationale:

- Self-contained: qualified symbols mean reload needs no re-walk of the
  include chain — no dependence on reconstructing the authoring context.
- Efficient: one text column, no blob; the Pratt parser is cheap and the
  grammar is frozen.
- Single source of truth for tree shape — `parse(unparse(node))` round-trips
  to the same tree, so create-time evaluation and template-layer emission
  cannot diverge.
- No second serialization format to define and maintain.

**Symbol syntax in the canonical form.** The qualified key is
`name/context` (e.g. `IP_DATA_WIDTH/ip_test`), and `/` is the division
operator, so qualified symbols are wrapped in `${...}` to tokenize as a
single symbol. Two symbol forms therefore exist: `$NAME` (bare; user input
only, resolved by `qualify`) and `${name/context}` (qualified; the
canonical persisted form, parsed directly). `$clog2` keeps its `$name(`
form.

**Literal syntax in the canonical form.** The IR records each literal's
authored base (`Num.base`), so it survives into persistence and emission.
`unparse` writes a `Num` in SV form for its base — decimal as `255`, hex as
`'hFF`, binary as `'b1010` (octal is normalized to hex at parse) — always
the **unsized** based
form (the evaluator does not model bit widths, so an authored width such as
`8'h..` is not reproduced; reproducing it could imply SV truncation
semantics the value math does not enforce). The canonical string is always
SV-subset parseable, so `parse(unparse(node)) == node`.

Alternative considered: serialize the node tree to JSON and store it as a
blob, deserializing on load. This avoids re-parsing but adds a
serializer/deserializer pair and a second tree-shape definition. Not
recommended unless re-parse cost proves material (it will not at this
grammar size). The schema change is approved for Stage E3.

## Worked Examples — What the IR Looks Like

The IR is a small node tree. Each node is shown below in a compact
constructor form: `Num(n)`, `Sym(name)`, `Unary(op, operand)`,
`Bin(op, lhs, rhs)`, `Clog2(operand)`. (In storage `Sym` holds the
qualified key, e.g. `IP_DATA_WIDTH/ip_test`, so reload needs no
re-scoping; the bare name is shown here for readability.)

Two properties the examples illustrate:

- **Precedence is encoded in tree shape, not in stored parentheses.** The
  parser discards parentheses; the emitters re-insert them from operator
  precedence so the emitted text preserves the tree's grouping.
- **One tree, all consumers.** The same node tree drives the create-time
  evaluator (UC2) and the target-language emitters (UC3).

### Example 1 — simple product

```
eval:       "$IP_DATA_WIDTH * 2"
IR:         Bin('*', Sym('IP_DATA_WIDTH/ip_test'), Num(2))
persisted:  "${IP_DATA_WIDTH/ip_test} * 2"

evaluate (IP_DATA_WIDTH = 12)  -> 24
SV emit                        -> IP_DATA_WIDTH * 2
C++ emit                       -> Config::IP_DATA_WIDTH * 2
```

### Example 2 — clog2 over an expression (the widthLog2 idiom)

```
eval:       "$clog2($IP_DATA_WIDTH + 1)"
IR:         Clog2(Bin('+', Sym('IP_DATA_WIDTH/ip_test'), Num(1)))
persisted:  "$clog2(${IP_DATA_WIDTH/ip_test} + 1)"

evaluate (IP_DATA_WIDTH = 12)  -> clog2(13) = 4
SV emit                        -> $clog2(IP_DATA_WIDTH + 1)
C++ emit                       -> clog2(Config::IP_DATA_WIDTH + 1)
```

### Example 3 — operator precedence (no parentheses authored)

`*` binds tighter than `+`, so the multiply sits below the add in the
tree:

```
eval:       "$A + $B * 2"
IR:         Bin('+',
                Sym('A/ip_test'),
                Bin('*', Sym('B/ip_test'), Num(2)))
persisted:  "${A/ip_test} + ${B/ip_test} * 2"

evaluate (A = 1, B = 3)  -> 1 + (3 * 2) = 7
SV emit                  -> A + B * 2        (no parens needed)
C++ emit                 -> Config::A + Config::B * 2
```

### Example 4 — parentheses change the tree, and the emitter restores them

Same tokens as Example 3 but grouped; the add now sits below the multiply,
and the emitter re-inserts parentheses because `+` is lower precedence than
its `*` parent:

```
eval:       "($A + $B) * 2"
IR:         Bin('*',
                Bin('+', Sym('A/ip_test'), Sym('B/ip_test')),
                Num(2))
persisted:  "(${A/ip_test} + ${B/ip_test}) * 2"

evaluate (A = 1, B = 3)  -> (1 + 3) * 2 = 8
SV emit                  -> (A + B) * 2     (parens restored)
C++ emit                 -> (Config::A + Config::B) * 2
```

### Example 5 — truncating division (round-up-to-bytes idiom)

Highlights the SV/C++ division semantics the evaluator must mirror
(truncate toward zero, not Python floor `//`):

```
eval:       "($DATA_BITS + 7) / 8"
IR:         Bin('/',
                Bin('+', Sym('DATA_BITS/ip_test'), Num(7)),
                Num(8))
persisted:  "(${DATA_BITS/ip_test} + 7) / 8"

evaluate (DATA_BITS = 20)  -> 27 / 8 = 3   (truncated)
SV emit                    -> (DATA_BITS + 7) / 8
C++ emit                   -> (Config::DATA_BITS + 7) / 8
```

### Example 6 — bitwise and shift

```
eval:       "($N & ~$MASK) << 2"
IR:         Bin('<<',
                Bin('&', Sym('N/ip_test'), Unary('~', Sym('MASK/ip_test'))),
                Num(2))
persisted:  "(${N/ip_test} & ~${MASK/ip_test}) << 2"

evaluate (N = 0xF3, MASK = 0x0F)  -> (0xF3 & ~0x0F) << 2 = 0xF0 << 2 = 0x3C0
SV emit                           -> (N & ~MASK) << 2
C++ emit                          -> (Config::N & ~Config::MASK) << 2
```

### Example 7 — SV hex literal (authored base is preserved)

The literal is authored in SV hex (`8'h20`). The IR records the value and
its base, so each emitter re-spells it in the developer's base (SV `'h20`,
C++ `0x20`) while the evaluator uses the integer value. The authored width
(`8`) is dropped — the canonical and SV forms are unsized — because the
evaluator does not model bit widths:

```
eval:       "$BASE_ADDR + 8'h20"
IR:         Bin('+', Sym('BASE_ADDR/ip_test'), Num(32, base=16))
persisted:  "${BASE_ADDR/ip_test} + 'h20"

evaluate (BASE_ADDR = 256)  -> 256 + 32 = 288
SV emit                     -> BASE_ADDR + 'h20
C++ emit                    -> Config::BASE_ADDR + 0x20
```

## Module Layout

The parser, IR, and evaluator are **language-neutral** and live in a
**new, standalone `pysrc` module** — proposed `pysrc/evalExpr.py` — not
bolted into `processYaml.py`. That module owns:

- the IR node classes (`Num`, `Sym`, `Unary`, `Bin`, `Clog2`),
- the tokenizer and Pratt parser (`parse(exprStr) -> node`),
- the numeric evaluator (`evaluate(node, resolve) -> int`).

`processYaml.py` becomes a **consumer** of this module at the two
create-time evaluation sites (UC2a / UC2b) and for address evaluation
(UC2c); it does not house the parser. `projectOpen` carries the persisted
`evalCanonical` string in views but does not parse it or call the numeric
evaluator.

The **language emitters (UC3) stay in the template layer**, per the
builder-base rule that language-specific syntax belongs in templates /
template utilities. The SV expression walk is a SystemVerilog template
helper consumed by the module-local parameterized-constant emission path
(the same area that emits parameterized declarations today), not a
`projectOpen` view. The C++/SystemC and firmware C walks live with the
C-style include/header emission helpers. Each exposes a thin API that
accepts the canonical expression string, parses it to IR, and emits
target-language text; the shared parser and node definitions remain in
`pysrc/evalExpr.py`.

## API Design

Three boundaries: the language-neutral module, its create-time consumers,
and the template-layer emitters. Symbol resolution and value lookup are
passed in as callbacks rather than wired to `ValueResolver`, keeping
`evalExpr.py` project-neutral. The callbacks are justified by concrete
policies at existing call sites (active value, worst-case maxValue,
per-variant addressing; SV versus C++ spelling), not speculative
flexibility.

### `pysrc/evalExpr.py` — language-neutral

IR nodes (pure data, walked externally):

```
class Num:    value: int; base: int  # base in {10,16,2}: authored radix, so
                                     # emitters re-spell in the dev's base
                                     # (octal is normalized to 16 at parse)
class Sym:    key: str            # qualified, e.g. "IP_DATA_WIDTH/ip_test"
class Unary:  op: str; operand    # op in {'+','-','~'}
class Bin:    op: str; lhs; rhs   # op in {+ - * / % & | ^ << >>}
class Clog2:  operand
```

Parsing:

```
def parse(text: str, qualify: Callable[[str], str | None] | None) -> Node
    # Accepts two symbol token forms:
    #   $NAME            bare; parser calls qualify(NAME) -> qualified key,
    #                    or None if unresolved (validation folds into parse).
    #   ${name/context}  already-qualified; parsed straight to Sym(key),
    #                    qualify not invoked (the canonical/reload form).
    # $clog2(...) is the function. Integer literals are SV literals:
    # unsized decimal or SV based literals (8'hFF, 'b1010, 12'd9). Raises
    # EvalParseError(message, col) on bad syntax, real literals, x/z digits,
    # C-style 0x prefixes, or an unresolved bare symbol.

def unparse(node: Node) -> str
    # Canonical serialization for persistence: symbols emitted as
    # ${qualified/key}, operators with normalized spacing, parentheses
    # restored via needsParens. Invariant: parse(unparse(n)) == n.
```

**Single validation gate.** All user-facing error handling lives in the
**create-time `parse` of user input** (syntax, unresolved symbols) and the
**create-time `evaluate`** (divide-by-zero). `unparse` and later parses of
the canonical string are **total** and trust their input: the canonical
string was produced by `unparse` from an already-validated tree, so any
failure while emitting from it is an internal invariant violation (corrupt
DB or generator bug), surfaced as an internal error, not a user diagnostic.
The emission path performs no re-validation.

Evaluation:

```
def evaluate(node: Node, resolve: Callable[[str], int]) -> int
    # resolve(symKey) -> the int to substitute for that symbol.
    # SV semantics: '/' truncates toward zero (not Python floor '//'),
    # '%' matches that truncation; $clog2 via arch2codeHelper.clog2.
    # Raises EvalEvalError on divide-by-zero.
```

Shared structural helper for the emitters (precedence is grammar, not
language syntax; SV and C++ orderings coincide for this subset):

```
PRECEDENCE: dict[str, int]                       # one table for both emitters
def needsParens(parentOp, child, side) -> bool   # restore grouping on emit
```

Errors: `class EvalParseError(Exception)` (carries message + column),
`class EvalEvalError(Exception)`.

### Create-time consumers in `processYaml.py`

Parse once, evaluate twice — replacing the two existing `eval()` sites:

```
node = evalExpr.parse(
    item['eval'],
    qualify=lambda n: resolver.qualifyKey(n, yamlFile, fatal=False))

# UC2a active value (replaces eval at processYaml.py:4911)
ret['value'] = evalExpr.evaluate(
    node, resolve=lambda k: resolver.lookupNamedRow(k, label)['value'])

# UC2b worst-case maxValue (replaces eval at processYaml.py:5077)
def resolveMax(k):
    row = resolver.lookupNamedRow(k, label)
    return row['maxValue'] if row['isParameterizable'] and row['maxValue'] \
        else row['value']
ret['maxValue'] = evalExpr.evaluate(node, resolve=resolveMax)
```

UC2c (address generation) reuses `evaluate` with a resolver bound to the
active (later per-variant) values.

### Template-layer emitters (consume `evalCanonical` from `projectOpen`)

```
# templates/systemVerilog/<module-local emission helper>
def emitSvCanonical(evalCanonical: str, symSpelling: Callable[[str], str]) -> str
    # Return a SystemVerilog expression string suitable for the RHS of a
    # module-local localparam.

# templates/systemc/includes.py and FW header helpers
def emitCStyleCanonical(evalCanonical: str, symSpelling: Callable[[str], str]) -> str
    # Return a C/C++ expression string suitable for a constexpr or FW header
    # initializer.
```

Caller contract:

- Pass the non-empty `evalCanonical` string from the `projectOpen` view.
- Provide `symSpelling(qualifiedKey) -> text` for the current emission site.
- Insert the returned expression string into the target declaration or
  initializer.
- Do not parse, rewrite, parenthesize, or numerically evaluate the
  expression in the caller.

`symSpelling` supplies the source-code spelling for one already-qualified
symbol at the current emission site. If the symbol is a parameter owned by
that site, it returns the parameter name. Otherwise it returns source text
from already-persisted project data, such as a constant row's `value` or an
enum row's numeric value formatted as a target-language literal. This is a
lookup/formatting decision for a single symbol, not evaluation of the eval
expression. The emitter helper then assembles those spellings into the
translated expression.

### Persistence / reload (UC4)

- **Persist:** `unparse(node)` — the canonical string with `${qualified/
  key}` symbols — in the new `constants.evalCanonical` column (distinct
  from the verbatim user-authored `eval` field), so the stored expression
  is context-independent. Non-`eval` constants store the empty string.
- **Reload:** `projectOpen` exposes `evalCanonical` as view data. Template
  emitter APIs consume that string directly; any internal canonical parse
  is hidden inside the emitter helper. Reload and emission do not call
  `evaluate`. No separate tree-serialization format — `parse`/`unparse`
  are the single source of truth for tree shape.

## E4 Status: Block-Local Declaration Selection Uses Dependency Closure

Stage E4 exposed a second selection problem beyond expression emission:
`isParameterizable` is not enough to decide which constants, types, and
structures a block can emit as module-local declarations.

`isParameterizable` answers only whether an object depends on some
parameterizable value somewhere in the project. It does not say whether a
particular block owns the module parameters needed to keep that object
symbolic in that block's SystemVerilog scope. Include-tree visibility is
also not enough: a visible declaration may ultimately depend on a parameter
owned by a different block.

The block-local declaration set must therefore be selected from a dependency
closure, not from `isParameterizable` alone. For a declaration emitted in a
block, every symbol in its expression/dependency graph must be one of:

- a module parameter owned by that block,
- a localparam emitted earlier in the same declaration set,
- or a non-parameterizable constant intentionally spelled from its persisted
  value.

Backing constants consumed as block params should remain module
`parameter`s, not be re-emitted as localparams. Eval-derived constants should
be emitted as module-local localparams only when their parameterizable
dependency closure is satisfied by the block's own params. Types and
structures should inherit closure requirements through width keys, array
size keys, variable types, sub-structures, and any eval-derived constants
they reference.

Resolved E4 behavior:

- A type or structure that uses an eval-derived parameterizable constant is
  selected when the derived constant ultimately depends only on the block's
  own params.
- Eval-derived constant chains are emitted symbolically as ordered
  module-local `localparam`s, so intermediate derived constants are not
  frozen to persisted numeric values.
- A visible parameterizable declaration from another include context is not
  emitted into a block whose params do not satisfy the declaration's full
  backing-parameter closure.
- Structures whose `arraySizeKey` names a selected eval-derived constant
  emit the symbolic localparam name in the SV packed-array range, not the
  resolved numeric value.

The implemented direction keeps the parser syntax-only, but preserves the
symbol facts it already knows so `projectCreate` can build a semantic
dependency graph.
`evalExpr.py` should continue to own only:

- the parsed expression tree,
- the canonical string from `unparse(node)`,
- the direct referenced-symbol set from `symbolKeys(node)`.

The parser should not classify symbols as block params, derived constants,
enums, or plain constants. That classification depends on project data that
is not complete, or not meaningfully block-local, at parse time.

During `projectCreate`, after eval parsing/evaluation and while the parsed
nodes are still available, the parsed eval nodes remain in memory and are
used to recover direct constant dependencies:

```python
evalConstDeps[constKey] = {
    "context": row["_context"],
    "symbols": evalExpr.symbolKeys(node),
}
```

`deriveParameterizedDeclSets()` turns those syntax-level symbol keys into
project-semantic declaration dependencies, because by then the relevant
project facts exist: constants, block params, include visibility, types,
structures, and structure variables. The per-declaration internal shape is:

```python
declDeps[("constant", constKey)] = {
    "paramDeps": set(),   # backing block-param constant keys required
    "localDeps": set(),   # ("constant"|"type"|"structure", key) emitted first
}

declDeps[("type", typeKey)] = {
    "paramDeps": set(),
    "localDeps": set(),
}

declDeps[("structure", structKey)] = {
    "paramDeps": set(),
    "localDeps": set(),
}
```

For constants, `localDeps` captures eval-derived constants referenced by the
expression; `paramDeps` is the transitive closure of backing params through
those local deps. For types, dependencies come from `widthKey`,
`widthLog2Key`, and `widthLog2minus1Key`. For structures, dependencies come
from variable types, sub-structures, and `arraySizeKey`. Non-parameterizable
constants and enums do not add `paramDeps`; they remain literal spellings at
emission sites.

Per block, `deriveParameterizedDeclSets()` now:

1. gather visible declarations by include context,
2. keep only declarations whose `paramDeps` are a subset of the block's own
   params,
3. include the selected declarations' required `localDeps` when those deps
   are also visible and satisfiable,
4. topologically order the final selected set by `localDeps`,
5. persist only the ordered result in `blockParameterizedDecls`.

This keeps the DB/view contract small: templates consume an ordered
block-local declaration list and format it. The richer dependency graph
remains a `projectCreate` implementation detail. The persisted
`blockParameterizedDecls` rows now carry `declKind` values for `constant`,
`type`, and `structure`; `projectOpen.getBDParameterizedDecls()` joins each
row to the corresponding body table for template consumption.

`ip_test` now carries example coverage for second-level eval-derived
constants:

- `IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2`
- `IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2`
- `ipDerivedWidthT` uses `IP_DATA_WIDTH_X4`
- `ipDerivedDepthMem` uses `wordLines: IP_MEM_DEPTH_X4` and an address type
  sized by `IP_MEM_DEPTH_X4`

The large struct-array case (`arraySize: IP_DATA_WIDTH_X4` with
`ipDataT`) is intentionally kept in `unittest/test_eval_sv_emit.py` rather
than the example YAML: it verifies SV symbolic array emission, but as a
full example structure its worst-case packed width currently exceeds the
SystemC structure emitter's supported packed-storage range.

## Implementation Stages

Each stage is independently verifiable. Per the project's testing
preference, verification favors make-driven runtime/asserts and emitted-code
checks plus parser/evaluator unit tests that execute functionality, rather
than reading back a committed generator DB.

- **E0 — Parser + IR module (standalone).** Create the new file
  `pysrc/evalExpr.py` holding the tokenizer, Pratt parser, and IR node
  classes. No integration with `processYaml.py` yet. Verify with unit tests
  covering precedence, associativity, unary, parentheses, `$clog2`,
  `$symbol`, SV integer literals (decimal and based forms such as `8'hFF` /
  `'b1010`), and rejection of out-of-grammar input — real literals, `x`/`z`
  digits, and C-style `0x` prefixes.
- **E1 — Evaluator.** `evaluate(node, resolve)` with SV semantics
  (truncating division). Unit tests, including division-toward-zero cases.
- **E1.5 — Migrate existing eval expressions to the SV subset.**
  **Status: DEFERRED (2026-06-10)** — back-burnered behind other conversion
  work. This does **not** block E2–E6: those stages develop and verify against
  the `ip_test` example, whose evals (`$IP_DATA_WIDTH * 2`,
  `$IP_FIXED_NIBBLE_COUNT + 1`) are already SV-valid and need no conversion, so
  it builds identically before and after the cutover. E1.5 covers the
  repo-wide migration of the **remaining** Python-syntax `eval` YAML (the
  debayer product `arch/yaml` plus the other `builder/base` examples and
  unittest arches); that migration is what those specific projects need before
  they build under the post-E2 generator, and it is independent of E2–E6
  development. The migration is scoped as a reusable, standalone Python→SV
  converter in
  [`plan-eval-python-to-sv-migration.md`](./plan-eval-python-to-sv-migration.md);
  pick it up when this stage is un-deferred.

  The
  current `eval` strings are authored in **Python**, not SV, and will not
  parse under the new grammar: `.bit_length()` (the dominant `_LOG2`
  idiom), floor `//`, real `/ 2.0`, and any C-style literals are all
  Python-only. A one-time conversion pass over the project YAML rewrites
  them into the SV subset — `($X-1).bit_length()` → `$clog2($X)` and
  `($X).bit_length()` → `$clog2($X + 1)`; `//` → `/` (the truncating
  evaluator matches Python floor for the non-negative operands these
  widths use); `valueType: real` evals become literal `value`s. This is in
  scope because the E2 cutover cannot land without it; the conversion is a
  small migration tool plus a manual review of the rewritten expressions.
- **E2 — Integrate evaluator into `projectCreate`.** Parse once; call the
  evaluator at the two existing sites (UC2a `processYaml.py:4911`, UC2b
  `processYaml.py:5077`); delete both `eval()` calls and the regex
  substitution helpers they used. Reject `valueType: real` with `eval`
  rather than preserving Python real-eval behavior. **Parity gate:**
  `make gen` / `make run` on the migrated (E1.5) examples must produce
  identical constant values and emitted code (no value drift for existing
  non-parameterized integer evals).
- **E3 — Persistence + reload (schema field approved).** Add the
  `constants.evalCanonical` string column following
  `config/SCHEMA_SPECIFICATION.md`; persist `unparse(node)` (qualified
  symbols) in `projectCreate`; expose the canonical string through
  `projectOpen` views without parsing or numeric evaluation. Verify the
  `parse(unparse(node)) == node` round-trip in parser tests and that
  generators receive the same canonical expression the evaluator used.
- **E4 — SV emission (the C4 deliverable).** **Status: implemented
  (2026-06-10).** Emit module-local
  `localparam` for eval-derived parameterizable constants from
  `evalCanonical`, using the `projectOpen` view plus the module-local SV
  template helper API. The implementation also selects block-local
  constants/types/structures by dependency closure and emits symbolic
  `arraySizeKey` ranges for selected eval-derived localparams. Verified with
  `make db`, `make gen`, and `unittest/test_eval_sv_emit.py`; full
  Verilator elaboration remains a follow-up if desired. Closes the deferred
  `evalCoupled` emission.
- **E5 — C++/SystemC and firmware C emission.** **Status: complete (SystemC
  C++ half 2026-06-11; firmware C half 2026-06-23).** The C-style emitter
  (`emitCStyleCanonical` + `_emitCNode` in `templates/systemc/includes.py`,
  the C/C++ analog of `package.py:emitSvCanonical`) translates `evalCanonical`
  to a C expression: operators pass through 1:1, `$clog2` → `clog2` (precedent
  `includes.py`), authored hex/binary re-spelled `0x..` / `0b..`, parentheses
  restored from precedence. `includeConfig` now emits eval-derived
  parameterizable constants symbolically into the `Config` structs, spelling a
  referent that is itself a struct member as its bare member name (declared
  earlier in dependency order) and any non-member referent from its persisted
  value. This **fixes a per-variant correctness bug**: the eval-derived
  `Config` members were previously frozen to the default-variant value across
  every variant (e.g. `ipVariant0Config` had `IP_DATA_WIDTH=8` but
  `IP_DATA_WIDTH_X2=140`), so the C++ `Config` disagreed with the
  symbol-correct SV localparams from E4. The derived constants must remain
  `Config` members because standalone templated type-encoder structs (e.g.
  `ipDerivedMemAddrSt<Config>` in `ipIncludes.cppm`) and `ip.cpp` reach them
  only as `Config::NAME`; a module-class-local constexpr would be invisible to
  those scopes. To make the bare name usable inside the block class, the class
  templates now also emit the same class-local alias the block params already
  use: `baseClassDecl.py` declares `static constexpr auto NAME = Config::NAME;`
  in the base class and `classDecl.py` re-imports it in the derived class as
  `using <Base>::NAME;` (a value, so no `typename`) — the E4 placeholders that
  skipped `declKind=='constant'` in both blocks are now filled. Verified with `make clean && make gen`
  (only `ipConfig.h` changes — derived members now read `IP_DATA_WIDTH * 2`
  etc.), `make run` on `ip_test` (model builds and runs, "No error"), and
  `unittest/test_eval_cpp_emit.py` (19g; emitter translation + real per-variant
  symbolic emission with dependency-order checks). Firmware C emission is a
  follow-up: it reuses the same `emitCStyleCanonical` walk with an FW-specific
  `symSpelling`. The exercising vehicle now exists (2026-06-23): `ip_test`
  enables the `includeFW` fileMap, so the `ip` context emits
  `fw/include/ip/ipIncludesFW.{h,cpp}` whose constants section is the FW
  back end's target (today it carries the non-parameterizable eval-derived
  `IP_FIXED_WORD_COUNT`; the parameterizable eval-derived constants
  `IP_DATA_WIDTH_X2` etc. are still skipped pending this stage). A base-only
  firmware TU (`fw/src/fwIpMain.{h,cpp}`) now performs the ip register
  read/write (moved out of the `cpu` model body, which retains only an apb
  transport seam) and consumes `ipIncludesFW.h` + `regAddresses.h`, so the FW
  header is build-verified and runtime-exercised by `make run` ("No error").
  The pro firmware BSP (`regRdWr.cpp` cross-thread queue) is unavailable to
  base examples, so the seam is a synchronous `ipRegBus` callback the cpu binds
  to its apb port rather than the product's global `regRead32`/`regWrite32`.
  FW constants emission (2026-06-23): `includeConstants` now detects fw mode
  (`args.mode == 'fw'`) and emits eval-derived parameterizable constants as flat
  `const`s via `emitCStyleCanonical`. FW has no per-variant `Config` struct, so
  the FW `symSpelling` keeps a referent that is itself an emitted FW eval
  constant symbolic (bare name, so `IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2`
  chains) and spells every other referent — block params and fixed constants —
  from its persisted default value (`IP_DATA_WIDTH_X2 = 70 * 2`). Non-eval
  parameterizable constants (the block params themselves) are still skipped:
  they have no single firmware value. `ip_test`'s firmware now consumes
  `IP_DATA_WIDTH_X2` (`fwCheckUIp1` write/readback). Verified with
  `make clean && make gen` (ipIncludesFW.h carries the symbolic constants),
  `make all && make run` (build + sim, "No error"), and
  `unittest/test_eval_cpp_emit.py` (`test_fw_constants_symbolic`: real
  projectCreate → getContextData → includeConstants emission with
  dependency-order and block-param-exclusion checks).
- **E6 — Variant-aware address evaluation (UC2c).** **Status: closed —
  not in C4 scope (2026-06-23).** The contingent scope question ("does C4
  want per-variant address-affecting evals?") is resolved as no.
  `calcAddresses` (`processYaml.py:3166`) sizes every parameterizable
  address object to its worst case — register/memory `width` uses
  `maxBitwidth` and `wordLines` uses the constant's `maxValue` — so offsets,
  `decodeSize`, and the overflow check are identical for every variant. All
  variants therefore share one address map (a smaller variant under-fills
  its worst-case slot), which is the property firmware and the SV register
  decoder depend on; per-variant address evaluation would *break* that
  shared map, not improve it. The invariant to preserve is that every
  address-affecting parameterizable constant carries a correct worst-case
  `maxValue`/`maxBitwidth`, not that addresses re-evaluate per variant. No
  code or variant fixture is required.

## Dependencies and Ordering

- E0 → E1 → E2 are prerequisites for everything; E2's parity gate must hold
  before emission stages.
- E1.5 (migration of existing Python-syntax evals) does **not** gate E2–E6
  development or verification: `ip_test` is already SV-valid and is the
  build-verifiable vehicle for the E2 parity gate and E4/E5 emission. E1.5 is
  required only before the **remaining** Python-syntax projects (debayer
  product `arch/yaml`, the other examples, the unittest arches) build under the
  post-E2 generator, since the new parser replaces the Python `eval()` and
  those expressions are not valid SV-subset input.
- E3 (persistence) is required before E4/E5, since the emitters run from
  `projectOpen` views and need the persisted canonical expression string.
- E4 and E5 are independent of each other (mirrors the C2/C3 independence
  in `plan-param-constant-collision.md`).
- The constant→constant reference edge currently discarded at parse
  (`plan-param-constant-collision.md:498`) is re-established by E3's stored
  expression, which is what the deferred `evalCoupled` work needed.

## Resolved Decisions

- **Integer-only eval.** The symbolic eval IR supports integer constants
  only; `valueType: real` with `eval`, real literals, and typed real
  expression semantics are out of scope.
- **Operator set.** The first-cut grammar keeps only operators with direct
  SV/C++ spelling: `+ - * / % & | ^ ~ << >>`. Excluded operators include
  `**`, `~^`, `^~`, arithmetic shifts, ternary, relational/logical
  operators, and `$bits`.
- **Literal syntax is SV, not C.** Integer literals are SystemVerilog
  literals only: unsized decimal and SV based literals (`8'hFF`, `'hFF`,
  `'b1010`, `12'd9`), with `_` separators allowed. C-style `0x` / `0o` /
  `0b` prefixes are not accepted, and `x` / `z` digits are rejected as
  non-evaluable. This keeps the whole authoring grammar consistently SV
  rather than a C/SV hybrid.
- **Literals preserve the authored base.** `Num` records the authored radix
  (decimal/hex/binary; octal is normalized to hex at parse since C has no
  clean octal spelling); emitters re-spell the literal in the developer's
  base (SV `'hFF`, C++ `0x..`), and `unparse` persists it in the
  unsized SV based form. This keeps width/count math in decimal and
  address/mask constants in hex, matching today's split convention (decimal
  constant packages, hex address headers). The authored bit width on a sized
  literal is dropped: the evaluator models unbounded integers, so a width is
  neither needed nor reproduced.
- **Existing evals are migrated, not grandfathered.** The current eval
  strings are Python (`.bit_length()`, `//`, real `/ 2.0`) and are
  converted to the SV subset in E1.5; the parser does not accept Python
  syntax for backward compatibility.
- **Division/modulo semantics.** Integer `/` truncates toward zero and `%`
  follows that quotient (`a % b == a - (a/b)*b`). The evaluator must not
  use Python `//` or Python `%`; divide-by-zero raises `EvalEvalError`.
- **Persistence form.** Store `unparse(node)` in
  `constants.evalCanonical` for eval rows and the empty string for non-eval
  rows; expose non-empty canonical strings through `projectOpen` views.
- **No open/template evaluation.** `projectOpen` does not parse or evaluate
  eval expressions. Template-layer emitter APIs parse the canonical string
  only to translate it to target-language text. Any required numeric result
  is a `projectCreate` responsibility and must be persisted before
  generation.
- **Emission placement.** Symbol spelling is decided per emission site:
  parameters owned by that site remain symbolic, while other constants,
  foreign parameters, and enums are spelled from already-persisted project
  data. Firmware C reuses the C-style expression walk with firmware-specific
  spelling.
- **Error boundary.** User-facing syntax, unresolved-symbol, real-literal,
  and divide-by-zero errors are create-time diagnostics. Emitting from a
  stored canonical expression trusts the DB and treats parse failure as an
  internal invariant violation.

## Out of Scope

- The `**`, `~^`, `^~`, arithmetic-shift, ternary, relational/logical, and
  `$bits` features excluded by the frozen grammar.
- Real-valued `eval` expressions. `valueType: real` constants may remain
  literal values, but real expression parsing/evaluation/emission is not
  part of this integer symbolic-eval pipeline.
- Any change to how non-`eval` constants, enums, or type widths are
  resolved or emitted.
