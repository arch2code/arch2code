// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=uvmTb --section=header

`timescale 1ns/1ps

module uvmMem_uvm_tb
    import uvm_pkg::*;
    import uvmMem_uvm_test_pkg::*;

// GENERATED_CODE_END

// further package imports here

// GENERATED_CODE_BEGIN --template=uvmTb --section=body

(
    // rdy_vld_if.dst on the DUT
    output bit cmd_vld,
    output bit [$bits(uvmMem_package::uvmMemCmdSt)-1:0] cmd_data,
    input  bit cmd_rdy,

    // rdy_vld_if.src on the DUT
    input  bit out_vld,
    input  bit [$bits(uvmMem_package::uvmMemWordSt)-1:0] out_data,
    output bit out_rdy,

    // memory_if.src on the DUT
    input  bit [$bits(uvmMem_package::uvmMemWordSt)-1:0] wr_write_data,
    output bit [$bits(uvmMem_package::uvmMemWordSt)-1:0] wr_read_data,
    input  bit [$bits(uvmMem_package::uvmMemAddrSt)-1:0] wr_addr,
    input  bit wr_enable,
    input  bit wr_wr_en,

    // memory_if.src on the DUT
    input  bit [$bits(uvmMem_package::uvmMemWordSt)-1:0] rd_write_data,
    output bit [$bits(uvmMem_package::uvmMemWordSt)-1:0] rd_read_data,
    input  bit [$bits(uvmMem_package::uvmMemAddrSt)-1:0] rd_addr,
    input  bit rd_enable,
    input  bit rd_wr_en,

    input clk,
    input rst_n,

    // Mode B credit of wr, between its agent and the model's BFM
    output bit [31:0] wr_model_credit,
    input  bit wr_model_held,

    // Mode B credit of rd, between its agent and the model's BFM
    output bit [31:0] rd_model_credit,
    input  bit rd_model_held,

    // completion, read by the SystemC side
    output bit uvm_done,
    output bit [31:0] uvm_errors,
    output bit rtl_dut,
    output bit model_dut
);

    rdy_vld_if #(.data_t(uvmMem_package::uvmMemCmdSt)) cmd();
    rdy_vld_if #(.data_t(uvmMem_package::uvmMemWordSt)) out();
    memory_if #(.addr_t(uvmMem_package::uvmMemAddrSt), .data_t(uvmMem_package::uvmMemWordSt)) wr();
    memory_if #(.addr_t(uvmMem_package::uvmMemAddrSt), .data_t(uvmMem_package::uvmMemWordSt)) rd();
    a2c_clk_if clk_if(.clk(clk), .rst_n(rst_n));

`ifdef A2C_UVM_BOTH_DUT
    rdy_vld_if #(.data_t(uvmMem_package::uvmMemCmdSt)) cmd_model();
    rdy_vld_if #(.data_t(uvmMem_package::uvmMemWordSt)) out_model();
    memory_if #(.addr_t(uvmMem_package::uvmMemAddrSt), .data_t(uvmMem_package::uvmMemWordSt)) wr_model();
    memory_if #(.addr_t(uvmMem_package::uvmMemAddrSt), .data_t(uvmMem_package::uvmMemWordSt)) rd_model();
    a2c_credit_if wr_credit();
    a2c_credit_if rd_credit();

    uvmMem_hdl_sv_wrapper dut (
        .cmd_vld(cmd.vld),
        .cmd_data(cmd.data),
        .cmd_rdy(cmd.rdy),
        .out_vld(out.vld),
        .out_data(out.data),
        .out_rdy(out.rdy),
        .wr_write_data(wr.write_data),
        .wr_read_data(wr.read_data),
        .wr_addr(wr.addr),
        .wr_enable(wr.enable),
        .wr_wr_en(wr.wr_en),
        .rd_write_data(rd.write_data),
        .rd_read_data(rd.read_data),
        .rd_addr(rd.addr),
        .rd_enable(rd.enable),
        .rd_wr_en(rd.wr_en),
        .clk(clk),
        .rst_n(rst_n)
    );

    assign cmd_vld = cmd_model.vld;
    assign cmd_data = cmd_model.data;
    assign cmd_model.rdy = cmd_rdy;
    assign out_model.vld = out_vld;
    assign out_model.data = out_data;
    assign out_rdy = out_model.rdy;
    assign wr_model.write_data = wr_write_data;
    assign wr_read_data = wr_model.read_data;
    assign wr_model.addr = wr_addr;
    assign wr_model.enable = wr_enable;
    assign wr_model.wr_en = wr_wr_en;
    assign rd_model.write_data = rd_write_data;
    assign rd_read_data = rd_model.read_data;
    assign rd_model.addr = rd_addr;
    assign rd_model.enable = rd_enable;
    assign rd_model.wr_en = rd_wr_en;
    assign wr_model_credit = wr_credit.credit;
    assign wr_credit.held = wr_model_held;
    assign rd_model_credit = rd_credit.credit;
    assign rd_credit.held = rd_model_held;
    assign rtl_dut = 1'b1;
    assign model_dut = 1'b1;
