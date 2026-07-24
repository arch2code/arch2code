// Dummy module for verilation in makefile
module vl_dummy();

  // triggers verilator to include verilated_dpi.c in build process
  export "DPI-C" function vl_dpi_f;

  function void vl_dpi_f();
  endfunction : vl_dpi_f

endmodule : vl_dummy
