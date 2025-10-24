/*
 * Notify-Ack Interface (Blocking)
 *                   ______________________
 *  src.notify _____/                      \__
 *                                       __
 *  dst.ack    _________________________/  \__
 *
 */

interface notify_ack_if #();

    logic notify;
    logic ack;

    // Source
    modport src (output notify, input ack);

    // Destination
    modport dst (input notify, output ack);

endinterface : notify_ack_if
