//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseTock
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmReuseTock
module uvmReuseTock
// Generated Import package statement(s)
import uvmReuse_package::*;
(
    push_ack_if.dst in,
    input clkTock, rstTock_n
);

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkTock;
    wire rst_n = rstTock_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    assign in.ack = in.push;

endmodule: uvmReuseTock
