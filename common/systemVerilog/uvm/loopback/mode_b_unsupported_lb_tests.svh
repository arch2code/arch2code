// Loopback test of the agents with no Mode B operations yet. Included in
// a2c_uvm_loopback_pkg after every agent's tests, whose typedefs it uses.

    // Turns each A2C_CFG fatal about a missing Mode B into UVM_INFO and keeps
    // its text, so every agent can report it in one run.
    class lb_mode_b_fatal_catcher extends uvm_report_catcher;
        string messages[$];

        `uvm_object_utils(lb_mode_b_fatal_catcher)

        function new(string name = "lb_mode_b_fatal_catcher");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_severity() == UVM_FATAL && get_id() == "A2C_CFG" && a2c_contains(get_message(), "has no Mode B operations yet")) begin
                messages.push_back(get_message());
                set_severity(UVM_INFO);
                set_action(UVM_DISPLAY);
            end
            return THROW;
        endfunction
    endclass : lb_mode_b_fatal_catcher

    // A passive agent on port PORT whose config has model_vif set.
    `define LB_MODE_B_UNSUPPORTED(CFG_T, AGENT_T, VIF_T, PORT) \
        begin \
            CFG_T   cfg = CFG_T::type_id::create({PORT, "_cfg"}); \
            AGENT_T agent; \
            if (!uvm_config_db#(VIF_T)::get(this, "", PORT, cfg.vif)) `uvm_fatal("LB_CFG", {"no interface ", PORT}) \
            cfg.model_vif = cfg.vif; \
            cfg.clk_vif   = clk_vif; \
            cfg.port_name = PORT; \
            cfg.is_active = UVM_PASSIVE; \
            uvm_config_db#(CFG_T)::set(this, {PORT, "_agent"}, "cfg", cfg); \
            agent = AGENT_T::type_id::create({PORT, "_agent"}, this); \
            ports.push_back(PORT); \
        end

    // Each agent with no Mode B operations yet, given a model_vif, stops
    // with one A2C_CFG naming its port.
    class mode_b_unsupported_test extends lb_base_test;
        lb_mode_b_fatal_catcher catcher;
        string                  ports[$];

        `uvm_component_utils(mode_b_unsupported_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            catcher = lb_mode_b_fatal_catcher::type_id::create("catcher");
            uvm_report_cb::add(null, catcher);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            `LB_MODE_B_UNSUPPORTED(axr_config_t, axr_agent_t, axr_vif_t, "axr")
            `LB_MODE_B_UNSUPPORTED(axw_config_t, axw_agent_t, axw_vif_t, "axw")
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            `uvm_info("LB_STATS", $sformatf("%0d A2C_CFG fatals caught", catcher.messages.size()), UVM_NONE)
            if (catcher.messages.size() != ports.size()) begin
                `uvm_error("LB_MODE_B", $sformatf("expected %0d A2C_CFG fatals, got %0d: %p", ports.size(), catcher.messages.size(),
                                                  catcher.messages))
            end
            foreach (ports[i]) begin
                int unsigned n = 0;
                foreach (catcher.messages[j]) n += a2c_contains(catcher.messages[j], {ports[i], ": "});
                if (n != 1) `uvm_error("LB_MODE_B", $sformatf("%0d A2C_CFG fatals name port %s, expected one", n, ports[i]))
            end
            super.report_phase(phase);
        endfunction
    endclass : mode_b_unsupported_test

    `undef LB_MODE_B_UNSUPPORTED
