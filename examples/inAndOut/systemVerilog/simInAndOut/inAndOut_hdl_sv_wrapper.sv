`ifndef _INANDOUT_HDL_SV_WRAPPER_SV_GUARD_
`define _INANDOUT_HDL_SV_WRAPPER_SV_GUARD_

// GENERATED_CODE_PARAM --block=inAndOut 
// GENERATED_CODE_BEGIN --template=module_hdl_sv_wrapper

module inAndOut_hdl_sv_wrapper
    // Generated Import package statement(s)
    import inAndOut_package::*;(
    // rdy_vld_if.src
    output bit aOut_vld,
    output bit [1:0] aOut_data,
    input bit aOut_rdy,

    // rdy_vld_if.dst
    input bit aIn_vld,
    input bit [1:0] aIn_data,
    output bit aIn_rdy,

    // req_ack_if.src
    output bit bOut_req,
    output bit [4:0] bOut_data,
    input bit bOut_ack,
    input bit bOut_rdata,

    // req_ack_if.dst
    input bit bIn_req,
    input bit [4:0] bIn_data,
    output bit bIn_ack,
    output bit bIn_rdata,

    // pop_ack_if.src
    output bit dOut_pop,
    input bit dOut_ack,
    input bit [6:0] dOut_rdata,

    // pop_ack_if.dst
    input bit dIn_pop,
    output bit dIn_ack,
    output bit [6:0] dIn_rdata,

    input clk,
    input rst_n
);
    // rdy_vld_if.src
    rdy_vld_if #(.data_t(aSt)) aOut();

    assign #0 aOut_vld = aOut.vld;
    assign #0 aOut_data = aOut.data;
    assign #0 aOut.rdy = aOut_rdy;

    // rdy_vld_if.dst
    rdy_vld_if #(.data_t(aSt)) aIn();

    assign #0 aIn.vld = aIn_vld;
    assign #0 aIn.data = aIn_data;
    assign #0 aIn_rdy = aIn.rdy;

    // req_ack_if.src
    req_ack_if #(.data_t(bSt), .rdata_t(bBSt)) bOut();

    assign #0 bOut_req = bOut.req;
    assign #0 bOut_data = bOut.data;
    assign #0 bOut.ack = bOut_ack;
    assign #0 bOut.rdata = bOut_rdata;

    // req_ack_if.dst
    req_ack_if #(.data_t(bSt), .rdata_t(bBSt)) bIn();

    assign #0 bIn.req = bIn_req;
    assign #0 bIn.data = bIn_data;
    assign #0 bIn_ack = bIn.ack;
    assign #0 bIn_rdata = bIn.rdata;

    // pop_ack_if.src
    pop_ack_if #(.rdata_t(dSt)) dOut();

    assign #0 dOut_pop = dOut.pop;
    assign #0 dOut.ack = dOut_ack;
    assign #0 dOut.rdata = dOut_rdata;

    // pop_ack_if.dst
    pop_ack_if #(.rdata_t(dSt)) dIn();

    assign #0 dIn.pop = dIn_pop;
    assign #0 dIn_ack = dIn.ack;
    assign #0 dIn_rdata = dIn.rdata;

    inAndOut dut (
        .aOut(aOut), // rdy_vld_if.src
        .aIn(aIn), // rdy_vld_if.dst
        .bOut(bOut), // req_ack_if.src
        .bIn(bIn), // req_ack_if.dst
        .dOut(dOut), // pop_ack_if.src
        .dIn(dIn), // pop_ack_if.dst
        .clk(clk),
        .rst_n(rst_n)
    );

    `ifdef VCS
    initial if ($test$plusargs("fsdbTrace")) begin
        $fsdbDumpvars($sformatf("%m"), "+all");
    end
    `endif

endmodule : inAndOut_hdl_sv_wrapper

//GENERATED_CODE_END

`endif // _INANDOUT_HDL_SV_WRAPPER_SV_GUARD_
