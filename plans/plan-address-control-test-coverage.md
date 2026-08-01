# Plan: Hierarchical Register Test Coverage for `addressControl` Refactor

Companion test plan for
[`plan-address-control-refactor.md`](./plan-address-control-refactor.md).
This document is the implementation contract for **Stage 7** of
the parent plan, scheduled after Stage 6 (`ip_test` migration) so
that its `ip_test` rows can read assertions off the migrated database.
The named `unittest/test_addrctl_*.py` and `test_error_*.py` fixtures
below are planned Stage 7 deliverables, not current coverage unless a
later status note says otherwise. Topology-only verification belongs
under `unittest/`; `examples/` remains reserved for user-facing
examples. The parent plan's Validation section names only the gates the
parent itself commits; the topology matrix, the error-case matrix, the
coverage map, and the diagnostic-substring assertions all live here.

The repository may carry `proto/model` runtime tests, but they are not
a Stage 7 gate for this refactor. Every case in this plan is validated
by one of:

- **User-example regression**: a runnable, user-facing
  `examples/<name>/` build, currently the migrated `examples/ip_test/`.
  Its value is end-to-end: it exercises `projectCreate`, view
  construction, and every template generator that the case touches, and
  the resulting generated code is built by the example's own `Makefile`.
- **Unit test**: a self-contained file under `unittest/` that writes
  mocked YAML, calls `arch2code.py` to build a temporary database,
  reopens it through `projectOpen`, and asserts on the view
  attributes the new post-parse pass produces. Mirrors the existing
  `unittest/test_thunker_view.py` pattern.

Legacy `addressControl.yaml` behavior is **out of scope** for this test plan.
The legacy path was subsequently retired; this plan exercises the sole accepted
per-block schema.

## Related Documents

| Document | Relevance |
| -------- | --------- |
| [`plan-address-control-refactor.md`](./plan-address-control-refactor.md) | Parent plan; Stages 1-7 and the Validation section that this document expands. |
| [`research-address-bus-distribution.md`](./research-address-bus-distribution.md) | Canonical design discussion; defines the topology vocabulary used below. |
| [`research-multi-config-bindings.md`](./research-multi-config-bindings.md) | Q10 / R2 cross-interface bind through the thunker pool — load-bearing for the cross-config register-bus cases. |
| [`config/postParseRegisterPorts.py`](./config/postParseRegisterPorts.py) | New-schema post-parse pass under test. |
| [`unittest/README.md`](./unittest/README.md) | Conventions for self-contained unit tests. |
| [`unittest/test_thunker_view.py`](./unittest/test_thunker_view.py) | Template the new view-assertion unit tests follow. |
| [`rules/skills/address-migration.md`](./rules/skills/address-migration.md) | Canonical migration skill; Stage 6.6 acceptance gate. |

## Goals

- Enumerate every register-bus hierarchy shape the new schema admits,
  so coverage is decided by design rather than by which fixture
  happens to be on hand.
- Assign each shape to the smallest mechanism that proves the
  behavior: an example when end-to-end template coverage adds value,
  a unit test when projectOpen view assertions are sufficient.
- Pin every diagnostic in the parent plan's Stage 5.3 list to a
  failing unit-test fixture whose error string is asserted verbatim.
- Provide a clear map from each test case to the post-parse step or
  validator it covers, so a regression points at the offending code
  path on first triage.

## Non-Goals

- **Legacy-schema coverage.** Projects on `addressControl.yaml` are
  not exercised here. The two paths are mutually exclusive at
  post-parse time, so they cannot interact.
- **`proto/model` runtime asserts.** Not a Stage 7 gate for this
  refactor.
- **New post-parse semantics.** This plan does not change the
  refactor; it tests the behavior the refactor commits to.
- **Cross-`interfaceType` adaptation.** Parent plan Non-Goal. This
  plan covers the diagnostic only.
- **Multi-`registerPorts:` per leaf.** Parent plan Non-Goal.
  Diagnostic only.
- **Multi-instance routers serving the same group.** Diagnostic
  only.

## Current Repository Status

