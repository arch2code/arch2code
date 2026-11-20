//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmReuseLeaf
module uvmReuseLeaf
// Generated Import package statement(s)
import uvmReuseLeaf_package::*;
#(
    parameter int unsigned UVM_REUSE_OFF_W = 32'h0000_0004
)
(
    rdy_vld_if.dst in,
    rdy_vld_if.src out,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[UVM_REUSE_OFF_W-1:0] uvmReuseOffT; //Offset added to each word
    typedef struct packed {
        uvmReuseOffT offset; //Added to each word
    } uvmReuseOffSt;

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(uvmReuseOffSt)) offset();

// Instances
uvmReuseLeaf_regs #(.UVM_REUSE_OFF_W(UVM_REUSE_OFF_W)) u_uvmReuseLeaf_regs (
    .apbReg (apbReg),
    .offset (offset),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

    assign out.vld = in.vld;
    assign in.rdy = out.rdy;
    always_comb begin
        out.data = in.data;
        out.data.word = in.data.word + uvmReuseWordT'(offset.data.offset);
    end

endmodule: uvmReuseLeaf
