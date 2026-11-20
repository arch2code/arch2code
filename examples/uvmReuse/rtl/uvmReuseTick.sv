//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseTick
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmReuseTick
module uvmReuseTick
// Generated Import package statement(s)
import uvmReuse_package::*;
(
    push_ack_if.src out,
    input clkTick, rstTick_n
);

    // Default-domain aliases: the bare flop macros expand to clk / rst_n
    wire clk = clkTick;
    wire rst_n = rstTick_n;

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // A count on every clkTick cycle out of reset, independent of the packet
    // path, so it keeps moving while the packets stall.
    `DFF_INST(uvmReuseCountT, count)

    assign out.push = rst_n;
    assign out.data.count = count;

    always_comb begin
        n_count = count;
        if (out.push && out.ack) n_count = count + 1'b1;
    end

endmodule: uvmReuseTick
