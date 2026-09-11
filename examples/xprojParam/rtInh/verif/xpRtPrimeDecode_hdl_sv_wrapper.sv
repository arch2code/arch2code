`ifndef _XPRTPRIMEDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _XPRTPRIMEDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=xpRtPrimeDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module xpRtPrimeDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import common_shared_types_package::*;
(
    // apb_if.src
    output bit [31:0] apbReg_uWrap_paddr,
    output bit apbReg_uWrap_psel,
    output bit apbReg_uWrap_penable,
    output bit apbReg_uWrap_pwrite,
    output bit [31:0] apbReg_uWrap_pwdata,
    input bit apbReg_uWrap_pready,
    input bit [31:0] apbReg_uWrap_prdata,
    input bit apbReg_uWrap_pslverr,

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
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uWrap();

    assign #0 apbReg_uWrap_paddr = apbReg_uWrap.paddr;
    assign #0 apbReg_uWrap_psel = apbReg_uWrap.psel;
    assign #0 apbReg_uWrap_penable = apbReg_uWrap.penable;
    assign #0 apbReg_uWrap_pwrite = apbReg_uWrap.pwrite;
    assign #0 apbReg_uWrap_pwdata = apbReg_uWrap.pwdata;
    assign #0 apbReg_uWrap.pready = apbReg_uWrap_pready;
    assign #0 apbReg_uWrap.prdata = apbReg_uWrap_prdata;
    assign #0 apbReg_uWrap.pslverr = apbReg_uWrap_pslverr;

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

    xpRtInh_xpRtPrimeDecode dut (
        .apbReg_uWrap(apbReg_uWrap), // apb_if.src
        .cpu_main(cpu_main), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : xpRtPrimeDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _XPRTPRIMEDECODE_HDL_SV_WRAPPER_SV_GUARD_
