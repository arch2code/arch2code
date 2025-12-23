// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: mixed
module mixed
// Generated Import package statement(s)
import mixedBlockC_package::*;
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
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBlockA();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBlockB();

// Instances
blockA uBlockA (
    .aStuffIf (aStuffIf),
    .cStuffIf (cStuffIf),
    .startDone (startDone),
    .dupIf (dupIf),
    .apbReg (apb_uBlockA),
    .clk (clk),
    .rst_n (rst_n)
);

apbDecode uAPBDecode (
    .cpu_main (cpu_main),
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
    .dupIf (dupIf),
    .apbReg (apb_uBlockB),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: mixed