//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegs
module uvmRegs
// Generated Import package statement(s)
import uvmRegs_package::*;
(
    rdy_vld_if.dst in,
    rdy_vld_if.src out,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    rdy_vld_if #(.data_t(uvmRegsWordSt)) scaled0();
    rdy_vld_if #(.data_t(uvmRegsWordSt)) scaled1();
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg_uScale0();
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg_uScale1();
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg_uStat();
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg_uWrap();
    apb_if #(.addr_t(uvmRegsAddrSt), .data_t(uvmRegsDataSt)) apbReg_uBridge();

// Instances
uvmRegsRouter uRouter (
    .apbReg (apbReg),
    .apbReg_uScale0 (apbReg_uScale0),
    .apbReg_uScale1 (apbReg_uScale1),
    .apbReg_uStat (apbReg_uStat),
    .apbReg_uWrap (apbReg_uWrap),
    .apbReg_uBridge (apbReg_uBridge),
    .clk (clk),
    .rst_n (rst_n)
);

uvmRegsScale #(.UVM_REGS_SCALE_W(4)) uScale0 (
    .in (in),
    .out (scaled0),
    .apbReg (apbReg_uScale0),
    .clk (clk),
    .rst_n (rst_n)
);

uvmRegsScale #(.UVM_REGS_SCALE_W(8)) uScale1 (
    .in (scaled0),
    .out (scaled1),
    .apbReg (apbReg_uScale1),
    .clk (clk),
    .rst_n (rst_n)
);

uvmRegsStat #(.UVM_REGS_TAB_W(12)) uStat (
    .out (out),
    .in (scaled1),
    .apbReg (apbReg_uStat),
    .clk (clk),
    .rst_n (rst_n)
);

uvmRegsBridge uBridge (
    .apbReg (apbReg_uBridge),
    .clk (clk),
    .rst_n (rst_n)
);

uvmRegsWrap uWrap (
    .apbReg (apbReg_uWrap),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: uvmRegs
