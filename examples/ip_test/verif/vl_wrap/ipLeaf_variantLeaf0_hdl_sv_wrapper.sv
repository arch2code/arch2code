`ifndef _IPLEAF_VARIANTLEAF0_HDL_SV_WRAPPER_SV_GUARD_
`define _IPLEAF_VARIANTLEAF0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ipLeaf --variant=variantLeaf0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "ipLeaf_hdl_sv_wrapper.svh"

module ipLeaf_variantLeaf0_hdl_sv_wrapper
#(
    localparam LEAF_DATA_WIDTH = 4,
    localparam LEAF_MEM_DEPTH = 4
)(
    input clk,
    input rst_n
);
    ipLeaf_hdl_sv_wrapper #(
        .LEAF_DATA_WIDTH(LEAF_DATA_WIDTH),
        .LEAF_MEM_DEPTH(LEAF_MEM_DEPTH)
    ) u_wrapper (
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : ipLeaf_variantLeaf0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IPLEAF_VARIANTLEAF0_HDL_SV_WRAPPER_SV_GUARD_
