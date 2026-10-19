`ifndef AXI_READ_UVM_PKG_SV
`define AXI_READ_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for axi_read_if: an AXI4 read master driver for the A2C_SRC role,
// a slave driver for the A2C_DST role, and a monitor. AMBA 5 calls the two
// sides Manager and Subordinate. One item is one burst. The type parameters
// and their defaults are the interface's.
//
// The master drives AR and R independently: it calls item_done() once the
// burst's AR transfers, so up to cfg.max_outstanding bursts are in flight,
// and returns each burst with put_response() when its last beat arrives. A
// sequence extends axi_read_base_seq to receive those responses.
//
// The slave serves bursts from cfg.mem, an a2c_mem_model of bytes at byte
// addresses, in the order their AR transfers, whatever their ID, or with
// cfg.reorder in any order that keeps each ID's bursts in AR order. Byte X of a
// beat sits on bus byte lane X % (1 << FULL_SIZE), as the AXI address rules
// place it. A bus that is not a power-of-two number of whole bytes carries
// only full-width transfers; the lanes beyond its width do not exist.
//
// Pin timing follows a2c_clk_if: drive at drive_edge(), sample at
// sample_edge().
package axi_read_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class axi_read_item #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                          type ruser_t = logic, type id_t = logic [3:0]) extends uvm_sequence_item;
        localparam int unsigned ADDR_W     = $bits(addr_t);
        localparam int unsigned DATA_BYTES = ($bits(data_t) + 7) / 8;
        // arsize of a full-width beat.
        localparam int unsigned FULL_SIZE  = $clog2(DATA_BYTES);
        // Narrow transfers need a bus of a power-of-two number of whole bytes.
        localparam bit          BYTE_LANES = ($bits(data_t) % 8 == 0) && (DATA_BYTES == (1 << FULL_SIZE));
        // An INCR burst stays within one 4 KB page, or within the address
        // space when that is smaller.
        localparam longint unsigned PAGE   = (ADDR_W < 12) ? (64'd1 << ADDR_W) : 64'd4096;

        rand bit [ADDR_W-1:0] addr;
        rand id_t             id;
        rand bit [7:0]        len;
        rand bit [2:0]        size;
        rand axi_burst_e      burst;
        rand aruser_t         aruser;
        // One entry per beat, filled from R: rdata, rresp and ruser.
        data_t                data[];
        axi_resp_e            resp[];
        ruser_t               ruser[];
        // src role: idle clocks (arvalid low) the master inserts before this AR.
        int unsigned          gap;
        // Bytes the burst may move, (len + 1) << size; 0 means no limit.
        // axi_read_base_seq::new_item() sets it from the port's config.
        int unsigned          max_transfer_bytes;

        constraint c_axi4 {
            solve burst before len, addr;
            solve size before len, addr;
            size <= FULL_SIZE;
            !BYTE_LANES -> size == FULL_SIZE;
            burst != AXI_INCR -> len <= 15;
            burst == AXI_WRAP -> len inside {1, 3, 7, 15};
            burst == AXI_WRAP -> (addr & ((64'd1 << size) - 1)) == 0;
            burst == AXI_INCR -> ((addr % PAGE) & ~((64'd1 << size) - 1)) + ((64'(len) + 1) << size) <= PAGE;
            max_transfer_bytes != 0 -> ((64'(len) + 1) << size) <= max_transfer_bytes;
        }

        `uvm_object_param_utils(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name = "axi_read_item");
            super.new(name);
        endfunction

        function int unsigned total_bytes();
            return (int'(len) + 1) << size;
        endfunction

        virtual function void do_copy(uvm_object rhs);
            axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            addr               = rhs_.addr;
            id                 = rhs_.id;
            len                = rhs_.len;
            size               = rhs_.size;
            burst              = rhs_.burst;
            aruser             = rhs_.aruser;
            data               = rhs_.data;
            resp               = rhs_.resp;
            ruser              = rhs_.ruser;
            gap                = rhs_.gap;
            max_transfer_bytes = rhs_.max_transfer_bytes;
        endfunction

        // gap and max_transfer_bytes shape the stimulus, so they take no
        // part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            if (!super.do_compare(rhs, comparer)) return 0;
            if (addr !== rhs_.addr || id !== rhs_.id || len !== rhs_.len || size !== rhs_.size ||
                burst !== rhs_.burst || aruser !== rhs_.aruser) return 0;
            if (data.size() != rhs_.data.size() || resp.size() != rhs_.resp.size() ||
                ruser.size() != rhs_.ruser.size()) return 0;
            foreach (data[i]) if (data[i] !== rhs_.data[i]) return 0;
            foreach (resp[i]) if (resp[i] !== rhs_.resp[i]) return 0;
            foreach (ruser[i]) if (ruser[i] !== rhs_.ruser[i]) return 0;
            return 1;
        endfunction

        virtual function string convert2string();
            return $sformatf("id=%0h addr=%0h len=%0d size=%0d burst=%s aruser=%0h beats=%0d", id, addr, len, size,
                             burst.name(), aruser, data.size());
        endfunction

        function string beat2string(int unsigned n);
            return $sformatf("id=%0h beat %0d of %0d rdata=%p rresp=%s ruser=%0h", id, n, int'(len) + 1, data[n],
                             resp[n].name(), ruser[n]);
        endfunction
    endclass : axi_read_item

    // The slave's memory: one byte per byte address.
    typedef a2c_mem_model #(bit [7:0]) axi_read_mem_t;

    class axi_read_config #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                            type ruser_t = logic, type id_t = logic [3:0]) extends uvm_object;
        virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                              .id_t(id_t))  vif;
        // The model DUT's pin set in Mode B; null otherwise. The agent has no
        // Mode B operations yet and stops with A2C_CFG when it is set.
        virtual axi_read_if #(.addr_t(addr_t), .data_t(data_t), .aruser_t(aruser_t), .ruser_t(ruser_t),
                              .id_t(id_t))  model_vif;
        virtual a2c_clk_if                  clk_vif;
        uvm_active_passive_enum             is_active = UVM_ACTIVE;
        a2c_role_e                          role = A2C_SRC;
        // Port name used in the A2C_TXN log line.
        string                              port_name = "";
        // Bytes one burst may move, 0 for no limit. The env sets it to the
        // interface's maxTransferSize. The SystemC channel counts that value
        // in beats, so reading it as bytes is the limit every bus width meets.
        int unsigned                        max_transfer_bytes = 0;
        // The port binds no id_t, so the design behind it carries no ID and
        // may answer every burst with ID 0. The master then sends every
        // burst with ID 0.
        bit                                 id_unbound = 0;
        // A2C_SRC role: bursts whose AR has gone out and whose last beat has
        // not arrived, and the percentage of clocks with rready high.
        int unsigned                        max_outstanding = 1;
        int unsigned                        rready_pct = 100;
        // A2C_DST role. The agent creates mem when the test leaves it null.
        // arready is high on arready_pct percent of clocks. Each burst draws
        // a delay of resp_delay_min to resp_delay_max clocks, counted from
        // its AR transfer, before its first beat may go out. A burst still
        // waits for the bursts ahead of it, or with reorder only for the
        // bursts ahead of it with its ID. A beat whose address falls in an
        // error range gets SLVERR and reads zero.
        axi_read_mem_t                      mem;
        int unsigned                        arready_pct = 100;
        int unsigned                        resp_delay_min = 0;
        int unsigned                        resp_delay_max = 0;
        bit                                 reorder = 0;
        axi_addr_range_t                    error_ranges[$];

        `uvm_object_param_utils(axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name = "axi_read_config");
            super.new(name);
        endfunction
    endclass : axi_read_config

    // The sequence an A2C_SRC test extends. The master returns each burst
    // with its read data as a response after item_done(); use_response_handler
    // keeps those responses out of the sequence's response queue, which would
    // otherwise overflow. send() counts the bursts, read_done() sees each
    // response, and wait_for_reads() holds body() until every burst has
    // returned, since a response to a sequence that has ended is dropped.
    // A response with no beats is an item the master refused. new_item()
    // gives an item whose constraints keep it within the port's
    // max_transfer_bytes.
    class axi_read_base_seq #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                              type ruser_t = logic, type id_t = logic [3:0])
        extends uvm_sequence #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t));
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t)   item_t;
        typedef axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) config_t;

        protected int unsigned reads_sent;
        protected int unsigned reads_done;
        protected config_t     cfg;

        `uvm_object_param_utils(axi_read_base_seq#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name = "axi_read_base_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        // The agent publishes its config to its sequencer, so this works once
        // the sequence has a sequencer.
        function item_t new_item(string name = "item");
            item_t it = item_t::type_id::create(name);
            if (cfg == null && !uvm_config_db#(config_t)::get(m_sequencer, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_read_base_seq: the sequencer has no axi_read config")
            end
            it.max_transfer_bytes = cfg.max_transfer_bytes;
            return it;
        endfunction

        task send(item_t it);
            start_item(it);
            finish_item(it);
            reads_sent++;
        endtask

        task wait_for_reads();
            wait (reads_done >= reads_sent);
        endtask

        // Called once per burst, with the request's AR fields and the beats read.
        virtual function void read_done(item_t rsp);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
            item_t rsp;
            $cast(rsp, response);
            reads_done++;
            read_done(rsp);
        endfunction
    endclass : axi_read_base_seq

    class axi_read_master_driver #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                                   type ruser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t));
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                   id_key_t;

        axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) cfg;

        // Responses waiting for their beats, oldest first per ID. Each is
        // built when its AR goes out, because a sequence may reuse the
        // request object for its next item.
        protected item_t       pending[id_key_t][$];
        protected int unsigned outstanding;

        `uvm_component_param_utils(axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            cfg.vif.arvalid <= 1'b0;
            cfg.vif.arid    <= '0;
            cfg.vif.araddr  <= '0;
            cfg.vif.arlen   <= '0;
            cfg.vif.arsize  <= '0;
            cfg.vif.arburst <= '0;
            cfg.vif.aruser  <= '0;
            cfg.vif.rready  <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            fork
                run_r();
            join_none
            run_ar();
        endtask

        // The response to req, with its AR fields and no beats yet.
        protected function item_t new_response(item_t req);
            item_t rsp = item_t::type_id::create("rsp");
            rsp.copy(req);
            rsp.set_id_info(req);
            rsp.data  = new[0];
            rsp.resp  = new[0];
            rsp.ruser = new[0];
            return rsp;
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back ARs go out on consecutive clocks, and arvalid drops on
        // the first drive point with no item or no free outstanding slot. An
        // item above a non-zero max_transfer_bytes is an A2C_CFG error and
        // never reaches the bus. It completes at once with a response that
        // has no beats, so a sequence waiting on its responses goes on.
        protected virtual task run_ar();
            item_t rsp;
            forever begin
                if (outstanding >= cfg.max_outstanding) begin
                    cfg.vif.arvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.arvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                if (cfg.max_transfer_bytes != 0 && req.total_bytes() > cfg.max_transfer_bytes) begin
                    `uvm_error("A2C_CFG", $sformatf("%s: %s moves %0d bytes, above max_transfer_bytes %0d, so it is not driven",
                                                    cfg.port_name, req.convert2string(), req.total_bytes(),
                                                    cfg.max_transfer_bytes))
                    rsp = new_response(req);
                    seq_item_port.item_done();
                    seq_item_port.put_response(rsp);
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.arvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                rsp = new_response(req);
                if (cfg.id_unbound) rsp.id = '0;
                pending[id_key_t'(rsp.id)].push_back(rsp);
                outstanding++;
                cfg.vif.arvalid <= 1'b1;
                cfg.vif.arid    <= rsp.id;
                cfg.vif.araddr  <= addr_t'(req.addr);
                cfg.vif.arlen   <= req.len;
                cfg.vif.arsize  <= req.size;
                cfg.vif.arburst <= req.burst;
                cfg.vif.aruser  <= req.aruser;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.arready !== 1'b1);
                // The AR transfers at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // A beat belongs to the oldest open burst of its rid. The burst ends
        // at rlast, or at its last beat when rlast is missing. The monitor
        // reports a misplaced rlast and a beat whose rid matches no burst.
        // The driver drops a beat that matches no burst.
        protected virtual task run_r();
            forever begin
                cfg.vif.rready <= ($urandom_range(99, 0) < cfg.rready_pct);
                cfg.clk_vif.sample_edge();
                if (cfg.vif.rvalid === 1'b1 && cfg.vif.rready === 1'b1) take_beat();
                cfg.clk_vif.drive_edge();
            end
        endtask

        protected function void take_beat();
            id_key_t     id = id_key_t'(cfg.vif.rid);
            item_t       rsp;
            int unsigned n;
            if (!pending.exists(id) || pending[id].size() == 0) return;
            rsp = pending[id][0];
            n   = rsp.data.size();
            rsp.data  = new[n + 1](rsp.data);
            rsp.resp  = new[n + 1](rsp.resp);
            rsp.ruser = new[n + 1](rsp.ruser);
            rsp.data[n]  = cfg.vif.rdata;
            rsp.resp[n]  = axi_resp_e'(cfg.vif.rresp);
            rsp.ruser[n] = cfg.vif.ruser;
            if (cfg.vif.rlast !== 1'b1 && n != rsp.len) return;
            void'(pending[id].pop_front());
            outstanding--;
            seq_item_port.put_response(rsp);
        endfunction
    endclass : axi_read_master_driver

    // Serves each burst from cfg.mem, in the order the ARs transfer, or with
    // cfg.reorder in any order that keeps each ID's bursts in AR order. A
    // beat is read from the memory when it first goes out and is held until
    // it transfers.
    class axi_read_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                                  type ruser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t));
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;
        localparam int unsigned DATA_BYTES = item_t::DATA_BYTES;
        localparam int unsigned FULL_SIZE  = item_t::FULL_SIZE;
        localparam bit          BYTE_LANES = item_t::BYTE_LANES;

        axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) cfg;

        `uvm_component_param_utils(axi_read_slave_driver#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // The index in queue of the burst that goes out next, or -1. A burst
        // is ready once its delay has passed and no older burst with its ID
        // is queued. Only the oldest burst may go, unless cfg.reorder lets
        // any ready one.
        protected function int next_burst(item_t queue[$], longint due[$], longint clocks);
            int ready[$];
            foreach (queue[i]) begin
                bit older = 0;
                if (!cfg.reorder && i != 0) break;
                for (int j = 0; j < i; j++) older |= (queue[j].id === queue[i].id);
                if (!older && due[i] <= clocks) ready.push_back(i);
            end
            if (ready.size() == 0) return -1;
            return cfg.reorder ? ready[$urandom_range(ready.size() - 1, 0)] : ready[0];
        endfunction

        // Beat n of burst ar, read from the memory: its data and response.
        protected function void read_beat(item_t ar, int unsigned n, output data_t data, output axi_resp_e resp);
            bit [8*DATA_BYTES-1:0] lanes = '0;
            bit [63:0]             first;
            int unsigned           count;
            axi_beat(64'(ar.addr), ar.size, ar.len, ar.burst, n, first, count);
            resp = AXI_OKAY;
            if (axi_in_error_range(first, cfg.error_ranges)) begin
                resp = AXI_SLVERR;
            end else begin
                for (int unsigned i = 0; i < count; i++) begin
                    int unsigned lane = int'((first + i) % (64'd1 << FULL_SIZE));
                    if (lane < DATA_BYTES) lanes[8 * lane +: 8] = cfg.mem.read(first + i);
                end
            end
            data = data_t'(lanes[$bits(data_t)-1:0]);
        endfunction

        // Each loop iteration starts at a drive point. A burst's first beat
        // goes out at the drive point after its AR transfers, plus its
        // response delay, and the next beat at the drive point after a beat
        // transfers.
        virtual task run_phase(uvm_phase phase);
            item_t       queue[$];
            longint      due[$];
            item_t       cur;
            int unsigned beat;
            bit          on_bus;
            longint      clocks;
            data_t       data;
            axi_resp_e   resp;
            int          pick;
            cfg.vif.arready <= 1'b0;
            cfg.vif.rvalid  <= 1'b0;
            cfg.vif.rid     <= '0;
            cfg.vif.rdata   <= '0;
            cfg.vif.rresp   <= '0;
            cfg.vif.rlast   <= 1'b0;
            cfg.vif.ruser   <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                cfg.vif.arready <= ($urandom_range(99, 0) < cfg.arready_pct);
                pick = (cur == null) ? next_burst(queue, due, clocks) : -1;
                if (pick >= 0) begin
                    cur  = queue[pick];
                    queue.delete(pick);
                    due.delete(pick);
                    beat = 0;
                end
                if (cur != null && !on_bus) begin
                    read_beat(cur, beat, data, resp);
                    cfg.vif.rvalid <= 1'b1;
                    cfg.vif.rid    <= cur.id;
                    cfg.vif.rdata  <= data;
                    cfg.vif.rresp  <= resp;
                    cfg.vif.rlast  <= (beat == cur.len);
                    cfg.vif.ruser  <= '0;
                    on_bus = 1;
                end else if (cur == null) begin
                    cfg.vif.rvalid <= 1'b0;
                    cfg.vif.rlast  <= 1'b0;
                end
                cfg.clk_vif.sample_edge();
                clocks++;
                if (on_bus && cfg.vif.rready === 1'b1) begin
                    on_bus = 0;
                    beat++;
                    if (beat > cur.len) cur = null;
                end
                if (cfg.vif.arvalid === 1'b1 && cfg.vif.arready === 1'b1) begin
                    item_t ar = item_t::type_id::create("ar");
                    ar.id     = cfg.vif.arid;
                    ar.addr   = cfg.vif.araddr;
                    ar.len    = cfg.vif.arlen;
                    ar.size   = cfg.vif.arsize;
                    ar.burst  = axi_burst_e'(cfg.vif.arburst);
                    ar.aruser = cfg.vif.aruser;
                    if (!BYTE_LANES && ar.size != FULL_SIZE) begin
                        `uvm_error("A2C_PROTO", $sformatf("%s: %s is a %0d-byte transfer on a %0d-bit bus, which carries only full-width transfers",
                                                          cfg.port_name, ar.convert2string(), 1 << ar.size, $bits(data_t)))
                    end
                    queue.push_back(ar);
                    due.push_back(clocks + $urandom_range(cfg.resp_delay_max, cfg.resp_delay_min));
                end
                cfg.clk_vif.drive_edge();
            end
        endtask
    endclass : axi_read_slave_driver

    class axi_read_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                             type ruser_t = logic, type id_t = logic [3:0]) extends uvm_monitor;
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                   id_key_t;
        localparam int unsigned FULL_SIZE = item_t::FULL_SIZE;

        axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) cfg;
        // One item per burst, at its last beat, with its AR fields and beats.
        uvm_analysis_port #(item_t)                               ap;

        // Bursts whose AR has transferred and whose last beat has not, oldest
        // first per ID.
        protected item_t open[id_key_t][$];

        `uvm_component_param_utils(axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        // The AR and R payloads, each with its valid, as one vector, so a
        // stalled transfer can be compared with the next clock.
        protected function logic [$bits(id_t)+$bits(addr_t)+13+$bits(aruser_t):0] ar_pins();
            return {cfg.vif.arvalid, cfg.vif.arid, cfg.vif.araddr, cfg.vif.arlen, cfg.vif.arsize, cfg.vif.arburst,
                    cfg.vif.aruser};
        endfunction

        protected function logic [$bits(id_t)+$bits(data_t)+3+$bits(ruser_t):0] r_pins();
            return {cfg.vif.rvalid, cfg.vif.rid, cfg.vif.rdata, cfg.vif.rresp, cfg.vif.rlast, cfg.vif.ruser};
        endfunction

        protected function string path();
            return {get_full_name(), ".", cfg.port_name};
        endfunction

        // A stalled AR or R must hold its valid and payload until ready. R
        // is taken before AR on each clock, since a beat may not share the
        // rising edge of its own AR.
        virtual task run_phase(uvm_phase phase);
            logic [$bits(id_t)+$bits(addr_t)+13+$bits(aruser_t):0] held_ar;
            logic [$bits(id_t)+$bits(data_t)+3+$bits(ruser_t):0]   held_r;
            bit                                                    ar_stalled;
            bit                                                    r_stalled;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (r_stalled && r_pins() !== held_r) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before rready took the stalled beat", cfg.port_name,
                                                     cfg.vif.rvalid !== 1'b1 ? "rvalid dropped" : "the R payload changed"))
                end
                if (ar_stalled && ar_pins() !== held_ar) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before arready took the stalled AR", cfg.port_name,
                                                     cfg.vif.arvalid !== 1'b1 ? "arvalid dropped" : "the AR payload changed"))
                end
                r_stalled  = cfg.vif.rvalid === 1'b1 && cfg.vif.rready !== 1'b1;
                ar_stalled = cfg.vif.arvalid === 1'b1 && cfg.vif.arready !== 1'b1;
                held_r     = r_pins();
                held_ar    = ar_pins();
                if (cfg.vif.rvalid === 1'b1 && cfg.vif.rready === 1'b1) take_beat();
                if (cfg.vif.arvalid === 1'b1 && cfg.vif.arready === 1'b1) take_ar();
            end
        endtask

        protected function void take_ar();
            item_t           it = item_t::type_id::create("item");
            longint unsigned nbytes;
            it.id     = cfg.vif.arid;
            it.addr   = cfg.vif.araddr;
            it.len    = cfg.vif.arlen;
            it.size   = cfg.vif.arsize;
            it.burst  = axi_burst_e'(cfg.vif.arburst);
            it.aruser = cfg.vif.aruser;
            it.data   = new[0];
            it.resp   = new[0];
            it.ruser  = new[0];
            nbytes    = 64'd1 << it.size;
            if (cfg.vif.arburst === 2'b11) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: arburst is the reserved value 2'b11", cfg.port_name))
            end
            if (it.size > FULL_SIZE) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: arsize is wider than the %0d-bit bus", cfg.port_name,
                                                  it.convert2string(), $bits(data_t)))
            end
            if (it.burst == AXI_FIXED && it.len > 15) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: a FIXED burst is at most 16 beats", cfg.port_name,
                                                  it.convert2string()))
            end
            if (it.burst == AXI_WRAP && !(it.len inside {1, 3, 7, 15})) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: a WRAP burst is 2, 4, 8 or 16 beats", cfg.port_name,
                                                  it.convert2string()))
            end
            if (it.burst == AXI_WRAP && (64'(it.addr) & (nbytes - 1)) != 0) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: a WRAP burst starts aligned to its transfer size",
                                                  cfg.port_name, it.convert2string()))
            end
            if (it.burst == AXI_INCR && ((64'(it.addr) % 4096) & ~(nbytes - 1)) + (64'(it.len) + 1) * nbytes > 4096) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s crosses a 4 KB boundary", cfg.port_name, it.convert2string()))
            end
            open[id_key_t'(it.id)].push_back(it);
        endfunction

        // A beat belongs to the oldest open burst of its rid. The burst ends
        // at rlast, or at its last beat when rlast is missing.
        protected function void take_beat();
            id_key_t     id = id_key_t'(cfg.vif.rid);
            item_t       it;
            int unsigned n;
            bit          last;
            if (!open.exists(id) || open[id].size() == 0) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: R beat with rid %0h matches no outstanding read", cfg.port_name, id))
                return;
            end
            it = open[id][0];
            n  = it.data.size();
            it.data  = new[n + 1](it.data);
            it.resp  = new[n + 1](it.resp);
            it.ruser = new[n + 1](it.ruser);
            it.data[n]  = cfg.vif.rdata;
            it.resp[n]  = axi_resp_e'(cfg.vif.rresp);
            it.ruser[n] = cfg.vif.ruser;
            last = (n == it.len);
            `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.beat2string(n), $sformatf("%0h", it.data[n])), UVM_HIGH)
            if (cfg.vif.rlast !== last) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: rlast is %b on beat %0d of the %0d-beat burst %s", cfg.port_name,
                                                  cfg.vif.rlast, n, int'(it.len) + 1, it.convert2string()))
            end
            if (cfg.vif.rlast !== 1'b1 && !last) return;
            void'(open[id].pop_front());
            `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.convert2string(), $sformatf("%0h", it.addr)), UVM_MEDIUM)
            ap.write(it);
        endfunction

        // Every burst must have received its last beat by the end of the run.
        virtual function void check_phase(uvm_phase phase);
            int unsigned left = 0;
            foreach (open[id]) left += open[id].size();
            if (left != 0) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: the run ended with %0d bursts still waiting for their last beat",
                                                  cfg.port_name, left))
            end
        endfunction
    endclass : axi_read_monitor

    class axi_read_agent #(type addr_t = logic [31:0], type data_t = logic [31:0], type aruser_t = logic,
                           type ruser_t = logic, type id_t = logic [3:0]) extends uvm_agent;
        typedef axi_read_item#(addr_t, data_t, aruser_t, ruser_t, id_t)   item_t;
        typedef axi_read_config#(addr_t, data_t, aruser_t, ruser_t, id_t) config_t;

        config_t                                                    cfg;
        // axi_read_master_driver for A2C_SRC, axi_read_slave_driver for A2C_DST.
        uvm_driver #(item_t)                                        drv;
        // A2C_SRC only.
        uvm_sequencer #(item_t)                                     sqr;
        axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t) mon;
        // Always null, because the agent has no Mode B operations yet; the env
        // names both on every port.
        axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t) model_mon;
        a2c_comparator_base                                        model_cmp;

        `uvm_component_param_utils(axi_read_agent#(addr_t, data_t, aruser_t, ruser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_read_agent has no cfg")
            end
            if (cfg.model_vif != null) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: axi_read has no Mode B operations yet", cfg.port_name))
            end
            mon = axi_read_monitor#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_SRC) begin
                axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t) master;
                if (cfg.max_outstanding == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: max_outstanding is 0, so no burst could go out", cfg.port_name))
                end
                if (cfg.rready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: rready_pct is 0, so no burst could complete", cfg.port_name))
                end
                master = axi_read_master_driver#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("drv", this);
                master.cfg = cfg;
                drv = master;
                sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
                uvm_config_db#(config_t)::set(this, "sqr", "cfg", cfg);
            end else begin
                axi_read_slave_driver#(addr_t, data_t, aruser_t, ruser_t, id_t) slave;
                if (cfg.arready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: arready_pct is 0, so no AR could transfer", cfg.port_name))
                end
                if (cfg.resp_delay_min > cfg.resp_delay_max) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: resp_delay_min %0d is above resp_delay_max %0d", cfg.port_name,
                                                    cfg.resp_delay_min, cfg.resp_delay_max))
                end
                if (cfg.mem == null) cfg.mem = axi_read_mem_t::type_id::create({get_full_name(), ".mem"});
                slave = axi_read_slave_driver#(addr_t, data_t, aruser_t, ruser_t, id_t)::type_id::create("drv", this);
                slave.cfg = cfg;
                drv = slave;
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
        endfunction
    endclass : axi_read_agent

endpackage : axi_read_uvm_pkg

`endif // AXI_READ_UVM_PKG_SV
