// Test protocol with a hdlparam derived from the struct parameter (axi4_stream tstrb pattern).
interface idth_if #(
        parameter type s_t  = logic,
        parameter type ts_t = logic,
        parameter type o2_t = logic [2:0]
    );
    localparam int unsigned P_S_BYTES = ($bits(s_t) + 7) / 8;
    logic  vld;
    s_t    s;
    logic [P_S_BYTES-1:0] sb;
    ts_t   ts;
    o2_t   o2;
    logic  rdy;
    modport src (output vld, s, sb, ts, o2, input rdy);
    modport dst (input vld, s, sb, ts, o2, output rdy);
endinterface : idth_if
