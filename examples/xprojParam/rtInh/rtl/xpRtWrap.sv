//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpRtWrap
module xpRtWrap
// Generated Import package statement(s)
import xpRtInh_package::*;
import shared_types_package::*;
#(
    parameter int unsigned RT_WIDTH = 32'h0000_0008
)
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[RT_WIDTH-1:0] cfgDataT; //xpRtLeaf configuration payload
    typedef struct packed {
        cfgDataT value; //xpRtLeaf configuration value
    } cfgSt;

    // Interface Instances, needed for between instanced modules inside this module
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uLeaf();

// Instances
xpRtNestDecode #(.RT_WIDTH(RT_WIDTH)) uNestDecode (
    .apbReg (apbReg),
    .apbReg_uLeaf (apbReg_uLeaf),
    .clk (clk),
    .rst_n (rst_n)
);

xpRtLeaf #(.RT_WIDTH(RT_WIDTH)) uLeaf (
    .apbReg (apbReg_uLeaf),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: xpRtWrap
