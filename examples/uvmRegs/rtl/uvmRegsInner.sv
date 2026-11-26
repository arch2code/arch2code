//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsInner
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegsInner
module uvmRegsInner
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(uvmRegsByteSt)) tag();

// Instances
uvmRegsInner_regs u_uvmRegsInner_regs (
    .apbReg (apbReg),
    .tag (tag),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: uvmRegsInner
