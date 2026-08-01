# Plan: Variant ≅ Config Unification (Path C)

## Status

- **Direction:** settled. Source of truth for the design is
  [`research-multi-config-bindings.md`](./research-multi-config-bindings.md).
- **Current role (reconciled 2026-07-24):** completed execution index for
  variant/config work on `feature/116-parameterized-types`. Stages 1-11 and the
  formerly cross-owned C3.6, registration, eval, and YAML-migration follow-ups
  are complete or descoped. Only the explicitly deferred decisions near the end
  of this plan remain future work.
- **Status model:** use this vocabulary when relevant: `design only`,
  `implemented in working tree`, `committed`, `verified`, `open`,
  `deferred`, `superseded`, and `historical`. Use `committed` only for
  work supported by `builder/base` git history, `implemented in working
  tree` only for local uncommitted implementation changes, and
  `verified` only when the plan records a concrete command or
  regression result. The plan file itself is currently workspace
  documentation; do not read its presence as a committed status change.
- **Supersedes:**
  [`plan-block-registration.md`](./plan-block-registration.md) Step 10
  (multi-Config-per-block regression). The block-registration plan
  remains authoritative only for the steps still named there (Steps
  1–9 and Steps 11–12); Step 10 is absorbed here.
- **Touches:**
  [`plan-block-config-postprocess.md`](./plan-block-config-postprocess.md)
  (per-variant `defaultConfig` becomes per-variant Config struct
  emission),
  [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md)
  (Config policy template extends to per-variant emission), and
  [`plan-development-ordering.md`](./plan-development-ordering.md) (T9
  follow-on work item).

## Active Stage Index

| Stage | Current status | Evidence / owner |
|---|---|---|
| Stage 1 — Per-variant Config infrastructure | committed | Branch history includes Path C per-variant Config registration work; detailed notes below record the implementation shape. |
| Stage 2 — Factory key simplification | committed | Branch history includes the variant refactor; detailed notes below record the factory key collapse. |
| Stage 3 — Container shape | committed | Branch history includes the variant refactor and wrapper work. Step C3.9 is verified in [`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md). |
| Stage 4 — `addParam` retirement | committed | Branch history includes the mixed migration and variant refactor; detailed notes below record the `addParam` / `getParam` removal. |
| Stage 5 — Bottom-up ports schema | committed and verified | Branch history includes parameterized-interface checks; C3.6 is closed by the 11/11 static-validation matrix in [`plan-param-constant-collision.md`](./plan-param-constant-collision.md). |
| Stage 6 — Thunker infrastructure (`rdy_vld`, `req_ack`) | committed | Branch history includes thunker improvements and wide packed protocol thunker support; proto/header smoke coverage is recorded below. |
| Stage 7 — Q11 resolution support | committed and verified | Branch history includes Q11 per-port parameterized bind support; `examples/ip_test` run evidence is recorded below. |
| Stage 8 — Validation regressions | committed and verified | Branch history includes the `ip_test` bridge regression; exact build/run evidence is recorded below. |
| Stage 9 — Examples migration | committed and verified | Branch history includes `helloWorld` and `mixed` migrations; exact build/run evidence is recorded below. |
| Stage 10 — Protocol coverage extension | committed and verified | Branch history includes thunker improvements and wide packed protocol support; proto and unit-test evidence is recorded below. |
| Stage 11 — Variant-aware generated testbenches | committed and verified | Branch history includes variant-aware SystemC testbench generation; the authoritative execution record is [`plan-step-11-variant-aware-testbenches.md`](./plan-step-11-variant-aware-testbenches.md). |

No stage in this index is currently classified as `implemented in
working tree` only. If a future local code change reopens a stage, mark
that stage `implemented in working tree` until git history supports
`committed`.

## Remaining Deferred Decisions

- Language-native compile-time eval policy (D2), templated `prt()` formatting,
  and D10 bottom-up checking semantics remain deferred.
- Register-bus E3.1/E3.2 implementation and coverage are complete. The
  leaf-to-handler compatibility question and protocol-changer guidance remain
  optional follow-ups in `plan-register-bus-cross-interface-check.md`.
- C3.6, registration encapsulation, symbolic eval E5/E6, and unified YAML
  migration are closed and are not current follow-ups.

## Progress

Historical per-stage detail follows. Some older entries below use words
such as "landed", "landed in working tree", or "awaiting commit" from
the session in which they were written; interpret those as historical
wording only. The Active Stage Index above is the authoritative current
committed / implemented-in-working-tree / verified status model.

- **Stage 1 — Per-variant Config infrastructure.** Landed.
  - Step 1.1 — Per-variant Config emission. Landed.
  - Step 1.2 — Block class always templated. Landed.
- **Stage 2 — Factory key simplification.** Landed.
  - Step 2.1 — Factory API collapse. Landed.
  - Step 2.2 — Trampoline per-variant emission. Landed.
  - Step 2.3 — Caller migration. Landed.
- **Stage 3 — Container shape.** Landed.
  - Step 3.1 — Container per-instance member types. Landed.
  - Step 3.2 — Parent non-templated. Landed.
  - Step 3.3 — Channel-type derivation. Landed.
  - Step C3.9 — Canonical exact-width Verilated wrapper follow-up.
    Complete. The wrapper path now emits one include-only canonical
    parameterized SV body (`<block>_hdl_sv_wrapper.svh`) plus tiny
    per-variant top trampolines, and the SystemC / SV flattened HDL
    boundary uses active per-variant widths. The execution record is
    [`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md).
- **Stage 4 — addParam retirement.** Landed.
  - Step 4.1 — Drop `addParam` emission. Landed.
  - Step 4.2 — Constructor reads from Config. Landed.
  - Step 4.3 — `IP_NONCONST_DEPTH` absorbed. Landed.
  - Step 4.4 — Delete the runtime `addParam` / `getParam` API on
    `instanceFactory`. Landed in working tree. The two `addParam`
    overloads, the `getParam` accessor, and the private
    `getVariantParams()` static-map helper have been removed from
    `common/systemc/instanceFactory.{h,cpp}`. `git grep -F` confirms
    no surviving callers under `common/`, `pysrc/`, `templates/`,
    `examples/`, or the proto smoke test. `examples/mixed` no longer
    carries the `instanceFactory::getParam(...)` reads in
    `blockFBase.h` (now `Config::bob` / `Config::fred`), no longer
    emits the class-body `instanceFactory::addParam({...})` scaffold
    in `blockF.h`, and the hand-authored
    `verif/blocks/blockF_variant0/src/sc_main.cpp` has dropped its
    direct `addParam` call.
- **Stage 5 — Bottom-up ports schema.** Landed.
  - Step 5.1 — Schema and parser support. Landed.
  - Step 5.2 — Generator consumption. Landed.
  - Step 5.3 — Diagnostics for partial declarations. Landed.
- **Stage 6 — Thunker infrastructure (rdy_vld, req_ack).** Implementation
  complete; awaiting commit.
  - Step 6.1 — Thunker class headers. Landed in working tree
    (`builder/base/interfaces/rdy_vld/rdy_vld_port_thunker.h`,
    `builder/base/interfaces/req_ack/req_ack_port_thunker.h`). Each
    header carries two constructor overloads: a port-reference shape
    for the connectionMap up-side and an interface-base-reference
    shape (`<proto>_in_if<...>&`) for the connections up-side, so a
    parent-side channel binds directly without an intermediate port.
    Header-only smoke test under
    `proto/model/test/test_port_thunker.cpp` `static_asserts` both
    shapes (including a direct channel-reference construction) and
    that source-port arguments remain rejected.
  - Step 6.2 — Packed-form compatibility check. Landed in working tree
    inside `pysrc/processYaml.py::validatePorts` (projectCreate-time
    barrier; no DB schema change, no persisted annotation).
  - Step 6.3 — Thunker emission. Landed in working tree across
    `pysrc/intf_gen_utils.py`, `templates/systemc/classDecl.py`, and
    `templates/systemc/constructor.py`. Off by default; current example
    YAML produces no cross-interface binds and regenerates byte-identically.
