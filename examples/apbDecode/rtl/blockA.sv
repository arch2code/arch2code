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
    status_if #(.data_t(aRegSt)) roA();
    status_if #(.data_t(un0ARegSt)) rwUn0A();
    status_if #(.data_t(un0ARegSt)) roUn0A();
    external_reg_if #(.data_t(un0ARegSt)) extA();

    // Memory Interfaces
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable0();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable0_reg();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATableX();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATableX_unused();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable1();
    memory_if #(.data_t(aMemSt), .addr_t(aMemAddrSt)) blockATable1_reg();

// Instances
blockARegs ublockARegs (
    .apbReg (apbReg),
    .blockATable0 (blockATable0_reg),
    .blockATable1 (blockATable1_reg),
    .roA (roA),
    .rwUn0A (rwUn0A),
    .roUn0A (roUn0A),
    .extA (extA),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
memory_dp #(.DEPTH(MEMORYA_WORDS), .data_t(aMemSt)) uBlockATable0 (
    .mem_portA (blockATable0),
    .mem_portB (blockATable0_reg),
    .clk (clk)
);

memory_dp #(.DEPTH(MEMORYA_WORDS), .data_t(aMemSt)) uBlockATableX (
    .mem_portA (blockATableX),
    .mem_portB (blockATableX_unused),
    .clk (clk)
);

memory_dp #(.DEPTH(MEMORYA_WORDS), .data_t(aMemSt)) uBlockATable1 (
    .mem_portA (blockATable1),
    .mem_portB (blockATable1_reg),
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
