# Plan: Canonical Exact-Width Verilated Wrappers

## Status

- **Direction:** verified / complete in the working tree. Stages 1-6 are
  implemented in working tree and verified by the Stage 6 regression record
  below; the documentation follow-up is complete in this plan and in
  `research-exact-width-verilated-wrappers.md`.
- **Scope of "complete" (2026-07-17):** this plan is validated only for the
  **monolithic single-project** case — a project Verilating variants of blocks
  it declares itself. The **cross-level / composed** case (a higher-level
  project declaring an ADDITIONAL variant of a reusable sub-component without
  modifying it) is NOT covered here. That case is **Direction A**, which moves
  each concrete foreign-variant wrapper to the immediate ASSEMBLING project;
  P1 has landed — registrar S3-H (the parent-owned foreign per-variant Config
  header) was committed 2026-07-21, so the composed `examples/ip_test` build is
  clean and P1 no longer depends on a stale child-owned Config. P3's
  ownership/identity contract is settled. Registrar S3-M/S6 and the explicit
  file->top manifest LANDED (committed 2026-07-22): the owner-qualified Q-C10
  wrapper-top identity is emitted by registrar S6, the build manifest carries
  explicit per-top `file->top` records, and the `vl_wrap.h/.cpp` aggregator is
  RETIRED suite-wide (**F10 DONE**). P2 now remains only on registrar S5; its
  Q-C8 SV Role C dependency (referenced type packages) is LATENT/DEFERRED
  (guarded by the module/package uniqueness gate), NOT a live gate — see
  [`plan-cross-level-variant-wrappers.md`](./plan-cross-level-variant-wrappers.md).
  The "does not change variant enumeration" stance below holds for the
  single-project case only.
- **Goal:** replace duplicated per-variant Verilated SV wrapper bodies with one
  canonical parameterized wrapper body plus tiny per-variant top-module
  trampolines, while making the flattened HDL boundary exact to each selected
  variant's active Config width.
- **Primary research input:**
  [`research-exact-width-verilated-wrappers.md`](./research-exact-width-verilated-wrappers.md).
- **Related variant/config work:**
  [`plan-variant-config-unification.md`](./plan-variant-config-unification.md).

## Problem

The current Verilated SV wrapper path emits a separate full wrapper body for
each variant. For parameterized payload structures, its flattened C++-visible
ports still use static structure metadata widths, which are worst-case widths
rather than active per-variant widths.

For example, `ip_variant0_hdl_sv_wrapper` binds `IP_DATA_WIDTH = 8`, but its
flattened `ipDataIf_data` port is still emitted at the wide variant's
`ipDataSt` maximum width. The SystemC wrapper mirrors that max-width ABI with
fixed `sc_bv<...>` HDL bridge types, so both sides must move together.

The isolated prototype proved that Verilator accepts active-width flattened
ports derived from wrapper parameters and also accepts tiny concrete top modules
that instantiate a parameterized wrapper body. It did not prove the generated
`ip_test` build, the C++ BFM / HDL_IF type changes, or the generator data
contract needed for both templates to consume the same active-width facts.

## Target Shape

For a parameterizable block with variants, generate:

1. One canonical parameterized SV wrapper body, emitted as an include-only
   header `ip_hdl_sv_wrapper.svh` in `verif/vl_wrap`:

```systemverilog
// ip_hdl_sv_wrapper.svh  (include-only; never a compilation top)
`ifndef _IP_HDL_SV_WRAPPER_SVH_GUARD_
`define _IP_HDL_SV_WRAPPER_SVH_GUARD_
module ip_hdl_sv_wrapper
    import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
) (
    input bit ipDataIf_push,
    input bit [(IP_DATA_WIDTH + $bits(enableT))-1:0] ipDataIf_data,
    output bit ipDataIf_ack,
    // other flattened ports
    input clk,
    input rst_n
);
    // Module-local parameterized typedefs / structs.
    // Interface reconstruction.
    // Parameterized DUT instantiation.
endmodule
`endif
```

2. One tiny top-module trampoline per variant (`.sv`), which `` `include ``s the
   body and keeps `localparam`s plus the symbolic port width (Stage-5 decision):

```systemverilog
// ip_variant0_hdl_sv_wrapper.sv  (the Verilated top)
`include "ip_hdl_sv_wrapper.svh"

