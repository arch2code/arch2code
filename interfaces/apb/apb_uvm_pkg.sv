`ifndef APB_UVM_PKG_SV
`define APB_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for apb_if: an APB3 master driver for the A2C_SRC role, a slave
// driver for the A2C_DST role, a monitor and the register adapter. AMBA 5
// calls the two sides Requester and Completer. Items carry 32-bit address and
// data; addr_t and data_t are the interface's packed types. Pin timing
// follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
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
        apb_config#(addr_t, data_t) cfg;

        `uvm_component_param_utils(apb_master_driver#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // One transfer per item: setup phase, access phase held until PREADY,
        // then the bus returns to idle. Read data and PSLVERR go back in req.
        virtual task run_phase(uvm_phase phase);
            cfg.vif.psel    <= 1'b0;
            cfg.vif.penable <= 1'b0;
            cfg.vif.pwrite  <= 1'b0;
            cfg.vif.paddr   <= addr_t'(32'h0);
            cfg.vif.pwdata  <= data_t'(32'h0);
            cfg.clk_vif.wait_reset_release();
            forever begin
                seq_item_port.get_next_item(req);
                cfg.clk_vif.drive_edge();
                cfg.vif.psel    <= 1'b1;
                cfg.vif.penable <= 1'b0;
                cfg.vif.pwrite  <= req.write;
                cfg.vif.paddr   <= addr_t'(req.addr);
                cfg.vif.pwdata  <= data_t'(req.write ? req.data : 32'h0);
                cfg.clk_vif.drive_edge();
                cfg.vif.penable <= 1'b1;
                do cfg.clk_vif.sample_edge(); while (cfg.vif.pready !== 1'b1);
                if (!req.write) begin
                    req.data = 32'(cfg.vif.prdata);
                end
                req.slverr = cfg.vif.pslverr;
                cfg.clk_vif.drive_edge();
                cfg.vif.psel    <= 1'b0;
                cfg.vif.penable <= 1'b0;
                cfg.vif.pwrite  <= 1'b0;
                seq_item_port.item_done();
            end
        endtask
    endclass : apb_master_driver

    // Serves each transfer from cfg.mem. The address, direction and write
    // data are taken in the setup phase; the monitor reports a master that
    // changes them later.
    class apb_slave_driver #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_driver #(apb_item);
        localparam int unsigned BYTES = $bits(data_t) / 8;

        apb_config#(addr_t, data_t) cfg;

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

        // pready is high for the one clock that ends the transfer, and the
        // sample point after it can see the next setup phase, so
        // back-to-back transfers are served.
        virtual task run_phase(uvm_phase phase);
            bit [31:0]                addr;
            bit                       write;
            logic [$bits(data_t)-1:0] wdata;
            logic [$bits(data_t)-1:0] rdata;
            bit                       error;
            int unsigned              wait_clocks;
            cfg.vif.pready  <= 1'b0;
            cfg.vif.prdata  <= '0;
            cfg.vif.pslverr <= 1'b0;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (!(cfg.vif.psel === 1'b1 && cfg.vif.penable !== 1'b1)) continue;
                addr        = 32'(cfg.vif.paddr);
                write       = cfg.vif.pwrite;
                wdata       = cfg.vif.pwdata;
                error       = in_error_range(addr);
                wait_clocks = $urandom_range(cfg.max_wait, 0);
                rdata       = '0;
                repeat (wait_clocks) cfg.clk_vif.drive_edge();
                cfg.clk_vif.drive_edge();
                if (!error) begin
                    for (int unsigned b = 0; b < BYTES; b++) begin
                        if (write) cfg.mem.write(addr + b, wdata[8 * b +: 8]);
                        else rdata[8 * b +: 8] = cfg.mem.read(addr + b);
                    end
                end
                cfg.vif.pready  <= 1'b1;
                cfg.vif.prdata  <= data_t'(rdata);
                cfg.vif.pslverr <= error;
                cfg.clk_vif.drive_edge();
                cfg.vif.pready  <= 1'b0;
                cfg.vif.pslverr <= 1'b0;
            end
        endtask
    endclass : apb_slave_driver

    class apb_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_monitor;
        apb_config#(addr_t, data_t)  cfg;
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
        // write's pwdata gives one A2C_HOLD.
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
                setup  = (cfg.vif.psel === 1'b1 && cfg.vif.penable !== 1'b1);
                access = (cfg.vif.psel === 1'b1 && cfg.vif.penable === 1'b1);
                if (access && !in_transfer) begin
                    `uvm_error("A2C_PROTO", $sformatf("%s: psel and penable are high with no setup phase on the clock before",
                                                      cfg.port_name))
                end
                if (access && in_transfer) begin
                    string changed[$];
                    if (cfg.vif.paddr !== held_addr) changed.push_back("paddr");
                    if (cfg.vif.pwrite !== held_write) changed.push_back("pwrite");
                    else if (held_write === 1'b1 && cfg.vif.pwdata !== held_wdata) changed.push_back("pwdata");
                    if (changed.size() != 0) begin
                        string what = changed[0];
                        for (int i = 1; i < changed.size(); i++) what = {what, ", ", changed[i]};
                        `uvm_error("A2C_HOLD", $sformatf("%s: %s changed before pready ended the transfer at paddr %h",
                                                         cfg.port_name, what, held_addr))
                    end
                end
                held_addr   = cfg.vif.paddr;
                held_write  = cfg.vif.pwrite;
                held_wdata  = cfg.vif.pwdata;
                in_transfer = setup || (access && cfg.vif.pready !== 1'b1);
                if (!(access && cfg.vif.pready === 1'b1)) continue;
                item = apb_item::type_id::create("item");
                item.write  = cfg.vif.pwrite;
                item.addr   = 32'(cfg.vif.paddr);
                item.data   = item.write ? 32'(cfg.vif.pwdata) : 32'(cfg.vif.prdata);
                item.slverr = cfg.vif.pslverr;
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
            if (sqr != null) begin
                drv.seq_item_port.connect(sqr.seq_item_export);
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
