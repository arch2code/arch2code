`ifndef _IPBRIDGE_HDL_SV_WRAPPER_SV_GUARD_
`define _IPBRIDGE_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module ipBridge_hdl_sv_wrapper
    // Generated Import package statement(s)
    import ip_package::*;
    import ip_top_package::*;
    import ipBridge_package::*;
(
    // push_ack_if.dst
    input bit data8In_push,
    input bit [8:0] data8In_data,
    output bit data8In_ack,

    // push_ack_if.dst
    input bit data70In_push,
    input bit [70:0] data70In_data,
    output bit data70In_ack,

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
    // push_ack_if.dst
    push_ack_if #(.data_t(data8St)) data8In();

    assign #0 data8In.push = data8In_push;
    assign #0 data8In.data = data8In_data;
    assign #0 data8In_ack = data8In.ack;

    // push_ack_if.dst
    push_ack_if #(.data_t(data70St)) data70In();

    assign #0 data70In.push = data70In_push;
    assign #0 data70In.data = data70In_data;
    assign #0 data70In_ack = data70In.ack;

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

    ipBridge dut (
        .data8In(data8In), // push_ack_if.dst
        .data70In(data70In), // push_ack_if.dst
        .apbReg(apbReg), // apb_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : ipBridge_hdl_sv_wrapper

// GENERATED_CODE_END

`endif // _IPBRIDGE_HDL_SV_WRAPPER_SV_GUARD_
