# F2 + F3 Implementation Design

**Status:** historical. F2/F3 are marked done in
`plan-development-ordering.md`; current parameterized-address and
symbolic-eval follow-up work lives in `plan-eval-symbolic-emission.md`,
with unified YAML migration active/in-process in `plan-yaml-migration.md`.

Authoritative design for foundation work items **F2** (transitive
propagation of `isParameterizable`) and **F3** (worst-case address
sizing) in `builder/base/pysrc/processYaml.py`.

This document supersedes the F2/F3 sketches in
`plan-foundation-address-decode.md`. Read that file for the broader
foundation-phase context (P0 background, A1/A2/A3 follow-on work,
phase-level success criteria); read this file for everything related to
implementing F2 and F3.

## Scope

In scope:

- `builder/base/config/schema.yaml` — additive schema fields listed in
  "Schema additions" below.
- `builder/base/pysrc/processYaml.py` — extensions to the existing
  per-section handlers plus two new auto handlers.
- `builder/base/examples/ip_test/arch/yaml/ip.yaml` — minimal additions
  to exercise the new propagation paths.

Out of scope:

- A1 / A2 / A3 (template-side named-constant work).
- Modules + Config Templates (Phase 2).
- Hand-written IP code, prototype tests, or `proto/`.
- Any `templates/` files.

## Design principle: correct-by-construction

Every decision about whether an entry is parameterizable, and what its
worst-case `maxValue` / `maxBitwidth` is, happens **inside the existing
per-section handler that runs during `processYamls()`**, at the moment
that entry is added to `self.data`. There is no post-pass, no fixup
sweep, no iterative re-resolution.

The design relies on three invariants. Each handler relies on them at
entry; each handler restores them at exit. Any violation is a
**generator bug** and is reported via the existing `printError` +
`exit(warningAndErrorReport())` pattern — never silently fixed up.

### Invariant 1 — Reference closure on entry

When any handler runs for entry *E*, every entry *R* that *E*
references is **already finalized** in `self.data` with its
`isParameterizable`, `maxValue`, and/or `maxBitwidth` set.

References covered:

- a constant's `eval` string referencing other constants
- a type's `width` / `widthLog2` / `widthLog2minus1` referencing a
  constant
- a structure's fields referencing types, sub-structures, or constants
  (via `arraySize`)
- a memory / register referencing a structure (and, for memories /
  `regType=='memory'`, a `wordLines` constant)

This invariant is guaranteed by:

1. The YAML dependency graph: a YAML file that uses a symbol must
   `include` the file that defines it (or the symbol is in the same
   file, in which case in-file ordering applies).
2. `processYamls()` (`processYaml.py` lines 2738–2800) walks files in
   dependency order, fully processing each file before any file that
   depends on it.
3. Within a file, `processSection` walks the section's items in their
   YAML declaration order. Inside a section, types referenced by a
   structure must already be defined — an existing constraint
   `_auto_structWidth` already relies on.

A handler that finds a referent missing or unfinalized must hard-error
with a message that names *E*, *R*, and the YAML location of *E*. This
is the only "safety net" the design has, and it triggers only on
generator bugs, not on legitimate user input.

### Invariant 2 — Single-write fields

Once a handler stamps `isParameterizable`, `maxValue`, or
`maxBitwidth` on an entry's record in `self.data`, no other code path
overwrites them. There is exactly one writer per field: the section's
own handler. There is no defensive "recompute-if-zero" logic anywhere
in the pipeline.

### Invariant 3 — Validation at the write site

Each handler validates the entry it just stamped, immediately. If the
entry is marked parameterizable, the handler asserts:

- `maxValue > 0` (constants), `maxBitwidth > 0` (types and structures);
- the resolved `value` / `width` does not exceed it.

Errors fire at the earliest point — typically with the exact YAML file
and line of the offending entry. There is no later "validation pass".

## Schema additions

The original F1 added `constants.maxValue` and `types.maxBitwidth`. F2
and F3 require the additional entries below in
`builder/base/config/schema.yaml`. All are additive and default such
that existing YAML is unaffected.

