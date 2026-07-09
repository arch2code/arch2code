`ifndef _IP_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
`define _IP_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ip --variant=variant0
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "ip_hdl_sv_wrapper.svh"

module ip_variant0_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_package::*;
#(
    localparam IP_DATA_WIDTH = 8,
    localparam IP_MEM_DEPTH = 16,
    localparam IP_NONCONST_DEPTH = 24,
    localparam IP_DATA_WIDTH_X2 = IP_DATA_WIDTH * 2,
    localparam IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2,
    localparam IP_MEM_DEPTH_X2 = IP_MEM_DEPTH * 2,
    localparam IP_MEM_DEPTH_X4 = IP_MEM_DEPTH_X2 * 2
)(
    // push_ack_if.dst
    input bit ipDataIf_push,
    input bit [(IP_DATA_WIDTH + 1)-1:0] ipDataIf_data,
    output bit ipDataIf_ack,

    // apb_if.dst
    input bit [31:0] regs_paddr,
    input bit regs_psel,
    input bit regs_penable,
    input bit regs_pwrite,
    input bit [31:0] regs_pwdata,
    output bit regs_pready,
    output bit [31:0] regs_prdata,
    output bit regs_pslverr,

    input clk,
    input rst_n
);
    ip_hdl_sv_wrapper #(
        .IP_DATA_WIDTH(IP_DATA_WIDTH),
        .IP_MEM_DEPTH(IP_MEM_DEPTH),
        .IP_NONCONST_DEPTH(IP_NONCONST_DEPTH)
    ) u_wrapper (
        .ipDataIf_push(ipDataIf_push),
        .ipDataIf_data(ipDataIf_data),
        .ipDataIf_ack(ipDataIf_ack),
        .regs_paddr(regs_paddr),
        .regs_psel(regs_psel),
        .regs_penable(regs_penable),
        .regs_pwrite(regs_pwrite),
        .regs_pwdata(regs_pwdata),
        .regs_pready(regs_pready),
        .regs_prdata(regs_prdata),
        .regs_pslverr(regs_pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : ip_variant0_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IP_VARIANT0_HDL_SV_WRAPPER_SV_GUARD_
