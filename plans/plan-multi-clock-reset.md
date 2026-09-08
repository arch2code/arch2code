# Plan: Multiple clocks and resets

- **Status:** Phase 1 derivation is landed, and so is the port-declaration half of
  §5 emission plus the cycle-based reset release. **The §6 clock-parameterized
  flop macros and the `<block>_regs` emission rows of §5 are now landed too, and
  so is the `apbDecode` router's — every flop any generator emits now names its
  own module's clock. The per-connection BFM binding of §5 is landed too.** The
  remaining §5 binding sites — child instance, memory instance — and §6.3's
  default-domain alias are not written.
  - **Decisions:** none block phase 1. Decision 0 (tandem) is settled by §10.1;
    7 (boundary binding) is deferred to phase 3; 1 (flop macro spelling),
    3 (reset release count), 4 (port spelling), 5 (no crossing report) and
    9 (decoder domain) are settled and landed. Items 2 and 8 shape the work only.
  - **Phase 0 (project scope) is implemented and accepted** — three remediation
    rounds and two adversarial reviews, no live defect. See
    [`plan-project-scope.md`](./plan-project-scope.md) §13.
  - **Landed in Phase 1 so far:** the exactly-one-default rule of §7, which makes
    `defaultClock(project)` / `defaultReset(project)` total; §2.5 default
    injection, so every project owns a default clock and reset whether or not it
    declares one; the resolution of an unstated reset `clock:` to that default
    (§2.2, §2.5); the connection and block domain fields of §2.3 and §2.4; the §3
    per-block derivation, persisted by `projectCreate.deriveBlockClocksResets`
    (`pysrc/processYaml.py:5391`) into the non-schema `blockClocksResets` table;
    the `projectOpen` view `getBDClocksResets` (`pysrc/processYaml.py:1388`); and
    the §7 rules that derivation makes reachable. A cross-domain report also
    landed here and has since been removed by user decision (§10.5), so the tool
    says nothing about a crossing.
  - **Landed next: the §5 port declarations and the cycle-based reset release.**
    Every emitted module port list, verilated SV wrapper port list, DUT
    instantiation, variant trampoline, and Verilated SystemC wrapper now spells
    the block's own resolved sets: one `sc_clock` per clock at its declared
    `period`/`timeUnit`, one `sc_signal<bool>` per reset, and one driver thread
    per reset releasing it after `releaseCycles` edges of that reset's own clock.
    The `resets:` schema gained `releaseCycles` in the same change as its only
    consumer (§2.2). Churn is 23 generated files, all of them the SC wrapper's
    behavioural reset-driver change; every port list is byte-identical to baseline
    for a single-clock project (§5.1). See §10 items 3 and 4.
  - **Remediation round on the §5 emission step — four confirmed findings, all
    closed.** An adversarial review of the step above found four defects, none of
    them in the emitted text of any in-tree project:
    - **The derivation floor could not seed a containment cycle.** The floor was
      applied to leaves only, so a design whose containment holds no leaf (`blkA`
      contains `blkB`, `blkB` contains `blkA`) left EVERY block at zero clocks and
      the emitters then produced a module with no clock port — silently in
      SystemVerilog, and as an `IndexError` on `clocks[0]` in the SC wrapper. Fixed
      as a second floor pass after the union converges; see §3.
    - **`releaseCycles` and `period` were unvalidated and two-typed.** Both are
      now validated as positive integers and coerced at parse time; see §2.2 and
      §7. This closes the `optional(N)` data-contract quirk §2.2 previously only
      recorded.
    - **Two comments asserted invariants that are false**, in
      `templates/systemc/module_hdl_wrapper.py` (the BFM's primary clock/reset
      pair is not a domain) and in `pysrc/intf_gen_utils.py` (the port spelling is
      each generator's, not each language construct's). Both corrected, and the
      test framing that repeated the second was retitled per generator; see §5.1.
    - **Seven checked-in SC wrappers were never regenerated**, because eight
      example databases predate the `releaseCycles` column and `make gen` cannot
      rebuild a database on a schema edit. Regenerated; see §5.2.
  - **Landed next: the §6 clock-parameterized flop macros and the `<block>_regs`
    emission.** `common/systemVerilog/flops.sv` now defines each family's body
    once, as a `_CLK` variant taking the clock as its first argument, with the bare
    macro a one-line alias passing `clk`; `templates/systemVerilog/moduleRegs.py`
    emits the `_CLK` form uniformly and sources the handler's port list from
    `intf_gen_utils.sv_clock_reset_input_lines`. Churn is 7 generated `_regs` files
    plus `flops.sv`, all inside generated regions. See §6.6 and §5.1.
  - **The §4.2 helper that step was said to need does not exist and was not
    needed.** This plan recorded the `<block>_regs` port list as binding ANOTHER
    object's set. It does not: `<leaf>Regs` is itself a row in `blocks`
    (`config/postParseRegisterPorts.py:78`), the generator is invoked with
    `--block=<leaf>Regs`, and `getBlockData` therefore already carries the
    handler's OWN derived sets through `getBDClocksResets`. The premise is
    withdrawn; see §6.6.
  - **Landed next: the `apbDecode` router's flops**, closing the one finding the
    `<block>_regs` step left open. `templates/systemVerilog/apbDecodeModule.py`
    now emits the `_CLK` form at all three of its flop-emitting sites, naming the
    router's own derived clock, so a non-default-domain decode tree no longer has
    a domain-correct handler and a wrong-domain router. Churn is 7 generated
    router files — the complete set in tree — 69 lines, all inside generated
    regions; no source file but the template moved. See §6.7.
  - **That step also settled the invariant `clocks[0]` rests on, and it does not
    hold for the router.** For `<block>_regs` it holds BY CONSTRUCTION and is now
    proved rather than assumed. For the router it is constructible to break with
    ordinary authored YAML, generation exits 0, and the emitted router is silently
    clocked by the wrong domain. Not fixed here; see §6.7 and the new §7 rule.
  - **Landed next: the per-connection BFM clock binding of §5.** Each BFM in a
    Verilated SystemC wrapper is now clocked by the clock of the connection it
    drives, taken from a new `domainClock` field on every port row of
    `getBlockData` (`projectOpen.getBDPortDomain`, `pysrc/processYaml.py`). The
    view resolves the connection's clock NAME inside the block's own derived set,
    so a composed IP's port never names a domain its project does not declare;
    §4.2's trap is therefore closed rather than sidestepped. **The reset stays
    the block's**, and that is a conclusion, not a deferral — see §5.3.
    Churn is ZERO: no shipped design has a block in more than one domain, so the
    per-connection clock equals the primary clock everywhere in tree (§5.3).
  - **Still to do in Phase 1:** the §5 rows that genuinely bind another object's
    set — the child-instance and memory-instance bindings, each of which needs a
    `projectOpen` view helper §4.2 defers — §6.3's default-domain alias, §6.4's
    reset-style selector, §6.5's `active: high`, and §7's new single-domain rule
    for a router block. §10 item 9's `postParseRegisterPorts` clock propagation
    is landed.
  - **Verification bar raised.** "Working" now means a verilated co-simulation
    build and run, not `make gen` succeeding. See §13 for the measured baseline
    and the acceptance criteria. The `examples/twoClk` fixture now meets them:
    `make two-clk` generates both projects, runs the model build and the
    `VL_DUT=1` build, and both reach `No error`.
- **Source:** `arch2code/arch2code` issue #129, plus the review decisions recorded in §1.
- **Components touched:** `config/schema.yaml`,
  `pysrc/processYaml.py` (`projectCreate` derivation, `_post_*` row hooks, and a
  `projectOpen` view; row hooks cannot live in `config/postParseChecks.py`,
  because `schema.py::_function_find` resolves `post(X)` only as
  `projectCreate._post_X`),
  `pysrc/intf_gen_utils.py`, `templates/systemVerilog/moduleInterfacesInstances.py`,
  `templates/systemVerilog/moduleRegs.py`,
  `templates/systemVerilog/module_hdl_wrapper.py`,
  `templates/systemc/module_hdl_wrapper.py`,
  `common/systemVerilog/flops.sv`, `common/systemVerilog/memory_*.sv`.
- **Fixture:** a new multi-clock example under `examples/`.
- **Depends on:** [`plan-project-scope.md`](./plan-project-scope.md), which owns
  the `scope: project` mechanism and lands first (§8, Phase 0).

---

## 1. Decisions taken

The issue text is directional. The following decisions supersede it and are the
basis of this plan.

| # | Question | Decision |
| :-- | :--- | :--- |
| D1 | What owns a clock? | The **connection**. A clock is a property of a wire between two instances, not of a reusable `interfaces:` protocol declaration. |
| D2 | What owns a reset? | The **block**, explicitly, or the project default reset when unstated. Resets are not derived from connections. |
| D3 | Clock domain crossing | **The user owns it.** The generator neither rejects, synthesises, nor reports a crossing, and ships CDC primitives so a crossing is never hand-rolled. An amendment adding a mandatory report was implemented and then removed by user decision — a crossing is the designer's business. See §3 and §10.5. |
| D4 | Clock and reset visibility | **Project-scoped**, not global. Within one project a clock is referable from any of that project's design files without include-chain plumbing, via `scope: project` (§2.0.3). Across composed projects the namespaces are distinct; phase 1 wires a boundary by name match with no report, and explicit boundary binding is deferred to phase 3 (§2.0.2, §10.7). `scope: global` is rejected. |
| D5 | Clock and reset suppliers | **Deferred to phase 2.** `suppliesClocks:` / `suppliesResets:` are not added to the schema in phase 1, per the "no planned-but-unused flexibility" rule in `CLAUDE.md`. Phase 1 treats every clock and reset as a primary input at the design top. |
| D6 | Backward compatibility | Required for **authored** input: an existing project with no `clocks:` or `resets:` section must build unchanged, and existing hand-written RTL must compile unchanged. Byte-level churn inside **generated** regions is acceptable where it buys a uniform emitter. **The naive reading of this does not hold** once a project renames its default clock: the bare `DFF` macros reference a literal `clk` that is then no longer a port. §6 resolves this with a generated default-domain alias; without that, D6 is true only for projects that declare nothing. |
| D7 | Terminology | The issue's `interval:` becomes `period:`. It is a simulation attribute only and carries no synthesis meaning. |
| D8 | File placement and scope | **Project file**, as `projectScope` schema sections stored in a `projectName`-keyed bucket that is deliberately not a context, resolved by the new `_validate` option `scope: project`. A general project-scope mechanism of which clocks are the first consumer; owned by [`plan-project-scope.md`](./plan-project-scope.md). See §2.0.3. |

---

## 2. Schema specification

### 2.0 Scope and file placement

The issue calls for "global projectName level scope". The toolchain has no
project-scope mechanism today, and the two obvious substitutes both fail. This
section records what was verified, then states the three viable options.

#### 2.0.1 Verified facts

- **`scope: global` is not the mechanism.** `config/SCHEMA_SPECIFICATION.md`
  states that global lookup "discards include-chain isolation and is therefore
  undesired" and that adding or retaining it "requires explicit architect
  signoff". It is also actively wrong for composition: `_lookupInGlobal`
  (`pysrc/processYaml.py:8311`) raises `Duplicate key ... found in global
  context` when two contexts declare the same name, so two composed projects
  that each declare `clk` would be a hard error rather than a merge.
- **`project.yaml` sections are genuinely parseable and well validated.**
  `instanceGroups:` and `addressObjects:` are structured sections with per-field
  validation and `projFile:line` diagnostics (`_validateProjectAddressRows`,
  `pysrc/processYaml.py:5807`). The only real cost is that the validator is
  hand-written rather than schema-declared. An earlier draft of this plan
  objected that these sections "become a config blob"; that objection was
  incorrect and is withdrawn.
- **`project.yaml` sections are, however, not composable today.** This is the
  decisive constraint.
  - `createProjectConfig` (`pysrc/processYaml.py:4112`) iterates `self.proj`,
    which is base merged with pro merged with the **root** user project only.
  - Child project files are read by `readRaw`, but only `dirs` and
    `fileGeneration` are merged from them, and only into `PROJECTLAYOUT`
    (`pysrc/processYaml.py:3990-4017`).
  - `_normalizeProjectAddressPolicy` reads `self.proj.get('instanceGroups')`
    (`pysrc/processYaml.py:5782`) — root only.
  - Therefore a child IP's own address policy is silently ignored in a composed
    build. On the current machinery, clocks declared in an IP's `project.yaml`
    would be ignored the moment that IP is composed.
  - Additionally, `createProjectConfig` adds **every** project-file key to
    `ignoreSections`, so a section name used in `project.yaml` is blacklisted
    from schema parsing in the design YAML. The two locations are mutually
    exclusive by construction; the choice cannot be deferred or hedged.
- **The design YAML is already composable.** Contexts are path-keyed,
  `CONTEXTOWNINGPROJECT` attributes each context to an owning `projectName`,
  provider selection reconciles duplicate physical copies of one logical project
  (`pysrc/projectScan.py`), and identity keys already carry `projectName` where
  composition demands it (`config/schema.yaml:342`).
- **One "declare once, reference anywhere" precedent exists: `_a2csystem`.**
  Files named in `systemFiles:` are parsed as ordinary schema sections into a
  reserved context (`pysrc/processYaml.py:6449-6453`), and `lookupInScope` falls
  back to that context from every non-global context
  (`pysrc/processYaml.py:8324`). Because the rows are schema rows,
  declarative `_validate` resolves through the fallback normally. The mechanism
  is a2c-wide rather than per-project, so it is a precedent for the shape rather
  than a solution as it stands.
- **Programmatic row injection into a chosen context is an established
  pattern.** `processSingleFile(context, sections=...)` is used for post-process
  synthesis at `pysrc/processYaml.py:4186` and `:5659` and throughout
  `config/postParseRegisterPorts.py`. A project-scoped section can therefore be
  authored in one place and landed in a chosen context without new parser
  machinery.

#### 2.0.2 The composition consequence

Two independently authored IP projects cannot be assumed to agree on clock
names. "Globally available by name" (D4) therefore cannot be the resolution rule
in a composed build: it either collides or silently unifies two unrelated
domains. The general answer is an explicit **binding at the IP instantiation
boundary** — the assembler stating that its `clkSlow` drives the IP's `clk` —
which is structurally the same problem as variant parameter binding, already
solved in `parameters:` (`config/schema.yaml:315`). A binding at the boundary
means a clock behaves as a port of the instantiated block, which reopens the
supplier question deferred in D5: a supplier drives a clock port outward, an
assembler binds a clock port inward.

**That binding is deferred to phase 3 (open decision 7, settled).** Deferring it
does not remove the wiring obligation, because the IP's module carries a real
input port named by the IP's own clock and the assembler must connect something
to it. Phase 1's rule is therefore:

- Drive the IP's clock port from the assembler clock of the **same name** if the
  assembler declares one; otherwise from the assembler's **default** clock.
- Same for resets.
- **Report** every such boundary connection whose two declarations differ in
  `period` or `timeUnit`, naming both projects and both values.

This is backwards compatible by construction **once §2.5 default injection
exists** — and it does not exist yet. An earlier revision of this plan asserted
that Phase 0 already injects a built-in `clk` into every project that declares
none. It does not: the pre-pass `processProjectScopeSections` still reads `if not
sections: continue` for a project that authors no project-scoped section, and
there is no injection code anywhere. **§2.5 injection is therefore the first item of Phase 1,
and every backwards-compatibility argument in this plan depends on it.** Once it
lands, both sides of every existing composition boundary are named `clk`, match by
name, and reproduce today's wiring exactly.

The cost is a genuine surprise, and documenting it here is the whole of the
mitigation: in a composed build **the IP's declared `period` does not drive its
RTL**. The assembler's clock does. The IP's own `period` then affects only its
standalone co-simulation wrapper's `sc_clock`. An IP author declaring a 10 ns
clock and finding it running at the assembler's 1 ns in the composed build has
not hit a bug; they have hit the deferral. A report announcing the mismatch was
implemented and then removed (§10.5), so nothing surfaces it at build time; §10
item 8 records that outcome.

#### 2.0.3 Selected design: project-scoped declarations

`clocks:` and `resets:` are authored in the **project file** and declared
`projectScope` in the schema. References from design YAML resolve with the new
`_validate` option `scope: project`.

