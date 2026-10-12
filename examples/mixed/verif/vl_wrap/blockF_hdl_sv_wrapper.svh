`ifndef _BLOCKF_HDL_SV_WRAPPER_SVH_GUARD_
`define _BLOCKF_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

`include "hdlBoundary.svh"

module blockF_hdl_sv_wrapper
    // Generated Import package statement(s)
    import mixed_package::*;
    import mixedBlockC_package::*;
#(
    parameter bob,
    parameter fred
) (
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
    // rdy_vld_if.src
    rdy_vld_if #(.data_t(seeSt)) cStuffIf();

    assign `A2C_HDL_BOUNDARY_DLY cStuffIf_vld = cStuffIf.vld;
    assign `A2C_HDL_BOUNDARY_DLY cStuffIf_data = cStuffIf.data;
    assign `A2C_HDL_BOUNDARY_DLY cStuffIf.rdy = cStuffIf_rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(dSt)) dStuffIf();

    assign `A2C_HDL_BOUNDARY_DLY dStuffIf.vld = dStuffIf_vld;
    assign `A2C_HDL_BOUNDARY_DLY dStuffIf.data = dStuffIf_data;
    assign `A2C_HDL_BOUNDARY_DLY dStuffIf_rdy = dStuffIf.rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(dSt)) dSin();

    assign `A2C_HDL_BOUNDARY_DLY dSin.vld = dSin_vld;
    assign `A2C_HDL_BOUNDARY_DLY dSin.data = dSin_data;
    assign `A2C_HDL_BOUNDARY_DLY dSin_rdy = dSin.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(dSt)) dSout();

    assign `A2C_HDL_BOUNDARY_DLY dSout_vld = dSout.vld;
    assign `A2C_HDL_BOUNDARY_DLY dSout_data = dSout.data;
    assign `A2C_HDL_BOUNDARY_DLY dSout.rdy = dSout_rdy;

    // status_if.dst
    status_if #(.data_t(dRegSt)) rwD();

    assign `A2C_HDL_BOUNDARY_DLY rwD.data = rwD_data;

    blockF #(.bob(bob), .fred(fred)) dut (
        .cStuffIf(cStuffIf), // rdy_vld_if.src
        .dStuffIf(dStuffIf), // rdy_vld_if.dst
        .dSin(dSin), // rdy_vld_if.dst
        .dSout(dSout), // rdy_vld_if.src
        .rwD(rwD), // status_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : blockF_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BLOCKF_HDL_SV_WRAPPER_SVH_GUARD_
