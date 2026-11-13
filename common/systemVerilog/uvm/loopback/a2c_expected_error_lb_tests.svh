// Loopback tests of a2c_expected_error. Included in a2c_uvm_loopback_pkg
// after a2c_txn_counter_lb_tests.svh. No agent is involved: each test raises
// its UVM_ERRORs itself, some containing "kept" and some not.

    // An a2c_expected_error expects want LB_EXPECT errors containing "kept".
    // The test raises n_kept of those and n_other LB_EXPECT errors without
    // "kept". Recording demoters, added after the helper's catcher, take what
    // the helper leaves as an error: extra LB_EXPECT errors and the helper's
    // own A2C_EXPECTED_ERROR. The test passes only when they took exactly
    // want_extra and want_mismatch reports.
    class expected_error_exact_test extends lb_base_test;
        a2c_expected_error   expect_kept;
        lb_recording_demoter extra;
        lb_recording_demoter mismatch;
        int unsigned         want = 2;
        int unsigned         n_kept = 2;
        int unsigned         n_other = 0;
        int unsigned         want_extra = 0;
        int unsigned         want_mismatch = 0;

        `uvm_component_utils(expected_error_exact_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            expect_kept       = a2c_expected_error::type_id::create("expect_kept", this);
            expect_kept.id    = "LB_EXPECT";
            expect_kept.text  = "kept";
            expect_kept.count = want;
        endfunction

        // After the helper's build_phase, so these catchers run after its own.
        virtual function void connect_phase(uvm_phase phase);
            extra = lb_recording_demoter::type_id::create("extra");
            extra.demote_id = "LB_EXPECT";
            uvm_report_cb::add(null, extra);
            mismatch = lb_recording_demoter::type_id::create("mismatch");
            mismatch.demote_id = "A2C_EXPECTED_ERROR";
            uvm_report_cb::add(null, mismatch);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            for (int i = 0; i < n_kept + n_other; i++) begin
                clk_vif.sample_edge();
                `uvm_error("LB_EXPECT", $sformatf("%s error %0d", i < n_kept ? "kept" : "other", i))
            end
            clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            int unsigned mismatches = mismatch.count($sformatf("expected %0d LB_EXPECT UVM_ERROR(s) containing \"kept\", saw %0d",
                                                               want, n_kept));
            if (extra.demoted != want_extra || extra.count("other") != n_other
                    || mismatch.demoted != want_mismatch || mismatches != want_mismatch || expect_kept.seen != n_kept) begin
                `uvm_error("LB_EXPECTED_ERROR", $sformatf({"helper saw %0d (want %0d); left %0d LB_EXPECT errors (want %0d, %0d without \"kept\"); ",
                                                           "%0d A2C_EXPECTED_ERROR (want %0d, %0d with the expected text)"},
                                                          expect_kept.seen, n_kept, extra.demoted, want_extra, n_other,
                                                          mismatch.demoted, want_mismatch, mismatches))
            end
            super.report_phase(phase);
        endfunction
    endclass : expected_error_exact_test

    // One expected error never comes.
    class expected_error_missing_test extends expected_error_exact_test;
        `uvm_component_utils(expected_error_missing_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_kept        = 1;
            want_mismatch = 1;
        endfunction
    endclass : expected_error_missing_test

    // One more than expected comes; it stays an error.
    class expected_error_extra_test extends expected_error_exact_test;
        `uvm_component_utils(expected_error_extra_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_kept        = 3;
            want_extra    = 1;
            want_mismatch = 1;
        endfunction
    endclass : expected_error_extra_test

    // An error with the ID but not the text is not counted and stays an error.
    class expected_error_text_test extends expected_error_exact_test;
        `uvm_component_utils(expected_error_text_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
            n_other    = 1;
            want_extra = 1;
        endfunction
    endclass : expected_error_text_test

    // Two helpers whose matches overlap: a_kept expects the one LB_OVERLAP
    // error containing "kept", b_any one LB_OVERLAP error with any message.
    // a_kept's name puts its catcher first, so it takes the "kept" report and
    // b_any, which sees it already at UVM_INFO, counts only the other one.
    class expected_error_overlap_test extends lb_base_test;
        a2c_expected_error   a_kept;
        a2c_expected_error   b_any;
        lb_recording_demoter left;

        `uvm_component_utils(expected_error_overlap_test)

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void build_phase(uvm_phase phase);
            super.build_phase(phase);
            a_kept       = a2c_expected_error::type_id::create("a_kept", this);
            a_kept.id    = "LB_OVERLAP";
            a_kept.text  = "kept";
            b_any        = a2c_expected_error::type_id::create("b_any", this);
            b_any.id     = "LB_OVERLAP";
        endfunction

        // After the helpers' build_phase, so it takes what both leave.
        virtual function void connect_phase(uvm_phase phase);
            left = lb_recording_demoter::type_id::create("left");
            left.demote_id = "A2C_EXPECTED_ERROR";
            uvm_report_cb::add(null, left);
        endfunction

        virtual task run_phase(uvm_phase phase);
            phase.raise_objection(this);
            clk_vif.sample_edge();
            `uvm_error("LB_OVERLAP", "kept error")
            clk_vif.sample_edge();
            `uvm_error("LB_OVERLAP", "other error")
            clk_vif.sample_edge();
            phase.drop_objection(this);
        endtask

        virtual function void report_phase(uvm_phase phase);
            if (a_kept.seen != 1 || b_any.seen != 1 || left.demoted != 0) begin
                `uvm_error("LB_EXPECTED_ERROR", $sformatf("a_kept saw %0d, b_any %0d (want 1 each); %0d A2C_EXPECTED_ERROR (want 0)",
                                                          a_kept.seen, b_any.seen, left.demoted))
            end
            super.report_phase(phase);
        endfunction
    endclass : expected_error_overlap_test
