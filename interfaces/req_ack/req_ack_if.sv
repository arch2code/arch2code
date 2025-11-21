/*
 * Req-Ack Interface (Blocking)
 *                  ______________________
 *  src.req   _____/                      \__
 *                  ______________________
 *  src.data  _____/         DATA         \__
 *                                      __
 *  dst.ack   _________________________/  \__
 *                                      __
 *  dst.rdata _________________________/RD\__
 *
 */

interface req_ack_if #(
        parameter type data_t = logic,
        parameter type rdata_t = logic
    );

    logic   req;
    data_t  data;
    logic   ack;
    rdata_t rdata;

    // Source
    modport src  (output req, data, input ack, rdata);

    // Destination
    modport dst  (input req, data, output ack, rdata);

endinterface : req_ack_if
