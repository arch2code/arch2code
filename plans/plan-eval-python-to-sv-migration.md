# Plan: Migrate Python `eval` Strings to the SV Subset (E1.5 tool)

Date: 2026-06-10
Status: **superseded for CLI ownership; design retained.** The converter
core described here (`pysrc/evalPyToSv.py`, committed) is now consumed by
the **landed** (2026-06-18/19) unified YAML migration work in
[`plan-yaml-migration.md`](./plan-yaml-migration.md).
The standalone `migrateEvalExpr.py` CLI remains deferred/superseded by
that unified command. This plan remains the design record for the
Python-to-SV expression conversion rules and tests. E1.5 still does not
block E2-E6, which use the already-SV-valid `ip_test` as their build
vehicle.
Owner: C4 (`plan-param-constant-collision.md`), via the symbolic-eval pipeline.

## Goal

The existing `eval:` constant expressions are authored in **Python**
(`.bit_length()`, floor `//`, real `/ 2.0`) and will not parse under the frozen
SV-subset grammar the new pipeline introduces (E0/E1). Before the E2 cutover
replaces the parse-time `eval()` in `processYaml.py`, every `eval` string the
generator consumes must be rewritten into the SV subset.

Rather than hand-edit, this stage delivers a **standalone, reusable converter**
that programmatically rewrites Python `eval` strings to SV-subset `eval` strings
in user YAML, across any project. It is purely syntactic: it reads the
authored expression, rewrites the Python-only constructs, and writes the new
`eval` string back in place.

## Locked Decisions

These were confirmed before drafting:

- **Front-end: Python `ast`.** The current `eval` strings are literal Python, so
  Python's own parser reads them robustly (including `.bit_length()` on
  arbitrary parenthesized receivers and nested expressions). No hand-rolled
  Python tokenizer. `$SYM` — the one non-Python token — is handled by a
  length-preserving placehold before parsing (see below).
- **Rewrite mechanism: targeted text replace.** Only the spans that actually
  change (`.bit_length()` calls and `//` operators) are replaced in the source
  text, using `ast` node offsets. All other characters — spacing, parentheses,
  comments on the line, quoting — are left byte-identical. No `ruamel`
  round-trip.
- **`valueType: real` evals: report, convert manually.** Converting a real eval
  (`$DWORD / 2.0`) to a literal `value:` requires *resolving symbol values*,
  which a syntactic rewriter does not have. The tool detects these, leaves them
  untouched, and lists them in its report for manual conversion. There is
  effectively one such row in the repo (`REAL_HALF` in `mixed.yaml`, duplicated
  in the unittest copy) and none in the debayer project.
- **Location: `builder/base`.** Testable core logic in
  `pysrc/evalPyToSv.py` (reuses `evalExpr` and `arch2codeHelper`); a thin
  top-level CLI `migrateEvalExpr.py` (file discovery, YAML scan, rewrite,
  report), mirroring the existing standalone `arch2code.py` / `getJiras.py`.

## Inventory (this repo)

Most `eval` rows are **already SV-valid** and must be left untouched
(`$BITS_PER_PIXEL_COLOR + 1`, `(1 << $BITS_PER_PIXEL_COLOR) - 1`,
`$A + $B - 1`, bare `$SYM`, `$TESTCONST1+4`). The Python-only rows needing
conversion are:

| Pattern (Python) | Files | Converts to |
|---|---|---|
| `($X - 1).bit_length()` | `arch/yaml/debayer.yaml`, `arch/yaml/isp_types.yaml`, and `builder/base` examples (`nested`, `mixedInclude`, `simple/pipe`, `apbDecode`) + unittest arches, plus `builder/pro` `lmmiDemo` | `$clog2($X)` |
| `($X).bit_length()` | `arch/yaml/debayer.yaml` (`DEBAYER_DIMENSION_LOG2`), `mixed.yaml` (`DWORD_LOG2`) | `$clog2($X + 1)` |
| floor `//` | `arch/yaml/debayer.yaml` (`DEBAYER_OFFSET`, `ENTRIES_PER_LINE`, `DEBAYER_RINGS`) | `/` |
| `valueType: real` eval (`$DWORD / 2.0`) | `mixed.yaml` (+ unittest copy) | **reported, not rewritten** |

Note: the `ip_test` example's evals (`$IP_DATA_WIDTH * 2`,
`$IP_FIXED_NIBBLE_COUNT + 1`) are **already SV-valid**, so the E2 example is not
blocked by migration. If a build-verifiable example is wanted before the broad
run, `ip_test` needs no conversion; the Python-syntax rows live in the other
examples and the debayer project.

## Converter Architecture (`pysrc/evalPyToSv.py`)

The core is a pure function over a single expression string:

```
def convertExpr(pyExpr: str) -> ConvertResult
```

