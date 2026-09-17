`ifndef _CLKCONSUMER_HDL_SV_WRAPPER_SV_GUARD_
`define _CLKCONSUMER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=clkConsumer
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module clkConsumer_hdl_sv_wrapper

(
    input clk,
    input rst_n
);
    clkGen_clkConsumer dut (
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : clkConsumer_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _CLKCONSUMER_HDL_SV_WRAPPER_SV_GUARD_
