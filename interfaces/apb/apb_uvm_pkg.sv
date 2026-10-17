`ifndef APB_UVM_PKG_SV
`define APB_UVM_PKG_SV

`timescale 1ns/1ps

// UVM agent for apb_if: an APB3 master driver, a monitor and the register
// adapter. The bus is 32-bit address and data; addr_t and data_t are the
// interface's packed types, which only the virtual interface handle needs.
// Pin timing follows a2c_clk_if: drive at drive_edge(), sample at sample_edge().
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

    class apb_config #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_object;
        virtual apb_if #(.addr_t(addr_t), .data_t(data_t)) vif;
        virtual a2c_clk_if                                 clk_vif;
        uvm_active_passive_enum                            is_active = UVM_ACTIVE;
        string                                             port_name = "";

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

    class apb_monitor #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_monitor;
        apb_config#(addr_t, data_t)  cfg;
        uvm_analysis_port #(apb_item) ap;

        `uvm_component_param_utils(apb_monitor#(addr_t, data_t))

        function new(string name, uvm_component parent);
            super.new(name, parent);
            ap = new("ap", this);
        endfunction

        virtual task run_phase(uvm_phase phase);
            apb_item item;
            cfg.clk_vif.wait_reset_release();
            forever begin
                cfg.clk_vif.sample_edge();
                if (!(cfg.vif.psel === 1'b1 && cfg.vif.penable === 1'b1 && cfg.vif.pready === 1'b1)) continue;
                item = apb_item::type_id::create("item");
                item.write  = cfg.vif.pwrite;
                item.addr   = 32'(cfg.vif.paddr);
                item.data   = item.write ? 32'(cfg.vif.pwdata) : 32'(cfg.vif.prdata);
                item.slverr = cfg.vif.pslverr;
                // The agent is the master, the src side of the bus.
                `uvm_info("A2C_TXN", a2c_txn({get_full_name(), ".", cfg.port_name}, A2C_SRC, item.convert2string(),
                                             $sformatf("%0h", {item.write, item.addr, item.data})), UVM_MEDIUM)
                ap.write(item);
            end
        endtask
    endclass : apb_monitor

    class apb_agent #(type addr_t = logic [31:0], type data_t = logic [31:0]) extends uvm_agent;
        typedef apb_item                    item_t;
        typedef apb_config#(addr_t, data_t) config_t;

        apb_config#(addr_t, data_t)        cfg;
        apb_master_driver#(addr_t, data_t) drv;
        uvm_sequencer #(apb_item)          sqr;
        apb_monitor#(addr_t, data_t)       mon;

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
            if (cfg.is_active == UVM_ACTIVE) begin
                drv = apb_master_driver#(addr_t, data_t)::type_id::create("drv", this);
                drv.cfg = cfg;
                sqr = uvm_sequencer#(apb_item)::type_id::create("sqr", this);
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
