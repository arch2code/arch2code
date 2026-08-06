# Plan: Cross-Level / Higher-Level-Owned Per-Variant Verilated Wrappers (Direction A)

## Status

- **Created:** 2026-07-17.
- **UPDATE 2026-07-22 — DONE (proven). Completion bar = "Proof only" (architect
  decision 2026-07-22).** Gap analysis found P2 already delivered by the
  S3-H/S3-M/S6/S5 landings (owner-qualified per-variant wrapper tops with
  resolved-literal binding + fixed-width pins, ownership-gated render, per-top
  manifest records; Q-C8 Role C confirmed NOT needed, stays latent). The
  acceptance proof run added `run-vl-ip1` (root `--vlInst ...uIp1`) and
  `run-vl-uBridgeIp1` (nested `--vlInst ...uBridge.uBridgeIp1`) to
  `examples/ip_test/rundir/Makefile`; both bind the parent-context-prefixed
  variant1 tops (`Vip_test_ip_variant1_hdl_sv_wrapper` root,
  `VipBridge_ip_variant1_hdl_sv_wrapper` nested, 70-bit payload) and reach
  "No error", and the byte-identity guard PASSES (13/13 wrappers idempotent after
  clean+gen across the three rundirs; no `variant1` under the reused `ip/` tree).
  The architect chose the "Proof only" completion bar: **Gap 1** (projectCreate
  negative-declaration-ownership validation / acceptance gate 7), **Gap 3**
  (fixture ownership reconciliation — bridge declaring `ip@variant1` in
  `ipBridge.yaml` rather than `bridgeStdTop.yaml`), and **Gap 4** (consolidated
  projectOpen view) are DEFERRED as hardening/hygiene, not required for P2
  completion. The historical P1/P2 status below is retained for the record.
