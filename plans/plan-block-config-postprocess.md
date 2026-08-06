# Plan: Block `isParameterizable` Computation as YAML Post-Processing Step

## Naming Note

This plan was originally titled "Plan: Block `usesConfig` Computation".
During implementation the field was renamed to `isParameterizable` so
that the same flag name is used at every scope where it already exists:

- `structures.isParameterizable` — the structure's compiled width
  depends on a parameter.
- `registers.isParameterizable` / `memories.isParameterizable` — the
  row inherits parameterizability from its referenced structure.
- `blocks.isParameterizable` — at least one structure on the block's
  reachable surface is itself `isParameterizable: true`, so the
  generated SystemC class needs a `template<typename Config>`
  decoration.

The block-level flag is the transitive closure of the structure-level
flag; the property being aggregated is identical across scopes, so the
name should be too. References to `usesConfig` in earlier plans, prior
commits, or related research notes refer to the same field.

## Implementation Status (2026-05-07)

Landed on branch `feature/116-parameterized-types`:

- `config/schema.yaml` — `blocks.isParameterizable: optional(false)`
  and `blocks.defaultConfig: optional("")` added alongside `maxAddress`.
- `config/project.yaml` — the `blockRegistrar` `fileMap` `cond:`
  predicate updated to `cond: {isParameterizable: true}`.
- `pysrc/processYaml.py::projectCreate.calcBlockConfigInfo()` —
  one-shot SQL-driven structure walk that persists the two block-level
  truths via `UPDATE blocks SET isParameterizable = ?, defaultConfig
  = ? WHERE blockKey = ?`. Wired into `processProject()` between
  `calcAddresses()` and `generateAddressEnums()`. Implemented in
  `projectCreate` (rather than `projectOpen`) because `getBlockData()`
  lives on `projectOpen` only; the walk reads the canonical SQL tables
  directly using the same row-selection rules as the per-block view
  (regHandler parent lookup for register / memory ownership, instance
  filtering by container vs port owner for connections, interface
  structure expansion via `interfacesstructures`).
- `pysrc/processYaml.py::projectOpen.getBDConfigInfo(ret)` — slim
  view-assembly: reads `isParameterizable` and `defaultConfig` off
  `self.data['blocks'][...]`, derives `configTag = defaultConfig`.
  No structure walk.
- `pysrc/processYaml.py::projectOpen.getBlockConfigView(qualBlock)` —
  helper that returns `{isParameterizable, defaultConfig, configTag}`
  without running the rest of `getBlockData()`.
- `pysrc/newModule.py` — uses `getBlockConfigView()` to build
  `blockCondData`. The dropped `configContexts` field is no longer
  forwarded.
- `templates/systemc/classDecl.py`, `constructor.py`, `testbench.py`,
  `blockRegistrar.py`, `baseClassDecl.py`, `module_hdl_wrapper.py` —
  read `data['isParameterizable']` (for templates that already hold
  a per-block view) or `prj.getBlockConfigView(key)['isParameterizable']`
  (for sub-block / instance-type lookups that previously called
  `getBlockData(key)['usesConfig']`).
- `pysrc/intf_gen_utils.py::block_config_decl` and `block_config_arg`
  parameter renamed from `uses_config` to `is_parameterizable`.
- `module_hdl_wrapper.py::render_sc` retains its
  `data.get('isParameterizable', False)` defensive read for the
  hierarchy-mode `vl_wrap.cpp` invocation, by design.

