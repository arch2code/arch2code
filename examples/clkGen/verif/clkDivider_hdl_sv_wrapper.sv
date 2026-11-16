`ifndef _CLKDIVIDER_HDL_SV_WRAPPER_SV_GUARD_
`define _CLKDIVIDER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=clkDivider
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module clkDivider_hdl_sv_wrapper

(
    input clkRef,
    output clkDiv,
    output clkDivBy2,
    input rstRef_n,
    output rstDivRaw_n
);
    clkDivider dut (
        .clkRef(clkRef),
        .clkDiv(clkDiv),
        .clkDivBy2(clkDivBy2),
        .rstRef_n(rstRef_n),
        .rstDivRaw_n(rstDivRaw_n)
    );

    `ifdef VCS_DEBUG
    // Module scope, so %m names this module and not the initial block.
    string a2c_waves_scope;
    initial if ($test$plusargs("fsdbTrace")) begin
        if (!$value$plusargs("a2c_waves_scope=%s", a2c_waves_scope)) a2c_waves_scope = $sformatf("%m");
        $fsdbDumpvars(0, "instance=", a2c_waves_scope, "+all");
    end
    `endif

endmodule : clkDivider_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CLKDIVIDER_HDL_SV_WRAPPER_SV_GUARD_
