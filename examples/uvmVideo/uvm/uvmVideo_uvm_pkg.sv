// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo
// GENERATED_CODE_BEGIN --template=uvmPkg --section=header

package uvmVideo_uvm_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import raw_uvm_pkg::*;
    import axi4_stream_uvm_pkg::*;
    // Generated Import package statement(s)
    import uvmVideo_package::*;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=uvmPkg --section=items

    typedef raw_agent #(.data_t(uvmVideoRawSt)) vin_agent_t;
    typedef vin_agent_t::item_t vin_item_t;
    typedef vin_agent_t::config_t vin_config_t;
    typedef virtual raw_if #(.data_t(uvmVideoRawSt)) vin_vif_t;
    typedef axi4_stream_agent #(.tdata_t(uvmVideoBeatSt), .tid_t(uvmVideoIdSt), .tdest_t(uvmVideoIdSt), .tuser_t(uvmVideoUserSt)) vout_agent_t;
    typedef vout_agent_t::item_t vout_item_t;
    typedef vout_agent_t::config_t vout_config_t;
    typedef virtual axi4_stream_if #(.tdata_t(uvmVideoBeatSt), .tid_t(uvmVideoIdSt), .tdest_t(uvmVideoIdSt), .tuser_t(uvmVideoUserSt)) vout_vif_t;

    class uvmVideo_env extends uvm_env;
        vin_agent_t vin_agent;
        vout_agent_t vout_agent;
        a2c_uvm_pkg::a2c_txn_counter #(vout_item_t) vout_counter;
        virtual a2c_clk_if clk_vif;
        // Mode B, set from a2c_dual_dut: each agent also drives and monitors
        // the model DUT's <port>_model pins, and comparators lists the agents'
        // model_cmp comparators.
        bit dual_dut;
        a2c_uvm_pkg::a2c_comparator_base comparators[$];

        `uvm_component_utils(uvmVideo_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            vin_config_t vin_cfg;
            vout_config_t vout_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(bit)::get(this, "", "a2c_dual_dut", dual_dut)) begin
                `uvm_fatal("A2C_CFG", "no a2c_dual_dut setting")
            end
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual a2c_clk_if 'clk'")
            end

            vin_cfg = vin_config_t::type_id::create("vin_cfg");
            if (!uvm_config_db#(vin_vif_t)::get(this, "", "vin", vin_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual raw_if 'vin'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(vin_vif_t)::get(this, "", "vin_model", vin_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual raw_if 'vin_model'")
                end
            end
            vin_cfg.clk_vif = clk_vif;
            vin_cfg.role = a2c_uvm_pkg::A2C_SRC;
            vin_cfg.port_name = "vin";
            uvm_config_db#(vin_config_t)::set(this, "vin_agent", "cfg", vin_cfg);
            vin_agent = vin_agent_t::type_id::create("vin_agent", this);

            vout_cfg = vout_config_t::type_id::create("vout_cfg");
            if (!uvm_config_db#(vout_vif_t)::get(this, "", "vout", vout_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual axi4_stream_if 'vout'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(vout_vif_t)::get(this, "", "vout_model", vout_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual axi4_stream_if 'vout_model'")
                end
            end
            vout_cfg.clk_vif = clk_vif;
            vout_cfg.role = a2c_uvm_pkg::A2C_DST;
            vout_cfg.port_name = "vout";
            vout_cfg.no_backpressure = 1;
            uvm_config_db#(vout_config_t)::set(this, "vout_agent", "cfg", vout_cfg);
            vout_agent = vout_agent_t::type_id::create("vout_agent", this);
            vout_counter = a2c_uvm_pkg::a2c_txn_counter#(vout_item_t)::type_id::create("vout_counter", this);
            vout_counter.port_name = "vout";
            vout_counter.dual = dual_dut;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            vout_agent.mon.ap.connect(vout_counter.analysis_export);
            if (dual_dut) begin
                vout_agent.model_mon.ap.connect(vout_counter.model_export);
                if (vin_agent.model_cmp != null) begin
                    comparators.push_back(vin_agent.model_cmp);
                end
                if (vout_agent.model_cmp != null) begin
                    comparators.push_back(vout_agent.model_cmp);
                end
                vout_agent.model_cmp.counted = 1;
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
    endclass : uvmVideo_env

// GENERATED_CODE_END

// user package items here

// GENERATED_CODE_BEGIN --template=uvmPkg --section=footer

endpackage : uvmVideo_uvm_pkg

// GENERATED_CODE_END