- **Historical pre-completion state:** **P1 SC-path VALIDATED — registrar S3-H (the independent
  parent-owned Config header beside the registrar) LANDED (committed
  2026-07-21), so the composed `ip_test` builds and runs `No error` on a clean
  child-first rebuild; P1 no longer depends on a stale sub-project artifact.**
  Registrar S3-M/S6 and the explicit file->top manifest LANDED (committed
  2026-07-22): the assembler-owned Verilated wrapper/registration routing, the
  Q-C10 `projectName`-qualified wrapper-top identity (see "Ownership of the
  wrapper top-module identity"), and the `vl_wrap` aggregator retirement (F10)
  are all in the generator. This paragraph predates the proof run above: P2 is
  DONE at the architect-selected proof bar and registrar S5 is committed.
  Q-C8/SV Role C remains LATENT/DEFERRED, guarded by the uniqueness gate.
- **Relationship:** extends the per-variant wrapper design in
  [`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md),
  which is validated only for the monolithic single-project case (a project
  Verilating variants of blocks it declares itself). This plan covers the
  composed / cross-level case and is coupled to
  [`plan-ip-project-composition.md`](./plan-ip-project-composition.md).

## Requirement (R)

A higher-level (composition/assembling) project may CREATE ADDITIONAL variants
of a reusable sub-component — variants the sub-project itself does not declare —
and those must be verilatable/simulatable WITHOUT MODIFYING THE SUB-PROJECT.
Building the Verilated library needs a distinctly-named SV top per variant
and assembling project. The physical file remains
`<block>_<variant>_hdl_sv_wrapper.sv` under the assembling project's
owner-scoped wrapper directory, but the composed end state requires the managed
SV top identity to be owner-qualified on the Q-C10 `projectName` axis
(`<projectName>_<block>_<variant>_hdl_sv_wrapper`; see the ownership resolution
below). The current filename-derived top/class spelling is a pre-qualification
build limitation, not the composed end-state contract.

## File naming convention

Authoritative source: the `fileMap` in `config/project.yaml` plus the stub
logic in `pysrc/newModule.py:139,147` (`moduleFileStub = block`, then
`+= '_' + data['variant']` when the file definition sets `variant: true`).

`<variant>` is the declared variant NAME string, NOT an index. The fixture's
variants are named `variant0` / `variant1`, so the emitted files read
`ip_variant0_...` / `ip_variant1_...` — that resemblance to an index is
coincidental. A variant named `wide` would emit `ip_wide_hdl_sv_wrapper.sv`.

| fileMap key | suffix + ext | `variant:` | emitted file | scope |
| :-- | :-- | :-- | :-- | :-- |
| `vlSvWrap` | `_hdl_sv_wrapper.sv` | `true` | `<block>_<variant>_hdl_sv_wrapper.sv` | one per assembler-owned declared variant; Q-C10 `projectName`-qualified `module` name is carried separately from this physical filename |
| `vlSvWrapBody` | `_hdl_sv_wrapper.svh` | `false` (parameterizable only) | `<block>_hdl_sv_wrapper.svh` | one shared include-only body; each trampoline `` `include``s it |
| `vlScWrap` | `_hdl_sc_wrapper.h` | (absent → false) | `<block>_hdl_sc_wrapper.h` | one per block — NOT per-variant today |

Today the Makefile derives the Verilator top from the filename and therefore
produces `V<block>_<variant>_hdl_sv_wrapper`. The composed end state instead
uses the owner-qualified top `<projectName>_<block>_<variant>_hdl_sv_wrapper`,
producing `V<projectName>_<block>_<variant>_hdl_sv_wrapper`; the composition C2
build manifest must carry the file-to-top mapping rather than recovering the top
from the filename.

## Ownership of the wrapper top-module identity — RESOLVED (2026-07-17)

The per-variant Verilated wrapper top module is a SystemVerilog design-unit
name keyed on `blockType` (+ variant), NOT on `includeName`/context. It
therefore does NOT belong to **Q-C8**: `proposal-qc8-identity-field.md:79-81`
scopes Q-C8 to `includeName`-keyed context/package identity (Roles A/C) and
explicitly excludes "block/base module qualification (a separate axis, already
keyed by `blockType`)". The wrapper module name is filename/block-derived
(`newModule.py:137-146`), which Q-C8 states it does not touch.

The owner is the **composition Q-C10 `projectName` axis** — the same
`{blockType, variant, projectName}` dimension that qualifies the factory key
and the per-project config structs (`plan-ip-project-composition.md:367-372`).
The owner-qualified spelling `<projectName>_<block>_<variant>_hdl_sv_wrapper`
is the SV design-unit name of that Q-C10 key, and it is **emitted by registrar
S6**, which already threads the Q-C10 `projectName` dimension through the
wrapper struct (`plan-reusable-ip-registrar.md` S6). Division of ownership:

- **Q-C10 (composition) + S6 (registrar):** the wrapper top-module / `V*` class
  identity and the per-variant Config struct identity — the `projectName`/
  `blockType` axis.
- **Q-C8 (Role C):** the SV package/type identities the wrapper *references*
  (the port struct/type packages) — the `includeName`/context axis. Q-C8 is
  invoked for those, not for the wrapper module name.
- **Composition C2 (build manifest):** consumes and records the physical
  file → qualified-top mapping; it does not define identity. This is the
  `plan-ip-project-composition.md` C2 (managed-SV files), distinct from the
  SystemC bare-name C2 in `plan-param-constant-collision.md`.

## Decision — Direction A

**The immediate assembling project creates the HDL wrapper for each foreign
child variant it instantiates and declares.** "Declaring project" below means
that assembler's `projectName`, not an arbitrary ancestor context that happens
to place rows in the composed DB. It emits, into its OWN
`verif/vl_wrap/<sub>/` tree, the per-variant SV trampoline (which
`` `include``s the sub-project-owned canonical
`<block>_hdl_sv_wrapper.svh` body), the SC `using` typedef, the `V*`, and the
factory registration.

If two distinct assembling projects instantiate the same foreign
`(block, variant)` — for example root `ip_test` and child assembler `ipBridge`
both instantiating `ip@variant1` — each project declares that binding and owns
its own Config, wrapper top, typedef, and registration under its own
`projectName`. Equal local variant names and values do not merge those
artifacts. The reusable `ip` project remains unchanged and owns only its
canonical generic wrapper body and variants it declares for its own standalone
use.

Rejected alternatives:

- **B — sub-project emits all declared variants.** Only works if the variant is
  declared in the sub-project, so it fails R.
- **C — explicit target list.** More machinery for the same placement decision.

## P1 Prototype Result — green build, but on a STALE artifact

> **RESOLVED (2026-07-21):** registrar S3-H has since LANDED and moved foreign
> per-variant Config generation to the immediate assembler, so a clean
> child-first rebuild of composed `ip_test` now builds and runs `No error`
> without any stale child artifact (re-verified 2026-07-21). The
> "P1 Prototype Result" and "Config-ownership blocker" record below documents
> the original prototype and the blocker S3-H fixed; it is historical.

With `variant1` of `ip` DECLARED at `ip_top` (value binding moved out of
`ip/ipVariants.yaml`) and no child implementation edit:

- Composed `ip_test` `make run` = **No error**. `uIp1` and bridge `uBridgeIp1`
  received the 70-bit variant1 payload.
- Composed `run-vl` / `run-vl-src` cosim = **No error**. The child
  `Vip_variant1_hdl_sv_wrapper.h` was verilated from the assembler-owned
  wrapper, linked, and the bridge received the data.

**These greens do NOT prove the requirement — see the Config-ownership blocker
below.** They hold only because the sub-project tree still carries a stale
pre-reshape `ipVariant1Config`.

## Config-ownership blocker (why the end state is NOT proven)

The assembler-owned SC typedef needs `ipVariant1Config`. Verified chain:

- `verif/vl_wrap/ip/ip_variant1_hdl_sc_wrapper.h` (assembler) uses
  `ipVariant1Config` and `` `include``s the child `ip_hdl_sc_wrapper.h`.
- The child `ip_hdl_sc_wrapper.h` pulls in `ip/model/ip/ipVariantConfig.h`
  (`GENERATED_CODE_PARAM --context=ip/ip.yaml`, **sub-project tree**).
- That header is the ONLY definition of `ipVariant1Config` — there is no
  assembler-owned Config struct.
- The reshaped child `ipVariants.yaml` no longer declares variant1 (`git diff`
  deletes its three param bindings), YET `ipVariantConfig.h` is git-unmodified
  and still contains `ipVariant1Config`: it is a **stale pre-reshape artifact**.
  A clean standalone `make clean gen` in `ip/` would drop `ipVariant1Config`,
  and the assembler typedef would fail to compile.

Consequence: the higher-level variant's Config lives in and is sourced from the
sub-project. The composed build's ownership gate skips regenerating ip-owned
files, so the composed run consumes the stale header rather than owning its own.
Either way this violates "without modifying/generating into the sub-project".
**P2 must consume registrar S3-H's move of per-variant Config generation
to the immediate assembler (the same axis as the wrapper), not only reroute the
wrappers.** Until then Direction A is not demonstrated end-to-end.

### Four unknowns resolved

1. A project CAN declare a variant of a foreign/included block at its level
   (`parameters: ip: variant1` in `ip_top.yaml`, byte-identical gen). BUT the
   generator currently keys per-variant WRAPPER ownership on the BLOCK (owner
   `ip`), so it still emits variant1's wrapper (broken, monolithic
   `module ip_hdl_sv_wrapper`) into the CHILD tree. This is the core P2 gap.
2. In the P1 build, cross-project `` `include`` of the child `.svh` works via a
   RELATIVE path + the per-wrapper `+incdir` (`a2c-vl-wrap.mk:56`). P2 still
   requires composition-C2 manifest/top integration for the Q-C10-qualified top;
   "no makefile change" applies only to proving include resolution, not to the
   composed end state.
3. The wrapper needs `GENERATED_CODE_` markers (grep discovery,
   `a2c-common.mk` `find_gen_sv_sources`) to be verilated; the file-ownership
   gate (child-block PARAM) keeps arch2code from clobbering the
   assembler-authored file.
4. SC typedef + `V*` + factory registration resolve at the assembler.

## P2 Recipe (generator automation) — pending

Emit into the immediate ASSEMBLING project's `verif/vl_wrap/<sub>/`:

- **(a) SV trampoline** `<block>_<variant>_hdl_sv_wrapper.sv` (per the naming
  table above): physical filename remains unqualified; the `module`/top
  design-unit is owner-qualified on the Q-C10 `projectName` axis
  (`<assemblerProjectName>_<block>_<variant>_hdl_sv_wrapper`; see the ownership
  resolution above); relative `` `include`` of the selected child owner's
  `.svh`; `localparam`s = resolved literals; `GENERATED_CODE_` markers. The SV
  type/package names the wrapper REFERENCES are the Q-C8/SV Role C concern; the
  wrapper module name itself is Q-C10, and the Verilator flow must not
  reconstruct it from the filename.
- **(b) SC typedef** — keep the reusable child's `vlScWrap` generic and
  single-emission (`variant: false`); do NOT flip that child-owned fileMap entry
  to per-variant emission. Emit the assembler-specific alias over
  `V<assemblerProjectName>_<block>_<variant>_hdl_sv_wrapper` and the generic
  child `<block>_hdl_sc_wrapper` in the assembler-owned, fully
  host-`VERILATOR`-guarded
  `<child>VlRegistrar.cpp` from S6. The alias and its direct registration
  have the same assembler-owned lifetime, so no second child-like
  `<block>_<variant>_hdl_sc_wrapper.h` API is introduced. The P1 standalone
  header is prototype-only and retires with S6.
- **(c) Factory wiring:** register into the **per-assembler `registrar/`**, NOT
  the project-wide `vl_wrap.h` / `vl_wrap.cpp` aggregator. This is
  `plan-reusable-ip-registrar.md` S6, which replaces
  `factory_register_vl_decl`/`factory_register_vl_incl` with
  `registrar/<child>VlRegistrar.cpp` (one guarded registrar per child; direct
  entries per instantiated variant) and retires `vl_wrap.h/.cpp`. The P1
  prototype hand-wired into `vl_wrap.h` only because S6 has not landed; do NOT
  bake the aggregator destination into P2.
- **(d) STOP** emitting the per-variant wrapper into the CHILD tree for variants
  the child does not declare, and ROUTE wrapper ownership to each immediate
  assembling project that declares and instantiates that variant.
- **(e) Config ownership (REQUIRED, not optional):** the per-variant Config
  struct must be generated by / owned by the immediate assembling project in
  its registrar domain, so the assembler no longer depends on the sub-project
  carrying that struct. S3-H emits an owner-qualified plain header beside the
  SC registrar; the parent container and registrar include it, while the
  generic child does not. This is the blocker above; without it P2
  only relocates wrappers over a Config the child still has to declare. This is
  the SAME parent-owned-config ownership axis as
  `plan-reusable-ip-registrar.md` S3, consumed later by S6 (its `dynamic_cast`
  requires the wrapper and container to share the parent-owned config type) —
  do NOT design a second, competing config-ownership mechanism here.
  **DECIDED (2026-07-20):** the SC-path portion of (e) lands as S3-H,
  independently of S6/S5. It preserves the registrar ownership/location and
  changes only header-vs-module emission form. See
  [`proposal-config-ownership-header-relocation.md`](./proposal-config-ownership-header-relocation.md).

## Reconciliation with the registrar plan — SETTLED

Item (e)'s SC ownership/emission checkpoint is owned by registrar S3-H and may
land independently. Item (c) is owned by registrar S6; S3-M/S6 LANDED (committed
2026-07-22), leaving only S5 of the coupled module/VL end state. S3-H does not
make P2 complete and does not add an intermediate wrapper implementation against
the current project-wide aggregator.

This plan owns only the cross-level wrapper emission/selection contract
(a)/(b)/(d) and the immediate-assembler ownership rule. The registrar plan owns
the S3-H Config header, the Config module (S3-M, landed), the
typedef/registration unit, and build discovery. S6/F10 retired `vl_wrap.h/.cpp`
suite-wide, so it has no residual C++ role. P2 cannot be called complete before
registrar S5 and P2's own generator automation/acceptance pass.

## Generator data contract

Wrapper ownership cannot be inferred from the foreign block row: that row names
the reusable child's project. It must come from the variant declaration and the
assembler that owns the consuming instances.

1. During `projectCreate`, make the declaration identity
   `(declaringProjectName, qualified block, variant)`, deriving
   `declaringProjectName` from each declaration row's `_context` through the
   existing DB-backed `CONTEXTOWNINGPROJECT` map. The current
   `data['parameters'][qualBlock]` / `getQualBlockVariants(qualBlock)` shape
   collapses the project dimension and is not the P2 contract. Validate that all
   parameter rows for one triple resolve to one project and one complete
   binding. If the current schema loader cannot preserve two same-local-name
   declarations under distinct projects, P2 requires an explicit schema/data
   contract change before renderer work; it must not emulate the dimension with
   path or name parsing.
2. Validate that every foreign-child variant instance is served by a matching
   declaration owned by the same immediate assembling `projectName`. An
   ancestor-only declaration does not silently supply a nested child assembler.
   Within one project, the existing invariant remains: `(block, variant)` maps
   to exactly one Config.
3. Surface a language-neutral `projectOpen` view grouped by assembling project,
   child block, and variant. Each entry supplies the selected child owner,
   assembler owner, resolved parameter literals, Config descriptor, physical
   output layout, owner-qualified language identities (Q-C8/Role C for the
   referenced type packages; Q-C10 `projectName` for the wrapper top and
   Config), and consuming instance set.
   `newModule`, both wrapper renderers, and registrar generation consume this
   view; templates do not walk raw cross-project tables or recover ownership
   from paths/names.
4. Resolve physical output directories through
   `PROJECTLAYOUT[assemblerProjectName]`. Resolve the canonical body through the
   selected provider/child owner already established by composition. The
   relative `` `include`` path is formatting of those resolved facts, not an
   ownership or provider-selection mechanism.
5. The generated managed-SV manifest records physical wrapper file, qualified
   top-module identity, and include directories explicitly. The Verilator flow
   must not infer the composed top identity from the unqualified filename.

Relevant generator sites:

- `newModule.py:81` — scaffold uses declared variants via
  `getQualBlockVariants`.
- `templates/systemVerilog/module_hdl_wrapper.py:34` — render gate uses
  instantiated variants via `getBDInstances`.
- `pysrc/systemVerilogGenerator.py:50-53` — ownership gate.
- `resolveFileOwner`.
- `processYaml.py::_buildVariantConfigDescriptors` /
  `getBlockConfigView` — current block-owned Config grouping that S3-H must
  replace for assembler-owned foreign variants.
- `CONTEXTOWNINGPROJECT`, `PROJECTLAYOUT`, and the composition C2 managed-SV
  manifest view (the `plan-ip-project-composition.md` C2, not the
  `plan-param-constant-collision.md` bare-name C2) — existing
  ownership/layout/identity seams; do not add path- or basename-based fallback
  ownership.

## Fixture reshape

Value bindings `parameters: ip: variant1` moved from `ip/ipVariants.yaml` to
`ip_top.yaml` (`ip.yaml` keeps the param defs). That P1 shape is insufficient:
one root declaration currently serves both `ip_top.uIp1` and
`ipBridge.uBridgeIp1`, conflating two distinct assembling projects.

Before end-state validation, reshape the fixture so root `ip_test` declares the
binding used by `ip_top.uIp1`, while project `ipBridge` independently declares
the binding used by `ipBridge.uBridgeIp1`. The values and local variant name may
match, but each project emits its own Config, qualified wrapper top, typedef,
and factory registration. The reusable `ip` project declares neither
assembler-added variant and remains byte-/git-unchanged after composed
generation.

## P3 — Shared-definition / identity reconciliation (SETTLED)

The earlier premise that SV type packages are consuming-project-owned per
`(IP, variant)` was incorrect. `plan-cross-project-shared-definitions.md`
defines:

- **Option R:** a shared definition/package has one referenced project owner
  and one owner-qualified identity.
- **Option D:** project-local copies remain distinct under their respective
  owner-qualified identities.

Packages are not per-variant artifacts and do not move to the wrapper
assembler. Direction A therefore does not impose one ownership axis on packages
and wrappers:

- the reusable child owns its canonical generic wrapper body and the packages
  its RTL references, following Option R/D and selected-provider rules;
- each immediate assembler owns the concrete variant top, Config, SC alias,
  and registration needed for its `(projectName, child block, variant)`;
- managed language identities are qualified by their actual owner along two
  axes: Q-C8/Role C owns the `includeName`/context package+type identities the
  wrapper references; the Q-C10 `projectName` axis owns the blockType-axis
  wrapper-top and Config identities (see the ownership resolution above); and
  composition C2's explicit manifest selects the exact physical files and
  carries the file → qualified-top mapping.

This contract is reconciled. Registrar S3-M/S6 and the explicit managed-SV
file/top manifest LANDED (committed 2026-07-22); P2 remains on registrar S5.
Its Q-C8 SV Role C dependency is LATENT/DEFERRED (the module/package uniqueness
gate covers the collision hazard), NOT a live gate — P2 is actionable for the
current fixture once S5 lands. S3-H was the independent SC Config prerequisite
(landed 2026-07-21).

## Acceptance gates

**UPDATE 2026-07-22 — completion bar reduced to "Proof only" (architect
decision).** P2 is DONE against the proof bar: the model+Verilated proof run at
both hierarchy paths (gates 4/6) PASSES via the `run-vl-ip1` (root) and
`run-vl-uBridgeIp1` (nested) `--vlInst` targets binding the parent-context
variant1 tops (70-bit payload, both "No error"), and the byte-identity guard
(gate 8, 13/13 wrappers idempotent) PASSES. Gate 7 (the negative-declaration
fixture) is DEFERRED as Gap 1, and the fixture-ownership (Gap 3) and consolidated
projectOpen view (Gap 4) are DEFERRED as hardening/hygiene. The original full
gate list is retained below as the (now non-blocking) hardening checklist.

P2 is complete only when all of the following pass:

1. Clean-regenerate the standalone child `ip` first. Its generated Config and
   wrapper trees contain no assembler-added `variant1`.
2. Generate the composed root. No generated or authored file under the reusable
   `ip` project changes; root `ip_test` and assembler `ipBridge` each receive
   their own `variant1` Config/wrapper/registrar artifacts.
3. The generated manifest names both unqualified physical files and distinct
   Q-C10 `projectName`-qualified tops/classes. Equal local `(block, variant)` names in the two
   assemblers produce no SV, C++, PCM, object, include-guard, or factory-key
   collision.
4. Model and Verilated runs select the foreign child at both hierarchy paths
   (`ip_top.uIp1` and `ip_top.uBridge.uBridgeIp1`) and exercise the 70-bit
   payload. This must test child-instance replacement, not only a whole-top or
   `src` replacement.
5. Factory registration and lookup use the matching assembler `projectName` for
   both paths; no `unregistered block type ip_verif` failure and no
   cross-project fallback occur.
6. Standalone `ip` (its own declared/default variants), standalone `ipBridge`,
   and composed `ip_test` model/VL flows pass. Tandem coverage required by S6
   also passes.
7. A negative fixture in which `ipBridge` instantiates `ip@variant1` but only
   root `ip_test` declares it fails during `projectCreate` with a diagnostic
   naming the assembler project, child block, variant, instance, and declaration
   owner.
8. A second generation is byte-identical, and the relevant focused unit tests
   cover owner grouping, incomplete/mixed-owner parameter rows, selected
   provider paths, and physical-file/qualified-top manifest entries.

## Remaining orthogonal pre-existing gap

`a2c-rtl.mk` `make lint` hardcodes the flat
  `verif/vl_wrap/<top>_hdl_sv_wrapper.sv` + positional `rtl/<top>.sv`
  (shared-mk escalation). The `ip_verif` `projectName` mismatch is not listed
  here: although pre-existing and affecting variant0, it blocks the child-level
  VL acceptance required above and is expected to close with registrar S6
  (LANDED 2026-07-22).
