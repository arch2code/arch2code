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
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each write strobe on both lanes on the same clock. Its model_cmp, an
// external_reg_comparator, checks the two lanes' rdata under its status
// policy, stable by default, because the model's rdata trails a write by a
// clock more than the RTL's. The A2C_DST driver holds a level per lane: the
// DUT lane's is cfg.value, and each lane loads its own writes. A change a
// test makes to cfg.value reaches both lanes. Its model_cmp compares the
// writes of the two lanes in order. Its replay log records each DUT lane
// write, with no response, and the model lane's write of the same index
// replays it, so a2c_replay_drain holds the end of the run phase until the
// model lane has made the DUT lane's writes. What the DUT produces that is
// not compared:
//   DUT dst port, A2C_SRC agent: intermediate `rdata`
//   DUT src port, A2C_DST agent: none
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
        // The model DUT's pin set in Mode B; null otherwise.
        virtual external_reg_if #(.data_t(data_t)) model_vif;
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

    class external_reg_driver #(type data_t = logic [31:0]) extends uvm_driver #(external_reg_item#(data_t))
        implements a2c_replay_lanes;
        typedef virtual external_reg_if #(.data_t(data_t)) vif_t;
        typedef a2c_replay_log #(bit) replay_t;

        external_reg_config#(data_t) cfg;
        // dst role in Mode B only.
        replay_t                     replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // dst role in Mode B: the model lane's level, and the last value of
        // cfg.value the driver set or saw, so a test's change is told apart
        // from the DUT lane's writes.
        protected data_t       model_value;
        protected data_t       seen_value;
        // dst role in Mode B: each lane's writes, and the model lane's
        // writes the DUT lane has yet to make.
        protected int unsigned writes[2];
        protected int unsigned ahead;

        `uvm_component_param_utils(external_reg_driver#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (cfg.model_vif == null || cfg.role != A2C_DST) return;
            replay = replay_t::type_id::create("replay", this);
            replay.driver  = this;
            replay.clk_vif = cfg.clk_vif;
        endfunction

        virtual task run_phase(uvm_phase phase);
            lane[A2C_DUT_LANE] = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            if (cfg.role == A2C_SRC) begin
                run_src();
            end else begin
                run_dst();
            end
        endtask

        protected function void drive_write(bit [1:0] write);
            for (int l = 0; l < lanes; l++) lane[l].write <= write;
        endfunction

        // Each loop iteration starts at a drive point. Writes go out on
        // consecutive clocks while items are ready; wdata holds its last
        // value between writes.
        protected virtual task run_src();
            for (int l = 0; l < lanes; l++) begin
                lane[l].write <= '0;
                lane[l].wdata <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_write('0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_write('0);
                    cfg.clk_vif.drive_edge();
                end
                for (int l = 0; l < lanes; l++) begin
                    lane[l].write <= req.write;
                    lane[l].wdata <= req.wdata;
                end
                cfg.clk_vif.drive_edge();
                drive_write('0);
                seq_item_port.item_done();
            end
        endtask

        // rdata follows its level from time 0, one drive point after each
        // change.
        protected virtual task run_dst();
            model_value = cfg.value;
            seen_value  = cfg.value;
            fork
                forever begin
                    if (lanes == 2 && cfg.value !== seen_value) begin
                        seen_value  = cfg.value;
                        model_value = cfg.value;
                    end
                    lane[A2C_DUT_LANE].rdata <= cfg.value;
                    if (lanes == 2) lane[A2C_MODEL_LANE].rdata <= model_value;
                    cfg.clk_vif.drive_edge();
                end
                begin
                    cfg.clk_vif.wait_reset_release();
                    forever begin
                        cfg.clk_vif.sample_edge();
                        for (int l = 0; l < lanes; l++) begin
                            if (lane[l].write === '0 || $isunknown(lane[l].write)) continue;
                            if (replay != null) count_write(a2c_lane_e'(l));
                            if (!cfg.update_on_write) continue;
                            if (l == A2C_DUT_LANE) begin
                                cfg.value  = lane[l].wdata;
                                seen_value = cfg.value;
                            end else begin
                                model_value = lane[l].wdata;
                            end
                        end
                    end
                end
            join
        endtask

        // A model lane write the DUT lane has yet to make waits, as the
        // model lane of a handshake port would, until the DUT lane's write
        // of the same index lets it replay.
        protected function void count_write(a2c_lane_e l);
            bit          unused;
            int unsigned delay;
            writes[l]++;
            if (l == A2C_DUT_LANE) replay.record(1'b0, 0);
            else ahead++;
            while (ahead > 0 && replay.can_replay()) begin
                replay.replay(unused, delay);
                ahead--;
            end
        endfunction

        // A write starts and completes on the clock that takes it.
        virtual function bit lane_busy(a2c_lane_e l);
            return 0;
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return writes[l];
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return writes[l];
        endfunction
    endclass : external_reg_driver

    class external_reg_monitor #(type data_t = logic [31:0]) extends uvm_monitor;
        external_reg_config#(data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual external_reg_if #(.data_t(data_t))     vif;
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
                if (first || vif.rdata !== last) begin
                    first = 0;
                    last  = vif.rdata;
                    item = external_reg_item#(data_t)::type_id::create("rdata");
                    item.write = '0;
                    item.rdata = last;
                    `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                                 $sformatf("%0h", item.rdata)), UVM_MEDIUM)
                    rdata_ap.write(item);
                end
                if (vif.write === '0 || $isunknown(vif.write)) continue;
                item = external_reg_item#(data_t)::type_id::create("item");
                item.write = vif.write;
                item.wdata = vif.wdata;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", item.wdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : external_reg_monitor

    // The A2C_SRC role's Mode B comparator, on the monitors' rdata items.
    // value() reads rdata, so the bounds policy needs no subclass; an rdata
    // wider than 64 bits is bounded on its low 64 bits. has_xz() checks every
    // bit of rdata.
    class external_reg_comparator #(type data_t = logic [31:0]) extends a2c_status_comparator #(external_reg_item#(data_t));
        `uvm_component_param_utils(external_reg_comparator#(data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function bit [63:0] value(external_reg_item#(data_t) t);
            return 64'(t.rdata);
        endfunction

        virtual function bit has_xz(external_reg_item#(data_t) t);
            return $isunknown(t.rdata);
        endfunction
    endclass : external_reg_comparator

    class external_reg_agent #(type data_t = logic [31:0]) extends uvm_agent;
        typedef external_reg_item#(data_t)   item_t;
        typedef external_reg_config#(data_t) config_t;

        config_t                                  cfg;
        external_reg_driver#(data_t)              drv;
        // A2C_SRC only.
        uvm_sequencer #(external_reg_item#(data_t)) sqr;
        external_reg_monitor#(data_t)             mon;
        // Mode B only. On the A2C_SRC role model_cmp is an
        // external_reg_comparator on rdata, on the A2C_DST role an
        // a2c_in_order_comparator on the writes.
        external_reg_monitor#(data_t)             model_mon;
        a2c_comparator_base                       model_cmp;

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
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = external_reg_monitor#(data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_SRC) model_cmp = external_reg_comparator#(data_t)::type_id::create("model_cmp", this);
                else model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active != UVM_ACTIVE) return;
            drv = external_reg_driver#(data_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            if (cfg.role == A2C_SRC) begin
                sqr = uvm_sequencer#(external_reg_item#(data_t))::type_id::create("sqr", this);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            external_reg_comparator#(data_t)   rdata_cmp;
            a2c_in_order_comparator #(item_t) write_cmp;
            if (sqr != null) drv.seq_item_port.connect(sqr.seq_item_export);
            if (model_cmp == null) return;
            if (cfg.role == A2C_SRC) begin
                void'($cast(rdata_cmp, model_cmp));
                mon.rdata_ap.connect(rdata_cmp.dut_export);
                model_mon.rdata_ap.connect(rdata_cmp.model_export);
            end else begin
                void'($cast(write_cmp, model_cmp));
                mon.ap.connect(write_cmp.dut_export);
                model_mon.ap.connect(write_cmp.model_export);
                if (drv != null && drv.replay != null) drv.replay.cmp = write_cmp;
            end
        endfunction
    endclass : external_reg_agent

endpackage : external_reg_uvm_pkg

`endif // EXTERNAL_REG_UVM_PKG_SV
