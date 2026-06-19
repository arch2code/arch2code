// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: someRapper
module someRapper
// Generated Import package statement(s)
import apbDecode_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBlockA();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBlockB();

// Instances
apbDecode uAPBDecode (
    .apbReg (apbReg),
    .apbReg_uBlockA (apbReg_uBlockA),
    .apbReg_uBlockB (apbReg_uBlockB),
    .clk (clk),
    .rst_n (rst_n)
);

blockA uBlockA (
    .apbReg (apbReg_uBlockA),
    .clk (clk),
    .rst_n (rst_n)
);

blockB uBlockB (
    .apbReg (apbReg_uBlockB),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule : someRapper