`elsif A2C_UVM_RTL_DUT
    uvmMem_hdl_sv_wrapper dut (
        .cmd_vld(cmd.vld),
        .cmd_data(cmd.data),
        .cmd_rdy(cmd.rdy),
        .out_vld(out.vld),
        .out_data(out.data),
        .out_rdy(out.rdy),
        .wr_write_data(wr.write_data),
        .wr_read_data(wr.read_data),
        .wr_addr(wr.addr),
        .wr_enable(wr.enable),
        .wr_wr_en(wr.wr_en),
        .rd_write_data(rd.write_data),
        .rd_read_data(rd.read_data),
        .rd_addr(rd.addr),
        .rd_enable(rd.enable),
        .rd_wr_en(rd.wr_en),
        .clk(clk),
        .rst_n(rst_n)
    );

    assign cmd_vld = 1'b0;
    assign cmd_data = '0;
    assign out_rdy = 1'b0;
    assign wr_read_data = '0;
    assign rd_read_data = '0;
    assign wr_model_credit = '0;
    assign rd_model_credit = '0;
    assign rtl_dut = 1'b1;
    assign model_dut = 1'b0;
`else
    assign cmd_vld = cmd.vld;
    assign cmd_data = cmd.data;
    assign cmd.rdy = cmd_rdy;
    assign out.vld = out_vld;
    assign out.data = out_data;
    assign out_rdy = out.rdy;
    assign wr.write_data = wr_write_data;
    assign wr_read_data = wr.read_data;
    assign wr.addr = wr_addr;
    assign wr.enable = wr_enable;
    assign wr.wr_en = wr_wr_en;
    assign rd.write_data = rd_write_data;
    assign rd_read_data = rd.read_data;
    assign rd.addr = rd_addr;
    assign rd.enable = rd_enable;
    assign rd.wr_en = rd_wr_en;
    assign wr_model_credit = '0;
    assign rd_model_credit = '0;
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
        uvm_config_db#(uvmMem_uvm_pkg::cmd_vif_t)::set(null, "uvm_test_top.*", "cmd", cmd);
        uvm_config_db#(uvmMem_uvm_pkg::out_vif_t)::set(null, "uvm_test_top.*", "out", out);
        uvm_config_db#(uvmMem_uvm_pkg::wr_vif_t)::set(null, "uvm_test_top.*", "wr", wr);
        uvm_config_db#(uvmMem_uvm_pkg::rd_vif_t)::set(null, "uvm_test_top.*", "rd", rd);
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top.*", "clk", clk_if);
`ifdef A2C_UVM_BOTH_DUT
        uvm_config_db#(uvmMem_uvm_pkg::cmd_vif_t)::set(null, "uvm_test_top.*", "cmd_model", cmd_model);
        uvm_config_db#(uvmMem_uvm_pkg::out_vif_t)::set(null, "uvm_test_top.*", "out_model", out_model);
        uvm_config_db#(uvmMem_uvm_pkg::wr_vif_t)::set(null, "uvm_test_top.*", "wr_model", wr_model);
        uvm_config_db#(uvmMem_uvm_pkg::rd_vif_t)::set(null, "uvm_test_top.*", "rd_model", rd_model);
        uvm_config_db#(virtual a2c_credit_if)::set(null, "uvm_test_top.*", "wr_credit", wr_credit);
        uvm_config_db#(virtual a2c_credit_if)::set(null, "uvm_test_top.*", "rd_credit", rd_credit);
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

endmodule : uvmMem_uvm_tb

// GENERATED_CODE_END