- **Stage 7 — Q11 resolution support.** Landed in working tree.
  - Step 7.1 — YAML convention documentation. Landed in working
    tree. Section 5 of `rules/skills/design-architecture.md` now
    carries the "Per-Port Parameters (Q11 producer pattern)"
    sub-bullet with the full worked YAML (per-port parameters,
    structures, interfaces, ports declaration, variant binding,
    connection shape). `research-multi-config-bindings.md` Q11
    cross-references the new skill section.
  - Step 7.2 — Example exercising Q11. Landed in working tree.
    `examples/ip_test`'s `src` block now carries the Q11 per-port
    parameter shape (`OUT0_DATA_WIDTH` / `OUT1_DATA_WIDTH`) under
    a new `examples/ip_test/arch/yaml/src.yaml` file with matching
    `srcOut0St` / `srcOut1St` structures and `srcOut0If` / `srcOut1If`
    push_ack interfaces. `examples/ip_test/arch/yaml/ip_top.yaml`
    binds `uSrc` to the new `variantSrc0` variant and routes the
    two cross-Config connections through the consumer's
    `dstport: ipDataIf` end. After regen, `examples/ip_test/base/srcBase.h`
    is emitted as `template<typename Config> class srcBase` whose
    output ports use `srcOut0St<Config>` and `srcOut1St<Config>`,
    and `examples/ip_test/model/ip_top.h` carries two
    `push_ack_port_thunker<...>` member declarations after the
    `uIp0`/`uIp1` instance pointers, each instantiated with the
    Stage 6.1 connections-shape constructor in `ip_top.cpp`. The
    end-to-end run prints the expected `0xa5` and `0x5a` on the
    two consumer paths and terminates cleanly with `No error`; the
    earlier finalisation-assertion diagnostic was retired together
    with the Stage 8.2 / Stage 11 fixes.
    - **Generator side-effects.** Step 7.2 required three
      generator adjustments to satisfy Q11's cross-Config typing
      contract end to end. None expand the schema:
      - `pysrc/intf_gen_utils.py::_resolve_channel_config_override`
        now prefers the producer (src) end's leaf Config on
        connections whose dst end is a cross-interface bind.
        Without this, the parent-emitted channel would reference
        the consumer's Config — which lacks the producer's
        per-port parameter — and the channel template would fail
        to instantiate.
      - `pysrc/processYaml.py::getBDCrossInterfaceBinds`
        propagates the producer-side parent Config the same way
        and walks `ret['connectionPorts']` so block views whose
        only exposure to a cross-interface bind is the boundary
        port (e.g., the `ip` block view) observe the annotation.
        It also pulls the child interface's structures into the
        block's include set so the matching `<childContext>Config.h`
        is reachable for the emitted thunker member type.
      - `pysrc/processYaml.py::getBDPorts` swaps the per-port
        `interfaceKey` to the child's declared interface when the
        end is cross-interface, so the consumer's port emits
        with the consumer's own structure rather than the
        producer's.
      - `pysrc/processYaml.py::getBDIncludes` also aggregates the
        contexts of parameterizable subBlockInstances' Config
        structs so each container's class-declaration TU resolves
        `<childContext>Config.h` (e.g., `srcBase.h` referencing
        `ipLeafVariantLeaf0Config`).
      - `templates/systemc/blockRegistrar.py` now reads
        `block_has_own_params` and omits the `<Config>` template
        argument on the trampoline's `make_shared<...>` call for
        non-leaf parameterizable containers (Stage 3.2 alignment).
      - `templates/systemc/testbench.py` mirrors the DUT's
        cross-interface thunker members inside the external
        pseudo-block (one thunker per cross-interface bind in
        `connections`) and emits per-connectionMap local channels
        named `_ext_cm_<inst>_<port>` so contained instances'
        connectionMap ports complete binding during external
        elaboration.
    - **Worked example summary.** Producer block: `src`. Per-port
      parameters: `OUT0_DATA_WIDTH` (value 8, maxValue 128) and
      `OUT1_DATA_WIDTH` (value 12, maxValue 128). The over-64
      maximums intentionally force array-backed `_packedSt` storage
      while the bound Config widths remain below 64 bits. Producer variant:
      `variantSrc0` (binds both per-port parameters to match the
      `variant0` and `variant1` consumer Configs). Consumer block
      instances: `uIp0` (variant `variant0`, IP_DATA_WIDTH=8) and
      `uIp1` (variant `variant1`, IP_DATA_WIDTH=12). Connection
      file: `examples/ip_test/arch/yaml/ip_top.yaml`. Producer-side
      structure / interface definitions: `examples/ip_test/arch/yaml/src.yaml`.
