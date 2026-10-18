`ifndef _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

`include "hdlBoundary.svh"

module apbDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import shared_types_package::*;
(
    // apb_if.src
    output bit [31:0] apbReg_uBridge_paddr,
    output bit apbReg_uBridge_psel,
    output bit apbReg_uBridge_penable,
    output bit apbReg_uBridge_pwrite,
    output bit [31:0] apbReg_uBridge_pwdata,
    input bit apbReg_uBridge_pready,
    input bit [31:0] apbReg_uBridge_prdata,
    input bit apbReg_uBridge_pslverr,

    // apb_if.src
    output bit [31:0] apbReg_uIp0_paddr,
    output bit apbReg_uIp0_psel,
    output bit apbReg_uIp0_penable,
    output bit apbReg_uIp0_pwrite,
    output bit [31:0] apbReg_uIp0_pwdata,
    input bit apbReg_uIp0_pready,
    input bit [31:0] apbReg_uIp0_prdata,
    input bit apbReg_uIp0_pslverr,

    // apb_if.src
    output bit [31:0] apbReg_uIp1_paddr,
    output bit apbReg_uIp1_psel,
    output bit apbReg_uIp1_penable,
    output bit apbReg_uIp1_pwrite,
    output bit [31:0] apbReg_uIp1_pwdata,
    input bit apbReg_uIp1_pready,
    input bit [31:0] apbReg_uIp1_prdata,
    input bit apbReg_uIp1_pslverr,

    // apb_if.dst
    input bit [31:0] cpu_main_paddr,
    input bit cpu_main_psel,
    input bit cpu_main_penable,
    input bit cpu_main_pwrite,
    input bit [31:0] cpu_main_pwdata,
    output bit cpu_main_pready,
    output bit [31:0] cpu_main_prdata,
    output bit cpu_main_pslverr,

    input clk,
    input rst_n
);
    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uBridge();

    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge_paddr = apbReg_uBridge.paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge_psel = apbReg_uBridge.psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge_penable = apbReg_uBridge.penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge_pwrite = apbReg_uBridge.pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge_pwdata = apbReg_uBridge.pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge.pready = apbReg_uBridge_pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge.prdata = apbReg_uBridge_prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uBridge.pslverr = apbReg_uBridge_pslverr;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uIp0();

    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0_paddr = apbReg_uIp0.paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0_psel = apbReg_uIp0.psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0_penable = apbReg_uIp0.penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0_pwrite = apbReg_uIp0.pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0_pwdata = apbReg_uIp0.pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0.pready = apbReg_uIp0_pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0.prdata = apbReg_uIp0_prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp0.pslverr = apbReg_uIp0_pslverr;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uIp1();

    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1_paddr = apbReg_uIp1.paddr;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1_psel = apbReg_uIp1.psel;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1_penable = apbReg_uIp1.penable;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1_pwrite = apbReg_uIp1.pwrite;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1_pwdata = apbReg_uIp1.pwdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1.pready = apbReg_uIp1_pready;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1.prdata = apbReg_uIp1_prdata;
    assign `A2C_HDL_BOUNDARY_DLY apbReg_uIp1.pslverr = apbReg_uIp1_pslverr;

    // apb_if.dst
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) cpu_main();

    assign `A2C_HDL_BOUNDARY_DLY cpu_main.paddr = cpu_main_paddr;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main.psel = cpu_main_psel;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main.penable = cpu_main_penable;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main.pwrite = cpu_main_pwrite;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main.pwdata = cpu_main_pwdata;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main_pready = cpu_main.pready;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main_prdata = cpu_main.prdata;
    assign `A2C_HDL_BOUNDARY_DLY cpu_main_pslverr = cpu_main.pslverr;

    apbDecode dut (
        .apbReg_uBridge(apbReg_uBridge), // apb_if.src
        .apbReg_uIp0(apbReg_uIp0), // apb_if.src
        .apbReg_uIp1(apbReg_uIp1), // apb_if.src
        .cpu_main(cpu_main), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS_DEBUG
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

    `ifndef VERILATOR
    apb_xcheck apbReg_uBridge_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg_uBridge));
    apb_xcheck apbReg_uIp0_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg_uIp0));
    apb_xcheck apbReg_uIp1_xcheck (.clk(clk), .rst_n(rst_n), .intf(apbReg_uIp1));
    apb_xcheck cpu_main_xcheck (.clk(clk), .rst_n(rst_n), .intf(cpu_main));
    `endif

endmodule : apbDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_
