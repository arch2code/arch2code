`ifndef _UVMREUSELEAF_HDL_SV_WRAPPER_SVH_GUARD_
`define _UVMREUSELEAF_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=uvmReuseLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

`include "hdlBoundary.svh"

module uvmReuseLeaf_hdl_sv_wrapper
    // Generated Import package statement(s)
    import uvmReuseLeaf_package::*;
#(
    parameter UVM_REUSE_OFF_W
) (
    // rdy_vld_if.dst
    input bit in_vld,
    input bit [18:0] in_data,
    output bit in_rdy,

    // rdy_vld_if.src
    output bit out_vld,
    output bit [18:0] out_data,
    input bit out_rdy,

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
    typedef logic[UVM_REUSE_OFF_W-1:0] uvmReuseOffT; //Offset added to each pixel
    typedef struct packed {
        uvmReuseOffT offset; //Added to each pixel
    } uvmReuseOffSt;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(uvmReuseBeatSt)) in();

    assign `A2C_HDL_BOUNDARY_DLY in.vld = in_vld;
    assign `A2C_HDL_BOUNDARY_DLY in.data = in_data;
    assign `A2C_HDL_BOUNDARY_DLY in_rdy = in.rdy;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(uvmReuseBeatSt)) out();

    assign `A2C_HDL_BOUNDARY_DLY out_vld = out.vld;
    assign `A2C_HDL_BOUNDARY_DLY out_data = out.data;
    assign `A2C_HDL_BOUNDARY_DLY out.rdy = out_rdy;

    // apb_if.dst
    apb_if #(.addr_t(uvmReuseAddrSt), .data_t(uvmReuseDataSt)) apbReg();

    assign `A2C_HDL_BOUNDARY_DLY apbReg.paddr = apbReg_paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.psel = apbReg_psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.penable = apbReg_penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwrite = apbReg_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwdata = apbReg_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pready = apbReg.pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_prdata = apbReg.prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pslverr = apbReg.pslverr;

    uvmReuseLeaf #(.UVM_REUSE_OFF_W(UVM_REUSE_OFF_W)) dut (
        .in(in), // rdy_vld_if.dst
        .out(out), // rdy_vld_if.src
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    // Module scope, so %m names this module and not the initial block.
    string a2c_waves_scope;
    initial if ($test$plusargs("fsdbTrace")) begin
        if (!$value$plusargs("a2c_waves_scope=%s", a2c_waves_scope)) a2c_waves_scope = $sformatf("%m");
        $fsdbDumpvars(0, "instance=", a2c_waves_scope, "+all");
    end
    `endif

    `ifndef VERILATOR
    rdy_vld_xcheck in_xcheck (.clk(clk), .rst_n(rst_n), .intf(in));
    rdy_vld_xcheck out_xcheck (.clk(clk), .rst_n(rst_n), .intf(out));
    apb_xcheck apbReg_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg));
    `endif

endmodule : uvmReuseLeaf_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _UVMREUSELEAF_HDL_SV_WRAPPER_SVH_GUARD_
