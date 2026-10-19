`ifndef _TWOCLKIPSRC_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLKIPSRC_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClkIpSrc
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module twoClkIpSrc_hdl_sv_wrapper
    // Generated Import package statement(s)
    import twoClkIp_package::*;
(
    // push_ack_if.src
    output bit out_push,
    output bit [7:0] out_data,
    input bit out_ack,

    input clk,
    input rst_n
);
    // push_ack_if.src
    push_ack_if #(.data_t(twoClkDataSt)) out();

    assign `A2C_HDL_BOUNDARY_DLY out_push = out.push;
    assign `A2C_HDL_BOUNDARY_DLY out_data = out.data;
    assign `A2C_HDL_BOUNDARY_DLY out.ack = out_ack;

    twoClkIpSrc dut (
        .out(out), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    push_ack_xcheck out_xcheck (.clk(clk), .rst_n(rst_n), .intf(out));
    `endif

endmodule : twoClkIpSrc_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLKIPSRC_HDL_SV_WRAPPER_SV_GUARD_
