//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtLeaf
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xpRtInh_xpRtLeaf
module xpRtInh_xpRtLeaf
// Generated Import package statement(s)
import common_shared_types_package::*;
import xpRtInh_package::*;
#(
    parameter RT_WIDTH
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
    status_if #(.data_t(cfgSt)) cfg();

// Instances
xpRtInh_xpRtLeafRegs #(.RT_WIDTH(RT_WIDTH)) uXpRtLeafRegs (
    .apbReg (apbReg),
    .cfg (cfg),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: xpRtInh_xpRtLeaf
