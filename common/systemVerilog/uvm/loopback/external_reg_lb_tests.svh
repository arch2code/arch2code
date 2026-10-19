// external_reg agent loopback tests, included in a2c_uvm_loopback_pkg after
// the scoreboard and the base test.

    typedef external_reg_agent #(.data_t(lb_data_t)) er_agent_t;
    typedef er_agent_t::item_t er_item_t;
    typedef er_agent_t::config_t er_config_t;
    typedef virtual external_reg_if #(.data_t(lb_data_t)) er_vif_t;

    // Sends each item of items as it is.
    class er_seq extends uvm_sequence #(er_item_t);
        er_item_t items[$];

        `uvm_object_utils(er_seq)

        function new(string name = "er_seq");
            super.new(name);
        endfunction

        virtual task body();
            foreach (items[i]) begin
                start_item(items[i]);
                finish_item(items[i]);
            end
        endtask
    endclass : er_seq

    // A src agent and a dst agent on er. The dst agent's monitor feeds sb with
    // its writes and level_sb with its rdata levels.
    virtual class er_pair_test extends lb_base_test;
        er_agent_t                src;
        er_agent_t                dst;
        er_config_t               dst_cfg;
        lb_scoreboard#(er_item_t) sb;
        lb_scoreboard#(er_item_t) level_sb;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(er_config_t cfg);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            er_config_t src_cfg;
            er_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(er_vif_t)::get(this, "", "er", vif)) `uvm_fatal("LB_CFG", "no virtual external_reg_if 'er'")
            src_cfg = er_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "er";
            dst_cfg = er_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "er";
            configure_dst(dst_cfg);
            uvm_config_db#(er_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(er_config_t)::set(this, "dst", "cfg", dst_cfg);
            src      = er_agent_t::type_id::create("src", this);
            dst      = er_agent_t::type_id::create("dst", this);
            sb       = lb_scoreboard#(er_item_t)::type_id::create("sb", this);
            level_sb = lb_scoreboard#(er_item_t)::type_id::create("level_sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
            dst.mon.rdata_ap.connect(level_sb.imp);
        endfunction

        function er_item_t write_item(bit [1:0] write, lb_data_t wdata, int unsigned gap);
            er_item_t it = er_item_t::type_id::create("it");
            it.write = write;
            it.wdata = wdata;
            it.gap   = gap;
            return it;
        endfunction

        function void expect_level(lb_data_t value);
            er_item_t it = er_item_t::type_id::create("level");
            it.write = '0;
            it.rdata = value;
            level_sb.expected.push_back(it);
        endfunction
    endclass : er_pair_test

    // n_items writes with strobes 1, 2 and 3 and gaps of 0 to 2 clocks, so
    // some go out back to back. The dst agent loads each one, so after the
    // reset value 0 the rdata levels the monitor reports are the written
    // words in order, and each must be on rdata at the sample one clock
    // after its write.
    class external_reg_strobe_test extends er_pair_test;
        int unsigned one_clock;

        `uvm_component_utils(external_reg_strobe_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        protected task watch_one_clock(er_vif_t vif);
            bit       pending;
            lb_data_t want;
            forever begin
                clk_vif.sample_edge();
                if (pending) begin
                    if (vif.rdata === want) begin
                        one_clock++;
                    end else begin
                        `uvm_error("LB_ER", $sformatf("rdata is 0x%0h one clock after the write of 0x%0h", vif.rdata, want))
                    end
                end
                pending = vif.write !== '0;
                want    = vif.wdata;
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            er_seq       seq = er_seq::type_id::create("seq");
            lb_data_t    level = '0;
            int unsigned back_to_back;
            phase.raise_objection(this);
            expect_level('0);
            for (int unsigned i = 0; i < n_items; i++) begin
                lb_data_t    wdata = lb_data_t'($urandom());
                int unsigned gap = $urandom_range(2, 0);
                if (wdata == level) wdata = ~wdata;
                if (gap == 0) back_to_back++;
                seq.items.push_back(write_item(2'($urandom_range(3, 1)), wdata, gap));
                sb.expected.push_back(seq.items[i]);
                expect_level(wdata);
                level = wdata;
            end
            clk_vif.wait_reset_release();
            fork
                watch_one_clock(src.cfg.vif);
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 4 * n_items);
            wait_matched(level_sb, n_items + 1, 10);
            // The last level and the watcher's check share a sample edge.
            clk_vif.drive_edge();
            disable fork;
            if (one_clock != n_items) begin
                `uvm_error("LB_ER", $sformatf("%0d writes, %0d on rdata one clock later", n_items, one_clock))
            end
            `uvm_info("LB_STATS", $sformatf("%0d writes, %0d back to back, %0d rdata levels, %0d one clock after their write",
                                            sb.matched, back_to_back, level_sb.matched, one_clock), UVM_NONE)
            phase.drop_objection(this);
        endtask
    endclass : external_reg_strobe_test

    // The dst agent holds rdata at cfg.value with update_on_write off. The
    // test sets four values, with a write between each, and rdata must take
    // each value and nothing the writes carried.
    class external_reg_level_test extends er_pair_test;
        `uvm_component_utils(external_reg_level_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void configure_dst(er_config_t cfg);
            cfg.update_on_write = 0;
            cfg.value           = lb_data_t'(24'h11_2233);
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_data_t values[4] = '{lb_data_t'(24'h44_5566), lb_data_t'(24'h77_8899), lb_data_t'(24'h0), lb_data_t'(24'hAA_BBCC)};
            phase.raise_objection(this);
            expect_level(dst_cfg.value);
            foreach (values[i]) expect_level(values[i]);
            clk_vif.wait_reset_release();
            foreach (values[i]) begin
                er_seq seq = er_seq::type_id::create("seq");
                seq.items.push_back(write_item(2'b01, ~values[i], 0));
                sb.expected.push_back(seq.items[0]);
                seq.start(src.sqr);
                repeat (3) clk_vif.drive_edge();
                dst_cfg.value = values[i];
                repeat (3) clk_vif.drive_edge();
            end
            wait_matched(sb, 4, 10);
            wait_matched(level_sb, 5, 10);
            `uvm_info("LB_STATS", $sformatf("%0d writes, %0d rdata levels", sb.matched, level_sb.matched), UVM_NONE)
            phase.drop_objection(this);
        endtask
    endclass : external_reg_level_test
