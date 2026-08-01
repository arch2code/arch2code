# Cross-Plan Index: IP Composition Workstream

**Authoritative ordering + ownership index for the composition workstream
(status reconciled 2026-07-24).**
This file is the single place that states the linear
dependency chain, who owns each cross-cutting decision, and what is
buildable on monolithic `ip_test` today versus gated on the project split.
The owner plans hold the detailed execution logs; this file decides
the next work item and resolves the tensions between them.

Created 2026-07-06 (reconciliation pass). The composition critical path is now
retired: C2/L2b, C5/L5, registrar S0-S6, standalone/composed model+VL,
cross-project clangd/compdb, and wrapper P2 are accepted. C1 remains a
contract-document refresh; Q-C8 Role C/C2.5, Q-C12/G5, Option-D collision
hardening, and wrapper Gaps 1/3/4 are deferred.
This index supplements the broader
[`plan-development-ordering.md`](./plan-development-ordering.md) item 8; that
file remains the branch-wide control document.

**LANDED 2026-07-17 (composition arc); foreign-Config S3-H LANDED 2026-07-21.**
The composed multi-project `examples/ip_test` reports `No error` in the ordinary
flow, and the tested base+pro suite is otherwise green (pre-existing `pySocket`
deferral excluded). A clean child-first regeneration now builds and runs `No
error`; registrar S3-H (parent-owned foreign per-variant Config header) fixed
the earlier `ipVariant1Config` blocker, so this green no longer depends on a
stale child Config. What landed:
- **`cpu` duplicate-basename clobber RESOLVED** — `cpu` is now a single
  `common`-owned generic APB master (running firmware via the lmmiDemo
  `workerBase`/`workerFactory` pattern on the BSP `regRead32`/`regWrite32`
  seam); the duplicate per-parent `cpu` blocks were removed, so the clobber is
  gone by de-duplication (Option R). Commit `ab75e9c`.
- **Definitions-only project can own a `hasMdl` block it never instantiates** —
  `validateDeclaredPorts` scoped to instantiated blocks (`91b69dc`); zero-
  instance boundary ports synthesized from the definition in
  `getBlockData`/`getBDDefinitionPorts` (`ab75e9c`, unittest
  `test_zero_instance_ported_block.py`).
- **Cross-project PLAIN-block registration ("Option B")** — a container emits
  each plain cross-project child's OWNING `projectName` in `createInstance`
  (derived `createInstanceProjectName` in the `projectOpen` view, emitted by
  `constructor.py`/`testbench.py`); parameterizable children stay
  assembler-scoped. Commit `4038204` ("make instance creation respect project").
- **BSP register-access code relocated pro→base** at `common/systemc/bsp/`
  (`regRdWr`/`modelComm`/`fwlog`) as a dir-level real-HW replacement point; one
  `A2C_SRC_DIRS` token. Commit `6791451`.
- **`bridgeDriver` stimulus relocated** out of reusable `ipBridge.yaml` into the
  bridge's own `bridgeStdTop` harness; `ip_top` drives `uBridge` from `uSrc`.
  Owner-aware cross-project RTL directories now feed `rtl.f`. Commit `6bbec76`.
- **VL wrapper Makefiles consume the DB manifest** through
  `VL_SRC_DIRS = $(A2C_VL_WRAP_DIRS)` instead of a fixed local wrapper directory.
  Commit `6113562`; end-to-end VL validation remains active work.

**Reconciled 2026-07-24:** the `projectFiles:`-only lookup is closed
will-not-implement; explicit managed SV selection, VL/clangd, scaffold
ownership, and provider acceptance are closed. The historical blocker sequence
below is retained for provenance.