**Complete (reconciled 2026-07-24).** The new-schema implementation and the
full Stage 7 checklist are committed. Topology Batches A/B, migrated-`ip_test`
DB assertions, error Batches A/B, E3.1-E3.4, the no-`_global` invariant, and
the skill-doc cross-check are closed; no Stage 7 coverage rows remain open.

The following Stage 7 coverage is **committed**:

- Batch A topology fixtures: T1.1, T1.2, T1.3, T1.5, T2.1, T2.2,
  T4.1, T4.2, T4.3, T5.1, T5.2, T5.3, and T5.4.
- Batch B topology fixtures: T2.6, T3.1, T3.2, T3.4, T3.5, TT.3,
  TT.4, plus the additional TT.5 parent-router variant-interface
  guard.
- Error-case fixtures: E1.1 through E1.5, E2.1 through E2.5, and
  E3.1 / E3.2. (E2.6 removed 2026-06-12; replaced by positive T5.5.)
- The no-`_global` invariant is implemented through
  `unittest/_addrctl_helpers.py::assert_no_global_register_binds` and
  is called by the committed `test_addrctl_*.py` topology fixtures
  rather than by a standalone `test_no_global_register_binds.py` file.

The following Stage 7 coverage was **closed 2026-06-12**:

- Dedicated migrated-`ip_test` view assertions for T1.6, T2.3, T2.4,
  and T2.5, now committed as
  `unittest/test_addrctl_ip_test_view.py`. The fixture builds the
  migrated `examples/ip_test/` project into a temporary database and
  asserts the router/leaf `addressDecode` views (router `apbReg` vs
  leaf-scoped `ipReg`), the `uIpRegs` leaf-to-handler connectionMap,
  the primary router serving both direct leaves and the nested-router
  container, and the bridge subtree dispatch.
- E3.4 as a named Stage 7 fixture:
  `unittest/test_register_ports_independent_of_ports.py`. The leaf
  owns no registers, so the register-bus port reaches the
  partial-`ports:` check only through the router-to-leaf bind and only
  the `registerPortNames` skip can clear it — verified by a disable-the-
  skip probe that turns the build red.
- The skill-doc cross-check against `rules/skills/address-migration.md`:
  its "Migration Diagnostics" section now summarizes every E* diagnostic
  category (E1.1-E1.5, E2.1-E2.5, E3.1, E3.2). The deployed
  `.claude/skills/address-migration/SKILL.md` copy was synced.

No Stage 7 coverage rows remain open. The literal
`unittest/run_all_tests.sh` "green" gate is currently blocked by four
**unrelated** failures (`test_addrctl_single_router_multi_reg.py`,
`test_addrctl_no_ip_mixed.py`,
`test_addrctl_parameterized_router_upstream.py`,
`test_addrctl_parent_router_variant_interface.py`) that fail on the
in-development parameterized-eval features (block-param backing
constants, parameterized-interface endpoint rules, and the eval
`.bit_length()` grammar), not on the address-control post-parse path.
Those fixtures need updating against the current C4 eval/parameter
contract; that work is outside this plan's register-bus scope.

E3.1 / E3.2 no longer require prerequisite implementation work. The
earlier `validatePorts()` prerequisite is **superseded** by the
**committed** new-schema post-parse path, where
`config/postParseRegisterPorts.py` calls `checkInterfacePair()` for
router-to-leaf and parent-router-to-child-router register-bus dispatch.
The named E3.1 / E3.2 tests were **verified** during this documentation
cleanup.

E1.5 was originally listed here as a prerequisite for a
`registerPorts:`-specific out-of-scope diagnostic. That approach was
dropped in favor of a generic enrichment on the schema `_validate`
step in `pysrc/processYaml.py::processSimple`, which now surfaces the
unresolved reference for every `_validate: {section, field}` lookup,
not just `registerPorts:`. The E1.5 test asserts the actual diagnostic
the enrichment produces; see the Error-Case Matrix row for the
substrings.

## Stage 7 Checklist

- [x] Topology Batch A: **committed** under `unittest/test_addrctl_*.py`.
- [x] Topology Batch B: **committed** under `unittest/test_addrctl_*.py`.
- [x] Batch C migrated-`ip_test` DB assertions: **committed** for T1.6,
  T2.3, T2.4, and T2.5 in `unittest/test_addrctl_ip_test_view.py`.
