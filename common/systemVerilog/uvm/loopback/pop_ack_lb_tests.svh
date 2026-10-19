// pop_ack agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef pop_ack_agent #(.rdata_t(lb_data_t)) po_agent_t;
    typedef po_agent_t::item_t po_item_t;
    typedef po_agent_t::config_t po_config_t;
    typedef virtual pop_ack_if #(.rdata_t(lb_data_t)) po_vif_t;
    typedef pop_ack_responder_seq #(lb_data_t) po_responder_t;

    // The rdata the test responders return for pop number seq. salt tells
    // the responders apart.
    function automatic lb_data_t po_answer(int unsigned seq, bit [3:0] salt);
        lb_data_t d;
        d.tag   = salt;
        d.value = 20'(seq);
        return d;
    endfunction

    // Answers each pop with its sequence number, salt 4'h5, after 0 to 3
    // extra clocks.
    class po_echo_responder extends po_responder_t;
        int unsigned answered;

        `uvm_object_utils(po_echo_responder)

        function new(string name = "po_echo_responder");
            super.new(name);
        endfunction

        virtual function void respond(po_item_t rsp);
            rsp.rdata = po_answer(answered++, 4'h5);
            rsp.delay = $urandom_range(3, 0);
        endfunction
    endclass : po_echo_responder

    // Answers each pop with its sequence number, salt 4'hA, with no delay,
    // and counts the pops it answered.
    class po_override_responder extends po_responder_t;
        static int unsigned answered;

        `uvm_object_utils(po_override_responder)

        function new(string name = "po_override_responder");
            super.new(name);
        endfunction

        virtual function void respond(po_item_t rsp);
            rsp.rdata = po_answer(answered++, 4'hA);
            rsp.delay = 0;
        endfunction
    endclass : po_override_responder

    // With check set, the scoreboard expects po_answer(i, salt) for pop i,
    // and the sequence checks that the same rdata came back in the item.
    class po_seq extends uvm_sequence #(po_item_t);
        int unsigned              n;
        int unsigned              max_gap;
        bit                       check;
        bit [3:0]                 salt;
        lb_scoreboard#(po_item_t) sb;

        `uvm_object_utils(po_seq)

        function new(string name = "po_seq");
            super.new(name);
        endfunction

        virtual task body();
            po_item_t it;
            po_item_t exp;
            for (int unsigned i = 0; i < n; i++) begin
                it = po_item_t::type_id::create("it");
                start_item(it);
                it.gap = $urandom_range(max_gap, 0);
                if (check) begin
                    exp = po_item_t::type_id::create("exp");
                    exp.rdata = po_answer(i, salt);
                    sb.expected.push_back(exp);
                end
                finish_item(it);
                if (check && it.rdata !== po_answer(i, salt)) begin
                    `uvm_error("LB_RDATA", $sformatf("pop %0d: rdata %p came back, the responder sent %p", i, it.rdata,
                                                     po_answer(i, salt)))
                end
            end
        endtask
    endclass : po_seq

    // Builds a pop_ack src agent and a dst agent on one interface, with the
    // dst agent's monitor feeding a scoreboard.
    virtual class po_pair_test extends lb_base_test;
        po_agent_t                src;
        po_agent_t                dst;
        lb_scoreboard#(po_item_t) sb;
        po_config_t               dst_cfg;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            po_config_t src_cfg;
            po_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(po_vif_t)::get(this, "", "po", vif)) `uvm_fatal("LB_CFG", "no virtual pop_ack_if 'po'")
            src_cfg = po_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "po";
            dst_cfg = po_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "po";
            uvm_config_db#(po_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(po_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = po_agent_t::type_id::create("src", this);
            dst = po_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(po_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        task send(int unsigned n, bit check, bit [3:0] salt = 0);
            po_seq seq = po_seq::type_id::create("seq");
            seq.n       = n;
            seq.max_gap = 2;
            seq.check   = check;
            seq.salt    = salt;
            seq.sb      = sb;
            seq.start(src.sqr);
        endtask
    endclass : po_pair_test

    // The test sets po_echo_responder as the dst sequencer's default
    // sequence, which answers each pop with its sequence number after 0 to 3
    // extra clocks. Every pop must be answered in order, the src driver must
    // hand the same rdata back, and the clocks pop waited for ack must cover
    // the whole delay range: 1 to 4.
    class pop_ack_random_test extends po_pair_test;
        int unsigned min_wait = '1;
        int unsigned max_wait;

        `uvm_component_utils(pop_ack_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(uvm_object_wrapper)::set(this, "dst.sqr.run_phase", "default_sequence",
                                                    po_echo_responder::type_id::get());
            super.build_phase(phase);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                watch_waits();
            join_none
            send(n_items, 1, 4'h5);
            wait_matched(sb, n_items, 20 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        protected task watch_waits();
            int unsigned run = 0;
            forever begin
                clk_vif.sample_edge();
                if (dst_cfg.vif.pop !== 1'b1) begin
                    run = 0;
                end else if (dst_cfg.vif.ack !== 1'b1) begin
                    run++;
                end else begin
                    if (run < min_wait) min_wait = run;
                    if (run > max_wait) max_wait = run;
                    run = 0;
                end
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d pops, pop waited %0d to %0d clocks", sb.matched, min_wait, max_wait),
                      UVM_NONE)
            if (min_wait != 1 || max_wait != 4) begin
                `uvm_error("LB_ACK_DELAY", $sformatf("delay 0 to 3 should make pop wait 1 to 4 clocks, it waited %0d to %0d",
                                                     min_wait, max_wait))
            end
        endfunction
    endclass : pop_ack_random_test

    // po_override_responder replaces the agent's default responder. The
    // agent sets its own default_sequence after the test, so this passes
    // only if the replacement takes precedence. Every pop must come back
    // with the replacement's rdata, and the replacement must have answered
    // all of them.
    virtual class po_override_test extends po_pair_test;
        int unsigned n = 50;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            send(n, 1, 4'hA);
            wait_matched(sb, n, 20 * n);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d pops, %0d answered by po_override_responder", sb.matched,
                                            po_override_responder::answered), UVM_NONE)
            if (po_override_responder::answered != n) begin
                `uvm_error("LB_OVERRIDE", $sformatf("po_override_responder answered %0d of %0d pops",
                                                    po_override_responder::answered, n))
            end
        endfunction
    endclass : po_override_test

    // Replaces the responder with a uvm_config_db set from the test.
    class pop_ack_config_db_responder_test extends po_override_test;
        `uvm_component_utils(pop_ack_config_db_responder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(uvm_object_wrapper)::set(this, "dst.sqr.run_phase", "default_sequence",
                                                    po_override_responder::type_id::get());
            super.build_phase(phase);
        endfunction
    endclass : pop_ack_config_db_responder_test

    // Replaces the responder with a factory type override.
    class pop_ack_factory_responder_test extends po_override_test;
        `uvm_component_utils(pop_ack_factory_responder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            po_responder_t::type_id::set_type_override(po_override_responder::get_type());
            super.build_phase(phase);
        endfunction
    endclass : pop_ack_factory_responder_test

    // The default responder answers with random rdata. The dst agent's
    // monitor feeds an a2c_txn_counter that expects exactly the pops sent;
    // any shortfall or excess is an A2C_TXN_COUNT error.
    class pop_ack_counter_test extends po_pair_test;
        a2c_txn_counter #(po_item_t) counter;

        `uvm_component_utils(pop_ack_counter_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            counter = a2c_txn_counter#(po_item_t)::type_id::create("counter", this);
            counter.port_name = "po";
        endfunction

        // The scoreboard cannot know random rdata, so only the counter listens.
        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(counter.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            counter.expect_count(n_items);
            send(n_items, 0);
            counter.wait_for_count(clk_vif, 20 * n_items, 50);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d pops counted", n_items - counter.outstanding()), UVM_NONE)
        endfunction
    endclass : pop_ack_counter_test

    // A passive monitor watches pins the test drives by hand: a pop after one
    // wait, pop dropped before ack, ack with no pop, a pop acked in its first
    // clock and two back to back. Expects exactly one A2C_HOLD and one
    // A2C_PROTO report, demoted to info, and the four transfers reported.
    class pop_ack_monitor_checks_test extends lb_base_test;
        po_agent_t                obs;
        lb_scoreboard#(po_item_t) sb;
        po_vif_t                  vif;

        `uvm_component_utils(pop_ack_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            po_config_t cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(po_vif_t)::get(this, "", "po", vif)) `uvm_fatal("LB_CFG", "no virtual pop_ack_if 'po'")
            cfg = po_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "po";
            uvm_config_db#(po_config_t)::set(this, "obs", "cfg", cfg);
            obs = po_agent_t::type_id::create("obs", this);
            sb  = lb_scoreboard#(po_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(sb.imp);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
        endfunction

        // One clock per call: the pins as the next rising edge sees them.
        task drive(bit pop, bit ack, int unsigned rvalue = 0);
            vif.pop   <= pop;
            vif.ack   <= ack;
            vif.rdata <= lb_data_t'(rvalue);
            clk_vif.drive_edge();
        endtask

        function void expect_transfer(int unsigned rvalue);
            po_item_t it = po_item_t::type_id::create("it");
            it.rdata = lb_data_t'(rvalue);
            sb.expected.push_back(it);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            drive(0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            expect_transfer('h11);
            expect_transfer('h22);
            expect_transfer('h33);
            expect_transfer('h44);
            drive(1, 0);         // pop after one wait
            drive(1, 1, 'h11);
            drive(0, 0);
            drive(1, 0);         // pop dropped before ack
            drive(0, 0);
            drive(0, 1, 'h99);   // ack with no pop
            drive(0, 0);
            drive(1, 1, 'h22);   // acked in its first clock
            drive(1, 1, 'h33);   // back to back
            drive(1, 1, 'h44);
            drive(0, 0);
            repeat (2) clk_vif.drive_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            int unsigned proto = srv.get_id_count("A2C_PROTO");
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_HOLD, %0d A2C_PROTO, %0d transfers reported", hold, proto, sb.matched),
                      UVM_NONE)
            if (hold != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_HOLD report, got %0d", hold))
            if (proto != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_PROTO report, got %0d", proto))
            if (sb.matched != 4) `uvm_error("LB_CHECKS", $sformatf("expected 4 transfers reported, got %0d", sb.matched))
        endfunction
    endclass : pop_ack_monitor_checks_test
