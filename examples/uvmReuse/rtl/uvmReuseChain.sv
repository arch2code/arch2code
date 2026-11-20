//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseChain
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmReuseChain
module uvmReuseChain
// Generated Import package statement(s)
import uvmReuse_package::*;
import uvmReuseLeaf_package::*;
#(
    parameter int unsigned UVM_REUSE_B_W = 32'h0000_0008
)
(
    rdy_vld_if.dst in,
    rdy_vld_if.src out,
    apb_if.dst apbReg,
    input clk, clkAux, rst_n, rstAux_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(uvmReuseBeatSt)) mid();
    push_ack_if #(.data_t(uvmReuseCountSt)) ticks();
    apb_if #(.addr_t(uvmReuseAddrSt), .data_t(uvmReuseDataSt)) apbReg_uLeafA();
    apb_if #(.addr_t(uvmReuseAddrSt), .data_t(uvmReuseDataSt)) apbReg_uLeafB();

// Instances
uvmReuseRouter uRouter (
    .apbReg (apbReg),
    .apbReg_uLeafA (apbReg_uLeafA),
    .apbReg_uLeafB (apbReg_uLeafB),
    .clk (clk),
    .rst_n (rst_n)
);

uvmReuseLeaf #(.UVM_REUSE_OFF_W(8)) uLeafA (
    .in (in),
    .out (mid),
    .apbReg (apbReg_uLeafA),
    .clk (clk),
    .rst_n (rst_n)
);

uvmReuseLeaf #(.UVM_REUSE_OFF_W(UVM_REUSE_B_W)) uLeafB (
    .out (out),
    .in (mid),
    .apbReg (apbReg_uLeafB),
    .clk (clk),
    .rst_n (rst_n)
);

uvmReuseTick uTick (
    .out (ticks),
    .clkTick (clkAux),
    .rstTick_n (rstAux_n)
);

uvmReuseTock uTock (
    .in (ticks),
    .clkTock (clkAux),
    .rstTock_n (rstAux_n)
);

// GENERATED_CODE_END

endmodule: uvmReuseChain