Validation (per the original plan's acceptance criteria):

- `examples/ip_test` and `examples/helloWorld` regenerate to
  byte-identical generated source compared with the pre-lift
  snapshot.
- `make -C ../../proto/model step6` reports `PASS`.
- `examples/ip_test/rundir` clean rebuild succeeds.
- All touched generators pass `python3 -m py_compile`.

The remainder of this plan describes the original design and is kept
as the canonical reference for *why* the lift was shaped this way.

## Goal

Split today's `getBDConfigInfo()` along the right boundary:

- **The expensive truth-finding work** — the per-block walk over
  structures referenced by ports / connections / registers /
  memories that determines whether a block uses parameterizable
  types — is lifted into a one-shot YAML post-processing pass
  (`calcBlockConfigInfo`) that runs after the project's YAML scan
  and persists its results onto the `blocks` table.
- **`getBDConfigInfo` is retained**, but slimmed to its proper
  role: a per-call view-assembly function that reads the persisted
  truths from `self.data['blocks']` and arranges them, plus any
  cheap view-shaped derivations, into the per-block `ret` dict
  that templates consume.

This is the structural analogue of `calcAddresses`: the address
calculation runs once after YAML scanning, writes results back to
the `blocks` table, and downstream code reads `maxAddress`
unconditionally. Address-related view work (e.g.,
`getBDAddressDecode` setting `addressDecode['addressBits'] =
(self.data['blocks'][decodeBlock]['maxAddress']).bit_length()`)
still runs per-call to assemble the per-block view from the
persisted truth — the post-processing pass replaces the
*derivation*, not the view assembly.

## Background

### Current state

`pysrc/processYaml.py::getBDConfigInfo` (lines 1011-1062) is invoked
at the end of `getBlockData()`. It walks the per-block view that
`getBlockData()` has already constructed (`ret['ports']`,
`ret['connectDouble']`, `ret['registers']`, `ret['memories']`,
`ret['memoriesParent']`, `ret['memoryConnections']`,
`ret['memoryPorts']`, `ret['registerPorts']`), checks every
referenced `structureKey` / `addressStructKey` against
`self.data['structures']` for `isParameterizable`, and from that
derives four fields stamped into `ret`:

- `isParameterizable` — boolean: does any structure this block touches
  carry parameterizable typing?
- `defaultConfig` — generated identifier
  (`<context>DefaultConfig`); falls back to
  `<blockName>DefaultConfig` when no context is found.
- `configTag` — currently identical to `defaultConfig` (the stable
  string the trampoline pass emits as the `instanceFactory` key).
- `configContexts` — ordered list of YAML-include contexts whose
  parameterizable structures the block touches.

The result is stamped into the `ret` dict but **not** persisted
anywhere. Every caller that needs it must call `getBlockData()`,
which re-walks every connection, register, memory, and port row
each time. The Critical Review section below classifies these
four fields by where they should actually live; the answer is
two persisted in the DB, one retained as a view-side derivation,
and one dropped entirely as an unused intermediate.

### What forced the recent defensive change

`templates/systemc/module_hdl_wrapper.py::render_sc` runs in two
distinct contexts:

- Per-block, when emitting `<block>_hdl_sc_wrapper.h` — `data` is
  the per-block view from `getBlockData()` and carries
  `isParameterizable` / `defaultConfig`.
- Project / hierarchy level, when emitting `vl_wrap.cpp` — `data`
  is a project-level dict with no per-block keys.

The hierarchy-level call therefore raised a `KeyError` on
`data['isParameterizable']`. The fix landed as
`data.get('isParameterizable', False)` plus an explanatory comment, but
that defensive read silently yields `False` whenever the data view
doesn't happen to come from `getBlockData()` — and there is no
mechanism to detect when that is wrong. Other callers
(`newModule.py` already builds a parallel `blockCondData` map by
calling `getBlockData()` for every block; `classDecl.py` calls
`prj.getBlockData(key)['isParameterizable']` for every sub-block) all pay
the same recomputation tax.

### Why post-processing is the right shape for *part* of this

`maxAddress` is the precedent. The blocks schema declares it
`optional(0) # filled out by address generation`, `calcAddresses`
runs once and emits `UPDATE blocks SET maxAddress = ...`, and every
later consumer reads `self.data['blocks'][qualBlock]['maxAddress']`
without recomputing. The same pattern fits the structure walk:

- Inputs (`structures.isParameterizable`, the connections / ports /
  registers / memories tables) are stable after YAML scanning
  completes. They do not change between generate invocations of
  the same processed project.
- The walk's primary outputs (`isParameterizable`, `configContexts`,
  `defaultConfig`) are facts about the block; their values do not
  depend on the caller.
- Computing them once instead of per-`getBlockData()` removes both
  the recomputation cost and the "is this view a per-block view?"
  ambiguity that produced the recent defensive `.get(...)` fix.

But not every output of today's `getBDConfigInfo` is a database
truth. The "Critical Review" section below classifies each field;
some belong in the post-processing pass, others belong in a slim
`getBDConfigInfo` that survives as a view-assembly layer.

## Critical Review of Today's `getBDConfigInfo` Outputs

`getBDConfigInfo` produces four fields. Classifying each by "expensive
truth that should live in the database" vs "cheap view-shaped
derivation that should live in the per-call view assembly":

### 1. `isParameterizable` (bool) — **DB truth**

- **Source.** Walk over every structure referenced by the block's
  ports, double-ended connections, registers, memories, memory
  parents, memory connections, memory ports, and register ports;
  check each `structureKey` / `addressStructKey` against
  `structures.isParameterizable`.
- **Stability.** Same value for the same block across every
  caller and every generate run.
- **Cost.** Linear in the block's row count across those tables;
  re-paid by every `getBlockData()` invocation today.
