`ifndef _RSTSYNC_HDL_SV_WRAPPER_SV_GUARD_
`define _RSTSYNC_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=rstSync
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module rstSync_hdl_sv_wrapper

(
    input clk,
    input rstIn_n,
    output rstOut_n
);
    clkGen_rstSync dut (
        .clk(clk),
        .rstIn_n(rstIn_n),
        .rstOut_n(rstOut_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : rstSync_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _RSTSYNC_HDL_SV_WRAPPER_SV_GUARD_