**Standalone `ipBridge` model run is RUNNABLE (2026-07-17).** `bridgeStdTop` was
flipped to `hasTb: true` and wrapped in a thin `bridgeStdTop_tb` container
(mirrors `ip_top`/`ip_top_tb`, empty External via `--excludeInst`); end-of-test
is data-driven from `bridgeDriver` (`push_ack` completion proves the full bridge
path). The bridge closure now declares `ip@variant1` in its own YAML (required to
build `uBridgeIp1`; the per-assembler foreign-variant declaration the cross-level
plan calls for). Standalone-only fixture edits; `bridgeDriver` is not in composed
`ip_top`. Two gaps surfaced and are PARKED (architect decision 2026-07-17): (1) a
clean composed-root rebuild now FAILS on `bridge/registrar/bridge/ipRegistrar.cppm`
→ `use of undeclared identifier 'ipVariant1Config'` — the documented
Config-ownership blocker, now hitting the FIXTURE registrar (not just wrapper P2),
because a clean regen of the child-context `ip/model/ip/ipVariantConfig.h` omits
`variant1` (reshaped up to `ip_top`/`bridge`); the shared symlinked header is
last-writer-wins across projects. **DECIDED (2026-07-20):** fix the SC blocker
as registrar S3-H, an owner-qualified plain Config header beside the
parent-owned registrar, independent of S6/S5 — see
[`proposal-config-ownership-header-relocation.md`](./proposal-config-ownership-header-relocation.md)
(LANDED 2026-07-21). The later registrar-module export (S3-M) and verilated
relocation (S6/F10) have since LANDED (committed 2026-07-22), and standalone
testability (S5) LANDED this session (staged) — registrar S0–S6 complete. (2) `make
newmodule` in the bridge rundir errored in its trailing `compdb`/VL-wrap step
(`a2c-vl-wrap.mk:55` duplicate target, missing `vl_wrap/vl_wrap.o` rule) — the
F10 `vl_wrap` retirement removes that dependency; did not affect the model-only
goal. The parameterizable registrar
still re-registers under the assembler (its same-name cross-project collision
hazard is pre-existing / out of scope — see the Q-C8 note in
[`proposal-qc8-identity-field.md`](./proposal-qc8-identity-field.md)).

## Owner plans

| Plan | Role | State |
|---|---|---|
| [`plan-ip-project-composition.md`](./plan-ip-project-composition.md) | **FOUNDATION** — project reference, factory/config boundary, generation ownership, composed manifest, and canonical `ip_test` fixture. | Q-C10, C0a ownership truth, `PROJECTLAYOUT`, and the DB-driven generation gate have landed. **Composed model build/run is GREEN as of 2026-07-17.** Cross-project SC/RTL/VL path discovery has landed through `6bbec76`/`6113562`. **UPDATE 2026-07-22 — C5 composition acceptance PASSED** (byte-identical parent address map G3/Q-C5 PASS with the recorded caveat; fwIpMain Q-C11/G4, provider-override negative, `projectName`-keyed registration, and distinct-type thunkers PASS; Q-C12/G5 DEFERRED). Q-C8 Role C stays LATENT/DEFERRED. |
| [`plan-cross-project-block-resolution.md`](./plan-cross-project-block-resolution.md) | **COMPLETE for the selected-provider contract.** | The `projectFiles:`-only fallback is closed will-not-implement; strict scaffold ownership and provider negative-path acceptance are landed. |
| [`plan-cross-project-shared-definitions.md`](./plan-cross-project-shared-definitions.md) | **IDENTITY/PROVIDER CONTRACT** — Options R/D, D→R migration, hierarchical `projectOverrides`, owner-qualified names, explicit managed SV files. | Decisions D-SD1–D-SD8 settled 2026-07-10; implementation open where noted. |
| [`plan-decomp-functional-layout.md`](./plan-decomp-functional-layout.md) | **DIRECTORY AXIS** — `functional` vs `hierarchical` layout selector, the single path seam, the DB build manifest, opt-in migration. | L1 + L2a + L3 + **L4 COMPLETE**. **UPDATE 2026-07-22 — L2b/C2 CLOSED/ACCEPTED** (composed SC paths, owner-aware RTL paths, VL manifest consumption, explicit SV lists via S6 file->top records, clangd via S4, full VL all landed) and **L5 full nested acceptance PASSED/ACCEPTED** on the split `ip`/`ipBridge`/`common` fixture (standalone + composed model/VL all `No error`; evidence checks all PASS; no gaps). |
| [`plan-reusable-ip-registrar.md`](./plan-reusable-ip-registrar.md) | **PER-ASSEMBLER TRAMPOLINE + config/verilated relocation.** | **S0-S6 COMPLETE.** S5 is committed as `a50f12c`; downstream P2 and standalone compdb acceptance are closed. |
| [`plan-cross-level-variant-wrappers.md`](./plan-cross-level-variant-wrappers.md) | **FOREIGN-VARIANT WRAPPER CONTRACT** — immediate-assembler ownership of concrete SV tops and the wrapper-emission/view contract; registrar owns Config and registration mechanics. | **UPDATE 2026-07-22 — DONE (proven; "Proof only" completion bar, architect decision 2026-07-22).** P2 was already delivered by the S3-H/S3-M/S6/S5 landings; acceptance proof run added `run-vl-ip1` (root) and `run-vl-uBridgeIp1` (nested) `--vlInst` targets, both binding the parent-context-prefixed variant1 tops (70-bit payload) and reaching `No error`, with the 13/13-wrapper byte-identity guard PASS. Gaps 1/3/4 (projectCreate negative-declaration-ownership validation, fixture ownership reconciliation, consolidated projectOpen view) DEFERRED as hardening/hygiene. |
| [`proposal-qc8-identity-field.md`](./proposal-qc8-identity-field.md) | **Q-C8 IMPLEMENTATION RECORD** — absolute owner-qualified C++/SV identity and generated-name collision validation. | C++ Role A partial; SV Role C **LATENT/DEFERRED**; interim uniqueness gate LANDED 2026-07-21. |
| [`plan-ip-namespaces-and-parameterization.md`](./plan-ip-namespaces-and-parameterization.md) | **DEFERRED YAML NAMESPACE DESIGN** — authored namespace/import semantics, distinct from composition linkage identity. | Not on the M-split critical path. |

