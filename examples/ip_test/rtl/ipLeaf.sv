//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ipLeaf
module ipLeaf
// Generated Import package statement(s)
import ipLeaf_package::*;
#(
    parameter LEAF_DATA_WIDTH,
    parameter LEAF_MEM_DEPTH
)
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(ipLeafMemSt), .addr_t(ipLeafMemAddrSt)) ipLeafMem();
    memory_if #(.data_t(ipLeafMemSt), .addr_t(ipLeafMemAddrSt)) ipLeafMem_unused();

// Instances
// Memory Instances
memory_dp #(.DEPTH(LEAF_MEM_DEPTH), .data_t(ipLeafMemSt)) uIpLeafMem (
    .mem_portA (ipLeafMem),
    .mem_portB (ipLeafMem_unused),
    .clk (clk)
);

// GENERATED_CODE_END

endmodule: ipLeaf
