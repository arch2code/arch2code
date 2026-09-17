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
    clkGen_clkDivider dut (
        .clkRef(clkRef),
        .clkDiv(clkDiv),
        .clkDivBy2(clkDivBy2),
        .rstRef_n(rstRef_n),
        .rstDivRaw_n(rstDivRaw_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : clkDivider_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CLKDIVIDER_HDL_SV_WRAPPER_SV_GUARD_
