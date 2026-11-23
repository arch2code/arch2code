`ifndef _AXIDEMO_HDL_SV_WRAPPER_SV_GUARD_
`define _AXIDEMO_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module axiDemo_hdl_sv_wrapper
    // Generated Import package statement(s)
    import axiDemo_package::*;
(
    input clk,
    input rst_n
);
    axiDemo dut (
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

endmodule : axiDemo_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _AXIDEMO_HDL_SV_WRAPPER_SV_GUARD_
