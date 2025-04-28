/*
 * Pop-Ack Interface (Blocking)
 *                  ______________________
 *  src.pop   _____/                      \__
 *                                      __
 *  dst.ack   _________________________/  \__
 *                                      __
 *  dst.rdata _________________________/RD\__
 *
 */

interface pop_ack_if #(
        parameter type rdata_t = logic
    );

    logic   pop;
    logic   ack;
    rdata_t rdata;

    // Source
    modport src (output pop, input ack, rdata);

    // Destination
    modport dst (input pop, output ack, rdata);

endinterface : pop_ack_if
