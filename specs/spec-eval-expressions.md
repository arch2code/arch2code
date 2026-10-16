# Specification: eval expressions

An `eval:` field is an integer SystemVerilog constant expression. `make db` parses it once,
evaluates it to an integer, and stores both the integer and a canonical copy of the expression
in the database. Generators never evaluate an expression. A constant that does not depend on a
block parameter is emitted as its integer value. A constant derived from a block parameter is
emitted as an expression in every target language, so each variant computes its own value: a
module-local `localparam` in SystemVerilog, a class constant in the C++ Base class, and a flat
constant in firmware headers. One parser (`pysrc/evalExpr.py`) serves user input, persistence
and emission, so the value `make db` computes and the text the generators emit come from the
same tree.

Scope: this spec covers the expression language, its evaluation, persistence and emission, and
the migration of Python-syntax evals. It does not cover parameter declaration, variants or
bindings (`specs/spec-parameter-inheritance.md`). The user-facing side is taught by
`rules/skills/design-types-structures.md` (writing `eval:`), `rules/skills/design-parameterizable-blocks.md`
(derived parameterizable constants) and `rules/skills/migrate-project.md` (converting old evals).

## 1. Where `eval:` appears

| Section | Field | Persisted |
| :--- | :--- | :--- |
| `constants:` and `ipParameters: constants:` | `value` | `value`, `evalCanonical`, `maxValue`, `isParameterizable` |
| `types:` / `enums:` entries under `enum:` | `value` | `value` only |

The schema declares these fields with the `eval` field type (`config/schema.yaml`), handled in
`pysrc/processYaml.py::processSimple`. When an entry gives both `value:` and `eval:`, `value:`
is used and the expression is ignored. An entry with neither is an error.

In-tree examples: `examples/ip_test/ip/yaml/ip.yaml` (parameterizable chain
`IP_DATA_WIDTH_X2`, `IP_DATA_WIDTH_X4`, and the fixed `IP_FIXED_WORD_COUNT`),
`examples/mixed/arch/yaml/mixed.yaml` (an eval referencing an enum value, an enum entry
computed by eval, and `$clog2` over a sum, `$clog2($DWORD + 1)`), `examples/nested/yaml/nested.yaml`
(`$clog2` over a constant, `$clog2($NUM_TAGS)`).

## 2. Grammar

**Literals.** SystemVerilog integer literals only.

- Unsized decimal: `255`, `4_095`.
- Based, sized or unsized: `8'hFF`, `'hFF`, `'b1010`, `12'd9`, `'o17`. The signed marker
  (`'sh80`) is accepted and has no effect. `_` separators are allowed in every base.
- Rejected: C-style `0x`/`0o`/`0b` prefixes, `x`/`z`/`?` digits, real literals (`1.5`, `1e3`).

**Symbols.**

- `$NAME` names a constant or an enum value in the row's include scope (its own file, its
  includes and their includes). The first match in include order wins, so a name in the row's
  own file shadows an included one. An unresolved name is an error.
- `${name/context}` is the qualified form. It is what the database stores (section 5); authors
  write `$NAME`. An authored qualified form is accepted as written and is not checked against the
  include scope, so it can reach a constant in a file the row does not include.

**Function.** `$clog2(expr)` is the only function.

**Operators**, tightest first. All binary operators are left-associative.

| Level | Operators |
| :--- | :--- |
| unary | `+ - ~` |
| 8 | `* / %` |
| 7 | `+ -` |
| 6 | `<< >>` |
| 5 | `< <= > >=` |
| 4 | `== !=` |
| 3 | `&` |
| 2 | `^` |
| 1 | `\|` |
| conditional | `c ? a : b`, right-associative, looser than every binary operator |

The binary levels are `pysrc/evalExpr.py::PRECEDENCE`; the conditional is parsed by
`_Parser._ternary` into a `Cond` node. Parentheses group and are not stored; grouping survives
as tree shape and the emitters restore parentheses from precedence
(`pysrc/evalExpr.py::needsParens`).

**Excluded:** `**`, `~^`, `<<<` and `>>>`, `&&`, `||` and `!`, `$bits` and every other system
function, and a lone `=` (diagnosed as a probable `==`). `^~` is not rejected: it parses as `^`
followed by unary `~`, which has the same value as SV XNOR. Every retained operator has the same
spelling and precedence in SystemVerilog, C++ and C, so the emitters copy each operator's
spelling and restore only parentheses. Two adjacent unary operators are the exception
(section 9).

## 3. Semantics

`pysrc/evalExpr.py::evaluate` follows SystemVerilog and C++ integer semantics, not Python.