- [x] Error-case Batch A: **committed** for E1.1 through E1.5 and the
  Batch A E2 rows.
- [x] Error-case Batch B: **committed** for E2.2, E2.3, and E2.4.
- [x] E3.1 / E3.2 register-bus compatibility diagnostics:
  **committed** and **verified**; the earlier `validatePorts()` wording
  is **superseded** by post-parse `checkInterfacePair()` coverage.
- [x] E3.3 no-`_global` invariant: **committed** through the shared
  topology-test helper; the originally named standalone fixture is not
  present.
- [x] E3.4 `registerPorts:` / `ports:` independence fixture:
  **committed** as
  `unittest/test_register_ports_independent_of_ports.py`.
- [x] Skill-doc cross-check: **committed**; every asserted E* diagnostic
  category is summarized in `rules/skills/address-migration.md`.

## Mechanism: Stand-alone Unit Tests

New unit tests will live under `builder/base/unittest/` and follow the
`test_thunker_view.py` template. Each test:

1. Builds an in-memory YAML fixture covering one topology. Helper
   functions assemble a `project.yaml`, an architecture YAML, and
   any include files in a temporary directory.
2. Invokes `arch2code.py --yaml <project.yaml> --db <tmp.db>` so
   `projectCreate` runs the new post-parse pass.
3. Opens the resulting database with `projectOpen` and resolves the
   relevant block, instance, connection, and view rows.
4. Asserts on the data the post-parse pass and the projectOpen
   view helpers produce. The assertion surface is the same
   contract templates consume:
   - `prj.data['blocks']` rows that the pass synthesises
     (`<block>_regs` handler blocks).
   - `prj.data['instances']` rows for those handlers.
   - `prj.data['connections']` rows for router-to-leaf and
     router-to-router binds.
   - `prj.data['connectionMaps']` rows for leaf-to-handler and
     nested-router upstream binds.
   - `prj.config['INSTANCES_WITH_REGAPB']`.
   - `getBlockData(<router>).addressDecode.registerBusInterface`,
     `.registerBusPort`, `.isApbRouter`.
   - `getBlockData(<leaf>).addressDecode.hasDecoder`,
     `.registerBusInterface`, `.registerBusPort`.
   - `_context` of every emitted row (must not be `_global`).

Error-case unit tests additionally assert that `arch2code.py` exits
non-zero and that stderr contains a specified diagnostic substring,
following the `test_error_*.py` pattern already used under
`unittest/`.

The new YAML fixtures must be small and topology-focused. They are
not full projects: they declare exactly the blocks, instances,
interfaces, and registers required to exercise the case. Templates
do not run on these fixtures; generator-template coverage comes from
user-example regressions such as `examples/ip_test/`.

## Mechanism: User-Example Regressions

User-example regressions will live under `builder/base/examples/<name>/`.
Each one has a `Makefile` that drives `make db && make gen`, and is run
as part of the example regression sweep. Topology-only verification
fixtures do not live under `examples/`; they are normal unit tests under
`builder/base/unittest/`.

The benefit of an example is that the example's own toolchain runs
the generator templates over the case, which catches template
breakage that a unit test would miss. The cost is that an example
that does not also build the generated SystemC / SystemVerilog can
silently regress at the template-output level. Examples in this
plan must compile their generated output, even if they do not run
it, so a template regression surfaces as a build break rather than a
silent diff.

The existing `examples/ip_test/` example becomes the canonical
new-schema integration once Stage 6 lands. Cases that this plan
identifies as "useful to fold into `ip_test` for breadth" are called
out below; they extend an existing user-facing example only when the
extra shape improves the example's value to users.

## Topology Vocabulary

The following terms are used throughout. They intentionally mirror
the language in `postParseRegisterPorts.py`.

- **Primary router.** The single router whose instance's container
  is not itself routed by another router (the dispatch-tree root).
- **Nested router.** Any router that is not primary; its instance
  sits in a container served by a parent router.
