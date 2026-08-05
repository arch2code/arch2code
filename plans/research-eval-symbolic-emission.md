# Research: Symbolic Eval Constants and Language-Neutral Emission

Date: 2026-06-09
Status: decision recorded (2026-06-09) — **authoring language is a
SystemVerilog constant-expression subset**, and the parser is an
**in-house precedence-climbing parser (Option A)**. The first-cut grammar
is frozen (see "Authoring Language"). Remaining open questions are
evaluation/emission details and schema plumbing, not the parser choice.
Owner: C4 (`plan-param-constant-collision.md`), follow-on to
`plan-variant-config-unification.md`.

This document opens the design space for the deferred **C4** problem:
variant-aware re-evaluation and multi-language emission of `eval`
constants. It states the problem precisely, surveys the option space
requested by the user — build our own evaluator, adopt a third-party
library, or something else — records the decisions reached, and tracks the
open questions that remain.

## Problem Statement

An `eval` constant is a `constants:` entry whose value is a computed
arithmetic expression over other constants, for example:

```yaml
IP_DATA_WIDTH_X2: { eval: "$IP_DATA_WIDTH * 2", desc: "..." }
```

Today the generator resolves such an expression **once, at parse time, to
a single integer**:

- `processYaml.py:4888`-`4921` handles the `eval` field type.
- Each `$TOKEN` is replaced with its referent's resolved integer value
  through `re_constReplace` (`processYaml.py:6196`).
- The substituted string is handed to Python's built-in
  `eval(myVal, {}, {})`, and the resulting integer is stored as the
  constant's `value`.
- The original expression text is then **discarded**: the `constants`
  table persists no expression string and no constant-to-constant
  reference edge. This is recorded as a deliberate parse-time decision in
  `plan-param-constant-collision.md:498`-`504`.

Downstream, that single integer is emitted as a literal into every target
language — a SystemVerilog package `localparam` (`package.py:95`-`119`), a
SystemC include constant, and a firmware C header.

This is correct only while every input is a single project-wide value. It
breaks under parameterization. Once `IP_DATA_WIDTH` becomes a per-instance
block parameter that takes different values per variant, the derived
constant `IP_DATA_WIDTH_X2`:

- Has **no single correct integer** — its value depends on the variant.
- Must be emitted as a **symbolic expression** that re-evaluates against
  the instance's parameters, not as a baked literal:
  - SystemVerilog: a module-local `localparam` inside the parameterized
    module, computed from the module's parameters.
  - SystemC: a `Config<Variant>::` member or a `constexpr` derived from
    `Config`.
  - Firmware C header: discussed under Open Questions — firmware targets a
    concrete built variant and may still want the resolved integer.

The core requirement that follows:

> The generator must capture each `eval` expression in a
> **language-neutral form** that can be (a) re-evaluated numerically given
> a concrete set of input values per variant, and (b) re-emitted as
> idiomatic source text in SystemC, SystemVerilog, and firmware C.

The expression grammar **in current use** is a subset of Python arithmetic,
because the parse-time path literally calls Python `eval`:

- Integer literals.
- Symbol references (`$TOKEN`) to constants and enums.
- Binary operators: `+`, `-`, `*`, `//` (Python integer/floor division),
  `%`, `**`, and bit operations where used.
- Parentheses for grouping.
- The `clog2(...)` function (ceiling log base 2), with the established
  dual-language spelling `clog2(...)` in C++ (`includes.py:85`) and
  `$clog2(...)` in SV (`package.py:28`); the Python helper is
  `arch2codeHelper.py:9`.

### Proposed authoring language: SystemVerilog constant-expression subset

The domain users are hardware engineers, and the dominant target is
SystemVerilog. It therefore makes sense to **define the authoring language
as a subset of SystemVerilog elaboration-time (constant) expressions**
rather than Python. The author writes what is, in effect, the body of an
SV `localparam`. The proposed operand and operator set:

- **Integer literals** and symbol references to constants, enums, and
  (under parameterization) block parameters.
- **Arithmetic:** `+`, `-` (binary and unary), `*`, `/`, `%`. The `**`
  power operator is excluded for now (decided 2026-06-09): it is the only
  operator with no one-to-one C++ spelling, and no current expression needs
  it. May be revisited if a concrete need arises.
- **Bitwise:** `&`, `|`, `^`, `~`, and `~^` / `^~` (xnor).
- **Logical shifts:** `<<`, `>>` only. Arithmetic shifts (`<<<` / `>>>`)
  are excluded: width and parameter values are non-negative integers, for
  which logical and arithmetic right shifts are identical, so the
  arithmetic variants add nothing (decided 2026-06-09).
