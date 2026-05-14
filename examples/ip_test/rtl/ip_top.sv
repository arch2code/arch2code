//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ip_top
module ip_top
// Generated Import package statement(s)
import ip_package::*;
import ipBridge_package::*;
import src_package::*;
import ip_top_package::*;
(
    apb_if.dst cpu_main,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(srcOut0St)) out0();
    push_ack_if #(.data_t(srcOut1St)) out1();
    push_ack_if #(.data_t(data8St)) out8();
    push_ack_if #(.data_t(data70St)) out70();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uIp0();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uIp1();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBridge();

// Instances
apbDecode uAPBDecode (
    .cpu_main (cpu_main),
    .apb_uIp0 (apb_uIp0),
    .apb_uIp1 (apb_uIp1),
    .apb_uBridge (apb_uBridge),
    .clk (clk),
    .rst_n (rst_n)
);

src #(.OUT0_DATA_WIDTH(8), .OUT1_DATA_WIDTH(70)) uSrc (
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

ip #(.IP_DATA_WIDTH(70), .IP_MEM_DEPTH(8), .IP_NONCONST_DEPTH(12)) uIp1 (
    .ipDataIf (out1),
    .apbReg (apb_uIp1),
    .clk (clk),
    .rst_n (rst_n)
);

bridgeDriver uBridgeDriver (
    .out8 (out8),
    .out70 (out70),
    .clk (clk),
    .rst_n (rst_n)
);

ipBridge uBridge (
    .data8In (out8),
    .data70In (out70),
    .apbReg (apb_uBridge),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ip_top
