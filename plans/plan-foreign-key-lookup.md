# Foreign-Key Lookup Refactor Plan

## Current Status

- **Classification (reconciled 2026-07-24):** complete / committed.
- **Status taxonomy:** implementation and focused tests landed in `fd9ee1d`.
- **Current state:** `lookupInScope()` and `validateForeignKey()` implement the
  split contracts; schema combo invariants are active; `getFromContext()` and
  its callers are gone from active Python. The staged-review finding #1 is
  closed. The staged rollout below is retained as the implementation record.

## Problem

`projectCreate.getFromContext()` has accumulated three semantically distinct
responsibilities behind one string-shape heuristic. Throughout this plan,
*FK* means *foreign key* — a schema field carrying `_validate: {section: T,
field: F}` that references a row in another section.

1. **Plain-FK dereference** of an already-qualified `*Key` handle held in a
   parsed row (`containerKey`, `interfaceKey`, `interfaceTypeKey`).
2. **Scoped resolution** of a raw user-authored name through a YAML file's
   include chain (e.g. validator targets, connection endpoints, `interfaceType`
   on an interface row).
3. **Combo-FK validation** that compares a row's combo field against rows of a
   target section.

The function disambiguates (1) vs (2) by `if '/' in key` and supports (3) via
an optional `field=` parameter. Both choices are fragile:

- Path (1) recovers structural facts (qualification, defining file) by
  splitting a string the producer just concatenated. The `_context` field on
  each row, and `flatData`, already carry those facts first-class.
- Path (3) requires the source and target combo concatenations to be
  string-equal. Today that holds only when `is_foreign_key` is symmetric across
  the source field and the target field's analogous component — which is not a
  schema invariant and is empirically violated by
  `memoryConnections.memoryBlockPort → memoriesports.memoryBlockPort`. The
  source concatenates `memoryBlockKey + port` (qualified), the target
  concatenates `memoryBlock + port` (unqualified). String equality cannot
  match.

The recently-staged `pysrc/schema.py:887-890` diff propagates `validator` and
`is_foreign_key` to combo fields, activating combo-FK validators that were
silently dropped before. With the current lookup machinery this causes
`test_nested_loading.py` and the four suites it represents to fail; see
`review-staged-python-changes.md` finding #1.

## Goal

Replace the single overloaded `getFromContext()` with three primitives, each
with a sharp contract that the schema enforces at load time. After the
refactor, no lookup path parses a qualified-key string, and combo-FK
validation is structurally correct regardless of `is_foreign_key` asymmetry.

## Invariants the refactor establishes

The schema validator (`pysrc/schema.py::Schema.validate`) enforces all of
these at schema load. Violations are hard errors.

1. **`_context` is on every row.** Already established by `processSimple` /
   `processSubTable`; documented and asserted.
2. **Every `_validate: {section: T, field: F}` resolves.** `T` must be a known
   section and `T.F` must exist.
3. **Plain-FK targets are `flat`.** If the validating field is plain (no
   `_combo`), then `T` must carry `flat` in `_attribs` and `F` must be `T`'s
   storage key.
4. **Combo-FK source and target combo declarations match.** If the validating
   field is `_combo: [s_1, ..., s_n]`, then `T.F` must also be a combo with
   the same source field names in the same order. The validating field's
   enclosing section must carry fields named `s_1, ..., s_n` (so component
   reads `source_row[s_i]` are always valid).
5. **Every `flat` section has a populated `storage_key_field_qualified`.**
   `addFlatRecord` reads `row[storage_key_field_qualified]`; the schema
   validator confirms the field exists in the section's field set, and the
   producer paths (`processSimple`, `processSubTable`) populate it before
   `addFlatRecord` runs.

These five invariants make the three primitives (below) total functions: no
"row not found because of a string-shape misinterpretation" failure mode is
reachable.

## What already exists (and is not changing)