**The mechanism is owned by
[`plan-project-scope.md`](./plan-project-scope.md)**, which lands first (§8,
Phase 0). It is general rather than clock-specific; clocks and resets are its
first consumer. That plan is the authority on parsing, storage, and resolution;
this section records only what the clock design depends on, so the two do not
drift.

What this plan relies on:

- **Declaration site.** `clocks:` and `resets:` are project-file sections marked
  `_attribs: [flat, projectScope]`, using the schema entries of §2.1 and §2.2
  unchanged.
- **Storage.** The rows land in the ordinary schema tables in a bucket keyed by
  the declaring **`projectName`**, parsed by a pre-pass that runs before the main
  YAML loop. (That bucket key is the parse-time shape; after `projectOpen` the
  rows are keyed by qualified storage key — see §4.2.) The bucket is deliberately
  **not** a context: it is registered in no context registry, generates no
  header, and is invisible to the ordinary context machinery.
- **Resolution.** A `scope: project` reference is a direct bucket hit keyed by
  `contextOwningProject[<referring file>]`. There is no include-chain walk and no
  fallback, so a reference resolves in its owning project or not at all.
- **Every project contributes.** In a composed build each project in the graph
  parses its own project-scoped rows into its own bucket. Ownership gates
  generation, never data.

**Why this composes.** An IP's `clk` and an assembling project's `clk` are
distinct rows in distinct buckets, and every reference resolves through the
owning project of the referring row. There is no shared namespace, no collision,
no `scope: global`, and no `_lookupInGlobal` duplicate-key error.

**Two consequences for this plan.**

- Because these sections are routed through the parser rather than
  `createProjectConfig`, they bypass the base/pro/user merge of `self.proj`. That
  is what makes §2.5's built-in default the right way to supply `clk`/`rst_n`
  rather than shipping them in the a2c base project file.
- `scope: project` solves **naming and resolution**. It does not solve
  **wiring**: an assembler instantiating an IP whose module carries a port named
  by the IP's own clock must still drive that port. With the boundary binding
  deferred, phase 1 wires it by the name-match-else-default rule of §2.0.2.

The timing pair `period:` / `timeUnit:` sits naturally with the declaration in
the project file and needs no separate treatment.

### 2.1 `clocks:` (new top-level section)

```yaml
clocks:
  clk:
    desc: "main design clock"
    default: true
    period: 1
    timeUnit: ns
  clkSlow:
    desc: "slow peripheral clock"
    period: 2
```

Schema entry (`config/schema.yaml`, Pattern 1 flat table):

```yaml
clocks:
  _attribs: [flat, projectScope]
  clock: key
  desc: required
  default: optional(false)
  period: optional(1)
  timeUnit:
    _type: optional(ns)
    _validate:
      values:
        - ps
        - ns
        - us
```

Notes:

- `period` and `timeUnit` are consumed **only** by the SystemC co-simulation
  wrapper. LANDED: `sec_clock_ctor_init`
  (`templates/systemc/module_hdl_wrapper.py:120`) emits one `sc_clock` per
  resolved clock at its own period, with the unit spelled through the explicit
  `SC_TIME_UNIT` map (`templates/systemc/module_hdl_wrapper.py:10`) rather than
  by transforming the stored string. Splitting the magnitude from the unit avoids
  parsing a `1ns` string, which the builder conventions discourage; the map is
  covered against the schema's declared `values:` by
  `unittest/test_clock_reset_emission.py`, so a unit added to the schema with no
  spelling fails there rather than in the first project to author it.
- Duty cycle, start delay, and first edge stay at the values the wrapper already
  hardcodes (`0.5`, `3 ns`, `true`). They are not exposed until a design needs
  them. The start delay is now load-bearing beyond cosmetics: the reset release
  counts edges from it, so moving it moves every release.
- `period` is validated as a positive integer and coerced to `int` at parse time
  by the `post(resolveClockPeriod)` row hook, sharing the one rule with
  `resets.releaseCycles` (§2.2, §7). Unvalidated it landed in
  `sc_time(<value>, ...)` verbatim, so `period: 0` gave a clock that never ticks
  and `period: abc` gave C++ that does not compile.

### 2.2 `resets:` (new top-level section)

```yaml
resets:
  rst_n:
    desc: "main design reset"
    default: true
    active: low
    clock: clk
  rstAlt_n:
    desc: "alternate reset"
    active: low
    clock: clkSlow
```

Schema entry:

```yaml
resets:
  _attribs: [flat, projectScope, post(resolveReset)]
  reset: key
  desc: required
  default: optional(false)
  active:
    _type: optional(low)
    _validate:
      values:
        - low
        - high
  clock:
    _type: optional()
    _validate:
      section: clocks
      field: clock
      scope: project
  releaseCycles: optional(3)
```

Notes:

- The declared key is the **emitted port name, verbatim**. There is no `_n`
  suffix synthesis and no name mangling. `active:` is metadata consumed by the
  flop macros and by the wrapper's release sequence. A project wanting the
  conventional spelling declares `rst_n`.
- `clock:` associates the reset with a domain. An unstated `clock:` means the
  declaring project's own default clock, resolved at parse time by
  `projectCreate._post_resolveReset` so the
  stored `clock` / `clockKey` are always populated and no consumer repeats the
  rule. That hook now also normalises `releaseCycles`: a section carries one
  `post()` hook, looked up by section name, so both of this section's row rules
  run from it, and its name covers only the first. LANDED as a consumer:
  `sec_reset_drivers`
  (`templates/systemc/module_hdl_wrapper.py:139`) releases each reset after
  `releaseCycles` `posedge_event()`s of that reset's own clock.
- `releaseCycles` is the per-reset release count, added in the same change as
  that consumer (§10 item 3). **Default 3**, chosen so that two rules hold at
  once: two is the minimum correct for a synchronous reset, and three edges of a
  1 ns clock started at 3 ns fall at 3, 4 and 5 ns — the same 5 ns the release
  had while it was an absolute `wait(5, SC_NS)`. Every existing project's release
  instant is therefore unchanged, which is what keeps a test that begins stimulus
  at a fixed time from surfacing as an unrelated regression. The plan's earlier
  suggestion of 8 had no measurement behind it and would have moved every
  release; it is superseded.

  **The value is now validated and coerced, and the data-contract quirk this
  paragraph used to only record is closed.** A schema `optional(N)` default is
  stored as the **string** from the schema text (`pysrc/schema.py:1153` coerces
  only `true`/`false`) while an authored `3` is an int, so an unstated
  `releaseCycles` read `'3'` and an authored one read `5` — one stored fact with
  two types. The emitter only interpolates it, so both spelled the same C++ and
  nothing surfaced it; anything comparing or adding had to convert first.

  Worse, nothing validated the value at all. `0` and `-1` emitted
  `for (int cycle = 0; cycle < 0; cycle++)`, so the loop never ran and `rst_n`
  was `true` at t=0 — **the reset was never asserted, with no diagnostic**. `2.5`
  compiled and released after 3 cycles. `abc` was a C++ compile error rather than
  a generation one.

  Both halves are fixed in one place, `projectCreate._resolvePositiveCount`,
  reached from the `post()` row hook of each section: the value must be a positive
  integer and is coerced to `int` at parse time, so authored and defaulted values
  are indistinguishable downstream. See §7. The generic `optional(N)`
  string-default behaviour is unchanged elsewhere in the schema
  (`count: optional(1)`, `maxValue: optional(0)`, …), as is the `optional(false)`
  boolean family §7 records; only these two fields are validated.
- **`active:` is still not consumed for polarity.** The emitted signal is
  initialised `0` and released to `true`, which is correct for `active: low`
  only. `active: high` remains rejected-in-principle by §6.5 and unimplemented in
  practice: nothing validates it, so authoring it produces a reset asserted the
  wrong way round. Unchanged by this step, and §6.5 still owns it.

### 2.3 `connections:` — new optional `clock:` field

```yaml
connections:
  - {interface: dataIn, src: uProducer, dst: uConsumer, clock: clkSlow}
```

LANDED. Added to both the `_dataSchema` and the storage schema of `connections:`,
and to `connectionMaps:`, `memoryConnections:`, and `registerConnections:`:

```yaml
  clock:
    _type: optional()
    _validate:
      section: clocks
      field: clock
      scope: project
```

**`scope: project` is mandatory, not optional as an earlier revision of this
snippet showed.** `schema.py::_validate_foreign_key_lookups`
(`pysrc/schema.py:788`) rejects any validator against a `projectScope` section
that omits it, in both directions, so the shorter form does not parse.

An unstated `clock:` resolves to the declaring project's default clock, filled in
once by the `post(resolveConnectionClock)` row hook
(`projectCreate._post_resolveConnectionClock`, `pysrc/processYaml.py:8276`) so no
consumer sees an empty `clock` and none repeats the rule — the same treatment
§2.5 settled for `resets.clock`. It also covers the rows post-parse synthesis
adds, since those are parsed through `processSingleFile` like authored ones.

`connections:` needs the field in **both** schemas and cannot use the hook alone.
Its custom handler parses through the `_dataSchema` node, whose section name is
`connections_dataSchema`, and `processSimple` looks the `post()` function up by
that section name (`pysrc/processYaml.py:6994`), so a hook declared on the
storage section never fires. `_process_connections` therefore calls the shared
resolution directly (`pysrc/processYaml.py:8017`). The storage-side `clock:` is
still declared with its validator, which is what creates the `clockKey` column,
exactly as the existing `interface`/`src`/`dst` storage fields are.

### 2.4 `blocks:` — new optional `clocks:` and `resets:` lists

```yaml
blocks:
  myBlock:
    desc: "..."
    clocks: [clkSlow]
    resets: [rstAlt_n]
```

LANDED, as scalar-`list` sub-tables under `blocks:` modelled on the existing
`blocks.params`:

```yaml
  clocks:
    _attribs: [optional, list, flat]
    clock:
      _type: key
      _validate:
        section: clocks
        field: clock
        scope: project
  resets:
    _attribs: [optional, list, flat]
    reset:
      _type: key
      _validate:
        section: resets
        field: reset
        scope: project
```

**`singleEntryList` + `listkey`, which an earlier revision of this section
specified, is rejected by schema validation and cannot be used for a key that is
also a foreign key.** The validator branch adds the qualified key field
`clockKey` with type `ignore` (`pysrc/schema.py:1073`); `Node.add_field` keeps the
first registration and discards the later `contextKey` one
(`pysrc/schema.py:415`); and the `singleEntryList` field-type whitelist
(`pysrc/schema.py:1264`) admits `contextKey` but not `ignore`, so the section is
reported as bad schema. The plain `list` form has no such whitelist, is authored
identically (a YAML list of scalars, handled at `pysrc/processYaml.py:8478`), and
composes the storage key with the parent's, so two blocks may name the same
clock. `flat` matches `blocks.params` and is what gives the derivation a
`blockKey`-carrying flat index.

`clocks:` on a block is additive to what the connections imply. `resets:` on a
block is the block's complete reset set; when absent the block gets the default
reset only (D2). Both are verified by mutation in
`unittest/test_clock_domains.py`.

### 2.5 Implicit defaults for projects that declare nothing

A project that declares no clocks and no resets must keep building unchanged
(D6). Two mechanisms were considered.

**Rejected: shipping the defaults in the a2c base project file.** Declaring
`clocks:`/`resets:` in `$a2c/config/project.yaml` and letting the existing
base/pro/user merge supply them is superficially attractive, but the merge
semantics make it worse than it looks. `merge_with_spec` defaults to
`dict_shallow` (`pysrc/merge_utils.py:44`), so base-shipped rows merge into every
project **per key**, which produces two defects:

- A project that renames its main clock cannot remove the inherited `clk`.
  Shallow merge has no removal sentinel, so a vestigial row persists in every
  project that does not happen to reuse the name.
- A project that declares its own clock with `default: true` then presents two
  rows flagged default, since the base row is still present. That either breaks
  the single-default validation of §7 or forces a special-case demotion rule.

Avoiding both would mean adding a removal sentinel, or splitting the default
designation out of the section into separate `defaultClock:`/`defaultReset:`
scalars purely to make the merge behave. That is machinery in service of the
mechanism rather than the design. The route is not worth its cost.

**Selected: a built-in default injected through the same parser path.** LANDED,
as `projectCreate.IMPLICIT_PROJECT_DECLARATIONS` (`pysrc/processYaml.py:3519`)
parsed by the project-scope pre-pass (`pysrc/processYaml.py:4074`). When a
project declares no `clocks:` section, the pre-pass parses a built-in section for
that project instead of an authored one:

- clock **`clk`**, `default: true`, `period: 1`, `timeUnit: ns`
- reset **`rst_n`**, `default: true`, `active: low`, and **no** `clock:` — see the
  resolution recorded at the end of this section

The injected rows are indistinguishable from authored rows downstream: same
table, same `projectName`-keyed bucket, same `scope: project` resolution, same
validation. Nothing in §3 onward needs to know whether a project authored its
clocks or inherited them, and there is no second code path to keep in step.

Note the interaction with `plan-project-scope.md` §9.2: that plan created a
bucket only for project files that **declare** a project-scoped section. Default
injection is the one case that creates a bucket for a project that declared
nothing, so an injected section is now itself a reason to create one, and
`plan-project-scope.md` §9.2 is updated to say so. Two consequences of every
project owning a bucket:

- The `projectName`-versus-context-key collision check
  (`pysrc/processYaml.py:4085`) now screens every project rather than only the
  declaring ones. That is the correct scope — the bucket it protects now exists
  for every project — and it rejects nothing that was previously valid, since a
  collision needs a project whose `projectName` equals one of its own YAML
  context keys, which no example has.
- Every example database now carries one injected clock and reset row per
  project, verified for `examples/simple` (`clk/simple`, `rst_n/simple` with
  `clockKey` `clk/simple`) and for all four projects of `examples/ip_test`.
  Generated output is byte-identical because nothing outside
  `_post_resolveReset` reads the two tables yet.

Injection is **all or nothing per section**. A project that declares a `clocks:`
section owns that section completely and receives no injection, which is what
keeps the single-default rule of §7 trivially true and sidesteps the merge
defects above entirely. The `clocks:` and `resets:` sections are independent, so
a project may declare its own clocks while inheriting the default reset.

Injection is also **per project, not per build**. In a composed build each
project in the graph is evaluated on its own: a downstream IP that declares no
clocks receives the built-in default in its own bucket, exactly as it would when
built standalone, so its design YAML resolves identically either way. This
follows the database invariant in
[`plan-project-scope.md`](./plan-project-scope.md) §5.2 — every project in the
build contributes its project-scoped rows, and ownership gates generation rather
than data.

A consequence worth stating: two projects that both inherit the default hold two
distinct `clk` rows with identical attributes, one per bucket. That is correct
under project scope, and it makes the common case of the boundary binding
(§2.0.2) a trivial name match.

These names are the ones every existing hand-written module and every flop macro
already use, so an untouched project resolves to exactly today's behaviour.

**RESOLVED — an unstated `clock:` on a reset means the declaring project's own
default clock.** An earlier draft gave the injected reset a literal `clock: clk`,
which contradicts per-section injection: that is a `scope: project` foreign key
into the *same* project's `clocks:` section, so a project declaring `clocks:`
**without** a clock named `clk` and declaring no `resets:` — §6.2's `coreClk`
project — failed on the injected row:

```
In file <proj>/project.yaml:12, section resets, key:rst_n field clock, value clk
is not declared in the clocks: section of project 'assembler'
```

The decision taken, and why the alternatives lost:

- **Rejected: a literal `clock: clk`.** Leaves the mixed case broken as above.
- **Rejected: omit `clock:` and leave the stored value empty.** Nothing breaks at
  parse time, but every consumer then owns the "empty means the default" rule —
  §3 derivation and §5 emission would each re-implement it, and the two could
  disagree.
- **Selected: omit `clock:` from the injected row, and resolve "unstated means the
  default clock" once, centrally.** `_post_resolveReset`
  (`pysrc/processYaml.py:8260`) is a `post()` row hook on `resets:` that fills
  `clock` and `clockKey` from the project's default clock row whenever the field
  is empty. It runs for authored rows as well as injected ones, so the rule has
  one implementation and no consumer ever sees an empty `resets.clock`. `clockKey`
  is copied from the target row's own qualified key, which is by construction what
  the `scope: project` validator (`pysrc/processYaml.py:6953`) builds, since the
  clock row was parsed with the `projectName` as its context.

