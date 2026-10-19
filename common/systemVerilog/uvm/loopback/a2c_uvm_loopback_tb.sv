`timescale 1ns/1ps

// Loopback tests of the interface agents and of a2c_uvm_pkg's classes, with
// no DUT: on each interface a src agent drives a dst agent, and a scoreboard
// matches what the dst agent's monitor reports against the items the test
// sent. The tests are in the *_lb_tests.svh files this package includes.
// run_loopback.sh builds this and runs every test those files declare.
package a2c_uvm_loopback_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;
    import rdy_vld_uvm_pkg::*;
    import axi4_stream_uvm_pkg::*;
    import raw_uvm_pkg::*;
    import status_uvm_pkg::*;
    import apb_uvm_pkg::*;
    import push_ack_uvm_pkg::*;
    import notify_ack_uvm_pkg::*;
    import req_ack_uvm_pkg::*;
    import pop_ack_uvm_pkg::*;
    import memory_uvm_pkg::*;
    import external_reg_uvm_pkg::*;
    import axi_read_uvm_pkg::*;
    import axi_write_uvm_pkg::*;

    typedef struct packed {
        logic [3:0]  tag;
        logic [19:0] value;
    } lb_data_t;

    virtual class lb_scoreboard_base extends uvm_component;
        int unsigned matched;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction
    endclass : lb_scoreboard_base

    // Matches each reported item against the oldest one not yet matched. A
    // sequence adds an item to expected before the driver puts it on the
    // pins, so the item is waiting when the monitor reports it.
    class lb_scoreboard #(type ITEM = uvm_sequence_item) extends lb_scoreboard_base;
        uvm_analysis_imp #(ITEM, lb_scoreboard#(ITEM)) imp;
        ITEM         expected[$];
        // A raw monitor reports every clock, so before the first sent item it
        // reports the idle value and after the last it repeats that item.
        bit          free_running;

        `uvm_component_param_utils(lb_scoreboard#(ITEM))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            imp = new("imp", this);
        endfunction

        virtual function void write(ITEM t);
            if (expected.size() == 0) begin
                if (!free_running) begin
                    `uvm_error("LB_EXTRA", $sformatf("reported %s after every sent item matched", t.convert2string()))
                end
                return;
            end
            if (!t.compare(expected[0])) begin
                if (free_running && matched == 0) return;
                `uvm_error("LB_MISMATCH", $sformatf("item %0d: reported %s, sent %s", matched, t.convert2string(),
                                                    expected[0].convert2string()))
            end
            void'(expected.pop_front());
            matched++;
        endfunction

        virtual function void check_phase(uvm_phase phase);
            if (expected.size() != 0) begin
                `uvm_error("LB_MISSING", $sformatf("%0d sent items never reported, %0d matched", expected.size(), matched))
            end
        endfunction
    endclass : lb_scoreboard

    class lb_base_test extends uvm_test;
        virtual a2c_clk_if clk_vif;
        int unsigned       n_items = 400;

        `uvm_component_utils(lb_base_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin
                `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
            end
        endfunction

        // Waits until the scoreboard has matched target items, or fails after
        // max_clocks.
        task wait_matched(lb_scoreboard_base sb, int unsigned target, int unsigned max_clocks);
            int unsigned clocks = 0;
            while (sb.matched < target && clocks < max_clocks) begin
                clk_vif.sample_edge();
                clocks++;
            end
            if (sb.matched < target) begin
                `uvm_error("LB_TIMEOUT", $sformatf("matched %0d of %0d items in %0d clocks", sb.matched, target, max_clocks))
            end
        endtask

        virtual function void report_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            if (srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL) == 0) begin
                `uvm_info("LB_PASS", get_type_name(), UVM_NONE)
            end
        endfunction
    endclass : lb_base_test

    `include "rdy_vld_lb_tests.svh"
    `include "axi4_stream_lb_tests.svh"
    `include "raw_lb_tests.svh"
    `include "status_lb_tests.svh"
    `include "apb_lb_tests.svh"
    `include "push_ack_lb_tests.svh"
    `include "notify_ack_lb_tests.svh"
    `include "req_ack_lb_tests.svh"
    `include "pop_ack_lb_tests.svh"
    `include "memory_lb_tests.svh"
    `include "external_reg_lb_tests.svh"
    `include "axi_read_lb_tests.svh"
    `include "axi_write_lb_tests.svh"
    `include "no_backpressure_lb_tests.svh"
    `include "a2c_txn_counter_lb_tests.svh"
    `include "a2c_mem_model_lb_tests.svh"

endpackage : a2c_uvm_loopback_pkg

module a2c_uvm_loopback_tb;

    import uvm_pkg::*;
    import a2c_uvm_loopback_pkg::*;

    bit clk;
    bit rst_n;

    always #5 clk = ~clk;

    // Released on a falling edge, so no driver sees it change at the rising
    // edge it samples.
    initial begin
        repeat (5) @(negedge clk);
        rst_n = 1'b1;
    end

    a2c_clk_if clk_if(.clk(clk), .rst_n(rst_n));
    rdy_vld_if #(.data_t(lb_data_t)) rv();
    axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis();
    raw_if #(.data_t(lb_data_t)) raw();
    status_if #(.data_t(lb_data_t)) st();
    apb_if #(.addr_t(lb_apb_word_t), .data_t(lb_apb_word_t)) apb();
    push_ack_if #(.data_t(lb_data_t)) pa();
    notify_ack_if na();
    req_ack_if #(.data_t(lb_data_t), .rdata_t(lb_rdata_t)) ra();
    pop_ack_if #(.rdata_t(lb_data_t)) po();
    memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem();
    memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem2();
    external_reg_if #(.data_t(lb_data_t)) er();
    axi_read_if #(.addr_t(lb_axr_addr_t), .data_t(lb_axr_data_t), .aruser_t(lb_axr_aruser_t),
                  .ruser_t(lb_axr_ruser_t), .id_t(lb_axr_id_t)) axr();
    axi_write_if #(.addr_t(lb_axw_addr_t), .data_t(lb_axw_data_t), .strb_t(lb_axw_strb_t), .awuser_t(lb_axw_awuser_t),
                   .wuser_t(lb_axw_wuser_t), .buser_t(lb_axw_buser_t), .id_t(lb_axw_id_t)) axw();

    initial begin
        uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top", "clk", clk_if);
        uvm_config_db#(rv_vif_t)::set(null, "uvm_test_top", "rv", rv);
        uvm_config_db#(axis_vif_t)::set(null, "uvm_test_top", "axis", axis);
        uvm_config_db#(raw_vif_t)::set(null, "uvm_test_top", "raw", raw);
        uvm_config_db#(st_vif_t)::set(null, "uvm_test_top", "st", st);
        uvm_config_db#(apb_vif_t)::set(null, "uvm_test_top", "apb", apb);
        uvm_config_db#(pa_vif_t)::set(null, "uvm_test_top", "pa", pa);
        uvm_config_db#(na_vif_t)::set(null, "uvm_test_top", "na", na);
        uvm_config_db#(ra_vif_t)::set(null, "uvm_test_top", "ra", ra);
        uvm_config_db#(po_vif_t)::set(null, "uvm_test_top", "po", po);
        uvm_config_db#(mem_vif_t)::set(null, "uvm_test_top", "mem", mem);
        uvm_config_db#(mem_vif_t)::set(null, "uvm_test_top", "mem2", mem2);
        uvm_config_db#(er_vif_t)::set(null, "uvm_test_top", "er", er);
        uvm_config_db#(axr_vif_t)::set(null, "uvm_test_top", "axr", axr);
        uvm_config_db#(axw_vif_t)::set(null, "uvm_test_top", "axw", axw);
        run_test();
    end

endmodule : a2c_uvm_loopback_tb
