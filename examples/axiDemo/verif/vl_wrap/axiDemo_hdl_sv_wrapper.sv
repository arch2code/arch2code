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

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : axiDemo_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _AXIDEMO_HDL_SV_WRAPPER_SV_GUARD_