The resolution is total. The pre-pass validates each project-scoped section's
default entry as soon as that section is parsed and before the next one is
(`pysrc/processYaml.py:4102`), and `clocks:` precedes `resets:` in schema
declaration order, so a default clock is known to exist by the time a reset row
resolves — authored, or injected by this section. The ordering is not luck:
`schema.py` rejects a schema declaring a `scope: project` target section after its
referrer.

---

## 3. Derivation rules

LANDED as `projectCreate.deriveBlockClocksResets` (`pysrc/processYaml.py:5391`),
persisted into the non-schema `blockClocksResets` table in the manner of
`blockParameterizedDecls`. For a block `B`:

```
clocks(B) = { clock(c) for every connection c touching a port of B }
          U { explicit block clocks: entries }
          U { union of clocks(child) for every instance contained in B }

resets(B) = { explicit block resets: entries }   if any were declared
          = { default reset }                     otherwise
          U { union of resets(child) for every instance contained in B }
```

Where "connection" covers `connections:`, `connectionMaps:`,
`memoryConnections:`, and `registerConnections:`, so that register-bus and memory
ports contribute their domain like any other port. The four are walked once, in
one shape, by `_connectionClockSites` (`pysrc/processYaml.py:5362`): a
connection's ends are its two instances' blocks, and for the other three they are
the block owning the object and the block of the instance reaching it.

**Two rules the formula above omits, both required and both landed.**

- **Every contribution is resolved into the receiving block's OWN project,** by
  clock/reset name with a fall back to that project's default. This is §2.0.2's
  name-match-else-default boundary rule applied to derivation rather than only to
  wiring, and it is not optional: a block's port list must be spelled in clocks
  its own project declares, or the same block would emit a different port list
  standalone than composed. Verified on `examples/twoClk`, where `twoClkIpSrc`
  derives `clk/twoClkIp` in the composed build and in its own standalone build
  alike, even though the connection that reaches it is declared in the
  assembler's `clk/twoClk`. A consequence worth restating: every block's set lies
  wholly inside one project, which is what makes the canonical order below
  unambiguous. The rule now has a second consumer — register-decode synthesis
  respells a propagated bus clock the same way (§10.9) — so it lives in one place,
  `projectCreate.resolveProjectScopedName` (`pysrc/processYaml.py:5346`).
- **A block whose derived clock set would be empty gets its project's default
  clock.** A leaf that no connection touches still has clocked RTL, and today's
  emitter gives every module a clock, so an empty set would silently drop it.
  Resets need no floor: the default reset is already the `otherwise` branch of the
  rule above.

  **The floor is two passes, and both are required.** The first runs BEFORE the
  container union and covers **leaves only** — a block with no contained
  instances. It cannot be widened to every empty set at that point, because a
  container whose children all live in a non-default domain would then carry an
  unused default clock as well as the domain it inherits; and it cannot be
  deferred past the union, because a container of a floored leaf has to inherit
  that leaf's clock or it binds a child port it does not declare. Both halves are
  pinned by `unittest/test_clock_domains.py` and each kills the other's mutation.

  The second runs AFTER the union converges and covers any block still empty.
  Only a containment cycle reaches it: a cycle holds no leaf, so the first pass
  never fires inside it and the union has nothing to propagate, leaving every
  block in the cycle at zero clocks. `templates/systemc/module_hdl_wrapper.py`
  then raises `IndexError` on `data['clocks'][0]`, and SV generation silently
  emits a module with no `clk` port that fails Verilator elaboration with
  `PINNOTFOUND`. Mutual containment is itself a design error that `projectCreate`
  accepts silently; **diagnosing the cycle is deliberately not done here** — the
  floor's job is only that no zero-clock block reaches an emitter.

**Ordering.** Both sets are emitted in the declaration order of the `clocks:` and
`resets:` sections, with the default first. Declaration order is a
churn-avoidance contract in `builder/base/CLAUDE.md`; a set-iteration order would
reshuffle port lists on unrelated edits. The resolved sets are therefore stored
as ordered lists, not sets.

**Container union.** A container's clock set is the union over its children plus
its own, which is what allows a clock to be threaded from the design top to any
consumer without an authored connection (D4).

**Crossing reporting — REMOVED by user decision.** A block whose set contains
more than one clock is normal and accepted (D3), and no synchroniser is
generated — inserting one automatically would be worse, since the correct
primitive depends on whether the signal is a level, a pulse, or a bus, and a
wrong choice is a silent functional bug.

A cross-domain report was implemented and shipped: `printWarning` per connection
whose two ends resolved to different clocks, naming the connection, both blocks,
both projects, and both domains with their `period`/`timeUnit`. It fired on
`examples/twoClk`, which has a genuine crossing, so every `make db` there
reported "Found 1 Warning."

**It has since been removed, and nothing replaces it — not an error, not a log
line, not a report file, not a quieter variant.** The tool now says nothing about
a crossing at all. The reason is that a crossing is the designer's business: the
tool has no basis to decide that a declared multi-domain design is a mistake, and
a warning that fires on every build of a correct design trains its reader to
ignore warnings. The argument the report was landed on — that the generator wires
child blocks together in `templates/systemVerilog/moduleInterfacesInstances.py`,
so the crossing appears in no file the user owns — is accepted as true and
accepted as not sufficient to justify complaining. Removed with it:
`_reportCrossDomainConnection` and the per-site label strings in
`_connectionClockSites` that existed only to phrase it. The derivation itself is
unchanged.

**Consequence — two crossings previously left open are no longer open.** An
earlier revision of this section recorded two cases as "unreported and open for
review": a block whose derived set holds more than one clock (the reachable
intra-project signal, which is exactly where a crossing physically sits), and a
container instantiating a foreign child whose domains differ in
`period`/`timeUnit` with no connection between them. Both were framed as "should
these be reported too?". With nothing reported at all, the question is answered by
the same decision: no crossing is reported, so there is no inconsistency left to
resolve and no decision outstanding.

**Retained correction — the intra-project connection crossing is unreachable.**
This is a fact about the derivation, not about the removed report, so it survives
it. An even earlier revision illustrated crossings with "child A resolves to `clk`
and child B to `clkSlow`" inside one project. That case cannot occur: D1 puts the
clock on the connection, so a connection has exactly one clock, and the derivation
above places that one clock in both endpoint blocks' sets. Within a single project
the two ends therefore always resolve to the same row. Only the cross-project
boundary can produce two differing rows, and only when the two projects' same-named
clocks disagree on `period` or `timeUnit` — agreement makes them one physical net
under the deferred name-match wiring (§2.0.2). §2.0.2's mandatory period/timeUnit
mismatch report was discharged by the removed report and is therefore also gone.

Note what the removal costs, since it is a real cost rather than a free
simplification: Verilator performs no CDC analysis whatsoever, is never passed
`-Wall`, and there is no `.vlt` file, so a broken crossing simulates
deterministically and passes every co-simulation and tandem run. Nothing now
signals it.

---

## 4. Where the work lives

Following the ownership split in `builder/base/CLAUDE.md`:

### 4.1 `projectCreate`

- Parse and validate the two new sections and the four new `clock:` fields.
- Synthesise the implicit default clock and reset when the sections are absent
  (§2.5). LANDED.
- Enforce the exactly-one-default rule per project per contributed section (§7).
  LANDED.
- Resolve an unstated reset `clock:` to the project's default clock (§2.2, §2.5).
  LANDED as the `post(resolveReset)` row hook.
- Compute the resolved per-block ordered clock and reset lists and persist them.
  LANDED as `deriveBlockClocksResets` (`pysrc/processYaml.py:5391`), run after
  `postYamlExternalScript()` so post-parse-synthesised connectivity is included.
  The union is a hierarchical fixed point over the instance tree — a real fixed
  point rather than a recursive descent, because a block may legally contain an
  instance of itself (the self-referencing testbench top). Persisted into the
  non-schema `blockClocksResets` table rather than the DB-backed config, following
  `blockParameterizedDecls`: it is per-block data queried one block at a time, so
  a table with an index on `blockKey` fits it better than a blob every generator
  invocation would load whole.
- Enforce the §7 rules derivation makes reachable: the clock/reset name collision
  (`_validateClockResetNames`, `pysrc/processYaml.py:8243`) and the single-domain
  memory and register-bus rules (`_validateSingleDomainObjects`,
  `pysrc/processYaml.py:5514`). LANDED.

### 4.2 `projectOpen`

- A new view helper `getBDClocksResets(ret)`, called from `getBlockData()` after
  `getBDPorts(ret)`. LANDED at `pysrc/processYaml.py:1388`, populating
  `ret['clocks']` and `ret['resets']` as ordered lists in the persisted canonical
  order. It queries `blockClocksResets` directly and does not re-walk the instance
  tree.

  **The entries are the declaration rows verbatim**, not a reshaped projection: a
  clock entry carries `clock`, `clockKey`, `desc`, `default`, `period`,
  `timeUnit`; a reset entry carries `reset`, `resetKey`, `desc`, `default`,
  `active`, `clock`, `clockKey`. An earlier revision of this section named the
  flag `isDefault`. That rename is not made: it would give one stored fact two
  spellings, and it would imply a boolean coercion §7 explicitly declines to
  perform, since `default:` is `optional(false)` and unvalidated. Handing out the
  row follows `ret['blockInfo']` and `parameterizedDecls['body']`.

  Note that after `projectOpen` a `flat` section is keyed by **qualified storage
  key** — `clk/<projectName>` — exactly as `data['blocks']` is keyed by
  `qualBlock`, which is what the persisted list stores. The bucket-keyed form is
  parse-time only ([`plan-project-scope.md`](./plan-project-scope.md) §6.3).

- STILL NOT DONE: the per-child ordered lists on `getBDInstances` and the
  resolved `clock` on `getBDMemoryConnections`. The §5 rows that landed all read
  the sets of the block being rendered, which `getBDClocksResets` already
  supplies; each of these two instead reads the set of a DIFFERENT object, and
  each is a short view helper over the persisted derivation when its emitter
  lands.

- LANDED: the per-**port** resolved clock, as `getBDPortDomain` writing a
  `domainClock` name onto every row of `ret['ports']`. `getBDClocksResets` now
  runs BEFORE `getBDPorts` so the block's set is available while the ports are
  deduplicated. Two annotation sites, because the two port shapes differ: a
  connection port row carries its connection's fields merged in at the top level,
  while a connectionMap / register / memory port keeps its source row whole under
  `'connection'`. Both sites pass the connection-shaped row, so the helper has one
  input shape and does no shape sniffing.

  **A fourth entry has been struck**: a register-bus clock and reset on
  `getBDAddressBlockView` / `getBDAddressBus`. `<block>_regs` was listed here on
  the assumption that its port list binds the bus's set rather than its own. It
  does not — the handler is its own block and its own `getBlockData` call — so the
  helper had no consumer and was not written. See §6.6.

  The per-port clock was the one with a trap worth recording, and the trap is
  real: a port row carries `clock` / `clockKey` copied from its connection, but
  spelled in the **connection's** declaring project, while a block's wrapper
  member is spelled in the **block's** project (§3). `examples/twoClk` already
  exhibits it — `twoClkIpSrc`'s port stores `clk/twoClk` while the block's set
  holds `clk/twoClkIp` — so selecting by `clockKey` would miss even there.
  `getBDPortDomain` therefore matches by NAME and falls back to the block set's
  default row, which is the same name-else-default rule
  `projectCreate.resolveProjectScopedName` applies. `resolveProjectScopedName`
  itself is a `projectCreate` method and is not reachable from `projectOpen`;
  re-applying the rule inside the block's own set is equivalent, because
  `deriveBlockClocksResets` built that set through the same rule, so the set is
  closed under it.

No clock or reset derivation is performed in `pysrc/intf_gen_utils.py` or in any
template; those consume the precomputed fields.

### 4.3 Templates

Each emission site below reads `data['clocks']` / `data['resets']` and iterates.

---

## 5. Emission changes, site by site

The split that decides what landed: a site emitting the **rendered block's own**
clock and reset names reads `getBDClocksResets` and is done; a site emitting
**another object's** set needs a `projectOpen` view helper §4.2 has not written
and is not.

| Site | Today | Change | State |
| :--- | :--- | :--- | :--- |
| `pysrc/intf_gen_utils.py:254` (`sv_gen_ports`) | `input clk, rst_n` on one line | The same one joined `input`, clocks then resets, in canonical order (§10 item 4). | LANDED |
| `templates/systemVerilog/module_hdl_wrapper.py:84` | `input clk,\ninput rst_n` | The same list, one `input` per line — the wrapper generator's own existing style. | LANDED |
| `templates/systemVerilog/module_hdl_wrapper.py:118` | `.clk(clk),\n.rst_n(rst_n)` on the DUT | One binding per resolved clock and reset, in the port-list order. | LANDED |
| `templates/systemVerilog/module_hdl_wrapper.py:242` | `['.clk(clk)', '.rst_n(rst_n)']` | Built from the resolved lists (variant trampoline). | LANDED |
| `templates/systemc/module_hdl_wrapper.py:117, 120` | one `sc_clock clk` at `sc_time(1, SC_NS)` | One `sc_clock` member per resolved clock, each at its own `period`/`timeUnit`. Duty, start delay, and first edge stay at the current constants. | LANDED |
| `templates/systemc/module_hdl_wrapper.py:130, 133, 136, 139` | one `sc_signal<bool> rst_n`, initialised `0`, released at 5 ns | One `sc_signal<bool>` per resolved reset, and one `SC_THREAD` per reset releasing it after `releaseCycles` `posedge_event()`s of its own clock. The absolute 5 ns was period-coupled and already wrong for any non-1 ns period: at `period: 10` posedges fall at 3, 13, 23 ns, so a 5 ns release deasserted after a single edge; at `period: 20`, before any meaningful reset. It also landed in the same nanosecond as an edge; counting edges puts the release one delta after one. | LANDED, except that `active:` is still not consumed for polarity (§2.2) |
| `templates/systemc/module_hdl_wrapper.py:159` | `dut_hdl->clk(clk); dut_hdl->rst_n(rst_n);` | One bind per resolved clock and reset. | LANDED |
| `templates/systemVerilog/moduleInterfacesInstances.py:114` | `.clk (clk), .rst_n (rst_n)` on every child instance | Emit `.<clock> (<clock>)` for each clock in the **child's** resolved list, then the same for resets. The parent's set is a superset of every child's by the container-union rule (§3), so the identifiers always exist. | NOT DONE — needs per-child lists on `getBDInstances` |
| `templates/systemVerilog/moduleInterfacesInstances.py:134` | `.clk (clk)` on every memory instance | Emit the memory's resolved clock. | NOT DONE — needs the resolved clock on `getBDMemoryConnections` |
| `templates/systemVerilog/moduleRegs.py:776-777` | `input clk, rst_n` on `<block>_regs` | Emit the handler block's own resolved clocks and resets, one `input` per line, through `intf_gen_utils.sv_clock_reset_input_lines`. | LANDED — the handler is its own block, so no new view was needed (§6.6) |
| `templates/systemVerilog/moduleRegs.py:803-804` | `... & rst_n` in the select terms | Use the resolved reset name, inverted when `active: high`. | LANDED for the name; the inversion half is still §6.5 |
| `templates/systemVerilog/moduleRegs.py` (every flop call) | `` `DFFR ``/`` `DFFREN ``/`` `DFF ``/`` `DFFEN `` capturing a literal `clk` | The `_CLK` variant naming the handler's own clock, at all five flop-emitting sites. | LANDED (§6.6) |
| `templates/systemc/module_hdl_wrapper.py:172` (BFM bind) | every BFM bound to the single `clk`/`rst_n` | Each BFM bound to the clock of **its own connection**. This is the concrete reason D1 puts the clock on the connection. | LANDED for the clock, via the `domainClock` field of §4.2. The RESET stays the block's first, which §5.3 argues is the end state and not an interim. The **pair is still not a domain**, and now for a stated reason rather than an accidental one. |
| `templates/systemVerilog/apbDecodeModule.py` (every flop call) | `` `DFF ``/`` `SCFF `` capturing a literal `clk` in the generated router | The `_CLK` variant naming the router's own clock, at all three flop-emitting sites. | LANDED — the router is its own block, so no new view was needed, exactly as for `<block>_regs`. See §6.7 |
| `templates/systemVerilog/moduleInterfacesInstances.py` (generated region) | nothing | Default-domain alias lines per §6.3, in blocks whose default clock or reset is not named `clk`/`rst_n`. | NOT DONE — §6 |

