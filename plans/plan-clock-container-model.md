# Plan: clocks and resets on the container model

- **Status:** IMPLEMENTED (2026-09-15). Phases 1-5 and 7 land in this tree;
  phase 6 (the register handler bridge, §7 item 6) is tracked as its own
  plan. Every §8 item is resolved.
- **Specification:** [`spec-clock-reset-requirements.md`](./spec-clock-reset-requirements.md).
  R and V numbers below refer to it. Where this plan and the specification
  disagree, the specification is right and this plan is stale.
- **Baseline:** the implementation recorded in
  [`plan-multi-clock-reset.md`](./plan-multi-clock-reset.md), which realises
  project-scoped clock nets with per-block derivation. That model is not
  released to users; this plan replaces it. Only the single implicit `clk` and
  `rst_n` behaviour is preserved (spec §4.2, R5, R10).
- **Source:** issue #129.

---

## 1. What changes, in one page

| Aspect | Baseline | Target (spec) | Where |
| :--- | :--- | :--- | :--- |
| A block's clocks | Derived from connections and an additive `clocks:` list of project references (`deriveBlockClocksResets`) | Declared completely on the block, or implicit `clk`/`rst_n`; nothing derived (R5) | §3.1 |
| Meaning of a block `clocks:` entry | A project clock the block carries | A module port with `direction`, `default`, `period` (§4.2) | §2.1 |
| Instance binding | Implied: child port name = project net name | `clocks:`/`resets:` maps on the instance; name match; default fallback for `clk`/`rst_n`; outputs explicit (§4.4) | §3.2 |
| Project `clocks:`/`resets:` | Nets of the design, referenced everywhere with `scope: project` | Testbench clocks bound to the top block; not used to bind a child instance, though a block's own `period`/`releaseCycles` for standalone simulation still come from it (§4.1, R3, V21) | §2.1, §3.5 |
| Output clocks and resets | Deferred (baseline §1 D5) | `direction: output`, local nets, export by declaration (§4.5) | §3.3 |
| Connection `clock:` | Project reference; also on maps, memory and register connections | Container clock; on `connections:` only (§4.3) | §2.2 |
| Memory domain | `memoryClocks` from connections | `clock:`/`reset:` on the memory declaration (§4.3, R19) | §2.3, §3.4 |
| Handler and router reset | `resets[0]` | Selected reset of the bus clock (R6, V19) | §5.3 |
| Wrapper clocks | One `sc_clock` per derived clock, from project attributes | Testbench view for the top; resolved or declared attributes for a standalone block (§4.8, R24, V21) | §5.5 |
| Flop macros, alias, reset styles | `_DOM` family, `wire clk`/`rst_n` aliases, three styles | Unchanged in shape; alias sources change to default clock and selected reset (§4.10) | §5.2 |

Things that do not change: the `_DOM` macro family and style selector in
`common/systemVerilog/flops.sv`; the `instanceClockResetBinds` view shape
`{port, signal}` consumed by `moduleInterfacesInstances.py`; per-port
`domainClock`/`domainReset` on port rows consumed by the wrapper's BFM binding;
the DB as the sole channel between `projectCreate` and `projectOpen`.

## 2. Schema (`config/schema.yaml`)

Follow `config/SCHEMA_SPECIFICATION.md` for every edit. The data contract
changes below need the schema owner's confirmation before implementation.

### 2.1 Declarations

- **Project `clocks:` / `resets:`** (lines 732–763). Fields unchanged: `desc`,
  `default`, `period`, `timeUnit`; `desc`, `default`, `clock`, `releaseCycles`.
  Keep `projectScope` and `flat`. Semantics change only in what consumes them
  (§3.5). `default` is implied for a single entry (§4.1).
- **Block `clocks:`** (lines 283–290). From `list` of project references to a
  keyed mapping: `clock` (key), `desc` optional, `direction` optional
  `input|output`, `default` optional bool, `period`/`timeUnit` optional. Drop
  `scope: project` from the validator: the key is a new name, not a reference.
  Accept the list short form with the single-entry limit of §4.2 in a
  pre-parse normaliser, not as a second schema shape.
- **Block `resets:`** (lines 291–298). Same change: `reset` (key), `desc`,
  `direction`, `default`, `clock` referencing the same block's `clocks:` (a
  block-local reference, `scope: block`, or validated in post), `async` bool.
- **Instances.** New optional `clocks:` and `resets:` mappings, key = child
  block clock, value = string or null (`~`). Both sides are validated in
  `projectCreate`, not by the schema, because the value set includes local nets
  that exist only after binding resolution (§3.2).
- **Memories.** New optional `clock:` and `reset:`, block-local references to
  the owning block's declarations, default block default clock and its
  selected reset.
- **`registerPorts:`, `addressBlock:` and `ports:`.** New optional `clock:`,
  block-local; `registerPorts:` and `addressBlock:` also get optional `reset:`
  (spec §4.3 "Routers").
- **Empty `resets: {}`** on a block declares no reset (spec §4.2); the
  normaliser distinguishes absent from empty.

### 2.2 Removals

- `clock:` on `connectionMaps:` (518–523), `memoryConnections:` (652–657),
  `registerConnections:` (687–692): delete the field and the
  `_post_resolveConnectionClock` post-parser attachments at schema lines 488,
  622 and 666. A row that still carries it fails schema validation with the
  standard unknown-field diagnostic.
- `clock:` on `connections:` (420–425, 465–470): keep the field, drop
  `scope: project`; validate in `projectCreate` against the container's nets
  (V13, V14). Drop the `_post_resolveConnectionClock` fill-in of the project
  default, called directly from `_process_connections`
  (`processYaml.py:8632`) rather than through a schema `post()` attachment:
  an unstated connection clock means rule 3 of §4.3, not a project reference.

