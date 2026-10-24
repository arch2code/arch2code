interface external_reg_if();
    parameter type data_t = logic [31:0];
    parameter type write_t = logic [1:0];
    data_t wdata;
    data_t rdata;
    write_t write;
    logic pslverr;

    // Source
    modport src (output write, wdata, input rdata, pslverr);

    // Destination
    modport dst (input write, wdata, output rdata, pslverr);

endinterface : external_reg_if
