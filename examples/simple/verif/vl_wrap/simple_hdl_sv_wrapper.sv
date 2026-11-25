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

    `ifdef VCS_DEBUG
    // Module scope, so %m names this module and not the initial block.
    string a2c_waves_scope;
    initial if ($test$plusargs("fsdbTrace")) begin
        if (!$value$plusargs("a2c_waves_scope=%s", a2c_waves_scope)) a2c_waves_scope = $sformatf("%m");
        $fsdbDumpvars(0, "instance=", a2c_waves_scope, "+all");
    end
    `endif

endmodule : simple_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SIMPLE_HDL_SV_WRAPPER_SV_GUARD_