## The Load-Bearing Invariant (encode identically in dependent plans)

> **Config is canonical per `(block, variant)` WITHIN a project;
> parent-ownership of per-variant config manifests only ACROSS projects,
> via `projectName`.**

Mechanics, proven by inspection of the current code:

- `instanceFactory::registerBlock` does `getMap().emplace(Key{blockType,
  variant, projectName}, fn)`—`std::map::emplace` is **first-wins** only
  within one assembler-qualified key.
- The container does
  `dynamic_pointer_cast<<child>Base<Config>>(createInstance(...))`
  (`constructor.py`, generated e.g. `ip_top.cpp` → `ipBase<ipVariant0Config>`);
  under `VL_DUT` the factory returns the leaf-shared verilated wrapper
  (`<block>_hdl_sc_wrapper<DUT,Config> : public <child>Base<Config>`), so the
  container's `Config` and the wrapper's `Config` must be the **same C++
  type**.
- A C++20 **module-exported** struct is a **distinct entity** from the
  same-named header struct. So relocating only the container's config into a
  registrar module (S3) makes the cast return null and breaks plain
  `make run` / `run-vl-ip0`.
- Therefore per-parent-**distinct** config *types* are correct **only when
  the parents are distinct projects** (distinct `projectName`, which
  namespaces the config type — Q-C8). On monolithic `ip_test`, `ip_top` and
  `ipBridge` share `projectName=ip_test`, collide on `(ip, variant0,
  ip_test)`, and the shared container cast forces **one canonical config**.

**Consequence.** Within a project, `(block, variant) → exactly one Config`,
and registration is idempotent first-wins (the accepted-duplication case:
`ip_top` containing `ipBridge`, both instancing `ip@variant0`). A parent
that needs different config *values* under one variant name must be a
distinct project; the `projectName` factory key (Q-C10) plus
`projectName`-based IP-qualified naming (Q-C8) are what make that safe.

## Linear Dependency Chain

```
landed foundation + green composed model run
  (Q-C10 + ownership + reachability + SC/RTL paths + generation gates)
        │
        ▼
C2 / L2b acceptance
  (explicit managed SV + VL + clangd)
        │
        ├─────────────── runnable ipBridge (provider acceptance DONE, 37bad48)
        ├─────────────── Q-C8 absolute identity / SV Role C
        │
        ▼
C5 / Milestone M-split
        │
        ▼
layout L5 → registrar S5  (S3-M / S6 / S5 LANDED 2026-07-22)
```

**UPDATE 2026-07-22 — critical path retired.** C2/L2b are CLOSED/ACCEPTED, C5
composition acceptance PASSED (byte-identical parent address map with the
recorded caveat; Q-C12/G5 DEFERRED), L5 full nested composition acceptance
PASSED, and cross-level wrapper P2 is DONE (proven; "Proof only" bar, Gaps 1/3/4
deferred). Registrar S3-M/S6/S5 LANDED 2026-07-22 (registrar S0–S6 complete).
The historical wording below is retained for the record.

**Current critical path (historical):** complete C2/L2b discovery and acceptance (explicit
managed SV files, VL and clangd) and establish a runnable standalone `ipBridge`;
provider-override acceptance is DONE (committed 37bad48 +
test_provider_override.py green). Complete Q-C8/SV identity in parallel,
then close C5/M-split → L5 → registrar S5 (S3-M/S6/S5 LANDED 2026-07-22; registrar S0–S6 complete). S3-H LANDED (committed
2026-07-21) and fixed the clean SC rebuild blocker. Q-C10, C0a,
authoritative ownership, router reachability, `PROJECTLAYOUT`, owner-aware
SC/RTL paths, and the SystemC/SV generation skip gates are landed and must not
be redone. The optional `projectFiles:`-only block-lookup contract remains a
separate unresolved design residual; it is no longer the composed-run blocker.

