`ifndef AXI_READ_UVM_PKG_SV
`define AXI_READ_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for axi_read_if: an AXI4 read master driver for the A2C_SRC role,
// a slave driver for the A2C_DST role, and a monitor. AMBA 5 calls the two
// sides Manager and Subordinate. One item is one burst. The type parameters
// and their defaults are the interface's.
//
// The master drives AR and R independently: it calls item_done() once the
// burst's AR transfers, so up to cfg.max_outstanding bursts are in flight,
// and returns each burst with put_response() when its last beat arrives. A
// sequence extends axi_read_base_seq to receive those responses.
//
// The slave serves bursts from cfg.mem, an a2c_mem_model of bytes at byte
// addresses, in the order their AR transfers, whatever their ID, or with
// cfg.reorder in any order that keeps each ID's bursts in AR order. Byte X of a
// beat sits on bus byte lane X % (1 << FULL_SIZE), as the AXI address rules
// place it. A bus that is not a power-of-two number of whole bytes carries
// only full-width transfers; the lanes beyond its width do not exist.
//
// Pin timing follows a2c_clk_if: drive at drive_edge(), sample at
// sample_edge().
//
// The master and the monitor take R beats of different IDs interleaved, each
// beat for the oldest open burst of its rid. The slave never interleaves: it
// sends a burst's beats in a row.
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon, and model_cmp, an
// axi_read_comparator, compares the bursts the two lanes report in order per
// ID: AR fields and every beat's rdata, rresp and ruser. The master puts each
// AR on both lanes at one drive point, each lane drops arvalid once its own
// AR has transferred, and the next item starts when both have; up to
// cfg.max_outstanding bursts are in flight on each lane. rready has the same
// level on both lanes. A burst's response returns once both lanes have its
// last beat, with the DUT lane's beats. A lane that trails the other by
// lane_skew_cycles clocks on a burst's AR or last beat is declared dead in
// one A2C_SKEW error (axi_read_master_driver::declare_dead()), and the master
// serves the sequence from the other lane alone from then on. The slave
// serves both lanes from the one cfg.mem. The DUT lane chooses each burst it
// serves, reads its beats from the memory and records them in its replay log;
// the model lane never chooses and never reads the memory. It serves the DUT
// lane's picks in order, each as its own AR with the same ID and the same
// place among that ID's ARs, after the delay the DUT lane drew, with the
// beats the DUT lane read. A model lane that leads waits for the DUT lane's
// pick, and then for each beat the DUT lane has not read yet. Since the
// model lane follows the DUT lane's order, the model must keep as many ARs
// outstanding as the RTL. One that holds an AR back until an earlier
// response leaves the model lane holding a pick, a model defect the slave
// reports. arready has the same level on both lanes. A burst one lane issues
// and the other never does is an A2C_REPLAY error at the end of the run. The
// replay log holds the end of the run phase while the model lane catches up
// (a2c_replay_drain). A passive agent on either pin set learns of a death and
// of a cut through a2c_pin_registry. What the DUT produces that is not
// compared:
//   DUT axi_read dst port, A2C_SRC master: valid and ready timing, order across IDs
//   DUT axi_read src port, A2C_DST slave: none
package axi_read_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class axi_read_item #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                          type ruser_t = logic, type id_t = logic [3:0]) extends uvm_sequence_item;
        localparam int unsigned ADDR_W     = $bits(addr_t);
        localparam int unsigned DATA_BYTES = ($bits(data_t) + 7) / 8;
        // arsize of a full-width beat.
        localparam int unsigned FULL_SIZE  = $clog2(DATA_BYTES);
        // Narrow transfers need a bus of a power-of-two number of whole bytes.
        localparam bit          BYTE_LANES = ($bits(data_t) % 8 == 0) && (DATA_BYTES == (1 << FULL_SIZE));
        // An INCR burst stays within one 4 KB page, or within the address
        // space when that is smaller.
        localparam longint unsigned PAGE   = (ADDR_W < 12) ? (64'd1 << ADDR_W) : 64'd4096;

        rand bit [ADDR_W-1:0] addr;
        rand id_t             id;
        rand bit [7:0]        len;
        rand bit [2:0]        size;
        rand axi_burst_e      burst;
        rand aruser_t         aruser;
        // One entry per beat, filled from R: rdata, rresp and ruser.
        data_t                data[];
        axi_resp_e            resp[];
        ruser_t               ruser[];
        // src role: idle clocks (arvalid low) the master inserts before this AR.
        int unsigned          gap;
        // Bytes the burst may move, (len + 1) << size; 0 means no limit.
        // axi_read_base_seq::new_item() sets it from the port's config.
        int unsigned          max_transfer_bytes;

        constraint c_axi4 {
            solve burst before len, addr;
            solve size before len, addr;
            size <= FULL_SIZE;
            !BYTE_LANES -> size == FULL_SIZE;
            burst != AXI_INCR -> len <= 15;
            burst == AXI_WRAP -> len inside {1, 3, 7, 15};
            burst == AXI_WRAP -> (addr & ((64'd1 << size) - 1)) == 0;
            burst == AXI_INCR -> ((addr % PAGE) & ~((64'd1 << size) - 1)) + ((64'(len) + 1) << size) <= PAGE;
            max_transfer_bytes != 0 -> ((64'(len) + 1) << size) <= max_transfer_bytes;
        }

        `uvm_object_param_utils(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name = "axi_read_item");
            super.new(name);
        endfunction

        function int unsigned total_bytes();
            return (int'(len) + 1) << size;
        endfunction

        virtual function void do_copy(uvm_object rhs);
            axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            addr               = rhs_.addr;
            id                 = rhs_.id;
            len                = rhs_.len;
            size               = rhs_.size;
            burst              = rhs_.burst;
            aruser             = rhs_.aruser;
            data               = rhs_.data;
            resp               = rhs_.resp;
            ruser              = rhs_.ruser;
            gap                = rhs_.gap;
            max_transfer_bytes = rhs_.max_transfer_bytes;
        endfunction

        // gap and max_transfer_bytes shape the stimulus, so they take no
        // part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            if (!super.do_compare(rhs, comparer)) return 0;
            if (addr !== rhs_.addr || id !== rhs_.id || len !== rhs_.len || size !== rhs_.size ||
                burst !== rhs_.burst || aruser !== rhs_.aruser) return 0;
            if (data.size() != rhs_.data.size() || resp.size() != rhs_.resp.size() ||
                ruser.size() != rhs_.ruser.size()) return 0;
            foreach (data[i]) if (data[i] !== rhs_.data[i]) return 0;
            foreach (resp[i]) if (resp[i] !== rhs_.resp[i]) return 0;
            foreach (ruser[i]) if (ruser[i] !== rhs_.ruser[i]) return 0;
            return 1;
        endfunction

        virtual function string convert2string();
            return $sformatf("id=%0h addr=%0h len=%0d size=%0d burst=%s aruser=%0h beats=%0d", id, addr, len, size,
                             burst.name(), aruser, data.size());
        endfunction

        function string beat2string(int unsigned n);
            return $sformatf("id=%0h beat %0d of %0d rdata=%p rresp=%s ruser=%0h", id, n, int'(len) + 1, data[n],
                             resp[n].name(), ruser[n]);
        endfunction
    endclass : axi_read_item

    // The slave's memory: one byte per byte address.
    typedef a2c_mem_model #(bit [7:0]) axi_read_mem_t;

    class axi_read_config #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                            type ruser_t = logic, type id_t = logic [3:0]) extends uvm_object;
        virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                              .id_t(id_t))  vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                              .id_t(id_t))  model_vif;
        virtual a2c_clk_if                  clk_vif;
        uvm_active_passive_enum             is_active = UVM_ACTIVE;
        a2c_role_e                          role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                              port_name = "";
        // Bytes one burst may move, 0 for no limit. The env sets it to the
        // port's maxTransferSize, a connection's override where one reaches
        // the port. The SystemC channel counts that value in beats, so
        // reading it as bytes is the limit every bus width meets.
        int unsigned                        max_transfer_bytes = 0;
        // The port binds no id_t, so the design behind it carries no ID and
        // may answer every burst with ID 0. The master then sends every
        // burst with ID 0.
        bit                                 id_unbound = 0;
        // A2C_SRC role: bursts whose AR has gone out and whose last beat has
        // not arrived, and the percentage of clocks with rready high.
        int unsigned                        max_outstanding = 1;
        int unsigned                        rready_pct = 100;
        // A2C_DST role. The agent creates mem when the test leaves it null.
        // arready is high on arready_pct percent of clocks. Each burst draws
        // a delay of resp_delay_min to resp_delay_max clocks, counted from
        // its AR transfer, before its first beat may go out. A burst still
        // waits for the bursts ahead of it, or with reorder only for the
        // bursts ahead of it with its ID. A beat whose address falls in an
        // error range gets SLVERR and reads zero.
        axi_read_mem_t                      mem;
        int unsigned                        arready_pct = 100;
        int unsigned                        resp_delay_min = 0;
        int unsigned                        resp_delay_max = 0;
        bit                                 reorder = 0;
        axi_addr_range_t                    error_ranges[$];

        `uvm_object_param_utils(axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name = "axi_read_config");
            super.new(name);
        endfunction
    endclass : axi_read_config

    // The sequence an A2C_SRC test extends. The master returns each burst
    // with its read data as a response after item_done(); use_response_handler
    // keeps those responses out of the sequence's response queue, which would
    // otherwise overflow. send() counts the bursts, read_done() sees each
    // response, and wait_for_reads() holds body() until every burst has
    // returned, since a response to a sequence that has ended is dropped.
    // A response with no beats is an item the master refused. new_item()
    // gives an item whose constraints keep it within the port's
    // max_transfer_bytes.
    class axi_read_base_seq #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                              type ruser_t = logic, type id_t = logic [3:0])
        extends uvm_sequence #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t));
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t)   item_t;
        typedef axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) config_t;

        protected int unsigned reads_sent;
        protected int unsigned reads_done;
        protected config_t     cfg;

        `uvm_object_param_utils(axi_read_base_seq#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name = "axi_read_base_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        // The agent publishes its config to its sequencer, so this works once
        // the sequence has a sequencer.
        function item_t new_item(string name = "item");
            item_t it = item_t::type_id::create(name);
            if (cfg == null && !uvm_config_db#(config_t)::get(m_sequencer, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_read_base_seq: the sequencer has no axi_read config")
            end
            it.max_transfer_bytes = cfg.max_transfer_bytes;
            return it;
        endfunction

        task send(item_t it);
            start_item(it);
            finish_item(it);
            reads_sent++;
        endtask

        task wait_for_reads();
            wait (reads_done >= reads_sent);
        endtask

        // Called once per burst, with the request's AR fields and the beats read.
        virtual function void read_done(item_t rsp);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
            item_t rsp;
            $cast(rsp, response);
            reads_done++;
            read_done(rsp);
        endfunction
    endclass : axi_read_base_seq

    // One burst of the master, built when its AR goes out, because a
    // sequence may reuse the request object for its next item. Indexed by
    // lane: the response that collects the lane's beats, whether its AR
    // transferred, and whether its last beat has. first_done is the clock
    // the first lane completed the burst on, or -1, and first_at its time.
    // settled is set once the burst has returned to the sequence.
    class axi_read_open #(type item_t = uvm_sequence_item);
        item_t   rsp[2];
        bit      ar_taken[2];
        bit      done[2];
        longint  first_done = -1;
        realtime first_at;
        bit      settled;
    endclass : axi_read_open

    typedef class axi_read_monitor;

    class axi_read_master_driver #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                                   type ruser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t));
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                   id_key_t;
        typedef virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                                      .id_t(id_t))                      vif_t;
        typedef axi_read_open #(item_t)                                 open_t;

        axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) cfg;
        // Mode B: the agent's model_cmp and its two monitors, indexed by
        // a2c_lane_e, which the master tells of a dead lane.
        a2c_comparator_base                                       cmp;
        axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t) mons[2];
        // The passive agents on each lane's pin set, indexed by a2c_lane_e.
        a2c_pin_watchers                                          watchers[2];

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // Mode B: the clocks a lane may trail the other on a burst's AR or
        // its last beat before the master declares it dead, and, once the
        // other lane is dead, the clocks the live lane may go without an AR
        // or a beat while it has one to take; 0 turns either rule off.
        // a2c_lane_skew_cycles and a2c_lone_lane_cycles in the uvm_config_db
        // set them. They are independent: a lone lane's stall is a slave's
        // latency or the DUT's backpressure, which a tight skew bound does
        // not limit.
        int unsigned           lane_skew_cycles = 200000;
        int unsigned           lone_lane_cycles = 200000;

        // Bursts waiting for their beats on each live lane, oldest first per
        // ID; every burst not yet returned, in AR order; the bursts one lane
        // has completed and the other has not, in the order the first lane
        // completed them; and the clocks run_r() has counted.
        protected open_t       pending[2][id_key_t][$];
        protected int unsigned outstanding[2];
        protected open_t       opened[$];
        protected open_t       skewed[$];
        protected longint      clocks;
        // The burst whose AR is on the bus, or null.
        protected open_t       ar_cur;
        // A dead lane is never driven or read again, apart from an arvalid
        // it had raised, which drops at the drive point after that AR
        // transfers. stuck counts the clocks the one live lane has gone
        // without progress, and moved_at is when each lane last made
        // progress.
        protected bit          dead[2];
        protected realtime     died_at[2];
        protected bit          drop_ar[2];
        protected int unsigned stuck;
        protected realtime     moved_at[2];

        `uvm_component_param_utils(axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lane[A2C_DUT_LANE]   = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            void'(a2c_get_config_int(this, "a2c_lane_skew_cycles", lane_skew_cycles));
            void'(a2c_get_config_int(this, "a2c_lone_lane_cycles", lone_lane_cycles));
            for (int l = 0; l < lanes; l++) begin
                lane[l].arvalid <= 1'b0;
                lane[l].arid    <= '0;
                lane[l].araddr  <= '0;
                lane[l].arlen   <= '0;
                lane[l].arsize  <= '0;
                lane[l].arburst <= '0;
                lane[l].aruser  <= '0;
                lane[l].rready  <= 1'b0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            fork
                run_r();
            join_none
            run_ar();
        endtask

        // The response to req, with its AR fields and no beats yet.
        protected function item_t new_response(item_t req);
            item_t rsp = item_t::type_id::create("rsp");
            rsp.copy(req);
            rsp.set_id_info(req);
            rsp.data  = new[0];
            rsp.resp  = new[0];
            rsp.ruser = new[0];
            return rsp;
        endfunction

        protected function bit all_dead();
            return lanes == 2 && dead[A2C_DUT_LANE] && dead[A2C_MODEL_LANE];
        endfunction

        // Whether lane l still leads a skew: a lane that died on an earlier
        // clock leads none, so neither process's order within one time step
        // decides whether both lanes die on it.
        protected function bit counts(int l);
            return !dead[l] || died_at[l] == $realtime;
        endfunction

        protected function void drive_arvalid(bit v);
            for (int l = 0; l < lanes; l++) if (!dead[l]) lane[l].arvalid <= v;
        endfunction

        protected function bit slot_free();
            for (int l = 0; l < lanes; l++) begin
                if (!dead[l] && outstanding[l] >= cfg.max_outstanding) return 0;
            end
            return 1;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back ARs go out on consecutive clocks, and arvalid drops on
        // the first drive point with no item or no free outstanding slot on
        // some lane. An item above a non-zero max_transfer_bytes is an
        // A2C_CFG error and never reaches the bus. It completes at once with
        // a response that has no beats, so a sequence waiting on its
        // responses goes on. Once both lanes are dead an item goes on no
        // lane, and run_r() returns it with no beats.
        protected virtual task run_ar();
            item_t rsp;
            open_t b;
            forever begin
                if (!slot_free()) begin
                    drive_arvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_arvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                if (cfg.max_transfer_bytes != 0 && req.total_bytes() > cfg.max_transfer_bytes) begin
                    `uvm_error("A2C_CFG", $sformatf("%s: %s moves %0d bytes, above max_transfer_bytes %0d, so it is not driven",
                                                    cfg.port_name, req.convert2string(), req.total_bytes(),
                                                    cfg.max_transfer_bytes))
                    rsp = new_response(req);
                    seq_item_port.item_done();
                    seq_item_port.put_response(rsp);
                    continue;
                end
                repeat (req.gap) begin
                    drive_arvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                b = new();
                for (int l = 0; l < lanes; l++) begin
                    b.rsp[l] = new_response(req);
                    if (cfg.id_unbound) b.rsp[l].id = '0;
                end
                rsp = b.rsp[A2C_DUT_LANE];
                opened.push_back(b);
                for (int l = 0; l < lanes; l++) begin
                    if (dead[l]) continue;
                    pending[l][id_key_t'(rsp.id)].push_back(b);
                    outstanding[l]++;
                    lane[l].arvalid <= 1'b1;
                    lane[l].arid    <= rsp.id;
                    lane[l].araddr  <= addr_t'(req.addr);
                    lane[l].arlen   <= req.len;
                    lane[l].arsize  <= req.size;
                    lane[l].arburst <= req.burst;
                    lane[l].aruser  <= req.aruser;
                end
                wait_ar(b);
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last live lane's AR
        // transferred, at the rising edge before it. A lane whose AR has
        // transferred holds arvalid low from the next drive point on. A
        // live lane that has not taken the AR lane_skew_cycles clocks after
        // the other did is declared dead.
        protected task wait_ar(open_t b);
            int unsigned lag = 0;
            bit          all;
            bit          led;
            realtime     led_at;
            ar_cur = b;
            forever begin
                cfg.clk_vif.sample_edge();
                all = 1;
                led = 0;
                for (int l = 0; l < lanes; l++) begin
                    if (!dead[l] && lane[l].arready === 1'b1) b.ar_taken[l] = 1'b1;
                    all &= b.ar_taken[l] || dead[l];
                    led |= b.ar_taken[l] && counts(l);
                end
                if (!all && led) begin
                    if (lag == 0) led_at = $realtime;
                    if (lag == lane_skew_cycles && lane_skew_cycles != 0) begin
                        for (int l = 0; l < lanes; l++) begin
                            if (b.ar_taken[l] || dead[l]) continue;
                            declare_dead(a2c_lane_e'(l), $sformatf("the %s lane has not taken the AR of %s %0d clocks after the %s lane did",
                                                           a2c_lane_name(a2c_lane_e'(l)), b.rsp[A2C_DUT_LANE].convert2string(),
                                                           lane_skew_cycles, a2c_lane_name(a2c_lane_e'(1 - l))), led_at);
                        end
                    end
                    lag++;
                end
                cfg.clk_vif.drive_edge();
                all = 1;
                for (int l = 0; l < lanes; l++) all &= b.ar_taken[l] || dead[l];
                if (all) break;
                for (int l = 0; l < lanes; l++) begin
                    if (b.ar_taken[l] && !dead[l]) lane[l].arvalid <= 1'b0;
                end
            end
            ar_cur = null;
        endtask

        // A beat belongs to the oldest open burst of its rid on its lane. The
        // burst ends at rlast, or at its last beat when rlast is missing. The
        // monitor reports a misplaced rlast and a beat whose rid matches no
        // burst. The driver drops a beat that matches no burst.
        protected virtual task run_r();
            bit ready;
            forever begin
                ready = ($urandom_range(99, 0) < cfg.rready_pct);
                for (int l = 0; l < lanes; l++) begin
                    if (drop_ar[l]) lane[l].arvalid <= 1'b0;
                    drop_ar[l] = 0;
                    lane[l].rready <= ready && !dead[l];
                end
                while (all_dead() && opened.size() > 0) settle(opened[0]);
                cfg.clk_vif.sample_edge();
                clocks++;
                for (int l = 0; l < lanes; l++) begin
                    if (counts(l) && lane[l].rvalid === 1'b1 && lane[l].rready === 1'b1) take_beat(l);
                end
                release_skewed();
                watch_lone();
                for (int l = 0; l < lanes; l++) if (dead[l]) note_ar_transfer(l);
                cfg.clk_vif.drive_edge();
            end
        endtask

        protected function void take_beat(int l);
            id_key_t     id = id_key_t'(lane[l].rid);
            open_t       b;
            item_t       rsp;
            int unsigned n;
            if (!pending[l].exists(id) || pending[l][id].size() == 0) return;
            b   = pending[l][id][0];
            rsp = b.rsp[l];
            n   = rsp.data.size();
            rsp.data  = new[n + 1](rsp.data);
            rsp.resp  = new[n + 1](rsp.resp);
            rsp.ruser = new[n + 1](rsp.ruser);
            rsp.data[n]  = lane[l].rdata;
            rsp.resp[n]  = axi_resp_e'(lane[l].rresp);
            rsp.ruser[n] = lane[l].ruser;
            if (lane[l].rlast !== 1'b1 && n != rsp.len) return;
            void'(pending[l][id].pop_front());
            outstanding[l]--;
            b.done[l] = 1'b1;
            if (lanes == 2 && !dead[1 - l] && !b.done[1 - l]) begin
                b.first_done = clocks;
                b.first_at   = $realtime;
                skewed.push_back(b);
                return;
            end
            if (lanes == 2 && dead[1 - l]) settle_owed();
            settle(b);
        endfunction

        // Returns the bursts this lane completed that the dead lane still
        // owed, oldest first, before a later burst returns at once. take_beat()
        // can see a death that wait_ar() declared before release_skewed() has
        // returned those bursts, so without this a burst could return ahead
        // of an older one of its ID.
        protected function void settle_owed();
            for (int i = 0; i < skewed.size(); ) begin
                if (dead[skewed[i].done[A2C_DUT_LANE] ? A2C_MODEL_LANE : A2C_DUT_LANE]) settle(skewed[i]);
                else i++;
            end
        endfunction

        // Returns b to the sequence with the DUT lane's beats, or the model
        // lane's once the DUT lane is dead, or with no beats once both are.
        // A burst both lanes complete in the time step of a death reaches
        // here once from each lane's take_beat(), as does one the dying lane
        // completes after settle_owed() returned it, so b returns only once.
        protected function void settle(open_t b);
            item_t rsp = b.rsp[dead[A2C_DUT_LANE] ? A2C_MODEL_LANE : A2C_DUT_LANE];
            if (b.settled) return;
            b.settled = 1;
            foreach (opened[i]) begin
                if (opened[i] == b) begin
                    opened.delete(i);
                    break;
                end
            end
            foreach (skewed[i]) begin
                if (skewed[i] == b) begin
                    skewed.delete(i);
                    break;
                end
            end
            if (all_dead()) begin
                rsp.data  = new[0];
                rsp.resp  = new[0];
                rsp.ruser = new[0];
            end
            seq_item_port.put_response(rsp);
        endfunction

        // A burst one lane completed lane_skew_cycles clocks ago and the
        // other has not declares the other dead. A burst whose late lane is
        // dead returns at once, and one whose leading lane died earlier
        // waits for the live lane alone.
        protected function void release_skewed();
            for (int i = 0; i < skewed.size(); ) begin
                open_t     b    = skewed[i];
                a2c_lane_e lead = b.done[A2C_DUT_LANE] ? A2C_DUT_LANE : A2C_MODEL_LANE;
                a2c_lane_e late = a2c_lane_e'(1 - lead);
                if (!dead[late] && counts(lead) && lane_skew_cycles != 0 && clocks - b.first_done >= lane_skew_cycles) begin
                    declare_dead(late, $sformatf("the %s lane has not returned the last R beat of %s %0d clocks after the %s lane did",
                                         a2c_lane_name(late), b.rsp[lead].convert2string(), lane_skew_cycles,
                                         a2c_lane_name(lead)), b.first_at);
                end
                if (dead[late]) begin
                    settle(b);
                end else if (!counts(lead)) begin
                    b.first_done = -1;
                    skewed.delete(i);
                end else begin
                    i++;
                end
            end
        endfunction

        // Once one lane is dead, the other must take an AR or a beat at least
        // once every lone_lane_cycles clocks while it has an AR on the bus
        // or a burst outstanding, or it is declared dead too, so a live lane
        // that stops, perhaps waiting on the dead one, ends the run.
        protected function void watch_lone();
            int    l;
            string what;
            if (lanes != 2) return;
            for (int k = 0; k < 2; k++) if (!dead[k] && moved(k)) moved_at[k] = $realtime;
            if (lone_lane_cycles == 0 || dead[A2C_DUT_LANE] == dead[A2C_MODEL_LANE]) return;
            l = dead[A2C_DUT_LANE] ? A2C_MODEL_LANE : A2C_DUT_LANE;
            if (moved(l)) begin
                stuck = 0;
                return;
            end
            if (++stuck < lone_lane_cycles) return;
            what = "a burst";
            if (lane[l].arvalid === 1'b1 && ar_cur != null) begin
                what = {"the AR of ", ar_cur.rsp[A2C_DUT_LANE].convert2string()};
            end else begin
                foreach (opened[i]) begin
                    if (opened[i].done[l]) continue;
                    what = {"the R beats of ", opened[i].rsp[l].convert2string()};
                    break;
                end
            end
            declare_dead(a2c_lane_e'(l), $sformatf("the %s lane, alone since the %s lane died, has taken no AR and returned no R beat for %0d clocks, waiting for %s",
                                           a2c_lane_name(a2c_lane_e'(l)), a2c_lane_name(a2c_lane_e'(1 - l)), lone_lane_cycles, what),
                         moved_at[l], "lone_lane_cycles, +a2c_lone_lane_cycles",
                         $sformatf("This is likely a consequence of the earlier A2C_SKEW, which declared the %s lane dead at %0t. ",
                                   a2c_lane_name(a2c_lane_e'(1 - l)), died_at[1 - l]));
        endfunction

        // Whether lane l has nothing to wait for, or took an AR or an R beat
        // on this clock.
        protected function bit moved(int l);
            return (outstanding[l] == 0 && lane[l].arvalid !== 1'b1) || (lane[l].arvalid === 1'b1 && lane[l].arready === 1'b1)
                   || (lane[l].rvalid === 1'b1 && lane[l].rready === 1'b1);
        endfunction

        // The AR a dead lane takes at the coming rising edge is the one its
        // arvalid held, so the valid drops at the drive point after it.
        protected function void note_ar_transfer(int l);
            if (lane[l].arvalid === 1'b1 && lane[l].arready === 1'b1) drop_ar[l] = 1;
        endfunction

        // One A2C_SKEW error per lane, at its death. It names the knob that
        // bounded it, for the second death the first, and the deaths other
        // ports declared before it, since a stall of the DUT or the model
        // can spread from one port to another. From then on the lane keeps
        // an asserted arvalid and its payload until that AR transfers, holds
        // rready low, so it takes no response, and gets no new AR; the
        // master serves the sequence from the other lane alone. The rising
        // edge after the death may still move an AR or a beat on the lane,
        // and take_beat() records it. The passive agents on the port learn
        // of the death as the agent's own monitor and model_cmp do. since is
        // when the lane began to trail, which dates the death for the
        // drain's clause in other ports' reports.
        protected function void declare_dead(a2c_lane_e l, string why, realtime since,
                                             string knob = "lane_skew_cycles, +a2c_lane_skew_cycles", string cause = "");
            string fate;
            if (dead[l]) return;
            dead[l]    = 1;
            died_at[l] = $realtime;
            stuck      = 0;
            fate = dead[1 - l] ? "No lane is left, so every open and later burst returns to the sequence with no beats."
                               : {"The ", a2c_lane_name(a2c_lane_e'(1 - l)), " lane serves every burst from now on."};
            `uvm_error("A2C_SKEW", $sformatf("%s: %s (%s), so the master declares the %s lane dead%s. %s%s",
                                             cfg.port_name, why, knob, a2c_lane_name(l),
                                             a2c_replay_drain::death_context($realtime, who()), cause, fate))
            note_ar_transfer(l);
            if (cmp != null) cmp.lane_dead(l);
            if (mons[l] != null) mons[l].lane_dead();
            if (watchers[l] != null) foreach (watchers[l].mons[i]) watchers[l].mons[i].lane_dead();
            if (watchers[A2C_DUT_LANE] != null) foreach (watchers[A2C_DUT_LANE].cmps[i]) watchers[A2C_DUT_LANE].cmps[i].lane_dead(l);
            a2c_replay_drain::lane_dead(l, who(), since);
        endfunction

        // How the drain's reports name this master's port.
        protected function string who();
            return $sformatf("%s (%s)", cfg.port_name, get_full_name());
        endfunction
    endclass : axi_read_master_driver

    // A burst the slave's DUT lane chose to serve, which its model lane
    // serves next: the model lane's own AR with ar's ID that arrived idx-th
    // among that ID's ARs, counted from 0. The DUT lane adds each beat as it
    // reads it from the memory.
    class axi_read_pick #(type item_t = uvm_sequence_item, type data_t = logic [31:0]);
        item_t       ar;
        int unsigned idx;
        data_t       data[$];
        axi_resp_e   resp[$];
    endclass : axi_read_pick

    // Serves each burst from cfg.mem, in the order the ARs transfer, or with
    // cfg.reorder in any order that keeps each ID's bursts in AR order. A
    // beat is read from the memory when it first goes out and is held until
    // it transfers. In Mode B the DUT lane chooses and reads, and the model
    // lane follows.
    class axi_read_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                                  type ruser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t)) implements a2c_replay_lanes;
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                   id_key_t;
        typedef virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                                      .id_t(id_t))                      vif_t;
        typedef axi_read_pick #(item_t, data_t)                         pick_t;
        typedef a2c_replay_log #(pick_t)                                replay_t;
        localparam int unsigned DATA_BYTES = item_t::DATA_BYTES;
        localparam int unsigned FULL_SIZE  = item_t::FULL_SIZE;
        localparam bit          BYTE_LANES = item_t::BYTE_LANES;

        // A burst whose AR a lane has taken: its place among its ID's ARs on
        // that lane, the clock and the time its AR transferred, and the
        // clocks after it before its first beat may go out. A model lane
        // burst takes the delay of the DUT lane's pick.
        typedef struct {
            item_t       ar;
            int unsigned idx;
            longint      at;
            realtime     taken;
            int unsigned delay;
        } entry_t;

        axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) cfg;
        // Mode B only.
        replay_t                                                  replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // Bursts whose AR has transferred and that no lane serves yet.
        protected entry_t      queue[2][$];
        // ARs taken per ID.
        protected int unsigned arrivals[2][id_key_t];
        // The burst each lane serves, its next beat, and whether that beat
        // is on the bus.
        protected item_t       cur[2];
        protected int unsigned beat[2];
        protected bit          on_bus[2];
        // The DUT lane's pick it is serving, and the model lane's, held from
        // the replay until its burst's last beat, since its AR may not have
        // arrived yet.
        protected pick_t       dut_pick;
        protected pick_t       held;
        protected int unsigned held_delay;
        protected realtime     held_at;
        protected longint      clocks;
        protected int unsigned starts[2];
        protected int unsigned done[2];

        `uvm_component_param_utils(axi_read_slave_driver#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (cfg.model_vif == null) return;
            replay = replay_t::type_id::create("replay", this);
            replay.driver  = this;
            replay.clk_vif = cfg.clk_vif;
        endfunction

        // The index in the DUT lane's queue of the burst that goes out next,
        // or -1. A burst is ready once its delay has passed and no older
        // burst with its ID is queued. Only the oldest burst may go, unless
        // cfg.reorder lets any ready one.
        protected function int next_burst();
            int ready[$];
            for (int i = 0; i < queue[A2C_DUT_LANE].size(); i++) begin
                bit older = 0;
                if (!cfg.reorder && i != 0) break;
                for (int j = 0; j < i; j++) older |= (queue[A2C_DUT_LANE][j].ar.id === queue[A2C_DUT_LANE][i].ar.id);
                if (!older && queue[A2C_DUT_LANE][i].at + queue[A2C_DUT_LANE][i].delay <= clocks) ready.push_back(i);
            end
            if (ready.size() == 0) return -1;
            return cfg.reorder ? ready[$urandom_range(ready.size() - 1, 0)] : ready[0];
        endfunction

        // Beat n of burst ar, read from the memory: its data and response.
        protected function void read_beat(item_t ar, int unsigned n, output data_t data, output axi_resp_e resp);
            bit [8*DATA_BYTES-1:0] bytes = '0;
            bit [63:0]             first;
            int unsigned           count;
            axi_beat(64'(ar.addr), ar.size, ar.len, ar.burst, n, first, count);
            resp = AXI_OKAY;
            if (axi_in_error_range(first, cfg.error_ranges)) begin
                resp = AXI_SLVERR;
            end else begin
                for (int unsigned i = 0; i < count; i++) begin
                    int unsigned bl = int'((first + i) % (64'd1 << FULL_SIZE));
                    if (bl < DATA_BYTES) bytes[8 * bl +: 8] = cfg.mem.read(first + i);
                end
            end
            data = data_t'(bytes[$bits(data_t)-1:0]);
        endfunction

        // The DUT lane's next burst, chosen by the DUT lane alone and
        // recorded for the model lane in Mode B.
        protected function void dut_choose();
            int pick;
            if (cur[A2C_DUT_LANE] != null) return;
            pick = next_burst();
            if (pick < 0) return;
            cur[A2C_DUT_LANE]  = queue[A2C_DUT_LANE][pick].ar;
            beat[A2C_DUT_LANE] = 0;
            if (replay != null) begin
                dut_pick = new();
                dut_pick.ar  = cur[A2C_DUT_LANE];
                dut_pick.idx = queue[A2C_DUT_LANE][pick].idx;
                replay.record(dut_pick, queue[A2C_DUT_LANE][pick].delay);
            end
            queue[A2C_DUT_LANE].delete(pick);
        endfunction

        // The model lane takes the DUT lane's next pick, and serves it once
        // its own AR of that burst has arrived and the pick's delay has
        // passed since. With no pick recorded it waits, and the replay log
        // counts it as waiting only when it has an AR of its own to serve.
        protected function void model_follow();
            int found = -1;
            if (cur[A2C_MODEL_LANE] != null) return;
            if (held == null) begin
                if (queue[A2C_MODEL_LANE].size() == 0 && replay.pending() == 0) return;
                if (!replay.can_replay()) return;
                replay.replay(held, held_delay);
                held_at = $realtime;
            end
            foreach (queue[A2C_MODEL_LANE][i]) begin
                if (id_key_t'(queue[A2C_MODEL_LANE][i].ar.id) == id_key_t'(held.ar.id) && queue[A2C_MODEL_LANE][i].idx == held.idx) begin
                    found = i;
                    break;
                end
            end
            if (found < 0 || queue[A2C_MODEL_LANE][found].at + held_delay > clocks) return;
            cur[A2C_MODEL_LANE]  = queue[A2C_MODEL_LANE][found].ar;
            beat[A2C_MODEL_LANE] = 0;
            queue[A2C_MODEL_LANE].delete(found);
        endfunction

        // The model lane sends the DUT lane's beat n of the pick, and holds
        // rvalid low until the DUT lane has read it. A model burst longer
        // than the DUT lane's gets SLVERR and zero data on its extra beats,
        // and model_cmp reports the difference in arlen.
        protected function void drive_beat(int l);
            data_t     data;
            axi_resp_e resp;
            if (cur[l] == null) begin
                lane[l].rvalid <= 1'b0;
                lane[l].rlast  <= 1'b0;
                return;
            end
            if (on_bus[l]) return;
            if (l == A2C_DUT_LANE) begin
                read_beat(cur[l], beat[l], data, resp);
                if (dut_pick != null) begin
                    dut_pick.data.push_back(data);
                    dut_pick.resp.push_back(resp);
                end
            end else if (beat[l] < held.data.size()) begin
                data = held.data[beat[l]];
                resp = held.resp[beat[l]];
            end else if (beat[l] > held.ar.len) begin
                data = '0;
                resp = AXI_SLVERR;
            end else begin
                lane[l].rvalid <= 1'b0;
                lane[l].rlast  <= 1'b0;
                return;
            end
            lane[l].rvalid <= 1'b1;
            lane[l].rid    <= cur[l].id;
            lane[l].rdata  <= data;
            lane[l].rresp  <= resp;
            lane[l].rlast  <= (beat[l] == cur[l].len);
            lane[l].ruser  <= '0;
            on_bus[l] = 1;
        endfunction

        protected function void take_ar(int l);
            entry_t  e;
            id_key_t id;
            e.ar        = item_t::type_id::create("ar");
            e.ar.id     = lane[l].arid;
            e.ar.addr   = lane[l].araddr;
            e.ar.len    = lane[l].arlen;
            e.ar.size   = lane[l].arsize;
            e.ar.burst  = axi_burst_e'(lane[l].arburst);
            e.ar.aruser = lane[l].aruser;
            if (!BYTE_LANES && e.ar.size != FULL_SIZE) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s is a %0d-byte transfer on a %0d-bit bus, which carries only full-width transfers",
                                                  cfg.port_name, e.ar.convert2string(), 1 << e.ar.size, $bits(data_t)))
            end
            id = id_key_t'(e.ar.id);
            if (!arrivals[l].exists(id)) arrivals[l][id] = 0;
            e.idx   = arrivals[l][id]++;
            e.at    = clocks;
            e.taken = $realtime;
            if (l == A2C_DUT_LANE) e.delay = $urandom_range(cfg.resp_delay_max, cfg.resp_delay_min);
            queue[l].push_back(e);
            starts[l]++;
        endfunction

        // Each loop iteration starts at a drive point. A burst's first beat
        // goes out at the drive point after its AR transfers, plus its
        // response delay, and the next beat at the drive point after a beat
        // transfers. One process serves both lanes, the DUT lane first, so a
        // model lane waiting for a pick or a beat takes it at the drive
        // point the DUT lane makes it.
        virtual task run_phase(uvm_phase phase);
            bit ready;
            lane[A2C_DUT_LANE]   = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            for (int l = 0; l < lanes; l++) begin
                lane[l].arready <= 1'b0;
                lane[l].rvalid  <= 1'b0;
                lane[l].rid     <= '0;
                lane[l].rdata   <= '0;
                lane[l].rresp   <= '0;
                lane[l].rlast   <= 1'b0;
                lane[l].ruser   <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                ready = ($urandom_range(99, 0) < cfg.arready_pct);
                for (int l = 0; l < lanes; l++) lane[l].arready <= ready;
                dut_choose();
                if (lanes == 2) model_follow();
                for (int l = 0; l < lanes; l++) drive_beat(l);
                cfg.clk_vif.sample_edge();
                clocks++;
                for (int l = 0; l < lanes; l++) begin
                    if (!on_bus[l] || lane[l].rready !== 1'b1) continue;
                    on_bus[l] = 0;
                    beat[l]++;
                    if (beat[l] <= cur[l].len) continue;
                    cur[l] = null;
                    done[l]++;
                    if (l == A2C_DUT_LANE) dut_pick = null;
                    else held = null;
                end
                for (int l = 0; l < lanes; l++) begin
                    if (lane[l].arvalid === 1'b1 && lane[l].arready === 1'b1) take_ar(l);
                end
                cfg.clk_vif.drive_edge();
            end
        endtask

        virtual function bit lane_busy(a2c_lane_e l);
            return queue[l].size() != 0 || cur[l] != null || (l == A2C_MODEL_LANE && held != null);
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return done[l];
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return starts[l];
        endfunction

        // The pick the model lane holds at the end of the run without its
        // AR, or "". A pick past a cut is not owed.
        protected function string held_report();
            id_key_t id;
            string   behind = "";
            string   listed = "";
            if (replay == null || held == null || cur[A2C_MODEL_LANE] != null) return "";
            if (replay.get_cut() != 0 && done[A2C_MODEL_LANE] >= replay.get_cut()) return "";
            id = id_key_t'(held.ar.id);
            if (arrivals[A2C_MODEL_LANE].exists(id) && arrivals[A2C_MODEL_LANE][id] > held.idx) return "";
            if (queue[A2C_MODEL_LANE].size() == 0) begin
                return $sformatf("%s: the DUT lane served %s, AR %0d of ID %0h, and the model lane never issued that AR",
                                 get_full_name(), held.ar.convert2string(), held.idx + 1, held.ar.id);
            end
            if (queue[A2C_MODEL_LANE].size() > 3) listed = ", the first 3";
            for (int i = 0; i < queue[A2C_MODEL_LANE].size() && i < 3; i++) begin
                behind = {behind, (i == 0) ? "" : "; ", $sformatf("%s, AR %0d of ID %0h", queue[A2C_MODEL_LANE][i].ar.convert2string(),
                                                                  queue[A2C_MODEL_LANE][i].idx + 1, queue[A2C_MODEL_LANE][i].ar.id)};
            end
            return $sformatf("%s: the model lane holds the DUT lane's pick %s, AR %0d of ID %0h, whose AR it has not issued, with %0d ARs of its own behind it%s: %s. The model lane serves the DUT lane's picks in the DUT lane's order. Either the model never issues that AR, or it issues it only after a response that the pick holds back. In the second case the model keeps fewer ARs outstanding than the RTL, so its queuing does not match the RTL's. Fix the model: issue each AR ahead of its response, from a thread other than the one that takes the responses, with a synchLock where those threads contend. Setting reorder to 0 on this port is only a stopgap, which hides the defect and ends the port's reorder coverage",
                             get_full_name(), held.ar.convert2string(), held.idx + 1, held.ar.id, queue[A2C_MODEL_LANE].size(),
                             listed, behind);
        endfunction

        // check_phase() reports it, and the replay log's own check_phase(),
        // which runs first, must know of it.
        protected string held_why;

        virtual function void extract_phase(uvm_phase phase);
            super.extract_phase(phase);
            held_why = held_report();
            if (replay != null) replay.pick_blocked = (held_why != "");
        endfunction

        // A burst one lane issued and the other never did, and a pick the
        // model lane cannot serve. A cut run leaves its later bursts
        // unchecked, and the replay log reports the cut.
        virtual function void check_phase(uvm_phase phase);
            int unsigned extra = 0;
            entry_t      first;
            super.check_phase(phase);
            if (held_why != "") begin
                `uvm_error("A2C_REPLAY", {held_why, a2c_replay_drain::death_context(held_at)})
                return;
            end
            if (replay == null || replay.get_cut() != 0) return;
            foreach (queue[A2C_MODEL_LANE][i]) begin
                id_key_t id = id_key_t'(queue[A2C_MODEL_LANE][i].ar.id);
                if (arrivals[A2C_DUT_LANE].exists(id) && arrivals[A2C_DUT_LANE][id] > queue[A2C_MODEL_LANE][i].idx) continue;
                if (extra == 0) first = queue[A2C_MODEL_LANE][i];
                extra++;
            end
            if (extra != 0) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: the model lane issued %0d ARs the DUT lane never issued, the first %s, AR %0d of ID %0h%s",
                                                   get_full_name(), extra, first.ar.convert2string(), first.idx + 1, first.ar.id,
                                                   a2c_replay_drain::death_context(first.taken)))
            end
        endfunction
    endclass : axi_read_slave_driver

    class axi_read_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                             type ruser_t = logic, type id_t = logic [3:0]) extends uvm_monitor implements a2c_lane_watch;
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                   id_key_t;
        localparam int unsigned FULL_SIZE = item_t::FULL_SIZE;

        axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                              .id_t(id_t))                        vif;
        // One item per burst, at its last beat, with its AR fields and beats.
        uvm_analysis_port #(item_t)                               ap;
        // The replay log of the Mode B slave on this monitor's pin set, or
        // null. A run the drain cut ends with bursts open on purpose.
        a2c_replay_log_base                                       replay;
        // When the master declared this monitor's lane dead, or 0. A dead
        // lane ends the run with bursts open on purpose too.
        realtime                                                  died_at;

        // Bursts whose AR has transferred and whose last beat has not, oldest
        // first per ID.
        protected item_t open[id_key_t][$];

        `uvm_component_param_utils(axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        // The AR and R payloads, each with its valid, as one vector, so a
        // stalled transfer can be compared with the next clock.
        protected function logic [$bits(id_t)+$bits(addr_t)+13+$bits(aruser_t):0] ar_pins();
            return {vif.arvalid, vif.arid, vif.araddr, vif.arlen, vif.arsize, vif.arburst, vif.aruser};
        endfunction

        protected function logic [$bits(id_t)+$bits(data_t)+3+$bits(ruser_t):0] r_pins();
            return {vif.rvalid, vif.rid, vif.rdata, vif.rresp, vif.rlast, vif.ruser};
        endfunction

        protected function string path();
            return {get_full_name(), ".", cfg.port_name};
        endfunction

        // A stalled AR or R must hold its valid and payload until ready. R
        // is taken before AR on each clock, since a beat may not share the
        // rising edge of its own AR.
        virtual task run_phase(uvm_phase phase);
            logic [$bits(id_t)+$bits(addr_t)+13+$bits(aruser_t):0] held_ar;
            logic [$bits(id_t)+$bits(data_t)+3+$bits(ruser_t):0]   held_r;
            bit                                                    ar_stalled;
            bit                                                    r_stalled;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (r_stalled && r_pins() !== held_r) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before rready took the stalled beat", cfg.port_name,
                                                     vif.rvalid !== 1'b1 ? "rvalid dropped" : "the R payload changed"))
                end
                if (ar_stalled && ar_pins() !== held_ar) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before arready took the stalled AR", cfg.port_name,
                                                     vif.arvalid !== 1'b1 ? "arvalid dropped" : "the AR payload changed"))
                end
                r_stalled  = vif.rvalid === 1'b1 && vif.rready !== 1'b1;
                ar_stalled = vif.arvalid === 1'b1 && vif.arready !== 1'b1;
                held_r     = r_pins();
                held_ar    = ar_pins();
                if (vif.rvalid === 1'b1 && vif.rready === 1'b1) take_beat();
                if (vif.arvalid === 1'b1 && vif.arready === 1'b1) take_ar();
            end
        endtask

        protected function void take_ar();
            item_t           it = item_t::type_id::create("item");
            longint unsigned nbytes;
            it.id     = vif.arid;
            it.addr   = vif.araddr;
            it.len    = vif.arlen;
            it.size   = vif.arsize;
            it.burst  = axi_burst_e'(vif.arburst);
            it.aruser = vif.aruser;
            it.data   = new[0];
            it.resp   = new[0];
            it.ruser  = new[0];
            nbytes    = 64'd1 << it.size;
            if (vif.arburst === 2'b11) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: arburst is the reserved value 2'b11", cfg.port_name))
            end
            if (it.size > FULL_SIZE) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: arsize is wider than the %0d-bit bus", cfg.port_name,
                                                  it.convert2string(), $bits(data_t)))
            end
            if (it.burst == AXI_FIXED && it.len > 15) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: a FIXED burst is at most 16 beats", cfg.port_name,
                                                  it.convert2string()))
            end
            if (it.burst == AXI_WRAP && !(it.len inside {1, 3, 7, 15})) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: a WRAP burst is 2, 4, 8 or 16 beats", cfg.port_name,
                                                  it.convert2string()))
            end
            if (it.burst == AXI_WRAP && (64'(it.addr) & (nbytes - 1)) != 0) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: a WRAP burst starts aligned to its transfer size",
                                                  cfg.port_name, it.convert2string()))
            end
            if (it.burst == AXI_INCR && ((64'(it.addr) % 4096) & ~(nbytes - 1)) + (64'(it.len) + 1) * nbytes > 4096) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s crosses a 4 KB boundary", cfg.port_name, it.convert2string()))
            end
            open[id_key_t'(it.id)].push_back(it);
        endfunction

        // A beat belongs to the oldest open burst of its rid. The burst ends
        // at rlast, or at its last beat when rlast is missing.
        protected function void take_beat();
            id_key_t     id = id_key_t'(vif.rid);
            item_t       it;
            int unsigned n;
            bit          last;
            if (!open.exists(id) || open[id].size() == 0) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: R beat with rid %0h matches no outstanding read", cfg.port_name, id))
                return;
            end
            it = open[id][0];
            n  = it.data.size();
            it.data  = new[n + 1](it.data);
            it.resp  = new[n + 1](it.resp);
            it.ruser = new[n + 1](it.ruser);
            it.data[n]  = vif.rdata;
            it.resp[n]  = axi_resp_e'(vif.rresp);
            it.ruser[n] = vif.ruser;
            last = (n == it.len);
            `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.beat2string(n), $sformatf("%0h", it.data[n])), UVM_HIGH)
            if (vif.rlast !== last) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: rlast is %b on beat %0d of the %0d-beat burst %s", cfg.port_name,
                                                  vif.rlast, n, int'(it.len) + 1, it.convert2string()))
            end
            if (vif.rlast !== 1'b1 && !last) return;
            void'(open[id].pop_front());
            `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.convert2string(), $sformatf("%0h", it.addr)), UVM_MEDIUM)
            ap.write(it);
        endfunction

        // The master calls it when it declares this monitor's lane dead.
        virtual function void lane_dead();
            if (died_at == 0) died_at = $realtime;
        endfunction

        // Every burst must have received its last beat by the end of a run
        // the drain did not cut, on a lane the master did not declare dead.
        virtual function void check_phase(uvm_phase phase);
            int unsigned left = 0;
            string       what;
            foreach (open[id]) left += open[id].size();
            if (left == 0) return;
            what = $sformatf("%s: the run ended with %0d bursts still waiting for their last beat", cfg.port_name, left);
            if (died_at != 0) `uvm_info("A2C_PROTO", $sformatf("%s, on a lane the master declared dead at %0t (A2C_SKEW)", what, died_at), UVM_LOW)
            else if (replay != null && replay.get_cut() != 0) `uvm_info("A2C_PROTO", {what, ", after the drain cut it"}, UVM_LOW)
            else `uvm_error("A2C_PROTO", what)
        endfunction
    endclass : axi_read_monitor

    // The Mode B comparator: AXI orders bursts only within an ID, so it
    // pairs the two lanes' bursts in order per ID.
    class axi_read_comparator #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                                type ruser_t = logic, type id_t = logic [3:0])
        extends a2c_in_order_comparator #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t));
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;

        `uvm_component_param_utils(axi_read_comparator#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string key(item_t t);
            return $sformatf("%0h", t.id);
        endfunction
    endclass : axi_read_comparator

    class axi_read_agent #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                           type ruser_t = logic, type id_t = logic [3:0]) extends uvm_agent;
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t)       item_t;
        typedef axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t)     config_t;
        typedef axi_read_slave_driver#(addr_t, data_t, aruser_t, ruser_t, id_t) slave_t;
        typedef virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                                      .id_t(id_t))                              vif_t;
        typedef a2c_pin_registry #(vif_t)                                       registry_t;

        config_t                                                    cfg;
        // axi_read_master_driver for A2C_SRC, axi_read_slave_driver for A2C_DST.
        uvm_driver #(item_t)                                        drv;
        // A2C_SRC only.
        uvm_sequencer #(item_t)                                     sqr;
        axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t) mon;
        // Mode B only.
        axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t)    model_mon;
        axi_read_comparator#(addr_t, data_t, aruser_t, ruser_t, id_t) model_cmp;

        `uvm_component_param_utils(axi_read_agent#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_read_agent has no cfg")
            end
            mon = axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                model_cmp = axi_read_comparator#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_SRC) begin
                axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t) master;
                if (cfg.max_outstanding == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: max_outstanding is 0, so no burst could go out", cfg.port_name))
                end
                if (cfg.rready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: rready_pct is 0, so no burst could complete", cfg.port_name))
                end
                master = axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("drv", this);
                master.cfg = cfg;
                drv = master;
                sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
                uvm_config_db#(config_t)::set(this, "sqr", "cfg", cfg);
            end else begin
                slave_t slave;
                if (cfg.arready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: arready_pct is 0, so no AR could transfer", cfg.port_name))
                end
                if (cfg.resp_delay_min > cfg.resp_delay_max) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: resp_delay_min %0d is above resp_delay_max %0d", cfg.port_name,
                                                    cfg.resp_delay_min, cfg.resp_delay_max))
                end
                if (cfg.mem == null) cfg.mem = axi_read_mem_t::type_id::create({get_full_name(), ".mem"});
                slave = slave_t::type_id::create("drv", this);
                slave.cfg = cfg;
                drv = slave;
            end
        endfunction

        // A passive agent has no driver, and a $cast from null succeeds, so
        // the driver block needs its own guard. A passive agent joins the
        // watchers of its pin sets. An active Mode B agent marks its DUT
        // lane's pin set as its own and hands the watchers to its master or
        // its slave's replay log.
        virtual function void connect_phase(uvm_phase phase);
            slave_t slave;
            axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t) master;
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
            end
            if (drv == null) begin
                registry_t::of(cfg.vif).mons.push_back(mon);
                if (model_cmp == null) return;
                registry_t::of(cfg.model_vif).mons.push_back(model_mon);
                registry_t::of(cfg.vif).cmps.push_back(model_cmp);
                return;
            end
            if (model_cmp == null) return;
            registry_t::of(cfg.vif).owner = get_full_name();
            if ($cast(master, drv)) begin
                master.cmp                      = model_cmp;
                master.mons[A2C_DUT_LANE]       = mon;
                master.mons[A2C_MODEL_LANE]     = model_mon;
                master.watchers[A2C_DUT_LANE]   = registry_t::of(cfg.vif);
                master.watchers[A2C_MODEL_LANE] = registry_t::of(cfg.model_vif);
            end
            if ($cast(slave, drv) && slave.replay != null) begin
                slave.replay.cmp                  = model_cmp;
                slave.replay.watchers             = registry_t::of(cfg.vif);
                registry_t::of(cfg.vif).log       = slave.replay;
                registry_t::of(cfg.model_vif).log = slave.replay;
                mon.replay                        = slave.replay;
                model_mon.replay                  = slave.replay;
            end
        endfunction

        // A passive agent's monitors read the cut from the replay log of the
        // active slave on their pin sets, which has registered by now. With
        // no such log a monitor keeps the replay a hand-written env gave it.
        virtual function void end_of_elaboration_phase(uvm_phase phase);
            super.end_of_elaboration_phase(phase);
            if (drv != null) return;
            if (registry_t::of(cfg.vif).log != null) mon.replay = registry_t::of(cfg.vif).log;
            if (model_mon == null) return;
            if (registry_t::of(cfg.model_vif).log != null) model_mon.replay = registry_t::of(cfg.model_vif).log;
            registry_t::note_unowned(cfg.vif, this, cfg.port_name);
        endfunction
    endclass : axi_read_agent

endpackage : axi_read_uvm_pkg

`endif // AXI_READ_UVM_PKG_SV
