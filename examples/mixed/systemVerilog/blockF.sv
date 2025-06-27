// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockF
module blockF
// Generated Import package statement(s)
import mixed_package::*;
import mixedBlockC_package::*;
#(
    parameter bob,
    parameter fred
)
(
    rdy_vld_if.src cStuffIf,
    rdy_vld_if.dst dStuffIf,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) test();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) testUnused();

// Instances
// Memory Instances
// dual port
memory_dp #(.DEPTH(bob), .data_t(seeSt)) uTest (
    .mem_portA (test),
    .mem_portB (testUnused),
    .clk (clk)
);


// GENERATED_CODE_END

endmodule: blockF