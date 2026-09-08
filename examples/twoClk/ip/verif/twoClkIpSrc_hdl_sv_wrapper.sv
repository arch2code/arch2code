`ifndef _TWOCLKIPSRC_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLKIPSRC_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClkIpSrc
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

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

    assign #0 out_push = out.push;
    assign #0 out_data = out.data;
    assign #0 out.ack = out_ack;

    twoClkIp_twoClkIpSrc dut (
        .out(out), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClkIpSrc_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLKIPSRC_HDL_SV_WRAPPER_SV_GUARD_
