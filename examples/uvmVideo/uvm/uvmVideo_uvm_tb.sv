// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo
// GENERATED_CODE_BEGIN --template=uvmTb --section=header

`timescale 1ns/1ps

module uvmVideo_uvm_tb
    import uvm_pkg::*;
    import uvmVideo_uvm_test_pkg::*;

// GENERATED_CODE_END

// further package imports here

// GENERATED_CODE_BEGIN --template=uvmTb --section=body

(
    // raw_if.dst on the DUT
    output bit [$bits(uvmVideo_package::uvmVideoRawSt)-1:0] vin_data,

    // axi4_stream_if.src on the DUT
    input  bit vout_tvalid,
    output bit vout_tready,
    input  bit [$bits(uvmVideo_package::uvmVideoBeatSt)-1:0] vout_tdata,
    input  bit [1:0] vout_tstrb,
    input  bit [1:0] vout_tkeep,
    input  bit vout_tlast,
    input  bit vout_tid,
    input  bit vout_tdest,
    input  bit vout_tuser,

    input clk,
    input rst_n,

    // completion, read by the SystemC side
    output bit uvm_done,
    output bit [31:0] uvm_errors,
    output bit rtl_dut,
    output bit model_dut
);

    raw_if #(.data_t(uvmVideo_package::uvmVideoRawSt)) vin();
    axi4_stream_if #(.tdata_t(uvmVideo_package::uvmVideoBeatSt), .tid_t(uvmVideo_package::uvmVideoIdSt), .tdest_t(uvmVideo_package::uvmVideoIdSt), .tuser_t(uvmVideo_package::uvmVideoUserSt)) vout();
    a2c_clk_if clk_if(.clk(clk), .rst_n(rst_n));

`ifdef A2C_UVM_BOTH_DUT
    raw_if #(.data_t(uvmVideo_package::uvmVideoRawSt)) vin_model();
    axi4_stream_if #(.tdata_t(uvmVideo_package::uvmVideoBeatSt), .tid_t(uvmVideo_package::uvmVideoIdSt), .tdest_t(uvmVideo_package::uvmVideoIdSt), .tuser_t(uvmVideo_package::uvmVideoUserSt)) vout_model();

    uvmVideo_hdl_sv_wrapper dut (
        .vin_data(vin.data),
        .vout_tvalid(vout.tvalid),
        .vout_tready(vout.tready),
        .vout_tdata(vout.tdata),
        .vout_tstrb(vout.tstrb),
        .vout_tkeep(vout.tkeep),
        .vout_tlast(vout.tlast),
        .vout_tid(vout.tid),
        .vout_tdest(vout.tdest),
        .vout_tuser(vout.tuser),
        .clk(clk),
        .rst_n(rst_n)
    );

    assign vin_data = vin_model.data;
    assign vout_model.tvalid = vout_tvalid;
    assign vout_tready = vout_model.tready;
    assign vout_model.tdata = vout_tdata;
    assign vout_model.tstrb = vout_tstrb;
    assign vout_model.tkeep = vout_tkeep;
    assign vout_model.tlast = vout_tlast;
    assign vout_model.tid = vout_tid;
    assign vout_model.tdest = vout_tdest;
    assign vout_model.tuser = vout_tuser;
    assign rtl_dut = 1'b1;
    assign model_dut = 1'b1;
`elsif A2C_UVM_RTL_DUT
    uvmVideo_hdl_sv_wrapper dut (
        .vin_data(vin.data),
        .vout_tvalid(vout.tvalid),
        .vout_tready(vout.tready),
        .vout_tdata(vout.tdata),
        .vout_tstrb(vout.tstrb),
        .vout_tkeep(vout.tkeep),
        .vout_tlast(vout.tlast),
        .vout_tid(vout.tid),
        .vout_tdest(vout.tdest),
        .vout_tuser(vout.tuser),
        .clk(clk),
        .rst_n(rst_n)
    );

    assign vin_data = '0;
    assign vout_tready = 1'b0;
    assign rtl_dut = 1'b1;
    assign model_dut = 1'b0;
`else
    assign vin_data = vin.data;
    assign vout.tvalid = vout_tvalid;
    assign vout_tready = vout.tready;
    assign vout.tdata = vout_tdata;
    assign vout.tstrb = vout_tstrb;
    assign vout.tkeep = vout_tkeep;
    assign vout.tlast = vout_tlast;
    assign vout.tid = vout_tid;
    assign vout.tdest = vout_tdest;
    assign vout.tuser = vout_tuser;
    assign rtl_dut = 1'b0;
    assign model_dut = 1'b1;
`endif

    // Each SystemC BFM contract break, such as a model that stalls a
    // backpressure: false producer, becomes an A2C_BFM_CONTRACT UVM_ERROR,
    // which a test can expect with a report catcher (a2c_expected_error).
    // SystemC fails the run on any break still queued when run_test() returns.
    import "DPI-C" function string a2c_bfm_contract_break();
    bit bfm_breaks_open = 1'b1;
    always @(negedge clk) begin
        string bfm_break;
        if (bfm_breaks_open) begin
            for (bfm_break = a2c_bfm_contract_break(); bfm_break != ""; bfm_break = a2c_bfm_contract_break()) begin
                uvm_report_error("A2C_BFM_CONTRACT", bfm_break, UVM_NONE);
            end
        end
    end

    // run_test() returns after the report phase because finish_on_completion
    // is off, and SystemC ends the simulation through its end-of-test vote.
    // A UVM_FATAL calls $finish inside run_test(), so uvm_done stays low and
    // the SystemC side fails the run.
    initial begin
        uvm_report_server srv;
        uvm_done = 1'b0;
        uvm_errors = '0;
        uvm_config_db#(uvmVideo_uvm_pkg::vin_vif_t)::set(null, "uvm_test_top.*", "vin", vin);
        uvm_config_db#(uvmVideo_uvm_pkg::vout_vif_t)::set(null, "uvm_test_top.*", "vout", vout);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top.*", "clk", clk_if);
`ifdef A2C_UVM_BOTH_DUT
        uvm_config_db#(uvmVideo_uvm_pkg::vin_vif_t)::set(null, "uvm_test_top.*", "vin_model", vin_model);
        uvm_config_db#(uvmVideo_uvm_pkg::vout_vif_t)::set(null, "uvm_test_top.*", "vout_model", vout_model);
        uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_dual_dut", 1'b1);
`else
        uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_dual_dut", 1'b0);
`endif
`ifdef A2C_UVM_BOTH_DUT
        uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_model_dut", 1'b0);
`elsif A2C_UVM_RTL_DUT
        uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_model_dut", 1'b0);
`else
        uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_model_dut", 1'b1);
`endif
        uvm_root::get().finish_on_completion = 0;
        run_test();
        bfm_breaks_open = 1'b0;
        srv = uvm_report_server::get_server();
        uvm_errors = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);
        @(posedge clk);
        uvm_done = 1'b1;
    end

// GENERATED_CODE_END

// user module body here

// GENERATED_CODE_BEGIN --template=uvmTb --section=footer

endmodule : uvmVideo_uvm_tb

// GENERATED_CODE_END
