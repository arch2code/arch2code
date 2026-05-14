`ifndef _IPLEAF_VARIANTLEAF0_HDL_SV_WRAPPER_SV_GUARD_
`define _IPLEAF_VARIANTLEAF0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ipLeaf --variant=variantLeaf0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module ipLeaf_variantLeaf0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ipLeaf_package::*;
(
    input clk,
    input rst_n
);
    ipLeaf #(.LEAF_DATA_WIDTH(4), .LEAF_MEM_DEPTH(4)) dut (
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ipLeaf_variantLeaf0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IPLEAF_VARIANTLEAF0_HDL_SV_WRAPPER_SV_GUARD_
