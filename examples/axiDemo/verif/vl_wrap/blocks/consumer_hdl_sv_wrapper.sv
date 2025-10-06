`ifndef _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_
`define _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module consumer_hdl_sv_wrapper
    // Generated Import package statement(s)
    import axiDemo_package::*;(
    // axi_read_if.dst
    input bit [31:0] axiRd0_araddr,
    input bit [3:0] axiRd0_arid,
    input bit [7:0] axiRd0_arlen,
    input bit [2:0] axiRd0_arsize,
    input bit [1:0] axiRd0_arburst,
    input bit axiRd0_arvalid,
    output bit axiRd0_arready,
    output bit [31:0] axiRd0_rdata,
    output bit [3:0] axiRd0_rid,
    output bit [1:0] axiRd0_rresp,
    output bit axiRd0_rlast,
    output bit axiRd0_rvalid,
    input bit axiRd0_rready,

    // axi_read_if.dst
    input bit [31:0] axiRd1_araddr,
    input bit [3:0] axiRd1_arid,
    input bit [7:0] axiRd1_arlen,
    input bit [2:0] axiRd1_arsize,
    input bit [1:0] axiRd1_arburst,
    input bit axiRd1_arvalid,
    output bit axiRd1_arready,
    output bit [31:0] axiRd1_rdata,
    output bit [3:0] axiRd1_rid,
    output bit [1:0] axiRd1_rresp,
    output bit axiRd1_rlast,
    output bit axiRd1_rvalid,
    input bit axiRd1_rready,

    // axi_read_if.dst
    input bit [31:0] axiRd2_araddr,
    input bit [3:0] axiRd2_arid,
    input bit [7:0] axiRd2_arlen,
    input bit [2:0] axiRd2_arsize,
    input bit [1:0] axiRd2_arburst,
    input bit axiRd2_arvalid,
    output bit axiRd2_arready,
    output bit [31:0] axiRd2_rdata,
    output bit [3:0] axiRd2_rid,
    output bit [1:0] axiRd2_rresp,
    output bit axiRd2_rlast,
    output bit axiRd2_rvalid,
    input bit axiRd2_rready,

    // axi_read_if.dst
    input bit [31:0] axiRd3_araddr,
    input bit [3:0] axiRd3_arid,
    input bit [7:0] axiRd3_arlen,
    input bit [2:0] axiRd3_arsize,
    input bit [1:0] axiRd3_arburst,
    input bit axiRd3_arvalid,
    output bit axiRd3_arready,
    output bit [31:0] axiRd3_rdata,
    output bit [3:0] axiRd3_rid,
    output bit [1:0] axiRd3_rresp,
    output bit axiRd3_rlast,
    output bit axiRd3_rvalid,
    input bit axiRd3_rready,

    // axi_write_if.dst
    input bit [31:0] axiWr0_awaddr,
    input bit [3:0] axiWr0_awid,
    input bit [7:0] axiWr0_awlen,
    input bit [2:0] axiWr0_awsize,
    input bit [1:0] axiWr0_awburst,
    input bit axiWr0_awvalid,
    output bit axiWr0_awready,
    input bit [31:0] axiWr0_wdata,
    input bit [3:0] axiWr0_wid,
    input bit [3:0] axiWr0_wstrb,
    input bit axiWr0_wlast,
    input bit axiWr0_wvalid,
    output bit axiWr0_wready,
    output bit [1:0] axiWr0_bresp,
    output bit [3:0] axiWr0_bid,
    output bit axiWr0_bvalid,
    input bit axiWr0_bready,

    // axi_write_if.dst
    input bit [31:0] axiWr1_awaddr,
    input bit [3:0] axiWr1_awid,
    input bit [7:0] axiWr1_awlen,
    input bit [2:0] axiWr1_awsize,
    input bit [1:0] axiWr1_awburst,
    input bit axiWr1_awvalid,
    output bit axiWr1_awready,
    input bit [31:0] axiWr1_wdata,
    input bit [3:0] axiWr1_wid,
    input bit [3:0] axiWr1_wstrb,
    input bit axiWr1_wlast,
    input bit axiWr1_wvalid,
    output bit axiWr1_wready,
    output bit [1:0] axiWr1_bresp,
    output bit [3:0] axiWr1_bid,
    output bit axiWr1_bvalid,
    input bit axiWr1_bready,

    // axi_write_if.dst
    input bit [31:0] axiWr2_awaddr,
    input bit [3:0] axiWr2_awid,
    input bit [7:0] axiWr2_awlen,
    input bit [2:0] axiWr2_awsize,
    input bit [1:0] axiWr2_awburst,
    input bit axiWr2_awvalid,
    output bit axiWr2_awready,
    input bit [31:0] axiWr2_wdata,
    input bit [3:0] axiWr2_wid,
    input bit [3:0] axiWr2_wstrb,
    input bit axiWr2_wlast,
    input bit axiWr2_wvalid,
    output bit axiWr2_wready,
    output bit [1:0] axiWr2_bresp,
    output bit [3:0] axiWr2_bid,
    output bit axiWr2_bvalid,
    input bit axiWr2_bready,

    // axi_write_if.dst
    input bit [31:0] axiWr3_awaddr,
    input bit [3:0] axiWr3_awid,
    input bit [7:0] axiWr3_awlen,
    input bit [2:0] axiWr3_awsize,
    input bit [1:0] axiWr3_awburst,
    input bit axiWr3_awvalid,
    output bit axiWr3_awready,
    input bit [31:0] axiWr3_wdata,
    input bit [3:0] axiWr3_wid,
    input bit [3:0] axiWr3_wstrb,
    input bit axiWr3_wlast,
    input bit axiWr3_wvalid,
    output bit axiWr3_wready,
    output bit [1:0] axiWr3_bresp,
    output bit [3:0] axiWr3_bid,
    output bit axiWr3_bvalid,
    input bit axiWr3_bready,

    // axi4_stream_if.dst
    input bit axiStr0_tvalid,
    output bit axiStr0_tready,
    input bit [31:0] axiStr0_tdata,
    input bit [3:0] axiStr0_tstrb,
    input bit [3:0] axiStr0_tkeep,
    input bit axiStr0_tlast,
    input bit [31:0] axiStr0_tid,
    input bit [31:0] axiStr0_tdest,
    input bit [31:0] axiStr0_tuser,

    // axi4_stream_if.dst
    input bit axiStr1_tvalid,
    output bit axiStr1_tready,
    input bit [31:0] axiStr1_tdata,
    input bit [3:0] axiStr1_tstrb,
    input bit [3:0] axiStr1_tkeep,
    input bit axiStr1_tlast,
    input bit [31:0] axiStr1_tid,
    input bit [31:0] axiStr1_tdest,
    input bit [31:0] axiStr1_tuser,

    input clk,
    input rst_n
);
    // axi_read_if.dst
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd0();

    assign #0 axiRd0.araddr = axiRd0_araddr;
    assign #0 axiRd0.arid = axiRd0_arid;
    assign #0 axiRd0.arlen = axiRd0_arlen;
    assign #0 axiRd0.arsize = axiRd0_arsize;
    assign #0 axiRd0.arburst = axiRd0_arburst;
    assign #0 axiRd0.arvalid = axiRd0_arvalid;
    assign #0 axiRd0_arready = axiRd0.arready;
    assign #0 axiRd0_rdata = axiRd0.rdata;
    assign #0 axiRd0_rid = axiRd0.rid;
    assign #0 axiRd0_rresp = axiRd0.rresp;
    assign #0 axiRd0_rlast = axiRd0.rlast;
    assign #0 axiRd0_rvalid = axiRd0.rvalid;
    assign #0 axiRd0.rready = axiRd0_rready;

    // axi_read_if.dst
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd1();

    assign #0 axiRd1.araddr = axiRd1_araddr;
    assign #0 axiRd1.arid = axiRd1_arid;
    assign #0 axiRd1.arlen = axiRd1_arlen;
    assign #0 axiRd1.arsize = axiRd1_arsize;
    assign #0 axiRd1.arburst = axiRd1_arburst;
    assign #0 axiRd1.arvalid = axiRd1_arvalid;
    assign #0 axiRd1_arready = axiRd1.arready;
    assign #0 axiRd1_rdata = axiRd1.rdata;
    assign #0 axiRd1_rid = axiRd1.rid;
    assign #0 axiRd1_rresp = axiRd1.rresp;
    assign #0 axiRd1_rlast = axiRd1.rlast;
    assign #0 axiRd1_rvalid = axiRd1.rvalid;
    assign #0 axiRd1.rready = axiRd1_rready;

    // axi_read_if.dst
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd2();

    assign #0 axiRd2.araddr = axiRd2_araddr;
    assign #0 axiRd2.arid = axiRd2_arid;
    assign #0 axiRd2.arlen = axiRd2_arlen;
    assign #0 axiRd2.arsize = axiRd2_arsize;
    assign #0 axiRd2.arburst = axiRd2_arburst;
    assign #0 axiRd2.arvalid = axiRd2_arvalid;
    assign #0 axiRd2_arready = axiRd2.arready;
    assign #0 axiRd2_rdata = axiRd2.rdata;
    assign #0 axiRd2_rid = axiRd2.rid;
    assign #0 axiRd2_rresp = axiRd2.rresp;
    assign #0 axiRd2_rlast = axiRd2.rlast;
    assign #0 axiRd2_rvalid = axiRd2.rvalid;
    assign #0 axiRd2.rready = axiRd2_rready;

    // axi_read_if.dst
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd3();

    assign #0 axiRd3.araddr = axiRd3_araddr;
    assign #0 axiRd3.arid = axiRd3_arid;
    assign #0 axiRd3.arlen = axiRd3_arlen;
    assign #0 axiRd3.arsize = axiRd3_arsize;
    assign #0 axiRd3.arburst = axiRd3_arburst;
    assign #0 axiRd3.arvalid = axiRd3_arvalid;
    assign #0 axiRd3_arready = axiRd3.arready;
    assign #0 axiRd3_rdata = axiRd3.rdata;
    assign #0 axiRd3_rid = axiRd3.rid;
    assign #0 axiRd3_rresp = axiRd3.rresp;
    assign #0 axiRd3_rlast = axiRd3.rlast;
    assign #0 axiRd3_rvalid = axiRd3.rvalid;
    assign #0 axiRd3.rready = axiRd3_rready;

    // axi_write_if.dst
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr0();

    assign #0 axiWr0.awaddr = axiWr0_awaddr;
    assign #0 axiWr0.awid = axiWr0_awid;
    assign #0 axiWr0.awlen = axiWr0_awlen;
    assign #0 axiWr0.awsize = axiWr0_awsize;
    assign #0 axiWr0.awburst = axiWr0_awburst;
    assign #0 axiWr0.awvalid = axiWr0_awvalid;
    assign #0 axiWr0_awready = axiWr0.awready;
    assign #0 axiWr0.wdata = axiWr0_wdata;
    assign #0 axiWr0.wid = axiWr0_wid;
    assign #0 axiWr0.wstrb = axiWr0_wstrb;
    assign #0 axiWr0.wlast = axiWr0_wlast;
    assign #0 axiWr0.wvalid = axiWr0_wvalid;
    assign #0 axiWr0_wready = axiWr0.wready;
    assign #0 axiWr0_bresp = axiWr0.bresp;
    assign #0 axiWr0_bid = axiWr0.bid;
    assign #0 axiWr0_bvalid = axiWr0.bvalid;
    assign #0 axiWr0.bready = axiWr0_bready;

    // axi_write_if.dst
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr1();

    assign #0 axiWr1.awaddr = axiWr1_awaddr;
    assign #0 axiWr1.awid = axiWr1_awid;
    assign #0 axiWr1.awlen = axiWr1_awlen;
    assign #0 axiWr1.awsize = axiWr1_awsize;
    assign #0 axiWr1.awburst = axiWr1_awburst;
    assign #0 axiWr1.awvalid = axiWr1_awvalid;
    assign #0 axiWr1_awready = axiWr1.awready;
    assign #0 axiWr1.wdata = axiWr1_wdata;
    assign #0 axiWr1.wid = axiWr1_wid;
    assign #0 axiWr1.wstrb = axiWr1_wstrb;
    assign #0 axiWr1.wlast = axiWr1_wlast;
    assign #0 axiWr1.wvalid = axiWr1_wvalid;
    assign #0 axiWr1_wready = axiWr1.wready;
    assign #0 axiWr1_bresp = axiWr1.bresp;
    assign #0 axiWr1_bid = axiWr1.bid;
    assign #0 axiWr1_bvalid = axiWr1.bvalid;
    assign #0 axiWr1.bready = axiWr1_bready;

    // axi_write_if.dst
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr2();

    assign #0 axiWr2.awaddr = axiWr2_awaddr;
    assign #0 axiWr2.awid = axiWr2_awid;
    assign #0 axiWr2.awlen = axiWr2_awlen;
    assign #0 axiWr2.awsize = axiWr2_awsize;
    assign #0 axiWr2.awburst = axiWr2_awburst;
    assign #0 axiWr2.awvalid = axiWr2_awvalid;
    assign #0 axiWr2_awready = axiWr2.awready;
    assign #0 axiWr2.wdata = axiWr2_wdata;
    assign #0 axiWr2.wid = axiWr2_wid;
    assign #0 axiWr2.wstrb = axiWr2_wstrb;
    assign #0 axiWr2.wlast = axiWr2_wlast;
    assign #0 axiWr2.wvalid = axiWr2_wvalid;
    assign #0 axiWr2_wready = axiWr2.wready;
    assign #0 axiWr2_bresp = axiWr2.bresp;
    assign #0 axiWr2_bid = axiWr2.bid;
    assign #0 axiWr2_bvalid = axiWr2.bvalid;
    assign #0 axiWr2.bready = axiWr2_bready;

    // axi_write_if.dst
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr3();

    assign #0 axiWr3.awaddr = axiWr3_awaddr;
    assign #0 axiWr3.awid = axiWr3_awid;
    assign #0 axiWr3.awlen = axiWr3_awlen;
    assign #0 axiWr3.awsize = axiWr3_awsize;
    assign #0 axiWr3.awburst = axiWr3_awburst;
    assign #0 axiWr3.awvalid = axiWr3_awvalid;
    assign #0 axiWr3_awready = axiWr3.awready;
    assign #0 axiWr3.wdata = axiWr3_wdata;
    assign #0 axiWr3.wid = axiWr3_wid;
    assign #0 axiWr3.wstrb = axiWr3_wstrb;
    assign #0 axiWr3.wlast = axiWr3_wlast;
    assign #0 axiWr3.wvalid = axiWr3_wvalid;
    assign #0 axiWr3_wready = axiWr3.wready;
    assign #0 axiWr3_bresp = axiWr3.bresp;
    assign #0 axiWr3_bid = axiWr3.bid;
    assign #0 axiWr3_bvalid = axiWr3.bvalid;
    assign #0 axiWr3.bready = axiWr3_bready;

    // axi4_stream_if.dst
    axi4_stream_if #(.tdata_t(axiDataSt), .tid_t(axiAddrSt), .tdest_t(axiAddrSt), .tuser_t(axiAddrSt)) axiStr0();

    assign #0 axiStr0.tvalid = axiStr0_tvalid;
    assign #0 axiStr0_tready = axiStr0.tready;
    assign #0 axiStr0.tdata = axiStr0_tdata;
    assign #0 axiStr0.tstrb = axiStr0_tstrb;
    assign #0 axiStr0.tkeep = axiStr0_tkeep;
    assign #0 axiStr0.tlast = axiStr0_tlast;
    assign #0 axiStr0.tid = axiStr0_tid;
    assign #0 axiStr0.tdest = axiStr0_tdest;
    assign #0 axiStr0.tuser = axiStr0_tuser;

    // axi4_stream_if.dst
    axi4_stream_if #(.tdata_t(axiDataSt), .tid_t(axiAddrSt), .tdest_t(axiAddrSt), .tuser_t(axiAddrSt)) axiStr1();

    assign #0 axiStr1.tvalid = axiStr1_tvalid;
    assign #0 axiStr1_tready = axiStr1.tready;
    assign #0 axiStr1.tdata = axiStr1_tdata;
    assign #0 axiStr1.tstrb = axiStr1_tstrb;
    assign #0 axiStr1.tkeep = axiStr1_tkeep;
    assign #0 axiStr1.tlast = axiStr1_tlast;
    assign #0 axiStr1.tid = axiStr1_tid;
    assign #0 axiStr1.tdest = axiStr1_tdest;
    assign #0 axiStr1.tuser = axiStr1_tuser;

    consumer dut (
        .axiRd0(axiRd0), // axi_read_if.dst
        .axiRd1(axiRd1), // axi_read_if.dst
        .axiRd2(axiRd2), // axi_read_if.dst
        .axiRd3(axiRd3), // axi_read_if.dst
        .axiWr0(axiWr0), // axi_write_if.dst
        .axiWr1(axiWr1), // axi_write_if.dst
        .axiWr2(axiWr2), // axi_write_if.dst
        .axiWr3(axiWr3), // axi_write_if.dst
        .axiStr0(axiStr0), // axi4_stream_if.dst
        .axiStr1(axiStr1), // axi4_stream_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : consumer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CONSUMER_HDL_SV_WRAPPER_SV_GUARD_