To keep the delta clear: the `flat`/`flatData` machinery itself is already
in place and is **not** part of this refactor. Specifically:

- **`flat` attribute in the schema** — `_attribs: [flat]` is read by
  `Schema` and populates `self.schema.data['flat'][section]`. See
  `pysrc/schema.py`.
- **`flatData[section]` index** — created by `createTable` when
  `self.schema.data['flat'][section]` is true (`processYaml.py:3004`).
- **`addFlatRecord(section, row)`** — already gated by the flat attribute
  (returns early if not set), reads `row[storage_key_field_qualified]`,
  hard-errors on duplicate keys, indexes into `flatData[section]`. Already
  nesting-agnostic in its implementation.
- **`storage_key_field_qualified`** — already synthesized by `set_key()`
  for both top-level and nested sections; for nested simple-key tables
  it is a composite combo `parent_storage_key + anchor` plus `'Key'`.
- **`_context`** — already populated by `processSimple` /
  `processSubTable` on every row, per review finding #4 / the staged
  changes.

The producer/consumer story for `flat` sections is already correct. What
fails today is just that (a) the few sections we want to dereference
through `flatData` are not yet marked `flat`, (b) `processSubTable`
doesn't call the existing `addFlatRecord`, and (c) the validator branch
still routes through `getFromContext`'s string-shape heuristic instead of
through the schema-driven path.

## What this refactor adds

The complete delta — there is no other new machinery:

1. **Five schema-load assertions** in `Schema.validate()` enforcing the
   invariants above. New code in `pysrc/schema.py`.
2. **Four `_attribs` additions** in `config/schema.yaml` — three top-level
   (`types`, `structures`, `interface_defs`) and one nested (`blocksparams`).
   Pure data, no code.
3. **One producer-side call** — `addFlatRecord(nestedContext, processed)`
   from `processSubTable`. One line in `pysrc/processYaml.py`.
4. **Two new lookup functions** — `lookupInScope` and `validateForeignKey`
   on `projectCreate`. New code in `pysrc/processYaml.py`. The scope-walk
   logic inside `lookupInScope` is lifted verbatim from the relevant branch
   of today's `getFromContext`; the only thing the new function does that
   the old one didn't is refuse to interpret `'/'` in the key.
5. **Eleven call-site rewrites** to use the new primitives or `flatData`
   directly (see migration table below).
6. **One deletion** — `getFromContext` and its TODO comment, after all
   callers move off it.

Everything else in this plan is consequences of (1)-(6), not additional
machinery.

## New API surface

| Operation | Primitive | Used by |
|---|---|---|
| Dereference a plain-FK handle | `prj.flatData[T][handle]` (direct) | Camp A: 3 sites |
| Resolve a raw user name through scope | `prj.lookupInScope(T, context, name)` | Camp B: 7 sites |
| Validate a foreign-key field | `prj.validateForeignKey(source_row, source_section, source_field, context)` | validator branch in `processSimple` |

`getFromContext` and its `field=` parameter retire entirely. No new
parameter, no compatibility wrapper, no fallback path.

### `lookupInScope`

Sample shown as it would land in `pysrc/processYaml.py`. Comments are
durable and describe behavior, not the absent old code path.

```python
def lookupInScope(self, objType, context, name):
    """Resolve an unqualified row name by walking the include chain of
    `context`. _a2csystem rows are visible from every non-global context.

    Returns (row, qualification) or (None, None).
    """
    if context == '_global':
        return self._lookupInGlobal(objType, name)
    for qualification in self.yamlContext[context]:
        rows = self.data[objType].get(qualification, {})
        if name in rows:
            return rows[name], qualification
    sys_rows = self.data[objType].get('_a2csystem', {})
    if name in sys_rows:
        return sys_rows[name], '_a2csystem'
    return None, None
```

