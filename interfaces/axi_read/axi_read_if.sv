// AMBA AXI4 Protocol
interface axi_read_if #(
        parameter type addr_t = logic [31:0],
        parameter type data_t = logic [31:0]
    );

    // Address Channel
    logic [3:0]     arid;
    addr_t          araddr;
    logic [7:0]     arlen;
    logic [2:0]     arsize;
    logic [1:0]     arburst;
    //axiUserSt     aruser; // optional
    logic           arvalid;
    logic           arready;

    // Data Channel
    logic [3:0]     rid;
    data_t          rdata;
    logic [1:0]     rresp;
    logic           rlast;
    //axiUserSt     ruser; // optional
    logic           rvalid;
    logic           rready;

    // Source
    modport src (
        // Address Channel
        output arid, araddr, arlen, arsize, arburst, /*aruser,*/ arvalid, input arready,
        // Data Channel
        input  rid, rdata, rresp, rlast, /*ruser,*/ rvalid, output rready
    );

    // Destination
    modport dst (
        // Address Channel
        input  arid, araddr, arlen, arsize, arburst, /*aruser,*/ arvalid, output arready,
        // Data Channel
        output rid, rdata, rresp, rlast, /*ruser,*/ rvalid, input rready
    );

endinterface : axi_read_if
