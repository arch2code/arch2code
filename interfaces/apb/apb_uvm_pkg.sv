`ifndef APB_UVM_PKG_SV
`define APB_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for apb_if: an APB3 master driver for the A2C_SRC role, a slave
// driver for the A2C_DST role, a monitor and the register adapter. AMBA 5
// calls the two sides Requester and Completer. Items carry 32-bit address and
// data; addr_t and data_t are the interface's packed types. Pin timing
// follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
//
// Mode B. With cfg.model_vif set the agent drives the model DUT's pin set
// beside the DUT's and monitors it with model_mon, and model_cmp compares
// the transfers the two lanes report, in order: write, addr, data (prdata on
// a read) and slverr. The master starts each transfer on both lanes at one
// drive point, each lane's access phase ends at its own pready, and the item
// completes when both have, with the DUT lane's prdata and pslverr in req.
// The slave serves both lanes from the one cfg.mem. The DUT lane applies
// every transfer and the model lane follows: it gets the DUT lane's
// response to transfer n after the same wait clocks, whatever its own
// transfer asks for, and a model lane that reaches transfer n first holds
// pready low until the DUT lane has applied it. When the run phase is ready
// to end, the slave's replay log holds it while the model lane catches up
// (a2c_replay_drain). What the DUT produces that is not compared:
//   DUT apb dst port, A2C_SRC master: wait states
//   DUT apb src port, A2C_DST slave: none
package apb_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"
    import a2c_uvm_pkg::*;

    class apb_item extends uvm_sequence_item;
        rand bit        write;
        rand bit [31:0] addr;
        rand bit [31:0] data;
        // Set by the driver and the monitor from PSLVERR.
        bit             slverr;

        `uvm_object_utils_begin(apb_item)
            `uvm_field_int(write,  UVM_ALL_ON)
            `uvm_field_int(addr,   UVM_ALL_ON)
            `uvm_field_int(data,   UVM_ALL_ON)
            `uvm_field_int(slverr, UVM_ALL_ON)
        `uvm_object_utils_end

        function new(string name = "apb_item");
            super.new(name);
        endfunction

        virtual function string convert2string();
            return $sformatf("write=%0d addr=0x%08h data=0x%08h slverr=%0d", write, addr, data, slverr);
        endfunction
    endclass : apb_item

    // The slave's memory: one byte per byte address.
    typedef a2c_mem_model #(bit [7:0]) apb_mem_t;

    // An inclusive range of byte addresses.
    typedef struct {
        bit [31:0] lo;
        bit [31:0] hi;
    } apb_addr_range_t;

    class apb_config #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_object;
        virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        // The model DUT's pin set in Mode B; null otherwise.
        virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) model_vif;
        virtual a2c_clk_if                                 clk_vif;
        uvm_active_passive_enum                            is_active = UVM_ACTIVE;
        a2c_role_e                                         role = A2C_SRC;
        string                                             port_name = "";
        // A2C_DST role. Byte k of the bus is the byte at paddr + k in mem,
        // which the agent creates when the test leaves it null. pready rises
        // after 0 to max_wait wait clocks of the access phase, drawn per
        // transfer. An access whose paddr falls in an error range gets
        // pslverr and leaves mem untouched.
        apb_mem_t                                          mem;
        int unsigned                                       max_wait = 0;
        apb_addr_range_t                                   error_ranges[$];

        `uvm_object_param_utils(apb_config#(addr_t, data_t))

        function new(string name = "apb_config");
            super.new(name);
        endfunction
    endclass : apb_config

    class apb_master_driver #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_driver #(apb_item);
        typedef virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) vif_t;

        apb_config#(addr_t, data_t) cfg;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;

        `uvm_component_param_utils(apb_master_driver#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // One transfer per item: setup phase, access phase held until PREADY,
        // then the bus returns to idle. Read data and PSLVERR go back in req.
        virtual task run_phase(uvm_phase phase);
            lane[A2C_DUT_LANE] = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            for (int l = 0; l < lanes; l++) begin
                lane[l].psel    <= 1'b0;
                lane[l].penable <= 1'b0;
                lane[l].pwrite  <= 1'b0;
                lane[l].paddr   <= addr_t'(32'h0);
                lane[l].pwdata  <= data_t'(32'h0);
            end
            cfg.clk_vif.wait_reset_release();
            forever begin
                seq_item_port.get_next_item(req);
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    lane[l].psel    <= 1'b1;
                    lane[l].penable <= 1'b0;
                    lane[l].pwrite  <= req.write;
                    lane[l].paddr   <= addr_t'(req.addr);
                    lane[l].pwdata  <= data_t'(req.write ? req.data : 32'h0);
                end
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) lane[l].penable <= 1'b1;
                wait_access();
                seq_item_port.item_done();
            end
        endtask

        // Returns at the drive point after the last lane's access phase
        // ended. Each lane returns to idle at the drive point after its own
        // pready.
        protected task wait_access();
            bit          pending[2];
            bit          ended[2];
            int unsigned left = lanes;
            for (int l = 0; l < lanes; l++) pending[l] = 1'b1;
            while (left > 0) begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    ended[l] = pending[l] && lane[l].pready === 1'b1;
                    if (!ended[l]) continue;
                    if (l == A2C_DUT_LANE) begin
                        if (!req.write) begin
                            req.data = 32'(lane[l].prdata);
                        end
                        req.slverr = lane[l].pslverr;
                    end
                    pending[l] = 1'b0;
                    left--;
                end
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (!ended[l]) continue;
                    lane[l].psel    <= 1'b0;
                    lane[l].penable <= 1'b0;
                    lane[l].pwrite  <= 1'b0;
                end
            end
        endtask
    endclass : apb_master_driver

    // Serves each transfer from cfg.mem. The address, direction and write
    // data are taken in the setup phase; the monitor reports a master that
    // changes them later. The slave applies the transfer to cfg.mem at that
    // setup sample, so a change to cfg.mem during the wait states is not seen.
    // In Mode B the DUT lane always applies and the model lane follows.
    class apb_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_driver #(apb_item)
        implements a2c_replay_lanes;
        localparam int unsigned BYTES = $bits(data_t) / 8;

        typedef virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) vif_t;
        // A transfer's response, which the replay log hands the model lane.
        typedef struct packed {
            logic [$bits(data_t)-1:0] rdata;
            bit                       slverr;
        } rsp_t;
        typedef a2c_replay_log #(rsp_t) replay_t;
        // LANE_SETUP: a model lane that has seen its setup phase and waits
        // for the DUT lane to apply the transfer.
        typedef enum {LANE_IDLE, LANE_SETUP, LANE_WAIT, LANE_READY} lane_state_e;

        apb_config#(addr_t, data_t) cfg;
        // Mode B only.
        replay_t                    replay;

        // Indexed by a2c_lane_e; lanes is 2 in Mode B and 1 otherwise.
        protected vif_t        lane[2];
        protected int unsigned lanes;
        protected lane_state_e state[2];
        protected int unsigned starts[2];
        // The transactions each lane has completed, each counted at the
        // drive point of its last clock, from which it cannot be withdrawn.
        protected int unsigned done[2];

        `uvm_component_param_utils(apb_slave_driver#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function bit in_error_range(bit [31:0] addr);
            foreach (cfg.error_ranges[i]) begin
                if (addr >= cfg.error_ranges[i].lo && addr <= cfg.error_ranges[i].hi) return 1;
            end
            return 0;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (cfg.model_vif == null) return;
            replay = replay_t::type_id::create("replay", this);
            replay.driver  = this;
            replay.clk_vif = cfg.clk_vif;
        endfunction

        // In Mode B this is the only place the model lane's response and
        // wait clocks are recorded.
        protected function void apply(output rsp_t rsp, output int unsigned wait_clocks);
            bit [31:0]                addr  = 32'(lane[A2C_DUT_LANE].paddr);
            bit                       write = lane[A2C_DUT_LANE].pwrite;
            logic [$bits(data_t)-1:0] wdata = lane[A2C_DUT_LANE].pwdata;
            rsp.slverr  = in_error_range(addr);
            wait_clocks = $urandom_range(cfg.max_wait, 0);
            rsp.rdata   = '0;
            if (!rsp.slverr) begin
                for (int unsigned b = 0; b < BYTES; b++) begin
                    if (write) cfg.mem.write(addr + b, wdata[8 * b +: 8]);
                    else rsp.rdata[8 * b +: 8] = cfg.mem.read(addr + b);
                end
            end
            if (replay != null) replay.record(rsp, wait_clocks);
        endfunction

        // One process serves every lane, sampling the DUT lane first, so a
        // model lane waiting on transfer n replays it on the clock the DUT
        // lane applies it. pready is high for the one clock that ends the
        // transfer, and the sample point after it can see the next setup
        // phase, so back-to-back transfers are served.
        virtual task run_phase(uvm_phase phase);
            int unsigned wait_clocks[2];
            rsp_t        rsp[2];
            lane[A2C_DUT_LANE] = cfg.vif;
            lane[A2C_MODEL_LANE] = cfg.model_vif;
            lanes = (cfg.model_vif != null) ? 2 : 1;
            for (int l = 0; l < lanes; l++) begin
                state[l] = LANE_IDLE;
                lane[l].pready  <= 1'b0;
                lane[l].prdata  <= '0;
                lane[l].pslverr <= 1'b0;
            end
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (state[l] == LANE_IDLE && lane[l].psel === 1'b1 && lane[l].penable !== 1'b1) begin
                        state[l] = LANE_SETUP;
                        starts[l]++;
                    end
                    if (state[l] != LANE_SETUP) continue;
                    if (l == A2C_DUT_LANE) apply(rsp[l], wait_clocks[l]);
                    else if (replay.can_replay()) replay.replay(rsp[l], wait_clocks[l]);
                    else continue;
                    state[l] = LANE_WAIT;
                end
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    case (state[l])
                        LANE_WAIT: begin
                            if (wait_clocks[l] > 0) begin
                                wait_clocks[l]--;
                            end else begin
                                lane[l].pready  <= 1'b1;
                                lane[l].prdata  <= data_t'(rsp[l].rdata);
                                lane[l].pslverr <= rsp[l].slverr;
                                state[l] = LANE_READY;
                                done[l]++;
                            end
                        end
                        LANE_READY: begin
                            lane[l].pready  <= 1'b0;
                            lane[l].pslverr <= 1'b0;
                            state[l] = LANE_IDLE;
                        end
                        default: ;
                    endcase
                end
            end
        endtask

        virtual function bit lane_busy(a2c_lane_e l);
            return state[l] != LANE_IDLE;
        endfunction

        virtual function int unsigned lane_done(a2c_lane_e l);
            return done[l];
        endfunction

        virtual function int unsigned lane_starts(a2c_lane_e l);
            return starts[l];
        endfunction
    endclass : apb_slave_driver

    class apb_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_monitor;
        apb_config#(addr_t, data_t)  cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        uvm_analysis_port #(apb_item) ap;

        `uvm_component_param_utils(apb_monitor#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        // An access phase continues the transfer when the clock before it was
        // the setup phase or an access phase pready did not end. Any other
        // clock with psel and penable high is an A2C_PROTO; penable with psel
        // low is not, because a completer that is not selected ignores it.
        // Within a transfer, each clock that changes paddr, pwrite, or a
        // write's pwdata gives one A2C_HOLD, and so does psel dropping before
        // the transfer completes.
        virtual task run_phase(uvm_phase phase);
            apb_item item;
            bit      setup;
            bit      access;
            bit      in_transfer = 0;
            addr_t   held_addr;
            logic    held_write;
            data_t   held_wdata;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                setup  = (vif.psel === 1'b1 && vif.penable !== 1'b1);
                access = (vif.psel === 1'b1 && vif.penable === 1'b1);
                if (in_transfer && vif.psel !== 1'b1) begin
                    `uvm_error("A2C_HOLD", $sformatf("%s: psel dropped before the transfer completed at paddr %h",
                                                     cfg.port_name, held_addr))
                end
                if (access && !in_transfer) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: psel and penable are high with no setup phase on the clock before",
                                                      cfg.port_name))
                end
                if (access && in_transfer) begin
                    string changed[$];
                    if (vif.paddr !== held_addr) changed.push_back("paddr");
                    if (vif.pwrite !== held_write) changed.push_back("pwrite");
                    else if (held_write === 1'b1 && vif.pwdata !== held_wdata) changed.push_back("pwdata");
                    if (changed.size() != 0) begin
                        string what = changed[0];
                        for (int i = 1; i < changed.size(); i++) what = {what, ", ", changed[i]};
                        `uvm_error("A2C_HOLD", $sformatf("%s: %s changed before pready ended the transfer at paddr %h",
                                                         cfg.port_name, what, held_addr))
                    end
                end
                held_addr   = vif.paddr;
                held_write  = vif.pwrite;
                held_wdata  = vif.pwdata;
                in_transfer = setup || (access && vif.pready !== 1'b1);
                if (!(access && vif.pready === 1'b1)) continue;
                item = apb_item::type_id::create("item");
                item.write  = vif.pwrite;
                item.addr   = 32'(vif.paddr);
                item.data   = item.write ? 32'(vif.pwdata) : 32'(vif.prdata);
                item.slverr = vif.pslverr;
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, cfg.role, item.convert2string(),
                                             $sformatf("%0h", {item.write, item.addr, item.data})), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : apb_monitor

    class apb_agent #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_agent;
        typedef apb_item                    item_t;
        typedef apb_config#(addr_t, data_t) config_t;

        apb_config#(addr_t, data_t)  cfg;
        // apb_master_driver for A2C_SRC, apb_slave_driver for A2C_DST.
        uvm_driver #(apb_item)       drv;
        // A2C_SRC only.
        uvm_sequencer #(apb_item)    sqr;
        apb_monitor#(addr_t, data_t) mon;
        // Mode B only.
        apb_monitor#(addr_t, data_t)        model_mon;
        a2c_in_order_comparator #(apb_item) model_cmp;

        `uvm_component_param_utils(apb_agent#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            if (!uvm_config_db#(apb_config#(addr_t, data_t))::get(this, "", "cfg", cfg)) begin
                `uvm_fatal("A2C_CFG", "apb_agent has no cfg")
            end
            mon = apb_monitor#(addr_t, data_t)::type_id::create("mon", this);
            mon.cfg = cfg;
            mon.vif = cfg.vif;
            if (cfg.model_vif != null) begin
                model_mon = apb_monitor#(addr_t, data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                model_cmp = a2c_in_order_comparator#(apb_item)::type_id::create("model_cmp", this);
            end
            if (cfg.is_active != UVM_ACTIVE) return;
            if (cfg.role == A2C_SRC) begin
                apb_master_driver#(addr_t, data_t) master;
                master = apb_master_driver#(addr_t, data_t)::type_id::create("drv", this);
                master.cfg = cfg;
                drv = master;
                sqr = uvm_sequencer#(apb_item)::type_id::create("sqr", this);
            end else begin
                apb_slave_driver#(addr_t, data_t) slave;
                if ($bits(data_t) % 8 != 0) begin
                    `uvm_fatal("A2C_CFG", $sformatf("%s: the apb slave serves whole bytes, and data_t is %0d bits",
                                                    cfg.port_name, $bits(data_t)))
                end
                if (cfg.mem == null) cfg.mem = apb_mem_t::type_id::create({get_full_name(), ".mem"});
                slave = apb_slave_driver#(addr_t, data_t)::type_id::create("drv", this);
                slave.cfg = cfg;
                drv = slave;
            end
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            apb_slave_driver#(addr_t, data_t) slave;
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
                if ($cast(slave, drv) && slave.replay != null) slave.replay.cmp = model_cmp;
            end
        endfunction
    endclass : apb_agent

    // A register access is one 32-bit APB transfer; PSLVERR maps to UVM_NOT_OK.
    class apb_reg_adapter extends uvm_reg_adapter;
        `uvm_object_utils(apb_reg_adapter)

        function new(string name = "apb_reg_adapter");
            super.new(name);
            supports_byte_enable = 0;
            provides_responses   = 0;
        endfunction

        virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
            apb_item item = apb_item::type_id::create("item");
            item.write = (rw.kind == UVM_WRITE);
            item.addr  = rw.addr;
            item.data  = rw.data;
            return item;
        endfunction

        virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
            apb_item item;
            if (!$cast(item, bus_item)) begin
                `uvm_fatal("A2C_REG", "bus2reg: not an apb_item")
            end
            rw.kind   = item.write ? UVM_WRITE : UVM_READ;
            rw.addr   = item.addr;
            rw.data   = item.data;
            rw.status = item.slverr ? UVM_NOT_OK : UVM_IS_OK;
        endfunction
    endclass : apb_reg_adapter

endpackage : apb_uvm_pkg

`endif // APB_UVM_PKG_SV
