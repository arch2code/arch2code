`ifndef _XPRTNESTDECODE_HDL_SV_WRAPPER_SVH_GUARD_
`define _XPRTNESTDECODE_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=xpRtNestDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

`include "hdlBoundary.svh"

module xpRtNestDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import xpRtInh_package::*;
    import shared_types_package::*;
#(
    parameter RT_WIDTH
) (
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
    typedef logic[RT_WIDTH-1:0] cfgDataT; //xpRtLeaf configuration payload
    typedef struct packed {
        cfgDataT value; //xpRtLeaf configuration value
    } cfgSt;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uLeaf();

    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf_paddr = apbReg_uLeaf.paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf_psel = apbReg_uLeaf.psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf_penable = apbReg_uLeaf.penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf_pwrite = apbReg_uLeaf.pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf_pwdata = apbReg_uLeaf.pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf.pready = apbReg_uLeaf_pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf.prdata = apbReg_uLeaf_prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uLeaf.pslverr = apbReg_uLeaf_pslverr;

    // apb_if.dst
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg();

    assign `A2C_HDL_BOUNDARY_DLY apbReg.paddr = apbReg_paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.psel = apbReg_psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.penable = apbReg_penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwrite = apbReg_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg.pwdata = apbReg_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pready = apbReg.pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_prdata = apbReg.prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_pslverr = apbReg.pslverr;

    xpRtNestDecode #(.RT_WIDTH(RT_WIDTH)) dut (
        .apbReg_uLeaf(apbReg_uLeaf), // apb_if.src
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    apb_xcheck apbReg_uLeaf_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg_uLeaf));
    apb_xcheck apbReg_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg));
    `endif

endmodule : xpRtNestDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _XPRTNESTDECODE_HDL_SV_WRAPPER_SVH_GUARD_
