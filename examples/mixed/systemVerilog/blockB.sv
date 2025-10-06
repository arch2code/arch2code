// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockB
module blockB
// Generated Import package statement(s)
import mixedInclude_package::*;
import mixedBlockC_package::*;
import mixed_package::*;
(
    req_ack_if.dst btod,
    notify_ack_if.dst startDone,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    rdy_vld_if #(
.data_t(seeSt)
) cStuffIf
();
    rdy_vld_if #(
.data_t(seeSt)
) cStuff1
();
    rdy_vld_if #(
.data_t(seeSt)
) cStuff2
();
    rdy_vld_if #(
.data_t(dSt)
) dee0
();
    rdy_vld_if #(
.data_t(dSt)
) dee1
();
    rdy_vld_if #(
.data_t(dSt)
) loopDF
();
    rdy_vld_if #(
.data_t(dSt)
) loopFF
();
    rdy_vld_if #(
.data_t(dSt)
) loopFD
();
    status_if #(
.data_t(dRegSt)
) rwD
();
    status_if #(
.data_t(bSizeRegSt)
) roBsize
();

    // Memory Interfaces
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable0();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable0_unused();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable1_port1();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable1_reg();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable2_port1();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable2_port2();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable3_read();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTable3_write();
    memory_if #(.data_t(seeSt), .addr_t(bSizeSt)) blockBTableSP0();
    memory_if #(.data_t(nestedSt), .addr_t(bSizeSt)) blockBTableSP_bob();

// Instances
blockBRegs uBlockBRegs (
    .apbReg (apbReg),
    .blockBTable1 (blockBTable1_reg),
    .rwD (rwD),
    .roBsize (roBsize),
    .clk (clk),
    .rst_n (rst_n)
);

blockD uBlockD (
    .btod (btod),
    .blockBTable1 (blockBTable1_port1),
    .blockBTableSP (blockBTableSP_bob),
    .cStuffIf (cStuffIf),
    .dee0 (dee0),
    .dee1 (dee1),
    .outD (loopDF),
    .inD (loopFD),
    .rwD (rwD),
    .roBsize (roBsize),
    .clk (clk),
    .rst_n (rst_n)
);

blockF #(.bob(BOB0), .fred(0)) uBlockF0 (
    .cStuffIf (cStuff1),
    .dStuffIf (dee0),
    .dSin (loopDF),
    .dSout (loopFF),
    .rwD (rwD),
    .clk (clk),
    .rst_n (rst_n)
);

blockF #(.bob(BOB1), .fred(1)) uBlockF1 (
    .cStuffIf (cStuff2),
    .dStuffIf (dee1),
    .dSin (loopFF),
    .dSout (loopFD),
    .rwD (rwD),
    .clk (clk),
    .rst_n (rst_n)
);

threeCs uThreeCs (
    .see0 (cStuffIf),
    .see1 (cStuff1),
    .see2 (cStuff2),
    .clk (clk),
    .rst_n (rst_n)
);

// Memory Instances
seeSt blockBTable0Mem [BSIZE-1:0];
memory_dp_ext #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable0 (
    .mem_portA (blockBTable0),
    .mem_portB (blockBTable0_unused),
    .mem (blockBTable0Mem),
    .clk (clk)
);

memory_dp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable1 (
    .mem_portA (blockBTable1_port1),
    .mem_portB (blockBTable1_reg),
    .clk (clk)
);

memory_dp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable2 (
    .mem_portA (blockBTable2_port1),
    .mem_portB (blockBTable2_port2),
    .clk (clk)
);

memory_dp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTable3 (
    .mem_portA (blockBTable3_read),
    .mem_portB (blockBTable3_write),
    .clk (clk)
);

memory_sp #(.DEPTH(BSIZE), .data_t(seeSt)) uBlockBTableSP0 (
    .mem_port (blockBTableSP0),
    .clk (clk)
);

memory_sp #(.DEPTH(BSIZE), .data_t(nestedSt)) uBlockBTableSP (
    .mem_port (blockBTableSP_bob),
    .clk (clk)
);

// GENERATED_CODE_END

endmodule: blockB