**The gap the landed half leaves, stated plainly.** A block whose port list no
longer names `clk`/`rst_n` is instantiated by a parent that still binds
`.clk (clk), .rst_n (rst_n)` — so the RTL does not elaborate. No in-tree project
reaches it: it needs an authored connection `clock:` or block `clocks:`/`resets:`
naming a non-default domain, which no example does. Before this step such a
declaration was inert and produced RTL clocked by the wrong domain silently; it now
fails at elaboration instead, which is the better of the two failures but is not
the end state. Closing it is the remaining NOT DONE rows above.

**Measured, not inferred.** A throwaway fixture with a `clkSlow` register bus was
linted whole-design against both the pre-`_regs` generator and the current one.
Before: 7 Verilator errors, every one a `PINNOTFOUND`/`variable` on
`.clk`/`.rst_n` at a child instance in the container. After: 9, the two additions
being `PINNOTFOUND` on the handler instance inside its leaf — which previously
bound a matching pin against an *implicitly created* `clk` net, a floating clock
Verilator reported only as `IMPLICIT`. So the `<block>_regs` step converts one
silent wrong-domain bind into a hard error and does not otherwise move the gap.
Whole-design elaboration of a non-default-domain project therefore still needs the
child-instance binding row, and no in-flow lint of a non-default-domain
`<block>_regs` is possible until it lands.

**A second gap, in the derivation rather than the emission.** A reset's clock is
not required to be in the block's clock set. A leaf reached only by a `clkSlow`
connection derives clocks `[clkSlow]` and, with no `resets:` authored, the
project default reset — whose clock is `clk`. The wrapper then counts edges of a
`clk` that is not one of its members, and the generated C++ does not compile. The
design is wrong (a synchronous reset must be released on a clock the block has),
so the fix is a §7 rule rejecting it, not an emitter fallback. Not added here: it
is a new diagnostic whose wording and severity are a user decision, and the
failure today is loud.

### 5.1 Accepted churn — measured

An earlier revision of this section predicted the port-list emitter would move to
one declaration per line and rewrite every generated `.sv` port list. **That
spelling is superseded by §10 item 4** and this section is replaced by the
measurement.

**What §10 item 4 settled is the ORDER, not one spelling for every generator.**
Clocks before resets, each in canonical order, and one shared port namespace —
that rule is global and lives in exactly one place,
`intf_gen_utils.clock_reset_port_names` (`pysrc/intf_gen_utils.py:222`). The
*spelling* is each generator's own local style, and both are built on that one
function:

- the **block module** port list joins clocks and resets onto one `input` —
  `sv_clock_reset_input` (`:238`);
- the **verilated SV wrapper** port list declares one per line —
  `sv_clock_reset_input_lines` (`:241`).

**The style belongs to the GENERATOR, not to the kind of module it emits.** An
earlier revision of this list said "the RTL module port list has always joined",
which is false in tree: `templates/systemVerilog/moduleRegs.py:776-777` emits an
RTL module port list one clock/reset per line, live at
`examples/apbDecode/rtl/blockARegs.sv:17-18`. `<block>_regs` is a **third**
generator with its own spelling. It now consumes `sv_clock_reset_input_lines`,
the same helper the verilated SV wrapper uses, because that helper already
spells exactly this generator's pre-existing style — so the two share a spelling
without either adopting the other's. Neither helper is a rule about RTL modules
or about SystemVerilog; each is a rule about one generator's output.

Restyling either to match the other buys nothing and costs a tracked file per
wrapper, so neither is restyled. An intermediate revision did impose the joined
form on the wrapper and churned 28 files for no gain; that is reverted. Note the
choice is *not* the same as leaving the wrapper's literal `clk`/`rst_n` in place —
that would also have been byte-identical for single-clock projects but wrong for
multi-domain ones, which is the whole point of the change.

Both spellings are therefore byte-identical to baseline for a single-clock
project, and **the measured churn is 23 generated files, in one category**:

- **23 verilated SystemC wrapper files** (`*_hdl_sc_wrapper.h`): the reset driver
  is renamed `reset_driver_<reset>` (one thread per reset now exists, so the name
  has to carry which) and its body becomes the cycle loop. Behavioural and
  unavoidable.

No block module, no `_regs` module, no `apbDecode` router, and **no SV wrapper**
moved at all. Nothing else in any example moved, a second full regeneration
reproduces the state byte for byte, and no user-region content churned.

`unittest/test_clock_reset_emission.py` asserts the two styles with **disjoint**
patterns, so a case written for one cannot be satisfied by the other: adopting
the joined form in the wrapper, or the per-line form in the block module, is
killed in either direction. A regex admitting both would have stopped detecting
exactly the confusion this section exists to prevent, so neither pattern is
widened.

The two readers are now named for the generator each covers —
`_block_module_input_line` and `_sv_wrapper_input_lines` — because the earlier
names and messages framed them as rules about "RTL modules", and the joined
reader would consequently reject correct `_regs` output if pointed at it. Both
mutations were re-run after the rename and both still die.

**Churn of the §6 / `<block>_regs` step, measured after a `make clean` sweep of
every project: 9 files, two categories, no third.** The database target depends
only on project YAML, so the sweep is `make clean` + `make db` + `make gen` per
project; a measurement without it re-renders from a stale database and measures
nothing. The comparison is a content hash of the whole tree — **tracked and
untracked** — against the same sweep run with the two edited files restored to
their pre-change content, so the `examples/twoClk` and `examples/simple` trees,
which are untracked, are inside the measurement rather than assumed out of it.

- **2 source files**: `common/systemVerilog/flops.sv` and
  `templates/systemVerilog/moduleRegs.py`.
- **7 generated `<block>_regs` files**, the complete set in tree — `apbDecode`
  ×2, `mixed` ×3, `ip_test/ip` and `simple_ip/ip` — each on the macro rename
  alone. 4 to 21 changed lines per file, **every one inside a
  `GENERATED_CODE_BEGIN`/`END` region**, verified by comparing each hunk's line
  range against the file's marker ranges rather than by inspection.

Nothing else moved: no block module, no SV or SC wrapper, no `apbDecode` router,
no port list, no user region, and no file in any project without a register
handler. The port list and the reset term are byte-identical to baseline for
every in-tree project, because `sv_clock_reset_input_lines` reproduces the
literal the template used to hold and every project's default reset is `rst_n`.
A second full sweep reproduces the state byte for byte, and so does a third taken
after all the build-and-run gates.

**Churn of the `apbDecode` router step: 7 generated files, 69 lines, one
category.** The complete set of generated routers in tree —
`apbDecode/rtl/apbDecode.sv` (10 lines), `ip_test/top/rtl/apbDecode.sv` (11),
`ip_test/bridge/rtl/bridgeApbDecode.sv` (10), `ip_test/ip/rtl/ipStdDecode.sv` (9),
`mixed/rtl/apbDecode.sv` (11), `simple_ip/rtl/apbDecode.sv` (9),
`simple_ip/ip/rtl/ipStdDecode.sv` (9) — each on the macro rename alone, every hunk
inside a `GENERATED_CODE_BEGIN`/`END` region, verified by comparing each hunk's
new-file line range against the file's marker ranges. No source file but the
template moved, nothing was added or removed, and no hand-maintained file churned.

**The measurement was taken against a sweep with the template restored to its
pre-change content, and that turned out to be necessary rather than cautious.**
`make clean` at the repo root does **not** reach the nested sub-projects —
`ip_test/{common,ip,bridge}` and `simple_ip/{common,ip}` are absent from its
`clean` rule — so their `.gen/*.svgen` stamp files and databases survive it. A
template edit invalidates no stamp (nothing in the dependency graph names the
template), so a sweep after a root-only `make clean` reports `Nothing to be done
for 'gen'` in those five projects and silently under-reports the churn: the first
attempt here measured 3 files rather than 7, missing every router owned by a
nested IP. The sweep therefore cleans each project root explicitly. This is the
same class of hazard as §5.2's stale databases, one level further in.

### 5.2 Stale databases — the seven wrappers that were never regenerated

Seven checked-in `_hdl_sc_wrapper.h` files still carried `void reset_driver()` and
`wait(5, SC_NS)`, text the current template cannot emit, long after the §5 step
landed.

**Cause.** `$(A2C_SQLDB_FILE)` depends only on `$(A2C_PRJ_YAML)` and
`$(YAML_FILES)` (`include/make/a2c-common.mk:135-137`), not on
`config/schema.yaml`. A schema edit therefore does not rebuild any database, and
`make gen` regenerates from whatever the database holds; only `make clean` forces
it. **Eight** non-snapshot databases predate the `releaseCycles` column:
`hierInclude`, `inAndOut`, `ip_test/bridge`, `ip_test/common`, `ip_test/ip`,
`pySocket`, `simple_ip/common`, `simple_ip/ip`.

**The mapping is not one-to-one.** Five of the eight own the seven files —
`ipBridge` and `pySocket` own two each — and **three** own none at all, because
`hierInclude`, `ip_test/common` and `simple_ip/common` emit no SC wrapper. An
earlier count of seven databases mapped 1:1 onto the seven files is wrong on both
halves.

**Fixed by regeneration, not by editing generated text**: `make clean` + `make db`
+ `make gen` per affected project, including each composed child project's own
Makefile, which the parent's `gen` does not recurse into.

**Two changes deliberately NOT made, both the user's call:**

- **The makefile dependency graph is untouched.** Adding `config/schema.yaml` as a
  prerequisite of the database target would rebuild every project's database on
  any schema edit — a repo-wide build-behaviour change.
- **No staleness diagnostic is added.** Where one would have to live is now known,
  and it needs nothing new persisted: `projectCreate` resolves exactly one schema
  file (`pysrc/processYaml.py:3611`) and the database already records its own
  column set, which sqlite exposes through `pragma table_info`. A `projectOpen`
  check comparing the schema's declared fields per table against the opened
  database's actual columns would detect exactly this failure and no more. The
  coarser alternative — persisting a hash of the schema text next to `A2CROOT` /
  `PRJFILE` (`:3598-3604`) and comparing on open — invalidates every database on
  any schema edit, which is the same over-broad behaviour as the makefile change.
  Nothing schema-identifying is recorded today, which is why the staleness was
  silent.

### 5.3 The per-connection BFM binding, and why the reset does not follow it

The BFM's CLOCK is now the clock of the connection the BFM drives. The view
supplies it as `domainClock` on every port row (§4.2); the template reads that
field and nothing else, so no clock rule lives in a template.

**The reset is NOT made per-connection, and that is a conclusion.** Three facts
decide it:

- A connection carries no reset. D2 puts the reset on the BLOCK, explicitly or by
  project default, and D1's argument for putting the clock on the wire has no
  counterpart for the reset.
- A reset does declare an associated `clock:`, so "the reset of this port's
  domain" is a phrase one can write. It is not a function. A block's reset set may
  hold **no** reset in a given port's domain — the ordinary case, a single-reset
  block reached from two domains, which is exactly the `cons` fixture — or more
  than one, and neither has a defensible tie-break.
- Emitting the block's first reset always names a member of the wrapper, so it
  compiles; a derived per-connection reset would not always exist.

The consequence is recorded rather than hidden: a BFM can be bound a clock and a
reset from different domains. That is the same crossing the plan already declines
to report (D3), and the wrapper is testbench scaffolding whose reset is released
once and never reasserted, so the pairing has no dynamic consequence in the only
mode that exists today. If per-domain reset release ever matters, the missing
input is a rule for the zero-reset and multi-reset cases, not a view field.

**Churn is zero, and the premise that it would not be was wrong.** Every block in
every shipped example resolves to exactly one clock and one reset, and no port's
connection clock differs from its block's first clock — checked across all 23
in-tree databases through `getBlockData`, not inferred. So the per-connection
clock and the primary clock coincide everywhere in tree and all 782 generated
files are byte-identical to baseline. The behaviour is therefore exercised only by
the `unittest/` fixtures, which is why the multi-domain `cons` case asserts on
emitted text and the composed case asserts on the view.

---

## 6. Flop macros, reset semantics, and user RTL authoring

`common/systemVerilog/flops.sv` is where the change reaches hand-written code,
because the macros reference the identifiers `clk` and `rstN` textually rather
than taking them as arguments (`flops.sv:10`, `14-95`).

### 6.1 What the ground truth turned out to be

Three findings reshape this section. All were established by inspection.

- **The ASIC branch has never been compiled.** The token `ASIC` appears in no
  makefile, no `.f` file, and no Python; the only preprocessor symbol pushed to a
  tool command line is `VL_DUT` (`include/make/a2c-vl-wrap.mk:19`). Every flow —
  Verilator lint, Verilator co-simulation, and the external VCS flow — compiles
  the **FPGA** branch (`flops.sv:50-96`), which contains no reset logic at all.
  That is why the `rstN`/`rst_n` defect has survived since the initial commit.
  It also means **reset is currently unverified in co-simulation**: the RTL
  power-up state comes from `initial` statements the model does not represent, so
  tandem cannot detect a reset bug.
- **Three reset semantics already coexist.** The ASIC branch is synchronous
  active-low; the FPGA branch has none; and eleven hand-written sites bypass the
  macros entirely with **asynchronous** reset —
  `examples/mixed/rtl/blockA.sv:39,48,63,72`, `blockD.sv:34,48`,
  `axi4sDemo.sv:82`, `hierVlDemo.sv:82`, `hierInclude/.../blockCX.sv:50,72`, and
  `pro/examples/lmmiDemo/rtl/lmmiDemo.sv:95`.
- **The generator is itself a major call site.** Of 248 macro calls across 39
  files, most of the 186 in `examples` sit inside generated regions emitted by
  `templates/systemVerilog/moduleRegs.py` and `apbDecodeModule.py`. Those change
  at zero migration cost. The compatibility obligation is owed to out-of-tree
  customer RTL, not to this repository.

### 6.2 The problem the earlier draft missed

§2.2 makes the declared reset name the emitted port name verbatim, and §2.1 does
the same for clocks. The bare `` `DFF `` macro references a literal `clk`. So the
first project that names its clock `coreClk` breaks **all of its own
hand-written RTL**, because the macro expands to an identifier that is not a
port. The previous "keep every existing macro exactly as is" treatment does not
survive that, and D6 would hold only for projects that declare nothing.

### 6.3 Selected treatment

Three pieces, each independently valuable:

- **A generated default-domain alias.** In the generated region of any block
  whose resolved default clock or reset is not literally named `clk`/`rst_n`,
  emit two lines:

  ```systemverilog
  wire clk   = coreClk;
  wire rst_n = coreRst_n;      // inverted for a reset declared active: high
  ```

  `templates/systemVerilog/moduleInterfacesInstances.py` already owns a generated
  region in every block module, including hand-written leaf blocks, so this has a
  natural home. This is what makes all 248 existing call sites and all
  out-of-tree RTL correct regardless of clock naming, and it normalises reset
  polarity in exactly one place so nothing downstream reasons about `active:`.
- **An explicit-argument macro family**, with the existing macros redefined as
  wrappers so no call site changes. **LANDED, clock only — see §6.6 for the
  spelling actually taken and why the reset half is not in it.** The generator
  uses the explicit form unconditionally at its own `<block>_regs` emission
  sites.
- **A CDC primitive library** — `cdcSync2`, `cdcPulse`, `cdcHandshake`,
  `cdcAsyncFifo` — in `common/systemVerilog`. Without it, making the user
  responsible for crossings (D3) means they hand-roll a raw `always_ff`, which is
  demonstrably what already happens (§6.1).

### 6.4 Reset style becomes a flow property

Replace the single `ASIC` switch with a three-way selector branched at the top
level of `flops.sv`: `A2C_RESET_NONE` (today's FPGA behaviour),
`A2C_RESET_SYNC` (today's intended ASIC behaviour), `A2C_RESET_ASYNC`. Do **not**
put `` `ifdef `` inside a `` `define `` body; branch at top level as the file
already does at `:6`/`:50`.

The asynchronous branch cannot take a normalised expression in its sensitivity
list, since synthesis rejects expressions in edge sensitivity. That is the second
reason for the alias: normalise polarity once in generated RTL so the macro's
sensitivity list is always `negedge rst_n` on a real net.

The FPGA and ASIC branches are orthogonal axes, not alternatives — reset style,
and whether to emit `initial` for bitstream power-up — and they compose legally
in one `always_ff`. **Co-simulation should compile with a real reset style
enabled**, so that tandem exercises the reset path at all. Today it does not.

### 6.5 `active: high` must not ship without the alias

On the FPGA branch an active-high reset is silently dead; on the ASIC branch
`` `define RST ~rstN `` would invert it, holding the design permanently in reset.
Two BFMs also hardcode `while(!rst_n)` (`interfaces/apb/apb_bfm.h:91`,
`interfaces/memory/memory_bfm.h:82`) and would hang. Accepting the attribute and
documenting that it does nothing is worse than rejecting it, so `active: high` is
rejected unless the §6.3 alias lands in the same change.

