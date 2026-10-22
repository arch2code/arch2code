// memory agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef logic [5:0] lb_mem_addr_t;
    typedef memory_agent #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem_agent_t;
    typedef mem_agent_t::item_t mem_item_t;
    typedef mem_agent_t::config_t mem_config_t;
    typedef virtual memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem_vif_t;
    typedef a2c_mem_model #(lb_data_t) lb_word_mem_t;

    // Sends the accesses in items with no gaps and checks each read's
    // response against the address in expected_addr and the word in
    // expected, in order. The test fills the queues before it starts the
    // sequence. With reuse set, every access goes out through one item
    // object, copied from items before each send, as a sequence that
    // re-randomises one item does.
    class mem_seq extends memory_base_seq #(lb_mem_addr_t, lb_data_t);
        mem_item_t    items[$];
        lb_data_t     expected[$];
        lb_mem_addr_t expected_addr[$];
        bit           reuse;
        int unsigned  checked;

        `uvm_object_utils(mem_seq)

        function new(string name = "mem_seq");
            super.new(name);
        endfunction

        virtual task body();
            mem_item_t one = mem_item_t::type_id::create("one");
            foreach (items[i]) begin
                if (reuse) begin
                    one.copy(items[i]);
                    send(one);
                end else begin
                    send(items[i]);
                end
            end
            wait_for_reads();
        endtask

        virtual function void read_done(mem_item_t rsp);
            lb_data_t     want = expected.pop_front();
            lb_mem_addr_t want_addr = expected_addr.pop_front();
            checked++;
            if (rsp.addr !== want_addr) begin
                `uvm_error("LB_MEM", $sformatf("read %0d answered for address 0x%0h, sent to 0x%0h", checked, rsp.addr,
                                               want_addr))
            end
            if (rsp.data !== want) begin
                `uvm_error("LB_MEM", $sformatf("read %0d at 0x%0h returned 0x%0h, expected 0x%0h", checked, rsp.addr,
                                               rsp.data, want))
            end
        endfunction
    endclass : mem_seq

    // A src agent and a dst agent on interface vif_name. The dst agent's
    // monitor feeds a scoreboard; the test sets the dst model before build.
    virtual class mem_pair_test extends lb_base_test;
        mem_agent_t              src;
        mem_agent_t              dst;
        lb_scoreboard#(mem_item_t) sb;
        lb_word_mem_t            mem;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // Builds one src and one dst agent on the interface the tb module set
        // under vif_name, the dst agent serving model.
        function void build_pair(string vif_name, string src_name, string dst_name, lb_word_mem_t model,
                                 output mem_agent_t src_agent, output mem_agent_t dst_agent);
            mem_config_t src_cfg;
            mem_config_t dst_cfg;
            mem_vif_t    vif;
            if (!uvm_config_db#(mem_vif_t)::get(this, "", vif_name, vif)) begin
                `uvm_fatal("LB_CFG", $sformatf("no virtual memory_if '%s'", vif_name))
            end
            src_cfg = mem_config_t::type_id::create({src_name, "_cfg"});
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = vif_name;
            dst_cfg = mem_config_t::type_id::create({dst_name, "_cfg"});
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = vif_name;
            dst_cfg.mem       = model;
            uvm_config_db#(mem_config_t)::set(this, src_name, "cfg", src_cfg);
            uvm_config_db#(mem_config_t)::set(this, dst_name, "cfg", dst_cfg);
            src_agent = mem_agent_t::type_id::create(src_name, this);
            dst_agent = mem_agent_t::type_id::create(dst_name, this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            mem = lb_word_mem_t::type_id::create("mem");
            build_pair("mem", "src", "dst", mem, src, dst);
            sb = lb_scoreboard#(mem_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        // Queues one access on seq and the item the dst monitor must report
        // for it; a read reports the word in shadow.
        function void add(mem_seq seq, bit write, lb_mem_addr_t addr, lb_data_t data, ref lb_data_t shadow[lb_mem_addr_t]);
            mem_item_t it = mem_item_t::type_id::create("it");
            mem_item_t ex = mem_item_t::type_id::create("ex");
            it.write = write;
            it.addr  = addr;
            it.data  = data;
            it.gap   = 0;
            if (write) begin
                shadow[addr] = data;
            end else begin
                it.data = '0;
                seq.expected.push_back(shadow.exists(addr) ? shadow[addr] : lb_data_t'(0));
                seq.expected_addr.push_back(addr);
            end
            ex.write = write;
            ex.addr  = addr;
            ex.data  = write ? data : (shadow.exists(addr) ? shadow[addr] : lb_data_t'(0));
            seq.items.push_back(it);
            sb.expected.push_back(ex);
        endfunction

        // Clocks with enable high, and the longest run of them, so a test can
        // show its accesses went out back to back.
        int unsigned access_clocks;
        int unsigned longest_run;

        protected task watch_enable(mem_vif_t vif);
            int unsigned run = 0;
            forever begin
                clk_vif.sample_edge();
                if (vif.enable === 1'b1) begin
                    access_clocks++;
                    run++;
                    if (run > longest_run) longest_run = run;
                end else begin
                    run = 0;
                end
            end
        endtask
    endclass : mem_pair_test

    // n_items random accesses over 64 words, half reads, all back to back.
    // Every read must return the last word written to its address, or zero,
    // the dst model's fill, and the dst monitor must report every access in
    // order. The accesses must take n_items consecutive clocks.
    class memory_random_test extends mem_pair_test;
        `uvm_component_utils(memory_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            mem_seq      seq = mem_seq::type_id::create("seq");
            lb_data_t    shadow[lb_mem_addr_t];
            int unsigned reads;
            phase.raise_objection(this);
            for (int unsigned i = 0; i < n_items; i++) begin
                add(seq, $urandom_range(1, 0), lb_mem_addr_t'($urandom()), lb_data_t'($urandom()), shadow);
            end
            reads = seq.expected.size();
            clk_vif.wait_reset_release();
            fork
                watch_enable(src.cfg.vif);
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 4 * n_items);
            disable fork;
            if (seq.checked != reads) begin
                `uvm_error("LB_MEM", $sformatf("%0d reads sent, %0d checked", reads, seq.checked))
            end
            `uvm_info("LB_STATS", $sformatf("%0d accesses, %0d reads checked, longest run of accesses %0d clocks",
                                            sb.matched, seq.checked, longest_run), UVM_NONE)
            if (longest_run != n_items) begin
                `uvm_error("LB_MEM", $sformatf("%0d accesses should take as many consecutive clocks, the longest run was %0d",
                                               n_items, longest_run))
            end
            phase.drop_objection(this);
        endtask
    endclass : memory_random_test

    // Each address is written and read on the next clock, n_items / 2 times,
    // so every read follows the write it must return by one clock. All the
    // accesses go out through one reused item object, and each read's
    // response must still carry the address that read went to.
    class memory_write_read_test extends mem_pair_test;
        `uvm_component_utils(memory_write_read_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            mem_seq   seq = mem_seq::type_id::create("seq");
            lb_data_t shadow[lb_mem_addr_t];
            phase.raise_objection(this);
            seq.reuse = 1'b1;
            for (int unsigned i = 0; i < n_items / 2; i++) begin
                lb_mem_addr_t addr = lb_mem_addr_t'($urandom());
                add(seq, 1, addr, lb_data_t'($urandom()), shadow);
                add(seq, 0, addr, '0, shadow);
            end
            clk_vif.wait_reset_release();
            fork
                watch_enable(src.cfg.vif);
            join_none
            seq.start(src.sqr);
            wait_matched(sb, 2 * (n_items / 2), 4 * n_items);
            disable fork;
            `uvm_info("LB_STATS", $sformatf("%0d accesses, %0d reads checked, longest run of accesses %0d clocks",
                                            sb.matched, seq.checked, longest_run), UVM_NONE)
            if (seq.checked != n_items / 2) begin
                `uvm_error("LB_MEM", $sformatf("%0d reads sent, %0d checked", n_items / 2, seq.checked))
            end
            if (longest_run != 2 * (n_items / 2)) begin
                `uvm_error("LB_MEM", $sformatf("the accesses should take consecutive clocks, the longest run was %0d",
                                               longest_run))
            end
            phase.drop_objection(this);
        endtask
    endclass : memory_write_read_test

    // Two ports, mem and mem2, each with a src and a dst agent, and one
    // a2c_mem_model behind both dst agents, as a dual-port memory. The test
    // writes 32 words through mem, reads them back through mem2, then on one
    // clock writes a new word through mem and reads the same address through
    // mem2, which must return the old word, as memory_dp does.
    class memory_shared_model_test extends mem_pair_test;
        mem_agent_t src2;
        mem_agent_t dst2;

        `uvm_component_utils(memory_shared_model_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            build_pair("mem2", "src2", "dst2", mem, src2, dst2);
        endfunction

        // The clock count of the last write of address 6 through mem and of
        // the last read of it through mem2.
        int unsigned wr_clock;
        int unsigned rd_clock;

        protected task watch_same_clock();
            int unsigned clocks = 0;
            forever begin
                clk_vif.sample_edge();
                clocks++;
                if (src.cfg.vif.enable === 1'b1 && src.cfg.vif.wr_en === 1'b1 && src.cfg.vif.addr === 6) wr_clock = clocks;
                if (src2.cfg.vif.enable === 1'b1 && src2.cfg.vif.wr_en === 1'b0 && src2.cfg.vif.addr === 6) rd_clock = clocks;
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            mem_seq    wr = mem_seq::type_id::create("wr");
            mem_seq    rd = mem_seq::type_id::create("rd");
            mem_seq    wr1 = mem_seq::type_id::create("wr1");
            mem_seq    rd1 = mem_seq::type_id::create("rd1");
            mem_item_t it;
            lb_data_t  shadow[lb_mem_addr_t];
            lb_data_t  old;
            lb_data_t  unused[lb_mem_addr_t];
            phase.raise_objection(this);
            for (int unsigned i = 0; i < 32; i++) add(wr, 1, lb_mem_addr_t'(2 * i), lb_data_t'($urandom()), shadow);
            for (int unsigned i = 0; i < 32; i++) begin
                it = mem_item_t::type_id::create("it");
                it.write = 0;
                it.addr  = lb_mem_addr_t'(2 * i);
                it.data  = '0;
                rd.items.push_back(it);
                rd.expected.push_back(shadow[it.addr]);
                rd.expected_addr.push_back(it.addr);
            end
            old = shadow[lb_mem_addr_t'(6)];
            add(wr1, 1, lb_mem_addr_t'(6), ~old, unused);
            it = mem_item_t::type_id::create("it");
            it.write = 0;
            it.addr  = lb_mem_addr_t'(6);
            it.data  = '0;
            rd1.items.push_back(it);
            rd1.expected.push_back(old);
            rd1.expected_addr.push_back(lb_mem_addr_t'(6));
            clk_vif.wait_reset_release();
            wr.start(src.sqr);
            rd.start(src2.sqr);
            fork
                watch_same_clock();
            join_none
            fork
                wr1.start(src.sqr);
                rd1.start(src2.sqr);
            join
            disable fork;
            wait_matched(sb, 33, 200);
            if (wr_clock == 0 || wr_clock != rd_clock) begin
                `uvm_error("LB_MEM", $sformatf("the last write and read of address 6 went out on clocks %0d and %0d, not the same one",
                                               wr_clock, rd_clock))
            end
            `uvm_info("LB_STATS", $sformatf("%0d reads through the second port checked, %0d same-clock read",
                                            rd.checked, rd1.checked), UVM_NONE)
            if (rd.checked != 32 || rd1.checked != 1) begin
                `uvm_error("LB_MEM", $sformatf("expected 32 and 1 reads checked, got %0d and %0d", rd.checked, rd1.checked))
            end
            if (mem.read(64'd6) !== ~old) begin
                `uvm_error("LB_MEM", $sformatf("the shared model holds 0x%0h at 6 after the write of 0x%0h", mem.read(64'd6), ~old))
            end
            phase.drop_objection(this);
        endtask
    endclass : memory_shared_model_test

    // Mode B on mem and mem_model. agent, the agent under test, has mem as
    // its DUT lane and mem_model as its model lane, and each lane has a
    // single-lane peer of the other role.
    //
    // As A2C_SRC the agent sends n_items random accesses over 64 words, and
    // the peers serve them from two memories with one random fill. Both
    // lanes must report the same accesses on the same clocks, every read
    // response must carry the DUT lane's word, and model_cmp must pair every
    // access.
    //
    // As A2C_DST the peers send the same accesses, each lane with its own
    // gaps, and the agent serves both lanes from one memory with a random
    // fill. A reference applies the DUT lane's accesses once, in order, to a
    // memory with the same fill. Each lane's reads must return the words
    // model_seq and seq expect, the agent's memory must end as the reference
    // does, and model_cmp must pair every access. With split set, writes go
    // to words 32 to 63 and reads to words 0 to 31, so a model lane that
    // reads ahead of the DUT lane reads no word the DUT lane has yet to
    // write. With both_lead set, both lanes must lead some accesses.
    class memory_mode_b_test extends lb_mode_b_base;
        a2c_role_e               role = A2C_SRC;
        lb_variant_e             variant = LB_MATCH;
        bit                      split = 1;
        // Makes the last access before the drop a read, whatever the seed.
        bit                      last_read = 0;
        bit                      both_lead = 1;
        mem_agent_t              agent;
        mem_agent_t              peer;
        mem_agent_t              model_peer;
        mem_config_t             agent_cfg;
        mem_config_t             peer_cfg;
        mem_config_t             model_peer_cfg;
        mem_vif_t                vif;
        mem_vif_t                model_vif;
        lb_word_mem_t            ref_mem;
        mem_seq                  seq;
        mem_seq                  model_seq;
        lb_arrivals#(mem_item_t) arrivals;
        lb_arrivals#(mem_item_t) model_arrivals;
        int unsigned             drain_quiet = 20;
        int unsigned             drain_deadline = 400;
        int unsigned             clocks;
        int unsigned             dropped_at;
        int unsigned             pending_at_drop;
        int unsigned             model_led;
        int unsigned             tail;
        bit                      done[2];

        `uvm_component_utils(memory_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function mem_config_t lane_cfg(string name, mem_vif_t lane_vif, a2c_role_e lane_role, string port);
            mem_config_t cfg = mem_config_t::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = port;
            return cfg;
        endfunction

        protected function lb_word_mem_t random_mem(string name, bit [31:0] seed);
            lb_word_mem_t m = lb_word_mem_t::type_id::create(name);
            m.fill = A2C_MEM_FILL_RANDOM;
            m.seed = seed;
            return m;
        endfunction

        // Appends one access to both lanes' sequences, applying it to the
        // reference, and returns the DUT lane's item.
        protected function mem_item_t add(bit write, lb_mem_addr_t addr, int unsigned gap, int unsigned model_gap);
            mem_item_t it = mem_item_t::type_id::create("it");
            mem_item_t m;
            it.write = write;
            it.addr  = addr;
            it.data  = write ? lb_data_t'($urandom()) : '0;
            it.gap   = gap;
            $cast(m, it.clone());
            m.gap = model_gap;
            if (write) begin
                ref_mem.write(addr, it.data);
            end else begin
                seq.expected.push_back(ref_mem.read(addr));
                seq.expected_addr.push_back(addr);
                model_seq.expected.push_back(ref_mem.read(addr));
                model_seq.expected_addr.push_back(addr);
            end
            seq.items.push_back(it);
            model_seq.items.push_back(m);
            return it;
        endfunction

        // Edits the streams and the expectations.
        virtual function void build_streams();
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_role_e peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            bit [31:0] seed = $urandom();
            super.build_phase(phase);
            if (!uvm_config_db#(mem_vif_t)::get(this, "", "mem", vif)) `uvm_fatal("LB_CFG", "no virtual memory_if 'mem'")
            if (!uvm_config_db#(mem_vif_t)::get(this, "", "mem_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual memory_if 'mem_model'")
            agent_cfg = lane_cfg("agent_cfg", vif, role, "mem");
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, "mem");
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, "mem_model");
            ref_mem = random_mem("ref_mem", seed);
            if (role == A2C_SRC) begin
                peer_cfg.mem       = random_mem("peer_mem", seed);
                model_peer_cfg.mem = random_mem("model_peer_mem", seed);
            end else begin
                agent_cfg.mem = random_mem("agent_mem", seed);
            end
            seq       = mem_seq::type_id::create("seq");
            model_seq = mem_seq::type_id::create("model_seq");
            for (int unsigned i = 0; i < n_items + tail; i++) begin
                bit           write = $urandom_range(1, 0);
                lb_mem_addr_t addr  = lb_mem_addr_t'($urandom());
                int unsigned  gap   = $urandom_range(3, 0);
                // A busy port's accesses after the drop are reads, so the
                // DUT lane's access on the clock of the cut is a read whatever
                // the seed, and its gaps repeat 0 to 3.
                if (variant == LB_BUSY && i >= n_items) write = 0;
                if (last_read && i == n_items - 1) write = 0;
                if (role == A2C_DST && split) addr = write ? {1'b1, addr[4:0]} : {1'b0, addr[4:0]};
                case (variant)
                    LB_MODEL_LEADS: void'(add(write, addr, $urandom_range(3, 1), 0));
                    LB_BUSY:        void'(add(write, addr, i % 4, i % 4 + (i == 0)));
                    LB_TAIL:        void'(add(write, addr, 0, i == 0));
                    // Memory has no handshake, so the model lane's lag is the
                    // sum of the gap differences. It rises to 8 clocks and
                    // falls to -8 in turn, so each lane leads.
                    default: begin
                        int signed step = (i % 32 < 8 || i % 32 >= 24) ? 1 : -1;
                        if (role == A2C_SRC) void'(add(write, addr, gap, gap));
                        else if (step > 0) void'(add(write, addr, gap % 3, gap % 3 + 1));
                        else void'(add(write, addr, gap % 3 + 1, gap % 3));
                    end
                endcase
            end
            build_streams();
            uvm_config_db#(mem_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(mem_config_t)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(mem_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent          = mem_agent_t::type_id::create("agent", this);
            peer           = mem_agent_t::type_id::create("peer", this);
            model_peer     = mem_agent_t::type_id::create("model_peer", this);
            arrivals       = lb_arrivals#(mem_item_t)::type_id::create("arrivals", this);
            model_arrivals = lb_arrivals#(mem_item_t)::type_id::create("model_arrivals", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (role == A2C_SRC) begin
                peer.mon.ap.connect(arrivals.analysis_export);
                model_peer.mon.ap.connect(model_arrivals.analysis_export);
                return;
            end
            agent.mon.ap.connect(arrivals.analysis_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
            agent.drv.replay.drain_quiet_cycles    = drain_quiet;
            agent.drv.replay.drain_deadline_cycles = drain_deadline;
            tracker.logs.push_back(agent.drv.replay);
        endfunction

        protected task send(mem_agent_t src, mem_seq s, a2c_lane_e lane);
            s.start(src.sqr);
            done[lane] = 1;
        endtask

        virtual task wait_drop();
            int unsigned idle = 0;
            wait (done[A2C_DUT_LANE]);
            while (!done[A2C_MODEL_LANE] && idle < 50) begin
                int unsigned last = model_arrivals.items.size();
                clk_vif.sample_edge();
                idle = (model_arrivals.items.size() == last) ? idle + 1 : 0;
            end
            repeat (2) clk_vif.sample_edge();
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                begin
                    bit was_waiting = 0;
                    forever begin
                        clk_vif.sample_edge();
                        clocks++;
                        if (role == A2C_DST) begin
                            if (agent.drv.replay.model_waiting() && !was_waiting) model_led++;
                            was_waiting = agent.drv.replay.model_waiting();
                        end
                    end
                end
            join_none
            if (role == A2C_SRC) begin
                send(agent, seq, A2C_DUT_LANE);
                repeat (2) clk_vif.sample_edge();
            end else begin
                fork
                    send(peer, seq, A2C_DUT_LANE);
                    send(model_peer, model_seq, A2C_MODEL_LANE);
                join_none
                wait_drop();
                pending_at_drop = agent.drv.replay.pending();
            end
            dropped_at = clocks;
            phase.drop_objection(this);
        endtask

        protected function int unsigned drain_clocks();
            return clocks - dropped_at;
        endfunction

        protected function void check_memory();
            int unsigned bad = 0;
            for (int unsigned a = 0; a < 64; a++) begin
                if (ref_mem.exists(a) != agent_cfg.mem.exists(a) || ref_mem.read(a) !== agent_cfg.mem.read(a)) bad++;
            end
            if (bad != 0) `uvm_error("LB_REPLAY", $sformatf("the agent's memory differs from the reference in %0d words", bad))
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned pairs = agent.model_cmp.get_pairs();
            int unsigned n = (arrivals.items.size() < model_arrivals.items.size()) ? arrivals.items.size()
                                                                                    : model_arrivals.items.size();
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d and %0d accesses on the DUT and model lanes, %0d pairs; the model lane led %0d; %0d unreplayed at the drop; the drain took %0d clocks",
                                            arrivals.items.size(), model_arrivals.items.size(), pairs, model_led, pending_at_drop,
                                            drain_clocks()), UVM_NONE)
            check_streams(n, pairs);
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            if (seq.expected.size() != 0) begin
                `uvm_error("LB_MODE_B", $sformatf("the DUT lane's sequence left %0d reads unanswered", seq.expected.size()))
            end
            if (pairs != n) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d accesses, expected %0d", pairs, n))
            if (role == A2C_SRC) begin
                for (int unsigned i = 0; i < n; i++) begin
                    if (arrivals.at[i] != model_arrivals.at[i] || !arrivals.items[i].compare(model_arrivals.items[i])) begin
                        `uvm_error("LB_MODE_B", $sformatf("access %0d: DUT lane %s at %0t, model lane %s at %0t", i,
                                                          arrivals.items[i].convert2string(), arrivals.at[i],
                                                          model_arrivals.items[i].convert2string(), model_arrivals.at[i]))
                    end
                end
                return;
            end
            if (model_seq.expected.size() != 0) begin
                `uvm_error("LB_MODE_B", $sformatf("the model lane's sequence left %0d reads unanswered", model_seq.expected.size()))
            end
            check_memory();
            case (variant)
                LB_MATCH: begin
                    if (both_lead && (model_led == 0 || model_led >= n)) begin
                        `uvm_error("LB_MODE_B", $sformatf("the model lane led %0d of %0d accesses, so one lane never led", model_led, n))
                    end
                end
                LB_MODEL_LEADS: begin
                    if (model_led == 0) `uvm_error("LB_MODE_B", "the model lane never led")
                end
                default: ;
            endcase
        endfunction
    endclass : memory_mode_b_test

    // The model lane's peer memory holds a different word at an address the
    // agent reads before writing: one A2C_MODEL_CMP per read of it before
    // the write, and each read response still carries the DUT lane's word,
    // which seq checks.
    class memory_mode_b_mismatch_test extends memory_mode_b_test;
        `uvm_component_utils(memory_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            bit           written[lb_mem_addr_t];
            lb_mem_addr_t addr;
            bit           found = 0;
            foreach (seq.items[i]) begin
                mem_item_t it = seq.items[i];
                if (found && it.addr == addr && it.write) break;
                if (it.write) begin
                    written[it.addr] = 1;
                end else if (!found && !written.exists(it.addr)) begin
                    found = 1;
                    addr  = it.addr;
                    model_peer_cfg.mem.write(addr, ~ref_mem.read(addr));
                end
                // Every read of addr before its first write mismatches.
                if (found && it.addr == addr) begin
                    want_errors++;
                    want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", i + 1));
                end
            end
            if (!found) `uvm_fatal("LB_RAND", "no read before a write of its address")
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            if (pairs != n) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d accesses, expected %0d", pairs, n))
        endfunction
    endclass : memory_mode_b_mismatch_test

    // The DUT lane's peer memory returns X for every word nothing wrote, as
    // memory_sp does, and the model lane's peer memory returns zero. After
    // n_items writes, reads of unwritten words, each followed by: a write of
    // its address, which passes; a read of another address; a write of
    // another address; a read of its address; and nothing, at the end of
    // the run. One A2C_MODEL_CMP for each of the last four.
    class memory_mode_b_xz_test extends memory_mode_b_test;
        `uvm_component_utils(memory_mode_b_xz_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // What the DUT lane's peer memory will hold.
        protected lb_data_t shadow[lb_mem_addr_t];

        protected function void add_x(bit write, lb_mem_addr_t addr);
            mem_item_t it = mem_item_t::type_id::create("it");
            it.write = write;
            it.addr  = addr;
            it.data  = write ? lb_data_t'($urandom()) : '0;
            if (write) begin
                shadow[addr] = it.data;
            end else begin
                seq.expected.push_back(shadow.exists(addr) ? shadow[addr] : lb_data_t'('x));
                seq.expected_addr.push_back(addr);
            end
            seq.items.push_back(it);
        endfunction

        virtual function void build_streams();
            // The X reads that a write of their address does not follow.
            int unsigned bad[3] = '{3, 5, 7};
            peer_cfg.mem.fill       = A2C_MEM_FILL_FIXED;
            peer_cfg.mem.fill_value = 'x;
            model_peer_cfg.mem.fill = A2C_MEM_FILL_ZERO;
            // Only writes before the X reads, so every read has an answer
            // on both lanes that does not depend on the fill.
            seq.items.delete();
            seq.expected.delete();
            seq.expected_addr.delete();
            for (int unsigned i = 0; i < n_items; i++) add_x(1, lb_mem_addr_t'(i % 32));
            add_x(0, 6'd40);
            add_x(1, 6'd40);
            add_x(0, 6'd41);
            add_x(0, 6'd3);
            add_x(0, 6'd43);
            add_x(1, 6'd44);
            add_x(0, 6'd45);
            add_x(0, 6'd45);
            add_x(1, 6'd45);
            add_x(0, 6'd42);
            want_errors = 4;
            foreach (bad[i]) want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", n_items + bad[i]));
            want_text.push_back("end of test with a read of X or Z that no access followed");
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            // The read at the end of the run is held, not paired.
            if (pairs != n - 1) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d accesses, expected %0d", pairs, n - 1))
        endfunction
    endclass : memory_mode_b_xz_test

    class memory_mode_b_dst_test extends memory_mode_b_test;
        `uvm_component_utils(memory_mode_b_dst_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_DST;
        endfunction
    endclass : memory_mode_b_dst_test

    // The model lane's peer issues every access on the first clock it can
    // and the DUT lane's peer one to three clocks later, so the model lane
    // reads ahead.
    class memory_mode_b_dst_model_leads_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_model_leads_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_MODEL_LEADS;
        endfunction
    endclass : memory_mode_b_dst_model_leads_test

    // Reads and writes over all 64 words, with the model lane four clocks
    // behind the DUT lane, so every read of a word the DUT lane wrote gets
    // that word replayed.
    class memory_mode_b_dst_dut_leads_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_dut_leads_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            split     = 0;
            both_lead = 0;
        endfunction

        virtual function void build_streams();
            foreach (model_seq.items[i]) model_seq.items[i].gap = seq.items[i].gap + 4 * (i == 0);
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            super.check_streams(n, pairs);
            if (model_led != 0) `uvm_error("LB_MODE_B", $sformatf("the model lane led %0d accesses", model_led))
        endfunction
    endclass : memory_mode_b_dst_dut_leads_test

    // The model lane's peer writes different data in one write: one
    // A2C_MODEL_CMP, and the agent's memory holds the DUT lane's data. The
    // write is the last to its address, made while the model lane lags, so
    // a model lane that applied it would leave its data in the memory.
    class memory_mode_b_dst_mismatch_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            bit written[lb_mem_addr_t];
            for (int i = model_seq.items.size() - 1; i >= 0; i--) begin
                mem_item_t it = model_seq.items[i];
                if (!it.write) continue;
                // The gap schedule has the model lane behind here.
                if (i % 32 >= 1 && i % 32 < 15 && !written.exists(it.addr)) begin
                    it.data = ~it.data;
                    want_errors = 1;
                    want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT ", i + 1));
                    return;
                end
                written[it.addr] = 1;
            end
            `uvm_fatal("LB_RAND", "no last write to an address while the model lane lags")
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            if (pairs != n) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d accesses, expected %0d", pairs, n))
            check_memory();
        endfunction
    endclass : memory_mode_b_dst_mismatch_test

    // As memory_mode_b_dst_test with reads and writes over all 64 words, so
    // a model lane that leads reads words the DUT lane has yet to write,
    // some of them words the model lane wrote first.
    class memory_mode_b_dst_unsplit_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_unsplit_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            split = 0;
        endfunction
    endclass : memory_mode_b_dst_unsplit_test

    // The lanes run in step, then the model lane writes word 33 and reads it
    // back 8 clocks before the DUT lane makes either access. Its read must
    // return the word it wrote, as the DUT lane's does, with no A2C_REPLAY.
    class memory_mode_b_dst_write_read_ahead_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_write_read_ahead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_REPLAY";
        endfunction

        virtual function void build_streams();
            // Memory has no handshake, so with the same gaps the lanes stay
            // in step, and the write's gaps put the model lane 8 clocks ahead.
            foreach (model_seq.items[i]) model_seq.items[i].gap = seq.items[i].gap;
            void'(add(1, 6'd33, 8, 0));
            void'(add(0, 6'd33, 0, 0));
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            super.check_streams(n, pairs);
            if (model_led == 0) `uvm_error("LB_MODE_B", "the model lane never led, so its read ahead went untested")
        endfunction
    endclass : memory_mode_b_dst_write_read_ahead_test

    // As memory_mode_b_dst_write_read_ahead_test, with the model lane
    // writing word 33 twice ahead of the DUT lane and reading it between
    // the DUT lane's two writes. The DUT lane's first write must leave the
    // model lane's second in place, so the read returns it.
    class memory_mode_b_dst_rewrite_ahead_test extends memory_mode_b_dst_write_read_ahead_test;
        `uvm_component_utils(memory_mode_b_dst_rewrite_ahead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // The model lane writes at clocks t and t+1 and reads at t+6; the
        // DUT lane writes at t+4 and t+11 and reads at t+12.
        virtual function void build_streams();
            foreach (model_seq.items[i]) model_seq.items[i].gap = seq.items[i].gap;
            void'(add(1, 6'd33, 4, 0));
            void'(add(1, 6'd33, 6, 0));
            void'(add(0, 6'd33, 0, 4));
        endfunction
    endclass : memory_mode_b_dst_rewrite_ahead_test

    // As memory_mode_b_dst_write_read_ahead_test, with the model lane's
    // peer writing different data: its read returns its own word, which
    // differs from the DUT lane's. One A2C_REPLAY when the DUT lane makes
    // the read, model_cmp reports the write and the read, and the agent's
    // memory holds the DUT lane's word.
    class memory_mode_b_dst_stale_test extends memory_mode_b_dst_write_read_ahead_test;
        `uvm_component_utils(memory_mode_b_dst_stale_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            int unsigned k = seq.items.size();
            mem_item_t   w;
            super.build_streams();
            w = model_seq.items[k];
            w.data = ~w.data;
            void'(model_seq.expected.pop_back());
            model_seq.expected.push_back(w.data);
            want_errors = 1;
            // The read follows the write at index k, counting from 0.
            want_text.push_back($sformatf("mem: the model lane read index 0x21 at access %0d before the DUT lane made that access", k + 2));
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.set_report_severity_id_override(UVM_ERROR, "A2C_MODEL_CMP", UVM_INFO);
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            uvm_report_server srv = uvm_report_server::get_server();
            if (pairs != n) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d accesses, expected %0d", pairs, n))
            if (srv.get_id_count("A2C_MODEL_CMP") != 2) begin
                `uvm_error("LB_MODE_B", $sformatf("expected two A2C_MODEL_CMP, for the write and the read, got %0d", srv.get_id_count("A2C_MODEL_CMP")))
            end
            check_memory();
        endfunction
    endclass : memory_mode_b_dst_stale_test

    // As memory_mode_b_dst_stale_test after a master elsewhere declared the
    // model lane dead on the first clock, so the report names the death.
    class memory_mode_b_dst_stale_dead_test extends memory_mode_b_dst_stale_test;
        `uvm_component_utils(memory_mode_b_dst_stale_dead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_text.push_back("; the model lane of uvm_test_top was declared dead at ");
            want_text.push_back(" (A2C_SKEW), which may be related");
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                begin
                    clk_vif.wait_reset_release();
                    clk_vif.sample_edge();
                    a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
                end
            join_none
            super.run_phase(phase);
        endtask
    endclass : memory_mode_b_dst_stale_dead_test

    // As memory_mode_b_dst_stale_test with the death after the run, which
    // the report therefore does not name.
    class memory_mode_b_dst_stale_dead_after_test extends memory_mode_b_dst_stale_test;
        `uvm_component_utils(memory_mode_b_dst_stale_dead_after_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            unwant_text.push_back("which may be related");
        endfunction

        virtual task run_phase(uvm_phase phase);
            super.run_phase(phase);
            a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
        endtask
    endclass : memory_mode_b_dst_stale_dead_after_test

    // The model lane's peer makes one access more, which the DUT lane never
    // records: the drain runs to its deadline, and the replay log reports
    // the wait in one A2C_REPLAY.
    class memory_mode_b_dst_model_extra_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_model_extra_test)

        // UVM ends the run phase after 20 rounds of phase_ready_to_end(), so
        // a deadline beyond 20 quiet windows tells a drain that waits for
        // the model lane from drains that each end on a quiet window.
        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id      = "A2C_REPLAY";
            drain_deadline = 1000;
        endfunction

        virtual function void build_streams();
            mem_item_t it = mem_item_t::type_id::create("it");
            it.write = 0;
            it.addr  = 6'd5;
            model_seq.items.push_back(it);
            model_seq.expected.push_back(ref_mem.read(6'd5));
            model_seq.expected_addr.push_back(6'd5);
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.drv.replay: the model lane waited for transaction %0d, which the DUT lane never recorded",
                                          n_items + 1));
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            if (pairs != n_items) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d accesses, expected %0d", pairs, n_items))
            // The clock counter races the drain on each edge, so it may be one off.
            if (drain_clocks() + 1 < drain_deadline || drain_clocks() > drain_deadline + 1) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected its deadline of %0d", drain_clocks(), drain_deadline))
            end
        endfunction

        // The extra access is unpaired by design.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.counted = 1;
        endfunction
    endclass : memory_mode_b_dst_model_extra_test

    // The test drops its objection when the DUT lane is done, 60 clocks
    // before the model lane's last access: the drain must hold the run phase
    // until the model lane has made it, with no A2C_REPLAY.
    class memory_mode_b_dst_drain_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_DRAIN;
        endfunction

        virtual function void build_streams();
            model_seq.items[n_items - 1].gap = 60;
        endfunction

        virtual task wait_drop();
            wait (done[A2C_DUT_LANE]);
            // The DUT lane's last read is answered on the next clock.
            repeat (2) clk_vif.sample_edge();
        endtask

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            super.check_streams(n, pairs);
            if (pending_at_drop == 0) `uvm_error("LB_MODE_B", "the model lane had replayed every access at the drop, so the drain went untested")
        endfunction
    endclass : memory_mode_b_dst_drain_test

    // As memory_mode_b_dst_drain_test with a quiet window of one clock, and
    // the model lane's last access a read. The clock that samples that read
    // finds nothing pending, so only the model lane's access in progress
    // keeps the window from closing before the read data is driven.
    class memory_mode_b_dst_drain_short_quiet_test extends memory_mode_b_dst_drain_test;
        `uvm_component_utils(memory_mode_b_dst_drain_short_quiet_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            drain_quiet = 1;
            last_read   = 1;
        endfunction
    endclass : memory_mode_b_dst_drain_short_quiet_test

    // Both peers keep accessing the memory after the test drops its
    // objection, the model lane a clock behind with the same gaps, so the
    // drain's quiet window never comes. It must cut the run at its
    // deadline, after the accesses the DUT lane has made then, and end once
    // both lanes have made them, with no A2C_REPLAY.
    class memory_mode_b_dst_drain_busy_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_drain_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant        = LB_BUSY;
            tail           = 10 * n_items;
            drain_quiet    = 30;
            drain_deadline = 300;
            demote_id      = "A2C_REPLAY";
        endfunction

        virtual task wait_drop();
            while (arrivals.items.size() < n_items) clk_vif.sample_edge();
        endtask

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            check_cut(agent.drv.replay, n_items, pairs, arrivals.items.size(), model_arrivals.items.size());
            if (arrivals.items.size() <= n_items) `uvm_error("LB_MODE_B", "the DUT lane's peer stopped at the drop, so the busy port went untested")
            if (arrivals.items.size() >= seq.items.size()) `uvm_error("LB_MODE_B", "the DUT lane's peer ran out of accesses, so the port paused")
            check_cut_time(drain_clocks(), drain_quiet, drain_deadline);
        endfunction
    endclass : memory_mode_b_dst_drain_busy_test

    // As memory_mode_b_dst_drain_busy_test with no gaps on either lane, so
    // both lanes access the memory on every clock from the start of the
    // test to its end.
    class memory_mode_b_dst_drain_busy_zero_test extends memory_mode_b_dst_drain_busy_test;
        `uvm_component_utils(memory_mode_b_dst_drain_busy_zero_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            foreach (seq.items[i]) begin
                seq.items[i].gap       = 0;
                model_seq.items[i].gap = 0;
            end
        endfunction
    endclass : memory_mode_b_dst_drain_busy_zero_test

    // As memory_mode_b_dst_drain_busy_zero_test, with a passive Mode B agent
    // watching the port: the drain's cut must cut its model_cmp too, so it
    // pairs what the agent pairs and reports no unpaired access. The model
    // lane pauses 10 clocks after the drop, so the DUT lane makes accesses
    // past the cut while the model lane catches up.
    class memory_mode_b_dst_busy_passive_test extends memory_mode_b_dst_drain_busy_zero_test;
        mem_agent_t watcher;

        `uvm_component_utils(memory_mode_b_dst_busy_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            super.build_streams();
            model_seq.items[n_items + 20].gap += 10;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            mem_config_t cfg;
            super.build_phase(phase);
            cfg = lane_cfg("watcher_cfg", vif, A2C_DST, "mem");
            cfg.model_vif = model_vif;
            cfg.is_active = UVM_PASSIVE;
            uvm_config_db#(mem_config_t)::set(this, "watcher", "cfg", cfg);
            watcher = mem_agent_t::type_id::create("watcher", this);
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (watcher.drv != null) `uvm_error("LB_MODE_B", "the passive agent built a driver")
            if (agent.model_cmp.get_pairs() == 0 || watcher.model_cmp.get_pairs() != agent.model_cmp.get_pairs()) begin
                `uvm_error("LB_MODE_B", $sformatf("the passive agent's model_cmp paired %0d transfers, the agent's %0d", watcher.model_cmp.get_pairs(),
                                                  agent.model_cmp.get_pairs()))
            end
            if (arrivals.items.size() <= agent.drv.replay.get_cut()) begin
                `uvm_error("LB_MODE_B", "the DUT lane made no access past the cut, so the passive agent's cut went untested")
            end
        endfunction
    endclass : memory_mode_b_dst_busy_passive_test

    // As memory_mode_b_dst_drain_busy_zero_test with the model lane two
    // clocks behind, so on no clock do the lanes make the same access.
    class memory_mode_b_dst_drain_busy_lag_test extends memory_mode_b_dst_drain_busy_zero_test;
        `uvm_component_utils(memory_mode_b_dst_drain_busy_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            super.build_streams();
            model_seq.items[0].gap = 2;
        endfunction
    endclass : memory_mode_b_dst_drain_busy_lag_test

    // As memory_mode_b_dst_drain_busy_zero_test with the model lane two
    // clocks ahead, so it makes each access before the DUT lane has
    // recorded it. The model lane has completed the cut's last access, a
    // read, by the clock of the cut, and the DUT lane completes it at the
    // drive point after, so the drain must wait for the DUT lane too.
    class memory_mode_b_dst_drain_busy_lead_test extends memory_mode_b_dst_drain_busy_zero_test;
        `uvm_component_utils(memory_mode_b_dst_drain_busy_lead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            super.build_streams();
            seq.items[0].gap = 2;
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            super.check_streams(n, pairs);
            if (model_led == 0) `uvm_error("LB_MODE_B", "the model lane never led, so the lead went untested")
        endfunction
    endclass : memory_mode_b_dst_drain_busy_lead_test

    // As memory_mode_b_dst_drain_busy_lag_test with the model lane 45
    // clocks behind, more than the quiet window of 30, as a DMA model with
    // a long latency may run. The drain cuts the run at its deadline, and
    // the model lane must have the default catch-up, the deadline of 300
    // clocks, to complete the accesses the cut keeps: no A2C_REPLAY, and
    // the drain ends about 45 clocks after the cut.
    class memory_mode_b_dst_drain_busy_far_lag_test extends memory_mode_b_dst_drain_busy_zero_test;
        int unsigned lag = 45;

        `uvm_component_utils(memory_mode_b_dst_drain_busy_far_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            super.build_streams();
            model_seq.items[0].gap = lag;
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            check_cut(agent.drv.replay, n_items, pairs, arrivals.items.size(), model_arrivals.items.size());
            // The clock counter races the drain on each edge, so it may be
            // a clock off.
            if (drain_clocks() + 1 < drain_deadline + lag || drain_clocks() > drain_deadline + lag + 2) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected a cut at its deadline of %0d and an end %0d clocks later",
                                                  drain_clocks(), drain_deadline, lag))
            end
        endfunction
    endclass : memory_mode_b_dst_drain_busy_far_lag_test

    // As memory_mode_b_dst_drain_busy_far_lag_test with a catch-up of 20
    // clocks, set as uvm_config_int, the type +uvm_set_config_int uses. The
    // model lane is 45 clocks behind at the cut, so the drain gives the log
    // up 20 clocks after the cut: one A2C_REPLAY naming the catch-up.
    class memory_mode_b_dst_drain_catchup_cfg_test extends memory_mode_b_dst_drain_busy_far_lag_test;
        `uvm_component_utils(memory_mode_b_dst_drain_catchup_cfg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("did not both complete it in the 20 clocks after the cut (drain_catchup_cycles, +a2c_drain_catchup_cycles)");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            uvm_config_int::set(this, "agent.drv.replay", "a2c_drain_catchup_cycles", 20);
        endfunction

        // The replay log reports the shortfall.
        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.counted = 1;
        endfunction

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            if (agent.drv.replay.get_cut() == 0) `uvm_error("LB_MODE_B", "the drain did not cut the run")
            if (drain_clocks() + 1 < drain_deadline + 20 || drain_clocks() > drain_deadline + 22) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected a cut at its deadline of %0d and the give-up 20 clocks later",
                                                  drain_clocks(), drain_deadline))
            end
        endfunction
    endclass : memory_mode_b_dst_drain_catchup_cfg_test

    // The model lane's second-to-last access is 40 clocks late, so the first
    // drain, with a deadline of 10 clocks, expires with it pending. On the
    // second phase_ready_to_end() call, when that drain drops, the test
    // holds the run phase until the model lane has made the late access,
    // raises the deadline, sends the last access with the model lane 30
    // clocks behind, and drops when the DUT lane has made it. The model lane
    // started an access after the expiry, so only a second drain keeps the
    // run phase alive until it replays the last: no A2C_REPLAY.
    class memory_mode_b_dst_after_expiry_test extends memory_mode_b_dst_test;
        mem_seq      last;
        mem_seq      model_last;
        int unsigned ready_calls;
        int unsigned resumed_at;
        int unsigned pending_at_second_drop;

        `uvm_component_utils(memory_mode_b_dst_after_expiry_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_AFTER_EXPIRY;
        endfunction

        protected function void split_last(mem_seq from, mem_seq to);
            mem_item_t it = from.items.pop_back();
            to.items.push_back(it);
            if (it.write) return;
            to.expected.push_back(from.expected.pop_back());
            to.expected_addr.push_back(from.expected_addr.pop_back());
        endfunction

        virtual function void build_streams();
            int unsigned n = seq.items.size();
            drain_quiet    = 10;
            drain_deadline = 10;
            model_seq.items[n - 2].gap = 40;
            last       = mem_seq::type_id::create("last");
            model_last = mem_seq::type_id::create("model_last");
            split_last(seq, last);
            split_last(model_seq, model_last);
            model_last.items[0].gap = 30;
        endfunction

        virtual task wait_drop();
            while (arrivals.items.size() < n_items - 1) clk_vif.sample_edge();
        endtask

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() != uvm_run_phase::get()) return;
            ready_calls++;
            if (ready_calls != 2) return;
            resumed_at = clocks;
            phase.raise_objection(this, "the last access");
            fork last_round(phase); join_none
        endfunction

        protected task last_round(uvm_phase phase);
            while (model_arrivals.items.size() < n_items - 1) clk_vif.sample_edge();
            agent.drv.replay.drain_deadline_cycles = 400;
            fork
                last.start(peer.sqr);
                model_last.start(model_peer.sqr);
            join_none
            while (arrivals.items.size() < n_items) clk_vif.sample_edge();
            pending_at_second_drop = agent.drv.replay.pending();
            phase.drop_objection(this, "the DUT lane made the last access");
        endtask

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            super.check_streams(n, pairs);
            `uvm_info("LB_STATS", $sformatf("%0d phase_ready_to_end calls; the first drain took %0d clocks; %0d unreplayed at the second drop",
                                            ready_calls, resumed_at - dropped_at, pending_at_second_drop), UVM_NONE)
            if (n != n_items) `uvm_error("LB_MODE_B", $sformatf("%0d accesses on both lanes, expected %0d", n, n_items))
            if (last.expected.size() != 0 || model_last.expected.size() != 0) `uvm_error("LB_MODE_B", "the last read went unanswered")
            if (ready_calls < 2) `uvm_error("LB_MODE_B", "the first drain never dropped, so the second round never ran")
            // The clock counter races the drain on each edge, so it may be one off.
            if (resumed_at - dropped_at + 1 < 10 || resumed_at - dropped_at > 11) begin
                `uvm_error("LB_MODE_B", $sformatf("the first drain took %0d clocks, expected its deadline of 10", resumed_at - dropped_at))
            end
            if (pending_at_second_drop == 0) begin
                `uvm_error("LB_MODE_B", "the model lane had replayed the last access at the second drop, so the second drain went untested")
            end
        endfunction
    endclass : memory_mode_b_dst_after_expiry_test

    // As memory_mode_b_dst_drain_busy_test with one idle clock before every
    // access on both lanes and the model lane a clock behind, so the lanes
    // take turns: on no clock do both make an access. The drain must still
    // cut the run at its deadline.
    class memory_mode_b_dst_drain_busy_interleave_test extends memory_mode_b_dst_drain_busy_test;
        `uvm_component_utils(memory_mode_b_dst_drain_busy_interleave_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            foreach (seq.items[i]) begin
                seq.items[i].gap       = 1;
                model_seq.items[i].gap = 1 + (i == 0);
            end
        endfunction
    endclass : memory_mode_b_dst_drain_busy_interleave_test

    // Both peers make 60 accesses more after the drop with no gaps, the
    // model lane a clock behind, and stop well before the deadline. The
    // drain must wait out the tail and check all of it, with no cut.
    class memory_mode_b_dst_tail_test extends memory_mode_b_dst_test;
        `uvm_component_utils(memory_mode_b_dst_tail_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant        = LB_TAIL;
            tail           = 60;
            drain_quiet    = 30;
            drain_deadline = 400;
        endfunction

        virtual task wait_drop();
            while (arrivals.items.size() < n_items) clk_vif.sample_edge();
        endtask

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            super.check_streams(n, pairs);
            if (agent.drv.replay.get_cut() != 0) `uvm_error("LB_MODE_B", "the drain cut a port that paused before its deadline")
            if (n != n_items + 60) `uvm_error("LB_MODE_B", $sformatf("%0d accesses on both lanes, expected %0d", n, n_items + 60))
            if (drain_clocks() >= drain_deadline) `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, its whole deadline", drain_clocks()))
        endfunction
    endclass : memory_mode_b_dst_tail_test

    // Both lanes access the memory on every clock of clk3, in step, as in
    // memory_mode_b_dst_drain_busy_zero_test, and clk3 stops low at the
    // sample edge after the DUT lane's 400th access, with enable high on
    // both lanes: a DUT that stops its clock with an access presented. A
    // memory port has no handshake, so only lane_busy() tells the drain
    // that the access sampled there is never served. The drain must give
    // the log up with one A2C_DRAIN for the stopped clock, not settle it.
    class memory_mode_b_dst_clock_stop_busy_test extends memory_mode_b_dst_test;
        virtual a2c_clk_if clk3_vif;
        lb_id_counter      drains;
        bit                enabled[2];
        bit                busy_at_end[2];

        `uvm_component_utils(memory_mode_b_dst_clock_stop_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_BUSY;
            tail    = n_items;
        endfunction

        virtual function void build_streams();
            foreach (seq.items[i]) begin
                seq.items[i].gap       = 0;
                model_seq.items[i].gap = 0;
            end
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk3", clk3_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk3'")
            // The agents read these in their own build_phase(), after this.
            agent_cfg.clk_vif      = clk3_vif;
            peer_cfg.clk_vif       = clk3_vif;
            model_peer_cfg.clk_vif = clk3_vif;
            drains = lb_id_counter::type_id::create("drains");
            drains.id = "A2C_DRAIN";
            uvm_report_cb::add(null, drains);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.drv.replay.clock_stop_cycles = 10;
        endfunction

        virtual task wait_drop();
            while (arrivals.items.size() < n_items) clk3_vif.sample_edge();
            lb_clk3_run = 0;
            enabled[A2C_DUT_LANE]   = vif.enable === 1'b1;
            enabled[A2C_MODEL_LANE] = model_vif.enable === 1'b1;
        endtask

        virtual function void check_streams(int unsigned n, int unsigned pairs);
            foreach (busy_at_end[l]) busy_at_end[l] = agent.drv.lane_busy(a2c_lane_e'(l));
            `uvm_info("LB_STATS", $sformatf("enable %p and lanes busy %p at the stop; %0d A2C_DRAIN: %p", enabled, busy_at_end, drains.warnings,
                                            drains.messages), UVM_NONE)
            if (!enabled[A2C_DUT_LANE] || !enabled[A2C_MODEL_LANE]) `uvm_error("LB_MODE_B", "clk3 stopped with enable low on a lane")
            if (!busy_at_end[A2C_DUT_LANE] || !busy_at_end[A2C_MODEL_LANE]) `uvm_error("LB_MODE_B", "a lane was not inside an access at the end")
            if (drains.warnings != 1 || !a2c_contains(drains.messages[0], "the clock stopped before the log settled")) begin
                `uvm_error("LB_MODE_B", $sformatf("expected one A2C_DRAIN for clk3's stop: %p", drains.messages))
            end
        endfunction
    endclass : memory_mode_b_dst_clock_stop_busy_test
