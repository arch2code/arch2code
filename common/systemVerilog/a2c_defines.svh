// Project-overridable a2c definitions.
`ifndef A2C_DEFINES_SVH
`define A2C_DEFINES_SVH

// AXI4 transaction ID width. Override with +define+AXI_ID_WIDTH=<n>, and pass
// the matching -DAXI_ID_WIDTH=<n> to the SystemC build so the BFM signal widths
// agree with the Verilated DUT ports. Default 4 preserves prior behaviour.
`ifndef AXI_ID_WIDTH
`define AXI_ID_WIDTH 4
`endif

`endif // A2C_DEFINES_SVH