- **Stage 8 — Validation regressions.** Landed in working tree.
  - Step 8.1 — Multi-Config-per-block regression. Landed in working
    tree. The maintained fixture is `examples/ip_test`: its
    `ip_top.yaml` binds `ip` to `variant0` (IP_DATA_WIDTH=8) and
    `variant1` (IP_DATA_WIDTH=70), the regenerated
    `examples/ip_test/model/ipConfig.h` emits the matching
    `ipVariant0Config` and `ipVariant1Config` structs, and
    `examples/ip_test/model/ipRegistrar.cpp` registers the two
    template instantiations `ip<ipVariant0Config>` and
    `ip<ipVariant1Config>` under their variant strings.
    `examples/ip_test/model/ip_top.cpp` then dynamic-casts each
    instance pointer to its per-variant `ipBase<...>` after the
    factory lookup. The regression is the maintained `examples/ip_test`
    build itself, exercised through the existing make targets:
    - `make -C examples/ip_test/rundir` compiles and links the SystemC
      model. The link succeeds only when both per-variant Config
      structs exist, both `ip<ipVariant*Config>` template
      instantiations are reachable through `ipRegistrar.cpp`, the
      `ip_top` external container instantiates the per-instance shared
      pointers with their concrete `ipBase<ipVariant*Config>` cast
      targets, and the `push_ack_port_thunker<srcOut0St<srcVariantSrc0Config>,
      ipDataSt<ipVariant0Config>>` / `<srcOut1St<...>, ipDataSt<ipVariant1Config>>`
      cross-Config bridges instantiate cleanly under their variant-
      specific bit widths.
    - `make -C examples/ip_test/verif/vl_wrap` runs verilator over the
      per-variant SV wrapper tops (`ip_variant0_hdl_sv_wrapper.sv`,
      `ip_variant1_hdl_sv_wrapper.sv`, `src_variantSrc0_hdl_sv_wrapper.sv`)
      that `` `include `` canonical include-only wrapper bodies
      (`ip_hdl_sv_wrapper.svh`, `src_hdl_sv_wrapper.svh`,
      `ipLeaf_hdl_sv_wrapper.svh`). The tops carry their bound
      `localparam`s in the parameter port list, so ports use exact
      symbolic active widths such as `[(IP_DATA_WIDTH + 1)-1:0]`
      while the Verilated pins resolve to 9 / 71 bits. The lint covers
      `rtl/ip.sv` at both per-variant parameter sets, `rtl/src.sv`
      at the variantSrc0 binding, and `rtl/ipLeaf.sv` instantiated
      from `rtl/src.sv` at LEAF_DATA_WIDTH=4 / LEAF_MEM_DEPTH=4.
    - RTL companion files this stage exercises:
      `examples/ip_test/rtl/ipLeaf.sv` is added (matching `ipLeaf`'s
      newly flipped `hasRtl: true`); `make newmodule` generates the
      module scaffold (parameter list, memory_if instances,
      `memory_dp` instantiation sized by LEAF_MEM_DEPTH), no hand
      body is required. `examples/ip_test/rtl/src.sv`'s hand-written
      stimulus body is repaired to use `srcOut0DataT` /
      `srcOut1DataT` (the Q11 per-port-parameterised types from
      `src_package.sv`) instead of the legacy `ipDataT` that no
      longer exists in `src`'s package import scope after the
      Stage 9.2 migration; the body now also drives the marker bit
      and a high-word constant (`0x2A << 64`) on the 70-bit output
      so RTL stimulus exercises a payload crossing the 64-bit packed
      boundary.
    - Stage 8.1 runtime gap closed: the
      `test_ip_structs<ipDefaultConfig>` startup check under
      `make -C examples/ip_test/rundir run` passes (the false
      positive was the `unpack_bits` defect retired under Stage 8.2)
      and the end-of-run finalisation Q_ASSERT no longer fires under
      `./build/run ip_top` (`No error`). The `make -C examples/ip_test
      VL_DUT=1` Verilated-wrapper link path is plausibly already
      covered by the Stage 11 `module_hdl_wrapper.py` rewrite but
      has not been re-verified independently of Stage 11's `ip`-only
      regression; tracked as a follow-on confirmation pass.
  - Step 8.2 — Cross-interface bridge regression. Landed in working
    tree. The maintained fixture extends `examples/ip_test` in
    parallel with the Q11 sibling-connection coverage; no separate
    project is introduced. A new `ipBridge` container holds two `ip`
    instances at the existing `variant0`/`variant1` parameterisations
    and exposes `data8If` / `data70If` non-parameterised parent ports.
    A new sibling `bridgeDriver` block produces those non-parameterised
    streams; each pair feeds one parent port via a sibling-level
    connection (non-cross-interface at the `ip_top` level), and
    `ipBridge` binds each parent port via `connectionMap` to the
    differently-Configed child's `ipDataIf` (cross-interface,
    push_ack → push_ack). Files and commands authoritative for this
    stage:
    - `examples/ip_test/arch/yaml/ipBridge.yaml` — new file. Declares
      the non-parameterised `data8T` / `data70T` types,
      `data8St` / `data70St` structures (marker + data field
      order/widths matching `ipDataSt` under `variant0`/`variant1` so
      the Stage 6.2 packed-form compatibility check passes),
      `data8If` / `data70If` push_ack interfaces, the `ipBridge`
      container block, the `bridgeDriver` stimulus block, and a
      separate `bridgeApbDecode` block type for the nested
      register-bus decoder (kept distinct from the top-level
      `apbDecode` block so the per-block port aggregation in
      `apbDecodeBase` does not merge two contexts with different
      connectivity — `uAPBDecode` owns `cpu_main` and dispatches to
      `uIp0`/`uIp1`/`uBridge`; `uBridgeAPBDecode` owns its own
      incoming `apbReg` and dispatches to `uBridgeIp0`/`uBridgeIp1`).
    - `examples/ip_test/arch/yaml/ip_top.yaml` — includes
      `ipBridge.yaml`; adds the new instances (`uBridgeDriver`,
      `uBridge`, `uBridgeAPBDecode`, `uBridgeIp0`, `uBridgeIp1`); adds
      the two sibling-level connections from
      `uBridgeDriver.out8`/`out70` to
      `uBridge.data8In`/`data70In`; adds the two cross-interface
      connectionMaps inside `ipBridge` (`data8In → uBridgeIp0.ipDataIf`,
      `data70In → uBridgeIp1.ipDataIf`). `uBridge` carries
      `addressGroup: top` so `uAPBDecode`'s generated decoder list
      includes `&apb_uBridge`; the bridge children carry
      `addressGroup: bridge` so `postParseRegister.py`'s "same level
      as decoder" check is satisfied by the in-container
      `uBridgeAPBDecode`.
    - `examples/ip_test/arch/yaml/exampleAddress.yaml` — adds the
      `bridge` AddressGroup with `decoderInstance: uBridgeAPBDecode`
      (no `primaryDecode`, so `postParseRegister.py`'s hierarchical
      decoder routing wires the parent register bus from
      `uAPBDecode` down through `ipBridge.apbReg` to
      `uBridgeAPBDecode` automatically).
    - `examples/ip_test/model/bridgeDriver.{h,cpp}` — hand-written
      stimulus. Two `SC_THREAD`s mirror `src.cpp`'s
      `driveOut0`/`driveOut1` pattern (`marker=1, data=0xA5` on
      `out8`; `marker=1, data.word[0]=0x5A, data.word[1]=0x2A` on
      `out70`) so `ipBase<Config>::dataHandler`'s existing marker and
      high-word assertions run end-to-end against both bridge
      children.
    - `examples/ip_test/model/ipBridge.{h,cpp}`,
      `examples/ip_test/model/bridgeApbDecode.{h,cpp}`,
      `examples/ip_test/base/ipBridgeBase.h`,
      `examples/ip_test/base/bridgeDriverBase.h`,
      `examples/ip_test/base/bridgeApbDecodeBase.h`,
      `examples/ip_test/model/ipBridgeIncludes.cppm`,
      `examples/ip_test/rtl/ipBridge_package.sv` — generated by
      `make newmodule` + `make gen`; no hand-edits outside the
      `GENERATED_CODE_END` markers.
    - Verification. `make -C examples/ip_test gen` produces an
      `ipBridge` class declaration carrying two cross-interface
      thunker members
      `push_ack_port_thunker< data8St, ipDataSt<ipVariant0Config> > thunker_uBridgeIp0`
      and
      `push_ack_port_thunker< data70St, ipDataSt<ipVariant1Config> > thunker_uBridgeIp1`
      (declared after the `uBridgeIp0`/`uBridgeIp1` instance pointers
      per Stage 6.3's ordering rule), and a constructor body that
      initialises each thunker with the parent port reference and the
      child's `ipDataIf` port.
      `make -C examples/ip_test/rundir` links the SystemC model;
      `make -C examples/ip_test/rundir run` produces
      `tb.ip_top.uBridge.uBridgeIp0 received data 0x000000000000000a5 marker 1`
      and
      `tb.ip_top.uBridge.uBridgeIp1 received data 0x2a000000000000005a marker 1`
      (plus the matching `tb.external.*` lines), and
      `ipBase<Config>::dataHandler`'s
      `Q_ASSERT(data.marker == 1, ...)` and
      `Q_ASSERT(data.data.word[1] == 0x2A, ...)` assertions both pass
      across the two bridge children. The end-of-run finalisation
      Q_ASSERT diagnostic that previously appeared at this site has
      been retired by the Stage 8.2 `unpack_bits` fix in concert with
      the Stage 11 testbench-template work; `./build/run ip_top`
      terminates with `No error`.
    - **Generator side-effects.** Stage 8.2 surfaced a pre-existing
      bug in the templated structures' generated `unpack()`:
      `templates/systemc/structures.py` emitted bare `pack_bits(...)`
      for array-backed parameterisable fields (line 1085) and for the
      misaligned nested-struct staging copy (line 1170), without
      zeroing the destination first and without masking the source
      word. Because `pack_bits` is an OR-based primitive that
      intentionally does not mask its source (the pack direction
      relies on that behaviour so in-storage overflow surfaces noisily
      through the `test_ip_structs` roundtrip canary), adjacent
      packed-form fields' bits — specifically
      `ipDataSt<Config>::marker` at packed position
      `IP_DATA_WIDTH` — leaked into the data field's storage under
      `unpack()`. The bug was masked at runtime since Stage 8.1
      because `ip_topConfig.cpp` short-circuited via the
      `test_ip_structs<ipDefaultConfig>::test()` startup assertion;
      the Stage 8.2 fixture both restores that canary and exercises
      the same path through two thunkers, so the failure became
      visible. The fix introduces a new unpack-direction sibling
      helper without changing `pack_bits`:
      - `common/systemc/bitTwiddling.{h,cpp}` adds
        `unpack_bits(uint64_t* dest, uint16_t destPos,
                     const uint64_t* src, uint16_t srcPos,
                     uint16_t bits)`,
        which masks each iteration's source word to `consume` bits
        before OR-ing into the destination. The header carries a
        comment block contrasting the contract with `pack_bits`:
        unpack legitimately encounters adjacent-field bits in the
        source and must drop them; pack legitimately encounters
        overflow bits that must propagate so the canary fires.
      - `templates/systemc/structures.py:1085` (the templated array
        unpack) now emits `memset((uint64_t *)&field, 0,
        sizeof(field))` to clear the field's storage, then
        `unpack_bits(...)` for the bit walk. The matching
        nested-struct staging path at `structures.py:1170` becomes
        `unpack_bits(...)` (no `memset` needed — `_tmp{0}` is
        already value-initialised at the staging declaration site).
        `pack` codegen (lines 1261/1264) is unchanged: pack still
        uses `pack_bits` and still relies on the pre-pack
        `memset(&_ret, 0, _byteWidth)` so the only bits in `_ret`
        come from source-field reads — any overflow in those reads
        continues to flow through into the packed form for the
        `test_ip_structs` canary to catch.
      The fix is library + template only; no schema changes, no
      block-data view changes. With both fixes in place,
      `test_ip_structs<ipDefaultConfig>::test()` passes for the first
      time since Stage 8.1 and the bridge end-to-end data flow
      validates correctly.
    - **Apb decode review note.** During design review the two
      `apbDecode` instances were observed to have incompatible
      connectivity (the top-level decoder owns `cpu_main` and three
      dispatch outputs at `ip_top`; the nested decoder owns its
      incoming `apbReg` and two dispatch outputs at `ipBridge`).
      The single-block emission would have merged both contexts into
      one `apbDecodeBase` with all seven ports, and
      `apbDecode.cpp`'s generated decoder list would have referenced
      whichever context was emitted last. Splitting into `apbDecode`
      (top-level) and `bridgeApbDecode` (nested) keeps each block's
      emitted port set and decoder list aligned with its sole
      instance.
  - Step 8.3 — Producer-with-per-port-parameters regression. Landed
    in working tree. The maintained fixture remains
    `examples/ip_test`: the existing `src` block already carries the
    Q11 per-port-parameter shape under Stage 7.2 / Step 9.2, and the
    Stage 8.3 work makes that coverage explicit at runtime so the
    Q11 producer pattern is exercised — not just snapshotted — by the
    make pipeline. The regression is functional: `make run` either
    produces the named markers / receive lines, or a Q_ASSERT fires.
    Artifacts:
    - `examples/ip_test/model/src.cpp` — hand-written
      `driveOut0` / `driveOut1` (below the constructor's
      `GENERATED_CODE_END` marker) emit a `[Stage 8.3]` marker log
      line and `Q_ASSERT` that `Config::OUT0_DATA_WIDTH == 8` /
      `Config::OUT1_DATA_WIDTH == 70` before pushing. Any future
      regression that decouples the producer's per-port widths from
      the bound consumer Configs surfaces as a hard Q_ASSERT failure
      rather than as silent thunker truncation. The existing
      `ipBase<Config>::dataHandler` `Q_ASSERT(data.marker == 1, ...)`
      and (for the 70-bit variant) `Q_ASSERT(data.data.word[1] == 0x2A, ...)`
      checks on the consumer side already prove the marker bit and
      high-word both survive the round-trip through each thunker;
      Stage 8.3 adds the matching producer-side parameter-consistency
      check.
    - `examples/ip_test/arch/yaml/src.yaml` — header comment carries
      the Stage 8.3 documentation anchor describing the runtime
      regression and the named log markers.
    - Validation (the regression itself is `make run`):
      `make -C examples/ip_test gen` regenerates only the
      hand-written portion of `src.cpp`. `make -C examples/ip_test/rundir`
      rebuilds the model and links cleanly.
      `make -C examples/ip_test/rundir run` produces
      `src:tb.ip_top.uSrc [Stage 8.3] Q11 out0 per-port width = 8 bits`
      and
      `src:tb.ip_top.uSrc [Stage 8.3] Q11 out1 per-port width = 70 bits`
      lines immediately before the existing push lines, and both
      `ip:tb.ip_top.uIp0 received data 0x000000000000000a5 marker 1`
      / `ip:tb.ip_top.uIp1 received data 0x2a000000000000005a marker 1`
      lines confirm round-trip across each thunker with the producer's
      per-port Config matching the consumer's bound Config. None of
      the Q_ASSERTs fire.
    - End-of-run state. The finalisation Q_ASSERT diagnostic that
      previously trailed Steps 7.2 / 8.1 / 8.2 / 8.3 no longer fires;
      `./build/run ip_top` terminates with `No error`. All Stage 8.3
      acceptance criteria pass without trailing diagnostics.
- **Stage 9 — Examples migration.** Landed.
  - Step 9.1 — `examples/helloWorld`. Landed in working tree. The
    plan's premise held: `helloWorld` declares no parameterizable
    blocks (no `isParameterizable`, `variants`, `ipParameters`, or
    `params:` in `arch/`), so the only Path C surface is the
    factory-API caller signature drop, and that is already in place.
    Verified against the current generator:
    - `common/systemc/instanceFactory.h` carries only the
      `(blockType, variant)` key shape — no `configTag` parameter and
      no `noConfigTag` sentinel.
    - Generated call sites match: `createInstance("", "uTop", "top", "")`
      passes the variant string only (empty string for the anonymous
      variant), and the inline `registerBlock("<block>_model", lambda, "")`
      registrations use the `(blockType, factoryFn, variant)` overload.
      Non-parameterizable blocks register inline in their own `.cpp`;
      no per-variant `*Registrar.cpp` trampolines are emitted, which is
      correct here.
    - No `getParam` / `addParam` references remain (Stage 4 clean), and
      `model/helloWorldTopConfig.h` carries an empty config section —
      no residual `defaultConfig` struct.
    - A clean DB rebuild, regen, model build, and `./build/helloWorld`
      run complete both `test_push_ack` and `test_pop_ack` with
      `No error`.
    - Regeneration is **not** byte-identical against the committed
      baseline; five files change, but none are Path C surfaces:
      `includes/{consumer,producer,top}_base.h` drop the
      `See plan-block-registration.md.` reference from the force-link
      anchor comment (builder/base "no plan-specific comments" rule),
      and `model/{producer,consumer}.h` drop the
      `#include "helloWorldTopIncludes.h"` aggregate include from the
      reusable leaf headers (the container `top.h` is unchanged). These
      diffs predate this assessment; a regeneration commit brings
      `helloWorld` byte-current.
  - Step 9.2 — `examples/ip_test`. Landed in working tree. The
    primary parameterized example is now on Path C end-to-end: the
    `src` block carries Q11 per-port parameters, each cross-Config
    bind goes through a `push_ack_port_thunker`, `srcBase.h`
    regenerates as a templated `srcBase<Config>` with per-port
    structure types, and `ip_top` carries two thunker members. See
    Stage 7.2 above for the worked example summary and the
    generator side-effects this migration required.
  - Step 9.3 — `examples/mixed`. Landed in working tree; full
    `make db` / `gen` / `rundir` / `rundir all VL_DUT=1` pipeline
    passes, and `./build/run mixed`, `--vlInst tb.mixed.uBlockB.uBlockF0`,
    and `--vlInst tb.mixed` all terminate with `No error`. `blockF`
    regenerates as `template<typename Config> class blockFBase` reading
    `Config::bob` / `Config::fred` directly;
    `blockF.h` no longer carries the in-class
    `instanceFactory::addParam({...})` scaffold; a new
    `blockF.cpp`-companion `blockFRegistrar.cpp` trampoline registers
    `blockF<blockFVariant0Config>` and `blockF<blockFVariant1Config>`
    against the factory; `mixedConfig.h` emits the per-variant
    `blockFVariant0Config` / `blockFVariant1Config` structs with the
    resolved override values; the Verilator block-level wrapper
    inherits `blockFBase<Config>` with per-variant typedefs binding
    the matching Config; and the hand-authored
    `verif/blocks/blockF_variant0/src/sc_main.cpp` has dropped its
    direct `instanceFactory::addParam({...})` call.
    - **YAML side.** `mixed.yaml` declares `bob` / `fred` as same-name
      `ipParameters` constants (with `maxValue`) so each block param has
      a backing constant, as `projectCreate` now requires; the variant
      bindings keep their symbolic form (`value: BOB0` / `BOB1`).
    - **Generator side-effects.** Several generator adjustments were
      required to unblock `blockF`'s migration. None expand the schema.
      - `pysrc/processYaml.py::calcBlockConfigInfo` now also flags a
        block as `isParameterizable: true` when it declares its own
        `params:` (the `blockF` shape, where no structure on the
        surface is parameterizable). Without this, per-variant Config
        descriptors and the `<block>Registrar.cpp` trampoline were
        skipped.
      - `pysrc/processYaml.py::_buildVariantConfigDescriptors`
        resolves `valueKey`-referenced constants from `parametersvariants`
        rows when populating per-variant override values. This lets
        symbolic references like `bob: BOB0` surface as numeric
        literals in the emitted `blockFVariant0Config` struct (matching
        the ip_test reference shape).
      - `templates/systemc/module_hdl_wrapper.py` now emits the
        Verilator wrapper as `template<typename DUT_T, typename Config>`
        and binds per-variant Config in the typedefs when the block
        has its own `params:` AND none of its port structures depend
        on `Config` (so BFM/HDL_IF declarations don't carry `<Config>`).
        Blocks with cross-Config port structures (ip_test's `ip`, `src`)
        continue to use `defaultConfig` consistently across inheritance
        and BFM types; ip_test regenerates byte-identically.
      - `templates/systemc/headers.py::_include_context_modules` now
        treats a missing `fileMapKey` in `data['includeFiles']` as an
        empty include set rather than raising `KeyError`, so files
        whose scaffold still references a retired include mode (e.g.,
        `examples/mixed`'s legacy `--fileMapKey=include_hdr` headers
        during the cppm migration) no longer block regeneration of
        unrelated targets.
      - `templates/systemVerilog/moduleRegs.py::section_module_params`
        guards the inherited-params emission so a register-bearing block
        with no `params:` (`None`) emits an empty parameter string,
        mirroring the owning-module emitter
        `moduleInterfacesInstances.py`. Exposed once `make db` passed
        for `blockA` / `blockB` (register handlers without params).
      - `templates/systemVerilog/module_hdl_wrapper.py::render_trampoline`
        now emits the block's package imports (via the shared
        `importPackages` helper, as the canonical body already does) so a
        binding value written as a project constant resolves by name in
        the trampoline's parameter port list. The trampoline keeps the
        symbol (`localparam bob = BOB0`); resolution stays at SV package
        scope rather than being inlined by the generator. `ip_test`
        trampolines gain a valid package-import line and still build /
        run with `VL_DUT=1`.
- **Stage 10 — Protocol coverage extension.** Landed in working tree.
  - Step 10.1 — `push_ack_port_thunker.h`. Landed in working tree.
    `builder/base/interfaces/push_ack/push_ack_port_thunker.h`
    mirrors the rdy_vld / req_ack thunker shape but preserves the
    push_ack request / acknowledge handshake (`pushReceive` →
    downstream `push(magic)` → `up->ack()`).
    `interfaces/push_ack/push_ack_if.yaml` initially declared
    `sc_channel.thunker: true`; the flag was retired in Stage 10.4
    once the on-disk presence of `push_ack_port_thunker.h` became
    the canonical eligibility signal. The proto smoke test under
    `proto/model/test/test_port_thunker.cpp` covers both
    constructor overloads and confirms source-side rejection, and
    `proto/model/Makefile` was extended with the push_ack include
    directory and the new header in `test_port_thunker.o`'s
    dependencies.
  - Step 10.2 — `axi_read_port_thunker.h` and
    `axi_write_port_thunker.h`. Landed in working tree.
    `builder/base/interfaces/axi_read/axi_read_port_thunker.h`
    bridges the AXI read address / data handshake
    (`up->receiveAddr` → `m_chDown.sendAddr` →
    `m_chDown.receiveData` → `up->sendData`); the template
    parameter list is `<UpA, UpD, DownA, DownD>` matching
    `axi_read_if.yaml::parameters`.
    `builder/base/interfaces/axi_write/axi_write_port_thunker.h`
    bridges the address / data / response triple; the template
    parameter list is `<UpA, UpD, UpS, DownA, DownD, DownS>`
    matching `axi_write_if.yaml::parameters` (addr / data / strb).
    Both headers cover single-beat semantics only — multi-beat
    burst handling remains guarded by the Stage 6.2 packed-form
    check and is documented in the file header. The proto smoke
    test and `proto/model/Makefile` were extended for both new
    headers; `static_assert` coverage confirms both constructor
    overloads and source-side rejection.
  - Step 10.3 — `apb_port_thunker.h`. Landed in working tree.
    `builder/base/interfaces/apb/apb_port_thunker.h` drives the
    APB request / completion handshake. The thunker calls
    `up->reqReceive(isWrite, addrIn, dataIn)`, pack-converts the
    address (and the write data on writes), invokes
    `m_chDown.request(isWrite, addrOut, dataOut)`, and — only on
    reads — pack-converts the response back and calls
    `up->complete(dataUp)`. Writes are not completed by the
    thunker: `apb_channel::reqReceive()` already acknowledges them
    and `apb_channel::complete()` asserts on writes. The proto
    smoke test and `proto/model/Makefile` were extended;
    `unittest/test_thunker_view.py` adds `apb` to the
    payload-ordering coverage and replaces the legacy
    `sc_channel.thunker: false` diagnostic test with one that
    confirms no-struct protocols such as `notify_ack` do not enter
    the thunker path.
  - Step 10.4 — Generator generalisation. Landed in working tree.
    `pysrc/processYaml.py::_checkThunkerSupport` and
    `pysrc/processYaml.py::buildThunkerView` no longer read
    `sc_channel.thunker`; eligibility now requires at least one
    `datatype: struct` parameter under
    `interface_defs.parameters`. The generated C++ include names
    the protocol-specific `<channelType>_port_thunker.h`; normal
    include-path handling and the build catch any missing header.
    `sc_channel.thunker: true` has been removed from every
    interface YAML under
    `builder/base/interfaces` (`builder/pro/interfaces/lmmi`
    never carried the flag); the schema's
    `thunker: optional(false)` entry is retained as a no-op for
    backwards compatibility but is no longer read. Regeneration of
    `examples/ip_test` is byte-identical against the
    pre-cleanup tree because that example exercises only push_ack
    thunkers, which were already eligible under Stage 10.1.
    - Stage 6.1 thunker headers (`rdy_vld`, `req_ack`) were
      simultaneously corrected to invoke `pack()` via the
      generator's out-parameter signature
      (`void pack(_packedSt& _ret) const`) rather than the
      proto-test-only return-value form, so all three thunkers
      compile against generated payload structures.
    - Wide `_packedSt` bridge support landed after Stage 10.4:
      all protocol thunkers now route packed payload conversion
      through `copy_packed_bits(...)`, covering scalar and
      array-backed packed forms without relying on cross-type
      `static_cast`.
- **Stage 11 — Variant-aware generated testbenches.** Complete on this
  branch. All six sub-steps (11.1 – 11.6) have landed against
  `examples/ip_test::ip` as the maintained fixture:
  - Generated TB / External / Config skeletons carry
    `GENERATED_CODE_PARAM --block=ip --variant=variant0` and bind to
    `ipVariant0Config` consistently; the DUT factory lookup is
    called with `"variant0"`.
  - `ipExternal::stimulusThread` drives a directed `push_ack`
    transaction (marker=1, data.word[1]=0x2A) and votes end-of-test;
    `./build/run ip` ends with `No error`.
  - `templates/systemc/module_hdl_wrapper.py` now emits a
    Config-templated wrapper (`template<typename DUT_T, typename
    Config>`) for every block that declares own `params:`. Per-variant
    `using` typedefs bind `Config = <block><Variant>Config` (e.g.
    `ipVariant0Config`, `ipVariant1Config`). Blocks parameterizable
    only through contained children (`ip_top`) keep the non-Config-
    templated wrapper. `make -C examples/ip_test/rundir all VL_DUT=1`
    builds clean, and `./build/run ip --vlInst tb.ip` runs the same
    directed check through the Verilated DUT to `No error`.
  - See [`plan-step-11-variant-aware-testbenches.md`](./plan-step-11-variant-aware-testbenches.md)
    for the per-sub-step record, including the incidental fixes
    landed alongside Steps 11.5 and 11.6 (`ip_top_tb`
    `--excludeInst=u_ip_top` correction, `set_test_names` wiring,
    `q_assert.cpp` non-thread `wait()` gating, stale orphan template
    line in `ipLeaf_hdl_sc_wrapper.h`).

## Goal

Adopt Path C across the generator, the SC runtime, and the YAML
schema. Variants and Configs collapse to a single dimension: each
variant maps 1:1 to a Config policy in C++ and 1:1 to a parameter set
in SystemVerilog. Outcomes:

- Every parameterizable block is emitted as a class template
  `template<typename Config> class B { ... };` whose source text is
  project-independent and variant-independent.
- Per-variant Config structs replace the auto-derived
  `<context>DefaultConfig` special case.
- The factory key collapses from `(blockType, variant, configTag)` to
  `(blockType, variant)`. The `configTag` infrastructure and the
  `noConfigTag` sentinel retire.
- The `addParam` / `getParam` runtime path retires. Block constructors
  read parameter values from `Config::*` directly.
- Container member types follow the connected child's Config exactly
  (D4 Option (a)). Channels in the parent are typed by the connected
  child's Config (D5).
- A bottom-up `ports:` map joins the YAML schema as the canonical way
  for parameterizable blocks (and any block that prefers explicit
  declaration) to expose port shape (D10).
- Cross-interface binds — including the connectionMap-driven external-
  boundary case — are bridged by a generator-emitted per-interface
  thunker class (Q10/R2). The thunker holds the IP-side channel,
  performs the elaboration-time bind to the child's port, and runs a
  forwarding thread that round-trips through `pack()` / `unpack()`.
- Producers with multiple differently-parameterised outputs declare
  per-port parameters in their Config (Q11 resolution); each
  cross-Config bind is a normal cross-interface bind handled by the
  thunker.

## Decisions Adopted

The decisions below are restated as one-line summaries; full text and
rationale live in `research-multi-config-bindings.md`.

- **D1** — Block class is always emitted as a template; one Config
  per variant (or one anonymous variant for blocks with none); naming
  `<block>Config` (anonymous) or `<block><Variant>Config` (named);
  intra-block dedup for byte-identical variants; hierarchical
  label-only variants supported.
- **D2** — Eval re-evaluation under variant overrides remains in
  `processYaml.py` against per-variant override sets; language-native
  compile-time eval is deferred to a follow-up plan step.
- **D3** — Factory key collapses to `(blockType, variant)`. Anonymous
  variant uses the empty string. `configTag` and `noConfigTag` retire.
- **D4** — Container member types reference per-instance concrete
  Configs: `std::shared_ptr<ipBase<ipVariant0Config>> uIp0;`.
- **D5** — Parent containers are non-templated. Channels in the
  parent are typed by the connected child's Config (or by a producer
  block's per-port parameter where applicable). Cross-Config binds
  go through a thunker (Q10/R2).
- **D6** — Subsumed by D4. Testbenches are fully YAML-declared; DUT
  cast sites follow per-instance concrete Config types. Follow-on
  Stage 11 extends this to generated `hasTb` harnesses whose DUT block
  itself declares variants; today those harnesses still default to the
  block context's `defaultConfig` and an empty variant string.
- **D7** — Verilated wrappers and tandem registration follow the same
  `(blockType, variant)` key shape; deeper migration is tracked in
  the block-registration plan.
- **D8** — All variants share one address map. Cross-variant
  `maxValue` sizing is preserved; `calcAddresses` already does the
  union.
- **D9** — `addParam` / `getParam` retired. Block constructors read
  `Config::*` directly. `IP_NONCONST_DEPTH` becomes a normal SV
  parameter and a normal Config field.
- **D10** — Bottom-up `ports:` declaration. A block (parameterizable
  or not) may declare its ports as a dict keyed by port name, with
  `interface` and `direction`. Top-down inference from `connections:`
  / `connectionMaps:` is retained for blocks that prefer it.
- **Q10 / R2** — Thunker class with encapsulated channel, packed-form
  `pack()`/`unpack()` round trip with `static_cast` on the packed
  value, `_bitWidth` exact-match compatibility check, header
  placement per-interface alongside the channel header.
- **Q11 (closed)** — Producers with multiple differently-parameterised
  outputs declare per-port parameters in their Config; each
  cross-Config bind is a normal cross-interface bind handled by the
  Q10/R2 thunker.

## Scope

In scope:

- All generator templates and `pysrc/` passes that emit Config
  structs, block class declarations, container member declarations,
  channel declarations, factory registrations, factory callers,
  cross-interface bind sites, and `addParam` / `getParam` calls.
- All SC runtime code under `builder/base/common/systemc/` (factory
  API and lookup) and per-protocol headers under
  `builder/base/interfaces/<protocol>/` /
  `builder/pro/interfaces/<protocol>/` (thunker class additions).
- YAML schema additions for `ports:` (D10) and the per-port parameter
  shape used by Q11's resolution.
- Migration of CI critical-path examples (`examples/ip_test`,
  `examples/helloWorld`, `examples/mixed`) in lockstep with generator
  changes.

Out of scope (deferred):

- D2's language-native compile-time eval (`parameter` /
  `localparam` in SV; `Config` field in C++).
