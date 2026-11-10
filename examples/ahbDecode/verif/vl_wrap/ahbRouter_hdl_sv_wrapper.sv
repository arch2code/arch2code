`ifndef _AHBROUTER_HDL_SV_WRAPPER_SV_GUARD_
`define _AHBROUTER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ahbRouter
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module ahbRouter_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ahbDecode_package::*;
(
    // ahb_if.src
    output bit ahbReg_uLeafA_hsel,
    output bit [31:0] ahbReg_uLeafA_haddr,
    output bit [1:0] ahbReg_uLeafA_htrans,
    output bit ahbReg_uLeafA_hwrite,
    output bit [2:0] ahbReg_uLeafA_hsize,
    output bit [31:0] ahbReg_uLeafA_hwdata,
    output bit ahbReg_uLeafA_hready,
    input bit ahbReg_uLeafA_hreadyout,
    input bit ahbReg_uLeafA_hresp,
    input bit [31:0] ahbReg_uLeafA_hrdata,

    // ahb_if.src
    output bit ahbReg_uLeafB_hsel,
    output bit [31:0] ahbReg_uLeafB_haddr,
    output bit [1:0] ahbReg_uLeafB_htrans,
    output bit ahbReg_uLeafB_hwrite,
    output bit [2:0] ahbReg_uLeafB_hsize,
    output bit [31:0] ahbReg_uLeafB_hwdata,
    output bit ahbReg_uLeafB_hready,
    input bit ahbReg_uLeafB_hreadyout,
    input bit ahbReg_uLeafB_hresp,
    input bit [31:0] ahbReg_uLeafB_hrdata,

    // ahb_if.src
    output bit ahbReg_uSubSys_hsel,
    output bit [31:0] ahbReg_uSubSys_haddr,
    output bit [1:0] ahbReg_uSubSys_htrans,
    output bit ahbReg_uSubSys_hwrite,
    output bit [2:0] ahbReg_uSubSys_hsize,
    output bit [31:0] ahbReg_uSubSys_hwdata,
    output bit ahbReg_uSubSys_hready,
    input bit ahbReg_uSubSys_hreadyout,
    input bit ahbReg_uSubSys_hresp,
    input bit [31:0] ahbReg_uSubSys_hrdata,

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
    // ahb_if.src
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uLeafA();

    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_hsel = ahbReg_uLeafA.hsel;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_haddr = ahbReg_uLeafA.haddr;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_htrans = ahbReg_uLeafA.htrans;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_hwrite = ahbReg_uLeafA.hwrite;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_hsize = ahbReg_uLeafA.hsize;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_hwdata = ahbReg_uLeafA.hwdata;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA_hready = ahbReg_uLeafA.hready;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA.hreadyout = ahbReg_uLeafA_hreadyout;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA.hresp = ahbReg_uLeafA_hresp;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafA.hrdata = ahbReg_uLeafA_hrdata;

    // ahb_if.src
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uLeafB();

    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_hsel = ahbReg_uLeafB.hsel;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_haddr = ahbReg_uLeafB.haddr;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_htrans = ahbReg_uLeafB.htrans;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_hwrite = ahbReg_uLeafB.hwrite;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_hsize = ahbReg_uLeafB.hsize;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_hwdata = ahbReg_uLeafB.hwdata;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB_hready = ahbReg_uLeafB.hready;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB.hreadyout = ahbReg_uLeafB_hreadyout;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB.hresp = ahbReg_uLeafB_hresp;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uLeafB.hrdata = ahbReg_uLeafB_hrdata;

    // ahb_if.src
    ahb_if #(.addr_t(ahbAddrSt), .data_t(ahbDataSt)) ahbReg_uSubSys();

    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_hsel = ahbReg_uSubSys.hsel;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_haddr = ahbReg_uSubSys.haddr;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_htrans = ahbReg_uSubSys.htrans;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_hwrite = ahbReg_uSubSys.hwrite;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_hsize = ahbReg_uSubSys.hsize;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_hwdata = ahbReg_uSubSys.hwdata;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys_hready = ahbReg_uSubSys.hready;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys.hreadyout = ahbReg_uSubSys_hreadyout;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys.hresp = ahbReg_uSubSys_hresp;
    assign `A2C_HDL_BOUNDARY_DLY ahbReg_uSubSys.hrdata = ahbReg_uSubSys_hrdata;

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

    ahbRouter dut (
        .ahbReg_uLeafA(ahbReg_uLeafA), // ahb_if.src
        .ahbReg_uLeafB(ahbReg_uLeafB), // ahb_if.src
        .ahbReg_uSubSys(ahbReg_uSubSys), // ahb_if.src
        .ahbReg(ahbReg), // ahb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ahbRouter_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _AHBROUTER_HDL_SV_WRAPPER_SV_GUARD_