| Section    | Field                | Schema entry                          | Rationale                                                                                          |
|------------|----------------------|---------------------------------------|----------------------------------------------------------------------------------------------------|
| constants  | `isParameterizable`  | `optional(false)`                     | Persist the bit so DB / templates see it; today only stamped in-memory by `_process_ipParameters`. |
| types      | `isParameterizable`  | `optional(false)`                     | Persist on every type for symmetry; F2.2 sets it for derived types and `ipParameters`-merged types. |
| structures | `isParameterizable`  | `auto(structIsParameterizable)`       | New; required by F3a SQL JOIN and consumed by F3b. Auto-derived; user never writes it directly.     |
| structures | `maxBitwidth`        | `auto(structMaxBitwidth)`             | New; computed alongside the existing `width: auto(structWidth)` (line 129).                         |
| memories   | `isParameterizable`  | `auto(memIsParameterizable)`          | Derived from referenced structure + `wordLines` constant; lets `calcAddresses` pick worst-case.     |
| registers  | `isParameterizable`  | `auto(regIsParameterizable)`          | Derived from referenced structure (and `wordLines` for memory-type registers).                      |
| registers  | `maxBytes`           | `auto(regMaxBytes)`                   | Required by F3b and consumed downstream by A3.                                                      |

`auto(...)` fields run inside `processSimple` via the schema's `fnStr`
map (line 3115); each is implemented as a method `_auto_<fnName>` on
the YAML processor — the same pattern as the existing
`_auto_structWidth` (line 3711) and `_auto_blockDir` (line 3717).

In the `structures:` schema entry, declare `isParameterizable` **before**
`maxBitwidth`. `processSimple` walks schema fields in declaration order
(line 2934), so the `maxBitwidth` handler can read the bit through
`processed['isParameterizable']`.

## F2 — Transitive propagation

The pipeline is unchanged: per-file YAML → `processSection` →
per-item handler → next file → `calcAddresses()`. Propagation is woven
into the existing per-item handlers.

### F2.1 — Constants (`_constants`, ~line 3213)

Extend the existing handler. The work happens **after** `ret['value']`
is computed and `self.const[yamlFile][itemkey]` is populated.

1. **Direct (user-declared) parameterizable.** If the entry was created
   via `ipParameters` (`_process_ipParameters` already set
   `isParameterizable = True`), or the user wrote a non-default
   `maxValue` directly on a regular constant, treat the constant as
   parameterizable. Validate `maxValue > 0` and `value <= maxValue`;
   hard-error with YAML location otherwise.
2. **Derived parameterizable.** Walk `self.constFind` over the original
   `item['eval']` string (the raw text is preserved on `item`, not on
   `ret`). For each `$TOKEN`, resolve via the same context-walk
   `constParse` uses (line 3848) to find the referenced constant entry
   in `self.data['constants']`. By Invariant 1, every referent is
   already present and finalized. If any referent has
   `isParameterizable = True`:
   - Set `ret['isParameterizable'] = True`.
   - Compute `ret['maxValue']` by re-running the eval-string substitution
     using each referent's `maxValue` (for parameterizable referents) or
     `value` (for non-parameterizable ones), then `eval()` the resulting
     expression in the same restricted globals as line 3100.
   - Validate `value <= maxValue`; hard-error otherwise.

To minimise duplication, factor the substitution + eval into a single
helper used by both the original `value` computation and the new
`maxValue` computation, parameterised by which field (`value` vs
`maxValue`) to read from each referent.

Constants cannot reference themselves (a constant's eval cannot mention
its own name); `processSection` adds the entry only after the handler
returns, and the YAML-side dependency model forbids cross-file cycles.
Within a file, forward references inside a section would fail today's
`value` computation under Invariant 1, so no new cycle handling is
required. A one-line assertion at the referent-lookup site hard-errors
if the lookup misses.

### F2.2 — Types (`_post_validateTypeWidth`, ~line 3629)

Extend the existing post-handler. By Invariant 1, every constant
referenced by `widthKey` / `widthLog2Key` / `widthLog2minus1Key` is
already finalized in `self.data['constants']`.

