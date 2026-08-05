# wordLines Helpers — Resolver Lifecycle Cleanup

## Current Status

- **Classification:** open.
- **Status taxonomy:** design only.
- **Current owner:** this plan owns the `wordLines` resolver-lifecycle cleanup.
  `plan-schema-controlled-flat-data.md` remains only a guardrail reference for
  why `constants` should not gain `flat` without a concrete caller.

## Problem

Two helpers in `pysrc/processYaml.py` carry parse-time/post-parse coupling
that has accumulated past its useful life:

1. `_resolveWordLinesConst(row, resolver)` and the standalone
   `_resolveBlockParamMaxWordLines(row, resolver)` both take a
   `resolver` parameter solely so they can call
   `resolver.lookupNamedRow(qualKey, 'constant')` for their qualified-key
   branches. Their parse-time callers (`_auto_memIsParameterizable`,
   `_auto_regIsParameterizable`, `_post_registers`) pass
   `self._parserResolver`. The post-parse caller (`calcAddresses`)
   constructs a one-shot `ValueResolver(self)` only to feed it back into
   `self.X(...)`. The `resolver` parameter is the only thing the helpers
   ever pass through — no other state from the resolver is consumed.
2. `_resolveBlockParamMaxWordLines` issues a raw SQL query against
   `parametersvariants` to enumerate bound values of a block parameter,
   when an equivalent in-memory walk over
   `self.data['parameters'][blockKey]['variants']` is already available.
   The standalone helper exists despite having exactly one caller
   (`calcAddresses`).

Together these create three avoidable surfaces:

- A `resolver=` parameter on two helpers with no consumer-specific need.
- A post-parse caller (`calcAddresses`) that constructs a `ValueResolver`
  it doesn't otherwise use, which conflicts with the `_parserResolver`
  docstring's "post-parse code must construct its own resolver" caveat.
- A raw SQL path that duplicates an in-memory walk, plus a top-level
  method that exists only to be called from one place.

