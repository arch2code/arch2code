`ifndef _BRIDGEDRIVER_HDL_SV_WRAPPER_SV_GUARD_
`define _BRIDGEDRIVER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module bridgeDriver_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ipBridge_package::*;
(
    // push_ack_if.src
    output bit out8_push,
    output bit [8:0] out8_data,
    input bit out8_ack,

    // push_ack_if.src
    output bit out70_push,
    output bit [70:0] out70_data,
    input bit out70_ack,

    input clk,
    input rst_n
);
    // push_ack_if.src
    push_ack_if #(.data_t(data8St)) out8();

    assign #0 out8_push = out8.push;
    assign #0 out8_data = out8.data;
    assign #0 out8.ack = out8_ack;

    // push_ack_if.src
    push_ack_if #(.data_t(data70St)) out70();

    assign #0 out70_push = out70.push;
    assign #0 out70_data = out70.data;
    assign #0 out70.ack = out70_ack;

    bridgeDriver dut (
        .out8(out8), // push_ack_if.src
        .out70(out70), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : bridgeDriver_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BRIDGEDRIVER_HDL_SV_WRAPPER_SV_GUARD_
