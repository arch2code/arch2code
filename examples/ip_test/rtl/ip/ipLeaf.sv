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

    // Module-local parameterizable type/struct declarations
    typedef logic[LEAF_DATA_WIDTH-1:0] ipLeafDataT; //ipLeaf data word, parameterizable
    typedef logic[$clog2(LEAF_MEM_DEPTH)-1:0] ipLeafMemAddrT; //Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
    typedef struct packed {
        ipLeafDataT data; //Leaf memory word
    } ipLeafMemSt;
    typedef struct packed {
        ipLeafMemAddrT address; //Leaf memory address
    } ipLeafMemAddrSt;

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
