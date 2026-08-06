# Research: Exact-Width Verilated SV Wrappers

## Purpose

This note records the prototype findings for variant-specific Verilated
SystemVerilog wrappers whose flattened boundary ports use the selected
variant's active width rather than the parameterizable structure's worst-case
width.

The decision is intentionally still open: we may either land an interim
exact-width version of the current per-variant wrapper shape, or move directly
to a more final wrapper architecture. This document separates what the
prototype proved from those implementation choices.

## Outcome (resolved)

The "more final wrapper architecture" path was taken and is implemented. The
execution plan is
[`plan-canonical-verilated-wrappers.md`](./plan-canonical-verilated-wrappers.md);
see its Stage 4 and Stage 5 "Validation result" sections for the generator
details. In summary, the prototype findings below held under the real
`a2c-vl-wrap.mk` flow:

- Each parameterizable block now emits one canonical, default-less parameterized
  body as an include-only `verif/vl_wrap/<block>_hdl_sv_wrapper.svh` (with live
  `GENERATED_CODE_` markers), plus one tiny per-variant top trampoline
  `<block>_<variant>_hdl_sv_wrapper.sv` that `` `include ``s the body.
- The `.svh` is never a Verilated top: a one-line `$(filter %.sv, …)` on
  `VL_OBJ_FILES` keeps it off the top list, and the body is reached only through
  each trampoline's `` `include `` (resolved from the trampoline's own directory,
  no `+incdir`).
- Flattened boundary ports carry the selected variant's active width
  (`ipDataIf_data` resolves to 9 bits for variant0 and 71 bits for variant1; APB
  stays 32 bits; `src` carries independent per-port widths), matching the SystemC
  `sc_bv<<Struct><Config>::_bitWidth>` ABI.
- The trampoline binds the variant's `localparam`s in its `#()` parameter port
  list (so the symbolic port widths reference an in-scope, already-declared
  identifier — unambiguously legal, no width-evaluation path added). A fully
  numeric trampoline port remains a future option gated on the deferred
  parameterized-eval work.
- Verified on `examples/ip_test`: the `verif/vl_wrap` build, the full
  `all VL_DUT=1` build, `make run VL_DUT=1` (wide path `uIp0` = `0x1a5`, narrow
  path `uIp1` = `0x5a`), and `make regr` (11/11) all pass.

## Background

The existing Verilated SV wrapper path exists because the cross-language
boundary cannot expose project `interface` ports directly to the SystemC/C++
wrapper. The SV wrapper therefore "blasts" each interface into scalar/vector
ports, reconstructs the real SV interface internally, and connects that
interface to the RTL DUT.

For a normal RTL module such as `examples/ip_test/rtl/ip.sv`, the port list is
not width-explicit for parameterized payloads:

```systemverilog
module ip
    import ip_package::*;
#(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
) (
    push_ack_if.dst ipDataIf,
    apb_if.dst regs,
    input clk, rst_n
);
```

The payload type is module-local and derived from the selected module
parameters:

```systemverilog
typedef logic[IP_DATA_WIDTH-1:0] ipDataT;
typedef struct packed {
    enableT marker;
    ipDataT data;
} ipDataSt;
```

The Verilated wrapper is different because its C++-visible boundary is
flattened:

```systemverilog
input bit ipDataIf_push,
input bit [70:0] ipDataIf_data,
output bit ipDataIf_ack,
```

Today that flattened vector width is taken from static structure metadata,
which represents the maximum/worst-case generated width. For a narrow variant,
that creates a max-width wrapper ABI even though the wrapper-local interface is
already active-width.

## Prototype

Prototype files:

- `proto/rtl/rtl/interpolate_flat_exact_wrapper.sv`
- `proto/rtl/test/tb_flat_exact_wrapper.sv`
- `proto/rtl/Makefile` target `step6`

The prototype adds:

1. A parameterized flattened wrapper:

