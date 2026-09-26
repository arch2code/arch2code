//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: ipBridge
module ipBridge
// Generated Import package statement(s)
import ip_package::*;
import shared_types_package::*;
import ipBridge_package::*;
(
    push_ack_if.dst data8In,
    push_ack_if.dst data70In,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBridgeIp0();
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBridgeIp1();

// Instances
bridgeApbDecode uBridgeAPBDecode (
    .apbReg (apbReg),
    .apbReg_uBridgeIp0 (apbReg_uBridgeIp0),
    .apbReg_uBridgeIp1 (apbReg_uBridgeIp1),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(8), .IP_MEM_DEPTH(16), .IP_NONCONST_DEPTH(24)) uBridgeIp0 (
    .ipDataIf (data8In),
    .regs (apbReg_uBridgeIp0),
    .clk (clk),
    .rst_n (rst_n)
);

ip #(.IP_DATA_WIDTH(70), .IP_MEM_DEPTH(8), .IP_NONCONST_DEPTH(12)) uBridgeIp1 (
    .ipDataIf (data70In),
    .regs (apbReg_uBridgeIp1),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: ipBridge
