`ifndef _IP_VARIANT1_HDL_SV_WRAPPER_SV_GUARD_
`define _IP_VARIANT1_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ip --variant=variant1
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module ip_variant1_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_top_package::*;
    import ip_package::*;
(
    // rdy_vld_if.dst
    input bit ipDataIf_vld,
    input bit [7:0] ipDataIf_data,
    output bit ipDataIf_rdy,

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
    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(ipDataSt)) ipDataIf();

    assign #0 ipDataIf.vld = ipDataIf_vld;
    assign #0 ipDataIf.data = ipDataIf_data;
    assign #0 ipDataIf_rdy = ipDataIf.rdy;

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

    ip #(.IP_DATA_WIDTH(12), .IP_MEM_DEPTH(8)) dut (
        .ipDataIf(ipDataIf), // rdy_vld_if.dst
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ip_variant1_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IP_VARIANT1_HDL_SV_WRAPPER_SV_GUARD_
