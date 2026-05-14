`ifndef _BRIDGEAPBDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _BRIDGEAPBDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module bridgeApbDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_top_package::*;
(
    // apb_if.src
    output bit [31:0] apb_uBridgeIp0_paddr,
    output bit apb_uBridgeIp0_psel,
    output bit apb_uBridgeIp0_penable,
    output bit apb_uBridgeIp0_pwrite,
    output bit [31:0] apb_uBridgeIp0_pwdata,
    input bit apb_uBridgeIp0_pready,
    input bit [31:0] apb_uBridgeIp0_prdata,
    input bit apb_uBridgeIp0_pslverr,

    // apb_if.src
    output bit [31:0] apb_uBridgeIp1_paddr,
    output bit apb_uBridgeIp1_psel,
    output bit apb_uBridgeIp1_penable,
    output bit apb_uBridgeIp1_pwrite,
    output bit [31:0] apb_uBridgeIp1_pwdata,
    input bit apb_uBridgeIp1_pready,
    input bit [31:0] apb_uBridgeIp1_prdata,
    input bit apb_uBridgeIp1_pslverr,

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
    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBridgeIp0();

    assign #0 apb_uBridgeIp0_paddr = apb_uBridgeIp0.paddr;
    assign #0 apb_uBridgeIp0_psel = apb_uBridgeIp0.psel;
    assign #0 apb_uBridgeIp0_penable = apb_uBridgeIp0.penable;
    assign #0 apb_uBridgeIp0_pwrite = apb_uBridgeIp0.pwrite;
    assign #0 apb_uBridgeIp0_pwdata = apb_uBridgeIp0.pwdata;
    assign #0 apb_uBridgeIp0.pready = apb_uBridgeIp0_pready;
    assign #0 apb_uBridgeIp0.prdata = apb_uBridgeIp0_prdata;
    assign #0 apb_uBridgeIp0.pslverr = apb_uBridgeIp0_pslverr;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBridgeIp1();

    assign #0 apb_uBridgeIp1_paddr = apb_uBridgeIp1.paddr;
    assign #0 apb_uBridgeIp1_psel = apb_uBridgeIp1.psel;
    assign #0 apb_uBridgeIp1_penable = apb_uBridgeIp1.penable;
    assign #0 apb_uBridgeIp1_pwrite = apb_uBridgeIp1.pwrite;
    assign #0 apb_uBridgeIp1_pwdata = apb_uBridgeIp1.pwdata;
    assign #0 apb_uBridgeIp1.pready = apb_uBridgeIp1_pready;
    assign #0 apb_uBridgeIp1.prdata = apb_uBridgeIp1_prdata;
    assign #0 apb_uBridgeIp1.pslverr = apb_uBridgeIp1_pslverr;

    // apb_if.dst
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg();

    assign #0 apbReg.paddr = apbReg_paddr;
    assign #0 apbReg.psel = apbReg_psel;
    assign #0 apbReg.penable = apbReg_penable;
    assign #0 apbReg.pwrite = apbReg_pwrite;
    assign #0 apbReg.pwdata = apbReg_pwdata;
    assign #0 apbReg_pready = apbReg.pready;
    assign #0 apbReg_prdata = apbReg.prdata;
    assign #0 apbReg_pslverr = apbReg.pslverr;

    bridgeApbDecode dut (
        .apb_uBridgeIp0(apb_uBridgeIp0), // apb_if.src
        .apb_uBridgeIp1(apb_uBridgeIp1), // apb_if.src
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : bridgeApbDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BRIDGEAPBDECODE_HDL_SV_WRAPPER_SV_GUARD_
