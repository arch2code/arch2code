// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockB
module blockB
// Generated Import package statement(s)
import apbDecode_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(bMemSt), .addr_t(bMemAddrSt)) blockBTable();
    memory_if #(.data_t(bMemSt), .addr_t(bMemAddrSt)) blockBTableRegs();

    // Register Interfaces
    status_if #(.data_t(un0BRegSt)) rwUn0B();
    status_if #(.data_t(aSizeRegSt)) roB();

// Instances
blockBRegs #(.APB_ADDR_MASK('hff_ffff)) uBlockBRegs (
    .apbReg (apbReg),
    .rwUn0B (rwUn0B),
    .roB (roB),
    .blockBTable (blockBTableRegs),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
// dual port
memory_dp #(.DEPTH(MEMORYB_WORDS), .data_t(bMemSt)) uBlockBTable (
    .mem_portA (blockBTable),
    .mem_portB (blockBTableRegs),
    .clk (clk)
);


// GENERATED_CODE_END

    assign roB.data = aSizeT'(29'h1b45f720);

endmodule // blockB
