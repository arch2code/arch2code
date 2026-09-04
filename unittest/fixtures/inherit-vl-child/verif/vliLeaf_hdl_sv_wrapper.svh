`ifndef _VLILEAF_HDL_SV_WRAPPER_SVH_GUARD_
`define _VLILEAF_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=vliLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

module vliLeaf_hdl_sv_wrapper
    // Generated Import package statement(s)
    import vlInh_vliCont_package::*;
#(
    parameter VLI_ALGO,
    parameter VLI_WIDTH
) (
    // push_ack_if.src
    output bit out_push,
    output bit [(8 + VLI_WIDTH + 8 + 8 + 8)-1:0] out_data,
    input bit out_ack,

    // push_ack_if.dst
    input bit in_push,
    input bit [(8 + VLI_WIDTH + 8 + 8 + 8)-1:0] in_data,
    output bit in_ack,

    input clk,
    input rst_n
);
    typedef logic[VLI_WIDTH-1:0] vliPixelT; //Parameterizable pixel word
    typedef struct packed {
        vliTagT tag; //Sample sequence tag
        vliAlgoT algo; //VLI_ALGO the leaf instance resolved
        vliWidT wid; //VLI_WIDTH the leaf instance resolved
        vliPixelT data; //Parameterizable pixel payload
        vliMarkT mark; //Trailing marker
    } vliSt;

    // push_ack_if.src
    push_ack_if #(.data_t(vliSt)) out();

    assign #0 out_push = out.push;
    assign #0 out_data = out.data;
    assign #0 out.ack = out_ack;

    // push_ack_if.dst
    push_ack_if #(.data_t(vliSt)) in();

    assign #0 in.push = in_push;
    assign #0 in.data = in_data;
    assign #0 in_ack = in.ack;

    vlInh_vliLeaf #(.VLI_ALGO(VLI_ALGO), .VLI_WIDTH(VLI_WIDTH)) dut (
        .out(out), // push_ack_if.src
        .in(in), // push_ack_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : vliLeaf_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _VLILEAF_HDL_SV_WRAPPER_SVH_GUARD_
