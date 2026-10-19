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

    // The test drives the master's pins by hand against a slave agent with
    // max_wait 0, whose monitor checks them: a clean write and a read back,
    // psel and penable from idle, penable with psel low, which a completer
    // that is not selected ignores, and three transfers that change paddr,
    // pwrite and pwdata between the setup and access phases. Expects exactly
    // one A2C_PROTO and three A2C_HOLD reports, demoted to info, and the five
    // completed transfers reported.
    class apb_monitor_checks_test extends lb_base_test;
        apb_agent_t                slave;
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
            cfg.role      = A2C_DST;
            cfg.port_name = "apb";
            uvm_config_db#(apb_config_t)::set(this, "slave", "cfg", cfg);
            slave = apb_agent_t::type_id::create("slave", this);
            sb    = lb_scoreboard#(apb_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            slave.mon.ap.connect(sb.imp);
            slave.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            slave.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
        endfunction

        // One clock per call: the master's pins as the next rising edge sees
        // them.
        task drive(bit sel, bit enable, bit write, bit [31:0] addr, bit [31:0] wdata);
            vif.psel    <= sel;
            vif.penable <= enable;
            vif.pwrite  <= write;
            vif.paddr   <= addr;
            vif.pwdata  <= wdata;
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
            drive(0, 0, 0, 0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            expect_transfer(1, 32'h40, 32'hA5A5_5A5A);
            expect_transfer(0, 32'h40, 32'hA5A5_5A5A);
            expect_transfer(1, 32'h14, 32'h1);
            expect_transfer(1, 32'h20, 32'h2);
            expect_transfer(1, 32'h30, 32'h6);
            drive(1, 0, 1, 32'h40, 32'hA5A5_5A5A);  // clean write
            drive(1, 1, 1, 32'h40, 32'hA5A5_5A5A);
            drive(1, 0, 0, 32'h40, 32'h0);          // clean read, back to back
            drive(1, 1, 0, 32'h40, 32'h0);
            drive(0, 0, 0, 32'h0, 32'h0);
            drive(1, 1, 0, 32'h50, 32'h0);          // penable with no setup phase
            drive(0, 0, 0, 32'h0, 32'h0);
            drive(0, 1, 0, 32'h50, 32'h0);          // penable without psel, not a report
            drive(0, 0, 0, 32'h0, 32'h0);
            drive(1, 0, 1, 32'h10, 32'h1);          // paddr changes
            drive(1, 1, 1, 32'h14, 32'h1);
            drive(0, 0, 0, 32'h0, 32'h0);
            drive(1, 0, 0, 32'h20, 32'h2);          // pwrite changes
            drive(1, 1, 1, 32'h20, 32'h2);
            drive(0, 0, 0, 32'h0, 32'h0);
            drive(1, 0, 1, 32'h30, 32'h5);          // pwdata changes
            drive(1, 1, 1, 32'h30, 32'h6);
            drive(0, 0, 0, 32'h0, 32'h0);
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
            if (hold != 3) `uvm_error("LB_CHECKS", $sformatf("expected 3 A2C_HOLD reports, got %0d", hold))
            if (sb.matched != 5) `uvm_error("LB_CHECKS", $sformatf("expected 5 transfers reported, got %0d", sb.matched))
        endfunction
    endclass : apb_monitor_checks_test
