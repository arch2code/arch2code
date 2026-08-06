# Plan: Reusable-IP Registrar Directory

## Status

- **S3 IS SPLIT BY EMISSION FORM (architect reconciliation 2026-07-20).**
  The parent-owned SC Config **header checkpoint** is independent of S5/S6:
  emit the consumer-selected Config as an owner-qualified plain header beside
  the parent-owned registrar, so container and registrar share one textual C++
  type while the generic child has no outward dependency. This checkpoint is
  specified by
  [`proposal-config-ownership-header-relocation.md`](./proposal-config-ownership-header-relocation.md)
  and is **LANDED (committed 2026-07-21); composed `ip_test` builds/runs No
  error**. The later **registrar-module export (S3-M)** and the
  **verilated-wrapper generalization (S6, incl. gate #6)** are now **LANDED
  (committed 2026-07-22, `d7f65b6`/`7cb32f3`/`c42b535`)**.
  **UPDATE 2026-07-24 — S5 (standalone-TB module home) is committed
  (`a50f12c`).** Q-C10 and
  the distinct `ip_test`/`ip`/`ipBridge` fixture are now landed and the composed
  model run is green. **Registrar plan S0–S6 is now COMPLETE** (S4 clangd
  confirmed landed — see the S4 section); remaining acceptance is tracked by
  the downstream P2 cross-level wrapper and sub-project compdb acceptance are
  also closed. See
  [`plan-composition-ordering.md`](./plan-composition-ordering.md) and
  [`plan-ip-project-composition.md`](./plan-ip-project-composition.md)
  (M-split). Finding (the reason for both the coupling and the gate):
  per-variant config content is parent/consumer-derived (`ip_top.yaml`
  defines `src`'s `variantSrc0`; `src.yaml` binds `ipLeaf`'s `variantLeaf0`
  `LEAF_DATA_WIDTH` to its own `OUT0_DATA_WIDTH` — values flow down from the
  assembler), so config is parent-owned, NOT leaf-intrinsic (a leaf-owned
  config module is ruled out; vindicates Q2). The container does
  `dynamic_pointer_cast<<child>Base<Config>>(createInstance(...))`; under
  `VL_DUT` the factory returns the LEAF-SHARED verilated wrapper
  (`<block>_hdl_sc_wrapper<DUT,Config> : public <child>Base<Config>`), so
  container Config and wrapper Config must be the SAME C++ type. A C++20
  module-exported struct is a distinct entity from the same-named header
  struct, so relocating only the container's config to a registrar module
  makes the cast return null and breaks `run-vl-ip0`. **On monolithic
  `ip_test`, `ip_top` and `ipBridge` share `projectName=ip_test` and force
  ONE canonical config for `(ip, variant0)`** (load-bearing invariant,
  owned by the composition plan), so distinct per-parent config *modules*
  are not merely unnecessary here — they are incorrect. They become correct
  only across distinct `projectName`s, which is what M-split creates. The
  single leaf-shared wrapper cannot import both parents' configs
  (parent-routing it = S6); a standalone leaf TB needs its own config home
  (= S5). **Current delivered checkpoint: S3.2a (below) — registrar is a
  parent-qualified `.cppm` module while Config remains in the child-context
  header.** The next SC checkpoint relocates only foreign consumer Configs into
  parent `registrar/` headers; the gated module form later folds those headers
  into the adjacent registrar modules.
- **UNBLOCKED (2026-06-30): layout axis decided `hierarchical`.** The
  registrar directory axis is now resolved by
  [`plan-decomp-functional-layout.md`](./plan-decomp-functional-layout.md),
  which owns it: the project layout is selected per project file via
  `fileGeneration.layout: functional | hierarchical`, and `hierarchical`
  (the strategic target) places every artifact under one node subtree
  (`<node>/registrar/<child>Registrar.*`) — i.e. the **decomposition-first**
  arrangement the composition plan draws, not S2's functional-first
  `registrar/<assembler>/`. Mode-aware path composition (that plan's L1)
  has **landed and is verified** (functional output byte-identical;
  hierarchical inversion locked by a structural golden). Consequences for
  this plan:
  - **S2 reconcile:** S2's functional-first `registrar/<assembler-yaml-dir>/`
    is the *functional-mode* placement and stays correct under
    `layout: functional`. Under `layout: hierarchical` the same
    `blockRegistrar` fileMap entry (`basePath: registrar`) is emitted by the
    shared seam as `<node>/registrar/<child>Registrar.*` automatically — no
    separate S2 path logic; the layout selector supplies the inversion. S2's
    path-level invariant (filename is the child's; directory follows the
    assembler) holds in both modes.
  - **S3-M (config module export) and S6 (verilated trampoline) — LANDED
    (committed 2026-07-22); S5 LANDED 2026-07-22 (staged).** (Historical: these
    were layout-axis-unblocked but had remained GATED on composition M-split.)
    Layout settles *where* the files sit (author once against the shared
    `basePath: registrar` seam; functional vs hierarchical placement is the
    layout selector's job, not a per-step `basePath` choice). Layout does
    **not** make per-parent-distinct config *types* correct — that needs
    distinct `projectName` (the load-bearing invariant), which only the
    composition split provides. "Layout-unblocked" ≠ "composition-ungated";
    see the S3 gate bullet above and
    [`plan-composition-ordering.md`](./plan-composition-ordering.md). The
    `ext` flips (`blockBase` h→cppm — **LANDED** (2026-07-07; see
    the blockBase-flip bullet below); `blockRegistrar` cpp→cppm — **landed**,
    see S3.2a) remain owned here.
  - S0–S2 + S3.1/S3.2a remain valid (see below); S3-H is LANDED (committed
    2026-07-21); S3-M/S6 are LANDED (committed 2026-07-22); S5 LANDED
  2026-07-22 and committed as `a50f12c` — **S0–S6 complete**.
- **State (UPDATE 2026-07-24):** S0–S6 are COMPLETE. S3.1/S3.2a complete;
  mechanism **(a) modules ADOPTED**. S3-H is LANDED (committed 2026-07-21);
  S3-M/S6 are LANDED (committed 2026-07-22); **S5 is committed as `a50f12c`**;
  **S4 clangd confirmed LANDED** (registrar dirs flow
  into `.clangd` via the build manifest — see the S4 section). Composed
  `ip_test` builds/runs No error. Downstream P2 and sub-project compdb
  acceptance are also closed. See
  [`plan-composition-ordering.md`](./plan-composition-ordering.md).
- **M3/T6 per-block `.cppm` promotion: DONE for `ip`, `ipLeaf`, `src`
  (2026-06-25).** Each parameterizable leaf is now a single C++20 module
  interface unit (`<block>.cppm`, `export module <block>.block;`) carrying the
  exported block class plus all template member bodies; `<block>.h`/`<block>.cpp`
  are retired (preserved in `unittest/fixtures/block-module-migration/before/`).
  A consumer registrar `import <block>.block;` instead of `#include "<block>.h"`.
  Generator surface landed: `intf_gen_utils.cpp_block_module_name` +
  `sc_class_dependency_includes` (shared ordered include helper);
  `moduleScaffold.blockModuleHeader` (GMF + `export module` + context import +
  contained-instance Base headers); `classDecl` module-mode (export-prefixed
  class, includes/forward-decls suppressed; classic mode byte-identical);
  `constructor` module-mode (drops same-TU self-include + instance includes,
  anchor retained pending S2); `fileGen.blockModule_cppm` scaffold (paired
  fileGen for the `blockModule` fileMap entry, so `make newmodule` is safe);
  `blockRegistrar` imports the block module for `hasOwnParams`;
  `a2c-systemc.mk` `cpp_module_name` gives block units the `.block` suffix,
  the import regex allows dotted names, and block-module pcms are ordered after
  all context (`*Includes.cppm`) pcms (the `<block>Base.h` → `import <context>;`
  transitive dependency is invisible to the .cppm import scan). **Gate green:**
  `make`+`make run` and `make VL_DUT=1`+`make run VL_DUT=1` both report
  `No error` in `examples/ip_test/rundir`; classic output byte-identical for
  non-promoted blocks (`ip.h`/`ip.cpp`/`apbDecode.h` regen check).
- **S2 trampoline relocation + anchor removal: DONE (2026-06-25).** The
  per-leaf `<block>Registrar.cpp` (formerly emitted in the leaf's own
  `model/<block>/` dir) is replaced by per-assembler trampolines under the
  `registrar` root, which mirrors the yaml dir tree the way `base/` does:
  `registrar/<assembler-yaml-dir>/<child>Registrar.cpp`, one per distinct
  parameterizable child the assembler instantiates, keyed on the child
  (`--block=<child>`). In `ip_test`: `registrar/top/{ip,src}Registrar.cpp`,
  `registrar/bridge/ipRegistrar.cpp`, `registrar/src/ipLeafRegistrar.cpp`
  (the `ip` trampoline compiled twice — under `top` and `bridge` — is the
  accepted-duplication case, emplace first-wins). Generator surface that
  landed: a new `mode: registrar` in `newModule.py`
  (`registrar_create_from_templates` / `create_registrar_file`, grouping
  instances by `containerKey` and applying the fileMap cond/condAnd to the
  child; shared `_condMatch` helper); `config/project.yaml` fileMap
  `blockRegistrar` flipped to `mode: registrar, basePath: registrar`;
  `a2c-common.mk` `SC_GEN_FILES` and `a2c-systemc.mk` `PRJ_SRC_DIRS` extended
  with `$(REPO_ROOT)/registrar` (mirroring `base/`). The
  `[[gnu::used]] _<className>_instantiate_variant_N` anchor is removed from
  `constructor.py::blockRegistrarInitLines` (the `hasOwnParams` branch now
  emits nothing — the consumer registrar `import`s the block module and
  instantiates `<block><Config>` directly); the non-templated Option-δ
  self-registration arm is byte-identical. Leaf `.cppm` init regions are free
  of any generated registration section. **Gate green:** `make`+`make run`
  and `make VL_DUT=1`+`make run VL_DUT=1` (plus `run-vl-src`/`run-vl-ip0`)
  all report `No error` in `examples/ip_test/rundir`. **Config relocation
  (S3-M) and verilated-trampoline relocation (S6) LANDED (committed
  2026-07-22); clangd (S4) confirmed LANDED and standalone (S5) LANDED
  2026-07-22 (staged) — S0–S6 complete.**
- **S3.1 / S3.2a — registrar promoted to a parent-qualified `.cppm` module:
  DONE (monolithic checkpoint; verified in code 2026-07-06).** The
  `blockRegistrar` fileMap is now `ext: {cppm: "cppm"}, mode: registrar,
  basePath: registrar` (`config/project.yaml`), so S2's per-assembler
  trampoline is emitted as a C++20 module interface unit, not the `.cpp` the
  S2 bullet above records. Each trampoline is a **parent-qualified module**:
  `registrar/top/ipRegistrar.cppm` →
  `export module ip_test_ip_top_ip_registrar;`,
  plus `registrar/bridge/ipRegistrar.cppm`, `registrar/src/ipLeafRegistrar.cppm`,
  `registrar/top/srcRegistrar.cppm` (`intf_gen_utils.cpp_registrar_module_name`
  from `PROJECTNAME` + parent + child). This is the `blockRegistrar`
  cpp→cppm `ext` flip landing. **Config is still canonical in the header:**
  the module does `#include "ipVariantConfig.h"` in its global-module
  fragment and instantiates `ip<ipVariant0Config>` — the config structs
  still live at `model/<ip>/<child>VariantConfig.h`, NOT relocated. The
  generated factory call is now
  `registerBlock("ip_model", fn, "variant0", projectName)`; Q-C10's
  `projectName` key has landed. Gate green (`make`+`make run`,
  `VL_DUT=1`+run).
  This is the current delivered state; S3-H is LANDED (committed 2026-07-21);
  S3-M/S6 are LANDED (committed 2026-07-22); S5 LANDED 2026-07-22 (staged) —
  S0–S6 complete.
- **`blockBase` h→cppm ext flip: LANDED (2026-07-07).** The
  per-block `<block>Base` is now a C++20 module (`export module <block>.base;`)
  instead of a header — the open "ext flip" this plan owned. Landed surface:
  `baseClassDecl.py` module mode, `moduleScaffold.py` `baseModuleHeader`,
  `fileGen.py` `blockBase_cppm` scaffold, `intf_gen_utils`
  `cpp_base_module_name` + `sc_base_dependency_includes`, the include→import
  ripple (`classDecl.py`/`blockRegs.py`/`testbench.py`/`module_hdl_wrapper.py`),
  base config `blockBase ext:{cppm}`, `newProject.py` scaffolder default
  flipped to cppm, and pro `classDeclTandem.py` switched to
  `import <block>.base`. Validated: all examples (simple, apbDecode, nested,
  axiDemo, helloWorld, axi4sDemo, ip_test, lmmiDemo) build+run `No error`;
  lmmiDemo model/model tandem `No error`. (VL_DUT/run-vl verification DONE: the
  Verilated SC wrapper is now generator-maintained/self-healing — its base
  `import <block>.base;` moved from the create-only preamble into a generated
  `preamble` section; `run-vl` passes for ip_test uSrc/uIp0, axi4sDemo,
  apbDecode, and lmmiDemo incl. the RTL/model tandem. `pySocket`
  excluded as a pre-existing separate migration (blocked at `make db`
  by the `yamlFormat:2` gate, needs `make migrate`); the `mixed` registrar
  orphan has since been migrated (orphan `model/blockFRegistrar.cpp` removed,
  un-skipped in `test_build_manifest`, full unit suite green).)
  **Regression found & fixed during the flip:**
  `intf_gen_utils.py::sc_class_dependency_includes` had drifted from its
  sibling `sc_base_dependency_includes` and stopped emitting interface
  `<intf>_channel.h` includes for the model `.h`; once `<block>Base` became a
  module the transitive channel includes vanished and any block with interface
  channel members failed to compile. Fixed by mirroring the channel-header
  loop.

### Phase 1 kickoff decisions (2026-06-25, locked with user)

These resolve the open items the Phase 1 prompt required before coding:

- **Existing-project migration is a separate, harder phase (future).**
  Promoting an existing block's `.h`/`.cpp` to `.cppm` is **not** the
  trivial delete-and-regenerate of `migrateIncludes` (context includes
  have no hand code). Block files carry hand-written user regions
  (member decls, out-of-line bodies, `SC_THREAD` tails) that must be
  **preserved**: the migration **concatenates `.h` + `.cpp` into one
  `.cppm` then transforms** (includes→GMF, `export` the class, import the
  types module, reorder into the `classDecl`/`constructor` markers). This
  becomes a 4th `migrateYaml` phase. Before-state fixtures for `ip`,
  `ipLeaf`, `src` captured at
  `unittest/fixtures/block-module-migration/before/`. The `ip_test`
  conversion mirrors this concatenate-then-transform shape so it serves
  as the tool's spec, but building the tool does not gate Phase 1.
- **M3/T6 editing surface = per-block module file (Option B).** The
  parameterizable block class and all its template member bodies
  (generated + user-authored) move into a **per-block module interface
  unit** (`<block>.cppm`, `export module <block>.block;`) that
  `import`s and re-exports the context types module (`<context>` from
  `<context>Includes.cppm`). The user authors in this per-block
  `.cppm`, preserving one-editable-file-per-block. The context types
  include stays types-only and fully generated. `<block>.h`/`<block>.cpp`
  are retired for parameterizable blocks. Chosen over merging into the
  context module so the user's editable surface stays one file per block
  and the generated types include stays generation-only.
- **Registrar layout = flat, one SC file per child (Q4/Q6).** Under
  `<assembler>/registrar/`, one `<child>Registrar.cpp` per child block
  the assembler instantiates. The verilated trampoline (S6) is a
  **separate sibling file** per child (e.g. `<child>VlRegistrar.cpp`),
  because the SC model trampoline links unconditionally while the
  verilated one compiles only under `VL_DUT=1`. Chosen over per-assembler
  aggregation: lowest generator risk (direct evolution of today's
  block-mode `blockRegistrar.py`), clean build-condition separation, and
  text-stable diffs as the child set changes.
- **Non-templated children keep Option-δ self-registration in Phase 1
  (Q7).** Only the parameterized (and later verilated) registration
  relocates to the assembler `registrar/`; non-templated SC blocks keep
  self-registering from their own `.cpp` via `A2C_REGISTRATION_RETAIN`.
  Uniform assembler-ownership of non-templated children is explicitly
  out of Phase 1 scope.
- **Q3 (standalone-registrar placement) DEFERRED to S5.** Not needed to
  begin S1/S2; decided when standalone testability is implemented.
- **Q5 (`vl_wrap.cpp` residual role) RESOLVED 2026-07-20.** S6 retires
  `vl_wrap.h/.cpp`; guarded per-parent VL registrar TUs own registration.

#### Routing key + `isParameterizable` model (2026-06-25, in discussion)

- **`.cppm` promotion routes on `hasOwnParams`, not `isParameterizable`.**
  The promotion targets class-template blocks (those whose member bodies
  must be module-visible), which is exactly `hasOwnParams` (declares its
  own `params:`). `hasOwnParams` is sourced for the `fileMap` `cond` from
  the existing `getBlockConfigView` (a cheap derived view fact), overlaid
  in `newModule.py`'s cond-match assembly — **not** persisted as a column
  and **not** mutated onto raw rows. (`isParameterizable` is persisted
  because it needs the transitive surface walk.)
- **Clarified model:** for any *valid* design, block-level
  `isParameterizable == hasOwnParams`. A parameterizable structure on a
  block's OWN surface (own register/memory/own-port interface) with no
  own params has no valid C++ realization (no `Config` source), so the
  `isParameterizable=1 / hasOwnParams=0` state should be **detected as an
  error**, not supported. A parameterizable struct reached only through a
  child at a frozen variant (e.g. `ip_top` via thunkers) is valid and
  must not flag the parent (`ip_top` is `isParameterizable=0` in
  `ip_test`, confirmed from the DB). The downstream
  "container-parameterizable"/"transit" branches
  (`classDecl.py`, `_resolveConnectionConfigOverride` transit_choice,
  etc.) handle that should-be-rejected state.
- **RESOLVED (2026-06-25): own-surface validator added; no dead-code
  removal.** A scoping subagent confirmed the divergent state
  (`isParameterizable=1 / hasOwnParams=0`) is reachable by construction
  but latent (absent in all examples), splits into a **valid** transit
  case (parameterizable struct reached only through a contained child at
  a frozen variant — walk step 2; relied on by the registrar relocation)
  and an **invalid** own-surface case (own register/memory/own-port
  interface parameterizable with no own params — no `Config` source).
  `calcBlockConfigInfo` now threads an `own_surface` flag through its
  accumulation helpers and `printError`s when an own-surface arm flags a
  block that declares no `params:`. The valid transit case (step 2,
  `own_surface=False`) is untouched. Per the report, the downstream
  `not hasOwnParams` branches are **kept** (they serve fully
  non-parameterizable blocks and the valid container/transit case); only
  the `transit_choice` fallbacks (`processYaml.py:~1258`, `~4556`, and a
  twin) are *candidate* dead code and were left in place (medium-risk,
  not proven dead). Verified: `make db` clean across ip_test, helloWorld,
  mixed, nested, simple, apbDecode, axiDemo, axi4sDemo (pySocket fails
  only on the pre-existing yamlFormat:2 gate). **Negative test landed
  (2026-06-25):** `unittest/test_block_own_surface_param_no_params.py`
  (registered in `run_all_tests.sh` as Suite 10b) — confirms the state is
  constructible from valid YAML (the validator is real, not defensive):
  two negatives (own-register arm step 4, own-port arm step 1) assert the
  build fails on "parameterizable structure on its own surface", plus a
  positive control proving the valid transit/container case (paramless
  container wiring parameterized children) does NOT error. 3/3 pass.
  Cross-references `plan-block-config-postprocess.md` and
  `plan-block-registration.md` (Naming Note).
- **Origin:** 2026-06-25 working session. Goal is to make IPs easily
  assemblible and reusable by relocating per-instance registration
  (trampolines) and per-instance configuration out of a reusable IP's
  `model/` tree into a per-assembler `registrar/` directory, and by
  keeping the reusable IP directory pure.
- **Parent / sibling plans:**
  [`plan-block-registration.md`](./plan-block-registration.md) owns the
  per-block trampoline pattern;
  [`plan-registration-encapsulation-cleanup.md`](./plan-registration-encapsulation-cleanup.md)
  owns Option δ (`A2C_REGISTRATION_RETAIN`, `force_link` retirement).
  This plan changes **where** the trampoline lives and **who owns it**,
  building on both.

## Problem Statement

Today the example `examples/ip_test` mixes three concerns inside the
reusable IP's own `model/<block>/` directory:

- **`ip.cpp`** carries a generated `[[gnu::used]] _ip_instantiate_variant_N`
  anchor block at the top of its constructor `init` section. These
  anchors exist only so the parameterized block's out-of-line template
  member bodies are instantiated in the one TU that has their
  definitions. They are visible build scaffolding inside a file the user
  treats as hand-authored implementation.
- **`ipRegistrar.cpp`** (fileMap `blockRegistrar`, `basePath: model`) is
  the trampoline that calls `instanceFactory::registerBlock(...)`. It is
  emitted in the leaf block's own directory and registers that block's
  own declared variants.
- **`ipVariantConfig.h`** (fileMap `config`, `basePath: model`) holds the
  default config plus every variant config.
- **`verif/vl_wrap/vl_wrap.cpp`** is a single project-level aggregator
  TU. Its `factory_register_vl_decl` section emits one
  explicit-specialization line per verilated block + variant
  (`template<> ip_variant0_hdl_sc_wrapper::registerBlock
  ip_variant0_hdl_sc_wrapper::registerBlock_("variant0");`), with the
  non-template form for non-parameterizable wrappers. The
  `registerBlock` struct and static live in each
  `<block>_hdl_sc_wrapper.h`. This is a project-wide aggregator, not a
  per-assembler artifact, so it has the same reuse problem as the SC
  registration: it hard-codes the project's verilated variant bindings
  in one shared TU.

This couples a reusable IP to a specific set of variant bindings and
scatters build/registration material through the implementation tree. A
reusable IP cannot be dropped into a new assembly without carrying its
registration and config decisions with it.

## Target Model (agreed 2026-06-25)

- **The registrar belongs to the assembling IP, not the leaf.** When
  `usb` instantiates a variant of `fifo`, the trampoline that binds
  `fifo` to that variant lives in `usb/registrar/`. When `top`
  instantiates `usb` and `fifo`, `top/registrar/` holds both
  trampolines.
- **A reusable leaf IP directory stays pure.** `fifo/arch`,
  `fifo/model`, `fifo/rtl`, `fifo/base` contain only the generic,
  reusable definition. Selecting and instancing a variant is a property
  of the consumer, captured in the consumer's `registrar/`.
- **`registrar/` is a checked-in sibling directory**, mirroring the
  existing generated-and-tracked `base/` directory precedent.
- **Registrar duplication is acceptable.** The same selected leaf may compile
  under more than one consumer's registrar. This is distinct from physical
  provider selection: multiple paths declaring the same `projectName` require
  an explicit hierarchical `projectOverrides` choice and are never
  content-deduplicated.
  When two assemblers register the same `(block, variant)` key in one
  binary (for example `ip_top` containing `ipBridge`, both instancing
  `ip@variant0`), the factory's `emplace` is first-wins and tolerates the
  duplicate — **safe only under the determinism rule** that
  `(block, variant)` maps to one config (see
  [`plan-ip-project-composition.md`](./plan-ip-project-composition.md),
  Q-C4/Q-C10).
- **A leaf built standalone is its own assembler.** When `fifo` is built
  alone for its own testbench, the testbench is the top-level assembler
  and drives registration of the config under test. (Standalone-registrar
  placement is resolved by S5, LANDED 2026-07-22; see below.)
- **The verilated variant trampoline relocates in the same manner.** The
  verilated registration for a child an assembler instantiates moves out
  of the single project-wide `vl_wrap.cpp` aggregator and into that
  assembler's `registrar/`, alongside the SC trampoline for the same
  child. The reusable leaf's verilator wrapper stays generic; the
  assembler owns the variant binding for both the model and the
  verilated side.

- **The registrar pattern is recursive; nesting is preserved.** A block
  may be both a reusable leaf and an assembler of its own children. Every
  block that instantiates children gets a `registrar/`; a block with no
  children gets none (its standalone testbench provides one). There is no
  special-casing of "top" versus "IP" versus "leaf" — ownership follows
  instantiation at every level, so user nesting depth and reuse remain
  unconstrained.

## Worked Example: `ip_test`

The canonical fixture target exercises the cases this plan must handle. Root
`ip_test` selects root `ip`; standalone `ipBridge` selects
the committed `bridge/ip -> ../ip` provider symlink modeling its vendored
Git-submodule provider. The root override supersedes the bridge override in
composition, while registrars remain owned by their assembling projects.
**UPDATE 2026-07-22 (S5 LANDED):** both `ip` and `ipBridge` now build and run
green standalone test harnesses (model+VL, under `make -j`). Instance
hierarchy (parameterizable leaves marked `*`, container-parameterizable
marked `~`, non-templated marked `-`):

```
ip_top_tb                         (testbench top = assembler)
└── u_ip_top : ip_top      ~      (assembler; hasVl, hasMdl, hasRtl)
    ├── uAPBDecode : apbDecode  -
    ├── uSrc : src         *      variantSrc0   (leaf AND assembler)
    │   └── uLeaf : ipLeaf *      variantLeaf0  (LEAF_DATA_WIDTH = src OUT0_DATA_WIDTH)
    ├── uIp0 : ip          *      variant0
    ├── uIp1 : ip          *      variant1
    ├── uBridgeDriver : bridgeDriver  -
    └── uBridge : ipBridge ~      (assembler; hasVl)
        ├── uBridgeAPBDecode : bridgeApbDecode  -
        ├── uBridgeIp0 : ip  *    variant0      (ip reused under a 2nd assembler)
        └── uBridgeIp1 : ip  *    variant1
└── uCPU : cpu             -      (no mdl, no vl)
```

**Fixture drift note (2026-07-17) — this diagram is now STALE in two spots (the
principles it illustrates are unchanged):**
- `uBridgeDriver : bridgeDriver` was **removed**; `bridgeDriver` stimulus moved
  into the bridge's own `bridgeStdTop` TB, and `ip_top` now drives `uBridge`
  from `uSrc` (two new `uSrc` outputs). Committed in `6bbec76`.
- `uCPU : cpu (no mdl, no vl)` is now a single **`common`-owned generic APB
  master WITH a model** (`hasMdl`), running firmware on the BSP
  `regRead32`/`regWrite32` seam (`common/systemc/bsp/`, `6791451`); the duplicate
  per-parent `cpu` blocks were removed (`ab75e9c`).

What the per-assembler registrars hold (SC + verilated trampolines for
each child the assembler instantiates):

- **`ip_top/registrar/`** — `src@variantSrc0`, `ip@variant0`,
  `ip@variant1` (plus the non-templated children, pending the open
  decision below).
- **`ipBridge/registrar/`** — `ip@variant0`, `ip@variant1`. These are a
  **second, independent** compilation of `ip`'s two variants. This is the
  accepted-duplication case: `ip_top` and `ipBridge` each own their own
  `ip` trampolines. Within one linked binary both sets register under distinct
  `(ip_model, variant, projectName)` keys, so each assembler resolves its own
  parent-owned Config.
- **`src/registrar/`** — `ipLeaf@variantLeaf0`. This is the nesting case:
  `src` is itself a reusable leaf yet owns a registrar for its own child,
  with the child's config derived from `src`'s own parameters.

Open within this example:

- **Non-templated children** (`apbDecode`, `bridgeDriver`,
  `bridgeApbDecode`, `cpu`) have no variant/config to select and today
  self-register from their own `.cpp` via `A2C_REGISTRATION_RETAIN`
  (Option δ). Decide whether the assembler `registrar/` also owns their
  registration (uniform, fully-clean leaf `.cpp`) or whether they keep
  Option-δ self-registration and only the parameterized registration
  relocates. See Q7.

## The Linkage Constraint

A parameterizable leaf defines its template members (constructor,
`regHandler`, threads) out-of-line in `<leaf>.cpp`; `<leaf>.h` declares
them. A consumer's registrar TU must construct `leaf<Config>` and
therefore must be able to **instantiate the leaf's template** — it must
see the member definitions.

The agreed surface is that **the registrar `#include`s the leaf IP `.h`**.
For that include to be sufficient to instantiate `leaf<Config>`, the
leaf's parameterizable template member bodies must be visible through
that header (header-only / module-exported bodies), with the leaf's
`.cpp` retaining only non-template, user-authored logic. Whether this is
achieved by:

- making parameterizable-leaf template member bodies header/module-only, or
- an explicit-instantiation mechanism that the consumer links against,

is **not pre-committed** and is the subject of the S0 proof-of-concept.
The existing self-registration retain attribute
(`A2C_REGISTRATION_RETAIN`, see `common/systemc/instanceFactory.h`) and
the direct-`.o` link model from Option δ carry forward unchanged.

## C++ Modules as a Simplifier (PROVEN on clang — S0, 2026-06-25)

> **Update 2026-06-25 (S0).** The hypothesis below **validated on clang** and
> **failed on gcc 13** named modules — see the S0 DECISION table under the S0
> work item. A SystemC block class with the process macros can live in an
> exported module interface behind the global module fragment, and a foreign
> registrar TU can `import` it and instantiate `block<Config>` with a clean
> leaf `.cpp`. gcc 13 named modules break consumer-side instantiation, but
> that is not a blocker — gcc is not primary, clang is the module toolchain,
> and a newer gcc is expected to resolve it; (b) header-visible bodies is the
> portable equal that builds on gcc 13 today. The original C2 text is kept
> below for history.

> **Review C2 correction (original).** This is a hypothesis gated on S0, **not** an
> agreed path. Today the block class is **not** in the module: `ipIncludes.cppm`
> exports only constants/types/structures; the `template<typename Config>
> SC_MODULE(ip)` class is declared in `ip.h` with member bodies out-of-line
> in `ip.cpp` (which is exactly why the anchor block exists). Promoting a
> `SC_MODULE`/`SC_THREAD`/`SC_HAS_PROCESS` class into an exported module
> interface (with the global module fragment) is unvalidated, and the
> dependent T9 in `plan-development-ordering.md` is **open**. The `proto/`
> tree is **available** (it was removed on `feature/116-no-proto` but is
> tracked on `feature/116-parameterized-types`, restored 2026-06-25 at
> `/work/ws/debayer/proto`), including `proto/model/test/block_registration_*`
> and `.cppm` module material (`interpolate.cppm`,
> `block_registration_delta.cppm`). S0 **extends** that proto rather than
> rebuilding it. Until S0 proves SystemC-class-in-module-interface, the
> viable mechanisms remain header-visible template bodies or explicit
> instantiation — both of which keep a `.cpp`/anchor dependency,
> qualifying the "genuinely clean leaf `.cpp`" done-criterion.

The cppm migration already in flight (M-series in
`plan-development-ordering.md`) *may* dissolve the linkage constraint
rather than work around it, which would be the preferable outcome *if* it
validates.

Today, `ip.cppm` is `export module ip;` and exports the block's **types
and structures**, but the block class `ip<Config>` is still declared in
`ip.h` (which does `import ip;`) with its member bodies out-of-line in
`ip.cpp`. That out-of-line split is the entire reason the anchor block
exists.

If the block class template and its member bodies were promoted into the
exported module interface (or a module partition), a consumer's registrar
TU could simply:

```cpp
import ip;                       // brings in ip_ns::ip<Config> + member templates
// + the consumer-selected Config
instanceFactory::registerBlock("ip_model",
    [](...) { return std::make_shared<ip_ns::ip<ipVariant0Config>>(...); },
    "variant0");
```

`import ip;` then makes `ip<Config>` instantiable wherever imported, with
no anchor in `ip.cpp`, no explicit instantiation, and a genuinely clean
leaf `.cpp`. In effect, the modules path **is** the "header/module-only
member bodies" branch of the linkage constraint, delivered through the
module system instead of plain headers, and it converges with the
in-progress M3/T6 block-class modularization rather than competing with
it.

Caveats to validate in S0: whether a SystemC block class
(`SC_MODULE`-style, `SC_THREAD`, `SC_HAS_PROCESS`) can live in a module
interface unit cleanly; how the global module fragment
(`module; #include "systemc.h"`) interacts; and whether per-variant
explicit registration still wants `A2C_REGISTRATION_RETAIN`. If the
SystemC macros resist modularization, the plain explicit-instantiation
branch remains the fallback.

## Current vs Target Layout

```
CURRENT (examples/ip_test)
  model/ip/
    ip.h                 declares template members
    ip.cpp               user logic + generated anchor block (init section)
    ipRegistrar.cpp      trampoline (leaf-scoped, basePath: model)
    ipVariantConfig.h    default + all variant configs

TARGET
  model/ip/
    ip.h                 declares (and, per S0, may define) template members
    ip.cpp               user logic ONLY — no generated registration section
  <assembler>/registrar/
    ipRegistrar.cpp      trampoline owned by the assembler, one per
                         (child block, variant) it instantiates;
                         includes the leaf ip.h and instantiates leaf<Config>
    ipVariantConfig.h    consumer-selected variant configs
  (default config placement: OPEN — working hypothesis is it travels
   with the IP for standalone test)
```

## Relationship to IP Project Composition

The reuse goal extends past blocks-in-one-project to **each IP being its
own standalone arch2code project** that a parent references. That
cross-project composition mechanism is foundational and partially landed:
the composed model run and SC/RTL/VL path discovery work, while full
C2/VL/clangd and M-split acceptance remain. It is owned by:
[`plan-ip-project-composition.md`](./plan-ip-project-composition.md). It
owns the project-reference declaration, the build-composition model
(source vs library), cross-project clangd, and address-space composition.

This registrar plan layers on top of that boundary. The piece that
crosses to the child's **implementation** is the trampoline: the parent's
`registrar/` is the one place that brings in a referenced child's full
class to instantiate `<child><Config>`. **Review C1 correction:** the
parent's *container* is not config-free — it emits
`dynamic_pointer_cast<<child>Base<ChildConfig>>(createInstance(...))`
(`constructor.py:217-235`), so it references `<child>Base.h` **and** the
parent-owned per-variant Config struct (which therefore must be reachable
from the container, not only the registrar). What stays hidden from the
container is the child's implementation class / `.cpp`. Everything below —
where the trampoline and config live,
the linkage/modules question, the directory layout — applies whether the
child is a block in the same project or a referenced standalone IP
project. The composition plan's `ip_test` split fixture (its C5) is the
acceptance vehicle for this plan's S6.

## Directory Structure — Resolved

Q4/Q6 settled the internal shape: one flat, suffix-named emission unit per
child under the parent registrar directory. The SystemC unit is
`<parent>/registrar/<child>Registrar.cppm`; S6 adds the sibling
`<child>VlRegistrar.cpp`. Consumer-selected config artifacts share that
registrar location. The layout selector determines functional-first versus
hierarchical placement; no registrar-specific alternate path scheme remains
open. S6 retires the project-wide `vl_wrap.h/.cpp` C++ aggregator.

## Generator Surface

- **`config/project.yaml` `dirs:`** — add `registrar: $root/registrar`.
- **`config/project.yaml` fileMap `blockRegistrar`** — change `basePath`
  from `model` to `registrar`; change ownership from leaf-self emission
  to per-assembler emission (one trampoline per distinct child block +
  variant the parent instantiates). Reconcile the existing `cond:
  {isParameterizable: true}, condAnd: {hasMdl: true}` predicate with the
  new per-parent iteration.
- **`config/project.yaml` foreign Config entry** — add a dedicated
  registrar-mode header for consumer-selected foreign variants. Keep the
  context-mode `config` entry for child defaults and same-project canonical
  variants.
- **`templates/systemc/constructor.py` `blockRegistrarInitLines`** —
  remove the parameterized `_<className>_instantiate_variant_N` anchor
  block from the `ip.cpp` `init` section. The leaf `.cpp` no longer
  carries a generated registration section. (Coordinate with the S0
  outcome on how instantiation is forced.)
- **`templates/systemc/blockRegistrar.py`** — emit a consumer-scoped
  trampoline: include the child leaf `.h`, register each `(child block,
  variant)` the parent instantiates, instantiate `child<Config>`.
- **`templates/systemc/module_hdl_wrapper.py` + new guarded VL registrar
  template** — strip concrete Config aliases/includes and factory registration
  from the reusable `<block>_hdl_sc_wrapper.h`; retain only the generic
  `wrapper<DUT_T, Config>`. Emit direct `_verif` registration in
  `<parent>/registrar/<child>VlRegistrar.cpp`, using the same S3-H Config
  descriptor/header as the SC path. Retire `vl_wrap.h/.cpp`.
- **`config/createBuildManifest.py` + `include/make/a2c-vl-wrap.mk`** — persist
  and consume explicit physical-SV→qualified-top records. Do not reconstruct a
  top/object from a physical filename or archive via a broad `V*` glob.
- **`pysrc/gen_compile_commands.py` / `include/make/a2c-systemc.mk`
  clangd target** — add each `registrar/` directory to the generated
  `.clangd` `-I` include list so clangd resolves registration and config
  symbols. Because the directory is checked in, this is a path-addition
  only (no build-tree indexing needed).
- **`pysrc/newProject.py` / `pysrc/newModule.py` /
  `templates/fileGen/fileGen.py`** — scaffold the `registrar/` directory
  for assembling blocks; migrate the in-tree examples.

## Open Questions

- **Q1 — Template-definition visibility (S0). RESOLVED (2026-06-25).** Yes —
  proven by the S0 DECISION table. Three mechanisms work; (a) modules
  (clang-only) and (b) header-visible bodies (clang+gcc) both give a clean
  leaf `.cpp`; (c) explicit instantiation works on both but keeps the `.cpp`
  anchor. Recommended: (a) modules with (b) as the portable equal.
- **Q2 — Default config placement. DECIDED** (Q-C4,
  [`plan-ip-project-composition.md`](./plan-ip-project-composition.md)):
  the default is **implicit** in the IP's `ipParameters` defaults
  (synthesized for standalone build, not a separately-owned artifact);
  the only owned configs are the consumer-selected instanced ones in the
  consumer's `registrar/`. **Spelling reconciled 2026-07-10:** the registrar
  module name is parent-qualified with the same direct underscore convention
  (`<project>_<parent>_<child>_registrar`) and
  the config STRUCT stays context-qualified (child + variant, e.g.
  `ipVariant0Config`); terminology uses "parent" not "assembler", and
  struct-name parent-qualification is deferred to the S6 co-import.
- **Q3 — Standalone registrar. RESOLVED by the canonical fixture
  (2026-07-10).** The active child project is its own assembler. Its
  testbench-selected/default variant registration lives in that project's
  registrar tree and is keyed by that project's `projectName`. The fake
  harness container supplies surrounding stimulus/decode blocks but does not
  become the owner of the reusable child implementation.
- **Q4 — Per-parent emission unit. RESOLVED (2026-06-25): one file per
  child block.** Flat per-child SC trampoline (`<child>Registrar.cpp`)
  under `<assembler>/registrar/`, not an aggregated per-assembler TU.
  Lowest generator risk and text-stable as the child set changes. Same
  basenames under different assembler directories are intentional and safe
  for plain `.cpp` TUs; when the registrar becomes a module/export surface,
  its **language-visible identity** must be parent-qualified (owning
  project + parent/assembler context + child + artifact kind), not merely
  file-stem-qualified.
- **Q5 — Verilator / tandem. RESOLVED (2026-07-20).** The per-assembler verilated
  trampoline is a **separate sibling file** from the SC trampoline for
  the same child (different build conditions: SC unconditional vs
  `VL_DUT=1`). It is a fully guarded ordinary `.cpp`. `vl_wrap.h/.cpp`
  disappears after its include aggregation and factory registration move to
  those files; the project-scoped Verilator build directory/library remains.
- **Q6 — Directory layout. RESOLVED (2026-06-25): flat, suffix-named.**
  `<assembler>/registrar/<child>Registrar.cpp` (SC) plus
  `<assembler>/registrar/<child>VlRegistrar.cpp` (verilated, S6).
  Consumer-selected config headers also live under `registrar/` (S3).
  Parent-scoped module names, header basenames, residual include spellings, and
  PCM/object targets use the parent-qualified artifact identity from Q4. Config
  type identity follows the composition invariant
  `(projectName, block, variant)`; repeated consumers in one project point to
  the one declaration-owning header rather than defining parent-distinct types.
- **Q7 — Non-templated child ownership. RESOLVED (2026-06-25): keep
  Option-δ self-registration in Phase 1.** Only parameterized (and later
  verilated) registration relocates; non-templated SC blocks keep
  self-registering from their own `.cpp`. Uniform assembler-ownership is
  out of Phase 1 scope.
- **Q8 — Modules vs explicit instantiation. RESOLVED (2026-06-25).** Yes for
  clang — promoting the SystemC block class into the exported module interface
  dissolves the linkage constraint: `import <leaf>;` in the registrar suffices
  to instantiate `leaf<Config>` with no anchor (S0 mechanism (a)). gcc 13
  named modules break consumer-side instantiation, but this is **not a
  blocker** — gcc is not primary, clang is the module toolchain, and a newer
  gcc is expected to resolve it (untested; only gcc 11/13 here). (b)
  header-visible bodies is the portable equal that builds on gcc 13 today, and
  (c) explicit instantiation the last-resort fallback. Converges with the
  M-series cppm migration. See the S0 DECISION table.

Cross-project questions (reference mechanism, build composition,
cross-project clangd, address-space composition) are owned by
[`plan-ip-project-composition.md`](./plan-ip-project-composition.md).

## Work Items

### S0 — Proof of concept: consumer registrar instantiates a leaf

Build a minimal proto (extend `proto/model/`): a reusable parameterizable
leaf, a separate consumer `registrar` TU that brings in the leaf and
calls
`instanceFactory::registerBlock(..., make_shared<leaf<Config>>(...))`.
Confirm linkage and registration across the three candidate mechanisms:

- **Modules (preferred):** the leaf's block class is in an exported
  module interface; the registrar does `import <leaf>;` and instantiates.
  Validate the SystemC-macro / global-module-fragment caveats (Q8).
- **Header/module-only member bodies:** the registrar `#include`s the
  leaf `.h` whose template member bodies are header-visible.
- **Explicit instantiation (fallback):** the leaf emits explicit
  instantiation TUs the registrar links against.

Matrix: direct-`.o` linking and C++20 modules; clang and gcc. Record the
chosen mechanism. Blocks S2/S3.

#### S0 DECISION (2026-06-25) — PROVEN; Q1/Q8 resolved

Proto extended under `proto/model/test/` (`s0_block.cppm`,
`s0_block_hdr.h`, `s0_block_ei.{h,cpp}`, `s0_registrar_{mod,hdr,ei}.cpp`,
`test_s0.cpp`) and driven by `test/s0_matrix.sh` (`make step8`). The proto
block is a parameterizable SystemC block — `sc_module` + `SC_HAS_PROCESS`
+ `SC_THREAD`, deriving from the factory `blockBase` — instantiated by a
**separate registrar TU** that calls
`instanceFactory::registerBlock("s0Block_model", []{ … make_shared<s0Block<Config>>(…) }, "variant0")`
with **no anchor in any block `.cpp`**; `test_s0.cpp` creates it through the
string-keyed factory and runs `sc_start()` (the `SC_THREAD` fires). Toolchains
here: clang 20.1.8, gcc 13.1.0, SystemC 2.3.4.

| Mechanism | clang | gcc | Clean leaf `.cpp`? |
|---|---|---|---|
| **(a) modules** — block class **and member bodies** in an exported module interface, behind `module; #include "systemc.h"`; registrar `import`s and instantiates | **PASS** | **FAIL** | **Yes** (no `.cpp`, no anchor) |
| **(b) header-visible template bodies** — block class+bodies in a header; registrar `#include`s and instantiates | **PASS** | **PASS** | **Yes** (no `.cpp`, no anchor) |
| **(c) explicit instantiation (fallback)** — bodies out-of-line in `<leaf>.cpp` + `template struct leaf<Config>;`; registrar links the object | **PASS** | **PASS** | **No** (`.cpp` anchor required) |

- **(a) validates the C2 "modules as a simplifier" hypothesis on clang.** A
  SystemC block class with the process macros lives cleanly in a module
  interface behind the global module fragment; a foreign registrar TU
  `import`s it, instantiates `block<Config>`, registers, and the simulation
  runs — with a genuinely clean leaf (no `.cpp` at all, no anchor).
- **(a) fails on gcc 13 named modules — NOT a blocker.** The module
  *interface* unit compiles, but **importing** it into the registrar
  mis-attributes `systemc.h` global-module-fragment entities to the module
  (diagnostic shows `sc_dt::sc_logic@s0_block`) and loses ADL for SystemC's
  free `operator<<`, so consumer-side instantiation does not compile. This is
  a known class of gcc named-modules limitation with large legacy headers in
  the GMF and is **expected to improve in newer gcc**; only gcc 11/13 are
  installed here, so a fix could not be confirmed. gcc is **not** the primary
  toolchain — clang is the project's module toolchain ("examples use clang for
  C++20 modules", `delta_matrix.sh`) — so this gcc-13 result does **not** gate
  the modules path. The portable fallback (b) covers any block that must build
  on gcc 13 today.

**ADOPTED MECHANISM (2026-06-25): (a) modules. Build S2/S3 on it.** The user
locked this as the path; (b) and (c) are fallbacks with narrow triggers,
below. Consequence: parameterizable blocks migrate their class declaration
(today in `<leaf>.h`) and out-of-line template member bodies (today in
`<leaf>.cpp`, incl. the generated anchor) into the exported module interface
unit — this is the M3/T6 block-class-into-module promotion, and it is the
load-bearing precondition for S2's anchor removal. (a) is chosen because it (i) delivers the clean leaf `.cpp` the
done-criterion requires (no `.cpp`, no anchor), (ii) converges with the
in-flight M3/T6 cppm migration that is already promoting the block class into
the module interface, and (iii) is proven for the full SystemC case on clang,
which is already the project's module toolchain. The gcc-13 modules failure is
explicitly **not** a blocker (gcc is not primary; a newer gcc is expected to
resolve it).

Fallbacks (do not default to these):

- **(b) header-visible template bodies** — use *only* for a specific block that
  must build under gcc 13 today without modules. It reaches the same clean-leaf
  outcome but keeps the block out of the module system, so it diverges from the
  cppm migration. Stopgap, not the destination.
- **(c) explicit instantiation** — last resort only. It is the one mechanism
  that retains a `.cpp` anchor, so it **fails** the "genuinely clean leaf
  `.cpp`" done-criterion. Use only if a block can be expressed by neither (a)
  nor (b); that block then keeps a generated explicit-instantiation TU.

Registration reachability (the `[[gnu::used, gnu::retain]]` static under
`--gc-sections` with direct-`.o` linking) is unchanged from Option δ and was
re-confirmed green here; S0 adds only the **template-linkage** result above.

> **Dependency:** the cross-project composition foundation is owned by
> [`plan-ip-project-composition.md`](./plan-ip-project-composition.md)
> (its C0–C5). The registrar relocation below applies within a single
> project today and extends across the IP boundary once that foundation
> lands; both share the composition plan's `ip_test` split fixture.

### S1 — `registrar` directory plumbing

Add the `registrar` dir to `dirs:`; teach `fileGen.py` /
`newProject.py` / `newModule.py` to create it for assembling blocks.

### S2 — Relocate the trampoline to the assembler — DONE (2026-06-25)

Moved `blockRegistrar` emission to `basePath: registrar` and to
per-assembler, per-child ownership via a new `mode: registrar` in
`newModule.py`; removed the instantiation anchor from `constructor.py`'s
`init` section so the leaf `.cppm` carries no generated registration.
Layout (decided with user, mirrors `base/`):
`registrar/<assembler-yaml-dir>/<child>Registrar.cpp`. See the S2 entry in
the Status block for the full landed surface and the green gate. Collision
invariant for S2: the trampoline filename is the child's and the directory is
the assembler's, so same child basenames under different assemblers are
expected. This is a path-level invariant only; S3/S6 must additionally use the
parent-qualified language identity from Q4 when these artifacts export modules,
Configs, or build PCM/object targets.

### S3 — Config relocation split: SC header checkpoint, then gated module export

**S3-H — parent-owned header checkpoint: LANDED (committed 2026-07-21); composed
`ip_test` builds/runs No error.** Move only
foreign consumer-selected variant Configs into owner-qualified plain headers
beside their parent-owned child registrars:
`registrar/<parent>/...VariantConfig.h` in functional mode and
`<parent>/registrar/...VariantConfig.h` in hierarchical mode. The parent
container and SC registrar include the same header; the generic child includes
neither. Child-owned defaults and same-project canonical variants stay in the
existing context Config header. This changes emission ownership without
creating a module-attached type, so it is independent of S5/S6. The complete
schema/view/naming/validation contract is owned by
[`proposal-config-ownership-header-relocation.md`](./proposal-config-ownership-header-relocation.md).

**S3-M — registrar-module export: LANDED (committed 2026-07-22, `d7f65b6`).**
Each parent-owned foreign Config HEADER was folded into a canonical config
MODULE interface unit (`.cppm`), one per `(owningProject, child)`, at the
registrar-domain location; the container and the SC registrar `import` it
instead of `#include`-ing the header. Config STRUCT names are unchanged
(`ip_test_ipVariant1Config` etc.), so no cast site moved; the module name comes
from `cpp_config_module_name` (persisted identity). This preserves the
project-canonical `(projectName, block, variant)` type identity, including the
accepted case where two assemblers in one project consume the same Config.
**STOP GATE CLOSED:** one canonical declaration/export unit per
`(projectName, qualifiedBlock, variant)` is emitted and every parent registrar
imports that exact entity.
Config is parent-owned and the `VL_DUT`
`dynamic_cast` forces the verilated wrapper (S6) and standalone TB (S5) to
share the container's module-attached parent-owned config type, so this form must be
implemented together with the S6 wrapper generalization and the S5
standalone-TB config home. But — per the load-bearing invariant (owned by
the composition plan) — distinct per-parent config *modules* are correct
only across distinct `projectName`s. On monolithic `ip_test` (`ip_top` and
`ipBridge` sharing `projectName=ip_test`) the shared `dynamic_cast` forces
one canonical config, so this change cannot be validated there. It proceeds
only after composition **M-split** (Q-C10 `projectName` factory key
implemented + a two-project `ip_top`/`ipBridge` split); full acceptance is
the C5 split `ip_test` fixture. See
[`plan-composition-ordering.md`](./plan-composition-ordering.md) and
[`plan-ip-project-composition.md`](./plan-ip-project-composition.md).

### S4 — clangd — LANDED (verified in code 2026-07-22)

Original intent: extend `gen_compile_commands.py` / the clangd make target to
add every `registrar/` directory to the `.clangd` include list, and verify
clangd resolves config and registration symbols in `examples/ip_test`.

**Disposition — LANDED, no registrar-specific code needed.** The registrar
directories reach the `.clangd` include list through the ordinary
build-manifest → include-path flow, not a special case:
- The build manifest lists every registrar source dir. Verified in code:
  `examples/ip_test/.gen/build.mk:7` — `A2C_SC_SRC_DIRS` includes
  `.../ip/registrar/ip`, `.../bridge/registrar/bridge`, `.../registrar/src`,
  and `.../registrar/top`.
- Those dirs become include flags. Verified in code:
  `include/make/a2c-systemc.mk:52` (`PRJ_SRC_DIRS := $(A2C_SC_SRC_DIRS)`) and
  `include/make/a2c-systemc.mk:151`
  (`CPP_INCLUDES += $(foreach dir, $(PRJ_SRC_DIRS), -I$(dir))`).
- The `clangd` make target emits every `$(CPP_INCLUDES)` dir into `.clangd`.
  Verified in code: `include/make/a2c-systemc.mk:331-333`
  (loop `for inc in $(CPP_INCLUDES); do echo "    - $$inc"`).
- Confirmed in the generated artifact: `examples/ip_test/.clangd` contains
  `-I.../ip/registrar/ip`, `-I.../bridge/registrar/bridge`,
  `-I.../registrar/src`, and `-I.../registrar/top`.

Because registrar dirs are carried by the manifest and flow through
`CPP_INCLUDES` identically to `base/`/`model/` dirs, no `gen_compile_commands.py`
or clangd-target change specific to `registrar/` was required. Cross-project
clangd (C3) was confirmed working earlier this session.

### S5 — Standalone IP testability — LANDED / committed (`a50f12c`)

**LANDED this session.** Implementation: a new general `mode: project` fileMap
mode (one artifact per project at the `basePath` root, keyed to the persisted
`TOPCONTEXT`, ownership-gated), `newModule`/`createBuildManifest` support, an
`rtlDotF` fileMap entry (`name: "rtl", ext: {f}, mode: project, basePath: rtl`),
and a `rtlDotF_f` fileGen skeleton. Validated under `make -j`: the 7 pre-existing
committed `rtl.f` are byte-identical; standalone `ip` (`--vlInst tb.ip`) and
`ipBridge` (`--vlInst tb.bridgeStdTop.uBridge`) build and run model+VL green
(distinct `--Mdir`/gate #6 exercised); composed `ip_test` run-vl + apbDecode
run-vl green; no `vl_wrap` reintroduced. Committed as `a50f12c`.

Original intent: implement the standalone-assembler registrar path so a
reusable IP builds and runs its own testbench using its default (or
testbench-selected) config. Its module-export form was coupled with S3-M/S6
(the standalone TB needs the same module-attached parent-owned Config type),
both LANDED (committed 2026-07-22); S3-H did not claim this module/VL
completion.

The acceptance fixture is concrete:

- `ip` is the reusable leaf. Its block-level testbench uses a fake harness
  container (DUT excluded from the External) containing local stimulus, APB
  master, and primary decode shell.
- `ipBridge` is both reusable child and assembler. Its block-level testbench
  uses a fake harness container with stimulus and an outer primary decoder so
  the production `bridgeApbDecode` remains nested.
- `ipBridge` standalone selects symlinked `bridge/ip`; root composition selects
  root `ip`. The selected child's generated identity is unchanged and each
  assembler's config/registrar remains distinct.
- Both standalone runs and the root-composed run must reach clean end-of-test.

**Historical progress note (2026-07-17):** the root-composed model run and the
`bridgeStdTop` fixture refactor are committed (`6bbec76`), and
`bridgeStdTop.hasTb: true` now makes the standalone model harness runnable.
At that checkpoint its clean Config relocation and VL acceptance remained open. `6113562` only
switches VL wrapper Makefiles to `A2C_VL_WRAP_DIRS`; it does not close S6
validation. S5 (and S3-M/S6) remain GATED — these commits did not relocate
Config to the registrar module.

**UPDATE 2026-07-22 —** superseded: S3-M/S6 LANDED (committed 2026-07-22) and
S5 LANDED this session (staged) via the general `mode: project` fileMap mode +
`rtlDotF` entry/skeleton (see the S5 header note above). Standalone `ip` and
`ipBridge` model+VL runs are green under `make -j`; the composed run remains
green; the 7 committed `rtl.f` are byte-identical.

### S6 — Relocate the verilated variant trampoline — LANDED (committed 2026-07-22)

**LANDED (`7cb32f3` foreign wrappers, `c42b535` vl_wrap retirement).**
Owner-qualified per-variant SV wrapper tops
`<projectName>_<child>_<variant>_hdl_sv_wrapper` (parent/assembler-owned,
foreign variants only; same-project variants keep the bare top); explicit
per-top `file->top` manifest records + `A2C_VL_BUILD_DIR`; `a2c-vl-wrap.mk`
drives verilate from the records (the `$(notdir)`-derived top and the `V*`
glob were removed) with a distinct `--Mdir` per top (**gate #6 closed**). A
per-assembler guarded `VlRegistrar.cpp` (`#ifdef VERILATOR`) `import`s the
S3-M config module and registers `Key{"<child>_verif", variant, <owner>}`,
which keeps the container `dynamic_pointer_cast` non-null under `VL_DUT`.
**Gate #5 (cross-assembler owning-key dedup) DROPPED** — not a bug:
`instanceFactory::registerBlock` uses `std::map::emplace` (first-wins), so a
duplicate owning-keyed `_verif` registration is silently ignored (harmless);
deferred as unused-today flexibility (re-add only if a real
multi-assembler-plain-`hasVl`-IP fixture appears). The former coupling to
S3-M/S5 and the composition M-split gate are historical (both preconditions
satisfied). Original design intent follows.

Move Verilated registration from the project-wide `vl_wrap.cpp` aggregator into
one guarded parent-owned `<child>VlRegistrar.cpp` per assembler/child. The
ordinary `.cpp` exports nothing, includes the same Config header as the SC
registrar, includes the generic child `<block>_hdl_sc_wrapper.h` and generated
`V<qualifiedTop>.h`, and directly registers
`child_hdl_sc_wrapper<VQualifiedTop, OwnerConfig>` under
`Key{child_verif, variant, assemblerProjectName}`. Its entire contents are
guarded by `VERILATOR` (the host C++ macro set by `a2c-systemc.mk` under
`VL_DUT=1`), so the registrar-directory wildcard compiles an empty TU in model
builds. Keep the reusable leaf wrapper generic and free of concrete
Config aliases/includes and factory statics.

This section is the single home for the registration destination that
`plan-cross-level-variant-wrappers.md` (Direction A) also needs; the coupled
parent-owned Config header is S3-H and its later module form is S3-M. Direction
A's P2(c) resolves here and P2(e)'s SC ownership resolves in S3-H; P2 completion
still requires S3-M/S5/S6 rather than the project-wide aggregator.

The "variant the assembler instantiates" set includes foreign-child variants
declared by that same immediate assembling `projectName`. An ancestor
project's declaration does not silently supply a nested child assembler. If
root `ip_test` and child assembler `ipBridge` both instantiate
`ip@variant1`, each project declares the binding and receives a distinct
Config/registration identity qualified by its own `projectName`.

Surface from review G6/C3:
- Split `vl_wrap.h`'s paired `factory_register_vl_incl` include-aggregation
  in lockstep with the `.cpp` decomposition.
- Remove the hard-coded single-file reference
  `CPP_SRC += $(REPO_ROOT)/verif/vl_wrap/vl_wrap.cpp`
  (`a2c-systemc.mk:102`) in favor of a discovered per-assembler registrar
  TU set.
- The verilated `registerBlock` lives in the wrapper-header struct and is
  invoked from a different TU than the SC container `createInstance`; the
  new `projectName` key dimension (composition Q-C10) must be threaded
  through the wrapper struct and the tandem `_model`/`_verif` blockType
  derivation — the "co-located, agrees for free" reasoning covers only the
  SC model path.
- S6 also emits the owner-qualified SV wrapper **top-module / `V*`-class
  name** `<projectName>_<block>_<variant>_hdl_sv_wrapper` — the SV design-unit
  spelling of the same Q-C10 `projectName` key threaded above. This blockType-
  axis identity is owned HERE (with composition Q-C10), NOT by Q-C8, which is
  the `includeName`/context axis and disclaims block-module qualification
  (`proposal-qc8-identity-field.md:79-81`). The composition C2 build manifest
  consumes the resulting file → qualified-top mapping. This closes the
  cross-level plan's wrapper-top ownership question (Direction A).
- The build manifest carries explicit managed-wrapper records
  `{physicalSv, qualifiedTop, includeDirs, generatedVHeader, object/archive
  identity}`. `a2c-vl-wrap.mk` emits one source→`--top` rule per record and must
  not derive top/object names from the physical filename or archive with a broad
  `V*` glob.
- Add a manifest-owned Verilator build directory and use it for recursive
  `vlwrap`/`clean` and library search; remove hard-coded
  `$(REPO_ROOT)/verif/vl_wrap`.
- **Q5 resolved:** retire `vl_wrap.h/.cpp` after include aggregation and
  registration move to guarded VL registrars. The project-scoped Verilator
  build directory/library remains; only the C++ aggregator disappears.
  **F10 — DONE (committed 2026-07-22, `c42b535`):** `vl_wrap.h/.cpp` is
  retired suite-wide; the generic child SC wrapper's `registerBlock`
  struct/aliases were removed.
- Before generator implementation, pass the disposable/fixture proof specified
  by `proposal-config-ownership-header-relocation.md`: same S3-H type at
  container/SC/VL sites, owner-qualified top, explicit source→top invocation,
  non-null factory cast, and exercised foreign-child data path.

### S7 — Migrate examples and validate

Regenerate every project in `examples/`; confirm `make gen`, build, and
`make run` pass, plus verilator and tandem paths, with the leaf `model/`
trees free of generated registration sections.

## Relationship to Other Plans

- **`plan-block-registration.md`** — the trampoline pattern this plan
  relocates. **The factory key changes** to `{blockType, variant,
  projectName}` (composition plan Q-C10), superseding that plan's
  `configTag` (Config-name) third dimension; see the composition plan's
  M1 reconciliation.
- **`plan-registration-encapsulation-cleanup.md`** — Option δ retain
  attribute and `force_link` retirement carry forward; this plan does not
  reintroduce parent→child symbol references.
- **`plan-variant-config-unification.md`** — owns the per-variant Config
  policy structs this plan relocates.
- **`plan-ip-project-composition.md`** — foundational dependency: defines
  the standalone-IP-project boundary and reference mechanism that this
  plan's cross-boundary trampoline assumes.
- **`plan-composition-ordering.md`** — the authoritative cross-plan index
  for the composition workstream (dependency chain, owner map, the
  load-bearing config-canonicality invariant, buildable-vs-gated table).
  This plan's S3-H versus S3-M/S6/S5 split is defined there.
- **`plan-development-ordering.md`** — high-level index; item 8 and its
  owner map record this plan's landed checkpoints and gate.

## Done Criteria

- S0 mechanism recorded; Q1 resolved. **DONE (2026-06-25):** recommended (a)
  modules / (b) header-visible bodies; (c) explicit instantiation does not meet
  the clean-leaf criterion. See the S0 DECISION table.
- Reusable leaf `model/` trees contain only `<leaf>.h` and user-authored
  `<leaf>.cpp` (no generated registration section).
- Each assembling block has a checked-in `registrar/` directory holding
  its child trampolines (SC and verilated) and consumer-selected configs.
- Parent-scoped registrar/header/build artifacts use parent-qualified identities
  (owning project + parent/assembler context + child + artifact kind), while
  Config types remain canonical by `(projectName, block, variant)`. Thus
  same-child artifacts under distinct assemblers do not collide and repeated
  consumers in one project share one Config entity.
- The verilated variant trampoline is owned by the assembler's
  `registrar/`; `vl_wrap.h/.cpp` is retired (Q5).
- Directory layout (Q6) decided and reflected in the fileMap `basePath`
  and per-artifact naming.
- Default-config placement (Q2/Q3) decided and implemented.
- clangd resolves all symbols across `examples/ip_test` with the new
  layout.
- Every `examples/` project regenerates, builds, and runs (including
  verilator and tandem) without regression.