### 2.3 Post-parsers

- `_post_resolveClockPeriod` (schema 733, `processYaml.py` 8899–8901): keep
  for the project section; add the same period validation for block clock
  `period`.
- `_post_resolveReset` (schema 747): keep; it fills a testbench reset's
  `clock` with the project default.

## 3. `projectCreate` (`pysrc/processYaml.py`)

All new validation lives here (builder-base-development skill: validate
user-authored YAML in `projectCreate`). Every diagnostic goes through
`diagnosticLocation`; row positions for instance maps come from the instance
row's `lc`.

### 3.1 Block declaration normalisation

Replaces the block-derivation body of `deriveBlockClocksResets` (5655–5934).
Phase 1 keeps its two callees, `_persistInstanceClockResetBinds` (5935) and
`_persistMemoryClocks` (6024), running on this section's output instead of
the deleted derivation, since
`templates/systemVerilog/moduleInterfacesInstances.py` (124, 146) reads
their tables in every phase; §3.2 replaces the first callee and §3.4 the
second, both in phase 2.

- Materialise implicit declarations: a block with no `clocks:` gets
  `clk` input; a block with no `resets:` and a default clock gets `rst_n` on
  it; a block with no input clock gets no resets (R5, V15).
- Compute the block default clock (V18) and the selected reset per block clock
  (R6, V18, V19). Candidates include local reset nets of a container (§3.3),
  excluding a net consumed only by asynchronous inputs, so the final selection
  runs after binding resolution; the declared-only part runs here.
- Project file: exactly one default clock and reset, default reset on the
  default clock (V23); the selected reset of a testbench clock.
- Checks: V1, V2 (`ports:`/`registerPorts:` `clock:`), V7 (names pairwise
  distinct including `clk`/`rst_n` aliases, interface ports, memories), V15,
  V18 (`default`/`period` never on an output).
- Persist into `blockClocksResets` with additional columns `direction`,
  `isDefault`, `period`, `timeUnit`, `clock` (reset membership), `async`,
  `selectedReset` (per clock). Keep `orderIndex` = declaration order (R18).

### 3.2 Instance binding resolution

New. Runs per container after §3.1, replacing `_persistInstanceClockResetBinds`
(5935, called from `deriveBlockClocksResets` at 5931).

- Container net set: the container's declared clocks and resets (or implicit),
  plus local nets discovered in this pass.
- Per child instance, per block clock and reset of the child, in this order:
  map entry; name match for inputs; default fallback for names `clk`/`rst_n`
  (R10, §4.4); else V3. Outputs: map entry required (V3); value is a declared
  `output` of the container (export), a new local net name, or `~`. A clock
  entry binds a clock net, a reset a reset net (V4). V12 for `count`.
- Drivers: one per net (V5); an output bound to a container input is an error;
  an instance never binds two entries to a net one of them drives.
- Local net membership: a local reset net belongs to the clock the driving
  child's output reset belongs to, mapped through that child (V6). Export
  membership is checked against the container's declaration (V6).
- Reset membership for every input binding (V6); async inputs exempt.
- V22: every local net has a child input consumer.
- V11: the fallback for `rst_n` uses the selected reset of the clock `clk`
  bound to; a clock with no selected reset makes the fallback an error.
- Persist `instanceClockResetBinds` unchanged in shape (`childPort`,
  `parentSignal`, `orderIndex`) so `moduleInterfacesInstances.py:120–124`
  keeps working; add `direction`. New table `containerLocalNets` (`blockKey`,
  `kind`, `netName`, `driverInstance`, `memberClock`).

### 3.3 Selected reset, second pass

After §3.2, complete the selected reset of each container clock with local
reset nets as candidates (R6, V19) and persist it. Routers and register
handlers read it (§5.3).

### 3.4 Port domains, memories, register trees

Replaces `getBDPortDomain` (3081) inputs and `_validateSingleDomainObjects`
(6071–6143).

- Port domain per connection end, rules 1–3 of §4.3, in the container's net
  names: declared port `clock:` mapped through the instance; connection
  `clock:` with reverse lookup (V13); block default mapped through the
  instance. Both present and different is V14.
- `connectionMaps:` boundary port: inner derived domain; must be a container
  block clock, not an unexported local net (V16); outer connection end must
  agree mapped through the container's instance (V16).
- Memories: domain from the declaration (`clock:`, default block default),
  `reset:` membership (V19); `memoryConnections:` accessors must derive to the
  same container clock as the memory through its owning instance (V8). Persist
  in `memoryClocks` with the reset added.
- Register trees: the feed's domain propagates down the decode tree through
  the bindings at each level; every router, handler and register is in it
  (V8). The router single-clock rule of the baseline is kept and becomes a
  consequence of this check.
- Register handler domain: for a reusable IP leaf, the block clock of its
  `registerPorts:` entry, else the block default; its reset is the entry's
  `reset:` else the selected reset of that clock (V19). For a top-down leaf,
  which authors no `registerPorts:`, the block clock and reset are the R25
  selection: the leaf's declared clock port that the instance's `clocks:`
  map binds to the bus clock, and independently the leaf's declared reset
  port its `resets:` map binds to that clock's selected reset; two ports
  bound to the same net break the tie by declaration order, and every
  instance of the block must resolve to the same pair (V8, V25, V26).
- Router domain: the `addressBlock:` entry's `clock:`, else the feed
  connection's, else the block default; reset likewise (spec §4.3 "Routers").
  A nested router's synthesised feed carries no clock.