1. **Direct.** If the user wrote a non-default `maxBitwidth` directly,
   or `_process_ipParameters` set `isParameterizable = True`, validate
   `maxBitwidth >= computedWidth` and hard-error otherwise. Set
   `item['isParameterizable'] = True`.
2. **Derived.** Identify the referenced constant via the same
   `getKeyPriority(['widthLog2','widthLog2minus1','width'])` logic
   already used at line 130. Look up the constant in
   `self.data['constants']`; missing referent is an Invariant-1 hard
   error. If `isParameterizable`, recompute `maxBitwidth`:
   - `widthLog2`      → `int(maxValue).bit_length()` (`+1` if `isSigned`)
   - `widthLog2minus1` → `(maxValue - 1).bit_length()` (`+1` if
     `isSigned`)
   - `width`           → `maxValue` (preserve current `width`-mode
     handling exactly: today `width` is treated as the literal width
     and the `+1` adjustment only applies to log2 forms)

   Set `item['isParameterizable'] = True` and validate the resolved
   `width <= maxBitwidth`; hard-error otherwise.
3. If neither path applies, leave `isParameterizable = False` and
   `maxBitwidth = 0`.

### F2.3 — Structures (`_auto_structIsParameterizable` + `_auto_structMaxBitwidth`)

Add two new auto handlers next to `_auto_structWidth` (line 3711),
wired by adding to the `structures:` schema entry:

```yaml
isParameterizable: auto(structIsParameterizable)
maxBitwidth:       auto(structMaxBitwidth)
```

(in that order — see "Schema additions" above for why).

Both handlers iterate `processed['vars']`. By Invariant 1 every
referenced type, sub-structure, or constant is finalized.

`_auto_structIsParameterizable` returns `True` iff any field meets one
of:

- field's `varType` resolves to a type with `isParameterizable = True`;
- field's `subStruct` resolves to a structure with
  `isParameterizable = True`;
- field's `arraySize` is non-empty and resolves through `arraySizeKey`
  to a constant with `isParameterizable = True`.

`_auto_structMaxBitwidth` computes the worst-case bit sum,
contributing per field:

