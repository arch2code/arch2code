`ifndef _AXI4SDEMO_HDL_SV_WRAPPER_SV_GUARD_
`define _AXI4SDEMO_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module axi4sDemo_hdl_sv_wrapper
    // Generated Import package statement(s)
    import axi4sDemo_tb_package::*;
(
    // axi4_stream_if.dst
    input bit axis4_t1_tvalid,
    output bit axis4_t1_tready,
    input bit [255:0] axis4_t1_tdata,
    input bit [31:0] axis4_t1_tstrb,
    input bit [31:0] axis4_t1_tkeep,
    input bit axis4_t1_tlast,
    input bit [3:0] axis4_t1_tid,
    input bit [3:0] axis4_t1_tdest,
    input bit [15:0] axis4_t1_tuser,

    // axi4_stream_if.src
    output bit axis4_t2_tvalid,
    input bit axis4_t2_tready,
    output bit [63:0] axis4_t2_tdata,
    output bit [7:0] axis4_t2_tstrb,
    output bit [7:0] axis4_t2_tkeep,
    output bit axis4_t2_tlast,
    output bit [3:0] axis4_t2_tid,
    output bit [3:0] axis4_t2_tdest,
    output bit [3:0] axis4_t2_tuser,

    input clk,
    input rst_n
);
    // axi4_stream_if.dst
    axi4_stream_if #(.tdata_t(data_t1_t), .tid_t(tid_t1_t), .tdest_t(tdest_t1_t), .tuser_t(tuser_t1_t)) axis4_t1();

    assign #0 axis4_t1.tvalid = axis4_t1_tvalid;
    assign #0 axis4_t1_tready = axis4_t1.tready;
    assign #0 axis4_t1.tdata = axis4_t1_tdata;
    assign #0 axis4_t1.tstrb = axis4_t1_tstrb;
    assign #0 axis4_t1.tkeep = axis4_t1_tkeep;
    assign #0 axis4_t1.tlast = axis4_t1_tlast;
    assign #0 axis4_t1.tid = axis4_t1_tid;
    assign #0 axis4_t1.tdest = axis4_t1_tdest;
    assign #0 axis4_t1.tuser = axis4_t1_tuser;

    // axi4_stream_if.src
    axi4_stream_if #(.tdata_t(data_t2_t), .tid_t(tid_t2_t), .tdest_t(tdest_t2_t), .tuser_t(tuser_t2_t)) axis4_t2();

    assign #0 axis4_t2_tvalid = axis4_t2.tvalid;
    assign #0 axis4_t2.tready = axis4_t2_tready;
    assign #0 axis4_t2_tdata = axis4_t2.tdata;
    assign #0 axis4_t2_tstrb = axis4_t2.tstrb;
    assign #0 axis4_t2_tkeep = axis4_t2.tkeep;
    assign #0 axis4_t2_tlast = axis4_t2.tlast;
    assign #0 axis4_t2_tid = axis4_t2.tid;
    assign #0 axis4_t2_tdest = axis4_t2.tdest;
    assign #0 axis4_t2_tuser = axis4_t2.tuser;

    axi4sDemo dut (
        .axis4_t1(axis4_t1), // axi4_stream_if.dst
        .axis4_t2(axis4_t2), // axi4_stream_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : axi4sDemo_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _AXI4SDEMO_HDL_SV_WRAPPER_SV_GUARD_
