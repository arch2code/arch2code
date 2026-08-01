# Development Ordering Analysis: Modules + Parameterization

**Status (refreshed 2026-07-24):** historical ordering record plus owner index.
The selected Option 4 sequence is complete through reusable-IP composition
acceptance. Use `plan-116-status-report.md` for current open work and the
specialized owner plans for execution detail; older "next work" prose below is
retained only as history.

## Current Control State (refreshed 2026-07-24)

The broad 116 branch is no longer in the original "foundation before
modules/config" phase. Foundation, Path C variant/config unification,
exact-width Verilated wrappers, generated testbench variant selection,
and the address-control new-schema path have all moved into execution
records. The remaining work is cleanup, validation, migration, and a few
explicit deferred decisions.

### Completed / Current Baseline

| Area | Current state | Owning record |
|---|---|---|
| P0 prototypes | Complete. SystemC/C++ module and RTL proof-of-concept records are historical. | [`plan-p0-proof-of-concept.md`](./plan-p0-proof-of-concept.md), [`plan-p0-rtl-proof-of-concept.md`](./plan-p0-rtl-proof-of-concept.md) |
| Foundation F1-F3 / A1-A3 | Complete for current branch purposes. | [`plan-foundation-address-decode.md`](./plan-foundation-address-decode.md), [`plan-f2-f3-design.md`](./plan-f2-f3-design.md) |
| Variant/config Path C | Complete; Stages 1-11 are committed/verified. Only explicitly deferred decisions remain. | [`plan-variant-config-unification.md`](./plan-variant-config-unification.md) |
| C1-C3 parameterized declarations / SV emission | Complete; the C3.6 matrix is 11/11 PASS. | [`plan-param-constant-collision.md`](./plan-param-constant-collision.md) |
| C3.R register handler | Historical/executed C3.R slice; current status lives in the collision plan. | [`plan-parameterized-register-decode.md`](./plan-parameterized-register-decode.md) |
| Exact-width Verilated wrappers | Verified/complete in working tree. | [`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md) |
| Generated testbench variant selection | Complete on this branch. | [`plan-step-11-variant-aware-testbenches.md`](./plan-step-11-variant-aware-testbenches.md) |
| Address-control new schema | Complete (2026-06-22): Stages 1-6 complete, Stage 7 coverage complete, Stage 8 legacy retirement complete (2026-06-12). | [`plan-address-control-refactor.md`](./plan-address-control-refactor.md), [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md) |
| Config header/template cleanup | Implemented and verified; follow-ups assigned or historical. | [`plan-config-policy-views.md`](./plan-config-policy-views.md) |

### Work To Do Next

The recommended ordering is:

> **Refresh 2026-07-24.** Items 1-7 are complete or explicitly descoped and
> item 8's composition critical path is accepted. The numbered sequence below
> is historical; current residuals live in `plan-116-status-report.md`.

1. ~~**Finish the active YAML migration workstream.**~~ **DONE
   (2026-06-18/19).** `pysrc/migrateAddressControl.py`, the unified
   `migrateYaml.py` command, the `make migrate` wrapper, the
   `yamlFormat: 2` gate, scaffolding updates, and stamping of every
   in-tree project are all committed/verified. Owner:
   `plan-yaml-migration.md`.

2. ~~**Close address-control Stage 7 coverage.**~~ **DONE.** The Stage 7
   checklist in `plan-address-control-test-coverage.md` is fully committed
   (Topology A/B, Batch C migrated-`ip_test` DB assertions, error A/B,
   E3.1-E3.4, skill-doc cross-check).

3. ~~**Implement C3.6 static validation.**~~ **DONE (2026-06-23; 11/11 PASS).**
   Add the positive/negative parser validation matrix for
   parameterized/non-parameterized parent, sub-block, interface, and
   channel combinations. This is distinct from C3.7 runtime cosim
   acceptance, which is already complete.

4. ~~**Finish or explicitly defer symbolic-eval follow-ups.**~~ **DONE.**
   `plan-eval-symbolic-emission.md` owns this. E4 is implemented; the
   SystemC side of E5 is implemented; firmware C emission remains
   deferred until a fixture/project exercises parameterizable
   eval-derived constants in firmware headers; E6 variant-aware address
   evaluation remains design/open if still in C4 scope.

5. ~~**Choose the registration encapsulation cleanup path.**~~ **DONE
   (2026-06-23).** Option delta landed and `force_link` is retired.

6. **Fix C++ module/template identity contracts.** **Complete.** Core work
   implemented in working tree (commit `1c09e53`, 2026-06-22): the trigger
   helpers `module_name_from_include()` / `namespace_name_from_include()` are
   removed; module/namespace/package identity is now spelled from
   `prj.includeName[context]` and the `getContextData` view fields
   `contextIncludeName` / `contextStem`. The residual WI6 is closed (descoped
   2026-06-23): the per-context `<context>DefaultConfig` name stays on the
   `contextStem` derivation because `blocks.defaultConfig` is keyed off a
   block's unpersisted `contexts[0]` and constant-only contexts have no block,
   so the column is not cleanly per-context-keyed; the only real defect (the
   template mapping `-` but not `.`) is fixed by aligning `config.py` to
   `calcBlockConfigInfo()`'s `.replace('-', '_').replace('.', '_')`. See
   `plan-cppm-include-contract-cleanup.md` (WI6).

7. ~~**Revisit address Stage 8 only after migration/coverage is stable.**~~
   **DONE (2026-06-12).** `config/postParseRegister.py` is deleted and the
   legacy `addressControl.yaml` loader is retired; the new schema is the
   only accepted input. See `plan-address-control-refactor.md` Stage 8.

8. **IP reuse and project composition (workstream, 2026-06-25).**
   Now **three** linked plans: relocate per-instance registration and
   config into a per-assembler `registrar/` directory
   ([`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md)),
   make each IP a standalone project a parent references
   ([`plan-ip-project-composition.md`](./plan-ip-project-composition.md)),
   and the `functional`/`hierarchical` layout axis
   ([`plan-decomp-functional-layout.md`](./plan-decomp-functional-layout.md)).

   > **Authoritative cross-plan ordering (implementation refreshed 2026-07-17
   > through committed HEAD `6113562`):**
   > [`plan-composition-ordering.md`](./plan-composition-ordering.md) is the
   > single index for the dependency chain, the single-owner-per-decision
   > map, the load-bearing config-canonicality invariant, and the
   > buildable-now-vs-gated table. Q-C10, C0a,
   > `CONTEXTOWNINGPROJECT`, `PROJECTLAYOUT`, the SystemC/SV generation skip
   > gates, registrar S1/S2/S3.2a, and the `blockBase` h→cppm flip have landed.
   > Registrar S3-H (parent-owned foreign Config header beside the registrar)
   > is decided and independently buildable. S3-M/S6 have **LANDED (committed
   > 2026-07-22, incl. F10 `vl_wrap` retirement)**; S5 LANDED this session
   > (staged) and S4 (clangd) confirmed landed — **registrar S0–S6 complete**.

   **Current state (2026-07-24):** C2/L2b, C5/L5, standalone and composed
   model/VL, cross-project clangd/compdb, provider acceptance, S3-H/S3-M/S5/S6,
   and wrapper P2 are closed. Registrar S0-S6 is complete. Q-C8 Role C/C2.5
   remains latent/deferred; C1 is a contract-document refresh. See the status
   report for migration and independent cleanup backlog.