module ip_variant0_hdl_sv_wrapper (
    input bit ipDataIf_push,
    input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data,
    output bit ipDataIf_ack,
    // other flattened ports
    input clk,
    input rst_n
);
    localparam IP_DATA_WIDTH = 8;
    localparam IP_MEM_DEPTH = 16;
    localparam IP_NONCONST_DEPTH = 24;
    ip_hdl_sv_wrapper #(
        .IP_DATA_WIDTH(IP_DATA_WIDTH),
        .IP_MEM_DEPTH(IP_MEM_DEPTH),
        .IP_NONCONST_DEPTH(IP_NONCONST_DEPTH)
    ) u_wrapper (
        .ipDataIf_push(ipDataIf_push),
        .ipDataIf_data(ipDataIf_data),
        .ipDataIf_ack(ipDataIf_ack),
        // other flattened ports
        .clk(clk),
        .rst_n(rst_n)
    );
endmodule
```

3. The existing per-variant C++ class names and factory typedefs:

```c++
using ip_variant0_hdl_sc_wrapper =
    ip_hdl_sc_wrapper<Vip_variant0_hdl_sv_wrapper, ipVariant0Config>;
```

4. Active-width C++ HDL bridge types:

```c++
push_ack_hdl_if<sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_hdl_if;
push_ack_dst_bfm<
    ipDataSt<Config>,
    sc_bv<ipDataSt<Config>::_bitWidth>
> ipDataIf_bfm;
```

Non-parameterized payloads and fixed hdlparams-derived signals continue to use
literal widths.

## Design Rules

- The SV top trampoline exists only to preserve Verilator top-module names and
  the current SystemC factory mapping.
- The canonical SV wrapper body owns interface reconstruction and DUT
  instantiation. Variant trampolines only bind parameters and wire ports
  through.
- Active boundary metadata must be assembled in a language-neutral
  `projectOpen` block view, not recomputed by SV and SystemC templates.
- Templates and `pysrc/intf_gen_utils.py` should consume prepared signal
  metadata and perform only language-specific spelling.
- Do not add compatibility paths for the old internal max-width shape. Replace
  the internal wrapper-boundary data contract directly.
- Do not change the broader variant/factory key model. This plan preserves the
  existing `(blockType, variant)` registration path.
- Do not attempt the further end state of Verilating one parameterized top
  multiple times with Verilator parameter overrides. That is a separate
  build/link prototype.

## Prototype First

### P0.1 - Hand-Built `ip_test` Canonical Wrapper Prototype

Create a non-generator prototype against the generated `examples/ip_test`
wrapper shape, run under the real `a2c-vl-wrap.mk` flow (not a bespoke
single-command-line Verilate). The build mechanics are the part this prototype
must prove, so the file layout has to match how the generated build discovers
and resolves modules:

- The `vl_wrap` build discovers tops by scanning `verif/vl_wrap` for `*.sv` /
  `*.svh` files containing a `GENERATED_CODE_` marker (`find_gen_sv_sources` in
  `a2c-common.mk`); `VL_OBJ_FILES` then Verilates each `.sv` as its own
  `-top <filename>` (`a2c-vl-wrap.mk`).
- A double-quoted `` `include `` is resolved from the including file's own
  directory (confirmed with Verilator), so a `.svh` body sitting beside its
  trampolines needs no `+incdir`. `-y` library search uses `+libext+.sv` only
  (a2c.f), so it never auto-grabs a `.svh`.

Therefore:

- Add a canonical `ip_hdl_sv_wrapper` body that contains the common wrapper logic
  once, with default-less parameters matching `rtl/ip.sv`, emitted as an
  **include-only header** `verif/vl_wrap/ip_hdl_sv_wrapper.svh` (it stays in the
  verif tree). It keeps its `GENERATED_CODE_` markers and is maintained by the
  generation scan, but is excluded from the top list by a one-line
  `$(filter %.sv, …)` on `VL_OBJ_FILES`. Standalone elaboration of a default-less
  parameterized module would fail in any simulator; the body is only ever reached
  through a trampoline `` `include `` with explicit parameter overrides.
  (Prototype-only caveat: the hand-built prototype `.svh` omits the marker,
  because a live marker makes `make` try to regenerate a DB entry that does not
  exist and crash. The real generated body keeps its marker.)
- Replace `ip_variant0_hdl_sv_wrapper` and `ip_variant1_hdl_sv_wrapper` bodies
  with tiny trampolines in `verif/vl_wrap` (`.sv`), each `` `include ``ing the
  `.svh` body and retaining its `GENERATED_CODE_` marker so it is discovered and
  Verilated as its own top.
- Keep the top-module names unchanged so Verilator still emits
  `Vip_variant0_hdl_sv_wrapper` and `Vip_variant1_hdl_sv_wrapper`.
- Trampoline ports keep `localparam`s and the Stage-1 symbolic width (Stage-5
  decision): `variant0` `ipDataIf_data` resolves to 9 bits, `variant1` to 71
  bits.
- Keep APB flattened ports at fixed 32-bit widths.

Validation:

```bash
make -C builder/base/examples/ip_test/verif/vl_wrap
```

