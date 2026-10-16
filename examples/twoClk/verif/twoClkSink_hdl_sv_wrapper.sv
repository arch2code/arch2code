`ifndef _TWOCLKSINK_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLKSINK_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClkSink
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module twoClkSink_hdl_sv_wrapper
    // Generated Import package statement(s)
    import twoClkIp_package::*;
(
    // push_ack_if.dst
    input bit in_push,
    input bit [7:0] in_data,
    output bit in_ack,

    input clk,
    input rst_n
);
    // push_ack_if.dst
    push_ack_if #(.data_t(twoClkDataSt)) in();

    assign `A2C_HDL_BOUNDARY_DLY in.push = in_push;
    assign `A2C_HDL_BOUNDARY_DLY in.data = in_data;
    assign `A2C_HDL_BOUNDARY_DLY in_ack = in.ack;

    twoClkSink dut (
        .in(in), // push_ack_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClkSink_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLKSINK_HDL_SV_WRAPPER_SV_GUARD_
