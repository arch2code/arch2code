`ifndef _SIMPLE_HDL_SV_WRAPPER_SV_GUARD_
`define _SIMPLE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module simple_hdl_sv_wrapper
    // Generated Import package statement(s)
    import simple_package::*;
(
    input clk,
    input rst_n
);
    simple dut (
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : simple_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SIMPLE_HDL_SV_WRAPPER_SV_GUARD_