The `rstN` → `rst_n` defect at `flops.sv:10` is **still open.** An earlier
revision of this line said it "is fixed as part of this work"; it was not, and it
was deliberately left alone by the §6.6 step as out of scope. `` `RST `` still
defaults to `~rstN` while every emitter spells `rst_n`, so the ASIC branch would
not compile against generated RTL. It is dead code — `ASIC` is defined nowhere in
the tree (§6.1) — so nothing observes it, which is why it can wait for §6.4 to
replace the switch entirely.

### 6.6 What the clock-parameterized family landed as

Decision 1's proposal was `DFFRC(c, r, q, d, rval)` with an active-high "in reset"
expression. **The reset is not parameterized** — the user scoped this step to the
clock — so the landed spelling is the family name plus `_CLK`, with the clock
prepended to the existing argument list and nothing else moved:

```systemverilog
`define DFFR_CLK(clkSig, q, d, rval)   // the body, once
`define DFFR(q, d, rval)  `DFFR_CLK(clk, q, d, rval)
```

All six families and all four `*_INST` wrappers have one. Three properties are
load-bearing and each is pinned by a mutation in
`unittest/test_clock_reset_emission.py`:

- **One body per family per branch.** The `_CLK` variant holds the body; the bare
  macro is a single line. Two bodies for one family is the failure this shape
  exists to prevent, and it is checked twice — by comparing each alias's text
  against `` `<FAMILY>_CLK(clk, <its own args>) `` argument for argument, and by
  counting `always_ff` bodies against the number of `_CLK` macros.
- **The aliases live OUTSIDE the `ifdef ASIC` / `else` branches**, once each,
  because both branches declare the same `_CLK` signatures. A per-branch alias
  cannot then drift, and the suite rejects any non-`_CLK` macro defined inside a
  branch.
- **Expansion is byte-identical.** Verified rather than argued: `verilator -E` on a
  module calling all ten bare macros produces a module body identical to the
  pre-change file's, in **both** branches (`+define+ASIC` and without). Only blank
  lines differ, from the added `define` lines themselves. That is what the
  compatibility obligation to out-of-tree customer RTL (§6.1) rests on.

**The ASIC branch still cannot express two resets**, and that is a consequence of
scoping this to the clock rather than an oversight: its reset comes from the
overridable `` `RST ``, which is per compilation unit, not per call site. A design
needing two synchronous reset domains needs §6.4's selector or a reset argument,
neither of which is here. The FPGA branch has no reset at all, so the question does
not arise there.

**`<block>_regs` sources its domain from its own block row, not from its owner.**
This is the part of the step whose rule had to be established rather than chosen.
`<leaf>Regs` is a real row in `blocks`, synthesised with `hasRtl: True` by
`config/postParseRegisterPorts.py:78`; the generated file carries
`GENERATED_CODE_PARAM --block=<leaf>Regs`; and `systemVerilogGenerator` calls
`prj.getBlockData` on it, which runs `getBDClocksResets`. So `data['clocks']` and
`data['resets']` in `moduleRegs.py` are already the handler's own persisted sets,
and no view helper was added.

That is not the same set as the served leaf's, and the difference is observable:
in the emission fixture `leafA` derives `[clk, clkSlow]` — the bus domain of its
generated decode plus the default domain of the block reaching its register —
while `leafA_regs` derives `[clkSlow]` alone. Reading the owner's set would
declare a port the handler never clocks anything with and could pick the wrong one
for the flops. A generated decode tree inherits exactly one bus domain by
construction (§10.9 Option A), which is what makes the first entry of each set
unambiguous; the index choice is unobservable and deliberately not mutation-tested,
since there is never a second entry to pick.

The reset the handler emits is always its project's **default** reset, because a
synthesised block declares no `resets:` and the derivation's `otherwise` branch
supplies the default (§3). Its polarity is still unhandled — §6.5 owns that.

### 6.7 The `apbDecode` router, and the invariant `clocks[0]` rests on

`templates/systemVerilog/apbDecodeModule.py` was the last emitter of a bare flop
macro. It now reads `data['clocks'][0]['clock']` once and passes it to all three
of its flop-emitting sites: the parent request-capture template (four `` `DFF ``
plus the `trans_active` `` `SCFF ``), the per-child select template (one
`` `SCFF `` per routed instance), and the parent response path appended in Python
(three `` `DFF ``). The router is its own block row, so `getBlockData` already
carries its own derived sets and **no view helper was needed** — the same finding
§6.6 recorded for the handler. Two spellings were normalised in passing: four
calls were written `` `DFF (q, d) `` with a space before the paren, and all nine
are now spelled uniformly.

**Why this one had to be closed.** The router's port list has come from
`sv_gen_ports` — the derived set — since the §5 step, so a non-default-domain
router already declared e.g. `clkSlow` and nothing else, while the bare macro
expanded to `posedge clk`. That is a **hard** failure, measured: Verilator
reports `%Error: Can't find definition of variable: 'clk'` and exits 1, with zero
`IMPLICIT` diagnostics. An undefined identifier in an event control is an error,
not an implicit net — implicit-net creation applies to PORT CONNECTIONS, which is
the separate case §5 describes, and there it is a warning (`%Warning-IMPLICIT:
Signal definition not found, creating implicitly`).

So the pre-fix router was not silently wrong-domain hardware; it was
unbuildable. That is what made this row worth closing on its own rather than
leaving to the emitter sweep: no shipped example puts its register bus off the
default clock, so nothing in the tree hit the error, and the first project to
author a non-default-domain register bus would have found its generated router
impossible to elaborate. Only two of the seven generated routers are reached by a
shipped lint target either (see the gate notes below), so the tree could not have
found this for a user.

**The invariant, investigated rather than assumed.** `moduleRegs.py` and now
`apbDecodeModule.py` both read the FIRST entry of the derived clock set. The
question is whether authored YAML can make that entry something other than the
register-bus domain. It was answered by building fixtures, not by reading code.

- **The handler is safe BY CONSTRUCTION, and this is now proved.** Exactly one
  connection-shaped row can ever touch a `<block>_regs` block — the boundary
  `connectionMap` this pass synthesises — and that row carries the feed clock.
  Nothing else can contribute: the handler block is synthesised without a
  `clocks:` list (`config/postParseRegisterPorts.py:81`), it contains no
  instances so the container union adds nothing, and an authored row **cannot**
  name the handler instance, because the instance does not exist when the
  authoring file is parsed — the attempt fails with `no instances row named
  'u_leafA_regs' was found in any context processed before this one`. So the set
  has exactly one entry and the index is unobservable. This is enforcement by
  construction, not by the absence of a fixture.
- **The suspected validation gap is not a gap.** `_validateSingleDomainObjects`
  (`pysrc/processYaml.py:5526`) does not fold the register-bus feed clock in with
  the register-connection clocks, and it **must not**: a bus feed on `apbClk`
  while the logic reaching the leaf's register is on `clk` is the supported and
  intended arrangement — the crossing sits on the leaf's `reg_rw`/`reg_ro` wires
  (§10.9), which is what `test_register_decode_clock.py`'s object-access case and
  the `<block>_regs` emission fixture both already assert. Measured: feed
  `clkSlow` with register connections resolving to `clk` builds exit 0, `leafA`
  derives `[clk, clkSlow]`, `leafA_regs` derives `[clkSlow]`. Folding the feed in
  would reject that design. Two register connections that disagree with **each
  other** are still correctly rejected by the existing rule.
- **The router is NOT safe, and it is constructible with ordinary authored
  YAML.** A block `clocks:` entry is *additive* (§2.4), and a router block is
  author-written, so it can carry one. The router's derived set is then wider than
  the bus and `clocks[0]` picks whichever clock the canonical order puts first.
  Four measured configurations, feed on `clkSlow` throughout:

  | authored on the router block | derived set | router flops | handler flops |
  | :--- | :--- | :--- | :--- |
  | nothing | `[clkSlow]` | `clkSlow` | `clkSlow` |
  | `clocks: [clk]` | `[clk, clkSlow]` | **`clk`** | `clkSlow` |
  | `clocks: [clkPico]`, declared *before* `clkSlow` | `[clkPico, clkSlow]` | **`clkPico`** | `clkSlow` |
  | `clocks: [clkPico]`, declared *after* `clkSlow` | `[clkSlow, clkPico]` | `clkSlow` | `clkSlow` |

  As measured when this step landed, each of the two failing rows built **exit 0
  with no diagnostic**, and the emitted router declared the wrong clock as a real
  port, so it elaborated cleanly — a clock crossing on the APB handshake between a
  router and its own handler. Note what this is and is not: the failure is order-dependent, not
  universal, and it is **not a regression** — before this step the bare macro
  captured `clk` unconditionally, so the `clocks: [clk]` row behaved identically
  and every other row was worse. The step strictly narrows the exposure without
  closing it.

  At the time this step landed the exposure was **known and unfixed**: the
  two-entry set is constructible with ordinary authored YAML, so nothing stopped
  a project reaching the wrong-domain rows, and no fixture built that shape
  either.

  **Now closed by validation (§7).** A router block whose derived clock set holds
  more than one entry is an **error**:
  `projectCreate._validateSingleDomainObjects` reports
  `Register-decode router block '<name>' resolves to more than one clock (...)`
  and directs the author to remove the `clocks:` entry, and the build exits 1.
  Every row of the table above except the first is now rejected — including the
  last one, whose emitted clock happened to be right, because the rule is on the
  CARDINALITY of the set and a router declaring a clock port nothing clocks is
  not a supported design either. `unittest/test_clock_reset_emission.py` covers
  the rejection end to end (built fixture, non-zero exit, message asserted) and
  `unittest/test_clock_domains.py` covers the rule directly on synthetic rows,
  each in both orderings.

  **Ordering note.** The rule's reachability set — the same
  `reachableInstanceKeys()` the register-decode pass calls, which is what scopes
  the rule to the routers a build actually routes — is now computed only after a
  multi-clock router has been found, instead of before the search. That walk reads
  `self.hierKey`, which `postYamlExternalScript()` populates and only when the
  merged project config carries `postProcess:`. This is ordering, not a guard:
  behaviour is identical for every design, so the ungating mutation is an
  equivalent mutant. It was proposed on the premise that a user project could
  remove `postProcess:` and turn every build into an `AttributeError`; that
  premise does not hold. `merge_with_spec` cannot delete a key, and
  `postProcess: []` or `postProcess:` (null) both leave the key present, so the
  `if` fires and `hierKey` is populated. Reaching the unpopulated state needs an
  edit to base `config/project.yaml` itself. The reordering is kept anyway,
  because a project-wide hierarchy walk on every build to serve a rule almost no
  build triggers is the wrong shape regardless.

  The consequence for the index read is that `clocks[0]` and `clocks[-1]` are now
  **provably the same read**: no set reaching the emitter has more than one entry.
  So the `[0]` → `[-1]` mutation is not killed and still cannot be, but it is now
  an *equivalent* mutant rather than an uncovered exposure — the same category as
  the two `moduleRegs.py` index survivors. What kills the DEFECT is the
  validation, and the validation is covered.

**Coverage and mutation results.** `unittest/test_clock_reset_emission.py`'s
`<block>_regs` fixture now also generates the router of the same decode tree, so
one build covers both generators and a third case compares their answers — the
router and its handler must name the same one clock, which is the invariant a
decode tree exists to have. The non-default-domain build is real rather than a
shape that collapses to `clk`: the router's port list reads
`input clkSlow, rstMain_n` and names no `clk` at all, so a bare macro fails there
on both the macro name and the clock. The flop families the emitter uses are
checked against the set `flops.sv` actually defines, discovered from the file, so
neither a renamed family nor an invented one passes.

**Nine of ten mutations die; the tenth is the index and is named as a survivor.**
Killed: hardcoding the clock to `clk`; sourcing it from `data['resets'][0]`
instead; reverting each of the three flop sites to its bare macro (three separate
mutations, each killed by the site-specific pattern as well as by the generic
check); clocking the per-child select from a literal `clk` rather than the
router's; withholding the clock from the child template so it renders empty; and
emitting a `DFFX_CLK` family the library does not define. **Survivor: `[0]` →
`[-1]`.** It is not killed and cannot be: with the §7 router rule landed, every
set reaching the emitter has exactly one entry, so the two reads are equivalent
by construction rather than merely uncovered. It is left standing and named
instead of being chased with a fixture, because no legal input distinguishes it.

---

## 7. Validation rules

Every rule below is landed except where marked.

- **Exactly one** clock and exactly one reset carries `default: true`, per
  project, per section. One whole-section check,
  `projectCreate._validateProjectScopeDefaults` (`pysrc/processYaml.py:8206`),
  reports zero and more-than-one as the two failure modes of the one rule. It is
  driven from the project-scope pre-pass, the only place that knows which sections
  a given project contributes, once per project per section and immediately after
  that section is parsed. Neither half can be a row hook: a row cannot see that no
  *other* row claimed the default, and the count is only final once the section is
  fully parsed. An earlier implementation split the rule, enforcing at-most-one in
  hand-written `_post_validateClocks` / `_post_validateResets` row hooks while the
  whole-section check enforced at-least-one; that made the rule only half generic,
  since a new project-scoped section carrying a `default:` field inherited the
  diagnostic promising "exactly one" but not the second half of the enforcement.
  Both halves now live in the one schema-driven check, which fires for any
  project-scoped section carrying a `default:` field rather than being named after
  `clocks:`/`resets:`, so the schema stays the single source of truth. The row
  hooks are removed.
- Zero is permitted only when the section itself is absent, in which case §2.5
  injects the implicit default — which, being injected, is itself a contributed
  section and is checked like any other.
- A `clocks:` section that is present but declares nothing (`clocks: {}`) is
  rejected by the same rule: it is a declared section with no default.
- No diagnostic asserts that the author wrote a particular value. `default:` is
  `optional(false)` and unvalidated, and YAML 1.2 parses `no` and `off` as truthy
  strings, so the earlier "entry 'x' declares `default: true`" wording was false
  for a file authoring `default: no`. The second-default message now reports the
  entry as *taken as* the default. (The unvalidated boolean is repo-wide, across
  18 `optional(false)` fields, and is out of scope here.)
- **`clocks.period` and `resets.releaseCycles` must each be a positive integer,
  and are coerced to `int` at parse time.** LANDED as
  `projectCreate._resolvePositiveCount`, one rule reached from each section's
  `post()` row hook — `resolveClockPeriod` on `clocks:`, and
  `resolveReset` on `resets:`, which carries this rule as well because a
  section has exactly one hook, looked up by section name. The diagnostic names
  the project file and line, the project, the section, the entry and the value.
  Both halves are load-bearing: the range because `0` and `-1` emitted
  `for (int cycle = 0; cycle < 0; cycle++)`, releasing the reset at t=0 with no
  diagnostic at all, and the coercion because the `optional(N)` default was a
  string while an authored value was an int (§2.2). This is deliberately scoped to
  these two fields; the repo-wide `optional(false)` boolean family below is
  untouched.