- **Verdict.** Expensive truth. Belongs in the DB row, computed
  once by the post-processing pass.

### 2. `configContexts` (list[str]) — **Intermediate; not persisted, dropped from view**

- **Source.** Same walk as `isParameterizable`; collects unique YAML
  context names of every parameterizable structure encountered,
  preserving discovery order. The first element drives the
  `defaultConfig` name.
- **Real consumers.** A grep across `templates/` and `pysrc/`
  shows three references and no real reader:
  - `processYaml.py` line 1052 uses `contexts[0]` *inside the
    producer itself* to derive `defaultConfig`.
  - `processYaml.py` line 1062 assigns the list onto `ret`.
  - `newModule.py` forwards it into `blockCondData` so file-map
    `cond:` clauses can reference it. But `cond:` evaluation is
    a scalar `==` check
    (`blockCondData[qualBlock][field] == value`); a list-valued
    field cannot be tested usefully, so this exposure is dead
    surface.
- **Verdict.** Intermediate value of the `defaultConfig`
  derivation. Not a fact about the block worth keeping.
  - Do **not** persist a JSON blob in the `blocks` row.
    JSON-in-column is the wrong shape for a relational schema,
    and the codebase's established pattern for list-valued
    block data is a sub-table (e.g., `blocks.params` with
    `_attribs: [optional, list]`).
  - Do **not** add a sub-table either, because no consumer
    needs the list. Adding one would be schema noise.
  - The post-processing pass uses the list locally during the
    walk to compute `defaultConfig`, then discards it. The
    field is removed from the `ret` view returned by
    `getBDConfigInfo`, and `newModule.py`'s `blockCondData`
    loop drops it from its forwarded field set.
- **If a real consumer appears later** (e.g., a future `cond:`
  predicate that wants "any context in list X" semantics, or a
  template that needs the full list), the migration is to add
  a `configContexts` sub-table to `blocks` following the
  `params` precedent:

  ```yaml
  blocks:
    ...
    configContexts:
      _attribs: [optional, list]
      context: key
  ```

  The sub-table loader's existing
  `_reconstruct_nested_structure` mechanism (see
  `loadData` / `_attach_subtables_recursive`) attaches the list
  back onto `self.data['blocks'][qualBlock]` automatically, so
  no view-side decode is required. Discovery-order
  preservation, if needed at that point, is handled by an
  explicit ordinal column on the sub-table row. Until then,
  the field stays out of the schema.

### 3. `defaultConfig` (string) — **DB truth**

- **Source.** Pure deterministic function of `(isParameterizable,
  configContexts[0], blockName)`. The transformation is:

  ```python
  if is_parameterizable:
      if contexts:
          default_config = sanitize(basename(contexts[0])) + 'DefaultConfig'
      else:
          default_config = blockName + 'DefaultConfig'
  else:
      default_config = ''
  ```

- **Stability.** Same value for the same block across every
  caller.
- **Cost.** Trivial (string substitution) given the other
  truths.
- **Cross-consumer surface.** This is the **trampoline contract
  string**. It is consumed by:
  - The trampoline pass (`templates/systemc/blockRegistrar.py`),
    which emits it as the `configTag` argument to
    `instanceFactory::registerBlock(...)`.
  - The constructor template
    (`templates/systemc/constructor.py`), which threads it as
    each child's `configTag` into `createInstance(...)` calls.
  - The testbench template
    (`templates/systemc/testbench.py`), same role for the DUT
    lookup.
  - Various places that need `<{defaultConfig}>` for
    template-arg substitution.
- **Verdict.** Persist in the DB even though the derivation is
  cheap. Reasoning:
  - Every consumer agrees on the exact string, so persisting
    makes "one source of truth" visible. The post-processing
    pass produces it; nobody else recomputes it. This eliminates
    the risk that two derivations drift (e.g., if the
    sanitisation rule ever changes).
  - The trampoline pass walks the project's instance tree and
    needs `defaultConfig` per child block; with persistence,
    that's a SQL `SELECT` against `blocks`. Without persistence,
    every walk step calls `getBDConfigInfo` (or re-derives) and
    pays the lookup tax that the lift is meant to eliminate.

### 4. `configTag` (string) — **View derivation**

- **Source today.** Identical to `defaultConfig` (line 1061 in
  `processYaml.py`).
- **Future shape per `plan-block-registration.md`.** The
  trampoline plan envisions `configTag` becoming per-`(variant,
  Config, instance)` once multi-Config-per-block bindings land
  (Step 10). At that point, `configTag` is a project-level
  artefact derived from the instance tree, not a fact about the
  block in isolation.