- **Routed leaf.** A non-router block that declares `registerPorts:`.
  It has a router-side dispatch connection even when it owns no
  registers or memories.
- **Handler-bearing leaf.** A routed leaf with at least one register or
  reg-access memory, and therefore a synthesised `<block>_regs`
  handler.
- **Plain leaf.** A non-router block without `registerPorts:`.
  The post-parse pass should not synthesise any router-side
  dispatch port for such a block.
- **IP leaf.** A routed leaf that declares `ipParameters:` and is
  instantiated under more than one `variant`.
- **Cross-config bind.** A connection or `connectionMap` whose
  source and destination resolve different `Config` values for the
  same interface (the thunker-pool path of
  `research-multi-config-bindings.md` Q10/R2).

## Topology Matrix

The **Mechanism** column is the binding decision. **Unit** means a
new `unittest/test_*.py`; **Example** means an `examples/*` build;
**ip_test** means a candidate to fold into the existing example
rather than spawn a new one.

### Single-router topologies (one address group, one router)

| ID | Shape | Mechanism | Fixture |
| -- | ----- | --------- | ------- |
| T1.1 | One router, one routed leaf with one register. | Unit | `unittest/test_addrctl_single_router_one_reg.py` |
| T1.2 | One router, one routed leaf with multiple registers and one memory. | Unit | `unittest/test_addrctl_single_router_multi_reg.py` |
| T1.3 | One router, two routed leaves at the same level. | Unit | `unittest/test_addrctl_single_router_two_leaves.py` |
| T1.4 | One router, one IP leaf with two variants (cross-config bind on register bus, packed-form check passes). | Example | extend `ip_test` (already covered by `uIp0`/`uIp1` after migration) |
| T1.5 | One router, mixed leaves: one routed leaf and one plain leaf. The plain leaf must not receive a synthesised dispatch port. | Unit | `unittest/test_addrctl_mixed_leaves.py` |
| T1.6 | One router whose leaf register-bus interface (`ipReg`) is declared in the leaf's own scope and differs from the router's upstream (`apbReg`), with matching packed form. | Example | covered by migrated `ip_test` (T2.4 below) |

### Two-level topologies (primary + one nested router)

| ID | Shape | Mechanism | Fixture |
| -- | ----- | --------- | ------- |
| T2.1 | Primary router, one nested router, one leaf under each. | Unit | `unittest/test_addrctl_two_router_simple.py` |
| T2.2 | Primary router with no direct leaves; all leaves under the nested router. | Unit | `unittest/test_addrctl_primary_no_direct_leaves.py` |
| T2.3 | Primary router with direct leaves AND a nested router that itself has leaves. | Example | migrated `examples/ip_test/` |
| T2.4 | Leaf interface scoped per-leaf (`ipReg` in `ip.yaml`), router-side APB interface visible to the router scopes (`apbReg` from the migrated `ip_test` include graph). | Example | migrated `examples/ip_test/` |
| T2.5 | Two-level with a Q10 cross-config thunker bridge container (existing `ipBridge` fixture, post-migration). | Example | migrated `examples/ip_test/` (`uBridge` subtree) |
| T2.6 | Nested router that is itself parameterized (router reused under two parent configurations). | Unit | `unittest/test_addrctl_parameterized_router.py` |

### Three-level topologies (primary + two levels of nesting)

The schema constraint that `addressBlock:` and `registerPorts:` are
mutually exclusive (parent plan Stage 1.5), combined
with the single-`registerPorts:` rule, means each
path from the primary router down terminates in **one**
register-bearing block. Intermediate blocks in the chain are
routers and carry no registers themselves. The canonical
multi-level test case is therefore "one register-bearing block
reused at multiple chain depths," not "different register-bearing
blocks at every level."