Plan-level notes that should **not** appear in the committed code: this
function never interprets `/` in `name`; it replaces the scope-walk path
of `getFromContext`; `_lookupInGlobal` preserves the existing
duplicate-in-global diagnostic. Those are landing-context, not behavior.

### `validateForeignKey`

```python
def validateForeignKey(self, source_row, source_section, source_field, context):
    """Validate a foreign-key field on `source_row` against its declared
    target. Plain targets resolve via scoped lookup; combo targets match
    component-wise against rows of the target section.

    Returns (target_row, qualification) or (None, None).
    """
    validator = self.schema.data['validator'][source_section + source_field]
    target_section = validator['section']
    target_field_name = validator['field']
    target_combo = self.schema.get_node(target_section) \
                       .get_field(target_field_name).combo_sources

    if not target_combo:
        return self.lookupInScope(target_section, context,
                                  source_row[source_field])

    # TODO(combo-fk-index): combo-target validation is O(rows-in-target *
    # qualifications-in-scope) because the schema has no secondary index
    # keyed by combo component tuple. Acceptable while validators run
    # once per parsed row at projectCreate time, but worth a per-section
    # tuple index if combo-FK validators become hot.
    for qualification in self.yamlContext[context] + ['_a2csystem']:
        for row in self.data[target_section].get(qualification, {}).values():
            if all(row[s] == source_row[s] for s in target_combo):
                return row, qualification
    return None, None
```

Plan-level notes that should **not** appear in the committed code: the
combo branch reads unqualified component values so it is immune to
`is_foreign_key` asymmetry between sections; schema invariant 4 makes
`source_row[s]` accesses safe. Those facts belong in this plan and in
the schema-load assertion's error messages, not in implementation
comments.

### Camp A becomes direct `flatData` access

The three Camp A sites already hold an `*Key` handle that was produced and
validated at parse time. They become:

```python
row = prj.flatData[T][handle]
defining_file = row['_context']
```

No helper, no visibility check (the handle was validated when it was
produced), no string parsing. Each site loses 2-3 lines.

## Migration table

| # | Site | Today | After refactor |
|---|------|-------|----------------|
| 1 | `processYaml.py:3442` | `getFromContext('instances', '_global', name)` | `lookupInScope('instances', '_global', name)` |
| 2 | `processYaml.py:3444` | `getFromContext('blocks', '_global', containerKey)` | `prj.flatData['blocks'][containerKey]` |
| 3 | `processYaml.py:4640` | `getFromContext(target, scope, value, field=...)` | `validateForeignKey(ret, section, field, scope)` |
| 4 | `processYaml.py:5070` | `getFromContext('interface_defs', yamlFile, interfaceType)` | `lookupInScope('interface_defs', yamlFile, interfaceType)` |
| 5 | `processYaml.py:5150` | `getFromContext('interfaces', yamlFile, interfaceKey)` | `prj.flatData['interfaces'][interfaceKey]` |
| 6 | `processYaml.py:5151` | `getFromContext('interface_defs', yamlFile, interfaceTypeKey)` | `prj.flatData['interface_defs'][interfaceTypeKey]` |
| 7 | `processYaml.py:5245` | `getFromContext('structures', yamlFile, baseStruct)` | `lookupInScope('structures', yamlFile, baseStruct)` |
| 8 | `processYaml.py:5402` | `getFromContext('variables', yamlFile, itemkey)` | `lookupInScope('variables', yamlFile, itemkey)` |
| 9 | `processYaml.py:5907` | `getFromContext('instances', yamlFile, row[dir])` | `lookupInScope('instances', yamlFile, row[dir])` |
| 10 | `processYaml.py:6014` | `getFromContext('blocks', context, block)` | `lookupInScope('blocks', context, block)` |
| 11 | `postParseRegisterPorts.py:178` | `getFromContext('interfaces', routerContext, upstreamPort)` | `lookupInScope('interfaces', routerContext, upstreamPort)` |

## Schema changes