- The one surviving row hook on these sections is
  `post(resolveReset)` (§2.2), which resolves rather than validates, plus the
  positive-count rule above. Row
  hooks live on `projectCreate` as `_post_<name>` in `pysrc/processYaml.py` —
  **not** in `config/postParseChecks.py`, which hosts whole-project scripts
  invoked by `postYamlExternalScript()`. `schema.py::_function_find` resolves
  `post(X)` only as `projectCreate._post_X`.
- Every `clock:` reference on a connection, a block, or a reset must resolve to a
  declared clock. Every block `resets:` entry must resolve to a declared reset.
  These are ordinary `_validate` section references and are free. LANDED with
  §2.3/§2.4; each of the three reference sites is mutation-checked.
- A clock name and a reset name may not collide, since both land in the same
  module port namespace. LANDED as `_validateClockResetNames`
  (`pysrc/processYaml.py:8243`), driven from the project-scope pre-pass once both
  sections of a bucket are parsed and only for a project that contributes both —
  either may be authored or injected, and a custom `dbSchema` need not declare
  them at all.
- A memory whose connections resolve to more than one clock is an error in
  phase 1, and a `dualPort` memory whose two ports resolve to different clocks
  gets a message naming dual-clock memory as unsupported — that is the first
  thing a user will try, and the generic message would not explain why. The
  single-port-clock case (a memory living wholly in a non-default domain) is
  supported and is just the emission change in §5. LANDED in
  `_validateSingleDomainObjects` (`pysrc/processYaml.py:5514`), reading the
  resolved clock so an unstated `clock:` cannot hide a disagreement.

  The reason is stronger than "the primitive has one `clk`".
  `common/systemVerilog/memory_dp.sv:26-32,44-50` writes the shared array from
  **two separate `always @(posedge clk)` blocks**, which is already a race on
  same-address access and is invisible only because Verilator is never passed
  `-Wall`, so `MULTIDRIVEN` is never reported. A second independent clock turns
  a same-address race into a race at every coincident edge, which two simulators
  need not resolve identically. Decisively, **tandem cannot verify a dual-clock
  memory, because the reference model has no clock domains at all.** Dual-clock
  memory is phase 2 (§8) and needs a per-**port** clock in the schema, not the
  per-memory granularity the current `getBDMemoryConnections` view resolves.
- A block whose register-bus connections resolve to more than one clock is an
  error, since `<block>_regs` is a single-domain module. LANDED in the same check.
  It is reachable only from an authored `registerConnections` `clock:`, and no
  change to register-port synthesis can widen that: the check iterates
  `self.flatData['registerConnections']` (`pysrc/processYaml.py:5541`) and
  synthesis writes no row into that section — `postParseRegisterPorts` emits only
  `('blocks', 'instances', 'connections', 'connectionMaps')`
  (`config/postParseRegisterPorts.py:763`). An earlier revision claimed the rule
  would "stop being vacuous for routers" once §10 item 9 landed; that was false
  and is struck. For generated routers the rule does not apply at all, rather than
  applying trivially. The rule and its message are correct for the authored case
  they do cover — `examples/mixed` is the one example with authored rows
  (7 `registerConnections`, 2 `memoryConnections`).
- **A block carrying `addressBlock:` whose derived clock set holds more than one
  clock must be an error. NOT DONE — this is the one rule §6.7's investigation
  opens.** The generated router is a single-domain module and its emitter reads
  the first entry of that set, so a second entry silently decides the domain of
  every flop in the dispatch path. The reachable authoring is an additive block
  `clocks:` entry on the router block (§2.4); §6.7 measures two spellings of it
  that build exit 0 and clock the router off its own bus.

  **Where it belongs: folded into `_validateSingleDomainObjects`**
  (`pysrc/processYaml.py:5526`), which already owns "one module in one domain must
  have connections that agree" for memories and register buses, and which
  `projectCreate` calls immediately after `deriveBlockClocksResets`
  (`pysrc/processYaml.py:5391`, called at `:3712`) — so the derived set is in hand
  at exactly that point. The only plumbing needed is for the derivation to hand
  its `blockClocks` map to the check instead of only persisting it, or for the
  check to read the `blockClocksResets` table it just wrote.

  Two scoping notes. The rule is **load-bearing for routers and vacuous for
  handlers**: `isRegHandler` blocks cannot reach two clocks at all (§6.7), so
  including them buys a cheap assert rather than a diagnostic — worth doing only
  if the message distinguishes the two cases. And the message must not simply say
  "put both in one domain", because the fix is to **remove** the `clocks:` entry,
  not to move the bus: the router's domain is not the author's to choose, it is
  the feed's.

  Deliberately **not** implemented in the step that found it: it is a new
  user-facing diagnostic whose wording and severity are the user's call, and the
  emission change stands on its own without it.
- **Cross-project name reuse is legal and must not be validated against.** Two
  composed projects declaring a clock of the same name, with different `period`,
  `timeUnit`, or `active`, are two distinct declarations in two distinct
  buckets, and each resolves within its own project. An earlier draft of this
  plan called the divergence an error, on the superseded assumption that the
  names denoted one shared global net. Under project scope that is wrong, and
  rejecting it would break the composition case that
  [`plan-project-scope.md`](./plan-project-scope.md) §8 uses as its acceptance
  gate. Note the asymmetry this creates in phase 1: the two declarations stay
  distinct **rows**, but with boundary binding deferred they become the same
  physical **net**, because §2.0.2 wires the boundary by name match. Validation
  must therefore not reject the divergence, and nothing else announces it either —
  the report that once did is removed (§10.5). Phase 3 replaces the name match
  with an explicit binding and the asymmetry disappears.
- All single-default, reference, and collision rules above are **per project**.
  They are evaluated within one project's bucket and never across buckets.

---

## 8. Phasing

### Phase 0 — project scope, landed first and standalone

**Owned by [`plan-project-scope.md`](./plan-project-scope.md).** The
`scope: project` mechanism of §2.0.3 lands as its own change, ahead of and
independent of any clock work. It is a general schema-and-parser capability the
toolchain currently lacks, it has consumers beyond clocks, and it is separately
testable. Landing it first keeps the clock feature to design content only.

This plan depends on Phase 0 for: the `projectScope` attribute and the project
file as the declaration site (§2.1, §2.2), `scope: project` on the four reference
sites (§2.3, §2.4), and the pre-pass that parses project-scoped sections into the
`projectName`-keyed bucket, which §2.5's built-in default also uses.

One item flowed the other way: default injection (§2.5) needs the pre-pass to
create a bucket for a project that declared nothing, which Phase 0's
declare-to-get-a-bucket condition excluded
([`plan-project-scope.md`](./plan-project-scope.md) §9.2). An injected section is
now itself a reason to create a bucket, so every project owns one.

**Phase 0 lands the §2.1 and §2.2 sections and the multi-clock example**, with no
derivation and no emission. The two plans share one fixture: the sections give
project scope real schema content to exercise, and Phase 1 then starts from an
example that already exists.

**Status.** Phase 0 landed the sections and the example; both items above are now
closed:

- **§2.5 default injection is landed.** Every project owns a default clock and
  reset, whether declared or injected, which is what §2.0.2, §3, §5 and the
  no-churn argument of §8 rest on. Generated output stayed byte-identical, as
  expected while nothing consumes the two tables.
- **`examples/twoClk` declares both sections** — in the assembling project
  (`prj/yaml/project.yaml`) and in the vendored child IP
  (`ip/prj/yaml/twoClkIpProject.yaml`), each declaring a clock named `clk` and a
  reset named `rst_n` with different attributes. It is reachable as `make
  two-clk` and from `make pipeline-test`, and its model and `VL_DUT=1` builds
  both run to `No error`. An earlier revision of this section said no example
  declared these sections; that is out of date.

§2.3, §2.4, §3, the §4.2 view, and the §7 rules that derivation makes reachable
are now landed too, with zero generated-file churn across every example and
`make two-clk` passing including its `VL_DUT=1` build. §10 item 9 is landed. The
§5 port declarations and the cycle-based reset release are landed on top of that,
with the churn §5.1 measures and the unit suite green at 98 suites. The §6
clock-parameterized macros and the `<block>_regs` rows are landed on top of that,
settling open decision 1. The `apbDecode` router's flops are landed on top of that
(§6.7), so no generator emits a bare flop macro any more. The per-connection BFM
clock binding is landed on top of that (§5.3), which is the first §5 row to
consume a per-**port** view field, again with zero churn. Phase 1 continues at
the two remaining §5 binding rows that need a further `projectOpen` view (§4.2 —
the child instance and the memory instance), §6.3's default-domain alias, and
§7's single-domain rule for a router block.

Phase 0's **eight confirmed defects** ([`plan-project-scope.md`](./plan-project-scope.md)
§12) are closed after three remediation rounds; §13 of that plan records the
residual pre-existing items. The two that sat directly in Phase 1's path are both
resolved: the pre-pass now orders project-scoped sections by **schema**
declaration order rather than the author's key order (verified by mutation — the
authored-order form reproduces the original "value clk is not declared" failure);
and the single-default rule now rejects zero and more-than-one alike (§7), so
`defaultClock(project)` and `defaultReset(project)` are total for **every**
project once §2.5 injection supplies the sections a project does not declare.

### Phase 1 — declared domains, primary inputs

Everything in §2 through §7. Every clock and reset is a primary input at the
design top and is threaded down to the minimal set of blocks that need it.
Suppliers, crossing analysis, and dual-clock memory are excluded.

Every clock and reset resolves **within its declaring project only**, per the
settled decision in §10.7. A composed IP runs on the clock its own project
declares, and an assembler cannot re-clock it. This is what makes phase 1
backwards compatible without a special case: each project receives a built-in
default clock and reset of its own (§2.5), so `ip_test` and `simple_ip` compose
exactly as they do today.

### Phase 2 — candidates, not committed

- `suppliesClocks:` / `suppliesResets:` on blocks (D5). The open problem is
  routing a supplied net from the supplier instance up to the common ancestor of
  its consumers and back down, and preventing the supplied clock from also
  appearing as an input on that ancestor's port list. A validation that a clock
  has at most one supplier project-wide is required at the same time.
- Dual-clock memory primitives and a per-**port** clock, which additionally
  requires rewriting `memory_dp.sv` away from its two-always-block form, a
  defined cross-domain read-during-write policy, and a model-side reference that
  does not exist today (§7).
- A generated SDC skeleton — one `create_clock` per declared clock from
  `period`/`timeUnit`, plus `set_clock_groups -asynchronous` between them — which
  is roughly twenty lines of template and makes commercial CDC tooling usable
  without hand-maintained constraints.
- Hoisting clocks and resets into one project-level generator module bound into
  every wrapper. Each wrapper constructs its **own** `sc_clock`
  (`sec_clock_ctor_init`, `templates/systemc/module_hdl_wrapper.py:120`), so N
  clocks across M wrappers is N×M objects phase-aligned only because their
  constructor arguments are byte-identical. Phase 1 keeps that: every wrapper's
  parameters now come from the same row, so the alignment is a load-bearing
  invariant rather than a structural guarantee. The same applies to the release
  count, which is now per reset rather than per wrapper — so two wrappers agree,
  but only because both read the one `resets:` row.
- Exposing duty cycle, start delay, and first edge on `clocks:`.
- A `project.yaml` per-assembler override of `period:` / `timeUnit:`, if running
  a composed IP at a different simulated speed becomes a requirement (§2.0).

---

## 9. Test plan

- **Shared example.** The multi-clock example under `examples/` is created in
  Phase 0 (see [`plan-project-scope.md`](./plan-project-scope.md) §8) and is
  extended, not replaced, here. It carries two clocks, two resets, a block in
  each domain, and one block holding ports in both domains, so that the
  multi-domain port list and the domain-explicit flop macros are both exercised.
  It is a **composed** fixture — a child IP project plus an assembling project —
  because Phase 0's acceptance gate requires that, and so that per-project
  resolution is demonstrated: the IP and the assembler each declare a clock named
  `clk` with a different `period`, and each side's flops must resolve to its own.
  With boundary binding deferred (§10.7), that is the composition case phase 1
  must prove. It should carry a co-simulation
  wrapper so the two `sc_clock` members and the two reset release sequences are
  exercised, and a regression entry.

  The two periods must be **non-commensurate** — for example 1 ns and 3 ns with a
  phase offset, not the 1 ns and 2 ns §2.1 illustrates. With commensurate periods
  every slow edge coincides with a fast edge, which is the single best way to
  hide a crossing bug in a simulator that models no metastability. This costs one
  line in the example YAML.
- **Backward-compatibility check.** Regenerate every existing example with no
  YAML change and confirm the only diff is the one §5.1 accounts for. This is the
  primary guard on D6, and it held for the landed half: 23 generated files, one
  explained category, no port list and no user region touched.
  **The fixture needed no extension for derivation.** It already carries a
  connection across the composition boundary between two projects whose same-named
  `clk` differ in `period`, which is the one shape where the two ends resolve to
  different rows (§3). Extending it with a block that genuinely lives in `clkSlow`
  is still deferred, and now for a sharper reason than "the declaration is inert":
  it is no longer inert, and a `clkSlow` block in `twoClk` would make the
  container's still-literal `.clk (clk)` binding fail to elaborate (§5). It lands
  with the child-instance binding row and the §6.3 alias.
- **Emission unit tests** in `unittest/test_clock_reset_emission.py`, 23 cases,
  wired into `run_all_tests.sh` as its own suite. It builds one fixture whose
  three generated leaves cover the shapes no example has — a leaf wholly in a
  non-default domain, a leaf in three domains (including one declared in `ps`)
  carrying two resets with different release counts, and a leaf reached from two
  domains — then runs `--newmodule` and renders the files, asserting the emitted
  text. The three-domain leaf is what separates "the reset's own clock" from "the
  block's primary clock" and "the reset's own count" from "one shared count";
  nothing else in the tree does. Two further cases are library-content checks:
  that every `timeUnit` the schema admits has an `SC_TIME_UNIT` spelling, and
  that the `releaseCycles` default is the behaviour-preserving 3. The block module
  and the verilated SV wrapper are asserted with **disjoint** patterns, one per
  generator, so a generator adopting the other's spelling is killed in
  either direction; a pattern admitting both would pass for exactly the confusion
  the cases exist to catch. Each reader is named for the generator it covers, so
  neither can be pointed at `<block>_regs`, whose per-line RTL module port list
  the joined reader would wrongly reject (§5.1). The non-default-domain leaf is parameterizable with
  one variant, so the variant trampoline is a covered emission site rather than an
  inferred one — a mutation restoring its literal `clk`/`rst_n` is byte-identical
  on every in-tree example and would otherwise be caught by nothing. Twenty-one
  mutations, all killed.

  **The §6 step extended this suite rather than adding one**, so the suite count is
  unchanged at 98 and nothing was removed. Six cases were added:

  - **Two library-content checks on `flops.sv`**, which **discover** the families
    from the file rather than listing them, so a family added to the library is
    covered without editing the suite. They pin the `_CLK`-in-both-branches rule,
    the argument-list agreement between the branches, the clock-first argument, the
    bijection between bare macros and `_CLK` variants in **both** directions, the
    exact alias text argument for argument, and the `always_ff` body count.
  - **A second fixture with a register-decode tree, built twice** — bus feed on
    `clkSlow`, and no feed clock at all. Those are the non-default-domain and
    default-domain shapes of one generator, and the default-domain build is what
    makes the uniformity claim testable: it is the only case that dies when the
    emitter falls back to the bare macro whenever the clock happens to be named
    `clk`. Its project declares its default reset as `rstMain_n`, so no name the
    handler emits could have come from a literal.
  - The fixture's leaf carries a fixed-width **and** a parameterizable register and
    memory, because the generator has **five** flop-emitting code paths and a
    fixture with only fixed-width objects reaches three of them. Each of the five
    is pinned by a shape only that path produces, so the fixture cannot quietly
    stop covering one.
  - The leaf spans two domains while its handler spans one, which is the case that
    separates "the handler's own set" from "its owning block's set" (§6.6).

  **Nineteen mutations on the new sites, all killed** — eight on `flops.sv`
  (drop a `_CLK` from one branch, give a bare macro its own body, alias a
  different clock, reorder an alias's arguments, delete an alias, delete a
  `_CLK` variant, disagree on the argument list between branches, duplicate a
  body) and nine on `moduleRegs.py` (literal clock, literal port list, literal
  reset term, and `_CLK` dropped at each of the five flop sites plus a
  default-domain-only fallback). Two survivors were found on the first pass and
  both were coverage holes rather than acceptable ones: the argument-order check
  read only the ASIC branch, and the bare/variant pairing was checked in one
  direction only. Both checks were widened and both mutations then died.

  Two mutations are recorded as **not** attempted, with reasons, rather than as
  passing: the choice of `clocks[0]` over any other index (a generated handler
  never has a second clock, so no test can distinguish them), and the port list
  emitting the whole set rather than only the used clock (identical output for
  every reachable handler, for the same reason).