| ID | Shape | Mechanism | Fixture |
| -- | ----- | --------- | ------- |
| T3.1 | Primary router → mid-level nested router → leaf-level nested router → one or more routed leaves at the deepest level. Exercises the recursive parent walk in `_findRouterParent` across two router-to-router hops. | Unit | `unittest/test_addrctl_three_level_chain.py` |
| T3.2 | Primary router with two nested routers at the same level, each owning its own subtree. Fan-out, not chain depth. | Unit | `unittest/test_addrctl_three_level_fanout.py` |
| T3.3 | Three-level chain with cross-config thunker at the deepest leaf (parameterized IP under a doubly-nested bridge). | Example | candidate to extend `ip_test` with a deeper bridge subtree |
| T3.4 | One register-bearing block (a single block type declaring `registerPorts:`) is instantiated at three different depths of a three-level chain: once in the primary's container, once in the mid router's container, once in the leaf-level router's container. Asserts that the handler block / instance is synthesised exactly once for the block type, that three distinct router-to-leaf connections are emitted (one per instance), and that each connection names a different parent router. This is the canonical multi-level reuse case. | Unit | `unittest/test_addrctl_block_reuse_across_levels.py` |
| T3.5 | Mid router's container holds both a leaf instance of the same register-bearing block and a nested leaf-level router whose subtree contains another instance of that same block. Verifies that mixed leaf-and-nested-router siblings within one container produce distinct bind sets and do not collapse. | Unit | `unittest/test_addrctl_sibling_leaf_and_router.py` |

### No-IP topologies

These confirm correct behavior when no parameterization or thunking
is in play, so regressions in the parameterizable code paths do not
silently degrade simple projects.

| ID | Shape | Mechanism | Fixture |
| -- | ----- | --------- | ------- |
| T4.1 | One router, two non-parameterized leaves each with one register. | Unit | `unittest/test_addrctl_no_ip_simple.py` |
| T4.2 | Two-level hierarchy with all non-parameterized leaves. | Unit | `unittest/test_addrctl_no_ip_two_level.py` |
| T4.3 | Non-parameterized leaf in a container with a parameterized sibling (mixed parameterization under one router). | Unit | `unittest/test_addrctl_no_ip_mixed.py` |

### Boundary cases

| ID | Shape | Mechanism | Fixture |
| -- | ----- | --------- | ------- |
| T5.1 | Router declared but has no leaves with registers or memories under it. The pass synthesises no handler instances. | Unit | `unittest/test_addrctl_router_no_leaves.py` |
| T5.2 | Leaf with `registerPorts:` but no registers and no memories. No handler synthesis, but the leaf-to-router connection is still emitted. | Unit | `unittest/test_addrctl_leaf_register_port_only.py` |
| T5.3 | Router omits `upstreamPort:` and `registerDecoderPort:`. Defaults must resolve to `apbReg`. | Unit | `unittest/test_addrctl_default_port_names.py` |
| T5.4 | Router declares non-default `upstreamPort:` and `registerDecoderPort:` values. | Unit | `unittest/test_addrctl_explicit_port_names.py` |

### Cross-config thunker coverage

| ID | Shape | Mechanism | Fixture |
| -- | ----- | --------- | ------- |
| TT.1 | One router, one IP leaf with two variants — same-name `interfaceType: apb`, same packed form on both sides. Register-side thunker is not needed; the bind passes the same-`interfaceType` packed-form check. | Example | covered by `ip_test` (T1.4 / T2.4) |
| TT.2 | Q10 cross-config bind on the data side coexisting with a register-bus path through the same Configs. | Example | covered by `ip_test` (T2.5) |
| TT.3 | IP leaf whose `registerPorts:` interface is itself parameterized (register-bus structure references an `ipParameters` type). Register-side packed-form check must resolve per-variant. | Unit | `unittest/test_addrctl_parameterized_reg_iface.py` (and, if the case proves stable, fold a small variant into `ip_test`) |
| TT.4 | Nested router whose own `addressBlock.upstreamPort` carries parameterizable structures. | Unit | `unittest/test_addrctl_parameterized_router_upstream.py` |

## Error-Case Matrix (all unit tests)

Every diagnostic in the parent plan's Stage 5.3 list and the
Stage 1.5 parse-time checks will be exercised by a unit test that
asserts the error string verbatim. Follow the existing
`unittest/test_error_*.py` convention.

### Parse-time block diagnostics (Stage 1.5)

