`ifndef _BLOCKF_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
`define _BLOCKF_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=blockF --variant=variant0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module blockF_variant0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import mixed_package::*;
    import mixedBlockC_package::*;
(
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

    assign #0 cStuffIf_vld = cStuffIf.vld;
    assign #0 cStuffIf_data = cStuffIf.data;
    assign #0 cStuffIf.rdy = cStuffIf_rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(dSt)) dStuffIf();

    assign #0 dStuffIf.vld = dStuffIf_vld;
    assign #0 dStuffIf.data = dStuffIf_data;
    assign #0 dStuffIf_rdy = dStuffIf.rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(dSt)) dSin();

    assign #0 dSin.vld = dSin_vld;
    assign #0 dSin.data = dSin_data;
    assign #0 dSin_rdy = dSin.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(dSt)) dSout();

    assign #0 dSout_vld = dSout.vld;
    assign #0 dSout_data = dSout.data;
    assign #0 dSout.rdy = dSout_rdy;

    // status_if.dst
    status_if #(.data_t(dRegSt)) rwD();

    assign #0 rwD.data = rwD_data;

    blockF #(.bob(BOB0), .fred(0)) dut (
        .cStuffIf(cStuffIf), // rdy_vld_if.src
        .dStuffIf(dStuffIf), // rdy_vld_if.dst
        .dSin(dSin), // rdy_vld_if.dst
        .dSout(dSout), // rdy_vld_if.src
        .rwD(rwD), // status_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : blockF_variant0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BLOCKF_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
