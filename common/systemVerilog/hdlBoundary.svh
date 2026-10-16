// Delay on the port assigns of a verification wrapper (<block>_hdl_sv_wrapper).
// VCS needs a delta delay on each assign inside the wrapper; a delay at the
// port map boundary does not replace it. Under Verilator --timing a #0 stops
// combinational outputs reaching SystemC, so the delay is empty there.
`ifndef HDL_BOUNDARY_SVH
`define HDL_BOUNDARY_SVH

`ifdef VERILATOR
`define A2C_HDL_BOUNDARY_DLY
`else
`define A2C_HDL_BOUNDARY_DLY #0
`endif

`endif