- **Derivation unit tests** in `unittest/test_clock_domains.py`, 27 cases, wired
  into `run_all_tests.sh` as its own suite. Six subprocess builds of a real
  design fixture assert the stored per-block sets (the default-domain shape, a
  connection `clock:`, block `clocks:`/`resets:`, a composed build whose two
  projects disagree on `clk`, a containment cycle, and a container holding only
  slow-domain children); three assert the reference diagnostics; five drive
  the single-domain memory and register-bus rules directly, in the manner of
  `test_build_manifest.py`, because authoring a register-decode hierarchy would
  exercise the decode machinery rather than the rule; one asserts the name
  collision; and two assert the `getBlockData` view. Every behaviour is
  mutation-checked, including the
  per-end project resolution, the canonical order, and each of the four `clock:`
  resolution wirings. The count was 25 before §10.5's removal took the two cases
  that asserted the crossing report.

  **Both halves of the two-pass derivation floor are pinned, and each kills the
  other's mutation** (§3). The containment-cycle case fails when the second,
  post-union pass is removed; the slow-domain-container case fails when the first
  pass is widened by dropping its `containedBlocks` guard. Neither case is
  satisfiable by the other's implementation, which is what makes the two passes a
  tested requirement rather than a coincidence.
- **Register-decode unit tests** in `unittest/test_register_decode_clock.py`, 6
  cases, wired into `run_all_tests.sh` as its own suite. The first four each build
  a design whose register-bus feed is authored in a different place — at the router
  instance, as the router's boundary map, at the router's container instance, and
  nowhere — and assert the stored clock of the synthesised rows plus the per-block
  sets they drive (§10.9). A fifth case reaches a routed leaf's register and memory from two
  separate accessor blocks, which is what makes the `registerConnections` and
  `memoryConnections` sites of `_connectionClockSites` load-bearing: dropping
  either from the walk costs an accessor its only domain. A sixth is a composed
  build whose child project does not declare the assembler's bus clock, so the
  respelling is exercised and not merely asserted. Eleven mutations, all killed.

  This coverage does not live in `test_clock_domains.py`, whose fixture has no
  register decode: a project owning a register with no `addressBlock:` router
  crashes in `calcAddresses` (`pysrc/processYaml.py:4648` indexes
  `addressControl['AddressGroups']`, which only a router creates). That defect is
  pre-existing and out of scope here.
- **Schema unit tests** in `unittest/` for the validation rules of §7, following
  the existing convention that library content is validated in tests rather than
  on every generator run. Landed in `unittest/test_project_scope.py`, which holds
  the fixture machinery for building throwaway projects: both failure modes of the
  exactly-one-default rule, for the root project and for a child IP; a multi-entry
  section with exactly one default accepted; and, for §2.5, the stored rows of a
  project declaring nothing, of a project declaring only its own differently-named
  clocks, and of an authored reset omitting `clock:`. Every one of those was
  mutation-checked. 75 cases.

  **The positive-count rule of §7 is covered here too**: eight rejection cases —
  `0`, `-1`, `2.5` and `abc` for each of `resets.releaseCycles` and
  `clocks.period`, each asserting that the message names the project file, the
  project, the section, the entry and the value — plus one build asserting the
  **stored type** of a defaulted and an authored value of each field. The type
  case has to read the type rather than the emitted text, because the emitter only
  interpolates the value and `'3'` and `3` spell the same C++; removing the
  coercion is invisible to every text assertion and fails only there.
- **Lint.** `make lint` over the new example, to confirm that multi-domain
  modules produce no unused-input or inferred-latch warnings. Done for the landed
  half: all six shipped lint targets are clean, and four of them lint a
  `_hdl_sv_wrapper` module as the top, so the changed port declaration is the
  linted text rather than an untouched neighbour. The multi-domain and
  non-default-domain wrappers of the emission fixture lint clean too.

---

## 10. Open decisions for review

0. *(Settled — not gating. See §10.1 for the evidence.)* Tandem semantics under
   two clock rates. An earlier draft of this plan called this the item most
   likely to gate the feature, on the assumption that differing clock periods
   would reorder interface transactions and produce spurious mismatches. The
   tandem sources live in `builder/pro`, which was not read when that draft was
   written. Having read them, the concern does not arise: the secondary side is
   always the untimed model, and comparison is per-port and sequence-based, not
   time-based.
1. *(Settled and LANDED — clock only.)* **Explicit macro family spelling** (§6.3).
   `DFFRC(c, r, q, d, rval)` with `r` as an active-high "in reset" expression is
   **superseded**. The reset is not parameterized: the user scoped this step to the
   clock, so the spelling is `<FAMILY>_CLK(clkSig, <the family's existing args>)`
   with the bare macro a one-line alias passing `clk`. Argument order is
   clock-first, which keeps every existing argument in its existing position and
   makes the alias a pure prefix.

   The accepted consequence is that the ASIC branch still cannot express two
   resets, since its reset comes from the per-compilation `` `RST ``. §6.4's
   three-way selector, or a later reset argument, is where that is answered. See
   §6.6 for what landed and how it is pinned.
2. **`period` / `timeUnit` split** (§2.1) versus a single authored string such
   as `1ns`. The split avoids string parsing, at the cost of being more verbose
   than the issue's original spelling.
3. *(Settled and LANDED, value included.)* **Reset release cycle count** (§5).
   Cycle-based release replacing the absolute 5 ns is settled by the
   period-coupling defect.

   **The count belongs in the reset definition** — a per-entry field on the
   `resets:` section — not a global project setting and not a hard-coded constant.
   A reset in a 3 ns domain and one in a 1 ns domain have no reason to share a
   release count: the count is a property of the reset's own release path, and the
   two resets are independent declarations that already carry their own `active:`
   and their own associated clock. A project-wide setting would force the slowest
   domain's requirement onto every domain, and a constant forecloses the choice
   entirely.

   **The field landed with its consumer, as `resets.releaseCycles`
   (`config/schema.yaml`), read by `sec_reset_drivers`
   (`templates/systemc/module_hdl_wrapper.py:139`).** Schema and consumer in one
   change, so nothing planned-but-unused was added.

   **The default is 3, not the 8 this item suggested.** Eight had no measurement
   behind it, and this item's own worry about "an existing test that begins
   driving stimulus at a fixed time" is exactly what it would have caused: the
   release would have moved from 5 ns to 10 ns in every existing project. Three
   is the smallest count that is both correct (two is the minimum for a
   synchronous reset) and behaviour-preserving: the wrapper's `sc_clock` starts at
   3 ns, so a 1 ns clock's third posedge is at 5 ns, the instant the absolute
   `wait(5, SC_NS)` used. Measured on `examples/twoClk`, where the two blocks'
   `clk` differ by project: `twoClkSink` (period 1 ns) releases at 5.0 ns and
   `twoClkIpSrc` (period 3 ns) at 9.0 ns, each on the third posedge, read from the
   verilated VCD. A project needing a longer synchronised release chain raises the
   count on the one reset that needs it, which is why the field is per reset.
4. *(Settled and LANDED.)* **What is settled is the ORDER: clocks then resets,
   each in canonical order, sharing one module port namespace. The spelling is
   each generator's own local style.** §5.1's "every port list moves to one
   declaration per line" is superseded — not by a different universal spelling,
   but by there being no universal spelling to impose. The block module port list
   keeps its joined `input clk, rst_n`; the verilated SV wrapper keeps its
   one-per-line `input clk,\ninput rst_n`; and `<block>_regs` is a third generator
   with its own per-line spelling in an RTL module, so "the RTL module style" is
   not a thing that exists (§5.1). Both helpers are generated from the one
   `clock_reset_port_names`, so the order rule has a single implementation, and
   both are byte-identical to baseline for a single-clock project.

   **The rule to apply at the remaining §5 sites: match the local style, keep the
   ordering global.** An earlier revision of this item read as settling the joined
   spelling everywhere and briefly did impose it on the wrapper; that churned 28
   files to no benefit and is reverted.

   **Churn is explicitly accepted for this change.** The single-line form happens
   to be byte-identical for single-clock projects, but that is a convenience, not
   a constraint the implementation must contort to preserve. Where the clock work
   causes generated-file churn, take it. This relaxes the no-churn requirement
   from a gate to a preference for the clock feature specifically, and §8's
   no-churn argument becomes supporting evidence rather than a hard gate.

   **Measured outcome: 23 generated files, one category, itemised in §5.1.** The
   byte-identity prediction held everywhere it could: the block-module port lists
   §5.1 predicted would rewrite everywhere rewrote nowhere, and so did every
   verilated SV wrapper. The residual churn is entirely the SC wrapper's reset
   driver gaining a per-reset name and a cycle-counting body, which is behavioural
   and cannot be avoided.

   **`test_build_manifest.py` needed no baseline refresh.** This item expected one;
   it holds no byte-identity expectation. It runs `make clean; make db; make gen`
   per example and compares the manifest's directory set against the makefile glob
   set, which no port-list spelling can move. Nothing in `unittest/` compares
   generated bytes: `unittest/functional_layout_regression.sh` is the only script
   that hashes generated output and `run_all_tests.sh` does not call it.
5. *(Settled — REMOVED by user decision. Supersedes this item's earlier
   "now mandatory, LANDED" ruling.)* Phase 1 reports **no** cross-domain
   connection.

   The report was implemented as a `printWarning` per crossing and did fire on
   `examples/twoClk`, which has a genuine crossing, so every `make db` there
   reported "Found 1 Warning." The user has since decided this should not be a
   warning at all: **a crossing is the designer's business, and the tool should
   not complain about it.** The report is removed, along with the per-site label
   strings that existed only to phrase it, and nothing replaces it — not an error,
   not a log line, not a report file, not a quieter variant. The derivation is
   unchanged. See §3.

   Consequence: the two crossings §3 previously recorded as "unreported and open"
   — a block carrying more than one clock, and a container instantiating a foreign
   child whose domains differ with no connection between them — are no longer open
   questions. Nothing is reported at all, so there is no inconsistency to resolve.
   The intra-project unreachability correction survives the removal, because it is
   a fact about the derivation rather than about the report.
6. *(Settled.)* Project scope lands first, and Phase 0 carries the §2.1/§2.2
   sections plus the shared multi-clock example, with no emission. See §8.
   **Phase 0 is now implemented and green** —
   see [`plan-project-scope.md`](./plan-project-scope.md).
7. *(Settled — deferred to phase 3.)* **Boundary binding** (§2.0.2). Phase 1
   resolves every clock and reset within its declaring project only, and no
   instantiation-time binding syntax is introduced. Rationale: no example in the
   workspace has a consumer for it, and adding an optional `clocks:` /
   `resets:` map to `instances:` later is a purely additive schema change, so
   nothing is foreclosed. This also keeps the D5 supplier work deferred, since a
   bound clock port and a supplied clock port are the same mechanism seen from
   opposite ends.

   The accepted consequence is that an assembler cannot re-clock an
   instantiated IP, and the same IP cannot appear twice on two clocks. Revisit
   when a real composed design needs either.
9. *(Settled — Option A, LANDED.)* **`postParseRegisterPorts` propagates the clock
   to generated decoders.** Phase 1 does NOT accept the restriction that a
   generated register decoder lives only in its project's default domain.

   **Option A, as implemented: the generated decode tree inherits the clock of the
   authored register-bus feed that reaches the primary router.** Every row the
   synthesis emits into `connections` and `connectionMaps` carries that clock,
   respelled in the clocks of the project that owns the receiving row's yaml file.
   `config/postParseRegisterPorts.py:290` resolves the feed;
   `config/postParseRegisterPorts.py:816` stamps the rows as they are emitted.

   The rationale is that a `<block>_regs` handler and an `apbDecode` router are
   bus endpoints, so their domain is the bus's, not the served block's. A slow
   peripheral behind a fast register bus is the normal arrangement, and the
   crossing then sits on the `reg_rw` / `reg_ro` wires into the block's own logic
   rather than on the bus. The served leaf consequently derives both domains,
   which is visible in `unittest/test_register_decode_clock.py`.

   **Option B — propagating each served block's own domain upward — was rejected.**
   A router serves many leaves, so under Option B a router whose leaves sit in
   different domains is reachable, and the synthesis would need a router-agreement
   check and a new error class to reject it. Under Option A the router's domain
   comes from exactly one row, the feed, so a multi-domain router is unreachable by
   construction and there is nothing to check. Option A therefore adds no error and
   no warning of any kind, consistent with §10.5.

   **The sections this item names.** An earlier revision said the synthesis is
   extended so a synthesised `registerConnections` / `memoryConnections` row
   carries the clock of the block it serves. It creates no such row.
   `config/postParseRegisterPorts.py:812` emits exactly
   `('blocks', 'instances', 'connections', 'connectionMaps')` through
   `processSingleFile`, and `examples/apbDecode/apbDecode.db` bears this out:
   0 `registerConnections` and 0 `memoryConnections` against 3 `connections` and
   3 `connectionMaps`. The sections that carry the clock are therefore
   **`connections` and `connectionMaps`**.

   **Where the feed is authored — four shapes, all in tree, and no error for the
   fourth.** An earlier claim that the feed is uniformly identified by the primary
   router's `instanceKey` is false; it is a two-tier search, and the fourth shape
   has no feed at all:
   - an authored `connectionMaps` row into the router instance — the assembler
     shape (`examples/apbDecode/arch/yaml/apbDecode.yaml:139`,
     `examples/ip_test/top/yaml/ip_top.yaml:119`);
   - an authored `connections` row into the router instance — the standalone
     reusable-IP shape (`examples/ip_test/ip/yaml/ipTop.yaml:88`);
   - an authored `connections` row into the instance of the router's **container**
     block, when the container declares `registerPorts:` and its inward boundary
     map is the one this pass synthesises
     (`examples/ip_test/bridge/yaml/bridgeStdTop.yaml:73`);
   - no authored feed at all, which is the shape of every `addressBlock:` fixture
     in `unittest/` (23 suites author no connections whatsoever). Such a tree
     states no domain, so its rows keep the unstated-`clock:` rule and resolve to
     their own project default. Nothing today diagnoses a primary router with no
     upstream feed, and this change does not start: it would fail 23 existing
     suites, and a decode tree's domain is not the place to introduce a
     structural rule about the bus.

   Only rows reaching the primary router are read. A `clock:` authored on the
   master connection *behind* an authored boundary map does not reach past that
   map, which is an authoring rule pinned by
   `unittest/test_register_decode_clock.py`. A candidate row must resolve to an
   `addressBus: true` interface, so a data stream into the same container instance
   cannot be mistaken for the feed.

   **The cross-project respelling is load-bearing, not cosmetic.** The rows land in
   several projects' yaml files (three in `examples/ip_test`), and a `scope: project`
   reference to a clock the receiving project does not declare is a hard error
   (`pysrc/processYaml.py:6931`). The propagated name is therefore resolved into the
   receiving row's project by the same name-else-default rule the derivation uses,
   now shared as `projectCreate.resolveProjectScopedName`
   (`pysrc/processYaml.py:5346`).

   What this does **not** do is make §7's register-bus rule reachable for routers.
   That rule iterates `registerConnections`, which synthesis never writes, so no
   change here can make it fire for a generated decoder. §7 records the strike.

   **No generated-file churn.** Every in-tree example resolves its feed to its own
   default clock, so all 21 example databases are unchanged row for row; and even
   with a non-default bus clock authored, generation is byte-identical, because
   nothing emits from `blockClocksResets` until §5 lands.
8. *(Settled by item 5 — nothing is reported.)* The deferral in item 7 means a
   composed IP's declared `period` does not drive its RTL — the assembler's clock
   does (§2.0.2). This item asked whether reporting that mismatch was sufficient
   or whether it should be an error. Item 5's removal answers it in the third
   direction: the mismatch is neither reported nor an error. Making it an error
   would force every composed IP and assembler to agree on `period` until phase 3
   lands, which is exactly the composition case project scope exists to allow.

   Derivation is still the half that makes the surprise concrete — the IP's block
   derives its OWN `clk` row, so the two declarations stay distinct in the
   database, and only the deferred wiring collapses them onto one net. That
   distinctness is asserted by `unittest/test_clock_domains.py`, which is now the
   only place the composed disagreement is pinned.

### 10.1 Tandem is insensitive to clock rate — evidence

Read from `builder/pro`, which holds the tandem harness this repository lacks.

- **The secondary side is always untimed.** The tandem wrapper
  (`templates/systemc/constructorTandem.py:84-85`) builds `verif` as
  `INSTANCE_FACTORY_PRIMARY_TYPE` and `model` as
  `INSTANCE_FACTORY_SECONDARY_TYPE`. The model has no clock, no period, and no
  domain. In `--vlType model` both sides are models, so no clock exists at all.
  Clocks are a property of the primary RTL side only, which is why a clock-rate
  change cannot desynchronise the pair.
- **Comparison is per-port and sequence-based, never time-based.**
  `common/systemc/rdy_vld_port_tee.h:29-42`: each tee thread reads the *n*-th
  transaction on *its own* port from each side and compares payloads. Nothing
  compares timestamps, and nothing compares the relative order of two different
  ports. Two ports in different domains therefore cannot produce a mismatch by
  reordering with respect to each other — that ordering is not observed.
- **The tee is a rendezvous, so rate differences are absorbed rather than
  accumulated.** `rdy_vld_tee_1in_2out::tee` holds the primary until the
  secondary has completed its write (`:96-99`), and `2in_1out` holds whichever
  side arrives first until the other produces its matching transaction
  (`:43-47`). Skew between the sides is bounded at one transaction per port by
  construction.
- **`synchLock` is clock-agnostic.** `common/systemc/synchLockPro.h` replicates
  arbitration decisions through a `std::queue` plus an `sc_event`
  (`:145-221`, `:227-260`). There is no clock, no period, and no `sc_time`
  anywhere in it. It works identically whether the primary's domains run at one
  rate or five.
- **Arbitrary skew is already a supported mode.** `--delay` / `--delayMode`
  (`common/systemc/simController.cpp:44-58,99-114` reaching
  `interfaceBase::setTimed`) deliberately injects fixed or random delay into one
  side. The framework is designed to tolerate the two implementations advancing
  at unrelated rates; differing clock periods are a milder case of what this
  mode already stresses.

What multi-clock *does* change for tandem is structural, and belongs to phase 2
rather than being a semantic risk:

- The wrapper used to declare exactly one
  `sc_clock clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true)` and bind
  it to the DUT and to *every* BFM. Both halves are FIXED: one `sc_clock` per
  clock in the block's set, at its own period, and each BFM clocked by the clock
  of the connection it drives (§5.3). The BFM's reset remains the block's, which
  §5.3 argues is correct rather than residual.
- The same template used to hard-code `rst_n` released at `wait(5, SC_NS)`, two
  periods after the 3 ns clock start. FIXED: `releaseCycles` edges of the reset's
  own clock, per reset (§10 item 3). The residual is polarity — `active: high` is
  still not consumed (§2.2).
- The residual verification gap is unchanged from §6: with the model untimed, a
  cross-domain race inside the RTL has no counterpart in the model to disagree
  with, so tandem cannot *confirm* dual-clock behaviour even though it cannot
  spuriously fail on it. That is the same reasoning that keeps dual-clock memory
  in phase 2 (§7).

## 11. Unverified assumptions

Recorded so they are not mistaken for established facts:

- **VCS compilation-unit behaviour.** The macro-delivery analysis in §6 assumes
  both Verilator and VCS treat the whole `-F` list as one compilation unit, so
  macros defined in `flops.sv` reach `-y`-resolved library files that never
  include it. That is demonstrably true today —
  `pro/common/systemVerilog/inPlaceList.sv` uses `` `DFF `` without including
  `flops.sv` — but no VCS command line exists anywhere in this workspace, so
  whether the external VCS makefile passes a multi-compilation-unit option is
  inference, not verification.
