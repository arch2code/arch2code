// req_ack agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef logic [27:0] lb_rdata_t;
    typedef req_ack_agent #(.data_t(lb_data_t), .rdata_t(lb_rdata_t)) ra_agent_t;
    typedef ra_agent_t::item_t ra_item_t;
    typedef ra_agent_t::config_t ra_config_t;
    typedef virtual req_ack_if #(.data_t(lb_data_t), .rdata_t(lb_rdata_t)) ra_vif_t;
    typedef req_ack_responder_seq #(lb_data_t, lb_rdata_t) ra_responder_t;

    // The rdata the test responders return for a request. salt tells the
    // responders apart.
    function automatic lb_rdata_t ra_answer(lb_data_t data, bit [3:0] salt);
        return {data.value, ~data.tag, salt};
    endfunction

    // Answers from the request, salt 4'h5, after 0 to 3 extra clocks.
    class ra_echo_responder extends ra_responder_t;
        `uvm_object_utils(ra_echo_responder)

        function new(string name = "ra_echo_responder");
            super.new(name);
        endfunction

        virtual function void respond(ra_item_t request, ra_item_t rsp);
            rsp.data  = request.data;
            rsp.rdata = ra_answer(request.data, 4'h5);
            rsp.delay = $urandom_range(3, 0);
        endfunction
    endclass : ra_echo_responder

    // Answers from the request, salt 4'hA, with no delay, and counts the
    // requests it answered.
    class ra_override_responder extends ra_responder_t;
        static int unsigned answered;

        `uvm_object_utils(ra_override_responder)

        function new(string name = "ra_override_responder");
            super.new(name);
        endfunction

        virtual function void respond(ra_item_t request, ra_item_t rsp);
            rsp.data  = request.data;
            rsp.rdata = ra_answer(request.data, 4'hA);
            rsp.delay = 0;
            answered++;
        endfunction
    endclass : ra_override_responder

    // Each request carries its sequence number in value. With check set, the
    // scoreboard expects ra_answer(data, salt) beside each request, and the
    // sequence checks that the same rdata came back in the item.
    class ra_seq extends uvm_sequence #(ra_item_t);
        int unsigned              n;
        int unsigned              max_gap;
        bit                       check;
        bit [3:0]                 salt;
        lb_scoreboard#(ra_item_t) sb;

        `uvm_object_utils(ra_seq)

        function new(string name = "ra_seq");
            super.new(name);
        endfunction

        virtual task body();
            ra_item_t it;
            ra_item_t exp;
            for (int unsigned i = 0; i < n; i++) begin
                it = ra_item_t::type_id::create("it");
                start_item(it);
                if (!it.randomize()) `uvm_fatal("LB_RAND", "req_ack item randomize failed")
                it.data.value = 20'(i);
                it.gap        = $urandom_range(max_gap, 0);
                if (check) begin
                    $cast(exp, it.clone());
                    exp.rdata = ra_answer(it.data, salt);
                    sb.expected.push_back(exp);
                end
                finish_item(it);
                if (check && it.rdata !== ra_answer(it.data, salt)) begin
                    `uvm_error("LB_RDATA", $sformatf("request %0d: rdata %h came back, the responder sent %h", i, it.rdata,
                                                     ra_answer(it.data, salt)))
                end
            end
        endtask
    endclass : ra_seq

    // Builds a req_ack src agent and a dst agent on one interface, with the
    // dst agent's monitor feeding a scoreboard.
    virtual class ra_pair_test extends lb_base_test;
        ra_agent_t                src;
        ra_agent_t                dst;
        lb_scoreboard#(ra_item_t) sb;
        ra_config_t               dst_cfg;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            ra_config_t src_cfg;
            ra_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(ra_vif_t)::get(this, "", "ra", vif)) `uvm_fatal("LB_CFG", "no virtual req_ack_if 'ra'")
            src_cfg = ra_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "ra";
            dst_cfg = ra_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "ra";
            uvm_config_db#(ra_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(ra_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = ra_agent_t::type_id::create("src", this);
            dst = ra_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(ra_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        task send(int unsigned n, bit check, bit [3:0] salt = 0);
            ra_seq seq = ra_seq::type_id::create("seq");
            seq.n       = n;
            seq.max_gap = 2;
            seq.check   = check;
            seq.salt    = salt;
            seq.sb      = sb;
            seq.start(src.sqr);
        endtask
    endclass : ra_pair_test

    // The test sets ra_echo_responder as the dst sequencer's default
    // sequence, which answers each request from its data after 0 to 3 extra
    // clocks. Every request must arrive in order with that rdata, the src
    // driver must hand the same rdata back, and the clocks req waited for
    // ack must cover the whole delay range: 1 to 4.
    class req_ack_random_test extends ra_pair_test;
        int unsigned min_wait = '1;
        int unsigned max_wait;

        `uvm_component_utils(req_ack_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(uvm_object_wrapper)::set(this, "dst.sqr.run_phase", "default_sequence",
                                                    ra_echo_responder::type_id::get());
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
                if (dst_cfg.vif.req !== 1'b1) begin
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
            `uvm_info("LB_STATS", $sformatf("%0d transfers, req waited %0d to %0d clocks", sb.matched, min_wait, max_wait),
                      UVM_NONE)
            if (min_wait != 1 || max_wait != 4) begin
                `uvm_error("LB_ACK_DELAY", $sformatf("delay 0 to 3 should make req wait 1 to 4 clocks, it waited %0d to %0d",
                                                     min_wait, max_wait))
            end
        endfunction
    endclass : req_ack_random_test

    // ra_override_responder replaces the agent's default responder. The
    // agent sets its own default_sequence after the test, so this passes
    // only if the replacement takes precedence. Every request must come back
    // with the replacement's rdata, and the replacement must have answered
    // all of them.
    virtual class ra_override_test extends ra_pair_test;
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
            `uvm_info("LB_STATS", $sformatf("%0d transfers, %0d answered by ra_override_responder", sb.matched,
                                            ra_override_responder::answered), UVM_NONE)
            if (ra_override_responder::answered != n) begin
                `uvm_error("LB_OVERRIDE", $sformatf("ra_override_responder answered %0d of %0d requests",
                                                    ra_override_responder::answered, n))
            end
        endfunction
    endclass : ra_override_test

    // Replaces the responder with a uvm_config_db set from the test.
    class req_ack_config_db_responder_test extends ra_override_test;
        `uvm_component_utils(req_ack_config_db_responder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            uvm_config_db#(uvm_object_wrapper)::set(this, "dst.sqr.run_phase", "default_sequence",
                                                    ra_override_responder::type_id::get());
            super.build_phase(phase);
        endfunction
    endclass : req_ack_config_db_responder_test

    // Replaces the responder with a factory type override.
    class req_ack_factory_responder_test extends ra_override_test;
        `uvm_component_utils(req_ack_factory_responder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            ra_responder_t::type_id::set_type_override(ra_override_responder::get_type());
            super.build_phase(phase);
        endfunction
    endclass : req_ack_factory_responder_test

    // The default responder answers with random rdata. The dst agent's
    // monitor feeds an a2c_txn_counter that expects exactly the requests
    // sent; any shortfall or excess is an A2C_TXN_COUNT error.
    class req_ack_counter_test extends ra_pair_test;
        a2c_txn_counter #(ra_item_t) counter;

        `uvm_component_utils(req_ack_counter_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            counter = a2c_txn_counter#(ra_item_t)::type_id::create("counter", this);
            counter.port_name = "ra";
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
            `uvm_info("LB_STATS", $sformatf("%0d transfers counted", n_items - counter.outstanding()), UVM_NONE)
        endfunction
    endclass : req_ack_counter_test

    // A passive monitor watches pins the test drives by hand: a transfer
    // after one wait, req dropped before ack, data changed before ack and
    // then a transfer, ack with no req, a transfer acked in its first clock
    // and two back to back. Expects exactly two A2C_HOLD and one A2C_PROTO
    // report, demoted to info, the five transfers on ap and the six requests
    // on req_ap.
    class req_ack_monitor_checks_test extends lb_base_test;
        ra_agent_t                        obs;
        lb_scoreboard#(ra_item_t)         sb;
        uvm_tlm_analysis_fifo#(ra_item_t) requests;
        ra_vif_t                          vif;

        `uvm_component_utils(req_ack_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            ra_config_t cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(ra_vif_t)::get(this, "", "ra", vif)) `uvm_fatal("LB_CFG", "no virtual req_ack_if 'ra'")
            cfg = ra_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "ra";
            uvm_config_db#(ra_config_t)::set(this, "obs", "cfg", cfg);
            obs      = ra_agent_t::type_id::create("obs", this);
            sb       = lb_scoreboard#(ra_item_t)::type_id::create("sb", this);
            requests = new("requests", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(sb.imp);
            obs.mon.req_ap.connect(requests.analysis_export);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
        endfunction

        // One clock per call: the pins as the next rising edge sees them.
        task drive(bit req, int unsigned value, bit ack, int unsigned rvalue = 0);
            vif.req   <= req;
            vif.data  <= lb_data_t'(value);
            vif.ack   <= ack;
            vif.rdata <= lb_rdata_t'(rvalue);
            clk_vif.drive_edge();
        endtask

        function void expect_transfer(int unsigned value, int unsigned rvalue);
            ra_item_t it = ra_item_t::type_id::create("it");
            it.data  = lb_data_t'(value);
            it.rdata = lb_rdata_t'(rvalue);
            sb.expected.push_back(it);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            drive(0, 0, 0);
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            expect_transfer(1, 'h11);
            expect_transfer(4, 'h44);
            expect_transfer(5, 'h55);
            expect_transfer(6, 'h66);
            expect_transfer(7, 'h77);
            drive(1, 1, 0);        // transfer after one wait
            drive(1, 1, 1, 'h11);
            drive(0, 0, 0);
            drive(1, 2, 0);        // req dropped before ack
            drive(0, 2, 0);
            drive(1, 3, 0);        // data changed before ack, then the transfer
            drive(1, 4, 0);
            drive(1, 4, 1, 'h44);
            drive(0, 0, 0);
            drive(0, 0, 1, 'h99);  // ack with no req
            drive(0, 0, 0);
            drive(1, 5, 1, 'h55);  // acked in its first clock
            drive(1, 6, 1, 'h66);  // back to back
            drive(1, 7, 1, 'h77);
            drive(0, 0, 0);
            repeat (2) clk_vif.drive_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            int unsigned proto = srv.get_id_count("A2C_PROTO");
            int unsigned seen  = requests.used();
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_HOLD, %0d A2C_PROTO, %0d transfers and %0d requests reported", hold,
                                            proto, sb.matched, seen), UVM_NONE)
            if (hold != 2) `uvm_error("LB_CHECKS", $sformatf("expected 2 A2C_HOLD reports, got %0d", hold))
            if (proto != 1) `uvm_error("LB_CHECKS", $sformatf("expected 1 A2C_PROTO report, got %0d", proto))
            if (sb.matched != 5) `uvm_error("LB_CHECKS", $sformatf("expected 5 transfers reported, got %0d", sb.matched))
            if (seen != 6) `uvm_error("LB_CHECKS", $sformatf("expected 6 requests on req_ap, got %0d", seen))
        endfunction
    endclass : req_ack_monitor_checks_test
