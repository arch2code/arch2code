// raw agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef raw_agent #(.data_t(lb_data_t)) raw_agent_t;
    typedef raw_agent_t::item_t raw_item_t;
    typedef raw_agent_t::config_t raw_config_t;
    typedef virtual raw_if #(.data_t(lb_data_t)) raw_vif_t;

    class raw_seq extends uvm_sequence #(raw_item_t);
        int unsigned               n;
        lb_scoreboard#(raw_item_t) sb;

        `uvm_object_utils(raw_seq)

        function new(string name = "raw_seq");
            super.new(name);
        endfunction

        // Every item is expected before the first goes out, so a clock that
        // repeats an item meets the next one in the scoreboard. A non-zero
        // value keeps the first item apart from the idle value.
        virtual task body();
            raw_item_t items[$];
            raw_item_t it;
            repeat (n) begin
                it = raw_item_t::type_id::create("it");
                if (!it.randomize() with { data.value != 0; }) `uvm_fatal("LB_RAND", "raw item randomize failed")
                items.push_back(it);
                sb.expected.push_back(it);
            end
            foreach (items[i]) begin
                start_item(items[i]);
                finish_item(items[i]);
            end
        endtask
    endclass : raw_seq

    // A raw src agent puts one item on data per clock and a passive dst
    // agent reports data every clock. Checks the items arrive on consecutive
    // clocks in order.
    class raw_test extends lb_base_test;
        raw_agent_t                src;
        raw_agent_t                dst;
        lb_scoreboard#(raw_item_t) sb;

        `uvm_component_utils(raw_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            raw_config_t src_cfg;
            raw_config_t dst_cfg;
            raw_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(raw_vif_t)::get(this, "", "raw", vif)) `uvm_fatal("LB_CFG", "no virtual raw_if 'raw'")
            src_cfg = raw_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "raw";
            dst_cfg = raw_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "raw";
            uvm_config_db#(raw_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(raw_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = raw_agent_t::type_id::create("src", this);
            dst = raw_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(raw_item_t)::type_id::create("sb", this);
            sb.free_running = 1;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            raw_seq seq = raw_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n  = n_items;
            seq.sb = sb;
            clk_vif.wait_reset_release();
            seq.start(src.sqr);
            wait_matched(sb, n_items, 10);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d items on consecutive clocks", sb.matched), UVM_NONE)
        endfunction
    endclass : raw_test
