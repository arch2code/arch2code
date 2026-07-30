// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: mixed
module mixed
// Generated Import package statement(s)
import mixed_mixedBlockC_package::*;
import mixed_package::*;
(
    apb_if.dst cpu_main,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    req_ack_if #(.data_t(aSt), .rdata_t(aASt)) aStuffIf();
    rdy_vld_if #(.data_t(seeSt)) cStuffIf();
    notify_ack_if #() startDone();
    rdy_vld_if #(.data_t(seeSt)) dupIf();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBlockA();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBlockB();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBlockG();

// Instances
mixed_blockA uBlockA (
    .aStuffIf (aStuffIf),
    .cStuffIf (cStuffIf),
    .startDone (startDone),
    .dupIf (dupIf),
    .apbReg (apbReg_uBlockA),
    .clk (clk),
    .rst_n (rst_n)
);

mixed_apbDecode uAPBDecode (
    .cpu_main (cpu_main),
    .apbReg_uBlockA (apbReg_uBlockA),
    .apbReg_uBlockB (apbReg_uBlockB),
    .apbReg_uBlockG (apbReg_uBlockG),
    .clk (clk),
    .rst_n (rst_n)
);

mixed_blockC uBlockC (
    .see (cStuffIf),
    .clk (clk),
    .rst_n (rst_n)
);

mixed_blockB uBlockB (
    .btod (aStuffIf),
    .startDone (startDone),
    .dupIf (dupIf),
    .apbReg (apbReg_uBlockB),
    .clk (clk),
    .rst_n (rst_n)
);

mixed_blockG #(.fred(0)) uBlockG (
    .apbReg (apbReg_uBlockG),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: mixed