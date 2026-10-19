// memory agent loopback tests, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test.

    typedef logic [5:0] lb_mem_addr_t;
    typedef memory_agent #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem_agent_t;
    typedef mem_agent_t::item_t mem_item_t;
    typedef mem_agent_t::config_t mem_config_t;
    typedef virtual memory_if #(.addr_t(lb_mem_addr_t), .data_t(lb_data_t)) mem_vif_t;
    typedef a2c_mem_model #(lb_data_t) lb_word_mem_t;

    // Sends the accesses in items with no gaps and checks each read's
    // response against the address in expected_addr and the word in
    // expected, in order. The test fills the queues before it starts the
    // sequence. With reuse set, every access goes out through one item
    // object, copied from items before each send, as a sequence that
    // re-randomises one item does.
    class mem_seq extends memory_base_seq #(lb_mem_addr_t, lb_data_t);
        mem_item_t    items[$];
        lb_data_t     expected[$];
        lb_mem_addr_t expected_addr[$];
        bit           reuse;
        int unsigned  checked;

        `uvm_object_utils(mem_seq)

        function new(string name = "mem_seq");
            super.new(name);
        endfunction

        virtual task body();
            mem_item_t one = mem_item_t::type_id::create("one");
            foreach (items[i]) begin
                if (reuse) begin
                    one.copy(items[i]);
                    send(one);
                end else begin
                    send(items[i]);
                end
            end
            wait_for_reads();
        endtask

        virtual function void read_done(mem_item_t rsp);
            lb_data_t     want = expected.pop_front();
            lb_mem_addr_t want_addr = expected_addr.pop_front();
            checked++;
            if (rsp.addr !== want_addr) begin
                `uvm_error("LB_MEM", $sformatf("read %0d answered for address 0x%0h, sent to 0x%0h", checked, rsp.addr,
                                               want_addr))
            end
            if (rsp.data !== want) begin
                `uvm_error("LB_MEM", $sformatf("read %0d at 0x%0h returned 0x%0h, expected 0x%0h", checked, rsp.addr,
                                               rsp.data, want))
            end
        endfunction
    endclass : mem_seq

    // A src agent and a dst agent on interface vif_name. The dst agent's
    // monitor feeds a scoreboard; the test sets the dst model before build.
    virtual class mem_pair_test extends lb_base_test;
        mem_agent_t              src;
        mem_agent_t              dst;
        lb_scoreboard#(mem_item_t) sb;
        lb_word_mem_t            mem;

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        // Builds one src and one dst agent on the interface the tb module set
        // under vif_name, the dst agent serving model.
        function void build_pair(string vif_name, string src_name, string dst_name, lb_word_mem_t model,
                                 output mem_agent_t src_agent, output mem_agent_t dst_agent);
            mem_config_t src_cfg;
            mem_config_t dst_cfg;
            mem_vif_t    vif;
            if (!uvm_config_db#(mem_vif_t)::get(this, "", vif_name, vif)) begin
                `uvm_fatal("LB_CFG", $sformatf("no virtual memory_if '%s'", vif_name))
            end
            src_cfg = mem_config_t::type_id::create({src_name, "_cfg"});
            src_cfg.vif       = vif;
            src_cfg.clk_vif   = clk_vif;
            src_cfg.role      = A2C_SRC;
            src_cfg.port_name = vif_name;
            dst_cfg = mem_config_t::type_id::create({dst_name, "_cfg"});
            dst_cfg.vif       = vif;
            dst_cfg.clk_vif   = clk_vif;
            dst_cfg.role      = A2C_DST;
            dst_cfg.port_name = vif_name;
            dst_cfg.mem       = model;
            uvm_config_db#(mem_config_t)::set(this, src_name, "cfg", src_cfg);
            uvm_config_db#(mem_config_t)::set(this, dst_name, "cfg", dst_cfg);
            src_agent = mem_agent_t::type_id::create(src_name, this);
            dst_agent = mem_agent_t::type_id::create(dst_name, this);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            mem = lb_word_mem_t::type_id::create("mem");
            build_pair("mem", "src", "dst", mem, src, dst);
            sb = lb_scoreboard#(mem_item_t)::type_id::create("sb", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            dst.mon.ap.connect(sb.imp);
        endfunction

        // Queues one access on seq and the item the dst monitor must report
        // for it; a read reports the word in shadow.
        function void add(mem_seq seq, bit write, lb_mem_addr_t addr, lb_data_t data, ref lb_data_t shadow[lb_mem_addr_t]);
            mem_item_t it = mem_item_t::type_id::create("it");
            mem_item_t ex = mem_item_t::type_id::create("ex");
            it.write = write;
            it.addr  = addr;
            it.data  = data;
            it.gap   = 0;
            if (write) begin
                shadow[addr] = data;
            end else begin
                it.data = '0;
                seq.expected.push_back(shadow.exists(addr) ? shadow[addr] : lb_data_t'(0));
                seq.expected_addr.push_back(addr);
            end
            ex.write = write;
            ex.addr  = addr;
            ex.data  = write ? data : (shadow.exists(addr) ? shadow[addr] : lb_data_t'(0));
            seq.items.push_back(it);
            sb.expected.push_back(ex);
        endfunction

        // Clocks with enable high, and the longest run of them, so a test can
        // show its accesses went out back to back.
        int unsigned access_clocks;
        int unsigned longest_run;

        protected task watch_enable(mem_vif_t vif);
            int unsigned run = 0;
            forever begin
                clk_vif.sample_edge();
                if (vif.enable === 1'b1) begin
                    access_clocks++;
                    run++;
                    if (run > longest_run) longest_run = run;
                end else begin
                    run = 0;
                end
            end
        endtask
    endclass : mem_pair_test

    // n_items random accesses over 64 words, half reads, all back to back.
    // Every read must return the last word written to its address, or zero,
    // the dst model's fill, and the dst monitor must report every access in
    // order. The accesses must take n_items consecutive clocks.
    class memory_random_test extends mem_pair_test;
        `uvm_component_utils(memory_random_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            mem_seq      seq = mem_seq::type_id::create("seq");
            lb_data_t    shadow[lb_mem_addr_t];
            int unsigned reads;
            phase.raise_objection(this);
            for (int unsigned i = 0; i < n_items; i++) begin
                add(seq, $urandom_range(1, 0), lb_mem_addr_t'($urandom()), lb_data_t'($urandom()), shadow);
            end
            reads = seq.expected.size();
            clk_vif.wait_reset_release();
            fork
                watch_enable(src.cfg.vif);
            join_none
            seq.start(src.sqr);
            wait_matched(sb, n_items, 4 * n_items);
            disable fork;
            if (seq.checked != reads) begin
                `uvm_error("LB_MEM", $sformatf("%0d reads sent, %0d checked", reads, seq.checked))
            end
            `uvm_info("LB_STATS", $sformatf("%0d accesses, %0d reads checked, longest run of accesses %0d clocks",
                                            sb.matched, seq.checked, longest_run), UVM_NONE)
            if (longest_run != n_items) begin
                `uvm_error("LB_MEM", $sformatf("%0d accesses should take as many consecutive clocks, the longest run was %0d",
                                               n_items, longest_run))
            end
            phase.drop_objection(this);
        endtask
    endclass : memory_random_test

    // Each address is written and read on the next clock, n_items / 2 times,
    // so every read follows the write it must return by one clock. All the
    // accesses go out through one reused item object, and each read's
    // response must still carry the address that read went to.
    class memory_write_read_test extends mem_pair_test;
        `uvm_component_utils(memory_write_read_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual task run_phase(uvm_phase phase);
            mem_seq   seq = mem_seq::type_id::create("seq");
            lb_data_t shadow[lb_mem_addr_t];
            phase.raise_objection(this);
            seq.reuse = 1'b1;
            for (int unsigned i = 0; i < n_items / 2; i++) begin
                lb_mem_addr_t addr = lb_mem_addr_t'($urandom());
                add(seq, 1, addr, lb_data_t'($urandom()), shadow);
                add(seq, 0, addr, '0, shadow);
            end
            clk_vif.wait_reset_release();
            fork
                watch_enable(src.cfg.vif);
            join_none
            seq.start(src.sqr);
            wait_matched(sb, 2 * (n_items / 2), 4 * n_items);
            disable fork;
            `uvm_info("LB_STATS", $sformatf("%0d accesses, %0d reads checked, longest run of accesses %0d clocks",
                                            sb.matched, seq.checked, longest_run), UVM_NONE)
            if (seq.checked != n_items / 2) begin
                `uvm_error("LB_MEM", $sformatf("%0d reads sent, %0d checked", n_items / 2, seq.checked))
            end
            if (longest_run != 2 * (n_items / 2)) begin
                `uvm_error("LB_MEM", $sformatf("the accesses should take consecutive clocks, the longest run was %0d",
                                               longest_run))
            end
            phase.drop_objection(this);
        endtask
    endclass : memory_write_read_test

    // Two ports, mem and mem2, each with a src and a dst agent, and one
    // a2c_mem_model behind both dst agents, as a dual-port memory. The test
    // writes 32 words through mem, reads them back through mem2, then on one
    // clock writes a new word through mem and reads the same address through
    // mem2, which must return the old word, as memory_dp does.
    class memory_shared_model_test extends mem_pair_test;
        mem_agent_t src2;
        mem_agent_t dst2;

        `uvm_component_utils(memory_shared_model_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            build_pair("mem2", "src2", "dst2", mem, src2, dst2);
        endfunction

        // The clock count of the last write of address 6 through mem and of
        // the last read of it through mem2.
        int unsigned wr_clock;
        int unsigned rd_clock;

        protected task watch_same_clock();
            int unsigned clocks = 0;
            forever begin
                clk_vif.sample_edge();
                clocks++;
                if (src.cfg.vif.enable === 1'b1 && src.cfg.vif.wr_en === 1'b1 && src.cfg.vif.addr === 6) wr_clock = clocks;
                if (src2.cfg.vif.enable === 1'b1 && src2.cfg.vif.wr_en === 1'b0 && src2.cfg.vif.addr === 6) rd_clock = clocks;
            end
        endtask

        virtual task run_phase(uvm_phase phase);
            mem_seq    wr = mem_seq::type_id::create("wr");
            mem_seq    rd = mem_seq::type_id::create("rd");
            mem_seq    wr1 = mem_seq::type_id::create("wr1");
            mem_seq    rd1 = mem_seq::type_id::create("rd1");
            mem_item_t it;
            lb_data_t  shadow[lb_mem_addr_t];
            lb_data_t  old;
            lb_data_t  unused[lb_mem_addr_t];
            phase.raise_objection(this);
            for (int unsigned i = 0; i < 32; i++) add(wr, 1, lb_mem_addr_t'(2 * i), lb_data_t'($urandom()), shadow);
            for (int unsigned i = 0; i < 32; i++) begin
                it = mem_item_t::type_id::create("it");
                it.write = 0;
                it.addr  = lb_mem_addr_t'(2 * i);
                it.data  = '0;
                rd.items.push_back(it);
                rd.expected.push_back(shadow[it.addr]);
                rd.expected_addr.push_back(it.addr);
            end
            old = shadow[lb_mem_addr_t'(6)];
            add(wr1, 1, lb_mem_addr_t'(6), ~old, unused);
            it = mem_item_t::type_id::create("it");
            it.write = 0;
            it.addr  = lb_mem_addr_t'(6);
            it.data  = '0;
            rd1.items.push_back(it);
            rd1.expected.push_back(old);
            rd1.expected_addr.push_back(lb_mem_addr_t'(6));
            clk_vif.wait_reset_release();
            wr.start(src.sqr);
            rd.start(src2.sqr);
            fork
                watch_same_clock();
            join_none
            fork
                wr1.start(src.sqr);
                rd1.start(src2.sqr);
            join
            disable fork;
            wait_matched(sb, 33, 200);
            if (wr_clock == 0 || wr_clock != rd_clock) begin
                `uvm_error("LB_MEM", $sformatf("the last write and read of address 6 went out on clocks %0d and %0d, not the same one",
                                               wr_clock, rd_clock))
            end
            `uvm_info("LB_STATS", $sformatf("%0d reads through the second port checked, %0d same-clock read",
                                            rd.checked, rd1.checked), UVM_NONE)
            if (rd.checked != 32 || rd1.checked != 1) begin
                `uvm_error("LB_MEM", $sformatf("expected 32 and 1 reads checked, got %0d and %0d", rd.checked, rd1.checked))
            end
            if (mem.read(64'd6) !== ~old) begin
                `uvm_error("LB_MEM", $sformatf("the shared model holds 0x%0h at 6 after the write of 0x%0h", mem.read(64'd6), ~old))
            end
            phase.drop_objection(this);
        endtask
    endclass : memory_shared_model_test
