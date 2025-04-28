`ifndef _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_
`define _APBDECODE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module apbDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import apbDecode_package::*;
(
    // apb_if.src
    output bit [31:0] apb_uBlockA_paddr,
    output bit apb_uBlockA_psel,
    output bit apb_uBlockA_penable,
    output bit apb_uBlockA_pwrite,
    output bit [31:0] apb_uBlockA_pwdata,
    input bit apb_uBlockA_pready,
    input bit [31:0] apb_uBlockA_prdata,
    input bit apb_uBlockA_pslverr,

    // apb_if.src
    output bit [31:0] apb_uBlockB_paddr,
    output bit apb_uBlockB_psel,
    output bit apb_uBlockB_penable,
    output bit apb_uBlockB_pwrite,
    output bit [31:0] apb_uBlockB_pwdata,
    input bit apb_uBlockB_pready,
    input bit [31:0] apb_uBlockB_prdata,
    input bit apb_uBlockB_pslverr,

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
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBlockA();

    assign #0 apb_uBlockA_paddr = apb_uBlockA.paddr;
    assign #0 apb_uBlockA_psel = apb_uBlockA.psel;
    assign #0 apb_uBlockA_penable = apb_uBlockA.penable;
    assign #0 apb_uBlockA_pwrite = apb_uBlockA.pwrite;
    assign #0 apb_uBlockA_pwdata = apb_uBlockA.pwdata;
    assign #0 apb_uBlockA.pready = apb_uBlockA_pready;
    assign #0 apb_uBlockA.prdata = apb_uBlockA_prdata;
    assign #0 apb_uBlockA.pslverr = apb_uBlockA_pslverr;

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apb_uBlockB();

    assign #0 apb_uBlockB_paddr = apb_uBlockB.paddr;
    assign #0 apb_uBlockB_psel = apb_uBlockB.psel;
    assign #0 apb_uBlockB_penable = apb_uBlockB.penable;
    assign #0 apb_uBlockB_pwrite = apb_uBlockB.pwrite;
    assign #0 apb_uBlockB_pwdata = apb_uBlockB.pwdata;
    assign #0 apb_uBlockB.pready = apb_uBlockB_pready;
    assign #0 apb_uBlockB.prdata = apb_uBlockB_prdata;
    assign #0 apb_uBlockB.pslverr = apb_uBlockB_pslverr;

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

    apbDecode dut (
        .apb_uBlockA(apb_uBlockA), // apb_if.src
        .apb_uBlockB(apb_uBlockB), // apb_if.src
        .apbReg(apbReg), // apb_if.dst
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