- Integers are unbounded. No bit width is modelled: the width on a sized literal is dropped,
  nothing truncates, and `~x` is `-x - 1`. Mask with `&` when a complement is intended
  (`($N & ~$MASK) << 2`).
- `/` truncates toward zero. `%` follows that quotient, `a % b == a - (a / b) * b`, so it takes
  the sign of the dividend.
- Relational and equality operators yield 0 or 1. A conditional takes its first branch when the
  condition is nonzero.
- `$clog2(x)` is the ceiling of log2 x (`pysrc/arch2codeHelper.py::clog2`); `$clog2(1)` is 0.
- A literal's authored base is kept for presentation (`Num.base`): decimal, hex or binary.
  Octal is recorded as hex, because C has no clean octal spelling. The base never affects the
  value.
- These raise a create-time error: division or modulo by zero, a negative shift count, and
  `$clog2` of a value of 0 or less.

A constant's declared `valueType` (default `uint`) is checked against the result: a negative
`uint` result is an error, and `valueType: int` allows negative results. `valueType: real` cannot
use `eval:`; a real constant takes a literal `value:`.

## 4. Values

`pysrc/processYaml.py::_constants` stamps every constant row with three facts.

| Field | Meaning |
| :--- | :--- |
| `value` | The active value: the expression evaluated with each referent's `value`. For a derived parameterizable constant this is its value at the root parameters' declared defaults. |
| `isParameterizable` | True when the expression names any parameterizable constant (a derived constant), or for a constant without a parameterizable referent that is declared under `ipParameters:` or given `maxValue` or `isParameterizable: true` (a direct one; `maxValue` is then required). |
| `maxValue` | Derived constant: the same tree evaluated with each parameterizable referent at its `maxValue` and every other referent at its `value`. Direct: the author's `maxValue`. Otherwise 0. |

A direct parameterizable constant must declare a `maxValue` greater than 0 with `value` not
above it; `maxValue` also accepts a quoted integer string such as `"0x10"`.

Rules for a derived constant:

- `maxValue` is computed, never written. `make db` rejects a hand-written one.
- The computed `maxValue` must be greater than 0, and `value` must not exceed it.
- It cannot back a block parameter. A name in a block's `params:` must resolve to a plain
  (non-eval) `ipParameters:` constant (`pysrc/processYaml.py::_post_validateBlockParamBacking`).

The `maxValue` evaluation substitutes every referent's maximum at once. That gives the largest
result for an expression that grows with each of its parameters (sums, products, `$clog2`). It
is not a bound for an expression that shrinks as a parameter grows, such as `$A - $B` or
`$A / $B`.

Address allocation (`pysrc/processYaml.py::calcAddresses`) sizes a parameterizable register or
memory from `maxBitwidth` and from the `maxValue` of a parameterizable `wordLines` constant. Every
variant therefore shares one address map, and a smaller variant under-fills its slot. Values for
a specific variant are evaluated at `make db` by `pysrc/valueResolver.py::ValueResolver` with that
variant's bindings, which re-evaluates a derived constant's stored tree with the bound values.

## 5. Persistence

`constants.evalCanonical` holds `pysrc/evalExpr.py::unparse(node)` for an eval row and the empty
string otherwise. The schema places `evalCanonical` before `value` so the generic optional-field
pass does not overwrite it. The canonical form:

- spells every symbol in the qualified `${name/context}` form, so reading it back needs no
  include-chain walk. The braces are needed because `/` is also the division operator;
- spells literals in unsized SV form in their authored base (`255`, `'hff`, `'b1010`);
- separates binary operators and `?`/`:` with single spaces and re-inserts only the
  parentheses precedence requires.

`examples/ip_test/ip/yaml/ip.yaml` declares `IP_DATA_WIDTH_X2: {eval: "$IP_DATA_WIDTH * 2"}`;
the stored canonical is `${IP_DATA_WIDTH/<context>} * 2`, where `<context>` is the context key
of the file that declares `IP_DATA_WIDTH`.

The contract is `parse(unparse(node)) == node`, so the tree `make db` evaluated and the tree an
emitter walks are the same (one exception, section 9). `projectOpen` exposes `evalCanonical` as
ordinary row data and never parses or evaluates an expression. An emitter parses the canonical
string inside `pysrc/emissionUtils.py::emitExpr` only to translate it. Any number a generator
needs (`value`, `maxValue`, addresses, per-variant widths) was computed and persisted by
`projectCreate`. `unittest/test_eval_canonical_view.py` enforces this by trapping
`evalExpr.parse` and `evalExpr.evaluate` during `projectOpen`.