Expected proof:

- Verilator accepts the `.svh` body `` `include ``d by the per-variant tops, in
  the real generated build environment.
- The canonical body is not Verilated as its own top and produces no
  duplicate-module or unbound-parameter error.
- Per-variant Verilator class names remain unchanged.

Prototype outcome (build-shape proof, `.svh` shape):

- A hand-built prototype (`verif/vl_wrap/ip_proto_hdl_sv_wrapper.svh` plus
  `ip_protoVariant0/1_hdl_sv_wrapper.sv` trampolines that `` `include `` it)
  Verilated cleanly through the Makefile's own per-file command. The body
  resolved via `` `include `` with no `+incdir`, was never a top
  (no `Vip_proto_hdl_sv_wrapper`), and pins resolved to exact per-variant widths
  (`sc_bv<9>`, `sc_bv<71>`). A normal `make` stays clean. The only build change
  the real design needs beyond this is the `$(filter %.sv, …)` one-liner, which
  applies once a marked `.svh` is generated into `verif/vl_wrap`.

### P0.2 - Hand-Built SystemC Exact HDL Boundary Prototype

In the same prototype, update the matching `ip_hdl_sc_wrapper.h` generated
region by hand only in the prototype copy:

- Change `push_ack_hdl_if<sc_bv<71>>` to
  `push_ack_hdl_if<sc_bv<ipDataSt<Config>::_bitWidth>>`.
- Change `push_ack_dst_bfm<ipDataSt<Config>, sc_bv<71>>` similarly.
- Leave APB bridge types as `sc_bv<32>`.
- Confirm both variant typedefs still bind the same wrapper class template with
  distinct Config types.

Validation:

```bash
make -C builder/base/examples/ip_test/rundir all VL_DUT=1
```

Expected proof:

- The C++ wrapper compiles with Config-dependent HDL bridge widths.
- The BFM, `hdl_if`, Verilated port connections, and factory typedefs remain
  consistent for both variants.
- The runtime test exercises at least the narrow and wide `ipDataIf` paths.

### P0.3 - Hand-Built `src` Per-Port Parameter Check

Repeat the width-shape check for `src_variantSrc0_hdl_sv_wrapper`, which has
two Config-dependent output ports with different active widths.

Validation:

```bash
make -C builder/base/examples/ip_test/rundir all VL_DUT=1
```

Expected proof:

- Per-port parameter payloads can use active boundary widths independently.
- The active-width metadata model cannot be only "one Config width per block";
  it must be per flattened boundary signal.

## Implementation Stages

### Stage 1 - Boundary Signal View (COMPLETE)

Make the flattened HDL wrapper boundary signals spell their active per-variant
width instead of the static worst-case structure width.

The original plan for this stage proposed a dedicated `projectOpen` boundary
signal view (`getBDBoundarySignals`) that would emit language-neutral width
descriptors consumed by both renderers. That view was not built. The simpler
shape that was implemented keeps the width decision inside the existing render
helpers in `pysrc/intf_gen_utils.py`, because those helpers already walk the
same interface definitions and per-port `intf_param[...]['structureKey']` facts,
and the width is spelled symbolically in each language rather than resolved to a
neutral term list:

- SystemC spells `<Struct><Config>::_bitWidth`, an existing generated handle
  (generated leaf structs already emit Config-dependent `_bitWidth`, for example
  `ipDataSt<Config>::_bitWidth = Config::IP_DATA_WIDTH + 1`).
- SV spells the active width as a parameter expression built from the
  structure's vars (for example `(IP_DATA_WIDTH + 1)`), legal in the per-variant
  wrapper because the variant binds the governing parameter as a module-local
  `localparam`.

No `projectCreate`, schema, or new view helper change is required: the
parameterizable facts (`isParameterizable`, the structure vars, and the
per-variant parameter values) are already persisted in `prj.data` and reachable
from the render helpers.

Validation:

- Add focused unit coverage for `ip` and `src` boundary spelling.
- Confirm `variant0` `ipDataIf_data` is represented as 9 bits and `variant1`
  as 71 bits.
- Confirm APB signals remain fixed at 32 bits.

Implemented as (`pysrc/intf_gen_utils.py`):

- `sv_boundary_struct_width_expression(struct_key, prj)` returns the static
  `structure['width']` for non-parameterizable payloads, and otherwise delegates
  to `sv_struct_width_expression()` for a symbolic active-width expression.
- `sv_struct_width_expression(struct_key, prj)` builds the SV width expression by
  iterating the structure vars (recursing through `NamedStruct`, summing
  `Reserved`/bitwidth terms, and applying array multipliers), with per-type
  spelling from `sv_type_width_expression()` (`width`, `$clog2(...)` forms, and a
  signed `+1`).
- `sv_packed_bit_type(width_expr)` formats the final port type, collapsing a
  one-bit payload to `bit` and otherwise emitting `bit [(<expr>)-1:0]`.
- `sv_gen_modport_signal_blast()` consumes these for parameterized payload
  signals; fixed hdlparam-derived and `bool` signals keep their literal widths.
- The SystemC side (`sc_gen_modport_signal_blast()` and its type helper) spells
  `sc_bv<<Struct><Config>::_bitWidth>` for parameterized payloads and literal
  `sc_bv<32>` for fixed APB signals.

Validation result:

- `unittest/test_boundary_signals.py` (registered in `run_all_tests.sh`) passes.
  It confirms `ipDataIf_data` spells `(IP_DATA_WIDTH + 1)` symbolically (9 bits
  for variant0, 71 bits for variant1), APB stays fixed at 32 bits, and `src`
  carries independent per-port parameters (`OUT0_DATA_WIDTH`, `OUT1_DATA_WIDTH`).
  The SystemC checks confirm `ipDataSt<Config>::_bitWidth`,
  `srcOut0St<Config>::_bitWidth`, and `srcOut1St<Config>::_bitWidth` bridge
  types.

### Stage 2 - SystemC Wrapper Boundary Types (COMPLETE)

Update the SystemC HDL wrapper generation to emit active Config-dependent
boundary types.

Changes:

- Emit `hdl_if` bridge types as `sc_bv<<Struct><Config>::_bitWidth>` for
  parameterized payloads.
- Emit BFM template arguments from the same `<Struct><Config>` expressions.
- Preserve the existing `template <typename DUT_T, typename Config>` shape for
  blocks with own params and variants.
- Keep non-parameterized blocks on literal fixed types.

Validation:

```bash
make -C builder/base/examples/ip_test/rundir all VL_DUT=1
```

This stage still uses the old full per-variant SV wrapper bodies. It proves
that the C++ side can accept active Config-dependent bridge types before the SV
template shape changes.

Validation result:

- Generated `examples/ip_test/verif/vl_wrap/ip_hdl_sc_wrapper.h` emits
  `push_ack_dst_bfm<ipDataSt<Config>, sc_bv<ipDataSt<Config>::_bitWidth>>` for
  `ipDataIf` and keeps `apb_dst_bfm<..., sc_bv<32>, sc_bv<32>>` for `regs`.
- `make -C examples/ip_test/rundir all VL_DUT=1` builds and links cleanly.

### Stage 3 - Exact-Width Full SV Wrappers (COMPLETE)

Update the current per-variant SV wrapper emission to use the active-width
spelling from Stage 1 and produce exact flattened port widths.

Changes:

- Replace static `structure['width']` use for parameterized payload boundary
  signals with `sv_boundary_struct_width_expression()` output.
- Keep full per-variant wrapper bodies temporarily.
- Keep module-local `localparam` and `parameterizedDecls` emission before
  interface declarations.

Validation:

```bash
make -C builder/base/examples/ip_test/verif/vl_wrap
make -C builder/base/examples/ip_test/rundir all VL_DUT=1
```

Expected proof:

- The ABI mismatch is fixed before template deduplication.
- Narrow and wide variants both build and run with exact C++/SV boundary
  widths.

Validation result:

- Generated `ip_variant0_hdl_sv_wrapper.sv` declares
  `input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data` with `localparam
  IP_DATA_WIDTH = 8`; `ip_variant1_hdl_sv_wrapper.sv` uses the same expression
  with `localparam IP_DATA_WIDTH = 70`. `src_variantSrc0_hdl_sv_wrapper.sv`
  carries independent `OUT0_DATA_WIDTH` / `OUT1_DATA_WIDTH` port widths.
- `make -C examples/ip_test/verif/vl_wrap` builds all Verilated wrappers.
- `make -C examples/ip_test/rundir all VL_DUT=1` followed by `make run VL_DUT=1`
  passes with no errors, exercising the wide path (`uIp0` reads `0x1a5`) and the
  narrow path (`uIp1` reads `0x5a`).

### Stage 4 - Canonical SV Wrapper Body

Restructure `templates/systemVerilog/module_hdl_wrapper.py` to emit one
canonical parameterized wrapper body for each parameterizable block.

Changes:

- Emit canonical module name `<block>_hdl_sv_wrapper`.
- Emit a parameter list matching the DUT parameters, **default-less**, mirroring
  the generated DUT module convention (`rtl/ip.sv` declares `parameter
  IP_DATA_WIDTH` with no default).
- Emit flattened ports using parameter-derived active-width expressions that are
  legal in an ANSI port list. Because the parameters are now in the `#()` list
  ahead of the ports, expressions such as `[(IP_DATA_WIDTH + 1)-1:0]` are legal;
  this also fixes the latent illegality in the Stage-3 bodies, where the port
  list references an `IP_DATA_WIDTH` `localparam` declared *after* the ports
  (Verilator currently tolerates it). Do not reference module-body typedefs that
  are declared after the port list.
