`ifndef _CLKGEN_HDL_SV_WRAPPER_SV_GUARD_
`define _CLKGEN_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=clkGen
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module clkGen_hdl_sv_wrapper

(
    input clkRef,
    output clkDiv,
    input rstRef_n
);
    clkGen dut (
        .clkRef(clkRef),
        .clkDiv(clkDiv),
        .rstRef_n(rstRef_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : clkGen_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CLKGEN_HDL_SV_WRAPPER_SV_GUARD_
