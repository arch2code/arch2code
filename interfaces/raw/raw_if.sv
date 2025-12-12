/*
 * Raw Interface (Blocking)
 *                  ______________________
 *  src.data  _____/         DATA         \__
 *
 */

interface raw_if #(
        parameter type data_t = logic
    );

    data_t data;

    // Source
    modport src (output data);

    // Destination
    modport dst (input data);

endinterface : raw_if
