`ifndef STATUS_UVM_PKG_SV
`define STATUS_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for status_if. A status value is a level, not a stream of
// transactions: the src driver holds data at the value in the config, which a
// test may change at any time, and the monitor reports the value after reset
// release and each change of it. The role (a2c_role_e) names the side of the
// interface the agent plays; a dst agent has nothing to drive. Pin timing
// follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The src driver holds the
// same level on both lanes. On the A2C_DST role model_cmp, a
// status_comparator, checks the two lanes under its policy, stable by
// default. What the DUT produces that is not compared:
//   DUT dst port, A2C_SRC agent: none
//   DUT src port, A2C_DST agent: intermediate values under `stable`
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
        // The model DUT's pin set in Mode B; null otherwise.
        virtual status_if #(.data_t(data_t)) model_vif;
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
                if (cfg.model_vif != null) cfg.model_vif.data <= cfg.value;
                cfg.clk_vif.drive_edge();
            end
        endtask
    endclass : status_driver

    class status_monitor #(type data_t = logic) extends uvm_monitor;
        status_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual status_if #(.data_t(data_t))      vif;
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
                if (!first && vif.data === last) continue;
                first = 0;
                last  = vif.data;
                item = status_item#(data_t)::type_id::create("item");
                item.data = last;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", item.data)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : status_monitor

    // The status agent's Mode B comparator. value() reads data, so the
    // bounds policy needs no subclass; a data_t wider than 64 bits is
    // bounded on its low 64 bits, and a signed data_t compares as unsigned
    // 64-bit. has_xz() checks every bit of data, including bits above the
    // low 64 that value() never reads, and the bounds policy reports a
    // flagged item instead of reading its bounds.
    class status_comparator #(type data_t = logic) extends a2c_status_comparator #(status_item#(data_t));
        `uvm_component_param_utils(status_comparator#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function bit [63:0] value(status_item#(data_t) t);
            return 64'(t.data);
        endfunction

        virtual function bit has_xz(status_item#(data_t) t);
            return $isunknown(t.data);
        endfunction
    endclass : status_comparator

    class status_agent #(type data_t = logic) extends uvm_agent;
        typedef status_item#(data_t)   item_t;
        typedef status_config#(data_t) config_t;

        config_t                cfg;
        status_driver#(data_t)  drv;
        status_monitor#(data_t) mon;
        // Mode B only. model_cmp exists on the A2C_DST role.
        status_monitor#(data_t)    model_mon;
        status_comparator#(data_t) model_cmp;

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
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = status_monitor#(data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_DST) model_cmp = status_comparator#(data_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active == UVM_ACTIVE && cfg.role == A2C_SRC) begin
                drv = status_driver#(data_t)::type_id::create("drv", this);
                drv.cfg = cfg;
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
            end
        endfunction
    endclass : status_agent

endpackage : status_uvm_pkg

`endif // STATUS_UVM_PKG_SV