Per "What this refactor adds" item 2, four sections gain the `flat`
attribute. These are pure `_attribs` additions; `flatData` indexing and
duplicate detection are already implemented and need no change.

| Section | Current `_attribs` | After | Why |
|---|---|---|---|
| `types` | `[post(validateTypeWidth)]` | `[flat, post(validateTypeWidth)]` | Plain-FK target of `variables.type` and `structures.vars.varType` |
| `structures` | `[]` | `[flat]` | Plain-FK target of six fields across `interfaces`, `memories`, `registers`, `specialStructures` |
| `interface_defs` | `[]` | `[flat]` | Plain-FK target of `interfaces.interfaceType` |
| `blocksparams` (nested under `blocks.params`) | `[optional, list]` | `[optional, list, flat]` | Plain-FK target of `parameters.variants.blockParam` |

The `blocksparams` entry depends on the one-line producer extension
described under "What this refactor adds" item 3. `addFlatRecord` itself
is unchanged.

`memoriesports` is a combo-FK target and intentionally does **not** gain
`flat` — invariant 4 routes combo-FK validation through component-wise
comparison, which does not consult `flatData`.

## Stages

Each stage is independently testable. Each lands the codebase in a
provably-consistent intermediate state.

### Stage 1 — Schema-load audit (no behavior change)

- Add `Schema.validate()` checks for invariants 2, 3, 4, 5 in **warn-only**
  mode initially.
- Run `make clean && make gen` on `examples/ip_test` (and any other example
  in the repo) and capture all warnings.
- Compare against the audit script output already prepared. Expect to see
  exactly the 12 violations identified, plus any I missed.

Exit criterion: every warning is accounted for. No code path changes.

### Stage 2 — Schema fixes to satisfy invariants

Items 2 and 3 of "What this refactor adds." One commit:

- Add `flat` to `types`, `structures`, `interface_defs`, `blocksparams` in
  `config/schema.yaml` (four `_attribs` edits).
- Call `addFlatRecord(nestedContext, processed)` from `processSubTable`
  (one new line, after the existing `self.data[...]` assignment).
- Confirm the warn-mode assertions added in Stage 1 now emit zero warnings.
- Run full unit test suite. Expect: same passes/fails as today (combo-FK
  validator is still broken; the rest of the suite is green).

Exit criterion: schema is provably consistent against the planned invariants.

### Stage 3 — Hard-fail the assertions

Flip the warnings from Stage 1 to errors. Any future schema additions are
checked at load time. No code path changes.

Exit criterion: `make gen` succeeds on examples. Schema invariants are
enforced.

### Stage 4 — Introduce primitives (additive, no migration)

In one commit:

- Add `lookupInScope` and `validateForeignKey` to `processYaml.py`.
- Add tests covering: plain-FK hit, plain-FK miss, combo-FK hit, combo-FK
  miss, `_a2csystem` fallback, `_global` duplicate diagnostic, raw-name with
  `/` (must error rather than misinterpret).

Exit criterion: primitives are present and unit-tested. No call site uses
them yet. `getFromContext` is unchanged.

### Stage 5 — Migrate the validator branch (the critical fix)

This is the smallest change that closes finding #1.

- In `processSimple`, replace the `validator` branch
  (`processYaml.py:4628-4670`) with a call to `validateForeignKey`.
- The error-message construction (lines 4649-4665) stays, just keyed off the
  new return value.
- Run `unittest/test_nested_loading.py`: expect pass.
- Run full unit suite: expect green.

Exit criterion: the failing suites identified in the review (Suites 1-5) pass.

### Stage 6 — Migrate the remaining 10 callers

One commit per cluster (Camp A together, Camp B together) or one per site.
No new primitives, no schema changes, just call-site rewrites per the
migration table above.

After each cluster:

- Run full unit suite.
- Grep the file for `getFromContext(` and confirm only the unmigrated sites
  remain.

Exit criterion: zero callers of `getFromContext` remain.

