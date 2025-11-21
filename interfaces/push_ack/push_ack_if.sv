/*
 * Push-Ack Interface (Blocking)
 *                  ______________________
 *  src.push  _____/                      \__
 *                  ______________________
 *  src.data  _____/         DATA         \__
 *                                      __
 *  dst.ack   _________________________/  \__
 *
 */

interface push_ack_if #(
        parameter type data_t = logic
    );

    logic  push;
    data_t data;
    logic  ack;

    // Source
    modport src (output push, data, input ack);

    // Destination
    modport dst (input push, data, output ack);

endinterface : push_ack_if
