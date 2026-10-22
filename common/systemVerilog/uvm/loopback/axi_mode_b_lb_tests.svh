// Mode B loopback tests of the axi_read and axi_write agents, included in
// a2c_uvm_loopback_pkg after both agents' tests, whose typedefs, sequences
// and reference model they use.

    // What a Mode B AXI test varies. AXB_DUT_EXTRA and AXB_MODEL_EXTRA give
    // one lane's master one burst more, at the end. AXB_BUSY keeps both
    // masters sending with no gap after the test drops its objection, the
    // model lane's a clock behind, so the drain must cut. As A2C_DST:
    //   - AXB_CROSS: the model lane's master sends some adjacent bursts of
    //     different IDs in the other order;
    //   - AXB_SERIAL: the model lane's master keeps one burst outstanding,
    //     fewer than the DUT lane's, a model defect the slave must report
    //     at the first pick the DUT lane reorders;
    //   - AXB_DUT_MID: the DUT lane's master sends one burst more, mid-run,
    //     with an ID no other burst has;
    //   - AXB_SKIP_CUT: as AXB_BUSY, and the model lane's master skips one
    //     burst mid-run, with an ID no other burst has.
    //   - AXB_DEAD_DRAIN: as AXB_DUT_EXTRA, with the model lane declared
    //     dead, as a master on another port would, dead_after clocks after
    //     the drop or just before it, or on the first clock with
    //     dead_early. The drain and the reports must not change, apart from
    //     the clause that names the death in the reports of what came after
    //     it.
    // As A2C_SRC the master's lane skew bound is under test. In each variant
    // but the last two one lane falls behind and dies:
    //   - AXB_MUTE: the model lane's slave takes each burst and never
    //     answers it;
    //   - AXB_DEAF: the model lane's slave takes no AR, or no AW;
    //   - AXB_DEAF_W: the model lane's slave takes AWs and no W beat;
    //   - AXB_DUT_LATE and AXB_MODEL_LATE: that lane's slave answers burst
    //     late_at late_by clocks late, and AXB_MODEL_LATE the burst after it
    //     too. The two bursts after late_at share its ID;
    //   - AXB_STALL: the model lane's slave takes no address and no W beat
    //     from just before burst stall_at until lane_skew + 40 clocks after
    //     the DUT lane took its address. The two bursts after it share its
    //     ID;
    //   - AXB_HALF (axi_write): the model lane's slave stops taking W beats
    //     once it has taken some of burst half_at's, and takes them again
    //     lane_skew + 40 clocks later;
    //   - AXB_BOTH_DEAD: the DUT lane's slave answers no burst from both_at
    //     on. On axi_write the model lane takes no AW and dies first, and
    //     the DUT lane then dies alone. On axi_read the DUT lane dies first,
    //     and the master's rready goes low for good once the model lane has
    //     returned part of a burst, so the model lane dies holding it;
    //   - AXB_ORDER_A and AXB_ORDER_W: each lane's slave is a script. The
    //     first three bursts share an ID, and the model lane's slave takes
    //     their addresses and W beats, then no address (AXB_ORDER_A) or no
    //     W beat (AXB_ORDER_W). The model lane dies lane_skew clocks after
    //     the DUT lane takes burst 3's address or W beat. The DUT lane's
    //     slave answers the three bursts 10 clocks before the death, on its
    //     clock and one clock after it, so their responses straddle the
    //     death whichever process sees it first. The model lane's slave
    //     answers as order_model says: nothing, burst 0 on the death's
    //     clock, or burst 0 with the DUT lane's and burst 1 on the death's
    //     clock, so that both lanes complete a burst on that clock;
    //   - AXB_LONE_STALL and AXB_LONE_OFF: as AXB_MUTE, and the DUT lane's
    //     slave then answers bursts stall_at to stall_at + 3 lane_skew + 150
    //     clocks late. The DUT lane, alone, must survive that stall under
    //     the default lone lane bound, and with the rule off;
    //   - AXB_LAG: the model lane's slave answers every burst lag clocks
    //     after its address, a skew under the bound;
    //   - AXB_SKEW_OFF: as AXB_LAG with the bound off.
    typedef enum {AXB_MATCH, AXB_MISMATCH, AXB_DUT_EXTRA, AXB_MODEL_EXTRA, AXB_BUSY, AXB_CROSS, AXB_SERIAL, AXB_DUT_MID,
                  AXB_SKIP_CUT, AXB_DEAD_DRAIN, AXB_MUTE, AXB_DEAF, AXB_DEAF_W, AXB_DUT_LATE, AXB_MODEL_LATE, AXB_STALL,
                  AXB_HALF, AXB_BOTH_DEAD, AXB_ORDER_A, AXB_ORDER_W, AXB_LONE_STALL, AXB_LONE_OFF, AXB_LAG,
                  AXB_SKEW_OFF} lb_axb_variant_e;

    // Keeps every message with one ID, whatever its severity.
    class lb_id_texts extends uvm_report_catcher;
        string id;
        string messages[$];

        `uvm_object_utils(lb_id_texts)

        function new(string name = "lb_id_texts");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == id) messages.push_back(get_message());
            return THROW;
        endfunction

        function int unsigned count(string sub);
            int unsigned n = 0;
            foreach (messages[i]) n += a2c_contains(messages[i], sub);
            return n;
        endfunction
    endclass : lb_id_texts

    // Checks one master channel of a lane the master has declared dead. A
    // valid it held at the death stays up with its payload until the
    // transfer at the rising edge after a falling edge that sees ready high,
    // and stays low after that; one it did not hold stays low; the payload
    // never changes. sample() takes the pins at each falling edge.
    class lb_frozen;
        string       what;
        int unsigned errors;

        protected bit            armed;
        protected bit            held;
        protected bit            gone;
        protected logic [1023:0] payload;
        protected bit            last_valid;
        protected bit            last_ready;
        protected logic [1023:0] last_payload;

        function new(string what);
            this.what = what;
        endfunction

        static function lb_frozen of(string what);
            lb_frozen f = new(what);
            return f;
        endfunction

        protected function void fail(string why);
            errors++;
            if (errors <= 3) `uvm_error("LB_MODE_B", $sformatf("%s of the dead lane: %s at %0t", what, why, $realtime))
        endfunction

        // died is the lane's death time; a death at this falling edge took
        // the pins it holds now, and an earlier one those of the last edge.
        function void sample(bit dead, realtime died, logic valid, logic ready, logic [1023:0] pins);
            if (!armed && dead) begin
                armed = 1;
                held  = (died == $realtime) ? valid === 1'b1 : last_valid;
                gone  = held && ((died == $realtime) ? ready === 1'b1 : last_ready);
                payload = (died == $realtime) ? pins : last_payload;
                if (died == $realtime) return;
            end
            last_valid   = valid === 1'b1;
            last_ready   = ready === 1'b1;
            last_payload = pins;
            if (!armed) return;
            if (pins !== payload) begin
                fail("its payload changed");
            end else if (!held || gone) begin
                if (valid !== 1'b0) fail(gone ? "its valid rose again after its transfer" : "its valid rose");
            end else if (valid !== 1'b1) begin
                fail("its valid dropped before its transfer");
            end else if (ready === 1'b1) begin
                gone = 1;
            end
        endfunction
    endclass : lb_frozen

    // Mode B on one AXI port. agent, the agent under test, has the port as
    // its DUT lane and <port>_model as its model lane.
    //
    // As A2C_DST the agent's slave reorders, and each lane has its own
    // master peer sending the same bursts, four outstanding, with its own
    // gaps: the model lane's run shorter than the DUT lane's for ten bursts
    // and longer for the next ten, so each lane leads in turn. Both lanes
    // must report the same bursts in the same order, which they do only if
    // the model lane served the DUT lane's picks, and the DUT lane must serve
    // some burst out of AR order.
    //
    // As A2C_SRC the agent sends the bursts to both lanes, four outstanding,
    // and each lane has its own slave. The lanes must complete some bursts in
    // different orders across IDs, which model_cmp pairs per ID.
    //
    // A family's test defines the items, the configs, the sequences and its
    // own checks.
    virtual class lb_axi_mode_b #(type AGENT_T = uvm_agent, type ITEM_T = uvm_sequence_item, type CFG_T = uvm_object,
                                  type VIF_T = int) extends lb_mode_b_base;
        string               port;
        a2c_role_e           role = A2C_DST;
        lb_axb_variant_e     variant = AXB_MATCH;
        // The clock the port runs on.
        string               clk_name = "clk";
        AGENT_T              agent;
        AGENT_T              peer;
        AGENT_T              model_peer;
        CFG_T                agent_cfg;
        CFG_T                peer_cfg;
        CFG_T                model_peer_cfg;
        VIF_T                vif;
        VIF_T                model_vif;
        // The bursts each lane's master sends, in order. As A2C_SRC the
        // agent sends items to both lanes.
        ITEM_T               items[$];
        ITEM_T               model_items[$];
        lb_arrivals#(ITEM_T) arrivals;
        lb_arrivals#(ITEM_T) model_arrivals;
        int unsigned         mismatch_at;
        // A2C_PROTO reports the test expects, from a monitor left with a
        // burst open at the end.
        int unsigned         want_proto;
        int unsigned         drain_quiet = 30;
        int unsigned         drain_deadline = 600;
        // AXB_DEAD_DRAIN: the clocks after the drop at which the model lane
        // is declared dead, so while the drain runs, or 0 for just before
        // the drop, so before it starts. AXB_BUSY with dead_in_catchup: the
        // model lane is declared dead 5 clocks after the drain's deadline,
        // while the lanes catch up with the cut, and caught_up records
        // whether they already had.
        int unsigned         dead_after;
        bit                  dead_in_catchup;
        // A port elsewhere declares the model lane dead on the first clock
        // after the reset, before any event the test reports, so every
        // report the test demotes must name the death. Without it none may
        // name a death.
        bit                  dead_early;
        bit                  caught_up;
        // The A2C_DRAIN and A2C_CUT reports.
        lb_id_texts          drains;
        lb_id_texts          cuts;
        // A passive Mode B agent on the port, which must build no driver
        // and pair what agent pairs.
        bit                  watch_passive;
        AGENT_T              watcher;
        // In a variant in which a lane dies holding bursts, the end-of-run
        // A2C_PROTO error of the test's own monitor on that lane. The
        // master tells only the agent's monitors of the death.
        a2c_error_demoter    peer_open;
        // AXB_MUTE (axi_read): the model lane's slave sends one R beat
        // whose rid matches no burst before the death, and strays demotes
        // the A2C_PROTO errors of the two monitors on that lane.
        bit                  stray;
        a2c_error_demoter    strays;
        // AXB_BUSY: the clocks for which the model lane's master takes no
        // response, from 20 before the drain's deadline. The model lane then
        // trails at the cut and stays behind while the DUT lane completes
        // bursts past it.
        int unsigned         model_stall;
        int unsigned         clocks;
        // The port's clock period, measured over the first two clocks.
        realtime             period;
        protected realtime   first_clock_at;
        int unsigned         dropped_at;
        int unsigned         ready_calls;
        // A2C_DST: the picks the model lane waited for.
        int unsigned         model_led;
        bit                  done[2];
        // Every config's id_unbound: the masters send every burst with ID 0.
        bit                  id_unbound;
        // AXB_CROSS: the pairs of bursts the model lane's master swapped.
        int unsigned         cross_swaps;
        // AXB_DUT_MID and AXB_SKIP_CUT: the place in items of the burst only
        // the DUT lane's master sends.
        int unsigned         lone_at;
        // A2C_SRC: the master's lane skew bound, and AXB_MUTE the clocks of
        // the DUT lane's first completed burst and of the first A2C_SKEW
        // error.
        int unsigned         lane_skew = 50;
        int unsigned         first_dut_at;
        int unsigned         first_skew_at;
        int unsigned         late_at;
        int unsigned         late_by = 260;
        int unsigned         stall_at;
        int unsigned         half_at;
        int unsigned         both_at;
        // AXB_BOTH_DEAD: the DUT lane dies first.
        bit                  dut_first;
        // AXB_ORDER_A and AXB_ORDER_W: 0, the model lane's slave answers
        // nothing; 1, it answers burst 0 on the clock of the death, on which
        // the DUT lane's slave answers burst 1; 2, it answers burst 0 with
        // the DUT lane's slave and burst 1 on the clock of the death, so both
        // lanes complete burst 1 then. Either way a lane completes a burst
        // the other has completed, or completes then, in the time step the
        // master sees the death, and the sequence must get it back once.
        int unsigned         order_model;
        int unsigned         lag = 100;
        // AXB_LONE_STALL and AXB_LONE_OFF: the most clocks the DUT lane went
        // without completing a burst once the model lane had died.
        int unsigned         lone_gap;
        protected int unsigned last_lone_done;
        // The fewest pairs model_cmp must have compared before the death,
        // and the pairs it had compared at the first falling edge after it.
        int unsigned         want_pairs;
        int                  pairs_at_death = -1;
        // Per lane: the master's channels, checked once the lane is dead,
        // and its ready errors.
        lb_frozen            frozen[2][$];
        int unsigned         ready_errors;
        // Per lane: the clock each burst completed on, by its ID and its
        // place among its ID's bursts.
        protected int unsigned done_at[2][string];
        protected int unsigned done_of[2][int unsigned];

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_items = 60;
        endfunction

        pure virtual function ITEM_T new_item(int unsigned i);

        // Sets the knobs of the three configs.
        virtual function void configure();
        endfunction

        // AXB_MISMATCH: makes the lanes differ in a way model_cmp reports,
        // and sets want_errors and want_text.
        pure virtual function void mismatch();

        // Adds to want_text what the slave's A2C_REPLAY error says of the
        // burst only the given lane issued, burst n_items of its master.
        pure virtual function void one_lane_text(a2c_lane_e lane);

        // What the slave's A2C_REPLAY error says of a held pick of burst it,
        // the n-th of its ID, whose request the model lane has not made.
        pure virtual function string held_text(ITEM_T it, int unsigned n);

        // Stops or restarts the model lane master's acceptance of responses.
        virtual function void stall_model(bit stall);
        endfunction

        // Runs list on src's sequencer and sets done[lane] when it returns.
        pure virtual task send(AGENT_T src, ITEM_T list[$], a2c_lane_e lane);

        // Watches the pins of both lanes until the end of the run.
        virtual task watch();
        endtask

        virtual function void check_family();
        endfunction

        pure virtual function a2c_replay_log_base replay();

        // A2C_SRC hooks of the lane skew variants. lane_delay() makes the
        // lane's slave answer the bursts whose delay it draws from now on n
        // clocks late, or as configure() set it when n is 0. lane_accept()
        // starts or stops the model lane's slave taking addresses and W
        // beats. addr_count() is the addresses the lane has taken, and
        // drawn_count() the bursts whose delay its slave has drawn.
        // done_word() is how an A2C_SKEW error of the master names a burst's
        // completion. left() and queued() are the master's bursts
        // outstanding and queued on a lane, returned() the bursts the
        // sequence got back and empties() those with no beats. is_dead(),
        // died() and kill_again() reach the master's dead lanes.
        virtual function void lane_delay(a2c_lane_e l, int unsigned n);
        endfunction

        virtual function void lane_accept(bit addr, bit data);
        endfunction

        virtual function int unsigned addr_count(a2c_lane_e l);
            return 0;
        endfunction

        virtual function int unsigned drawn_count(a2c_lane_e l);
            return 0;
        endfunction

        pure virtual function string done_word();

        // AXB_DUT_LATE and AXB_MODEL_LATE: makes the response to
        // items[late_at + 1] differ from those of the bursts on either side,
        // so a late answer credited to the wrong one, or a response taken
        // from the lane the master gave up on, fails the sequence's check.
        virtual function void tell_apart();
        endfunction

        pure virtual function int unsigned left(a2c_lane_e l);

        pure virtual function int unsigned queued(a2c_lane_e l);

        pure virtual function int unsigned returned();

        pure virtual function int unsigned empties();

        pure virtual function bit is_dead(a2c_lane_e l);

        pure virtual function realtime died(a2c_lane_e l);

        pure virtual function void kill_again(a2c_lane_e l);

        // AXB_HALF: the W beats the lane has taken.
        virtual function int unsigned data_count(a2c_lane_e l);
            return 0;
        endfunction

        // The n-th response the sequence got back.
        pure virtual function ITEM_T response(int unsigned n);

        // AXB_ORDER_A and AXB_ORDER_W: when the lane's slave completed burst
        // n, or 0.
        virtual function realtime answered_at(int unsigned n, a2c_lane_e l = A2C_DUT_LANE);
            return 0;
        endfunction

        // model_cmp still compares the pairs of the death's own time step, so
        // the count is read at the first falling edge after it.
        protected function void note_death();
            if (pairs_at_death >= 0) return;
            for (int l = 0; l < 2; l++) begin
                if (is_dead(a2c_lane_e'(l)) && died(a2c_lane_e'(l)) < $realtime) pairs_at_death = agent.model_cmp.get_pairs();
            end
        endfunction

        // A dead lane's ready is low at every falling edge after its death.
        protected function void check_ready(a2c_lane_e l, logic ready, string name);
            if (!is_dead(l) || died(l) == $realtime || ready === 1'b0) return;
            ready_errors++;
            if (ready_errors <= 3) `uvm_error("LB_MODE_B", $sformatf("%s of the dead %s lane is %b at %0t", name, a2c_lane_name(l), ready, $realtime))
        endfunction

        // The A2C_SRC variants that test the lane skew bound, and those in
        // which a lane dies, after which the lanes no longer move in step.
        protected function bit skews();
            return dies() || variant inside {AXB_LAG, AXB_SKEW_OFF};
        endfunction

        protected function bit dies();
            return variant inside {AXB_MUTE, AXB_DEAF, AXB_DEAF_W, AXB_DUT_LATE, AXB_MODEL_LATE, AXB_STALL, AXB_HALF,
                                   AXB_BOTH_DEAD, AXB_ORDER_A, AXB_ORDER_W, AXB_LONE_STALL, AXB_LONE_OFF};
        endfunction

        // The lane that dies first.
        protected function a2c_lane_e dead_lane();
            return (variant == AXB_DUT_LATE) ? A2C_DUT_LANE : A2C_MODEL_LANE;
        endfunction

        // The clause of a report of an event after the test declared the
        // model lane dead, and the end of every such clause.
        protected function string death_text();
            return "; the model lane of uvm_test_top was declared dead at ";
        endfunction

        protected function string related_text();
            return ", which may be related";
        endfunction

        // How the master's reports name it.
        protected function string item_text(ITEM_T it);
            return $sformatf("id=%0h addr=%0h len=%0d ", it.id, it.addr, it.len);
        endfunction

        // Gives items[at] and the two after it items[at]'s ID and at most
        // four beats each.
        protected function void same_id_run(int unsigned at);
            int unsigned keep = int'(items[at].id);
            for (int unsigned i = at; i < at + 3; i++) begin
                int unsigned gap = items[i].gap;
                if (!items[i].randomize() with { len <= 3; id == keep; }) `uvm_fatal("LB_RAND", "same_id_run randomize failed")
                items[i].gap = gap;
            end
        endfunction

        // Called by a family's watch() as lane l completes a burst of ID id.
        protected function void note_done(int l, int unsigned id);
            if (!done_of[l].exists(id)) done_of[l][id] = 0;
            done_at[l][$sformatf("%0h/%0d", id, done_of[l][id]++)] = clocks;
            if (role != A2C_SRC || l != A2C_DUT_LANE || !is_dead(A2C_MODEL_LANE)) return;
            if (last_lone_done != 0 && clocks - last_lone_done > lone_gap) lone_gap = clocks - last_lone_done;
            last_lone_done = clocks;
        endfunction

        // AXB_ORDER_A and AXB_ORDER_W: six one-beat bursts at their own
        // addresses, the first three of one ID and each of the others of
        // its own.
        protected function void order_items();
            while (items.size() > 6) void'(items.pop_back());
            foreach (items[i]) begin
                int unsigned want_id = (i < 3) ? 1 : (i - 1) % 4;
                if (!items[i].randomize() with { len == 0; burst == AXI_INCR; id == want_id; addr == 'h40 * (i + 1); }) begin
                    `uvm_fatal("LB_RAND", "order_items randomize failed")
                end
                items[i].gap = 0;
            end
        endfunction

        // The sequence got the bursts of each ID back in the order it sent
        // them.
        protected function void check_order();
            int unsigned next[int unsigned];
            for (int unsigned n = 0; n < returned(); n++) begin
                ITEM_T       r  = response(n);
                int unsigned id = int'(r.id);
                int          of_id[$] = items.find_index(it) with (int'(it.id) == id);
                if (!next.exists(id)) next[id] = 0;
                if (next[id] >= of_id.size() || items[of_id[next[id]]].addr !== r.addr || items[of_id[next[id]]].len !== r.len) begin
                    `uvm_error("LB_MODE_B", $sformatf("response %0d, %s, is not the next burst of its ID the sequence sent", n, item_text(r)))
                end
                next[id]++;
            end
        endfunction

        // The most clocks between the lanes' completions of one burst.
        protected function int unsigned max_skew();
            int unsigned most = 0;
            foreach (done_at[A2C_DUT_LANE][k]) begin
                int unsigned d = done_at[A2C_DUT_LANE][k];
                int unsigned m;
                if (!done_at[A2C_MODEL_LANE].exists(k)) continue;
                m = done_at[A2C_MODEL_LANE][k];
                if ((d > m ? d - m : m - d) > most) most = d > m ? d - m : m - d;
            end
            return most;
        endfunction

        // Makes the lanes' slaves late or deaf at the clocks the variant
        // needs. Each change lands at a drive point, after the slaves have
        // taken the addresses and beats of the edge before it, so the burst
        // the change is for draws it.
        protected task shape_lanes();
            bit          stalled;
            int unsigned stall_left;
            forever begin
                clk_vif.drive_edge();
                case (variant)
                    AXB_DUT_LATE: lane_delay(A2C_DUT_LANE, (drawn_count(A2C_DUT_LANE) == late_at) ? late_by : 0);
                    AXB_MODEL_LATE: begin
                        lane_delay(A2C_MODEL_LANE, (drawn_count(A2C_MODEL_LANE) inside {late_at, late_at + 1}) ? late_by : 0);
                    end
                    AXB_STALL: begin
                        if (!stalled && drawn_count(A2C_DUT_LANE) >= stall_at && drawn_count(A2C_MODEL_LANE) >= stall_at) begin
                            lane_accept(0, 0);
                            stalled    = 1;
                            stall_left = lane_skew + 40;
                        end
                        if (stalled && stall_left != 0 && addr_count(A2C_DUT_LANE) > stall_at && --stall_left == 0) lane_accept(1, 1);
                    end
                    AXB_HALF: begin
                        if (!stalled && data_count(A2C_MODEL_LANE) > beats_before(half_at)) begin
                            lane_accept(1, 0);
                            stalled    = 1;
                            stall_left = lane_skew + 40;
                        end
                        if (stalled && stall_left != 0 && --stall_left == 0) lane_accept(1, 1);
                    end
                    AXB_BOTH_DEAD: if (drawn_count(A2C_DUT_LANE) == both_at) lane_delay(A2C_DUT_LANE, 1000000);
                    AXB_LONE_STALL, AXB_LONE_OFF: begin
                        lane_delay(A2C_DUT_LANE, (drawn_count(A2C_DUT_LANE) inside {[stall_at:stall_at + 3]}) ? lane_skew + 150 : 0);
                    end
                    default: return;
                endcase
            end
        endtask

        // The W beats of the bursts before items[n].
        protected function int unsigned beats_before(int unsigned n);
            int unsigned b = 0;
            for (int unsigned i = 0; i < n; i++) b += int'(items[i].len) + 1;
            return b;
        endfunction

        protected function CFG_T lane_cfg(string name, VIF_T lane_vif, a2c_role_e lane_role, string lane_port);
            CFG_T cfg = CFG_T::type_id::create(name);
            cfg.vif       = lane_vif;
            cfg.clk_vif   = clk_vif;
            cfg.role      = lane_role;
            cfg.port_name = lane_port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            a2c_role_e   peer_role = (role == A2C_SRC) ? A2C_DST : A2C_SRC;
            bit          busy = variant inside {AXB_BUSY, AXB_SKIP_CUT};
            int unsigned tail = busy ? 10 * n_items : 0;
            if (variant inside {AXB_DUT_EXTRA, AXB_MODEL_EXTRA, AXB_SERIAL, AXB_DUT_MID, AXB_SKIP_CUT, AXB_DEAD_DRAIN}) demote_id = "A2C_REPLAY";
            if (skews()) demote_id = "A2C_SKEW";
            mismatch_at = $urandom_range(n_items - 1, 0);
            super.build_phase(phase);
            if (clk_name != "clk" && !uvm_config_db#(virtual a2c_clk_if)::get(this, "", clk_name, clk_vif)) begin
                `uvm_fatal("LB_CFG", {"no virtual a2c_clk_if ", clk_name})
            end
            if (!uvm_config_db#(VIF_T)::get(this, "", port, vif)) `uvm_fatal("LB_CFG", {"no interface ", port})
            if (!uvm_config_db#(VIF_T)::get(this, "", {port, "_model"}, model_vif)) `uvm_fatal("LB_CFG", {"no interface ", port, "_model"})
            agent_cfg = lane_cfg("agent_cfg", vif, role, port);
            agent_cfg.model_vif = model_vif;
            peer_cfg       = lane_cfg("peer_cfg", vif, peer_role, port);
            model_peer_cfg = lane_cfg("model_peer_cfg", model_vif, peer_role, {port, "_model"});
            for (int unsigned i = 0; i < n_items + tail; i++) begin
                ITEM_T it = new_item(i);
                ITEM_T m;
                $cast(m, it.clone());
                if (busy) begin
                    it.gap = 0;
                    m.gap  = (i == 0);
                end else begin
                    it.gap = $urandom_range(3, 0);
                    m.gap  = ((i / 10) % 2 == 0) ? $urandom_range(1, 0) : $urandom_range(3, 2);
                end
                items.push_back(it);
                model_items.push_back(m);
            end
            configure();
            if (id_unbound) begin
                agent_cfg.id_unbound      = 1;
                peer_cfg.id_unbound       = 1;
                model_peer_cfg.id_unbound = 1;
            end
            // The lone burst's ID is the all-ones one, which no other burst
            // keeps, so no later burst of the model lane's can stand in for it.
            if (variant inside {AXB_DUT_MID, AXB_SKIP_CUT}) begin
                lone_at = n_items / 2;
                foreach (items[i]) begin
                    if (items[i].id === '1) items[i].id = '0;
                    if (model_items[i].id === '1) model_items[i].id = '0;
                end
            end
            case (variant)
                // The extra burst goes out once the lanes are idle, so the
                // DUT lane picks it last. Picked earlier, it would hold back
                // every pick the model lane serves after it.
                AXB_DUT_EXTRA, AXB_DEAD_DRAIN: begin
                    items.push_back(new_item(n_items));
                    items[n_items].gap = 400;
                    want_errors = 1;
                    one_lane_text(A2C_DUT_LANE);
                end
                // The model lane's master and the agent's model_mon are left
                // with the burst open.
                AXB_MODEL_EXTRA: begin
                    model_items.push_back(new_item(n_items));
                    want_errors = 2;
                    want_proto  = 2;
                    want_text.push_back($sformatf("uvm_test_top.agent.drv.replay: the model lane waited for transaction %0d, which the DUT lane never recorded",
                                                  n_items + 1));
                    one_lane_text(A2C_MODEL_LANE);
                end
                AXB_MISMATCH: mismatch();
                // A model with more bursts outstanding than the DUT's always
                // has the AR of the DUT lane's pick.
                AXB_CROSS: begin
                    for (int unsigned i = 0; i + 1 < n_items; i += 3) begin
                        ITEM_T t = model_items[i];
                        if (t.id === model_items[i + 1].id) continue;
                        model_items[i]     = model_items[i + 1];
                        model_items[i + 1] = t;
                        cross_swaps++;
                    end
                    model_peer_cfg.max_outstanding = 8;
                end
                // The held pick, and the picks the DUT lane recorded after
                // it.
                AXB_SERIAL: begin
                    model_peer_cfg.max_outstanding = 1;
                    want_errors = 2;
                    want_text.push_back("uvm_test_top.agent.drv: the model lane holds the DUT lane's pick ");
                    want_text.push_back(" of its own behind it: ");
                    want_text.push_back("so its queuing does not match the RTL's");
                end
                AXB_DUT_MID: begin
                    ITEM_T lone = new_item(n_items);
                    lone.id  = '1;
                    lone.gap = $urandom_range(3, 0);
                    items.insert(lone_at, lone);
                    want_errors = 2;
                    want_text.push_back(held_text(lone, 1));
                    // The model lane's four outstanding requests wait behind
                    // the pick, one more than the report lists.
                    want_text.push_back(" of its own behind it, the first 3: ");
                end
                // The held pick, and the cut it keeps the lanes from
                // completing.
                AXB_SKIP_CUT: begin
                    items[lone_at].id = '1;
                    model_items.delete(lone_at);
                    drain_deadline = 300;
                    drain_quiet    = 100;
                    want_errors    = 2;
                    want_text.push_back(held_text(items[lone_at], 1));
                    want_text.push_back("uvm_test_top.agent.drv.replay: the drain cut the run after transaction ");
                    want_text.push_back("because the model lane holds a pick whose request it has not made");
                end
                // The model lane dies on the first burst and completes none.
                AXB_MUTE, AXB_DEAF, AXB_DEAF_W, AXB_LONE_STALL, AXB_LONE_OFF: begin
                    if (stray) foreach (items[i]) if (items[i].id === '1) items[i].id = '0;
                    if (variant inside {AXB_LONE_STALL, AXB_LONE_OFF}) stall_at = n_items / 2;
                    want_errors = 1;
                    want_text.push_back({port, ": the model lane has not "});
                    want_text.push_back($sformatf({" %0d clocks after the DUT lane did (lane_skew_cycles, +a2c_lane_skew_cycles), so the master",
                                                   " declares the model lane dead"}, lane_skew));
                    want_text.push_back({dead_early ? related_text() : "", ". The DUT lane serves every burst from now on."});
                    if (variant inside {AXB_MUTE, AXB_LONE_STALL, AXB_LONE_OFF}) want_text.push_back({"has not returned ", done_word()});
                    if (variant == AXB_DEAF) want_text.push_back("has not taken the A");
                    if (variant == AXB_DEAF_W) want_text.push_back("has not taken W beat 0 of ");
                end
                // The late lane dies on the late burst, so the bursts before it
                // are paired; a burst of another ID after it may pair before
                // the death too. A late answer credited to a later burst
                // would show.
                AXB_DUT_LATE, AXB_MODEL_LATE: begin
                    a2c_lane_e lead = (variant == AXB_DUT_LATE) ? A2C_MODEL_LANE : A2C_DUT_LANE;
                    late_at    = n_items / 2;
                    lane_skew  = 200;
                    want_pairs = late_at;
                    same_id_run(late_at);
                    tell_apart();
                    if (variant == AXB_DUT_LATE) begin
                        items[late_at + 1].gap = 220;
                    end else begin
                        items[late_at + 1].gap = 80;
                        items[late_at + 2].gap = 220;
                    end
                    want_errors = 1;
                    want_text.push_back({"the ", a2c_lane_name(a2c_lane_e'(1 - lead)), " lane has not returned ", done_word(),
                                         item_text(items[late_at])});
                    want_text.push_back({"declares the ", a2c_lane_name(a2c_lane_e'(1 - lead)), " lane dead. The ",
                                         a2c_lane_name(lead), " lane serves every burst from now on."});
                end
                // The stall starts once each lane has taken every address and
                // W beat of the bursts before it, which the gap leaves time
                // for, and the model lane dies on burst stall_at's address
                // or first W beat.
                AXB_STALL: begin
                    stall_at   = n_items / 2;
                    lane_skew  = 200;
                    want_pairs = stall_at;
                    same_id_run(stall_at);
                    items[stall_at].gap = 100;
                    want_errors = 1;
                    want_text.push_back("the model lane has not taken ");
                    want_text.push_back({"of ", item_text(items[stall_at])});
                    want_text.push_back("declares the model lane dead. The DUT lane serves every burst from now on.");
                end
                // An eight-beat burst after a gap, so the stall lands with the
                // model lane's slave holding its AW and part of its W.
                AXB_HALF: begin
                    half_at    = n_items / 2;
                    lane_skew  = 200;
                    want_pairs = half_at;
                    if (!items[half_at].randomize() with { len == 7; burst == AXI_INCR; }) `uvm_fatal("LB_RAND", "AXB_HALF randomize failed")
                    items[half_at].gap = 100;
                    want_errors = 1;
                    want_text.push_back({"the model lane has not taken W beat "});
                    want_text.push_back({"of ", item_text(items[half_at])});
                    want_text.push_back("declares the model lane dead. The DUT lane serves every burst from now on.");
                end
                // Without dut_first the model lane dies on the first address,
                // and the DUT lane once its outstanding bursts, which its
                // slave never answers, hold it still for the bound. With it
                // the DUT lane dies on burst both_at's completion, and the
                // model lane once the watch holds rready low.
                AXB_BOTH_DEAD: begin
                    a2c_lane_e first = dut_first ? A2C_DUT_LANE : A2C_MODEL_LANE;
                    both_at     = n_items / 2;
                    want_errors = 2;
                    want_text.push_back({"the ", a2c_lane_name(first), " lane has not ", dut_first ? "returned " : "taken the A"});
                    want_text.push_back({"the ", a2c_lane_name(a2c_lane_e'(1 - first)), " lane, alone since the ", a2c_lane_name(first),
                                         " lane died, has taken no A"});
                    want_text.push_back("clocks, waiting for ");
                    want_text.push_back({" (lone_lane_cycles, +a2c_lone_lane_cycles), so the master declares the ", a2c_lane_name(a2c_lane_e'(1 - first)),
                                         " lane dead. This is likely a consequence of the earlier A2C_SKEW, which declared the ", a2c_lane_name(first),
                                         " lane dead at "});
                    want_text.push_back("No lane is left, so every open and later burst returns to the sequence with no beats.");
                    uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_lone_lane_cycles", 150);
                end
                // The model lane dies on burst 3's address or W beat.
                AXB_ORDER_A, AXB_ORDER_W: begin
                    order_items();
                    want_errors = 1;
                    want_text.push_back((variant == AXB_ORDER_A) ? "the model lane has not taken the A" : "the model lane has not taken W beat 0 of ");
                    want_text.push_back({"of ", item_text(items[3])});
                    want_text.push_back("declares the model lane dead. The DUT lane serves every burst from now on.");
                end
                // Bursts of at most eight beats keep the four outstanding
                // within about 50 clocks at 70 percent rready, so the lanes
                // stay well under the bound.
                AXB_LAG, AXB_SKEW_OFF: begin
                    lane_skew = (variant == AXB_LAG) ? 300 : 0;
                    foreach (items[i]) begin
                        int unsigned keep = int'(items[i].id);
                        int unsigned gap  = items[i].gap;
                        if (!items[i].randomize() with { len <= 7; id == keep; }) `uvm_fatal("LB_RAND", "AXB_LAG randomize failed")
                        items[i].gap = gap;
                    end
                end
                // A window of 100 clocks keeps four long bursts at half
                // ready from reading as a pause.
                AXB_BUSY: begin
                    drain_deadline = 300;
                    drain_quiet    = 100;
                end
                default: ;
            endcase
            if (dead_early && want_errors != 0) want_text.push_back(death_text());
            if (!dead_early) unwant_text.push_back(related_text());
            if (role == A2C_SRC && skews()) uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_lane_skew_cycles", lane_skew);
            if (variant == AXB_LONE_OFF) uvm_config_db#(int unsigned)::set(this, "agent.drv", "a2c_lone_lane_cycles", 0);
            if (watch_passive) begin
                CFG_T watcher_cfg = lane_cfg("watcher_cfg", vif, role, port);
                watcher_cfg.model_vif = model_vif;
                watcher_cfg.is_active = UVM_PASSIVE;
                uvm_config_db#(CFG_T)::set(this, "watcher", "cfg", watcher_cfg);
                watcher = AGENT_T::type_id::create("watcher", this);
            end
            drains    = lb_id_texts::type_id::create("drains");
            drains.id = "A2C_DRAIN";
            cuts      = lb_id_texts::type_id::create("cuts");
            cuts.id   = "A2C_CUT";
            uvm_report_cb::add(null, drains);
            uvm_report_cb::add(null, cuts);
            uvm_config_db#(CFG_T)::set(this, "agent", "cfg", agent_cfg);
            uvm_config_db#(CFG_T)::set(this, "peer", "cfg", peer_cfg);
            uvm_config_db#(CFG_T)::set(this, "model_peer", "cfg", model_peer_cfg);
            agent          = AGENT_T::type_id::create("agent", this);
            peer           = AGENT_T::type_id::create("peer", this);
            model_peer     = AGENT_T::type_id::create("model_peer", this);
            arrivals       = lb_arrivals#(ITEM_T)::type_id::create("arrivals", this);
            model_arrivals = lb_arrivals#(ITEM_T)::type_id::create("model_arrivals", this);
        endfunction

        // The peers are the test's own agents, so their monitors' reports of
        // bursts a busy run leaves open are not checked.
        virtual function void connect_phase(uvm_phase phase);
            a2c_replay_log_base log;
            agent.mon.ap.connect(arrivals.analysis_export);
            agent.model_mon.ap.connect(model_arrivals.analysis_export);
            // The model lane's master and model_mon are left with bursts open.
            if (variant inside {AXB_SERIAL, AXB_DUT_MID, AXB_SKIP_CUT}) begin
                model_peer.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
                agent.model_mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            end
            // A dead lane's monitors are left with the bursts it never
            // completed. The agent's report them as info, and the peers' end
            // of run error is demoted; any other A2C_PROTO stays an error.
            if (dies()) begin
                peer_open = a2c_error_demoter::type_id::create("peer_open");
                peer_open.demote_id   = "A2C_PROTO";
                peer_open.demote_text = "the run ended with";
                for (int l = 0; l < 2; l++) begin
                    if (variant != AXB_BOTH_DEAD && l != dead_lane()) continue;
                    uvm_report_cb::add((l == A2C_DUT_LANE) ? peer.mon : model_peer.mon, peer_open);
                end
            end
            if (stray) begin
                strays = a2c_error_demoter::type_id::create("strays");
                strays.demote_id   = "A2C_PROTO";
                strays.demote_text = "matches no outstanding";
                uvm_report_cb::add(null, strays);
            end
            if (variant inside {AXB_BUSY, AXB_SKIP_CUT}) begin
                peer.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
                model_peer.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            end
            if (variant == AXB_MODEL_EXTRA) begin
                model_peer.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
                agent.model_mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            end
            if (role == A2C_SRC) return;
            log = replay();
            log.drain_quiet_cycles    = drain_quiet;
            log.drain_deadline_cycles = drain_deadline;
            tracker.logs.push_back(log);
            // As the env marks a counted port, whose counter reports the
            // unpaired bursts.
            if (variant inside {AXB_DUT_EXTRA, AXB_SERIAL, AXB_DUT_MID, AXB_SKIP_CUT, AXB_DEAD_DRAIN}) agent.model_cmp.counted = 1;
        endfunction

        // A model lane left waiting never finishes, so after the DUT lane is
        // done the test waits only while the model lane completes a burst at
        // least once every 50 clocks.
        virtual task wait_drop();
            int unsigned idle = 0;
            if (variant inside {AXB_BUSY, AXB_SKIP_CUT}) begin
                while (arrivals.items.size() < n_items) clk_vif.sample_edge();
                return;
            end
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
            if (dead_early) begin
                fork
                    begin
                        clk_vif.sample_edge();
                        a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
                    end
                join_none
            end
            fork
                begin
                    bit was_waiting = 0;
                    forever begin
                        clk_vif.sample_edge();
                        clocks++;
                        if (clocks == 1) first_clock_at = $realtime;
                        if (clocks == 2) period = $realtime - first_clock_at;
                        if (role == A2C_DST) begin
                            if (replay().model_waiting() && !was_waiting) model_led++;
                            was_waiting = replay().model_waiting();
                        end
                    end
                end
                watch();
            join_none
            // The bound returns every burst, so the sequence ends; the guard
            // stands in for the UVM timeout. The slaves first read their
            // configs at the drive point after the reset release, so a deaf
            // lane is deaf from its first clock.
            if (role == A2C_SRC && skews()) begin
                if (variant == AXB_DEAF || (variant == AXB_BOTH_DEAD && !dut_first)) lane_accept(0, 1);
                if (variant == AXB_DEAF_W) lane_accept(1, 0);
                if (variant inside {AXB_LAG, AXB_SKEW_OFF}) lane_delay(A2C_MODEL_LANE, lag);
                fork
                    shape_lanes();
                    send(agent, items, A2C_DUT_LANE);
                    begin
                        wait (arrivals.items.size() != 0);
                        first_dut_at = clocks;
                        wait (demoter.demoted != 0);
                        first_skew_at = clocks;
                    end
                join_none
                for (int unsigned i = 0; !done[A2C_DUT_LANE] && i < items.size() * (lane_skew + lag + 100); i++) clk_vif.sample_edge();
                if (!done[A2C_DUT_LANE]) `uvm_error("LB_MODE_B", "the master did not return every burst to the sequence")
                repeat (2) clk_vif.sample_edge();
                // A lane dies once.
                if (dies()) kill_again(dead_lane());
            end else if (role == A2C_SRC) begin
                send(agent, items, A2C_DUT_LANE);
                repeat (2) clk_vif.sample_edge();
            end else begin
                fork
                    send(peer, items, A2C_DUT_LANE);
                    send(model_peer, model_items, A2C_MODEL_LANE);
                join_none
                wait_drop();
                if (variant == AXB_DEAD_DRAIN && !dead_early && dead_after == 0) a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
                if (variant == AXB_DEAD_DRAIN && !dead_early && dead_after != 0) begin
                    fork
                        begin
                            repeat (dead_after) clk_vif.sample_edge();
                            a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
                        end
                    join_none
                end
            end
            dropped_at = clocks;
            if (dead_in_catchup) begin
                fork
                    begin
                        repeat (drain_deadline + 5) clk_vif.sample_edge();
                        caught_up = arrivals.items.size() >= replay().get_cut() && model_arrivals.items.size() >= replay().get_cut();
                        a2c_replay_drain::lane_dead(A2C_MODEL_LANE, "uvm_test_top");
                    end
                join_none
            end
            if (model_stall != 0) begin
                fork
                    begin
                        repeat (drain_deadline - 20) clk_vif.sample_edge();
                        stall_model(1);
                        repeat (model_stall) clk_vif.sample_edge();
                        stall_model(0);
                    end
                join_none
            end
            phase.drop_objection(this);
        endtask

        virtual function void phase_ready_to_end(uvm_phase phase);
            super.phase_ready_to_end(phase);
            if (phase.get_imp() == uvm_run_phase::get()) ready_calls++;
        endfunction

        // The bursts of the DUT lane whose place in its completion order
        // differs from their place in the order they were sent.
        protected function int unsigned out_of_order();
            int unsigned n = 0;
            foreach (arrivals.items[i]) begin
                if (i >= items.size()) break;
                n += (arrivals.items[i].id !== items[i].id || arrivals.items[i].addr !== items[i].addr);
            end
            return n;
        endfunction

        // A death dates itself, for other ports' reports, by when its lane
        // began to trail, bound clocks before it: the clause of an event half
        // the bound before the death names it, and that of an event 2 clocks
        // more than the bound before it does not. The second event must come
        // after time 0, or a death dated at time 0 would pass unseen.
        protected function void check_since(a2c_lane_e l, int unsigned bound);
            string   tag    = {"the ", a2c_lane_name(l), " lane of ", port, " (uvm_test_top.agent.drv) began to trail at "};
            realtime far_at = died(l) - period * (bound + 2);
            string   near   = a2c_replay_drain::death_context(died(l) - period * (bound / 2));
            string   far    = a2c_replay_drain::death_context(far_at);
            if (far_at <= 0) begin
                `uvm_error("LB_MODE_B", $sformatf("the %s lane died at %0t, too soon after time 0 to test the date of its death", a2c_lane_name(l), died(l)))
            end
            if (!a2c_contains(near, tag) || a2c_contains(far, tag)) begin
                `uvm_error("LB_MODE_B", $sformatf("the %s lane died at %0t, %0d clocks after it began to trail, but the clause of an event %0d clocks before the death is '%s' and of one %0d clocks before it '%s'",
                                                  a2c_lane_name(l), died(l), bound, bound / 2, near, bound + 2, far))
            end
        endfunction

        // The bursts each lane completes, the master's books at the end, and
        // the timing each variant sets up. Once a lane dies the live one
        // completes every burst and the sequence gets each burst's own
        // response from it; the dead lane completes none after the rising
        // edge that follows its death, and model_cmp compares no pair from
        // the death on.
        protected function void check_skews(int unsigned pairs);
            lb_arrivals#(ITEM_T) got[2];
            a2c_lane_e           live = a2c_lane_e'(1 - dead_lane());
            int unsigned         skew = max_skew();
            int unsigned         late;
            got[A2C_DUT_LANE]   = arrivals;
            got[A2C_MODEL_LANE] = model_arrivals;
            `uvm_info("LB_STATS", $sformatf("the lanes completed bursts at most %0d clocks apart; the DUT lane, alone, went at most %0d clocks without completing a burst",
                                            skew, lone_gap), UVM_NONE)
            if (returned() != items.size()) `uvm_error("LB_MODE_B", $sformatf("%0d bursts sent, %0d returned", items.size(), returned()))
            if (!dies()) begin
                if (arrivals.items.size() != items.size() || model_arrivals.items.size() != items.size()) begin
                    `uvm_error("LB_MODE_B", $sformatf("the lanes completed %0d and %0d bursts, expected %0d each",
                                                      arrivals.items.size(), model_arrivals.items.size(), items.size()))
                end
                if (pairs != items.size()) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d bursts, expected %0d", pairs, items.size()))
                for (int l = 0; l < 2; l++) begin
                    if (is_dead(a2c_lane_e'(l))) `uvm_error("LB_MODE_B", {"the master declared the ", a2c_lane_name(a2c_lane_e'(l)), " lane dead"})
                end
                if (skew < lag / 2) `uvm_error("LB_MODE_B", $sformatf("the lanes completed bursts at most %0d clocks apart, so the lag went untested", skew))
                if (variant == AXB_LAG && skew >= lane_skew) begin
                    `uvm_error("LB_MODE_B", $sformatf("the lanes completed a burst %0d clocks apart, not under the bound of %0d", skew, lane_skew))
                end
                return;
            end
            for (int l = 0; l < 2; l++) begin
                a2c_lane_e lane = a2c_lane_e'(l);
                bit        want = (variant == AXB_BOTH_DEAD) || lane != live;
                if (is_dead(lane) != want) begin
                    `uvm_error("LB_MODE_B", $sformatf("the master %s the %s lane dead", want ? "did not declare" : "declared", a2c_lane_name(lane)))
                end
                if (!is_dead(lane)) continue;
                late = 0;
                foreach (got[l].at[i]) late += (got[l].at[i] > died(lane));
                if (late > 1) begin
                    `uvm_error("LB_MODE_B", $sformatf("the dead %s lane completed %0d bursts after its death, at most 1 expected",
                                                      a2c_lane_name(lane), late))
                end
            end
            for (int l = 0; l < 2; l++) begin
                if (agent.model_cmp.uncompared(a2c_lane_e'(l)) != got[l].items.size() - pairs) begin
                    `uvm_error("LB_MODE_B", $sformatf("model_cmp counts %0d %s items uncompared, expected %0d",
                                                      agent.model_cmp.uncompared(a2c_lane_e'(l)), a2c_lane_name(a2c_lane_e'(l)),
                                                      got[l].items.size() - pairs))
                end
                foreach (frozen[l][i]) begin
                    if (is_dead(a2c_lane_e'(l)) && frozen[l][i].errors != 0) begin
                        `uvm_error("LB_MODE_B", $sformatf("%0d clocks moved %s of the dead %s lane", frozen[l][i].errors, frozen[l][i].what,
                                                          a2c_lane_name(a2c_lane_e'(l))))
                    end
                end
            end
            if (!agent.model_cmp.stopped()) `uvm_error("LB_MODE_B", "model_cmp was not told of the dead lane")
            // The first death trails by the skew bound, and a second, of the
            // lane left alone, by the lone lane bound, 150 here.
            if (variant == AXB_BOTH_DEAD) begin
                a2c_lane_e first = dut_first ? A2C_DUT_LANE : A2C_MODEL_LANE;
                check_since(first, lane_skew);
                check_since(a2c_lane_e'(1 - first), 150);
            end else begin
                check_since(dead_lane(), lane_skew);
            end
            check_order();
            if (variant inside {AXB_ORDER_A, AXB_ORDER_W}
                    && !(answered_at(0) < died(A2C_MODEL_LANE) && answered_at(1) == died(A2C_MODEL_LANE) && answered_at(2) > died(A2C_MODEL_LANE))) begin
                `uvm_error("LB_MODE_B", $sformatf("the DUT lane completed bursts 0 to 2 at %0t, %0t and %0t and the model lane died at %0t, so the order around the death went untested",
                                                  answered_at(0), answered_at(1), answered_at(2), died(A2C_MODEL_LANE)))
            end
            if (order_model != 0 && answered_at(order_model - 1, A2C_MODEL_LANE) != died(A2C_MODEL_LANE)) begin
                `uvm_error("LB_MODE_B", $sformatf("the model lane completed burst %0d at %0t and died at %0t, so a burst completed in the time step of the death went untested",
                                                  order_model - 1, answered_at(order_model - 1, A2C_MODEL_LANE), died(A2C_MODEL_LANE)))
            end
            if (variant inside {AXB_LONE_STALL, AXB_LONE_OFF} && lone_gap < lane_skew + 100) begin
                `uvm_error("LB_MODE_B", $sformatf("the DUT lane, alone, went at most %0d clocks without completing a burst, so the stall went untested", lone_gap))
            end
            if (stray && strays.demoted != 2) begin
                `uvm_error("LB_MODE_B", $sformatf("%0d A2C_PROTO errors of the stray R beat, expected one from each monitor of the model lane", strays.demoted))
            end
            if (pairs < want_pairs) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d bursts, expected at least %0d", pairs, want_pairs))
            if (pairs != pairs_at_death) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d bursts, but %0d by the death", pairs, pairs_at_death))
            end
            // Only the lane that died last returns beats once the other is
            // dead.
            if (variant == AXB_BOTH_DEAD) begin
                a2c_lane_e last = dut_first ? A2C_MODEL_LANE : A2C_DUT_LANE;
                if (empties() != items.size() - got[last].items.size()) begin
                    `uvm_error("LB_MODE_B", $sformatf("%0d bursts returned with no beats, expected the %0d the %s lane did not complete",
                                                      empties(), items.size() - got[last].items.size(), a2c_lane_name(last)))
                end
                if (addr_count(A2C_DUT_LANE) < both_at) `uvm_error("LB_MODE_B", "the DUT lane died before it took address both_at")
                return;
            end
            if (empties() != 0) `uvm_error("LB_MODE_B", $sformatf("%0d bursts returned with no beats", empties()))
            if (got[live].items.size() != items.size()) begin
                `uvm_error("LB_MODE_B", $sformatf("the live %s lane completed %0d bursts, expected %0d", a2c_lane_name(live),
                                                  got[live].items.size(), items.size()))
            end
            if (left(live) != 0 || queued(live) != 0) begin
                `uvm_error("LB_MODE_B", $sformatf("the master counts %0d bursts outstanding and %0d queued on the live %s lane at the end",
                                                  left(live), queued(live), a2c_lane_name(live)))
            end
            // The first A2C_SKEW error comes one bound after the DUT lane's
            // first burst; the clock counter may be one off either way.
            if (variant == AXB_MUTE && (first_skew_at + 1 < first_dut_at + lane_skew || first_skew_at > first_dut_at + lane_skew + 1)) begin
                `uvm_error("LB_MODE_B", $sformatf("the first A2C_SKEW error came %0d clocks after the DUT lane's first burst, expected %0d",
                                                  first_skew_at - first_dut_at, lane_skew))
            end
        endfunction

        virtual function void check_phase(uvm_phase phase);
            int unsigned pairs = agent.model_cmp.get_pairs();
            int unsigned n = (arrivals.items.size() < model_arrivals.items.size()) ? arrivals.items.size()
                                                                                    : model_arrivals.items.size();
            int unsigned apart = 0;
            int unsigned ids[int unsigned];
            int unsigned kinds[axi_burst_e];
            int unsigned took = clocks - dropped_at;
            super.check_phase(phase);
            for (int unsigned i = 0; i < n; i++) begin
                apart += (arrivals.items[i].id !== model_arrivals.items[i].id
                          || arrivals.items[i].addr !== model_arrivals.items[i].addr);
            end
            foreach (arrivals.items[i]) begin
                ids[int'(arrivals.items[i].id)] = 1;
                kinds[arrivals.items[i].burst] = 1;
            end
            `uvm_info("LB_STATS", $sformatf("%0d and %0d bursts on the DUT and model lanes, %0d in different places; %0d pairs; %0d IDs; %0d out of send order on the DUT lane; the model lane waited for %0d picks; the drain took %0d clocks",
                                            arrivals.items.size(), model_arrivals.items.size(), apart, pairs, ids.num(),
                                            out_of_order(), model_led, took), UVM_NONE)
            if (watch_passive) begin
                if (watcher.drv != null) `uvm_error("LB_MODE_B", "the passive agent built a driver")
                if (pairs == 0 || watcher.model_cmp.get_pairs() != pairs) begin
                    `uvm_error("LB_MODE_B", $sformatf("the passive agent's model_cmp paired %0d bursts, the agent's %0d", watcher.model_cmp.get_pairs(), pairs))
                end
                if (dies() && !watcher.model_cmp.is_dead(dead_lane())) `uvm_error("LB_MODE_B", "the passive agent's model_cmp was not told of the death")
            end
            if (dead_early && demoter.count(death_text()) != demoter.messages.size()) begin
                `uvm_error("LB_MODE_B", $sformatf("a demoted report does not name the death: %p", demoter.messages))
            end
            if (role == A2C_SRC && skews()) begin
                check_skews(pairs);
                return;
            end
            if (id_unbound) begin
                int unsigned sent[int unsigned];
                foreach (items[i]) sent[int'(items[i].id)] = 1;
                if (sent.num() < 2) `uvm_error("LB_MODE_B", "the bursts were sent with one ID, so the masters' ID 0 went untested")
                foreach (arrivals.items[i]) if (arrivals.items[i].id !== '0) `uvm_error("LB_MODE_B", "a DUT lane burst has an ID other than 0")
                foreach (model_arrivals.items[i]) if (model_arrivals.items[i].id !== '0) `uvm_error("LB_MODE_B", "a model lane burst has an ID other than 0")
            end else if (ids.num() < 2) begin
                `uvm_error("LB_MODE_B", "the bursts used one ID, so per-ID order went untested")
            end
            if (kinds.num() != 3) `uvm_error("LB_MODE_B", "the DUT lane did not complete a FIXED, an INCR and a WRAP burst")
            if (variant inside {AXB_MATCH, AXB_MISMATCH, AXB_DUT_EXTRA, AXB_MODEL_EXTRA, AXB_CROSS}
                && uvm_report_server::get_server().get_id_count("A2C_PROTO") != want_proto) begin
                `uvm_error("LB_MODE_B", $sformatf("%0d A2C_PROTO reports, expected %0d", uvm_report_server::get_server().get_id_count("A2C_PROTO"),
                                                  want_proto))
            end
            check_family();
            if (role == A2C_SRC) begin
                if (arrivals.items.size() != items.size() || model_arrivals.items.size() != items.size()) begin
                    `uvm_error("LB_MODE_B", $sformatf("the lanes completed %0d and %0d bursts, expected %0d", arrivals.items.size(),
                                                      model_arrivals.items.size(), items.size()))
                end
                if (pairs != items.size()) `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d bursts, expected %0d", pairs, items.size()))
                if (apart == 0 && !id_unbound) begin
                    `uvm_error("LB_MODE_B", "the lanes completed every burst in the same order, so the per-ID pairing went untested")
                end
                return;
            end
            if (apart != 0) begin
                `uvm_error("LB_MODE_B", $sformatf("the lanes completed %0d bursts in different places, so the model lane did not serve the DUT lane's picks in order",
                                                  apart))
            end
            if (out_of_order() == 0 && !(variant inside {AXB_BUSY, AXB_SKIP_CUT})) begin
                `uvm_error("LB_MODE_B", "the DUT lane served every burst in AR order, so the reorder pick went untested")
            end
            if (!(variant inside {AXB_BUSY, AXB_SKIP_CUT}) && pairs != n) begin
                `uvm_error("LB_MODE_B", $sformatf("model_cmp paired %0d bursts, expected %0d", pairs, n))
            end
            case (variant)
                AXB_MATCH, AXB_MISMATCH: begin
                    if (model_led == 0 || model_led >= n) begin
                        `uvm_error("LB_MODE_B", $sformatf("the model lane waited for %0d of %0d picks, so one lane never led", model_led, n))
                    end
                end
                // The lane left with a burst keeps the drain to its deadline,
                // a death on another port included, which only adds its
                // clause to the reports. The clock counter races the drain on
                // each edge, so it may be one off.
                AXB_DUT_EXTRA, AXB_MODEL_EXTRA, AXB_SERIAL, AXB_DUT_MID, AXB_DEAD_DRAIN: begin
                    if (took + 1 < drain_deadline || took > drain_deadline + 1) begin
                        `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected its deadline of %0d", took, drain_deadline))
                    end
                    if (variant == AXB_DEAD_DRAIN && (drains.messages.size() != 1 || drains.count(death_text()) != 1)) begin
                        `uvm_error("LB_MODE_B", $sformatf("expected one A2C_DRAIN report, naming the death: %p", drains.messages))
                    end
                    // "; " separates the requests the held report lists.
                    if (variant == AXB_DUT_MID) begin
                        foreach (demoter.messages[i]) begin
                            string       m      = demoter.messages[i];
                            int unsigned listed = 1;
                            if (!a2c_contains(m, "the first 3: ")) continue;
                            for (int c = 0; c + 1 < m.len(); c++) listed += (m.substr(c, c + 1) == "; ");
                            if (listed != 3) `uvm_error("LB_MODE_B", $sformatf("the held report lists %0d requests, expected 3: %s", listed, m))
                        end
                    end
                end
                AXB_BUSY: begin
                    check_cut(replay(), n_items, pairs, arrivals.items.size(), model_arrivals.items.size());
                    // A trailing model lane keeps the run going while the DUT
                    // lane completes bursts past the cut, which model_cmp
                    // must hold back.
                    if (model_stall != 0 && arrivals.items.size() <= replay().get_cut()) begin
                        `uvm_error("LB_MODE_B", $sformatf("the DUT lane completed %0d bursts, none past the cut at %0d, so the hold went untested",
                                                          arrivals.items.size(), replay().get_cut()))
                    end
                    if (arrivals.items.size() >= items.size()) begin
                        `uvm_error("LB_MODE_B", "the DUT lane's master ran out of bursts, so the port paused")
                    end
                    if (ready_calls != 2) `uvm_error("LB_MODE_B", $sformatf("%0d phase_ready_to_end calls, expected 2", ready_calls))
                    // A death during the catch-up neither ends the drain nor
                    // holds it, and the cut's report names it.
                    if (dead_in_catchup && caught_up) begin
                        `uvm_error("LB_MODE_B", "the lanes had caught up with the cut before the death, so a death during the catch-up went untested")
                    end
                    // The cut came before a death in the catch-up, so its
                    // report names only an earlier one.
                    if (dead_early ? cuts.count(death_text()) != 1 : cuts.count(related_text()) != 0) begin
                        `uvm_error("LB_MODE_B", $sformatf("expected an A2C_CUT report %s the death: %p", dead_early ? "naming" : "not naming",
                                                          cuts.messages))
                    end
                    // After the cut each lane completes the bursts the DUT
                    // lane had started: up to four, of up to 32 beats, at
                    // 70 percent ready.
                    if (took + 1 < drain_deadline || took > drain_deadline + 200) begin
                        `uvm_error("LB_MODE_B", $sformatf("the drain took %0d clocks, expected a cut at its deadline of %0d and an end within 200 clocks more",
                                                          took, drain_deadline))
                    end
                end
                AXB_CROSS: if (cross_swaps == 0) `uvm_error("LB_MODE_B", "no two bursts of different IDs were swapped, so the cross-ID order went untested")
                // More catch-up clocks would not help, so the advice to
                // raise them must not appear.
                AXB_SKIP_CUT: begin
                    if (replay().get_cut() <= lone_at) `uvm_error("LB_MODE_B", $sformatf("the cut at %0d does not keep the skipped burst", replay().get_cut()))
                    if (demoter.count("drain_catchup_cycles") != 0) `uvm_error("LB_MODE_B", "an A2C_REPLAY report advises drain_catchup_cycles for a held pick")
                end
                default: ;
            endcase
        endfunction
    endclass : lb_axi_mode_b

    // ---------------------------------------------------------------- axi_read

    // Sends a prepared list of bursts and checks each response as axr_seq
    // does, except that with allow_empty set a response with no beats, as a
    // master with both lanes dead returns, is only counted.
    class axr_list_seq extends axr_seq;
        axr_item_t   list[$];
        // The master sends every burst with ID 0, so each comes back with
        // ID 0.
        bit          id_unbound;
        bit          allow_empty;
        int unsigned empties;

        `uvm_object_utils(axr_list_seq)

        function new(string name = "axr_list_seq");
            super.new(name);
        endfunction

        virtual task body();
            axr_item_t copy;
            n = list.size();
            foreach (list[i]) begin
                $cast(copy, list[i].clone());
                if (id_unbound) copy.id = '0;
                waiting.push_back(copy);
                send(list[i]);
            end
            wait_for_reads();
        endtask

        virtual function void read_done(axr_item_t rsp);
            int found[$];
            if (!allow_empty || rsp.data.size() != 0) begin
                super.read_done(rsp);
                return;
            end
            found = waiting.find_first_index(w) with (w.id === rsp.id && w.addr === rsp.addr);
            if (found.size() != 0) waiting.delete(found[0]);
            responses.push_back(rsp);
            empties++;
        endfunction
    endclass : axr_list_seq

    typedef axi_read_master_driver #(lb_axr_addr_t, lb_axr_data_t, lb_axr_aruser_t, lb_axr_ruser_t, lb_axr_id_t) axr_master_t;

    // The master, with its books open to the test.
    class axr_master_probe extends axr_master_t;
        `uvm_component_utils(axr_master_probe)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function int unsigned left(int l);
            return outstanding[l];
        endfunction

        function int unsigned queued(int l);
            int unsigned n = 0;
            id_key_t     k;
            if (pending[l].first(k)) do n += pending[l][k].size(); while (pending[l].next(k));
            return n;
        endfunction

        function bit is_dead(int l);
            return dead[l];
        endfunction

        function realtime died(int l);
            return died_at[l];
        endfunction

        function void kill_again(int l);
            declare_dead(a2c_lane_e'(l), "kill_again", $realtime);
        endfunction
    endclass : axr_master_probe

    // An axi_read slave that interleaves: each beat goes to a random burst
    // among the oldest open one of each ID, from a few clocks after its AR.
    // It reads mem and never answers SLVERR.
    class axr_interleave_slave extends uvm_component;
        axr_vif_t          vif;
        virtual a2c_clk_if clk_vif;
        axi_read_mem_t     mem;
        // Beats sent to a burst other than the last beat's, while that one
        // was still open.
        int unsigned       switches;
        // Takes ARs and never answers one.
        bit                mute;
        // Holds arready low.
        bit                ar_off;
        // The clocks from an AR to its burst's first beat; 0 draws 0 to 8.
        int unsigned       late;
        // Sends one beat with the all-ones rid, after the first AR.
        bit                stray;

        typedef struct {
            axr_item_t   ar;
            int unsigned beat;
            longint      due;
        } open_t;

        protected open_t open[$];

        `uvm_component_utils(axr_interleave_slave)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected function lb_axr_data_t beat_data(axr_item_t ar, int unsigned n);
            bit [31:0]   word = '0;
            bit [63:0]   first;
            int unsigned count;
            axi_beat(64'(ar.addr), ar.size, ar.len, ar.burst, n, first, count);
            for (int unsigned i = 0; i < count; i++) word[8 * ((first + i) % 4) +: 8] = mem.read(first + i);
            return lb_axr_data_t'(word);
        endfunction

        virtual task run_phase(uvm_phase phase);
            int          cur = -1;
            axr_item_t   last;
            bit          on_bus;
            longint      clocks;
            vif.arready <= 1'b0;
            vif.rvalid  <= 1'b0;
            vif.rlast   <= 1'b0;
            vif.rresp   <= '0;
            vif.ruser   <= '0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            forever begin
                vif.arready <= ($urandom_range(99, 0) < 70) && !ar_off;
                if (!on_bus && stray && open.size() != 0) begin
                    vif.rvalid <= 1'b1;
                    vif.rid    <= '1;
                    vif.rdata  <= '0;
                    vif.rlast  <= 1'b1;
                    on_bus = 1;
                    stray  = 0;
                    cur    = -1;
                end else if (!on_bus && mute) begin
                    vif.rvalid <= 1'b0;
                    vif.rlast  <= 1'b0;
                end else if (!on_bus) begin
                    int ready[$];
                    foreach (open[i]) begin
                        bit older = 0;
                        for (int j = 0; j < i; j++) older |= (open[j].ar.id === open[i].ar.id);
                        if (!older && open[i].due <= clocks) ready.push_back(i);
                    end
                    cur = (ready.size() == 0) ? -1 : ready[$urandom_range(ready.size() - 1, 0)];
                    if (cur >= 0) begin
                        if (last != null && last != open[cur].ar && open.size() > 0) begin
                            foreach (open[i]) if (open[i].ar == last) switches++;
                        end
                        last = open[cur].ar;
                        vif.rvalid <= 1'b1;
                        vif.rid    <= open[cur].ar.id;
                        vif.rdata  <= beat_data(open[cur].ar, open[cur].beat);
                        vif.rlast  <= (open[cur].beat == open[cur].ar.len);
                        on_bus = 1;
                    end else begin
                        vif.rvalid <= 1'b0;
                        vif.rlast  <= 1'b0;
                    end
                end
                clk_vif.sample_edge();
                clocks++;
                if (on_bus && vif.rready === 1'b1) begin
                    on_bus = 0;
                    if (cur < 0) ;
                    else if (open[cur].beat == open[cur].ar.len) open.delete(cur);
                    else open[cur].beat++;
                end
                if (vif.arvalid === 1'b1 && vif.arready === 1'b1) begin
                    open_t o;
                    o.ar       = axr_item_t::type_id::create("ar");
                    o.ar.id    = vif.arid;
                    o.ar.addr  = vif.araddr;
                    o.ar.len   = vif.arlen;
                    o.ar.size  = vif.arsize;
                    o.ar.burst = axi_burst_e'(vif.arburst);
                    o.due      = clocks + ((late != 0) ? late : $urandom_range(8, 0));
                    open.push_back(o);
                end
                clk_vif.drive_edge();
            end
        endtask
    endclass : axr_interleave_slave

    // An axi_read slave whose bursts are one beat each, answered at clocks
    // the test sets. It takes the first ar_limit ARs, or every AR when
    // ar_limit is negative. Unless mute, the AR of burst anchor sets the
    // clocks of bursts 0 to offs.size() - 1, offs[n] after it, and each
    // later burst is answered 2 clocks after its AR. With lead set, the
    // anchor of lead, the other lane's script, sets them instead, and an
    // offs entry of 0 leaves its burst unanswered.
    class axr_script_slave extends axr_interleave_slave;
        int              ar_limit = -1;
        int              anchor = -1;
        int unsigned     offs[$];
        axr_script_slave lead;
        // The clock of this script's anchor, or 0 before it.
        longint          anchored_at;
        // Per burst: its AR, the clock its beat goes out on, or 0 until set,
        // and when the beat transferred, or 0.
        axr_item_t   ars[$];
        longint      due[$];
        realtime     done_at[$];

        `uvm_component_utils(axr_script_slave)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            int     cur = -1;
            longint now = 0;
            bit     led;
            vif.arready <= 1'b0;
            vif.rvalid  <= 1'b0;
            vif.rlast   <= 1'b0;
            vif.rresp   <= '0;
            vif.ruser   <= '0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            forever begin
                vif.arready <= ar_limit < 0 || ars.size() < ar_limit;
                if (lead != null && !led && lead.anchored_at != 0) begin
                    led = 1;
                    foreach (offs[n]) if (offs[n] != 0 && n < due.size()) due[n] = lead.anchored_at + offs[n];
                end
                if (cur < 0 && !mute) begin
                    foreach (due[n]) begin
                        if (done_at[n] == 0 && due[n] != 0 && due[n] <= now + 1) begin
                            cur = n;
                            break;
                        end
                    end
                end
                vif.rvalid <= cur >= 0;
                vif.rlast  <= cur >= 0;
                if (cur >= 0) begin
                    vif.rid   <= ars[cur].id;
                    vif.rdata <= beat_data(ars[cur], 0);
                end
                clk_vif.sample_edge();
                now++;
                if (cur >= 0 && vif.rready === 1'b1) begin
                    done_at[cur] = $realtime;
                    cur = -1;
                end
                if (vif.arvalid === 1'b1 && vif.arready === 1'b1) begin
                    axr_item_t ar = axr_item_t::type_id::create("ar");
                    ar.id    = vif.arid;
                    ar.addr  = vif.araddr;
                    ar.len   = vif.arlen;
                    ar.size  = vif.arsize;
                    ar.burst = axi_burst_e'(vif.arburst);
                    ars.push_back(ar);
                    done_at.push_back(0);
                    due.push_back((ars.size() > offs.size()) ? now + 2 : 0);
                    if (ars.size() == anchor + 1) begin
                        anchored_at = now;
                        foreach (offs[n]) due[n] = now + offs[n];
                    end
                end
                clk_vif.drive_edge();
            end
        endtask
    endclass : axr_script_slave

    // Mode B on an axi_read port whose DUT masters it: the agent is the
    // slave, serving both lanes from one memory with the random fill.
    class axi_read_mode_b_test extends lb_axi_mode_b #(axr_agent_t, axr_item_t, axr_config_t, axr_vif_t);
        axi_read_mem_t       mem;
        // A2C_SRC: the model lane's slave's memory, a copy of mem.
        axi_read_mem_t       model_mem;
        axr_interleave_slave interleaver;
        axr_list_seq         seqs[2];
        // Per lane: the most bursts outstanding at once.
        int unsigned         peak[2];
        // A2C_SRC: the clocks one lane's AR transferred and the other's did
        // not, and per lane the ARs taken.
        int unsigned         ar_apart;
        int unsigned         ars[2];
        // A2C_DST: the slave answers SLVERR on a quarter of the addresses,
        // and the model lane gets the DUT lane's rresp.
        bit                  slverr;
        // AXB_BOTH_DEAD: the master's rready went low for good mid-burst.
        bit                  rready_cut;
        // AXB_ORDER_A: each lane's slave.
        axr_script_slave     scripts[2];

        `uvm_component_utils(axi_read_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            port = "axr";
        endfunction

        virtual function axr_item_t new_item(int unsigned i);
            axr_item_t it = axr_item_t::type_id::create($sformatf("it%0d", i));
            if (!it.randomize() with { len dist {[0:7] :/ 90, [8:31] :/ 10}; }) `uvm_fatal("LB_RAND", "axi_read item randomize failed")
            it.gap = 0;
            return it;
        endfunction

        virtual function void configure();
            mem = axi_read_mem_t::type_id::create("mem");
            mem.fill = A2C_MEM_FILL_RANDOM;
            if (role == A2C_DST) begin
                agent_cfg.mem            = mem;
                agent_cfg.reorder        = 1'b1;
                agent_cfg.resp_delay_max = 8;
                agent_cfg.arready_pct    = 70;
                if (slverr) agent_cfg.error_ranges.push_back('{lo: 64'h0, hi: 64'h3fff});
                // The model lane's master takes beats faster, so the model
                // lane often ends a burst first and waits for the next pick.
                peer_cfg.max_outstanding       = 4;
                peer_cfg.rready_pct            = 50;
                model_peer_cfg.max_outstanding = 4;
                model_peer_cfg.rready_pct      = 100;
                return;
            end
            agent_cfg.max_outstanding = 4;
            agent_cfg.rready_pct      = 70;
            axr_master_t::type_id::set_inst_override(axr_master_probe::get_type(), "agent.drv", this);
            // Scripts serve both lanes, and the peers only watch.
            if (variant == AXB_ORDER_A) begin
                agent_cfg.rready_pct = 100;
                peer_cfg.is_active   = UVM_PASSIVE;
            end
            peer_cfg.mem            = mem;
            peer_cfg.reorder        = 1'b1;
            peer_cfg.resp_delay_max = 8;
            peer_cfg.arready_pct    = 70;
            model_mem      = axi_read_mem_t::type_id::create("model_mem");
            model_mem.fill = A2C_MEM_FILL_RANDOM;
            model_mem.seed = mem.seed;
            // The interleaving slave answers the model lane.
            model_peer_cfg.is_active = UVM_PASSIVE;
        endfunction

        // A2C_DST: the model lane's burst carries another aruser. A2C_SRC:
        // the model lane's memory differs in one byte the burst reads, so
        // every burst that reads it differs.
        virtual function void mismatch();
            bit [63:0]   first;
            int unsigned count;
            want_errors = 0;
            if (role == A2C_DST) begin
                model_items[mismatch_at].aruser = ~model_items[mismatch_at].aruser;
                want_errors = 1;
            end else begin
                axr_item_t it = items[mismatch_at];
                bit [63:0] byte_at;
                axi_beat(64'(it.addr), it.size, it.len, it.burst, 0, byte_at, count);
                model_mem.write(byte_at, ~mem.read(byte_at));
                foreach (items[i]) begin
                    bit hit = 0;
                    for (int unsigned b = 0; b <= items[i].len; b++) begin
                        axi_beat(64'(items[i].addr), items[i].size, items[i].len, items[i].burst, b, first, count);
                        hit |= (byte_at >= first && byte_at < first + count);
                    end
                    want_errors += hit;
                end
            end
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair "));
            want_text.push_back($sformatf(" key %0h: DUT ", items[mismatch_at].id));
        endfunction

        virtual function void one_lane_text(a2c_lane_e lane);
            axr_item_t it = items[n_items];
            string     head = "uvm_test_top.agent.drv: the DUT lane served ";
            string     tail = ", and the model lane never issued that AR";
            if (lane == A2C_MODEL_LANE) begin
                it   = model_items[n_items];
                head = "uvm_test_top.agent.drv: the model lane issued 1 ARs the DUT lane never issued, the first ";
                tail = "";
            end
            want_text.push_back(head);
            want_text.push_back($sformatf(", AR %0d of ID %0h%s", dut_count(it.id), it.id, tail));
        endfunction

        virtual function string held_text(axr_item_t it, int unsigned n);
            return $sformatf(", AR %0d of ID %0h, whose AR it has not issued, with ", n, it.id);
        endfunction

        // The bursts with ID id among the first n_items + 1 the masters send.
        protected function int unsigned dut_count(lb_axr_id_t id);
            int unsigned n = 0;
            for (int unsigned i = 0; i <= n_items; i++) n += ((i < n_items ? items[i].id : id) === id);
            return n;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (role != A2C_SRC) return;
            for (int l = 0; l < 2; l++) frozen[l].push_back(lb_frozen::of("the AR channel"));
            if (variant == AXB_ORDER_A) begin
                for (int l = 0; l < 2; l++) begin
                    scripts[l] = axr_script_slave::type_id::create($sformatf("script%0d", l), this);
                    scripts[l].vif     = (l == A2C_DUT_LANE) ? vif : model_vif;
                    scripts[l].clk_vif = clk_vif;
                    scripts[l].mem     = (l == A2C_DUT_LANE) ? mem : model_mem;
                end
                scripts[A2C_DUT_LANE].anchor     = 3;
                scripts[A2C_DUT_LANE].offs       = '{lane_skew - 10, lane_skew, lane_skew + 1, lane_skew + 5};
                scripts[A2C_MODEL_LANE].ar_limit = 3;
                scripts[A2C_MODEL_LANE].mute     = (order_model == 0);
                scripts[A2C_MODEL_LANE].lead     = scripts[A2C_DUT_LANE];
                scripts[A2C_MODEL_LANE].offs     = (order_model == 1) ? '{lane_skew, 0, 0} : '{lane_skew - 10, lane_skew, 0};
                return;
            end
            interleaver = axr_interleave_slave::type_id::create("interleaver", this);
            interleaver.vif     = model_vif;
            interleaver.clk_vif = clk_vif;
            interleaver.mem     = model_mem;
            interleaver.mute    = variant inside {AXB_MUTE, AXB_LONE_STALL, AXB_LONE_OFF};
            interleaver.stray   = stray;
        endfunction

        virtual function a2c_replay_log_base replay();
            axr_agent_t::slave_t s;
            $cast(s, agent.drv);
            return s.replay;
        endfunction

        virtual function void lane_delay(a2c_lane_e l, int unsigned n);
            if (l == A2C_MODEL_LANE) begin
                interleaver.late = n;
                return;
            end
            peer_cfg.resp_delay_min = n;
            peer_cfg.resp_delay_max = (n != 0) ? n : 8;
        endfunction

        virtual function void lane_accept(bit addr, bit data);
            interleaver.ar_off = !addr;
        endfunction

        virtual function int unsigned addr_count(a2c_lane_e l);
            return ars[l];
        endfunction

        virtual function int unsigned drawn_count(a2c_lane_e l);
            return ars[l];
        endfunction

        virtual function string done_word();
            return "the last R beat of ";
        endfunction

        protected function axr_master_probe probe();
            $cast(probe, agent.drv);
        endfunction

        virtual function int unsigned left(a2c_lane_e l);
            return probe().left(l);
        endfunction

        virtual function int unsigned queued(a2c_lane_e l);
            return probe().queued(l);
        endfunction

        virtual function int unsigned returned();
            return seqs[A2C_DUT_LANE].responses.size();
        endfunction

        virtual function int unsigned empties();
            return seqs[A2C_DUT_LANE].empties;
        endfunction

        virtual function bit is_dead(a2c_lane_e l);
            return probe().is_dead(l);
        endfunction

        virtual function realtime died(a2c_lane_e l);
            return probe().died(l);
        endfunction

        virtual function void kill_again(a2c_lane_e l);
            probe().kill_again(l);
        endfunction

        virtual function axr_item_t response(int unsigned n);
            return seqs[A2C_DUT_LANE].responses[n];
        endfunction

        virtual function realtime answered_at(int unsigned n, a2c_lane_e l = A2C_DUT_LANE);
            return (n < scripts[l].done_at.size()) ? scripts[l].done_at[n] : 0;
        endfunction

        virtual task send(axr_agent_t src, axr_item_t list[$], a2c_lane_e lane);
            axr_list_seq seq = axr_list_seq::type_id::create($sformatf("seq%0d", lane));
            seq.list        = list;
            seq.mem         = mem;
            seq.id_unbound  = id_unbound;
            seq.allow_empty = (variant == AXB_BOTH_DEAD);
            if (role == A2C_DST) seq.error_ranges = agent_cfg.error_ranges;
            seqs[lane] = seq;
            seq.start(src.sqr);
            done[lane] = 1;
        endtask

        // As A2C_SRC an AR may go out on a lane only once both lanes took the
        // one before, until a lane dies, and a dead lane's master pins stay
        // as lb_frozen and check_ready() require.
        virtual task watch();
            axr_vif_t    v[2];
            int unsigned open[2];
            bit          hs[2];
            v[A2C_DUT_LANE]   = vif;
            v[A2C_MODEL_LANE] = model_vif;
            forever begin
                clk_vif.sample_edge();
                for (int l = 0; l < 2; l++) begin
                    if (role == A2C_SRC && !dies() && v[l].arvalid === 1'b1 && ars[l] > ars[1 - l]) begin
                        `uvm_error("LB_MODE_B", $sformatf("AR %0d went out on the %s lane before the other lane took AR %0d", ars[l] + 1,
                                                          a2c_lane_name(a2c_lane_e'(l)), ars[l]))
                    end
                    if (role == A2C_SRC && skews()) begin
                        frozen[l][0].sample(is_dead(a2c_lane_e'(l)), died(a2c_lane_e'(l)), v[l].arvalid, v[l].arready,
                                            {v[l].arid, v[l].araddr, v[l].arlen, v[l].arsize, v[l].arburst, v[l].aruser});
                        check_ready(a2c_lane_e'(l), v[l].rready, "rready");
                        note_death();
                    end
                    hs[l] = v[l].arvalid === 1'b1 && v[l].arready === 1'b1;
                end
                ar_apart += (hs[0] != hs[1]);
                for (int l = 0; l < 2; l++) begin
                    if (v[l].rvalid === 1'b1 && v[l].rready === 1'b1 && v[l].rlast === 1'b1) begin
                        open[l]--;
                        note_done(l, int'(v[l].rid));
                    end
                    if (hs[l]) begin
                        ars[l]++;
                        open[l]++;
                    end
                    if (open[l] > peak[l]) peak[l] = open[l];
                end
                // The model lane then dies holding some beats of a burst,
                // which must come back with none.
                if (variant == AXB_BOTH_DEAD && !rready_cut && is_dead(A2C_DUT_LANE) && v[A2C_MODEL_LANE].rvalid === 1'b1
                        && v[A2C_MODEL_LANE].rready === 1'b1 && v[A2C_MODEL_LANE].rlast !== 1'b1) begin
                    agent_cfg.rready_pct = 0;
                    rready_cut           = 1;
                end
            end
        endtask

        virtual function void check_family();
            `uvm_info("LB_STATS", $sformatf("at most %0d and %0d bursts outstanding; %0d clocks with an AR on one lane only; %0d interleaved beats",
                                            peak[A2C_DUT_LANE], peak[A2C_MODEL_LANE], ar_apart,
                                            interleaver == null ? 0 : interleaver.switches), UVM_NONE)
            if (variant inside {AXB_MATCH, AXB_MISMATCH, AXB_DUT_EXTRA, AXB_MODEL_EXTRA} && (peak[A2C_DUT_LANE] != 4 || peak[A2C_MODEL_LANE] != 4)) begin
                `uvm_error("LB_MODE_B", $sformatf("max_outstanding is 4, but at most %0d and %0d bursts were outstanding",
                                                  peak[A2C_DUT_LANE], peak[A2C_MODEL_LANE]))
            end
            if (slverr) begin
                `uvm_info("LB_STATS", $sformatf("%0d and %0d SLVERR beats on the DUT and model lanes", seqs[A2C_DUT_LANE].slverr_beats,
                                                seqs[A2C_MODEL_LANE].slverr_beats), UVM_NONE)
                if (seqs[A2C_DUT_LANE].slverr_beats == 0 || seqs[A2C_MODEL_LANE].slverr_beats != seqs[A2C_DUT_LANE].slverr_beats) begin
                    `uvm_error("LB_MODE_B", "the lanes did not both read the same SLVERR beats, so the rresp replay went untested")
                end
            end
            if (role != A2C_SRC) return;
            if (variant == AXB_BOTH_DEAD && !rready_cut) `uvm_error("LB_MODE_B", "the model lane, alone, returned no beat of a burst before its last")
            if (seqs[A2C_DUT_LANE].responses.size() != items.size()) begin
                `uvm_error("LB_MODE_B", $sformatf("%0d bursts sent, %0d returned", items.size(), seqs[A2C_DUT_LANE].responses.size()))
            end
            if (interleaver != null && interleaver.switches == 0 && !id_unbound) begin
                `uvm_error("LB_MODE_B", "the model lane's slave never interleaved, so interleaved R went untested")
            end
            if (ar_apart == 0) `uvm_error("LB_MODE_B", "every AR transferred on both lanes on one clock, so the per-lane handshake went untested")
        endfunction
    endclass : axi_read_mode_b_test

    class axi_read_mode_b_mismatch_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MISMATCH;
        endfunction
    endclass : axi_read_mode_b_mismatch_test

    // The DUT lane's master sends one burst more, which the model lane
    // never issues: the slave reports it at the end of the run.
    class axi_read_mode_b_dut_extra_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_dut_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DUT_EXTRA;
        endfunction
    endclass : axi_read_mode_b_dut_extra_test

    class axi_read_mode_b_model_extra_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_model_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MODEL_EXTRA;
        endfunction
    endclass : axi_read_mode_b_model_extra_test

    // Both masters keep sending with no gap after the drop, so the drain
    // cuts the slave's log, and model_cmp, keyed per ID, holds the bursts
    // past the cut.
    class axi_read_mode_b_busy_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_BUSY;
        endfunction
    endclass : axi_read_mode_b_busy_test

    // As axi_read_mode_b_busy_test with the model lane stalled across the
    // cut, so the DUT lane completes bursts past the cut before the model
    // lane reaches it.
    class axi_read_mode_b_busy_lag_test extends axi_read_mode_b_busy_test;
        `uvm_component_utils(axi_read_mode_b_busy_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_stall = 80;
        endfunction

        int unsigned kept;

        virtual function void stall_model(bit stall);
            if (stall) kept = model_peer_cfg.rready_pct;
            model_peer_cfg.rready_pct = stall ? 0 : kept;
        endfunction
    endclass : axi_read_mode_b_busy_lag_test

    // The agent is the master. The DUT lane's slave reorders, and the model
    // lane's interleaves R beats across IDs.
    class axi_read_mode_b_master_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_master_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_SRC;
        endfunction
    endclass : axi_read_mode_b_master_test

    class axi_read_mode_b_master_mismatch_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MISMATCH;
        endfunction
    endclass : axi_read_mode_b_master_mismatch_test

    // The model lane's master sends some bursts of different IDs in the
    // other order, so the model lane must find each pick by its ID and its
    // place among the bursts of that ID.
    class axi_read_mode_b_cross_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_cross_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_CROSS;
        endfunction
    endclass : axi_read_mode_b_cross_test

    // The model lane's master sends its next AR only after the last
    // response, and the DUT lane reorders: the model lane holds the first
    // reordered pick, whose AR its master waits to send, and the slave
    // reports the pick and the ARs behind it as a model defect.
    class axi_read_mode_b_serial_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_serial_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_SERIAL;
        endfunction
    endclass : axi_read_mode_b_serial_test

    // The DUT lane's master sends one burst more mid-run, among the others:
    // the model lane holds that pick, with its later ARs behind it, until
    // the end.
    class axi_read_mode_b_dut_mid_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_dut_mid_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DUT_MID;
        endfunction
    endclass : axi_read_mode_b_dut_mid_test

    // Both masters keep sending, and the model lane's skips one burst
    // mid-run. The drain cuts the run past that burst, and the slave still
    // reports the held pick, which the cut keeps.
    class axi_read_mode_b_skip_cut_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_skip_cut_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_SKIP_CUT;
        endfunction
    endclass : axi_read_mode_b_skip_cut_test

    // The agent is the master of a port that binds no id_t: it sends every
    // burst on both lanes with ID 0.
    class axi_read_mode_b_master_id_unbound_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_id_unbound_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            id_unbound = 1;
        endfunction
    endclass : axi_read_mode_b_master_id_unbound_test

    // The agent is the master, and the model lane's slave never answers.
    // The model lane dies lane_skew clocks after the DUT lane completes the
    // first burst, and the DUT lane serves the rest.
    class axi_read_mode_b_master_mute_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_mute_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MUTE;
        endfunction
    endclass : axi_read_mode_b_master_mute_test

    // The agent is the master, and the model lane's slave takes no AR. The
    // model lane dies lane_skew clocks after the DUT lane took the first,
    // with its arvalid held, and the DUT lane serves every burst.
    class axi_read_mode_b_master_deaf_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_deaf_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DEAF;
        endfunction
    endclass : axi_read_mode_b_master_deaf_test

    // The DUT lane answers one burst past the bound and dies, and the model
    // lane serves that burst and the rest.
    class axi_read_mode_b_master_dut_late_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DUT_LATE;
        endfunction
    endclass : axi_read_mode_b_master_dut_late_test

    // The model lane answers one burst and the next past the bound. It dies
    // on the first, and raises no second A2C_SKEW error on the next.
    class axi_read_mode_b_master_model_late_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MODEL_LATE;
        endfunction
    endclass : axi_read_mode_b_master_model_late_test

    // The model lane's slave stops taking ARs for a while. The model lane
    // dies on the AR it missed, and takes that AR once, with arvalid low
    // after it, when its slave resumes.
    class axi_read_mode_b_master_stall_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_STALL;
        endfunction
    endclass : axi_read_mode_b_master_stall_test

    // The model lane answers every burst lag clocks late, under the bound,
    // so no burst is an A2C_SKEW error.
    class axi_read_mode_b_master_lag_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_LAG;
        endfunction
    endclass : axi_read_mode_b_master_lag_test

    // As the lag test with lane_skew_cycles 0, which turns the bound off.
    class axi_read_mode_b_master_skew_off_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_skew_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_SKEW_OFF;
        endfunction
    endclass : axi_read_mode_b_master_skew_off_test

    // The DUT lane's slave stops answering and the DUT lane dies, and later
    // the master's rready goes low mid-burst, so the model lane dies too and
    // the sequence gets the rest of its bursts back with no beats, the one
    // the model lane had returned part of included.
    class axi_read_mode_b_master_both_dead_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_both_dead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant   = AXB_BOTH_DEAD;
            dut_first = 1;
        endfunction
    endclass : axi_read_mode_b_master_both_dead_test

    // The model lane dies on an AR while the DUT lane returns three bursts
    // of one ID around the death, and the sequence must get them back in
    // order.
    class axi_read_mode_b_master_order_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_order_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_ORDER_A;
        endfunction
    endclass : axi_read_mode_b_master_order_test

    // As the order test, with the model lane's slave answering burst 0 on
    // the clock of the death, on which the DUT lane completes burst 1.
    class axi_read_mode_b_master_order_m0_test extends axi_read_mode_b_master_order_test;
        `uvm_component_utils(axi_read_mode_b_master_order_m0_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            order_model = 1;
        endfunction
    endclass : axi_read_mode_b_master_order_m0_test

    // As the order test, with both lanes completing burst 1 on the clock of
    // the death.
    class axi_read_mode_b_master_order_both_test extends axi_read_mode_b_master_order_test;
        `uvm_component_utils(axi_read_mode_b_master_order_both_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            order_model = 2;
        endfunction
    endclass : axi_read_mode_b_master_order_both_test

    // The model lane dies, and the DUT lane, alone, then waits lane_skew +
    // 150 clocks for four bursts, under the default lone lane bound.
    class axi_read_mode_b_master_lone_stall_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_lone_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_LONE_STALL;
        endfunction
    endclass : axi_read_mode_b_master_lone_stall_test

    // As the lone stall test with a2c_lone_lane_cycles 0, which turns the
    // rule off.
    class axi_read_mode_b_master_lone_off_test extends axi_read_mode_b_master_test;
        `uvm_component_utils(axi_read_mode_b_master_lone_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_LONE_OFF;
        endfunction
    endclass : axi_read_mode_b_master_lone_off_test

    // As the mute test, with IDs 0 to 2 only, and the model lane's slave
    // sends one R beat of ID 3 before the death. Both monitors of the model
    // lane must still report it as an A2C_PROTO error, the agent's
    // included, though the master later tells it of the death.
    class axi_read_mode_b_master_stray_test extends axi_read_mode_b_master_mute_test;
        `uvm_component_utils(axi_read_mode_b_master_stray_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            stray = 1;
        endfunction
    endclass : axi_read_mode_b_master_stray_test

    // The DUT lane's master sends one burst the model lane's never does,
    // and a master elsewhere declares the model lane dead before the drop:
    // the drain still waits to its deadline, and its A2C_DRAIN report names
    // the death. The slave held the pick before the death, so its report of
    // the pick names none.
    class axi_read_mode_b_dead_drain_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_dead_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DEAD_DRAIN;
        endfunction
    endclass : axi_read_mode_b_dead_drain_test

    // As axi_read_mode_b_dead_drain_test with the death on the first clock,
    // before the pick, so the report of the pick names it too.
    class axi_read_mode_b_dead_early_drain_test extends axi_read_mode_b_dead_drain_test;
        `uvm_component_utils(axi_read_mode_b_dead_early_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_early = 1;
        endfunction
    endclass : axi_read_mode_b_dead_early_drain_test

    // As axi_read_mode_b_model_extra_test with a death on the first clock:
    // every report of the slave names it.
    class axi_read_mode_b_model_extra_dead_test extends axi_read_mode_b_model_extra_test;
        `uvm_component_utils(axi_read_mode_b_model_extra_dead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_early = 1;
        endfunction
    endclass : axi_read_mode_b_model_extra_dead_test

    // As axi_read_mode_b_master_mute_test after a death on another port, so
    // the master's A2C_SKEW report names that death.
    class axi_read_mode_b_master_mute_cascade_test extends axi_read_mode_b_master_mute_test;
        `uvm_component_utils(axi_read_mode_b_master_mute_cascade_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_early = 1;
        endfunction
    endclass : axi_read_mode_b_master_mute_cascade_test

    // A passive Mode B agent watches the port of a master whose model lane
    // dies: its monitors and model_cmp learn of the death, so they raise
    // no A2C_PROTO or A2C_MODEL_CMP error.
    class axi_read_mode_b_master_late_passive_test extends axi_read_mode_b_master_model_late_test;
        `uvm_component_utils(axi_read_mode_b_master_late_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            watch_passive = 1;
        endfunction
    endclass : axi_read_mode_b_master_late_passive_test

    // A passive Mode B agent watches a port the drain cuts: its model_cmp
    // is cut with the slave's, and its monitors learn of the cut.
    class axi_read_mode_b_busy_passive_test extends axi_read_mode_b_busy_lag_test;
        `uvm_component_utils(axi_read_mode_b_busy_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            watch_passive = 1;
        endfunction
    endclass : axi_read_mode_b_busy_passive_test

    // A passive Mode B agent watches the port beside the slave under test.
    class axi_read_mode_b_passive_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            watch_passive = 1;
        endfunction
    endclass : axi_read_mode_b_passive_test

    // The slave answers SLVERR on a quarter of the addresses, and the model
    // lane must replay each beat's rresp.
    class axi_read_mode_b_slverr_test extends axi_read_mode_b_test;
        `uvm_component_utils(axi_read_mode_b_slverr_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            slverr = 1;
        endfunction
    endclass : axi_read_mode_b_slverr_test

    class axi_read_mode_b_slverr_mismatch_test extends axi_read_mode_b_slverr_test;
        `uvm_component_utils(axi_read_mode_b_slverr_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MISMATCH;
        endfunction
    endclass : axi_read_mode_b_slverr_mismatch_test

    // --------------------------------------------------------------- axi_write

    // Sends a prepared list of bursts, checks each response as axw_seq does,
    // except that with allow_empty set a response with no beats, as a
    // master with both lanes dead returns, is only counted, and applies them
    // to model in the order sent.
    class axw_list_seq extends axw_seq;
        axw_item_t   list[$];
        // The master sends every burst with ID 0, so each comes back with
        // ID 0.
        bit          id_unbound;
        bit          allow_empty;
        int unsigned empties;

        `uvm_object_utils(axw_list_seq)

        function new(string name = "axw_list_seq");
            super.new(name);
        endfunction

        virtual task body();
            axw_item_t copy;
            n = list.size();
            foreach (list[i]) begin
                $cast(copy, list[i].clone());
                if (id_unbound) copy.id = '0;
                sent.push_back(copy);
                waiting.push_back(copy);
                send(list[i]);
            end
            wait_for_writes();
            foreach (sent[i]) model.apply(sent[i]);
        endtask

        virtual function void write_done(axw_item_t rsp);
            int found[$];
            if (!allow_empty || rsp.data.size() != 0) begin
                super.write_done(rsp);
                return;
            end
            found = waiting.find_first_index(w) with (w.id === rsp.id && w.addr === rsp.addr);
            if (found.size() != 0) waiting.delete(found[0]);
            responses.push_back(rsp);
            empties++;
        endfunction
    endclass : axw_list_seq

    typedef axi_write_master_driver #(lb_axw_addr_t, lb_axw_data_t, lb_axw_strb_t, lb_axw_awuser_t, lb_axw_wuser_t,
                                      lb_axw_buser_t, lb_axw_id_t) axw_master_t;

    // A master whose W beats lead their AW: each burst joins the W queue and
    // its AW goes out one to four clocks later. Single lane.
    class axw_w_first_master extends axw_master_t;
        `uvm_component_utils(axw_w_first_master)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected virtual task run_aw();
            open_t b;
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
                b = new_open(req);
                w_queue.push_back(b);
                pending[A2C_DUT_LANE][id_key_t'(b.rsp[A2C_DUT_LANE].id)].push_back(b);
                outstanding[A2C_DUT_LANE]++;
                repeat ($urandom_range(4, 1)) begin
                    drive_awvalid(1'b0);
                    cfg.clk_vif.drive_edge();
                end
                lane[A2C_DUT_LANE].awvalid <= 1'b1;
                lane[A2C_DUT_LANE].awid    <= b.rsp[A2C_DUT_LANE].id;
                lane[A2C_DUT_LANE].awaddr  <= lb_axw_addr_t'(req.addr);
                lane[A2C_DUT_LANE].awlen   <= req.len;
                lane[A2C_DUT_LANE].awsize  <= req.size;
                lane[A2C_DUT_LANE].awburst <= req.burst;
                lane[A2C_DUT_LANE].awuser  <= req.awuser;
                wait_aw(b);
                seq_item_port.item_done();
            end
        endtask
    endclass : axw_w_first_master

    // The master, with its books open to the test.
    class axw_master_probe extends axw_master_t;
        `uvm_component_utils(axw_master_probe)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function int unsigned left(int l);
            return outstanding[l];
        endfunction

        function int unsigned queued(int l);
            int unsigned n = 0;
            id_key_t     k;
            if (pending[l].first(k)) do n += pending[l][k].size(); while (pending[l].next(k));
            return n;
        endfunction

        function bit is_dead(int l);
            return dead[l];
        endfunction

        function realtime died(int l);
            return died_at[l];
        endfunction

        function void kill_again(int l);
            declare_dead(a2c_lane_e'(l), "kill_again", $realtime);
        endfunction

        // With late_take set, the Bs of each falling edge are taken after
        // the other processes of that time step have run, so a death
        // run_w() declares on the edge comes first.
        bit late_take;

        protected virtual task b_sampled();
            if (late_take) repeat (10) #0;
        endtask
    endclass : axw_master_probe

    // An axi_write slave whose bursts are one beat each, answered with B at
    // clocks the test sets. It takes the first aw_limit AWs and w_limit W
    // beats, or every one when the limit is negative. Unless mute, the AW,
    // or with anchor_w the W beat, of burst anchor sets the clocks of the
    // B of bursts 0 to offs.size() - 1, offs[n] after it, and each later
    // burst gets its B 2 clocks after it has both its AW and its W beat.
    // With lead set, the anchor of lead, the other lane's script, sets them
    // instead, and an offs entry of 0 leaves its burst unanswered.
    class axw_script_slave extends uvm_component;
        axw_vif_t          vif;
        virtual a2c_clk_if clk_vif;
        bit                mute;
        int                aw_limit = -1;
        int                w_limit = -1;
        int                anchor = -1;
        bit                anchor_w;
        int unsigned       offs[$];
        axw_script_slave   lead;
        // The clock of this script's anchor, or 0 before it.
        longint            anchored_at;
        // Per burst: its AW ID, the clocks its AW and its W beat transferred
        // on, or 0, the clock its B goes out on, or 0 until set, and when
        // the B transferred, or 0.
        lb_axw_id_t        ids[$];
        longint            aw_at[int unsigned];
        longint            w_at[int unsigned];
        longint            due[int unsigned];
        realtime           done_at[int unsigned];

        `uvm_component_utils(axw_script_slave)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // Called as burst n gets its AW or its W beat at clock now.
        protected function void arrived(int unsigned n, longint now, bit is_w);
            if (n == anchor && is_w == anchor_w) begin
                anchored_at = now;
                foreach (offs[i]) due[i] = now + offs[i];
            end
            if (n >= offs.size() && aw_at.exists(n) && w_at.exists(n)) due[n] = now + 2;
        endfunction

        virtual task run_phase(uvm_phase phase);
            int          cur = -1;
            longint      now = 0;
            int unsigned ws = 0;
            bit          led;
            vif.awready <= 1'b0;
            vif.wready  <= 1'b0;
            vif.bvalid  <= 1'b0;
            vif.bresp   <= '0;
            vif.buser   <= '0;
            clk_vif.wait_reset_release();
            clk_vif.drive_edge();
            forever begin
                vif.awready <= aw_limit < 0 || ids.size() < aw_limit;
                vif.wready  <= w_limit < 0 || ws < w_limit;
                if (lead != null && !led && lead.anchored_at != 0) begin
                    led = 1;
                    foreach (offs[n]) if (offs[n] != 0) due[n] = lead.anchored_at + offs[n];
                end
                if (cur < 0 && !mute) begin
                    foreach (ids[n]) begin
                        if (!done_at.exists(n) && due.exists(n) && due[n] <= now + 1) begin
                            cur = n;
                            break;
                        end
                    end
                end
                vif.bvalid <= cur >= 0;
                if (cur >= 0) vif.bid <= ids[cur];
                clk_vif.sample_edge();
                now++;
                if (cur >= 0 && vif.bready === 1'b1) begin
                    done_at[cur] = $realtime;
                    cur = -1;
                end
                if (vif.awvalid === 1'b1 && vif.awready === 1'b1) begin
                    ids.push_back(vif.awid);
                    aw_at[ids.size() - 1] = now;
                    arrived(ids.size() - 1, now, 0);
                end
                if (vif.wvalid === 1'b1 && vif.wready === 1'b1) begin
                    w_at[ws] = now;
                    arrived(ws++, now, 1);
                end
                clk_vif.drive_edge();
            end
        endtask
    endclass : axw_script_slave

    // Mode B on an axi_write port whose DUT masters it: the agent is the
    // slave, and only its DUT lane writes the memory. The model lane's
    // master sends each burst's W before its AW. The port runs on clk2.
    class axi_write_mode_b_test extends lb_axi_mode_b #(axw_agent_t, axw_item_t, axw_config_t, axw_vif_t);
        axi_write_mem_t mem;
        // A2C_SRC: the model lane's slave's memory.
        axi_write_mem_t model_mem;
        axw_list_seq    seqs[2];
        int unsigned    peak[2];
        // A2C_SRC: the clocks one lane's AW, or W beat, transferred and the
        // other's did not.
        int unsigned    aw_apart;
        int unsigned    w_apart;
        // The model lane's W bursts that started before their AW transferred.
        int unsigned    w_led;
        // A2C_DST: two IDs, so two bursts of one ID wait for B at once, and
        // SLVERR on half the addresses, so a B answering the wrong one of
        // them carries the wrong bresp.
        bit             same_id;
        // The most DUT lane bursts of one ID waiting for B at once.
        int unsigned    same_peak;
        // Per lane: the AWs, the W beats and the last W beats taken.
        int unsigned    aws[2];
        int unsigned    ws[2];
        int unsigned    w_ends[2];
        // AXB_ORDER_A and AXB_ORDER_W: each lane's slave.
        axw_script_slave scripts[2];

        `uvm_component_utils(axi_write_mode_b_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            port     = "axw";
            clk_name = "clk2";
        endfunction

        virtual function axw_item_t new_item(int unsigned i);
            axw_item_t it = axw_item_t::type_id::create($sformatf("it%0d", i));
            // IDs in turn, so the bursts a reorder can swap often share their
            // arrival index within their IDs, and only the ID tells them apart.
            if (!it.randomize() with { len dist {[0:7] :/ 90, [8:31] :/ 10}; id == i % (same_id ? 2 : 4); }) begin
                `uvm_fatal("LB_RAND", "axi_write item randomize failed")
            end
            it.gap = 0;
            return it;
        endfunction

        virtual function void configure();
            mem = axi_write_mem_t::type_id::create("mem");
            if (role == A2C_DST) begin
                agent_cfg.mem            = mem;
                agent_cfg.reorder        = 1'b1;
                agent_cfg.resp_delay_max = 8;
                agent_cfg.awready_pct    = 70;
                agent_cfg.wready_pct     = 70;
                agent_cfg.error_ranges.push_back('{lo: 64'h3000, hi: 64'h30ff});
                if (same_id) agent_cfg.error_ranges.push_back('{lo: 64'h0, hi: 64'h7fff});
                peer_cfg.max_outstanding       = 4;
                peer_cfg.bready_pct            = 70;
                model_peer_cfg.max_outstanding = 4;
                model_peer_cfg.bready_pct      = 70;
                axw_master_t::type_id::set_inst_override(axw_w_first_master::get_type(), "model_peer.drv", this);
                return;
            end
            agent_cfg.max_outstanding = 4;
            agent_cfg.bready_pct      = 70;
            axw_master_t::type_id::set_inst_override(axw_master_probe::get_type(), "agent.drv", this);
            model_mem = axi_write_mem_t::type_id::create("model_mem");
            peer_cfg.mem                  = mem;
            model_peer_cfg.mem            = model_mem;
            peer_cfg.reorder              = 1'b1;
            model_peer_cfg.reorder        = 1'b1;
            // Long B delays keep several bursts waiting for B at once, so the
            // two slaves' reorder picks part the lanes' orders.
            peer_cfg.resp_delay_max       = 32;
            model_peer_cfg.resp_delay_max = 32;
            peer_cfg.awready_pct          = 70;
            model_peer_cfg.awready_pct    = 70;
            peer_cfg.wready_pct           = 70;
            model_peer_cfg.wready_pct     = 70;
            for (int l = 0; l < 2; l++) begin
                frozen[l].push_back(lb_frozen::of("the AW channel"));
                frozen[l].push_back(lb_frozen::of("the W channel"));
            end
            if (variant inside {AXB_MUTE, AXB_LONE_STALL, AXB_LONE_OFF}) begin
                model_peer_cfg.resp_delay_min = 1000000;
                model_peer_cfg.resp_delay_max = 1000000;
            end
            // Scripts serve both lanes, and the peers only watch.
            if (variant inside {AXB_ORDER_A, AXB_ORDER_W}) begin
                agent_cfg.bready_pct      = 100;
                peer_cfg.is_active        = UVM_PASSIVE;
                model_peer_cfg.is_active  = UVM_PASSIVE;
            end
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!(variant inside {AXB_ORDER_A, AXB_ORDER_W})) return;
            for (int l = 0; l < 2; l++) begin
                scripts[l] = axw_script_slave::type_id::create($sformatf("script%0d", l), this);
                scripts[l].vif     = (l == A2C_DUT_LANE) ? vif : model_vif;
                scripts[l].clk_vif = clk_vif;
            end
            scripts[A2C_DUT_LANE].anchor   = 3;
            scripts[A2C_DUT_LANE].anchor_w = (variant == AXB_ORDER_W);
            scripts[A2C_DUT_LANE].offs     = '{lane_skew - 10, lane_skew, lane_skew + 1, lane_skew + 5};
            scripts[A2C_MODEL_LANE].mute   = (order_model == 0);
            scripts[A2C_MODEL_LANE].lead   = scripts[A2C_DUT_LANE];
            scripts[A2C_MODEL_LANE].offs   = (order_model == 1) ? '{lane_skew, 0, 0} : '{lane_skew - 10, lane_skew, 0};
            if (variant == AXB_ORDER_A) scripts[A2C_MODEL_LANE].aw_limit = 3;
            else scripts[A2C_MODEL_LANE].w_limit = 3;
        endfunction

        // A2C_DST: the model lane's burst carries other data on its first
        // beat. A2C_SRC: the model lane's slave answers SLVERR at the first
        // byte the burst writes, so every burst with a beat that starts there
        // gets another bresp.
        virtual function void mismatch();
            want_errors = 0;
            if (role == A2C_DST) begin
                model_items[mismatch_at].data[0] = ~model_items[mismatch_at].data[0];
                want_errors = 1;
            end else begin
                axw_item_t    it = items[mismatch_at];
                axw_ref_model r = new();
                bit [63:0]    first;
                int unsigned  count;
                axi_beat(64'(it.addr), it.size, it.len, it.burst, 0, first, count);
                model_peer_cfg.error_ranges.push_back('{lo: first, hi: first});
                r.error_ranges = model_peer_cfg.error_ranges;
                foreach (items[i]) want_errors += (r.expected_resp(items[i]) != AXI_OKAY);
            end
            want_text.push_back($sformatf("uvm_test_top.agent.model_cmp: pair "));
            want_text.push_back($sformatf(" key %0h: DUT ", items[mismatch_at].id));
        endfunction

        virtual function void one_lane_text(a2c_lane_e lane);
            axw_item_t it = items[n_items];
            string     head = "uvm_test_top.agent.drv: the DUT lane answered ";
            string     tail = ", and the model lane never ended that burst";
            if (lane == A2C_MODEL_LANE) begin
                it   = model_items[n_items];
                head = "uvm_test_top.agent.drv: the model lane issued 1 AWs the DUT lane never issued, the first ";
                tail = "";
            end
            want_text.push_back(head);
            want_text.push_back($sformatf(", AW %0d of ID %0h%s", dut_count(it.id), it.id, tail));
        endfunction

        virtual function string held_text(axw_item_t it, int unsigned n);
            return $sformatf(", AW %0d of ID %0h, whose burst it has not ended, with ", n, it.id);
        endfunction

        protected function int unsigned dut_count(lb_axw_id_t id);
            int unsigned n = 0;
            for (int unsigned i = 0; i <= n_items; i++) n += ((i < n_items ? items[i].id : id) === id);
            return n;
        endfunction

        virtual function a2c_replay_log_base replay();
            axw_agent_t::slave_t s;
            $cast(s, agent.drv);
            return s.replay;
        endfunction

        // Both lanes' slaves answer SLVERR at the first byte
        // items[late_at] writes and at the first byte items[late_at + 2]
        // writes, and items[late_at + 1] writes elsewhere, so a B credited to
        // the wrong one of the three carries the wrong bresp. The late burst
        // expects SLVERR, which a response the lane given up on never filled
        // in does not carry.
        virtual function void tell_apart();
            axw_ref_model r = new();
            int unsigned  keep = int'(items[late_at + 1].id);
            for (int unsigned i = late_at; i < late_at + 3; i += 2) begin
                bit [63:0]   first;
                int unsigned count;
                axi_beat(64'(items[i].addr), items[i].size, items[i].len, items[i].burst, 0, first, count);
                peer_cfg.error_ranges.push_back('{lo: first, hi: first});
                model_peer_cfg.error_ranges.push_back('{lo: first, hi: first});
            end
            r.error_ranges = peer_cfg.error_ranges;
            for (int unsigned t = 0; r.expected_resp(items[late_at + 1]) != AXI_OKAY; t++) begin
                if (t == 100 || !items[late_at + 1].randomize() with { len <= 3; id == keep; }) begin
                    `uvm_fatal("LB_RAND", "tell_apart randomize failed")
                end
            end
        endfunction

        virtual function void lane_delay(a2c_lane_e l, int unsigned n);
            axw_config_t c = (l == A2C_DUT_LANE) ? peer_cfg : model_peer_cfg;
            c.resp_delay_min = n;
            c.resp_delay_max = (n != 0) ? n : 32;
        endfunction

        virtual function void lane_accept(bit addr, bit data);
            model_peer_cfg.awready_pct = addr ? 70 : 0;
            model_peer_cfg.wready_pct  = data ? 70 : 0;
        endfunction

        virtual function int unsigned addr_count(a2c_lane_e l);
            return aws[l];
        endfunction

        // The write slave draws a burst's delay once it has the AW and the
        // last W beat, and the bursts end in AW order.
        virtual function int unsigned drawn_count(a2c_lane_e l);
            return (aws[l] < w_ends[l]) ? aws[l] : w_ends[l];
        endfunction

        virtual function int unsigned data_count(a2c_lane_e l);
            return ws[l];
        endfunction

        virtual function string done_word();
            return "the B of ";
        endfunction

        protected function axw_master_probe probe();
            $cast(probe, agent.drv);
        endfunction

        virtual function int unsigned left(a2c_lane_e l);
            return probe().left(l);
        endfunction

        virtual function int unsigned queued(a2c_lane_e l);
            return probe().queued(l);
        endfunction

        virtual function int unsigned returned();
            return seqs[A2C_DUT_LANE].responses.size();
        endfunction

        virtual function int unsigned empties();
            return seqs[A2C_DUT_LANE].empties;
        endfunction

        virtual function bit is_dead(a2c_lane_e l);
            return probe().is_dead(l);
        endfunction

        virtual function realtime died(a2c_lane_e l);
            return probe().died(l);
        endfunction

        virtual function void kill_again(a2c_lane_e l);
            probe().kill_again(l);
        endfunction

        virtual function axw_item_t response(int unsigned n);
            return seqs[A2C_DUT_LANE].responses[n];
        endfunction

        virtual function realtime answered_at(int unsigned n, a2c_lane_e l = A2C_DUT_LANE);
            return scripts[l].done_at.exists(n) ? scripts[l].done_at[n] : 0;
        endfunction

        virtual task send(axw_agent_t src, axw_item_t list[$], a2c_lane_e lane);
            axw_list_seq seq = axw_list_seq::type_id::create($sformatf("seq%0d", lane));
            seq.list               = list;
            seq.id_unbound         = id_unbound;
            seq.allow_empty        = (variant == AXB_BOTH_DEAD);
            seq.model              = new();
            seq.model.error_ranges = (role == A2C_DST) ? agent_cfg.error_ranges : peer_cfg.error_ranges;
            seqs[lane] = seq;
            seq.start(src.sqr);
            done[lane] = 1;
        endtask

        // As A2C_SRC an AW, or a W beat, may go out on a lane only once both
        // lanes took the one before, until a lane dies, and a dead lane's
        // master pins stay as lb_frozen and check_ready() require.
        virtual task watch();
            axw_vif_t    v[2];
            int unsigned w_bursts[2];
            bit          w_open[2];
            int unsigned open[2];
            bit          aw_hs[2];
            bit          w_hs[2];
            int unsigned by_id[int unsigned];
            v[A2C_DUT_LANE]   = vif;
            v[A2C_MODEL_LANE] = model_vif;
            forever begin
                clk_vif.sample_edge();
                for (int l = 0; l < 2; l++) begin
                    if (role == A2C_SRC && !dies() && v[l].awvalid === 1'b1 && aws[l] > aws[1 - l]) begin
                        `uvm_error("LB_MODE_B", $sformatf("AW %0d went out on the %s lane before the other lane took AW %0d", aws[l] + 1,
                                                          a2c_lane_name(a2c_lane_e'(l)), aws[l]))
                    end
                    if (role == A2C_SRC && !dies() && v[l].wvalid === 1'b1 && ws[l] > ws[1 - l]) begin
                        `uvm_error("LB_MODE_B", $sformatf("W beat %0d went out on the %s lane before the other lane took beat %0d", ws[l] + 1,
                                                          a2c_lane_name(a2c_lane_e'(l)), ws[l]))
                    end
                    if (role == A2C_SRC && skews()) begin
                        frozen[l][0].sample(is_dead(a2c_lane_e'(l)), died(a2c_lane_e'(l)), v[l].awvalid, v[l].awready,
                                            {v[l].awid, v[l].awaddr, v[l].awlen, v[l].awsize, v[l].awburst, v[l].awuser});
                        frozen[l][1].sample(is_dead(a2c_lane_e'(l)), died(a2c_lane_e'(l)), v[l].wvalid, v[l].wready,
                                            {v[l].wid, v[l].wdata, v[l].wstrb, v[l].wlast, v[l].wuser});
                        check_ready(a2c_lane_e'(l), v[l].bready, "bready");
                        note_death();
                    end
                    if (v[l].wvalid === 1'b1 && !w_open[l]) begin
                        w_open[l] = 1;
                        w_bursts[l]++;
                        if (l == A2C_MODEL_LANE && w_bursts[l] > aws[l]) w_led++;
                    end
                    aw_hs[l] = v[l].awvalid === 1'b1 && v[l].awready === 1'b1;
                    w_hs[l]  = v[l].wvalid === 1'b1 && v[l].wready === 1'b1;
                end
                aw_apart += (aw_hs[0] != aw_hs[1]);
                w_apart  += (w_hs[0] != w_hs[1]);
                for (int l = 0; l < 2; l++) begin
                    if (w_hs[l]) begin
                        ws[l]++;
                        if (v[l].wlast === 1'b1) begin
                            w_open[l] = 0;
                            w_ends[l]++;
                        end
                    end
                    if (v[l].bvalid === 1'b1 && v[l].bready === 1'b1) begin
                        open[l]--;
                        note_done(l, int'(v[l].bid));
                        if (l == A2C_DUT_LANE) by_id[int'(v[l].bid)]--;
                    end
                    if (aw_hs[l]) begin
                        aws[l]++;
                        open[l]++;
                        if (l == A2C_DUT_LANE) begin
                            int unsigned id = int'(v[l].awid);
                            if (!by_id.exists(id)) by_id[id] = 0;
                            by_id[id]++;
                            if (by_id[id] > same_peak) same_peak = by_id[id];
                        end
                    end
                    if (open[l] > peak[l]) peak[l] = open[l];
                end
            end
        endtask

        // Only the DUT lane wrote the memory: it holds exactly what the DUT
        // lane's bursts write, whatever the model lane's carried.
        virtual function void check_family();
            int unsigned compared;
            `uvm_info("LB_STATS", $sformatf("at most %0d and %0d bursts outstanding, %0d of one ID on the DUT lane; %0d and %0d clocks with an AW or a W beat on one lane only; %0d model lane W bursts ahead of their AW",
                                            peak[A2C_DUT_LANE], peak[A2C_MODEL_LANE], same_peak, aw_apart, w_apart, w_led), UVM_NONE)
            if (same_id && same_peak < 2) `uvm_error("LB_MODE_B", "no two bursts of one ID waited for B at once, so the same-ID order went untested")
            if (variant inside {AXB_MATCH, AXB_MISMATCH, AXB_DUT_EXTRA, AXB_MODEL_EXTRA} && (peak[A2C_DUT_LANE] != 4 || peak[A2C_MODEL_LANE] != 4)) begin
                `uvm_error("LB_MODE_B", $sformatf("max_outstanding is 4, but at most %0d and %0d bursts were outstanding",
                                                  peak[A2C_DUT_LANE], peak[A2C_MODEL_LANE]))
            end
            if (role == A2C_DST) begin
                if (w_led == 0) `uvm_error("LB_MODE_B", "no model lane W burst started before its AW, so W before AW went untested")
                if (variant inside {AXB_BUSY, AXB_SKIP_CUT}) return;
                compared = seqs[A2C_DUT_LANE].model.check(mem, "LB_MODE_B");
                `uvm_info("LB_MEM", $sformatf("%0d bytes compared with the DUT lane's bursts", compared), UVM_NONE)
                return;
            end
            if (seqs[A2C_DUT_LANE].responses.size() != items.size()) begin
                `uvm_error("LB_MODE_B", $sformatf("%0d bursts sent, %0d returned", items.size(), seqs[A2C_DUT_LANE].responses.size()))
            end
            if (aw_apart == 0 || w_apart == 0) begin
                `uvm_error("LB_MODE_B", "every AW, or every W beat, transferred on both lanes on one clock, so the per-lane handshake went untested")
            end
            // The scripts keep no memory.
            if (variant inside {AXB_ORDER_A, AXB_ORDER_W}) return;
            compared = seqs[A2C_DUT_LANE].model.check(mem, "LB_MODE_B");
            if (variant == AXB_MATCH) compared += seqs[A2C_DUT_LANE].model.check(model_mem, "LB_MODE_B");
            `uvm_info("LB_MEM", $sformatf("%0d bytes compared on the two lanes' memories", compared), UVM_NONE)
        endfunction
    endclass : axi_write_mode_b_test

    class axi_write_mode_b_mismatch_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MISMATCH;
        endfunction
    endclass : axi_write_mode_b_mismatch_test

    class axi_write_mode_b_dut_extra_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_dut_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DUT_EXTRA;
        endfunction
    endclass : axi_write_mode_b_dut_extra_test

    class axi_write_mode_b_model_extra_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_model_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MODEL_EXTRA;
        endfunction
    endclass : axi_write_mode_b_model_extra_test

    // As axi_write_mode_b_model_extra_test with a death on the first clock:
    // every report of the slave names it.
    class axi_write_mode_b_model_extra_dead_test extends axi_write_mode_b_model_extra_test;
        `uvm_component_utils(axi_write_mode_b_model_extra_dead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_early = 1;
        endfunction
    endclass : axi_write_mode_b_model_extra_dead_test

    class axi_write_mode_b_busy_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_busy_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_BUSY;
        endfunction
    endclass : axi_write_mode_b_busy_test

    // As axi_write_mode_b_busy_test with the model lane stalled across the
    // cut, so the DUT lane completes bursts past the cut before the model
    // lane reaches it.
    class axi_write_mode_b_busy_lag_test extends axi_write_mode_b_busy_test;
        `uvm_component_utils(axi_write_mode_b_busy_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_stall = 80;
        endfunction

        int unsigned kept;

        virtual function void stall_model(bit stall);
            if (stall) kept = model_peer_cfg.bready_pct;
            model_peer_cfg.bready_pct = stall ? 0 : kept;
        endfunction
    endclass : axi_write_mode_b_busy_lag_test

    // The agent is the master; each lane's slave reorders on its own and
    // has its own memory.
    class axi_write_mode_b_master_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_master_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            role = A2C_SRC;
        endfunction
    endclass : axi_write_mode_b_master_test

    class axi_write_mode_b_master_mismatch_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_mismatch_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MISMATCH;
        endfunction
    endclass : axi_write_mode_b_master_mismatch_test

    // The model lane's master sends some bursts of different IDs in the
    // other order, so the model lane must find each pick by its ID and its
    // place among the bursts of that ID.
    class axi_write_mode_b_cross_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_cross_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_CROSS;
        endfunction
    endclass : axi_write_mode_b_cross_test

    // The model lane's master sends its next AW only after the last
    // response, and the DUT lane reorders: the model lane holds the first
    // reordered pick, whose AW its master waits to send, and the slave
    // reports the pick and the AWs behind it as a model defect.
    class axi_write_mode_b_serial_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_serial_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_SERIAL;
        endfunction
    endclass : axi_write_mode_b_serial_test

    // The DUT lane's master sends one burst more mid-run, among the others:
    // the model lane holds that pick, with its later AWs behind it, until
    // the end.
    class axi_write_mode_b_dut_mid_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_dut_mid_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DUT_MID;
        endfunction
    endclass : axi_write_mode_b_dut_mid_test

    // Both masters keep sending, and the model lane's skips one burst
    // mid-run. The drain cuts the run past that burst, and the slave still
    // reports the held pick, which the cut keeps.
    class axi_write_mode_b_skip_cut_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_skip_cut_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_SKIP_CUT;
        endfunction
    endclass : axi_write_mode_b_skip_cut_test

    // The agent is the master of a port that binds no id_t: it sends every
    // burst on both lanes with ID 0.
    class axi_write_mode_b_master_id_unbound_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_id_unbound_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            id_unbound = 1;
        endfunction
    endclass : axi_write_mode_b_master_id_unbound_test

    // The agent is the master, and the model lane's slave never answers.
    // The model lane dies lane_skew clocks after the DUT lane's first B, and
    // the DUT lane serves the rest.
    class axi_write_mode_b_master_mute_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_mute_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MUTE;
        endfunction
    endclass : axi_write_mode_b_master_mute_test

    // The agent is the master, and the model lane's slave takes no AW. The
    // model lane dies lane_skew clocks after the DUT lane took the first,
    // with its awvalid held, and the DUT lane serves every burst.
    class axi_write_mode_b_master_deaf_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_deaf_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DEAF;
        endfunction
    endclass : axi_write_mode_b_master_deaf_test

    // The agent is the master, and the model lane's slave takes AWs and no W
    // beat. The model lane dies lane_skew clocks after the DUT lane took the
    // first W beat, with its wvalid held, and the DUT lane serves every
    // burst.
    class axi_write_mode_b_master_deaf_w_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_deaf_w_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DEAF_W;
        endfunction
    endclass : axi_write_mode_b_master_deaf_w_test

    // The DUT lane answers one burst past the bound and dies, and the model
    // lane serves that burst and the rest.
    class axi_write_mode_b_master_dut_late_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_dut_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_DUT_LATE;
        endfunction
    endclass : axi_write_mode_b_master_dut_late_test

    // The model lane answers one burst and the next past the bound. It dies
    // on the first, and raises no second A2C_SKEW error on the next.
    class axi_write_mode_b_master_model_late_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_model_late_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_MODEL_LATE;
        endfunction
    endclass : axi_write_mode_b_master_model_late_test

    // The model lane's slave stops taking AWs and W beats for a while. The
    // model lane dies on the AW or W beat it missed, and takes each of them
    // once, with its valid low after it, when its slave resumes.
    class axi_write_mode_b_master_stall_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_STALL;
        endfunction
    endclass : axi_write_mode_b_master_stall_test

    // The model lane answers every burst lag clocks late, under the bound,
    // so no burst is an A2C_SKEW error.
    class axi_write_mode_b_master_lag_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_lag_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_LAG;
        endfunction
    endclass : axi_write_mode_b_master_lag_test

    // As the lag test with lane_skew_cycles 0, which turns the bound off.
    class axi_write_mode_b_master_skew_off_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_skew_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_SKEW_OFF;
        endfunction
    endclass : axi_write_mode_b_master_skew_off_test

    // The model lane's slave takes the AW and some W beats of one burst,
    // stops taking W beats past the bound and then takes them again. The
    // model lane dies holding half a burst, takes the beat its wvalid held
    // once when its slave resumes, and the DUT lane serves every burst.
    class axi_write_mode_b_master_half_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_half_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_HALF;
        endfunction
    endclass : axi_write_mode_b_master_half_test

    // The model lane takes no AW and dies, and later the DUT lane's slave
    // stops answering, so the DUT lane dies too and the sequence gets the
    // rest of its bursts back with no beats.
    class axi_write_mode_b_master_both_dead_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_both_dead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_BOTH_DEAD;
        endfunction
    endclass : axi_write_mode_b_master_both_dead_test

    // The model lane dies on an AW while the DUT lane returns the B of three
    // bursts of one ID around the death, and the sequence must get them
    // back in order.
    class axi_write_mode_b_master_order_aw_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_order_aw_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_ORDER_A;
        endfunction
    endclass : axi_write_mode_b_master_order_aw_test

    // As the order_aw test, with the model lane's slave returning the B of
    // burst 0 on the clock of the death, on which the DUT lane completes
    // burst 1.
    class axi_write_mode_b_master_order_aw_m0_test extends axi_write_mode_b_master_order_aw_test;
        `uvm_component_utils(axi_write_mode_b_master_order_aw_m0_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            order_model = 1;
        endfunction
    endclass : axi_write_mode_b_master_order_aw_m0_test

    // As the order_aw test, with both lanes completing burst 1 on the clock
    // of the death.
    class axi_write_mode_b_master_order_aw_both_test extends axi_write_mode_b_master_order_aw_test;
        `uvm_component_utils(axi_write_mode_b_master_order_aw_both_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            order_model = 2;
        endfunction
    endclass : axi_write_mode_b_master_order_aw_both_test

    // As the order_aw test, with the death on a W beat.
    class axi_write_mode_b_master_order_w_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_order_w_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_ORDER_W;
        endfunction
    endclass : axi_write_mode_b_master_order_w_test

    // As the order_aw_m0 test, with the death on a W beat. Xcelium and VCS
    // both take the Bs of the death's edge before run_w() declares the
    // death, so the master takes them late, which gives the other order.
    class axi_write_mode_b_master_order_w_m0_test extends axi_write_mode_b_master_order_w_test;
        `uvm_component_utils(axi_write_mode_b_master_order_w_m0_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            order_model = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            probe().late_take = 1;
        endfunction
    endclass : axi_write_mode_b_master_order_w_m0_test

    // As the order_aw_both test, with the death on a W beat and the Bs
    // taken late, as in the order_w_m0 test.
    class axi_write_mode_b_master_order_w_both_test extends axi_write_mode_b_master_order_w_m0_test;
        `uvm_component_utils(axi_write_mode_b_master_order_w_both_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            order_model = 2;
        endfunction
    endclass : axi_write_mode_b_master_order_w_both_test

    // The model lane dies, and the DUT lane, alone, then waits lane_skew +
    // 150 clocks for four Bs, under the default lone lane bound.
    class axi_write_mode_b_master_lone_stall_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_lone_stall_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_LONE_STALL;
        endfunction
    endclass : axi_write_mode_b_master_lone_stall_test

    // As the lone stall test with a2c_lone_lane_cycles 0, which turns the
    // rule off.
    class axi_write_mode_b_master_lone_off_test extends axi_write_mode_b_master_test;
        `uvm_component_utils(axi_write_mode_b_master_lone_off_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant = AXB_LONE_OFF;
        endfunction
    endclass : axi_write_mode_b_master_lone_off_test

    // The DUT lane's master sends one burst the model lane's never does,
    // and 20 clocks into the drain a master elsewhere declares the model
    // lane dead: the drain still waits to its deadline, and its A2C_DRAIN
    // report names the death. The slave held the pick before the death, so
    // its report of the pick names none.
    class axi_write_mode_b_dead_drain_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_dead_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant    = AXB_DEAD_DRAIN;
            dead_after = 20;
        endfunction
    endclass : axi_write_mode_b_dead_drain_test

    // As axi_write_mode_b_dead_drain_test with the death on the first
    // clock, before the pick, so the report of the pick names it too.
    class axi_write_mode_b_dead_early_drain_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_dead_early_drain_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            variant    = AXB_DEAD_DRAIN;
            dead_early = 1;
        endfunction
    endclass : axi_write_mode_b_dead_early_drain_test

    // As axi_write_mode_b_busy_lag_test, and a master elsewhere declares the
    // model lane dead while the lanes catch up with the cut. The drain ends
    // once they reach it, as without the death. The death came after the
    // cut, so the A2C_CUT report does not name it.
    class axi_write_mode_b_busy_dead_test extends axi_write_mode_b_busy_lag_test;
        `uvm_component_utils(axi_write_mode_b_busy_dead_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_in_catchup = 1;
        endfunction
    endclass : axi_write_mode_b_busy_dead_test

    // As axi_write_mode_b_busy_lag_test with a death on the first clock, so
    // the A2C_CUT report names it.
    class axi_write_mode_b_busy_dead_early_test extends axi_write_mode_b_busy_lag_test;
        `uvm_component_utils(axi_write_mode_b_busy_dead_early_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_early = 1;
        endfunction
    endclass : axi_write_mode_b_busy_dead_early_test

    // As axi_write_mode_b_master_mute_test after a death on another port, so
    // the master's A2C_SKEW report names that death.
    class axi_write_mode_b_master_mute_cascade_test extends axi_write_mode_b_master_mute_test;
        `uvm_component_utils(axi_write_mode_b_master_mute_cascade_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            dead_early = 1;
        endfunction
    endclass : axi_write_mode_b_master_mute_cascade_test

    // A passive Mode B agent watches the port of a master whose model lane
    // dies: its monitors and model_cmp learn of the death, so they raise
    // no A2C_PROTO or A2C_MODEL_CMP error.
    class axi_write_mode_b_master_late_passive_test extends axi_write_mode_b_master_model_late_test;
        `uvm_component_utils(axi_write_mode_b_master_late_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            watch_passive = 1;
        endfunction
    endclass : axi_write_mode_b_master_late_passive_test

    // A passive Mode B agent watches a port the drain cuts: its model_cmp
    // is cut with the slave's, and its monitors learn of the cut.
    class axi_write_mode_b_busy_passive_test extends axi_write_mode_b_busy_lag_test;
        `uvm_component_utils(axi_write_mode_b_busy_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            watch_passive = 1;
        endfunction
    endclass : axi_write_mode_b_busy_passive_test

    // A passive Mode B agent watches the port beside the slave under test.
    class axi_write_mode_b_passive_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            watch_passive = 1;
        endfunction
    endclass : axi_write_mode_b_passive_test

    // Two IDs, so two bursts of one ID wait for B at once, and the reorder
    // must answer the older first.
    class axi_write_mode_b_same_id_test extends axi_write_mode_b_test;
        `uvm_component_utils(axi_write_mode_b_same_id_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            same_id = 1;
        endfunction
    endclass : axi_write_mode_b_same_id_test

    // ------------------------------------------------------------ two ports

    // Two Mode B ports: axw, on clk2, whose agent is the master, and axr, on
    // clk, whose agent is the slave. axw's model lane slave never answers,
    // so the master declares that lane dead early in the run. axr's model
    // lane master starts 50 clocks after the DUT lane's has finished, so it
    // trails at the drop, and the drain must wait for it as if nothing had
    // died: every axr burst is paired, axr's model_cmp is not stopped, and
    // no A2C_DRAIN, A2C_REPLAY or A2C_CUT report is raised.
    //
    // With trail set, axr's DUT lane master starts 10 clocks after axw's
    // DUT lane takes its first B, which axw's model lane never takes, and
    // axr's model lane master sends nothing. axw's lane skew bound is 1000
    // clocks of clk2, so axr's DUT lane records every burst before the
    // master declares axw's model lane dead. axr's two A2C_REPLAY errors,
    // for the records never replayed and the pick the model lane never
    // issued, are dated by events after the model lane began to trail and
    // before its death, and both must name the death.
    class axi_mode_b_two_port_test extends lb_mode_b_base;
        int unsigned       n = 30;
        bit                trail;
        virtual a2c_clk_if clk2_vif;
        axr_agent_t        rd;
        axr_agent_t        rd_peer;
        axr_agent_t        rd_model_peer;
        axw_agent_t        wr;
        axw_agent_t        wr_peer;
        axw_agent_t        wr_model_peer;
        axi_read_mem_t     mem;
        axr_item_t         rd_items[2][$];
        axw_item_t         wr_items[$];
        a2c_error_demoter  peer_open;
        // trail: the DUT lane monitors' bursts, axr's A2C_REPLAY errors, and
        // the time of axw's first B on its DUT lane.
        lb_arrivals#(axr_item_t) rd_arrivals;
        lb_arrivals#(axw_item_t) wr_arrivals;
        lb_recording_demoter     replays;
        realtime                 first_b_at;

        `uvm_component_utils(axi_mode_b_two_port_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_SKEW";
            want_errors = 1;
            want_text.push_back("axw: the model lane has not returned the B of ");
        endfunction

        protected function axr_config_t rd_cfg(string name, string port, a2c_role_e role);
            axr_config_t cfg = axr_config_t::type_id::create(name);
            if (!uvm_config_db#(axr_vif_t)::get(this, "", port, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", port})
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = port;
            return cfg;
        endfunction

        protected function axw_config_t wr_cfg(string name, string port, a2c_role_e role);
            axw_config_t cfg = axw_config_t::type_id::create(name);
            if (!uvm_config_db#(axw_vif_t)::get(this, "", port, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", port})
            cfg.clk_vif   = clk2_vif;
            cfg.role      = role;
            cfg.port_name = port;
            return cfg;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            axr_config_t rc[3];
            axw_config_t wc[3];
            super.build_phase(phase);
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk2", clk2_vif)) `uvm_fatal("LB_CFG", "no virtual a2c_clk_if clk2")
            mem      = axi_read_mem_t::type_id::create("mem");
            mem.fill = A2C_MEM_FILL_RANDOM;
            rc[0] = rd_cfg("rd_cfg", "axr", A2C_DST);
            rc[1] = rd_cfg("rd_peer_cfg", "axr", A2C_SRC);
            rc[2] = rd_cfg("rd_model_peer_cfg", "axr_model", A2C_SRC);
            if (!uvm_config_db#(axr_vif_t)::get(this, "", "axr_model", rc[0].model_vif)) `uvm_fatal("LB_CFG", "no interface axr_model")
            rc[0].mem            = mem;
            rc[0].reorder        = 1'b1;
            rc[0].resp_delay_max = 8;
            rc[0].arready_pct    = 70;
            for (int i = 1; i < 3; i++) begin
                rc[i].max_outstanding = 4;
                rc[i].rready_pct      = 70;
            end
            wc[0] = wr_cfg("wr_cfg", "axw", A2C_SRC);
            wc[1] = wr_cfg("wr_peer_cfg", "axw", A2C_DST);
            wc[2] = wr_cfg("wr_model_peer_cfg", "axw_model", A2C_DST);
            if (!uvm_config_db#(axw_vif_t)::get(this, "", "axw_model", wc[0].model_vif)) `uvm_fatal("LB_CFG", "no interface axw_model")
            wc[0].max_outstanding = 4;
            wc[0].bready_pct      = 70;
            for (int i = 1; i < 3; i++) begin
                wc[i].mem            = axi_write_mem_t::type_id::create($sformatf("wmem%0d", i));
                wc[i].awready_pct    = 70;
                wc[i].wready_pct     = 70;
                wc[i].resp_delay_max = 8;
            end
            wc[2].resp_delay_min = 1000000;
            wc[2].resp_delay_max = 1000000;
            uvm_config_db#(axr_config_t)::set(this, "rd", "cfg", rc[0]);
            uvm_config_db#(axr_config_t)::set(this, "rd_peer", "cfg", rc[1]);
            uvm_config_db#(axr_config_t)::set(this, "rd_model_peer", "cfg", rc[2]);
            uvm_config_db#(axw_config_t)::set(this, "wr", "cfg", wc[0]);
            uvm_config_db#(axw_config_t)::set(this, "wr_peer", "cfg", wc[1]);
            uvm_config_db#(axw_config_t)::set(this, "wr_model_peer", "cfg", wc[2]);
            uvm_config_db#(int unsigned)::set(this, "wr.drv", "a2c_lane_skew_cycles", trail ? 1000 : 100);
            if (trail) begin
                rd_arrivals = lb_arrivals#(axr_item_t)::type_id::create("rd_arrivals", this);
                wr_arrivals = lb_arrivals#(axw_item_t)::type_id::create("wr_arrivals", this);
                replays     = lb_recording_demoter::type_id::create("replays");
                replays.demote_id = "A2C_REPLAY";
                uvm_report_cb::add(null, replays);
            end
            rd            = axr_agent_t::type_id::create("rd", this);
            rd_peer       = axr_agent_t::type_id::create("rd_peer", this);
            rd_model_peer = axr_agent_t::type_id::create("rd_model_peer", this);
            wr            = axw_agent_t::type_id::create("wr", this);
            wr_peer       = axw_agent_t::type_id::create("wr_peer", this);
            wr_model_peer = axw_agent_t::type_id::create("wr_model_peer", this);
            for (int unsigned i = 0; i < n; i++) begin
                axr_item_t r = axr_item_t::type_id::create($sformatf("rd%0d", i));
                axr_item_t m;
                axw_item_t w = axw_item_t::type_id::create($sformatf("wr%0d", i));
                if (!r.randomize() with { len <= 7; } || !w.randomize() with { len <= 7; }) `uvm_fatal("LB_RAND", "two-port randomize failed")
                r.gap = $urandom_range(3, 0);
                w.gap = $urandom_range(3, 0);
                $cast(m, r.clone());
                rd_items[A2C_DUT_LANE].push_back(r);
                rd_items[A2C_MODEL_LANE].push_back(m);
                wr_items.push_back(w);
            end
        endfunction

        // The test's own monitor on axw's model lane is not told of the
        // death, so its end-of-run report of the bursts left open there is
        // demoted.
        virtual function void connect_phase(uvm_phase phase);
            axr_agent_t::slave_t s;
            peer_open = a2c_error_demoter::type_id::create("peer_open");
            peer_open.demote_id   = "A2C_PROTO";
            peer_open.demote_text = "the run ended with";
            uvm_report_cb::add(wr_model_peer.mon, peer_open);
            $cast(s, rd.drv);
            s.replay.drain_quiet_cycles    = 30;
            s.replay.drain_deadline_cycles = trail ? 300 : 3000;
            if (!trail) return;
            rd.mon.ap.connect(rd_arrivals.analysis_export);
            wr.mon.ap.connect(wr_arrivals.analysis_export);
            // As the env marks a counted port, whose counter reports the
            // bursts the model lane never paired.
            rd.model_cmp.counted = 1;
        endfunction

        protected task read(axr_agent_t src, a2c_lane_e lane);
            axr_list_seq seq = axr_list_seq::type_id::create($sformatf("rd_seq%0d", lane));
            seq.list = rd_items[lane];
            seq.mem  = mem;
            seq.start(src.sqr);
        endtask

        protected task write();
            axw_list_seq seq = axw_list_seq::type_id::create("wr_seq");
            seq.list  = wr_items;
            seq.model = new();
            seq.start(wr.sqr);
        endtask

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            if (trail) begin
                fork
                    write();
                    begin
                        wait (wr_arrivals.items.size() != 0);
                        first_b_at = wr_arrivals.at[0];
                        repeat (10) clk_vif.sample_edge();
                        read(rd_peer, A2C_DUT_LANE);
                    end
                join
                phase.drop_objection(this);
                return;
            end
            fork
                read(rd_peer, A2C_DUT_LANE);
                write();
            join
            fork
                begin
                    repeat (50) clk_vif.sample_edge();
                    read(rd_model_peer, A2C_MODEL_LANE);
                end
            join_none
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            string            ids[3] = '{"A2C_DRAIN", "A2C_REPLAY", "A2C_CUT"};
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("axr pairs %0d, axw pairs %0d", rd.model_cmp.get_pairs(), wr.model_cmp.get_pairs()), UVM_NONE)
            if (!wr.model_cmp.stopped()) `uvm_error("LB_MODE_B", "axw's model lane did not die")
            if (trail) begin
                check_trail();
                return;
            end
            if (rd.model_cmp.stopped()) `uvm_error("LB_MODE_B", "axr's model_cmp stopped on axw's death")
            if (rd.model_cmp.get_pairs() != n) `uvm_error("LB_MODE_B", $sformatf("axr's model_cmp paired %0d bursts, expected %0d", rd.model_cmp.get_pairs(), n))
            foreach (ids[i]) if (srv.get_id_count(ids[i]) != 0) `uvm_error("LB_MODE_B", $sformatf("%0d %s reports, expected none", srv.get_id_count(ids[i]), ids[i]))
        endfunction

        protected function void check_trail();
            realtime died = wr.model_cmp.died_at(A2C_MODEL_LANE);
            string   clause = $sformatf("; the model lane of axw (uvm_test_top.wr.drv) began to trail at %0t and was declared dead at %0t (A2C_SKEW), which may be related",
                                        first_b_at, died);
            if (rd_arrivals.items.size() != n || rd_arrivals.at[n - 1] >= died) begin
                `uvm_error("LB_MODE_B", $sformatf("axr's DUT lane completed %0d of %0d bursts before axw's model lane died at %0t, so the reports went untested",
                                                  rd_arrivals.items.size(), n, died))
            end
            if (replays.demoted != 2 || replays.count(clause) != 2) begin
                `uvm_error("LB_MODE_B", $sformatf("expected two A2C_REPLAY errors, each ending '%s': %p", clause, replays.messages))
            end
        endfunction
    endclass : axi_mode_b_two_port_test

    class axi_mode_b_two_port_trail_test extends axi_mode_b_two_port_test;
        `uvm_component_utils(axi_mode_b_two_port_trail_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            trail = 1;
        endfunction
    endclass : axi_mode_b_two_port_trail_test

    // ------------------------------------------------- passive agents alone

    // Builds a passive Mode B agent of AGENT_T named port under parent, on
    // the pin sets pins and pins_model, by default those of port.
    class lb_passive #(type AGENT_T = uvm_agent, type CFG_T = uvm_object, type VIF_T = int);
        static function AGENT_T make(uvm_component parent, string port, a2c_role_e role, virtual a2c_clk_if clk_vif, string pins = "");
            CFG_T cfg = CFG_T::type_id::create({port, "_cfg"});
            if (pins == "") pins = port;
            if (!uvm_config_db#(VIF_T)::get(parent, "", pins, cfg.vif) || !uvm_config_db#(VIF_T)::get(parent, "", {pins, "_model"}, cfg.model_vif)) begin
                `uvm_fatal("LB_CFG", {"no interfaces ", pins, " and ", pins, "_model"})
            end
            cfg.clk_vif   = clk_vif;
            cfg.role      = role;
            cfg.port_name = port;
            cfg.is_active = UVM_PASSIVE;
            uvm_config_db#(CFG_T)::set(parent, port, "cfg", cfg);
            return AGENT_T::type_id::create(port, parent);
        endfunction
    endclass : lb_passive

    // A passive Mode B agent of each family whose passive agents learn of a
    // cut or a death, each on its port with no active agent, as on an
    // internal port of a top design: each raises one A2C_PASSIVE info that
    // names its port and cfg.vif. A passive A2C_SRC agent of pop_ack,
    // req_ack and memory, the families that build a model_cmp in that role,
    // shares each of those ports' pins and raises none, as no active agent
    // of that role would claim the pin set. The two AXI agents' monitors
    // keep the replay log the test gives them in connect_phase, as a
    // hand-written env may.
    class mode_b_unowned_passive_test extends lb_mode_b_base;
        string                ports[9] = '{"pa", "na", "ra", "po", "mem", "er", "apb", "axr", "axw"};
        axr_agent_t           axr;
        axw_agent_t           axw;
        a2c_replay_log #(bit) kept;
        lb_id_texts           notes;

        `uvm_component_utils(mode_b_unowned_passive_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_unowned = 9;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            pa_agent_t  pa;
            na_agent_t  na;
            ra_agent_t  ra;
            po_agent_t  po;
            mem_agent_t mem;
            er_agent_t  er;
            apb_agent_t apb;
            ra_agent_t  ra_src;
            po_agent_t  po_src;
            mem_agent_t mem_src;
            super.build_phase(phase);
            notes    = lb_id_texts::type_id::create("notes");
            notes.id = "A2C_PASSIVE";
            uvm_report_cb::add(null, notes);
            kept = a2c_replay_log#(bit)::type_id::create("kept", this);
            pa   = lb_passive#(pa_agent_t, pa_config_t, pa_vif_t)::make(this, "pa", A2C_DST, clk_vif);
            na   = lb_passive#(na_agent_t, na_config_t, na_vif_t)::make(this, "na", A2C_DST, clk_vif);
            ra   = lb_passive#(ra_agent_t, ra_config_t, ra_vif_t)::make(this, "ra", A2C_DST, clk_vif);
            po   = lb_passive#(po_agent_t, po_config_t, po_vif_t)::make(this, "po", A2C_DST, clk_vif);
            mem  = lb_passive#(mem_agent_t, mem_config_t, mem_vif_t)::make(this, "mem", A2C_DST, clk_vif);
            er   = lb_passive#(er_agent_t, er_config_t, er_vif_t)::make(this, "er", A2C_DST, clk_vif);
            apb  = lb_passive#(apb_agent_t, apb_config_t, apb_vif_t)::make(this, "apb", A2C_DST, clk_vif);
            axr  = lb_passive#(axr_agent_t, axr_config_t, axr_vif_t)::make(this, "axr", A2C_DST, clk_vif);
            axw  = lb_passive#(axw_agent_t, axw_config_t, axw_vif_t)::make(this, "axw", A2C_SRC, clk_vif);
            ra_src  = lb_passive#(ra_agent_t, ra_config_t, ra_vif_t)::make(this, "ra_src", A2C_SRC, clk_vif, "ra");
            po_src  = lb_passive#(po_agent_t, po_config_t, po_vif_t)::make(this, "po_src", A2C_SRC, clk_vif, "po");
            mem_src = lb_passive#(mem_agent_t, mem_config_t, mem_vif_t)::make(this, "mem_src", A2C_SRC, clk_vif, "mem");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            axr.mon.replay       = kept;
            axr.model_mon.replay = kept;
            axw.mon.replay       = kept;
            axw.model_mon.replay = kept;
        endfunction

        virtual function void start_of_simulation_phase(uvm_phase phase);
            if (axr.mon.replay != kept || axr.model_mon.replay != kept || axw.mon.replay != kept || axw.model_mon.replay != kept) begin
                `uvm_error("LB_MODE_B", "a passive AXI agent dropped the replay log the test gave its monitors")
            end
        endfunction

        virtual function void report_phase(uvm_phase phase);
            foreach (ports[i]) begin
                if (notes.count({ports[i], ": no active Mode B agent has the interface instance in this agent's cfg.vif as its own"}) != 1) begin
                    `uvm_error("LB_MODE_B", $sformatf("expected one A2C_PASSIVE info for %s: %p", ports[i], notes.messages))
                end
            end
            `uvm_info("LB_STATS", $sformatf("%p", notes.messages), UVM_NONE)
            super.report_phase(phase);
        endfunction
    endclass : mode_b_unowned_passive_test