## Single Owner Per Cross-Cutting Decision

Each decision has exactly **one contract owner**. A separate implementation
record may execute that contract; other plans should point to those owners
rather than restating the decision.

| Decision | Owner |
|---|---|
| Determinism rule (`(block,variant)→one config`) | **composition** (Q-C10) |
| `projectName` scoping + factory key `Key{blockType, variant, projectName}` | **composition** (Q-C10) |
| Config-across-boundary rule (parent-owned across projects) | **composition** (Q-C4) |
| Per-variant Config semantic identity `(projectName, block, variant)` | **composition** (Q-C10; `projectName` via `CONTEXTOWNINGPROJECT`) — NOT `CONTEXTMODULEIDENTITY` |
| Per-variant Config C++ spelling + generated-name uniqueness | **shared definitions** (D-SD4/D-SD6) + [`proposal-qc8-identity-field.md`](./proposal-qc8-identity-field.md) impl; helper `cpp_variant_config_name` in `intf_gen_utils.py` |
| Linkage identity and `projectName_localName` spelling, including SV Role C | **shared definitions** owns contract (D-SD4/D-SD6); [`proposal-qc8-identity-field.md`](./proposal-qc8-identity-field.md) owns implementation |
| YAML namespace/import semantics | `plan-ip-namespaces-and-parameterization.md` |
| Option R / Option D and explicit D→R migration | **shared definitions** (D-SD1/D-SD5) |
| Hierarchical physical-provider selection; no content dedup | **shared definitions** (D-SD3); `readRaw` implementation in block resolution |
| Explicit file lists for managed SV; user/fixed-library `-y` | **shared definitions** (D-SD2/D-SD7) |
| SystemC thunk at distinct-type crossings; packed RTL direct | **shared definitions** (Option D) |
| Generation-ownership gate + per-project `PROJECTLAYOUT` | **composition** (Q-C9/G2) |
| Cross-project module discovery + PCM target ownership | **composition** (Q-C3/C2); layout owns the single-project `.gen/build.mk` seam |
| Boundary artifact contract (`Base` module/header + parent-owned Config) | **composition** (C1) |
| Foreign-child variant wrapper selection/emission and immediate-assembler ownership | **cross-level variant wrappers** (Direction A/P2); Config/registration mechanics remain registrar S3-H/S3-M/S6 |
| Cross-project clangd confirmation | **composition** (C3) |
| Address-space composition proof | **composition** (C4/Q-C5) |
| The unblocking milestone (M-split) | **composition** |
| Canonical `ip` and `ipBridge` standalone harness contract | **composition** (C5); config/trampoline mechanics in registrar S5/S6 |
| `functional`/`hierarchical` layout selector + path seam | **layout** (L1) |
| DB build manifest (`.gen/build.mk`) | **layout** (L2a) |
| Opt-in layout migration | **layout** (L4) |
| Registrar module structure (parent-qualified `.cppm`) | **registrar** (S2/S3.2a, Q2) |
| The `ext` flips (`blockBase` h→cppm, `blockRegistrar` cpp→cppm) | **registrar** |
| Config / verilated relocation *mechanics* | **registrar** (S3-H/S3-M/S6) |
| Registrar clangd include coverage | **registrar** (S4) |

## Buildable on Monolithic `ip_test` NOW vs Gated on the Split