- **Verdict.** Belongs in the view-assembly layer
  (`getBDConfigInfo`), not in the DB.
  - Today's value is a one-line copy of `defaultConfig`. No
    benefit to persisting separately.
  - Tomorrow's value depends on per-instance Config bindings
    that the `blocks` table cannot represent.
  - Centralising the derivation in `getBDConfigInfo` gives the
    future per-variant logic a natural home and keeps every
    consumer reading `data['configTag']` (a stable view-side
    contract) regardless of how the value is computed under the
    hood.

### Summary table

| Field            | Expensive? | Per-block? | Per-caller drift?      | Where it belongs                              |
| ---------------- | ---------- | ---------- | ---------------------- | --------------------------------------------- |
| `isParameterizable`     | Yes        | Yes        | No                     | DB (post-processing)                          |
| `defaultConfig`  | No         | Yes        | No                     | DB (post-processing)                          |
| `configTag`      | No         | Yes        | Future yes (per-inst.) | View (`getBDConfigInfo`)                      |
| `configContexts` | —          | —          | —                      | Dropped (intermediate; no consumer; no field) |

### Why retain `getBDConfigInfo`

Even after the lift, `getBDConfigInfo` keeps a real job:

1. **One point of view assembly.** Templates depend on a stable
   bundle of fields (`isParameterizable`, `defaultConfig`, `configTag`)
   on the per-block `ret` dict. Whether each
   is "read from a persisted column," "derived in place," or
   "computed at view-assembly time" is an implementation detail.
   `getBDConfigInfo` is the boundary that hides that detail from
   templates.
2. **Future-proofs `configTag`.** When the trampoline plan's
   per-instance `configTag` lands, the derivation lives here and
   remains invisible to templates. Without `getBDConfigInfo`,
   every template would gain a `configTag = ...` derivation of
   its own, drifting on the first divergent edit.
3. **Natural home for additional view-shaped helpers.** The
   templates currently compute `cfg = '<Config>' if isParameterizable
   else ''` and `templateDecl = 'template<typename Config>' if
   isParameterizable else ''` independently in many places (constructor,
   classDecl, testbench, blockRegistrar, module_hdl_wrapper).
   Bundling these into `getBDConfigInfo` is a future cleanup
   that this plan does not propose, but the room is here.

## Selected Architecture

### Pipeline placement

A new method `calcBlockConfigInfo()` is added to `processYaml.py`
and called from `processProject()` immediately after
`generateIndexes()` and either before or after `calcAddresses()`
(see "Ordering" below). The exact insertion point is:

```python
# create database indexes
self.generateIndexes()
# perform all address calculations
self.calcAddresses()
# NEW: derive per-block config info (isParameterizable, defaultConfig, ...)
self.calcBlockConfigInfo()
# generate address enums and types
self.generateAddressEnums()
```

### Persisted fields

Two scalar fields are added to the `blocks` schema in
`config/schema.yaml` (alongside `maxAddress`). `configTag` is
deliberately *not* persisted (it is a view derivation) and
`configContexts` is deliberately *not* persisted (it is an
intermediate of the `defaultConfig` derivation with no real
consumer) — see the Critical Review.

```yaml
blocks:
  block: key
  desc: required
  ...
  maxAddress: optional(0)        # filled out by address generation
  isParameterizable: optional(false)    # filled out by block config post-processing
  defaultConfig: optional("")    # filled out by block config post-processing
```

No JSON-in-column fields. No new sub-tables. If the
`configContexts` list ever gains a real consumer, it is added at
that point as a sub-table on `blocks` matching the `params`
precedent (see Critical Review for the shape).

### `calcBlockConfigInfo()` implementation (post-processing)

The new method implements the **structure walk** that today's
`getBDConfigInfo` performs, driven by direct table access rather
than by the per-block view that `getBlockData()` constructs. It
produces and persists the two database truths (`isParameterizable`,
`defaultConfig`); it does *not* produce `configTag`, and it does
not persist or return `configContexts`.

The important implementation constraint is equivalence with the
assembled `ret` view, not merely equivalence with the YAML tables.
Today's `getBDConfigInfo` runs after `getBlockData()` has already
expanded reg-handler views, implied register connections,
memory/register ports, deduplicated ports, and `connectDouble`
entries. A raw-table implementation must reproduce those row
selection rules exactly before it changes the source of truth.

Inputs the pass reads from `self.data` (already populated by
`processYamls()` and finalised by `generateIndexes()`):

- `self.data['structures']` — to look up `isParameterizable` and
  `_context` for any referenced structure key.
