// a2c_txn_digest loopback tests, included in a2c_uvm_loopback_pkg after the
// rdy_vld, external_reg and axi_read tests, whose item types and vifs they
// use. run_loopback.sh also runs txn_digest_rv_test, txn_digest_er_test and
// txn_digest_axi_test from this file, and txn_digest_cut_test from
// a2c_replay_drain_lb_tests.svh, under seedRepro.py.

    typedef a2c_txn_digest #(rv_item_t) rv_digest_t;

    function automatic rv_item_t lb_digest_item(int unsigned value);
        rv_item_t it = rv_item_t::type_id::create("it");
        it.data = '{tag: value[3:0], value: value[19:0]};
        return it;
    endfunction

    // Feeds digests directly, with no agent, and checks which streams hash
    // alike: the same items at the same times must match, and a change of
    // one item's time, one item's data, or the order must not, nor may an
    // extra item on the side export. A dual digest keeps its lanes apart.
    // Also checks which comparators pair every item.
    class txn_digest_test extends lb_base_test;
        rv_digest_t ref_d;
        rv_digest_t same_d;
        rv_digest_t late_d;
        rv_digest_t data_d;
        rv_digest_t order_d;
        rv_digest_t dual_d;
        rv_digest_t side_d;
        // Fed nothing.
        rv_digest_t empty_d;
        a2c_in_order_comparator #(rv_item_t) in_order;
        a2c_status_comparator #(rv_item_t)   status;

        `uvm_component_utils(txn_digest_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            ref_d   = digest("ref");
            same_d  = digest("same");
            late_d  = digest("late");
            data_d  = digest("data");
            order_d = digest("order");
            dual_d  = digest("dual");
            side_d  = digest("side");
            empty_d = digest("empty");
            dual_d.dual = 1;
            in_order = a2c_in_order_comparator#(rv_item_t)::type_id::create("in_order", this);
            status   = a2c_status_comparator#(rv_item_t)::type_id::create("status", this);
        endfunction

        function rv_digest_t digest(string port);
            rv_digest_t d = rv_digest_t::type_id::create({port, "_d"}, this);
            d.port_name = port;
            return d;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            #10ns;
            ref_d.analysis_export.write(lb_digest_item(1));
            same_d.analysis_export.write(lb_digest_item(1));
            side_d.analysis_export.write(lb_digest_item(1));
            side_d.side_export.write(lb_digest_item(1));
            late_d.analysis_export.write(lb_digest_item(1));
            data_d.analysis_export.write(lb_digest_item(1));
            order_d.analysis_export.write(lb_digest_item(2));
            dual_d.model_export.write(lb_digest_item(1));
            #10ns;
            ref_d.analysis_export.write(lb_digest_item(2));
            same_d.analysis_export.write(lb_digest_item(2));
            side_d.analysis_export.write(lb_digest_item(2));
            data_d.analysis_export.write(lb_digest_item(3));
            order_d.analysis_export.write(lb_digest_item(1));
            dual_d.model_export.write(lb_digest_item(2));
            #1ns;
            late_d.analysis_export.write(lb_digest_item(2));
            phase.drop_objection(this);
        endtask

        function void expect_digest(string what, rv_digest_t d, bit equal);
            if ((d.digest(A2C_DUT_LANE) == ref_d.digest(A2C_DUT_LANE)) != equal) begin
                `uvm_error("LB_DIGEST", $sformatf("%s: digest %016h, reference %016h, expected them %s", what,
                                                  d.digest(A2C_DUT_LANE), ref_d.digest(A2C_DUT_LANE),
                                                  equal ? "equal" : "different"))
            end
        endfunction

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            expect_digest("the same items at the same times", same_d, 1);
            expect_digest("the second item 1ns later", late_d, 0);
            expect_digest("the second item's data changed", data_d, 0);
            expect_digest("the two items swapped", order_d, 0);
            expect_digest("an extra item on the side export", side_d, 0);
            if (dual_d.digest(A2C_MODEL_LANE) != ref_d.digest(A2C_DUT_LANE)) begin
                `uvm_error("LB_DIGEST", "the model lane's digest of the reference items differs from the reference")
            end
            if (dual_d.digest(A2C_DUT_LANE) != empty_d.digest(A2C_DUT_LANE)) begin
                `uvm_error("LB_DIGEST", "the DUT lane's digest moved with only model lane items")
            end
            check_pairing();
        endfunction

        function void check_pairing();
            if (!in_order.pairs_every_item()) begin
                `uvm_error("LB_DIGEST", "the in-order comparator does not pair every item")
            end
            if (status.pairs_every_item()) begin
                `uvm_error("LB_DIGEST", "the status comparator pairs every item")
            end
        endfunction
    endclass : txn_digest_test

    // A rdy_vld src agent drives a dst agent, and a digest on each monitor
    // reports the stream. c_digest and d_digest are dual, with the dst
    // monitor as their DUT lane and the src monitor as their model lane;
    // c_digest's cmp is an in-order comparator and d_digest's a status
    // comparator, neither fed, as the env's model_cmp would be.
    // +lb_digest_vary picks what the seed changes:
    //   data    random data, no gaps, rdy always high (the default)
    //   timing  data 0, 1, 2 and so on, with random gaps
    //   none    fixed data with no gaps, so every seed gives the same digests
    //   run     as none, plus one item on b_digest from a count the test
    //           keeps in lb_digest_runs.txt, so a second run with the same
    //           seed changes b_digest and leaves a_digest alone
    //   lane    as none, plus one item on c_digest's model lane, so its two
    //           lanes count different items
    //   status  as none, plus one item on d_digest's model lane
    class txn_digest_rv_test extends lb_base_test;
        rv_agent_t                src;
        rv_agent_t                dst;
        lb_scoreboard#(rv_item_t) sb;
        rv_digest_t               a_digest;
        rv_digest_t               b_digest;
        rv_digest_t               c_digest;
        rv_digest_t               d_digest;
        string                    vary = "data";

        `uvm_component_utils(txn_digest_rv_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t src_cfg;
            rv_config_t dst_cfg;
            rv_vif_t    vif;
            super.build_phase(phase);
            void'($value$plusargs("lb_digest_vary=%s", vary));
            if (vary != "data" && vary != "timing" && vary != "none" && vary != "run" && vary != "lane"
                && vary != "status") begin
                `uvm_fatal("LB_CFG", {"unknown +lb_digest_vary=", vary})
            end
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            src_cfg = rv_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "rv";
            dst_cfg = rv_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "rv";
            uvm_config_db#(rv_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(rv_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = rv_agent_t::type_id::create("src", this);
            dst = rv_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(rv_item_t)::type_id::create("sb", this);
            a_digest = rv_digest_t::type_id::create("a_digest", this);
            b_digest = rv_digest_t::type_id::create("b_digest", this);
            c_digest = rv_digest_t::type_id::create("c_digest", this);
            d_digest = rv_digest_t::type_id::create("d_digest", this);
            a_digest.port_name = "a";
            b_digest.port_name = "b";
            c_digest.port_name = "c";
            d_digest.port_name = "d";
            c_digest.dual      = 1;
            d_digest.dual      = 1;
            c_digest.cmp       = a2c_in_order_comparator#(rv_item_t)::type_id::create("c_cmp", this);
            d_digest.cmp       = a2c_status_comparator#(rv_item_t)::type_id::create("d_cmp", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
            src.mon.ap.connect(a_digest.analysis_export);
            dst.mon.ap.connect(b_digest.analysis_export);
            c_digest.watch(dst.mon, A2C_DUT_LANE);
            c_digest.watch(src.mon, A2C_MODEL_LANE);
            d_digest.watch(dst.mon, A2C_DUT_LANE);
            d_digest.watch(src.mon, A2C_MODEL_LANE);
        endfunction

        // The runs before this one, counted in the file the test rewrites.
        function int unsigned bump_run_count();
            int unsigned n = 0;
            int          fd = $fopen("lb_digest_runs.txt", "r");
            if (fd != 0) begin
                void'($fscanf(fd, "%d", n));
                $fclose(fd);
            end
            fd = $fopen("lb_digest_runs.txt", "w");
            $fdisplay(fd, "%0d", n + 1);
            $fclose(fd);
            return n;
        endfunction

        virtual task run_phase(uvm_phase phase);
            int unsigned n = 50;
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            for (int unsigned i = 0; i < n; i++) begin
                rv_item_t it = lb_digest_item(i);
                if (vary == "data" && !it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                if (vary == "timing") it.gap = $urandom_range(3, 0);
                sb.expected.push_back(it);
                src.sqr.execute_item(it);
            end
            wait_matched(sb, n, 100 * n);
            if (vary == "run") b_digest.analysis_export.write(lb_digest_item(bump_run_count()));
            if (vary == "lane") c_digest.model_export.write(lb_digest_item(0));
            if (vary == "status") d_digest.model_export.write(lb_digest_item(0));
            phase.drop_objection(this);
        endtask
    endclass : txn_digest_rv_test

    typedef a2c_txn_digest #(er_item_t) er_digest_t;

    // The dst agent holds rdata at a value drawn from the seed, with
    // update_on_write off, while the src agent sends fixed writes with no
    // gaps, so only the rdata levels on the dst monitor's rdata_ap change
    // with the seed. A digest that watches the dst monitor must see them.
    class txn_digest_er_test extends er_pair_test;
        er_digest_t digest;

        `uvm_component_utils(txn_digest_er_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(er_config_t cfg);
            cfg.update_on_write = 0;
            cfg.value           = lb_data_t'($urandom());
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            digest = er_digest_t::type_id::create("digest", this);
            digest.port_name = "er";
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            digest.watch(dst.mon, A2C_DUT_LANE);
        endfunction

        virtual task run_phase(uvm_phase phase);
            er_seq seq = er_seq::type_id::create("seq");
            phase.raise_objection(this);
            expect_level(dst_cfg.value);
            for (int unsigned i = 0; i < 8; i++) begin
                seq.items.push_back(write_item(2'b01, lb_data_t'(i), 0));
                sb.expected.push_back(seq.items[i]);
            end
            clk_vif.wait_reset_release();
            seq.start(src.sqr);
            wait_matched(sb, 8, 40);
            wait_matched(level_sb, 1, 10);
            phase.drop_objection(this);
        endtask
    endclass : txn_digest_er_test

    typedef a2c_txn_digest #(axr_item_t) axr_digest_t;

    // Sends n bursts at fixed addresses, lengths and sizes with no gaps, so
    // only the read data, which the slave's memory draws from the seed,
    // changes with the seed.
    class axr_digest_seq extends axr_seq;
        `uvm_object_utils(axr_digest_seq)

        function new(string name = "axr_digest_seq");
            super.new(name);
        endfunction

        virtual task body();
            for (int unsigned i = 0; i < n; i++) begin
                axr_item_t it = new_item($sformatf("it%0d", i));
                axr_item_t copy;
                it.addr   = 16'h0100 + 16'h40 * i;
                it.id     = 0;
                it.len    = 3;
                it.size   = 2;
                it.burst  = AXI_INCR;
                it.aruser = 0;
                it.gap    = 0;
                $cast(copy, it.clone());
                waiting.push_back(copy);
                send(it);
            end
            wait_for_reads();
        endtask
    endclass : axr_digest_seq

    // An axi_read master reads the slave's random-fill memory, and a digest
    // on the slave's monitor reports the bursts.
    class txn_digest_axi_test extends axr_pair_test;
        axr_digest_t digest;

        `uvm_component_utils(txn_digest_axi_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            digest = axr_digest_t::type_id::create("digest", this);
            digest.port_name = "axr";
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            slave.mon.ap.connect(digest.analysis_export);
        endfunction

        virtual task run_phase(uvm_phase phase);
            axr_digest_seq seq = axr_digest_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n = 20;
            run_seq(seq);
            phase.drop_objection(this);
        endtask
    endclass : txn_digest_axi_test
