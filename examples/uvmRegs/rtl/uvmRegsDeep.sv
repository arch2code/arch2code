//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsDeep
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegsDeep
module uvmRegsDeep
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(uvmRegsIdentSt)) ident();
    status_if #(.data_t(uvmRegsByteSt)) cfg();

// Instances
uvmRegsDeep_regs u_uvmRegsDeep_regs (
    .apbReg (apbReg),
    .ident (ident),
    .cfg (cfg),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

    assign ident.data.ident = uvmRegsWordT'(UVM_REGS_IDENT);

endmodule: uvmRegsDeep
