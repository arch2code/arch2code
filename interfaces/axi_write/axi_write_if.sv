// AMBA AXI4 Protocol
interface axi_write_if #(
        parameter type addr_t = logic[1:0],
        parameter type data_t = logic[1:0],
        parameter type strb_t = logic[1:0]
    );

    // Address Channel
    logic [3:0]     awid;
    addr_t          awaddr;
    logic [7:0]     awlen;
    logic [2:0]     awsize;
    logic [1:0]     awburst;
    //axiUserSt     awuser; // optional
    logic           awvalid;
    logic           awready;

    // Data Channel
    logic [3:0]     wid;
    data_t          wdata;
    strb_t          wstrb;
    logic           wlast;
    //axiUserSt     wuser; // optional
    logic           wvalid;
    logic           wready;

    // Response Channel
    logic [3:0]     bid;
    logic [1:0]     bresp;
    //axiUserSt     buser; // optional
    logic           bvalid;
    logic           bready;

    // Source
    modport src (
        // Address Channel
        output awid, awaddr, awlen, awsize, awburst, /*awuser,*/ awvalid, input awready,
        // Data Channel
        output wid, wdata, wstrb, wlast, /*wuser,*/ wvalid, input wready,
        // Response Channel
        input  bid, bresp, /*buser,*/ bvalid, output bready
    );

    // Destination
    modport dst (
        // Address Channel
        input awid, awaddr, awlen, awsize, awburst, /*awuser,*/ awvalid, output awready,
        // Data Channel
        input wid, wdata, wstrb, wlast, /*wuser,*/ wvalid, output wready,
        // Response Channel
        output  bid, bresp, /*buser,*/ bvalid, input bready
    );

endinterface : axi_write_if
