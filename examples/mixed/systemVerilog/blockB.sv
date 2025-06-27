// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockB
module blockB
// Generated Import package statement(s)
import mixedInclude_package::*;
import mixed_package::*;
import mixedBlockC_package::*;
(
    req_ack_if.dst btod,
    notify_ack_if.dst startDone,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(seeSt)) cStuffIf[3]();
    rdy_vld_if #(.data_t(dSt)) dee0();
    rdy_vld_if #(.data_t(dSt)) dee1();

    // Memory Interfaces
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable0();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable0Unused();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable1();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable1Unused();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable2Port2();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable2();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable3Write();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable3Read();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTableSP0();
    memory_if #(.data_t(nestedSt), .addr_t(bSizeSt)) blockBTableSP();

    // Register Interfaces
    status_if #(.data_t(dRegSt)) rwD();
    status_if #(.data_t(bSizeRegSt)) roBsize();

// Instances
blockBRegs #(.APB_ADDR_MASK('hff_ffff)) uBlockBRegs (
    .apbReg (apbReg),
    .rwD (rwD),
    .roBsize (roBsize),
    .clk (clk),
    .rst_n (rst_n)
);

blockD uBlockD (
    .btod (btod),
    .blockBTable1 (blockBTable1),
    .blockBTableSP (blockBTableSP),
    .cStuffIf (cStuffIf[0]),
    .dee0 (dee0),
    .dee1 (dee1),
    .clk (clk),
    .rst_n (rst_n)
);

blockF #(.bob(BOB0), .fred(0)) uBlockF0 (
    .dStuffIf (dee0),
    .cStuffIf (cStuffIf[1]),
    .clk (clk),
    .rst_n (rst_n)
);

blockF #(.bob(BOB1), .fred(1)) uBlockF1 (
    .dStuffIf (dee1),
    .cStuffIf (cStuffIf[2]),
    .clk (clk),
    .rst_n (rst_n)
);

threeCs uThreeCs (
    .see0 (cStuffIf[0]),
    .see1 (cStuffIf[1]),
    .see2 (cStuffIf[2]),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
// dual port external
seeSt blockBTable0Mem [BSIZE-1:0];
memory_dp_ext #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable0 (
    .mem_portA (blockBTable0),
    .mem_portB (blockBTable0Unused),
    .mem (blockBTable0Mem),
    .clk (clk)
);

// dual port
memory_dp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable1 (
    .mem_portA (blockBTable1),
    .mem_portB (blockBTable1Unused),
    .clk (clk)
);

// dual port
memory_dp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable2 (
    .mem_portA (blockBTable2Port2),
    .mem_portB (blockBTable2),
    .clk (clk)
);

// dual port
memory_dp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable3 (
    .mem_portA (blockBTable3Write),
    .mem_portB (blockBTable3Read),
    .clk (clk)
);

// single port
memory_sp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTableSP0 (
    .mem_port (blockBTableSP0),
    .clk (clk)
);

// single port
memory_sp #(.DEPTH(BSIZE), .data_t(nestedSt)) uBlockBTableSP (
    .mem_port (blockBTableSP),
    .clk (clk)
);


// GENERATED_CODE_END

endmodule: blockB