```systemverilog
module interpolate_flat_exact_wrapper
    import shared_types_pkg::*;
    import isp_types_package::*;
#(
    parameter int unsigned BITS_PER_PIXEL_COLOR = isp_types_package::BITS_PER_PIXEL_COLOR,
    parameter int unsigned MAX_PIXEL_VALUE = isp_types_package::MAX_PIXEL_VALUE,
    parameter int unsigned PIXELS_PER_CLOCK = isp_types_package::PIXELS_PER_CLOCK
) (
    input bit bayer_in_vld,
    input bit [(BITS_PER_PIXEL_COLOR * PIXELS_PER_CLOCK + $bits(video_frame_t))-1:0] bayer_in_data,
    output bit bayer_in_rdy,
    output bit rgb_out_vld,
    output bit [(BITS_PER_PIXEL_COLOR * 3 * PIXELS_PER_CLOCK + $bits(video_frame_t))-1:0] rgb_out_data,
    input bit rgb_out_rdy,
    input clk,
    input rst_n
);
```

2. Concrete variant top modules with exact numeric port widths:

```systemverilog
module interpolate_variant8_exact_wrapper (
    input bit bayer_in_vld,
    input bit [34:0] bayer_in_data,
    output bit bayer_in_rdy,
    output bit rgb_out_vld,
    output bit [98:0] rgb_out_data,
    input bit rgb_out_rdy,
    input clk,
    input rst_n
);
```

```systemverilog
module interpolate_variant12_exact_wrapper (
    input bit bayer_in_vld,
    input bit [98:0] bayer_in_data,
    output bit bayer_in_rdy,
    output bit rgb_out_vld,
    output bit [290:0] rgb_out_data,
    input bit rgb_out_rdy,
    input clk,
    input rst_n
);
```

3. A self-checking testbench that verifies both elaborated widths and payload
integrity across the flattened boundary.

Validation command:

```bash
cd proto/rtl
make step6
```

Observed result:

```text
INFO: variant8  bayer=35 rgb=99
INFO: variant12 bayer=99 rgb=291
PASS: Exact flattened wrapper ports preserve active variant widths
```

## Learnings

- Verilator accepts flattened port widths derived from module parameters in a
  wrapper module header.
- Verilator also accepts concrete per-variant top modules whose flattened port
  widths are exact active widths rather than worst-case widths.
- The wrapper can reconstruct parameterized SV interfaces internally using
  module-local typedefs and bind them to the parameterized DUT cleanly.
- The active-width boundary preserves payload bits for both a narrow variant
  and a wider variant in one testbench.
- The current max-width wrapper ABI is not required by the SV side. It is a
  generator/SC-wrapper integration choice, not a Verilator limitation shown by
  this prototype.

## Initial Shape

The lowest-risk implementation keeps the current per-variant SV wrapper
topology but changes the flattened boundary widths to the selected variant's
active widths.

For `ip`, that means:

```systemverilog
module ip_variant0_hdl_sv_wrapper
    import ip_package::*;
(
    input bit ipDataIf_push,
    input bit [8:0] ipDataIf_data,
    output bit ipDataIf_ack,
    ...
);
    localparam IP_DATA_WIDTH = 8;
    localparam IP_MEM_DEPTH = 16;
    localparam IP_NONCONST_DEPTH = 24;

    typedef logic[IP_DATA_WIDTH-1:0] ipDataT;
    typedef struct packed {
        enableT marker;
        ipDataT data;
    } ipDataSt;

    push_ack_if #(.data_t(ipDataSt)) ipDataIf();
    assign #0 ipDataIf.push = ipDataIf_push;
    assign #0 ipDataIf.data = ipDataIf_data;
    assign #0 ipDataIf_ack = ipDataIf.ack;

    ip #(
        .IP_DATA_WIDTH(IP_DATA_WIDTH),
        .IP_MEM_DEPTH(IP_MEM_DEPTH),
        .IP_NONCONST_DEPTH(IP_NONCONST_DEPTH)
    ) dut (...);
endmodule
```

