// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: apbDecode_blockA
module apbDecode_blockA
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
apbDecode_blockARegs ublockARegs (
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

    // LocalRegAccess parity: reproduce the model blockA startup thread so the
    // RTL block establishes the same power-up state the model seeds locally.

    // extA local write {fa='a', fb=0xfefe1234, fc='c'}: power-up seed value,
    // then capture subsequent bus write pulses (extA.write) as before.
    localparam un0ARegSt EXTA_SEED = '{fa: 8'h61, fb: 32'hfefe1234, fc: 8'h63};
    `DFFR_INST(un0ARegSt, extAReg, EXTA_SEED)
    always_comb begin
        n_extAReg = extAReg;
        if (|extA.write) begin
            n_extAReg = extA.wdata;
        end
    end

    assign extA.rdata = extAReg;

    // blockATable1[0x5] = 0x2a782d645e49c378: one-shot local write on port A
    // after power-up, then leave port A idle so a bus (port B) read sees it.
    `DFF_INST(logic, seedDone)
    always_comb begin
        n_seedDone = 1'b1;

        blockATable1.addr       = '0;
        blockATable1.write_data = '0;
        blockATable1.wr_en      = 1'b0;
        blockATable1.enable     = 1'b0;
        if (!seedDone) begin
            blockATable1.addr.address    = aAddrBitsT'(5);
            blockATable1.write_data.data = aDataBitsT'(64'h2a782d645e49c378);
            blockATable1.wr_en           = 1'b1;
            blockATable1.enable          = 1'b1;
        end
    end


endmodule // blockA
