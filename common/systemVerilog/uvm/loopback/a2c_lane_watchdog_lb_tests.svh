// Mode B lane-death tests of the single-transfer masters (push_ack,
// notify_ack, req_ack, pop_ack, rdy_vld, axi4_stream and apb), and of the
// joint stall rule across ports (a2c_joint_watch), included in
// a2c_uvm_loopback_pkg after the agents' tests, whose typedefs and
// sequences it uses, and after axi_mode_b_lb_tests.svh, whose lb_frozen it
// uses.

    // What a lane-death test varies. late_at, stall_at and the delays are
    // members of lb_skew_mode_b:
    //   - LB_SK_MODEL_LATE and LB_SK_DUT_LATE: that lane answers item
    //     late_at late_by clocks late, so it trails the other lane by more
    //     than the skew bound and dies;
    //   - LB_SK_JOINT: both lanes answer item late_at late_by clocks late, so
    //     neither trails and both die in one A2C_JOINT_STALL;
    //   - LB_SK_LAG: the model lane answers every item lag clocks late, a
    //     skew under the bound;
    //   - LB_SK_SKEW_OFF: as LB_SK_MODEL_LATE with the skew bound off;
    //   - LB_SK_LONE: as LB_SK_MODEL_LATE, and the DUT lane, alone, then
    //     answers item stall_at stall_by clocks late and dies under the lone
    //     lane bound;
    //   - LB_SK_LONE_OFF: as LB_SK_LONE with the lone lane bound off;
    //   - LB_SK_JOINT_OFF: as LB_SK_JOINT with the joint stall bound off;
    //   - LB_SK_JOINT_UNDER: as LB_SK_MODEL_LATE with the joint stall bound
    //     below the skew bound. Once the DUT lane has completed the item no
    //     lane moves, and the trailing lane is still the skew bound's;
    //   - LB_SK_JOINT_MODEL_LATE and LB_SK_JOINT_DUT_LATE: as LB_SK_MODEL_LATE
    //     and LB_SK_DUT_LATE with the skew bound off, so once the other lane
    //     has completed the item no lane moves, and both die in one
    //     A2C_JOINT_STALL that names only the late lane as waiting.
    typedef enum {LB_SK_MODEL_LATE, LB_SK_DUT_LATE, LB_SK_JOINT, LB_SK_LAG, LB_SK_SKEW_OFF, LB_SK_LONE, LB_SK_LONE_OFF,
                  LB_SK_JOINT_OFF, LB_SK_JOINT_UNDER, LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE} lb_skew_variant_e;

    // Mode B on one port of a master that puts one item on both lanes and
    // waits for each live lane to complete it. agent, the A2C_SRC agent under
    // test, has the port as its DUT lane and <port>_model as its model lane,
    // and a passive agent, watcher, watches both. Each lane's other side is
    // a script, serve(), that answers the lane's transfer k after the delay
    // the variant gives it, and drives the answer for one clock. Checks:
    //   - the lanes that die, when, and with which message, to the clock;
    //   - how many transfers each lane made: a dead lane holds a request it
    //     had raised, with its payload, until its transfer, and raises no
    //     other (lb_frozen);
    //   - that the master stops waiting for a lane when it declares it dead:
    //     after a skew death the live lane requests the next item before the
    //     dead lane makes its late transfer;
    //   - each item's response, from the DUT lane, or from the model lane
    //     once the DUT lane is dead, or the one it was sent with once both
    //     are;
    //   - the agent's and the watcher's model_cmp report nothing, since the
    //     master tells them of each death.
    // A family's test defines the pin accessors, new_item() and watchdog(),
    // and, with a response, item_ok().
    virtual class lb_skew_mode_b #(type AGENT_T = uvm_agent, type ITEM_T = uvm_sequence_item, type CFG_T = uvm_object,
                                   type VIF_T = int) extends lb_mode_b_base;
        string            port;
        lb_skew_variant_e variant = LB_SK_MODEL_LATE;
        AGENT_T           agent;
        AGENT_T           watcher;
        // Indexed by a2c_lane_e.
        VIF_T             vif[2];
        int unsigned      n_sent = 20;
        int unsigned      late_at = 5;
        int unsigned      stall_at = 10;
        int unsigned      late_by = 100;
        int unsigned      stall_by = 200;
        int unsigned      lag = 30;
        int unsigned      lane_skew = 60;
        int unsigned      lone = 80;
        int unsigned      joint = 70;
        int unsigned      joint_under = 20;
        // The clocks from a lane's transfer to the sample point at which the
        // master counts the item done on it.
        int unsigned      done_lag;
        ITEM_T            items[$];
        // Indexed by a2c_lane_e: the transfers each lane made, and for
        // transfer k the sample point that first saw its request and the
        // one that saw its transfer.
        int unsigned      served[2];
        realtime          seen_at[2][$];
        realtime          took_at[2][$];
        realtime          period;
        lb_frozen         frozen[2];
        lb_list_seq#(ITEM_T) seq;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        pure virtual function bit requested(a2c_lane_e l);
        pure virtual function logic [1023:0] payload(a2c_lane_e l);
        // Drives lane l's side of the port for the coming clock: the answer
        // to transfer k if ack is set, and with post set the clock after
        // transfer k.
        pure virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
        pure virtual function ITEM_T new_item(int unsigned i);
        pure virtual function a2c_lane_watchdog watchdog();

        // Whether item i holds the response it should: the answer to
        // transfer i if a live lane answered it, else what it was sent with.
        virtual function bit item_ok(int unsigned i, ITEM_T it, bit answered);
            return 1;
        endfunction

        // How the master's messages name item i, or "" to leave it unchecked.
        virtual function string what(int unsigned i);
            return "";
        endfunction

        protected function CFG_T lane_cfg(string name, uvm_active_passive_enum active);
            CFG_T cfg = CFG_T::type_id::create(name);
            cfg.vif       = vif[A2C_DUT_LANE];
            cfg.model_vif = vif[A2C_MODEL_LANE];
            cfg.clk_vif   = clk_vif;
            cfg.role      = A2C_SRC;
            cfg.port_name = port;
            cfg.is_active = active;
            return cfg;
        endfunction

        protected function string lane(int l);
            return a2c_lane_name(a2c_lane_e'(l));
        endfunction

        protected function bit joint_dies();
            return variant inside {LB_SK_JOINT, LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE};
        endfunction

        // In LB_SK_JOINT_MODEL_LATE and LB_SK_JOINT_DUT_LATE, the lane that
        // answers late.
        protected function a2c_lane_e late_lane();
            return (variant == LB_SK_JOINT_DUT_LATE) ? A2C_DUT_LANE : A2C_MODEL_LANE;
        endfunction

        protected function void want_skew(a2c_lane_e l);
            want_text.push_back({port, ": the ", lane(l), " lane has not completed ", what(late_at)});
            want_text.push_back($sformatf(" %0d clocks after the %s lane did (lane_skew_cycles, +a2c_lane_skew_cycles), so the master declares the %s lane dead. The %s lane serves every item from now on.",
                                          lane_skew, lane(1 - l), lane(l), lane(1 - l)));
        endfunction

        virtual function void build_phase(uvm_phase phase);
            CFG_T agent_cfg;
            CFG_T watcher_cfg;
            if (joint_dies()) demote_id = "A2C_JOINT_STALL";
            else demote_id = "A2C_SKEW";
            super.build_phase(phase);
            if (!uvm_config_db#(VIF_T)::get(this, "", port, vif[A2C_DUT_LANE])) `uvm_fatal("LB_CFG", {"no interface ", port})
            if (!uvm_config_db#(VIF_T)::get(this, "", {port, "_model"}, vif[A2C_MODEL_LANE])) `uvm_fatal("LB_CFG", {"no interface ", port, "_model"})
            agent_cfg   = lane_cfg("agent_cfg", UVM_ACTIVE);
            watcher_cfg = lane_cfg("watcher_cfg", UVM_PASSIVE);
            uvm_config_db#(CFG_T)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(CFG_T)::set(this, "watcher", "cfg", watcher_cfg);
            agent   = AGENT_T::type_id::create("agent", this);
            watcher = AGENT_T::type_id::create("watcher", this);
            uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_lane_skew_cycles",
                                              (variant inside {LB_SK_SKEW_OFF, LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE}) ? 0 : lane_skew);
            uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_lone_lane_cycles", (variant == LB_SK_LONE_OFF) ? 0 : lone);
            uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_joint_stall_cycles", joint_bound());
            for (int unsigned i = 0; i < n_sent; i++) items.push_back(new_item(i));
            for (int l = 0; l < 2; l++) frozen[l] = lb_frozen::of({port, " ", lane(l), " lane"});
            case (variant)
                LB_SK_MODEL_LATE, LB_SK_LONE_OFF, LB_SK_JOINT_UNDER: begin
                    want_errors = 1;
                    want_skew(A2C_MODEL_LANE);
                end
                LB_SK_DUT_LATE: begin
                    want_errors = 1;
                    want_skew(A2C_DUT_LANE);
                end
                LB_SK_LONE: begin
                    want_errors = 2;
                    want_skew(A2C_MODEL_LANE);
                    want_text.push_back($sformatf("%s: the DUT lane, alone since the model lane died, has completed nothing for %0d clocks, waiting for ",
                                                  port, lone));
                    want_text.push_back(" (lone_lane_cycles, +a2c_lone_lane_cycles), so the master declares the DUT lane dead. This is likely a consequence of the earlier A2C_SKEW, which declared the model lane dead at ");
                    want_text.push_back(". No lane is left, so every open and later item completes at once");
                end
                LB_SK_JOINT, LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE: begin
                    string waiters = "both lanes";
                    if (variant != LB_SK_JOINT) waiters = {"the ", lane(late_lane()), " lane"};
                    want_errors = 1;
                    want_text.push_back($sformatf("%s: no port has made a handshake on any lane for %0d of this port's clocks (joint_stall_cycles, +a2c_joint_stall_cycles), while lanes waited on these ports: %s (uvm_test_top.agent.drv), %s waiting for ",
                                                  port, joint, port, waiters));
                    want_text.push_back(". No port made progress, so the cause may lie in the DUT, the model or the stimulus");
                    want_text.push_back(". Every Mode B master, whatever its own joint_stall_cycles, declares the live lanes of its port dead, and serves its open and later items as it does once both lanes are dead.");
                end
                default: ;
            endcase
        endfunction

        // With the skew bound off, a trailing lane that waits while no port
        // moves is the joint bound's, so LB_SK_SKEW_OFF sets that above the
        // late lane's wait.
        protected function int unsigned joint_bound();
            case (variant)
                LB_SK_JOINT_OFF:   return 0;
                LB_SK_JOINT_UNDER: return joint_under;
                LB_SK_SKEW_OFF:    return late_by + joint;
            endcase
            return joint;
        endfunction

        // The clocks lane l waits before it answers transfer k.
        protected function int unsigned delay(a2c_lane_e l, int unsigned k);
            case (variant)
                LB_SK_MODEL_LATE, LB_SK_SKEW_OFF, LB_SK_JOINT_UNDER, LB_SK_JOINT_MODEL_LATE:
                                                  return (l == A2C_MODEL_LANE && k == late_at) ? late_by : 0;
                LB_SK_DUT_LATE, LB_SK_JOINT_DUT_LATE: return (l == A2C_DUT_LANE && k == late_at) ? late_by : 0;
                LB_SK_JOINT, LB_SK_JOINT_OFF:     return (k == late_at) ? late_by : 0;
                LB_SK_LAG:                        return (l == A2C_MODEL_LANE) ? lag : 0;
                LB_SK_LONE, LB_SK_LONE_OFF: begin
                    if (l == A2C_MODEL_LANE && k == late_at) return late_by;
                    return (l == A2C_DUT_LANE && k == stall_at) ? stall_by : 0;
                end
            endcase
            return 0;
        endfunction

        protected function int unsigned want_served(a2c_lane_e l);
            case (variant)
                LB_SK_MODEL_LATE, LB_SK_LONE_OFF, LB_SK_JOINT_UNDER: return (l == A2C_MODEL_LANE) ? late_at + 1 : n_sent;
                LB_SK_DUT_LATE:                   return (l == A2C_DUT_LANE) ? late_at + 1 : n_sent;
                LB_SK_JOINT, LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE: return late_at + 1;
                LB_SK_LONE:                       return (l == A2C_MODEL_LANE) ? late_at + 1 : stall_at + 1;
            endcase
            return n_sent;
        endfunction

        protected function bit want_dead(a2c_lane_e l);
            case (variant)
                LB_SK_MODEL_LATE, LB_SK_LONE_OFF, LB_SK_JOINT_UNDER: return l == A2C_MODEL_LANE;
                LB_SK_DUT_LATE:                   return l == A2C_DUT_LANE;
                LB_SK_JOINT, LB_SK_LONE, LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE: return 1;
            endcase
            return 0;
        endfunction

        // A trailing lane dies lane_skew clocks after the sample point at
        // which the other lane completed the item; a lone stalled lane after
        // lone sample points without progress, counting the first that saw
        // the request. The joint stall counts the sample points at which a
        // lane waits and no handshake came since the master's previous one,
        // so the first it counts is the second at which a lane waits after
        // the last handshake.
        protected function realtime want_died(a2c_lane_e l);
            if (variant == LB_SK_JOINT) return seen_at[l][late_at] + joint * period;
            if (variant inside {LB_SK_JOINT_MODEL_LATE, LB_SK_JOINT_DUT_LATE}) begin
                return took_at[1 - late_lane()][late_at] + (done_lag + joint + 1) * period;
            end
            if (variant == LB_SK_LONE && l == A2C_DUT_LANE) return seen_at[l][stall_at] + (lone - 1) * period;
            return took_at[1 - l][late_at] + (done_lag + lane_skew) * period;
        endfunction

        protected function bit answered(int unsigned i);
            if (variant == LB_SK_JOINT) return i < late_at;
            if (variant == LB_SK_LONE) return i < stall_at;
            return 1;
        endfunction

        // Lane l's other side. Each clock it records a transfer the last
        // clock's answer made, and answers a request it has waited delay()
        // clocks for.
        protected task serve(a2c_lane_e l);
            a2c_lane_watchdog wd;
            int unsigned      waited;
            bit               acking;
            bit               post;
            realtime          last;
            drive(l, 0, 0, 0);
            clk_vif.wait_reset_release();
            forever begin
                clk_vif.sample_edge();
                if (period == 0 && last != 0) period = $realtime - last;
                last = $realtime;
                wd = watchdog();
                if (wd != null) frozen[l].sample(wd.dead[l], wd.died_at[l], requested(l), acking, payload(l));
                post = acking;
                if (acking) begin
                    took_at[l].push_back($realtime);
                    served[l]++;
                    acking = 0;
                    waited = 0;
                end else if (requested(l)) begin
                    if (seen_at[l].size() == served[l]) seen_at[l].push_back($realtime);
                    if (waited >= delay(l, served[l])) acking = 1;
                    else waited++;
                end
                clk_vif.drive_edge();
                drive(l, acking, post, post ? served[l] - 1 : served[l]);
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            int unsigned clocks;
            seq = lb_list_seq#(ITEM_T)::type_id::create("seq");
            phase.raise_objection(this);
            fork
                serve(A2C_DUT_LANE);
                serve(A2C_MODEL_LANE);
            join_none
            clk_vif.wait_reset_release();
            seq.items = items;
            seq.start(agent.sqr);
            // A dead lane's open transfer still ends, after the sequence.
            while ((served[A2C_DUT_LANE] < want_served(A2C_DUT_LANE) || served[A2C_MODEL_LANE] < want_served(A2C_MODEL_LANE))
                   && clocks < 1000) begin
                clk_vif.sample_edge();
                clocks++;
            end
            repeat (done_lag + 3) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            a2c_lane_watchdog wd = watchdog();
            super.check_phase(phase);
            for (int l = 0; l < 2; l++) begin
                a2c_lane_e e = a2c_lane_e'(l);
                if (served[l] != want_served(e)) begin
                    `uvm_error("LB_MODE_B", $sformatf("the %s lane made %0d transfers, expected %0d", lane(l), served[l], want_served(e)))
                end
                if (wd.dead[l] != want_dead(e)) begin
                    `uvm_error("LB_MODE_B", $sformatf("the %s lane is %s, expected it %s", lane(l), wd.dead[l] ? "dead" : "live",
                                                      want_dead(e) ? "dead" : "live"))
                end
                if (wd.dead[l] && want_dead(e) && wd.died_at[l] != want_died(e)) begin
                    `uvm_error("LB_MODE_B", $sformatf("the %s lane died at %0t, expected %0t", lane(l), wd.died_at[l], want_died(e)))
                end
            end
            if (variant inside {LB_SK_MODEL_LATE, LB_SK_DUT_LATE, LB_SK_LONE, LB_SK_LONE_OFF, LB_SK_JOINT_UNDER}) begin
                int d = (variant == LB_SK_DUT_LATE) ? A2C_DUT_LANE : A2C_MODEL_LANE;
                if (seen_at[1 - d].size() <= late_at + 1 || took_at[d].size() <= late_at || seen_at[1 - d][late_at + 1] >= took_at[d][late_at]) begin
                    `uvm_error("LB_MODE_B", $sformatf("the %s lane did not request item %0d before the dead %s lane's late transfer",
                                                      lane(1 - d), late_at + 1, lane(d)))
                end
                // The death ends the item the dead lane owed within its
                // clock, at the sample point or the drive point after it.
                if (seq.done_at.size() <= late_at || seq.done_at[late_at] < wd.died_at[d] || seq.done_at[late_at] >= wd.died_at[d] + period) begin
                    `uvm_error("LB_MODE_B", $sformatf("item %0d completed at %0t, expected within the clock of the %s lane's death at %0t", late_at,
                                                      (seq.done_at.size() > late_at) ? seq.done_at[late_at] : 0, lane(d), wd.died_at[d]))
                end
            end
            foreach (items[i]) begin
                if (!item_ok(i, items[i], answered(i))) begin
                    `uvm_error("LB_MODE_B", $sformatf("item %0d holds %s", i, items[i].convert2string()))
                end
            end
        endfunction
    endclass : lb_skew_mode_b

    // The response the scripts give to transfer k.
    function automatic logic [31:0] lb_skew_answer(int unsigned k);
        return 32'(k * 37 + 11);
    endfunction

    class pa_skew extends lb_skew_mode_b #(pa_agent_t, pa_item_t, pa_config_t, pa_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "pa";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].push === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return 1024'(vif[l].data);
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].ack <= ack;
        endfunction

        virtual function pa_item_t new_item(int unsigned i);
            pa_item_t it = pa_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
            it.data.value = 20'(i);
            return it;
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            return agent.drv.wd;
        endfunction
    endclass : pa_skew

    class push_ack_mode_b_model_late_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : push_ack_mode_b_model_late_test

    class push_ack_mode_b_dut_late_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : push_ack_mode_b_dut_late_test

    class push_ack_mode_b_joint_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : push_ack_mode_b_joint_test

    class push_ack_mode_b_lag_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_LAG;
        endfunction
    endclass : push_ack_mode_b_lag_test

    class push_ack_mode_b_skew_off_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_skew_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_SKEW_OFF;
        endfunction
    endclass : push_ack_mode_b_skew_off_test

    class push_ack_mode_b_lone_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_lone_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_LONE;
        endfunction
    endclass : push_ack_mode_b_lone_test

    class push_ack_mode_b_lone_off_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_lone_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_LONE_OFF;
        endfunction
    endclass : push_ack_mode_b_lone_off_test

    class push_ack_mode_b_joint_off_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_joint_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT_OFF;
        endfunction
    endclass : push_ack_mode_b_joint_off_test

    class push_ack_mode_b_joint_under_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_joint_under_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT_UNDER;
        endfunction
    endclass : push_ack_mode_b_joint_under_test

    class push_ack_mode_b_joint_model_late_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_joint_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT_MODEL_LATE;
        endfunction
    endclass : push_ack_mode_b_joint_model_late_test

    class push_ack_mode_b_joint_dut_late_test extends pa_skew;
        `uvm_component_utils(push_ack_mode_b_joint_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT_DUT_LATE;
        endfunction
    endclass : push_ack_mode_b_joint_dut_late_test

    class na_skew extends lb_skew_mode_b #(na_agent_t, na_item_t, na_config_t, na_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "na";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].notify === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return '0;
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].ack <= ack;
        endfunction

        virtual function na_item_t new_item(int unsigned i);
            return na_item_t::type_id::create("it");
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            return agent.drv.wd;
        endfunction
    endclass : na_skew

    class notify_ack_mode_b_model_late_test extends na_skew;
        `uvm_component_utils(notify_ack_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : notify_ack_mode_b_model_late_test

    class notify_ack_mode_b_dut_late_test extends na_skew;
        `uvm_component_utils(notify_ack_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : notify_ack_mode_b_dut_late_test

    class notify_ack_mode_b_joint_test extends na_skew;
        `uvm_component_utils(notify_ack_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : notify_ack_mode_b_joint_test

    class ra_skew extends lb_skew_mode_b #(ra_agent_t, ra_item_t, ra_config_t, ra_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "ra";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].req === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return 1024'(vif[l].data);
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].ack   <= ack;
            vif[l].rdata <= ack ? lb_rdata_t'(lb_skew_answer(k)) : '0;
        endfunction

        virtual function ra_item_t new_item(int unsigned i);
            ra_item_t it = ra_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "req_ack item randomize failed")
            it.data.value = 20'(i);
            it.rdata      = '1;
            return it;
        endfunction

        virtual function bit item_ok(int unsigned i, ra_item_t it, bit answered);
            return it.rdata === (answered ? lb_rdata_t'(lb_skew_answer(i)) : lb_rdata_t'('1));
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            return agent.drv.wd;
        endfunction
    endclass : ra_skew

    class req_ack_mode_b_model_late_test extends ra_skew;
        `uvm_component_utils(req_ack_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : req_ack_mode_b_model_late_test

    class req_ack_mode_b_dut_late_test extends ra_skew;
        `uvm_component_utils(req_ack_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : req_ack_mode_b_dut_late_test

    class req_ack_mode_b_joint_test extends ra_skew;
        `uvm_component_utils(req_ack_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : req_ack_mode_b_joint_test

    class po_skew extends lb_skew_mode_b #(po_agent_t, po_item_t, po_config_t, po_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "po";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].pop === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return '0;
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].ack   <= ack;
            vif[l].rdata <= ack ? lb_data_t'(24'(lb_skew_answer(k))) : '0;
        endfunction

        virtual function po_item_t new_item(int unsigned i);
            po_item_t it = po_item_t::type_id::create("it");
            it.rdata = '1;
            return it;
        endfunction

        virtual function bit item_ok(int unsigned i, po_item_t it, bit answered);
            return it.rdata === (answered ? lb_data_t'(24'(lb_skew_answer(i))) : lb_data_t'('1));
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            return agent.drv.wd;
        endfunction
    endclass : po_skew

    class pop_ack_mode_b_model_late_test extends po_skew;
        `uvm_component_utils(pop_ack_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : pop_ack_mode_b_model_late_test

    class pop_ack_mode_b_dut_late_test extends po_skew;
        `uvm_component_utils(pop_ack_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : pop_ack_mode_b_dut_late_test

    class pop_ack_mode_b_joint_test extends po_skew;
        `uvm_component_utils(pop_ack_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : pop_ack_mode_b_joint_test

    class rv_skew extends lb_skew_mode_b #(rv_agent_t, rv_item_t, rv_config_t, rv_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "rv";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].vld === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return 1024'(vif[l].data);
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].rdy <= ack;
        endfunction

        virtual function rv_item_t new_item(int unsigned i);
            rv_item_t it = rv_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
            it.data.value = 20'(i);
            return it;
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            return agent.drv.wd;
        endfunction
    endclass : rv_skew

    class rdy_vld_mode_b_model_late_test extends rv_skew;
        `uvm_component_utils(rdy_vld_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : rdy_vld_mode_b_model_late_test

    class rdy_vld_mode_b_dut_late_test extends rv_skew;
        `uvm_component_utils(rdy_vld_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : rdy_vld_mode_b_dut_late_test

    class rdy_vld_mode_b_joint_test extends rv_skew;
        `uvm_component_utils(rdy_vld_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : rdy_vld_mode_b_joint_test

    class axis_skew extends lb_skew_mode_b #(axis_agent_t, axis_item_t, axis_config_t, axis_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "axis";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].tvalid === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return 1024'({vif[l].tdata, vif[l].tid, vif[l].tdest, vif[l].tuser, vif[l].tlast, vif[l].tstrb, vif[l].tkeep});
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].tready <= ack;
        endfunction

        virtual function axis_item_t new_item(int unsigned i);
            axis_item_t it = axis_item_t::type_id::create("it");
            if (!it.randomize()) `uvm_fatal("LB_RAND", "axi4_stream item randomize failed")
            return it;
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            return agent.drv.wd;
        endfunction
    endclass : axis_skew

    class axi4_stream_mode_b_model_late_test extends axis_skew;
        `uvm_component_utils(axi4_stream_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : axi4_stream_mode_b_model_late_test

    class axi4_stream_mode_b_dut_late_test extends axis_skew;
        `uvm_component_utils(axi4_stream_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : axi4_stream_mode_b_dut_late_test

    class axi4_stream_mode_b_joint_test extends axis_skew;
        `uvm_component_utils(axi4_stream_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : axi4_stream_mode_b_joint_test

    // Even items write and odd ones read, so item late_at reads.
    class apb_skew extends lb_skew_mode_b #(apb_agent_t, apb_item_t, apb_config_t, apb_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "apb";
        endfunction

        virtual function bit requested(a2c_lane_e l);
            return vif[l].psel === 1'b1 && vif[l].penable === 1'b1;
        endfunction

        virtual function logic [1023:0] payload(a2c_lane_e l);
            return 1024'({vif[l].paddr, vif[l].pwdata, vif[l].pwrite});
        endfunction

        virtual function void drive(a2c_lane_e l, bit ack, bit post, int unsigned k);
            vif[l].pready  <= ack;
            vif[l].prdata  <= ack ? lb_skew_answer(k) : '0;
            vif[l].pslverr <= 1'b0;
        endfunction

        virtual function apb_item_t new_item(int unsigned i);
            apb_item_t it = apb_item_t::type_id::create("it");
            it.write = (i % 2 == 0);
            it.addr  = 4 * i;
            it.data  = it.write ? 3 * i : 32'hffff_ffff;
            return it;
        endfunction

        virtual function string what(int unsigned i);
            if (i % 2 == 0) return $sformatf("the write of address 0x%08h ", 4 * i);
            return $sformatf("the read of address 0x%08h ", 4 * i);
        endfunction

        virtual function bit item_ok(int unsigned i, apb_item_t it, bit answered);
            if (it.write) return it.data == 3 * i;
            return it.data == (answered ? lb_skew_answer(i) : 32'hffff_ffff);
        endfunction

        virtual function a2c_lane_watchdog watchdog();
            apb_master_driver#(lb_apb_word_t, lb_apb_word_t) master;
            if (!$cast(master, agent.drv)) return null;
            return master.wd;
        endfunction
    endclass : apb_skew

    class apb_mode_b_model_late_test extends apb_skew;
        `uvm_component_utils(apb_mode_b_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_MODEL_LATE;
        endfunction
    endclass : apb_mode_b_model_late_test

    class apb_mode_b_dut_late_test extends apb_skew;
        `uvm_component_utils(apb_mode_b_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_DUT_LATE;
        endfunction
    endclass : apb_mode_b_dut_late_test

    class apb_mode_b_joint_test extends apb_skew;
        `uvm_component_utils(apb_mode_b_joint_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_SK_JOINT;
        endfunction
    endclass : apb_mode_b_joint_test

    // The master a2c_lane_watchdog_rules_test gives its watchdogs, which
    // says each lane waits for what the test puts in waits_for.
    class lb_wd_master extends uvm_component implements a2c_lane_waits;
        // Indexed by a2c_lane_e.
        string waits_for[2] = '{"an item", "an item"};

        `uvm_component_utils(lb_wd_master)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function string waiting_for(a2c_lane_e l);
            return waits_for[l];
        endfunction
    endclass : lb_wd_master

    // a2c_lane_watchdog's stall rules on their own, through progress(),
    // with no port: each case feeds a new watchdog clocks of lane progress,
    // one each nanosecond, and checks the clock on which a rule fires, if
    // any.
    //   - joint: both lanes live and waiting fire A2C_BOTH_STALL on the
    //     joint_stall_cycles-th clock, and so does one lane waiting while
    //     the other is idle; a handshake on either lane or anywhere else in
    //     the environment restarts the count from the clock after it,
    //     whether it came before or after progress() in its time step; two
    //     idle lanes never stall; 0 turns the rule off;
    //   - a trailing lane leaves the stall to the skew bound while that is
    //     on, and not once it is off;
    //   - lone: with one lane dead, the other stuck fires A2C_LONE_STALL on
    //     the lone_lane_cycles-th clock, and 0 turns the rule off;
    //   - Mode A: the one lane waiting fires A2C_BOTH_STALL on the
    //     joint_stall_cycles-th clock, a handshake elsewhere restarts the
    //     count, an idle lane never stalls, and 0 turns the rule off;
    //   - after one quiet clock, wait_text() names the lanes that waited in
    //     each of its forms, and joint_waiting() says whether one did,
    //     whatever joint_stall_cycles;
    //   - waiting_now() says whether a live lane waited on the last clock,
    //     after a handshake elsewhere too, with one lane as with two, and
    //     not once every lane that waited is dead; wait_text() of one lane
    //     names no lane.
    class a2c_lane_watchdog_rules_test extends lb_base_test;
        lb_wd_master master;

        `uvm_component_utils(a2c_lane_watchdog_rules_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            master = lb_wd_master::type_id::create("master", this);
        endfunction

        protected function a2c_lane_watchdog make(int unsigned skew, int unsigned lone, int unsigned joint, bit model_dead = 0);
            a2c_lane_watchdog wd = new(master, "unit", 2, "item", "nothing");
            wd.lane_skew_cycles   = skew;
            wd.lone_lane_cycles   = lone;
            wd.joint_stall_cycles = joint;
            wd.dead[A2C_MODEL_LANE] = model_dead;
            return wd;
        endfunction

        // A Mode A watchdog, of one lane.
        protected function a2c_lane_watchdog make_one(int unsigned joint);
            a2c_lane_watchdog wd = new(master, "unit", 1, "item", "nothing");
            wd.joint_stall_cycles = joint;
            return wd;
        endfunction

        // Feeds clocks clocks with no handshake, except on the DUT lane on
        // clock move_at and elsewhere in the environment on clock other_at,
        // each if not 0, and with the lanes idle as dut_idle and model_idle
        // say throughout, and returns the clock, from 1, on which a rule
        // fired, with the rule, or 0. The lane's move is also a handshake,
        // which its monitor would count. The other handshake is two, as two
        // monitors of one transfer report it, before progress() in its time
        // step, or after it with other_after set.
        protected task feed(a2c_lane_watchdog wd, int unsigned clocks, bit trailing, int unsigned move_at, int unsigned other_at,
                            bit other_after, bit dut_idle, bit model_idle, output int unsigned fired, output a2c_stall_e rule);
            bit took[2];
            bit idle[2];
            idle[A2C_DUT_LANE]   = dut_idle;
            idle[A2C_MODEL_LANE] = model_idle;
            rule  = A2C_PROGRESS;
            fired = 0;
            for (int unsigned c = 1; c <= clocks; c++) begin
                #1ns;
                if (c == other_at && !other_after) repeat (2) a2c_joint_watch::handshake();
                took[A2C_DUT_LANE] = (c == move_at);
                if (took[A2C_DUT_LANE]) a2c_joint_watch::handshake();
                rule = wd.progress(took, idle, trailing);
                if (c == other_at && other_after) repeat (2) a2c_joint_watch::handshake();
                if (rule != A2C_PROGRESS) begin
                    fired = c;
                    return;
                end
            end
        endtask

        // Feeds wd as feed() does and checks that rule want_rule fires on
        // clock want, or none if want is 0.
        protected task expect_rule(string what, a2c_lane_watchdog wd, int unsigned clocks, bit trailing, int unsigned move_at,
                                   int unsigned want, a2c_stall_e want_rule, int unsigned other_at = 0, bit dut_idle = 0,
                                   bit model_idle = 0, bit other_after = 0);
            a2c_stall_e  rule;
            int unsigned got;
            feed(wd, clocks, trailing, move_at, other_at, other_after, dut_idle, model_idle, got, rule);
            if (got != want || (want != 0 && rule != want_rule)) begin
                `uvm_error("LB_WD", $sformatf("%s: fired %s on clock %0d, expected %s on clock %0d", what, rule.name(), got, want_rule.name(), want))
            end
            // Else a handshake on the last clock would fall in the window of
            // the next case's first clock.
            #1ns;
        endtask

        // Feeds wd one clock with no handshake and the lanes idle as
        // dut_idle and model_idle say, waiting for dut_for and model_for,
        // and checks what wait_text() and joint_waiting() then return.
        protected task expect_text(string what, a2c_lane_watchdog wd, bit dut_idle, bit model_idle, string dut_for, string model_for,
                                   string want, bit want_waiting = 1);
            bit took[2];
            bit idle[2];
            idle[A2C_DUT_LANE]                = dut_idle;
            idle[A2C_MODEL_LANE]              = model_idle;
            master.waits_for[A2C_DUT_LANE]   = dut_for;
            master.waits_for[A2C_MODEL_LANE] = model_for;
            #1ns;
            void'(wd.progress(took, idle, 0));
            if (wd.joint_waiting() != want_waiting) begin
                `uvm_error("LB_WD", $sformatf("%s: joint_waiting() is %0d, expected %0d", what, wd.joint_waiting(), want_waiting))
            end
            if (want_waiting && wd.wait_text() != want) begin
                `uvm_error("LB_WD", $sformatf("%s: wait_text() is '%s', expected '%s'", what, wd.wait_text(), want))
            end
            #1ns;
        endtask

        // Feeds wd one clock with a handshake elsewhere in the environment
        // and the lanes as took and idle say, with dead lanes as dut_dead and
        // model_dead say after it, and checks waiting_now(), and with
        // want_text set wait_text() too.
        protected task expect_now(string what, a2c_lane_watchdog wd, bit took[2], bit idle[2], bit dut_dead, bit model_dead,
                                  bit want, string want_text = "");
            master.waits_for = '{"x", "y"};
            #1ns;
            a2c_joint_watch::handshake();
            void'(wd.progress(took, idle, 0));
            if (dut_dead || model_dead) wd.dead = '{dut_dead, model_dead};
            if (wd.waiting_now() != want) begin
                `uvm_error("LB_WD", $sformatf("%s: waiting_now() is %0d, expected %0d", what, wd.waiting_now(), want))
            end
            if (want_text != "" && wd.wait_text() != want_text) begin
                `uvm_error("LB_WD", $sformatf("%s: wait_text() is '%s', expected '%s'", what, wd.wait_text(), want_text))
            end
            #1ns;
        endtask

        virtual task run_phase(uvm_phase phase);
            a2c_lane_watchdog one;
            phase.raise_objection(this);
            expect_rule("joint", make(10, 3, 5), 20, 0, 0, 5, A2C_BOTH_STALL);
            expect_rule("joint after a move", make(10, 3, 5), 20, 0, 4, 10, A2C_BOTH_STALL);
            expect_rule("joint after a handshake on another port", make(10, 3, 5), 20, 0, 0, 10, A2C_BOTH_STALL, 4);
            expect_rule("joint after a handshake on another port after progress()", make(10, 3, 5), 20, 0, 0, 10, A2C_BOTH_STALL, 4, 0, 0, 1);
            expect_rule("joint, a handshake on another port on the bound's clock", make(10, 3, 5), 20, 0, 0, 5, A2C_BOTH_STALL, 5);
            expect_rule("joint, the DUT lane idle", make(10, 3, 5), 20, 0, 0, 5, A2C_BOTH_STALL, 0, 1);
            expect_rule("joint, both lanes idle", make(10, 3, 5), 100, 0, 0, 0, A2C_PROGRESS, 0, 1, 1);
            expect_rule("joint off", make(10, 3, 0), 100, 0, 0, 0, A2C_PROGRESS);
            expect_rule("joint while trailing", make(10, 3, 5), 100, 1, 0, 0, A2C_PROGRESS);
            expect_rule("joint while trailing, skew off", make(0, 3, 5), 20, 1, 0, 5, A2C_BOTH_STALL);
            expect_rule("lone", make(10, 3, 5, 1), 20, 0, 0, 3, A2C_LONE_STALL);
            expect_rule("lone off", make(10, 0, 5, 1), 100, 0, 0, 0, A2C_PROGRESS);
            expect_rule("Mode A joint", make_one(5), 20, 0, 0, 5, A2C_BOTH_STALL);
            expect_rule("Mode A joint after a handshake on another port", make_one(5), 20, 0, 0, 10, A2C_BOTH_STALL, 4);
            expect_rule("Mode A joint, the lane idle", make_one(5), 100, 0, 0, 0, A2C_PROGRESS, 0, 1);
            expect_rule("Mode A joint off", make_one(0), 100, 0, 0, 0, A2C_PROGRESS);
            expect_text("both lanes, one text", make(10, 3, 5), 0, 0, "x", "x", "unit (uvm_test_top.master), both lanes waiting for x");
            expect_text("both lanes, two texts", make(10, 3, 5), 0, 0, "x", "y",
                        "unit (uvm_test_top.master), the DUT lane waiting for x and the model lane for y");
            expect_text("the DUT lane", make(10, 3, 5), 0, 1, "x", "y", "unit (uvm_test_top.master), the DUT lane waiting for x");
            expect_text("the model lane", make(10, 3, 5), 1, 0, "x", "y", "unit (uvm_test_top.master), the model lane waiting for y");
            expect_text("the DUT lane alone", make(10, 3, 5, 1), 0, 0, "x", "y", "unit (uvm_test_top.master), the DUT lane, alone, waiting for x");
            expect_text("joint off", make(10, 3, 0), 0, 0, "x", "x", "unit (uvm_test_top.master), both lanes waiting for x");
            expect_text("both lanes idle", make(10, 3, 5), 1, 1, "x", "y", "", 0);
            expect_now("now, both lanes waiting", make(10, 3, 5), '{0, 0}, '{0, 0}, 0, 0, 1,
                       "unit (uvm_test_top.master), the DUT lane waiting for x and the model lane for y");
            expect_now("now, the model lane waiting", make(10, 3, 5), '{1, 0}, '{0, 0}, 0, 0, 1);
            expect_now("now, both lanes moved", make(10, 3, 5), '{1, 0}, '{0, 1}, 0, 0, 0);
            expect_now("now, the model lane dead", make(10, 3, 5), '{0, 0}, '{0, 0}, 0, 1, 1);
            expect_now("now, both lanes dead", make(10, 3, 5), '{0, 0}, '{0, 0}, 1, 1, 0);
            one = new(master, "unit", 1, "item", "nothing");
            expect_now("now, one lane waiting", one, '{0, 0}, '{0, 0}, 0, 0, 1, "unit (uvm_test_top.master), waiting for x");
            expect_now("now, one lane moved", one, '{1, 0}, '{0, 0}, 0, 0, 0);
            expect_now("now, one lane idle", one, '{0, 0}, '{1, 0}, 0, 0, 0);
            phase.drop_objection(this);
        endtask
    endclass : a2c_lane_watchdog_rules_test

    // Mode A agents on one port that keep it moving from reset until stop
    // is set, for the joint stall tests: an A2C_SRC agent sends round after
    // round of items to an A2C_DST agent, or alone where the interface needs
    // no answer, or a script makes the requests of an A2C_DST agent alone.
    // With idle set it sends nothing. Each round is one send(); sent counts
    // the rounds done.
    virtual class lb_mover extends uvm_component;
        string             port;
        virtual a2c_clk_if clk_vif;
        bit                idle;
        bit                stop;
        bit                done;
        int unsigned       sent;
        realtime           started_at;

        function new(string name, uvm_component parent, string port);
            super.new(name, parent);
            this.port = port;
        endfunction

        pure virtual task send();

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(null, "uvm_test_top", "clk", clk_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if 'clk'")
        endfunction

        virtual task run_phase(uvm_phase phase);
            clk_vif.wait_reset_release();
            started_at = $realtime;
            while (!idle && !stop) begin
                send();
                sent++;
            end
            done = 1;
        endtask
    endclass : lb_mover

    // The agents of an lb_mover; src is null with has_src clear, and dst
    // with has_dst clear.
    virtual class lb_pair_mover #(type AGENT_T = uvm_agent, type CFG_T = uvm_object, type VIF_T = int) extends lb_mover;
        bit     has_src = 1;
        bit     has_dst = 1;
        AGENT_T src;
        AGENT_T dst;
        CFG_T   src_cfg;
        CFG_T   dst_cfg;
        VIF_T   vif;

        function new(string name, uvm_component parent, string port);
            super.new(name, parent, port);
        endfunction

        // Sets what the agents need beyond the pins, role and port name.
        virtual function void configure();
        endfunction

        protected function CFG_T make_cfg(string name, a2c_role_e role);
            CFG_T cfg = CFG_T::type_id::create(name);
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(VIF_T)::get(null, "uvm_test_top", port, vif)) `uvm_fatal("LB_CFG", {"no interface ", port})
            src_cfg = make_cfg("src_cfg", A2C_SRC);
            dst_cfg = make_cfg("dst_cfg", A2C_DST);
            configure();
            if (has_src) begin
                uvm_config_db#(CFG_T)::set(this, "src", "cfg", src_cfg);
                src = AGENT_T::type_id::create("src", this);
            end
            if (has_dst) begin
                uvm_config_db#(CFG_T)::set(this, "dst", "cfg", dst_cfg);
                dst = AGENT_T::type_id::create("dst", this);
            end
        endfunction
    endclass : lb_pair_mover

    class lb_na_mover extends lb_pair_mover #(na_agent_t, na_config_t, na_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "na");
        endfunction

        virtual task send();
            lb_list_seq#(na_item_t) seq = new("seq");
            repeat (4) seq.items.push_back(na_item_t::type_id::create("it"));
            seq.start(src.sqr);
        endtask
    endclass : lb_na_mover

    class lb_ra_mover extends lb_pair_mover #(ra_agent_t, ra_config_t, ra_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "ra");
        endfunction

        virtual task send();
            lb_list_seq#(ra_item_t) seq = new("seq");
            repeat (4) begin
                ra_item_t it = ra_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "req_ack item randomize failed")
                it.gap = 0;
                seq.items.push_back(it);
            end
            seq.start(src.sqr);
        endtask
    endclass : lb_ra_mover

    class lb_po_mover extends lb_pair_mover #(po_agent_t, po_config_t, po_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "po");
        endfunction

        virtual task send();
            lb_list_seq#(po_item_t) seq = new("seq");
            repeat (4) seq.items.push_back(po_item_t::type_id::create("it"));
            seq.start(src.sqr);
        endtask
    endclass : lb_po_mover

    class lb_apb_mover extends lb_pair_mover #(apb_agent_t, apb_config_t, apb_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "apb");
        endfunction

        virtual task send();
            lb_list_seq#(apb_item_t) seq = new("seq");
            repeat (4) begin
                apb_item_t it = apb_item_t::type_id::create("it");
                if (!it.randomize() with { addr < 32'h200; addr[1:0] == 2'b00; }) `uvm_fatal("LB_RAND", "apb item randomize failed")
                seq.items.push_back(it);
            end
            seq.start(src.sqr);
        endtask
    endclass : lb_apb_mover

    // An A2C_SRC agent alone, which writes, so only the requester's monitor
    // sees the accesses.
    class lb_mem_mover extends lb_pair_mover #(mem_agent_t, mem_config_t, mem_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "mem");
            has_dst = 0;
        endfunction

        virtual task send();
            mem_seq seq = mem_seq::type_id::create("seq");
            repeat (4) begin
                mem_item_t it = mem_item_t::type_id::create("it");
                it.write = 1;
                it.addr  = lb_mem_addr_t'($urandom());
                it.data  = lb_data_t'($urandom());
                it.gap   = 0;
                seq.items.push_back(it);
            end
            seq.start(src.sqr);
        endtask
    endclass : lb_mem_mover

    // An A2C_SRC agent alone, so only the writer's monitor sees the writes.
    class lb_er_mover extends lb_pair_mover #(er_agent_t, er_config_t, er_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "er");
            has_dst = 0;
        endfunction

        virtual task send();
            er_seq seq = er_seq::type_id::create("seq");
            repeat (4) begin
                er_item_t it = er_item_t::type_id::create("it");
                it.wdata = lb_data_t'($urandom());
                seq.items.push_back(it);
            end
            seq.start(src.sqr);
        endtask
    endclass : lb_er_mover

    // An A2C_DST agent alone, with a script as the stream's source, so only
    // the responder's monitor sees the transfers.
    class lb_axis_mover extends lb_pair_mover #(axis_agent_t, axis_config_t, axis_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "axis");
            has_src = 0;
        endfunction

        virtual task run_phase(uvm_phase phase);
            vif.tvalid <= 1'b0;
            vif.tdata  <= '0;
            vif.tid    <= '0;
            vif.tdest  <= '0;
            vif.tuser  <= '0;
            vif.tlast  <= 1'b0;
            vif.tstrb  <= '1;
            vif.tkeep  <= '1;
            super.run_phase(phase);
        endtask

        virtual task send();
            clk_vif.drive_edge();
            repeat (4) begin
                vif.tvalid <= 1'b1;
                vif.tdata  <= lb_tdata_t'($urandom());
                do clk_vif.sample_edge(); while (vif.tready !== 1'b1);
                clk_vif.drive_edge();
            end
            vif.tvalid <= 1'b0;
        endtask
    endclass : lb_axis_mover

    class lb_axr_mover extends lb_pair_mover #(axr_agent_t, axr_config_t, axr_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "axr");
        endfunction

        virtual function void configure();
            dst_cfg.mem = axi_read_mem_t::type_id::create("mem");
        endfunction

        virtual task send();
            axr_seq seq = axr_seq::type_id::create("seq");
            seq.n            = 4;
            seq.mem          = dst_cfg.mem;
            seq.error_ranges = dst_cfg.error_ranges;
            seq.start(src.sqr);
        endtask
    endclass : lb_axr_mover

    class lb_axw_mover extends lb_pair_mover #(axw_agent_t, axw_config_t, axw_vif_t);
        function new(string name, uvm_component parent);
            super.new(name, parent, "axw");
        endfunction

        virtual task send();
            axw_seq seq = axw_seq::type_id::create("seq");
            seq.n                  = 4;
            seq.model              = new();
            seq.model.error_ranges = dst_cfg.error_ranges;
            seq.start(src.sqr);
        endtask
    endclass : lb_axw_mover

    // What a2c_joint_watch's tests vary:
    //   - LB_JS_ONE_WAITS: both lanes of pa hold item 0's ack for hold
    //     clocks, more than the joint stall bound, while rv transfers an
    //     item every two clocks;
    //   - LB_JS_STOP: from item stop_at on neither port's scripts answer, so
    //     no lane anywhere makes a handshake;
    //   - LB_JS_PAUSE_OFF: as LB_JS_STOP with the joint stall bound off, and
    //     the scripts answering item stop_at after hold clocks;
    //   - LB_JS_RV_WAITS: rv's lanes hold item 0 for hold clocks while pa
    //     transfers;
    //   - LB_JS_RV_DST: as LB_JS_ONE_WAITS with rv's agent an A2C_DST
    //     responder;
    //   - LB_JS_PA_DST: rv's lanes hold item 0 for hold clocks while pa's
    //     agent, an A2C_DST responder, acks a push every three clocks;
    //   - LB_JS_KNOB_OFF: as LB_JS_STOP with pa's joint stall bound off, so
    //     only rv's watchdog can raise the stall;
    //   - LB_JS_LONE: as LB_JS_KNOB_OFF with pa's model lane never answering
    //     item 0, so it dies under pa's skew bound, skew, and pa's DUT lane
    //     waits alone under a lone lane bound above the joint stall bound;
    //   - LB_JS_LONE_DIES: as LB_JS_LONE with pa's lone lane bound,
    //     lone_under, below the joint stall bound and item stop_at pa's
    //     last, so pa's DUT lane dies alone, pa has no item left, and rv
    //     then raises the stall;
    //   - LB_JS_MOVER: rv's lanes hold item 0 for hold clocks while pa sends
    //     nothing and a Mode A pair on another port, mover, moves.
    typedef enum {LB_JS_ONE_WAITS, LB_JS_STOP, LB_JS_PAUSE_OFF, LB_JS_RV_WAITS, LB_JS_RV_DST, LB_JS_PA_DST, LB_JS_KNOB_OFF, LB_JS_LONE,
                  LB_JS_LONE_DIES, LB_JS_MOVER} lb_joint_variant_e;

    // Mode B on two ports at once, push_ack pa and rdy_vld rv, each with an
    // A2C_SRC agent whose lanes' other sides are scripts that answer item k
    // after the delay the variant gives it, on both lanes alike but in
    // LB_JS_LONE and LB_JS_LONE_DIES, so no lane ever trails the other
    // there. In LB_JS_RV_DST and LB_JS_PA_DST that port's agent is an
    // A2C_DST responder and the scripts make its requests. Checks:
    //   - the variants that do not stall: no error and every lane makes
    //     every transfer, and the other port, or in LB_JS_MOVER the mover,
    //     keeps transferring while one port waits;
    //   - LB_JS_STOP, LB_JS_KNOB_OFF and LB_JS_LONE: one A2C_JOINT_STALL,
    //     from rv's watchdog in the last two, which names both ports and
    //     what their live lanes wait for, and every live lane dies with it,
    //     on the clock joint + 1 clocks after the last handshake; an idle
    //     Mode A notify_ack pair beside them, bystander, keeps its master's
    //     lane live; in LB_JS_LONE pa's model lane dies earlier, alone, by
    //     A2C_SKEW;
    //   - LB_JS_LONE_DIES: as LB_JS_LONE, except that both of pa's lanes die
    //     by A2C_SKEW before the stall, which names rv alone.
    virtual class lb_joint_env extends lb_mode_b_base;
        lb_joint_variant_e   variant;
        pa_agent_t           pa_agent;
        rv_agent_t           rv_agent;
        // Indexed by a2c_lane_e.
        pa_vif_t             pa_vif[2];
        rv_vif_t             rv_vif[2];
        int unsigned         n_pa = 4;
        int unsigned         n_rv = 120;
        int unsigned         stop_at = 2;
        int unsigned         joint = 50;
        int unsigned         hold = 150;
        int unsigned         skew = 20;
        int unsigned         lone_under = 30;
        lb_mover             mover;
        lb_na_mover          bystander;
        lb_recording_demoter skews;
        // Indexed by a2c_lane_e: the transfers each lane made.
        int unsigned         pa_served[2];
        int unsigned         rv_served[2];
        // When the last transfer on any lane was sampled, the clock period,
        // and the other port's transfers while the waiting port's item 0
        // waited.
        realtime             last_at;
        realtime             period;
        int unsigned         moved_while_waiting;
        bit                  waiting;
        // LB_JS_MOVER: when rv's DUT lane first saw item 0 and when it took
        // it, and the mover's rounds done then.
        realtime             wait_began;
        realtime             wait_ended;
        int unsigned         sent_at_wait_end;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // LB_JS_MOVER: the mover, which the test makes.
        virtual function lb_mover make_mover();
            return null;
        endfunction

        protected function bit stalls();
            return variant inside {LB_JS_STOP, LB_JS_KNOB_OFF, LB_JS_LONE, LB_JS_LONE_DIES};
        endfunction

        virtual function void build_phase(uvm_phase phase);
            pa_config_t pa_cfg;
            rv_config_t rv_cfg;
            demote_id = "A2C_JOINT_STALL";
            if (stalls()) begin
                // In LB_JS_STOP either port may raise it.
                string by = "rv";
                if (variant == LB_JS_STOP) by = "";
                want_errors = 1;
                want_text.push_back($sformatf("%s: no port has made a handshake on any lane for %0d of this port's clocks (joint_stall_cycles, +a2c_joint_stall_cycles), while lanes waited on these ports: ",
                                              by, joint));
                if (variant == LB_JS_LONE) want_text.push_back("pa (uvm_test_top.pa_agent.drv), the DUT lane, alone, waiting for the transfer of ");
                else if (variant == LB_JS_LONE_DIES) unwant_text.push_back("pa (uvm_test_top.pa_agent.drv), ");
                else want_text.push_back("pa (uvm_test_top.pa_agent.drv), both lanes waiting for the transfer of ");
                want_text.push_back("rv (uvm_test_top.rv_agent.drv), both lanes waiting for the transfer of ");
                want_text.push_back(". No port made progress, so the cause may lie in the DUT, the model or the stimulus");
            end
            super.build_phase(phase);
            skews = lb_recording_demoter::type_id::create("skews");
            skews.demote_id = "A2C_SKEW";
            uvm_report_cb::add(null, skews);
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa", pa_vif[A2C_DUT_LANE])) `uvm_fatal("LB_CFG", "no interface pa")
            if (!uvm_config_db#(pa_vif_t)::get(this, "", "pa_model", pa_vif[A2C_MODEL_LANE])) `uvm_fatal("LB_CFG", "no interface pa_model")
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv", rv_vif[A2C_DUT_LANE])) `uvm_fatal("LB_CFG", "no interface rv")
            if (!uvm_config_db#(rv_vif_t)::get(this, "", "rv_model", rv_vif[A2C_MODEL_LANE])) `uvm_fatal("LB_CFG", "no interface rv_model")
            pa_cfg = pa_config_t::type_id::create("pa_cfg");
            pa_cfg.vif       = pa_vif[A2C_DUT_LANE];
            pa_cfg.model_vif = pa_vif[A2C_MODEL_LANE];
            pa_cfg.clk_vif   = clk_vif;
            pa_cfg.role      = A2C_SRC;
            pa_cfg.port_name = "pa";
            rv_cfg = rv_config_t::type_id::create("rv_cfg");
            rv_cfg.vif       = rv_vif[A2C_DUT_LANE];
            rv_cfg.model_vif = rv_vif[A2C_MODEL_LANE];
            rv_cfg.clk_vif   = clk_vif;
            rv_cfg.role      = A2C_SRC;
            rv_cfg.port_name = "rv";
            if (variant == LB_JS_PA_DST) pa_cfg.role = A2C_DST;
            if (variant == LB_JS_RV_DST) begin
                rv_cfg.role            = A2C_DST;
                rv_cfg.no_backpressure = 1;
            end
            uvm_config_db#(pa_config_t)::set(this, "pa_agent", "cfg", pa_cfg);
            uvm_config_db#(rv_config_t)::set(this, "rv_agent", "cfg", rv_cfg);
            uvm_config_db#(int unsigned)::set(this, "pa_agent.drv", "a2c_lane_skew_cycles", (variant inside {LB_JS_LONE, LB_JS_LONE_DIES}) ? skew : 1000);
            uvm_config_db#(int unsigned)::set(this, "rv_agent.drv", "a2c_lane_skew_cycles", 1000);
            uvm_config_db#(int unsigned)::set(this, "pa_agent.drv", "a2c_lone_lane_cycles", (variant == LB_JS_LONE_DIES) ? lone_under : 1000);
            uvm_config_db#(int unsigned)::set(this, "rv_agent.drv", "a2c_lone_lane_cycles", 1000);
            uvm_config_db#(int unsigned)::set(this, "pa_agent.drv", "a2c_joint_stall_cycles",
                                              (variant inside {LB_JS_PAUSE_OFF, LB_JS_KNOB_OFF, LB_JS_LONE, LB_JS_LONE_DIES}) ? 0 : joint);
            uvm_config_db#(int unsigned)::set(this, "rv_agent.drv", "a2c_joint_stall_cycles", (variant == LB_JS_PAUSE_OFF) ? 0 : joint);
            pa_agent = pa_agent_t::type_id::create("pa_agent", this);
            rv_agent = rv_agent_t::type_id::create("rv_agent", this);
            if (variant == LB_JS_MOVER) mover = make_mover();
            if (stalls()) begin
                bystander = new("bystander", this);
                bystander.idle = 1;
            end
        endfunction

        // The clocks each port's scripts wait before they answer item k.
        protected function int unsigned pa_delay(a2c_lane_e l, int unsigned k);
            case (variant)
                LB_JS_ONE_WAITS, LB_JS_RV_DST: return (k == 0) ? hold : 0;
                LB_JS_STOP, LB_JS_KNOB_OFF:    return (k >= stop_at) ? 1000000 : 0;
                LB_JS_PAUSE_OFF:               return (k == stop_at) ? hold : 0;
                LB_JS_LONE, LB_JS_LONE_DIES: begin
                    if (l == A2C_MODEL_LANE) return 1000000;
                    return (k >= stop_at) ? 1000000 : 0;
                end
            endcase
            return 0;
        endfunction

        protected function int unsigned rv_delay(int unsigned k);
            case (variant)
                LB_JS_STOP, LB_JS_KNOB_OFF, LB_JS_LONE, LB_JS_LONE_DIES: return (k >= stop_at) ? 1000000 : 0;
                LB_JS_PAUSE_OFF:                                         return (k == stop_at) ? hold : 0;
                LB_JS_RV_WAITS, LB_JS_PA_DST, LB_JS_MOVER:               return (k == 0) ? hold : 0;
            endcase
            return 0;
        endfunction

        // Whether rv's item 0 is the one that waits while something else
        // moves.
        protected function bit rv_waits();
            return variant inside {LB_JS_RV_WAITS, LB_JS_PA_DST, LB_JS_MOVER};
        endfunction

        protected function void note_transfer();
            last_at = $realtime;
        endfunction

        // pa lane l's side: acks a push it has waited pa_delay() clocks for,
        // for one clock.
        protected task serve_pa(a2c_lane_e l);
            int unsigned waited;
            bit          acking;
            pa_vif[l].ack <= 1'b0;
            clk_vif.wait_reset_release();
            forever begin
                clk_vif.sample_edge();
                if (acking) begin
                    pa_served[l]++;
                    if (l == A2C_DUT_LANE && waiting && variant == LB_JS_RV_WAITS) moved_while_waiting++;
                    note_transfer();
                    acking = 0;
                    waited = 0;
                end else if (pa_vif[l].push === 1'b1) begin
                    if (l == A2C_DUT_LANE && pa_served[l] == 0 && !rv_waits()) waiting = 1;
                    if (waited >= pa_delay(l, pa_served[l])) acking = 1;
                    else waited++;
                end
                if (l == A2C_DUT_LANE && pa_served[l] != 0 && !rv_waits()) waiting = 0;
                clk_vif.drive_edge();
                pa_vif[l].ack <= acking;
            end
        endtask

        // rv lane l's side: raises rdy once it has seen vld for rv_delay()
        // clocks, for one clock.
        protected task serve_rv(a2c_lane_e l);
            int unsigned waited;
            bit          ready;
            rv_vif[l].rdy <= 1'b0;
            clk_vif.wait_reset_release();
            forever begin
                clk_vif.sample_edge();
                if (ready && rv_vif[l].vld === 1'b1) begin
                    rv_served[l]++;
                    if (l == A2C_DUT_LANE && waiting && !rv_waits()) moved_while_waiting++;
                    if (l == A2C_DUT_LANE && rv_served[l] == 1 && rv_waits()) begin
                        wait_ended = $realtime;
                        if (mover != null) sent_at_wait_end = mover.sent;
                    end
                    note_transfer();
                    ready  = 0;
                    waited = 0;
                end else if (rv_vif[l].vld === 1'b1) begin
                    if (l == A2C_DUT_LANE && rv_served[l] == 0 && rv_waits() && !waiting) begin
                        waiting    = 1;
                        wait_began = $realtime;
                    end
                    if (waited >= rv_delay(rv_served[l])) ready = 1;
                    else waited++;
                end
                if (l == A2C_DUT_LANE && rv_served[l] != 0 && rv_waits()) waiting = 0;
                clk_vif.drive_edge();
                rv_vif[l].rdy <= ready;
            end
        endtask

        // pa lane l's requester in LB_JS_PA_DST: pushes n_pa items, each
        // held until its ack, with one idle clock between them.
        protected task push_pa(a2c_lane_e l);
            pa_vif[l].push <= 1'b0;
            pa_vif[l].data <= '0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            for (int unsigned k = 0; k < n_pa; k++) begin
                pa_vif[l].push <= 1'b1;
                pa_vif[l].data <= '{tag: 4'(k), value: 20'(k)};
                do clk_vif.sample_edge(); while (pa_vif[l].ack !== 1'b1);
                pa_served[l]++;
                if (l == A2C_DUT_LANE && waiting) moved_while_waiting++;
                note_transfer();
                clk_vif.drive_edge();
                pa_vif[l].push <= 1'b0;
                clk_vif.drive_edge();
            end
        endtask

        // rv lane l's sender in LB_JS_RV_DST: sends n_rv items, one every
        // two clocks.
        protected task push_rv(a2c_lane_e l);
            rv_vif[l].vld  <= 1'b0;
            rv_vif[l].data <= '0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            for (int unsigned k = 0; k < n_rv; k++) begin
                rv_vif[l].vld  <= 1'b1;
                rv_vif[l].data <= '{tag: 4'(k), value: 20'(k)};
                do clk_vif.sample_edge(); while (rv_vif[l].rdy !== 1'b1);
                rv_served[l]++;
                if (l == A2C_DUT_LANE && waiting) moved_while_waiting++;
                note_transfer();
                clk_vif.drive_edge();
                rv_vif[l].vld <= 1'b0;
                clk_vif.drive_edge();
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            lb_list_seq#(pa_item_t) pa_seq = lb_list_seq#(pa_item_t)::type_id::create("pa_seq");
            lb_list_seq#(rv_item_t) rv_seq = lb_list_seq#(rv_item_t)::type_id::create("rv_seq");
            realtime                t0;
            phase.raise_objection(this);
            for (int unsigned i = 0; i < n_pa; i++) begin
                pa_item_t it = pa_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "push_ack item randomize failed")
                pa_seq.items.push_back(it);
            end
            for (int unsigned i = 0; i < n_rv; i++) begin
                rv_item_t it = rv_item_t::type_id::create("it");
                if (!it.randomize()) `uvm_fatal("LB_RAND", "rdy_vld item randomize failed")
                rv_seq.items.push_back(it);
            end
            for (int l = 0; l < 2; l++) begin
                fork
                    automatic a2c_lane_e e = a2c_lane_e'(l);
                    if (variant == LB_JS_PA_DST) push_pa(e);
                    else serve_pa(e);
                    if (variant == LB_JS_RV_DST) push_rv(e);
                    else serve_rv(e);
                join_none
            end
            clk_vif.wait_reset_release();
            clk_vif.sample_edge();
            t0 = $realtime;
            clk_vif.sample_edge();
            period = $realtime - t0;
            fork
                if (variant == LB_JS_PA_DST) wait (pa_served[A2C_DUT_LANE] == n_pa && pa_served[A2C_MODEL_LANE] == n_pa);
                else pa_seq.start(pa_agent.sqr);
                if (variant == LB_JS_RV_DST) wait (rv_served[A2C_DUT_LANE] == n_rv && rv_served[A2C_MODEL_LANE] == n_rv);
                else rv_seq.start(rv_agent.sqr);
            join
            if (mover != null) begin
                mover.stop = 1;
                wait (mover.done);
            end
            repeat (3) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        // What each lane must have done, for check_phase.
        protected function int unsigned want_pa(a2c_lane_e l);
            if (variant inside {LB_JS_LONE, LB_JS_LONE_DIES} && l == A2C_MODEL_LANE) return 0;
            return stalls() ? stop_at : n_pa;
        endfunction

        protected function string want_died_by(string port, a2c_lane_e l);
            if (!stalls()) return "";
            if (variant == LB_JS_LONE && port == "pa" && l == A2C_MODEL_LANE) return "A2C_SKEW";
            if (variant == LB_JS_LONE_DIES && port == "pa") return "A2C_SKEW";
            return "A2C_JOINT_STALL";
        endfunction

        virtual function void check_phase(uvm_phase phase);
            a2c_lane_watchdog wd[$];
            realtime          stall_at = last_at + (joint + 1) * period;
            int unsigned      want_skews = (variant == LB_JS_LONE) ? 1 : (variant == LB_JS_LONE_DIES) ? 2 : 0;
            super.check_phase(phase);
            if (variant != LB_JS_PA_DST) wd.push_back(pa_agent.drv.wd);
            if (variant != LB_JS_RV_DST) wd.push_back(rv_agent.drv.wd);
            for (int l = 0; l < 2; l++) begin
                a2c_lane_e   e = a2c_lane_e'(l);
                int unsigned want_rv = stalls() ? stop_at : n_rv;
                if (pa_served[l] != want_pa(e) || rv_served[l] != want_rv) begin
                    `uvm_error("LB_MODE_B", $sformatf("the %s lanes made %0d pa and %0d rv transfers, expected %0d and %0d", a2c_lane_name(e),
                                                      pa_served[l], rv_served[l], want_pa(e), want_rv))
                end
                foreach (wd[p]) begin
                    string by = want_died_by(wd[p].port_name, e);
                    if (wd[p].dead[l] != (by != "") || wd[p].died_by[l] != by) begin
                        `uvm_error("LB_MODE_B", $sformatf("the %s lane of %s is %s by '%s', expected %s by '%s'", a2c_lane_name(e), wd[p].port_name,
                                                          wd[p].dead[l] ? "dead" : "live", wd[p].died_by[l], (by != "") ? "dead" : "live", by))
                    end
                    if (by == "A2C_JOINT_STALL" && wd[p].died_at[l] != stall_at) begin
                        `uvm_error("LB_MODE_B", $sformatf("the %s lane of %s died at %0t, expected %0d clocks after the last handshake at %0t",
                                                          a2c_lane_name(e), wd[p].port_name, wd[p].died_at[l], joint + 1, last_at))
                    end
                end
            end
            if (stalls() && (bystander.src.drv.wd.dead[A2C_DUT_LANE] || bystander.src.drv.wd.dead[A2C_MODEL_LANE])) begin
                `uvm_error("LB_MODE_B", "the joint stall declared a lane of the Mode A notify_ack master dead")
            end
            if (skews.demoted != want_skews) begin
                `uvm_error("LB_MODE_B", $sformatf("%0d A2C_SKEW, expected %0d: %p", skews.demoted, want_skews, skews.messages))
            end
            if (variant inside {LB_JS_ONE_WAITS, LB_JS_RV_WAITS, LB_JS_RV_DST, LB_JS_PA_DST} && moved_while_waiting < hold / 4) begin
                `uvm_error("LB_MODE_B", $sformatf("the other port made %0d transfers while one waited, so the wait was not tested beside a moving port",
                                                  moved_while_waiting))
            end
            if (variant == LB_JS_MOVER && (wait_ended == 0 || mover.started_at > wait_began || mover.sent <= sent_at_wait_end)) begin
                `uvm_error("LB_MODE_B", $sformatf("the %s mover ran from %0t through %0d rounds, %0d of them by %0t, so it did not move throughout rv's wait from %0t",
                                                  mover.port, mover.started_at, mover.sent, sent_at_wait_end, wait_ended, wait_began))
            end
        endfunction
    endclass : lb_joint_env

    class joint_stall_one_port_waits_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_one_port_waits_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_ONE_WAITS;
        endfunction
    endclass : joint_stall_one_port_waits_test

    class joint_stall_env_stop_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_env_stop_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_STOP;
        endfunction
    endclass : joint_stall_env_stop_test

    class joint_stall_pause_off_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_pause_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_PAUSE_OFF;
        endfunction
    endclass : joint_stall_pause_off_test

    class joint_stall_master_moves_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_master_moves_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_RV_WAITS;
            n_pa    = 120;
            n_rv    = 4;
        endfunction
    endclass : joint_stall_master_moves_test

    class joint_stall_rv_dst_moves_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_rv_dst_moves_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_RV_DST;
        endfunction
    endclass : joint_stall_rv_dst_moves_test

    class joint_stall_pa_dst_moves_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_pa_dst_moves_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_PA_DST;
            n_pa    = 120;
            n_rv    = 4;
        endfunction
    endclass : joint_stall_pa_dst_moves_test

    class joint_stall_knob_off_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_knob_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_KNOB_OFF;
        endfunction
    endclass : joint_stall_knob_off_test

    class joint_stall_lone_lane_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_lone_lane_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_LONE;
        endfunction
    endclass : joint_stall_lone_lane_test

    class joint_stall_lone_lane_dies_test extends lb_joint_env;
        `uvm_component_utils(joint_stall_lone_lane_dies_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_LONE_DIES;
            n_pa    = stop_at + 1;
        endfunction
    endclass : joint_stall_lone_lane_dies_test

    // LB_JS_MOVER with the mover on one interface each, so each monitor's
    // count of transfers is what keeps rv's wait from stalling.
    virtual class lb_joint_mover_test extends lb_joint_env;
        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = LB_JS_MOVER;
            n_pa    = 0;
            n_rv    = 4;
        endfunction
    endclass : lb_joint_mover_test

    class joint_stall_na_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_na_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_na_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_na_mover_test

    class joint_stall_ra_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_ra_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_ra_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_ra_mover_test

    class joint_stall_po_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_po_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_po_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_po_mover_test

    class joint_stall_apb_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_apb_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_apb_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_apb_mover_test

    class joint_stall_mem_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_mem_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_mem_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_mem_mover_test

    class joint_stall_er_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_er_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_er_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_er_mover_test

    class joint_stall_axis_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_axis_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_axis_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_axis_mover_test

    class joint_stall_axr_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_axr_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_axr_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_axr_mover_test

    class joint_stall_axw_mover_test extends lb_joint_mover_test;
        `uvm_component_utils(joint_stall_axw_mover_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function lb_mover make_mover();
            lb_axw_mover m = new("mover", this);
            return m;
        endfunction
    endclass : joint_stall_axw_mover_test
