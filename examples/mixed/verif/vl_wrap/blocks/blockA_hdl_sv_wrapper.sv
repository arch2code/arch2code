`ifndef _BLOCKA_HDL_SV_WRAPPER_SV_GUARD_
`define _BLOCKA_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module blockA_hdl_sv_wrapper
    // Generated Import package statement(s)
    import mixedBlockC_package::*;
    import mixed_package::*;(
    // req_ack_if.src
    output bit aStuffIf_req,
    output bit [3:0] aStuffIf_data,
    input bit aStuffIf_ack,
    input bit aStuffIf_rdata,

    // rdy_vld_if.src
    output bit cStuffIf_vld,
    output bit [4:0] cStuffIf_data,
    input bit cStuffIf_rdy,

    // notify_ack_if.src
    output bit startDone_notify,
    input bit startDone_ack,

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
    // req_ack_if.src
    req_ack_if #(.data_t(aSt), .rdata_t(aASt)) aStuffIf();

    assign #0 aStuffIf_req = aStuffIf.req;
    assign #0 aStuffIf_data = aStuffIf.data;
    assign #0 aStuffIf.ack = aStuffIf_ack;
    assign #0 aStuffIf.rdata = aStuffIf_rdata;

    // rdy_vld_if.src
    rdy_vld_if #(.data_t(seeSt)) cStuffIf();

    assign #0 cStuffIf_vld = cStuffIf.vld;
    assign #0 cStuffIf_data = cStuffIf.data;
    assign #0 cStuffIf.rdy = cStuffIf_rdy;

    // notify_ack_if.src
    notify_ack_if #() startDone();

    assign #0 startDone_notify = startDone.notify;
    assign #0 startDone.ack = startDone_ack;

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

    blockA dut (
        .aStuffIf(aStuffIf), // req_ack_if.src
        .cStuffIf(cStuffIf), // rdy_vld_if.src
        .startDone(startDone), // notify_ack_if.src
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : blockA_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _BLOCKA_HDL_SV_WRAPPER_SV_GUARD_
