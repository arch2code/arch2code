//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsBridge
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegsBridge
module uvmRegsBridge
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg_uDeep();

// Instances
uvmRegsBridgeRouter uBridgeRouter (
    .apbReg (apbReg),
    .apbReg_uDeep (apbReg_uDeep),
    .clk (clk),
    .rst_n (rst_n)
);

uvmRegsDeep uDeep (
    .apbReg (apbReg_uDeep),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: uvmRegsBridge
