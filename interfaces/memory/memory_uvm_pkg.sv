`ifndef MEMORY_UVM_PKG_SV
`define MEMORY_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for memory_if. One access per rising edge with enable high: a
// write stores write_data at addr, and a read returns read_data on the
// following clock, which then holds until the next read, as memory_sp and
// memory_dp do. There is no handshake, so neither side can stall the other.
// The A2C_SRC driver issues one access per clock, so reads go out back to
// back: item_done() on the edge that takes the access, and for a read
// put_response() with the read data at the falling edge after that edge, so
// at most one read response is pending; memory_base_seq handles those
// responses. The A2C_DST driver serves accesses from cfg.mem, an
// a2c_mem_model of data_t words indexed by addr, which a test may preload,
// inspect, or share between agents. Pin timing follows a2c_clk_if: drive at
// drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon. The A2C_SRC driver puts
// each access on both lanes on the same clock, so the lanes stay in step,
// and the read responses come from the DUT lane. Its model_cmp, a
// memory_comparator, compares each access of the two lanes in order, read
// data included, under the next-access rule for an X or Z read word. The
// A2C_DST driver serves both lanes from the one cfg.mem. The DUT lane
// applies access n and records its read word, and the model lane's access n
// gets that word and writes nothing. memory has no handshake, so a model lane
// that reaches access n first cannot wait. Its write is kept aside for its
// own later reads, never in cfg.mem, and its read takes that word or the
// one cfg.mem holds then. When the DUT lane makes access n, an A2C_REPLAY
// error reports any difference between the two reads. An early read of a
// word that another port's DUT lane has yet to write gets the old word and
// is reported as A2C_REPLAY, even when the design is correct. The A2C_DST
// driver's replay log holds the end of the run phase while the model lane
// catches up (a2c_replay_drain), and its model_cmp compares the access
// streams in order. A DUT lane still accessing the port at the drain's
// deadline is cut there, and the accesses after the cut go unchecked on
// both lanes. The model lane must complete the accesses the cut keeps
// within drain_catchup_cycles clocks of the cut, by default the drain's
// deadline, so only a model lane further behind than that at the cut is an
// A2C_REPLAY error. What the DUT produces that is not compared:
//   DUT dst port, A2C_SRC agent: none
//   DUT src port, A2C_DST agent: none
package memory_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class memory_item #(type addr_t = logic, type data_t = logic) extends uvm_sequence_item;
        rand bit    write;
        rand addr_t addr;
        // The data written, or the data a read returned.
        rand data_t data;
        // src role: idle clocks (enable low) the driver inserts before this access.
        int unsigned gap;

        `uvm_object_param_utils(memory_item#(addr_t, data_t))

        function new(string name = "memory_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            memory_item#(addr_t, data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            write = rhs_.write;
            addr  = rhs_.addr;
            data  = rhs_.data;
            gap   = rhs_.gap;
        endfunction

        // gap is stimulus timing, not payload, so it takes no part in the
        // compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            memory_item#(addr_t, data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (write === rhs_.write) && (addr === rhs_.addr) &&
                   (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%s addr=%p data=%p", write ? "write" : "read", addr, data);
        endfunction
    endclass : memory_item

    class memory_config #(type addr_t = logic, type data_t = logic) extends uvm_object;
        virtual memory_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual memory_if #(.addr_t(addr_t), .data_t(data_t)) model_vif;
        virtual a2c_clk_if                                    clk_vif;
        uvm_active_passive_enum                               is_active = UVM_ACTIVE;
        a2c_role_e                                            role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                                port_name = "";
        // dst role: the storage the driver serves. The agent creates one when
        // the test leaves it null.
        a2c_mem_model #(data_t)                               mem;

        `uvm_object_param_utils(memory_config#(addr_t, data_t))

        function new(string name = "memory_config");
            super.new(name);
        endfunction
    endclass : memory_config

    // The sequence a src-role test extends. Read data arrives at the falling
    // edge after item_done(), as a response the driver routes back through the
    // sequencer; use_response_handler keeps those responses out of the
    // sequence's response queue, which would otherwise overflow. send()
    // counts the reads, read_done() sees each response, and wait_for_reads()
    // holds body() until every read has returned, since a response to a
    // sequence that has ended is dropped.
    class memory_base_seq #(type addr_t = logic, type data_t = logic)
        extends uvm_sequence #(memory_item#(addr_t, data_t));
        protected int unsigned reads_sent;
        protected int unsigned reads_done;

        `uvm_object_param_utils(memory_base_seq#(addr_t, data_t))

        function new(string name = "memory_base_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        task send(memory_item#(addr_t, data_t) it);
            start_item(it);
            finish_item(it);
            if (!it.write) reads_sent++;
        endtask

        task wait_for_reads();
            wait (reads_done >= reads_sent);
        endtask

        // Called once per read, with the request's addr and the data read.
        virtual function void read_done(memory_item#(addr_t, data_t) rsp);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
            memory_item#(addr_t, data_t) rsp;
            $cast(rsp, response);
            reads_done++;
            read_done(rsp);
        endfunction
    endclass : memory_base_seq

    class memory_driver #(type addr_t = logic, type data_t = logic)
        extends uvm_driver #(memory_item#(addr_t, data_t)) implements a2c_replay_lanes;
        typedef virtual memory_if #(.addr_t(addr_t), .data_t(data_t)) vif_t;
        // What the DUT lane's access gives the model lane's access of the
        // same index: the word a read returned.
        typedef struct {
            bit    write;
            data_t word;
        } rsp_t;
        typedef a2c_replay_log #(rsp_t) replay_t;
        // A model lane access served before the DUT lane made it.
        typedef struct {
            int unsigned n;
            bit          write;
            bit [63:0]   index;
            data_t       word;
        } early_t;

        memory_config#(addr_t, data_t) cfg;
        // dst role in Mode B only.
        replay_t                       replay;

        // src role: responses to the reads taken on the last rising edge,
        // waiting for read_data. Each is built when its read is accepted,
        // because a sequence may reuse the request object for its next item.
        protected memory_item#(addr_t, data_t) reads[$];
        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        // dst role: an access sampled and not yet served at the drive point.
        protected bit          in_access[2];
        protected int unsigned starts[2];
        // The accesses each lane has completed, each counted by the sample
        // point at which its monitor reports it: a write at the sample edge
        // before its clock, a read at the drive point after, where
        // read_data goes out for the next sample edge.
        protected int unsigned done[2];
        protected early_t      early[$];
        // The model lane's early writes, which cfg.mem never takes: per
        // index, the last word written and the access that wrote it. Its
        // early reads see them. An entry goes at the drive point where
        // cfg.mem takes the DUT lane's write of the same access.
        protected data_t       ahead_word[bit [63:0]];
        protected int unsigned ahead_n[bit [63:0]];
        protected early_t      retire[$];

        `uvm_component_param_utils(memory_driver#(addr_t, data_t))

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

        protected function void drive_enable(bit enable);
            for (int l = 0; l < lanes; l++) lane[l].enable <= enable;
        endfunction

        // Each loop iteration starts at a drive point, and the access goes out
        // on the rising edge before the next one. A read is answered at the
        // sample edge after that, by capture_reads(), while the loop drives
        // the next access.
        protected virtual task run_src();
            for (int l = 0; l < lanes; l++) begin
                lane[l].enable     <= 1'b0;
                lane[l].wr_en      <= 1'b0;
                lane[l].addr       <= '0;
                lane[l].write_data <= '0;
            end
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            fork
                capture_reads();
            join_none
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    drive_enable(1'b0);
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    drive_enable(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                for (int l = 0; l < lanes; l++) begin
                    lane[l].enable <= 1'b1;
                    lane[l].wr_en  <= req.write;
                    lane[l].addr   <= req.addr;
                    if (req.write) lane[l].write_data <= req.data;
                end
                cfg.clk_vif.drive_edge();
                if (!req.write) begin
                    memory_item#(addr_t, data_t) rsp = memory_item#(addr_t, data_t)::type_id::create("rsp");
                    rsp.set_id_info(req);
                    rsp.write = 1'b0;
                    rsp.addr  = req.addr;
                    reads.push_back(rsp);
                end
                seq_item_port.item_done();
            end
        endtask

        // At most one read waits here: it was taken on the rising edge just
        // before this sample edge, so read_data now holds its word. The
        // response carries the DUT lane's word.
        protected virtual task capture_reads();
            memory_item#(addr_t, data_t) rsp;
            forever begin
                cfg.clk_vif.sample_edge();
                if (reads.size() == 0) continue;
                rsp = reads.pop_front();
                rsp.data = cfg.vif.read_data;
                seq_item_port.put_response(rsp);
            end
        endtask

        // The model lane's accesses served early, matched against the DUT
        // lane's records as they arrive.
        protected function void settle_early();
            rsp_t        rsp;
            int unsigned delay;
            early_t      e;
            while (early.size() > 0 && replay.can_replay()) begin
                replay.replay(rsp, delay);
                e = early.pop_front();
                if (e.write) retire.push_back(e);
                if (!e.write && !rsp.write && e.word !== rsp.word) begin
                    `uvm_error("A2C_REPLAY", $sformatf("%s: the model lane read index 0x%0h at access %0d before the DUT lane made that access, and got %p; the DUT lane's access %0d returns %p",
                                                       cfg.port_name, e.index, e.n + 1, e.word, e.n + 1, rsp.word))
                end
            end
        endfunction

        // A read takes its word at the sample edge, before any write the
        // rising edge applies, so a read and a write of one address on the
        // same clock through two agents sharing cfg.mem return the old word,
        // as memory_dp does. read_data holds until the next read. One
        // process serves every lane, sampling the DUT lane first, so the
        // model lane's access n on the clock of the DUT lane's access n
        // takes its recorded word.
        protected virtual task run_dst();
            bit        is_write[2];
            bit        active[2];
            bit [63:0] index[2];
            data_t     wdata[2];
            data_t     rdata[2];
            rsp_t      rsp;
            for (int l = 0; l < lanes; l++) lane[l].read_data <= '0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    active[l] = (lane[l].enable === 1'b1);
                    if (!active[l]) continue;
                    is_write[l] = (lane[l].wr_en === 1'b1);
                    index[l]    = 64'(lane[l].addr);
                    wdata[l]    = lane[l].write_data;
                    in_access[l] = 1'b1;
                    starts[l]++;
                    if (is_write[l]) done[l]++;
                    if (l == A2C_DUT_LANE) begin
                        if (!is_write[l]) rdata[l] = cfg.mem.read(index[l]);
                        if (replay != null) begin
                            replay.record('{write: is_write[l], word: is_write[l] ? data_t'('0) : rdata[l]}, 0);
                            settle_early();
                        end
                    end else begin
                        int unsigned delay;
                        if (early.size() == 0 && replay.can_replay()) begin
                            replay.replay(rsp, delay);
                            rdata[l] = rsp.word;
                        end else begin
                            if (is_write[l]) begin
                                ahead_word[index[l]] = wdata[l];
                                ahead_n[index[l]]    = starts[l] - 1;
                            end else begin
                                rdata[l] = ahead_word.exists(index[l]) ? ahead_word[index[l]] : cfg.mem.read(index[l]);
                            end
                            early.push_back('{n: starts[l] - 1, write: is_write[l], index: index[l], word: rdata[l]});
                        end
                    end
                end
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (!active[l]) continue;
                    in_access[l] = 1'b0;
                    if (!is_write[l]) done[l]++;
                    if (!is_write[l]) begin
                        lane[l].read_data <= rdata[l];
                    end else if (l == A2C_DUT_LANE) begin
                        cfg.mem.write(index[l], wdata[l]);
                    end
                end
                foreach (retire[i]) begin
                    if (ahead_n.exists(retire[i].index) && ahead_n[retire[i].index] == retire[i].n) begin
                        ahead_word.delete(retire[i].index);
                        ahead_n.delete(retire[i].index);
                    end
                end
                retire.delete();
            end
        endtask

        virtual function bit lane_busy(a2c_lane_e l);
            return in_access[l];
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return done[l];
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return starts[l];
        endfunction
    endclass : memory_driver

    class memory_monitor #(type addr_t = logic, type data_t = logic) extends uvm_monitor;
        memory_config#(addr_t, data_t)                    cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual memory_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        // One item per access, in access order; a read's item carries the
        // word read_data held on the next clock.
        uvm_analysis_port #(memory_item#(addr_t, data_t)) ap;

        `uvm_component_param_utils(memory_monitor#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        protected function void publish(memory_item#(addr_t, data_t) item);
            `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                         $sformatf("%0h %0h %0h", item.write, item.addr, item.data)), UVM_MEDIUM)
            ap.write(item);
        endfunction

        virtual task run_phase(uvm_phase phase);
            memory_item#(addr_t, data_t) item;
            memory_item#(addr_t, data_t) read;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (read != null) begin
                    read.data = vif.read_data;
                    publish(read);
                    read = null;
                end
                if (vif.enable !== 1'b1) continue;
                item = memory_item#(addr_t, data_t)::type_id::create("item");
                item.write = (vif.wr_en === 1'b1);
                item.addr  = vif.addr;
                if (item.write) begin
                    item.data = vif.write_data;
                    publish(item);
                end else begin
                    read = item;
                end
            end
        endtask
    endclass : memory_monitor

    // The A2C_SRC role's Mode B comparator, for a DUT that is the memory. A
    // pair of reads in which either word has X or Z is held, not compared.
    // It passes if each lane whose word has X or Z makes its next access a
    // write of the same address, which replaces the word, and is a mismatch
    // otherwise, as the memory checker's next-access rule fails it. A pair
    // still held at the end of the run is an A2C_MODEL_CMP error.
    class memory_comparator #(type addr_t = logic, type data_t = logic)
        extends a2c_in_order_comparator #(memory_item#(addr_t, data_t));
        typedef memory_item#(addr_t, data_t) item_t;

        protected item_t held_dut;
        protected item_t held_model;

        `uvm_component_param_utils(memory_comparator#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function bit xz_read(item_t t);
            return !t.write && $isunknown(t.data);
        endfunction

        // Whether next replaces the X or Z word read, or no word needs it.
        protected function bit replaced(item_t read, item_t next);
            return !xz_read(read) || (next.write && next.addr === read.addr);
        endfunction

        protected virtual function void compare_pair(item_t dut, item_t model, string k);
            if (held_dut != null) begin
                check_pair(replaced(held_dut, dut) && replaced(held_model, model), held_dut, held_model, k);
                held_dut   = null;
                held_model = null;
            end
            if (xz_read(dut) || xz_read(model)) begin
                held_dut   = dut;
                held_model = model;
                return;
            end
            super.compare_pair(dut, model, k);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (held_dut == null) return;
            `uvm_error("A2C_MODEL_CMP", $sformatf("%s: end of test with a read of X or Z that no access followed, after %0d pairs: DUT %s, model %s",
                                              get_full_name(), pairs, held_dut.convert2string(), held_model.convert2string()))
        endfunction
    endclass : memory_comparator

    class memory_agent #(type addr_t = logic, type data_t = logic) extends uvm_agent;
        typedef memory_item#(addr_t, data_t)   item_t;
        typedef memory_config#(addr_t, data_t) config_t;

        config_t                                     cfg;
        memory_driver#(addr_t, data_t)               drv;
        // A2C_SRC only.
        uvm_sequencer #(memory_item#(addr_t, data_t)) sqr;
        memory_monitor#(addr_t, data_t)              mon;
        // Mode B only. On the A2C_SRC role model_cmp is a memory_comparator.
        memory_monitor#(addr_t, data_t)              model_mon;
        a2c_in_order_comparator #(item_t)            model_cmp;

        `uvm_component_param_utils(memory_agent#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "memory_agent has no cfg")
            end
            mon = memory_monitor#(addr_t, data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = memory_monitor#(addr_t, data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                if (cfg.role == A2C_SRC) model_cmp = memory_comparator#(addr_t, data_t)::type_id::create("model_cmp", this);
                else model_cmp = a2c_in_order_comparator#(item_t)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_DST && cfg.mem == null) begin
                cfg.mem = a2c_mem_model#(data_t)::type_id::create({get_name(), "_mem"});
            end
            drv = memory_driver#(addr_t, data_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            if (cfg.role == A2C_SRC) begin
                sqr = uvm_sequencer#(memory_item#(addr_t, data_t))::type_id::create("sqr", this);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) drv.seq_item_port.connect(sqr.seq_item_export);
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
                if (drv != null && drv.replay != null) drv.replay.cmp = model_cmp;
            end
        endfunction
    endclass : memory_agent

endpackage : memory_uvm_pkg

`endif // MEMORY_UVM_PKG_SV
