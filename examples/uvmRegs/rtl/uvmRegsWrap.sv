//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsWrap
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegsWrap
module uvmRegsWrap
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
uvmRegsInner uInner (
    .apbReg (apbReg),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: uvmRegsWrap
