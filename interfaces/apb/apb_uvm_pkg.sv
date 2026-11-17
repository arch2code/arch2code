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
// beside the DUT's and monitors it with model_mon, and model_cmp compares the
// transfers the two lanes report, in order: write, addr, data (prdata on a
// read) and slverr. The master starts each transfer on both lanes at one drive
// point, each lane's access phase ends at its own pready, and the item
// completes when both have, with the DUT lane's prdata and pslverr in req. A
// lane of the master that trails the other by lane_skew_cycles clocks, or
// stalls, is declared dead as for the AXI masters (a2c_lane_watchdog), and the
// other lane serves the sequence alone. The slave serves both lanes from the
// one cfg.mem. The DUT lane applies every transfer and the model lane follows:
// it gets the DUT lane's response to transfer n after the same wait clocks,
// whatever its own transfer asks for, and a model lane that reaches transfer n
// first holds pready low until the DUT lane has applied it. When the run phase
// is ready to end, the slave's replay log holds it while the model lane
// catches up (a2c_replay_drain). What the DUT produces that is not compared:
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

    class apb_config #(type addr_t = logic [31:0], type data_t = logic [31:0])
        extends a2c_agent_config #(virtual apb_if #(.addr_t(addr_t), .data_t(data_t)));
        // A2C_DST role. Byte k of the bus is the byte at paddr + k in mem,
        // which the agent creates when the test leaves it null. pready rises
        // after 0 to max_wait wait clocks of the access phase, drawn per
        // transfer. An access whose paddr falls in an error range gets
        // pslverr and leaves mem untouched.
        apb_mem_t         mem;
        rand int unsigned max_wait = 0;
        apb_addr_range_t  error_ranges[$];

        constraint c_default { soft max_wait == 0; }

        `uvm_object_param_utils(apb_config#(addr_t, data_t))

        function new(string name = "apb_config");
            super.new(name);
        endfunction
    endclass : apb_config

    class apb_master_driver #(type addr_t = logic [31:0], type data_t = logic [31:0])
        extends a2c_lane_driver #(apb_item, virtual apb_if #(.addr_t(addr_t), .data_t(data_t)), apb_config#(addr_t, data_t));
        `uvm_component_param_utils(apb_master_driver#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            none_left = "every open and later item completes at once, a read with the data it was sent with";
        endfunction

        // One transfer per item: setup phase, access phase held until PREADY,
        // then the bus returns to idle. Read data and PSLVERR go back in req.
        protected virtual task run_src();
            for (int l = 0; l < lanes; l++) begin
                lane[l].psel    <= 1'b0;
                lane[l].penable <= 1'b0;
                lane[l].pwrite  <= 1'b0;
                lane[l].paddr   <= addr_t'(32'h0);
                lane[l].pwdata  <= data_t'(32'h0);
            end
            cfg.clk_vif.wait_reset_release();
            if (lanes == 2) begin
                fork
                    release_dead();
                join_none
            end
            forever begin
                get_item();
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) begin
                    if (wd.dead[l]) continue;
                    lane[l].psel    <= 1'b1;
                    lane[l].penable <= 1'b0;
                    lane[l].pwrite  <= req.write;
                    lane[l].paddr   <= addr_t'(req.addr);
                    lane[l].pwdata  <= data_t'(req.write ? req.data : 32'h0);
                end
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) if (!wd.dead[l]) lane[l].penable <= 1'b1;
                wait_access();
                item_finished();
            end
        endtask

        // Returns at the drive point after the last live lane's access
        // phase ended, with the DUT lane's read data and PSLVERR in req, or
        // the model lane's once the DUT lane is dead. Each lane returns to
        // idle at the drive point after its own pready. In Mode B wd bounds
        // how long one lane may trail the other and how long the lanes may
        // stall (a2c_lane_watchdog), and a lane it declares dead drops out of
        // the wait.
        protected task wait_access();
            bit        pending[2];
            bit        ended[2];
            bit        finished[2];
            bit [31:0] prdata[2];
            bit        pslverr[2];
            wd.begin_item();
            for (int l = 0; l < lanes; l++) pending[l] = !wd.dead[l];
            while (pending[A2C_DUT_LANE] || pending[A2C_MODEL_LANE]) begin
                cfg.clk_vif.sample_edge();
                for (int l = 0; l < lanes; l++) begin
                    ended[l]     = pending[l] && request_taken(l);
                    pending[l]  &= !ended[l];
                    finished[l] |= ended[l];
                    if (!ended[l]) continue;
                    prdata[l]  = 32'(lane[l].prdata);
                    pslverr[l] = lane[l].pslverr;
                    if (l != A2C_DUT_LANE) continue;
                    if (!req.write) req.data = prdata[l];
                    req.slverr = pslverr[l];
                end
                wd.step(ended, pending);
                cfg.clk_vif.drive_edge();
                for (int l = 0; l < lanes; l++) if (ended[l]) drop_request(l);
            end
            if (finished[A2C_DUT_LANE] || !finished[A2C_MODEL_LANE]) return;
            if (!req.write) req.data = prdata[A2C_MODEL_LANE];
            req.slverr = pslverr[A2C_MODEL_LANE];
        endtask

        virtual function string waiting_for(a2c_lane_e l);
            return $sformatf("the %s of address 0x%08h", a2c_access_name(req.write), req.addr);
        endfunction

        // A dead lane stays in its access phase, with its address, direction
        // and write data, until pready ends it (release_dead()).
        protected virtual function void drop_request(int l);
            lane[l].psel    <= 1'b0;
            lane[l].penable <= 1'b0;
            lane[l].pwrite  <= 1'b0;
        endfunction

        protected virtual function bit request_held(int l);
            return lane[l].psel === 1'b1 && lane[l].penable === 1'b1;
        endfunction

        protected virtual function bit request_taken(int l);
            return lane[l].pready === 1'b1;
        endfunction

        // A transfer a mid-run reset cut short failed, so apb_reg_adapter
        // returns UVM_NOT_OK rather than OK with the data it was sent with.
        protected virtual function void abandon_held(apb_item item);
            item.slverr = 1'b1;
        endfunction
    endclass : apb_master_driver

    // Serves each transfer from cfg.mem. The address, direction and write
    // data are taken in the setup phase; the monitor reports a master that
    // changes them later. The slave applies the transfer to cfg.mem at that
    // setup sample, so a change to cfg.mem during the wait states is not seen.
    // In Mode B the DUT lane always applies and the model lane follows: a
    // model lane waiting on transfer n replays it on the clock the DUT lane
    // applies it. pready is high for the one clock that ends the transfer,
    // and the sample point after it can see the next setup phase, so
    // back-to-back transfers are served.
    class apb_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0])
        extends a2c_lane_driver #(apb_item, virtual apb_if #(.addr_t(addr_t), .data_t(data_t)), apb_config#(addr_t, data_t),
                                  logic [$bits(data_t):0]);
        localparam int unsigned BYTES = $bits(data_t) / 8;

        // A transfer's response, which the replay log hands the model lane.
        typedef struct packed {
            logic [$bits(data_t)-1:0] rdata;
            bit                       slverr;
        } rsp_t;

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

        protected virtual function bit request_seen(int l);
            return lane[l].psel === 1'b1 && lane[l].penable !== 1'b1;
        endfunction

        // An APB master cannot withdraw a transfer.
        protected virtual function bit request_withdrawn(int l);
            return 0;
        endfunction

        // In Mode B this is the only place the model lane's response and
        // wait clocks are drawn.
        protected virtual task respond(output logic [$bits(data_t):0] r, output int unsigned delay, output bit at_edge);
            bit [31:0]                addr  = 32'(lane[A2C_DUT_LANE].paddr);
            bit                       write = lane[A2C_DUT_LANE].pwrite;
            logic [$bits(data_t)-1:0] wdata = lane[A2C_DUT_LANE].pwdata;
            rsp_t                     rsp;
            rsp.slverr = in_error_range(addr);
            delay      = policy.next_delay("pready", 0, cfg.max_wait);
            rsp.rdata  = '0;
            if (!rsp.slverr) begin
                for (int unsigned b = 0; b < BYTES; b++) begin
                    if (write) cfg.mem.write(addr + b, wdata[8 * b +: 8]);
                    else rsp.rdata[8 * b +: 8] = cfg.mem.read(addr + b);
                end
            end
            r       = rsp;
            at_edge = 0;
        endtask

        protected virtual function void idle_response(int l);
            lane[l].pready  <= 1'b0;
            lane[l].prdata  <= '0;
            lane[l].pslverr <= 1'b0;
        endfunction

        protected virtual function void drive_response(int l, logic [$bits(data_t):0] r);
            rsp_t rsp = r;
            lane[l].pready  <= 1'b1;
            lane[l].prdata  <= data_t'(rsp.rdata);
            lane[l].pslverr <= rsp.slverr;
        endfunction

        protected virtual function void end_response(int l);
            lane[l].pready  <= 1'b0;
            lane[l].pslverr <= 1'b0;
        endfunction
    endclass : apb_slave_driver

    class apb_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends a2c_monitor;
        apb_config#(addr_t, data_t)  cfg;
        // The lane this monitor samples, cfg.vif or cfg.model_vif.
        virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        uvm_analysis_port #(apb_item) ap;

        `uvm_component_param_utils(apb_monitor#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual function a2c_clk_vif_t monitor_clock();
            return cfg.clk_vif;
        endfunction

        // An access phase continues the transfer when the clock before it was
        // the setup phase or an access phase pready did not end. Any other
        // clock with psel and penable high is an A2C_PROTO; penable with psel
        // low is not, because a completer that is not selected ignores it.
        // Within a transfer, each clock that changes paddr, pwrite, or a
        // write's pwdata gives one A2C_HOLD, and so does psel dropping before
        // the transfer completes.
        virtual task run_from_reset();
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
                if (cfg.clk_vif.in_reset()) continue;
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
                // Each transfer counts for the joint stall rule (a2c_joint_watch).
                if (cfg.joint_watch) a2c_joint_watch::handshake();
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

    // The apb agent's model_cmp.
    class apb_comparator extends a2c_reg_comparator #(apb_item);
        `uvm_component_utils(apb_comparator)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function bit is_read(apb_item t, output uvm_reg_addr_t addr);
            addr = t.addr;
            return !t.write;
        endfunction

        virtual function bit same_but_data(apb_item dut, apb_item model);
            return dut.write == model.write && dut.addr == model.addr && dut.slverr == model.slverr;
        endfunction
    endclass : apb_comparator

    // Coverage of the APB transfers on the DUT lane: read or write, the address in
    // 16 equal ranges of addr_t, and the two crossed.
    class apb_coverage #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_subscriber #(apb_item);
        covergroup cg_access with function sample(bit is_write, bit [$bits(addr_t)-1:0] addr);
            option.per_instance = 1;
            dir: coverpoint is_write {
                bins read = {0}; bins write = {1};
            }
            addr_range: coverpoint addr {
                option.auto_bin_max = 16;
            }
            dir_x_addr: cross dir, addr_range;
        endgroup

        `uvm_component_param_utils(apb_coverage#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            cg_access = new();
            cg_access.set_inst_name({get_full_name(), ".cg_access"});
        endfunction

        virtual function void write(apb_item t);
            cg_access.sample(t.write, t.addr);
        endfunction
    endclass : apb_coverage

    class apb_agent #(type addr_t = logic [31:0], type data_t = logic [31:0])
        extends a2c_lane_agent #(virtual apb_if #(.addr_t(addr_t), .data_t(data_t)));
        typedef apb_item                    item_t;
        typedef apb_config#(addr_t, data_t) config_t;
        typedef apb_coverage #(addr_t, data_t) cov_t;

        apb_config#(addr_t, data_t)  cfg;
        // apb_master_driver for A2C_SRC, apb_slave_driver for A2C_DST.
        uvm_driver #(apb_item)       drv;
        // A2C_SRC only.
        uvm_sequencer #(apb_item)    sqr;
        apb_monitor#(addr_t, data_t) mon;
        // Mode B only.
        apb_monitor#(addr_t, data_t) model_mon;
        apb_comparator               model_cmp;

        // has_coverage only.
        cov_t cov;

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
            if (coverage_on()) cov = a2c_coverage#(cov_t)::create("cov", this);
            if (cfg.model_vif != null) begin
                model_mon = apb_monitor#(addr_t, data_t)::type_id::create("model_mon", this);
                model_mon.cfg = cfg;
                model_mon.vif = cfg.model_vif;
                model_cmp = apb_comparator::type_id::create("model_cmp", this);
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
            super.connect_phase(phase);
            if (cov != null) mon.ap.connect(cov.analysis_export);
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
            end
            if (model_cmp != null) begin
                mon.ap.connect(model_cmp.dut_export);
                model_mon.ap.connect(model_cmp.model_export);
            end
        endfunction

        virtual function lane_cfg_t lane_cfg();
            return cfg;
        endfunction

        // The master and the slave are both lane drivers; drv holds either.
        virtual function a2c_lane_joiner lane_joiner();
            a2c_lane_joiner j;
            void'($cast(j, drv));
            return j;
        endfunction

        virtual function uvm_monitor lane_monitor(a2c_lane_e l);
            return (l == A2C_DUT_LANE) ? mon : model_mon;
        endfunction

        virtual function a2c_comparator_base lane_cmp();
            return model_cmp;
        endfunction
    endclass : apb_agent

    // A register access is one 32-bit APB transfer; PSLVERR maps to UVM_NOT_OK.
    // UVM passes each word of a memory burst as its own access, of kind
    // UVM_BURST_WRITE or UVM_BURST_READ.
    class apb_reg_adapter extends uvm_reg_adapter;
        `uvm_object_utils(apb_reg_adapter)

        function new(string name = "apb_reg_adapter");
            super.new(name);
            supports_byte_enable = 0;
            provides_responses   = 0;
        endfunction

        virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
            apb_item item = apb_item::type_id::create("item");
            item.write = rw.kind inside {UVM_WRITE, UVM_BURST_WRITE};
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
