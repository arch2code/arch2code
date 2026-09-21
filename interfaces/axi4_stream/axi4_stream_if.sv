// AMBA AXI4-Stream Protocol
// The TUSER sideband parameter is optional. It defaults to a plain one-bit
// `logic` placeholder, so a stream that binds no TUSER type carries a single
// undriven bit that nothing in the design ever references.
interface axi4_stream_if #(
        parameter type tdata_t = logic [31:0],
        parameter type tid_t = logic [7:0],
        parameter type tdest_t = logic [7:0],
        parameter type tuser_t = logic
    );

    localparam int unsigned P_TDATA_WIDTH = $size(tdata_t);

    logic                       tvalid;
    logic                       tready;
    tdata_t                     tdata;
    logic [P_TDATA_WIDTH/8-1:0] tstrb;
    logic [P_TDATA_WIDTH/8-1:0] tkeep;
    logic                       tlast;
    tid_t                       tid;
    tdest_t                     tdest;
    tuser_t                     tuser;

    // Source
    modport src (
        output tvalid, tdata, tstrb, tkeep, tlast, tid, tdest, tuser,
        input tready
    );

    // Destination
    modport dst (
        input tvalid, tdata, tstrb, tkeep, tlast, tid, tdest, tuser,
        output tready
    );

endinterface : axi4_stream_if
