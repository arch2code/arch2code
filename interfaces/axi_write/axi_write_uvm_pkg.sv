`ifndef AXI_WRITE_UVM_PKG_SV
`define AXI_WRITE_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for axi_write_if: an AXI4 write master driver for the A2C_SRC
// role, a slave driver for the A2C_DST role, and a monitor. AMBA 5 calls the
// two sides Manager and Subordinate. One item is one burst with its data
// beats. The type parameters and the defaults of the optional ones are the
// interface's.
//
// The master drives AW, W and B independently: it calls item_done() once the
// burst's AW transfers, so up to cfg.max_outstanding bursts are in flight,
// and returns each burst with put_response() when its B arrives. A burst's
// first W beat goes out no earlier than its AW, and W bursts follow AW order.
// A sequence extends axi_write_base_seq to receive the responses.
//
// The slave writes bursts to cfg.mem, an a2c_mem_model of bytes at byte
// addresses, and answers with B in the order the AWs transfer, whatever their
// ID, or with cfg.reorder in any order that keeps each ID's bursts in AW
// order. It takes W beats before their AW and holds them until the AW
// arrives.
// Byte X of a beat sits on bus byte lane X % (1 << FULL_SIZE), as the AXI
// address rules place it, and is written only when its wstrb bit is set.
//
// wstrb has one bit per byte lane, so the agent needs $bits(data_t) to be
// 8 * $bits(strb_t) and stops at build with A2C_CFG otherwise. A bus that is
// not a power-of-two number of whole bytes carries only full-width transfers.
//
// Pin timing follows a2c_clk_if: drive at drive_edge(), sample at
// sample_edge().
package axi_write_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class axi_write_item #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                           type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                           type id_t = logic [3:0]) extends uvm_sequence_item;
        localparam int unsigned ADDR_W     = $bits(addr_t);
        localparam int unsigned STRB_W     = $bits(strb_t);
        localparam int unsigned DATA_BYTES = ($bits(data_t) + 7) / 8;
        // awsize of a full-width beat.
        localparam int unsigned FULL_SIZE  = $clog2(DATA_BYTES);
        // Narrow transfers need a bus of a power-of-two number of whole bytes.
        localparam bit          BYTE_LANES = ($bits(data_t) % 8 == 0) && (DATA_BYTES == (1 << FULL_SIZE));
        // An INCR burst stays within one 4 KB page, or within the address
        // space when that is smaller.
        localparam longint unsigned PAGE   = (ADDR_W < 12) ? (64'd1 << ADDR_W) : 64'd4096;

        // A strobe as bits, so constraints and lane masks can work on it.
        typedef bit [STRB_W-1:0] strb_bits_t;

        rand bit [ADDR_W-1:0] addr;
        rand id_t             id;
        rand bit [7:0]        len;
        rand bit [2:0]        size;
        rand axi_burst_e      burst;
        rand awuser_t         awuser;
        // One entry per beat: wdata, wstrb and wuser.
        rand data_t           data[];
        rand strb_bits_t      strb[];
        rand wuser_t          wuser[];
        // Filled from B.
        axi_resp_e            resp;
        buser_t               buser;
        // src role: idle clocks (awvalid low) the master inserts before this AW.
        int unsigned          gap;
        // Bytes the burst may move, (len + 1) << size; 0 means no limit.
        // axi_write_base_seq::new_item() sets it from the port's config.
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

        // A strobe may set only the lanes its beat carries.
        constraint c_beats {
            data.size()  == int'(len) + 1;
            strb.size()  == int'(len) + 1;
            wuser.size() == int'(len) + 1;
            foreach (strb[i]) (strb[i] & ~beat_lanes(addr, size, len, burst, i)) == 0;
        }

        `uvm_object_param_utils(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name = "axi_write_item");
            super.new(name);
        endfunction

        function int unsigned total_bytes();
            return (int'(len) + 1) << size;
        endfunction

        // The byte lanes beat n of a burst carries.
        function strb_bits_t beat_lanes(bit [ADDR_W-1:0] start, bit [2:0] beat_size, bit [7:0] beat_len,
                                        bit [1:0] beat_burst, int unsigned n);
            bit [63:0]   first;
            int unsigned count;
            strb_bits_t  lanes = '0;
            axi_beat(64'(start), beat_size, beat_len, beat_burst, n, first, count);
            for (int unsigned i = 0; i < count; i++) begin
                int unsigned lane = int'((first + i) % (64'd1 << FULL_SIZE));
                if (lane < STRB_W) lanes[lane] = 1'b1;
            end
            return lanes;
        endfunction

        virtual function void do_copy(uvm_object rhs);
            axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) rhs_;
            super.do_copy(rhs);
            $cast(rhs_, rhs);
            addr               = rhs_.addr;
            id                 = rhs_.id;
            len                = rhs_.len;
            size               = rhs_.size;
            burst              = rhs_.burst;
            awuser             = rhs_.awuser;
            data               = rhs_.data;
            strb               = rhs_.strb;
            wuser              = rhs_.wuser;
            resp               = rhs_.resp;
            buser              = rhs_.buser;
            gap                = rhs_.gap;
            max_transfer_bytes = rhs_.max_transfer_bytes;
        endfunction

        // gap and max_transfer_bytes shape the stimulus, so they take no
        // part in the compare.
        virtual function bit do_compare(uvm_object rhs, uvm_comparer comparer);
            axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) rhs_;
            if (!$cast(rhs_, rhs)) return 0;
            if (!super.do_compare(rhs, comparer)) return 0;
            if (addr !== rhs_.addr || id !== rhs_.id || len !== rhs_.len || size !== rhs_.size ||
                burst !== rhs_.burst || awuser !== rhs_.awuser || resp !== rhs_.resp || buser !== rhs_.buser) return 0;
            if (data.size() != rhs_.data.size() || strb.size() != rhs_.strb.size() ||
                wuser.size() != rhs_.wuser.size()) return 0;
            foreach (data[i]) if (data[i] !== rhs_.data[i]) return 0;
            foreach (strb[i]) if (strb[i] !== rhs_.strb[i]) return 0;
            foreach (wuser[i]) if (wuser[i] !== rhs_.wuser[i]) return 0;
            return 1;
        endfunction

        virtual function string convert2string();
            return $sformatf("id=%0h addr=%0h len=%0d size=%0d burst=%s awuser=%0h beats=%0d bresp=%s buser=%0h", id, addr,
                             len, size, burst.name(), awuser, data.size(), resp.name(), buser);
        endfunction

        function string beat2string(int unsigned n);
            return $sformatf("id=%0h beat %0d of %0d wdata=%p wstrb=%0h wuser=%0h", id, n, int'(len) + 1, data[n],
                             strb[n], wuser[n]);
        endfunction
    endclass : axi_write_item

    // The slave's memory: one byte per byte address.
    typedef a2c_mem_model #(bit [7:0]) axi_write_mem_t;

    class axi_write_config #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                             type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                             type id_t = logic [3:0]) extends uvm_object;
        virtual axi_write_if #(.addr_t(addr_t), .data_t(data_t), .strb_t(strb_t), .awuser_t(awuser_t),
                               .wuser_t(wuser_t), .buser_t(buser_t), .id_t(id_t)) vif;
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
        // burst with ID 0, and the monitor does not compare wid with awid.
        bit                                 id_unbound = 0;
        // A2C_SRC role: bursts whose AW has gone out and whose B has not
        // arrived, and the percentage of clocks with bready high.
        int unsigned                        max_outstanding = 1;
        int unsigned                        bready_pct = 100;
        // A2C_DST role. The agent creates mem when the test leaves it null.
        // awready and wready are high on awready_pct and wready_pct percent
        // of clocks. Each burst draws a delay of resp_delay_min to
        // resp_delay_max clocks, counted from the clock its AW and last W
        // have both transferred, before its B may go out. A burst's B still
        // waits for the B of every burst ahead of it, or with reorder only
        // for the bursts ahead of it with its ID. A burst with a beat whose
        // address falls in an error range gets SLVERR and writes nothing.
        axi_write_mem_t                     mem;
        int unsigned                        awready_pct = 100;
        int unsigned                        wready_pct = 100;
        int unsigned                        resp_delay_min = 0;
        int unsigned                        resp_delay_max = 0;
        bit                                 reorder = 0;
        axi_addr_range_t                    error_ranges[$];

        `uvm_object_param_utils(axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name = "axi_write_config");
            super.new(name);
        endfunction
    endclass : axi_write_config

    // The sequence an A2C_SRC test extends. The master returns each burst
    // with its B as a response after item_done(); use_response_handler keeps
    // those responses out of the sequence's response queue, which would
    // otherwise overflow. send() counts the bursts, write_done() sees each
    // response, and wait_for_writes() holds body() until every burst has
    // returned, since a response to a sequence that has ended is dropped.
    // A response with no beats is an item the master refused, and its resp
    // and buser mean nothing. new_item() gives an item whose constraints keep
    // it within the port's max_transfer_bytes.
    class axi_write_base_seq #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                               type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                               type id_t = logic [3:0])
        extends uvm_sequence #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t));
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)   item_t;
        typedef axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) config_t;

        protected int unsigned writes_sent;
        protected int unsigned writes_done;
        protected config_t     cfg;

        `uvm_object_param_utils(axi_write_base_seq#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name = "axi_write_base_seq");
            super.new(name);
            use_response_handler(1);
        endfunction

        // The agent publishes its config to its sequencer, so this works once
        // the sequence has a sequencer.
        function item_t new_item(string name = "item");
            item_t it = item_t::type_id::create(name);
            if (cfg == null && !uvm_config_db#(config_t)::get(m_sequencer, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_write_base_seq: the sequencer has no axi_write config")
            end
            it.max_transfer_bytes = cfg.max_transfer_bytes;
            return it;
        endfunction

        task send(item_t it);
            start_item(it);
            finish_item(it);
            writes_sent++;
        endtask

        task wait_for_writes();
            wait (writes_done >= writes_sent);
        endtask

        // Called once per burst, with the request's fields and beats and the
        // B response.
        virtual function void write_done(item_t rsp);
        endfunction

        virtual function void response_handler(uvm_sequence_item response);
            item_t rsp;
            $cast(rsp, response);
            writes_done++;
            write_done(rsp);
        endfunction
    endclass : axi_write_base_seq

    class axi_write_master_driver #(type addr_t = logic [31:0], type data_t = logic [31:0],
                                    type strb_t = logic [3:0], type awuser_t = logic, type wuser_t = logic,
                                    type buser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t));
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;
        typedef bit [$bits(id_t)-1:0]                                                      id_key_t;

        axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) cfg;

        // Responses waiting for their B, oldest first per ID, and the same
        // objects waiting for their W beats, in AW order. Each is built when
        // its AW goes out, because a sequence may reuse the request object
        // for its next item.
        protected item_t       pending[id_key_t][$];
        protected item_t       w_queue[$];
        protected int unsigned outstanding;

        `uvm_component_param_utils(axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            cfg.vif.awvalid <= 1'b0;
            cfg.vif.awid    <= '0;
            cfg.vif.awaddr  <= '0;
            cfg.vif.awlen   <= '0;
            cfg.vif.awsize  <= '0;
            cfg.vif.awburst <= '0;
            cfg.vif.awuser  <= '0;
            cfg.vif.wvalid  <= 1'b0;
            cfg.vif.wid     <= '0;
            cfg.vif.wdata   <= '0;
            cfg.vif.wstrb   <= '0;
            cfg.vif.wlast   <= 1'b0;
            cfg.vif.wuser   <= '0;
            cfg.vif.bready  <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            fork
                run_w();
                run_b();
            join_none
            run_aw();
        endtask

        // The response to req, with its AW fields and beats and no B yet.
        protected function item_t new_response(item_t req);
            item_t rsp = item_t::type_id::create("rsp");
            rsp.copy(req);
            rsp.set_id_info(req);
            rsp.resp  = AXI_OKAY;
            rsp.buser = '0;
            return rsp;
        endfunction

        // Why req cannot go on the bus, or "" when it can.
        protected function string refusal(item_t req);
            int unsigned beats = int'(req.len) + 1;
            if (req.data.size() != beats || req.strb.size() != beats || req.wuser.size() != beats) begin
                return $sformatf("has %0d data, %0d strobe and %0d wuser entries for %0d beats", req.data.size(),
                                 req.strb.size(), req.wuser.size(), beats);
            end
            if (cfg.max_transfer_bytes != 0 && req.total_bytes() > cfg.max_transfer_bytes) begin
                return $sformatf("moves %0d bytes, above max_transfer_bytes %0d", req.total_bytes(),
                                 cfg.max_transfer_bytes);
            end
            return "";
        endfunction

        // Each loop iteration starts at a drive point. try_next_item lets
        // back-to-back AWs go out on consecutive clocks, and awvalid drops on
        // the first drive point with no item or no free outstanding slot. An
        // item above a non-zero max_transfer_bytes, or without one data,
        // strobe and wuser entry per beat, is an A2C_CFG error and never
        // reaches the bus. It completes at once with a response that has no
        // beats, so a sequence waiting on its responses goes on.
        protected virtual task run_aw();
            item_t rsp;
            string why;
            forever begin
                if (outstanding >= cfg.max_outstanding) begin
                    cfg.vif.awvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                seq_item_port.try_next_item(req);
                if (req == null) begin
                    cfg.vif.awvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                    continue;
                end
                why = refusal(req);
                if (why != "") begin
                    `uvm_error("A2C_CFG", $sformatf("%s: %s %s, so it is not driven", cfg.port_name,
                                                    req.convert2string(), why))
                    rsp = new_response(req);
                    rsp.data  = new[0];
                    rsp.strb  = new[0];
                    rsp.wuser = new[0];
                    seq_item_port.item_done();
                    seq_item_port.put_response(rsp);
                    continue;
                end
                repeat (req.gap) begin
                    cfg.vif.awvalid <= 1'b0;
                    cfg.clk_vif.drive_edge();
                end
                rsp = new_response(req);
                if (cfg.id_unbound) rsp.id = '0;
                pending[id_key_t'(rsp.id)].push_back(rsp);
                w_queue.push_back(rsp);
                outstanding++;
                cfg.vif.awvalid <= 1'b1;
                cfg.vif.awid    <= rsp.id;
                cfg.vif.awaddr  <= addr_t'(req.addr);
                cfg.vif.awlen   <= req.len;
                cfg.vif.awsize  <= req.size;
                cfg.vif.awburst <= req.burst;
                cfg.vif.awuser  <= req.awuser;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.awready !== 1'b1);
                // The AW transfers at the rising edge before this drive point.
                cfg.clk_vif.drive_edge();
                seq_item_port.item_done();
            end
        endtask

        // A burst joins w_queue at the drive point that raises its awvalid,
        // so its first beat goes out at that drive point or a later one.
        // wlast marks beat len.
        protected virtual task run_w();
            item_t       cur;
            int unsigned beat;
            forever begin
                if (cur == null && w_queue.size() != 0) begin
                    cur  = w_queue.pop_front();
                    beat = 0;
                end
                if (cur != null) begin
                    cfg.vif.wvalid <= 1'b1;
                    cfg.vif.wid    <= cur.id;
                    cfg.vif.wdata  <= cur.data[beat];
                    cfg.vif.wstrb  <= strb_t'(cur.strb[beat]);
                    cfg.vif.wlast  <= (beat == cur.len);
                    cfg.vif.wuser  <= cur.wuser[beat];
                end else begin
                    cfg.vif.wvalid <= 1'b0;
                    cfg.vif.wlast  <= 1'b0;
                end
                cfg.clk_vif.sample_edge();
                if (cur != null && cfg.vif.wready === 1'b1) begin
                    beat++;
                    if (beat > cur.len) cur = null;
                end
                cfg.clk_vif.drive_edge();
            end
        endtask

        protected virtual task run_b();
            forever begin
                cfg.vif.bready <= ($urandom_range(99, 0) < cfg.bready_pct);
                cfg.clk_vif.sample_edge();
                if (cfg.vif.bvalid === 1'b1 && cfg.vif.bready === 1'b1) take_b();
                cfg.clk_vif.drive_edge();
            end
        endtask

        // A B completes the oldest outstanding burst of its bid. The monitor
        // reports a B whose bid matches no burst and a B before its burst's
        // last W. The driver drops a B that matches no burst.
        protected function void take_b();
            id_key_t id = id_key_t'(cfg.vif.bid);
            item_t   rsp;
            if (!pending.exists(id) || pending[id].size() == 0) return;
            rsp       = pending[id].pop_front();
            rsp.resp  = axi_resp_e'(cfg.vif.bresp);
            rsp.buser = cfg.vif.buser;
            outstanding--;
            seq_item_port.put_response(rsp);
        endfunction
    endclass : axi_write_master_driver

    // Writes each burst to cfg.mem once its AW and its last W have both
    // transferred, and answers with B in the order the AWs transfer, or with
    // cfg.reorder in any order that keeps each ID's bursts in AW order. W beats
    // belong to the AWs in order, whether they come before or after the AW.
    // A burst's W ends at wlast, or at its last beat when wlast is missing.
    class axi_write_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0],
                                   type strb_t = logic [3:0], type awuser_t = logic, type wuser_t = logic,
                                   type buser_t = logic, type id_t = logic [3:0])
        extends uvm_driver #(axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t));
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;
        typedef item_t::strb_bits_t                                                        strb_bits_t;
        localparam int unsigned DATA_BYTES = item_t::DATA_BYTES;
        localparam int unsigned FULL_SIZE  = item_t::FULL_SIZE;
        localparam bit          BYTE_LANES = item_t::BYTE_LANES;

        typedef struct {
            data_t      data;
            strb_bits_t strb;
            wuser_t     wuser;
            logic       last;
        } w_beat_t;

        axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) cfg;

        `uvm_component_param_utils(axi_write_slave_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // The index in queue of the burst whose B goes out next, or -1. A
        // burst is ready once its delay has passed and no older burst with
        // its ID is queued. Only the oldest burst may go, unless
        // cfg.reorder lets any ready one.
        protected function int next_b(item_t queue[$], longint due[$], longint clocks);
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

        // Writes the burst's strobed bytes to the memory, or none of them and
        // SLVERR when a beat's address is in an error range.
        protected function void write_burst(item_t aw);
            bit [63:0]   first;
            int unsigned count;
            aw.resp = AXI_OKAY;
            foreach (aw.data[n]) begin
                axi_beat(64'(aw.addr), aw.size, aw.len, aw.burst, n, first, count);
                if (axi_in_error_range(first, cfg.error_ranges)) aw.resp = AXI_SLVERR;
            end
            if (aw.resp == AXI_SLVERR) return;
            foreach (aw.data[n]) begin
                bit [8*DATA_BYTES-1:0] lanes = '0;
                lanes[$bits(data_t)-1:0] = aw.data[n];
                axi_beat(64'(aw.addr), aw.size, aw.len, aw.burst, n, first, count);
                for (int unsigned i = 0; i < count; i++) begin
                    int unsigned lane = int'((first + i) % (64'd1 << FULL_SIZE));
                    if (lane < DATA_BYTES && aw.strb[n][lane]) cfg.mem.write(first + i, lanes[8 * lane +: 8]);
                end
            end
        endfunction

        // Each loop iteration starts at a drive point. A burst's B goes out
        // at the drive point after its AW and last W have both transferred,
        // plus its response delay, and no earlier than the drive point after
        // the B before it transfers.
        virtual task run_phase(uvm_phase phase);
            item_t       aw_queue[$];
            w_beat_t     w_queue[$];
            item_t       b_queue[$];
            longint      due[$];
            item_t       b_cur;
            longint      clocks;
            int          pick;
            cfg.vif.awready <= 1'b0;
            cfg.vif.wready  <= 1'b0;
            cfg.vif.bvalid  <= 1'b0;
            cfg.vif.bid     <= '0;
            cfg.vif.bresp   <= '0;
            cfg.vif.buser   <= '0;
            cfg.clk_vif.wait_reset_release();
            cfg.clk_vif.drive_edge();
            forever begin
                cfg.vif.awready <= ($urandom_range(99, 0) < cfg.awready_pct);
                cfg.vif.wready  <= ($urandom_range(99, 0) < cfg.wready_pct);
                pick = (b_cur == null) ? next_b(b_queue, due, clocks) : -1;
                if (pick >= 0) begin
                    b_cur = b_queue[pick];
                    b_queue.delete(pick);
                    due.delete(pick);
                    cfg.vif.bvalid <= 1'b1;
                    cfg.vif.bid    <= b_cur.id;
                    cfg.vif.bresp  <= b_cur.resp;
                    cfg.vif.buser  <= '0;
                end else if (b_cur == null) begin
                    cfg.vif.bvalid <= 1'b0;
                end
                cfg.clk_vif.sample_edge();
                clocks++;
                if (b_cur != null && cfg.vif.bready === 1'b1) b_cur = null;
                if (cfg.vif.wvalid === 1'b1 && cfg.vif.wready === 1'b1) begin
                    w_queue.push_back('{data: cfg.vif.wdata, strb: strb_bits_t'(cfg.vif.wstrb), wuser: cfg.vif.wuser,
                                        last: cfg.vif.wlast});
                end
                if (cfg.vif.awvalid === 1'b1 && cfg.vif.awready === 1'b1) begin
                    item_t aw = item_t::type_id::create("aw");
                    aw.id     = cfg.vif.awid;
                    aw.addr   = cfg.vif.awaddr;
                    aw.len    = cfg.vif.awlen;
                    aw.size   = cfg.vif.awsize;
                    aw.burst  = axi_burst_e'(cfg.vif.awburst);
                    aw.awuser = cfg.vif.awuser;
                    aw.data   = new[0];
                    aw.strb   = new[0];
                    aw.wuser  = new[0];
                    if (!BYTE_LANES && aw.size != FULL_SIZE) begin
                        `uvm_error("A2C_PROTO", $sformatf("%s: %s is a %0d-byte transfer on a %0d-bit bus, which carries only full-width transfers",
                                                          cfg.port_name, aw.convert2string(), 1 << aw.size, $bits(data_t)))
                    end
                    aw_queue.push_back(aw);
                end
                while (aw_queue.size() != 0 && w_queue.size() != 0) begin
                    item_t       aw   = aw_queue[0];
                    w_beat_t     beat = w_queue.pop_front();
                    int unsigned n    = aw.data.size();
                    aw.data  = new[n + 1](aw.data);
                    aw.strb  = new[n + 1](aw.strb);
                    aw.wuser = new[n + 1](aw.wuser);
                    aw.data[n]  = beat.data;
                    aw.strb[n]  = beat.strb;
                    aw.wuser[n] = beat.wuser;
                    if (beat.last !== 1'b1 && n != aw.len) continue;
                    void'(aw_queue.pop_front());
                    write_burst(aw);
                    b_queue.push_back(aw);
                    due.push_back(clocks + $urandom_range(cfg.resp_delay_max, cfg.resp_delay_min));
                end
                cfg.clk_vif.drive_edge();
            end
        endtask
    endclass : axi_write_slave_driver

    class axi_write_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                              type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                              type id_t = logic [3:0]) extends uvm_monitor;
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) item_t;
        typedef item_t::strb_bits_t                                                        strb_bits_t;
        typedef bit [$bits(id_t)-1:0]                                                      id_key_t;
        localparam int unsigned FULL_SIZE = item_t::FULL_SIZE;
        localparam int unsigned AW_W = $bits(id_t) + $bits(addr_t) + 13 + $bits(awuser_t) + 1;
        localparam int unsigned W_W  = $bits(id_t) + $bits(data_t) + $bits(strb_t) + 1 + $bits(wuser_t) + 1;
        localparam int unsigned B_W  = $bits(id_t) + 2 + $bits(buser_t) + 1;

        typedef struct {
            id_t        wid;
            data_t      data;
            strb_bits_t strb;
            wuser_t     wuser;
            logic       last;
        } w_beat_t;

        axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) cfg;
        // One item per burst, at its B, with its AW fields, beats and B.
        uvm_analysis_port #(item_t)                                                 ap;

        // Bursts whose AW has transferred and whose W has not ended, in AW
        // order; W beats no AW has claimed yet; and bursts whose W has ended
        // and whose B has not arrived, oldest first per ID.
        protected item_t   aw_open[$];
        protected w_beat_t w_early[$];
        protected item_t   b_open[id_key_t][$];

        `uvm_component_param_utils(axi_write_monitor#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        // The AW, W and B payloads, each with its valid, as one vector, so a
        // stalled transfer can be compared with the next clock.
        protected function logic [AW_W-1:0] aw_pins();
            return {cfg.vif.awvalid, cfg.vif.awid, cfg.vif.awaddr, cfg.vif.awlen, cfg.vif.awsize, cfg.vif.awburst,
                    cfg.vif.awuser};
        endfunction

        protected function logic [W_W-1:0] w_pins();
            return {cfg.vif.wvalid, cfg.vif.wid, cfg.vif.wdata, cfg.vif.wstrb, cfg.vif.wlast, cfg.vif.wuser};
        endfunction

        protected function logic [B_W-1:0] b_pins();
            return {cfg.vif.bvalid, cfg.vif.bid, cfg.vif.bresp, cfg.vif.buser};
        endfunction

        protected function string path();
            return {get_full_name(), ".", cfg.port_name};
        endfunction

        // A stalled AW, W or B must hold its valid and payload until ready.
        // B is taken first on each clock, since a B may not share the rising
        // edge of its burst's last W.
        virtual task run_phase(uvm_phase phase);
            logic [AW_W-1:0] held_aw;
            logic [W_W-1:0]  held_w;
            logic [B_W-1:0]  held_b;
            bit              aw_stalled;
            bit              w_stalled;
            bit              b_stalled;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (b_stalled && b_pins() !== held_b) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before bready took the stalled response", cfg.port_name,
                                                     cfg.vif.bvalid !== 1'b1 ? "bvalid dropped" : "the B payload changed"))
                end
                if (w_stalled && w_pins() !== held_w) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before wready took the stalled beat", cfg.port_name,
                                                     cfg.vif.wvalid !== 1'b1 ? "wvalid dropped" : "the W payload changed"))
                end
                if (aw_stalled && aw_pins() !== held_aw) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: %s before awready took the stalled AW", cfg.port_name,
                                                     cfg.vif.awvalid !== 1'b1 ? "awvalid dropped" : "the AW payload changed"))
                end
                b_stalled  = cfg.vif.bvalid === 1'b1 && cfg.vif.bready !== 1'b1;
                w_stalled  = cfg.vif.wvalid === 1'b1 && cfg.vif.wready !== 1'b1;
                aw_stalled = cfg.vif.awvalid === 1'b1 && cfg.vif.awready !== 1'b1;
                held_b     = b_pins();
                held_w     = w_pins();
                held_aw    = aw_pins();
                if (cfg.vif.bvalid === 1'b1 && cfg.vif.bready === 1'b1) take_b();
                if (cfg.vif.wvalid === 1'b1 && cfg.vif.wready === 1'b1) begin
                    w_early.push_back('{wid: cfg.vif.wid, data: cfg.vif.wdata, strb: strb_bits_t'(cfg.vif.wstrb),
                                        wuser: cfg.vif.wuser, last: cfg.vif.wlast});
                end
                if (cfg.vif.awvalid === 1'b1 && cfg.vif.awready === 1'b1) take_aw();
                claim_beats();
            end
        endtask

        protected function void take_aw();
            item_t           it = item_t::type_id::create("item");
            longint unsigned nbytes;
            it.id     = cfg.vif.awid;
            it.addr   = cfg.vif.awaddr;
            it.len    = cfg.vif.awlen;
            it.size   = cfg.vif.awsize;
            it.burst  = axi_burst_e'(cfg.vif.awburst);
            it.awuser = cfg.vif.awuser;
            it.data   = new[0];
            it.strb   = new[0];
            it.wuser  = new[0];
            nbytes    = 64'd1 << it.size;
            if (cfg.vif.awburst === 2'b11) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: awburst is the reserved value 2'b11", cfg.port_name))
            end
            if (it.size > FULL_SIZE) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: %s: awsize is wider than the %0d-bit bus", cfg.port_name,
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
            aw_open.push_back(it);
        endfunction

        // W beats belong to the AWs in order, whether they transfer before or
        // after the AW. A burst's W ends at wlast, or at its last beat when
        // wlast is missing. A beat must carry its burst's ID, as the SystemC
        // channel asserts, and set no strobe outside the lanes it carries.
        protected function void claim_beats();
            while (aw_open.size() != 0 && w_early.size() != 0) begin
                item_t       it    = aw_open[0];
                w_beat_t     beat  = w_early.pop_front();
                int unsigned n     = it.data.size();
                bit          last  = (n == it.len);
                strb_bits_t  lanes = it.beat_lanes(it.addr, it.size, it.len, it.burst, n);
                it.data  = new[n + 1](it.data);
                it.strb  = new[n + 1](it.strb);
                it.wuser = new[n + 1](it.wuser);
                it.data[n]  = beat.data;
                it.strb[n]  = beat.strb;
                it.wuser[n] = beat.wuser;
                `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.beat2string(n), $sformatf("%0h", it.data[n])), UVM_HIGH)
                if (!cfg.id_unbound && beat.wid !== it.id) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: wid %0h on beat %0d of the burst %s", cfg.port_name,
                                                      beat.wid, n, it.convert2string()))
                end
                if ((beat.strb & ~lanes) != 0) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: wstrb %b on beat %0d of the burst %s sets lanes outside %b",
                                                      cfg.port_name, beat.strb, n, it.convert2string(), lanes))
                end
                if (beat.last !== last) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: wlast is %b on beat %0d of the %0d-beat burst %s", cfg.port_name,
                                                      beat.last, n, int'(it.len) + 1, it.convert2string()))
                end
                if (beat.last !== 1'b1 && !last) continue;
                void'(aw_open.pop_front());
                b_open[id_key_t'(it.id)].push_back(it);
            end
        endfunction

        // A B completes the oldest burst of its bid whose W has ended.
        protected function void take_b();
            id_key_t id = id_key_t'(cfg.vif.bid);
            item_t   it;
            if (!b_open.exists(id) || b_open[id].size() == 0) begin
                foreach (aw_open[i]) begin
                    if (id_key_t'(aw_open[i].id) == id) begin
                        `uvm_error("A2C_PROTO", $sformatf("%s: B with bid %0h arrived before the last W of %s",
                                                          cfg.port_name, id, aw_open[i].convert2string()))
                        return;
                    end
                end
                `uvm_error("A2C_PROTO", $sformatf("%s: B with bid %0h matches no outstanding write", cfg.port_name, id))
                return;
            end
            it       = b_open[id].pop_front();
            it.resp  = axi_resp_e'(cfg.vif.bresp);
            it.buser = cfg.vif.buser;
            `uvm_info("A2C_TXN", a2c_txn(path(), cfg.role, it.convert2string(), $sformatf("%0h", it.addr)), UVM_MEDIUM)
            ap.write(it);
        endfunction

        // Every W beat must belong to a burst, and every burst must have
        // ended its W and received its B, by the end of the run.
        virtual function void check_phase(uvm_phase phase);
            int unsigned waiting = 0;
            foreach (b_open[id]) waiting += b_open[id].size();
            if (w_early.size() != 0 || aw_open.size() != 0 || waiting != 0) begin
                `uvm_error("A2C_PROTO", $sformatf("%s: the run ended with %0d W beats no AW claimed, %0d bursts whose W had not ended and %0d bursts waiting for B",
                                                  cfg.port_name, w_early.size(), aw_open.size(), waiting))
            end
        endfunction
    endclass : axi_write_monitor

    class axi_write_agent #(type addr_t = logic [31:0], type data_t = logic [31:0], type strb_t = logic [3:0],
                            type awuser_t = logic, type wuser_t = logic, type buser_t = logic,
                            type id_t = logic [3:0]) extends uvm_agent;
        typedef axi_write_item#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)   item_t;
        typedef axi_write_config#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) config_t;

        config_t                                                                       cfg;
        // axi_write_master_driver for A2C_SRC, axi_write_slave_driver for A2C_DST.
        uvm_driver #(item_t)                                                           drv;
        // A2C_SRC only.
        uvm_sequencer #(item_t)                                                        sqr;
        axi_write_monitor#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) mon;

        `uvm_component_param_utils(axi_write_agent#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(config_t)::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "axi_write_agent has no cfg")
            end
            if ($bits(data_t) != 8 * $bits(strb_t)) begin
                `uvm_fatal("A2C_CFG", $sformatf("%s: data_t is %0d bits and strb_t %0d, but wstrb needs one bit per data byte",
                                                cfg.port_name, $bits(data_t), $bits(strb_t)))
            end
            mon = axi_write_monitor#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_SRC) begin
                axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) master;
                if (cfg.max_outstanding == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: max_outstanding is 0, so no burst could go out", cfg.port_name))
                end
                if (cfg.bready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: bready_pct is 0, so no burst could complete", cfg.port_name))
                end
                master = axi_write_master_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)::type_id::create("drv", this);
                master.cfg = cfg;
                drv = master;
                sqr = uvm_sequencer#(item_t)::type_id::create("sqr", this);
                uvm_config_db#(config_t)::set(this, "sqr", "cfg", cfg);
            end else begin
                axi_write_slave_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t) slave;
                if (cfg.awready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: awready_pct is 0, so no AW could transfer", cfg.port_name))
                end
                if (cfg.wready_pct == 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: wready_pct is 0, so no W beat could transfer", cfg.port_name))
                end
                if (cfg.resp_delay_min > cfg.resp_delay_max) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: resp_delay_min %0d is above resp_delay_max %0d", cfg.port_name,
                                                    cfg.resp_delay_min, cfg.resp_delay_max))
                end
                if (cfg.mem == null) cfg.mem = axi_write_mem_t::type_id::create({get_full_name(), ".mem"});
                slave = axi_write_slave_driver#(addr_t, data_t, strb_t, awuser_t, wuser_t, buser_t, id_t)::type_id::create("drv", this);
                slave.cfg = cfg;
                drv = slave;
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
        endfunction
    endclass : axi_write_agent

endpackage : axi_write_uvm_pkg

`endif // AXI_WRITE_UVM_PKG_SV
