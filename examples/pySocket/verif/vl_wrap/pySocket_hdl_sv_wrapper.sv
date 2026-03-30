`ifndef _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_
`define _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module pySocket_hdl_sv_wrapper

(
    input clk,
    input rst_n
);
    pySocket dut (
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : pySocket_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _PYSOCKET_HDL_SV_WRAPPER_SV_GUARD_