- Detailed mechanics of partial bottom-up declarations interacting
  with top-down inference at conflict (D10 final mechanics).
- Further Verilated-wrapper build/link experiments such as Verilating
  one parameterized top multiple times with Verilator parameter
  overrides. The landed C3.9 path keeps per-variant top names and
  factory registration unchanged.
- Tandem-pair registration record shape (tracked separately in
  `plan-block-registration.md` Plan-9).
- Selective module-export refinements; classic-header / module shape
  decisions remain governed by the block-registration plan.
- Source-port thunking. Step 6 bridges destination-side endpoints
  only (`<proto>_in<...>` on the child end). Cross-interface binds
  whose child-end direction is `src` are rejected by the generator's
  cross-interface predicate. Adding a source-side thunker — and the
  matching emission rules — is tracked alongside the Stage 10
  protocol coverage extension.

## Implementation Stages

Stages are listed in dependency order. Each stage is a small set of
implementation steps; each step is sized to land independently with
its own validation. Any step that introduces a generator emission
change is paired with a regeneration and build of the CI critical-
path examples.

### Stage 1 — Per-variant Config infrastructure

The Config struct shape changes from `<context>DefaultConfig` (one
per parameterizable block) to one struct per variant. Block class
text becomes project- and variant-independent; the project-specific
TU is the trampoline.

