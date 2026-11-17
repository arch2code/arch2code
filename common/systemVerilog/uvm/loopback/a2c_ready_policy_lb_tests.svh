// a2c_ready_policy, the config knobs' constraints and the item gap, included
// in a2c_uvm_loopback_pkg after the agent and video tests.

    // The dst agent's policy is a2c_always_ready_policy, by an instance
    // override from the test, so the agent acks each transfer in the clock
    // push rises, though its config asks for 0 to 3 extra clocks. The src
    // driver raises push at the drive point after the rising edge, with 0 to
    // 2 idle clocks between items. Every clock with push high must have ack
    // high, and so transfer an item.
    class push_ack_dst_same_clock_test extends pa_pair_test;
        int unsigned push_clocks;

        `uvm_component_utils(push_ack_dst_same_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(pa_config_t cfg);
            cfg.ack_delay_max = 3;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_ready_policy::type_id::set_inst_override(a2c_always_ready_policy::get_type(), "dst.drv.policy", this);
            super.build_phase(phase);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (dst_cfg.vif.push === 1'b1) begin
                        push_clocks++;
                        if (dst_cfg.vif.ack !== 1'b1) `uvm_error("LB_SAME_CLOCK", "push is high and ack low: the transfer waited")
                    end
                end
            join_none
            send(n_items);
            wait_matched(sb, n_items, 4 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            a2c_always_ready_policy p;
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d transfers in %0d clocks with push high", sb.matched, push_clocks), UVM_NONE)
            if (!$cast(p, dst.drv.policy)) `uvm_error("LB_POLICY", $sformatf("the dst driver's policy is %s", dst.drv.policy.get_type_name()))
            if (push_clocks != sb.matched) begin
                `uvm_error("LB_SAME_CLOCK", $sformatf("%0d transfers took %0d clocks with push high", sb.matched, push_clocks))
            end
        endfunction
    endclass : push_ack_dst_same_clock_test

    // As push_ack_dst_same_clock_test, for notify_ack, with a type override.
    class notify_ack_dst_same_clock_test extends na_pair_test;
        int unsigned notify_clocks;

        `uvm_component_utils(notify_ack_dst_same_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(na_config_t cfg);
            cfg.ack_delay_max = 3;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_ready_policy::type_id::set_type_override(a2c_always_ready_policy::get_type());
            super.build_phase(phase);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (dst_cfg.vif.notify === 1'b1) begin
                        notify_clocks++;
                        if (dst_cfg.vif.ack !== 1'b1) `uvm_error("LB_SAME_CLOCK", "notify is high and ack low: the event waited")
                    end
                end
            join_none
            send(n_items);
            wait_matched(sb, n_items, 4 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d events in %0d clocks with notify high", sb.matched, notify_clocks), UVM_NONE)
            if (notify_clocks != sb.matched) begin
                `uvm_error("LB_SAME_CLOCK", $sformatf("%0d events took %0d clocks with notify high", sb.matched, notify_clocks))
            end
        endfunction
    endclass : notify_ack_dst_same_clock_test

    // Mode B: the A2C_DST agent with a2c_always_ready_policy acks both lanes,
    // whose peers push with gaps drawn per lane, so either lane reaches a
    // transfer first. The DUT lane must ack every transfer in the clock its
    // push rises. The model lane must ack transfer n in the clock its own
    // push rises if the DUT lane has acked n by then, and otherwise in the
    // clock the DUT lane acks it. lb_hs_mode_b checks the rest.
    class push_ack_mode_b_dst_same_clock_test extends pa_mode_b;
        // Per lane, the clocks each transfer's push rose and its ack came.
        int unsigned started[2][$];
        int unsigned ended[2][$];

        `uvm_component_utils(push_ack_mode_b_dst_same_clock_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role    = A2C_DST;
            variant = LB_MATCH;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_ready_policy::type_id::set_inst_override(a2c_always_ready_policy::get_type(), "agent.drv.policy", this);
            super.build_phase(phase);
        endfunction

        virtual task run_phase(uvm_phase phase);
            fork
                watch();
            join_none
            super.run_phase(phase);
        endtask

        protected task watch();
            int unsigned clk;
            bit          open[2];
            clk_vif.wait_reset_release();
            forever begin
                clk_vif.sample_edge();
                clk++;
                for (int l = 0; l < 2; l++) begin
                    pa_vif_t v = (l == A2C_DUT_LANE) ? vif : model_vif;
                    if (v.push !== 1'b1) continue;
                    if (!open[l]) started[l].push_back(clk);
                    open[l] = 1;
                    if (v.ack !== 1'b1) continue;
                    ended[l].push_back(clk);
                    open[l] = 0;
                end
            end
        endtask

        virtual function void check_phase(uvm_phase phase);
            int unsigned n = (ended[A2C_DUT_LANE].size() < ended[A2C_MODEL_LANE].size()) ? ended[A2C_DUT_LANE].size()
                                                                                          : ended[A2C_MODEL_LANE].size();
            int unsigned waited = 0;
            super.check_phase(phase);
            foreach (ended[A2C_DUT_LANE][i]) begin
                if (ended[A2C_DUT_LANE][i] != started[A2C_DUT_LANE][i]) begin
                    `uvm_error("LB_SAME_CLOCK", $sformatf("DUT lane transfer %0d: push rose on clock %0d and ack came on clock %0d", i,
                                                          started[A2C_DUT_LANE][i], ended[A2C_DUT_LANE][i]))
                end
            end
            for (int unsigned i = 0; i < n; i++) begin
                int unsigned want = (started[A2C_MODEL_LANE][i] > ended[A2C_DUT_LANE][i]) ? started[A2C_MODEL_LANE][i]
                                                                                         : ended[A2C_DUT_LANE][i];
                waited += (ended[A2C_MODEL_LANE][i] != started[A2C_MODEL_LANE][i]);
                if (ended[A2C_MODEL_LANE][i] != want) begin
                    `uvm_error("LB_SAME_CLOCK", $sformatf("model lane transfer %0d: push rose on clock %0d and ack came on clock %0d; the DUT lane acked it on clock %0d, so it is due on clock %0d",
                                                          i, started[A2C_MODEL_LANE][i], ended[A2C_MODEL_LANE][i],
                                                          ended[A2C_DUT_LANE][i], want))
                end
            end
            `uvm_info("LB_STATS", $sformatf("%0d transfers paired; the model lane waited for the DUT lane on %0d", n, waited), UVM_NONE)
            if (n != n_items) `uvm_error("LB_SAME_CLOCK", $sformatf("%0d transfers completed on both lanes, expected %0d", n, n_items))
            if (waited == 0 || waited == n) begin
                `uvm_error("LB_SAME_CLOCK", $sformatf("the model lane waited on %0d of %0d transfers, so one timing went untested", waited, n))
            end
        endfunction
    endclass : push_ack_mode_b_dst_same_clock_test

    // The dst agent's policy is a2c_pattern_ready_policy, by a type override,
    // with a stall pattern for rdy. The rdy level of every clock must follow
    // the pattern, from whatever entry the first clock after reset release
    // finds, and every beat must arrive in order.
    class rdy_vld_ready_pattern_test extends lb_base_test;
        rv_agent_t                src;
        rv_agent_t                dst;
        lb_scoreboard#(rv_item_t) sb;
        rv_vif_t                  vif;
        bit                       pattern[$] = '{1, 0, 0, 1, 1, 1, 0};
        bit                       seen[$];

        `uvm_component_utils(rdy_vld_ready_pattern_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            rv_config_t src_cfg = rv_config_t::type_id::create("src_cfg");
            rv_config_t dst_cfg = rv_config_t::type_id::create("dst_cfg");
            super.build_phase(phase);
            a2c_ready_policy::type_id::set_type_override(a2c_pattern_ready_policy::get_type());
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", vif)) `uvm_fatal("LB_CFG", "no virtual rdy_vld_if 'rv'")
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "rv";
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "rv";
            uvm_config_db#(rv_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(rv_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = rv_agent_t::type_id::create("src", this);
            dst = rv_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(rv_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            a2c_pattern_ready_policy p;
            dst.mon.ap.connect(sb.imp);
            if (!$cast(p, dst.drv.policy)) `uvm_fatal("LB_POLICY", $sformatf("the dst driver's policy is %s", dst.drv.policy.get_type_name()))
            p.ready_pattern = pattern;
        endfunction

        virtual task run_phase(uvm_phase phase);
            rv_seq seq = rv_seq::type_id::create("seq");
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    seen.push_back(vif.rdy === 1'b1);
                end
            join_none
            seq.n       = n_items;
            seq.max_gap = 1;
            seq.sb      = sb;
            seq.start(src.sqr);
            wait_matched(sb, n_items, 4 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            int unsigned n = pattern.size();
            int          at = -1;
            super.check_phase(phase);
            for (int unsigned o = 0; o < n && at < 0; o++) begin
                bit fits = 1;
                for (int unsigned j = 0; j < n && j < seen.size(); j++) fits &= (seen[j] == pattern[(o + j) % n]);
                if (fits) at = o;
            end
            if (at < 0) begin
                `uvm_error("LB_PATTERN", $sformatf("the first rdy levels %p are no rotation of the pattern %p", seen[0:n - 1], pattern))
                return;
            end
            foreach (seen[j]) begin
                if (seen[j] != pattern[(at + j) % n]) begin
                    `uvm_error("LB_PATTERN", $sformatf("clock %0d after reset release: rdy %0b, the pattern has %0b", j, seen[j], pattern[(at + j) % n]))
                    break;
                end
            end
            `uvm_info("LB_STATS", $sformatf("%0d beats over %0d clocks of the rdy pattern", sb.matched, seen.size()), UVM_NONE)
        endfunction
    endclass : rdy_vld_ready_pattern_test

    // The dst agent's policy is a2c_pattern_ready_policy with ack delays 0,
    // 2, 1 and 3 in turn. Transfer i must wait the pattern's entry i, in
    // clocks with push high and ack low, and a delay of 0 acks in push's
    // own clock.
    class push_ack_delay_pattern_test extends pa_pair_test;
        int unsigned pattern[$] = '{0, 2, 1, 3};
        int unsigned waits[$];

        `uvm_component_utils(push_ack_delay_pattern_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_ready_policy::type_id::set_inst_override(a2c_pattern_ready_policy::get_type(), "dst.drv.policy", this);
            super.build_phase(phase);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            a2c_pattern_ready_policy p;
            super.connect_phase(phase);
            if (!$cast(p, dst.drv.policy)) `uvm_fatal("LB_POLICY", $sformatf("the dst driver's policy is %s", dst.drv.policy.get_type_name()))
            p.delay_pattern = pattern;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            fork
                begin
                    int unsigned run = 0;
                    forever begin
                        clk_vif.sample_edge();
                        if (dst_cfg.vif.push !== 1'b1) continue;
                        if (dst_cfg.vif.ack === 1'b1) begin
                            waits.push_back(run);
                            run = 0;
                        end else begin
                            run++;
                        end
                    end
                end
            join_none
            send(n_items);
            wait_matched(sb, n_items, 8 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (waits.size() != n_items) `uvm_error("LB_PATTERN", $sformatf("%0d transfers, expected %0d", waits.size(), n_items))
            foreach (waits[i]) begin
                if (waits[i] != pattern[i % pattern.size()]) begin
                    `uvm_error("LB_PATTERN", $sformatf("transfer %0d waited %0d clocks, the pattern has %0d", i, waits[i], pattern[i % pattern.size()]))
                    break;
                end
            end
            `uvm_info("LB_STATS", $sformatf("%0d transfers waited by the pattern %p", waits.size(), pattern), UVM_NONE)
        endfunction
    endclass : push_ack_delay_pattern_test

    // A derived config of the kind a test would add, constraining one knob.
    class lb_slow_rv_config extends rv_config_t;
        constraint c_slow { ready_pct == 25; }

        `uvm_object_utils(lb_slow_rv_config)

        function new(string name = "lb_slow_rv_config");
            super.new(name);
        endfunction
    endclass : lb_slow_rv_config

    // randomize() with no constraint of the test's own leaves every config,
    // video cfg and item knob at its declared default; an inline constraint
    // replaces a soft default it excludes and keeps the others; c_valid
    // holds a range together; and a config class a factory override puts in
    // the env's place applies its own constraints.
    class a2c_rand_knobs_test extends lb_base_test;
        `uvm_component_utils(a2c_rand_knobs_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function void expect_eq(string what, longint unsigned got, longint unsigned want);
            if (got != want) `uvm_error("LB_RAND_KNOBS", $sformatf("%s is %0d, expected %0d", what, got, want))
        endfunction

        protected function void defaults();
            rv_config_t   rv = rv_config_t::type_id::create("rv");
            axis_config_t axis = axis_config_t::type_id::create("axis");
            pa_config_t   pa = pa_config_t::type_id::create("pa");
            na_config_t   na = na_config_t::type_id::create("na");
            apb_config_t  apb = apb_config_t::type_id::create("apb");
            axr_config_t  axr = axr_config_t::type_id::create("axr");
            axw_config_t  axw = axw_config_t::type_id::create("axw");
            a2c_video_cfg v = a2c_video_cfg::type_id::create("v");
            rv_item_t     rvi = rv_item_t::type_id::create("rvi");
            pa_item_t     pai = pa_item_t::type_id::create("pai");
            axr_item_t    axri = axr_item_t::type_id::create("axri");
            if (!(rv.randomize() && axis.randomize() && pa.randomize() && na.randomize() && apb.randomize() && axr.randomize()
                  && axw.randomize() && v.randomize() && rvi.randomize() && pai.randomize() && axri.randomize())) begin
                `uvm_error("LB_RAND_KNOBS", "a randomize() with no inline constraint failed")
                return;
            end
            expect_eq("rdy_vld ready_pct", rv.ready_pct, 100);
            expect_eq("rdy_vld burst", rv.burst, 0);
            expect_eq("rdy_vld burst_max", rv.burst_max, 8);
            expect_eq("axi4_stream ready_pct", axis.ready_pct, 100);
            expect_eq("push_ack ack_delay_max", pa.ack_delay_max, 0);
            expect_eq("notify_ack ack_delay_max", na.ack_delay_max, 0);
            expect_eq("apb max_wait", apb.max_wait, 0);
            expect_eq("axi_read arready_pct", axr.arready_pct, 100);
            expect_eq("axi_read resp_delay_max", axr.resp_delay_max, 0);
            expect_eq("axi_read max_outstanding", axr.max_outstanding, 1);
            expect_eq("axi_write wready_pct", axw.wready_pct, 100);
            expect_eq("axi_write reorder", axw.reorder, 0);
            expect_eq("video width", v.width, 64);
            expect_eq("video height", v.height, 8);
            expect_eq("video frames", v.frames, 3);
            expect_eq("video h_blank_min", v.h_blank_min, 2);
            expect_eq("video v_blank_max", v.v_blank_max, 8);
            expect_eq("video lead_clocks", v.lead_clocks, 4);
            expect_eq("video pixel_mode", v.pixel_mode, A2C_PIX_RAMP);
            expect_eq("rdy_vld item gap", rvi.gap, 0);
            expect_eq("push_ack item gap", pai.gap, 0);
            expect_eq("axi_read item gap", axri.gap, 0);
        endfunction

        protected function void constrained();
            rv_config_t   rv = rv_config_t::type_id::create("rv");
            a2c_video_cfg v = a2c_video_cfg::type_id::create("v");
            rv_item_t     it = rv_item_t::type_id::create("it");
            if (!rv.randomize() with { ready_pct inside {[30:60]}; burst == 1; }) `uvm_error("LB_RAND_KNOBS", "rdy_vld config randomize() failed")
            if (!(rv.ready_pct inside {[30:60]}) || rv.burst != 1) begin
                `uvm_error("LB_RAND_KNOBS", $sformatf("rdy_vld config drew ready_pct %0d and burst %0d", rv.ready_pct, rv.burst))
            end
            expect_eq("rdy_vld burst_max beside a constrained ready_pct", rv.burst_max, 8);
            if (!v.randomize() with { h_blank_max == 1; width == 32; }) `uvm_error("LB_RAND_KNOBS", "video cfg randomize() failed")
            if (v.h_blank_min > 1) `uvm_error("LB_RAND_KNOBS", $sformatf("h_blank_min %0d is above h_blank_max 1", v.h_blank_min))
            expect_eq("video width", v.width, 32);
            expect_eq("video height beside a constrained width", v.height, 8);
            if (!it.randomize() with { gap inside {[2:5]}; }) `uvm_error("LB_RAND_KNOBS", "rdy_vld item randomize() failed")
            if (!(it.gap inside {[2:5]})) `uvm_error("LB_RAND_KNOBS", $sformatf("rdy_vld item drew gap %0d", it.gap))
        endfunction

        protected function void overridden();
            rv_config_t rv;
            rv_config_t::type_id::set_type_override(lb_slow_rv_config::get_type());
            rv = rv_config_t::type_id::create("rv");
            if (!rv.randomize()) `uvm_error("LB_RAND_KNOBS", "the derived config's randomize() failed")
            expect_eq("ready_pct of the derived config", rv.ready_pct, 25);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            defaults();
            constrained();
            overridden();
        endfunction
    endclass : a2c_rand_knobs_test
