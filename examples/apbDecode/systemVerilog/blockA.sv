// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockA
module blockA
// Generated Import package statement(s)
import apbDecode_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Memory Interfaces
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable0();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable0Regs();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATableX();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATableXUnused();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable1();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable1Regs();

    // Register Interfaces
    status_if #(.data_t(aRegSt)) roA();
    status_if #(.data_t(un0ARegSt)) rwUn0A();
    status_if #(.data_t(un0ARegSt)) roUn0A();
    external_reg_if #(.data_t(un0ARegSt)) extA();

// Instances
blockARegs #(.APB_ADDR_MASK('hff_ffff)) uBlockARegs (
    .apbReg (apbReg),
    .roA (roA),
    .rwUn0A (rwUn0A),
    .roUn0A (roUn0A),
    .extA (extA),
    .blockATable0 (blockATable0Regs),
    .blockATable1 (blockATable1Regs),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
// dual port
memory_dp #(.DEPTH(MEMORYA_WORDS), .data_t(aMemSt)) uBlockATable0 (
    .mem_portA (blockATable0),
    .mem_portB (blockATable0Regs),
    .clk (clk)
);

// dual port
memory_dp #(.DEPTH(MEMORYA_WORDS), .data_t(aMemSt)) uBlockATableX (
    .mem_portA (blockATableX),
    .mem_portB (blockATableXUnused),
    .clk (clk)
);

// dual port
memory_dp #(.DEPTH(MEMORYA_WORDS), .data_t(aMemSt)) uBlockATable1 (
    .mem_portA (blockATable1),
    .mem_portB (blockATable1Regs),
    .clk (clk)
);


// GENERATED_CODE_END

    assign roA.data.a = 37'h1063686172;

    assign roUn0A.data = rwUn0A.data;
    
    un0ARegSt extAReg;
    
    always @(posedge clk) if(|extA.write) begin
        extAReg <= extA.wdata;
    end
    
    assign extA.rdata = extAReg;
    

endmodule // blockA