- Emit module-local parameterized declarations once.
- Reuse existing interface reconstruction, assignment, DUT instantiation, and
  trace logic in the canonical body.

Output shape and build integration (resolved — see Resolved Decisions):

- The canonical body is emitted as an **include-only header**
  `<block>_hdl_sv_wrapper.svh` in `verif/vl_wrap` (it stays in the verif tree),
  and **keeps its `GENERATED_CODE_` markers**; the generator owns and maintains it
  in place like any other generated artifact. The generation scan
  `SV_GEN_FILES = find_gen_sv_sources(rtl/ + verif/vl_wrap)` already matches
  `*.svh`, so the body is generated and refreshed normally.
- Each variant trampoline `` `include ``s the body. The body is **never a
  compilation/elaboration top**: a default-less parameterized module cannot be a
  top in any simulator, the include guard makes repeated inclusion safe, and the
  `.svh` extension is excluded from the top list (next bullet).
- The top scan derives `VL_OBJ_FILES` via `patsubst %.sv,%.o`, which leaves a
  `.svh` as a malformed object target. Add a one-line filter so only `.sv` files
  become tops:
  `VL_OBJ_FILES = $(subst ./,obj_dir/V, $(patsubst %.sv,%.o, $(filter %.sv, $(VL_GEN_SV_FILES))))`
  in `include/make/a2c-vl-wrap.mk`. This is the only build change required for the
  Verilator flow. Verilator resolves the `` `include `` from the trampoline's own
  directory, so no `+incdir` change is needed; a non-Verilator flow should add an
  `+incdir` for the wrapper directory and treat `.svh` as include-only.
