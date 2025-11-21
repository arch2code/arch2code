// AMBA APB3 Protocol
interface apb_if #(
        parameter type data_t = logic,
        parameter type addr_t = logic
    );

    addr_t paddr;
    logic  psel;
    logic  penable;
    logic  pwrite; // one write, zero read
    data_t pwdata;
    logic  pready;
    data_t prdata;
    logic  pslverr;

    // Source
    modport src (output paddr, psel, penable, pwrite, pwdata, input  pready, prdata, pslverr);

    // Destination
    modport dst (input  paddr, psel, penable, pwrite, pwdata, output pready, prdata, pslverr);

endinterface : apb_if