- **Conditional (ternary):** excluded for now (decided 2026-06-09). It
  would pull in the relational/logical operator set its condition requires
  (`==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||`, `!`); none of these are in
  the first cut. May be revisited if a concrete need arises.
- **System functions:** `$clog2(...)` only (decided 2026-06-09). `$bits`
  and other constant-time functions are excluded; arch2code already owns
  type widths through its type system, so they add no value here.
- **Parentheses** for grouping.

This reframing has three consequences that reshape the option analysis
below:

1. **The front-end parser is no longer Python-shaped.** SV-specific syntax
   — `$clog2` with its dollar sign, and the `?:` ternary — is **not valid
   Python**, so Python's standard-library `ast.parse` can no longer serve
   as the front end. This substantially weakens Option C1 and shifts the
   lean toward an SV-aware parser (own or library).
2. **Integer-division semantics align with C++.** SV integer `/`
   truncates toward zero, as does C++ integer `/` (since C++11). Choosing
   SV as the source language removes the Python `//` floor-division-versus-
   C++ truncation mismatch that the Python-source framing carried.
3. **SV emission becomes near-identity.** The authored text is already SV;
   the SV emitter mainly re-spells symbols (module parameters) and is
   otherwise a pass-through. The real transform work moves to the C++/
   SystemC and firmware emitters (`$clog2` → `clog2`, `**` has no C++
   operator, etc.).

### Existing precedent

A symbolic, dual-language emission path already exists for type widths.
`typeWidthExpression_cpp` (`includes.py:66`-`103`) and the SV counterpart
in `package.py` already emit `clog2(C+1)` / `$clog2(C+1)` rather than a
resolved width. This proves the pattern — per-language spelling of the
same symbolic relationship — is already accepted in the codebase. C4
generalizes it from the fixed `clog2(width)` shape to arbitrary
user-authored expressions.

### Secondary benefit: removing `eval()`

The current path executes user-authored text through Python's built-in
`eval()`. Any approach that parses the expression into a validated,
allow-listed structure removes that arbitrary-code-execution surface as a
side effect. This is not the primary driver but is a real benefit worth
weighing.

## Scope and Non-Goals

In scope:

- Choosing a representation for `eval` expressions that survives past
  parse time.
- Numeric re-evaluation of that representation per variant.
- Emission of that representation into SystemC, SystemVerilog, and
  firmware C.

Out of scope for this document (flagged, not solved):

- Persisting the constant-to-constant reference edge in the schema (a
  prerequisite plumbing task; see `plan-param-constant-collision.md:498`).
- The multi-block input case — an expression whose inputs are parameters
  of more than one block, which no single SV module can compute. This
  needs a placement rule and is noted under Open Questions.
- Firmware-side variant selection policy.

## Option Space

### Option A — Build our own evaluator and emitter

Write a dedicated tokenizer and recursive-descent (or shunting-yard)
parser for the expression grammar above, producing a small in-house
expression tree. Provide three consumers: a numeric evaluator and one
emitter per target language.

- **Pros:**
  - Full control of the grammar; `clog2` and the `//` integer-division
    semantics are first-class rather than coerced.
  - No new external dependency in the builder toolchain.
  - The expression tree is exactly the language-neutral IR C4 needs, with
    no impedance mismatch.
  - Smallest possible runtime surface; easy to validate node-by-node.
- **Cons:**
  - We own a parser, including operator precedence, associativity, unary
    minus, and error reporting — classic sources of subtle bugs.
  - Re-implements functionality that already exists in the standard
    library (see Option C1).
  - Ongoing maintenance burden as the grammar grows.

### Option B — Adopt a third-party library

Pull in an external package to handle parsing and/or evaluation.
Candidates considered, now weighed against an **SV-subset** source
language:

- **`pyparsing` / `lark`** — general parser frameworks. We author an
  SV-constant-expression grammar and the framework handles tokenizing,
  precedence, and tree construction. Under the SV-source framing this is
  the strongest library option: the grammar is small and the framework
  removes the most error-prone hand-written code. Cost: a build-toolchain
  dependency where there is none today, and the three emitters remain ours.
- **SV-aware parsers (`pyslang`, `hdlConvertor`)** — parse real
  SystemVerilog and can expose an expression AST, matching the source
  language exactly and potentially evaluating constant expressions for us.
  Cost: heavy, SV-toolchain-grade dependencies for what is a small grammar;
  likely disproportionate.
- **`sympy`** — symbolic algebra. Heavy, performs unwanted simplification,
  no native `$clog2`, no SystemVerilog printer. Overkill.
- **`asteval`** — safe Python-expression evaluation. Tied to Python syntax
  (so incompatible with the SV-source framing) and produces a value, not a
  reusable tree. Does not address multi-language emission.