- `config/postParseRegisterPorts.py`: its register-bus synthesis stamps a
  project-scoped clock via `resolveProjectScopedName('clocks', ...)`
  (811–822) onto every synthesised `connections` and `connectionMaps` row,
  read through `_registerBusFeedClock` (291–332). Once §2.2 drops `clock:`
  from `connectionMaps:` and `scope: project` from `connections:`, this
  stamp must stop touching `connectionMaps` rows and switch the
  `connections` stamp to a block-local reference, or every synthesised
  `addressBlock:` project (`apbDecode`, `mixed`) fails schema validation.
  A top-down leaf's register clock and reset selection (R25) does not move
  with it. `_leafRegisterBinding` (206–238) runs in this pass, before §3.2's
  instance binds exist, so it resolves only the reusable-IP case: the leaf's
  declared `registerPorts:` entry, else the block default.
  The R25 selection for a top-down leaf runs after §3.2, per leaf instance:
  map match of the leaf's declared clock port to the container clock, in the
  leaf's own container, of the far end of its synthesised feed: the router's
  `addressBlock` port when the router is in the immediate parent, or the
  parent's own synthesised register-bus port when the parent is itself a
  single-consumer router-less container; and of its declared reset port
  to that clock's selected reset; two ports bound to the same net resolve by
  declaration order (tie); every instance of the block must resolve to the
  same pair.
  No clock match is V8, no reset match is V25, and disagreement is V26.
- Blocks with `hasVl`: every clock timing a port has a selected
  reset, for the BFM (V19; `clockTree.build()`,
  `unittest/test_clock_domains.py`).

### 3.5 Testbench binding and resolution

New.

- Bind the `topInstance` block to the project file's clocks and resets by the
  §4.4 rules (R3, V9, V10), with the testbench as the top's container for reset
  membership (V6) and `count` 1. A child project's file is not used to bind
  the child instance (R14), though the child block's own `period`/`releaseCycles`
  for standalone simulation still come from it (V21);
  `IMPLICIT_PROJECT_DECLARATIONS` (3782–3787) stays as the source of the
  implicit testbench `clk`/`rst_n`.
- Resolved clock per block clock per instance path (§2 "Resolved clock"):
  follow bindings upward through inputs; at a net driven by a child output
  that is an export, continue through the exporting container's own binding;
  stop at a testbench clock, a local net, a top-block output, or `~`. Persist
  per block: for each input clock, the set of resolved nets across instances.
- Supply graph over resolved nets (V20): edges at every instance of a block
  for each output no child drives, from the block's inputs to that output; a
  block with no inputs is a root. Cycle and root check, hierarchical instance
  spelling in the diagnostic.
- V21 for blocks with `hasVl`, evaluated in the declaring project
  only: declared `period`, or exactly one resolved testbench clock through at
  least one instance; resets likewise for `releaseCycles`.
- Persist a `standaloneClockAttrs` view source: per block input clock, the
  `period`/`timeUnit` to use; per input reset, the `releaseCycles`.

### 3.6 Deletions

- `deriveBlockClocksResets` body and its "reset follows clock" invariant; the
  default floor for disconnected leaves (baseline §3); the additive semantics
  of block `clocks:`.
- `_post_resolveConnectionClock` default fill (8923–8938).
- Any `scope: project` lookup of clocks from blocks, connections, memory or
  register connection rows.

### 3.7 Container net model

The model phases 2-4 build. Five entities, no more:

- **Container.** A block that instantiates others, and the testbench project
  acting as the root container.
- **Net.** One per clock or reset within a container. Kinds: declared (a
  container clock or reset), local (a net a child output drives inside the
  container), testbench (at the root). A reset net belongs to one clock net,
  except an asynchronous reset input's net, which belongs to none.
- **Driver.** Exactly one per net: the container's own input port, a child
  instance's output port, the container's own implementation behind a
  declared `output` no child drives, or the environment at the root. This is
  the spec §4.6 table (`Net inside container B` / `Driver`) expressed as a
  field; V20's root case is a block with no driving input, this driver kind
  among them.
- **Consumer.** A child instance's block clock or reset bound to the net by
  map, name match or fallback (§4.4, R10). The consumer edge records how it
  was bound.
- **Block declaration.** The per-block clocks, resets, default clock and
  selected reset phase 1 already derives: the `blockClocks`, `blockResets`,
  `blockDefaultClock` and `selectedResetByClock` maps `deriveBlockClocksResets`
  builds (`pysrc/processYaml.py:5686-5689`), persisted into `blockClocksResets`
  and read back by `getBDClocksResets` (`pysrc/processYaml.py:1559`).

Each verification item checks one invariant of this model:

| Check | Model invariant |
| :--- | :--- |
| V3 | Every input block clock/reset of an instance has a consumer edge; every output appears in the map. |
| V4 | A map key names a block clock or reset of the child; an `input` map value names a declared net or a driven local net; an `output` map value names a declared `output` of the container, a local net name, or `~`; a clock entry binds a clock net and a reset entry a reset net. An unmapped asynchronous reset input with no same-name net is an error. |
| V6 | A consumer reset's net belongs to the net its own clock's consumer edge resolves to: for a declared net, the container's `clock` field; for a local net, the clock its driving output's block reset belongs to, mapped through the supplier's instance. The same check applies to an `output` reset bound onto a declared `output` reset. An asynchronous reset input's consumer edge is exempt. |
| V13 | A connection `clock:` names a net exactly one input block clock of the instance's consumer edges resolves to. |
| V8 | A memory node's clock is a block clock of its owning block; every `memoryConnections:` consumer edge resolves to the same net as the memory's, mapped through the memory's instance, and a memory with such consumers has no driver of `~`. A register-bus tree is one net throughout, from the feed to every router, handler and register in it. |
| V20, V22 | V20: the supply graph, an edge at every instance from each of a block's input nets (asynchronous reset inputs included) to each output net the block itself drives (not a child's export), is acyclic and rooted; a block with no input clock or reset is a root, and every supplied net reaches a testbench net or a root. V22: every local net has at least one consumer edge. |
| V21 | Per instance of a `hasVl` block in its declaring project, the input clock's consumer chain resolves to one testbench net across every instance, of which there is at least one, or the clock declares its own `period`; disagreement across instances is the error. Each input reset resolves to one testbench reset the same way, else takes the default `releaseCycles`. An asynchronous reset input's release count needs the block default clock to be an input clock. |
| V25, V26 (R25) | Register-port selection for a top-down leaf: the consumer, among the instance's block clocks, of the bus net; and, independently, the consumer among its reset nets of the bus net's selected reset. Every instance of the leaf block must agree (unanimity). |
| crossings (R16) | Two connection ends cross when their block clocks bind to different nets of the same container; two container clocks bound to one parent net remain distinct nets, so binding through a parent does not by itself remove a crossing. |

