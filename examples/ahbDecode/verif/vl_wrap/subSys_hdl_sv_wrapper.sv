`ifndef _SUBSYS_HDL_SV_WRAPPER_SV_GUARD_
`define _SUBSYS_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=subSys
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module subSys_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ahbDecode_package::*;
(
    // ahb_if.dst
    input bit ahbReg_hsel,
    input bit [31:0] ahbReg_haddr,
    input bit [1:0] ahbReg_htrans,
    input bit ahbReg_hwrite,
    input bit [2:0] ahbReg_hsize,
    input bit [31:0] ahbReg_hwdata,
    input bit ahbReg_hready,
    output bit ahbReg_hreadyout,
    output bit ahbReg_hresp,
    output bit [31:0] ahbReg_hrdata,

    input clk,
    input rst_n
);
    // ahb_if.dst
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg();

    assign `A2C_HDL_BOUNDARY_DLY ahbReg.hsel = ahbReg_hsel;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg.haddr = ahbReg_haddr;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg.htrans = ahbReg_htrans;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg.hwrite = ahbReg_hwrite;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg.hsize = ahbReg_hsize;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg.hwdata = ahbReg_hwdata;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg.hready = ahbReg_hready;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_hreadyout = ahbReg.hreadyout;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_hresp = ahbReg.hresp;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_hrdata = ahbReg.hrdata;

    subSys dut (
        .ahbReg(ahbReg), // ahb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : subSys_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SUBSYS_HDL_SV_WRAPPER_SV_GUARD_