where `ConvertResult` carries the outcome category and, when converted, the new
SV string. Categories:

- `ALREADY_SV` — already parses under the SV grammar; no change.
- `CONVERTED` — Python constructs rewritten; new SV string produced.
- `NEEDS_MANUAL` — real literal / out-of-grammar construct; left untouched,
  flagged with a reason.

### Step 1 — idempotency / skip gate (reuse `evalExpr.parse`)

Try `evalExpr.parse(pyExpr, qualify=<accept-all>)`. If it **succeeds**, the
expression is already SV-subset → return `ALREADY_SV`, no rewrite. This makes
the tool idempotent and minimal-diff for free: every already-migrated or
natively-SV row is skipped, and re-running the tool is a no-op. Only rows that
fail the SV parse proceed to conversion.

(The `<accept-all>` qualify maps any bare name to a dummy key; the migration
only cares whether the *shape* is in-grammar, not whether symbols resolve in a
project. Symbol resolution is a create-time concern, not a syntactic one.)

### Step 2 — placehold `$SYM`, parse with `ast`

Replace `$` → `_` (both width 1, so **all source columns stay aligned**), giving
valid Python where `$NAME` becomes the identifier `_NAME`. `ast.parse(...,
mode='eval')` yields a tree whose `col_offset` / `end_col_offset` index into the
original string unchanged. (`$clog2` does not occur in current Python evals; if
encountered it is treated as out-of-grammar for the Python front-end and
reported.)

### Step 3 — validate the tree is convertible

Walk the tree; permit only: `BinOp` over `{Add, Sub, Mult, FloorDiv, Div, Mod,
LShift, RShift, BitAnd, BitOr, BitXor}`, `UnaryOp` over `{UAdd, USub, Invert}`,
`Name` (a placeheld symbol), integer `Constant`, and the `.bit_length()` `Call`.
Anything else — `Pow` (`**`), `Compare`, `BoolOp`, a **float** `Constant`, a
non-`bit_length` `Call`, an unknown attribute — makes the row `NEEDS_MANUAL`
with a specific reason (e.g. "real literal", "unsupported operator `**`"). Float
constants are the real-eval signal; rows with `valueType: real` are also routed
to `NEEDS_MANUAL` by the file driver regardless of tree contents.

### Step 4 — collect rewrite spans (right-to-left)

Only two constructs are rewritten; everything else is copied verbatim. Spans are
applied **right-to-left** so earlier offsets stay valid.