- **Step 1.1 — Per-variant Config emission.** Extend the per-block
  Config-policy emission (today driven by
  `plan-parameterizable-config-template.md`) to emit one struct per
  variant the project's instance tree binds. Naming follows D1
  (`<block>Config` for the anonymous variant; `<block><Variant>Config`
  for named variants). Intra-block dedup folds byte-identical
  variants to a single struct, preserving variant identity at the
  factory-key level.
  - Templates touched: `templates/systemc/configPolicy.py` (or
    equivalent), `templates/systemc/baseClassDecl.py`.
  - `pysrc/processYaml.py::projectCreate.calcBlockConfigInfo()`
    extends to populate a per-variant Config descriptor (replaces
    the singular `defaultConfig` field; see
    `plan-block-config-postprocess.md`).
- **Step 1.2 — Block class always templated.** Every block flagged
  `isParameterizable` is emitted as `template<typename Config> class
  B { ... };` regardless of declared variants. Source text becomes
  project- and variant-independent.
  - Templates touched: `templates/systemc/classDecl.py`,
    `templates/systemc/baseClassDecl.py`,
    `templates/systemc/constructor.py`.
  - For blocks with no declared variants, the per-block Config
    struct (`<block>Config`) is the anonymous-variant Config; the
    template instantiation in the trampoline names it.

