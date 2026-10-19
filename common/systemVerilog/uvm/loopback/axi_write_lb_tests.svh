// axi_write agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef struct packed {
        logic [15:0] a;
    } lb_axw_addr_t;
    typedef struct packed {
        logic [15:0] hi;
        logic [15:0] lo;
    } lb_axw_data_t;
    typedef logic [3:0] lb_axw_strb_t;
    typedef logic [2:0] lb_axw_awuser_t;
    typedef logic [1:0] lb_axw_wuser_t;
    typedef logic [2:0] lb_axw_buser_t;
    typedef logic [1:0] lb_axw_id_t;
    typedef axi_write_agent #(.addr_t(lb_axw_addr_t), .data_t(lb_axw_data_t), .strb_t(lb_axw_strb_t),
                              .awuser_t(lb_axw_awuser_t), .wuser_t(lb_axw_wuser_t), .buser_t(lb_axw_buser_t),
                              .id_t(lb_axw_id_t)) axw_agent_t;
    typedef axw_agent_t::item_t axw_item_t;
    typedef axw_agent_t::config_t axw_config_t;
    typedef axi_write_base_seq #(lb_axw_addr_t, lb_axw_data_t, lb_axw_strb_t, lb_axw_awuser_t, lb_axw_wuser_t,
                                 lb_axw_buser_t, lb_axw_id_t) axw_base_seq_t;
    typedef virtual axi_write_if #(.addr_t(lb_axw_addr_t), .data_t(lb_axw_data_t), .strb_t(lb_axw_strb_t),
                                   .awuser_t(lb_axw_awuser_t), .wuser_t(lb_axw_wuser_t), .buser_t(lb_axw_buser_t),
                                   .id_t(lb_axw_id_t)) axw_vif_t;

    // What the slave's memory must hold after a run of bursts, applied in AW
    // order, the order the slave writes them: each OKAY burst's bytes whose
    // strobe is set. touched holds every byte address a burst's beats
    // covered, strobed or not and SLVERR or not, so check() also proves that
    // no unstrobed byte and no byte of an SLVERR burst was written.
    class axw_ref_model;
        bit [7:0]        bytes[bit [63:0]];
        bit              touched[bit [63:0]];
        axi_addr_range_t error_ranges[$];

        // The response the burst must get.
        function axi_resp_e expected_resp(axw_item_t it);
            bit [63:0]   first;
            int unsigned count;
            foreach (it.data[n]) begin
                axi_beat(64'(it.addr), it.size, it.len, it.burst, n, first, count);
                if (axi_in_error_range(first, error_ranges)) return AXI_SLVERR;
            end
            return AXI_OKAY;
        endfunction

        // Records the bytes a burst covers, and the ones it writes when it
        // gets OKAY.
        function void apply(axw_item_t it);
            bit [63:0]   first;
            int unsigned count;
            bit [31:0]   word;
            bit          writes = (expected_resp(it) == AXI_OKAY);
            foreach (it.data[n]) begin
                axi_beat(64'(it.addr), it.size, it.len, it.burst, n, first, count);
                word = it.data[n];
                for (int unsigned i = 0; i < count; i++) begin
                    int unsigned lane = int'((first + i) % 4);
                    touched[first + i] = 1'b1;
                    if (writes && it.strb[n][lane]) bytes[first + i] = word[8 * lane +: 8];
                end
            end
        endfunction

        // Compares the memory with the model at every touched address and
        // returns the number of bytes compared.
        function int unsigned check(axi_write_mem_t mem, string tag);
            int unsigned compared;
            foreach (touched[a]) begin
                compared++;
                if (bytes.exists(a)) begin
                    if (!mem.exists(a) || mem.read(a) !== bytes[a]) begin
                        `uvm_error(tag, $sformatf("byte 0x%0h: memory %s, expected 0x%02h", a,
                                                  mem.exists(a) ? $sformatf("0x%02h", mem.read(a)) : "unwritten", bytes[a]))
                    end
                end else if (mem.exists(a)) begin
                    `uvm_error(tag, $sformatf("byte 0x%0h: no strobe ever wrote it, but memory holds 0x%02h", a, mem.read(a)))
                end
            end
            return compared;
        endfunction
    endclass : axw_ref_model

    // Sends n bursts and checks each response: its fields and beats against
    // the oldest unanswered burst sent with its ID, since a slave keeps each
    // ID's bursts in order, and its bresp against the error ranges. Every
    // burst goes into the reference model in the order sent. With reuse set,
    // every burst goes out through one item object, randomised again for
    // each send while earlier bursts are still outstanding.
    class axw_seq extends axw_base_seq_t;
        int unsigned   n;
        bit            reuse;
        axw_ref_model  model;
        axw_item_t     sent[$];
        axw_item_t     waiting[$];
        axw_item_t     responses[$];
        // Responses that answered a burst other than the oldest unanswered one.
        int unsigned   reordered;
        int unsigned   bursts[axi_burst_e];
        int unsigned   narrow;
        int unsigned   unaligned;
        int unsigned   beats;
        int unsigned   partial_strobes;
        int unsigned   slverr_bursts;
        int unsigned   largest;

        `uvm_object_utils(axw_seq)

        function new(string name = "axw_seq");
            super.new(name);
        endfunction

        // Mostly short bursts, so a test of a few hundred stays quick, and
        // one in ten addresses in the first error range.
        virtual function void pick(axw_item_t it);
            if (!it.randomize() with {
                    len dist {[0:15] :/ 90, [16:255] :/ 10};
                    addr dist {[16'h3000:16'h30ff] :/ 10, [16'h0000:16'hffff] :/ 90};
                }) begin
                `uvm_fatal("LB_RAND", "axi_write item randomize failed")
            end
        endfunction

        virtual task body();
            axw_item_t one = new_item("one");
            axw_item_t it;
            axw_item_t copy;
            for (int unsigned i = 0; i < n; i++) begin
                it = reuse ? one : new_item($sformatf("it%0d", i));
                pick(it);
                it.gap = ($urandom_range(3, 0) == 0) ? $urandom_range(2, 1) : 0;
                $cast(copy, it.clone());
                sent.push_back(copy);
                waiting.push_back(copy);
                send(it);
            end
            wait_for_writes();
            foreach (sent[i]) model.apply(sent[i]);
        endtask

        virtual function void write_done(axw_item_t rsp);
            axw_item_t want;
            axi_resp_e exp;
            int        found[$] = waiting.find_first_index(w) with (w.id === rsp.id);
            responses.push_back(rsp);
            if (found.size() == 0) begin
                `uvm_error("LB_AXW", $sformatf("response %0d is for %s, which matches no burst sent", responses.size(),
                                               rsp.convert2string()))
                return;
            end
            want = waiting[found[0]];
            waiting.delete(found[0]);
            if (found[0] != 0) reordered++;
            if (rsp.addr !== want.addr || rsp.id !== want.id || rsp.len !== want.len || rsp.size !== want.size ||
                rsp.burst !== want.burst || rsp.awuser !== want.awuser) begin
                `uvm_error("LB_AXW", $sformatf("response %0d is for %s, sent %s", responses.size(), rsp.convert2string(),
                                               want.convert2string()))
                return;
            end
            if (rsp.data.size() != int'(rsp.len) + 1 || rsp.data != want.data || rsp.strb != want.strb ||
                rsp.wuser != want.wuser) begin
                `uvm_error("LB_AXW", $sformatf("%s returned beats that differ from the %0d sent", rsp.convert2string(),
                                               int'(want.len) + 1))
                return;
            end
            exp = model.expected_resp(rsp);
            if (rsp.resp != exp) begin
                `uvm_error("LB_AXW", $sformatf("%s: bresp %s, expected %s", rsp.convert2string(), rsp.resp.name(), exp.name()))
            end
            if (exp != AXI_OKAY) slverr_bursts++;
            if (!bursts.exists(rsp.burst)) bursts[rsp.burst] = 0;
            bursts[rsp.burst]++;
            if (rsp.size < 2) narrow++;
            if (rsp.burst != AXI_WRAP && (rsp.addr & ((16'd1 << rsp.size) - 1)) != 0) unaligned++;
            if (rsp.total_bytes() > largest) largest = rsp.total_bytes();
            foreach (rsp.strb[b]) begin
                beats++;
                if (rsp.strb[b] != rsp.beat_lanes(rsp.addr, rsp.size, rsp.len, rsp.burst, b)) partial_strobes++;
            end
        endfunction
    endclass : axw_seq

    // A master agent and a slave agent on one bus. The slave's monitor feeds
    // observed.
    virtual class axw_pair_test extends lb_base_test;
        axw_agent_t                         master;
        axw_agent_t                         slave;
        axw_config_t                        master_cfg;
        axw_config_t                        slave_cfg;
        uvm_tlm_analysis_fifo #(axw_item_t) observed;
        axw_vif_t                           vif;
        // Bursts whose AW has transferred and whose B has not, and the most
        // there were at once.
        int unsigned                        in_flight;
        int unsigned                        peak;
        // AWs transferred, and W bursts whose first beat has been on the bus.
        int unsigned                        aw_done;
        int unsigned                        w_started;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axw_config_t master_cfg, axw_config_t slave_cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(axw_vif_t)::get(this, "", "axw", vif)) `uvm_fatal("LB_CFG", "no virtual axi_write_if 'axw'")
            master_cfg = axw_config_t::type_id::create("master_cfg");
            master_cfg.vif       = vif;
            master_cfg.clk_vif   = clk_vif;
            master_cfg.role      = A2C_SRC;
            master_cfg.port_name = "axw";
            slave_cfg = axw_config_t::type_id::create("slave_cfg");
            slave_cfg.vif       = vif;
            slave_cfg.clk_vif   = clk_vif;
            slave_cfg.role      = A2C_DST;
            slave_cfg.port_name = "axw";
            slave_cfg.mem       = axi_write_mem_t::type_id::create("slave_mem");
            configure(master_cfg, slave_cfg);
            uvm_config_db#(axw_config_t)::set(this, "master", "cfg", master_cfg);
            uvm_config_db#(axw_config_t)::set(this, "slave", "cfg", slave_cfg);
            master   = axw_agent_t::type_id::create("master", this);
            slave    = axw_agent_t::type_id::create("slave", this);
            observed = new("observed", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            slave.mon.ap.connect(observed.analysis_export);
        endfunction

        // Also fails a W burst that starts before its AW is on the bus: the
        // W bursts started may never outnumber the AWs transferred plus the
        // one awvalid offers.
        protected task watch_in_flight();
            bit w_open = 0;
            forever begin
                clk_vif.sample_edge();
                if (vif.wvalid === 1'b1 && !w_open) begin
                    w_open = 1;
                    w_started++;
                    if (w_started > aw_done + (vif.awvalid === 1'b1)) begin
                        `uvm_error("LB_AXW", $sformatf("W burst %0d started with %0d AWs transferred and awvalid %b",
                                                       w_started, aw_done, vif.awvalid))
                    end
                end
                if (vif.wvalid === 1'b1 && vif.wready === 1'b1 && vif.wlast === 1'b1) w_open = 0;
                if (vif.bvalid === 1'b1 && vif.bready === 1'b1) in_flight--;
                if (vif.awvalid === 1'b1 && vif.awready === 1'b1) begin
                    in_flight++;
                    aw_done++;
                end
                if (in_flight > peak) peak = in_flight;
            end
        endtask

        // Runs seq on the master, then checks that the slave's monitor
        // reported every burst the master returned, beat for beat, in order,
        // that W never led its AW, and that the slave's memory matches the
        // reference model.
        task run_seq(axw_seq seq);
            axw_item_t   seen;
            int unsigned compared;
            seq.model              = new();
            seq.model.error_ranges = slave_cfg.error_ranges;
            clk_vif.wait_reset_release();
            fork
                watch_in_flight();
            join_none
            seq.start(master.sqr);
            repeat (2) clk_vif.sample_edge();
            disable fork;
            if (seq.responses.size() != seq.n) begin
                `uvm_error("LB_AXW", $sformatf("%0d bursts sent, %0d returned", seq.n, seq.responses.size()))
            end
            foreach (seq.responses[i]) begin
                if (!observed.try_get(seen)) begin
                    `uvm_error("LB_MISSING", $sformatf("the slave's monitor did not report %s", seq.responses[i].convert2string()))
                    break;
                end
                if (!seen.compare(seq.responses[i])) begin
                    `uvm_error("LB_MISMATCH", $sformatf("burst %0d: the master returned %s, the slave's monitor reported %s",
                                                        i, seq.responses[i].convert2string(), seen.convert2string()))
                end
            end
            if (observed.used() != 0) begin
                `uvm_error("LB_EXTRA", $sformatf("the slave's monitor reported %0d bursts the master never returned",
                                                 observed.used()))
            end
            if (w_started != seq.n || aw_done != seq.n) begin
                `uvm_error("LB_AXW", $sformatf("%0d bursts sent, %0d AWs and %0d W bursts seen", seq.n, aw_done, w_started))
            end
            compared = seq.model.check(slave_cfg.mem, "LB_AXW");
            `uvm_info("LB_MEM", $sformatf("%0d bytes compared with the reference model, %0d written", compared,
                                          seq.model.bytes.num()), UVM_NONE)
        endtask
    endclass : axw_pair_test

    // 200 random bursts of every type and size up to the 32-bit bus, with
    // random legal strobes and up to four outstanding, awready, wready and
    // bready each high on 70 percent of clocks, a response delay of up to
    // three clocks, and an error range at 'h3000 to 'h30ff. Also checks the
    // lanes of five beats against worked examples of the AXI address rules,
    // since the item's strobe constraint and the model use the same function.
    // With the slave's reorder set, at least one B must answer a burst other
    // than the oldest outstanding one.
    class axi_write_random_test extends axw_pair_test;
        `uvm_component_utils(axi_write_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axw_config_t master_cfg, axw_config_t slave_cfg);
            master_cfg.max_outstanding = 4;
            master_cfg.bready_pct      = 70;
            slave_cfg.awready_pct      = 70;
            slave_cfg.wready_pct       = 70;
            slave_cfg.resp_delay_max   = 3;
            slave_cfg.error_ranges.push_back('{lo: 64'h3000, hi: 64'h30ff});
        endfunction

        function void check_lanes(string what, bit [15:0] start, bit [2:0] size, bit [7:0] len, axi_burst_e burst,
                                  int unsigned n, bit [3:0] want);
            axw_item_t   it = axw_item_t::type_id::create("lanes");
            bit [3:0]    got = it.beat_lanes(start, size, len, burst, n);
            if (got != want) begin
                `uvm_error("LB_AXW", $sformatf("%s beat %0d: lanes %b, expected %b", what, n, got, want))
            end
        endfunction

        virtual task run_phase(uvm_phase phase);
            axw_seq seq = axw_seq::type_id::create("seq");
            phase.raise_objection(this);
            check_lanes("INCR 4x4 at 'h07", 'h07, 2, 3, AXI_INCR, 0, 4'b1000);
            check_lanes("INCR 4x4 at 'h07", 'h07, 2, 3, AXI_INCR, 1, 4'b1111);
            check_lanes("INCR 3x2 at 'h03", 'h03, 1, 2, AXI_INCR, 2, 4'b1100);
            check_lanes("FIXED 2x1 at 'h05", 'h05, 0, 1, AXI_FIXED, 1, 4'b0010);
            check_lanes("WRAP 4x2 at 'h06", 'h06, 1, 3, AXI_WRAP, 1, 4'b0011);
            seq.n = 200;
            run_seq(seq);
            `uvm_info("LB_STATS", $sformatf("%0d bursts (%0d FIXED, %0d INCR, %0d WRAP; %0d narrow, %0d unaligned), %0d beats (%0d with partial strobes), %0d SLVERR, at most %0d outstanding, %0d answered out of AW order",
                                            seq.responses.size(), seq.bursts[AXI_FIXED], seq.bursts[AXI_INCR],
                                            seq.bursts[AXI_WRAP], seq.narrow, seq.unaligned, seq.beats,
                                            seq.partial_strobes, seq.slverr_bursts, peak, seq.reordered), UVM_NONE)
            if (peak != 4) `uvm_error("LB_AXW", $sformatf("max_outstanding is 4, but at most %0d bursts were outstanding", peak))
            foreach (seq.bursts[b]) begin
                if (seq.bursts[b] == 0) `uvm_error("LB_AXW", $sformatf("no %s burst", b.name()))
            end
            if (seq.bursts.num() != 3) `uvm_error("LB_AXW", "not every burst type was sent")
            if (seq.narrow == 0 || seq.unaligned == 0 || seq.slverr_bursts == 0 || seq.partial_strobes == 0) begin
                `uvm_error("LB_AXW", "the bursts covered no narrow transfer, no unaligned start, no error range or no partial strobe")
            end
            if (slave_cfg.reorder && seq.reordered == 0) `uvm_error("LB_AXW", "reorder is set, but every B came in AW order")
            if (!slave_cfg.reorder && seq.reordered != 0) begin
                `uvm_error("LB_AXW", $sformatf("reorder is clear, but %0d Bs came out of AW order", seq.reordered))
            end
            phase.drop_objection(this);
        endtask
    endclass : axi_write_random_test

    // As axi_write_random_test, with the slave answering ready bursts in a
    // random order that keeps each ID's bursts in AW order, and response
    // delays of up to eight clocks so that several IDs are ready at once.
    // The master and the monitor must each pair a B with the oldest burst of
    // its bid.
    class axi_write_reorder_test extends axi_write_random_test;
        `uvm_component_utils(axi_write_reorder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axw_config_t master_cfg, axw_config_t slave_cfg);
            super.configure(master_cfg, slave_cfg);
            slave_cfg.reorder        = 1'b1;
            slave_cfg.resp_delay_max = 8;
        endfunction
    endclass : axi_write_reorder_test

    // As axi_write_random_test, but every burst goes out through one item
    // object, randomised again before each send while up to three earlier
    // bursts are still outstanding. Each response must still carry the
    // address, ID, shape and beats of its own burst, and the memory must
    // match the reference model.
    class axi_write_reuse_test extends axw_pair_test;
        `uvm_component_utils(axi_write_reuse_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axw_config_t master_cfg, axw_config_t slave_cfg);
            master_cfg.max_outstanding = 4;
            slave_cfg.resp_delay_min   = 2;
            slave_cfg.resp_delay_max   = 6;
        endfunction

        virtual task run_phase(uvm_phase phase);
            axw_seq seq = axw_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n     = 100;
            seq.reuse = 1'b1;
            run_seq(seq);
            `uvm_info("LB_STATS", $sformatf("%0d bursts through one item, %0d beats checked, at most %0d outstanding",
                                            seq.responses.size(), seq.beats, peak), UVM_NONE)
            if (peak < 2) `uvm_error("LB_AXW", $sformatf("the item was never reused with a burst outstanding (peak %0d)", peak))
            for (int unsigned i = 1; i < seq.responses.size(); i++) begin
                if (seq.responses[i] == seq.responses[i - 1]) begin
                    `uvm_error("LB_AXW", $sformatf("responses %0d and %0d are one object", i - 1, i))
                end
            end
            phase.drop_objection(this);
        endtask
    endclass : axi_write_reuse_test

    // Randomises with no constraint beyond the item's own, so the port's
    // max_transfer_bytes is the only bound on a burst's size.
    class axw_limit_seq extends axw_seq;
        `uvm_object_utils(axw_limit_seq)

        function new(string name = "axw_limit_seq");
            super.new(name);
        endfunction

        virtual function void pick(axw_item_t it);
            if (!it.randomize()) `uvm_fatal("LB_RAND", "axi_write item randomize failed")
        endfunction
    endclass : axw_limit_seq

    // Sends items as given and keeps their responses.
    class axw_given_seq extends axw_base_seq_t;
        axw_item_t items[$];
        axw_item_t rsps[$];

        `uvm_object_utils(axw_given_seq)

        function new(string name = "axw_given_seq");
            super.new(name);
        endfunction

        virtual task body();
            foreach (items[i]) send(items[i]);
            wait_for_writes();
        endtask

        virtual function void write_done(item_t rsp);
            rsps.push_back(rsp);
        endfunction
    endclass : axw_given_seq

    // max_transfer_bytes 16 on the master's port. Every item new_item()
    // gives must randomise to at most 16 bytes, with some at exactly 16, and
    // the bursts must complete. An item made without new_item() has no
    // limit, so some of those randomise above 16 bytes, which shows the limit
    // comes from the port. Last, the master must refuse two items: one over
    // the limit, and one without a data, strobe and wuser entry per beat.
    class axi_write_max_transfer_test extends axw_pair_test;
        `uvm_component_utils(axi_write_max_transfer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axw_config_t master_cfg, axw_config_t slave_cfg);
            master_cfg.max_transfer_bytes = 16;
            master_cfg.max_outstanding    = 2;
        endfunction

        virtual task run_phase(uvm_phase phase);
            axw_limit_seq seq = axw_limit_seq::type_id::create("seq");
            axw_item_t    free_item = axw_item_t::type_id::create("free_item");
            int unsigned  over = 0;
            int unsigned  at_limit = 0;
            phase.raise_objection(this);
            repeat (50) begin
                if (!free_item.randomize()) `uvm_fatal("LB_RAND", "axi_write item randomize failed")
                if (free_item.total_bytes() > 16) over++;
            end
            if (over == 0) `uvm_error("LB_AXW", "50 items with no limit all randomised to 16 bytes or fewer")
            seq.n = 200;
            run_seq(seq);
            foreach (seq.responses[i]) begin
                if (seq.responses[i].total_bytes() > 16) begin
                    `uvm_error("LB_AXW", $sformatf("%s moves %0d bytes, above max_transfer_bytes 16",
                                                   seq.responses[i].convert2string(), seq.responses[i].total_bytes()))
                end
                if (seq.responses[i].total_bytes() == 16) at_limit++;
            end
            `uvm_info("LB_STATS", $sformatf("%0d bursts within 16 bytes, %0d at exactly 16; %0d of 50 unlimited items above 16",
                                            seq.responses.size(), at_limit, over), UVM_NONE)
            if (at_limit == 0) `uvm_error("LB_AXW", "no burst reached max_transfer_bytes")
            send_refused();
            phase.drop_objection(this);
        endtask

        // Two items made with type_id::create, so no constraint holds them:
        // a 32-byte burst with its eight beats, over the port's 16, and a
        // 4-beat burst with one beat of data. The master must report one
        // A2C_CFG error for each, complete each with no beats, and leave the
        // bus without an AW or a W beat.
        task send_refused();
            axw_given_seq      given = axw_given_seq::type_id::create("given");
            a2c_error_demoter  demoter = a2c_error_demoter::type_id::create("demoter");
            axw_item_t         over = axw_item_t::type_id::create("over");
            axw_item_t         short_beats = axw_item_t::type_id::create("short_beats");
            int unsigned       aws = 0;
            int unsigned       ws = 0;
            demoter.demote_id = "A2C_CFG";
            uvm_report_cb::add(null, demoter);
            over.addr  = 'h100;
            over.len   = 7;
            over.size  = 2;
            over.burst = AXI_INCR;
            over.data  = new[8];
            over.strb  = new[8];
            over.wuser = new[8];
            short_beats.addr  = 'h200;
            short_beats.len   = 3;
            short_beats.size  = 2;
            short_beats.burst = AXI_INCR;
            short_beats.data  = new[1];
            short_beats.strb  = new[1];
            short_beats.wuser = new[1];
            given.items = {over, short_beats};
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (vif.awvalid === 1'b1 && vif.awready === 1'b1) aws++;
                    if (vif.wvalid === 1'b1 && vif.wready === 1'b1) ws++;
                end
            join_none
            given.start(master.sqr);
            repeat (4) clk_vif.sample_edge();
            disable fork;
            uvm_report_cb::delete(null, demoter);
            `uvm_info("LB_STATS", $sformatf("two refused items: %0d A2C_CFG, %0d AWs, %0d W beats, %0d responses",
                                            demoter.demoted, aws, ws, given.rsps.size()), UVM_NONE)
            if (demoter.demoted != 2) `uvm_error("LB_AXW", $sformatf("expected two A2C_CFG errors, caught %0d", demoter.demoted))
            if (aws != 0 || ws != 0) `uvm_error("LB_AXW", $sformatf("the refused items put %0d AWs and %0d W beats on the bus", aws, ws))
            if (given.rsps.size() != 2) `uvm_error("LB_AXW", $sformatf("expected two responses, got %0d", given.rsps.size()))
            foreach (given.rsps[i]) begin
                if (given.rsps[i].data.size() != 0) `uvm_error("LB_AXW", $sformatf("refused item %0d returned with beats", i))
            end
            if (observed.used() != 0) `uvm_error("LB_EXTRA", "the slave's monitor reported a burst for a refused item")
        endtask
    endclass : axi_write_max_transfer_test

    // Shared by the tests that drive the pins by hand.
    virtual class axw_pins_test extends lb_base_test;
        axw_vif_t vif;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(axw_vif_t)::get(this, "", "axw", vif)) `uvm_fatal("LB_CFG", "no virtual axi_write_if 'axw'")
        endfunction

        // Set the AW, W and B pins for the next clock.
        task aw(bit valid, bit ready, bit [1:0] id = 0, bit [15:0] addr = 0, bit [7:0] len = 0,
                bit [2:0] size = 2, axi_burst_e burst = AXI_INCR);
            vif.awvalid <= valid;
            vif.awready <= ready;
            vif.awid    <= id;
            vif.awaddr  <= lb_axw_addr_t'(addr);
            vif.awlen   <= len;
            vif.awsize  <= size;
            vif.awburst <= burst;
            vif.awuser  <= '0;
        endtask

        task w(bit valid, bit ready, bit [1:0] id = 0, bit [31:0] data = 0, bit [3:0] strb = 4'hf, bit last = 0);
            vif.wvalid <= valid;
            vif.wready <= ready;
            vif.wid    <= id;
            vif.wdata  <= lb_axw_data_t'(data);
            vif.wstrb  <= strb;
            vif.wlast  <= last;
            vif.wuser  <= '0;
        endtask

        task b(bit valid, bit ready, bit [1:0] id = 0, axi_resp_e resp = AXI_OKAY);
            vif.bvalid <= valid;
            vif.bready <= ready;
            vif.bid    <= id;
            vif.bresp  <= resp;
            vif.buser  <= '0;
        endtask

        task tick(int unsigned n = 1);
            repeat (n) clk_vif.drive_edge();
        endtask
    endclass : axw_pins_test

    // An active slave against W and AW the test drives by hand, each beat
    // and AW held until the slave's random ready takes it: burst A sends its
    // four W beats, then its AW; burst B one W beat, its AW, then its other
    // two beats; bursts C and D send all their W beats before either AW.
    // The slave must answer A, B, C, D in order with OKAY, its monitor must
    // report each burst with its own beats, and its memory must match the
    // reference model. The count of W beats transferred when each AW
    // transfers shows the W beats came first on the bus.
    class axi_write_w_before_aw_test extends axw_pins_test;
        axw_agent_t                         slave;
        axw_config_t                        cfg;
        uvm_tlm_analysis_fifo #(axw_item_t) observed;
        int unsigned                        w_count;
        int unsigned                        w_at_aw[$];
        bit [1:0]                           bids[$];
        axi_resp_e                          bresps[$];

        `uvm_component_utils(axi_write_w_before_aw_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            cfg = axw_config_t::type_id::create("cfg");
            cfg.vif            = vif;
            cfg.clk_vif        = clk_vif;
            cfg.role           = A2C_DST;
            cfg.port_name      = "axw";
            cfg.awready_pct    = 70;
            cfg.wready_pct     = 70;
            cfg.resp_delay_max = 2;
            uvm_config_db#(axw_config_t)::set(this, "slave", "cfg", cfg);
            slave    = axw_agent_t::type_id::create("slave", this);
            observed = new("observed", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            slave.mon.ap.connect(observed.analysis_export);
        endfunction

        // Holds bready high and records each B, and counts the W beats
        // transferred at each AW transfer.
        protected task watch();
            vif.bready <= 1'b1;
            forever begin
                clk_vif.sample_edge();
                if (vif.bvalid === 1'b1) begin
                    bids.push_back(vif.bid);
                    bresps.push_back(axi_resp_e'(vif.bresp));
                end
                if (vif.wvalid === 1'b1 && vif.wready === 1'b1) w_count++;
                if (vif.awvalid === 1'b1 && vif.awready === 1'b1) w_at_aw.push_back(w_count);
            end
        endtask

        // Each returns at the drive point after its transfer, with its valid
        // set low for the next clock.
        task send_w(axw_item_t it, int unsigned n);
            vif.wvalid <= 1'b1;
            vif.wid    <= it.id;
            vif.wdata  <= it.data[n];
            vif.wstrb  <= it.strb[n];
            vif.wlast  <= (n == it.len);
            vif.wuser  <= it.wuser[n];
            do clk_vif.sample_edge(); while (vif.wready !== 1'b1);
            clk_vif.drive_edge();
            vif.wvalid <= 1'b0;
        endtask

        task send_aw(axw_item_t it);
            vif.awvalid <= 1'b1;
            vif.awid    <= it.id;
            vif.awaddr  <= it.addr;
            vif.awlen   <= it.len;
            vif.awsize  <= it.size;
            vif.awburst <= it.burst;
            vif.awuser  <= it.awuser;
            do clk_vif.sample_edge(); while (vif.awready !== 1'b1);
            clk_vif.drive_edge();
            vif.awvalid <= 1'b0;
        endtask

        function axw_item_t burst(bit [1:0] id, bit [15:0] addr, bit [7:0] len, bit [2:0] size, axi_burst_e kind);
            axw_item_t it = axw_item_t::type_id::create("it");
            if (!it.randomize() with {id == local::id; addr == local::addr; len == local::len; size == local::size;
                                      burst == local::kind;}) begin
                `uvm_fatal("LB_RAND", "axi_write item randomize failed")
            end
            return it;
        endfunction

        virtual task run_phase(uvm_phase phase);
            axw_item_t    sent[$];
            axw_item_t    a = burst(1, 'h100, 3, 2, AXI_INCR);
            axw_item_t    bb = burst(2, 'h202, 2, 1, AXI_INCR);
            axw_item_t    c = burst(0, 'h304, 1, 2, AXI_WRAP);
            axw_item_t    d = burst(3, 'h401, 0, 0, AXI_FIXED);
            axw_item_t    seen;
            axw_ref_model model = new();
            int unsigned  want_w[$] = {4, 5, 10, 10};
            bit [1:0]     want_ids[$] = {1, 2, 0, 3};
            int unsigned  compared;
            phase.raise_objection(this);
            sent = {a, bb, c, d};
            vif.awvalid <= 1'b0;
            vif.wvalid  <= 1'b0;
            vif.bready  <= 1'b0;
            clk_vif.wait_reset_release();
            fork
                watch();
            join_none
            clk_vif.drive_edge();
            for (int unsigned n = 0; n <= a.len; n++) send_w(a, n);
            tick(2);
            send_aw(a);
            send_w(bb, 0);
            send_aw(bb);
            send_w(bb, 1);
            send_w(bb, 2);
            for (int unsigned n = 0; n <= c.len; n++) send_w(c, n);
            send_w(d, 0);
            send_aw(c);
            send_aw(d);
            for (int unsigned i = 0; i < 20 && bids.size() < 4; i++) tick();
            tick(2);
            disable fork;
            `uvm_info("LB_STATS", $sformatf("W beats transferred at each AW: %p; B ids %p", w_at_aw, bids), UVM_NONE)
            if (w_at_aw != want_w) `uvm_error("LB_AXW", $sformatf("W beats at each AW were %p, expected %p", w_at_aw, want_w))
            if (bids != want_ids) `uvm_error("LB_AXW", $sformatf("B ids were %p, expected %p", bids, want_ids))
            foreach (bresps[i]) begin
                if (bresps[i] != AXI_OKAY) `uvm_error("LB_AXW", $sformatf("B %0d is %s", i, bresps[i].name()))
            end
            foreach (sent[i]) begin
                sent[i].resp  = AXI_OKAY;
                sent[i].buser = '0;
                model.apply(sent[i]);
                if (!observed.try_get(seen)) begin
                    `uvm_error("LB_MISSING", $sformatf("the slave's monitor did not report %s", sent[i].convert2string()))
                end else if (!seen.compare(sent[i])) begin
                    `uvm_error("LB_MISMATCH", $sformatf("burst %0d: sent %s, the slave's monitor reported %s", i,
                                                        sent[i].convert2string(), seen.convert2string()))
                end
            end
            compared = model.check(cfg.mem, "LB_AXW");
            `uvm_info("LB_MEM", $sformatf("%0d bytes compared with the reference model, %0d written", compared,
                                          model.bytes.num()), UVM_NONE)
            phase.drop_objection(this);
        endtask
    endclass : axi_write_w_before_aw_test

    // A passive monitor watches pins the test drives by hand, both master
    // and slave: a clean two-beat burst; an AW whose awaddr changes while
    // awready is low; an AW whose awvalid drops before awready; a beat whose
    // wdata changes while wready is low; a beat whose wvalid drops before
    // wready; a B whose bresp changes while bready is low; a B whose bvalid
    // drops before bready; wlast on the first of two beats; no wlast on the
    // last of two beats; a B whose bid matches no AW; a B before its burst's
    // last W; the reserved awburst 2'b11; an 8-byte awsize on the 32-bit
    // bus; a 17-beat FIXED burst; a three-beat WRAP burst; a WRAP burst from
    // an address not aligned to its 4-byte transfers; an INCR burst across a
    // 4 KB boundary; a clean burst whose W beats come before its AW; two
    // clean bursts, AW id 1 then AW id 2, answered B id 2 then B id 1; a
    // one-byte beat whose wstrb sets a lane it does not carry; and a beat
    // whose wid is not its burst's awid. Expects exactly six A2C_HOLD and
    // twelve A2C_PROTO reports, demoted to info, and nineteen bursts
    // reported with the addresses that transferred, the two answered out of
    // order each with its own.
    class axi_write_monitor_checks_test extends axw_pins_test;
        axw_agent_t                         obs;
        uvm_tlm_analysis_fifo #(axw_item_t) observed;

        `uvm_component_utils(axi_write_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            axw_config_t cfg;
            super.build_phase(phase);
            cfg = axw_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "axw";
            uvm_config_db#(axw_config_t)::set(this, "obs", "cfg", cfg);
            obs      = axw_agent_t::type_id::create("obs", this);
            observed = new("observed", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(observed.analysis_export);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
        endfunction

        task idle();
            aw(0, 0);
            w(0, 0);
            b(0, 0);
            tick();
        endtask

        // One AW and its beats, the first beat on the AW's clock, then its B.
        // Each beat strobes exactly the lanes it carries.
        task burst(bit [15:0] addr, bit [7:0] len, bit [2:0] size = 2, axi_burst_e kind = AXI_INCR);
            axw_item_t lanes = axw_item_t::type_id::create("lanes");
            aw(1, 1, 0, addr, len, size, kind);
            for (int unsigned i = 0; i <= len; i++) begin
                w(1, 1, 0, addr + i, lanes.beat_lanes(addr, size, len, kind, i), i == len); tick();
                aw(0, 0);
            end
            w(0, 0); b(1, 1, 0); tick();
            idle();
        endtask

        virtual task run_phase(uvm_phase phase);
            axw_item_t   seen;
            bit [15:0]   want[$] = {'h100, 'h200, 'h300, 'h400, 'h500, 'h580, 'h600, 'h680, 'h700, 'h800, 'h900,
                                    'ha00, 'hb00, 'hc02, 'hff8, 'hd00, 'he80, 'he00, 'hf01, 'hf40};
            int unsigned n = 0;
            phase.raise_objection(this);
            aw(0, 0);
            w(0, 0);
            b(0, 0);
            clk_vif.wait_reset_release();
            tick();
            burst('h100, 1);                                          // clean two-beat burst
            aw(1, 0, 1, 'h1f0); tick();                               // awaddr changes while stalled
            aw(1, 1, 1, 'h200); tick();
            aw(0, 0); w(1, 1, 1, 'h21, 4'hf, 1); tick();
            w(0, 0); b(1, 1, 1); tick();
            idle();
            aw(1, 0, 1, 'h280); tick();                               // awvalid drops before awready
            aw(0, 0); tick();
            idle();
            aw(1, 1, 0, 'h300); tick();                               // wdata changes while stalled
            aw(0, 0); w(1, 0, 0, 'h31, 4'hf, 1); tick();
            w(1, 1, 0, 'h32, 4'hf, 1); tick();
            w(0, 0); b(1, 1, 0); tick();
            idle();
            aw(1, 1, 0, 'h400); tick();                               // wvalid drops before wready
            aw(0, 0); w(1, 0, 0, 'h41, 4'hf, 1); tick();
            w(0, 0); tick();
            w(1, 1, 0, 'h41, 4'hf, 1); tick();
            w(0, 0); b(1, 1, 0); tick();
            idle();
            aw(1, 1, 0, 'h500); w(1, 1, 0, 'h51, 4'hf, 1); tick();    // bresp changes while stalled
            aw(0, 0); w(0, 0); b(1, 0, 0, AXI_OKAY); tick();
            b(1, 1, 0, AXI_SLVERR); tick();
            idle();
            aw(1, 1, 0, 'h580); w(1, 1, 0, 'h58, 4'hf, 1); tick();    // bvalid drops before bready
            aw(0, 0); w(0, 0); b(1, 0, 0); tick();
            b(0, 0); tick();
            b(1, 1, 0); tick();
            idle();
            aw(1, 1, 2, 'h600, 1); w(1, 1, 2, 'h61, 4'hf, 1); tick(); // wlast on the first of two beats
            aw(0, 0); w(0, 0); b(1, 1, 2); tick();
            idle();
            aw(1, 1, 0, 'h680, 1); w(1, 1, 0, 'h68, 4'hf, 0); tick(); // no wlast on the last of two beats
            aw(0, 0); w(1, 1, 0, 'h69, 4'hf, 0); tick();
            w(0, 0); b(1, 1, 0); tick();
            idle();
            b(1, 1, 3); tick();                                       // bid matches no AW
            idle();
            aw(1, 1, 1, 'h700, 1); w(1, 1, 1, 'h71, 4'hf, 0); tick(); // B before the last W
            aw(0, 0); w(0, 0); b(1, 1, 1); tick();
            b(0, 0); w(1, 1, 1, 'h72, 4'hf, 1); tick();
            w(0, 0); b(1, 1, 1); tick();
            idle();
            burst('h800, 0, 2, axi_burst_e'(2'b11));                  // reserved awburst
            burst('h900, 0, 3);                                       // 8-byte awsize on the 32-bit bus
            burst('ha00, 16, 2, AXI_FIXED);                           // 17-beat FIXED
            burst('hb00, 2, 2, AXI_WRAP);                             // three-beat WRAP
            burst('hc02, 3, 2, AXI_WRAP);                             // WRAP from an address not 4-byte aligned
            burst('hff8, 3);                                          // 16 bytes from 'hff8
            w(1, 1, 0, 'hd1, 4'hf, 0); tick();                        // W before its AW
            w(1, 1, 0, 'hd2, 4'hf, 1); tick();
            w(0, 0); aw(1, 1, 0, 'hd00, 1); tick();
            aw(0, 0); b(1, 1, 0); tick();
            idle();
            aw(1, 1, 1, 'he00); w(1, 1, 1, 'he1, 4'hf, 1); tick();    // AW id 1, AW id 2, B id 2, B id 1
            aw(1, 1, 2, 'he80); w(1, 1, 2, 'he8, 4'hf, 1); tick();
            aw(0, 0); w(0, 0); b(1, 1, 2); tick();
            b(1, 1, 1); tick();
            idle();
            aw(1, 1, 0, 'hf01, 0, 0); w(1, 1, 0, 'hf1, 4'b0011, 1); tick(); // wstrb lane 0 on a lane-1 beat
            aw(0, 0); w(0, 0); b(1, 1, 0); tick();
            idle();
            aw(1, 1, 1, 'hf40); w(1, 1, 3, 'hf4, 4'hf, 1); tick();    // wid 3 on an awid 1 burst
            aw(0, 0); w(0, 0); b(1, 1, 1); tick();
            idle();
            tick(2);
            while (observed.try_get(seen)) begin
                if (n < want.size() && seen.addr !== want[n]) begin
                    `uvm_error("LB_CHECKS", $sformatf("burst %0d reported at 0x%0h, expected 0x%0h", n, seen.addr, want[n]))
                end
                n++;
            end
            if (n != want.size()) `uvm_error("LB_CHECKS", $sformatf("expected %0d bursts reported, got %0d", want.size(), n))
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            uvm_report_server srv = uvm_report_server::get_server();
            int unsigned proto = srv.get_id_count("A2C_PROTO");
            int unsigned hold  = srv.get_id_count("A2C_HOLD");
            super.check_phase(phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_PROTO, %0d A2C_HOLD", proto, hold), UVM_NONE)
            if (proto != 12) `uvm_error("LB_CHECKS", $sformatf("expected 12 A2C_PROTO reports, got %0d", proto))
            if (hold != 6) `uvm_error("LB_CHECKS", $sformatf("expected 6 A2C_HOLD reports, got %0d", hold))
        endfunction
    endclass : axi_write_monitor_checks_test
