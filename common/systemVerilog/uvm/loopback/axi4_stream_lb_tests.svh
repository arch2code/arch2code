// axi4_stream agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    // Four bytes, so tstrb and tkeep are four bits wide.
    typedef struct packed {
        logic [7:0] b3;
        logic [7:0] b2;
        logic [7:0] b1;
        logic [7:0] b0;
    } lb_tdata_t;
    typedef logic [3:0] lb_tid_t;
    typedef logic [2:0] lb_tdest_t;
    typedef logic [1:0] lb_tuser_t;

    typedef axi4_stream_agent #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_agent_t;
    typedef axis_agent_t::item_t axis_item_t;
    typedef axis_agent_t::config_t axis_config_t;
    typedef virtual axi4_stream_if #(.tdata_t(lb_tdata_t), .tid_t(lb_tid_t), .tdest_t(lb_tdest_t), .tuser_t(lb_tuser_t)) axis_vif_t;

    class axis_seq extends uvm_sequence #(axis_item_t);
        int unsigned                n;
        lb_scoreboard#(axis_item_t) sb;

        `uvm_object_utils(axis_seq)

        function new(string name = "axis_seq");
            super.new(name);
        endfunction

        // Every fourth item sets tstrb and tkeep; the rest keep the all-ones
        // default.
        virtual task body();
            axis_item_t it;
            for (int unsigned i = 0; i < n; i++) begin
                it = axis_item_t::type_id::create("it");
                start_item(it);
                if (!it.randomize()) `uvm_fatal("LB_RAND", "axi4_stream item randomize failed")
                if (i % 4 == 3) begin
                    it.tstrb = $urandom();
                    it.tkeep = $urandom();
                end
                it.gap = $urandom_range(2, 0);
                sb.expected.push_back(it);
                finish_item(it);
            end
        endtask
    endclass : axis_seq

    // An axi4_stream src agent drives a dst agent whose tready is random.
    // Checks every field of every beat, and that tstrb and tkeep are all ones
    // on beats that do not set them.
    class axi4_stream_test extends lb_base_test;
        axis_agent_t                src;
        axis_agent_t                dst;
        lb_scoreboard#(axis_item_t) sb;
        axis_config_t               dst_cfg;
        int unsigned                stalls;
        int unsigned                all_ones;

        `uvm_component_utils(axi4_stream_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            axis_config_t src_cfg;
            axis_vif_t    vif;
            super.build_phase(phase);
            if (!uvm_config_db#(axis_vif_t)::get(this, "", "axis", vif)) `uvm_fatal("LB_CFG", "no virtual axi4_stream_if 'axis'")
            src_cfg = axis_config_t::type_id::create("src_cfg");
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = "axis";
            dst_cfg = axis_config_t::type_id::create("dst_cfg");
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = "axis";
            dst_cfg.ready_pct = 50;
            uvm_config_db#(axis_config_t)::set(this, "src", "cfg", src_cfg);
            uvm_config_db#(axis_config_t)::set(this, "dst", "cfg", dst_cfg);
            src = axis_agent_t::type_id::create("src", this);
            dst = axis_agent_t::type_id::create("dst", this);
            sb  = lb_scoreboard#(axis_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        virtual task run_phase(uvm_phase phase);
            axis_seq seq = axis_seq::type_id::create("seq");
            phase.raise_objection(this);
            seq.n  = n_items;
            seq.sb = sb;
            clk_vif.wait_reset_release();
            fork
                forever begin
                    clk_vif.sample_edge();
                    if (dst_cfg.vif.tvalid === 1'b1 && dst_cfg.vif.tready !== 1'b1) stalls++;
                    if (dst_cfg.vif.tvalid === 1'b1 && dst_cfg.vif.tready === 1'b1
                        && &dst_cfg.vif.tstrb === 1'b1 && &dst_cfg.vif.tkeep === 1'b1) all_ones++;
                end
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 100 * n_items);
            disable fork;
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d beats, %0d stalled clocks, %0d beats with all-ones tstrb and tkeep",
                                            sb.matched, stalls, all_ones), UVM_NONE)
            if (stalls == 0) `uvm_error("LB_NO_STALL", "tready never held a beat back, so back-pressure was not exercised")
            if (all_ones < n_items / 2) `uvm_error("LB_STRB", "under half the beats carried all-ones tstrb and tkeep")
        endfunction
    endclass : axi4_stream_test
