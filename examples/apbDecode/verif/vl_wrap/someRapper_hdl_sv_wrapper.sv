`ifndef _SOMERAPPER_HDL_SV_WRAPPER_SV_GUARD_
`define _SOMERAPPER_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module someRapper_hdl_sv_wrapper
    // Generated Import package statement(s)
    import apbDecode_package::*;
(
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

    someRapper dut (
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : someRapper_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _SOMERAPPER_HDL_SV_WRAPPER_SV_GUARD_
