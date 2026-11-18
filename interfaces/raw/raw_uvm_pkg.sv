`ifndef RAW_UVM_PKG_SV
`define RAW_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for raw_if, which has no handshake: the src driver puts one item
// on data per clock and the monitor reports data on every clock. The role
// (a2c_role_e) names the side of the interface the agent plays; a dst agent
// has nothing to drive. Pin timing follows a2c_clk_if: drive at
// drive_edge(), sample at sample_edge().
//
// Support is limited. Against the RTL DUT the agent sees every clock. Against
// the model DUT it is best effort: the SystemC raw BFM is not transactional,
// so the model can drop or repeat a word.
//
// Paired mode. With cfg.model_vif set the agent drives the model DUT's pin
// set beside the DUT's and monitors it with model_mon. The src driver puts
// the same word on both lanes every clock. Nothing is compared. What the DUT
// produces that is not compared:
//   DUT dst port, A2C_SRC agent: none
//   DUT src port, A2C_DST agent: the word stream: no transfer boundary, and
//   the model lane is best effort
// so such an agent reports an A2C_UNCOMPARED UVM_WARNING naming its port at
// end_of_elaboration_phase, and a run that passes says what it did not check.
package raw_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class raw_item #(type data_t = logic) extends uvm_sequence_item;
        rand data_t data;

        `uvm_object_param_utils(raw_item#(data_t))

        function new(string name = "raw_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            raw_item#(data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            data = rhs_.data;
        endfunction

        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            raw_item#(data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            // A field that differs is also passed to comparer, whose
            // miscompares string then names it.
            if (data !== rhs_.data) void'(comparer.compare_field("data", data, rhs_.data, $bits(data)));
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : raw_item

    class raw_config #(type data_t = logic) extends a2c_agent_config #(virtual raw_if #(.data_t(data_t)));
        `uvm_object_param_utils(raw_config#(data_t))

        function new(string name = "raw_config");
            super.new(name);
        endfunction
    endclass : raw_config

    // src role only. data holds its last value on a clock with no item.
    class raw_driver #(type data_t = logic) extends uvm_driver #(raw_item#(data_t));
        raw_config#(data_t) cfg;

        `uvm_component_param_utils(raw_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            cfg.vif.data <= '0;
            if (cfg.model_vif != null) cfg.model_vif.data <= '0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.drive_edge();
                seq_item_port.try_next_item(req);
                if (req == null) continue;
                cfg.vif.data <= req.data;
                if (cfg.model_vif != null) cfg.model_vif.data <= req.data;
                seq_item_port.item_done();
            end
        endtask
    endclass : raw_driver

    class raw_monitor #(type data_t = logic) extends a2c_monitor;
        raw_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual raw_if #(.data_t(data_t))      vif;
        uvm_analysis_port #(raw_item#(data_t)) ap;

        `uvm_component_param_utils(raw_monitor#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual function a2c_clk_vif_t monitor_clock();
            return cfg.clk_vif;
        endfunction

        virtual task run_from_reset();
            raw_item#(data_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.clk_vif.in_reset()) continue;
                item = raw_item#(data_t)::type_id::create("item");
                item.data = vif.data;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", item.data)), UVM_HIGH)
                ap.write(item);
            end
        endtask
    endclass : raw_monitor

    class raw_agent #(type data_t = logic) extends uvm_agent;
        typedef raw_item#(data_t)   item_t;
        typedef raw_config#(data_t) config_t;

        config_t                  cfg;
        raw_driver#(data_t)       drv;
        uvm_sequencer #(item_t)   sqr;
        raw_monitor#(data_t)      mon;
        // Paired mode only.
        raw_monitor#(data_t)      model_mon;
        // Always null, because raw compares nothing; the env lists every
        // agent's model_cmp that is set.
        a2c_comparator_base       model_cmp;

        `uvm_component_param_utils(raw_agent#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "raw_agent has no cfg")
            end
            mon = raw_monitor#(data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = raw_monitor#(data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
            end
            if (cfg.is_active == UVM_ACTIVE && cfg.role == A2C_SRC) begin
                drv = raw_driver#(data_t)::type_id::create("drv", this);
                drv.cfg = cfg;
                sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
        endfunction

        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (cfg.model_vif == null || cfg.role != A2C_DST) return;
            `uvm_warning("A2C_UNCOMPARED", $sformatf("%s: paired mode does not compare raw port %s; the DUT's words on it are monitored but not checked against the model's",
                                                     get_full_name(), cfg.port_name))
        endfunction
    endclass : raw_agent

endpackage : raw_uvm_pkg

`endif // RAW_UVM_PKG_SV