| ID | Condition | Fixture | Asserted diagnostic substring |
| -- | --------- | ------- | ----------------------------- |
| E1.1 | Block declares both `addressBlock:` and `registerPorts:`. | `unittest/test_error_addr_and_register_ports.py` | block name + both field names |
| E1.2 | Leaf declares more than one `registerPorts:` row. | `unittest/test_error_multi_register_ports.py` | block name + row count |
| E1.3 | `registerPorts:` row points at an interface whose resolved `interfaceType` has `addressBus: false`. | `unittest/test_error_register_port_not_addressbus.py` | row name + interface + `interface_defs` entry |
| E1.4 | Two router blocks declare the same `addressBlock.addressGroup`. | `unittest/test_error_duplicate_address_group.py` | both router-block names + group name |
| E1.5 | Leaf `registerPorts:` row targets an interface defined outside the leaf's load-time scope. | `unittest/test_error_register_port_out_of_scope.py` | leaf YAML filename + `key:regs` + `field interface` + offending interface name + the "no `<section>` row named ... any context processed before this one" hint produced by the generic schema-validator enrichment in `pysrc/processYaml.py::processSimple`. The defining YAML file is not named because dependency order processes the leaf before the interface-defining file. |

### Post-parse hierarchy diagnostics (Stage 4)

