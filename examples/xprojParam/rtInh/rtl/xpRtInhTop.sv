//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpRtInh_xpRtInhTop
module xpRtInh_xpRtInhTop
// Generated Import package statement(s)
import xpRtInh_package::*;
import common_shared_types_package::*;
(
    apb_if.dst cpu_main,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uWrap();

// Instances
xpRtInh_xpRtPrimeDecode uPrimeDecode (
    .cpu_main (cpu_main),
    .apbReg_uWrap (apbReg_uWrap),
    .clk (clk),
    .rst_n (rst_n)
);

xpRtInh_xpRtWrap #(.RT_WIDTH(32)) uWrap (
    .apbReg (apbReg_uWrap),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: xpRtInh_xpRtInhTop
