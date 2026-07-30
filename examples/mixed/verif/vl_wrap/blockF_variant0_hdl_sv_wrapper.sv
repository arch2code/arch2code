`ifndef _BLOCKF_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
`define _BLOCKF_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=blockF --variant=variant0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "blockF_hdl_sv_wrapper.svh"

module blockF_variant0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import mixed_package::*;
    import mixed_mixedBlockC_package::*;
#(
    localparam bob = 16,
    localparam fred = 0
)(
    // rdy_vld_if.src
    output bit cStuffIf_vld,
    output bit [4:0] cStuffIf_data,
    input bit cStuffIf_rdy,

    // rdy_vld_if.dst
    input bit dStuffIf_vld,
    input bit [6:0] dStuffIf_data,
    output bit dStuffIf_rdy,

    // rdy_vld_if.dst
    input bit dSin_vld,
    input bit [6:0] dSin_data,
    output bit dSin_rdy,

    // rdy_vld_if.src
    output bit dSout_vld,
    output bit [6:0] dSout_data,
    input bit dSout_rdy,

    // status_if.dst
    input bit [6:0] rwD_data,

    input clk,
    input rst_n
);
    blockF_hdl_sv_wrapper #(
        .bob(bob),
        .fred(fred)
    ) u_wrapper (
        .cStuffIf_vld(cStuffIf_vld),
        .cStuffIf_data(cStuffIf_data),
        .cStuffIf_rdy(cStuffIf_rdy),
        .dStuffIf_vld(dStuffIf_vld),
        .dStuffIf_data(dStuffIf_data),
        .dStuffIf_rdy(dStuffIf_rdy),
        .dSin_vld(dSin_vld),
        .dSin_data(dSin_data),
        .dSin_rdy(dSin_rdy),
        .dSout_vld(dSout_vld),
        .dSout_data(dSout_data),
        .dSout_rdy(dSout_rdy),
        .rwD_data(rwD_data),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : blockF_variant0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BLOCKF_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
