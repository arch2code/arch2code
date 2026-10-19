// axi_read agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef struct packed {
        logic [15:0] a;
    } lb_axr_addr_t;
    typedef struct packed {
        logic [15:0] hi;
        logic [15:0] lo;
    } lb_axr_data_t;
    typedef logic [2:0] lb_axr_aruser_t;
    typedef logic [1:0] lb_axr_ruser_t;
    typedef logic [1:0] lb_axr_id_t;
    typedef axi_read_agent #(.addr_t(lb_axr_addr_t), .data_t(lb_axr_data_t), .aruser_t(lb_axr_aruser_t),
                             .ruser_t(lb_axr_ruser_t), .id_t(lb_axr_id_t)) axr_agent_t;
    typedef axr_agent_t::item_t axr_item_t;
    typedef axr_agent_t::config_t axr_config_t;
    typedef axi_read_base_seq #(lb_axr_addr_t, lb_axr_data_t, lb_axr_aruser_t, lb_axr_ruser_t, lb_axr_id_t) axr_base_seq_t;
    typedef virtual axi_read_if #(.addr_t(lb_axr_addr_t), .data_t(lb_axr_data_t), .aruser_t(lb_axr_aruser_t),
                                  .ruser_t(lb_axr_ruser_t), .id_t(lb_axr_id_t)) axr_vif_t;

    // Sends n bursts and checks each response: its AR fields against the
    // oldest unanswered burst sent with its ID, since a slave keeps each
    // ID's bursts in order, and each beat against the slave's memory. A beat in an error range
    // must be SLVERR with zero data; any other must be OKAY and carry the
    // memory's bytes on the lanes the AXI address rules give it. With reuse
    // set, every burst goes out through one item object, randomised again
    // for each send while earlier bursts are still outstanding.
    class axr_seq extends axr_base_seq_t;
        int unsigned          n;
        bit                   reuse;
        axi_read_mem_t        mem;
        axi_addr_range_t      error_ranges[$];
        axr_item_t            waiting[$];
        axr_item_t            responses[$];
        // Responses that answered a burst other than the oldest unanswered one.
        int unsigned          reordered;
        int unsigned          bursts[axi_burst_e];
        int unsigned          narrow;
        int unsigned          unaligned;
        int unsigned          beats;
        int unsigned          slverr_beats;
        int unsigned          largest;

        `uvm_object_utils(axr_seq)

        function new(string name = "axr_seq");
            super.new(name);
        endfunction

        // Mostly short bursts, so a test of a few hundred stays quick, and
        // one in ten addresses in the first error range.
        virtual function void pick(axr_item_t it);
            if (!it.randomize() with {
                    len dist {[0:15] :/ 90, [16:255] :/ 10};
                    addr dist {[16'h3000:16'h30ff] :/ 10, [16'h0000:16'hffff] :/ 90};
                }) begin
                `uvm_fatal("LB_RAND", "axi_read item randomize failed")
            end
        endfunction

        virtual task body();
            axr_item_t one = new_item("one");
            axr_item_t it;
            axr_item_t copy;
            for (int unsigned i = 0; i < n; i++) begin
                it = reuse ? one : new_item($sformatf("it%0d", i));
                pick(it);
                it.gap = ($urandom_range(3, 0) == 0) ? $urandom_range(2, 1) : 0;
                $cast(copy, it.clone());
                waiting.push_back(copy);
                send(it);
            end
            wait_for_reads();
        endtask

        virtual function void read_done(axr_item_t rsp);
            axr_item_t   want;
            bit [63:0]   first;
            int unsigned count;
            bit [31:0]   word;
            int          found[$] = waiting.find_first_index(w) with (w.id === rsp.id);
            responses.push_back(rsp);
            if (found.size() == 0) begin
                `uvm_error("LB_AXR", $sformatf("response %0d is for %s, which matches no burst sent", responses.size(),
                                               rsp.convert2string()))
                return;
            end
            want = waiting[found[0]];
            waiting.delete(found[0]);
            if (found[0] != 0) reordered++;
            if (rsp.addr !== want.addr || rsp.id !== want.id || rsp.len !== want.len || rsp.size !== want.size ||
                rsp.burst !== want.burst || rsp.aruser !== want.aruser) begin
                `uvm_error("LB_AXR", $sformatf("response %0d is for %s, sent %s", responses.size(), rsp.convert2string(),
                                               want.convert2string()))
                return;
            end
            if (rsp.data.size() != int'(rsp.len) + 1) begin
                `uvm_error("LB_AXR", $sformatf("%s returned %0d beats", rsp.convert2string(), rsp.data.size()))
                return;
            end
            if (!bursts.exists(rsp.burst)) bursts[rsp.burst] = 0;
            bursts[rsp.burst]++;
            if (rsp.size < 2) narrow++;
            if (rsp.burst != AXI_WRAP && (rsp.addr & ((16'd1 << rsp.size) - 1)) != 0) unaligned++;
            if (rsp.total_bytes() > largest) largest = rsp.total_bytes();
            foreach (rsp.data[b]) begin
                beats++;
                axi_beat(64'(rsp.addr), rsp.size, rsp.len, rsp.burst, b, first, count);
                word = rsp.data[b];
                if (axi_in_error_range(first, error_ranges)) begin
                    slverr_beats++;
                    if (rsp.resp[b] != AXI_SLVERR || word !== '0) begin
                        `uvm_error("LB_AXR", $sformatf("%s beat %0d at 0x%0h: rresp %s rdata 0x%08h, expected SLVERR and 0",
                                                       rsp.convert2string(), b, first, rsp.resp[b].name(), word))
                    end
                    continue;
                end
                if (rsp.resp[b] != AXI_OKAY) begin
                    `uvm_error("LB_AXR", $sformatf("%s beat %0d at 0x%0h: rresp %s", rsp.convert2string(), b, first,
                                                   rsp.resp[b].name()))
                end
                for (int unsigned i = 0; i < count; i++) begin
                    int unsigned lane = int'((first + i) % 4);
                    if (word[8 * lane +: 8] !== mem.read(first + i)) begin
                        `uvm_error("LB_AXR", $sformatf("%s beat %0d: lane %0d holds 0x%02h, memory 0x%0h holds 0x%02h",
                                                       rsp.convert2string(), b, lane, word[8 * lane +: 8], first + i,
                                                       mem.read(first + i)))
                    end
                end
            end
        endfunction
    endclass : axr_seq

    // A master agent and a slave agent on one bus, the slave serving a
    // memory with the random fill. The slave's monitor feeds observed.
    virtual class axr_pair_test extends lb_base_test;
        axr_agent_t                         master;
        axr_agent_t                         slave;
        axr_config_t                        master_cfg;
        axr_config_t                        slave_cfg;
        uvm_tlm_analysis_fifo #(axr_item_t) observed;
        axr_vif_t                           vif;
        // Bursts whose AR has transferred and whose last beat has not, and
        // the most there were at once.
        int unsigned                        in_flight;
        int unsigned                        peak;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axr_config_t master_cfg, axr_config_t slave_cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(axr_vif_t)::get(this, "", "axr", vif)) `uvm_fatal("LB_CFG", "no virtual axi_read_if 'axr'")
            master_cfg = axr_config_t::type_id::create("master_cfg");
            master_cfg.vif       = vif;
            master_cfg.clk_vif   = clk_vif;
            master_cfg.role      = A2C_SRC;
            master_cfg.port_name = "axr";
            slave_cfg = axr_config_t::type_id::create("slave_cfg");
            slave_cfg.vif       = vif;
            slave_cfg.clk_vif   = clk_vif;
            slave_cfg.role      = A2C_DST;
            slave_cfg.port_name = "axr";
            slave_cfg.mem       = axi_read_mem_t::type_id::create("slave_mem");
            slave_cfg.mem.fill  = A2C_MEM_FILL_RANDOM;
            configure(master_cfg, slave_cfg);
            uvm_config_db#(axr_config_t)::set(this, "master", "cfg", master_cfg);
            uvm_config_db#(axr_config_t)::set(this, "slave", "cfg", slave_cfg);
            master   = axr_agent_t::type_id::create("master", this);
            slave    = axr_agent_t::type_id::create("slave", this);
            observed = new("observed", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            slave.mon.ap.connect(observed.analysis_export);
        endfunction

        protected task watch_in_flight();
            forever begin
                clk_vif.sample_edge();
                if (vif.rvalid === 1'b1 && vif.rready === 1'b1 && vif.rlast === 1'b1) in_flight--;
                if (vif.arvalid === 1'b1 && vif.arready === 1'b1) in_flight++;
                if (in_flight > peak) peak = in_flight;
            end
        endtask

        // Runs seq on the master, then checks that the slave's monitor
        // reported every burst the master returned, beat for beat, in order.
        task run_seq(axr_seq seq);
            axr_item_t seen;
            seq.mem          = slave_cfg.mem;
            seq.error_ranges = slave_cfg.error_ranges;
            clk_vif.wait_reset_release();
            fork
                watch_in_flight();
            join_none
            seq.start(master.sqr);
            repeat (2) clk_vif.sample_edge();
            disable fork;
            if (seq.responses.size() != seq.n) begin
                `uvm_error("LB_AXR", $sformatf("%0d bursts sent, %0d returned", seq.n, seq.responses.size()))
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
        endtask
    endclass : axr_pair_test

    // 200 random bursts of every type and size up to the 32-bit bus, with up
    // to four outstanding, arready and rready each high on 70 percent of
    // clocks, a response delay of up to three clocks, and an error range at
    // 'h3000 to 'h30ff. Also checks the beat addresses of three bursts
    // against worked examples of the AXI address rules, since the sequence
    // checks every beat through the same function. With the slave's reorder
    // set, at least one burst must be served ahead of an older one.
    class axi_read_random_test extends axr_pair_test;
        `uvm_component_utils(axi_read_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axr_config_t master_cfg, axr_config_t slave_cfg);
            master_cfg.max_outstanding = 4;
            master_cfg.rready_pct      = 70;
            slave_cfg.arready_pct      = 70;
            slave_cfg.resp_delay_max   = 3;
            slave_cfg.error_ranges.push_back('{lo: 64'h3000, hi: 64'h30ff});
        endfunction

        function void check_beats(string what, bit [63:0] start, bit [2:0] size, bit [7:0] len, axi_burst_e burst,
                                  bit [63:0] want_addr[4], int unsigned want_bytes[4]);
            bit [63:0]   addr;
            int unsigned bytes;
            for (int unsigned n = 0; n <= len; n++) begin
                axi_beat(start, size, len, burst, n, addr, bytes);
                if (addr != want_addr[n] || bytes != want_bytes[n]) begin
                    `uvm_error("LB_AXR", $sformatf("%s beat %0d: address 0x%0h with %0d bytes, expected 0x%0h with %0d",
                                                   what, n, addr, bytes, want_addr[n], want_bytes[n]))
                end
            end
        endfunction

        virtual task run_phase(uvm_phase phase);
            axr_seq seq = axr_seq::type_id::create("seq");
            phase.raise_objection(this);
            check_beats("WRAP 4x4 at 'h38", 'h38, 2, 3, AXI_WRAP, '{'h38, 'h3c, 'h30, 'h34}, '{4, 4, 4, 4});
            check_beats("INCR 4x4 at 'h07", 'h07, 2, 3, AXI_INCR, '{'h07, 'h08, 'h0c, 'h10}, '{1, 4, 4, 4});
            check_beats("FIXED 3x4 at 'h05", 'h05, 2, 2, AXI_FIXED, '{'h05, 'h05, 'h05, 0}, '{3, 3, 3, 0});
            seq.n = 200;
            run_seq(seq);
            `uvm_info("LB_STATS", $sformatf("%0d bursts (%0d FIXED, %0d INCR, %0d WRAP; %0d narrow, %0d unaligned), %0d beats, %0d SLVERR, at most %0d outstanding, %0d served out of AR order",
                                            seq.responses.size(), seq.bursts[AXI_FIXED], seq.bursts[AXI_INCR],
                                            seq.bursts[AXI_WRAP], seq.narrow, seq.unaligned, seq.beats,
                                            seq.slverr_beats, peak, seq.reordered), UVM_NONE)
            if (peak != 4) `uvm_error("LB_AXR", $sformatf("max_outstanding is 4, but at most %0d bursts were outstanding", peak))
            foreach (seq.bursts[b]) begin
                if (seq.bursts[b] == 0) `uvm_error("LB_AXR", $sformatf("no %s burst", b.name()))
            end
            if (seq.bursts.num() != 3) `uvm_error("LB_AXR", "not every burst type was sent")
            if (seq.narrow == 0 || seq.unaligned == 0 || seq.slverr_beats == 0) begin
                `uvm_error("LB_AXR", "the bursts covered no narrow transfer, no unaligned start or no error range")
            end
            if (slave_cfg.reorder && seq.reordered == 0) `uvm_error("LB_AXR", "reorder is set, but every burst came in AR order")
            if (!slave_cfg.reorder && seq.reordered != 0) begin
                `uvm_error("LB_AXR", $sformatf("reorder is clear, but %0d bursts came out of AR order", seq.reordered))
            end
            phase.drop_objection(this);
        endtask
    endclass : axi_read_random_test

    // As axi_read_random_test, with the slave serving ready bursts in a
    // random order that keeps each ID's bursts in AR order, and response
    // delays of up to eight clocks so that several IDs are ready at once.
    // The master and the monitor must each give a beat to the oldest open
    // burst of its rid.
    class axi_read_reorder_test extends axi_read_random_test;
        `uvm_component_utils(axi_read_reorder_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axr_config_t master_cfg, axr_config_t slave_cfg);
            super.configure(master_cfg, slave_cfg);
            slave_cfg.reorder        = 1'b1;
            slave_cfg.resp_delay_max = 8;
        endfunction
    endclass : axi_read_reorder_test

    // As axi_read_random_test, but every burst goes out through one item
    // object, randomised again before each send while up to three earlier
    // bursts are still outstanding. Each response must still carry the
    // address, ID and shape of its own burst, and its beats the memory's.
    class axi_read_reuse_test extends axr_pair_test;
        `uvm_component_utils(axi_read_reuse_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axr_config_t master_cfg, axr_config_t slave_cfg);
            master_cfg.max_outstanding = 4;
            slave_cfg.resp_delay_min   = 2;
            slave_cfg.resp_delay_max   = 6;
        endfunction

        virtual task run_phase(uvm_phase phase);
            axr_seq seq = axr_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n     = 100;
            seq.reuse = 1'b1;
            run_seq(seq);
            `uvm_info("LB_STATS", $sformatf("%0d bursts through one item, %0d beats checked, at most %0d outstanding",
                                            seq.responses.size(), seq.beats, peak), UVM_NONE)
            if (peak < 2) `uvm_error("LB_AXR", $sformatf("the item was never reused with a burst outstanding (peak %0d)", peak))
            for (int unsigned i = 1; i < seq.responses.size(); i++) begin
                if (seq.responses[i] == seq.responses[i - 1]) begin
                    `uvm_error("LB_AXR", $sformatf("responses %0d and %0d are one object", i - 1, i))
                end
            end
            phase.drop_objection(this);
        endtask
    endclass : axi_read_reuse_test

    // max_transfer_bytes 16 on the master's port. Every item new_item()
    // gives must randomise to at most 16 bytes, with some at exactly 16,
    // and the bursts must complete. An item made without new_item() has no
    // limit, so some of those randomise above 16 bytes, which shows the limit
    // comes from the port. Last, one such item over the limit goes to the
    // master, which must refuse it.
    class axr_limit_seq extends axr_seq;
        `uvm_object_utils(axr_limit_seq)

        function new(string name = "axr_limit_seq");
            super.new(name);
        endfunction

        virtual function void pick(axr_item_t it);
            if (!it.randomize()) `uvm_fatal("LB_RAND", "axi_read item randomize failed")
        endfunction
    endclass : axr_limit_seq

    // Sends one item as given and keeps its response.
    class axr_one_seq extends axr_base_seq_t;
        axr_item_t it;
        axr_item_t rsp;

        `uvm_object_utils(axr_one_seq)

        function new(string name = "axr_one_seq");
            super.new(name);
        endfunction

        virtual task body();
            send(it);
            wait_for_reads();
        endtask

        virtual function void read_done(item_t rsp);
            this.rsp = rsp;
        endfunction
    endclass : axr_one_seq

    class axi_read_max_transfer_test extends axr_pair_test;
        `uvm_component_utils(axi_read_max_transfer_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure(axr_config_t master_cfg, axr_config_t slave_cfg);
            master_cfg.max_transfer_bytes = 16;
            master_cfg.max_outstanding    = 2;
        endfunction

        virtual task run_phase(uvm_phase phase);
            axr_limit_seq seq = axr_limit_seq::type_id::create("seq");
            axr_item_t    free_item = axr_item_t::type_id::create("free_item");
            int unsigned  over = 0;
            int unsigned  at_limit = 0;
            phase.raise_objection(this);
            repeat (50) begin
                if (!free_item.randomize()) `uvm_fatal("LB_RAND", "axi_read item randomize failed")
                if (free_item.total_bytes() > 16) over++;
            end
            if (over == 0) `uvm_error("LB_AXR", "50 items with no limit all randomised to 16 bytes or fewer")
            seq.n = 200;
            run_seq(seq);
            foreach (seq.responses[i]) begin
                if (seq.responses[i].total_bytes() > 16) begin
                    `uvm_error("LB_AXR", $sformatf("%s moves %0d bytes, above max_transfer_bytes 16",
                                                   seq.responses[i].convert2string(), seq.responses[i].total_bytes()))
                end
                if (seq.responses[i].total_bytes() == 16) at_limit++;
            end
            `uvm_info("LB_STATS", $sformatf("%0d bursts within 16 bytes, %0d at exactly 16; %0d of 50 unlimited items above 16",
                                            seq.responses.size(), at_limit, over), UVM_NONE)
            if (at_limit == 0) `uvm_error("LB_AXR", "no burst reached max_transfer_bytes")
            send_over_limit();
            phase.drop_objection(this);
        endtask

        // A 32-byte item made with type_id::create, so no constraint holds it
        // to the port's 16. The master must report exactly one A2C_CFG error,
        // complete it with no beats, and leave the bus without an AR.
        task send_over_limit();
            axr_one_seq        one = axr_one_seq::type_id::create("one");
            a2c_error_demoter  demoter = a2c_error_demoter::type_id::create("demoter");
            int unsigned       ars = 0;
            demoter.demote_id = "A2C_CFG";
            uvm_report_cb::add(null, demoter);
            one.it       = axr_item_t::type_id::create("over");
            one.it.addr  = 'h100;
            one.it.len   = 7;
            one.it.size  = 2;
            one.it.burst = AXI_INCR;
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (vif.arvalid === 1'b1 && vif.arready === 1'b1) ars++;
                end
            join_none
            one.start(master.sqr);
            repeat (4) clk_vif.sample_edge();
            disable fork;
            uvm_report_cb::delete(null, demoter);
            `uvm_info("LB_STATS", $sformatf("a %0d-byte item over the 16-byte limit: %0d A2C_CFG, %0d ARs, %0d beats returned",
                                            one.it.total_bytes(), demoter.demoted, ars,
                                            one.rsp == null ? -1 : one.rsp.data.size()), UVM_NONE)
            if (demoter.demoted != 1) `uvm_error("LB_AXR", $sformatf("expected one A2C_CFG error, caught %0d", demoter.demoted))
            if (ars != 0) `uvm_error("LB_AXR", $sformatf("the over-limit item put %0d ARs on the bus", ars))
            if (one.rsp == null || one.rsp.data.size() != 0) `uvm_error("LB_AXR", "the over-limit item did not return with no beats")
            if (observed.used() != 0) `uvm_error("LB_EXTRA", "the slave's monitor reported a burst for the over-limit item")
        endtask
    endclass : axi_read_max_transfer_test

    // A passive monitor watches pins the test drives by hand, both master
    // and slave: a clean two-beat burst; an AR whose araddr changes while
    // arready is low; an AR whose arvalid drops before arready; a beat whose
    // rdata changes while rready is low; a beat whose rvalid drops before
    // rready; rlast on the first beat of a two-beat burst; a beat whose rid
    // matches no AR; a three-beat WRAP burst; an INCR burst across a 4 KB
    // boundary; the reserved arburst 2'b11; an 8-byte arsize on the 32-bit
    // bus; a 17-beat FIXED burst; and a WRAP burst from an address not
    // aligned to its 4-byte transfers. Expects exactly four A2C_HOLD and
    // eight A2C_PROTO reports, demoted to info, and eleven bursts reported
    // with the addresses that transferred.
    class axi_read_monitor_checks_test extends lb_base_test;
        axr_agent_t                         obs;
        uvm_tlm_analysis_fifo #(axr_item_t) observed;
        axr_vif_t                           vif;

        `uvm_component_utils(axi_read_monitor_checks_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            axr_config_t cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(axr_vif_t)::get(this, "", "axr", vif)) `uvm_fatal("LB_CFG", "no virtual axi_read_if 'axr'")
            cfg = axr_config_t::type_id::create("cfg");
            cfg.vif       = vif;
            cfg.clk_vif   = clk_vif;
            cfg.is_active = UVM_PASSIVE;
            cfg.role      = A2C_DST;
            cfg.port_name = "axr";
            uvm_config_db#(axr_config_t)::set(this, "obs", "cfg", cfg);
            obs      = axr_agent_t::type_id::create("obs", this);
            observed = new("observed", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            obs.mon.ap.connect(observed.analysis_export);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_PROTO", UVM_INFO);
            obs.mon.set_report_severity_id_override(UVM_ERROR, "A2C_HOLD", UVM_INFO);
        endfunction

        // Sets the AR pins for the next clock.
        task ar(bit valid, bit ready, bit [1:0] id = 0, bit [15:0] addr = 0, bit [7:0] len = 0,
                         bit [2:0] size = 2, axi_burst_e burst = AXI_INCR);
            vif.arvalid <= valid;
            vif.arready <= ready;
            vif.arid    <= id;
            vif.araddr  <= lb_axr_addr_t'(addr);
            vif.arlen   <= len;
            vif.arsize  <= size;
            vif.arburst <= burst;
            vif.aruser  <= '0;
        endtask

        // Sets the R pins for the next clock.
        task r(bit valid, bit ready, bit [1:0] id = 0, bit [31:0] data = 0, bit last = 0);
            vif.rvalid <= valid;
            vif.rready <= ready;
            vif.rid    <= id;
            vif.rdata  <= lb_axr_data_t'(data);
            vif.rresp  <= AXI_OKAY;
            vif.rlast  <= last;
            vif.ruser  <= '0;
        endtask

        task tick(int unsigned n = 1);
            repeat (n) clk_vif.drive_edge();
        endtask

        task idle();
            ar(0, 0);
            r(0, 0);
            tick();
        endtask

        virtual task run_phase(uvm_phase phase);
            axr_item_t   seen;
            bit [15:0]   want[$] = {'h100, 'h200, 'h300, 'h400, 'h500, 'h600, 'hff8, 'h700, 'h800, 'h900, 'ha02};
            int unsigned n = 0;
            phase.raise_objection(this);
            ar(0, 0);
            r(0, 0);
            clk_vif.wait_reset_release();
            tick();
            ar(1, 1, 0, 'h100, 1); r(0, 0); tick();                // clean two-beat burst
            ar(0, 0); r(1, 1, 0, 'h11, 0); tick();
            r(1, 1, 0, 'h12, 1); tick();
            idle();
            ar(1, 0, 1, 'h1f0); r(0, 0); tick();                    // araddr changes while stalled
            ar(1, 1, 1, 'h200); tick();
            ar(0, 0); r(1, 1, 1, 'h21, 1); tick();
            idle();
            ar(1, 0, 1, 'h280); tick();                             // arvalid drops before arready
            ar(0, 0); tick();
            idle();
            ar(1, 1, 0, 'h300); tick();                             // rdata changes while stalled
            ar(0, 0); r(1, 0, 0, 'h31, 1); tick();
            r(1, 1, 0, 'h32, 1); tick();
            idle();
            ar(1, 1, 0, 'h400); tick();                             // rvalid drops before rready
            ar(0, 0); r(1, 0, 0, 'h41, 1); tick();
            r(0, 0); tick();
            r(1, 1, 0, 'h41, 1); tick();
            idle();
            ar(1, 1, 2, 'h500, 1); tick();                          // rlast on the first of two beats
            ar(0, 0); r(1, 1, 2, 'h51, 1); tick();
            idle();
            r(1, 1, 3, 'h99, 1); tick();                            // rid matches no AR
            idle();
            ar(1, 1, 0, 'h600, 2, 2, AXI_WRAP); tick();             // three-beat WRAP
            ar(0, 0); r(1, 1, 0, 'h61, 0); tick();
            r(1, 1, 0, 'h62, 0); tick();
            r(1, 1, 0, 'h63, 1); tick();
            idle();
            ar(1, 1, 0, 'hff8, 3); tick();                          // 16 bytes from 'hff8
            ar(0, 0); r(1, 1, 0, 'h71, 0); tick();
            r(1, 1, 0, 'h72, 0); tick();
            r(1, 1, 0, 'h73, 0); tick();
            r(1, 1, 0, 'h74, 1); tick();
            idle();
            ar(1, 1, 0, 'h700, 0, 2, axi_burst_e'(2'b11)); tick();  // reserved arburst
            ar(0, 0); r(1, 1, 0, 'h81, 1); tick();
            idle();
            ar(1, 1, 0, 'h800, 0, 3); tick();                       // 8-byte arsize on the 32-bit bus
            ar(0, 0); r(1, 1, 0, 'h91, 1); tick();
            idle();
            ar(1, 1, 0, 'h900, 16, 2, AXI_FIXED); tick();           // 17-beat FIXED
            ar(0, 0);
            for (int unsigned i = 0; i < 17; i++) begin
                r(1, 1, 0, 'ha0 + i, i == 16); tick();
            end
            idle();
            ar(1, 1, 0, 'ha02, 3, 2, AXI_WRAP); tick();             // WRAP from an address not 4-byte aligned
            ar(0, 0); r(1, 1, 0, 'hb1, 0); tick();
            r(1, 1, 0, 'hb2, 0); tick();
            r(1, 1, 0, 'hb3, 0); tick();
            r(1, 1, 0, 'hb4, 1); tick();
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
            if (proto != 8) `uvm_error("LB_CHECKS", $sformatf("expected 8 A2C_PROTO reports, got %0d", proto))
            if (hold != 4) `uvm_error("LB_CHECKS", $sformatf("expected 4 A2C_HOLD reports, got %0d", hold))
        endfunction
    endclass : axi_read_monitor_checks_test
