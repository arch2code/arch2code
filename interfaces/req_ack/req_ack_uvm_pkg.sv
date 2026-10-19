`ifndef REQ_ACK_UVM_PKG_SV
`define REQ_ACK_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for req_ack_if. A transfer is a clock with req and ack both high;
// rdata is valid with ack, and req still high on the next clock is a new
// request. The A2C_SRC driver sends one sequence item at a time and writes
// the rdata it gets back into that item before item_done(). The A2C_DST
// driver is a reactive responder: for each request it samples it takes one
// item from its sequencer and drives ack and the item's rdata after the
// item's delay. The agent starts req_ack_responder_seq on that sequencer as
// its run_phase default_sequence; a test replaces it with a uvm_config_db
// set from higher in the hierarchy or with a factory override. Pin timing
// follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
package req_ack_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class req_ack_item #(type data_t = logic, type rdata_t = logic) extends uvm_sequence_item;
        rand data_t  data;
        rand rdata_t rdata;
        // src role: idle clocks (req low) the driver inserts before this request.
        int unsigned gap;
        // dst role: extra clocks the driver waits after it samples the request
        // before it raises ack.
        int unsigned delay;

        `uvm_object_param_utils(req_ack_item#(data_t, rdata_t))

        function new(string name = "req_ack_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            req_ack_item#(data_t, rdata_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            data  = rhs_.data;
            rdata = rhs_.rdata;
            gap   = rhs_.gap;
            delay = rhs_.delay;
        endfunction

        // gap and delay are stimulus timing, not payload, so they take no part
        // in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            req_ack_item#(data_t, rdata_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (data === rhs_.data) && (rdata === rhs_.rdata);
        endfunction

        virtual function string convert2string();
            return $sformatf("data=%p rdata=%p", data, rdata);
        endfunction
    endclass : req_ack_item

    class req_ack_config #(type data_t = logic, type rdata_t = logic) extends uvm_object;
        virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise. The agent has no
        // Mode B operations yet and stops with A2C_CFG when it is set.
        virtual req_ack_if #(.data_t(data_t), .rdata_t(rdata_t)) model_vif;
        virtual a2c_clk_if                                       clk_vif;
        uvm_active_passive_enum                                  is_active = UVM_ACTIVE;
        a2c_role_e                                               role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                                   port_name = "";

        `uvm_object_param_utils(req_ack_config#(data_t, rdata_t))

        function new(string name = "req_ack_config");
            super.new(name);
        endfunction
    endclass : req_ack_config

    // request_fifo holds each request the monitor sees, data only, in order,
    // so a responder sequence can compute rdata from the request. The agent
    // connects it in the A2C_DST role only.
    class req_ack_sequencer #(type data_t = logic, type rdata_t = logic)
        extends uvm_sequencer #(req_ack_item#(data_t, rdata_t));
        uvm_tlm_analysis_fifo #(req_ack_item#(data_t, rdata_t)) request_fifo;

        `uvm_component_param_utils(req_ack_sequencer#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            request_fifo = new("request_fifo", this);
        endfunction

        // A responder takes one request per transfer, so more than one left
        // at the end means the responder sequence does not drain the fifo,
        // which then grows for the whole run.
        virtual function void check_phase(uvm_phase phase);
            super.check_phase(phase);
            if (request_fifo.used() > 1) begin
                `uvm_error("A2C_RESPONDER", $sformatf("request_fifo holds %0d requests at the end of the test: the responder sequence must take one per request",
                                                      request_fifo.used()))
            end
        endfunction
    endclass : req_ack_sequencer

    // The default A2C_DST responder: one item per request in request_fifo,
    // with random rdata and no delay. A replacement extends this class and
    // overrides respond(), or replaces body() and keeps request_fifo drained.
    class req_ack_responder_seq #(type data_t = logic, type rdata_t = logic)
        extends uvm_sequence #(req_ack_item#(data_t, rdata_t));
        `uvm_object_param_utils(req_ack_responder_seq#(data_t, rdata_t))
        `uvm_declare_p_sequencer(req_ack_sequencer#(data_t, rdata_t))

        function new(string name = "req_ack_responder_seq");
            super.new(name);
        endfunction

        // Sets rsp.rdata and rsp.delay for request.
        virtual function void respond(req_ack_item#(data_t, rdata_t) request, req_ack_item#(data_t, rdata_t) rsp);
            if (!rsp.randomize()) `uvm_fatal("A2C_RAND", "req_ack response randomize failed")
            rsp.data  = request.data;
            rsp.delay = 0;
        endfunction

        virtual task body();
            req_ack_item#(data_t, rdata_t) request;
            req_ack_item#(data_t, rdata_t) rsp;
            forever begin
                p_sequencer.request_fifo.get(request);
                rsp = req_ack_item#(data_t, rdata_t)::type_id::create("rsp");
                start_item(rsp);
                respond(request, rsp);
                finish_item(rsp);
            end
        endtask
    endclass : req_ack_responder_seq

    class req_ack_driver #(type data_t = logic, type rdata_t = logic)
        extends uvm_driver #(req_ack_item#(data_t, rdata_t));
        req_ack_config#(data_t, rdata_t) cfg;

        `uvm_component_param_utils(req_ack_driver#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            if (cfg.role == A2C_SRC) begin
                run_src();
            end else begin
                run_dst();
            end
        endtask

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back requests go out on consecutive clocks, and req drops
        // on the first drive point with no item.
        protected virtual task run_src();
            cfg.vif.req  <= 1'b0;
            cfg.vif.data <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.req <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.req <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.req  <= 1'b1;
                cfg.vif.data <= req.data;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.ack !== 1'b1);
                req.rdata = cfg.vif.rdata;
                // The transfer happens at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // ack and rdata are driven for one clock per transfer, and rise only
        // after req has been sampled, so with no delay a transfer takes two
        // clocks. rdata is zero while ack is low.
        protected virtual task run_dst();
            cfg.vif.ack   <= 1'b0;
            cfg.vif.rdata <= '0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.vif.req !== 1'b1) continue;
                seq_item_port.get_next_item(req);
                repeat (req.delay) cfg.clk_vif.drive_edge();
                cfg.clk_vif.drive_edge();
                cfg.vif.ack   <= 1'b1;
                cfg.vif.rdata <= req.rdata;
                cfg.clk_vif.drive_edge();
                cfg.vif.ack   <= 1'b0;
                cfg.vif.rdata <= '0;
                seq_item_port.item_done();
            end
        endtask
    endclass : req_ack_driver

    class req_ack_monitor #(type data_t = logic, type rdata_t = logic) extends uvm_monitor;
        req_ack_config#(data_t, rdata_t)                    cfg;
        // One item per completed transfer, with data and rdata.
        uvm_analysis_port #(req_ack_item#(data_t, rdata_t)) ap;
        // One item per request, data only, on the clock the request is first
        // seen.
        uvm_analysis_port #(req_ack_item#(data_t, rdata_t)) req_ap;

        `uvm_component_param_utils(req_ack_monitor#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap     = new("ap", this);
            req_ap = new("req_ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            logic   req;
            logic   ack;
            data_t  data;
            rdata_t rdata;
            data_t  held;
            bit     waiting = 0;
            req_ack_item#(data_t, rdata_t) item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                req   = cfg.vif.req;
                ack   = cfg.vif.ack;
                data  = cfg.vif.data;
                rdata = cfg.vif.rdata;
                // A source waiting for ack must hold req and data until the transfer.
                if (waiting && (req !== 1'b1 || data !== held)) begin
                    string what = (req !== 1'b1) ? "req dropped" : "data changed";
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before ack of %h", cfg.port_name, what, held))
                end
                if (ack === 1'b1 && req !== 1'b1) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: ack is high with req %b", cfg.port_name, req))
                end
                if (req === 1'b1 && !waiting) begin
                    item = req_ack_item#(data_t, rdata_t)::type_id::create("request");
                    item.data = data;
                    req_ap.write(item);
                end
                waiting = (req === 1'b1 && ack !== 1'b1);
                held    = data;
                // X/Z checks only fire on a 4-state boundary. Across a 2-state
                // SystemC boundary an X or Z from the DUT arrives as 0.
                if ($isunknown(req)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: req is %b after reset release", cfg.port_name, req))
                    continue;
                end
                if (req !== 1'b1) continue;
                if ($isunknown(data)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: data has X or Z while req is high: %h", cfg.port_name, data))
                end
                if (ack !== 1'b1) continue;
                if ($isunknown(rdata)) begin
                    `uvm_error("A2C_XZ", $sformatf("%s: rdata has X or Z while ack is high: %h", cfg.port_name, rdata))
                end
                item = req_ack_item#(data_t, rdata_t)::type_id::create("item");
                item.data  = data;
                item.rdata = rdata;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h %0h", data, rdata)), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : req_ack_monitor

    class req_ack_agent #(type data_t = logic, type rdata_t = logic) extends uvm_agent;
        typedef req_ack_item#(data_t, rdata_t)   item_t;
        typedef req_ack_config#(data_t, rdata_t) config_t;

        req_ack_config#(data_t, rdata_t)    cfg;
        req_ack_driver#(data_t, rdata_t)    drv;
        req_ack_sequencer#(data_t, rdata_t) sqr;
        req_ack_monitor#(data_t, rdata_t)   mon;
        // Always null, because the agent has no Mode B operations yet; the env
        // names both on every port.
        req_ack_monitor#(data_t, rdata_t)   model_mon;
        a2c_comparator_base                 model_cmp;

        `uvm_component_param_utils(req_ack_agent#(data_t, rdata_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(req_ack_config#(data_t, rdata_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "req_ack_agent has no cfg")
            end
            if (cfg.model_vif != null) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: req_ack has no Mode B operations yet", cfg.port_name))
            end
            mon = req_ack_monitor#(data_t, rdata_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active != UVM_ACTIVE) return;
            drv = req_ack_driver#(data_t, rdata_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            sqr = req_ack_sequencer#(data_t, rdata_t)::type_id::create("sqr", this);
            // A set from the test or env is higher in the hierarchy, so it
            // wins over this one during build.
            if (cfg.role == A2C_DST) begin
                uvm_config_db#(uvm_object_wrapper)::set(this, "sqr.run_phase", "default_sequence",
                                                        req_ack_responder_seq#(data_t, rdata_t)::type_id::get());
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr == null) return;
            drv.seq_item_port.connect(sqr.seq_item_export);
            if (cfg.role == A2C_DST) begin
                mon.req_ap.connect(sqr.request_fifo.analysis_export);
            end
        endfunction
    endclass : req_ack_agent

endpackage : req_ack_uvm_pkg

`endif // REQ_ACK_UVM_PKG_SV
