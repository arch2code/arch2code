`ifndef STATUS_UVM_PKG_SV
`define STATUS_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for status_if. A status value is a level, not a stream of
// transactions: the src driver holds data at the value in the config, which a
// test may change at any time, and the monitor reports the value after reset
// release and each change of it. The role (a2c_role_e) names the side of the
// interface the agent plays; a dst agent has nothing to drive. Pin timing
// follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
package status_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class status_item #(type data_t = logic) extends uvm_sequence_item;
        data_t data;

        `uvm_object_param_utils(status_item#(data_t))

        function new(string name = "status_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            status_item#(data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            data = rhs_.data;
        endfunction

        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            status_item#(data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : status_item

    class status_config #(type data_t = logic) extends uvm_object;
        virtual status_if #(.data_t(data_t)) vif;
        virtual a2c_clk_if                   clk_vif;
        uvm_active_passive_enum              is_active = UVM_ACTIVE;
        a2c_role_e                           role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                               port_name = "";
        // src role: the value the driver holds on data.
        data_t                               value = '0;

        `uvm_object_param_utils(status_config#(data_t))

        function new(string name = "status_config");
            super.new(name);
        endfunction
    endclass : status_config

    // src role only. data follows cfg.value from time 0, one drive point
    // after each change.
    class status_driver #(type data_t = logic) extends uvm_component;
        status_config#(data_t) cfg;

        `uvm_component_param_utils(status_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            forever begin
                cfg.vif.data <= cfg.value;
                cfg.clk_vif.drive_edge();
            end
        endtask
    endclass : status_driver

    class status_monitor #(type data_t = logic) extends uvm_monitor;
        status_config#(data_t)                    cfg;
        uvm_analysis_port #(status_item#(data_t)) ap;

        `uvm_component_param_utils(status_monitor#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            status_item#(data_t) item;
            data_t               last;
            bit                  first = 1;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (!first && cfg.vif.data === last) continue;
                first = 0;
                last  = cfg.vif.data;
                item = status_item#(data_t)::type_id::create("item");
                item.data = last;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", item.data)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : status_monitor

    class status_agent #(type data_t = logic) extends uvm_agent;
        typedef status_item#(data_t)   item_t;
        typedef status_config#(data_t) config_t;

        config_t                cfg;
        status_driver#(data_t)  drv;
        status_monitor#(data_t) mon;

        `uvm_component_param_utils(status_agent#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "status_agent has no cfg")
            end
            mon = status_monitor#(data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active == UVM_ACTIVE && cfg.role == A2C_SRC) begin
                drv = status_driver#(data_t)::type_id::create("drv", this);
                drv.cfg = cfg;
            end
        endfunction
    endclass : status_agent

endpackage : status_uvm_pkg

`endif // STATUS_UVM_PKG_SV
