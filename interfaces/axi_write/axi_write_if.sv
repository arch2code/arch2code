// AMBA AXI4 Protocol
// The USER sideband parameters are optional. Each defaults to a plain one-bit
// `logic` placeholder, so an interface that binds no USER type carries a single
// undriven bit per channel that nothing in the design ever references. id_t is
// optional too, defaulting to the plain 4-bit AXI4 transaction id.
interface axi_write_if #(
        parameter type addr_t = logic[1:0],
        parameter type data_t = logic[1:0],
        parameter type strb_t = logic[1:0],
        parameter type awuser_t = logic,
        parameter type wuser_t = logic,
        parameter type buser_t = logic,
        parameter type id_t = logic [3:0]
    );

    // Address Channel
    id_t            awid;
    addr_t          awaddr;
    logic [7:0]     awlen;
    logic [2:0]     awsize;
    logic [1:0]     awburst;
    awuser_t        awuser;
    logic           awvalid;
    logic           awready;

    // Data Channel
    id_t            wid;
    data_t          wdata;
    strb_t          wstrb;
    logic           wlast;
    wuser_t         wuser;
    logic           wvalid;
    logic           wready;

    // Response Channel
    id_t            bid;
    logic [1:0]     bresp;
    buser_t         buser;
    logic           bvalid;
    logic           bready;

    // Source
    modport src (
        // Address Channel
        output awid, awaddr, awlen, awsize, awburst, awuser, awvalid, input awready,
        // Data Channel
        output wid, wdata, wstrb, wlast, wuser, wvalid, input wready,
        // Response Channel
        input  bid, bresp, buser, bvalid, output bready
    );

    // Destination
    modport dst (
        // Address Channel
        input awid, awaddr, awlen, awsize, awburst, awuser, awvalid, output awready,
        // Data Channel
        input wid, wdata, wstrb, wlast, wuser, wvalid, output wready,
        // Response Channel
        output  bid, bresp, buser, bvalid, input bready
    );

endinterface : axi_write_if
