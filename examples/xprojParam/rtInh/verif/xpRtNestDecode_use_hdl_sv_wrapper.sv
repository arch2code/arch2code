`ifndef _XPRTNESTDECODE_USE_HDL_SV_WRAPPER_SV_GUARD_
`define _XPRTNESTDECODE_USE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=xpRtNestDecode --variant=use
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "xpRtNestDecode_hdl_sv_wrapper.svh"

module xpRtNestDecode_use_hdl_sv_wrapper
    // Generated Import package statement(s)
    import xpRtInh_package::*;
    import common_shared_types_package::*;
#(
    localparam RT_WIDTH = 32
)(
    // apb_if.src
    output bit [31:0] apbReg_uLeaf_paddr,
    output bit apbReg_uLeaf_psel,
    output bit apbReg_uLeaf_penable,
    output bit apbReg_uLeaf_pwrite,
    output bit [31:0] apbReg_uLeaf_pwdata,
    input bit apbReg_uLeaf_pready,
    input bit [31:0] apbReg_uLeaf_prdata,
    input bit apbReg_uLeaf_pslverr,

    // apb_if.dst
    input bit [31:0] apbReg_paddr,
    input bit apbReg_psel,
    input bit apbReg_penable,
    input bit apbReg_pwrite,
    input bit [31:0] apbReg_pwdata,
    output bit apbReg_pready,
    output bit [31:0] apbReg_prdata,
    output bit apbReg_pslverr,

    input clk,
    input rst_n
);
    xpRtNestDecode_hdl_sv_wrapper #(
        .RT_WIDTH(RT_WIDTH)
    ) u_wrapper (
        .apbReg_uLeaf_paddr(apbReg_uLeaf_paddr),
        .apbReg_uLeaf_psel(apbReg_uLeaf_psel),
        .apbReg_uLeaf_penable(apbReg_uLeaf_penable),
        .apbReg_uLeaf_pwrite(apbReg_uLeaf_pwrite),
        .apbReg_uLeaf_pwdata(apbReg_uLeaf_pwdata),
        .apbReg_uLeaf_pready(apbReg_uLeaf_pready),
        .apbReg_uLeaf_prdata(apbReg_uLeaf_prdata),
        .apbReg_uLeaf_pslverr(apbReg_uLeaf_pslverr),
        .apbReg_paddr(apbReg_paddr),
        .apbReg_psel(apbReg_psel),
        .apbReg_penable(apbReg_penable),
        .apbReg_pwrite(apbReg_pwrite),
        .apbReg_pwdata(apbReg_pwdata),
        .apbReg_pready(apbReg_pready),
        .apbReg_prdata(apbReg_prdata),
        .apbReg_pslverr(apbReg_pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : xpRtNestDecode_use_hdl_sv_wrapper

`include "xpRtNestDecode_hdl_sv_wrapper.svh"

module p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper
    // Generated Import package statement(s)
    import xpRtInh_package::*;
    import common_shared_types_package::*;
#(
    localparam RT_WIDTH = 32
)(
    // apb_if.src
    output bit [31:0] apbReg_uLeaf_paddr,
    output bit apbReg_uLeaf_psel,
    output bit apbReg_uLeaf_penable,
    output bit apbReg_uLeaf_pwrite,
    output bit [31:0] apbReg_uLeaf_pwdata,
    input bit apbReg_uLeaf_pready,
    input bit [31:0] apbReg_uLeaf_prdata,
    input bit apbReg_uLeaf_pslverr,

    // apb_if.dst
    input bit [31:0] apbReg_paddr,
    input bit apbReg_psel,
    input bit apbReg_penable,
    input bit apbReg_pwrite,
    input bit [31:0] apbReg_pwdata,
    output bit apbReg_pready,
    output bit [31:0] apbReg_prdata,
    output bit apbReg_pslverr,

    input clk,
    input rst_n
);
    xpRtNestDecode_hdl_sv_wrapper #(
        .RT_WIDTH(RT_WIDTH)
    ) u_wrapper (
        .apbReg_uLeaf_paddr(apbReg_uLeaf_paddr),
        .apbReg_uLeaf_psel(apbReg_uLeaf_psel),
        .apbReg_uLeaf_penable(apbReg_uLeaf_penable),
        .apbReg_uLeaf_pwrite(apbReg_uLeaf_pwrite),
        .apbReg_uLeaf_pwdata(apbReg_uLeaf_pwdata),
        .apbReg_uLeaf_pready(apbReg_uLeaf_pready),
        .apbReg_uLeaf_prdata(apbReg_uLeaf_prdata),
        .apbReg_uLeaf_pslverr(apbReg_uLeaf_pslverr),
        .apbReg_paddr(apbReg_paddr),
        .apbReg_psel(apbReg_psel),
        .apbReg_penable(apbReg_penable),
        .apbReg_pwrite(apbReg_pwrite),
        .apbReg_pwdata(apbReg_pwdata),
        .apbReg_pready(apbReg_pready),
        .apbReg_prdata(apbReg_prdata),
        .apbReg_pslverr(apbReg_pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule : p16_xpRtInh_xpRtWrap_c22_xpRtInh_xpRtNestDecode_use_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _XPRTNESTDECODE_USE_HDL_SV_WRAPPER_SV_GUARD_