- `self.data['interfaces']` and `self.data['interface_defs']` —
  to enumerate the structures each interface carries, mirroring
  the `get_intf_data` / `get_connection_intf_data` resolution
  used by today's `getBDConfigInfo`.
- `self.data['instances']`, `self.data['connections']`,
  `self.data['connectionMaps']`, `self.data['registerConnections']`,
  and `self.data['memoryConnections']` — to reconstruct the same
  port and `connectDouble` candidates that `getBlockData()`
  exposes today.
- `self.data['registers']` and `self.data['memories']`, interpreted
  through the same reg-handler, memory-connection, and
  register-connection rules used by `getBDRegistersMemories()`,
  `getBDMemoryConnections()`, and `getBDRegisterConnections()` —
  to pick up `structureKey` and `addressStructKey` references.

Algorithm (per qualified block):

1. Initialise local-only `is_parameterizable = False`, `contexts = []`.
   The list is a function-local intermediate — it never leaves
   `calcBlockConfigInfo()`.
2. Reconstruct the same port candidates that today's
   `ret['ports']` would expose. For each one, resolve the
   connection's interface data (matching today's
   `get_connection_intf_data`) and call `add_struct_context(...)`
   on every structure the interface declares.
3. Reconstruct the same double-ended connection candidates that
   today's `ret['connectDouble']` would expose. Do the same
   interface resolution and structure enumeration.
4. Reconstruct the same register/memory row candidates that
   today's `ret['registers']`, `ret['memories']`,
   `ret['memoriesParent']`, `ret['memoryConnections']`,
   `ret['memoryPorts']`, and `ret['registerPorts']` would expose.
   For each row, call `add_struct_context(...)` on `structureKey`
   and `addressStructKey`.