### Stage 7 — Retire `getFromContext`

- Delete `getFromContext` from `processYaml.py`.
- Delete the `field=`-related TODO comment (lines 6025-6035).
- Run full unit suite.
- `rg "getFromContext"` — expect only references in plan/review markdown.

Exit criterion: function is gone, no call sites, no helpers, no string-
splitting of qualified keys anywhere in `pysrc/` or `config/`.

## What dies

- `getFromContext` function.
- The `'/' in key` heuristic.
- The `key.split('/', 1)` call.
- The `field=` secondary-index parameter.
- The TODO comment about indexing by arbitrary fields.
- The two-return-value pattern `(row, qualification)` at the 3 Camp A sites
  (those sites now read `row['_context']` if they need the qualification).
- The implicit dependency on combo-source `is_foreign_key` symmetry across
  sections.

## What stays

- `self.data[section][qualification][name]` as the authoritative parse-time
  store.
- `flatData[section][qualifiedKey]` as the derived flat index.
- `_context` on every row.
- The `is_foreign_key` flag and `compute_qualified_combo_sources` (used for
  storage-key construction, which is correct and unaffected).
- The `_a2csystem` always-visible context semantics.
- The `_global` cross-context search semantics with duplicate diagnostics.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Adding `flat` to `structures`/`types`/`interface_defs` exposes a hidden duplicate-key bug (some producer emits the same row twice). | `addFlatRecord` already hard-errors on duplicates. Catch in Stage 2 testing, fix the producer per `AGENTS.md`. |
| `processSubTable` calling `addFlatRecord` for a nested section without `flat` is a no-op (gate already exists at line 3014). | None needed; the gate makes the extension safe by default. |
| `validateForeignKey` combo branch is O(rows-in-target * qualifications-in-scope) per validator call. | Acceptable for parse-time; existing scope-walk path is also linear. Marked with a `TODO(combo-fk-index)` in the implementation; revisit by adding a per-section tuple index keyed on `combo_sources` values if profiling shows it. |
| A future schema author writes a combo validator whose source/target combo declarations don't match. | Invariant 4 catches it at schema load. |
| A future caller wants to look up by a non-key field (resurrecting the `field=` use case). | The invariants force the caller to model it as a combo validator with matching declarations, or add a real secondary index to the schema. Neither resurrects string parsing. |
| Camp A sites that currently expect a `(row, qualification)` tuple have callers reading both values. | Migration table treats this per-site; replace `qualification` reads with `row['_context']`. The three sites are small and self-contained. |

## Verification

At each stage:

1. `cd builder/base && bash unittest/run_all_tests.sh` — full suite.
2. For Stages 2, 5, 6, 7: `cd examples/ip_test && make clean && make gen` —
   end-to-end on the bundled example. Any other example projects under
   `examples/` should also build clean.
3. After Stage 7: `rg "key\.split\('/'|'/' in key|getFromContext" pysrc/ config/`
   — expect zero matches in active code.

The failing test `unittest/test_nested_loading.py` is the canary for Stage 5.

## Out of scope

These items are referenced by `review-staged-python-changes.md` but are not
covered here:

- Finding #6 (`constParse` / `_lookupConstByQualKey` parallel to ValueResolver
  helpers).
- Finding #8 (`_valueResolver` lifecycle for `varWidth` / `arraySize` /
  `_structPackedFields` callers).
- Finding #10 (`busWidth = 4` magic number in `calcAddresses`).
- Migrating any other callers that string-parse qualified keys outside the
  11 sites above (none identified during the inventory; flag as a follow-up
  if any surface during Stage 7's final grep).

## Ownership boundary

All changes in this plan live in `projectCreate` per `AGENTS.md`. No
generator, template, or template utility is touched. The `flatData`
extension to nested tables and the new lookup primitives are all
parse-time, `projectCreate`-owned concerns; the SQLite DB content shape is
unchanged.
