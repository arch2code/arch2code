//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsScale
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmRegsScale
module uvmRegsScale
// Generated Import package statement(s)
import uvmRegs_package::*;
#(
    parameter int unsigned UVM_REGS_SCALE_W = 32'h0000_0004
)
(
    rdy_vld_if.src out,
    rdy_vld_if.dst in,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Module-local parameterizable type/struct declarations
    typedef logic[UVM_REGS_SCALE_W-1:0] uvmRegsScaleT; //Scale offset
    typedef struct packed {
        uvmRegsScaleT offset; //Added to each word
    } uvmRegsScaleSt;

    // Interface Instances, needed for between instanced modules inside this module
    status_if #(.data_t(uvmRegsScaleSt)) offset();

// Instances
uvmRegsScale_regs #(.UVM_REGS_SCALE_W(UVM_REGS_SCALE_W)) u_uvmRegsScale_regs (
    .apbReg (apbReg),
    .offset (offset),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

    assign out.vld = in.vld;
    assign in.rdy = out.rdy;
    assign out.data.word = in.data.word + uvmRegsWordT'(offset.data.offset);

endmodule: uvmRegsScale
