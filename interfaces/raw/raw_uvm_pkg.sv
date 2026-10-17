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
            return super.do_compare(rhs, comparer) && (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%p", data);
        endfunction
    endclass : raw_item

    class raw_config #(type data_t = logic) extends uvm_object;
        virtual raw_if #(.data_t(data_t)) vif;
        virtual a2c_clk_if                clk_vif;
        uvm_active_passive_enum           is_active = UVM_ACTIVE;
        a2c_role_e                        role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                            port_name = "";

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
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.drive_edge();
                seq_item_port.try_next_item(req);
                if (req == null) continue;
                cfg.vif.data <= req.data;
                seq_item_port.item_done();
            end
        endtask
    endclass : raw_driver

    class raw_monitor #(type data_t = logic) extends uvm_monitor;
        raw_config#(data_t)                    cfg;
        uvm_analysis_port #(raw_item#(data_t)) ap;

        `uvm_component_param_utils(raw_monitor#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            raw_item#(data_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                item = raw_item#(data_t)::type_id::create("item");
                item.data = cfg.vif.data;
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
    endclass : raw_agent

endpackage : raw_uvm_pkg

`endif // RAW_UVM_PKG_SV