### Owner Map For Open Work

| Workstream | Status | Owner |
|---|---|---|
| Unified YAML migration | DONE (2026-06-18/19) | [`plan-yaml-migration.md`](./plan-yaml-migration.md) |
| Address Stage 7 residual tests | DONE | [`plan-address-control-test-coverage.md`](./plan-address-control-test-coverage.md) |
| C3.6 static validation | DONE (11/11 PASS) | [`plan-param-constant-collision.md`](./plan-param-constant-collision.md) |
| Symbolic eval E5 firmware / E6 addressing | DONE / E6 descoped | [`plan-eval-symbolic-emission.md`](./plan-eval-symbolic-emission.md) |
| Registration encapsulation | DONE / committed (Option delta) | [`plan-registration-encapsulation-cleanup.md`](./plan-registration-encapsulation-cleanup.md) |
| C++ module identity cleanup | complete (commit `1c09e53` + 2026-06-23 WI6 descope) | [`plan-cppm-include-contract-cleanup.md`](./plan-cppm-include-contract-cleanup.md) |
| Address legacy-path retirement | DONE (2026-06-12) | [`plan-address-control-refactor.md`](./plan-address-control-refactor.md) |
| Reusable-IP registrar relocation | **S0–S2 + S3.1/S3.2a + `blockBase` h→cppm DONE**. **S3-H LANDED (committed 2026-07-21); composed `ip_test` builds/runs No error on a clean child-first rebuild.** **S3-M/S6 LANDED (committed 2026-07-22, incl. F10 `vl_wrap` retirement); S5 LANDED 2026-07-22 (staged) and S4 (clangd) confirmed landed — S0–S6 complete**. | [`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md) |
| IP project composition | DELIVERED / ACCEPTED. C1 contract refresh and latent Q-C8/C2.5 remain; Q-C12/G5 is deferred. | [`plan-ip-project-composition.md`](./plan-ip-project-composition.md) |
| Project layout mode (`functional`/`hierarchical`) | L1-L5 COMPLETE / ACCEPTED | [`plan-decomp-functional-layout.md`](./plan-decomp-functional-layout.md) |
| **Composition cross-plan index** | authoritative ordering / owner map / buildable-vs-gated for the three plans above | [`plan-composition-ordering.md`](./plan-composition-ordering.md) |

### Status Report

[`plan-116-status-report.md`](./plan-116-status-report.md) records the
one-time documentation cleanup and fact-checking pass. It is an audit
report, not the control document. Update this file first when ordering or
ownership changes; update the report only when a summarized status needs
to be preserved.

## Historical Option-4 Roadmap

The remainder of this document preserves the original analysis for
implementing C++ modules (namespace/scoping) and Config template
parameterization. The goal was to minimize duplicated work across
generator code and hand-written IP code. Some row-level status words below
come from older checkpoints and are not authoritative for current branch
status; use the control state above for current ordering.

## Progress

Selected path: **Option 4** (Foundation + Address -> Modules + Config Templates combined).

| ID | Status | Notes |
|----|--------|-------|
| **P0** | **done** | Both SystemC (V1–V8) and SV (R1–R4, R6) prototypes validated; conclusions copied to [`p0-conclusions.md`](./p0-conclusions.md). All deferred items closed (see [`p0-deferred-tasks.md`](./p0-deferred-tasks.md)). Option 4 confirmed; no fallback needed. |
| **F1** | **done** | Schema additions for `ipParameters`, `isParameterizable`, `maxBitwidth/maxValue` landed |
| **F2** | **done** | Transitive `isParameterizable` propagation implemented per [`plan-f2-f3-design.md`](./plan-f2-f3-design.md). |
| **F3** | **done** | Worst-case address sizing via `maxBitwidth` / `maxValue` implemented per [`plan-f2-f3-design.md`](./plan-f2-f3-design.md). |
| A1, A2, A3 | done | Address decode now uses locally scoped named constants; SystemC register sizing uses `maxBytes` where available. |
| M1-M5 | in progress | 2026-05-01 checkpoint: hard replacement path selected (`*Includes.h/.cpp` -> `.cppm`, not side-by-side). Dedicated `moduleScaffold` sections now own the generated `.cppm` module header scaffold; dependency imports remain in `headers`; content sections own complete exported namespace blocks. The generated module scaffold now also carries structure test harness sections in `include_cppmTemplate`. `ip_test` now regenerates and builds through the current make-based module flow. See [Checkpoint: Hard Replace Modules + Config Templates](#checkpoint-hard-replace-modules--config-templates). |
| T1-T8 | in progress | 2026-05-01 checkpoint: T1-T5 are implemented in generated `.cppm` context units for `ip_test`; T6/T7 have enough current implementation for the `ip_test` hard-replace build to pass. The structure test harness is now `Config`-templated in module mode and tests both parameterizable and fixed structs. T8 static validation remains open. |
| **T9** | **open** | Per-block trampoline registration with an active force-link path for pure non-templated SC blocks. Subsumes the resolution path for review items B1 and B2 (`review-cppm-config-template-findings.md`). The current self-registration pattern (`static registerBlock registerBlock_;` inside the templated block class) does not work for class templates: the static is declared but never defined, and the registration lambda hard-codes `ip<ipDefaultConfig>` regardless of `Config`. Resolution moves parameterized registration into generated per-block-per-project trampolines that directly emit `instanceFactory::registerBlock(...)` lambdas for each `(block, variant, Config, configTag)`. Pure non-templated SC blocks self-register from their own TU and are made reachable by active `force_link_<block>()` calls. |
| S1, S2 | partially unblocked | F1 done; S1 unblocked. S2 remains blocked on T7. |

Test base: new `ip_test` example project added to exercise the schema and serve as the migration target for subsequent steps.

## Checkpoint: Hard Replace Modules + Config Templates

Date: 2026-05-01

User decision: use **hard replacement** for M1, not side-by-side generation. Generated context include files are intended to become `.cppm` module interface units immediately, accepting that consumers must be migrated as part of the same work stream.

Current checkpoint state:

- Generation now creates `examples/ip_test/model/ipIncludes.cppm` and `examples/ip_test/model/ip_topIncludes.cppm` instead of `ipIncludes.h/.cpp` and `ip_topIncludes.h/.cpp`.
- `.cppm` files declare `--mode=module` at file level.
- The top-of-file module scaffold (`module;`, required global-module-fragment includes, and `export module <name>;`) is emitted inside `moduleScaffold --section=moduleHeader`.
- Cross-context module dependencies are emitted by the existing `headers` section as `import <module>;` plus `using namespace <module>_ns;`.
- Each generated content section emits a complete `export namespace <name>_ns { ... }` block in module mode.
- Parameterizable constants are omitted from generated C++ include/module contents.
- Parameterizable scalar types are emitted as `template<typename Config> using <type> = uint64_t`.
- Parameterizable structs are emitted as `template<typename Config> struct <name>` with `Config::` in `_bitWidth`, pack/unpack, and sc_pack/sc_unpack paths.
- `_packedSt` for parameterizable structs uses worst-case `maxBitwidth` sizing; single-word parameterizable structs use `uint64_t`, multi-word structs use `uint64_t[N]`.
- Struct implementations for module mode are inline/header-only inside the `.cppm` unit.
- The generated structure test harness is present in `.cppm` module units through `structures --section=testStructsHeader` and `structures --section=testStructsCPP` sections.
- In module mode, the structure test harness is `template<typename Config> class test_<context>_structs`; it emits parameterizable structure references as `<Struct><Config>` and fixed structure references as `<Struct>`.
- Legacy non-module structure test generation keeps the previous behavior of skipping parameterizable structs.
- `examples/ip_test/tb/ip_top/ip_topConfig.cpp` calls `test_ip_structs<ipDefaultConfig>::test()` and includes `ipConfig.h` so the default Config is visible.
- `make gen` in `examples/ip_test` completes after regenerating from the current checkpoint state.
- `make clean && make` in `examples/ip_test/rundir` completes with the current make-based C++ module flow.
- `make run` in `examples/ip_test/rundir` reaches and prints `Running test_ip_structs`; it then fails at the known factory-registration issue rather than in structure tests.

Known incomplete areas:

- Broader project coverage beyond `examples/ip_test` is not yet proven. `ip_test` is build-complete in the current checkpoint, but the hard-replace flow still needs validation on other examples/projects.
- T6/T7 have enough implementation for `ip_test` to build, but the intended final API and cross-project coverage still need review before marking the work items done.
- T9 (per-block trampoline registration) is not implemented. The existing in-class `registerBlock_` static is structurally incompatible with class templates and is the root cause of review items B1 and B2. Resolution requires generated trampoline TUs so the IP block file stays text-stable and the registration lambda can be parameterized on the project's chosen `Config` without exposing child class definitions to parent containers. Pure non-templated SC blocks keep self-registration, with active `force_link_<block>()` calls to guarantee reachability. See [`review-cppm-config-template-findings.md`](./review-cppm-config-template-findings.md) B1, B2.
- `make run` currently fails after structure tests at `Attempted to create an instance ip_top of an unregistered block type ip_top_model`, which is consistent with the T9/B1/B2 factory-registration gap and is not a structure-harness failure.
- M4 has a working make-based path for `ip_test` (`.cppm` precompile, PCM-to-object compilation, and `-fmodule-file=` flags), but this remains bounded checkpoint validation rather than final build-system cleanup.
- `make reset` removed tracked `ip_test` support scaffolding that `make newmodule` does not recreate (`rtl/Makefile`, `rtl/rtl.f`, several `verif/*` support files). These deletions are checkpoint artifacts, not an intentional final cleanup.

Files with meaningful generator changes at this checkpoint:

- `config/project.yaml`
- `pysrc/newProject.py`
- `include/make/a2c-common.mk`
- `pysrc/intf_gen_utils.py`
- `templates/fileGen/fileGen.py`
- `templates/systemc/includes.py`
- `templates/systemc/structures.py`
- `templates/systemc/headers.py`
- `templates/systemc/moduleScaffold.py`
- `templates/systemc/baseClassDecl.py`
- `templates/systemc/classDecl.py`
- `templates/systemc/blockRegs.py`
- `examples/ip_test/model/ipIncludes.cppm`
- `examples/ip_test/tb/ip_top/ip_topConfig.cpp`

Verification performed:

- `python3 -m py_compile templates/systemc/structures.py templates/fileGen/fileGen.py templates/systemc/moduleScaffold.py` passed.
- `make db` was run from `builder/base/examples/ip_test` and was up to date.
- `make gen` was run from `builder/base/examples/ip_test` and regenerated `model/ipIncludes.cppm` from the current markers.
- `make` was run from `builder/base/examples/ip_test/rundir` and completed successfully.
- `make run` was run from `builder/base/examples/ip_test/rundir`; it printed `Running test_ip_structs` and then failed at the known T9/B1/B2 factory-registration issue.

Continuation prompt: [`prompt-continue-hard-replace-m3-t6.md`](./prompt-continue-hard-replace-m3-t6.md).

## Related Plans

| Plan | Scope |
|------|-------|
| `plan-ip-namespaces-and-parameterization.md` | High-level plan covering namespaces, parameterization, C++ modules, address decode, IP packaging |
| `plan-parameterizable-config-template.md` | Detailed plan for Config policy template + P1 symbolic foundation (the recommended approach) |
| `plan-parameterizableTypesAndStructs.prompt.md` | Earlier P1-only plan (superseded by config-template plan) |

## Work Items and Dependencies

### Atomic Work Items

| ID | Work Item | Touches (generators) | Touches (hand-written) |
|----|-----------|---------------------|----------------------|
| **P0** | Prototype: SC_MODULE + templates + modules | none (throwaway) | none |
| **F1** | Schema: `ipParameters`, `isParameterizable`, `maxBitwidth/maxValue` | `schema.yaml` | none |
| **F2** | processYaml: transitive propagation of `isParameterizable` | `processYaml.py` | none |
| **F3** | processYaml: worst-case address sizing via `maxBitwidth` | `processYaml.py` | none |
| **M1** | File format: `*Includes.h` to `.cppm` module interface units | `fileGen.py`, `systemcGen.py` | none |
| **M2** | Content wrapping: `export module X; export namespace X { ... }` | `includes.py`, `structures.py` | none |
| **M3** | Consumer side: `#include` to `import` + `using namespace` | `fileGen.py`, `constructor.py` | **all IP .h/.cpp** |
| **M4** | Build system: module dependency scanning | `Makefile` / CMake | none |
| **M5** | SystemC global module fragment: `module; #include "systemc.h"` | `includes.py`, `fileGen.py` | none |
| **T1** | Parameterizable constants: omit from IP includes, live in Config | `includes.py` | none |
| **T2** | Parameterizable types: `template<typename Config> using X = uint64_t` | `includes.py`, `systemcGen.py` | none |
| **T3** | Parameterizable structs: `template<typename Config> struct X` | `structures.py` | none |
| **T4** | `Config::` prefix on `_bitWidth`, pack/unpack, masks/shifts | `structures.py` | none |
| **T5** | `_packedSt` via `maxBitwidth`, header-only for template structs | `structures.py` | none |
| **T6** | Block/base class: `template<typename Config>` | `fileGen.py`, `constructor.py` | **all IP block .h/.cpp** |
| **T7** | Config struct generation per instance | new generator | none |
| **T8** | `static_assert` validation of maxBitwidth/maxValue | `includes.py` or new | none |
| **T9** | Block registration: per-block trampolines for parameterized / verilated registrations plus active force-link for pure non-templated self-registration | `classDecl.py`, `constructor.py`, `module_hdl_wrapper.py`, new registrar support/trampoline generator, `fileGen.py`, factory call-site templates | none (IP block files stay text-stable) |
| **A1** | Named constants for address offsets in SC decode | `blockRegs.py`, `constructor.py` | none |
| **A2** | Named constants for address offsets in SV decode | `moduleRegs.py` | none |
| **A3** | `hwRegister<N>` worst-case sizing | `blockRegs.py` | none |
| **S1** | SV: omit parameterizable constants from IP package | `package.py` | none |
| **S2** | SV: per-instance package generation | new generator | none |

### Hard Dependencies

```
P0 ──validates──> M1-M5, T1-T8

F1 -> F2 -> F3
F1 -> T1, T2, T3, T4
F2 -> T3, T4 (need to know what's parameterizable)
F3 -> A1, A2, A3

M1 -> M2 -> M3 (file format before wrapping before consumer changes)
M5 depends on M1

T1 -> T7 (constants move to Config, so Config must exist)
T2 -> T3 -> T4 -> T5 (build up from types to structs to expressions)
T3 -> T6 (structs templated before blocks that use them)
T6 -> T9 (block must be templated before registration can be Config-aware)
T7 -> T9 (registrar passes Config type, so Config struct must exist)

A1, A2 independent of M* and T* (just referencing named constants)
S1 depends on F1
S2 depends on T7
```

### T9 design intent

- IP block files (`<block>.h`, `<block>.cpp`) must remain text-stable across project Config changes. No `template<...> typename ip<Config>::registerBlock ip<Config>::registerBlock_;` definitions or per-Config explicit instantiations get added inside the IP TU.
- A generated per-block-per-project trampoline is the only TU that needs both the child class definition and the project-selected Config type. Parent containers continue to see only `<child>Base.h`.
- Generator surface: replace the in-class `struct registerBlock { ... }; static registerBlock registerBlock_;` pattern. Parameterized blocks get direct `instanceFactory::registerBlock(...)` lambdas in the trampoline, keyed by `(blockType, variant, configTag)`. Pure non-templated SC blocks get a non-templated helper / self-registering static plus generated active `force_link_<block>()` calls at factory lookup sites.
- Verilated wrapper registration is also trampoline-owned for `hasVl` blocks, including non-Config wrappers, so wrapper-local `registerBlock_` emission is removed.
- Side benefit: today's lambda hard-codes `make_shared<ip<ipDefaultConfig>>(...)` even inside `ip<Config>::registerBlock`, which is a latent bug for any non-default Config. The trampoline lambda names the selected `Config` directly and removes that special case.
- Detailed design is in [`plan-block-registration.md`](./plan-block-registration.md). Stage 0 C++ mechanics are prototyped by `make -C ../../proto/model step6`.

## Where Duplication Actually Lives

The generators have **low duplication risk** -- modules changes affect file-level structure (wrapping, import/export), while Config template changes affect content-level logic (template declarations, `Config::` prefixes, `uint64_t` forcing). They touch the same files (`includes.py`, `structures.py`) but at different layers. Doing one doesn't invalidate the other.

The real duplication risk is in **hand-written IP code migration**:

| If you do... | Hand-written changes |
|--------------|---------------------|
| M3 then T6 | Pass 1: `#include` to `import`, add `using namespace` everywhere. Pass 2: `pixel_t` to `pixel_t<Config>`, `BITS` to `Config::BITS`, block classes gain `template<typename Config>` |
| T6 then M3 | Pass 1: template changes. Pass 2: import changes |
| M3 + T6 together | Single pass: all changes at once |

Two passes through hand-written code isn't catastrophic (they're different edits), but combining them avoids touching every file twice.

## Ordering Options

### Option 1: Foundation -> Modules -> Config Templates

```
P0: Prototype (validate both)
 |
 +-> F1 -> F2 -> F3          (schema + propagation + worst-case sizing)
 |     |
 |     +-> A1, A2, A3        (address decode, parallel with M*)
 |
 +-> M1 -> M5 -> M2 -> M3    (modules infrastructure)
 |     |
 |     +-> M4                 (build system, parallel with M2/M3)
 |
 +-> (after M2 done)
       T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8
                                              |
                                              +-> S1, S2
```

| Pro | Con |
|-----|-----|
| `Config::` expressions naturally live inside `export namespace` from day one | Modules is a large infrastructure change before any parameterization value is delivered |
| `template<typename Config>` structs are emitted into module interface units directly | Two hand-written migration passes (M3 then T6) unless deferred together |
| Module validation failures surface early | Longer time to first parameterizable IP |

**Duplication**: Low in generators. Two passes on hand-written code (can be mitigated by deferring M3 hand-written migration until T6 is also ready).

### Option 2: Foundation -> Config Templates -> Modules

```
P0: Prototype (validate both)
 |
 +-> F1 -> F2 -> F3
 |     |
 |     +-> A1, A2, A3
 |
 +-> T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8
       |                              |
       |                              +-> S1, S2
       |
       +-> (after T5 done)
             M1 -> M5 -> M2 -> M3 -> M4
```

| Pro | Con |
|-----|-----|
| Parameterization delivered sooner (more urgent capability) | Template struct methods go header-only in `.h` first, then those headers become `.cppm` |
| Config template patterns validated on simpler header-based build first | `export namespace` wrapping must handle both template and non-template structs |

**Duplication**: Low in generators. The template content emitted into `.h` files transfers directly into `.cppm` module interface units. The `codeMapping` move from `split` to `inline` (T5) actually makes the modules migration easier since header-only content maps cleanly to module interface units.

### Option 3: Foundation -> Modules + Config Templates Together

```
P0: Prototype (validate both together -- required)
 |
 +-> F1 -> F2 -> F3
 |     |
 |     +-> A1, A2, A3
 |
 +-> [M1+M5+M2 + T1+T2+T3+T4+T5] -> [M3+T6] -> [M4+T7+T8+S1+S2]
     (generators in one pass)      (hand-written   (additive
                                    migration once)  outputs)
```

| Pro | Con |
|-----|-----|
| Zero duplication -- generators touched once, hand-written code migrated once | Largest single change -- harder to review, test, bisect |
| Conceptually cleanest target form written directly | Requires both prototypes validated before starting |
| Single migration tool handles both changes | If either feature hits a problem, the combined change is blocked |

**Duplication**: None. Minimum-work option if both features are going in.

### Option 4: Foundation + Address -> Modules + Config Templates (Recommended)

```
P0: Prototype (validate both)
 |
 +-> F1 -> F2 -> F3 -> A1 + A2 + A3
 |
 +-> [M1+M5+M2 + T1+T2+T3+T4+T5] -> [M3+T6] -> [M4+T7+T8+S1+S2]
```

| Pro | Con |
|-----|-----|
| All Option 3 benefits | All Option 3 risks |
| Address decode is a clean, low-risk deliverable first | Address decode depends on F3 which depends on F1+F2 |
| Validates `maxBitwidth` infrastructure end-to-end before big change | |

## Recommendation

**Option 4** minimizes duplication while managing risk:

1. **P0** validates modules and templates *together* since the target form is a templated struct inside a module interface unit with SystemC. Non-negotiable prerequisite.

2. **F1+F2+F3 -> A1+A2+A3** is safe, additive, independent work. Delivers schema infrastructure, validates `maxBitwidth`/`maxValue` propagation, and cleans up address decode without touching hand-written code.

3. **M\*+T\* combined** edits each generator once and migrates hand-written code once.

**Fallback**: If P0 reveals problems with modules that require significant iteration (e.g., SystemC macro incompatibilities), fall back to **Option 2** -- get Config templates working on headers, then migrate to modules once toolchain issues are resolved. The template content won't need to change; only file-level wrapping gets added.
