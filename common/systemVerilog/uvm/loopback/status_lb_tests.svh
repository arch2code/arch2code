// status agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef status_agent #(.data_t(lb_data_t)) st_agent_t;
    typedef st_agent_t::item_t st_item_t;
    typedef st_agent_t::config_t st_config_t;
    typedef virtual status_if #(.data_t(lb_data_t)) st_vif_t;

    // A status src agent holds data at its config value and a passive dst
    // agent reports each change. The test changes the value every few clocks
    // and checks every value is reported once, in order.
    class status_test extends lb_base_test;
        st_agent_t                src;
        st_agent_t                dst;
        lb_scoreboard#(st_item_t) sb;
        st_config_t               src_cfg;

        `uvm_component_utils(status_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            st_config_t dst_cfg;
            st_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(st_vif_t)::get(this, "", "st", vif)) `uvm_fatal("LB_CFG", "no virtual status_if 'st'")
            src_cfg = st_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "st";
            src_cfg.value     = lb_data_t'($urandom());
            dst_cfg = st_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "st";
            uvm_config_db#(st_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(st_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = st_agent_t::type_id::create("src", this);
            dst = st_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(st_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        function void expect_value(lb_data_t value);
            st_item_t it = st_item_t::type_id::create("it");
            it.data = value;
            sb.expected.push_back(it);
        endfunction

        // The value driven through reset is the first one reported.
        virtual task run_phase(uvm_phase phase);
            lb_data_t next;
            int unsigned changes = n_items / 8;
            phase.raise_objection(this);
            expect_value(src_cfg.value);
            clk_vif.wait_reset_release();
            repeat (changes) begin
                repeat ($urandom_range(5, 2)) clk_vif.sample_edge();
                do next = lb_data_t'($urandom()); while (next === src_cfg.value);
                expect_value(next);
                src_cfg.value = next;
            end
            wait_matched(sb, changes + 1, 10);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d values reported", sb.matched), UVM_NONE)
        endfunction
    endclass : status_test
