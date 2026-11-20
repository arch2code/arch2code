`ifndef _CLKCONSUMER_HDL_SV_WRAPPER_SV_GUARD_
`define _CLKCONSUMER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=clkConsumer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module clkConsumer_hdl_sv_wrapper

(
    input clk,
    input rst_n
);
    clkConsumer dut (
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

endmodule : clkConsumer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CLKCONSUMER_HDL_SV_WRAPPER_SV_GUARD_