Per `AGENTS.md` ("Avoid parallel APIs … optional `resolver=None` unless
each path has an existing, tested consumer", "Prefer one direct path
through the code"), these surfaces should be removed.

## Scope

In scope:

- Drop the `resolver` parameter from `_resolveWordLinesConst`. Inline its
  qualified-key constant lookup directly against `self.data['constants']`
  and `self.enums`.
- Drop the `resolver` parameter from `_resolveBlockParamMaxWordLines` and
  re-locate it as a nested closure inside `calcAddresses` (its single
  caller). Inline its qualified-key bound-value lookup the same way.
- Replace the raw SQL on `parametersvariants` with an in-memory walk over
  `self.data['parameters'][blockKey]['variants']`.
- Update the 4 callers of `_resolveWordLinesConst` to drop the second
  argument, and stop constructing the local `ValueResolver` in
  `calcAddresses`.
- Update the `_parserResolver` docstring to remove the "post-parse code
  must construct its own resolver" caveat. After this change no
  post-parse code touches a `ValueResolver` on the wordLines path.
- Add a durable comment to `_resolveWordLinesConst`'s bare-name branch
  documenting the parameterizable-constant shadow-lookup it implements
  (see "Behaviour to preserve" below). The shadow lookup is load-bearing
  for `ip_test`-style worst-case sizing and must not be removed by a
  future "simplification" pass.

Out of scope (explicitly not done in this plan):

- Adding `_attribs: [flat]` to `constants` (or `enums`). No current
  caller needs a flat constants index in `projectCreate`. `projectOpen`'s
  flat-by-key access to `data['constants']` is produced by `loadData()`
  from SQLite and is independent of any `flatData` machinery. Per the
  guardrail in `plan-schema-controlled-flat-data.md` ("Do not mark a
  schema section `flat` unless a current caller uses that flattened
  index"), constants remains nested.
- Changing the include-chain semantics of the bare-name branch in
  `_resolveWordLinesConst`. The block-context-only shadow lookup is the
  current behaviour and all current examples place their
  parameterizable-constants in the block's own file. No consumer needs
  include-chain expansion.
- Migrating `ValueResolver.lookupNamedRow` / `lookupVisibleRow` /
  `_visibleNamedKey` / `_lookupQualified` onto any flat index. Those
  helpers remain unchanged. They are not on this plan's path.

## Behaviour to preserve

`_resolveWordLinesConst`'s bare-name branch implements
**parameterizable-constant worst-case sizing**. The shape:

```python
# wlKey == '' AND wl is a non-numeric bare name
ctx = blockKey.split('/', 1)[1]
entry = self.data['constants'].get(ctx, {}).get(wl)
if entry is not None:
    return entry              # Job A: shadow lookup
if self.checkIsParam(block, wl, ctx):
    return None               # Job B: pure block param, no backing constant
printError(...)               # typo / scope violation
```

Concretely, `ip_test`'s `ip.yaml` declares (via `ipParameters:`):

```yaml
constants:
    IP_MEM_DEPTH:     { value: 16, maxValue: 32, ... }   # parameterizable
blocks:
    ip:
        params: [IP_DATA_WIDTH, IP_MEM_DEPTH, IP_NONCONST_DEPTH]
memories:
    - { memory: ipFixedMem, block: ip, ..., wordLines: IP_MEM_DEPTH, ... }
```

`IP_MEM_DEPTH` is simultaneously a block parameter and a parameterizable
constant. The `param` field type at the parser
(`processYaml.py:4564-4592`) takes the `checkIsParam` branch first, so
`wordLinesKey == ''` even though the symbol is also a constant. The
bare-name branch's `self.data['constants'].get(ctx, {}).get(wl)` is what
recovers the constant row so `calcAddresses` can size to `maxValue=32`
instead of the max variant binding (16). Removing or narrowing that
lookup re-introduces a silent under-allocation. The plan keeps it
unchanged and documents it.

The pure-block-param case (`ipNonConstMem`'s `wordLines: IP_NONCONST_DEPTH`,
no backing constant) is handled by `_resolveBlockParamMaxWordLines`, which
walks the variants for the worst-case bound value. That helper is moved
into `calcAddresses` as a closure but its behaviour is unchanged.

## Why now

The motivating cleanup is `review-staged-python-changes.md` finding 8,
which landed the parser-resolver lifecycle bound: `self._parserResolver`
was scoped to YAML-parse time and the `processYaml` finalize phase nulls
it. The two wordLines helpers are the remaining post-parse code path
that reaches a `ValueResolver`-shaped surface, and they do so for one
operation (qualified-key dereference) that does not need a resolver at
all — it's a two-line `self.data['constants'][ctx][name]` lookup with an
enum fallback. Removing the parameter completes the lifecycle bound and
makes `_parserResolver` genuinely parse-time-only.

## Change delta

### `_resolveWordLinesConst`

- Signature: `_resolveWordLinesConst(self, row)` (drop `resolver`).
- Qualified-key branch: replace
  `resolver.lookupNamedRow(wlKey, 'constant')` with inlined
  `split + self.data['constants']` lookup + enum fallback + hard-fail.
- Bare-name branch: unchanged (Job A and Job B both stay).
- Docstring: add a "Behaviour to preserve" note covering Job A so the
  shadow lookup is not removed in a future pass.

Shape after the change (qualified-key branch):

```python
if wlKey and '/' in wlKey:
    name, context = wlKey.split('/', 1)
    constants = self.data['constants']
    if context in constants and name in constants[context]:
        return constants[context][name]
    if context in self.enums and name in self.enums[context]:
        enumRow = self.enums[context][name]
        return {'value': enumRow['value'],
                'isParameterizable': False, 'maxValue': 0}
    printError(f"Internal error: wordLines constant '{wlKey}' is not "
               f"present in project data.")
    exit(warningAndErrorReport())
```

### `_resolveBlockParamMaxWordLines`

- Delete the top-level method.
- Re-implement as a nested closure inside `calcAddresses`. The closure:
  - Has no `resolver` parameter.
  - Walks `self.data['parameters'].get(blockKey, {}).get('variants', {})`
    instead of issuing the SQL. Filters by `row['param'] == wl`.
  - Inlines the qualified-key bound-value constant lookup with the same
    5-line split + nested-dict + enum-fallback shape as
    `_resolveWordLinesConst`.

### Callers

- `_auto_memIsParameterizable` (line ≈ 5756): drop the second argument.
- `_auto_regIsParameterizable` (line ≈ 5785): drop the second argument.
- `_post_registers` (line ≈ 5846): drop the second argument.
- `calcAddresses` (line ≈ 3143): drop the second argument to
  `_resolveWordLinesConst`; remove the local
  `resolver = ValueResolver(self)`; call the new nested closure for the
  block-param branch.

### `_parserResolver` docstring

Remove the "Post-parse code (calcAddresses, future derivations) must
construct its own ValueResolver instead of reaching through this
attribute" caveat from `__init__`. After this change no post-parse code
on the wordLines path constructs a `ValueResolver` at all. The
parse-time scoping ("rebound on processSingleFile entry, nulled at the
end of each parse phase") is retained.

## What dies

- The `resolver=` parameter on `_resolveWordLinesConst` and (the now-
  deleted) standalone `_resolveBlockParamMaxWordLines`.
- The top-level `_resolveBlockParamMaxWordLines` method (becomes a
  nested closure inside `calcAddresses`).
- The raw SQL query against `parametersvariants` in the wordLines
  worst-case path. The only remaining SQL caller on `parametersvariants`
  is `variantValueBindings`, which serves a different need (one-variant
  active bindings, not max across variants).
- The local `ValueResolver(self)` construction in `calcAddresses`.
- The "post-parse code must construct its own resolver" sentence in the
  `_parserResolver` docstring.

## What stays

- `self.data['constants'][yamlFile][name]` as the authoritative parse-
  time store for constants. Nested by yamlFile; no flat index.
- `self.enums` (nested) and `self.qualEnums` (qualified-name dict).
  `_post_add_enum` continues to populate both.
- The parameterizable-constant shadow lookup in
  `_resolveWordLinesConst`'s bare-name branch (Job A). Documented in the
  docstring.
- `ValueResolver` and all its helpers (`lookupNamedRow`,
  `lookupVisibleRow`, `_visibleNamedKey`, `_resolveActiveValue`,
  `qualifyKey`, `_lookupQualified`, `_splitQualifiedKey`). The parse-
  time call sites in `processYaml.py` keep using
  `self._parserResolver.lookupVisibleRow` /
  `self._parserResolver.qualifyKey` / `self._parserResolver.value`
  exactly as today.
- `variantValueBindings` SQL on `parametersvariants` — different
  semantics from the deleted wordLines worst-case query.

## Verification

1. `cd builder/base && bash unittest/run_all_tests.sh` — full suite.
   Expect: same passes/fails as today.
2. `cd builder/base/examples/ip_test && make clean && make gen` —
   end-to-end including the `IP_MEM_DEPTH` / `IP_NONCONST_DEPTH` /
   `IP_FIXED_DEPTH` worst-case-sizing cases. Confirm
   `ipFixedMem` and `ipMem` are sized using `IP_MEM_DEPTH.maxValue = 32`
   (Job A) and `ipNonConstMem` uses the max variant binding for
   `IP_NONCONST_DEPTH` (`_resolveBlockParamMaxWordLines` closure).
3. Repeat `make clean && make gen` for any other example projects under
   `builder/base/examples/` that build today.
4. Targeted greps:
   - `rg "resolver" pysrc/processYaml.py` — no remaining occurrences of
     `resolver` as a parameter name on `_resolveWordLinesConst` or
     anywhere on the wordLines path.
   - `rg "parametersvariants" pysrc/processYaml.py` — expect exactly the
     one legitimate `variantValueBindings` SQL call site.
   - `rg "_resolveBlockParamMaxWordLines" pysrc/` — expect only the
     nested closure definition inside `calcAddresses`.
   - `rg "ValueResolver\(self" pysrc/processYaml.py` — expect zero
     occurrences outside of `processSingleFile`-scoped code.

## Ownership boundary

All changes live in `projectCreate` and the two affected methods. No
template, template utility, generator, schema, or view helper is
touched. No DB content shape changes. No new helper or abstraction is
introduced.

## Cross-references

- `review-staged-python-changes.md` finding 8 — the originating refactor
  that landed the parser-resolver lifecycle bound. This plan is the
  follow-on cleanup that finishes the lifecycle story by removing the
  last two parse-time/post-parse straddlers.
- `plan-schema-controlled-flat-data.md` — establishes the "do not mark a
  schema section flat unless a current caller needs it" guardrail this
  plan honours.
