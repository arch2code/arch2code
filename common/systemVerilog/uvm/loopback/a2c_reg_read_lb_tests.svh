// Loopback tests of register reads in Mode B: a2c_midstream_guard's rule
// for volatile reads, and a2c_reg_comparator's skip list through the apb
// agent's apb_comparator. The reg_read_* tests write synthetic apb items
// into a comparator by hand; the reg_read_pins_* tests read through a
// register model and the apb agent on the apb pin sets, in Mode B and in
// Mode A, and reg_read_pins_stride_test moves a2c_reg_map memory rows over
// them; reg_read_stride_cfg_test checks a2c_reg_map's fatals. Included in a2c_uvm_loopback_pkg after
// a2c_joint_stall_lb_tests.svh, and uses the rdy_vld, apb and Mode B
// classes of the files before it.

    // A read-only register the hardware updates: its field is volatile, as
    // the generated register model marks ro and ext registers.
    class lb_vreg extends uvm_reg;
        rand uvm_reg_field value;

        `uvm_object_utils(lb_vreg)

        function new(string name = "lb_vreg", int unsigned n_bits = 32);
            super.new(name, n_bits, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            value = uvm_reg_field::type_id::create("value");
            value.configure(this, get_n_bits(), 0, "RO", 1, '0, 1, 0, 0);
        endfunction
    endclass : lb_vreg

    class lb_rw_reg extends uvm_reg;
        rand uvm_reg_field value;

        `uvm_object_utils(lb_rw_reg)

        function new(string name = "lb_rw_reg");
            super.new(name, 32, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            value = uvm_reg_field::type_id::create("value");
            value.configure(this, 32, 0, "RW", 0, 32'h0, 1, 1, 0);
        endfunction
    endclass : lb_rw_reg

    // Two fields, only busy volatile. busy holds the low bits because
    // get_fields() lists fields by position, and only a volatile field
    // ahead of a non-volatile one tells whether every field counts.
    class lb_mixed_reg extends uvm_reg;
        rand uvm_reg_field busy;
        rand uvm_reg_field mode;

        `uvm_object_utils(lb_mixed_reg)

        function new(string name = "lb_mixed_reg");
            super.new(name, 32, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            busy = uvm_reg_field::type_id::create("busy");
            busy.configure(this, 16, 0, "RO", 1, 16'h0, 1, 0, 0);
            mode = uvm_reg_field::type_id::create("mode");
            mode.configure(this, 16, 16, "RW", 0, 16'h0, 1, 1, 0);
        endfunction
    endclass : lb_mixed_reg

    // In default_map: status, volatile, at 0x0; ctrl, not volatile, at 0x4;
    // level, volatile and two bus words wide, at 0x8; mixed at 0x10; rom, a
    // read-only memory of four two-word rows, at 0x80; tbl, a read-write
    // memory of four words, at 0xa0. alt_map holds level again, at 0x108.
    class lb_vreg_block extends uvm_reg_block;
        rand lb_vreg      status;
        rand lb_rw_reg    ctrl;
        rand lb_vreg      level;
        rand lb_mixed_reg mixed;
        uvm_mem           rom;
        uvm_mem           tbl;
        uvm_reg_map       alt_map;

        `uvm_object_utils(lb_vreg_block)

        function new(string name = "lb_vregs");
            super.new(name, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            status = new("status");
            status.configure(this);
            status.build();
            ctrl = lb_rw_reg::type_id::create("ctrl");
            ctrl.configure(this);
            ctrl.build();
            level = new("level", 64);
            level.configure(this);
            level.build();
            mixed = lb_mixed_reg::type_id::create("mixed");
            mixed.configure(this);
            mixed.build();
            rom = new("rom", 4, 64, "RO", UVM_NO_COVERAGE);
            rom.configure(this);
            tbl = new("tbl", 4, 32, "RW", UVM_NO_COVERAGE);
            tbl.configure(this);
            default_map = create_map("default_map", 'h0, 4, UVM_LITTLE_ENDIAN, 1);
            default_map.add_reg(status, 'h0, "RO");
            default_map.add_reg(ctrl, 'h4, "RW");
            default_map.add_reg(level, 'h8, "RO");
            default_map.add_reg(mixed, 'h10, "RW");
            default_map.add_mem(rom, 'h80, "RO");
            default_map.add_mem(tbl, 'ha0, "RW");
            alt_map = create_map("alt_map", 'h100, 4, UVM_LITTLE_ENDIAN, 1);
            alt_map.add_reg(level, 'h8, "RO");
            lock_model();
        endfunction
    endclass : lb_vreg_block

    // Records the messages of one ID at every severity.
    class lb_id_recorder extends uvm_report_catcher;
        string id;
        string messages[$];

        `uvm_object_utils(lb_id_recorder)

        function new(string name = "lb_id_recorder");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_id() == id) messages.push_back(get_message());
            return THROW;
        endfunction

        function int unsigned count(string sub);
            int unsigned n = 0;
            foreach (messages[i]) n += a2c_contains(messages[i], sub);
            return n;
        endfunction
    endclass : lb_id_recorder

    // A guard over a dual-lane rv counter, an rv comparator and an
    // apb_comparator, wired as a generated env wires them in Mode B. The
    // test writes apb items into the apb_comparator's exports, and rv items
    // into the counter and the rv comparator. recorders[id] keeps the
    // messages of each ID in record_ids.
    class lb_reg_read_base extends lb_mode_b_base;
        a2c_midstream_guard            guard;
        a2c_txn_counter #(rv_item_t)   counter;
        lb_cmp_t                       data_cmp;
        apb_comparator                 cmp;
        lb_vreg_block                  regs;
        uvm_analysis_port #(apb_item)  dut_ap;
        uvm_analysis_port #(apb_item)  model_ap;
        uvm_analysis_port #(rv_item_t) rv_dut_ap;
        uvm_analysis_port #(rv_item_t) rv_model_ap;
        string                         record_ids[$] = '{"A2C_MIDSTREAM", "A2C_MODEL_CMP_MIDSTREAM", "A2C_REG_SKIP"};
        lb_id_recorder                 recorders[string];

        `uvm_component_utils(lb_reg_read_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            foreach (record_ids[i]) begin
                recorders[record_ids[i]] = lb_id_recorder::type_id::create({"rec_", record_ids[i]});
                recorders[record_ids[i]].id = record_ids[i];
                uvm_report_cb::add(null, recorders[record_ids[i]]);
            end
            guard    = a2c_midstream_guard::type_id::create("guard", this);
            counter  = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            data_cmp = lb_cmp_t::type_id::create("data_cmp", this);
            cmp      = apb_comparator::type_id::create("cmp", this);
            regs     = lb_vreg_block::type_id::create("lb_vregs");
            regs.build();
            counter.port_name = "rv";
            counter.dual      = 1;
            dut_ap      = new("dut_ap", this);
            model_ap    = new("model_ap", this);
            rv_dut_ap   = new("rv_dut_ap", this);
            rv_model_ap = new("rv_model_ap", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            guard.map = regs.default_map;
            guard.counters.push_back(counter);
            guard.comparators.push_back(data_cmp);
            guard.comparators.push_back(cmp);
            cmp.guard = guard;
            dut_ap.connect(cmp.dut_export);
            model_ap.connect(cmp.model_export);
            rv_dut_ap.connect(counter.analysis_export);
            rv_dut_ap.connect(data_cmp.dut_export);
            rv_model_ap.connect(counter.model_export);
            rv_model_ap.connect(data_cmp.model_export);
        endfunction

        function apb_item bus_item(bit write, bit [31:0] addr, bit [31:0] data, bit slverr);
            apb_item it = apb_item::type_id::create("it");
            it.write  = write;
            it.addr   = addr;
            it.data   = data;
            it.slverr = slverr;
            return it;
        endfunction

        // One transfer on each lane, the DUT lane's first unless model_first
        // is set.
        function void transfer(bit write, bit [31:0] addr, bit [31:0] dut_data, bit [31:0] model_data, bit model_first = 0,
                               bit model_slverr = 0);
            if (model_first) model_ap.write(bus_item(write, addr, model_data, model_slverr));
            dut_ap.write(bus_item(write, addr, dut_data, 0));
            if (!model_first) model_ap.write(bus_item(write, addr, model_data, model_slverr));
        endfunction

        function void read(bit [31:0] addr, bit [31:0] dut_data, bit [31:0] model_data, bit model_first = 0, bit model_slverr = 0);
            transfer(0, addr, dut_data, model_data, model_first, model_slverr);
        endfunction

        // One rv output pending on each lane.
        function void busy();
            counter.expect_count(1);
        endfunction

        // The pending rv output arrives on both lanes, the model lane's
        // different with flip set.
        function void settle(bit flip = 0);
            rv_dut_ap.write(lb_rv_item(lb_data_t'(0)));
            rv_model_ap.write(lb_rv_item(flip ? ~lb_data_t'(0) : lb_data_t'(0)));
        endfunction

        function int unsigned id_count(string id);
            return uvm_report_server::get_server().get_id_count(id);
        endfunction

        function void expect_ids(string id, int unsigned n);
            if (id_count(id) != n) `uvm_error("LB_REG_READ", $sformatf("%0d %s reports, expected %0d", id_count(id), id, n))
        endfunction

        function void expect_text(string id, string sub);
            if (recorders[id].count(sub) == 0) begin
                `uvm_error("LB_REG_READ", $sformatf("no %s message holds '%s': %p", id, sub, recorders[id].messages))
            end
        endfunction
    endclass : lb_reg_read_base

    // A read of a volatile register while the rv output is pending raises
    // A2C_MIDSTREAM naming the register and the remedy, the upper word of
    // the two-word level included. The same reads when quiescent, a read
    // of the non-volatile ctrl and one of an unmapped address raise none.
    // Every pair matches, and with no skip list the comparator reports no
    // A2C_REG_SKIP.
    class reg_read_midstream_error_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_midstream_error_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 2;
            want_text.push_back("read of volatile register lb_vregs.status at 0x0 while outputs have transactions pending: rv (DUT 1, model 1). The RTL and the model may update it at different times; read it after wait_for_outputs(), or skip its address on the register bus comparator; +a2c_predict_midstream=1 relaxes the rule for debugging");
            want_text.push_back("read of volatile register lb_vregs.level at 0xc while");
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            read('h0, 1, 1);
            read('hc, 2, 2);
            busy();
            read('h0, 3, 3);
            read('hc, 4, 4);
            read('h4, 5, 5);
            read('h40, 6, 6);
            settle();
            read('h0, 7, 7);
            read('hc, 8, 8);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MODEL_CMP", 0);
            expect_ids("A2C_REG_SKIP", 0);
            if (cmp.get_pairs() != 8) `uvm_error("LB_REG_READ", $sformatf("cmp paired %0d reads, expected 8", cmp.get_pairs()))
            super.report_phase(phase);
        endfunction
    endclass : reg_read_midstream_error_test

    // Without the plusarg a mismatched volatile read while pending is both
    // the A2C_MIDSTREAM error and an A2C_MODEL_CMP error: the guard demotes
    // nothing.
    class reg_read_midstream_compare_test extends lb_reg_read_base;
        lb_recording_demoter guard_demoter;

        `uvm_component_utils(reg_read_midstream_compare_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("uvm_test_top.cmp: pair 1: DUT write=0 addr=0x00000000 data=0x00000001");
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            guard_demoter = lb_recording_demoter::type_id::create("guard_demoter");
            guard_demoter.demote_id = "A2C_MIDSTREAM";
            uvm_report_cb::add(null, guard_demoter);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h0, 1, 2);
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (guard_demoter.demoted != 1 || guard_demoter.count("read of volatile register lb_vregs.status at 0x0") != 1) begin
                `uvm_error("LB_REG_READ", $sformatf("expected one A2C_MIDSTREAM error for the read: %p", guard_demoter.messages))
            end
            expect_ids("A2C_MODEL_CMP_MIDSTREAM", 0);
            super.report_phase(phase);
        endfunction
    endclass : reg_read_midstream_compare_test

    // Under predict_midstream, which +a2c_predict_midstream=1 sets, each of
    // two mismatched volatile reads while pending, one with its DUT item
    // first and one with its model item first, logs an A2C_MIDSTREAM info
    // and is an A2C_MODEL_CMP_MIDSTREAM warning naming the read. Neither
    // opens a window: the mismatched rv output that follows is an
    // A2C_MODEL_CMP error, and so is a mismatched volatile read once
    // quiescent.
    class reg_read_midstream_predict_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_midstream_predict_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 2;
            want_text.push_back("uvm_test_top.data_cmp: pair 1: DUT");
            want_text.push_back("uvm_test_top.cmp: pair 3: DUT write=0 addr=0x00000000 data=0x00000005");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h0, 1, 2);
            read('h0, 3, 4, 1);
            settle(1);
            read('h0, 5, 6);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 2);
            expect_ids("A2C_MODEL_CMP_MIDSTREAM", 2);
            expect_text("A2C_MIDSTREAM", "read of volatile register lb_vregs.status at 0x0 while outputs have transactions pending: rv (DUT 1, model 1); +a2c_predict_midstream=1 demotes a mismatch of this read");
            expect_text("A2C_MODEL_CMP_MIDSTREAM", "uvm_test_top.cmp: pair 1: DUT write=0 addr=0x00000000 data=0x00000001 slverr=0, model write=0 addr=0x00000000 data=0x00000002 slverr=0; a read of a volatile register or read-only memory while outputs had transactions pending");
            expect_text("A2C_MODEL_CMP_MIDSTREAM", "uvm_test_top.cmp: pair 2: DUT write=0 addr=0x00000000 data=0x00000003");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_midstream_predict_test

    // A volatile read is compared when quiescent: before any output is
    // declared, and once a declared output has arrived. Both mismatch, and
    // neither raises A2C_MIDSTREAM.
    class reg_read_quiescent_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_quiescent_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 2;
            want_text.push_back("uvm_test_top.cmp: pair 1: DUT");
            want_text.push_back("uvm_test_top.cmp: pair 2: DUT");
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            read('h0, 1, 2);
            busy();
            settle();
            read('h8, 3, 4);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 0);
            super.report_phase(phase);
        endfunction
    endclass : reg_read_quiescent_test

    // While the rv output is pending, and under predict_midstream, a
    // mismatched read of the non-volatile ctrl and one of an unmapped
    // address are A2C_MODEL_CMP errors, and the guard says nothing.
    class reg_read_nonvolatile_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_nonvolatile_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 2;
            want_text.push_back("uvm_test_top.cmp: pair 1: DUT write=0 addr=0x00000004");
            want_text.push_back("uvm_test_top.cmp: pair 2: DUT write=0 addr=0x00000040");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h4, 1, 2);
            read('h40, 3, 4);
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 0);
            expect_ids("A2C_MODEL_CMP_MIDSTREAM", 0);
            super.report_phase(phase);
        endfunction
    endclass : reg_read_nonvolatile_test

    // With 0x0 on the skip list, mismatched reads of status pass, while
    // pending and when quiescent, and the guard ignores them. A read whose
    // model lane has pslverr and a write to 0x0 with different data are
    // still compared, and so are a DUT read of 0x0 that the model lane
    // makes as a write and one it makes at 0x4: four A2C_MODEL_CMP errors.
    // check_phase reports the five skipped reads in one A2C_REG_SKIP info.
    class reg_read_skip_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_skip_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 4;
            want_text.push_back("uvm_test_top.cmp: pair 2: DUT write=0 addr=0x00000000 data=0x00000003 slverr=0, model write=0 addr=0x00000000 data=0x00000003 slverr=1");
            want_text.push_back("uvm_test_top.cmp: pair 4: DUT write=1");
            want_text.push_back("uvm_test_top.cmp: pair 5: DUT write=0 addr=0x00000000 data=0x00000009 slverr=0, model write=1 addr=0x00000000 data=0x00000009");
            want_text.push_back("uvm_test_top.cmp: pair 6: DUT write=0 addr=0x00000000 data=0x0000000a slverr=0, model write=0 addr=0x00000004");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.skip_address('h0);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h0, 1, 2);
            read('h0, 3, 3, 0, 1);
            settle();
            read('h0, 5, 6, 1);
            transfer(1, 'h0, 7, 8);
            dut_ap.write(bus_item(0, 'h0, 9, 0));
            model_ap.write(bus_item(1, 'h0, 9, 0));
            dut_ap.write(bus_item(0, 'h0, 'ha, 0));
            model_ap.write(bus_item(0, 'h4, 'ha, 0));
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 0);
            expect_ids("A2C_REG_SKIP", 1);
            expect_text("A2C_REG_SKIP", "uvm_test_top.cmp: reads compared without their data, per skip list entry:\n  0x0: 5");
            if (!cmp.is_skipped('h0) || cmp.is_skipped('h4)) `uvm_error("LB_REG_READ", "is_skipped() disagrees with the skip list")
            super.report_phase(phase);
        endfunction
    endclass : reg_read_skip_test

    // skip_reg(level) lists both of its bus words as one entry. Mismatched
    // reads of each while pending pass, and the guard ignores them; a read
    // of status, which is not listed, raises A2C_MIDSTREAM. The
    // A2C_REG_SKIP info has one line per entry, 0x40 never read.
    class reg_read_skip_reg_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_skip_reg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 1;
            want_text.push_back("read of volatile register lb_vregs.status at 0x0 while");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.skip_reg(regs.level);
            cmp.skip_address('h40);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h8, 1, 2);
            read('hc, 3, 4);
            read('h0, 5, 5);
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MODEL_CMP", 0);
            expect_text("A2C_REG_SKIP", "per skip list entry:\n  lb_vregs.level 0x8..0xc: 2\n  0x40: 0");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_skip_reg_test

    // skip_reg(level, alt_map) lists level's words in alt_map, 0x108 and
    // 0x10c. Mismatched reads there pass. A read of level at 0x8 in
    // default_map is not listed and raises A2C_MIDSTREAM.
    class reg_read_skip_reg_map_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_skip_reg_map_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 1;
            want_text.push_back("read of volatile register lb_vregs.level at 0x8 while");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.skip_reg(regs.level, regs.alt_map);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h108, 1, 2);
            read('h10c, 3, 4);
            read('h8, 5, 5);
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MODEL_CMP", 0);
            expect_text("A2C_REG_SKIP", "per skip list entry:\n  lb_vregs.level 0x108..0x10c: 2");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_skip_reg_map_test

    // mixed has a volatile first field and a plain second one, so it is
    // volatile: a read of it while pending raises A2C_MIDSTREAM.
    class reg_read_field_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_field_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 1;
            want_text.push_back("read of volatile register lb_vregs.mixed at 0x10 while");
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h10, 1, 1);
            settle();
            phase.drop_objection(this);
        endtask
    endclass : reg_read_field_test

    // A read of the read-only memory rom while pending raises A2C_MIDSTREAM,
    // in its first word and its last; a read of the read-write tbl does not,
    // and neither does a read of rom once quiescent. Every pair matches.
    class reg_read_mem_error_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_mem_error_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 2;
            want_text.push_back("read of read-only memory lb_vregs.rom at 0x80 while outputs have transactions pending: rv (DUT 1, model 1). The RTL and the model may update it at different times; read it after wait_for_outputs()");
            want_text.push_back("read of read-only memory lb_vregs.rom at 0x9c while");
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h80, 1, 1);
            read('h9c, 2, 2);
            read('ha4, 3, 3);
            settle();
            read('h84, 4, 4);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MODEL_CMP", 0);
            super.report_phase(phase);
        endfunction
    endclass : reg_read_mem_error_test

    // Under predict_midstream a mismatched read of rom while pending logs an
    // A2C_MIDSTREAM info and is an A2C_MODEL_CMP_MIDSTREAM warning; a
    // mismatched read of tbl while pending is an A2C_MODEL_CMP error.
    class reg_read_mem_predict_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_mem_predict_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("uvm_test_top.cmp: pair 2: DUT write=0 addr=0x000000a0");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h88, 1, 2);
            read('ha0, 3, 4);
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 1);
            expect_ids("A2C_MODEL_CMP_MIDSTREAM", 1);
            expect_text("A2C_MIDSTREAM", "read of read-only memory lb_vregs.rom at 0x88 while outputs have transactions pending: rv (DUT 1, model 1); +a2c_predict_midstream=1 demotes a mismatch of this read");
            expect_text("A2C_MODEL_CMP_MIDSTREAM", "uvm_test_top.cmp: pair 1: DUT write=0 addr=0x00000088");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_mem_predict_test

    // skip_mem(rom) lists all of rom as one entry, and skip_reg(status) the
    // one word of status. Mismatched reads of rom's first and last words
    // and of status while pending pass, and the guard ignores them; a
    // mismatched read of tbl is an A2C_MODEL_CMP error. The A2C_REG_SKIP
    // info has one line per entry.
    class reg_read_skip_mem_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_skip_mem_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("uvm_test_top.cmp: pair 4: DUT write=0 addr=0x000000a0");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            cmp.skip_mem(regs.rom);
            cmp.skip_reg(regs.status);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            read('h80, 1, 2);
            read('h9c, 3, 4);
            read('h0, 5, 6);
            read('ha0, 7, 8);
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 0);
            expect_text("A2C_REG_SKIP", "uvm_test_top.cmp: reads compared without their data, per skip list entry:\n  lb_vregs.rom 0x80..0x9c: 2\n  lb_vregs.status 0x0: 1");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_skip_mem_test

    // Under predict_midstream two volatile reads while pending match, and
    // inject_mismatch() forces pair 2, a demoted read: an
    // A2C_MODEL_CMP_MIDSTREAM warning. Forced pair 3, read once quiescent,
    // is an A2C_MODEL_CMP error, so the demotions stay on their own pairs.
    class reg_read_inject_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_inject_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("uvm_test_top.cmp: pair 3 (injected mismatch)");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            cmp.inject_mismatch(2);
            read('h0, 1, 1);
            read('h0, 2, 2);
            settle();
            cmp.inject_mismatch(3);
            read('h0, 3, 3);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MODEL_CMP_MIDSTREAM", 1);
            expect_text("A2C_MODEL_CMP_MIDSTREAM", "uvm_test_top.cmp: pair 2 (injected mismatch)");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_inject_test

    // Under predict_midstream, with the comparison cut after pair 1, two
    // mismatched volatile reads while pending: pair 1 is compared and the
    // second read is held. uncut() releases it, and it is still demoted.
    // A mismatched read once quiescent is pair 3 and an A2C_MODEL_CMP
    // error.
    class reg_read_cut_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_cut_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            want_errors = 1;
            want_text.push_back("uvm_test_top.cmp: pair 3: DUT write=0 addr=0x00000000 data=0x00000005");
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            guard.predict_midstream = 1;
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            cmp.cut(1);
            read('h0, 1, 9);
            read('h0, 2, 8);
            if (cmp.get_pairs() != 1) `uvm_error("LB_REG_READ", $sformatf("%0d pairs compared under the cut, expected 1", cmp.get_pairs()))
            cmp.uncut();
            settle();
            read('h0, 5, 6);
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MODEL_CMP_MIDSTREAM", 2);
            expect_text("A2C_MODEL_CMP_MIDSTREAM", "uvm_test_top.cmp: pair 2: DUT write=0 addr=0x00000000 data=0x00000002");
            super.report_phase(phase);
        endfunction
    endclass : reg_read_cut_test

    // A volatile read on the DUT lane while pending, in the time step the
    // model lane dies, still raises A2C_MIDSTREAM; the same read a time step
    // later, once the comparison has stopped, raises none.
    class reg_read_dead_lane_test extends lb_reg_read_base;
        `uvm_component_utils(reg_read_dead_lane_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 1;
            want_text.push_back("read of volatile register lb_vregs.status at 0x0 while");
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            busy();
            cmp.lane_dead(A2C_MODEL_LANE);
            dut_ap.write(bus_item(0, 'h0, 1, 0));
            #1;
            dut_ap.write(bus_item(0, 'h0, 1, 0));
            settle();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            expect_ids("A2C_MIDSTREAM", 1);
            super.report_phase(phase);
        endfunction
    endclass : reg_read_dead_lane_test

    // skip_reg() of a register that the given map does not hold is one
    // A2C_CFG fatal naming the register and the map, and lists nothing.
    class reg_read_skip_reg_unmapped_test extends lb_reg_read_base;
        lb_cfg_fatal_catcher catcher;

        `uvm_component_utils(reg_read_skip_reg_unmapped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            catcher = lb_cfg_fatal_catcher::type_id::create("catcher");
            uvm_report_cb::add(null, catcher);
            cmp.skip_reg(regs.status, regs.alt_map);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (catcher.messages.size() != 1 || catcher.messages[0] != "skip_reg(): lb_vregs.status has no address in lb_vregs.alt_map") begin
                `uvm_error("LB_REG_READ", $sformatf("expected one A2C_CFG fatal from skip_reg(): %p", catcher.messages))
            end
            if (cmp.is_skipped('h0)) `uvm_error("LB_REG_READ", "0x0 is on the skip list")
            super.report_phase(phase);
        endfunction
    endclass : reg_read_skip_reg_unmapped_test

    // skip_mem() of a memory that the given map does not hold is one
    // A2C_CFG fatal naming the memory and the map, and lists nothing.
    class reg_read_skip_mem_unmapped_test extends lb_reg_read_base;
        lb_cfg_fatal_catcher catcher;

        `uvm_component_utils(reg_read_skip_mem_unmapped_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            catcher = lb_cfg_fatal_catcher::type_id::create("catcher");
            uvm_report_cb::add(null, catcher);
            cmp.skip_mem(regs.rom, regs.alt_map);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (catcher.messages.size() != 1 || catcher.messages[0] != "skip_mem(): lb_vregs.rom has no address in lb_vregs.alt_map") begin
                `uvm_error("LB_REG_READ", $sformatf("expected one A2C_CFG fatal from skip_mem(): %p", catcher.messages))
            end
            if (cmp.is_skipped('h0)) `uvm_error("LB_REG_READ", "0x0 is on the skip list")
            super.report_phase(phase);
        endfunction
    endclass : reg_read_skip_mem_unmapped_test

    // The apb agent as master on the apb pin set and, in Mode B, on
    // apb_model too, each served by a slave peer. status reads 'h11 on the
    // DUT lane and dut_status ^ model_xor on the model lane. A register
    // model on the agent's sequencer, an rv counter with one output pending
    // throughout, and in Mode B a guard wired as a generated env wires it.
    // The test reads status through the register model.
    class lb_reg_read_pins_base extends lb_mode_b_base;
        bit                 mode_b = 1;
        bit [31:0]          dut_status = 'h11;
        bit [31:0]          model_xor = 0;
        apb_agent_t         agent;
        apb_agent_t         peer;
        apb_agent_t         model_peer;
        apb_config_t        peer_cfg;
        apb_config_t        model_peer_cfg;
        lb_vreg_block       regs;
        apb_reg_adapter     adapter;
        a2c_midstream_guard guard;
        a2c_txn_counter #(rv_item_t) counter;
        uvm_analysis_port #(rv_item_t) rv_dut_ap;
        uvm_analysis_port #(rv_item_t) rv_model_ap;
        uvm_reg_data_t      value;

        `uvm_component_utils(lb_reg_read_pins_base)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            apb_vif_t    vif;
            apb_vif_t    model_vif;
            apb_config_t agent_cfg;
            super.build_phase(phase);
            if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb", vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb'")
            agent_cfg = lb_apb_cfg("agent_cfg", vif, clk_vif, A2C_SRC, "apb");
            peer_cfg  = lb_apb_cfg("peer_cfg", vif, clk_vif, A2C_DST, "apb");
            peer_cfg.mem = apb_mem_t::type_id::create("peer_mem");
            for (int unsigned b = 0; b < 4; b++) peer_cfg.mem.write(b, dut_status[8 * b +: 8]);
            uvm_config_db#(apb_config_t)::set(this, "peer", "cfg", peer_cfg);
            peer = apb_agent_t::type_id::create("peer", this);
            if (mode_b) begin
                bit [31:0] word = dut_status ^ model_xor;
                if (!uvm_config_db#(apb_vif_t)::get(this, "", "apb_model", model_vif)) `uvm_fatal("LB_CFG", "no virtual apb_if 'apb_model'")
                agent_cfg.model_vif = model_vif;
                model_peer_cfg = lb_apb_cfg("model_peer_cfg", model_vif, clk_vif, A2C_DST, "apb_model");
                model_peer_cfg.mem = apb_mem_t::type_id::create("model_peer_mem");
                for (int unsigned b = 0; b < 4; b++) model_peer_cfg.mem.write(b, word[8 * b +: 8]);
                uvm_config_db#(apb_config_t)::set(this, "model_peer", "cfg", model_peer_cfg);
                model_peer = apb_agent_t::type_id::create("model_peer", this);
                guard = a2c_midstream_guard::type_id::create("guard", this);
            end
            uvm_config_db#(apb_config_t)::set(this, "agent", "cfg", agent_cfg);
            agent   = apb_agent_t::type_id::create("agent", this);
            regs    = lb_vreg_block::type_id::create("lb_vregs");
            regs.build();
            adapter = apb_reg_adapter::type_id::create("adapter");
            counter = a2c_txn_counter#(rv_item_t)::type_id::create("counter", this);
            counter.port_name = "rv";
            counter.dual      = mode_b;
            rv_dut_ap   = new("rv_dut_ap", this);
            rv_model_ap = new("rv_model_ap", this);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            regs.default_map.set_sequencer(agent.sqr, adapter);
            regs.default_map.set_auto_predict(1);
            rv_dut_ap.connect(counter.analysis_export);
            if (!mode_b) return;
            rv_model_ap.connect(counter.model_export);
            guard.map = regs.default_map;
            guard.counters.push_back(counter);
            agent.model_cmp.guard = guard;
        endfunction

        virtual task run_phase(uvm_phase phase);
            uvm_status_e status;
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            counter.expect_count(1);
            regs.status.read(status, value);
            if (status != UVM_IS_OK || value != dut_status) begin
                `uvm_error("LB_REG_READ", $sformatf("status read 'h%0h (%s), the DUT lane holds 'h%0h", value, status.name(), dut_status))
            end
            rv_dut_ap.write(lb_rv_item(lb_data_t'(0)));
            if (mode_b) rv_model_ap.write(lb_rv_item(lb_data_t'(0)));
            repeat (2) clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask
    endclass : lb_reg_read_pins_base

    // Mode B: the read of status while the rv output is pending reaches the
    // guard through the agent's model_cmp and raises one A2C_MIDSTREAM. The
    // lanes agree, so the pair matches.
    class reg_read_pins_test extends lb_reg_read_pins_base;
        `uvm_component_utils(reg_read_pins_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            demote_id   = "A2C_MIDSTREAM";
            want_errors = 1;
            want_text.push_back("read of volatile register lb_vregs.status at 0x0 while outputs have transactions pending: rv (DUT 1, model 1).");
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (agent.model_cmp.get_pairs() != 1) `uvm_error("LB_REG_READ", $sformatf("model_cmp paired %0d reads, expected 1", agent.model_cmp.get_pairs()))
            if (uvm_report_server::get_server().get_id_count("A2C_MODEL_CMP") != 0) `uvm_error("LB_REG_READ", "an A2C_MODEL_CMP report")
            super.report_phase(phase);
        endfunction
    endclass : reg_read_pins_test

    // Mode B with status on model_cmp's skip list through skip_reg(): the
    // lanes return different words while the rv output is pending, and the
    // run raises nothing but the A2C_REG_SKIP info.
    class reg_read_pins_skip_test extends lb_reg_read_pins_base;
        lb_id_recorder skip_infos;

        `uvm_component_utils(reg_read_pins_skip_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            model_xor = 'hff;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            skip_infos = lb_id_recorder::type_id::create("skip_infos");
            skip_infos.id = "A2C_REG_SKIP";
            uvm_report_cb::add(null, skip_infos);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            agent.model_cmp.skip_reg(regs.status);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (skip_infos.count("uvm_test_top.agent.model_cmp: reads compared without their data, per skip list entry:\n  lb_vregs.status 0x0: 1") != 1) begin
                `uvm_error("LB_REG_READ", $sformatf("expected one A2C_REG_SKIP info for 0x0: %p", skip_infos.messages))
            end
            if (uvm_report_server::get_server().get_id_count("A2C_MIDSTREAM") != 0) `uvm_error("LB_REG_READ", "an A2C_MIDSTREAM report")
            super.report_phase(phase);
        endfunction
    endclass : reg_read_pins_skip_test

    // Mode A: the agent has no model_cmp and there is no guard, so the same
    // read while the rv output is pending raises nothing.
    class reg_read_pins_mode_a_test extends lb_reg_read_pins_base;
        `uvm_component_utils(reg_read_pins_mode_a_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 0;
        endfunction

        virtual function void report_phase(uvm_phase phase);
            if (agent.model_cmp != null) `uvm_error("LB_REG_READ", "the Mode A agent has a model_cmp")
            if (uvm_report_server::get_server().get_id_count("A2C_MIDSTREAM") != 0) `uvm_error("LB_REG_READ", "an A2C_MIDSTREAM report")
            super.report_phase(phase);
        endfunction
    endclass : reg_read_pins_mode_a_test

    // In default_map, an a2c_reg_map: narrow, four 20-bit rows on an 8-byte
    // stride at 0x200, and wide, four 40-bit rows on a 16-byte stride at
    // 0x300. word_map, a word-addressed a2c_reg_map at word 0x1000, holds
    // narrow again at word 0x80.
    class lb_stride_block extends uvm_reg_block;
        uvm_mem     narrow;
        uvm_mem     wide;
        a2c_reg_map word_map;

        `uvm_object_utils(lb_stride_block)

        function new(string name = "lb_strides");
            super.new(name, UVM_NO_COVERAGE);
        endfunction

        virtual function void build();
            a2c_reg_map map = a2c_reg_map::type_id::create("default_map", , get_full_name());
            narrow = new("narrow", 4, 20, "RW", UVM_NO_COVERAGE);
            narrow.configure(this);
            wide = new("wide", 4, 40, "RW", UVM_NO_COVERAGE);
            wide.configure(this);
            map.configure(this, 'h0, 4, UVM_LITTLE_ENDIAN, 1);
            add_map(map);
            map.add_mem(narrow, 'h200, "RW");
            map.set_mem_stride(narrow, 8);
            map.add_mem(wide, 'h300, "RW");
            map.set_mem_stride(wide, 16);
            word_map = a2c_reg_map::type_id::create("word_map", , get_full_name());
            word_map.configure(this, 'h1000, 4, UVM_LITTLE_ENDIAN, 0);
            add_map(word_map);
            word_map.add_mem(narrow, 'h80, "RW");
            word_map.set_mem_stride(narrow, 8);
            lock_model();
        endfunction
    endclass : lb_stride_block

    // Mode A: full-width rows written through narrow by one burst and through
    // wide row by row land on the slave at the row stride, in the row's own
    // words only, and read back whole. Each map finds a memory at every word
    // of its rows, unused words of the last row included, and none past it.
    class reg_read_pins_stride_test extends lb_reg_read_pins_base;
        lb_stride_block strides;

        `uvm_component_utils(reg_read_pins_stride_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            mode_b = 0;
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            strides = lb_stride_block::type_id::create("lb_strides");
            strides.build();
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            super.connect_phase(phase);
            strides.default_map.set_sequencer(agent.sqr, adapter);
            strides.default_map.set_auto_predict(1);
        endfunction

        // The slave's word at addr, or 'x when it holds none of its bytes.
        function logic [31:0] slave_word(bit [31:0] addr);
            logic [31:0] w = 'x;
            for (int unsigned b = 0; b < 4; b++) if (peer_cfg.mem.exists(addr + b)) w[8 * b +: 8] = peer_cfg.mem.read(addr + b);
            return w;
        endfunction

        function void expect_word(bit [31:0] addr, logic [31:0] want);
            logic [31:0] got = slave_word(addr);
            if (got !== want) `uvm_error("LB_REG_STRIDE", $sformatf("the slave holds 'h%0h at 'h%0h, expected 'h%0h", got, addr, want))
        endfunction

        function void expect_mem(uvm_reg_map map, uvm_reg_addr_t addr, uvm_mem want);
            uvm_mem got = map.get_mem_by_offset(addr);
            if (got != want) begin
                `uvm_error("LB_REG_STRIDE", $sformatf("%s finds %s at 'h%0h, expected %s", map.get_full_name(),
                                                      got == null ? "no memory" : got.get_full_name(), addr,
                                                      want == null ? "none" : want.get_full_name()))
            end
        endfunction

        function void expect_addresses(uvm_mem mem, uvm_reg_addr_t row, uvm_reg_map map, uvm_reg_addr_t want[]);
            uvm_reg_addr_t got[];
            bit            same;
            void'(mem.get_addresses(row, map, got));
            same = got.size() == want.size();
            foreach (got[i]) same &= i < want.size() && got[i] == want[i];
            if (!same) `uvm_error("LB_REG_STRIDE", $sformatf("%s row %0d is at %p, expected %p", mem.get_full_name(), row, got, want))
        endfunction

        virtual task run_phase(uvm_phase phase);
            uvm_status_e   status;
            uvm_reg_data_t narrow_rows[] = {20'hfa5a0, 20'hfa5a1, 20'hfa5a2, 20'hfa5a3};
            uvm_reg_data_t wide_rows[4];
            phase.raise_objection(this);
            clk_vif.wait_reset_release();
            strides.narrow.burst_write(status, 0, narrow_rows);
            if (status != UVM_IS_OK) `uvm_error("LB_REG_STRIDE", $sformatf("narrow burst write status %s", status.name()))
            foreach (wide_rows[r]) begin
                wide_rows[r] = 40'hc3_5a5a_0000 + r;
                strides.wide.write(status, r, wide_rows[r]);
                if (status != UVM_IS_OK) `uvm_error("LB_REG_STRIDE", $sformatf("wide[%0d] write status %s", r, status.name()))
            end
            for (int unsigned r = 0; r < 4; r++) begin
                expect_word('h200 + 8 * r, narrow_rows[r]);
                expect_word('h204 + 8 * r, 'x);
                expect_word('h300 + 16 * r, wide_rows[r][31:0]);
                expect_word('h304 + 16 * r, wide_rows[r][39:32]);
                expect_word('h308 + 16 * r, 'x);
                expect_word('h30c + 16 * r, 'x);
            end
            for (int unsigned r = 0; r < 4; r++) begin
                uvm_reg_data_t value;
                strides.narrow.read(status, r, value);
                if (status != UVM_IS_OK || value != narrow_rows[r]) begin
                    `uvm_error("LB_REG_STRIDE", $sformatf("narrow[%0d] read 'h%0h (%s), wrote 'h%0h", r, value, status.name(), narrow_rows[r]))
                end
                strides.wide.read(status, r, value);
                if (status != UVM_IS_OK || value != wide_rows[r]) begin
                    `uvm_error("LB_REG_STRIDE", $sformatf("wide[%0d] read 'h%0h (%s), wrote 'h%0h", r, value, status.name(), wide_rows[r]))
                end
            end
            expect_mem(strides.default_map, 'h21c, strides.narrow);
            expect_mem(strides.default_map, 'h220, null);
            expect_mem(strides.default_map, 'h33c, strides.wide);
            expect_mem(strides.default_map, 'h340, null);
            expect_mem(strides.word_map, 'h1087, strides.narrow);
            expect_mem(strides.word_map, 'h1088, null);
            expect_addresses(strides.narrow, 3, null, {'h218});
            expect_addresses(strides.wide, 2, null, {'h320, 'h324});
            expect_addresses(strides.narrow, 3, strides.word_map, {'h1086});
            phase.drop_objection(this);
        endtask
    endclass : reg_read_pins_stride_test

    // A stride that is not whole bus words, one shorter than a row's words,
    // and an a2c_reg_map added as a submap are each one A2C_CFG fatal, and a
    // rejected stride leaves the memory's stride as it was.
    class reg_read_stride_cfg_test extends lb_reg_read_base;
        lb_cfg_fatal_catcher catcher;
        lb_stride_block      strides;

        `uvm_component_utils(reg_read_stride_cfg_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void connect_phase(uvm_phase phase);
            uvm_reg_block top;
            uvm_reg_block sub;
            uvm_reg_map   top_map;
            a2c_reg_map   sub_map;
            uvm_reg_addr_t addrs[];
            a2c_reg_map   map;
            super.connect_phase(phase);
            catcher = lb_cfg_fatal_catcher::type_id::create("catcher");
            uvm_report_cb::add(null, catcher);
            strides = lb_stride_block::type_id::create("lb_strides");
            strides.build();
            void'($cast(map, strides.default_map));
            map.set_mem_stride(strides.narrow, 6);
            map.set_mem_stride(strides.wide, 4);
            void'(strides.narrow.get_addresses(1, null, addrs));
            if (addrs.size() != 1 || addrs[0] != 'h208) `uvm_error("LB_REG_STRIDE", $sformatf("narrow row 1 is at %p after the rejected stride, expected '{'h208}", addrs))
            void'(strides.wide.get_addresses(1, null, addrs));
            if (addrs.size() != 2 || addrs[0] != 'h310) `uvm_error("LB_REG_STRIDE", $sformatf("wide row 1 is at %p after the rejected stride, expected '{'h310, 'h314}", addrs))
            // uvm_reg_block is virtual; these two are never built, so they hold no map of their own.
            top = lb_stride_block::type_id::create("lb_top");
            sub = lb_stride_block::type_id::create("lb_sub");
            sub.configure(top);
            top_map = top.create_map("top_map", 'h0, 4, UVM_LITTLE_ENDIAN, 1);
            sub_map = a2c_reg_map::type_id::create("sub_map", , sub.get_full_name());
            sub_map.configure(sub, 'h0, 4, UVM_LITTLE_ENDIAN, 1);
            sub.add_map(sub_map);
            top_map.add_submap(sub_map, 'h100);
        endfunction

        virtual function void report_phase(uvm_phase phase);
            string want[$] = '{"set_mem_stride(): lb_strides.narrow needs a stride of whole 4-byte bus words and at least 4 bytes, not 6",
                               "set_mem_stride(): lb_strides.wide needs a stride of whole 4-byte bus words and at least 8 bytes, not 4",
                               "lb_top.lb_sub.sub_map is an a2c_reg_map, which must be a root map, so it cannot be a submap of lb_top.top_map"};
            bit same = catcher.messages.size() == want.size();
            foreach (want[i]) same &= i < catcher.messages.size() && catcher.messages[i] == want[i];
            if (!same) `uvm_error("LB_REG_STRIDE", $sformatf("expected the A2C_CFG fatals %p, got %p", want, catcher.messages))
            super.report_phase(phase);
        endfunction
    endclass : reg_read_stride_cfg_test
