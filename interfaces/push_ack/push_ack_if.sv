/*
 * Push-Ack Interface (Blocking)
 *                  ______________________
 *  src.push  _____/                      \__
 *                  ______________________
 *  src.data  _____/         DATA         \__
 *                                      __
 *  dst.ack   _________________________/  \__
 *
 * The source must not wait for ack before raising push, and once push is
 * high it holds push and data until the transfer completes. ack may wait
 * for push.
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