- The `.svh` vs `.sv` split also removes a naming ambiguity: non-parameterized
  blocks keep their top at `<block>_hdl_sv_wrapper.sv`, while the parameterized
  canonical body is `<block>_hdl_sv_wrapper.svh` and the tops are the
  `<block>_<variant>_hdl_sv_wrapper.sv` trampolines.

fileGen wiring (required — the generator must be told to emit the new file):

- Add a `fileMap` entry in the project `fileGeneration` table (see
  `pysrc/newProject.py`) for the canonical body, for example:
  `vlSvWrapBody : { name : "_hdl_sv_wrapper", ext: {svh: "svh"}, cond: {hasVl: true, hasRtl: true, isParameterizable: true}, mode: block, basePath: vl_wrap, variant: false, desc: "Canonical parameterized SV wrapper body (include-only)" }`.
  The `isParameterizable` condition restricts it to parameterizable blocks, so
  non-parameterized blocks emit no `.svh` and keep their single `.sv` top.
  Confirm `isParameterizable` is a block-condition field the `cond:` matcher can
  read; if not, surface it through the same path that exposes `hasVl`/`hasRtl`.
- Add the matching scaffold and dispatch case in
  `templates/fileGen/fileGen.py` (a `vlSvWrapBody_svh` target) that emits the
  include guard plus `GENERATED_CODE_PARAM --block=<block>` and a
  `GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=<canonical body>`
  region, mirroring the existing `vlSvWrap_sv` / `vlSvWrap_svVariant` scaffolds.
- Update the variant trampoline scaffold (`vlSvWrap_svVariantTemplate`) to emit
  `` `include "<block>_hdl_sv_wrapper.svh"`` ahead of the trampoline module.
- `module_hdl_wrapper.py` then renders the canonical body into the `.svh` region
  and the trampoline into the `.sv` region (Stage 5).

Validation:

```bash
make -C builder/base/examples/ip_test/verif/vl_wrap
```

Expected proof:

- The canonical `.svh` body is generated/maintained, `` `include ``d by each
  trampoline, and compiles in the Verilator wrapper build.
- It is not Verilated as its own top (no `V<block>_hdl_sv_wrapper`), raises no
  unbound-parameter error, and is not emitted redundantly in every variant top
  file.

Prototype proof (build-shape, `.svh` shape, validated):

