`ifndef _XPRTNESTDECODE_HDL_SV_WRAPPER_SVH_GUARD_
`define _XPRTNESTDECODE_HDL_SV_WRAPPER_SVH_GUARD_

// GENERATED_CODE_PARAM --block=xpRtNestDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper --section=body

module xpRtNestDecode_hdl_sv_wrapper
    // Generated Import package statement(s)
    import xpRtInh_package::*;
    import common_shared_types_package::*;
#(
    parameter RT_WIDTH
) (
    // apb_if.src
    output bit [31:0] apbReg_uLeaf_paddr,
    output bit apbReg_uLeaf_psel,
    output bit apbReg_uLeaf_penable,
    output bit apbReg_uLeaf_pwrite,
    output bit [31:0] apbReg_uLeaf_pwdata,
    input bit apbReg_uLeaf_pready,
    input bit [31:0] apbReg_uLeaf_prdata,
    input bit apbReg_uLeaf_pslverr,

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

    // apb_if.src
    apb_if #(.addr_t(apbAddrSt), .data_t(apbDataSt)) apbReg_uLeaf();

    assign #0 apbReg_uLeaf_paddr = apbReg_uLeaf.paddr;
    assign #0 apbReg_uLeaf_psel = apbReg_uLeaf.psel;
    assign #0 apbReg_uLeaf_penable = apbReg_uLeaf.penable;
    assign #0 apbReg_uLeaf_pwrite = apbReg_uLeaf.pwrite;
    assign #0 apbReg_uLeaf_pwdata = apbReg_uLeaf.pwdata;
    assign #0 apbReg_uLeaf.pready = apbReg_uLeaf_pready;
    assign #0 apbReg_uLeaf.prdata = apbReg_uLeaf_prdata;
    assign #0 apbReg_uLeaf.pslverr = apbReg_uLeaf_pslverr;

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

    xpRtInh_xpRtNestDecode #(.RT_WIDTH(RT_WIDTH)) dut (
        .apbReg_uLeaf(apbReg_uLeaf), // apb_if.src
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : xpRtNestDecode_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _XPRTNESTDECODE_HDL_SV_WRAPPER_SVH_GUARD_