### Stage 2 — Factory key simplification

The factory's `configTag` dimension retires; the variant string is
now the unique key.

- **Step 2.1 — Factory API collapse.** Drop the `configTag`
  parameter from `instanceFactory::registerBlock(...)` and
  `instanceFactory::createInstance(...)`. Drop the `noConfigTag`
  sentinel. Lookup key becomes `(blockType, variant)`. Variant
  fallback to the empty string remains as the lookup-time fallback
  for blocks with anonymous variants.
  - Files touched: `common/systemc/instanceFactory.{h,cpp}`.
- **Step 2.2 — Trampoline per-variant emission.** Update
  `templates/systemc/blockRegistrar.py` to emit one
  `registerBlock(...)` lambda per variant, naming the per-variant
  Config struct from Stage 1.1. The lambda constructs
  `make_shared<B<<block><Variant>Config>>`. `addParam(...)` calls
  retire (Stage 4.1).
- **Step 2.3 — Caller migration.** Every generator-emitted
  `instanceFactory::createInstance(...)` call drops the `configTag`
  argument and passes the variant string only. Anonymous-variant
  callers pass the empty string.
  - Templates touched: `templates/systemc/constructor.py`,
    `templates/systemc/testbench.py`,
    `templates/fileGen/fileGen.py`,
    `templates/systemc/module_hdl_wrapper.py`,
    `templates/systemc/blockRegs.py`.

### Stage 3 — Container shape

Container member types and channel types follow per-instance Configs.
The parent stops being a class template.

- **Step 3.1 — Container per-instance member types.** The generator
  emits each parameterizable child's `shared_ptr` typed by the
  child's variant Config (D4 Option (a)). Casts at construction are
  `std::dynamic_pointer_cast<<B><<Variant>Config>>(...)`.
  - Templates touched: `templates/systemc/classDecl.py`,
    `templates/systemc/constructor.py`.
- **Step 3.2 — Parent non-templated.** Drop any
  `template<typename Config>` on parent containers. Each parent
  becomes a non-templated class.
  - Templates touched: `templates/systemc/classDecl.py`,
    `templates/systemc/baseClassDecl.py`.
- **Step 3.3 — Channel-type derivation.** Channels in the parent are
  typed by the connected child's Config (or by a producer block's
  per-port parameter under Q11). The generator's connection-walking
  pass derives each channel's type from the connection's endpoints.
  - Templates touched: `templates/systemc/constructor.py`,
    relevant connection-walk helpers in
    `pysrc/intf_gen_utils.py` /
    `pysrc/processYaml.py`.
