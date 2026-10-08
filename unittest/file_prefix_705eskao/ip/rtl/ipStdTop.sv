//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdTop
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ipStdTop
module ipStdTop
// Generated Import package statement(s)
import ipTop_package::*;
import ip_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(ipRegAddrSt), .data_t(ipRegDataSt)) apbOut();
    push_ack_if #(.data_t(ipStdData8St)) out0();
    apb_if #(.addr_t(ipRegAddrSt), .data_t(ipRegDataSt)) ipReg_uIp();

// Instances
ipStdMaster uIpStdMaster (
    .apbOut (apbOut),
    .clk (clk),
    .rst_n (rst_n)
);

ipStdDriver uIpStdDriver (
    .out0 (out0),
    .clk (clk),
    .rst_n (rst_n)
);

ipStdDecode uIpStdDecode (
    .ipReg (apbOut),
    .ipReg_uIp (ipReg_uIp),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), .IP_NONCONST_DEPTH(24)) uIp (
    .ipDataIf (out0),
    .regs (ipReg_uIp),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ipStdTop
