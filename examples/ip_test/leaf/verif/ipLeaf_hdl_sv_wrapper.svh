`ifndef _IPLEAF_HDL_SV_WRAPPER_SVH_GUARD_
`define _IPLEAF_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

module ipLeaf_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_test_ipLeaf_package::*;
#(
    parameter LEAF_DATA_WIDTH,
    parameter LEAF_MEM_DEPTH
) (
    input clk,
    input rst_n
);
    typedef logic[$clog2(LEAF_MEM_DEPTH)-1:0] ipLeafMemAddrT; //Index into ipLeaf's private memory (0..LEAF_MEM_DEPTH-1)
    typedef logic[LEAF_DATA_WIDTH-1:0] ipLeafDataT; //ipLeaf data word, parameterizable
    typedef struct packed {
        ipLeafDataT data; //Leaf memory word
    } ipLeafMemSt;
    typedef struct packed {
        ipLeafMemAddrT address; //Leaf memory address
    } ipLeafMemAddrSt;

    ip_test_ipLeaf #(.LEAF_DATA_WIDTH(LEAF_DATA_WIDTH), .LEAF_MEM_DEPTH(LEAF_MEM_DEPTH)) dut (
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ipLeaf_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IPLEAF_HDL_SV_WRAPPER_SVH_GUARD_
