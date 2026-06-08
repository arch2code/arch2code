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
    localparam LEAF_DATA_WIDTH = 4;
    localparam LEAF_MEM_DEPTH = 4;
    typedef logic[LEAF_DATA_WIDTH-1:0] ipLeafDataT; //ipLeaf data word, parameterizable
    typedef logic[$clog2(LEAF_MEM_DEPTH)-1:0] ipLeafMemAddrT; //Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
    typedef struct packed {
        ipLeafDataT data; //Leaf memory word
    } ipLeafMemSt;
    typedef struct packed {
        ipLeafMemAddrT address; //Leaf memory address
    } ipLeafMemAddrSt;

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