- A hand-built prototype (`verif/vl_wrap/ip_proto_hdl_sv_wrapper.svh` plus
  `ip_protoVariant0/1_hdl_sv_wrapper.sv` trampolines that `` `include `` it) was
  Verilated through the Makefile's own per-file command. Both tops built; the
  body was resolved by `` `include `` with no `+incdir`, was never a top, and the
  pins resolved to exact per-variant widths (`sc_bv<9>` and `sc_bv<71>`), matching
  the SystemC `sc_bv<ipDataSt<Config>::_bitWidth>` ABI.

Validation result (generator implementation):

- `fileGen` wiring: a `vlSvWrapBody` `fileMap` entry was added in the base
  `config/project.yaml` (the config `ip_test` inherits; the per-project
  `project.yaml` leaves `fileMap` commented out). The `cond:` matcher is OR
  semantics and `condAnd:` is AND, so the entry is gated
  `cond: {isParameterizable: true}, condAnd: {hasVl: true}` (mirroring the
  existing `blockRegistrar` entry), not the single `cond:` map the plan text
  sketched. `isParameterizable` is a block-row field read directly by the matcher
  in `pysrc/newModule.py`; no new surfacing path was needed.
- Scaffold/dispatch: `templates/fileGen/fileGen.py` gained a `vlSvWrapBody_svh`
  case and `vlSvWrapBody_svhTemplate` (include guard + `GENERATED_CODE_PARAM`
  + `GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body`).
- Template: `templates/systemVerilog/module_hdl_wrapper.py` was restructured to
  dispatch on `args.section == 'body'` (canonical body) versus `args.variant`
  (trampoline) versus neither (`render_non_parameterizable`, the single
  self-contained body for non-parameterizable blocks). The body emits default-less
  `#()` parameters ahead of the ports, the Stage-1 active-width ports, the
  module-local typedefs, interface reconstruction, and a DUT instantiation whose
  parameters pass through by name.
- Generated `examples/ip_test/verif/vl_wrap/ip_hdl_sv_wrapper.svh` is the single
  canonical body; `src_hdl_sv_wrapper.svh` and `ipLeaf_hdl_sv_wrapper.svh` were
  likewise produced. Non-parameterizable `apbDecode` keeps its single
  `apbDecode_hdl_sv_wrapper.sv` with no `.svh`.
- `make -C examples/ip_test/verif/vl_wrap` builds with no `V<block>_hdl_sv_wrapper`
  top and no unbound-parameter error; the body is reached only through each
  trampoline's `` `include ``.

### Stage 5 - Variant Top Trampolines

Change per-variant SV wrapper files to emit only top-module trampolines.

Changes:

- Keep generated filenames and module names:
  `<block>_<variant>_hdl_sv_wrapper.sv`.
- Emit flattened port declarations for the selected variant. See the trampoline
  port-width decision below: the variant's concrete parameter values are declared
  as `localparam`s in the trampoline's `#()` parameter port list, and the ports
  reuse the Stage-1 symbolic width expression. This avoids introducing a
  per-variant numeric width-resolution path that does not yet exist in the render
  helpers, while keeping the width references legal (the localparams precede the
  ports).
- Emit `` `include "<block>_hdl_sv_wrapper.svh"`` ahead of the trampoline module
  so the canonical body is visible in the trampoline's own Verilate run. The
  `` `include `` is rendered by the template into the trampoline's
  `GENERATED_CODE` region (not baked into the static scaffold), so `make gen`
  alone keeps it in sync after a template change.
- Instantiate `<block>_hdl_sv_wrapper` with the selected parameter values.
- Wire every flattened port through by name.
- Drop the package import, typedefs, and interface reconstruction from the
  trampoline; those now live only in the canonical body. This assumes the
  trampoline's flattened port declarations are package-free (`bit`, packed
  `bit[...]`, or parameter-derived packed bits). Built-in interfaces satisfy
  this today because struct interface parameters and hdlparams are flattened to
  packed bits before declaration.
- Preserve include guards and generated-region ownership.

Trampoline port-width decision:

- A trampoline declared with no parameters has no in-scope source for a symbolic
  width such as `(IP_DATA_WIDTH + 1)`, and the only available numeric width
  helpers today are either the symbolic expression (Stage 1) or the static
  worst-case `structure['width']` — neither is the resolved per-variant integer.
  Producing a literal `[8:0]` would require arithmetic resolution of the width
  expression against the variant binding, which is a new capability and brushes
  against deferred parameterized-eval work.
- **Decision: declare the variant's `localparam`s in the trampoline's `#()`
  parameter port list and reuse the Stage-1 symbolic port-width expression.**
  This is a refinement of the original decision (which placed the `localparam`s
  in the module body, after the port list): a port-list reference to a body
  `localparam` declared later is a forward reference that Verilator tolerates but
  stricter front-ends may reject. Putting the `localparam`s in the `#()` list
  makes them precede — and be in scope for — the port widths, so the references
  are unambiguously legal with no evaluation path added. `localparam` in the
  parameter port list is core IEEE 1800 (confirmed under Verilator, including a
  `$clog2(...)`-derived port width). The Verilated pin still resolves to a
  concrete width, so the SystemC `sc_bv<...::_bitWidth>` ABI still matches. A
  fully numeric trampoline port (`[8:0]`) remains a future option but requires
  the deferred width-evaluation path.

