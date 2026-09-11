`ifndef _XPRTLEAF_HDL_SV_WRAPPER_SVH_GUARD_
`define _XPRTLEAF_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=xpRtLeaf
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

module xpRtLeaf_hdl_sv_wrapper
    // Generated Import package statement(s)
    import common_shared_types_package::*;
    import xpRtInh_package::*;
#(
    parameter RT_WIDTH
) (
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

    xpRtInh_xpRtLeaf #(.RT_WIDTH(RT_WIDTH)) dut (
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : xpRtLeaf_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _XPRTLEAF_HDL_SV_WRAPPER_SVH_GUARD_