Boundaries: the model is built inside `projectCreate` during derivation
(§3.2-§3.5) and flattened into the tables the `projectOpen` views already
read: `blockClocksResets` (`getBDClocksResets`), `instanceClockResetBinds`
(`getBDInstanceClockResetBinds`), `containerLocalNets` (`getBDLocalNets`,
new in phase 3, not present at HEAD), and `memoryClocks`
(`getBDMemoryClock`). Templates never see the model; they consume the
`projectOpen` view fields as today. No general graph library, visitor
framework or plugin layer is introduced. The implementation is the four
classes of §3.8, `BlockDomains`, `Net`, `Container` and `ClockTree`; a driver
and a consumer are records `Net` holds, not separate classes.

### 3.8 Implementation module: the clock tree model

The model exists to make checking and using clocks and resets simple. It is an
in-memory structure built during `projectCreate`, not persisted. The three
existing tables, `blockClocksResets`, `instanceClockResetBinds` and
`memoryClocks` (CREATE at `pysrc/processYaml.py:5946-5949`, `:6076-6078`,
`:6112`), remain the persisted form and are produced from the model. The model
does not replace parser functionality: `processSimple` normalisation,
`_normalizeClockResetShortForm` (`pysrc/processYaml.py:7328`), the three
surviving schema `post(...)` hooks (`pysrc/processYaml.py:8985, 8995, 9001`)
and the row shapes in `flatData` stay as they are; the model consumes parsed
rows.

`pysrc/clockTree.py` holds four plain classes, dataclasses or plain classes
with no base class and no framework:

- `BlockDomains`. One per block: clocks and resets in declaration order, the
  default clock, and the selected reset per clock. Built from a
  `flatData['blocks']` row (fields per `config/schema.yaml:258-380`: the
  `clocks` subtable rows `clock, desc, direction, default, period, timeUnit`;
  the `resets` rows `reset, desc, direction, default, clock, async`), applying
  the implicit `clk`/`rst_n` rules (R5) and the empty-`resets:` flag the parser
  records. Owns V1, V2, V7, V15, V18. Replaces the phase 1 dictionaries
  `blockClocks`, `blockResets`, `blockDefaultClock` and `selectedResetByClock`
  (`pysrc/processYaml.py:5686-5689`), and the per-container alias
  `containerSelectedReset` (`pysrc/processYaml.py:5988`, itself
  `selectedResetByClock[containerKey]`, a block fact).
- `Net`. One per clock or reset in a container: name, `isReset`, kind
  (declared, local, testbench), for a reset the clock net it belongs to (none
  for an asynchronous input), exactly one driver (kinds per §3.7: own input
  port, child output, own implementation behind an undriven output,
  environment at root), and consumers as an (instanceKey, block clock or
  reset, binding kind) tuple, where binding kind is map, name match or
  fallback. Replaces `clockBindNet` (`pysrc/processYaml.py:5991`).
- `Container`. A block that instantiates children, or the testbench root; holds
  nets by name and child instances.