Validation result (generator implementation):

- `render_trampoline` (in `templates/systemVerilog/module_hdl_wrapper.py`) emits
  the `` `include ``, then the trampoline `module` with the variant `localparam`s
  in its `#()` list, the Stage-1 symbolic ports, and an instantiation of
  `<block>_hdl_sv_wrapper` with all parameters and flattened ports wired by name
  (the bare port names come from a new `names` list on the modport blast helper).
- Generated `ip_variant0/1_hdl_sv_wrapper.sv` declare
  `#( localparam IP_DATA_WIDTH = 8|70, ... )` with port
  `[(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data` (9 / 71 bits); APB stays 32 bits.
  `src_variantSrc0_hdl_sv_wrapper.sv` carries independent `OUT0_DATA_WIDTH = 8`
  and `OUT1_DATA_WIDTH = 70`. `ipLeaf_variantLeaf0_hdl_sv_wrapper.sv` (a
  parameter-only block with no flattened data ports) renders cleanly; the
  by-name wiring emits no dangling leading comma.
- `make -C examples/ip_test/verif/vl_wrap` produces
  `Vip_variant0/1`, `Vsrc_variantSrc0`, and `VipLeaf_variantLeaf0` tops with no
  canonical-body top. `make -C examples/ip_test/rundir all VL_DUT=1` and
  `make run VL_DUT=1` pass, exercising the wide path (`uIp0` reads `0x1a5`) and
  the narrow path (`uIp1` reads `0x5a`). `make regr` passes 11/11.

### Stage 6 - Regression And Cleanup

Run the broader wrapper-relevant examples and remove obsolete helper paths.

Validation:

```bash
make -C builder/base/examples/ip_test/rundir all VL_DUT=1
make -C builder/base/examples/ip_test/verif/vl_wrap
make -C builder/base/examples/mixed/rundir all VL_DUT=1
```

Cleanup:

- Delete old max-width wrapper-boundary helper usage from SV/SC wrapper paths.
- Keep `get_struct_width()` for contexts that still intentionally need static
  maximum structure width.
- Delete the throwaway P0.1 prototype files from `examples/ip_test`
  (`verif/vl_wrap/ip_proto_hdl_sv_wrapper.svh`,
  `verif/vl_wrap/ip_protoVariant0_hdl_sv_wrapper.sv`,
  `verif/vl_wrap/ip_protoVariant1_hdl_sv_wrapper.sv`) once the generator emits the
  real `.svh` body and trampolines.
- Confirm the `$(filter %.sv, …)` change to `a2c-vl-wrap.mk` is in place so a
  generated `.svh` in `verif/vl_wrap` is maintained but never a Verilated top.
- Update `research-exact-width-verilated-wrappers.md` with the prototype result
  and link this plan as the execution path.

Status:

- **Regression:** `make -C examples/ip_test/rundir all VL_DUT=1`, the
  `verif/vl_wrap` build, `make run VL_DUT=1`, and `make regr` (11/11) all pass.
  `make -C examples/mixed/rundir all VL_DUT=1` fails at `make db` on a
  pre-existing, unrelated `mixed.yaml` issue (block params `bob`/`fred` lack
  same-name `ipParameters` constants); this failure is in `projectCreate` before
  any `fileGen`/template code runs, and `ip_test` rebuilds its DB cleanly with
  the new `fileMap` entry, so it is not caused by this work.
- **No max-width helper removal was required.** The remaining `get_struct_width()`
  / `structure['width']` uses in the wrapper boundary path are the intentional
  fixed-width branch; parameterizable payloads already route to active widths
  (`<Struct><Config>::_bitWidth` on the SC side, `(IP_DATA_WIDTH + 1)` on the SV
  side). These fixed-width uses are kept by design.
- **Prototype files deleted** and the **`$(filter %.sv, …)`** one-liner is in
  place.
- **Docs:** this plan and `research-exact-width-verilated-wrappers.md` are
  updated.

## Deferred Questions

- **deferred:** Anonymous/default variants for parameterizable Verilated
  wrappers remain outside this plan. The current implementation is centered on
  named per-instance variants; if default variants continue to be supported for
  parameterizable blocks, that future work needs an explicit canonical-body
  parameter-list and trampoline-generation contract rather than deriving
  parameters only from named variant rows.

## Resolved Decisions

- **One-bit Config-dependent payload spelling is historical.** Preserve the
  existing BFM convention: helper code already special-cases `w == 1`, and this
  plan does not require a new `bit` / `bool` versus one-bit-vector policy.
