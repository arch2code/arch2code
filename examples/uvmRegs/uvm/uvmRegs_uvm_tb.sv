// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegs
// GENERATED_CODE_BEGIN --template=uvmTb --section=header

`timescale 1ns/1ps

module uvmRegs_uvm_tb
    import uvm_pkg::*;
    import uvmRegs_uvm_test_pkg::*;

// GENERATED_CODE_END

// further package imports here

// GENERATED_CODE_BEGIN --template=uvmTb --section=body

(
    // rdy_vld_if.dst on the DUT
    output bit in_vld,
    output bit [$bits(uvmRegs_package::uvmRegsWordSt)-1:0] in_data,
    input  bit in_rdy,

    // rdy_vld_if.src on the DUT
    input  bit out_vld,
    input  bit [$bits(uvmRegs_package::uvmRegsWordSt)-1:0] out_data,
    output bit out_rdy,

    // apb_if.dst on the DUT
    output bit [$bits(uvmRegs_package::uvmRegsAddrSt)-1:0] apbReg_paddr,
    output bit apbReg_psel,
    output bit apbReg_penable,
    output bit apbReg_pwrite,
    output bit [$bits(uvmRegs_package::uvmRegsDataSt)-1:0] apbReg_pwdata,
    input  bit apbReg_pready,
    input  bit [$bits(uvmRegs_package::uvmRegsDataSt)-1:0] apbReg_prdata,
    input  bit apbReg_pslverr,

    input clk,
    input rst_n,

    // completion, read by the SystemC side
    output bit uvm_done,
    output bit [31:0] uvm_errors,
    output bit rtl_dut,
    output bit model_dut
);

    rdy_vld_if #(.data_t(uvmRegs_package::uvmRegsWordSt)) in();
    rdy_vld_if #(.data_t(uvmRegs_package::uvmRegsWordSt)) out();
    apb_if #(.addr_t(uvmRegs_package::uvmRegsAddrSt), .data_t(uvmRegs_package::uvmRegsDataSt)) apbReg();
    a2c_clk_if clk_if(.clk(clk), .rst_n(rst_n));

`ifdef A2C_UVM_BOTH_DUT
    rdy_vld_if #(.data_t(uvmRegs_package::uvmRegsWordSt)) in_model();
    rdy_vld_if #(.data_t(uvmRegs_package::uvmRegsWordSt)) out_model();
    apb_if #(.addr_t(uvmRegs_package::uvmRegsAddrSt), .data_t(uvmRegs_package::uvmRegsDataSt)) apbReg_model();

    uvmRegs_hdl_sv_wrapper dut (
        .in_vld(in.vld),
        .in_data(in.data),
        .in_rdy(in.rdy),
        .out_vld(out.vld),
        .out_data(out.data),
        .out_rdy(out.rdy),
        .apbReg_paddr(apbReg.paddr),
        .apbReg_psel(apbReg.psel),
        .apbReg_penable(apbReg.penable),
        .apbReg_pwrite(apbReg.pwrite),
        .apbReg_pwdata(apbReg.pwdata),
        .apbReg_pready(apbReg.pready),
        .apbReg_prdata(apbReg.prdata),
        .apbReg_pslverr(apbReg.pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

    assign in_vld = in_model.vld;
    assign in_data = in_model.data;
    assign in_model.rdy = in_rdy;
    assign out_model.vld = out_vld;
    assign out_model.data = out_data;
    assign out_rdy = out_model.rdy;
    assign apbReg_paddr = apbReg_model.paddr;
    assign apbReg_psel = apbReg_model.psel;
    assign apbReg_penable = apbReg_model.penable;
    assign apbReg_pwrite = apbReg_model.pwrite;
    assign apbReg_pwdata = apbReg_model.pwdata;
    assign apbReg_model.pready = apbReg_pready;
    assign apbReg_model.prdata = apbReg_prdata;
    assign apbReg_model.pslverr = apbReg_pslverr;
    assign rtl_dut = 1'b1;
    assign model_dut = 1'b1;
`elsif A2C_UVM_RTL_DUT
    uvmRegs_hdl_sv_wrapper dut (
        .in_vld(in.vld),
        .in_data(in.data),
        .in_rdy(in.rdy),
        .out_vld(out.vld),
        .out_data(out.data),
        .out_rdy(out.rdy),
        .apbReg_paddr(apbReg.paddr),
        .apbReg_psel(apbReg.psel),
        .apbReg_penable(apbReg.penable),
        .apbReg_pwrite(apbReg.pwrite),
        .apbReg_pwdata(apbReg.pwdata),
        .apbReg_pready(apbReg.pready),
        .apbReg_prdata(apbReg.prdata),
        .apbReg_pslverr(apbReg.pslverr),
        .clk(clk),
        .rst_n(rst_n)
    );

    assign in_vld = 1'b0;
    assign in_data = '0;
    assign out_rdy = 1'b0;
    assign apbReg_paddr = '0;
    assign apbReg_psel = 1'b0;
    assign apbReg_penable = 1'b0;
    assign apbReg_pwrite = 1'b0;
    assign apbReg_pwdata = '0;
    assign rtl_dut = 1'b1;
    assign model_dut = 1'b0;
`else
    assign in_vld = in.vld;
    assign in_data = in.data;
    assign in.rdy = in_rdy;
    assign out.vld = out_vld;
    assign out.data = out_data;
    assign out_rdy = out.rdy;
    assign apbReg_paddr = apbReg.paddr;
    assign apbReg_psel = apbReg.psel;
    assign apbReg_penable = apbReg.penable;
    assign apbReg_pwrite = apbReg.pwrite;
    assign apbReg_pwdata = apbReg.pwdata;
    assign apbReg.pready = apbReg_pready;
    assign apbReg.prdata = apbReg_prdata;
    assign apbReg.pslverr = apbReg_pslverr;
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
        uvm_config_db#(uvmRegs_uvm_pkg::in_vif_t)::set(null, "uvm_test_top.*", "in", in);
        uvm_config_db#(uvmRegs_uvm_pkg::out_vif_t)::set(null, "uvm_test_top.*", "out", out);
        uvm_config_db#(uvmRegs_uvm_pkg::apbReg_vif_t)::set(null, "uvm_test_top.*", "apbReg", apbReg);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top.*", "clk", clk_if);
`ifdef A2C_UVM_BOTH_DUT
        uvm_config_db#(uvmRegs_uvm_pkg::in_vif_t)::set(null, "uvm_test_top.*", "in_model", in_model);
        uvm_config_db#(uvmRegs_uvm_pkg::out_vif_t)::set(null, "uvm_test_top.*", "out_model", out_model);
        uvm_config_db#(uvmRegs_uvm_pkg::apbReg_vif_t)::set(null, "uvm_test_top.*", "apbReg_model", apbReg_model);
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

endmodule : uvmRegs_uvm_tb

// GENERATED_CODE_END
