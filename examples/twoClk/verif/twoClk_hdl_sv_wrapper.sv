`ifndef _TWOCLK_HDL_SV_WRAPPER_SV_GUARD_
`define _TWOCLK_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=twoClk
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module twoClk_hdl_sv_wrapper
    // Generated Import package statement(s)
    import twoClkIp_package::*;
(
    input clk,
    input clkSlow,
    input rst_n,
    input rstSlow_n
);
    twoClk dut (
        .clk(clk),
        .clkSlow(clkSlow),
        .rst_n(rst_n),
        .rstSlow_n(rstSlow_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : twoClk_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _TWOCLK_HDL_SV_WRAPPER_SV_GUARD_
