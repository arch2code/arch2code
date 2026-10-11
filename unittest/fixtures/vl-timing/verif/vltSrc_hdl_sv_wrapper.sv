`ifndef _VLTSRC_HDL_SV_WRAPPER_SV_GUARD_
`define _VLTSRC_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=vltSrc
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module vltSrc_hdl_sv_wrapper
    // Generated Import package statement(s)
    import vlt_package::*;
(
    // push_ack_if.src
    output bit out_push,
    output bit [31:0] out_data,
    input bit out_ack,

    input clk,
    input rst_n
);
    // push_ack_if.src
    push_ack_if #(.data_t(vltSt)) out();

    assign #0 out_push = out.push;
    assign #0 out_data = out.data;
    assign #0 out.ack = out_ack;

    vltSrc dut (
        .out(out), // push_ack_if.src
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : vltSrc_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _VLTSRC_HDL_SV_WRAPPER_SV_GUARD_