- per-element width = type's `maxBitwidth` if the type is
  parameterizable (else type's `width`); or the nested structure's
  `maxBitwidth` / `width` by the same rule;
- multiplier = the `arraySize` constant's `maxValue` if the array size
  is parameterizable; else the resolved integer `arraySize` (1 if
  empty);
- contribution = per-element width × multiplier.

Sum the contributions. If the structure is not parameterizable
(`processed['isParameterizable']` is False), return 0 — callers consult
`isParameterizable` first, and `maxBitwidth = 0` then means "use
`width`".

If `processed['isParameterizable']` is True, validate the computed
`maxBitwidth >= width` and hard-error otherwise.

### F2.4 — Memories and registers (auto fields)

Three new auto handlers, all thin combiners over the already-finalized
referenced entries:

```python
def _auto_memIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
    structKey = processed['structureKey']
    structIsParam = self.data['structures'][structKey]['isParameterizable']  # Invariant 1
    wlKey = processed['wordLinesKey']
    wlConst = self._lookupConstByQualKey(wlKey) if wlKey else None
    wlIsParam = bool(wlConst and wlConst['isParameterizable'])
    return structIsParam or wlIsParam

def _auto_regIsParameterizable(self, section, itemkey, item, field, yamlFile, processed):
    structKey = processed['structureKey']
    structIsParam = self.data['structures'][structKey]['isParameterizable']
    if processed.get('regType') == 'memory':
        wlKey = processed.get('wordLinesKey')
        wlConst = self._lookupConstByQualKey(wlKey) if wlKey else None
        return structIsParam or bool(wlConst and wlConst['isParameterizable'])
    return structIsParam

def _auto_regMaxBytes(self, section, itemkey, item, field, yamlFile, processed):
    structKey = processed['structureKey']
    struct = self.data['structures'][structKey]
    width = struct['maxBitwidth'] if struct['isParameterizable'] else struct['width']
    return (width + 7) >> 3
```

`_lookupConstByQualKey` is a small new helper. It takes a
`name/yamlFile` string (the form `wordLinesKey` already uses), returns
the constant entry from `self.data['constants']`, and hard-errors if
the lookup misses (Invariant 1 violation = generator bug).

### F2.5 — `ipParameters` file-context check

`ipParameters` may only appear in an IP block's own YAML, not in shared
includes. This is a minor extension to `_process_ipParameters` (line
3810): compare `yamlFile` against the shared-include set
(`self.includeValid`). If the file is a shared include, hard-error.
See `plan-shared-vs-ip-boundary.md` for the policy.

This is independent of F2.0–F2.4 and can be reviewed separately, but
lands in the same commit so the IP/shared boundary is enforced from
day one.

## F3 — Worst-case address sizing

### F3a — `calcAddresses` (line 2526)

Extend the SQL JOINs to fetch the new persisted fields.

```sql
-- memories
select a.*, a.ROWID,
       s.width, s.maxBitwidth, s.isParameterizable as structIsParam,
       a.isParameterizable as rowIsParam
  from memories as a, structures as s
 where a.structureKey = s.structureKey
   and a.regAccess = 1
 order by blockKey, a.ROWID;

-- registers (analogous; no regAccess filter)
```

For each row, pick the worst-case width and word-count when the row is
parameterizable:

```python
isParam = bool(row['rowIsParam'])
width = row['maxBitwidth'] if isParam and row['maxBitwidth'] else row['width']

if addressType == 'memories' or (addressType == 'registers' and row['regType'] == 'memory'):
    wlConst = self._lookupConstByQualKey(row['wordLinesKey'])
    wordLines = (wlConst['maxValue']
                 if isParam and wlConst['isParameterizable']
                 else self.qualConstParse(row['wordLinesKey']))
    size = roundup_pow2min4((width + 7) >> 3) * wordLines
    if sizeRoundUpPowerOf2:
        size = roundup_pow2min4(size)
    if alignmentModeValue:
        size = ((size + alignment - 1) // alignment) * alignment
elif addressType == 'registers':
    size = ((((width + 7) >> 3) + alignment - 1) // alignment) * alignment
else:
    continue
```

Non-parameterizable rows hit the existing path because `isParam` is
False and `maxBitwidth` is 0 — bit-identical to today's behaviour. This
is the only change required in `calcAddresses`; the alignment, offset,
and address-space-overflow logic at lines 2570–2607 is untouched.

### F3b — Register `bytes` derivation (lines 1016 and 1509)

`registers.maxBytes` is already persisted via the
`_auto_regMaxBytes` handler (F2.4). The two `getBlockData*` call sites
that build per-register dicts in memory just need to surface it
alongside `bytes`:

```python
struct = self.data['structures'][regInfo['structureKey']]
ret['registers'][reg]['bytes'] = (struct['width'] + 7) >> 3
ret['registers'][reg]['maxBytes'] = (
    (struct['maxBitwidth'] + 7) >> 3
    if struct['isParameterizable'] else
    ret['registers'][reg]['bytes']
)
```

The DB column `registers.maxBytes` is the source of truth; these
in-`getBlockData*` writes are redundant refreshes for callers that
build the dict from `self.data['registers']` rather than re-reading
the DB. Both writers compute from the same `struct['maxBitwidth']`, so
Invariant 2 is preserved (one logical writer, two physical surfaces).

## Test fixture: `examples/ip_test/arch/yaml/ip.yaml`

Today the fixture exercises:

- Parameterizable constant via `ipParameters` (`IP_DATA_WIDTH`,
  `IP_MEM_DEPTH`).
- Parameterizable type via `ipParameters` with explicit `maxBitwidth`
  (`ipDataT`).
- Parameterizable type using `widthLog2minus1` against a
  parameterizable constant, *without* explicit `maxBitwidth` (exercises
  F2.2 derivation: `ipMemAddrT`).
- Structure containing parameterizable-typed fields (`ipDataSt`,
  `ipMemSt`, `ipMemAddrSt`) — exercises F2.3 type→struct.

Gaps to close so all F2/F3 paths run under `make db`:

- No constant whose `eval` derives from a parameterizable constant.
- No structure with an array field whose `arraySize` is a
  parameterizable constant (F2.3 array-size path).
- The `memories:` line is commented out, so F3a's memory worst-case
  sizing path doesn't run.

Minimal additions:

```yaml
ipParameters:
    constants:
        IP_DATA_WIDTH:    { value: 8,  maxValue: 16, desc: "Per-instance data width" }
        IP_MEM_DEPTH:     { value: 16, maxValue: 32, desc: "Per-instance memory depth" }
        IP_DATA_WIDTH_X2: { eval: "$IP_DATA_WIDTH * 2", maxValue: 32, desc: "Derived width, 2x data" }   # NEW
    types:
        ipDataT:
            width: IP_DATA_WIDTH
            maxBitwidth: 16
            desc: "IP data word, parameterizable"

structures:
    ...
    ipBurstSt:                                                                                          # NEW
        samples: { varType: ipDataT, arraySize: IP_MEM_DEPTH, desc: "Burst of parameterizable samples" }
```

…and uncomment the `memories:` line so F3a's memory path runs.

## Rollout

1. **Schema additions** — one commit, the seven entries from the
   "Schema additions" table.
2. **F2 implementation** — one commit covering F2.1 (constants), F2.2
   (types), F2.3 (structures), F2.4 (memories/registers auto handlers),
   and F2.5 (ipParameters file-context check). These are
   interdependent under correctness-by-construction and ship together.
3. **F3 implementation** — one commit covering F3a + F3b.
4. **Test fixture** — one commit adding `IP_DATA_WIDTH_X2`,
   `ipBurstSt`, and uncommenting the `memories:` line in
   `ip_test/arch/yaml/ip.yaml`.
5. **Verification** —
   `make db` on `ip_test`, every `examples/*` project, and the host
   debayer project. Hand-inspect `ip_test`'s SQLite DB for
   `isParameterizable`, `maxBitwidth`, and `maxBytes` on the
   propagated entries.
6. **Progress** — mark F2 and F3 done in
   `plan-development-ordering.md`.

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Invariant 1 violated by a real-world include graph we haven't seen | Low | The Invariant-1 assertion at every referent lookup hard-errors with the offending YAML location. Loud, not silent. |
| Eval-string substitution helper diverges from `re_constReplace` | Medium | Single shared closure factory, parameterised by which field (`value` vs `maxValue`) to read from each referent. The `IP_DATA_WIDTH_X2` test fixture exercises the path. |
| Schema additions rejected as out of scope | Reviewer call | Authorisation is the gate; this doc is the request. |
| Cycle in const→const refs | Very low | `processYamls` already rejects circular YAML includes (line 2796); within a file, today's `value` resolution would already fail on a forward reference. The Invariant-1 assertion catches any residual case as a generator bug. |
| Two-handler ordering in `structures` schema | Low | Schema-comment + the natural reading order; `processSimple` walks fields in declaration order (line 2934). |

## Verification checklist

- [x] `make db` on `examples/ip_test` succeeds.
- [x] `examples/ip_test` SQLite DB shows `isParameterizable=1` on
      `IP_DATA_WIDTH`, `IP_MEM_DEPTH`, `IP_DATA_WIDTH_X2`, `ipDataT`,
      `ipMemAddrT`, `ipDataSt`, `ipMemSt`, `ipMemAddrSt`, `ipBurstSt`,
      `ipMem` (memory), `ipCfg` and `ipLastData` (registers, via their
      structures).
- [x] `IP_DATA_WIDTH_X2` row has `value=16`, `maxValue=32`.
- [x] `ipMemAddrT` has `maxBitwidth = (32-1).bit_length() = 5`
      (versus `width = (16-1).bit_length() = 4`).
- [x] `ipBurstSt` has `width = 8 * 16 = 128` and
      `maxBitwidth = 16 * 32 = 512`.
- [x] `ipLastData.maxBytes = 2` (vs `bytes = 1`); `ipMem`'s allocated
      address space reflects worst-case 32 entries × 2 bytes.
- [ ] `make db` on every other `examples/*` project succeeds with no
      behavioural change (none declare `ipParameters`, so propagation
      is a no-op).
- [ ] `make db` on the host debayer project at the workspace root
      succeeds unchanged.
