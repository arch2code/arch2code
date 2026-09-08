`ifndef _TWOCLKSLOWTICK_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLKSLOWTICK_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClkSlowTick
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module twoClkSlowTick_hdl_sv_wrapper

(
    input clkSlow,
    input rstSlow_n
);
    twoClk_twoClkSlowTick dut (
        .clkSlow(clkSlow),
        .rstSlow_n(rstSlow_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClkSlowTick_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLKSLOWTICK_HDL_SV_WRAPPER_SV_GUARD_