- **Step C3.9 — Canonical exact-width Verilated wrapper follow-up.**
  Complete. The Verilated wrapper path now emits one canonical
  parameterized SV wrapper body per parameterizable block plus tiny
  per-variant top-module trampolines, with exact active-width
  flattened HDL boundaries on both the SV and SystemC sides. The
  execution plan and validation record are tracked in
  [`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md).
  The landed shape keeps the existing `(blockType, variant)` factory
  and Verilator top-module names intact:
  - `config/project.yaml` adds a `vlSvWrapBody` file-generation entry
    gated by `isParameterizable` and `hasVl`.
  - `templates/fileGen/fileGen.py` scaffolds the generated
    `<block>_hdl_sv_wrapper.svh` body with normal generated-region
    ownership.
  - `templates/systemVerilog/module_hdl_wrapper.py` renders either
    the canonical body, a variant trampoline, or the unchanged
    non-parameterized single wrapper.
  - `templates/systemc/module_hdl_wrapper.py` emits Config-dependent
    `sc_bv<<Struct><Config>::_bitWidth>` HDL bridge types where the
    payload is parameterized; fixed hdlparam-derived signals such as
    APB stay literal-width.
  - `include/make/a2c-vl-wrap.mk` filters the Verilated top list to
    `*.sv`, so generated `.svh` bodies are maintained by generation
    but never elaborated as standalone tops.
  Validation: `make -C examples/ip_test/verif/vl_wrap`,
  `make -C examples/ip_test/rundir all VL_DUT=1`, `make run VL_DUT=1`,
  and `make regr` passed for `ip_test`. `make -C examples/mixed/rundir
  all VL_DUT=1` now also passes; the earlier `make db` failure was the
  missing `bob` / `fred` backing `ipParameters` constants, resolved
  under Step 9.3.
  - **Wrapper axis, cross-level note (2026-07-17):** the C3.9 wrapper path
    is validated only for the monolithic single-project case. When a
    higher-level (composition) project declares an ADDITIONAL variant of a
    reusable sub-component, per-variant wrapper ownership moves to the
    immediate ASSEMBLING project (Direction A: each assembler owns the concrete
    wrappers for foreign variants it both declares and instantiates). P1's
    SC-path Config blocker is resolved by the landed S3-H (composed `ip_test`
    clean rebuild builds/runs No error); P3's contract
    is settled and P2 remains gated on the coupled composition/registrar work;
    see
    [`plan-cross-level-variant-wrappers.md`](./plan-cross-level-variant-wrappers.md).

### Stage 4 — addParam retirement

Block constructors read parameter values from `Config::*` directly;
the runtime parameter table goes away.

- **Step 4.1 — Drop `addParam` emission.** Trampolines stop emitting
  `instanceFactory::addParam(...)` calls. The `addParam` /
  `getParam` API in `instanceFactory.{h,cpp}` is removed.
- **Step 4.2 — Constructor reads from Config.** Update block
  constructor templates so that any parameter formerly read via
  `getParam(...)` is read from `Config::*`. The block class is
  already templated on `Config` from Stage 1.2, so the access is
  direct.
  - Templates touched: `templates/systemc/constructor.py` and any
    block-body emitter that referenced `getParam`.
- **Step 4.3 — `IP_NONCONST_DEPTH` absorbed.** The "no backing
  constant" pattern becomes a normal Config field. YAML schema drops
  the special distinction; the generator emits the field exactly
  like any other parameter.

### Stage 5 — Bottom-up ports schema

A new schema surface lets blocks declare their port shape
explicitly.

- **Step 5.1 — Schema and parser support.** Accept a `ports:` map
  under each block, keyed by port name, with `interface` and
  `direction` (`src` / `dst`) values. Validate uniqueness within a
  block.
  - Files touched: `pysrc/schemaCheck.py` /
    `pysrc/yamlSchema.py`,
    `pysrc/processYaml.py`.
- **Step 5.2 — Generator consumption.** Where a block declares
  `ports:`, use the declared shape directly. Where it does not, fall
  back to top-down inference from `connections:` /
  `connectionMaps:` as today.
  - Files touched: `pysrc/intf_gen_utils.py` and the connection-walk
    helpers.
- **Step 5.3 — Diagnostics for partial declarations.** When a block
  declares some ports under `ports:` and others appear only via
  connections, emit a diagnostic naming the missing port and the
  YAML files involved. Final mechanics are deferred (see "Out of
  scope"); minimal "name the offending port" coverage is in scope.

### Stage 6 — Thunker infrastructure (rdy_vld, req_ack)

The thunker class is added per protocol; the generator emits one
thunker member per cross-interface bind.

- **Step 6.1 — Thunker class headers.** Add
  `rdy_vld_port_thunker.h` to
  `builder/base/interfaces/rdy_vld/` and
  `req_ack_port_thunker.h` to
  `builder/base/interfaces/req_ack/`. Class form per R2: each thunker
  owns the IP-side channel, performs the elaboration-time
  `downPort(m_chDown)` bind, spawns the forwarding thread via
  `sc_spawn`, and runs the forwarding loop with
  `outVal.unpack(static_cast<typename DownT::_packedSt>(inVal.pack()))`.
  Two constructor overloads cover the two cross-interface shapes:
  - `(name, <proto>_in<UpT>& upPort, <proto>_in<DownT>& downPort,
    blockName)` — connectionMap up-side, where the up endpoint is a
    parent port. The port's bound interface is resolved lazily on the
    first iteration of the forwarding thread (sc_port binding is
    complete by the time the spawned thread first runs).
  - `(name, <proto>_in_if<UpT>& upIface, <proto>_in<DownT>& downPort,
    blockName)` — connections up-side, where the parent-side channel
    is passed directly through its interface base. `<proto>_channel<T>`
    publicly inherits `<proto>_in_if<T>`, so the channel reference
    binds to this overload without an intermediate port.

  The destination-side `<proto>_in<DownT>&` argument is unchanged
  between overloads. Source-port thunking (the up endpoint being a
  `<proto>_out<...>` port) is rejected by the generator and remains
  out of scope (see "Out of scope" below).
- **Step 6.2 — Packed-form compatibility check.** Extend the YAML
  processor to validate, on every connectionMap or connection whose
  endpoint interfaces differ:
  - same meta-protocol (rdy_vld with rdy_vld, etc.);
  - same field count and order;
  - same field names;
  - per-field `_bitWidth` exact match (under bound Config for
    parameterized fields);
  - same bit positions in the packed form.
  On failure: hard-error naming each offending field and pointing at
  both YAML files.
  - Files touched: `pysrc/processYaml.py`,
    `pysrc/intf_gen_utils.py`.
- **Step 6.3 — Thunker emission.** When a connection or
  connectionMap is detected as cross-interface and passes the
  compatibility check, the generator emits one thunker member
  declaration and one initialiser-list entry in the surrounding
  container, with the declaration ordered after the child instance
  pointer. Generator output is exactly two lines per bind. The
  up-side argument in the initialiser-list entry differs by shape:
  for a connectionMap the generator passes the parent port reference
  (`this->parentPortName`); for a connection the generator passes the
  parent-side channel member directly. The two Step 6.1 constructor
  overloads pick up the matching shape without any further emission
  branching.
  - Templates touched: `templates/systemc/classDecl.py`,
    `templates/systemc/constructor.py`.

### Stage 7 — Q11 resolution support

Producers with multiple differently-parameterised outputs declare
per-port parameters. The generator does not need a special branch;
this stage records the YAML conventions and validates an example
exercises the path.

- **Step 7.1 — YAML convention documentation.** Write up the
  per-port-parameter convention in the relevant skill / README:
  blocks with multiple differently-parameterised outputs declare
  one (or more) parameters per port and reference them in the
  port's structure type via the block's Config schema.
  - **Landing location:** the `design-architecture` skill at
    `builder/base/rules/skills/design-architecture.md`, section 5
    "Parameterizable IP Parameters", sub-bullet "Per-Port Parameters
    (Q11 producer pattern)". The skill is the document arch2code
    authors read when defining new blocks; the per-port-parameter
    convention sits alongside the existing `ipParameters` guidance
    rather than diluting `plan-parameterizable-config-template.md`
    (Phase 2 implementation plan) or duplicating the worked example
    that already lives in `research-multi-config-bindings.md` Q11.
  - **Cross-reference:** `research-multi-config-bindings.md` Q11
    carries a pointer to the new skill section so the worked
    example and the YAML convention stay discoverable from each
    other.
- **Step 7.2 — Example exercising Q11.** Update or create an
  example whose producer has two outputs with different parameter
  values. Confirm the generator emits two cross-interface binds (two
  thunkers) and the build succeeds. Candidate: a refactored
  `examples/ip_test` so that `uSrc` carries
  `OUT0_DATA_WIDTH` and `OUT1_DATA_WIDTH` per the Q11 worked case.
  - **Dependency note:** Step 7.2 is gated on two prior pieces of
    work.
    - Stage 9.2 (full migration of `examples/ip_test` to Path C).
      Today, `examples/ip_test` fails to build because `src`
      carries `ipDataSt<Config>` on its ports while `src` itself
      is non-leaf-parameterizable, producing the canonical Option-B
      failure called out in `pysrc/intf_gen_utils.py`
      `resolve_instance_config_arg()`. Q11's resolution
      *is* the fix — declaring `OUT0_DATA_WIDTH` and
      `OUT1_DATA_WIDTH` per-port parameters on `src` lifts it to
      leaf-parameterizable status and types each port
      independently. The hand-written `src.h` / `src.cpp` /
      `srcBase.h` regeneration is therefore Stage 9.2 territory
      with Stage 7.2 as the YAML-side contract.
    - Stage 10.1 (push_ack thunker header and
      `sc_channel.thunker: true` on
      `interfaces/push_ack/push_ack_if.yaml`). The existing
      `ipDataIf` is `push_ack`, and the Stage 6.2 packed-form
      check hard-errors when the meta-protocol does not declare
      thunker support. Until push_ack joins the supported set,
      Q11 cannot bridge through the existing `ip` consumer.
      Alternatively, the migrated `src` could expose `rdy_vld` or
      `req_ack` outputs (those interfaces already carry
      `sc_channel.thunker: true`), but that requires `ip` to
      declare a matching consumer-side interface — i.e., a
      consumer-side migration as well.

### Stage 8 — Validation regressions

Three regressions confirm the new shape works end-to-end.

- **Step 8.1 — Multi-Config-per-block regression.** A synthetic
  project binds `ip` to two variants
  (`ipVariant0Config`, `ipVariant1Config`). Confirm both reach the
  factory under their variant strings, construct distinct C++
  template instantiations, and pack/unpack at the variant-specific
  bit widths. Replaces the prior `plan-block-registration.md`
  Step 10.
- **Step 8.2 — Cross-interface bridge regression.** The Q10 worked
  example: a parent exposing two non-parameterized data interfaces
  (`data8If`, `data16If`) each binding through a connectionMap to a
  parameterized child (`uIp8` / `uIp16`). Confirm two thunker
  members are emitted in `container`, the build links, and runtime
  data flows correctly across both bridges.
- **Step 8.3 — Producer-with-per-port-parameters regression.** The
  Q11 worked case: a producer feeding two differently-Configed
  consumers, with per-port parameters in the producer's Config.
  Confirm two thunker members are emitted, no error from the
  generator, and the build/run succeeds with parameter consistency
  checks.

### Stage 9 — Examples migration

CI critical-path examples migrate to Path C in lockstep with the
generator landings. Per-example items to verify:

- Every variant overrides at least one parameter (no label-only
  variants).
- Producers feeding multiple differently-Configed consumers declare
  per-port parameters in their Config (Q11).
- No block constructor reads `getParam(...)` after Stage 4.
- Every `instanceFactory::createInstance(...)` caller passes the
  variant string only.
- Every cross-interface bind passes the packed-form compatibility
  check; thunker members appear in the generated container.

Examples in scope:

- **Step 9.1 — `examples/helloWorld`.** No parameterizable blocks
  today; expected to require no migration changes beyond the
  factory-API caller signature drop.
- **Step 9.2 — `examples/ip_test`.** The primary parameterized
  example. Migrates to per-variant Configs, per-instance container
  member types, addParam removal, and (under Stage 7.2) the Q11
  per-port-parameter convention.
- **Step 9.3 — `examples/mixed`.** Parameterized and non-templated
  blocks side by side; verilated wrappers retained on the existing
  `(blockType, variant)` key shape from
  `plan-block-registration.md`. This step retires the runtime
  parameter table from the model and Verilator-wrapper paths; the
  maintained generated block-testbench path for a parameterized DUT is
  tracked separately in Stage 11.

### Stage 10 — Protocol coverage extension

The thunker headers extend to additional protocols.

- **Step 10.1 — `push_ack_port_thunker.h`.** Per-protocol thunker in
  `builder/base/interfaces/push_ack/`. Same shape as rdy_vld; one
  data type per side.
- **Step 10.2 — `axi_port_thunker.h` (read and write).** Per-protocol
  thunker for `axi_read` and `axi_write` in
  `builder/base/interfaces/axi_read/` and
  `builder/base/interfaces/axi_write/`. AXI carries multiple
  structures (address, data, response); the thunker takes the
  corresponding type parameters.
- **Step 10.3 — `apb_port_thunker.h`.** Per-protocol thunker in
  `builder/base/interfaces/apb/`.
- **Step 10.4 — Thunker emission across protocols.** Generator
  emission from Stage 6.3 generalises across protocols once the
  thunker headers exist; the emission selects the protocol-specific
  thunker class based on the connection's interface meta-protocol.

Temporary implementation note: the current generator uses
`sc_channel.thunker: true` as a create-time guard so cross-interface
binds fail cleanly when a protocol does not yet have a thunker header.
That guard is transitional. Once Stage 10 adds thunker headers for all
interfaces, remove the protocol-support check and rely on
`interface_defs.parameters` plus the standard
`{sc_channel.type}_port_thunker` naming convention for all protocols.

Stage 10.4 retirement (landed): the transitional
`sc_channel.thunker: true` flag has been removed from every interface
YAML under `builder/base/interfaces` and `builder/pro/interfaces`. The
generator now derives cross-interface thunker eligibility from the
protocol declaring at least one `datatype: struct` parameter. The
generated C++ include names `<channelType>_port_thunker.h`; normal
include-path handling and the build system catch any missing header.
The schema's `thunker: optional(false)` slot is left in place for
backwards compatibility but is no longer read.

### Stage 11 — Variant-aware generated testbenches

Complete on this branch. The standalone Step 11 plan
([`plan-step-11-variant-aware-testbenches.md`](./plan-step-11-variant-aware-testbenches.md))
records the per-sub-step landing notes and verification commands.
Summary: `templates/systemc/testbench.py` and
`templates/systemc/module_hdl_wrapper.py` both thread the selected
per-variant Config through; `examples/ip_test::ip` is the maintained
fixture; both `./build/run ip` (model path) and `./build/run ip
--vlInst tb.ip` (Verilated DUT path) drive the same directed
push_ack transaction to `No error`.

## Generator / Template Changes

| Area | File / Template | Change |
|---|---|---|
| Config emission | `templates/systemc/configPolicy.py` (or equivalent) | One struct per variant; intra-block dedup |
| Block class | `templates/systemc/classDecl.py`, `baseClassDecl.py`, `constructor.py` | Always templated; Config::* reads in body |
| Trampoline | `templates/systemc/blockRegistrar.py` | Per-variant `registerBlock` lambdas; `addParam` removed; `configTag` removed |
| Factory API | `common/systemc/instanceFactory.{h,cpp}` | Key collapses to `(blockType, variant)` |
| Container | `templates/systemc/classDecl.py`, `constructor.py` | Per-instance Config types; non-templated parent; thunker members at cross-interface binds |
| Channel typing | `pysrc/processYaml.py`, `pysrc/intf_gen_utils.py` | Channel types derived from connected child's Config |
| Schema | `pysrc/schemaCheck.py`, `pysrc/yamlSchema.py` | `ports:` map under blocks |
| Compat check | `pysrc/processYaml.py`, `pysrc/intf_gen_utils.py` | Packed-form compatibility check on cross-interface binds |
| Thunker headers | `builder/base/interfaces/<protocol>/<protocol>_port_thunker.h` | Per-protocol thunker class |
| Verilated wrapper | `templates/systemc/module_hdl_wrapper.py`, `templates/systemVerilog/module_hdl_wrapper.py`, `templates/fileGen/fileGen.py`, `include/make/a2c-vl-wrap.mk` | Drop `configTag`; keep variant string; emit Config-dependent SystemC HDL bridge types plus canonical include-only SV wrapper bodies and per-variant trampolines; see Step C3.9 |
| Testbench | `templates/systemc/testbench.py` | See standalone Stage 11 plan |

## Verification

For each stage that lands generator emission changes:

```bash
python3 -m py_compile \
  templates/systemc/blockRegistrar.py \
  templates/systemc/classDecl.py \
  templates/systemc/baseClassDecl.py \
  templates/systemc/constructor.py \
  templates/systemc/testbench.py \
  templates/systemc/module_hdl_wrapper.py \
  templates/fileGen/fileGen.py \
  pysrc/processYaml.py \
  pysrc/intf_gen_utils.py

rm -rf examples/ip_test/.gen
make -C examples/ip_test gen
make -C examples/ip_test/rundir clean
make -C examples/ip_test/rundir
```

Stage-specific checks:

- **Stage 1.** Inspect a parameterizable block's `<block>.h`: it is
  emitted as `template<typename Config> class <block> { ... };`
  regardless of project. The per-context Config header carries one
  struct per variant.
- **Stage 2.** Inspect `instanceFactory.h`: the API takes
  `(blockType, variant)` only. The trampoline `<block>Registrar.cpp`
  emits one `registerBlock(...)` lambda per variant.
- **Stage 3.** Inspect `<parent>.h`: parent is non-templated; child
  members are typed by per-variant Config; channel members are typed
  by the connected child's Config.
- **Stage C3.9.** Inspect `examples/ip_test/verif/vl_wrap`: each
  parameterizable block has one `<block>_hdl_sv_wrapper.svh` canonical
  body and per-variant `<block>_<variant>_hdl_sv_wrapper.sv`
  trampolines. `make -C examples/ip_test/verif/vl_wrap`,
  `make -C examples/ip_test/rundir all VL_DUT=1`, and `make -C
  examples/ip_test/rundir run VL_DUT=1` pass; no
  `V<block>_hdl_sv_wrapper` canonical-body top is produced.
- **Stage 4.** Grep generated source: no `addParam` or `getParam`
  references remain. Block constructors read `Config::*` directly.
- **Stage 5.** A YAML with `ports:` declared on a parameterizable
  block generates correctly; a partial declaration produces the
  Stage 5.3 diagnostic.
- **Stage 6.** Q10 worked example builds and runs; the generated
  `container.h` carries one `<protocol>_port_thunker<...>` member
  per cross-interface bind, with declaration order after the child
  instance pointer.
- **Stage 8.** Each regression's smoke run passes:
  - Stage 8.1 — `make -C examples/ip_test_multi_config gen && make`
    (or equivalent project name once chosen) builds and runs both
    variants through the factory.
  - Stage 8.2 — `make -C examples/cross_interface_bridge gen &&
    make` (project name TBD) builds and runs the worked example.
  - Stage 8.3 — `make -C examples/ip_test gen && make` builds with
    the per-port-parameter producer convention exercised.
- **Stage 10.** Each protocol thunker compiles in a small unit test
  before any generator pass tries to emit it.
- **Stage 11.** See
  [`plan-step-11-variant-aware-testbenches.md`](./plan-step-11-variant-aware-testbenches.md).

## Migration Impact

- **YAML changes for end users.** Producers with multiple
  differently-parameterised outputs must declare per-port parameters
  in the block's parameter list (Q11). Blocks that need explicit
  port shape (parameterizable blocks; any block that prefers it) may
  declare a `ports:` map (D10). Existing top-down inference is
  preserved for blocks that do not.
- **C++ changes for end users.** None for generated code (the
  generator regenerates everything). Hand-written tails that called
  `getParam(...)` migrate to `Config::*` reads; this is mechanical.
- **Build changes.** No new build flags. Trampoline TUs continue to
  link unconditionally as today; new thunker headers are picked up
  via existing per-interface includes. The Verilated wrapper makefile
  filters generated tops to `*.sv` so canonical `.svh` wrapper bodies
  are regenerated but not Verilated as standalone tops.
- **Behavioural changes.** None at the protocol level — the thunker
  copies bits with the same semantics as a direct connection. Bit
  widths are validated at generation time rather than coerced at
  runtime; the `_bitWidth` exact-match check fails fast instead of
  silently bridging mismatched widths.

## Deferred Decisions

- **D2 — Language-native compile-time eval.** Move
  `isParameterizable` constants into compileable output in each
  target language. Tracked as a follow-up plan.
- **Templated `prt()` format selection.** Follow on from D2 with a
  C++ compile-time formatting path for parameterized structures.
  Today generated `prt()` code chooses field widths from worst-case
  YAML metadata, which is wrong for templated structs whose active
  `Config::*` width differs from the maximum (for example a 70-bit
  variant vs. an 8-bit variant sharing the same structure template).
  Add a `consteval` / `constexpr` helper that derives the per-field
  hex digit count and wide-word print shape from the bound Config,
  and use it to emit correct `std::format` strings / argument lists
  for scalar and `word[]` fields without hiding oversized-storage
  errors.
- **D10 mechanics — bottom-up vs. top-down checking semantics.**
  Detailed conflict diagnostics, partial-declaration handling, and
  schema validation rules. Stage 5.3 lands the minimal coverage; the
  full design is deferred.
- **Synthesised register-bus ports under bottom-up declaration.**
  Open item exposed by Stage 5.2 / 5.3. Today the register-bus
  interface (for example `apbReg` in `examples/ip_test`) is declared
  by the parent file that wires the CPU to the IP top
  (`ip_top.yaml`), and the per-block register-bus port is synthesised
  during post-parse by `config/postParseRegister.py` (using
  `addressControl.RegisterBusInterface`). The synthesised port
  surfaces as a connectionMap with `_context: '_global'`. The leaf
  block's own YAML therefore cannot include this port in a bottom-up
  `ports:` map: the interface is not in the leaf file's load-time
  scope (the parent has not yet been parsed), and the port itself
  does not exist in `self.data` until the post-parse pass has run.
  Stage 5.3 currently exempts ports whose inferring entry carries
  `_context: '_global'` from the partial-declaration diagnostic, so
  the leaf's bottom-up declaration can validly omit the
  register-bus port. This is acceptable for the Stage 5 exemplar but
  leaves an architectural gap: an IP used under a different
  address-decode configuration (different register-bus interface,
  different address group) cannot capture that contract on itself.
  Resolution likely requires (a) declaring the IP's register-bus
  interface locally on the IP block, and (b) corresponding changes
  to `config/postParseRegister.py` so that the synthesised
  connections refer to the locally declared interface instead of the
  project-wide `addressControl.RegisterBusInterface` only.

  The follow-up must preserve text stability for both generated block
  surfaces: `<block>.h` and `<block>Base.h`. The base header is just
  as reusable as the concrete class header, so it must not import a
  parent/container context merely because a higher-level project wires
  the register bus. In the `ip_test` bridge fixture this is the same
  distinction as the cross-interface `connectionMap` case: the parent
  side owns `data8If` / `data70If`, but the reusable child-side
  `ipBase.h` must be typed by the child's declared `ipDataIf`. The
  register-bus follow-up should apply that ownership rule to
  synthesised APB/register ports as well.

  Any interim generator split between a broad port include set and a
  narrower class include set should be removed once this is fixed.
  There should be a single IP-owned include surface for reusable
  block headers, with parent-only contexts isolated in the containing
  block that owns the wiring/thunker. Tracked here as a follow-up to
  Stage 5; out of scope for Stage 5 itself.
- **Verilated-wrapper parameter-override experiment.** The canonical
  wrapper body / trampoline migration is complete under Step C3.9.
  A separate future experiment could try Verilating one parameterized
  top multiple times with tool parameter overrides, but that is not
  required for Path C.
- **Tandem-pair registration record shape.** Tracked in
  `plan-block-registration.md` Plan-9.
- **Trampoline placement, naming, and module unit shape.** Resolved
  for Verilated wrappers by Step C3.9: canonical bodies live as
  generated include-only `.svh` files in `verif/vl_wrap`, variant
  trampolines keep the existing `.sv` filenames and module names.

## Related Plans / Documents

- [`research-multi-config-bindings.md`](./research-multi-config-bindings.md)
  — design surface, decisions D1–D10, Q10/R2, Q11 resolution,
  appendices.
- [`plan-block-registration.md`](./plan-block-registration.md) —
  per-block trampoline (T9). Step 10 absorbed here; Steps 1–9 and
  11–12 remain authoritative.
- [`plan-block-config-postprocess.md`](./plan-block-config-postprocess.md)
  — per-block `defaultConfig` post-processing. Stage 1.1 extends it
  to per-variant.
- [`plan-parameterizable-config-template.md`](./plan-parameterizable-config-template.md)
  — Config policy template. Stage 1.1 extends to per-variant
  emission.
- [`plan-development-ordering.md`](./plan-development-ordering.md) —
  T9 work item; this plan is a Path C follow-on after T9 lands.
- [`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md)
  — completed Step C3.9 execution record for exact-width canonical
  Verilated wrappers.