- **Whether VCS expands a macro whose body is another macro invocation.** The §6.6
  alias shape depends on it: `` `DFF `` expands to `` `DFF_CLK(clk, ...) ``, which
  the preprocessor must then expand again, and the inner definition is multi-line
  with backslash continuations. IEEE 1800 §22.5.1 permits it and Verilator 5.038
  does it — the expansion identity of §6.6 is measured through `verilator -E` — but
  no VCS command line exists anywhere in this workspace, so VCS is inference. The
  failure mode would be loud (every bare macro call site at once) rather than
  silent.
- **Whether a clock alias survives ASIC clock-tree synthesis.** `wire clk =
  coreClk;` is a buffer CTS should absorb, but some flows and CDC tools object to
  a clock that is neither a top-level port nor a generated clock, and an SDC
  written against `coreClk` may not propagate without a `create_generated_clock`.
  No ASIC flow exists here to test against and no SDC generation exists today.
  The fallback is to alias only the reset, where polarity normalisation is
  genuinely required, and require explicit macros for any non-`clk`-named
  clock — which reintroduces the §6.2 migration problem.
- **FPGA area cost of enabling a reset.** §6.4 argues the branches unify. On some
  FPGA families a flip-flop has one set/reset resource, so adding a per-flop
  reset where none existed can cost a LUT input or force a different primitive.
  No data on the targeted family.

---

## 13. Verification baseline — what "working" must mean

Established empirically in an isolated tree copy. Every figure below was measured,
not estimated, except where marked.

### 13.1 The generation-only gate is not sufficient

`unittest/run_all_tests.sh` runs `make clean; make db; make gen` per example
(`unittest/test_build_manifest.py:128`) and contains **no reference to Verilator
or `VL_DUT`**. It has never compiled a model, invoked Verilator, run a
simulation, or run tandem. An "all suites green" result therefore proves the
generator emitted the expected files — nothing about whether the design works.
For a feature whose entire purpose is clock and reset behaviour, that gate is
too weak. (The suite count in this plan is deliberately not restated; it moves
every time a suite is added, and 98 as of the §5 emission step.)

### 13.2 Verilated co-simulation works natively

No container required; Docker is not installed. The four variables
`docker/Dockerfile` bakes into `/etc/skel/.bash_custom` are valid on this host and
are **unset in a clean shell**, while `include/make/a2c-systemc.mk:18` hard-errors
without them:

```
SYSTEMC_INCLUDE=/usr/include        SYSTEMC_LIBDIR=/usr/lib
BOOST_INCLUDE=/usr/include/boost    LD_BOOST=/usr/lib/x86_64-linux-gnu
```

`SYSTEMC_HOME` is referenced by no makefile. `VERILATOR_ROOT` needs no setting.
Verilator 5.038, SystemC 2.3.4, clang++ 20.1.8.

Proven: `examples/ip_test` builds with `make -C rundir -j8 all VL_DUT=1` in 33.4 s
and runs clean on five `--vlInst` targets; `axi4sDemo` likewise. **Negative
control** — the same design built without `VL_DUT=1` and given `--vlInst` aborts
with `unregistered block type <block>_verif`, confirming the passing runs are
genuinely verilated rather than silently falling back to the model.
`--vlType` defaults to `verif` (`common/systemc/simController.cpp:94`).

### 13.3 Tandem cannot run from `base/examples` — by design

`pysrc/processYaml.py:191-200` refuses to promote `a2cRoot` to the parent when the
project file lives inside `builder/base`, so `pro/` is never merged, `A2CPRO` is
undefined, `simController.cpp:60-62` asserts `Tandem mode not supported`, and no
`*Tandem.h/.cpp` is generated. Confirmed by relocating `ip_test` outside `base`,
where `make newmodule` scaffolded the tandem wrappers and both configurations ran
clean: model/model in 26.9 s (no Verilator) and RTL/model in 34.0 s, with
`Tandem instance ... initialized` in the log proving tandem engaged rather than
skipped.

**Consequence for this plan:** the `examples/twoClk` fixture, living under
`base/examples/`, can be verilated but can **never** exercise tandem. Tandem
coverage of multi-clock requires a fixture outside `builder/base`. This does not
reopen §10.1 — that analysis stands on the untimed-secondary and per-port
sequence comparison, both re-confirmed here — but it does mean the claim cannot
be regression-tested from this example.

### 13.4 A generator defect blocked the fixture — FIXED

The `tbExternal` template emitted raw forward declarations (`class <child>Base;`)
in the header's generated region, while the `.cpp`'s generated `init` region emits
`import <project>_<child>.base;` **before** `#include "<x>External.h"`. Under
C++20 that is illegal — "global module declaration follows module declaration".
It fired whenever a testbench External had non-excluded child instances, so it hit
`twoClk` (two children) and `lmmiDemo` (monolithic — this was not
composition-specific). `examples/simple_ip` escaped it only because a
*user-authored* `#include "…External.h"` sat above the generated region and pulled
the forward declarations in first.

The template now emits `import <project>_<child>.base;` in place of the forward
declarations, so the header carries no global-module declaration after a module
declaration. `make two-clk` builds and runs both the model and the `VL_DUT=1`
configuration.

### 13.5 Cost, and why the VL gate must be a separate target

| Step | Time | Disk |
| :-- | :-- | :-- |
| current suite, per example | ~1.8 s | negligible |
| `twoClk` model build from clean | 9.4 s | 312 M |
| `twoClk` `VL_DUT=1` on top, 3 tops | +11.4 s | +46 M |
| `ip_test` VL from clean, 10 tops | 33.4 s | 1.7 G |

Verilation itself is cheap; the cost is the SystemC compile, which the
`.build_flavor` stamp forces to recompile on every model↔VL flip, plus
`-g -fstandalone-debug` objects and PCMs. Eleven examples declare `hasVl: true`.
A full VL sweep is **3–5 minutes and 5–10 GB (extrapolated from four measured
examples, not measured across all eleven)**.

It also cannot be a blanket sweep today: `simple` and `axiDemo` **hang** at
`Simulation Start` and `apbDecode` asserts in the model — all pre-existing and
already recorded at `plans/plan-composition-ordering.md:261`. A blanket target
would need per-run timeouts and an expected-fail list.

**Selected: a curated `regr`-style target over the known-good set, not
`run_all_tests.sh`.** That shape already exists — `examples/ip_test/rundir/regr_ip_test.json`
drives `make -j all VL_DUT=1` plus ten `--vlInst` cases.

### 13.6 Acceptance criteria for the clock feature

A phase is not "working" until, for the multi-clock fixture:

1. `make db` and `make gen` succeed and existing examples regenerate as expected.
2. The model-only build compiles and the simulation runs to `No error`.
3. The `VL_DUT=1` build compiles and each verilated top runs to `No error`,
   with the negative control of §13.2 confirming the run is genuinely verilated.
4. The fixture is reachable from a build target. It is not enough for it to exist
   in `examples/` — see [`plan-project-scope.md`](./plan-project-scope.md) §12.

All four hold today for `examples/twoClk` via `make two-clk`, which is itself a
prerequisite of `make pipeline-test`. Each later phase must re-establish them, and
the §5 emission step did: `make two-clk` exits 0 with the model run and all three
`--vlInst` verilated runs at `No error`, and `make db` prints no warnings.

Re-established after the §5 remediation round: `make two-clk` exits 0 with all
four runs at `No error`, `examples/simple` `make run` and `make run-vl` both exit
0 at `No error`, all six shipped lint targets are clean with zero warnings, the
unit suite is green at 98 suites with no suite added or removed, and a second full
regeneration of every re-generated project reproduces the state byte for byte.

Re-established again after the §6 macro and `<block>_regs` step, with the
register-heavy examples added because they are the ones this step rewrites:
`make two-clk` exits 0 with all four runs at `No error`; `examples/simple`
`make run` and `make run-vl` both exit 0; `make apbDecode`, `make mixed`,
`make ip-test` and `make simple-ip` all exit 0 — 18 `No error` runs from
`ip-test` alone, and `mixed` includes its `VL_DUT=1` build and its lint. All six
shipped lint targets are clean at zero warnings and zero errors, and five of the
seven rewritten `_regs` files are linted in flow by `apbDecode/rtl` and
`mixed/rtl` rather than only regenerated. The unit suite is green at 98 suites,
zero FAIL, with no suite added and none removed. The tree is a fixed point across
a second sweep and across all the build-and-run gates.

**`make lint` mattered more than usual here and found nothing**, which is the
result worth recording: this step rewrites the `always_ff` body of every register
block in the tree, so an inferred latch, a multi-driven signal or an unused input
is exactly what would have surfaced. None did, in any of the six targets. The
non-default-domain shape cannot be linted in flow yet, for the reason §5 records
— the child-instance binding row has not landed — so the evidence for that shape
is the `verilator -E` expansion identity of §6.6 and the emission suite's text
assertions, not a lint run.

**One addition the §5 step earns: a behavioural gate, not only a build gate.**
For anything that changes clock or reset timing, "it built" proves nothing.
`--vlTrace` writes the verilated VCD, and the release instant is read from it
directly: for `examples/twoClk`, `rst_n` rises at 5.0 ns in the `twoClk.uSink`
wrapper (period 1 ns, posedges 3/4/5) and at 9.0 ns in the `twoClk.uIpSrc`
wrapper (period 3 ns, posedges 3/6/9). Two wrappers, the same `releaseCycles: 3`,
two release times — which is the whole point of the change and is invisible to
every other gate. Re-measured after the remediation round on the VCD's own
timescale of 1 ps: `rst_n` rises at 5000 ps and at 9000 ps respectively.

**Re-established again after the `apbDecode` router step (§6.7).** `make two-clk`,
`examples/simple` `make run` and `make run-vl`, `make apbDecode`, `make ip-test`,
`make simple-ip` and `make mixed` (which carries its own `VL_DUT=1` build and its
lint) all exit 0 — 40 `No error` runs across the seven targets, 18 of them from
`ip-test`. The unit suite is green: exit 0, 98 suites, zero `FAIL`, and the suite
NAME set is identical before and after, because the router cases were added to the
existing `test_clock_reset_emission.py` rather than as a new suite. The tree is a
fixed point: a second full clean sweep after all the build gates leaves every
generated file byte-identical.

**Two things this step's gates surfaced that are worth recording as they are.**

- **`make lint` found nothing, and covers less of this change than of the last
  one.** Every generated router's `always_ff` body is rewritten here, so an
  inferred latch or a multi-driven signal is exactly what lint would catch; the six
  shipped lint targets are clean at zero warnings and zero errors. But only **two**
  of the seven rewritten routers — `apbDecode/rtl/apbDecode.sv` and
  `mixed/rtl/apbDecode.sv` — are reached by a shipped lint target. The other five
  are owned by nested IP projects, and their evidence is verilation instead:
  `make ip-test` and `make simple-ip` both run `run-vl`, which elaborates and
  compiles `ip_test/top`, `ip_test/bridge`, `ip_test/ip`, `simple_ip` and
  `simple_ip/ip` — a stronger check than lint, though it reports no lint warnings.
- **Eleven of the nineteen directories that include `a2c-rtl.mk` cannot run
  `lint` at all, for a reason predating this work.** Their `Makefile:1` sets
  `REPO_ROOT = $(shell git rev-parse --show-toplevel)` without the
  `/examples/<project>` suffix its siblings carry, so `shared.mk` is not found,
  `A2C_ROOT` is empty, and the include fails with
  `/include/make/a2c-rtl.mk: No such file or directory`. Affected:
  `helloWorld`, `nested`, `xif`, `ip_test{,/common,/ip,/bridge}`,
  `simple_ip{,/common,/ip}` and `twoClk/ip` (which resolves its makefiles but then
  has no `rtl.f`, so verilator is invoked with an empty `--top-module` and reports
  two errors). `hierInclude/systemVerilog` and `inAndOut/systemVerilog` are not
  among the nineteen: they carry their own `lint` targets and do not include
  `a2c-rtl.mk` at all. None of the eleven is invoked by any shipped target, which is why
  the breakage is invisible; it is recorded here rather than fixed because it is
  unrelated to clocks.
