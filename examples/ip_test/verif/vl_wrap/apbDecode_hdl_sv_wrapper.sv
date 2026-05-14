`ifndef _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module apbDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_top_package::*;
(
    // apb_if.src
    output bit [31:0] apb_uIp0_paddr,
    output bit apb_uIp0_psel,
    output bit apb_uIp0_penable,
    output bit apb_uIp0_pwrite,
    output bit [31:0] apb_uIp0_pwdata,
    input bit apb_uIp0_pready,
    input bit [31:0] apb_uIp0_prdata,
    input bit apb_uIp0_pslverr,

    // apb_if.src
    output bit [31:0] apb_uIp1_paddr,
    output bit apb_uIp1_psel,
    output bit apb_uIp1_penable,
    output bit apb_uIp1_pwrite,
    output bit [31:0] apb_uIp1_pwdata,
    input bit apb_uIp1_pready,
    input bit [31:0] apb_uIp1_prdata,
    input bit apb_uIp1_pslverr,

    // apb_if.src
    output bit [31:0] apb_uBridge_paddr,
    output bit apb_uBridge_psel,
    output bit apb_uBridge_penable,
    output bit apb_uBridge_pwrite,
    output bit [31:0] apb_uBridge_pwdata,
    input bit apb_uBridge_pready,
    input bit [31:0] apb_uBridge_prdata,
    input bit apb_uBridge_pslverr,

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
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uIp0();

    assign #0 apb_uIp0_paddr = apb_uIp0.paddr;
    assign #0 apb_uIp0_psel = apb_uIp0.psel;
    assign #0 apb_uIp0_penable = apb_uIp0.penable;
    assign #0 apb_uIp0_pwrite = apb_uIp0.pwrite;
    assign #0 apb_uIp0_pwdata = apb_uIp0.pwdata;
    assign #0 apb_uIp0.pready = apb_uIp0_pready;
    assign #0 apb_uIp0.prdata = apb_uIp0_prdata;
    assign #0 apb_uIp0.pslverr = apb_uIp0_pslverr;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uIp1();

    assign #0 apb_uIp1_paddr = apb_uIp1.paddr;
    assign #0 apb_uIp1_psel = apb_uIp1.psel;
    assign #0 apb_uIp1_penable = apb_uIp1.penable;
    assign #0 apb_uIp1_pwrite = apb_uIp1.pwrite;
    assign #0 apb_uIp1_pwdata = apb_uIp1.pwdata;
    assign #0 apb_uIp1.pready = apb_uIp1_pready;
    assign #0 apb_uIp1.prdata = apb_uIp1_prdata;
    assign #0 apb_uIp1.pslverr = apb_uIp1_pslverr;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBridge();

    assign #0 apb_uBridge_paddr = apb_uBridge.paddr;
    assign #0 apb_uBridge_psel = apb_uBridge.psel;
    assign #0 apb_uBridge_penable = apb_uBridge.penable;
    assign #0 apb_uBridge_pwrite = apb_uBridge.pwrite;
    assign #0 apb_uBridge_pwdata = apb_uBridge.pwdata;
    assign #0 apb_uBridge.pready = apb_uBridge_pready;
    assign #0 apb_uBridge.prdata = apb_uBridge_prdata;
    assign #0 apb_uBridge.pslverr = apb_uBridge_pslverr;

    // apb_if.dst
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) cpu_main();

    assign #0 cpu_main.paddr = cpu_main_paddr;
    assign #0 cpu_main.psel = cpu_main_psel;
    assign #0 cpu_main.penable = cpu_main_penable;
    assign #0 cpu_main.pwrite = cpu_main_pwrite;
    assign #0 cpu_main.pwdata = cpu_main_pwdata;
    assign #0 cpu_main_pready = cpu_main.pready;
    assign #0 cpu_main_prdata = cpu_main.prdata;
    assign #0 cpu_main_pslverr = cpu_main.pslverr;

    apbDecode dut (
        .apb_uIp0(apb_uIp0), // apb_if.src
        .apb_uIp1(apb_uIp1), // apb_if.src
        .apb_uBridge(apb_uBridge), // apb_if.src
        .cpu_main(cpu_main), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : apbDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_
