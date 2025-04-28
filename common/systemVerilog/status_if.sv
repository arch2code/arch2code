interface status_if #(
        parameter type data_t = logic
    );

    data_t data;

    // Source
    modport src (output data);

    // Destination
    modport dst (input data);

endinterface : status_if
