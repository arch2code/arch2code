`ifndef MEMORY_UVM_PKG_SV
`define MEMORY_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for memory_if. One access per rising edge with enable high: a
// write stores write_data at addr, and a read returns read_data on the
// following clock, which then holds until the next read, as memory_sp and
// memory_dp do. There is no handshake, so neither side can stall the other.
// The A2C_SRC driver issues one access per clock, so reads go out back to
// back: item_done() on the edge that takes the access, and for a read
// put_response() with the read data at the falling edge after that edge, so
// at most one read response is pending; memory_base_seq handles those
// responses. The A2C_DST driver serves accesses from cfg.mem, an
// a2c_mem_model of data_t words indexed by addr, which a test may preload,
// inspect, or share between agents. Pin timing follows a2c_clk_if: drive at
// drive_edge(), sample at sample_edge().
package memory_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class memory_item #(type addr_t = logic, type data_t = logic) extends uvm_sequence_item;
        rand bit    write;
        rand addr_t addr;
        // The data written, or the data a read returned.
        rand data_t data;
        // src role: idle clocks (enable low) the driver inserts before this access.
        int unsigned gap;

        `uvm_object_param_utils(memory_item#(addr_t, data_t))

        function new(string name = "memory_item");
            super.new(name);
        endfunction

        virtual function void do_copy(uvm_object rhs);
            memory_item#(addr_t, data_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            write = rhs_.write;
            addr  = rhs_.addr;
            data  = rhs_.data;
            gap   = rhs_.gap;
        endfunction

        // gap is stimulus timing, not payload, so it takes no part in the
        // compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            memory_item#(addr_t, data_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            return super.do_compare(rhs, comparer) && (write === rhs_.write) && (addr === rhs_.addr) &&
                   (data === rhs_.data);
        endfunction

        virtual function string convert2string();
            return $sformatf("%s addr=%p data=%p", write ? "write" : "read", addr, data);
        endfunction
    endclass : memory_item

    class memory_config #(type addr_t = logic, type data_t = logic) extends uvm_object;
        virtual memory_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        virtual a2c_clk_if                                    clk_vif;
        uvm_active_passive_enum                               is_active = UVM_ACTIVE;
        a2c_role_e                                            role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                                                port_name = "";
        // dst role: the storage the driver serves. The agent creates one when
        // the test leaves it null.
        a2c_mem_model #(data_t)                               mem;

        `uvm_object_param_utils(memory_config#(addr_t, data_t))

        function new(string name = "memory_config");
            super.new(name);
        endfunction
    endclass : memory_config

    // The sequence a src-role test extends. Read data arrives at the falling
    // edge after item_done(), as a response the driver routes back through the
    // sequencer; use_response_handler keeps those responses out of the
    // sequence's response queue, which would otherwise overflow. send()
    // counts the reads, read_done() sees each response, and wait_for_reads()
    // holds body() until every read has returned, since a response to a
    // sequence that has ended is dropped.
    class memory_base_seq #(type addr_t = logic, type data_t = logic)
        extends uvm_sequence #(memory_item#(addr_t, data_t));
        protected int unsigned reads_sent;
        protected int unsigned reads_done;

        `uvm_object_param_utils(memory_base_seq#(addr_t, data_t))

        function new(string name = "memory_base_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        task send(memory_item#(addr_t, data_t) it);
            start_item(it);
            finish_item(it);
            if (!it.write) reads_sent++;
        endtask

        task wait_for_reads();
            wait (reads_done >= reads_sent);
        endtask

        // Called once per read, with the request's addr and the data read.
        virtual function void read_done(memory_item#(addr_t, data_t) rsp);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
            memory_item#(addr_t, data_t) rsp;
            $cast(rsp, response);
            reads_done++;
            read_done(rsp);
        endfunction
    endclass : memory_base_seq

    class memory_driver #(type addr_t = logic, type data_t = logic)
        extends uvm_driver #(memory_item#(addr_t, data_t));
        memory_config#(addr_t, data_t) cfg;

        // src role: responses to the reads taken on the last rising edge,
        // waiting for read_data. Each is built when its read is accepted,
        // because a sequence may reuse the request object for its next item.
        protected memory_item#(addr_t, data_t) reads[$];

        `uvm_component_param_utils(memory_driver#(addr_t, data_t))

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

        // Each loop iteration starts at a drive point, and the access goes out
        // on the rising edge before the next one. A read is answered at the
        // sample edge after that, by capture_reads(), while the loop drives
        // the next access.
        protected virtual task run_src();
            cfg.vif.enable     <= 1'b0;
            cfg.vif.wr_en      <= 1'b0;
            cfg.vif.addr       <= '0;
            cfg.vif.write_data <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            fork
                capture_reads();
            join_none
            forever begin
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.enable <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.enable <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                cfg.vif.enable <= 1'b1;
                cfg.vif.wr_en  <= req.write;
                cfg.vif.addr   <= req.addr;
                if (req.write) cfg.vif.write_data <= req.data;
                cfg.clk_vif.drive_edge();
                if (!req.write) begin
                    memory_item#(addr_t, data_t) rsp = memory_item#(addr_t, data_t)::type_id::create("rsp");
                    rsp.set_id_info(req);
                    rsp.write = 1'b0;
                    rsp.addr  = req.addr;
                    reads.push_back(rsp);
                end
                seq_item_port.item_done();
            end
        endtask

        // At most one read waits here: it was taken on the rising edge just
        // before this sample edge, so read_data now holds its word.
        protected virtual task capture_reads();
            memory_item#(addr_t, data_t) rsp;
            forever begin
                cfg.clk_vif.sample_edge();
                if (reads.size() == 0) continue;
                rsp = reads.pop_front();
                rsp.data = cfg.vif.read_data;
                seq_item_port.put_response(rsp);
            end
        endtask

        // A read takes its word at the sample edge, before any write the
        // rising edge applies, so a read and a write of one address on the
        // same clock through two agents sharing cfg.mem return the old word,
        // as memory_dp does. read_data holds until the next read.
        protected virtual task run_dst();
            bit        is_write;
            bit [63:0] index;
            data_t     wdata;
            data_t     rdata;
            cfg.vif.read_data <= '0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (cfg.vif.enable !== 1'b1) continue;
                is_write = (cfg.vif.wr_en === 1'b1);
                index    = 64'(cfg.vif.addr);
                wdata    = cfg.vif.write_data;
                if (!is_write) rdata = cfg.mem.read(index);
                cfg.clk_vif.drive_edge();
                if (is_write) begin
                    cfg.mem.write(index, wdata);
                end else begin
                    cfg.vif.read_data <= rdata;
                end
            end
        endtask
    endclass : memory_driver

    class memory_monitor #(type addr_t = logic, type data_t = logic) extends uvm_monitor;
        memory_config#(addr_t, data_t)                    cfg;
        // One item per access, in access order; a read's item carries the
        // word read_data held on the next clock.
        uvm_analysis_port #(memory_item#(addr_t, data_t)) ap;

        `uvm_component_param_utils(memory_monitor#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        protected function void publish(memory_item#(addr_t, data_t) item);
            `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                         $sformatf("%0h %0h %0h", item.write, item.addr, item.data)), UVM_MEDIUM)
            ap.write(item);
        endfunction

        virtual task run_phase(uvm_phase phase);
            memory_item#(addr_t, data_t) item;
            memory_item#(addr_t, data_t) read;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (read != null) begin
                    read.data = cfg.vif.read_data;
                    publish(read);
                    read = null;
                end
                if (cfg.vif.enable !== 1'b1) continue;
                item = memory_item#(addr_t, data_t)::type_id::create("item");
                item.write = (cfg.vif.wr_en === 1'b1);
                item.addr  = cfg.vif.addr;
                if (item.write) begin
                    item.data = cfg.vif.write_data;
                    publish(item);
                end else begin
                    read = item;
                end
            end
        endtask
    endclass : memory_monitor

    class memory_agent #(type addr_t = logic, type data_t = logic) extends uvm_agent;
        typedef memory_item#(addr_t, data_t)   item_t;
        typedef memory_config#(addr_t, data_t) config_t;

        config_t                                     cfg;
        memory_driver#(addr_t, data_t)               drv;
        // A2C_SRC only.
        uvm_sequencer #(memory_item#(addr_t, data_t)) sqr;
        memory_monitor#(addr_t, data_t)              mon;

        `uvm_component_param_utils(memory_agent#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "memory_agent has no cfg")
            end
            mon = memory_monitor#(addr_t, data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_DST && cfg.mem == null) begin
                cfg.mem = a2c_mem_model#(data_t)::type_id::create({get_name(), "_mem"});
            end
            drv = memory_driver#(addr_t, data_t)::type_id::create("drv", this);
            drv.cfg = cfg;
            if (cfg.role == A2C_SRC) begin
                sqr = uvm_sequencer#(memory_item#(addr_t, data_t))::type_id::create("sqr", this);
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) drv.seq_item_port.connect(sqr.seq_item_export);
        endfunction
    endclass : memory_agent

endpackage : memory_uvm_pkg

`endif // MEMORY_UVM_PKG_SV
