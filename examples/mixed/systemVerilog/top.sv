// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: top
module top
// Generated Import package statement(s)
import mixedBlockC_package::*;
import mixed_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    req_ack_if #(.data_t(aSt), .rdata_t(aASt)) aStuffIf();
    rdy_vld_if #(.data_t(seeSt)) cStuffIf();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg();
    notify_ack_if #() startDone();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBlockA();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBlockB();

// Instances
cpu uCPU (
    .apbReg (apbReg),
    .clk (clk),
    .rst_n (rst_n)
);

blockA uBlockA (
    .aStuffIf (aStuffIf),
    .cStuffIf (cStuffIf),
    .startDone (startDone),
    .apbReg (apb_uBlockA),
    .clk (clk),
    .rst_n (rst_n)
);

apbDecode uAPBDecode (
    .apbReg (apbReg),
    .apb_uBlockA (apb_uBlockA),
    .apb_uBlockB (apb_uBlockB),
    .clk (clk),
    .rst_n (rst_n)
);

blockC uBlockC (
    .see (cStuffIf),
    .clk (clk),
    .rst_n (rst_n)
);

blockB uBlockB (
    .btod (aStuffIf),
    .startDone (startDone),
    .apbReg (apb_uBlockB),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: top