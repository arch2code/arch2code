//

// GENERATED_CODE_PARAM --block=vltSrc
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: vltSrc
module vltSrc
// Generated Import package statement(s)
import vlt_package::*;
(
    push_ack_if.src out,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // The start-up delay ends at 2ns, before the first clock edge at 5ns, so no
    // input clock edge arrives while it is pending. The stamp is the time it
    // ended, in picoseconds.
    vltStampT stamp;
    logic     started;

    initial begin
        stamp   = '0;
        started = 1'b0;
        #(VLT_START_DELAY_PS * 1ps);
        stamp   = vltStampT'($time);
        started = 1'b1;
    end

    `DFFR_INST(logic, push, 1'b0)
    `DFFR_INST(logic, sent, 1'b0)

    // One push once the delay has ended, held until the checker acks it.
    always_comb begin
        n_push = push;
        n_sent = sent;
        if (push && out.ack) begin
            n_push = 1'b0;
            n_sent = 1'b1;
        end else if (started && !sent) begin
            n_push = 1'b1;
        end
    end

    // The data output is combinational, so the stamp reaches SystemC only if
    // the wrapper passes a combinational update through under --timing.
    assign out.push = push;
    assign out.data = vltSt'(stamp);

endmodule: vltSrc
