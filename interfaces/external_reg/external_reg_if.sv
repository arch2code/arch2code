interface external_reg_if();
    parameter type data_t = logic [31:0];
    parameter type write_t = logic [1:0];
    data_t wdata;
    data_t rdata;
    write_t write;
    // The owner refuses a write by driving pslverr with write. The register
    // handler reads it only under project.yaml fileGeneration.regBusErrorResponses,
    // so an owner in a project without that option leaves it undriven.
    /* verilator lint_off UNUSEDSIGNAL */
    logic pslverr;
    /* verilator lint_on UNUSEDSIGNAL */

    // Source
    modport src (output write, wdata, input rdata, pslverr);

    // Destination
    modport dst (input write, wdata, output rdata, pslverr);

endinterface : external_reg_if