The wide variant stays exact to its own active type:

```systemverilog
input bit [70:0] ipDataIf_data
```

This keeps the existing Verilator class names and SystemC factory mapping:

- `Vip_variant0_hdl_sv_wrapper`
- `Vip_variant1_hdl_sv_wrapper`
- `ip_variant0_hdl_sc_wrapper`
- `ip_variant1_hdl_sc_wrapper`

### Generator Implications

- `templates/systemVerilog/module_hdl_wrapper.py` can remain per-variant for
  parameterized blocks.
- The SV port-blasting path needs a variant-aware active-width source for
  parameterized interface payloads instead of `structure['width']`.
- The wrapper's module-local `localparam` declarations and
  `parameterizedDecls` emission remain useful and should stay before internal
  interface declarations.
- The SystemC wrapper side must use the same active width for the HDL-side
  bridge types. For a parameterized payload, this should be based on the
  selected Config, for example conceptually:

```c++
push_ack_hdl_if<sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_hdl_if;
push_ack_dst_bfm<ipDataSt<Config>, sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_bfm;
```

This avoids a mismatched C++/SV boundary where the SV wrapper is exact-width
but the SC-side `hdl_if` remains max-width.

## Eventual Shape

The eventual cleanup may separate the reusable wrapper body from the
per-variant top names:

1. Emit one canonical parameterized flattened wrapper body:

```systemverilog
module ip_hdl_sv_wrapper #(
    parameter IP_DATA_WIDTH,
    parameter IP_MEM_DEPTH,
    parameter IP_NONCONST_DEPTH
) (... active-width flattened ports ...);
    // module-local parameterized typedefs
    // internal interface reconstruction
    // parameterized DUT instantiation
endmodule
```

2. Emit tiny per-variant top modules only as Verilator/factory trampolines:

```systemverilog
module ip_variant0_hdl_sv_wrapper (... exact variant0 ports ...);
    ip_hdl_sv_wrapper #(
        .IP_DATA_WIDTH(8),
        .IP_MEM_DEPTH(16),
        .IP_NONCONST_DEPTH(24)
    ) u_wrapper (...);
endmodule
```

This reduces duplicated generated SV while preserving the unique top-module
names that the current Verilator and SystemC registration path expects.

A further possible end state is to remove the per-variant SV top modules
entirely and Verilate one parameterized top multiple times with distinct C++
class prefixes and parameter overrides. That would need a separate build-system
and link-path prototype. It is not proven by `step6`.

## Open Decision

Two viable implementation paths remain:

1. **Interim exact-width variant wrappers.**
   - Smaller change.
   - Keeps the current Verilator class/factory structure.
   - Fixes the max-width ABI directly.
   - Still duplicates most wrapper body text per variant.

2. **Go directly to canonical wrapper plus tiny variant trampolines.**
   - Cleaner generated SV shape.
   - Less duplication across variants.
   - Still preserves current per-variant Verilator top names.
   - Requires more template restructuring than the interim path.

The prototype supports both paths. The choice is a sequencing decision, not a
technical blocker discovered in Verilator.

## Follow-Up Checks

Before changing the generator, confirm:

- Active-width computation has a language-neutral owner in the block/context
  view, rather than recomputing cross-object semantics inside templates.
- The SC wrapper/BFM path can emit `sc_bv<Struct<Config>::_bitWidth>` for every
  parameterized payload that reaches a flattened HDL boundary.
- Non-parameterized blocks continue to use literal fixed widths.
- APB and other hdlparams-derived signals remain fixed-width unless their
  interface definitions intentionally make them Config-dependent.
- `make -C builder/base/examples/ip_test/rundir all VL_DUT=1` builds and runs
  both the narrow and wide parameterized Verilated wrapper tests once the
  generator is updated.
