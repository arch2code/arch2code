// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: top
module top
// Generated Import package statement(s)
import apbDecode_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg();

// Instances
cpu uCPU (
    .apbReg (apbReg),
    .clk (clk),
    .rst_n (rst_n)
);

someRapper uSomeRapper (
    .apbReg (apbReg),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule : top