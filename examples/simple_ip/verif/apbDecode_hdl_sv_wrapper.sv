`ifndef _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module apbDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import common_shared_types_package::*;
(
    // apb_if.src
    output bit [31:0] apbReg_uIp_paddr,
    output bit apbReg_uIp_psel,
    output bit apbReg_uIp_penable,
    output bit apbReg_uIp_pwrite,
    output bit [31:0] apbReg_uIp_pwdata,
    input bit apbReg_uIp_pready,
    input bit [31:0] apbReg_uIp_prdata,
    input bit apbReg_uIp_pslverr,

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
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uIp();

    assign #0 apbReg_uIp_paddr = apbReg_uIp.paddr;
    assign #0 apbReg_uIp_psel = apbReg_uIp.psel;
    assign #0 apbReg_uIp_penable = apbReg_uIp.penable;
    assign #0 apbReg_uIp_pwrite = apbReg_uIp.pwrite;
    assign #0 apbReg_uIp_pwdata = apbReg_uIp.pwdata;
    assign #0 apbReg_uIp.pready = apbReg_uIp_pready;
    assign #0 apbReg_uIp.prdata = apbReg_uIp_prdata;
    assign #0 apbReg_uIp.pslverr = apbReg_uIp_pslverr;

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

    simple_ip_apbDecode dut (
        .apbReg_uIp(apbReg_uIp), // apb_if.src
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
