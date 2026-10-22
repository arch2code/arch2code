`ifndef AXI_WRITE_UVM_PKG_SV
`define AXI_WRITE_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for axi_write_if: an AXI4 write master driver for the A2C_SRC
// role, a slave driver for the A2C_DST role, and a monitor. AMBA 5 calls the
// two sides Manager and Subordinate. One item is one burst with its data
// beats. The type parameters and the defaults of the optional ones are the
// interface's.
//
// The master drives AW, W and B independently: it calls item_done() once the
// burst's AW transfers, so up to cfg.max_outstanding bursts are in flight,
// and returns each burst with put_response() when its B arrives. A burst's
// first W beat goes out no earlier than its AW, and W bursts follow AW order.
// A sequence extends axi_write_base_seq to receive the responses.
//
// The slave writes bursts to cfg.mem, an a2c_mem_model of bytes at byte
// addresses, and answers with B in the order the AWs transfer, whatever their
// ID, or with cfg.reorder in any order that keeps each ID's bursts in AW
// order. It takes W beats before their AW and holds them until the AW
// arrives.
// Byte X of a beat sits on bus byte lane X % (1 << FULL_SIZE), as the AXI
// address rules place it, and is written only when its wstrb bit is set.
//
// wstrb has one bit per byte lane, so the agent needs $bits(data_t) to be
// 8 * $bits(strb_t) and stops at build with A2C_CFG otherwise. A bus that is
// not a power-of-two number of whole bytes carries only full-width transfers.
//
// Pin timing follows a2c_clk_if: drive at drive_edge(), sample at
// sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon, and model_cmp, an
// axi_write_comparator, compares the bursts the two lanes report in order per
// ID: AW fields, every beat's wdata, wstrb and wuser, and bresp and buser.
// The master puts each AW on both lanes at one drive point, each lane drops
// awvalid once its own AW has transferred, and the next item starts when both
// have; up to cfg.max_outstanding bursts are in flight on each lane. Each W
// beat goes out on both lanes at one drive point, a lane that has taken it
// drops wvalid, and the next beat goes out once both lanes have taken it.
// bready has the same level on both lanes. A burst's response returns once
// both lanes have its B, with the DUT lane's bresp and buser. A lane that
// trails the other by lane_skew_cycles clocks on a burst's AW, a W beat or
// its B is declared dead in one A2C_SKEW error
// (axi_write_master_driver::declare_dead()), and the master serves the
// sequence from the other lane alone from then on. The slave serves both
// lanes from the one cfg.mem, and each lane pairs its own W beats with its
// own AWs, before or after them. Only the DUT lane writes the memory. It
// chooses each B it sends and records it in its replay log; the model lane
// never chooses and never writes. It sends the DUT lane's B picks in order,
// each for its own burst with the same ID and the same place among that ID's
// AWs, once that burst's W has ended and the delay the DUT lane drew has
// passed, with the DUT lane's bresp. A model lane that leads waits for the
// DUT lane's pick. Since the model lane follows the DUT lane's order, the
// model must keep as many bursts outstanding as the RTL. One that holds a
// burst back until an earlier B leaves the model lane holding a pick, a
// model defect the slave reports. awready and wready have the same level on
// both lanes. A burst one lane issues and the other never does is an
// A2C_REPLAY error at the end of the run. The replay log holds the end of the
// run phase while the model lane catches up (a2c_replay_drain). A passive
// agent on either pin set learns of a death and of a cut through
// a2c_pin_registry. What the DUT produces that is not compared:
//   DUT axi_write dst port, A2C_SRC master: channel timing, order across IDs
//   DUT axi_write src port, A2C_DST slave: none
package axi_write_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class axi_write_item #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                           type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                           type id_t = logic [3:0]) extends uvm_sequence_item;
        localparam int unsigned ADDR_W     = $bits(addr_t);
        localparam int unsigned STRB_W     = $bits(strb_t);
        localparam int unsigned DATA_BYTES = ($bits(data_t) + 7) / 8;
        // awsize of a full-width beat.
        localparam int unsigned FULL_SIZE  = $clog2(DATA_BYTES);
        // Narrow transfers need a bus of a power-of-two number of whole bytes.
        localparam bit          BYTE_LANES = ($bits(data_t) % 8 == 0) && (DATA_BYTES == (1 << FULL_SIZE));
        // An INCR burst stays within one 4 KB page, or within the address
        // space when that is smaller.
        localparam longint unsigned PAGE   = (ADDR_W < 12) ? (64'd1 << ADDR_W) : 64'd4096;

        // A strobe as bits, so constraints and lane masks can work on it.
        typedef bit [STRB_W-1:0] strb_bits_t;

        rand bit [ADDR_W-1:0] addr;
        rand id_t             id;
        rand bit [7:0]        len;
        rand bit [2:0]        size;
        rand axi_burst_e      burst;
        rand awuser_t         awuser;
        // One entry per beat: wdata, wstrb and wuser.
        rand data_t           data[];
        rand strb_bits_t      strb[];
        rand wuser_t          wuser[];
        // Filled from B.
        axi_resp_e            resp;
        buser_t               buser;
        // src role: idle clocks (awvalid low) the master inserts before this AW.
        int unsigned          gap;
        // Bytes the burst may move, (len + 1) << size; 0 means no limit.
        // axi_write_base_seq::new_item() sets it from the port's config.
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

        // A strobe may set only the lanes its beat carries.
        constraint c_beats {
            data.size()  == int'(len) + 1;
            strb.size()  == int'(len) + 1;
            wuser.size() == int'(len) + 1;
            foreach (strb[i]) (strb[i] & ~beat_lanes(addr, size, len, burst, i)) == 0;
        }

        `uvm_object_param_utils(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name = "axi_write_item");
            super.new(name);
        endfunction

        function int unsigned total_bytes();
            return (int'(len) + 1) << size;
        endfunction

        // The byte lanes beat n of a burst carries.
        function strb_bits_t beat_lanes(bit [ADDR_W-1:0] start, bit [2:0] beat_size, bit [7:0] beat_len,
                                        bit [1:0] beat_burst, int unsigned n);
            bit [63:0]   first;
            int unsigned count;
            strb_bits_t  lanes = '0;
            axi_beat(64'(start), beat_size, beat_len, beat_burst, n, first, count);
            for (int unsigned i = 0; i < count; i++) begin
                int unsigned lane = int'((first + i) % (64'd1 << FULL_SIZE));
                if (lane < STRB_W) lanes[lane] = 1'b1;
            end
            return lanes;
        endfunction

        virtual function void do_copy(uvm_object rhs);
            axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            addr               = rhs_.addr;
            id                 = rhs_.id;
            len                = rhs_.len;
            size               = rhs_.size;
            burst              = rhs_.burst;
            awuser             = rhs_.awuser;
            data               = rhs_.data;
            strb               = rhs_.strb;
            wuser              = rhs_.wuser;
            resp               = rhs_.resp;
            buser              = rhs_.buser;
            gap                = rhs_.gap;
            max_transfer_bytes = rhs_.max_transfer_bytes;
        endfunction

        // gap and max_transfer_bytes shape the stimulus, so they take no
        // part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            if (!super.do_compare(rhs, comparer)) return 0;
            if (addr !== rhs_.addr || id !== rhs_.id || len !== rhs_.len || size !== rhs_.size ||
                burst !== rhs_.burst || awuser !== rhs_.awuser || resp !== rhs_.resp || buser !== rhs_.buser) return 0;
            if (data.size() != rhs_.data.size() || strb.size() != rhs_.strb.size() ||
                wuser.size() != rhs_.wuser.size()) return 0;
            foreach (data[i]) if (data[i] !== rhs_.data[i]) return 0;
            foreach (strb[i]) if (strb[i] !== rhs_.strb[i]) return 0;
            foreach (wuser[i]) if (wuser[i] !== rhs_.wuser[i]) return 0;
            return 1;
        endfunction

        virtual function string convert2string();
            return $sformatf("id=%0h addr=%0h len=%0d size=%0d burst=%s awuser=%0h beats=%0d bresp=%s buser=%0h", id, addr,
                             len, size, burst.name(), awuser, data.size(), resp.name(), buser);
        endfunction

        function string beat2string(int unsigned n);
            return $sformatf("id=%0h beat %0d of %0d wdata=%p wstrb=%0h wuser=%0h", id, n, int'(len) + 1, data[n],
                             strb[n], wuser[n]);
        endfunction
    endclass : axi_write_item

    // The slave's memory: one byte per byte address.
    typedef a2c_mem_model #(bit [7:0]) axi_write_mem_t;

    class axi_write_config #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                             type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                             type id_t = logic [3:0]) extends uvm_object;
        virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                               .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                               .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t)) model_vif;
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
        // burst with ID 0, and the monitor does not compare wid with awid.
        bit                                 id_unbound = 0;
        // A2C_SRC role: bursts whose AW has gone out and whose B has not
        // arrived, and the percentage of clocks with bready high.
        int unsigned                        max_outstanding = 1;
        int unsigned                        bready_pct = 100;
        // A2C_DST role. The agent creates mem when the test leaves it null.
        // awready and wready are high on awready_pct and wready_pct percent
        // of clocks. Each burst draws a delay of resp_delay_min to
        // resp_delay_max clocks, counted from the clock its AW and last W
        // have both transferred, before its B may go out. A burst's B still
        // waits for the B of every burst ahead of it, or with reorder only
        // for the bursts ahead of it with its ID. A burst with a beat whose
        // address falls in an error range gets SLVERR and writes nothing.
        axi_write_mem_t                     mem;
        int unsigned                        awready_pct = 100;
        int unsigned                        wready_pct = 100;
        int unsigned                        resp_delay_min = 0;
        int unsigned                        resp_delay_max = 0;
        bit                                 reorder = 0;
        axi_addr_range_t                    error_ranges[$];

        `uvm_object_param_utils(axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name = "axi_write_config");
            super.new(name);
        endfunction
    endclass : axi_write_config

    // The sequence an A2C_SRC test extends. The master returns each burst
    // with its B as a response after item_done(); use_response_handler keeps
    // those responses out of the sequence's response queue, which would
    // otherwise overflow. send() counts the bursts, write_done() sees each
    // response, and wait_for_writes() holds body() until every burst has
    // returned, since a response to a sequence that has ended is dropped.
    // A response with no beats is an item the master refused, and its resp
    // and buser mean nothing. new_item() gives an item whose constraints keep
    // it within the port's max_transfer_bytes.
    class axi_write_base_seq #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                               type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                               type id_t = logic [3:0])
        extends uvm_sequence #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t));
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)   item_t;
        typedef axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) config_t;

        protected int unsigned writes_sent;
        protected int unsigned writes_done;
        protected config_t     cfg;

        `uvm_object_param_utils(axi_write_base_seq#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name = "axi_write_base_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        // The agent publishes its config to its sequencer, so this works once
        // the sequence has a sequencer.
        function item_t new_item(string name = "item");
            item_t it = item_t::type_id::create(name);
            if (cfg == null && !uvm_config_db#(config_t)::get(m_sequencer, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_write_base_seq: the sequencer has no axi_write config")
            end
            it.max_transfer_bytes = cfg.max_transfer_bytes;
            return it;
        endfunction

        task send(item_t it);
            start_item(it);
            finish_item(it);
            writes_sent++;
        endtask

        task wait_for_writes();
            wait (writes_done >= writes_sent);
        endtask

        // Called once per burst, with the request's fields and beats and the
        // B response.
        virtual function void write_done(item_t rsp);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
            item_t rsp;
            $cast(rsp, response);
            writes_done++;
            write_done(rsp);
        endfunction
    endclass : axi_write_base_seq

    // One burst of the master, built when its AW goes out, because a
    // sequence may reuse the request object for its next item. Indexed by
    // lane: the response that takes the lane's B, whether its AW
    // transferred, and whether its B has. first_done is the clock the first
    // lane's B arrived on, or -1, and first_at its time. settled is set once
    // the burst has returned to the sequence.
    class axi_write_open #(type item_t = uvm_sequence_item);
        item_t   rsp[2];
        bit      aw_taken[2];
        bit      done[2];
        longint  first_done = -1;
        realtime first_at;
        bit      settled;
    endclass : axi_write_open

    typedef class axi_write_monitor;

    class axi_write_master_driver #(type addr_t = logic [31:0], type data_t = logic [31:0],
                                    type strb_t = logic [3:0], type awuser_t = logic, type wuser_t = logic,
                                    type buser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t));
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                                      id_key_t;
        typedef virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                                       .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t))  vif_t;
        typedef axi_write_open #(item_t)                                                   open_t;

        axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) cfg;
        // Mode B: the agent's model_cmp and its two monitors, indexed by
        // a2c_lane_e, which the master tells of a dead lane.
        a2c_comparator_base                                                          cmp;
        axi_write_monitor#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) mons[2];
        // The passive agents on each lane's pin set, indexed by a2c_lane_e.
        a2c_pin_watchers                                                             watchers[2];

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // Mode B: the clocks a lane may trail the other on a burst's AW, one
        // of its W beats or its B before the master declares it dead, and,
        // once the other lane is dead, the clocks the live lane may go
        // without an AW, a W beat or a B while it has one to take; 0 turns
        // either rule off. a2c_lane_skew_cycles and a2c_lone_lane_cycles in
        // the uvm_config_db set them. They are independent: a lone lane's
        // stall is a slave's latency or the DUT's backpressure, which a tight
        // skew bound does not limit.
        int unsigned           lane_skew_cycles = 200000;
        int unsigned           lone_lane_cycles = 200000;

        // Bursts waiting for their B on each live lane, oldest first per ID;
        // the bursts waiting for their W beats, in AW order; every burst not
        // yet returned, in AW order; the bursts one lane has a B for and the
        // other has not, in the order the first B arrived; and the clocks
        // run_b() has counted.
        protected open_t       pending[2][id_key_t][$];
        protected open_t       w_queue[$];
        protected int unsigned outstanding[2];
        protected open_t       opened[$];
        protected open_t       skewed[$];
        protected longint      clocks;
        // The burst whose AW is on the bus, and the burst and beat run_w()
        // drives, or null.
        protected open_t       aw_cur;
        protected open_t       w_cur;
        protected int unsigned w_beat;
        // A dead lane is never driven or read again, apart from an awvalid
        // or wvalid it had raised, which drops at the drive point after that
        // AW or beat transfers. stuck counts the clocks the one live lane
        // has gone without progress, and moved_at is when each lane last
        // made progress.
        protected bit          dead[2];
        protected realtime     died_at[2];
        protected bit          drop_aw[2];
        protected bit          drop_w[2];
        protected int unsigned stuck;
        protected realtime     moved_at[2];

        `uvm_component_param_utils(axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

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
                lane[l].awvalid <= 1'b0;
                lane[l].awid    <= '0;
                lane[l].awaddr  <= '0;
                lane[l].awlen   <= '0;
                lane[l].awsize  <= '0;
                lane[l].awburst <= '0;
                lane[l].awuser  <= '0;
                lane[l].wvalid  <= 1'b0;
                lane[l].wid     <= '0;
                lane[l].wdata   <= '0;
                lane[l].wstrb   <= '0;
                lane[l].wlast   <= 1'b0;
                lane[l].wuser   <= '0;
                lane[l].bready  <= 1'b0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            fork
                run_w();
                run_b();
            join_none
            run_aw();
        endtask

        // The response to req, with its AW fields and beats and no B yet.
        protected function item_t new_response(item_t req);
            item_t rsp = item_t::type_id::create("rsp");
            rsp.copy(req);
            rsp.set_id_info(req);
            rsp.resp  = AXI_OKAY;
            rsp.buser = '0;
            return rsp;
        endfunction

        // rsp with its beats removed, as for a burst that never reached the
        // bus.
        protected function item_t no_beats(item_t rsp);
            rsp.data  = new[0];
            rsp.strb  = new[0];
            rsp.wuser = new[0];
            return rsp;
        endfunction

        // Why req cannot go on the bus, or "" when it can.
        protected function string refusal(item_t req);
            int unsigned beats = int'(req.len) + 1;
            if (req.data.size() != beats || req.strb.size() != beats || req.wuser.size() != beats) begin
                return $sformatf("has %0d data, %0d strobe and %0d wuser entries for %0d beats", req.data.size(),
                                 req.strb.size(), req.wuser.size(), beats);
            end
            if (cfg.max_transfer_bytes != 0 && req.total_bytes() > cfg.max_transfer_bytes) begin
                return $sformatf("moves %0d bytes, above max_transfer_bytes %0d", req.total_bytes(),
                                 cfg.max_transfer_bytes);
            end
            return "";
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

        protected function void drive_awvalid(bit v);
            for (int l = 0; l < lanes; l++) if (!dead[l]) lane[l].awvalid <= v;
        endfunction

        protected function bit slot_free();
            for (int l = 0; l < lanes; l++) begin
                if (!dead[l] && outstanding[l] >= cfg.max_outstanding) return 0;
            end
            return 1;
        endfunction

        // The burst for req, with one response per lane.
        protected function open_t new_open(item_t req);
            open_t b = new();
            for (int l = 0; l < lanes; l++) begin
                b.rsp[l] = new_response(req);
                if (cfg.id_unbound) b.rsp[l].id = '0;
            end
            return b;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back AWs go out on consecutive clocks, and awvalid drops on
        // the first drive point with no item or no free outstanding slot on
        // some lane. An item above a non-zero max_transfer_bytes, or without
        // one data, strobe and wuser entry per beat, is an A2C_CFG error and
        // never reaches the bus. It completes at once with a response that
        // has no beats, so a sequence waiting on its responses goes on. Once
        // both lanes are dead an item goes on no lane, and run_b() returns it
        // with no beats.
        protected virtual task run_aw();
            item_t rsp;
            open_t b;
            string why;
            forever begin
                if (!slot_free()) begin
                    drive_awvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_awvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                why = refusal(req);
                if (why != "") begin
                    `uvm_error("A2C_CFG", $sformatf("%s: %s %s, so it is not driven", cfg.port_name,
                                                    req.convert2string(), why))
                    seq_item_port.item_done();
                    seq_item_port.put_response(no_beats(new_response(req)));
                    continue;
                end
                repeat (req.gap) begin
                    drive_awvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                b   = new_open(req);
                rsp = b.rsp[A2C_DUT_LANE];
                w_queue.push_back(b);
                opened.push_back(b);
                for (int l = 0; l < lanes; l++) begin
                    if (dead[l]) continue;
                    pending[l][id_key_t'(rsp.id)].push_back(b);
                    outstanding[l]++;
                    lane[l].awvalid <= 1'b1;
                    lane[l].awid    <= rsp.id;
                    lane[l].awaddr  <= addr_t'(req.addr);
                    lane[l].awlen   <= req.len;
                    lane[l].awsize  <= req.size;
                    lane[l].awburst <= req.burst;
                    lane[l].awuser  <= req.awuser;
                end
                wait_aw(b);
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last live lane's AW
        // transferred, at the rising edge before it. A lane whose AW has
        // transferred holds awvalid low from the next drive point on. A
        // live lane that has not taken the AW lane_skew_cycles clocks after
        // the other did is declared dead.
        protected task wait_aw(open_t b);
            int unsigned lag = 0;
            bit          all;
            bit          led;
            realtime     led_at;
            aw_cur = b;
            forever begin
                cfg.clk_vif.sample_edge();
                all = 1;
                led = 0;
                for (int l = 0; l < lanes; l++) begin
                    if (!dead[l] && lane[l].awready === 1'b1) b.aw_taken[l] = 1'b1;
                    all &= b.aw_taken[l] || dead[l];
                    led |= b.aw_taken[l] && counts(l);
                end
                if (!all && led) begin
                    if (lag == 0) led_at = $realtime;
                    if (lag == lane_skew_cycles && lane_skew_cycles != 0) begin
                        for (int l = 0; l < lanes; l++) begin
                            if (b.aw_taken[l] || dead[l]) continue;
                            declare_dead(a2c_lane_e'(l), $sformatf("the %s lane has not taken the AW of %s %0d clocks after the %s lane did",
                                                           a2c_lane_name(a2c_lane_e'(l)), b.rsp[A2C_DUT_LANE].convert2string(),
                                                           lane_skew_cycles, a2c_lane_name(a2c_lane_e'(1 - l))), led_at);
                        end
                    end
                    lag++;
                end
                cfg.clk_vif.drive_edge();
                all = 1;
                for (int l = 0; l < lanes; l++) all &= b.aw_taken[l] || dead[l];
                if (all) break;
                for (int l = 0; l < lanes; l++) begin
                    if (b.aw_taken[l] && !dead[l]) lane[l].awvalid <= 1'b0;
                end
            end
            aw_cur = null;
        endtask

        // A burst joins w_queue at the drive point that raises its awvalid,
        // so its first beat goes out at that drive point or a later one.
        // wlast marks beat len. A lane that has taken the beat holds wvalid
        // low until every other live lane has taken it too. A live lane that
        // has not taken a beat lane_skew_cycles clocks after the other did
        // is declared dead.
        protected virtual task run_w();
            bit          taken[2];
            bit          all;
            bit          led;
            int unsigned lag;
            realtime     led_at;
            forever begin
                if (w_cur == null && w_queue.size() != 0) begin
                    w_cur  = w_queue.pop_front();
                    w_beat = 0;
                    lag    = 0;
                end
                for (int l = 0; l < lanes; l++) begin
                    if (dead[l]) begin
                        if (drop_w[l]) lane[l].wvalid <= 1'b0;
                        drop_w[l] = 0;
                    end else if (w_cur != null && !taken[l]) begin
                        lane[l].wvalid <= 1'b1;
                        lane[l].wid    <= w_cur.rsp[A2C_DUT_LANE].id;
                        lane[l].wdata  <= w_cur.rsp[A2C_DUT_LANE].data[w_beat];
                        lane[l].wstrb  <= strb_t'(w_cur.rsp[A2C_DUT_LANE].strb[w_beat]);
                        lane[l].wlast  <= (w_beat == w_cur.rsp[A2C_DUT_LANE].len);
                        lane[l].wuser  <= w_cur.rsp[A2C_DUT_LANE].wuser[w_beat];
                    end else begin
                        lane[l].wvalid <= 1'b0;
                        lane[l].wlast  <= 1'b0;
                    end
                end
                cfg.clk_vif.sample_edge();
                if (w_cur != null) begin
                    all = 1;
                    led = 0;
                    for (int l = 0; l < lanes; l++) begin
                        if (!dead[l] && lane[l].wready === 1'b1) taken[l] = 1'b1;
                        all &= taken[l] || dead[l];
                        led |= taken[l] && counts(l);
                    end
                    if (!all && led) begin
                        if (lag == 0) led_at = $realtime;
                        if (lag == lane_skew_cycles && lane_skew_cycles != 0) begin
                            for (int l = 0; l < lanes; l++) begin
                                if (taken[l] || dead[l]) continue;
                                declare_dead(a2c_lane_e'(l), $sformatf("the %s lane has not taken W beat %0d of %s %0d clocks after the %s lane did",
                                                               a2c_lane_name(a2c_lane_e'(l)), w_beat,
                                                               w_cur.rsp[A2C_DUT_LANE].convert2string(), lane_skew_cycles,
                                                               a2c_lane_name(a2c_lane_e'(1 - l))), led_at);
                            end
                        end
                        lag++;
                    end
                    all = 1;
                    for (int l = 0; l < lanes; l++) all &= taken[l] || dead[l];
                    if (all) begin
                        taken  = '{default: 1'b0};
                        lag    = 0;
                        w_beat++;
                        if (w_beat > w_cur.rsp[A2C_DUT_LANE].len) w_cur = null;
                    end
                end
                for (int l = 0; l < lanes; l++) if (dead[l]) note_w_transfer(l);
                cfg.clk_vif.drive_edge();
            end
        endtask

        protected virtual task run_b();
            bit ready;
            forever begin
                ready = ($urandom_range(99, 0) < cfg.bready_pct);
                for (int l = 0; l < lanes; l++) begin
                    if (drop_aw[l]) lane[l].awvalid <= 1'b0;
                    drop_aw[l] = 0;
                    lane[l].bready <= ready && !dead[l];
                end
                while (all_dead() && opened.size() > 0) settle(opened[0]);
                cfg.clk_vif.sample_edge();
                clocks++;
                b_sampled();
                for (int l = 0; l < lanes; l++) begin
                    if (counts(l) && lane[l].bvalid === 1'b1 && lane[l].bready === 1'b1) take_b(l);
                end
                release_skewed();
                watch_lone();
                for (int l = 0; l < lanes; l++) if (dead[l]) note_aw_transfer(l);
                cfg.clk_vif.drive_edge();
            end
        endtask

        // Runs at each falling edge before run_b() takes the Bs, and is
        // empty here. A subclass may put off the take within this time step,
        // for instance until the other processes of the edge have run. It
        // must not let time advance, since run_b() would then read the pins
        // of a later clock.
        protected virtual task b_sampled();
        endtask

        // A B completes the oldest outstanding burst of its bid on its lane.
        // The monitor reports a B whose bid matches no burst and a B before
        // its burst's last W. The driver drops a B that matches no burst.
        protected function void take_b(int l);
            id_key_t id = id_key_t'(lane[l].bid);
            open_t   b;
            if (!pending[l].exists(id) || pending[l][id].size() == 0) return;
            b = pending[l][id].pop_front();
            outstanding[l]--;
            b.rsp[l].resp  = axi_resp_e'(lane[l].bresp);
            b.rsp[l].buser = lane[l].buser;
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

        // Returns the bursts this lane has a B for that the dead lane still
        // owed, oldest first, before a later burst returns at once. take_b()
        // can see a death that wait_aw() or run_w() declared before
        // release_skewed() has returned those bursts, so without this a
        // burst could return ahead of an older one of its ID.
        protected function void settle_owed();
            for (int i = 0; i < skewed.size(); ) begin
                if (dead[skewed[i].done[A2C_DUT_LANE] ? A2C_MODEL_LANE : A2C_DUT_LANE]) settle(skewed[i]);
                else i++;
            end
        endfunction

        // Returns b to the sequence with the DUT lane's bresp and buser, or
        // the model lane's once the DUT lane is dead, or with no beats once
        // both are. A burst both lanes complete in the time step of a death
        // reaches here once from each lane's take_b(), as does one the dying
        // lane completes after settle_owed() returned it, so b returns only
        // once.
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
            seq_item_port.put_response(all_dead() ? no_beats(rsp) : rsp);
        endfunction

        // A burst one lane has had its B for lane_skew_cycles clocks and the
        // other has not declares the other dead. A burst whose late lane is
        // dead returns at once, and one whose leading lane died earlier
        // waits for the live lane alone.
        protected function void release_skewed();
            for (int i = 0; i < skewed.size(); ) begin
                open_t     b    = skewed[i];
                a2c_lane_e lead = b.done[A2C_DUT_LANE] ? A2C_DUT_LANE : A2C_MODEL_LANE;
                a2c_lane_e late = a2c_lane_e'(1 - lead);
                if (!dead[late] && counts(lead) && lane_skew_cycles != 0 && clocks - b.first_done >= lane_skew_cycles) begin
                    declare_dead(late, $sformatf("the %s lane has not returned the B of %s %0d clocks after the %s lane did",
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

        // Once one lane is dead, the other must take an AW or a W beat or
        // return a B at least once every lone_lane_cycles clocks while it
        // has an AW or a beat on the bus or a burst outstanding, or it is
        // declared dead too, so a live lane that stops, perhaps waiting on
        // the dead one, ends the run.
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
            if (lane[l].awvalid === 1'b1 && aw_cur != null) begin
                what = {"the AW of ", aw_cur.rsp[A2C_DUT_LANE].convert2string()};
            end else if (lane[l].wvalid === 1'b1 && w_cur != null) begin
                what = $sformatf("W beat %0d of %s", w_beat, w_cur.rsp[A2C_DUT_LANE].convert2string());
            end else begin
                foreach (opened[i]) begin
                    if (opened[i].done[l]) continue;
                    what = {"the B of ", opened[i].rsp[A2C_DUT_LANE].convert2string()};
                    break;
                end
            end
            declare_dead(a2c_lane_e'(l), $sformatf("the %s lane, alone since the %s lane died, has taken no AW and no W beat and returned no B for %0d clocks, waiting for %s",
                                           a2c_lane_name(a2c_lane_e'(l)), a2c_lane_name(a2c_lane_e'(1 - l)), lone_lane_cycles, what),
                         moved_at[l], "lone_lane_cycles, +a2c_lone_lane_cycles",
                         $sformatf("This is likely a consequence of the earlier A2C_SKEW, which declared the %s lane dead at %0t. ",
                                   a2c_lane_name(a2c_lane_e'(1 - l)), died_at[1 - l]));
        endfunction

        // Whether lane l has nothing to wait for, or took an AW or a W beat
        // or returned a B on this clock.
        protected function bit moved(int l);
            return (outstanding[l] == 0 && lane[l].awvalid !== 1'b1 && lane[l].wvalid !== 1'b1)
                   || (lane[l].awvalid === 1'b1 && lane[l].awready === 1'b1)
                   || (lane[l].wvalid === 1'b1 && lane[l].wready === 1'b1)
                   || (lane[l].bvalid === 1'b1 && lane[l].bready === 1'b1);
        endfunction

        // The AW or W beat a dead lane takes at the coming rising edge is the
        // one its valid held, so the valid drops at the drive point after it.
        protected function void note_aw_transfer(int l);
            if (lane[l].awvalid === 1'b1 && lane[l].awready === 1'b1) drop_aw[l] = 1;
        endfunction

        protected function void note_w_transfer(int l);
            if (lane[l].wvalid === 1'b1 && lane[l].wready === 1'b1) drop_w[l] = 1;
        endfunction

        // One A2C_SKEW error per lane, at its death. It names the knob that
        // bounded it, for the second death the first, and the deaths other
        // ports declared before it, since a stall of the DUT or the model
        // can spread from one port to another. From then on the lane keeps
        // an asserted awvalid or wvalid and its payload until that AW or
        // beat transfers, holds bready low, so it takes no B, and gets no
        // new AW or beat; the master serves the sequence from the other lane
        // alone. The rising edge after the death may still move an AW, a W
        // beat or a B on the lane, and take_b() records a B. The passive
        // agents on the port learn of the death as the agent's own monitor
        // and model_cmp do. since is when the lane began to trail, which
        // dates the death for the drain's clause in other ports' reports.
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
            note_aw_transfer(l);
            note_w_transfer(l);
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
    endclass : axi_write_master_driver

    // A B the slave's DUT lane chose to send, which its model lane sends
    // next: for the model lane's own burst with aw's ID that arrived idx-th
    // among that ID's AWs, counted from 0, with aw's bresp.
    class axi_write_pick #(type item_t = uvm_sequence_item);
        item_t       aw;
        int unsigned idx;
    endclass : axi_write_pick

    // Writes each burst to cfg.mem once its AW and its last W have both
    // transferred, and answers with B in the order the AWs transfer, or with
    // cfg.reorder in any order that keeps each ID's bursts in AW order. W beats
    // belong to the AWs in order, whether they come before or after the AW.
    // A burst's W ends at wlast, or at its last beat when wlast is missing.
    // In Mode B the DUT lane writes and chooses, and the model lane follows.
    class axi_write_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0],
                                   type strb_t = logic [3:0], type awuser_t = logic, type wuser_t = logic,
                                   type buser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))
        implements a2c_replay_lanes;
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;
        typedef item_t::strb_bits_t                                                        strb_bits_t;
        typedef bit [$bits(id_t)-1:0]                                                      id_key_t;
        typedef virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                                       .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t))  vif_t;
        typedef axi_write_pick #(item_t)                                                   pick_t;
        typedef a2c_replay_log #(pick_t)                                                   replay_t;
        localparam int unsigned DATA_BYTES = item_t::DATA_BYTES;
        localparam int unsigned FULL_SIZE  = item_t::FULL_SIZE;
        localparam bit          BYTE_LANES = item_t::BYTE_LANES;

        typedef struct {
            data_t      data;
            strb_bits_t strb;
            wuser_t     wuser;
            logic       last;
        } w_beat_t;

        // A burst whose AW a lane has taken: its place among its ID's AWs on
        // that lane, the time its AW transferred, the clock its W ended, and
        // the clocks after that before its B may go out. A model lane burst
        // takes the delay of the DUT lane's pick.
        typedef struct {
            item_t       aw;
            int unsigned idx;
            realtime     taken;
            longint      at;
            int unsigned delay;
        } entry_t;

        axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) cfg;
        // Mode B only.
        replay_t                                                                    replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // Bursts whose W has not ended, in AW order; W beats no AW has
        // claimed yet; and bursts whose W has ended and whose B has not gone
        // out.
        protected entry_t      aw_queue[2][$];
        protected w_beat_t     w_queue[2][$];
        protected entry_t      b_queue[2][$];
        // AWs taken per ID.
        protected int unsigned arrivals[2][id_key_t];
        // The burst whose B each lane has on the bus.
        protected item_t       b_cur[2];
        // The model lane's pick, held from the replay until its B transfers,
        // since its burst may not have ended its W yet.
        protected pick_t       held;
        protected int unsigned held_delay;
        protected realtime     held_at;
        protected longint      clocks;
        protected int unsigned starts[2];
        protected int unsigned done[2];

        `uvm_component_param_utils(axi_write_slave_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

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

        // The index in the DUT lane's b_queue of the burst whose B goes out
        // next, or -1. A burst is ready once its delay has passed and no
        // older burst with its ID is queued. Only the oldest burst may go,
        // unless cfg.reorder lets any ready one.
        protected function int next_b();
            int ready[$];
            for (int i = 0; i < b_queue[A2C_DUT_LANE].size(); i++) begin
                bit older = 0;
                if (!cfg.reorder && i != 0) break;
                for (int j = 0; j < i; j++) older |= (b_queue[A2C_DUT_LANE][j].aw.id === b_queue[A2C_DUT_LANE][i].aw.id);
                if (!older && b_queue[A2C_DUT_LANE][i].at + b_queue[A2C_DUT_LANE][i].delay <= clocks) ready.push_back(i);
            end
            if (ready.size() == 0) return -1;
            return cfg.reorder ? ready[$urandom_range(ready.size() - 1, 0)] : ready[0];
        endfunction

        // Writes the burst's strobed bytes to the memory, or none of them and
        // SLVERR when a beat's address is in an error range.
        protected function void write_burst(item_t aw);
            bit [63:0]   first;
            int unsigned count;
            aw.resp = AXI_OKAY;
            foreach (aw.data[n]) begin
                axi_beat(64'(aw.addr), aw.size, aw.len, aw.burst, n, first, count);
                if (axi_in_error_range(first, cfg.error_ranges)) aw.resp = AXI_SLVERR;
            end
            if (aw.resp == AXI_SLVERR) return;
            foreach (aw.data[n]) begin
                bit [8*DATA_BYTES-1:0] bytes = '0;
                bytes[$bits(data_t)-1:0] = aw.data[n];
                axi_beat(64'(aw.addr), aw.size, aw.len, aw.burst, n, first, count);
                for (int unsigned i = 0; i < count; i++) begin
                    int unsigned bl = int'((first + i) % (64'd1 << FULL_SIZE));
                    if (bl < DATA_BYTES && aw.strb[n][bl]) cfg.mem.write(first + i, bytes[8 * bl +: 8]);
                end
            end
        endfunction

        protected function void send_b(int l, id_t id, axi_resp_e resp);
            lane[l].bvalid <= 1'b1;
            lane[l].bid    <= id;
            lane[l].bresp  <= resp;
            lane[l].buser  <= '0;
        endfunction

        // The DUT lane's next B, chosen by the DUT lane alone and recorded
        // for the model lane in Mode B.
        protected function void dut_choose();
            int    pick;
            pick_t p;
            if (b_cur[A2C_DUT_LANE] != null) return;
            pick = next_b();
            if (pick < 0) return;
            b_cur[A2C_DUT_LANE] = b_queue[A2C_DUT_LANE][pick].aw;
            if (replay != null) begin
                p = new();
                p.aw  = b_cur[A2C_DUT_LANE];
                p.idx = b_queue[A2C_DUT_LANE][pick].idx;
                replay.record(p, b_queue[A2C_DUT_LANE][pick].delay);
            end
            b_queue[A2C_DUT_LANE].delete(pick);
            send_b(A2C_DUT_LANE, b_cur[A2C_DUT_LANE].id, b_cur[A2C_DUT_LANE].resp);
        endfunction

        // The model lane takes the DUT lane's next pick, and sends its B once
        // its own burst of that pick has ended its W and the pick's delay
        // has passed since. With no pick recorded it waits, and the replay
        // log counts it as waiting only when it has an ended burst of its
        // own to answer.
        protected function void model_follow();
            int found = -1;
            if (b_cur[A2C_MODEL_LANE] != null) return;
            if (held == null) begin
                if (b_queue[A2C_MODEL_LANE].size() == 0 && replay.pending() == 0) return;
                if (!replay.can_replay()) return;
                replay.replay(held, held_delay);
                held_at = $realtime;
            end
            foreach (b_queue[A2C_MODEL_LANE][i]) begin
                if (id_key_t'(b_queue[A2C_MODEL_LANE][i].aw.id) == id_key_t'(held.aw.id) && b_queue[A2C_MODEL_LANE][i].idx == held.idx) begin
                    found = i;
                    break;
                end
            end
            if (found < 0 || b_queue[A2C_MODEL_LANE][found].at + held_delay > clocks) return;
            b_cur[A2C_MODEL_LANE] = b_queue[A2C_MODEL_LANE][found].aw;
            b_queue[A2C_MODEL_LANE].delete(found);
            send_b(A2C_MODEL_LANE, b_cur[A2C_MODEL_LANE].id, held.aw.resp);
        endfunction

        protected function void take_aw(int l);
            entry_t  e;
            id_key_t id;
            e.aw        = item_t::type_id::create("aw");
            e.aw.id     = lane[l].awid;
            e.aw.addr   = lane[l].awaddr;
            e.aw.len    = lane[l].awlen;
            e.aw.size   = lane[l].awsize;
            e.aw.burst  = axi_burst_e'(lane[l].awburst);
            e.aw.awuser = lane[l].awuser;
            e.aw.data   = new[0];
            e.aw.strb   = new[0];
            e.aw.wuser  = new[0];
            if (!BYTE_LANES && e.aw.size != FULL_SIZE) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s is a %0d-byte transfer on a %0d-bit bus, which carries only full-width transfers",
                                                  cfg.port_name, e.aw.convert2string(), 1 << e.aw.size, $bits(data_t)))
            end
            id = id_key_t'(e.aw.id);
            if (!arrivals[l].exists(id)) arrivals[l][id] = 0;
            e.idx   = arrivals[l][id]++;
            e.taken = $realtime;
            aw_queue[l].push_back(e);
            starts[l]++;
        endfunction

        // Gives each W beat to the oldest burst whose W has not ended. Only
        // the DUT lane writes an ended burst to the memory and draws its
        // delay.
        protected function void claim_beats(int l);
            while (aw_queue[l].size() != 0 && w_queue[l].size() != 0) begin
                item_t       aw   = aw_queue[l][0].aw;
                w_beat_t     beat = w_queue[l].pop_front();
                int unsigned n    = aw.data.size();
                entry_t      e;
                aw.data  = new[n + 1](aw.data);
                aw.strb  = new[n + 1](aw.strb);
                aw.wuser = new[n + 1](aw.wuser);
                aw.data[n]  = beat.data;
                aw.strb[n]  = beat.strb;
                aw.wuser[n] = beat.wuser;
                if (beat.last !== 1'b1 && n != aw.len) continue;
                e    = aw_queue[l].pop_front();
                e.at = clocks;
                if (l == A2C_DUT_LANE) begin
                    write_burst(aw);
                    e.delay = $urandom_range(cfg.resp_delay_max, cfg.resp_delay_min);
                end
                b_queue[l].push_back(e);
            end
        endfunction

        // Each loop iteration starts at a drive point. A burst's B goes out
        // at the drive point after its AW and last W have both transferred,
        // plus its response delay, and no earlier than the drive point after
        // the B before it transfers. One process serves both lanes, the DUT
        // lane first, so a model lane waiting for a pick takes it at the
        // drive point the DUT lane makes it.
        virtual task run_phase(uvm_phase phase);
            bit aw_ready;
            bit w_ready;
            lane[A2C_DUT_LANE]   = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            for (int l = 0; l < lanes; l++) begin
                lane[l].awready <= 1'b0;
                lane[l].wready  <= 1'b0;
                lane[l].bvalid  <= 1'b0;
                lane[l].bid     <= '0;
                lane[l].bresp   <= '0;
                lane[l].buser   <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                aw_ready = ($urandom_range(99, 0) < cfg.awready_pct);
                w_ready  = ($urandom_range(99, 0) < cfg.wready_pct);
                for (int l = 0; l < lanes; l++) begin
                    lane[l].awready <= aw_ready;
                    lane[l].wready  <= w_ready;
                end
                dut_choose();
                if (lanes == 2) model_follow();
                for (int l = 0; l < lanes; l++) begin
                    if (b_cur[l] == null) lane[l].bvalid <= 1'b0;
                end
                cfg.clk_vif.sample_edge();
                clocks++;
                for (int l = 0; l < lanes; l++) begin
                    if (b_cur[l] == null || lane[l].bready !== 1'b1) continue;
                    b_cur[l] = null;
                    done[l]++;
                    if (l == A2C_MODEL_LANE) held = null;
                end
                for (int l = 0; l < lanes; l++) begin
                    if (lane[l].wvalid === 1'b1 && lane[l].wready === 1'b1) begin
                        w_queue[l].push_back('{data: lane[l].wdata, strb: strb_bits_t'(lane[l].wstrb),
                                               wuser: lane[l].wuser, last: lane[l].wlast});
                    end
                    if (lane[l].awvalid === 1'b1 && lane[l].awready === 1'b1) take_aw(l);
                    claim_beats(l);
                end
                cfg.clk_vif.drive_edge();
            end
        endtask

        virtual function bit lane_busy(a2c_lane_e l);
            return aw_queue[l].size() != 0 || w_queue[l].size() != 0 || b_queue[l].size() != 0 || b_cur[l] != null
                || (l == A2C_MODEL_LANE && held != null);
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return done[l];
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return starts[l];
        endfunction

        // The pick the model lane holds at the end of the run without having
        // ended its burst, or "". A pick past a cut is not owed.
        protected function string held_report();
            string behind = "";
            string listed = "";
            if (replay == null || held == null || b_cur[A2C_MODEL_LANE] != null) return "";
            if (replay.get_cut() != 0 && done[A2C_MODEL_LANE] >= replay.get_cut()) return "";
            foreach (b_queue[A2C_MODEL_LANE][i]) begin
                if (id_key_t'(b_queue[A2C_MODEL_LANE][i].aw.id) == id_key_t'(held.aw.id) && b_queue[A2C_MODEL_LANE][i].idx == held.idx) return "";
            end
            if (b_queue[A2C_MODEL_LANE].size() == 0) begin
                return $sformatf("%s: the DUT lane answered %s, AW %0d of ID %0h, and the model lane never ended that burst",
                                 get_full_name(), held.aw.convert2string(), held.idx + 1, held.aw.id);
            end
            if (b_queue[A2C_MODEL_LANE].size() > 3) listed = ", the first 3";
            for (int i = 0; i < b_queue[A2C_MODEL_LANE].size() && i < 3; i++) begin
                behind = {behind, (i == 0) ? "" : "; ", $sformatf("%s, AW %0d of ID %0h", b_queue[A2C_MODEL_LANE][i].aw.convert2string(),
                                                                  b_queue[A2C_MODEL_LANE][i].idx + 1, b_queue[A2C_MODEL_LANE][i].aw.id)};
            end
            return $sformatf("%s: the model lane holds the DUT lane's pick %s, AW %0d of ID %0h, whose burst it has not ended, with %0d ended bursts of its own behind it%s: %s. The model lane answers the DUT lane's picks in the DUT lane's order. Either the model never ends that burst, or it issues it only after a B that the pick holds back. In the second case the model keeps fewer bursts outstanding than the RTL, so its queuing does not match the RTL's. Fix the model: issue each burst's AW and W beats ahead of its B, from a thread other than the one that takes the Bs, with a synchLock where those threads contend. Setting reorder to 0 on this port is only a stopgap, which hides the defect and ends the port's reorder coverage",
                             get_full_name(), held.aw.convert2string(), held.idx + 1, held.aw.id, b_queue[A2C_MODEL_LANE].size(),
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
            entry_t      model[$];
            super.check_phase(phase);
            if (held_why != "") begin
                `uvm_error("A2C_REPLAY", {held_why, a2c_replay_drain::death_context(held_at)})
                return;
            end
            if (replay == null || replay.get_cut() != 0) return;
            model = {b_queue[A2C_MODEL_LANE], aw_queue[A2C_MODEL_LANE]};
            foreach (model[i]) begin
                id_key_t id = id_key_t'(model[i].aw.id);
                if (arrivals[A2C_DUT_LANE].exists(id) && arrivals[A2C_DUT_LANE][id] > model[i].idx) continue;
                if (extra == 0) first = model[i];
                extra++;
            end
            if (extra != 0) begin
                `uvm_error("A2C_REPLAY", $sformatf("%s: the model lane issued %0d AWs the DUT lane never issued, the first %s, AW %0d of ID %0h%s",
                                                   get_full_name(), extra, first.aw.convert2string(), first.idx + 1, first.aw.id,
                                                   a2c_replay_drain::death_context(first.taken)))
            end
        endfunction
    endclass : axi_write_slave_driver

    class axi_write_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                              type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                              type id_t = logic [3:0]) extends uvm_monitor implements a2c_lane_watch;
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;
        typedef item_t::strb_bits_t                                                        strb_bits_t;
        typedef bit [$bits(id_t)-1:0]                                                      id_key_t;
        localparam int unsigned FULL_SIZE = item_t::FULL_SIZE;
        localparam int unsigned AW_W = $bits(id_t) + $bits(addr_t) + 13 + $bits(awuser_t) + 1;
        localparam int unsigned W_W  = $bits(id_t) + $bits(data_t) + $bits(strb_t) + 1 + $bits(wuser_t) + 1;
        localparam int unsigned B_W  = $bits(id_t) + 2 + $bits(buser_t) + 1;

        typedef struct {
            id_t        wid;
            data_t      data;
            strb_bits_t strb;
            wuser_t     wuser;
            logic       last;
        } w_beat_t;

        axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                               .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t))  vif;
        // One item per burst, at its B, with its AW fields, beats and B.
        uvm_analysis_port #(item_t)                                                 ap;
        // The replay log of the Mode B slave on this monitor's pin set, or
        // null. A run the drain cut ends with bursts open on purpose.
        a2c_replay_log_base                                                         replay;
        // When the master declared this monitor's lane dead, or 0. A dead
        // lane ends the run with bursts open on purpose too.
        realtime                                                                    died_at;

        // Bursts whose AW has transferred and whose W has not ended, in AW
        // order; W beats no AW has claimed yet; and bursts whose W has ended
        // and whose B has not arrived, oldest first per ID.
        protected item_t   aw_open[$];
        protected w_beat_t w_early[$];
        protected item_t   b_open[id_key_t][$];

        `uvm_component_param_utils(axi_write_monitor#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        // The AW, W and B payloads, each with its valid, as one vector, so a
        // stalled transfer can be compared with the next clock.
        protected function logic [AW_W-1:0] aw_pins();
            return {vif.awvalid, vif.awid, vif.awaddr, vif.awlen, vif.awsize, vif.awburst,
                    vif.awuser};
        endfunction

        protected function logic [W_W-1:0] w_pins();
            return {vif.wvalid, vif.wid, vif.wdata, vif.wstrb, vif.wlast, vif.wuser};
        endfunction

        protected function logic [B_W-1:0] b_pins();
            return {vif.bvalid, vif.bid, vif.bresp, vif.buser};
        endfunction

        protected function string path();
            return {get_full_name(), ".", cfg.port_name};
        endfunction

        // A stalled AW, W or B must hold its valid and payload until ready.
        // B is taken first on each clock, since a B may not share the rising
        // edge of its burst's last W.
        virtual task run_phase(uvm_phase phase);
            logic [AW_W-1:0] held_aw;
            logic [W_W-1:0]  held_w;
            logic [B_W-1:0]  held_b;
            bit              aw_stalled;
            bit              w_stalled;
            bit              b_stalled;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (b_stalled && b_pins() !== held_b) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before bready took the stalled response", cfg.port_name,
                                                     vif.bvalid !== 1'b1 ? "bvalid dropped" : "the B payload changed"))
                end
                if (w_stalled && w_pins() !== held_w) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before wready took the stalled beat", cfg.port_name,
                                                     vif.wvalid !== 1'b1 ? "wvalid dropped" : "the W payload changed"))
                end
                if (aw_stalled && aw_pins() !== held_aw) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before awready took the stalled AW", cfg.port_name,
                                                     vif.awvalid !== 1'b1 ? "awvalid dropped" : "the AW payload changed"))
                end
                b_stalled  = vif.bvalid === 1'b1 && vif.bready !== 1'b1;
                w_stalled  = vif.wvalid === 1'b1 && vif.wready !== 1'b1;
                aw_stalled = vif.awvalid === 1'b1 && vif.awready !== 1'b1;
                held_b     = b_pins();
                held_w     = w_pins();
                held_aw    = aw_pins();
                if (vif.bvalid === 1'b1 && vif.bready === 1'b1) take_b();
                if (vif.wvalid === 1'b1 && vif.wready === 1'b1) begin
                    w_early.push_back('{wid: vif.wid, data: vif.wdata, strb: strb_bits_t'(vif.wstrb),
                                        wuser: vif.wuser, last: vif.wlast});
                end
                if (vif.awvalid === 1'b1 && vif.awready === 1'b1) take_aw();
                claim_beats();
            end
        endtask

        protected function void take_aw();
            item_t           it = item_t::type_id::create("item");
            longint unsigned nbytes;
            it.id     = vif.awid;
            it.addr   = vif.awaddr;
            it.len    = vif.awlen;
            it.size   = vif.awsize;
            it.burst  = axi_burst_e'(vif.awburst);
            it.awuser = vif.awuser;
            it.data   = new[0];
            it.strb   = new[0];
            it.wuser  = new[0];
            nbytes    = 64'd1 << it.size;
            if (vif.awburst === 2'b11) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: awburst is the reserved value 2'b11", cfg.port_name))
            end
            if (it.size > FULL_SIZE) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: awsize is wider than the %0d-bit bus", cfg.port_name,
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
            aw_open.push_back(it);
        endfunction

        // W beats belong to the AWs in order, whether they transfer before or
        // after the AW. A burst's W ends at wlast, or at its last beat when
        // wlast is missing. A beat must carry its burst's ID, as the SystemC
        // channel asserts, and set no strobe outside the lanes it carries.
        protected function void claim_beats();
            while (aw_open.size() != 0 && w_early.size() != 0) begin
                item_t       it    = aw_open[0];
                w_beat_t     beat  = w_early.pop_front();
                int unsigned n     = it.data.size();
                bit          last  = (n == it.len);
                strb_bits_t  lanes = it.beat_lanes(it.addr, it.size, it.len, it.burst, n);
                it.data  = new[n + 1](it.data);
                it.strb  = new[n + 1](it.strb);
                it.wuser = new[n + 1](it.wuser);
                it.data[n]  = beat.data;
                it.strb[n]  = beat.strb;
                it.wuser[n] = beat.wuser;
                `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.beat2string(n), $sformatf("%0h", it.data[n])), UVM_HIGH)
                if (!cfg.id_unbound && beat.wid !== it.id) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: wid %0h on beat %0d of the burst %s", cfg.port_name,
                                                      beat.wid, n, it.convert2string()))
                end
                if ((beat.strb & ~lanes) != 0) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: wstrb %b on beat %0d of the burst %s sets lanes outside %b",
                                                      cfg.port_name, beat.strb, n, it.convert2string(), lanes))
                end
                if (beat.last !== last) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: wlast is %b on beat %0d of the %0d-beat burst %s", cfg.port_name,
                                                      beat.last, n, int'(it.len) + 1, it.convert2string()))
                end
                if (beat.last !== 1'b1 && !last) continue;
                void'(aw_open.pop_front());
                b_open[id_key_t'(it.id)].push_back(it);
            end
        endfunction

        // A B completes the oldest burst of its bid whose W has ended.
        protected function void take_b();
            id_key_t id = id_key_t'(vif.bid);
            item_t   it;
            if (!b_open.exists(id) || b_open[id].size() == 0) begin
                foreach (aw_open[i]) begin
                    if (id_key_t'(aw_open[i].id) == id) begin
                        `uvm_error("A2C_PROTO", $sformatf("%s: B with bid %0h arrived before the last W of %s",
                                                          cfg.port_name, id, aw_open[i].convert2string()))
                        return;
                    end
                end
                `uvm_error("A2C_PROTO", $sformatf("%s: B with bid %0h matches no outstanding write", cfg.port_name, id))
                return;
            end
            it       = b_open[id].pop_front();
            it.resp  = axi_resp_e'(vif.bresp);
            it.buser = vif.buser;
            `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.convert2string(), $sformatf("%0h", it.addr)), UVM_MEDIUM)
            ap.write(it);
        endfunction

        // The master calls it when it declares this monitor's lane dead.
        virtual function void lane_dead();
            if (died_at == 0) died_at = $realtime;
        endfunction

        // Every W beat must belong to a burst, and every burst must have
        // ended its W and received its B, by the end of a run the drain did
        // not cut, on a lane the master did not declare dead.
        virtual function void check_phase(uvm_phase phase);
            int unsigned waiting = 0;
            string       what;
            foreach (b_open[id]) waiting += b_open[id].size();
            if (w_early.size() == 0 && aw_open.size() == 0 && waiting == 0) return;
            what = $sformatf("%s: the run ended with %0d W beats no AW claimed, %0d bursts whose W had not ended and %0d bursts waiting for B",
                             cfg.port_name, w_early.size(), aw_open.size(), waiting);
            if (died_at != 0) `uvm_info("A2C_PROTO", $sformatf("%s, on a lane the master declared dead at %0t (A2C_SKEW)", what, died_at), UVM_LOW)
            else if (replay != null && replay.get_cut() != 0) `uvm_info("A2C_PROTO", {what, ", after the drain cut it"}, UVM_LOW)
            else `uvm_error("A2C_PROTO", what)
        endfunction
    endclass : axi_write_monitor

    // The Mode B comparator: AXI orders bursts only within an ID, so it
    // pairs the two lanes' bursts in order per ID.
    class axi_write_comparator #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                                 type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                                 type id_t = logic [3:0])
        extends a2c_in_order_comparator #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t));
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;

        `uvm_component_param_utils(axi_write_comparator#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string key(item_t t);
            return $sformatf("%0h", t.id);
        endfunction
    endclass : axi_write_comparator

    class axi_write_agent #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                            type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                            type id_t = logic [3:0]) extends uvm_agent;
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)         item_t;
        typedef axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)       config_t;
        typedef axi_write_monitor#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)      monitor_t;
        typedef axi_write_slave_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) slave_t;
        typedef virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                                       .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t))        vif_t;
        typedef a2c_pin_registry #(vif_t)                                                         registry_t;

        config_t                                                                          cfg;
        // axi_write_master_driver for A2C_SRC, axi_write_slave_driver for A2C_DST.
        uvm_driver #(item_t)                                                              drv;
        // A2C_SRC only.
        uvm_sequencer #(item_t)                                                           sqr;
        monitor_t                                                                         mon;
        // Mode B only.
        monitor_t                                                                         model_mon;
        axi_write_comparator#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) model_cmp;

        `uvm_component_param_utils(axi_write_agent#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_write_agent has no cfg")
            end
            if ($bits(data_t) != 8 * $bits(strb_t)) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: data_t is %0d bits and strb_t %0d, but wstrb needs one bit per data byte",
                                                cfg.port_name, $bits(data_t), $bits(strb_t)))
            end
            mon = monitor_t::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = monitor_t::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                model_cmp = axi_write_comparator#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_SRC) begin
                axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) master;
                if (cfg.max_outstanding == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: max_outstanding is 0, so no burst could go out", cfg.port_name))
                end
                if (cfg.bready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: bready_pct is 0, so no burst could complete", cfg.port_name))
                end
                master = axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)::type_id::create("drv", this);
                master.cfg = cfg;
                drv = master;
                sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
                uvm_config_db#(config_t)::set(this, "sqr", "cfg", cfg);
            end else begin
                slave_t slave;
                if (cfg.awready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: awready_pct is 0, so no AW could transfer", cfg.port_name))
                end
                if (cfg.wready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: wready_pct is 0, so no W beat could transfer", cfg.port_name))
                end
                if (cfg.resp_delay_min > cfg.resp_delay_max) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: resp_delay_min %0d is above resp_delay_max %0d", cfg.port_name,
                                                    cfg.resp_delay_min, cfg.resp_delay_max))
                end
                if (cfg.mem == null) cfg.mem = axi_write_mem_t::type_id::create({get_full_name(), ".mem"});
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
            axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) master;
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
    endclass : axi_write_agent

endpackage : axi_write_uvm_pkg

`endif // AXI_WRITE_UVM_PKG_SV