- **Pros:** mature parsing; less hand-written parser code (`lark`/
  `pyparsing`); exact source-language match (`pyslang`).
- **Cons:** adds an external dependency to a standard-library-only
  toolchain; no surveyed library emits SystemVerilog *and* C++, so the
  emitters remain our work regardless.

### Option C — Something else

Three sub-options that do not fit cleanly into "from scratch" or
"third-party."

#### C1 — Reuse the Python standard-library `ast` as the front end (hybrid)

Parse each expression with `ast.parse(expr, mode='eval')`, validate the
node tree against an allow-list, and use it as the IR with a numeric
evaluator and three per-language emitters.

- **Status under the SV-source framing: largely invalidated.** This option
  only works if the authoring language stays Python-shaped. Under the
  proposed SV-constant-expression authoring language it fails at the front
  door: `$clog2(...)` and the `?:` ternary are not valid Python and
  `ast.parse` rejects them. It remains listed only as the alternative that
  would apply *if* the authoring language were kept Python-shaped — a
  choice this document recommends against, given the hardware-engineer
  audience.
- **If authoring stayed Python-shaped, pros/cons:** the standard library
  supplies a correct parser at no dependency cost and the allow-list
  removes the `eval()` surface; but the audience would author in a
  non-native syntax, and operator mapping (`//` floor versus C/SV
  truncation) would need correction.

#### C2 — Per-language string rewriting of the retained expression

Persist the raw expression string and, at emit time, transform it with
targeted substitutions: replace symbol names with the language-scoped
spelling (`Config::NAME`, module parameter, macro), swap `clog2` ↔
`$clog2`, and rewrite operators (`//` → `/`).

- **Pros:**
  - Minimal new machinery; closest to the current code.
- **Cons:**
  - String rewriting without a parse tree is fragile: operator rewrites,
    precedence-sensitive substitutions, and nested calls are error-prone.
  - Directly contradicts the builder-base guidance discouraging string
    processing for field extraction and lookup (see `builder/base`
    rules). Not recommended, included for completeness.

#### C3 — Structured expression authoring in YAML

Change the authoring surface so users write a structured operation tree in
YAML instead of an expression string, removing the parsing step entirely.

- **Pros:**
  - No parser at all; the IR is authored directly.
- **Cons:**
  - Significant ergonomic regression — `{op: mul, args: [$IP_DATA_WIDTH,
    2]}` versus `"$IP_DATA_WIDTH * 2"`.
  - Breaks every existing `eval` author. High migration cost for marginal
    benefit. Included for completeness.

## Comparison Summary

Axes are weighed for an **SV-subset authoring language** (the recommended
framing).

| Axis | A: own SV parser | B: parser framework | B: SV-aware lib | C1: stdlib `ast` | C2: string | C3: structured YAML |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| New dependency | none | yes | yes (heavy) | none | none | none |
| Parses SV source syntax | yes | yes | yes | **no** | n/a | n/a |
| Reusable IR for all emitters | yes | yes | yes | yes | no | yes |
| Removes `eval()` surface | yes | yes | yes | yes | yes | yes |
| SV emission near-identity | yes | yes | yes | n/a | yes | yes |
| Emitter work still ours | yes | yes | partial | yes | yes | yes |
| Author writes native SV | yes | yes | yes | **no** | yes | no |
| Implementation effort | medium | low–medium | low (front end) | n/a | low | medium |

## Decision: Option A — In-House Parser (2026-06-09)

**Selected: Option A, an in-house precedence-climbing (Pratt) parser, with
no external dependency.** The decisive factors:

- The grammar is small and **frozen** (seven binary precedence levels plus
  unary; ternary, relational/logical, `**`, and arithmetic shifts are all
  excluded). A framework's principal benefit — taming a large or evolving
  grammar — does not apply.
- The builder toolchain is **standard-library-only** today. A framework
  (`lark` / `pyparsing`) would add a dependency (packaging, version
  pinning, CI availability) for marginal code saving over a hand-written
  Pratt parser at this grammar size. This is consistent with the
  builder-base simplicity rules.
- Option A yields exactly the IR the emitters need, parses the native SV
  syntax, makes SV emission near-identity, and rejects out-of-grammar input
  by construction (removing the `eval()` surface).

**Rejected:**

- **Option B** (parser framework or SV-aware library) — dependency cost not
  justified for a frozen seven-level grammar; SV-aware libraries
  (`pyslang`, `hdlConvertor`) are disproportionately heavy.
- **Option C1** (Python `ast`) — cannot parse `$clog2`; only viable if
  authoring were kept Python-shaped, which is rejected for this audience.
- **Options C2 / C3** — documented but not recommended (fragile string
  rewriting; authoring-ergonomics regression).

