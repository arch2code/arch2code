// Loopback test of a2c_mem_model, included in a2c_uvm_loopback_pkg after the
// scoreboard and the base test. It drives no pins.

    typedef a2c_mem_model #(lb_data_t) lb_mem_t;

    // Three models, one per fill policy. On each the test writes words at
    // indexes that differ only above bit 31, rewrites one, reads them back,
    // and reads unwritten words: zero and fixed fills return their value,
    // a random fill returns more than one value over 32 reads, and no read
    // makes a word exist. Expects one A2C_MEM line per model.
    class a2c_mem_model_test extends lb_base_test;
        int unsigned checked;

        `uvm_component_utils(a2c_mem_model_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        function void expect_word(string what, lb_data_t got, lb_data_t want);
            checked++;
            if (got !== want) `uvm_error("LB_MEM", $sformatf("%s: read 0x%0h, expected 0x%0h", what, got, want))
        endfunction

        function void check_model(lb_mem_t mem);
            bit [63:0] index[4] = '{64'h0, 64'h1_0000_0000, 64'h8000_0000_0000_0010, '1};
            lb_data_t  data[4];
            lb_data_t  first;
            bit        varied;
            foreach (index[i]) begin
                data[i] = lb_data_t'($urandom());
                mem.write(index[i], data[i]);
            end
            data[2] = ~data[2];
            mem.write(index[2], data[2]);
            foreach (index[i]) begin
                expect_word($sformatf("%s index 0x%0h", mem.get_name(), index[i]), mem.read(index[i]), data[i]);
                if (!mem.exists(index[i])) `uvm_error("LB_MEM", $sformatf("%s: written index 0x%0h does not exist", mem.get_name(), index[i]))
            end
            first = mem.read(64'h20);
            for (int unsigned i = 0; i < 32; i++) begin
                lb_data_t got = mem.read(64'h20 + i);
                case (mem.fill)
                    A2C_MEM_FILL_ZERO:   expect_word({mem.get_name(), " unwritten"}, got, '0);
                    A2C_MEM_FILL_FIXED:  expect_word({mem.get_name(), " unwritten"}, got, mem.fill_value);
                    A2C_MEM_FILL_RANDOM: if (got !== first) varied = 1;
                endcase
                if (mem.exists(64'h20 + i)) `uvm_error("LB_MEM", $sformatf("%s: a read made index 0x%0h exist", mem.get_name(), 64'h20 + i))
            end
            if (mem.fill == A2C_MEM_FILL_RANDOM && !varied) begin
                `uvm_error("LB_MEM", $sformatf("%s: 33 unwritten reads all returned 0x%0h", mem.get_name(), first))
            end
        endfunction

        virtual task run_phase(uvm_phase phase);
            lb_mem_t zero_mem   = lb_mem_t::type_id::create("zero");
            lb_mem_t fixed_mem  = lb_mem_t::type_id::create("fixed");
            lb_mem_t random_mem = lb_mem_t::type_id::create("random");
            phase.raise_objection(this);
            fixed_mem.fill       = A2C_MEM_FILL_FIXED;
            fixed_mem.fill_value = lb_data_t'(24'hA5C3E1);
            random_mem.fill      = A2C_MEM_FILL_RANDOM;
            check_model(zero_mem);
            check_model(fixed_mem);
            check_model(random_mem);
            phase.drop_objection(this);
        endtask

        virtual function void check_phase(uvm_phase phase);
            int unsigned logged = uvm_report_server::get_server().get_id_count("A2C_MEM");
            `uvm_info("LB_STATS", $sformatf("%0d words checked, %0d A2C_MEM lines", checked, logged), UVM_NONE)
            if (logged != 3) `uvm_error("LB_MEM", $sformatf("expected one A2C_MEM line per model, 3 in all, got %0d", logged))
        endfunction
    endclass : a2c_mem_model_test
