/*
 * Ready-Valid Interface (Non blocking)
 *                  _____________________
 *  src.vld  _____/                      \__
 *                 ______________________
 *  src.data _____/          D           \__
 *           __                        _____
 *  dst.rdy    \______________________/
 *
 * The source must not wait for rdy before raising vld, and once vld is high
 * it holds vld and data until the transfer completes. rdy may wait for vld.
 */

interface rdy_vld_if #(
        parameter type data_t = logic
    );
    logic  vld;
    data_t data;
    logic  rdy;

    // Source
    modport src  (output vld, data, input rdy);

    // Destination
    modport dst  (input vld, data, output rdy);

endinterface : rdy_vld_if
