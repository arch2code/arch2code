`ifndef _IP_VARIANT1_HDL_SV_WRAPPER_SV_GUARD_
`define _IP_VARIANT1_HDL_SV_WRAPPER_SV_GUARD_

// PROTOTYPE (P1) — ASSEMBLER-OWNED per-variant HDL wrapper.
//
// This file is hand-authored in the ASSEMBLER tree (examples/ip_test top-level
// verif/vl_wrap/ip), NOT in the 'ip' sub-project. It is the variant1 analog of
// the sub-project's correct variant0 trampoline
// (ip/verif/vl_wrap/ip/ip_variant0_hdl_sv_wrapper.sv): a distinct top module
// name, an `include of the sub-project-owned canonical body
// (ip_hdl_sv_wrapper.svh), and localparams bound to variant1's RESOLVED
// literals (IP_DATA_WIDTH=70, IP_MEM_DEPTH=8, IP_NONCONST_DEPTH=12).
//
// The `include reaches the sub-project's .svh via a relative path resolved
// against verilator's `+incdir+<this file's dir>` (the per-wrapper incdir added
// by a2c-vl-wrap.mk:56). No makefile/incdir change is required for the include
// to resolve.
//
// NOTE: the generated-code markers below are REQUIRED for build discovery. The
// make build finds verilator tops by grepping the marker token over the
// VL_WRAP_DIRS (a2c-common.mk find_gen_sv_sources), NOT from a manifest. Without
// a marker this file is never verilated and Vip_variant1_hdl_sv_wrapper.h is
// never produced.

// GENERATED_CODE_PARAM --block=ip --variant=variant1
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "../../../ip/verif/vl_wrap/ip/ip_hdl_sv_wrapper.svh"

module ip_variant1_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_package::*;
#(
    localparam IP_DATA_WIDTH = 70,
    localparam IP_MEM_DEPTH = 8,
    localparam IP_NONCONST_DEPTH = 12,
    localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2,
    localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2,
    localparam IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2,
    localparam IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2
)(
    // push_ack_if.dst
    input bit ipDataIf_push,
    input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data,
    output bit ipDataIf_ack,

    // apb_if.dst
    input bit [31:0] regs_paddr,
    input bit regs_psel,
    input bit regs_penable,
    input bit regs_pwrite,
    input bit [31:0] regs_pwdata,
    output bit regs_pready,
    output bit [31:0] regs_prdata,
    output bit regs_pslverr,

    input clk,
    input rst_n
);
    ip_hdl_sv_wrapper #(
        .IP_DATA_WIDTH(IP_DATA_WIDTH),
        .IP_MEM_DEPTH(IP_MEM_DEPTH),
        .IP_NONCONST_DEPTH(IP_NONCONST_DEPTH)
    ) u_wrapper (
        .ipDataIf_push(ipDataIf_push),
        .ipDataIf_data(ipDataIf_data),
        .ipDataIf_ack(ipDataIf_ack),
        .regs_paddr(regs_paddr),
        .regs_psel(regs_psel),
        .regs_penable(regs_penable),
        .regs_pwrite(regs_pwrite),
        .regs_pwdata(regs_pwdata),
        .regs_pready(regs_pready),
        .regs_prdata(regs_prdata),
        .regs_pslverr(regs_pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : ip_variant1_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IP_VARIANT1_HDL_SV_WRAPPER_SV_GUARD_