## 6. Emission

`pysrc/emissionUtils.py::emitExpr(evalCanonical, symSpelling, lang)` walks the tree. `lang` is
`emissionUtils.SV` or `emissionUtils.C` and fixes two leaves: the log2 spelling (`$clog2` or
`clog2`, the latter from `common/systemc/clog2.h`) and literal spelling (SV `'hff`/`'b101`, C
`0xff`/`0b101`). The emission site supplies `symSpelling`, which decides how each referenced
constant is written. That choice is the whole difference between the sites below.

| Site | Fixed eval constant | Derived parameterizable constant |
| :--- | :--- | :--- |
| SV context package | `localparam int unsigned NAME = 32'h...` (the value) | omitted |
| SV module | not declared | `localparam NAME = <expr>;` in module scope |
| SV HDL wrapper | not declared | `localparam NAME = <expr>` in the parameter port list, ahead of the ports whose widths use it |
| C++ context module | `inline constexpr uint32_t NAME = <value>;` | omitted |
| C++ per-variant `Config` struct | not a member | not a member |
| C++ `<block>Base` class | not declared | `static constexpr auto NAME = <expr>;` |
| C++ derived block class | not declared | `using <block>Base<Config>::NAME;` |
| Firmware header | `inline constexpr uint32_t NAME = <value>;` | `inline constexpr uint32_t NAME = <expr>;` |

A fixed constant's emitted type follows its `valueType` and magnitude: SV `int unsigned` or
`longint unsigned` for `uint` and `int` or `longint` for `int`; C++ and firmware `uint32_t` or
`uint64_t`, and `int32_t` or `int64_t`.

**SystemVerilog.** A package cannot be parameterized, so the package skips every
parameterizable declaration (`templates/systemVerilog/package.py::render`). Each parameterizable
block declares the ones it can use inside its own modules. `pysrc/processYaml.py::deriveParameterizedDeclSets`
selects them at `make db` and persists the ordered set in the `blockParameterizedDecls` table.
A derived constant, type or structure is selected for a block when all of these hold:

- its declaring context is visible from the block's file;
- every backing parameter in its dependency closure is one of the block's own `params:`;
- every derived constant, type or structure it depends on is also selected.

Selected declarations are ordered so each follows the declarations it uses.
`templates/systemVerilog/package.py::parameterizedDeclLines` renders them, spelling a block
parameter by its SV parameter name, an earlier selected localparam by its name, and any other
referent as its persisted value. `examples/ip_test/ip/rtl/ip.sv` carries:

```systemverilog
localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2;
localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
typedef logic[IP_DATA_WIDTH_X4-1:0] ipDerivedWidthT;
```

The same set is emitted by the register module, the APB decoder and the HDL wrappers.

**C++.** A `Config` struct carries only the root parameters a variant binds
(`templates/systemc/config.py`). A derived constant appears in two forms.

- In the block's Base class (`templates/systemc/baseClassDecl.py::renderClass`) it is a class
  constant in the block's `parameterizedDecls` order, with block parameters spelled
  `Config::NAME` and earlier derived constants by bare name. The derived class re-imports it
  (`templates/systemc/classDecl.py`). From `examples/ip_test/ip/base/ipBase.cppm`:

  ```cpp
  static constexpr auto IP_DATA_WIDTH_X2 = Config::IP_DATA_WIDTH * 2;
  static constexpr auto IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
  ```

- Anywhere else, a reference to it expands inline to its parenthesized expression over the
  root parameters (`pysrc/emissionUtils.py::constReference_cpp`,
  `templates/systemc/includes.py::constReferenceValueKeyed_cpp`). Inside a value-keyed `_v`
  template a root parameter is the template's own value parameter and spells bare. Examples:
  `((Config::IP_MEM_DEPTH * 2) * 2)` in `examples/ip_test/ip/model/ip.cppm` and
  `clog2(((IP_MEM_DEPTH * 2) * 2))` in `examples/ip_test/ip/model/ipIncludes.cppm`.

A block whose derived declarations use `$clog2` includes `clog2.h` (`blockUsesClog2`, from the
`usesClog2` column of `blockParameterizedDecls`).

**Firmware.** A firmware header has no per-variant `Config`, so it carries one value per
constant (`templates/systemc/includes.py::includeConstants` in `fw` mode). A derived constant is
emitted as a flat constant whose expression keeps other emitted derived constants symbolic and
spells every other referent, block parameters included, as its persisted default value. Root
parameters themselves are not emitted. From `examples/ip_test/ip/fw/ipIncludesFW.h`:

```cpp
inline constexpr uint32_t IP_DATA_WIDTH_X2 = 70 * 2;
inline constexpr uint32_t IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2;
```

## 7. Errors

User diagnostics, raised during `make db` with the file, line and key:

| Condition | Raised by |
| :--- | :--- |
| Bad syntax, excluded operator, C-style or real literal, `x`/`z` digit, unresolved `$NAME` | `evalExpr.parse` (`EvalParseError`) |
| Division or modulo by zero, negative shift, `$clog2` of 0 or less | `evalExpr.evaluate` (`EvalEvalError`) |
| Hand-written `maxValue` on a derived constant; derived `maxValue` of 0 or less; `value` above `maxValue` | `processYaml.py::_constants` |
| Negative result for `valueType: uint`; `eval:` with `valueType: real` | `processYaml.py::_constants` |
| Block parameter backed by an eval constant | `processYaml.py::_post_validateBlockParamBacking` |

Internal invariant failures, which mean a generator bug rather than bad YAML: a dependency cycle
or a missing parse-time tree in `deriveParameterizedDeclSets` ("Generator bug in
deriveParameterizedDeclSets"), and a parse failure inside `emitExpr`, which trusts the database.

## 8. Migrating Python evals

Older projects wrote `eval:` in Python. `make migrate` phase A (`migrateYaml.py`, calling
`pysrc/evalPyToSv.py::convertEvalsInFile`) converts them. Each `eval` row in a YAML file,
constants and enum entries alike, gets one outcome:

| Outcome | When | Effect |
| :--- | :--- | :--- |
| `ALREADY_SV` | The string already parses under the grammar. | Untouched. This makes the phase idempotent. |
| `CONVERTED` | Only convertible Python constructs remain. | Rewritten in place, every other byte kept. |
| `NEEDS_MANUAL` | Anything else. | Untouched and reported; the project is not stamped. |

Conversions, applied as text spans over Python's own `ast` of the expression:

- `(e - 1).bit_length()` becomes `$clog2(e)`; any other `e.bit_length()` becomes `$clog2(e + 1)`.
- A C-style literal is respelled: `0x10` becomes `'h10`, `0b101` becomes `'b101`, and octal
  becomes hex.
- `+ - * / % << >> & | ^` and unary `+ - ~` are copied unchanged. A legacy integer constant
  whose Python `/` gave a fraction was already rejected, so for a project that built, `/` gives
  the same result under truncation.

`NEEDS_MANUAL` reasons:

- Floor division `//`. Python floors toward minus infinity and SV `/` truncates toward zero, so
  they disagree on negative operands and a blind rewrite breaks the ceiling idiom `-(-a//b)`.
  Rewrite by hand, for example `(a + b - 1) / b` for a positive ceiling.
- `**`. Rewrite without it, for example `1 << $N` for `2**$N`.
- A real literal, or any row with `valueType: real`. Replace the `eval:` with a literal `value:`.
- Any other construct: comparisons or conditionals mixed with a Python-only construct, `and`/`or`,
  `x if c else y`, other calls and attributes.

The converter re-parses each rewritten string under the grammar; a failure there is a converter
bug (`EvalConvertError`) and nothing is written. `unittest/test_eval_py_to_sv.py` checks numeric
equivalence between each Python input and its converted form.

## 9. Known limitations

- A unary operator applied to a parenthesized conditional, such as `-($A ? 1 : 2)`, loses its
  parentheses in `unparse` and in `emitExpr`, which wrap a unary operand only when it is a binary
  expression. The value `make db` computes is correct, but the stored canonical and the emitted
  text read as `(-A) ? 1 : 2`. Write the operator inside each branch instead.
- Two adjacent unary operators are emitted without a separator. `- -$A` (or `-(-$A)`) is stored
  as `--${A/<context>}` and emitted as `--Config::A` or `--A`, and `+ +$A` as `++...`. The
  canonical re-parses to the same tree, but C++ reads the emitted text as a decrement or
  increment and fails to compile. Avoid stacking unary operators.
- `$clog2` is computed through floating-point `math.log2`, so for arguments above 2^49 the
  create-time value can be one less than the true ceiling. The emitted C++ `clog2` is exact.
- The SystemC structure emitter declares `_bitWidth` as `uint16_t`
  (`templates/systemc/structures.py`). A structure array sized by an eval-derived constant can
  exceed that range at worst case even when its default fits. The `ip_test` case
  `arraySize: IP_DATA_WIDTH_X4` over `ipDataT` (worst case 512 x 128 = 65536 bits) is therefore
  exercised only for its SV emission, by `unittest/test_eval_sv_emit.py`, and is not part of the
  example YAML.