| Work item | Owner | Status | Blocked by |
|---|---|---|---|
| S0 linkage proof | registrar | **DONE** | — |
| Registrar S1/S2 (trampoline relocation, anchor removal) | registrar | **DONE** | — |
| Registrar S3.1/S3.2a (registrar = parent-qualified `.cppm` module; config canonical in header) | registrar | **DONE** (monolithic checkpoint; gate green) | — |
| Layout L1/L2a/L3/L4 | layout | **DONE** | — |
| `blockBase` h→cppm ext flip | registrar | **LANDED** (validated example set green; documented exclusions remain) | — |
| Q-C8 Role C owner-qualified naming | Q-C8 proposal | **LATENT/DEFERRED; interim uniqueness gate LANDED 2026-07-21** (C++ Role A landed; seam `contextModuleIdentity` exists bare-stem; Absolute `{owningProject}_{stem}` is the settled rule if landed; no collision in current fixture) | not active — Role C lands only on a real cross-project same-stem collision |
| **Q-C10 `projectName` factory key (implement)** | composition | **DONE** (implemented & validated; delegating-overload removal DONE 2026-07-08 — 5 non-projectName overloads dropped, full-suite gen/build/run `No error`) | **the unblocker — landed** |
| Composition C0a (ownership truth) | composition | **DONE** — `CONTEXTOWNINGPROJECT`, child-project detection, `PROJECTLAYOUT`, owner-relative expansion, and SystemC/SV generation skip gates are in source. `--project` emission was intentionally replaced by the DB-driven gate. | — |
| Composition Q-C9 (ownership gate) | composition / block resolution | **LANDED** — authoritative child ownership, generation skip gates, and strict root-invoked scaffold skip semantics (ownership gate in `newModule.py`, 2026-07-21) all landed | — |
| Cross-project resolution + provider overrides | block resolution | **PARTIAL / RUN-UNBLOCKED** — composed model build/run green; authoritative ownership and positive override selection are in source. `projectFiles:`-only FK fallback is CLOSED as will-not-implement (2026-07-21; `include:` is the scope contract, orthogonal to `projectFiles:`); negative override acceptance is DONE (committed 37bad48 + test_provider_override.py green) | — |
| Router/address reachability | block resolution / Q-C5 | **LANDED** — `REACHABLEINSTANCES` and router/address filtering are in source | final address-map proof in C5 |
| `newModule`/`fileGen` scaffold ownership gate | block resolution | **LANDED (2026-07-21)** — paths resolve through the owning project's layout, and `newModule.py` skips non-owned blocks (`contextOwningProject == PROJECTNAME`, mirroring the generation gates); no-op on monolithic, child-owned skipped in composed | — |
| Explicit managed SV file lists (E1/D-SD7) | shared definitions / C2 | module file list LANDED 2026-07-21; file->top record + `vl_wrap` retirement LANDED 2026-07-22 (S6/F10) | — |
| Composition C1 (boundary artifact contract refresh) | composition | open | buildable now; keep aligned to `Base` + parent-owned Config |
| Composition C2 (cross-project manifest + module/PCM discovery) | composition | **CLOSED/ACCEPTED** — composed SC paths/build, owner-aware RTL paths, VL manifest consumption, explicit managed SV selection, wrapper file-to-top records, composed VL, cross-project clangd, and standalone compdb are landed. Q-C8 Role C remains LATENT/DEFERRED, not a C2 gate. | — |
| Composition C2.5 (search-path disambiguation) | composition / Q-C8 | open | owner-qualified identity |
| Composition C3 (cross-project clangd) | composition | **CONFIRMED for the composed root (2026-07-21)** — `make compdb`/`make clangd` in `examples/ip_test/rundir` give child-owned files their own compile entries with child include roots and no extra `gen_compile_commands.py` path logic; `.clangd` mirrors them. Standalone sub-project `make compdb` deferred behind F10 (`vl_wrap` retirement); its only blocker is the missing child `verif/vl_wrap/vl_wrap.cpp` at the VL capture pass, not compdb/clangd | C2 |
| Composition C4 / Q-C5 (address-space composition proof) | composition | open | C0a; final proof in C5 |
| Registrar S4 (clangd include coverage for registrar dirs) | registrar | **LANDED (verified in code 2026-07-22)** — registrar dirs flow into `.clangd` via the build manifest (`examples/ip_test/.gen/build.mk:7` → `a2c-systemc.mk:52,151,331`); generated `examples/ip_test/.clangd` carries the registrar `-I` lines; no registrar-specific code needed | — |
| Layout L2b (composed/nested build) | layout | **CLOSED/ACCEPTED (2026-07-22)** — explicit managed SV lists (S6 file->top), active-project VL closure + standalone (S5), cross-project clangd (S4) all landed; L5 is the acceptance vehicle and it PASSED | — |
| **Registrar S3-H** (foreign Config → parent registrar-domain header) | registrar | **LANDED (committed 2026-07-21)** | project-qualified variant declaration key + owner-qualified C++ identity + mandatory hand-shaped VL/S6 type/top/factory proof before implementation |
| **Registrar S3-M** (header → registrar module export) | registrar | **LANDED (committed 2026-07-22, `d7f65b6`)** | — |
| **Registrar S6** (verilated trampoline relocation) | registrar | **LANDED (committed 2026-07-22, `7cb32f3`/`c42b535`; F10 `vl_wrap` retired, gate #6 closed)** | — |
| Cross-level wrapper P2 (foreign variant SV top/view/manifest integration) | cross-level variant wrappers | **DONE (proven; "Proof only" bar, 2026-07-22)** — delivered by S3-H/S3-M/S6/S5; acceptance proof run (`run-vl-ip1` root + `run-vl-uBridgeIp1` nested `--vlInst` targets, variant1 tops, 70-bit payload, both `No error`; 13/13 byte-identity guard PASS). Gaps 1/3/4 DEFERRED as hardening/hygiene | — |
| **Registrar S5** (standalone-TB module config home) | registrar | **LANDED / committed (`a50f12c`)** — general `mode: project` fileMap mode + `rtlDotF` entry/skeleton; standalone `ip`/`ipBridge` model+VL green under `-j`; 7 committed `rtl.f` byte-identical. **Registrar S0–S6 complete.** | — |
| Layout L5 (nested `ip_test` fixture) | layout | **PASSED/ACCEPTED (2026-07-22)** — full matrix green under `make -j` (standalone `ip` model+VL, standalone `ipBridge` model+VL, composed `ip_test` model + VL-src/ip0/ip1, all `No error`); evidence checks (provider override precedence, N7 distinct identities, N8 one-selected-child-file-set, scope, no `vl_wrap`) all PASS; no code gaps | — |
| Composition C5 (canonical split `ip_test`) | composition | **PASSED/ACCEPTED (2026-07-22)** — headline byte-identical parent address map (G3/Q-C5) PASS with an explicit caveat (no same-design monolithic-vs-composed byte-diff exists; established via split-reorganization byte-identity `16da8ca`≡`53456ed` PLUS a self-consistency proof of the current composed map). fwIpMain Q-C11/G4, provider-override + duplicate negative, `projectName`-keyed SC+verilated registration, and distinct-type thunkers all PASS. Cross-project eval Q-C12/G5 DEFERRED (`src`/`ipLeaf` not split). No gaps | — |

**Landed during the `blockBase` flip (2026-07-07).** Two
collateral changes rode in with the item-1 h→cppm flip:

- **Channel-header regression fixed.**
  `intf_gen_utils.py::sc_class_dependency_includes` had drifted from its
  sibling `sc_base_dependency_includes` and stopped emitting interface
  `<intf>_channel.h` includes for the model `.h`; once `<block>Base` became a
  module the transitive channel includes vanished and any block with interface
  channel members failed to compile. Fixed by mirroring the channel-header
  loop.
- **fileMap hygiene.** Example `project.yaml` files were normalized to inherit
  base mappings, retaining only project-specific entries such as optional
  `includeFW`. This removed stale overrides that masked newer base entries
  (`blockModule`/`blockRegistrar`/`include`/`config` and the divergent `block`
  entry).
- **Verilated SC wrapper made generator-maintained / self-healing.** The
  wrapper's base reference (`import <block>.base;`) and DUT SV-wrapper include
  moved out of the create-only preamble into a generated `preamble` section
  (`fileGen.py::vlScWrap_hdrTemplate` reduced to a minimal stub;
  `module_hdl_wrapper.py` gains `sec_preamble`), so `make gen` re-emits them
  every run (confirmed self-heal). 16 example wrappers migrated via
  delete + `make newmodule` + `gen`. `run-vl` passes for ip_test (uSrc/uIp0),
  axi4sDemo, apbDecode, and lmmiDemo — including lmmiDemo's previously-failing
  RTL/model (`VL_DUT`) tandem. Remaining `run-vl` failures (axiDemo/simple hang
  at "Simulation Start"; apbDecode top/uBlockA model register assert at
  `cpu.cpp:130`) are pre-existing runtime/functional issues, not emission bugs.

**Deferred (pre-existing, user-agreed — not flip failures).** The `mixed`
registrar orphan (`model/blockFRegistrar.cpp` lacking `--parent`) is now
COMPLETE — the orphan was removed and its `test_build_manifest` case un-skipped,
with the full unit suite green. `pySocket` is blocked at `make db` by the
`yamlFormat:2` gate (needs `make migrate`); it is a separate migration, excluded
from the example validation above, not a regression from this work.

**UPDATE (2026-07-22): S3-M/S6 have since LANDED after M-split was satisfied
(incl. F10 `vl_wrap` retirement), and S5 LANDED this session (staged) — registrar
S0–S6 complete. The rationale below is historical.**

**Why S3-M/S6/S5 are gated, not merely "unblocked by layout."** The
layout axis (`hierarchical`) settles *where* the registrar/config files sit;
it does **not** make per-parent-distinct config *types* correct. That
requires distinct `projectName` (invariant above). On monolithic `ip_test`
the single canonical config is forced and masks/breaks the feature, so these
three module/VL steps cannot be validated there. S3-H does not create distinct
module-attached types and landed independently of the split (LANDED
2026-07-21). "Layout-unblocked" ≠
"composition-ungated."

## Historical next-task sequence (superseded 2026-07-24)

The sequence below records how the critical path was closed. It is not a current
work queue. C2/L2b, standalone `ipBridge` model/VL/compdb, provider acceptance,
C3 clangd, S3-H/S3-M/S5/S6, C5/L5, and P2 all landed.

1. Finish and verify C2/L2b: the explicit managed SV module file list is DONE
   (`A2C_SV_FILES` LANDED 2026-07-21; lint/cosim consume it, no `-y` for managed
   modules). Cross-project clangd (C3) is confirmed, and the WRAPPER
   file->top record + `vl_wrap` retirement LANDED (committed 2026-07-22, S6/F10).
   Q-C8 SV Role C is LATENT/DEFERRED (interim uniqueness gate LANDED 2026-07-21)
   — not an active next item.
2. Standalone `ipBridge` model harness is RUNNABLE (done 2026-07-17; see the
   note near the top). Remaining: its VL-wrap `compdb` gap. The composed-root
   clean-rebuild `ipVariant1Config` failure was fixed by registrar S3-H (LANDED
   2026-07-21).
3. Provider acceptance — DONE (committed 37bad48 + test_provider_override.py
   green). Both paths are covered: root/bridge selection collapses onto the
   single real provider, and removing the root override yields the detailed
   duplicate-provider error naming both conflicting paths and the
   `projectOverrides` recovery. The committed provider link is
   `bridge/ip -> ../ip`.
4. The `projectFiles:`-only `validateForeignKey` fallback is CLOSED as
   will-not-implement (architect, 2026-07-21). It would conflate two deliberately
   independent concepts — `include:` governs definition scope (visible symbols,
   compiled context) while `projectFiles:` governs ownership/discovery only — and
   would silently widen compilation scope plus add a second resolution path to
   `validateForeignKey`, against generator discipline. It is not a correctness
   gap: composed builds are green because parents explicitly `include:` the child
   design YAML for scope. `include:` REMAINS the cross-project definition-scope
   contract, orthogonal to `projectFiles:`.
5. Strict `newModule`/`fileGen` scaffold skip semantics — **LANDED (2026-07-21).**
   `newModule.py` gates all three scaffold write sites on ownership
   (`contextOwningProject == PROJECTNAME`), mirroring the SystemC/SV generation
   skip gates; byte-identical no-op on monolithic examples (0 skips), child-owned
   blocks skipped on the composed `ip_test` root. `fileGen.py` needed no change.

Current residuals: C1 is buildable but not on the critical path; Q-C8 Role
C/C2.5 is latent until a real same-stem collision; Q-C12/G5 and wrapper Gaps
1/3/4 are deferred. The `projectFiles:`-only fallback is closed
will-not-implement and scaffold ownership is landed.

### Exit gates for the active task

- Monolithic regression set named by the blocker plan remains generated
  byte-identically and builds/runs to `No error` (documented `pySocket`
  exclusion only).
- From `examples/ip_test/ip/rundir` and
  `examples/ip_test/bridge/rundir`: `make clean && make gen && make &&
  make run` reaches `No error`.
- From `examples/ip_test/rundir`: `make clean && make db && make gen && make &&
  make run` reaches `No error`; `.gen/build.mk` contains owner-correct
  `ip/model`, `ip/fw/include`, and `bridge` paths.
- Root override wins and emits one `ip` provider; removing it produces the
  detailed duplicate-provider error.
- The parsing/layout unit-test set listed in the blocker plan passes, with only
  its explicitly recorded pre-existing exclusions.

## Milestone M-split (owner: composition)

The single concrete gate that let registrar S3-M/S6/S5 proceed (**all now
LANDED 2026-07-22 — historical**):

1. **Q-C10 factory qualification — DONE.** The factory key is
   `Key{blockType, variant, projectName}` and fallback holds `projectName`
   fixed across SC, verilated, tandem, and testbench call sites.
2. **Ownership foundation — DONE.** `CONTEXTOWNINGPROJECT`,
   authoritative child ownership, `PROJECTLAYOUT`, owner-relative expansion,
   reachability, and SystemC/SV generation skip gates are landed. The last
   partial — strict root-invoked scaffold skip semantics — LANDED 2026-07-21
   (ownership gate in `newModule.py`, `contextOwningProject == PROJECTNAME`).
3. **Q-C8 language identity — SATISFIED for M-split.** C++ Role A exists and the
   interim generated-name uniqueness gate LANDED 2026-07-21; SV Role C is
   LATENT/DEFERRED by the architect (fires only on a real cross-project
   same-stem collision, absent in this fixture), so it does not gate M-split.
4. **Canonical composed fixture — SATISFIED for M-split; full C5 open.** Root `ip_test`, reusable leaf
   `ip`, and reusable assembler `ipBridge` are distinct projects. The provider
   link (`bridge/ip -> ../ip`), overrides, and fixture refactor are committed;
   the composed model run is green, including on a clean child-first rebuild. The
   standalone `ipBridge` model harness is now runnable (2026-07-17); the provider
   negative-path proof is DONE (committed 37bad48 + test_provider_override.py
   green). Registrar S3-H (foreign per-variant Config owned
   in the parent registrar domain) LANDED 2026-07-21 and fixed the earlier
   clean-rebuild `ipVariant1Config` failure, so the composed green no longer
   depends on a stale `ipVariantConfig.h`.
5. **Cross-project manifest — SATISFIED for M-split.** Correct child SC paths,
   owner-aware RTL paths, and VL manifest-variable consumption are committed.
   The explicit managed SV file list (`A2C_SV_FILES`) LANDED 2026-07-21
   (`cdf78b1`) and cross-project clangd is CONFIRMED for the composed root (C3).
   The S6/F10 `vl_wrap` retirement and file->top record LANDED (committed
   2026-07-22) and composed VL is now GREEN.

The **full** target is the C5 / L5 split `ip_test` fixture; M-split is the
minimal precondition for registrar S3-M/S6/S5, referenced from layout L5
and registrar S3.

**M-split progress (updated 2026-07-17 through `6113562`).** Generator mechanisms landed + reviewed:
Q-C10 factory key + cleanup; C0a `CONTEXTOWNINGPROJECT`; child detection;
`PROJECTLAYOUT` per-project dirs; DB-driven SystemC/SV generation gates;
authoritative ownership and reachability; owner-relative `moduleDir` (committed);
identity completion still open. Fixture: `ip_test` split in
place into nested `ip`/`bridge`/`ip_top` projects (committed); `ip` standalone
build+run green; `ip_top` `db`+`gen`+gate green. **Composed `ip_top`
build+run is now GREEN (2026-07-17)** — resolved via `cpu` de-duplication to a
`common`-owned generic APB master (`ab75e9c`), definitions-only `hasMdl`
ownership (`91b69dc`/`ab75e9c`), cross-project plain-block registration
(`4038204`), and the BSP relocation to `common/systemc/bsp/` (`6791451`); see
the LANDED note at the top of this file. Commit `6bbec76` adds the final fixture
stimulus refactor and owner-aware RTL paths; `6113562` makes VL wrapper
Makefiles consume `A2C_VL_WRAP_DIRS`. The canonical target still requires a
runnable standalone `ipBridge`, explicit managed SV files, and complete VL/Q-C8
acceptance (provider negative-path proof is DONE — committed 37bad48 +
test_provider_override.py green).

**Reconciliation (2026-07-21).** Folding in this session's landings, all five
M-split preconditions above are SATISFIED at the minimal level: Q-C10 DONE,
ownership foundation DONE (scaffold-skip landed), Q-C8 satisfied for M-split
(uniqueness gate landed; SV Role C deferred), canonical fixture satisfied
(standalone `ipBridge` runnable `0b3a699`, provider negative DONE `37bad48`,
S3-H landed `52be673`), and the cross-project manifest satisfied (managed SV
`cdf78b1`, clangd C3 confirmed). **M-split no longer blocks registrar
S3-M/S6/S5; S3-M/S6 LANDED (committed 2026-07-22,
`d7f65b6`/`7cb32f3`/`c42b535`, incl. F10 `vl_wrap` retirement and gate #6) and
S5 LANDED this session (staged) — registrar S0–S6 complete.** Composed VL is
now GREEN. Full C5/L5
(byte-identical address proof, cross-project eval Q-C12, `src`/`ipLeaf` split)
remains, downstream of M-split, not a precondition to it.
