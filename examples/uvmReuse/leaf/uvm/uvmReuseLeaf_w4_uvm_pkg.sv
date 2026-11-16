// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeaf --variant=w4
// GENERATED_CODE_BEGIN --template=uvmPkg --section=header

package uvmReuseLeaf_w4_uvm_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import rdy_vld_uvm_pkg::*;
    import apb_uvm_pkg::*;
    // Generated Import package statement(s)
    import uvmReuseLeaf_package::*;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=uvmPkg --section=items

    localparam UVM_REUSE_OFF_W = 4;
    typedef logic[UVM_REUSE_OFF_W-1:0] uvmReuseOffT; //Offset added to each pixel
    typedef struct packed {
        uvmReuseOffT offset; //Added to each pixel
    } uvmReuseOffSt;

    typedef rdy_vld_agent #(.data_t(uvmReuseBeatSt)) in_agent_t;
    typedef in_agent_t::item_t in_item_t;
    typedef in_agent_t::config_t in_config_t;
    typedef virtual rdy_vld_if #(.data_t(uvmReuseBeatSt)) in_vif_t;
    typedef rdy_vld_agent #(.data_t(uvmReuseBeatSt)) out_agent_t;
    typedef out_agent_t::item_t out_item_t;
    typedef out_agent_t::config_t out_config_t;
    typedef virtual rdy_vld_if #(.data_t(uvmReuseBeatSt)) out_vif_t;
    typedef apb_agent #(.addr_t(uvmReuseAddrSt), .data_t(uvmReuseDataSt)) apbReg_agent_t;
    typedef apbReg_agent_t::item_t apbReg_item_t;
    typedef apbReg_agent_t::config_t apbReg_config_t;
    typedef virtual apb_if #(.addr_t(uvmReuseAddrSt), .data_t(uvmReuseDataSt)) apbReg_vif_t;

    class uvmReuseLeaf_reg_offset extends uvm_reg;
        rand uvm_reg_field offset;

        `uvm_object_utils(uvmReuseLeaf_reg_offset)

        function new(string name = "offset");
            super.new(name, 4, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            offset = uvm_reg_field::type_id::create("offset");
            offset.configure(this, 4, 0, "RW", 0, 4'h1, 1, 1, 0);
        endfunction
    endclass : uvmReuseLeaf_reg_offset

    class uvmReuseLeaf_reg_block extends uvm_reg_block;
        rand uvmReuseLeaf_reg_offset offset;

        `uvm_object_utils(uvmReuseLeaf_reg_block)

        function new(string name = "uvmReuseLeaf_reg_block");
            super.new(name, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            offset = uvmReuseLeaf_reg_offset::type_id::create("offset");
            offset.configure(this);
            offset.build();
            default_map = create_map("default_map", 'h0, 4, UVM_LITTLE_ENDIAN, 1);
            default_map.add_reg(offset, 'h0, "RW");
            if (get_parent() == null) begin
                lock_model();
            end
        endfunction
    endclass : uvmReuseLeaf_reg_block

    class uvmReuseLeaf_env extends uvm_env;
        in_agent_t in_agent;
        out_agent_t out_agent;
        apbReg_agent_t apbReg_agent;
        a2c_uvm_pkg::a2c_txn_counter #(out_item_t) out_counter;
        a2c_uvm_pkg::a2c_txn_digest #(in_item_t) in_digest;
        a2c_uvm_pkg::a2c_txn_digest #(out_item_t) out_digest;
        a2c_uvm_pkg::a2c_txn_digest #(apbReg_item_t) apbReg_digest;
        virtual a2c_clk_if clk_vif;
        uvmReuseLeaf_reg_block regmodel;
        apb_reg_adapter adapter;
        uvm_reg_predictor #(apbReg_item_t) predictor;
        // Mode B, set from a2c_dual_dut: each agent also drives and monitors
        // the model DUT's <port>_model pins, and comparators lists the agents'
        // model_cmp comparators.
        bit dual_dut;
        a2c_uvm_pkg::a2c_comparator_base comparators[$];
        a2c_uvm_pkg::a2c_midstream_guard guard;
        a2c_uvm_pkg::a2c_reg_write_subscriber #(apbReg_item_t) reg_writes;

        `uvm_component_utils(uvmReuseLeaf_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            in_config_t in_cfg;
            out_config_t out_cfg;
            apbReg_config_t apbReg_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(bit)::get(this, "", "a2c_dual_dut", dual_dut)) begin
                `uvm_fatal("A2C_CFG", "no a2c_dual_dut setting")
            end
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual a2c_clk_if 'clk'")
            end

            in_cfg = in_config_t::type_id::create("in_cfg");
            if (!uvm_config_db#(in_vif_t)::get(this, "", "in", in_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual rdy_vld_if 'in'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(in_vif_t)::get(this, "", "in_model", in_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual rdy_vld_if 'in_model'")
                end
            end
            in_cfg.clk_vif = clk_vif;
            in_cfg.role = a2c_uvm_pkg::A2C_SRC;
            in_cfg.port_name = "in";
            in_cfg.no_backpressure = 0;
            uvm_config_db#(in_config_t)::set(this, "in_agent", "cfg", in_cfg);
            in_agent = in_agent_t::type_id::create("in_agent", this);
            in_digest = a2c_uvm_pkg::a2c_txn_digest#(in_item_t)::type_id::create("in_digest", this);
            in_digest.port_name = "in";
            in_digest.dual = dual_dut;

            out_cfg = out_config_t::type_id::create("out_cfg");
            if (!uvm_config_db#(out_vif_t)::get(this, "", "out", out_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual rdy_vld_if 'out'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(out_vif_t)::get(this, "", "out_model", out_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual rdy_vld_if 'out_model'")
                end
            end
            out_cfg.clk_vif = clk_vif;
            out_cfg.role = a2c_uvm_pkg::A2C_DST;
            out_cfg.port_name = "out";
            out_cfg.no_backpressure = 0;
            uvm_config_db#(out_config_t)::set(this, "out_agent", "cfg", out_cfg);
            out_agent = out_agent_t::type_id::create("out_agent", this);
            out_counter = a2c_uvm_pkg::a2c_txn_counter#(out_item_t)::type_id::create("out_counter", this);
            out_counter.port_name = "out";
            out_counter.dual = dual_dut;
            out_digest = a2c_uvm_pkg::a2c_txn_digest#(out_item_t)::type_id::create("out_digest", this);
            out_digest.port_name = "out";
            out_digest.dual = dual_dut;

            apbReg_cfg = apbReg_config_t::type_id::create("apbReg_cfg");
            if (!uvm_config_db#(apbReg_vif_t)::get(this, "", "apbReg", apbReg_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual apb_if 'apbReg'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(apbReg_vif_t)::get(this, "", "apbReg_model", apbReg_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual apb_if 'apbReg_model'")
                end
            end
            apbReg_cfg.clk_vif = clk_vif;
            apbReg_cfg.role = a2c_uvm_pkg::A2C_SRC;
            apbReg_cfg.port_name = "apbReg";
            uvm_config_db#(apbReg_config_t)::set(this, "apbReg_agent", "cfg", apbReg_cfg);
            apbReg_agent = apbReg_agent_t::type_id::create("apbReg_agent", this);
            apbReg_digest = a2c_uvm_pkg::a2c_txn_digest#(apbReg_item_t)::type_id::create("apbReg_digest", this);
            apbReg_digest.port_name = "apbReg";
            apbReg_digest.dual = dual_dut;

            regmodel = uvmReuseLeaf_reg_block::type_id::create("regmodel");
            regmodel.build();
            regmodel.reset();
            adapter = apb_reg_adapter::type_id::create("adapter");
            predictor = uvm_reg_predictor#(apbReg_item_t)::type_id::create("predictor", this);
            if (dual_dut) begin
                guard = a2c_uvm_pkg::a2c_midstream_guard::type_id::create("guard", this);
                reg_writes = a2c_uvm_pkg::a2c_reg_write_subscriber#(apbReg_item_t)::type_id::create("reg_writes", this);
            end
        endfunction

        // The register model's mirror follows the DUT lane's bus through the
        // explicit predictor, not the register calls' own prediction. In Mode B
        // the guard sees every write on the DUT lane's bus, and the bus agent's
        // comparator asks it about each read.
        virtual function void connect_phase(uvm_phase phase);
            out_agent.mon.ap.connect(out_counter.analysis_export);
            in_digest.watch(in_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            out_digest.watch(out_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            apbReg_digest.watch(apbReg_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            regmodel.default_map.set_sequencer(apbReg_agent.sqr, adapter);
            regmodel.default_map.set_auto_predict(0);
            predictor.map     = regmodel.default_map;
            predictor.adapter = adapter;
            apbReg_agent.mon.ap.connect(predictor.bus_in);
            if (dual_dut) begin
                out_agent.model_mon.ap.connect(out_counter.model_export);
                in_digest.watch(in_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                out_digest.watch(out_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                apbReg_digest.watch(apbReg_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                if (in_agent.model_cmp != null) begin
                    comparators.push_back(in_agent.model_cmp);
                    in_digest.cmp = in_agent.model_cmp;
                end
                if (out_agent.model_cmp != null) begin
                    comparators.push_back(out_agent.model_cmp);
                    out_digest.cmp = out_agent.model_cmp;
                end
                if (apbReg_agent.model_cmp != null) begin
                    comparators.push_back(apbReg_agent.model_cmp);
                    apbReg_digest.cmp = apbReg_agent.model_cmp;
                end
                out_agent.model_cmp.counted = 1;
                reg_writes.map     = regmodel.default_map;
                reg_writes.adapter = adapter;
                apbReg_agent.mon.ap.connect(reg_writes.analysis_export);
                reg_writes.ap.connect(guard.analysis_export);
                guard.map = regmodel.default_map;
                apbReg_agent.model_cmp.guard = guard;
                guard.counters.push_back(out_counter);
                guard.comparators = comparators;
            end
        endfunction

        // The base test calls this in Mode B each time wait_for_outputs()
        // returns. A comparator with auto_stable cleared takes its stable
        // points from the user region instead.
        function void model_stable_point();
            foreach (comparators[i]) begin
                if (comparators[i].auto_stable) begin
                    comparators[i].stable_point();
                end
            end
        endfunction
    endclass : uvmReuseLeaf_env

// GENERATED_CODE_END

// user package items here
    `include "uvmReuseLeaf_lib.svh"

// GENERATED_CODE_BEGIN --template=uvmPkg --section=footer

endpackage : uvmReuseLeaf_w4_uvm_pkg

// GENERATED_CODE_END
