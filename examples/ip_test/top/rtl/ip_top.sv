//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ip_test_ip_top
module ip_test_ip_top
// Generated Import package statement(s)
import ipBridge_package::*;
import ip_package::*;
import ip_test_src_package::*;
import ip_test_ip_top_package::*;
import common_shared_types_package::*;
(
    apb_if.dst cpu_main,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(srcOut0BoundarySt)) out0();
    push_ack_if #(.data_t(srcOut1BoundarySt)) out1();
    push_ack_if #(.data_t(srcOut0BoundarySt)) out2();
    push_ack_if #(.data_t(srcOut1BoundarySt)) out3();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBridge();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uIp0();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uIp1();

// Instances
ip_test_apbDecode uAPBDecode (
    .cpu_main (cpu_main),
    .apbReg_uBridge (apbReg_uBridge),
    .apbReg_uIp0 (apbReg_uIp0),
    .apbReg_uIp1 (apbReg_uIp1),
    .clk (clk),
    .rst_n (rst_n)
);

ip_test_src #(.OUT0_DATA_WIDTH(8), .OUT1_DATA_WIDTH(70)) uSrc (
    .out0 (out0),
    .out1 (out1),
    .out2 (out2),
    .out3 (out3),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), .IP_NONCONST_DEPTH(24)) uIp0 (
    .ipDataIf (out0),
    .regs (apbReg_uIp0),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(70), .IP_MEM_DEPTH(8), .IP_NONCONST_DEPTH(12)) uIp1 (
    .ipDataIf (out1),
    .regs (apbReg_uIp1),
    .clk (clk),
    .rst_n (rst_n)
);

ipBridge uBridge (
    .data8In (out2),
    .data70In (out3),
    .apbReg (apbReg_uBridge),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ip_test_ip_top