- **Canonical body is an include-only `.svh` header in the verif tree.** It is
  emitted as `verif/vl_wrap/<block>_hdl_sv_wrapper.svh`, keeps its
  `GENERATED_CODE_` markers, and is maintained by the generation scan (which
  covers `verif/vl_wrap` and matches `*.svh`). Each variant trampoline
  `` `include ``s it; the body is never a compilation/elaboration top. It is kept
  off the top list by a one-line `$(filter %.sv, …)` on `VL_OBJ_FILES` in
  `a2c-vl-wrap.mk` (a `.svh` otherwise becomes a malformed object target). This
  was chosen over an `rtl/` placement because the body belongs in the verif tree,
  and over a same-directory `.sv` because that would be indistinguishable from a
  non-parameterized block's `<block>_hdl_sv_wrapper.sv` top. `` `include `` and
  include guards are core IEEE 1800, portable across VCS, Xcelium, Questa, and
  Verilator; `.svh` is already an established include idiom here (`asserts.svh`).
  Portability requirement per flow: treat `.svh` as include-only (never a
  standalone analyze/elaborate unit) and `+incdir` the wrapper directory in any
  non-Verilator file list. Emitting this new file requires `fileGen` wiring (a
  `fileMap` entry plus a scaffold/dispatch case); see Stage 4. This supersedes the
  former Open Question about file placement; the build-shape prototype in P0.1
  confirmed the behavior under the real `a2c-vl-wrap.mk` flow. The prototype
  `.svh` omits the marker only because it is hand-built with no DB entry to
  regenerate from; the real generated body keeps its marker.
- **Trampolines declare `localparam`s in the `#()` parameter port list and reuse
  the Stage-1 symbolic port widths.** Resolved per-variant numeric port widths
  would need a width-expression evaluation path that does not exist in the render
  helpers and overlaps deferred parameterized-eval work. Reusing the symbolic
  widths reuses Stages 1/3 unchanged; the Verilated pin still resolves to a
  concrete width, so the SystemC `sc_bv<...::_bitWidth>` ABI still matches. The
  `localparam`s are placed in the parameter port list (not the module body) so
  they precede and are in scope for the port-width expressions, making the
  references unambiguously legal rather than relying on Verilator's tolerance of a
  forward reference to a body `localparam`. See Stage 5.
- **The trampoline `` `include `` is rendered into the generated region, not the
  static scaffold.** `module_hdl_wrapper.py` emits `` `include
  "<block>_hdl_sv_wrapper.svh"`` as the first line of the trampoline render
  output, inside `GENERATED_CODE_BEGIN`/`END`. The scaffold
  (`vlSvWrap_svVariantTemplate`) therefore carries only the include guard and the
  generated-region markers. This keeps the `` `include `` in sync via `make gen`
  after a template change, instead of requiring a scaffold rewrite (which
  `make newmodule` only performs for files that do not yet exist).
- **No dedicated boundary signal view; width spelled in render helpers.** The
  proposed `getBDBoundarySignals` `projectOpen` view was not built. The width
  decision lives in the existing `pysrc/intf_gen_utils.py` modport-blast helpers,
  which already reach the structure vars and per-port `structureKey` facts and
  spell the active width symbolically per language. See Stage 1 for the helper
  contract.
- **Eval-derived hdlparams are deferred.** hdlparams whose values are
  eval-derived from parameterized structures are out of scope for this plan and
  are not given Config-dependent treatment here. APB and other hdlparam-derived
  signals remain fixed-width.
- **No `projectCreate` or schema change.** The active-width spelling reads
  parameterizable facts already persisted in `prj.data` directly from the render
  helpers; no schema, `projectCreate`, or new `projectOpen` view was needed.
- **C++ Config-dependent width is already implemented.** The
  `# TODO: handle variable size parameters` in
  `templates/systemc/includes.py::typeWidthExpression_cpp` is stale for this
  path: `useConfig=True` already routes parameterizable constants through
  `constReference_cpp` to `Config::<NAME>`, and generated structs already emit
  Config-dependent `_bitWidth`. Stage 2 consumes the existing
  `<Struct><Config>::_bitWidth` handle and does not need to complete that TODO.

## Done Criteria

- `ip_test` Verilated wrappers use exact active widths for both narrow and wide
  variants.
- `src` per-port parameterized outputs use independent exact active widths.
- The generated SV has one canonical parameterized wrapper body per
  parameterizable block plus tiny variant top trampolines.
- The SystemC HDL wrapper uses Config-dependent `sc_bv<...::_bitWidth>` bridge
  types where required.
- Per-variant Verilator class names and SystemC factory registration remain
  unchanged.
- Fixed-width signals, including APB, remain fixed-width.
- Relevant `ip_test` and `mixed` Verilated builds pass.
