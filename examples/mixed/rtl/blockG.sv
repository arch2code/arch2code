//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockG
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: mixed_blockG
module mixed_blockG
// Generated Import package statement(s)
import mixed_package::*;
#(
    parameter fred
)
(
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(dRegSt)) rwG();

// Instances
mixed_blockGLeaf uBlockGLeaf (
    .rwG (rwG),
    .clk (clk),
    .rst_n (rst_n)
);

mixed_blockGRegs #(.fred(fred)) uBlockGRegs (
    .apbReg (apbReg),
    .rwG (rwG),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: mixed_blockG