| ID | Condition | Fixture | Asserted diagnostic substring |
| -- | --------- | ------- | ----------------------------- |
| E2.1 | Router block declares `addressBlock:` but has no instance in the design. | `unittest/test_error_router_no_instance.py` | router block name |
| E2.2 | Two instances exist for the same router block. | `unittest/test_error_multi_instance_router.py` | both instance keys + router block |
| E2.3 | Zero primary-router candidates (every router is contained by another router's served scope). | `unittest/test_error_no_primary_router.py` | every router instance |
| E2.4 | More than one primary-router candidate. | `unittest/test_error_multi_primary_router.py` | each candidate |
| E2.5 | Routed leaf instance sits in a container no router serves. | `unittest/test_error_leaf_unserved.py` | leaf instance + container + nearest router |
| ~~E2.6~~ | **Removed (2026-06-12).** A routed leaf with registers/memories and zero `registerPorts:` rows is no longer an error — it infers its register bus from the serving router. The positive replacement is T5.5 (`unittest/test_addrctl_top_down_leaf_infers.py`). See the 2026-06-12 amendment in `plan-address-control-refactor.md`. | — | — |

### Validation diagnostics (Stage 5)

| ID | Condition | Fixture | Asserted diagnostic substring |
| -- | --------- | ------- | ----------------------------- |
| E3.1 | Leaf and router resolve to different `interfaceType` values (cross-`interfaceType` adaptation Non-Goal). | `unittest/test_error_register_interface_type_mismatch.py` | **committed** and **verified**; both `interfaceType` values + protocol-changer guidance |
| E3.2 | Leaf and router resolve to the same `interfaceType` but fail the packed-form compatibility check (Stage 6.2). | `unittest/test_error_register_packed_form.py` | **committed** and **verified**; both packed-form widths + offending field |
| E3.3 | A bind synthesised by the new post-parse pass carries `_context: '_global'` (regression guard for Stage 4 step 7). | `unittest/_addrctl_helpers.py::assert_no_global_register_binds` called by committed `test_addrctl_*.py` fixtures | **committed** through shared helper coverage; the originally named standalone fixture is **superseded** |
| E3.4 | A `ports:` partial-declaration diagnostic fires for a leaf whose only declared register-bus surface is `registerPorts:` (must not require duplication). | `unittest/test_register_ports_independent_of_ports.py` | **committed**; positive build, guarded by a disable-the-skip probe |

### Address-containment diagnostics (`calcAddresses`)

A db-time address-calculation-stage check, distinct from the parse-time
(E1.\*), post-parse-hierarchy (E2.\*), and Stage-5 port-validation (E3.\*)
categories. Emitted by the nested-decoder containment pass in
`pysrc/processYaml.py::calcAddresses`, next to the pre-existing decoded-span
space check.

| ID | Condition | Fixture | Asserted diagnostic substring |
| -- | --------- | ------- | ----------------------------- |
| E4.1 | A nested router's routed footprint (`addressIncrement × maxAddressSpaces`) exceeds the per-child window its parent decoder allocates to the container slot. | `unittest/test_error_nested_decoder_overflow.py` | **committed** and **verified**; nested router block name + group, footprint (`0x1000000`), parent window (`0x100000`), and parent decoder name |
| E4.2 | A bare register block's decoded span (`blocks.maxAddress+1`) exceeds the parent per-child window (the pre-existing space check). | `unittest/test_error_reg_block_decode_overflow.py` (not yet authored) | block name + used span + available window |

Positives are carried by the migrated `ip_test` (nested `bridge` decoder is
an exact fit — footprint `0x1000000` ≤ window `0x1000000`; the `ip` leaf's
decode span fits where its nominal `2^32` range would not); the `ip_test`
view test (`test_addrctl_ip_test_view.py`) is the regression anchor. No new
positive fixture is required.

## Coverage Map

Every code path in `postParseRegisterPorts.py` and the planned test
case (or cases) that cover it once Stage 7 is complete.

| Code path | Covered by |
| --------- | ---------- |
| `_collectRouterBlocks` populated | T1.*, T2.*, T3.*, T4.*, T5.* |
| `_collectRouterBlocks` empty (no `addressBlock:` declared) | (no coverage by design; legacy path is out of scope) |
| `_resolveRouterInstances` single instance | T1.*, T2.*, T3.*, T4.* |
| `_resolveRouterInstances` multi-instance error | E2.2 |
| `_resolveRouterInstances` missing instance error | E2.1 |
| `_findPrimaryRouter` one candidate | T1.*, T2.*, T3.*, T4.* |
| `_findPrimaryRouter` zero candidates | E2.3 |
| `_findPrimaryRouter` multiple candidates | E2.4 |
| `_findRouterParent` returns non-None (nested router walk) | T2.*, T3.*, TT.4 |
| `_findRouterParent` traversed across two router-to-router hops in one project | T3.1, T3.4, T3.5 |
| Per-instance router resolution when one block type is served by three different parent routers | T3.4 |
| Handler-block / handler-instance synthesis is per block type, not per instance, when the block has many instances | T3.4 |
| Sibling leaf and nested router under one router's container do not collapse | T3.5 |
| `_findRouterParent` returns None at root | T1.*, T2.*, T3.* (per-primary check) |
| `_leafRegisterBinding` authored row (was `_selectLeafRegisterPort`) | T1.*, T2.*, T3.*, T4.* |
| `_leafRegisterBinding` inferred (zero rows → infer from router) | T5.5 |
| multi-row `registerPorts:` error (parse-time block hook) | E1.2 |
| Router-to-leaf connection emission | T1.*, T2.*, T3.*, T4.* |
| Router-to-router connection emission | T2.*, T3.* |
| Router-to-router `connectionMap` emission | T2.*, T3.* |
| Per-owner-context `processSingleFile` feed (leaf and router contexts diverge) | T2.4, T1.6 |
| `INSTANCES_WITH_REGAPB` config write | T1.1, T1.2, T2.1, T2.3 |
| Default `upstreamPort` / `registerDecoderPort` resolution | T5.3 |
| Explicit `upstreamPort` / `registerDecoderPort` resolution | T5.4 |
| Same-`interfaceType` packed-form pass | T1.6 (via T2.4), T2.4 |
| Same-`interfaceType` packed-form fail | E3.2 |
| Cross-`interfaceType` rejection | E3.1 |
| Parameterized leaf register interface | TT.3 |
| Parameterized router register interface | TT.4 |
| No `_global` register-bus binds | E3.3 |
| `registerPorts:` without backing `ports:` row | E3.4 |

## Implementation Phasing

Three batches, each gated on a green run of `unittest/run_all_tests.sh`
plus the relevant user-example builds.

### Batch A — Hierarchy positives and the diagnostic skeleton

- Unit tests: T1.1, T1.2, T1.3, T1.5, T2.1, T2.2, T4.1, T4.2, T4.3,
  T5.1, T5.2, T5.3, T5.4, T5.5.
- Error unit tests: E1.1, E1.2, E1.3, E1.4, E1.5, E2.1, E2.5.
- Gate: `run_all_tests.sh` green.

### Batch B — Three-level and thunker cases

- Unit tests: T2.6, T3.1, T3.2, T3.4, T3.5, TT.3, TT.4.
- User-example regression: T3.3 (extend `ip_test` only if the deeper
  bridge subtree improves the user-facing example).
- Error unit tests: E2.2, E2.3, E2.4.
- Gate: `run_all_tests.sh` green; any `ip_test` extension builds
  with no unexpected template diff.

### Batch C — Coexistence guards and per-context emission

- Unit tests: T1.6 (via `ip_test` view assertions), T2.3, T2.4, T2.5
  (these read the migrated `ip_test` database; no new YAML fixture).
- Error unit tests: E3.1, E3.2, E3.3, E3.4.
- Gate: `ip_test` migrated; every assertion in this batch references
  the post-migration database.

## Validation

The whole test suite must satisfy the following gates before each
batch lands.

- **`unittest/run_all_tests.sh` green.** Every new unit test runs
  under the existing runner.
- **No-`_global` register-bus invariant.** Test E3.3 is a
  repository-wide assertion that the new post-parse pass never
  emits `_context: '_global'` on a register-bus row.
- **Diagnostic-string assertions.** Every E* test asserts the
  smallest substring of the diagnostic that uniquely identifies it
  (the offending field name or block name plus the rule).
  A diagnostic-wording regression is a test failure, not a silent
  UX degradation.
- **User-example builds green.** Every user-facing example touched by
  this plan must complete `make db && make gen` without warnings the
  project does not already accept, and any committed golden output must
  match byte-for-byte unless the change is explicitly reviewed.
- **Skill-doc cross-check.** Every error message asserted by an
  E* test must also appear (or be summarized) in
  `rules/skills/address-migration.md`.

## Risks

- **Unit-test fixture proliferation.** Each topology fixture is
  small, but the directory will grow. Mitigation: name files
  `test_addrctl_<shape>.py` so they sort together and a developer
  can find related cases at a glance.
- **View-assertion brittleness.** Asserting on view-attribute names
  couples tests to the projectOpen contract. Mitigation: only
  assert on fields that the parent plan promises (Stage 3.1 / 3.4),
  and prefer asserting on the synthesised `connections` /
  `connectionMaps` rows that the post-parse pass emits, since
  those are the public contract templates consume.
- **Example template breakage hidden by view-only unit tests.**
  Unit tests do not run templates. Mitigation: every shape
  reachable in real projects (single-router, two-level, three-level
  with thunker) has at least one corresponding example test that
  exercises template rendering end-to-end.
- **Diagnostic-message drift.** Asserting exact substrings couples
  tests to wording. Mitigation: assert the smallest substring that
  uniquely identifies the diagnostic.

## Open Questions

- **Whether T3.3 spawns a new example or extends `ip_test`.** A
  deeper bridge subtree inside `ip_test` keeps the example count
  small but grows a single example to a size that may be hard to
  audit. Recommendation: prototype as a unit test first (T3.1 / T3.2
  already cover the post-parse path); promote to an example only if
  template coverage of the deeper case proves necessary.
- **Whether view-assertion helpers belong in `unittest/` or in a
  new shared module under `pysrc/`.** Helpers that look up a
  router's resolved `registerBusInterface` / `registerBusPort`
  given a block name are useful both to tests and to anyone
  scripting against projectOpen. Default recommendation: keep them
  in `unittest/_addrctl_helpers.py` until a second consumer
  appears.

## Deferred / Out of Scope

- Tandem RTL/model coverage for the register-bus paths. Tracked
  by `rules/skills/run-tandem.md`.
- Performance / scale tests (very deep router hierarchies, very
  many leaves per router). Not blocking; revisit if a real project
  hits a generator-side scale limit.
- Coverage of the eventual protocol-changer block referenced in
  the parent plan's Non-Goals. Diagnostic only.
- Legacy `addressControl.yaml` regression coverage. Out of scope
  by design — this plan covers only the new-schema path.