- **`.bit_length()` call** — the `Call` node spans the entire
  `(...).bit_length()` (its `col_offset` includes a leading `(`). Let `recv` be
  the `Attribute.value`:
  - if `recv` is `BinOp(left=L, op=Sub, right=Constant(1))` →
    replace the call span with `$clog2(` + `src(L)` + `)`
    (the `($X - 1)` → `$clog2($X)` simplification).
  - otherwise → replace with `$clog2(` + `src(recv)` + ` + 1)`
    (the general `e.bit_length() ≡ $clog2(e + 1)` identity).

  `src(node)` is the original-string slice `[node.col_offset:node.end_col_offset]`
  (carrying the developer's symbols and spacing through unchanged).
- **`FloorDiv`** — the `//` token lies in the gap between
  `left.end_col_offset` and `right.col_offset`; locate the `//` substring there
  and replace that 2-char span with `/`.

The empirically confirmed offsets (Python 3.10) back this exactly:
`($NUM_LINE_BUFFERS-1).bit_length()` → receiver-left slice `$NUM_LINE_BUFFERS`
→ `$clog2($NUM_LINE_BUFFERS)`; `($DWORD).bit_length()` → `$clog2($DWORD + 1)`;
`A // B` → `A / B`.

### Step 5 — validate the output

Parse the produced SV string back through `evalExpr.parse` (`<accept-all>`
qualify). It **must** succeed; failure is a converter bug, surfaced as an
internal error, not written to YAML. This guarantees every written `eval` string
is in-grammar for the new pipeline.

## File Driver & CLI (`migrateEvalExpr.py`)

```
migrateEvalExpr.py [--write] <file-or-dir> [<file-or-dir> ...]
```

- **Discovery.** Walk the given paths for `*.yaml`. For each, enumerate `eval`
  rows. Source strings and `valueType` are read via PyYAML (authoritative
  values), with a line-number-capturing loader so each row's line is known for
  targeted write-back. `eval` appears both as a constant field and as an enum
  `eval` field; both are handled.
- **Convert.** Run `convertExpr` per row; route `valueType: real` rows to
  `NEEDS_MANUAL` directly.
- **Write-back (targeted text replace).** For a `CONVERTED` row, replace the
  exact original `eval` expression substring on its line with the new string,
  leaving the rest of the line (quotes, `desc:`, comments) untouched. Read the
  file as text, edit the located line, write it back. `ALREADY_SV` and
  `NEEDS_MANUAL` rows are never written.
- **Default is dry-run.** Without `--write`, the tool prints the report and the
  per-row before/after but does not modify files. `--write` applies the edits.
- **Report.** Grouped by file with `file:line`, listing converted rows
  (`old → new`), skipped already-SV rows (count), and `NEEDS_MANUAL` rows with
  reasons. The report is the human-review surface E1.5 calls for.
- **Idempotent.** Re-running over migrated files yields only `ALREADY_SV` and
  the same `NEEDS_MANUAL` list; no further writes.

## Testing (`builder/base/unittest/test_eval_py_to_sv.py`)

Following the project's "tests must execute functionality" preference and the
existing `test_eval_expr_*` convention (`test_*` functions, `_TESTS` registry,
`main()` printing PASS/FAIL, exit code):

- **Per-rule string conversion.** `convertExpr` over each idiom yields the
  expected SV string: `($X-1).bit_length()`→`$clog2($X)`,
  `($X).bit_length()`→`$clog2($X + 1)`, `A // B`→`A / B`, and combinations
  (`$clog2` inside a larger expression, `//` alongside other operators).
- **Numeric equivalence (the strongest check).** For each migrated expression,
  evaluate the **original Python** (via `eval` on the `$SYM`-substituted string,
  mirroring the mechanism being replaced) and the **converted SV** (via
  `evalExpr.parse` + `evalExpr.evaluate` with the same symbol values) over
  several symbol assignments; assert equal. This proves the rewrite preserves
  values, not just shape — and exercises the real E1 evaluator end to end.
- **Skip / idempotency.** Already-SV inputs return `ALREADY_SV` unchanged;
  `convertExpr(convertExpr(x)) == convertExpr(x)` for converted inputs.
- **`NEEDS_MANUAL`.** Real literals (`$DWORD / 2.0`), `**`, and other
  out-of-grammar constructs are reported, never silently rewritten.
- **File round-trip.** Run the file driver over a small temp YAML fixture;
  assert the `eval` values changed as expected and every other byte of the file
  is unchanged (targeted-replace guarantee).

Wire the suite into `unittest/run_all_tests.sh` as the next suite after **19d**
(the E1 evaluator), matching the surrounding style.

## Verification Strategy & Relationship to E2

- **E1.5 verifies itself** through the converter unit tests (string +
  numeric-equivalence + idempotency + file round-trip) and the dry-run report's
  manual review. It does **not** rely on `make gen`, because migrating to
  `$clog2` breaks the current parse-time `eval()` (which has no `$clog2`
  support) until E2 lands. This is expected and is why E1.5 precedes E2.
- **E2–E6 are not blocked by this stage.** They develop and verify against
  `ip_test`, which is already SV-valid and builds identically before and after
  the cutover, so no migration is needed for an E2 parity example or for the
  E4/E5 emission work.
- **Running the migration on real YAML** (debayer `arch/yaml`, the `builder/base`
  examples + unittest arches, `builder/pro` `lmmiDemo`) is what lets those
  **specific** projects build under the post-E2 generator. Each migrated file's
  build goes red until E2 lands, so write those edits as part of (or after) the
  E2 cutover; the tool supports dry-run vs `--write` for either sequencing.

## Constraints

- `builder/base` is a git submodule; the tool and its tests are added but **not**
  staged or committed (user-managed).
- Builder-base rules: one direct path, no speculative parameters or fallback
  knobs. The converter exposes `convertExpr` (pure) and the file driver; no
  optional resolver wiring (real-eval resolution is deliberately out of scope).
- Language-neutral reuse only: the converter depends on `evalExpr` (parse
  validation) and `arch2codeHelper` (none needed beyond reuse symmetry); it
  introduces no SV/C++ emission concerns — those are the later E-stages.

## Out of Scope

- Real-eval → literal conversion (resolution-dependent; reported only).
- Any operator outside the frozen grammar (`**`, ternary, relational/logical,
  `$bits`); reported as `NEEDS_MANUAL`.
- The E2 cutover itself (deleting the `eval()` sites) and persistence/emission
  (E3+). This stage only rewrites authored `eval` strings.

## Rejected Alternatives

- **Hand-rolled Python tokenizer/parser** — reimplements `ast` for no benefit;
  the source is literal Python.
- **Full precedence-aware re-emit of every converted expression** — would need
  an SV emitter (`needsParens`/`PRECEDENCE`) that belongs to the E4 emission
  stage; building it here is premature. Span-based surgical replacement needs
  no emitter and yields minimal diffs.
- **`ruamel` round-trip rewrite** — heavier dependency, risks reformatting
  unrelated lines; rejected in favor of targeted text replace.
- **Tool evaluates real evals to literals** — couples a syntactic standalone
  tool to a resolved/built project for a single expression; rejected.