- `ClockTree`. Blocks by key, containers by key, and the root. `build()` takes
  explicit arguments only: the `flatData` sub-dicts the phase 1 derivation
  reads today (`blocks`, `instances`, `connections`, `memories` at
  `pysrc/processYaml.py:5683, 6095`, `memoryConnections` at `:6124`,
  `registerConnections` at `:6145`), the testbench clocks and resets from
  project `data`, the two parser-recorded sets `_blocksDeclaringNoResets`
  (`:3847`, read at `:5783`) and `_connectionsWithAuthoredClock` (`:3855`,
  read at `:5914`), and `diag`. The exact signature is fixed by the
  implementation; `build()` reaches into no `projectCreate` attribute other
  than `diag`'s two methods, `logError(msg)` and `diagnosticLocation(yamlFile,
  lc)` (signatures at `pysrc/processYaml.py:4463` and `:7244`); in production
  `diag` is the `projectCreate` instance, in tests a stub. `check()` runs the
  invariants of §3.7. `rows()` returns the three row lists in the exact column
  order of the existing INSERTs (`pysrc/processYaml.py:5950-5953`,
  `:6079-6081`, `:6113-6114`).

Decisions recorded:

- Block declarations live inside the tree (`ClockTree.blocks`).
- Resolution for V21 (`_resolveAllInstances`/`_resolveStandaloneAttrs`) is
  computed during `build()` and is not persisted.
- Persistence stays in `processYaml.py`: the tree returns rows and the existing
  SQL writes them; the module-level cursor (`g.cur`) never enters the model.
  The module does not import `processYaml`.

`processYaml.py` keeps `_normalizeClockResetShortForm`, the three
`_post_resolve*` hooks, the `getBD*` views (`pysrc/processYaml.py:1559, 1602,
1617, 3106, 3138`), and the CREATE/INSERT SQL. `_validateClockResetNames`
(`pysrc/processYaml.py:8944`) also stays: it checks a name collision between a
project's own `clocks:` and `resets:` sections
(`self.data['clocks'][projectName]` against `self.data['resets'][projectName]`)
before any tree exists, so it is parser-side, not model-side.

The four call sites at `pysrc/processYaml.py:4008, 4010, 4403, 7384` reduce to
three. `deriveBlockClocksResets()` at 4008 and
`_validateSingleDomainObjects(blockClocks)` at 4010 become `build()` then
`check()` at that same site, followed by persisting `rows()`.
`_normalizeClockResetShortForm` at 7384 is unchanged: it runs inline from
`processSimple`'s per-item dispatch, before a tree exists to build.
`_validateClockResetNames` at 4403 is unchanged, for the reason above.

Phase mapping: phase 2 adds the map binding kind and the R25 selection as a
lookup on the bus net's consumers. Phase 3 adds the local net kind and the
child-output and own-implementation drivers; V20 and V22 become one loop over
nets. Phase 4 adds `Net.resolve()`, V21 and the end-of-run report.

Tests: `unittest/test_clock_domains.py` builds a `ClockTree` from dict inputs
and a stub `diag`. The `object.__new__(projectCreate)` construction
(`unittest/test_clock_domains.py:707`) is removed in this step, since
`build()`'s explicit inputs make it unnecessary. Existing cases keep their
assertions.

Introducing the model changes no output. Verification, sequential (memory:
`a2c-build-serialization`): `make clean`, `make -j8 unittest`, `make -j8
two-clk`. A `diff -r` of `examples/twoClk`'s `rtl` and `verif` (and `ip/rtl`,
`ip/verif`) captured before and after must be empty. The four `TODO phase`
markers move with their code; `grep -rn 'TODO phase' pysrc` returns the same
count before and after. This step lands as its own commit, before any phase 2
behaviour.

## 4. `projectOpen` views

Language-neutral, DB-backed; templates consume fields, never `prj.data` walks.

- **Derived tables load at open.** `loadData()` (`pysrc/processYaml.py:499`)
  gains a loader for the four non-schema tables, run from `loadData()` itself
  or from `__init__` beside the `self.loadData()` call (`:479`):
  `blockClocksResets` grouped by `blockKey`, `instanceClockResetBinds` grouped
  by `instanceKey`, `memoryClocks` grouped by `memoryBlockKey`, and
  `blockParameterizedDecls` grouped by `blockKey`, included so one loader
  pattern covers all four derived tables rather than three plus an exception.
  Each becomes a `SELECT * FROM <table>` grouped into `self.data[table]`; none
  of the four names collides with a schema table name (checked against
  `self.schema.tables` and against `self.data`'s existing keys), so
  `self.data` is the right home, not a second sibling dict. `getBDClocksResets`
  (1560), `getBDInstanceClockResetBinds` (1603), `getBDMemoryClock` (1619) and
  `getBDParameterizedDecls` (1537) read `self.data[table][key]` in place of
  their `g.cur.execute` call; return shapes are unchanged. The four `CREATE
  INDEX` statements in `_persistClockTree` and `deriveParameterizedDeclSets`'s
  persist step (`idx_blockClocksResets_blockKey`,
  `idx_instanceClockResetBinds_instanceKey`, `idx_memoryClocks_memoryBlockKey`,
  `idx_blockParameterizedDecls_blockKey`) are dropped; a per-key index only
  earned its keep when the query ran per key, and the loader replaces that
  with one scan. `projectOpen` keeps exactly one SELECT per table, in the
  loader; no `g.cur.execute` remains in any `getBD*` helper. Gate: `make
  clean`, `make -j8 unittest`, `make -j8 two-clk` run sequentially (memory:
  `a2c-build-serialization`); `diff -r` of `twoClk`'s generated artifacts
  before and after is empty; a unit test asserts the loaded dicts equal the
  four tables' contents for a small project, or equivalently that each of the
  four helpers' output is unchanged against a direct SELECT.
- `getBDClocksResets` (1559): rows gain `direction`, `isDefault`,
  `selectedReset`, `async`, `period`, `timeUnit`. Order is declaration order.
  Add `defaultClock` and `defaultReset` (the selected reset of the default
  clock, possibly absent) on the block for the alias helper.
- `getBDInstanceClockResetBinds` (1602): unchanged shape; add
  `direction` so the SV template can emit an output binding.
- New `getBDLocalNets(blockKey)` (new in phase 3, not present at HEAD):
  `[{kind, name, memberClock}]` for the container's wire declarations (R18).
- `getBDMemoryClock` (1617): return clock and reset.
- `getBDPortDomain` (3106) / `getBDPortDomainReset` (3138): source from the
  §3.4 results; unchanged field names `domainClock`, `domainReset`.
- New `getTestbenchClocksResets()`: for the top block, the testbench entries
  with the top port each binds, with `period`, `timeUnit`, `releaseCycles`.
- New `getBDStandaloneClocks(blockKey)`: per input clock and reset, the
  attributes from §3.5, and whether each reset is `async`.
- Register handler and router views expose `busClock` and `busReset` (§3.4)
  in place of the `clocks[0]`/`resets[0]` convention.

## 5. Templates

### 5.1 SystemVerilog module (`templates/systemVerilog/moduleInterfacesInstances.py`)

- Ports: declared clocks then resets in declaration order, `input` or `output`
  per `direction` (R18). `clock_reset_port_names` and
  `sv_clock_reset_input_lines` in `intf_gen_utils.py` (222–243) gain
  direction.
- Container body: `wire` per local net from `getBDLocalNets` (R18); child
  instance binds from `getBDInstanceClockResetBinds` including outputs; a `~`
  output left unconnected.
- Memory instantiation (line 146): clock from the memory's declared domain;
  reset passed where the bridge exists (§7, deferred).
- `templates/systemVerilog/module_hdl_wrapper.py` (84, 118, 242) also emits
  clock/reset ports and binds, through the same
  `sv_clock_reset_input_lines`/`sv_clock_reset_binds` helpers in
  `intf_gen_utils.py`; give it the same direction handling so an output
  clock on a `hasVl` top is not declared `input`.

### 5.2 Default-domain aliases (`intf_gen_utils.sv_default_domain_aliases`, 257–263)

- `wire clk = <defaultClock>` only when the block has a default clock and does
  not declare `clk`; `wire rst_n = <selectedReset of defaultClock>` only when
  that exists and the block does not declare `rst_n` (§4.2, §4.10). Never the
  first entry.

### 5.3 Register handler and router (`moduleRegs.py` 26–35, `apbDecodeModule.py` 43–50)

- `regs_clk`/`regs_rst` and `decode_clk`/`decode_rst` from the `busClock` and
  `busReset` view fields, not index 0. The `_DOM` emission is otherwise
  unchanged. `pslverr` propagation through routers is part of the bridge (§7).

### 5.4 Flop macros (`common/systemVerilog/flops.sv`)

- No change. The style selector and `_DOM` bodies already carry the spec's
  §4.9 obligations; the alias change in §5.2 is what the bare macros need.

### 5.5 SystemC wrapper (`templates/systemc/module_hdl_wrapper.py`)

- Top: construct one `sc_clock` per testbench clock and one reset driver per
  testbench reset from `getTestbenchClocksResets` (lines 128–160, 393–430),
  bound to the top ports they bind. Output clocks and resets of the top are
  bound to `sc_signal`s and observed, not driven; today the wrapper drives
  every entry of `data['clocks']` (121–143), so output entries must be
  excluded from `clock_gen`.
- Standalone block: the same from `getBDStandaloneClocks`; an async reset
  input counts `releaseCycles` on the block default clock (§4.8).
- Lockstep (416–434): `reset_driver`'s existing behaviour is unchanged. The
  reset is copied at the partner's event and never waits on a clock (§4.8).
- BFM binding (195–196): unchanged in mechanism, from `domainClock` and the
  selected reset of that clock as `domainReset`; a port on an observed output
  clock binds to the observed signal.
- End-of-run report (R23): count edges on every clock net the wrapper can see
  that is not testbench-generated, and observe release of every non-testbench
  reset; report at `sc_stop`. Scope for the first drop: the top's exported
  outputs and, where the wrapper has visibility, internal supplied nets;
  record what is not visible.
- Phase randomisation is not planned (§7, Q7).

### 5.6 SystemC block module and testbench templates

- Models carry no clock or reset ports (R26); the block module template does
  not change. The SystemC wrapper (§5.5) drives clocks and resets to the RTL
  side only; co-simulation compares data ports only.

## 6. Fixtures, tests, documentation

### 6.1 Examples

- `examples/twoClk`: rewrite to the new syntax. The container declares
  `clk` and `clkSlow` with resets; `twoClkSlowTick` declares its clock as a
  block port; the connection `clock: clkSlow` names the container clock; the
  child project `twoClkIp` keeps its own project file for standalone use and
  is bound by instance maps in the assembler. This fixture is the composition
  and renaming test.
- New `examples/clkGen` (or extend `twoClk`): a divider with an `output`
  clock, a synchroniser with an async input and an `output` reset, consumers on
  the local nets, one export to the parent, a `~` binding. Covers §4.5, V5,
  V6 membership of local nets, V20, V22, R23 in simulation.
- The divider and synchroniser blocks need `.sv` and `.cppm` implementation
  files. Scaffold both with `make newmodule`, then `make gen`, per
  `rules/skills/manage-build.md`'s rule that an implementation file arch2code
  scaffolds is never created by hand. Do not write either file directly.
- The examples' churn gate needs `make clean` first (memory:
  `a2c-make-clean-after-infra-change`). Example builds and the unit suite are
  never run concurrently (memory: `a2c-build-serialization`).

### 6.2 Unit tests (`unittest/`)

- New: the derived-tables loader (§4, "Derived tables load at open") on a
  small project, asserting `self.data['blockClocksResets']`,
  `self.data['instanceClockResetBinds']`, `self.data['memoryClocks']` and
  `self.data['blockParameterizedDecls']` equal the four tables' contents, or
  equivalently that `getBDClocksResets`, `getBDInstanceClockResetBinds`,
  `getBDMemoryClock` and `getBDParameterizedDecls` return the same values as
  before the loader replaced their per-key SELECT.
- `test_clock_domains.py`: phase 2's first step (§3.8) removes its
  `object.__new__` construction of an empty `projectCreate`
  (`unittest/test_clock_domains.py:707`); tests build a `ClockTree` from a
  declaration set and `flatData` instead. Beyond that, replace derivation
  assertions with declaration and binding assertions; one test per V entry
  with a minimal failing fixture and a diagnostic-substring assertion,
  V1–V23.
- `test_clock_reset_emission.py`: today asserts additive block `clocks:`
  lists, canonical order, an alias onto the block's first clock, and the
  feed-clock decode tree. Rewrite the additive-list, canonical-order and
  first-clock-alias assertions for §2.1's declared clock mapping and §5.2's
  default-clock alias in phase 1; rewrite the feed-clock decode-tree
  assertions for §3.4's router and handler domain rules in phase 2.
- `test_register_decode_clock.py`: router and handler domain from the feed
  through container bindings; selected reset selection with two resets; the
  respelling case becomes an explicit-map case; a top-down leaf's
  register-port selection (R25): no leaf clock bound to the bus clock (V8),
  no leaf reset bound to the bus reset (V25), instances that disagree on the
  resolved pair (V26), and two leaf clock ports bound to one container clock
  accepted as a tie.
- `test_project_scope.py`: two projects with same-named clocks bound to
  different assembler clocks; child project file not used to bind the child
  instance in composition (R14), though its `period`/`releaseCycles` for
  standalone simulation still come from it (V21).
- New: testbench binding (V9, V10), fallback (R10, V11), resolved clock and
  V21 with `hasVl` on a twice-instantiated child block, local nets and V22,
  supply graph cycles (V20), alias emission with and without a selected reset.
- As implemented: `test_clock_domains.py`, `test_clock_reset_emission.py`,
  `test_register_decode_clock.py` and `test_project_scope.py` cover the
  above; `test_clock_local_nets.py` is a new file added for local nets,
  exports and `~` bindings. `unittest/run_all_tests.sh` runs 53 test files.
- Generation gate is insufficient on its own (baseline §13.1): the clkGen
  fixture runs under `make VL_DUT=1`. The end-of-run report itself is not
  asserted at run time: the example's `make VL_DUT=1` target streams its
  output rather than capturing it, so there is nowhere in the example build
  to check the report's text against.

### 6.3 Documentation

- `rules/skills/design-architecture.md` lines 99–107 (the "Clocks and
  Resets" bullets, including "Emitted ports" at 102), `rules/skills/setup-project.md`
  lines 89–101 ("Design YAML must not declare them"), and
  `rules/skills/rtl-core.md` line 138 ("wire clk = <first clock>") all
  describe the baseline; rewrite each for the declared-port model and add
  the instance map.
- Add a clocks and resets section to the RTL core and SystemC core skills:
  declaring block clocks, the bare macros and their aliases, output clocks.
- `plan-multi-clock-reset.md`: insert this sentence at the front of its
  `- **Status:**` line: "Superseded by
  [`plan-clock-container-model.md`](./plan-clock-container-model.md) and
  [`spec-clock-reset-requirements.md`](./spec-clock-reset-requirements.md);
  kept as the record of the landed `_DOM` macro, alias and reset-style work
  described below." The rest of the header stays; it records work that
  survives. When this sentence is inserted, also correct lines 9-10 of that
  file, which still list §6.4's reset-style selector as remaining Phase 1
  work even though §6.4's body is marked LANDED, so the selector is no
  longer listed as remaining.
  - Retired along with it: the CDC primitive library (its §6.3, the
    `cdcSync2`/`cdcPulse`/`cdcHandshake`/`cdcAsyncFifo` item at line 1306);
    its §8 Phase 2 candidates (`suppliesClocks:`/`suppliesResets:`,
    dual-clock memory primitives, a generated SDC skeleton, hoisting clock
    generation into one project module, exposing duty cycle/start
    delay/first edge, a per-assembler `period:` override); and, from its §1
    decisions table, D4 (project-scoped visibility) and D5 (clock/reset
    suppliers deferred to phase 2), together with item 7 of its §10 open
    decisions (boundary binding, deferred to phase 3). This plan's declared
    ports and instance maps replace all of them; none carries forward.
  - Survives as the record of landed work: its §6.1-6.4, §6.6 and §6.7,
    which describe the `_DOM` macro family, the default-domain alias, the
    reset-style selector, and the clock-parameterized flops already shipped
    in `flops.sv`, `moduleRegs.py` and `apbDecodeModule.py`.

## 7. Phasing

Each phase ends with, in order and from `/work/ws/test/builder/base`:
`make clean`, then `make -j8 unittest`, then separately `make -j8 two-clk`,
never run concurrently (memory: `a2c-build-serialization`). Both must be green
before the next phase starts.

1. **Declarations.** §2.1 block schema, §3.1, §4 `getBDClocksResets`, §5.1
   ports, §5.2 aliases. Inputs only; instance binding by name match and
   fallback only (no maps yet); connections keep `clock:` as a container
   clock. Also land the top and standalone attribute source of §3.5/§4/§5.5
   here: `templates/systemc/module_hdl_wrapper.py`'s `row["period"]`/
   `row["timeUnit"]` (132–133) and `row["releaseCycles"]` (160) reads lose
   their source the moment `deriveBlockClocksResets`'s derivation body is
   gone, and `twoClk`'s `run-vl` build fails without it. Deletes only that
   derivation body; `_persistInstanceClockResetBinds` and
   `_persistMemoryClocks` keep running until §3.2 and §3.4 replace them in
   phase 2. Fixture: `twoClk` rewritten.
2. **Instance maps.** First step: introduce the clock tree model (§3.8), its
   own commit, before any behaviour in this phase lands. Second step: the
   derived-tables loader (§4, "Derived tables load at open"), its own commit.
   Then §2.1 instance maps, §3.2 for inputs, §3.4 port domains and
   memory/register rules,
   including the top-down leaf register-port selection (R25, V8, V25, V26),
   the §3.7 container net model, §5.3 handler and router domains, §2.2
   removals. Fixture: `twoClk` composition with explicit maps and renaming.
3. **Outputs and local nets.** `direction: output`, local nets, export, `~`,
   V5, V6 for local nets and exports, V20, V22, §3.3, §5.1 wires and output
   binds. Fixture: `clkGen`.
4. **Testbench and standalone.** The rest of §3.5 binding and resolution
   (V9, V10, V21, resolved clock, supply graph) and the rest of §5.5 wrapper
   behaviour (R26); attribute sourcing moved to phase 1. End-of-run report.
5. **Documentation and skills.** §6.3.
6. **Register handler bridge (R20, V24).** Separate plan once phases 1–4
   are in: handshake bridge in `moduleRegs.py`, memory-side reset from
   `reset:`, `pslverr` generation and router propagation, bridge behaviour
   with the memory side in reset. Until then a memory with `regAccess` whose
   clock differs from its handler's bus clock is rejected at build (§3.4,
   V24; `clockTree.build()`, `unittest/test_clock_domains.py`). Of
   phases 1-7, the bridge itself is the only one not implemented in this
   tree.
7. **Cleanup.** Once phases 1-5 are in, remove every plan-specific artefact
   phases 1-5 left in the tree; these markers are kept deliberately during
   development, so intermediate commits carry them, and removing them is the
   last step before this plan is marked done. This phase does not wait on
   phase 6, which is tracked as its own plan.
   - The `TODO phase N` markers: exactly four today, all in
     `pysrc/processYaml.py` (lines 1577, 1592, 5713, 5801; `grep -rn 'TODO
     phase' pysrc config templates unittest`), each replaced by the
     behaviour it deferred or deleted along with the placeholder it marks.
   - The `SKIPPED` registries and their phase-naming reason strings, in
     `unittest/test_clock_reset_emission.py` (from line 2029) and
     `unittest/test_register_decode_clock.py` (from line 478): every skipped
     case is either rewritten to pass against the final behaviour or deleted
     as retired, so the skipped count returns to zero. Remove the `Skipped
     cases:` reporting in `unittest/run_all_tests.sh` (lines 439, 442) and
     `unittest/run_all_tests_parallel.sh` (lines 150-151) if nothing else
     populates `SKIPPED_COUNT`.
   - Any comment, docstring or diagnostic text that names a plan phase or a
     section of this plan as bookkeeping rather than a durable reference, in
     the files this plan touches: `pysrc/processYaml.py`, the new
     `pysrc/clockTree.py`, `pysrc/intf_gen_utils.py`, `config/schema.yaml`,
     `templates/systemc/module_hdl_wrapper.py`,
     `templates/systemVerilog/moduleInterfacesInstances.py`,
     `templates/systemVerilog/module_hdl_wrapper.py`,
     `templates/systemVerilog/moduleRegs.py`,
     `templates/systemVerilog/apbDecodeModule.py`, `unittest/test_clock_*.py`
     and `unittest/test_register_decode_clock.py`. The check is `grep -rn -i
     'phase [0-9]\|plan-clock' <those files>`, restricted to them: it must
     return nothing but a V or R number in a user-facing diagnostic (a
     durable reference, which stays). `spec §` citations are exempt
     throughout and are not swept: they cite the normative specification, not
     this plan, and are durable wherever they appear (for example
     `pysrc/processYaml.py:3148`, `pysrc/intf_gen_utils.py:268`,
     `config/schema.yaml:300`, `config/postParseRegisterPorts.py:510`).
     Hits outside the listed files, such as
     `unittest/test_migrate_layout.py:3` or
     `unittest/test_nested_ownership.py:307`, belong to other plans and are
     out of scope for this sweep.
   - This plan's own status line moves from PROPOSED to the tree's convention
     for a finished plan, `IMPLEMENTED` with a date (`plan-new-project-onboarding.md`,
     `bug7-crossinterface-boundary-thunker-proposal.md`).
   - Verified by the same `make clean`, `make -j8 unittest`, `make -j8
     two-clk` sequence as every other phase.

