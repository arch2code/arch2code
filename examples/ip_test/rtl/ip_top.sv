//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ip_top
module ip_top
// Generated Import package statement(s)
import ip_package::*;
import ip_top_package::*;
(
    apb_if.dst cpu_main,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(ipDataSt)) out0();
    push_ack_if #(.data_t(ipDataSt)) out1();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uIp0();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uIp1();

// Instances
apbDecode uAPBDecode (
    .cpu_main (cpu_main),
    .apb_uIp0 (apb_uIp0),
    .apb_uIp1 (apb_uIp1),
    .clk (clk),
    .rst_n (rst_n)
);

src uSrc (
    .out0 (out0),
    .out1 (out1),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), .IP_NONCONST_DEPTH(24)) uIp0 (
    .ipDataIf (out0),
    .apbReg (apb_uIp0),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(12), .IP_MEM_DEPTH(8), .IP_NONCONST_DEPTH(12)) uIp1 (
    .ipDataIf (out1),
    .apbReg (apb_uIp1),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ip_top