5. Compute `defaultConfig`:
   - If `is_parameterizable` and `contexts` is non-empty:
     `<basename(contexts[0]) sanitized>DefaultConfig` (verbatim
     transcription of today's logic at lines 1051-1054).
   - Else if `is_parameterizable`: `<blockName>DefaultConfig`.
   - Else: `""`.
6. Persist via SQL:

   ```sql
   UPDATE blocks
   SET isParameterizable = ?, defaultConfig = ?
   WHERE blockKey = ?
   ```

7. Mirror the two values back onto
   `self.data['blocks'][qualBlock]` so in-memory readers see the
   new fields without a reload. The local `contexts` list is
   discarded.

The structure-context detection helper is identical in intent
to today's `add_struct_context` closure inside `getBDConfigInfo`.
The lift moves it to a private method (e.g.,
`_blockConfigStructWalk`) so it can be unit-tested in isolation.

Equivalence checklist for the raw-table walk:

- Reg-handler blocks use the parent block's register/memory rows
  where today's `getBDRegistersMemories()` does.
- Memory and register port rows include both explicit connections
  and implied ports created by `getBDMemoryConnections()` /
  `getBDRegisterConnections()`.
- Connection structures are enumerated from the same interface data
  and in the same order as `getBDPorts()` and
  `getBDConnectionsFinal()` expose them to today's
  `getBDConfigInfo()`.
- Discovery order of parameterizable contexts is preserved exactly.
  `defaultConfig` is derived from `contexts[0]`, so a stable but
  different order is still a behavior change.

### Slim `getBDConfigInfo()` (view assembly)

`getBDConfigInfo` survives, but its body shrinks to a per-call
view-assembly step. It is still invoked from `getBlockData()`
exactly where it is invoked today (line 1006), and templates
continue to read three of the four field names off `ret`
(`configContexts` is dropped — see Critical Review):

```python
def getBDConfigInfo(self, ret):
    block_row = self.data['blocks'][ret['blockInfo']['blockKey']]

    # Persisted truths — read directly from the blocks row.
    ret['isParameterizable']    = bool(block_row.get('isParameterizable', False))
    ret['defaultConfig'] = block_row.get('defaultConfig', '')

    # View-shaped derivation — today an alias for defaultConfig;
    # future per-(variant, Config, instance) logic lands here when
    # plan-block-registration.md Step 10 multi-Config support
    # arrives. Keeping the derivation centralised means templates
    # never read configTag from anywhere except this assembled
    # view.
    ret['configTag'] = ret['defaultConfig']
```

This is constant-time, requires no walks, and gives templates a
stable surface (`data['isParameterizable']`, `data['defaultConfig']`,
`data['configTag']`) regardless of how each field is computed
underneath.

### Ordering relative to `calcAddresses`

`calcBlockConfigInfo()` does not depend on address values and
`calcAddresses()` does not depend on config info, so the two are
independent. Running config-info second (after `calcAddresses`)
keeps the existing pipeline's narrative ordering ("addresses are
the first calculated thing, then everything else"). If a future
change makes one depend on the other, the ordering is a
single-line move.

### `getBlockData()` changes

`getBlockData()` keeps its existing `self.getBDConfigInfo(ret)`
call site at line 1006. The body of `getBDConfigInfo` is what
changes: the structure walk is gone, replaced by the constant-time
view-assembly shown in "Slim `getBDConfigInfo()`" above. There is
no behavioural change visible to callers that use the supported
config-info surface (`isParameterizable`, `defaultConfig`, `configTag`) —
the cost and the source of truth move. The unsupported
`configContexts` intermediate is removed from `ret`.

### Caller migration

For callers that hold a per-block `data` dict from
`getBlockData()`, the only behavioural change is that
`data['configContexts']` is gone. Templates do not read that
field today, so the visible impact is limited to:

- `pysrc/newModule.py` line 37 currently forwards
  `configContexts` into `blockCondData`. The forwarding loop
  drops `configContexts` from its field list:

  ```python
  for field in ['isParameterizable', 'defaultConfig', 'configTag']:
      blockCondData[qualBlock][field] = blockData[field]
  ```

  No `cond:` clause uses the field today (it cannot, since the
  evaluator is a scalar `==` check), so this is a pure surface
  cleanup.

For callers that only need `isParameterizable` / `defaultConfig` and
would otherwise pay a full `getBlockData()` walk just to read
them, a faster path becomes available against the persisted
truths. Two known hot spots:

- `pysrc/newModule.py` builds `blockCondData` by calling
  `getBlockData(qualBlock, trimRegLeafInstance=True)` for every
  block in the project, purely to extract the config-info
  fields. After the lift, the loop can read
  `prj.getBlockConfigView(qualBlock)` for the three-field bundle.
  This removes one full `getBlockData()` walk per block per
  `newModule` invocation while keeping `configTag` derivation in
  one place.
- `templates/systemc/classDecl.py` line 73 calls
  `prj.getBlockData(key)['isParameterizable']` for every direct child
  block when emitting forward declarations (and again at line
  118 for instance handling). After the lift, this becomes
  `prj.getBlockConfigView(key)['isParameterizable']`. The walk over the
  *child block's* connections / ports / registers — currently
  re-run inside every parent's `getBlockData()` — disappears.

`templates/systemc/module_hdl_wrapper.py::render_sc` keeps the
`data.get('isParameterizable', False)` defensive read for the
hierarchy-mode `vl_wrap.cpp` invocation (the project-level `data`
dict still doesn't carry per-block fields by design). The defence
stays a defence, but it now coexists with a strict invariant in
the per-block path: per-block templates always see the field
populated, because `getBDConfigInfo` always writes it.

## Implementation Steps

1. **Schema.** Add `isParameterizable` and `defaultConfig` entries
   under `blocks:` in `config/schema.yaml`, each with
   `optional(<empty default>)` and the explanatory comment
   matching the `maxAddress` style. Do **not** add `configTag`
   (view-side derivation), `configContexts` / a JSON column /
   a sub-table (intermediate value with no consumer — see
   Critical Review).
2. **Post-processing pass.** Implement
   `processYaml.py::calcBlockConfigInfo()` per the algorithm
   above. The structure walk transcribes today's observable
   `getBDConfigInfo` result, including the row selection already
   performed by `getBlockData()`, but obtains those candidates
   from raw tables instead of from a constructed `ret` dict.
   Persist the two truths via `UPDATE blocks SET ...` and mirror
   them onto `self.data['blocks'][qualBlock]`. The local
   `contexts` list is used only to compute `defaultConfig` and is
   then discarded.
3. **Pipeline wiring.** Call `self.calcBlockConfigInfo()` from
   `processProject()` after `self.calcAddresses()` and before
   `self.generateAddressEnums()`.
4. **Slim `getBDConfigInfo()`.** Replace its body with the
   constant-time view-assembly shown above: read the two
   persisted fields off `self.data['blocks'][qualBlock]` and
   derive `configTag` (today: identity copy of
   `defaultConfig`). Stop writing `ret['configContexts']`. The
   call site in `getBlockData()` is unchanged.
5. **Config view helper.** Add `prj.getBlockConfigView(qualBlock)`
   that returns the three-field bundle (`isParameterizable`,
   `defaultConfig`, `configTag`) without running the rest of
   `getBlockData()`. This is the only supported entry point for
   callers that do not already have a full per-block view; do not
   duplicate `configTag = defaultConfig` at call sites.
6. **`newModule.py` simplification.** Replace the
   `getBlockData(qualBlock, trimRegLeafInstance=True)` walk that
   builds `blockCondData` with `prj.getBlockConfigView(qualBlock)`.
   Drop `configContexts` from the forwarded field set in the
   `for field in [...]` loop at line 37 — it has no `cond:`
   consumer and is no longer produced anyway. The `blockCondData`
   dict itself stays.
7. **Template simplification.** Update
   `templates/systemc/classDecl.py` (sub-block forward decls and
   sub-block instance config check) to read `isParameterizable` via the
   helper instead of
   `prj.getBlockData(key)['isParameterizable']`. Identical refactor
   anywhere else in `templates/` that calls `getBlockData()`
   solely to read one of the three config-info fields — a `grep`
   pass during implementation will list them. Templates that
   already have a per-block `data` from `getBlockData()` need
   **no change** —
   the three supported fields appear on `data` exactly as before.
8. **Defensive-read review.** Inspect every call site that today
   uses `data.get('isParameterizable', ...)`. Confirm the only legitimate
   one is `module_hdl_wrapper.py::render_sc`'s hierarchy-mode
   path. Anywhere else the defensive read masked a real per-block
   shortfall, the lift makes the field reliably present and the
   `.get(...)` reverts to a strict `data['isParameterizable']`.
9. **Trampoline-pass alignment.** The block-registration plan
   (`plan-block-registration.md`) currently pulls `isParameterizable`,
   `defaultConfig`, and `configTag` out of
   `getBlockData()`. After this lift, the trampoline pass reads
   the same fields via the helper from step 5, which makes the
   project-level instance walk faster and removes one place
   where `getBlockData()` is invoked solely to access derived
   fields. When `plan-block-registration.md` Step 10 lands the
   per-instance `configTag`, that derivation moves into
   `getBDConfigInfo` (or a sibling view function the trampoline
   pass calls) — it does **not** require schema changes.

## Validation

```bash
# Existing prototype gate (must keep passing).
make -C ../../proto/model step6

# Compile-check the touched generators.
python3 -m py_compile \
  pysrc/processYaml.py \
  pysrc/newModule.py \
  templates/systemc/classDecl.py \
  templates/systemc/module_hdl_wrapper.py

# End-to-end: regenerate and rebuild the two reference projects
# and confirm the generated outputs are byte-identical to a
# pre-lift baseline.
rm -rf examples/ip_test/.gen
make -C examples/ip_test gen
diff -ru <pre-lift-snapshot>/examples/ip_test/model examples/ip_test/model
make -C examples/ip_test/rundir clean
make -C examples/ip_test/rundir

rm -rf examples/helloWorld/.gen
make -C examples/helloWorld gen
diff -ru <pre-lift-snapshot>/examples/helloWorld/model examples/helloWorld/model
make -C examples/helloWorld/model gen && make -C examples/helloWorld/model
```

Acceptance criteria:

- The diff against the pre-lift snapshot is empty for every
  generated artifact in `ip_test` and `helloWorld`. The lift is a
  pure refactor of *where* the values are computed, not *what*
  they evaluate to.
- `make -C ../../proto/model step6` still reports `PASS`.
- `examples/ip_test` continues to emit
  `model/ipRegistrar.cpp`, `model/ipLeafRegistrar.cpp`,
  `model/srcRegistrar.cpp`, and `model/ip_topRegistrar.cpp` with
  identical content.
- A `grep -n "getBlockData(" templates/ pysrc/newModule.py` listing
  shows the call count has dropped relative to the pre-lift
  baseline (call sites reading only the config-info fields move
  to `getBlockConfigView(...)`).
- A targeted multi-context fixture confirms that a block touching
  parameterizable structures from more than one YAML include
  still selects the same `contexts[0]` and therefore the same
  `defaultConfig` name as the pre-lift implementation.

## Benefits

- **Eliminates the recomputation tax.** A typical generate run
  calls `getBlockData()` many times per block; today each call
  re-walks every connection, port, register, and memory just to
  fill in `isParameterizable`. After the lift, the walk happens once
  at YAML-processing time. `getBDConfigInfo` survives but
  becomes a constant-time view assembler.
- **Clean responsibility split.** Post-processing owns the
  expensive truth-finding work and DB persistence;
  `getBDConfigInfo` owns the per-call view assembly. The two
  layers have non-overlapping responsibilities and a stable
  contract between them (`isParameterizable` and `defaultConfig` are
  persisted; `configTag` is assembled in one helper).
- **Removes the "is this view a per-block view?" ambiguity.**
  Every place that legitimately holds a per-block dict can rely
  on `isParameterizable` / `defaultConfig` / `configTag` being present.
  The hierarchy-mode `vl_wrap.cpp` call is the lone defensive
  `.get(...)` and remains by design.
- **Aligns with the existing post-processing precedent.**
  `calcAddresses` already establishes the pattern of "derive
  once, persist on the `blocks` row, view-assemble downstream."
  This lift adds a sibling pass with the same shape.
- **Simplifies `newModule.py`.** Today the file rebuilds a
  parallel `blockCondData` map specifically because the
  config-info fields aren't on the raw block schema row. After
  the lift, the schema row carries the persisted truths
  directly, and `getBlockConfigView(...)` supplies the full
  bundle.
- **Closes a future trampoline-pass dependency cleanly.** The
  per-block trampoline emission needs `(qualBlock, isParameterizable,
  defaultConfig, configTag)` for every block. After the lift,
  `isParameterizable` and `defaultConfig` are a SQL `SELECT` over the
  `blocks` table; `configTag` comes from the same view-assembly
  function templates use, so future per-instance `configTag`
  logic lands in one place.

## Risks / Considerations

- **Schema migration.** Adding columns to `blocks` invalidates
  any pickled / cached schema artefacts. The existing
  `maxAddress` precedent shows this has been handled before, so
  the cost is presumed low; this plan flags it for the
  implementer to confirm.
- **Removing `configContexts` from the per-block view.** The
  field is currently produced by `getBDConfigInfo` and forwarded
  by `newModule.py`. The grep across `templates/` and `pysrc/`
  showed no real consumer beyond the `defaultConfig` derivation
  inside the producer itself, so removal is safe. If a
  downstream branch or third-party template not in the grep
  scope reads `data['configContexts']`, it will break — the
  byte-diff regen step in Validation will surface that
  immediately. Recovery is a sub-table per the Critical Review,
  added at that point.
- **Caller drift.** Anywhere the codebase reads `isParameterizable`
  through `getBlockData()` rather than the new helper after the
  lift, the lift produces no benefit but no harm — the field
  arrives via `getBDConfigInfo` either way. A follow-up `grep`
  pass during implementation cleans up the cases that do
  benefit from the helper; none of them block correctness.
- **Raw-table equivalence.** The largest implementation risk is
  missing a synthesized row that today's assembled `ret` view
  includes before `getBDConfigInfo()` runs. The implementation
  must preserve the current row selection and context discovery
  order; the targeted multi-context validation exists to catch
  drift in `defaultConfig`.
- **`configTag` future shape.** The plan parks `configTag` in
  view assembly specifically because
  `plan-block-registration.md` Step 10 wants it per-instance.
  If a different decision lands there (e.g., `configTag` stays
  per-block forever), `defaultConfig` and `configTag` collapse
  into a single column and `getBDConfigInfo`'s view-side
  derivation simplifies to a row read. Either outcome is
  cheaper than today's structure walk.
- **Test coverage.** The lift is a pure refactor, so the
  existing `ip_test` and `helloWorld` byte-diff comparison is
  the strongest broad test. Add one targeted multi-context
  regression for `defaultConfig` ordering; the trampoline pass's
  existing regressions
  (`make -C ../../proto/model step6`, the templated-grandchild
  `ipLeaf` regression) cover the consumer side.

## Out of Scope

- Any change to *what* `isParameterizable`, `defaultConfig`, or
  `configTag` mean. The lift transcribes today's supported
  derivation logic verbatim into the new layers; `configContexts`
  remains only a local intermediate of the `defaultConfig`
  derivation.
- Per-instance `configTag` enumeration. That is
  `plan-block-registration.md` Step 10 territory. This plan
  parks `configTag` in the view-assembly layer specifically so
  Step 10 can land without schema or post-processing changes.
- Bundling additional view-shaped helpers (`cfg`,
  `templateDecl`, etc.) into `getBDConfigInfo`. The plan
  identifies this as the natural growth direction but does not
  propose it now — templates continue to compute those locally.
- The list-vs-scalar encoding of `configContexts`. The plan
  records the trade-off and deliberately avoids adding storage
  until a real consumer exists.

## Related Plans

- [`plan-block-registration.md`](./plan-block-registration.md)
  — the per-block trampoline pass that consumes the three
  config-info fields. This lift removes one
  `getBlockData()` round-trip per block from that pass.
- [`research-block-registration-options.md`](./research-block-registration-options.md)
  — option-space and decision rationale for the trampoline
  approach; the lift is independent but eliminates one of the
  recurring "where do we read `isParameterizable`?" friction points
  recorded there.
