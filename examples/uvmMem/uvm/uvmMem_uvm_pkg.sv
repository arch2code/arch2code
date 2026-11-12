// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=uvmPkg --section=header

package uvmMem_uvm_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import rdy_vld_uvm_pkg::*;
    import memory_uvm_pkg::*;
    // Generated Import package statement(s)
    import uvmMem_package::*;

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=uvmPkg --section=items

    typedef rdy_vld_agent #(.data_t(uvmMemCmdSt)) cmd_agent_t;
    typedef cmd_agent_t::item_t cmd_item_t;
    typedef cmd_agent_t::config_t cmd_config_t;
    typedef virtual rdy_vld_if #(.data_t(uvmMemCmdSt)) cmd_vif_t;
    typedef rdy_vld_agent #(.data_t(uvmMemWordSt)) out_agent_t;
    typedef out_agent_t::item_t out_item_t;
    typedef out_agent_t::config_t out_config_t;
    typedef virtual rdy_vld_if #(.data_t(uvmMemWordSt)) out_vif_t;
    typedef memory_agent #(.addr_t(uvmMemAddrSt), .data_t(uvmMemWordSt)) wr_agent_t;
    typedef wr_agent_t::item_t wr_item_t;
    typedef wr_agent_t::config_t wr_config_t;
    typedef virtual memory_if #(.addr_t(uvmMemAddrSt), .data_t(uvmMemWordSt)) wr_vif_t;
    typedef memory_agent #(.addr_t(uvmMemAddrSt), .data_t(uvmMemWordSt)) rd_agent_t;
    typedef rd_agent_t::item_t rd_item_t;
    typedef rd_agent_t::config_t rd_config_t;
    typedef virtual memory_if #(.addr_t(uvmMemAddrSt), .data_t(uvmMemWordSt)) rd_vif_t;

    class uvmMem_env extends uvm_env;
        cmd_agent_t cmd_agent;
        out_agent_t out_agent;
        wr_agent_t wr_agent;
        rd_agent_t rd_agent;
        a2c_uvm_pkg::a2c_txn_counter #(out_item_t) out_counter;
        a2c_uvm_pkg::a2c_txn_digest #(cmd_item_t) cmd_digest;
        a2c_uvm_pkg::a2c_txn_digest #(out_item_t) out_digest;
        a2c_uvm_pkg::a2c_txn_digest #(wr_item_t) wr_digest;
        a2c_uvm_pkg::a2c_txn_digest #(rd_item_t) rd_digest;
        virtual a2c_clk_if clk_vif;
        // Mode B, set from a2c_dual_dut: each agent also drives and monitors
        // the model DUT's <port>_model pins, and comparators lists the agents'
        // model_cmp comparators.
        bit dual_dut;
        a2c_uvm_pkg::a2c_comparator_base comparators[$];

        `uvm_component_utils(uvmMem_env)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            cmd_config_t cmd_cfg;
            out_config_t out_cfg;
            wr_config_t wr_cfg;
            rd_config_t rd_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(bit)::get(this, "", "a2c_dual_dut", dual_dut)) begin
                `uvm_fatal("A2C_CFG", "no a2c_dual_dut setting")
            end
            if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "clk", clk_vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual a2c_clk_if 'clk'")
            end

            cmd_cfg = cmd_config_t::type_id::create("cmd_cfg");
            if (!uvm_config_db#(cmd_vif_t)::get(this, "", "cmd", cmd_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual rdy_vld_if 'cmd'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(cmd_vif_t)::get(this, "", "cmd_model", cmd_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual rdy_vld_if 'cmd_model'")
                end
            end
            cmd_cfg.clk_vif = clk_vif;
            cmd_cfg.role = a2c_uvm_pkg::A2C_SRC;
            cmd_cfg.port_name = "cmd";
            cmd_cfg.no_backpressure = 0;
            uvm_config_db#(cmd_config_t)::set(this, "cmd_agent", "cfg", cmd_cfg);
            cmd_agent = cmd_agent_t::type_id::create("cmd_agent", this);
            cmd_digest = a2c_uvm_pkg::a2c_txn_digest#(cmd_item_t)::type_id::create("cmd_digest", this);
            cmd_digest.port_name = "cmd";
            cmd_digest.dual = dual_dut;

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

            wr_cfg = wr_config_t::type_id::create("wr_cfg");
            if (!uvm_config_db#(wr_vif_t)::get(this, "", "wr", wr_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual memory_if 'wr'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(wr_vif_t)::get(this, "", "wr_model", wr_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual memory_if 'wr_model'")
                end
                if (!uvm_config_db#(virtual a2c_credit_if)::get(this, "", "wr_credit", wr_cfg.credit_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual a2c_credit_if 'wr_credit'")
                end
            end
            wr_cfg.clk_vif = clk_vif;
            wr_cfg.role = a2c_uvm_pkg::A2C_DST;
            wr_cfg.port_name = "wr";
            uvm_config_db#(wr_config_t)::set(this, "wr_agent", "cfg", wr_cfg);
            wr_agent = wr_agent_t::type_id::create("wr_agent", this);
            wr_digest = a2c_uvm_pkg::a2c_txn_digest#(wr_item_t)::type_id::create("wr_digest", this);
            wr_digest.port_name = "wr";
            wr_digest.dual = dual_dut;

            rd_cfg = rd_config_t::type_id::create("rd_cfg");
            if (!uvm_config_db#(rd_vif_t)::get(this, "", "rd", rd_cfg.vif)) begin
                `uvm_fatal("A2C_CFG", "no virtual memory_if 'rd'")
            end
            if (dual_dut) begin
                if (!uvm_config_db#(rd_vif_t)::get(this, "", "rd_model", rd_cfg.model_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual memory_if 'rd_model'")
                end
                if (!uvm_config_db#(virtual a2c_credit_if)::get(this, "", "rd_credit", rd_cfg.credit_vif)) begin
                    `uvm_fatal("A2C_CFG", "no virtual a2c_credit_if 'rd_credit'")
                end
            end
            rd_cfg.clk_vif = clk_vif;
            rd_cfg.role = a2c_uvm_pkg::A2C_DST;
            rd_cfg.port_name = "rd";
            uvm_config_db#(rd_config_t)::set(this, "rd_agent", "cfg", rd_cfg);
            rd_agent = rd_agent_t::type_id::create("rd_agent", this);
            rd_digest = a2c_uvm_pkg::a2c_txn_digest#(rd_item_t)::type_id::create("rd_digest", this);
            rd_digest.port_name = "rd";
            rd_digest.dual = dual_dut;
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            out_agent.mon.ap.connect(out_counter.analysis_export);
            cmd_digest.watch(cmd_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            out_digest.watch(out_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            wr_digest.watch(wr_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            rd_digest.watch(rd_agent.mon, a2c_uvm_pkg::A2C_DUT_LANE);
            if (dual_dut) begin
                out_agent.model_mon.ap.connect(out_counter.model_export);
                cmd_digest.watch(cmd_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                out_digest.watch(out_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                wr_digest.watch(wr_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                rd_digest.watch(rd_agent.model_mon, a2c_uvm_pkg::A2C_MODEL_LANE);
                if (cmd_agent.model_cmp != null) begin
                    comparators.push_back(cmd_agent.model_cmp);
                    cmd_digest.cmp = cmd_agent.model_cmp;
                end
                if (out_agent.model_cmp != null) begin
                    comparators.push_back(out_agent.model_cmp);
                    out_digest.cmp = out_agent.model_cmp;
                end
                if (wr_agent.model_cmp != null) begin
                    comparators.push_back(wr_agent.model_cmp);
                    wr_digest.cmp = wr_agent.model_cmp;
                end
                if (rd_agent.model_cmp != null) begin
                    comparators.push_back(rd_agent.model_cmp);
                    rd_digest.cmp = rd_agent.model_cmp;
                end
                out_agent.model_cmp.counted = 1;
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
    endclass : uvmMem_env

// GENERATED_CODE_END

// user package items here

// GENERATED_CODE_BEGIN --template=uvmPkg --section=footer

endpackage : uvmMem_uvm_pkg

// GENERATED_CODE_END
