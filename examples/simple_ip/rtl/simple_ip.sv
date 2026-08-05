//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: simple_ip
module simple_ip
// Generated Import package statement(s)
import ip_package::*;
import simple_ip_package::*;
import common_shared_types_package::*;
(
    apb_if.dst cpu_main,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(simpleData8St)) out();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uIp();

// Instances
simple_ip_apbDecode uAPBDecode (
    .cpu_main (cpu_main),
    .apbReg_uIp (apbReg_uIp),
    .clk (clk),
    .rst_n (rst_n)
);

simple_ip_dataGen uDataGen (
    .out (out),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), .IP_NONCONST_DEPTH(24)) uIp (
    .ipDataIf (out),
    .regs (apbReg_uIp),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: simple_ip
