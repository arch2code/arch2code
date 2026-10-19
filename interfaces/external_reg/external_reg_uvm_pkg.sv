`ifndef EXTERNAL_REG_UVM_PKG_SV
`define EXTERNAL_REG_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for external_reg_if, a register that lives in the dst block. A
// write is one clock with write != 0, carrying wdata; rdata is a level the
// register's owner drives on every clock. There is no handshake. The
// A2C_SRC driver sends each item as a one-clock write strobe. The A2C_DST
// driver holds rdata at cfg.value and, when cfg.update_on_write is set,
// loads each write's wdata into it, so rdata follows a write one clock
// later, as a register flop does. Pin timing follows a2c_clk_if: drive at
// drive_edge(), sample at sample_edge().
//
// Against a model DUT, the A2C_SRC agent sees rdata from the SystemC
// register's mirror, which the BFM copies to the pins. After a write, that
// rdata trails the write by up to two clocks, where an RTL register's trails
// it by one.
package external_reg_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    // A write item has write != 0 and leaves rdata zero. An rdata item, from
    // the monitor's rdata_ap, has write zero and only rdata set.
    class external_reg_item #(type data_t = logic [31:0]) extends uvm_sequence_item;
        // The strobe value; any set bit requests a write.
        bit [1:0]   write = 2'b01;
        rand data_t wdata;
        data_t      rdata;
        // src role: idle clocks (write zero) the driver inserts before this write.
        int unsigned gap;

        `uvm_object_param_utils(external_reg_item#(data_t))

        function new(string name = "external_reg_item");
            super.new(name);
            wdata = '0;
            rdata = '0;
        endfunction

        virtual function void do_copy(uvm_object rhs);
            external_reg_item#(data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            write = rhs_.write;
            wdata = rhs_.wdata;
            rdata = rhs_.rdata;
            gap   = rhs_.gap;
        endfunction

        // gap is stimulus timing, not payload, so it takes no part in the
        // compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            external_reg_item#(data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (write === rhs_.write) && (wdata === rhs_.wdata) &&
                   (rdata === rhs_.rdata);
        endfunction

        virtual function string convert2string();
            if (write == 0) return $sformatf("rdata=%p", rdata);
            return $sformatf("write=%b wdata=%p", write, wdata);
        endfunction
    endclass : external_reg_item

    class external_reg_config #(type data_t = logic [31:0]) extends uvm_object;
        virtual external_reg_if #(.data_t(data_t)) vif;
        virtual a2c_clk_if                         clk_vif;
        uvm_active_passive_enum                    is_active = UVM_ACTIVE;
        a2c_role_e                                 role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                     port_name = "";
        // dst role: the value the driver holds on rdata. A test may change it
        // at any time.
        data_t                                     value = '0;
        // dst role: each write loads its wdata into value.
        bit                                        update_on_write = 1'b1;

        `uvm_object_param_utils(external_reg_config#(data_t))

        function new(string name = "external_reg_config");
            super.new(name);
        endfunction
    endclass : external_reg_config

    class external_reg_driver #(type data_t = logic [31:0]) extends uvm_driver #(external_reg_item#(data_t));
        external_reg_config#(data_t) cfg;

        `uvm_component_param_utils(external_reg_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            if (cfg.role == A2C_SRC) begin
                run_src();
            end else begin
                run_dst();
            end
        endtask

        // Each loop iteration starts at a drive point. Writes go out on
        // consecutive clocks while items are ready; wdata holds its last
        // value between writes.
        protected virtual task run_src();
            cfg.vif.write <= '0;
            cfg.vif.wdata <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.write <= '0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.write <= '0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.write <= req.write;
                cfg.vif.wdata <= req.wdata;
                cfg.clk_vif.drive_edge();
                cfg.vif.write <= '0;
                seq_item_port.item_done();
            end
        endtask

        // rdata follows cfg.value from time 0, one drive point after each
        // change.
        protected virtual task run_dst();
            fork
                forever begin
                    cfg.vif.rdata <= cfg.value;
                    cfg.clk_vif.drive_edge();
                end
                begin
                    cfg.clk_vif.wait_reset_release();
                    forever begin
                        cfg.clk_vif.sample_edge();
                        if (cfg.update_on_write && cfg.vif.write !== '0 && !$isunknown(cfg.vif.write)) begin
                            cfg.value = cfg.vif.wdata;
                        end
                    end
                end
            join
        endtask
    endclass : external_reg_driver

    class external_reg_monitor #(type data_t = logic [31:0]) extends uvm_monitor;
        external_reg_config#(data_t)                    cfg;
        // One item per write.
        uvm_analysis_port #(external_reg_item#(data_t)) ap;
        // One item with rdata after reset release, and one per change of it.
        uvm_analysis_port #(external_reg_item#(data_t)) rdata_ap;

        `uvm_component_param_utils(external_reg_monitor#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap       = new("ap", this);
            rdata_ap = new("rdata_ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            external_reg_item#(data_t) item;
            data_t                     last;
            bit                        first = 1;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (first || cfg.vif.rdata !== last) begin
                    first = 0;
                    last  = cfg.vif.rdata;
                    item = external_reg_item#(data_t)::type_id::create("rdata");
                    item.write = '0;
                    item.rdata = last;
                    `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                                 $sformatf("%0h", item.rdata)), UVM_MEDIUM)
                    rdata_ap.write(item);
                end
                if (cfg.vif.write === '0 || $isunknown(cfg.vif.write)) continue;
                item = external_reg_item#(data_t)::type_id::create("item");
                item.write = cfg.vif.write;
                item.wdata = cfg.vif.wdata;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", item.wdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : external_reg_monitor

    class external_reg_agent #(type data_t = logic [31:0]) extends uvm_agent;
        typedef external_reg_item#(data_t)   item_t;
        typedef external_reg_config#(data_t) config_t;

        config_t                                  cfg;
        external_reg_driver#(data_t)              drv;
        // A2C_SRC only.
        uvm_sequencer #(external_reg_item#(data_t)) sqr;
        external_reg_monitor#(data_t)             mon;

        `uvm_component_param_utils(external_reg_agent#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "external_reg_agent has no cfg")
            end
            mon = external_reg_monitor#(data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active != UVM_ACTIVE) return;
            drv = external_reg_driver#(data_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            if (cfg.role == A2C_SRC) begin
                sqr = uvm_sequencer#(external_reg_item#(data_t))::type_id::create("sqr", this);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) drv.seq_item_port.connect(sqr.seq_item_export);
        endfunction
    endclass : external_reg_agent

endpackage : external_reg_uvm_pkg

`endif // EXTERNAL_REG_UVM_PKG_SV
