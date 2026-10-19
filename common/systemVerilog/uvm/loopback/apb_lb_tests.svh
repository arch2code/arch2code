// apb agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef logic [31:0] lb_apb_word_t;
    typedef apb_agent #(.addr_t(lb_apb_word_t), .data_t(lb_apb_word_t)) apb_agent_t;
    typedef apb_agent_t::item_t apb_item_t;
    typedef apb_agent_t::config_t apb_config_t;
    typedef virtual apb_if #(.addr_t(lb_apb_word_t), .data_t(lb_apb_word_t)) apb_vif_t;

    // Random word-aligned reads and writes below 'h200. After each transfer
    // the sequence checks it against the slave's memory: a write must have
    // stored its bytes, a read must return the stored bytes, and a transfer
    // in an error range must have pslverr and leave its bytes unwritten. The
    // slave's monitor must have reported the same transfer by then, because
    // it samples the completing clock before the master driver ends the item.
    class apb_check_seq extends uvm_sequence #(apb_item_t);
        int unsigned                         n;
        apb_mem_t                            mem;
        apb_addr_range_t                     error_ranges[$];
        uvm_tlm_analysis_fifo #(apb_item_t) observed;
        int unsigned                         reads;
        int unsigned                         writes;
        int unsigned                         errors;
        int unsigned                         matched;

        `uvm_object_utils(apb_check_seq)

        function new(string name = "apb_check_seq");
            super.new(name);
        endfunction

        function bit in_error_range(bit [31:0] addr);
            foreach (error_ranges[i]) begin
                if (addr >= error_ranges[i].lo && addr <= error_ranges[i].hi) return 1;
            end
            return 0;
        endfunction

        virtual task body();
            apb_item_t it;
            apb_item_t seen;
            bit [31:0] stored;
            bit        error;
            repeat (n) begin
                it = apb_item_t::type_id::create("it");
                start_item(it);
                if (!it.randomize() with { addr < 32'h200; addr[1:0] == 2'b00; }) `uvm_fatal("LB_RAND", "apb item randomize failed")
                finish_item(it);
                if (!observed.try_get(seen)) begin
                    `uvm_error("LB_MISSING", $sformatf("%s: the slave's monitor did not report it", it.convert2string()))
                end else if (!seen.compare(it)) begin
                    `uvm_error("LB_MISMATCH", $sformatf("sent %s, the slave's monitor reported %s", it.convert2string(),
                                                        seen.convert2string()))
                end else begin
                    matched++;
                end
                error = in_error_range(it.addr);
                for (int unsigned b = 0; b < 4; b++) stored[8 * b +: 8] = mem.read(it.addr + b);
                if (it.slverr !== error) begin
                    `uvm_error("LB_APB", $sformatf("%s: pslverr %0d, expected %0d", it.convert2string(), it.slverr, error))
                end
                if (error) begin
                    errors++;
                    if (it.write && mem.exists(it.addr)) begin
                        `uvm_error("LB_APB", $sformatf("%s: a write in an error range stored its bytes", it.convert2string()))
                    end
                end else if (it.write) begin
                    writes++;
                    if (stored !== it.data) `uvm_error("LB_APB", $sformatf("%s: memory holds 0x%08h", it.convert2string(), stored))
                end else begin
                    reads++;
                    if (stored !== it.data) `uvm_error("LB_APB", $sformatf("%s: memory holds 0x%08h", it.convert2string(), stored))
                end
            end
        endtask
    endclass : apb_check_seq

    // A master agent drives a slave agent on one bus. The slave's memory
    // has the random fill, so reads of unwritten words check that the fill
    // returns the same bytes the sequence reads back from the model. With
    // the default max_wait of 0 every transfer takes two clocks, so the
    // test also counts access clocks with pready low and expects none.
    class apb_random_test extends lb_base_test;
        apb_agent_t                         master;
        apb_agent_t                         slave;
        apb_config_t                        slave_cfg;
        uvm_tlm_analysis_fifo #(apb_item_t) observed;
        apb_check_seq                       seq;
        int unsigned                        wait_clocks;
        int unsigned                        max_run;

        `uvm_component_utils(apb_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_slave(apb_config_t cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            apb_config_t master_cfg;
            apb_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb", vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb'")
            master_cfg = apb_config_t::type_id::create("master_cfg");
            master_cfg.vif       = vif;
            master_cfg.clk_vif   = clk_vif;
            master_cfg.role      = A2C_SRC;
            master_cfg.port_name = "apb";
            slave_cfg = apb_config_t::type_id::create("slave_cfg");
            slave_cfg.vif       = vif;
            slave_cfg.clk_vif   = clk_vif;
            slave_cfg.role      = A2C_DST;
            slave_cfg.port_name = "apb";
            slave_cfg.mem       = apb_mem_t::type_id::create("slave_mem");
            slave_cfg.mem.fill  = A2C_MEM_FILL_RANDOM;
            configure_slave(slave_cfg);
            uvm_config_db#(apb_config_t)::set(this, "master", "cfg", master_cfg);
            uvm_config_db#(apb_config_t)::set(this, "slave", "cfg", slave_cfg);
            master   = apb_agent_t::type_id::create("master", this);
            slave    = apb_agent_t::type_id::create("slave", this);
            observed = new("observed", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            slave.mon.ap.connect(observed.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            seq = apb_check_seq::type_id::create("seq");
            seq.n            = n_items;
            seq.mem          = slave_cfg.mem;
            seq.error_ranges = slave_cfg.error_ranges;
            seq.observed     = observed;
            clk_vif.wait_reset_release();
            fork
                watch_wait_clocks();
            join_none
            seq.start(master.sqr);
            repeat (2) clk_vif.sample_edge();
            disable fork;
            phase.drop_objection(this);
        endtask

        // Counts the access clocks pready held back, in all and per transfer.
        protected task watch_wait_clocks();
            int unsigned run = 0;
            forever begin
                clk_vif.sample_edge();
                if (slave_cfg.vif.psel === 1'b1 && slave_cfg.vif.penable === 1'b1 && slave_cfg.vif.pready !== 1'b1) begin
                    wait_clocks++;
                    run++;
                    if (run > max_run) max_run = run;
                end else begin
                    run = 0;
                end
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transfers matched: %0d reads, %0d writes, %0d errors; %0d wait clocks, at most %0d in a row",
                                            seq.matched, seq.reads, seq.writes, seq.errors, wait_clocks, max_run), UVM_NONE)
            if (seq.matched != n_items) `uvm_error("LB_APB", $sformatf("matched %0d of %0d transfers", seq.matched, n_items))
            if (observed.used() != 0) `uvm_error("LB_EXTRA", $sformatf("the slave's monitor reported %0d transfers the master never sent",
                                                                     observed.used()))
            check_counts();
        endfunction

        virtual function void check_counts();
            if (wait_clocks != 0) `uvm_error("LB_APB", $sformatf("max_wait 0 but pready held back %0d access clocks", wait_clocks))
            if (seq.reads == 0 || seq.writes == 0) `uvm_error("LB_APB", "the sequence did not both read and write")
        endfunction
    endclass : apb_random_test

    // As apb_random_test, with up to three wait clocks per transfer and an
    // error range over 'h100 to 'h17f.
    class apb_wait_error_test extends apb_random_test;
        `uvm_component_utils(apb_wait_error_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_slave(apb_config_t cfg);
            cfg.max_wait = 3;
            cfg.error_ranges.push_back('{lo: 32'h100, hi: 32'h17f});
        endfunction

        virtual function void check_counts();
            if (wait_clocks == 0) `uvm_error("LB_APB", "max_wait 3 but pready never held a transfer back")
            if (max_run > 3) `uvm_error("LB_APB", $sformatf("max_wait 3 but pready held one transfer back %0d clocks", max_run))
            if (seq.errors == 0) `uvm_error("LB_APB", "no transfer fell in the error range")
            if (seq.reads == 0 || seq.writes == 0) `uvm_error("LB_APB", "the sequence did not both read and write")
        endfunction
    endclass : apb_wait_error_test

    // A passive monitor watches pins the test drives by hand, both master
    // and slave: a clean write and a read back, psel and penable from idle,
    // completed in that clock, penable with psel low, which a completer that
    // is not selected ignores, three transfers that change paddr, pwrite and
    // pwdata between the setup and access phases, a transfer whose psel
    // drops while pready is low, and one whose psel drops straight after the
    // setup phase. Expects exactly one A2C_PROTO and five A2C_HOLD reports,
    // demoted to info, and the six completed transfers reported.
    class apb_monitor_checks_test extends lb_base_test;
        apb_agent_t                obs;
        lb_scoreboard#(apb_item_t) sb;
        apb_vif_t                  vif;

        `uvm_component_utils(apb_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            apb_config_t cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb", vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb'")
            cfg = apb_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "apb";
            uvm_config_db#(apb_config_t)::set(this, "obs", "cfg", cfg);
            obs = apb_agent_t::type_id::create("obs", this);
            sb  = lb_scoreboard#(apb_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(sb.imp);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
        endfunction

        // One clock per call: the pins as the next rising edge sees them.
        task drive(bit sel, bit enable, bit write, bit [31:0] addr, bit [31:0] wdata, bit ready,
                   bit [31:0] rdata = 0);
            vif.psel    <= sel;
            vif.penable <= enable;
            vif.pwrite  <= write;
            vif.paddr   <= addr;
            vif.pwdata  <= wdata;
            vif.pready  <= ready;
            vif.prdata  <= rdata;
            vif.pslverr <= 1'b0;
            clk_vif.drive_edge();
        endtask

        function void expect_transfer(bit write, bit [31:0] addr, bit [31:0] data);
            apb_item_t it = apb_item_t::type_id::create("it");
            it.write  = write;
            it.addr   = addr;
            it.data   = data;
            it.slverr = 0;
            sb.expected.push_back(it);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            drive(0, 0, 0, 0, 0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            expect_transfer(1, 32'h40, 32'hA5A5_5A5A);
            expect_transfer(0, 32'h40, 32'hA5A5_5A5A);
            expect_transfer(0, 32'h50, 32'h0);
            expect_transfer(1, 32'h14, 32'h1);
            expect_transfer(1, 32'h20, 32'h2);
            expect_transfer(1, 32'h30, 32'h6);
            drive(1, 0, 1, 32'h40, 32'hA5A5_5A5A, 0);  // clean write
            drive(1, 1, 1, 32'h40, 32'hA5A5_5A5A, 1);
            drive(1, 0, 0, 32'h40, 32'h0, 0);          // clean read, back to back
            drive(1, 1, 0, 32'h40, 32'h0, 1, 32'hA5A5_5A5A);
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(1, 1, 0, 32'h50, 32'h0, 1);          // penable with no setup phase
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(0, 1, 0, 32'h50, 32'h0, 0);          // penable without psel, not a report
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(1, 0, 1, 32'h10, 32'h1, 0);          // paddr changes
            drive(1, 1, 1, 32'h14, 32'h1, 1);
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(1, 0, 0, 32'h20, 32'h2, 0);          // pwrite changes
            drive(1, 1, 1, 32'h20, 32'h2, 1);
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(1, 0, 1, 32'h30, 32'h5, 0);          // pwdata changes
            drive(1, 1, 1, 32'h30, 32'h6, 1);
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(1, 0, 1, 32'h60, 32'h7, 0);          // psel drops while pready is low
            drive(1, 1, 1, 32'h60, 32'h7, 0);
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            drive(1, 0, 0, 32'h70, 32'h0, 0);          // psel drops after the setup phase
            drive(0, 0, 0, 32'h0, 32'h0, 0);
            repeat (2) clk_vif.drive_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned proto = srv.get_id_count("A2C_PROTO");
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_PROTO, %0d A2C_HOLD, %0d transfers reported", proto, hold, sb.matched),
                      UVM_NONE)
            if (proto != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_PROTO report, got %0d", proto))
            if (hold != 5) `uvm_error("LB_CHECKS", $sformatf("expected 5 A2C_HOLD reports, got %0d", hold))
            if (sb.matched != 6) `uvm_error("LB_CHECKS", $sformatf("expected 6 transfers reported, got %0d", sb.matched))
        endfunction
    endclass : apb_monitor_checks_test

    function automatic apb_config_t lb_apb_cfg(string name, apb_vif_t vif, virtual a2c_clk_if clk_vif, a2c_role_e role,
                                               string port);
        apb_config_t cfg = apb_config_t::type_id::create(name);
        cfg.vif       = vif;
        cfg.clk_vif   = clk_vif;
        cfg.role      = role;
        cfg.port_name = port;
        return cfg;
    endfunction

    // Mode B with the agent as master: apb is its DUT lane and apb_model its
    // model lane, each served by a slave peer. The peers' memories have the
    // same random fill and the same error range over 'h100 to 'h17f. The DUT
    // lane's peer adds up to one wait clock per transfer and the model lane's
    // up to three, so the lanes fall out of step. apb_check_seq checks every
    // transfer against the DUT lane's memory, so req must carry the DUT
    // lane's response. model_cmp must pair every transfer with no mismatch.
    class apb_mode_b_test extends lb_mode_b_base;
        apb_agent_t                         agent;
        apb_agent_t                         peer;
        apb_agent_t                         model_peer;
        apb_config_t                        peer_cfg;
        apb_config_t                        model_peer_cfg;
        apb_vif_t                           vif;
        apb_vif_t                           model_vif;
        uvm_tlm_analysis_fifo #(apb_item_t) observed;
        apb_check_seq                       seq;
        int unsigned                        want_pairs;
        int unsigned                        skew;

        `uvm_component_utils(apb_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            apb_config_t agent_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb", vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb'")
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb_model'")
            agent_cfg = lb_apb_cfg("agent_cfg", vif, clk_vif, A2C_SRC, "apb");
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lb_apb_cfg("peer_cfg", vif, clk_vif, A2C_DST, "apb");
            model_peer_cfg = lb_apb_cfg("model_peer_cfg", model_vif, clk_vif, A2C_DST, "apb_model");
            peer_cfg.mem       = apb_mem_t::type_id::create("peer_mem");
            model_peer_cfg.mem = apb_mem_t::type_id::create("model_peer_mem");
            peer_cfg.mem.fill       = A2C_MEM_FILL_RANDOM;
            model_peer_cfg.mem.fill = A2C_MEM_FILL_RANDOM;
            model_peer_cfg.mem.seed = peer_cfg.mem.seed;
            peer_cfg.max_wait       = 1;
            model_peer_cfg.max_wait = 3;
            peer_cfg.error_ranges.push_back('{lo: 32'h100, hi: 32'h17f});
            model_peer_cfg.error_ranges = peer_cfg.error_ranges;
            uvm_config_db#(apb_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(apb_config_t)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(apb_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent      = apb_agent_t::type_id::create("agent", this);
            peer       = apb_agent_t::type_id::create("peer", this);
            model_peer = apb_agent_t::type_id::create("model_peer", this);
            observed   = new("observed", this);
            want_pairs = n_items;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            peer.mon.ap.connect(observed.analysis_export);
        endfunction

        // Transfers after the checked sequence.
        virtual task finish();
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            seq = apb_check_seq::type_id::create("seq");
            seq.n            = n_items;
            seq.mem          = peer_cfg.mem;
            seq.error_ranges = peer_cfg.error_ranges;
            seq.observed     = observed;
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (vif.psel !== model_vif.psel || vif.penable !== model_vif.penable) skew++;
                end
            join_none
            seq.start(agent.sqr);
            finish();
            repeat (2) clk_vif.sample_edge();
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transfers checked against the DUT lane, %0d pairs; the lanes were out of step on %0d clocks",
                                            seq.matched, agent.model_cmp.get_pairs(), skew), UVM_NONE)
            if (seq.matched != n_items) `uvm_error("LB_APB", $sformatf("matched %0d of %0d transfers", seq.matched, n_items))
            if (seq.reads == 0 || seq.writes == 0 || seq.errors == 0) `uvm_error("LB_APB", "the sequence missed a read, a write or an error")
            if (agent.model_cmp.get_pairs() != want_pairs) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d transfers, expected %0d", agent.model_cmp.get_pairs(), want_pairs))
            end
            if (skew == 0) `uvm_error("LB_MODE_B", "the lanes never fell out of step, so per-lane completion went untested")
        endfunction
    endclass : apb_mode_b_test

    // The model lane's peer alone has an error range over 'h300, which one
    // more read fetches: one A2C_MODEL_CMP, and req carries the DUT lane's
    // word and pslverr 0.
    class apb_mode_b_mismatch_test extends apb_mode_b_test;
        bit [31:0] word;

        `uvm_component_utils(apb_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            apb_item_t dut;
            apb_item_t model;
            super.build_phase(phase);
            word = $urandom();
            for (int unsigned b = 0; b < 4; b++) peer_cfg.mem.write(32'h300 + b, word[8 * b +: 8]);
            model_peer_cfg.error_ranges.push_back('{lo: 32'h300, hi: 32'h303});
            want_pairs  = n_items + 1;
            want_errors = 1;
            dut   = apb_item_t::type_id::create("dut");
            model = apb_item_t::type_id::create("model");
            dut.addr   = 32'h300;
            model.addr = 32'h300;
            dut.data     = word;
            model.data   = '0;
            model.slverr = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT %s, model %s", n_items + 1,
                                          dut.convert2string(), model.convert2string()));
        endfunction

        virtual task finish();
            lb_list_seq#(apb_item_t) read = lb_list_seq#(apb_item_t)::type_id::create("read");
            apb_item_t               it   = apb_item_t::type_id::create("it");
            it.write = 0;
            it.addr  = 32'h300;
            read.items.push_back(it);
            read.start(agent.sqr);
            if (it.slverr !== 0 || it.data !== word) begin
                `uvm_error("LB_APB", $sformatf("req holds 0x%08h slverr %0d, the DUT lane gave 0x%08h slverr 0", it.data, it.slverr, word))
            end
            observed.flush();
        endtask
    endclass : apb_mode_b_mismatch_test

    // Sends a list of transfers with idle clocks before each. With follow
    // set, transfer hold_at waits until follow has reported that many
    // transfers and one more, then for hold_clocks idle clocks.
    class apb_gap_seq extends uvm_sequence #(apb_item_t);
        apb_item_t                items[$];
        int unsigned              gaps[$];
        virtual a2c_clk_if        clk_vif;
        lb_arrivals#(apb_item_t)  follow;
        int                       hold_at = -1;
        int unsigned              hold_clocks = 0;

        `uvm_object_utils(apb_gap_seq)

        function new(string name = "apb_gap_seq");
            super.new(name);
        endfunction

        virtual task body();
            foreach (items[i]) begin
                repeat (gaps[i]) clk_vif.drive_edge();
                if (i == hold_at) begin
                    while (follow.items.size() <= i) clk_vif.sample_edge();
                    repeat (hold_clocks) clk_vif.drive_edge();
                end
                start_item(items[i]);
                finish_item(items[i]);
            end
        endtask
    endclass : apb_gap_seq

    // Mode B with the agent as slave: apb is its DUT lane and apb_model its
    // model lane, each driven by a master peer. The peers send the same
    // n_items transfers to 16 words, one of them in an error range, each lane
    // with its own random idle clocks between transfers, so either lane may
    // reach a transfer first. The agent serves both lanes from one memory
    // with up to two wait clocks. A reference applies the transfers once, in
    // order, to a memory with the same fill. Each lane's read data and
    // pslverr must match it, and the agent's memory must end as it does.
    // model_cmp must pair every transfer with no mismatch, and each lane must
    // reach the setup phase of some transfers first. The DUT lane applies
    // every transfer, so the model lane must never complete one before it.
    class apb_mode_b_slave_test extends lb_mode_b_base;
        apb_agent_t              agent;
        apb_agent_t              peer;
        apb_agent_t              model_peer;
        apb_config_t             agent_cfg;
        apb_vif_t                vif;
        apb_vif_t                model_vif;
        apb_mem_t                ref_mem;
        lb_arrivals#(apb_item_t) arrivals;
        lb_arrivals#(apb_item_t) model_arrivals;
        apb_gap_seq              seq;
        apb_gap_seq              model_seq;
        // The response the reference gives each transfer.
        bit [31:0]               want_data[$];
        bit                      want_slverr[$];
        // The setup phase of each transfer on each lane, and the lane that
        // reached it first.
        realtime                 setup_at[2][$];
        int unsigned             led[2];
        bit                      done[2];
        int unsigned             idle;

        `uvm_component_utils(apb_mode_b_slave_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // Edits model_seq and the expectations.
        virtual function void build_streams();
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb", vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb'")
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb_model'")
            agent_cfg = lb_apb_cfg("agent_cfg", vif, clk_vif, A2C_DST, "apb");
            agent_cfg.model_vif = model_vif;
            agent_cfg.mem       = apb_mem_t::type_id::create("slave_mem");
            agent_cfg.mem.fill  = A2C_MEM_FILL_RANDOM;
            agent_cfg.max_wait  = 2;
            // A test whose model lane waits forever waits out the drain's
            // whole deadline.
            agent_cfg.drain_deadline_cycles = 2000;
            agent_cfg.error_ranges.push_back('{lo: 32'h30, hi: 32'h33});
            ref_mem      = apb_mem_t::type_id::create("ref_mem");
            ref_mem.fill = A2C_MEM_FILL_RANDOM;
            ref_mem.seed = agent_cfg.mem.seed;
            uvm_config_db#(apb_config_t)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(apb_config_t)::set(this, "peer", "cfg", lb_apb_cfg("peer_cfg", vif, clk_vif, A2C_SRC, "apb"));
            uvm_config_db#(apb_config_t)::set(this, "model_peer", "cfg",
                                              lb_apb_cfg("model_peer_cfg", model_vif, clk_vif, A2C_SRC, "apb_model"));
            agent          = apb_agent_t::type_id::create("agent", this);
            peer           = apb_agent_t::type_id::create("peer", this);
            model_peer     = apb_agent_t::type_id::create("model_peer", this);
            arrivals       = lb_arrivals#(apb_item_t)::type_id::create("arrivals", this);
            model_arrivals = lb_arrivals#(apb_item_t)::type_id::create("model_arrivals", this);
            seq       = apb_gap_seq::type_id::create("seq");
            model_seq = apb_gap_seq::type_id::create("model_seq");
            seq.clk_vif       = clk_vif;
            model_seq.clk_vif = clk_vif;
            model_seq.follow  = arrivals;
            for (int unsigned i = 0; i < n_items; i++) begin
                apb_item_t it = apb_item_t::type_id::create("it");
                apb_item_t m;
                bit [31:0] word;
                if (!it.randomize() with { addr < 32'h40; addr[1:0] == 2'b00; }) `uvm_fatal("LB_RAND", "apb item randomize failed")
                $cast(m, it.clone());
                seq.items.push_back(it);
                model_seq.items.push_back(m);
                seq.gaps.push_back($urandom_range(3, 0));
                model_seq.gaps.push_back($urandom_range(3, 0));
                for (int unsigned b = 0; b < 4; b++) word[8 * b +: 8] = ref_mem.read(it.addr + b);
                want_slverr.push_back(it.addr inside {[32'h30 : 32'h33]});
                if (!want_slverr[i] && it.write) begin
                    for (int unsigned b = 0; b < 4; b++) ref_mem.write(it.addr + b, it.data[8 * b +: 8]);
                    word = it.data;
                end
                want_data.push_back(word);
            end
            build_streams();
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            agent.mon.ap.connect(arrivals.analysis_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (vif.psel === 1'b1 && vif.penable !== 1'b1) setup_at[A2C_DUT_LANE].push_back($realtime);
                    if (model_vif.psel === 1'b1 && model_vif.penable !== 1'b1) setup_at[A2C_MODEL_LANE].push_back($realtime);
                end
            join_none
            fork
                begin
                    seq.start(peer.sqr);
                    done[A2C_DUT_LANE] = 1;
                end
                begin
                    model_seq.start(model_peer.sqr);
                    done[A2C_MODEL_LANE] = 1;
                end
            join_none
            // A model lane transfer the DUT lane never makes never ends, so
            // after the DUT lane's last transfer the test waits only while
            // the model lane completes a transfer at least once every 50 clocks.
            wait (done[A2C_DUT_LANE]);
            while (!done[A2C_MODEL_LANE] && idle < 50) begin
                int unsigned last = model_arrivals.items.size();
                clk_vif.sample_edge();
                idle = (model_arrivals.items.size() == last) ? idle + 1 : 0;
            end
            repeat (2) clk_vif.sample_edge();
            disable fork;
            phase.drop_objection(this);
        endtask

        protected function void check_lane(string lane, apb_item_t got[$]);
            for (int unsigned i = 0; i < got.size() && i < want_data.size(); i++) begin
                if (got[i].slverr !== want_slverr[i] || (!got[i].write && !want_slverr[i] && got[i].data !== want_data[i])) begin
                    `uvm_error("LB_REPLAY", $sformatf("%s lane transfer %0d: got %s, the reference gives data 0x%08h slverr %0d",
                                                      lane, i, got[i].convert2string(), want_data[i], want_slverr[i]))
                end
            end
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned bad_bytes = 0;
            super.check_phase(phase);
            check_lane("DUT", seq.items);
            check_lane("model", model_seq.items);
            for (int unsigned a = 0; a < 32'h40; a++) begin
                if (ref_mem.exists(a) != agent_cfg.mem.exists(a) || (ref_mem.exists(a) && ref_mem.read(a) !== agent_cfg.mem.read(a))) begin
                    bad_bytes++;
                end
            end
            if (bad_bytes != 0) `uvm_error("LB_REPLAY", $sformatf("the agent's memory differs from the reference in %0d bytes", bad_bytes))
            for (int unsigned i = 0; i < setup_at[A2C_DUT_LANE].size() && i < setup_at[A2C_MODEL_LANE].size(); i++) begin
                if (setup_at[A2C_MODEL_LANE][i] < setup_at[A2C_DUT_LANE][i]) led[A2C_MODEL_LANE]++;
                else led[A2C_DUT_LANE]++;
            end
            for (int unsigned i = 0; i < arrivals.at.size() && i < model_arrivals.at.size(); i++) begin
                if (model_arrivals.at[i] < arrivals.at[i]) begin
                    `uvm_error("LB_REPLAY", $sformatf("the model lane completed transfer %0d before the DUT lane", i))
                end
            end
            `uvm_info("LB_STATS", $sformatf("%0d pairs; the DUT lane led %0d transfers and the model lane %0d", agent.model_cmp.get_pairs(),
                                            led[A2C_DUT_LANE], led[A2C_MODEL_LANE]), UVM_NONE)
            if (agent.model_cmp.get_pairs() != n_items) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d transfers, expected %0d", agent.model_cmp.get_pairs(), n_items))
            end
            check_led();
        endfunction

        virtual function void check_led();
            if (led[A2C_DUT_LANE] == 0 || led[A2C_MODEL_LANE] == 0) `uvm_error("LB_MODE_B", "one lane never led, so replay went untested")
        endfunction
    endclass : apb_mode_b_slave_test

    // The model lane's peer writes different data in one transfer, which it
    // starts only after the DUT lane has completed it, so the DUT lane
    // applies the transfer: one A2C_MODEL_CMP, and the memory and every read
    // still match the reference.
    class apb_mode_b_slave_mismatch_test extends apb_mode_b_slave_test;
        `uvm_component_utils(apb_mode_b_slave_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            apb_item_t m;
            int        k = -1;
            for (int unsigned i = n_items / 2; i < n_items && k < 0; i++) begin
                if (seq.items[i].write && !want_slverr[i]) k = i;
            end
            if (k < 0) `uvm_fatal("LB_RAND", "no write in the second half of the transfers")
            m = model_seq.items[k];
            m.data = ~m.data;
            model_seq.hold_at = k;
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT %s, model %s", k + 1,
                                          seq.items[k].convert2string(), m.convert2string()));
        endfunction
    endclass : apb_mode_b_slave_mismatch_test

    // The model lane's peer starts every transfer on the first clock it can
    // and the DUT lane's peer one to three clocks later, so the model lane
    // reaches every transfer first. In one transfer the model lane's peer
    // writes different data, and the next transfer reads that address back.
    // The DUT lane applies the write, so both lanes must read the DUT
    // lane's data and the memory must match the reference: one
    // A2C_MODEL_CMP, for the write.
    class apb_mode_b_slave_model_leads_test extends apb_mode_b_slave_test;
        `uvm_component_utils(apb_mode_b_slave_model_leads_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            apb_item_t m;
            int        k = -1;
            foreach (seq.gaps[i]) begin
                seq.gaps[i]       = $urandom_range(3, 1);
                model_seq.gaps[i] = 0;
            end
            for (int unsigned i = 0; i + 1 < n_items && k < 0; i++) begin
                if (seq.items[i].write && !want_slverr[i] && !seq.items[i + 1].write) k = i;
            end
            if (k < 0) `uvm_fatal("LB_RAND", "no write followed by a read")
            // A read leaves the reference unchanged, so moving its address
            // changes only its own expected response.
            seq.items[k + 1].addr       = seq.items[k].addr;
            model_seq.items[k + 1].addr = seq.items[k].addr;
            want_data[k + 1]            = seq.items[k].data;
            want_slverr[k + 1]          = 0;
            m = model_seq.items[k];
            m.data = ~m.data;
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair %0d: DUT %s, model %s", k + 1,
                                          seq.items[k].convert2string(), m.convert2string()));
        endfunction

        virtual function void check_led();
            if (led[A2C_MODEL_LANE] != n_items) begin
                `uvm_error("LB_MODE_B", $sformatf("the model lane led %0d of %0d transfers", led[A2C_MODEL_LANE], n_items))
            end
        endfunction
    endclass : apb_mode_b_slave_model_leads_test

    // The model lane's peer sends one transfer more than the DUT lane's. The
    // DUT lane never records it, so the model lane waits for it until the
    // slave's end-of-test drain gives up: one A2C_REPLAY.
    class apb_mode_b_slave_extra_test extends apb_mode_b_slave_test;
        `uvm_component_utils(apb_mode_b_slave_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_REPLAY";
        endfunction

        virtual function void build_streams();
            apb_item_t it = apb_item_t::type_id::create("it");
            if (!it.randomize() with { addr < 32'h30; addr[1:0] == 2'b00; }) `uvm_fatal("LB_RAND", "apb item randomize failed")
            model_seq.items.push_back(it);
            model_seq.gaps.push_back(0);
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.drv.replay: the model lane waited for transaction %0d, which the DUT lane never recorded",
                                          n_items));
        endfunction
    endclass : apb_mode_b_slave_extra_test

    // The test ends as a generated Mode B test does once its outputs are
    // done: it drops its objection, and the slave's phase_ready_to_end()
    // drain holds the run phase. Here the outputs are done when the DUT lane
    // has completed every transfer, and the model lane's peer starts the
    // last one 50 clocks later, after a quiet window of 20 clocks: the model
    // lane must still replay it and model_cmp must pair it, with no
    // A2C_REPLAY.
    class apb_mode_b_slave_drain_test extends apb_mode_b_slave_test;
        apb_slave_driver#(lb_apb_word_t, lb_apb_word_t) slave;
        int unsigned clocks;
        int unsigned dropped_at;
        int unsigned pending_at_drop;
        bit          waiting_at_drop;

        `uvm_component_utils(apb_mode_b_slave_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            agent_cfg.drain_quiet_cycles    = 20;
            agent_cfg.drain_deadline_cycles = 400;
            model_seq.hold_at     = n_items - 1;
            model_seq.hold_clocks = 50;
        endfunction

        virtual task wait_drop();
            while (arrivals.items.size() < n_items) clk_vif.sample_edge();
        endtask

        // The clock counter runs until the run phase ends.
        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            if (!$cast(slave, agent.drv)) `uvm_fatal("LB_CFG", "the agent's driver is not an apb_slave_driver")
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    clocks++;
                end
                seq.start(peer.sqr);
                model_seq.start(model_peer.sqr);
            join_none
            wait_drop();
            pending_at_drop = slave.replay.pending();
            waiting_at_drop = slave.replay.model_waiting();
            dropped_at      = clocks;
            phase.drop_objection(this);
        endtask

        protected function int unsigned drain_clocks();
            return clocks - dropped_at;
        endfunction

        virtual function void check_led();
            `uvm_info("LB_STATS", $sformatf("%0d responses unreplayed and model lane waiting %0d at the drop; the drain took %0d clocks",
                                            pending_at_drop, waiting_at_drop, drain_clocks()), UVM_NONE)
            if (pending_at_drop == 0) begin
                `uvm_error("LB_MODE_B", "the model lane had replayed every response at the drop, so the drain went untested")
            end
        endfunction

        // The clock counter races the drain on each edge, so it may be one off.
        protected function void check_deadline();
            if (drain_clocks() + 1 < agent_cfg.drain_deadline_cycles || drain_clocks() > agent_cfg.drain_deadline_cycles + 1) begin
                `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected the deadline of %0d", drain_clocks(),
                                                  agent_cfg.drain_deadline_cycles))
            end
        endfunction
    endclass : apb_mode_b_slave_drain_test

    // As apb_mode_b_slave_drain_test, with the model lane's last transfer 40
    // clocks late and a drain deadline of 10 clocks: the drain gives up at
    // the deadline, and the replay log's check_phase() reports the
    // responses left in one A2C_REPLAY. The unpaired DUT lane transfers are
    // the replay log's to report, so model_cmp is marked counted.
    class apb_mode_b_slave_drain_deadline_test extends apb_mode_b_slave_drain_test;
        `uvm_component_utils(apb_mode_b_slave_drain_deadline_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_REPLAY";
        endfunction

        virtual function void build_streams();
            super.build_streams();
            agent_cfg.drain_deadline_cycles = 10;
            model_seq.hold_clocks = 40;
            want_errors = 1;
            want_text.push_back("responses the DUT lane recorded and the model lane never replayed");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.counted = 1;
        endfunction

        // The lanes' data checks of apb_mode_b_slave_test would read the
        // model lane's transfer that never ran.
        virtual function void check_phase(uvm_phase phase);
            check_deadline();
        endfunction
    endclass : apb_mode_b_slave_drain_deadline_test

    // The model lane leads every transfer, and the DUT lane's peer starts
    // the last one 20 clocks late. The test drops its objection while the
    // model lane waits for that unrecorded transfer, with a quiet window of
    // one clock and up to eight wait clocks per transfer, so only the model
    // lane's completion keeps the run phase alive through the last
    // transfer: no A2C_REPLAY, every pair compared, and the model lane idle
    // when the run ends.
    class apb_mode_b_slave_drain_model_leads_test extends apb_mode_b_slave_drain_test;
        `uvm_component_utils(apb_mode_b_slave_drain_model_leads_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            agent_cfg.drain_quiet_cycles    = 1;
            agent_cfg.drain_deadline_cycles = 400;
            agent_cfg.max_wait              = 8;
            foreach (seq.gaps[i]) begin
                seq.gaps[i]       = $urandom_range(3, 1);
                model_seq.gaps[i] = 0;
            end
            seq.gaps[n_items - 1] = 20;
        endfunction

        // The model lane's setup phase of the last transfer, and one clock
        // more so the slave has sampled it.
        virtual task wait_drop();
            do clk_vif.sample_edge();
            while (model_arrivals.items.size() < n_items - 1 || model_vif.psel !== 1'b1 || model_vif.penable === 1'b1);
            clk_vif.sample_edge();
        endtask

        virtual function void check_led();
            `uvm_info("LB_STATS", $sformatf("model lane waiting %0d at the drop; the drain took %0d clocks", waiting_at_drop,
                                            drain_clocks()), UVM_NONE)
            if (!waiting_at_drop) `uvm_error("LB_MODE_B", "the model lane was not waiting at the drop, so the drain went untested")
            if (model_vif.psel === 1'b1) `uvm_error("LB_MODE_B", "the run ended inside a model lane transfer")
        endfunction
    endclass : apb_mode_b_slave_drain_model_leads_test

    // The model lane's peer sends one transfer more than the DUT lane's. The
    // test drops its objection when the DUT lane is done, before the model
    // lane has started the extra transfer. The quiet window sees it start,
    // the model lane then waits for it until the drain's deadline, and the
    // replay log reports the wait: one A2C_REPLAY.
    class apb_mode_b_slave_drain_extra_test extends apb_mode_b_slave_drain_test;
        `uvm_component_utils(apb_mode_b_slave_drain_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id = "A2C_REPLAY";
        endfunction

        virtual function void build_streams();
            apb_item_t it = apb_item_t::type_id::create("it");
            agent_cfg.drain_quiet_cycles    = 20;
            agent_cfg.drain_deadline_cycles = 400;
            if (!it.randomize() with { addr < 32'h30; addr[1:0] == 2'b00; }) `uvm_fatal("LB_RAND", "apb item randomize failed")
            model_seq.items.push_back(it);
            model_seq.gaps.push_back(0);
            want_errors = 1;
            want_text.push_back($sformatf("uvm_test_top.agent.drv.replay: the model lane waited for transaction %0d, %s",
                                          n_items, "which the DUT lane never recorded"));
        endfunction

        virtual function void check_led();
            check_deadline();
        endfunction
    endclass : apb_mode_b_slave_drain_extra_test

    // As apb_mode_b_slave_drain_extra_test, with the drop in the setup phase
    // of the extra transfer.
    class apb_mode_b_slave_drain_extra_setup_test extends apb_mode_b_slave_drain_extra_test;
        `uvm_component_utils(apb_mode_b_slave_drain_extra_setup_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task wait_drop();
            do clk_vif.sample_edge();
            while (model_arrivals.items.size() < n_items || model_vif.psel !== 1'b1 || model_vif.penable === 1'b1);
            clk_vif.sample_edge();
        endtask
    endclass : apb_mode_b_slave_drain_extra_setup_test

    // As apb_mode_b_slave_drain_test, in two rounds. The first sends every
    // transfer but the last, and its drain replays them all. On its second
    // phase_ready_to_end() call, which comes when that drain drops, the test
    // raises its objection again, sends the last transfer with the model
    // lane's peer 30 clocks behind, and drops it when the DUT lane has
    // completed the transfer. Only a second drain from the slave's repeated
    // phase_ready_to_end() keeps the run phase alive until the model lane
    // replays it: no A2C_REPLAY, and every pair compared.
    class apb_mode_b_slave_drain_twice_test extends apb_mode_b_slave_drain_test;
        apb_gap_seq  last_seq;
        apb_gap_seq  model_last_seq;
        int unsigned ready_calls;
        bit          resumed;
        int unsigned resumed_at;
        int unsigned pending_at_second_drop;

        `uvm_component_utils(apb_mode_b_slave_drain_twice_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            agent_cfg.drain_quiet_cycles    = 20;
            agent_cfg.drain_deadline_cycles = 400;
            last_seq       = apb_gap_seq::type_id::create("last_seq");
            model_last_seq = apb_gap_seq::type_id::create("model_last_seq");
            last_seq.clk_vif       = clk_vif;
            model_last_seq.clk_vif = clk_vif;
            last_seq.items.push_back(seq.items.pop_back());
            last_seq.gaps.push_back(seq.gaps.pop_back());
            model_last_seq.items.push_back(model_seq.items.pop_back());
            void'(model_seq.gaps.pop_back());
            model_last_seq.gaps.push_back(30);
        endfunction

        virtual task wait_drop();
            while (arrivals.items.size() < n_items - 1) clk_vif.sample_edge();
        endtask

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() != uvm_run_phase::get()) return;
            ready_calls++;
            if (ready_calls != 2) return;
            resumed    = 1;
            resumed_at = clocks;
            phase.raise_objection(this, "the last transfer");
            fork last_round(phase); join_none
        endfunction

        // Runs before the last transfer is sent.
        virtual task before_last();
        endtask

        protected task last_round(uvm_phase phase);
            before_last();
            fork
                last_seq.start(peer.sqr);
                model_last_seq.start(model_peer.sqr);
            join_none
            while (arrivals.items.size() < n_items) clk_vif.sample_edge();
            pending_at_second_drop = slave.replay.pending();
            phase.drop_objection(this, "the DUT lane completed the last transfer");
        endtask

        // The lanes' data checks read every transfer from seq and model_seq.
        virtual function void check_phase(uvm_phase phase);
            seq.items.push_back(last_seq.items[0]);
            model_seq.items.push_back(model_last_seq.items[0]);
            super.check_phase(phase);
        endfunction

        virtual function void check_led();
            `uvm_info("LB_STATS", $sformatf("%0d phase_ready_to_end calls; %0d responses unreplayed at the second drop",
                                            ready_calls, pending_at_second_drop), UVM_NONE)
            if (!resumed) `uvm_error("LB_MODE_B", "the first drain never dropped, so the second round never ran")
            if (pending_at_second_drop == 0) begin
                `uvm_error("LB_MODE_B", {"the model lane had replayed the last transfer at the second drop, ",
                                         "so the second drain went untested"})
            end
        endfunction
    endclass : apb_mode_b_slave_drain_twice_test

    // As apb_mode_b_slave_drain_twice_test, with the model lane's peer 40
    // clocks late on the first round's last transfer and a deadline of 10
    // clocks, so the first drain expires with the model lane busy. The test
    // sends the last transfer once the model lane has completed the late
    // one, and raises the deadline to 400 clocks. The model lane started a
    // transfer after the expiry, so the slave must drain again: no
    // A2C_REPLAY, and every pair compared.
    class apb_mode_b_slave_drain_after_expiry_test extends apb_mode_b_slave_drain_twice_test;
        `uvm_component_utils(apb_mode_b_slave_drain_after_expiry_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_streams();
            super.build_streams();
            agent_cfg.drain_deadline_cycles = 10;
            model_seq.hold_at     = n_items - 2;
            model_seq.hold_clocks = 40;
        endfunction

        virtual task before_last();
            while (model_arrivals.items.size() < n_items - 1) clk_vif.sample_edge();
            agent_cfg.drain_deadline_cycles = 400;
        endtask

        virtual function void check_led();
            int unsigned first = resumed_at - dropped_at;
            super.check_led();
            // The clock counter races the drain on each edge, so it may be one off.
            if (first + 1 < 10 || first > 11) begin
                `uvm_error("LB_MODE_B", $sformatf("the first drain took %0d clocks, expected its deadline of 10", first))
            end
        endfunction
    endclass : apb_mode_b_slave_drain_after_expiry_test
