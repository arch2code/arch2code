// AMBA AHB-Lite Protocol, one manager and one subordinate on a point-to-point link.
// The subordinate drives a single hready. A subordinate with separate HREADY and
// HREADYOUT pins ties them together in its own wrapper.
interface ahb_if #(
        parameter type addr_t = logic [31:0],
        parameter type data_t = logic [31:0]
    );

    // Address phase
    addr_t          haddr;
    logic           hsel;
    logic [1:0]     htrans;
    logic           hwrite; // one write, zero read
    logic [2:0]     hsize;
    logic [2:0]     hburst;
    logic [3:0]     hprot;
    logic           hmastlock;

    // Data phase
    data_t          hwdata;
    logic           hready;
    data_t          hrdata;
    logic           hresp; // one ERROR, zero OKAY

    // Source
    modport src (
        output haddr, hsel, htrans, hwrite, hsize, hburst, hprot, hmastlock, hwdata,
        input  hready, hrdata, hresp
    );

    // Destination
    modport dst (
        input  haddr, hsel, htrans, hwrite, hsize, hburst, hprot, hmastlock, hwdata,
        output hready, hrdata, hresp
    );

endinterface : ahb_if
