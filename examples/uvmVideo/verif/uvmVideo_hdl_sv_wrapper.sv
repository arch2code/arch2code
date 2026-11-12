`ifndef _UVMVIDEO_HDL_SV_WRAPPER_SV_GUARD_
`define _UVMVIDEO_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=uvmVideo
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module uvmVideo_hdl_sv_wrapper
    // Generated Import package statement(s)
    import uvmVideo_package::*;
(
    // raw_if.dst
    input bit [17:0] vin_data,

    // axi4_stream_if.src
    output bit vout_tvalid,
    input bit vout_tready,
    output bit [15:0] vout_tdata,
    output bit [1:0] vout_tstrb,
    output bit [1:0] vout_tkeep,
    output bit vout_tlast,
    output bit vout_tid,
    output bit vout_tdest,
    output bit vout_tuser,

    input clk,
    input rst_n
);
    // raw_if.dst
    raw_if #(.data_t(uvmVideoRawSt)) vin();

    assign `A2C_HDL_BOUNDARY_DLY vin.data = vin_data;

    // axi4_stream_if.src
    axi4_stream_if #(.tdata_t(uvmVideoBeatSt), .tid_t(uvmVideoIdSt), .tdest_t(uvmVideoIdSt), .tuser_t(uvmVideoUserSt)) vout();

    assign `A2C_HDL_BOUNDARY_DLY vout_tvalid = vout.tvalid;
    assign `A2C_HDL_BOUNDARY_DLY vout.tready = vout_tready;
    assign `A2C_HDL_BOUNDARY_DLY vout_tdata = vout.tdata;
    assign `A2C_HDL_BOUNDARY_DLY vout_tstrb = vout.tstrb;
    assign `A2C_HDL_BOUNDARY_DLY vout_tkeep = vout.tkeep;
    assign `A2C_HDL_BOUNDARY_DLY vout_tlast = vout.tlast;
    assign `A2C_HDL_BOUNDARY_DLY vout_tid = vout.tid;
    assign `A2C_HDL_BOUNDARY_DLY vout_tdest = vout.tdest;
    assign `A2C_HDL_BOUNDARY_DLY vout_tuser = vout.tuser;

    uvmVideo dut (
        .vin(vin), // raw_if.dst
        .vout(vout), // axi4_stream_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    raw_xcheck vin_xcheck (.clk(clk), .rst_n(rst_n), .intf(vin));
    axi4_stream_xcheck #(.CHECK_TUSER(1'b1)) vout_xcheck (.clk(clk), .rst_n(rst_n), .intf(vout));
    `endif

endmodule : uvmVideo_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _UVMVIDEO_HDL_SV_WRAPPER_SV_GUARD_