## 8. Open items, resolved

- **Containers with own logic on local nets.** Resolved: no authored
  statement was added. `ClockTree`'s V22 check counts only child input
  bindings as consumers (`pysrc/clockTree.py`); a container's own
  hand-written body registers no such binding, so a local net it alone
  consumes is still rejected.
- **End-of-run visibility.** Resolved: the wrapper's R23 report observes only
  the block's own output clocks and resets
  (`templates/systemc/module_hdl_wrapper.py`'s `sec_end_of_simulation`);
  internal nets elsewhere in the design are not visible to it.
- **Pro library.** Checked: `../pro/common/systemVerilog` blocks need no
  change.
- **Downstream flops fork.** Independent of this plan; unaffected.
- **Schema-owned clock and reset references.** Resolved: the existence
  part of V1 and V2 is now a schema combo foreign key. `resets.clock`,
  `ports.clock`, `registerPorts.clock`/`reset`, `addressBlock.clock`/`reset`
  and `memories.clock`/`reset` each carry a `blockClock`/`blockReset` combo
  (block + name) validated against the sibling `blocksclocks.blockclock` /
  `blocksresets.blockreset` storage key, the same shape
  `parameters.variants.params.blockParam` already used against
  `blocksparams`. The hand-written name checks left `pysrc/clockTree.py`;
  the semantic rules (async, one default, direction, V15, selected reset)
  stayed. Two parser changes made it fit: a non-key combo built from an
  unstated optional source is itself unstated and skips its validator, and
  a failing combo diagnostic names the components rather than their
  concatenation. The memory `clock:`/`reset:` gap is closed by the same
  key.
  - Decision: no implicit rows. The implicit `clk`/`rst_n` of a block that
    declares nothing stay a fact of `BlockDomains.build()` alone, so a
    stated `clock:` on such a block is rejected whatever the name, `clk`
    included: it is redundant there. No example or test stated one. The
    normaliser option (materialise marked rows) was built, run and
    withdrawn. The marker it needed served only a diagnostic label and the
    "no default clock, no implicit reset" rule, and both would have moved
    V18 logic into the parser.
  - Not marked `flat`: a combo foreign key matches components in scope
    order and needs no flat index (Foreign-Key Invariants rule 4); `flat`
    is required of plain foreign-key targets only.