### Proposed architecture

A single pipeline with one front end and three back ends:

- **Tokenizer** — regex scanner producing tokens: integer literals,
  `$symbol` references, the `$clog2` function, operators (`+ - * / % & | ^
  ~ ~^ ^~ << >>`), parentheses, and the `clog2` argument's parentheses.
  `$clog2` is distinguished from a `$symbol` by the trailing `(`.
- **Parser** — precedence-climbing driven by a binding-power table (the
  seven-level table above), with unary-prefix handling for `+ - ~`. Builds
  a small node-tree IR.
- **IR node set** — `Num`, `Sym`, `Unary(op, operand)`, `Bin(op, lhs,
  rhs)`, `Clog2(operand)`. This tree is the language-neutral construct
  persisted/derived for C4.
- **Back end 1 — Python evaluator** — `evaluate(node, symbolValues) -> int`
  for DB default values and per-variant values. Mirrors SV constant
  semantics; integer `/` truncates toward zero (Open Question 2), not
  Python floor `//`.
- **Back end 2 — SV emitter** — near-identity walk; re-spells `$symbol` to
  the module-scoped parameter name. `$clog2` and all operators pass
  through.
- **Back end 3 — C++/SystemC emitter** — walk emitting `clog2` for
  `$clog2` (existing precedent) and the scoped symbol spelling
  (`Config::NAME`); every retained operator has a one-to-one C++ spelling,
  so no operator special-casing is needed.

Estimated size: roughly 150–250 lines plus unit tests.

The staged implementation derived from this decision lives in
[`plan-eval-symbolic-emission.md`](./plan-eval-symbolic-emission.md),
organized around the four use cases (parse, evaluate, emit, persist).

## Open Questions

1. **Operator-set scope — resolved (2026-06-09).** The first-cut grammar
   is: arithmetic (`+`, `-`, `*`, `/`, `%`), bitwise (`&`, `|`, `^`, `~`,
   `~^` / `^~`), logical shifts (`<<`, `>>`), `$clog2`, symbol references,
   and parentheses. Excluded: the `**` power operator, arithmetic shifts
   (`<<<` / `>>>`), the `?:` ternary, and the relational/logical operators
   a ternary would require. With `**` gone, every included operator has a
   one-to-one C++ spelling.
2. **SV evaluation semantics in Python — resolved (2026-06-09).** Integer
   `/` truncates toward zero and `%` takes the dividend's sign (`a % b ==
   a - (a/b)*b`); both match SV and C++ exactly, so C++ emission of `/` and
   `%` is identity. The evaluator must **not** use Python `//` (floor) or
   Python `%` (divisor-signed); it implements truncating div/mod with an
   abs-based integer helper (no float, exact for all magnitudes).
   Divide-by-zero raises `EvalEvalError`, surfaced as a create-time error.
   In practice operands are non-negative width/depth/parameter values, for
   which truncation and floor coincide, so no current result changes;
   signedness/self-determined-width nuances are out of scope (unbounded
   Python integers, non-negative magnitudes).
3. **System-function allow-list — resolved (2026-06-09).** `$clog2` is the
   only system function in the first cut; its C++ spelling drops the `$`
   (`clog2`, per the existing precedent). `$bits` is excluded: arch2code
   already owns type widths through its type system (e.g.
   `resolveTypeWidth`, the `widthLog2` machinery), so an author references
   a type or its width constant rather than `$bits(T)`, and `$bits` has no
   one-to-one C++ spelling. May be revisited if a concrete need arises.
4. **Firmware emission — resolved (2026-06-09).** FW follows the C++
   emission rules (operators, `clog2`, and literals are already largely
   identical); no separate FW back end — it reuses the C-style emission
   walk with a FW-specific `symSpelling`.
5. **Multi-block inputs — resolved (2026-06-09).** Not an impossibility and
   not rejected. Emission is decided per site: a symbol that is one of the
   emitting module/variant's parameters is emitted symbolically; every
   other symbol resolves to its integer literal. So any module can emit any
   expression, mixing its own parameters (symbolic) with others' values
   (literal). Assumption (already enforced by the parameter/include model):
   genuine cross-block coupling is expressed via the block's own parameter,
   so the eval references that block's parameter, not a foreign instance's.
6. **Schema plumbing — resolved (2026-06-09).** Add a new `constants`
   string column holding the canonical `unparse(node)` form (user-approved);
   it re-establishes the constant-to-constant edge previously discarded at
   parse (`plan-param-constant-collision.md:498`). Follows
   `config/SCHEMA_SPECIFICATION.md`.

All research open questions are now resolved. Remaining work is execution
per `plan-eval-symbolic-emission.md`.
