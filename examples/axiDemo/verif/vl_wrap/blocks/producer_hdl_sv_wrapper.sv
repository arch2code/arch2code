`ifndef _PRODUCER_HDL_SV_WRAPPER_SV_GUARD_
`define _PRODUCER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module producer_hdl_sv_wrapper
    // Generated Import package statement(s)
    import axiDemo_package::*;
(
    // axi_read_if.src
    output bit [31:0] axiRd0_araddr,
    output bit [3:0] axiRd0_arid,
    output bit [7:0] axiRd0_arlen,
    output bit [2:0] axiRd0_arsize,
    output bit [1:0] axiRd0_arburst,
    output bit axiRd0_arvalid,
    input bit axiRd0_arready,
    input bit [31:0] axiRd0_rdata,
    input bit [3:0] axiRd0_rid,
    input bit [1:0] axiRd0_rresp,
    input bit axiRd0_rlast,
    input bit axiRd0_rvalid,
    output bit axiRd0_rready,

    // axi_read_if.src
    output bit [31:0] axiRd1_araddr,
    output bit [3:0] axiRd1_arid,
    output bit [7:0] axiRd1_arlen,
    output bit [2:0] axiRd1_arsize,
    output bit [1:0] axiRd1_arburst,
    output bit axiRd1_arvalid,
    input bit axiRd1_arready,
    input bit [31:0] axiRd1_rdata,
    input bit [3:0] axiRd1_rid,
    input bit [1:0] axiRd1_rresp,
    input bit axiRd1_rlast,
    input bit axiRd1_rvalid,
    output bit axiRd1_rready,

    // axi_read_if.src
    output bit [31:0] axiRd2_araddr,
    output bit [3:0] axiRd2_arid,
    output bit [7:0] axiRd2_arlen,
    output bit [2:0] axiRd2_arsize,
    output bit [1:0] axiRd2_arburst,
    output bit axiRd2_arvalid,
    input bit axiRd2_arready,
    input bit [31:0] axiRd2_rdata,
    input bit [3:0] axiRd2_rid,
    input bit [1:0] axiRd2_rresp,
    input bit axiRd2_rlast,
    input bit axiRd2_rvalid,
    output bit axiRd2_rready,

    // axi_read_if.src
    output bit [31:0] axiRd3_araddr,
    output bit [3:0] axiRd3_arid,
    output bit [7:0] axiRd3_arlen,
    output bit [2:0] axiRd3_arsize,
    output bit [1:0] axiRd3_arburst,
    output bit axiRd3_arvalid,
    input bit axiRd3_arready,
    input bit [31:0] axiRd3_rdata,
    input bit [3:0] axiRd3_rid,
    input bit [1:0] axiRd3_rresp,
    input bit axiRd3_rlast,
    input bit axiRd3_rvalid,
    output bit axiRd3_rready,

    // axi_write_if.src
    output bit [31:0] axiWr0_awaddr,
    output bit [3:0] axiWr0_awid,
    output bit [7:0] axiWr0_awlen,
    output bit [2:0] axiWr0_awsize,
    output bit [1:0] axiWr0_awburst,
    output bit axiWr0_awvalid,
    input bit axiWr0_awready,
    output bit [31:0] axiWr0_wdata,
    output bit [3:0] axiWr0_wid,
    output bit [3:0] axiWr0_wstrb,
    output bit axiWr0_wlast,
    output bit axiWr0_wvalid,
    input bit axiWr0_wready,
    input bit [1:0] axiWr0_bresp,
    input bit [3:0] axiWr0_bid,
    input bit axiWr0_bvalid,
    output bit axiWr0_bready,

    // axi_write_if.src
    output bit [31:0] axiWr1_awaddr,
    output bit [3:0] axiWr1_awid,
    output bit [7:0] axiWr1_awlen,
    output bit [2:0] axiWr1_awsize,
    output bit [1:0] axiWr1_awburst,
    output bit axiWr1_awvalid,
    input bit axiWr1_awready,
    output bit [31:0] axiWr1_wdata,
    output bit [3:0] axiWr1_wid,
    output bit [3:0] axiWr1_wstrb,
    output bit axiWr1_wlast,
    output bit axiWr1_wvalid,
    input bit axiWr1_wready,
    input bit [1:0] axiWr1_bresp,
    input bit [3:0] axiWr1_bid,
    input bit axiWr1_bvalid,
    output bit axiWr1_bready,

    // axi_write_if.src
    output bit [31:0] axiWr2_awaddr,
    output bit [3:0] axiWr2_awid,
    output bit [7:0] axiWr2_awlen,
    output bit [2:0] axiWr2_awsize,
    output bit [1:0] axiWr2_awburst,
    output bit axiWr2_awvalid,
    input bit axiWr2_awready,
    output bit [31:0] axiWr2_wdata,
    output bit [3:0] axiWr2_wid,
    output bit [3:0] axiWr2_wstrb,
    output bit axiWr2_wlast,
    output bit axiWr2_wvalid,
    input bit axiWr2_wready,
    input bit [1:0] axiWr2_bresp,
    input bit [3:0] axiWr2_bid,
    input bit axiWr2_bvalid,
    output bit axiWr2_bready,

    // axi_write_if.src
    output bit [31:0] axiWr3_awaddr,
    output bit [3:0] axiWr3_awid,
    output bit [7:0] axiWr3_awlen,
    output bit [2:0] axiWr3_awsize,
    output bit [1:0] axiWr3_awburst,
    output bit axiWr3_awvalid,
    input bit axiWr3_awready,
    output bit [31:0] axiWr3_wdata,
    output bit [3:0] axiWr3_wid,
    output bit [3:0] axiWr3_wstrb,
    output bit axiWr3_wlast,
    output bit axiWr3_wvalid,
    input bit axiWr3_wready,
    input bit [1:0] axiWr3_bresp,
    input bit [3:0] axiWr3_bid,
    input bit axiWr3_bvalid,
    output bit axiWr3_bready,

    // axi4_stream_if.src
    output bit axiStr0_tvalid,
    input bit axiStr0_tready,
    output bit [31:0] axiStr0_tdata,
    output bit [31:0] axiStr0_tstrb,
    output bit [31:0] axiStr0_tkeep,
    output bit axiStr0_tlast,
    output bit [31:0] axiStr0_tid,
    output bit [31:0] axiStr0_tdest,
    output bit [31:0] axiStr0_tuser,

    // axi4_stream_if.src
    output bit axiStr1_tvalid,
    input bit axiStr1_tready,
    output bit [31:0] axiStr1_tdata,
    output bit [31:0] axiStr1_tstrb,
    output bit [31:0] axiStr1_tkeep,
    output bit axiStr1_tlast,
    output bit [31:0] axiStr1_tid,
    output bit [31:0] axiStr1_tdest,
    output bit [31:0] axiStr1_tuser,

    input clk,
    input rst_n
);
    // axi_read_if.src
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd0();

    assign #0 axiRd0_araddr = axiRd0.araddr;
    assign #0 axiRd0_arid = axiRd0.arid;
    assign #0 axiRd0_arlen = axiRd0.arlen;
    assign #0 axiRd0_arsize = axiRd0.arsize;
    assign #0 axiRd0_arburst = axiRd0.arburst;
    assign #0 axiRd0_arvalid = axiRd0.arvalid;
    assign #0 axiRd0.arready = axiRd0_arready;
    assign #0 axiRd0.rdata = axiRd0_rdata;
    assign #0 axiRd0.rid = axiRd0_rid;
    assign #0 axiRd0.rresp = axiRd0_rresp;
    assign #0 axiRd0.rlast = axiRd0_rlast;
    assign #0 axiRd0.rvalid = axiRd0_rvalid;
    assign #0 axiRd0_rready = axiRd0.rready;

    // axi_read_if.src
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd1();

    assign #0 axiRd1_araddr = axiRd1.araddr;
    assign #0 axiRd1_arid = axiRd1.arid;
    assign #0 axiRd1_arlen = axiRd1.arlen;
    assign #0 axiRd1_arsize = axiRd1.arsize;
    assign #0 axiRd1_arburst = axiRd1.arburst;
    assign #0 axiRd1_arvalid = axiRd1.arvalid;
    assign #0 axiRd1.arready = axiRd1_arready;
    assign #0 axiRd1.rdata = axiRd1_rdata;
    assign #0 axiRd1.rid = axiRd1_rid;
    assign #0 axiRd1.rresp = axiRd1_rresp;
    assign #0 axiRd1.rlast = axiRd1_rlast;
    assign #0 axiRd1.rvalid = axiRd1_rvalid;
    assign #0 axiRd1_rready = axiRd1.rready;

    // axi_read_if.src
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd2();

    assign #0 axiRd2_araddr = axiRd2.araddr;
    assign #0 axiRd2_arid = axiRd2.arid;
    assign #0 axiRd2_arlen = axiRd2.arlen;
    assign #0 axiRd2_arsize = axiRd2.arsize;
    assign #0 axiRd2_arburst = axiRd2.arburst;
    assign #0 axiRd2_arvalid = axiRd2.arvalid;
    assign #0 axiRd2.arready = axiRd2_arready;
    assign #0 axiRd2.rdata = axiRd2_rdata;
    assign #0 axiRd2.rid = axiRd2_rid;
    assign #0 axiRd2.rresp = axiRd2_rresp;
    assign #0 axiRd2.rlast = axiRd2_rlast;
    assign #0 axiRd2.rvalid = axiRd2_rvalid;
    assign #0 axiRd2_rready = axiRd2.rready;

    // axi_read_if.src
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd3();

    assign #0 axiRd3_araddr = axiRd3.araddr;
    assign #0 axiRd3_arid = axiRd3.arid;
    assign #0 axiRd3_arlen = axiRd3.arlen;
    assign #0 axiRd3_arsize = axiRd3.arsize;
    assign #0 axiRd3_arburst = axiRd3.arburst;
    assign #0 axiRd3_arvalid = axiRd3.arvalid;
    assign #0 axiRd3.arready = axiRd3_arready;
    assign #0 axiRd3.rdata = axiRd3_rdata;
    assign #0 axiRd3.rid = axiRd3_rid;
    assign #0 axiRd3.rresp = axiRd3_rresp;
    assign #0 axiRd3.rlast = axiRd3_rlast;
    assign #0 axiRd3.rvalid = axiRd3_rvalid;
    assign #0 axiRd3_rready = axiRd3.rready;

    // axi_write_if.src
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr0();

    assign #0 axiWr0_awaddr = axiWr0.awaddr;
    assign #0 axiWr0_awid = axiWr0.awid;
    assign #0 axiWr0_awlen = axiWr0.awlen;
    assign #0 axiWr0_awsize = axiWr0.awsize;
    assign #0 axiWr0_awburst = axiWr0.awburst;
    assign #0 axiWr0_awvalid = axiWr0.awvalid;
    assign #0 axiWr0.awready = axiWr0_awready;
    assign #0 axiWr0_wdata = axiWr0.wdata;
    assign #0 axiWr0_wid = axiWr0.wid;
    assign #0 axiWr0_wstrb = axiWr0.wstrb;
    assign #0 axiWr0_wlast = axiWr0.wlast;
    assign #0 axiWr0_wvalid = axiWr0.wvalid;
    assign #0 axiWr0.wready = axiWr0_wready;
    assign #0 axiWr0.bresp = axiWr0_bresp;
    assign #0 axiWr0.bid = axiWr0_bid;
    assign #0 axiWr0.bvalid = axiWr0_bvalid;
    assign #0 axiWr0_bready = axiWr0.bready;

    // axi_write_if.src
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr1();

    assign #0 axiWr1_awaddr = axiWr1.awaddr;
    assign #0 axiWr1_awid = axiWr1.awid;
    assign #0 axiWr1_awlen = axiWr1.awlen;
    assign #0 axiWr1_awsize = axiWr1.awsize;
    assign #0 axiWr1_awburst = axiWr1.awburst;
    assign #0 axiWr1_awvalid = axiWr1.awvalid;
    assign #0 axiWr1.awready = axiWr1_awready;
    assign #0 axiWr1_wdata = axiWr1.wdata;
    assign #0 axiWr1_wid = axiWr1.wid;
    assign #0 axiWr1_wstrb = axiWr1.wstrb;
    assign #0 axiWr1_wlast = axiWr1.wlast;
    assign #0 axiWr1_wvalid = axiWr1.wvalid;
    assign #0 axiWr1.wready = axiWr1_wready;
    assign #0 axiWr1.bresp = axiWr1_bresp;
    assign #0 axiWr1.bid = axiWr1_bid;
    assign #0 axiWr1.bvalid = axiWr1_bvalid;
    assign #0 axiWr1_bready = axiWr1.bready;

    // axi_write_if.src
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr2();

    assign #0 axiWr2_awaddr = axiWr2.awaddr;
    assign #0 axiWr2_awid = axiWr2.awid;
    assign #0 axiWr2_awlen = axiWr2.awlen;
    assign #0 axiWr2_awsize = axiWr2.awsize;
    assign #0 axiWr2_awburst = axiWr2.awburst;
    assign #0 axiWr2_awvalid = axiWr2.awvalid;
    assign #0 axiWr2.awready = axiWr2_awready;
    assign #0 axiWr2_wdata = axiWr2.wdata;
    assign #0 axiWr2_wid = axiWr2.wid;
    assign #0 axiWr2_wstrb = axiWr2.wstrb;
    assign #0 axiWr2_wlast = axiWr2.wlast;
    assign #0 axiWr2_wvalid = axiWr2.wvalid;
    assign #0 axiWr2.wready = axiWr2_wready;
    assign #0 axiWr2.bresp = axiWr2_bresp;
    assign #0 axiWr2.bid = axiWr2_bid;
    assign #0 axiWr2.bvalid = axiWr2_bvalid;
    assign #0 axiWr2_bready = axiWr2.bready;

    // axi_write_if.src
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr3();

    assign #0 axiWr3_awaddr = axiWr3.awaddr;
    assign #0 axiWr3_awid = axiWr3.awid;
    assign #0 axiWr3_awlen = axiWr3.awlen;
    assign #0 axiWr3_awsize = axiWr3.awsize;
    assign #0 axiWr3_awburst = axiWr3.awburst;
    assign #0 axiWr3_awvalid = axiWr3.awvalid;
    assign #0 axiWr3.awready = axiWr3_awready;
    assign #0 axiWr3_wdata = axiWr3.wdata;
    assign #0 axiWr3_wid = axiWr3.wid;
    assign #0 axiWr3_wstrb = axiWr3.wstrb;
    assign #0 axiWr3_wlast = axiWr3.wlast;
    assign #0 axiWr3_wvalid = axiWr3.wvalid;
    assign #0 axiWr3.wready = axiWr3_wready;
    assign #0 axiWr3.bresp = axiWr3_bresp;
    assign #0 axiWr3.bid = axiWr3_bid;
    assign #0 axiWr3.bvalid = axiWr3_bvalid;
    assign #0 axiWr3_bready = axiWr3.bready;

    // axi4_stream_if.src
    axi4_stream_if #(.tdata_t(axiDataSt), .tid_t(axiAddrSt), .tdest_t(axiAddrSt), .tuser_t(axiAddrSt)) axiStr0();

    assign #0 axiStr0_tvalid = axiStr0.tvalid;
    assign #0 axiStr0.tready = axiStr0_tready;
    assign #0 axiStr0_tdata = axiStr0.tdata;
    assign #0 axiStr0_tstrb = axiStr0.tstrb;
    assign #0 axiStr0_tkeep = axiStr0.tkeep;
    assign #0 axiStr0_tlast = axiStr0.tlast;
    assign #0 axiStr0_tid = axiStr0.tid;
    assign #0 axiStr0_tdest = axiStr0.tdest;
    assign #0 axiStr0_tuser = axiStr0.tuser;

    // axi4_stream_if.src
    axi4_stream_if #(.tdata_t(axiDataSt), .tid_t(axiAddrSt), .tdest_t(axiAddrSt), .tuser_t(axiAddrSt)) axiStr1();

    assign #0 axiStr1_tvalid = axiStr1.tvalid;
    assign #0 axiStr1.tready = axiStr1_tready;
    assign #0 axiStr1_tdata = axiStr1.tdata;
    assign #0 axiStr1_tstrb = axiStr1.tstrb;
    assign #0 axiStr1_tkeep = axiStr1.tkeep;
    assign #0 axiStr1_tlast = axiStr1.tlast;
    assign #0 axiStr1_tid = axiStr1.tid;
    assign #0 axiStr1_tdest = axiStr1.tdest;
    assign #0 axiStr1_tuser = axiStr1.tuser;

    producer dut (
        .axiRd0(axiRd0), // axi_read_if.src
        .axiRd1(axiRd1), // axi_read_if.src
        .axiRd2(axiRd2), // axi_read_if.src
        .axiRd3(axiRd3), // axi_read_if.src
        .axiWr0(axiWr0), // axi_write_if.src
        .axiWr1(axiWr1), // axi_write_if.src
        .axiWr2(axiWr2), // axi_write_if.src
        .axiWr3(axiWr3), // axi_write_if.src
        .axiStr0(axiStr0), // axi4_stream_if.src
        .axiStr1(axiStr1), // axi4_stream_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : producer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _PRODUCER_HDL_SV_WRAPPER_SV_GUARD_
