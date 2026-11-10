// AMBA AHB-Lite, one slave per link. The src end drives hsel and the slave's
// hready input, which it ties to hreadyout because no other slave shares the
// link.
interface ahb_if #(
        parameter type data_t = logic,
        parameter type addr_t = logic
    );

    logic        hsel;
    addr_t       haddr;
    logic [1:0]  htrans; // 0 IDLE, 1 BUSY, 2 NONSEQ, 3 SEQ
    logic        hwrite; // one write, zero read
    logic [2:0]  hsize;  // 2 is a 32-bit word
    data_t       hwdata;
    logic        hready;
    logic        hreadyout;
    logic        hresp;  // one ERROR, zero OKAY
    data_t       hrdata;

    // Source
    modport src (output hsel, haddr, htrans, hwrite, hsize, hwdata, hready, input  hreadyout, hresp, hrdata);

    // Destination
    modport dst (input  hsel, haddr, htrans, hwrite, hsize, hwdata, hready, output hreadyout, hresp, hrdata);

endinterface : ahb_if
