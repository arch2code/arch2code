// AMBA AXI4 Protocol
// The USER sideband parameters are optional. Each defaults to a plain one-bit
// `logic` placeholder, so an interface that binds no USER type carries a single
// undriven bit per channel that nothing in the design ever references. id_t is
// optional too, defaulting to the plain 4-bit AXI4 transaction id.
interface axi_read_if #(
        parameter type addr_t = logic [31:0],
        parameter type data_t = logic [31:0],
        parameter type aruser_t = logic,
        parameter type ruser_t = logic,
        parameter type id_t = logic [3:0]
    );

    // Address Channel
    id_t            arid;
    addr_t          araddr;
    logic [7:0]     arlen;
    logic [2:0]     arsize;
    logic [1:0]     arburst;
    aruser_t        aruser;
    logic           arvalid;
    logic           arready;

    // Data Channel
    id_t            rid;
    data_t          rdata;
    logic [1:0]     rresp;
    logic           rlast;
    ruser_t         ruser;
    logic           rvalid;
    logic           rready;

    // Source
    modport src (
        // Address Channel
        output arid, araddr, arlen, arsize, arburst, aruser, arvalid, input arready,
        // Data Channel
        input  rid, rdata, rresp, rlast, ruser, rvalid, output rready
    );

    // Destination
    modport dst (
        // Address Channel
        input  arid, araddr, arlen, arsize, arburst, aruser, arvalid, output arready,
        // Data Channel
        output rid, rdata, rresp, rlast, ruser, rvalid, input rready
    );

endinterface : axi_read_if
