`ifndef A2C_UVM_PKG_SV
`define A2C_UVM_PKG_SV

`timescale 1ns/1ps

// What the interface agent packages and the generated environments share.
package a2c_uvm_pkg;

    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // The side of the interface an agent plays, the opposite of the DUT
    // port's modport: a DUT dst input gets an A2C_SRC agent.
    typedef enum {A2C_SRC, A2C_DST} a2c_role_e;

    // The A2C_TXN line every monitor logs per transaction: the time in ns,
    // the port, the role, the item's fields, and the packed value in hex so a
    // SystemC test can rebuild the payload with sc_unpack().
    function automatic string a2c_txn(string path, a2c_role_e role, string fields, string hex);
        return $sformatf("A2C_TXN %0.3f %s %s %s hex=%s", $realtime, path,
                         (role == A2C_SRC) ? "src" : "dst", fields, hex);
    endfunction

    // Counts the transactions one output port delivers against the number
    // the test expects, with no check of their content. Each
    // wait_for_count() holds the test until every expected transaction has
    // arrived and then for a quiet window, so an extra one from the DUT
    // arrives inside the test, and reports a shortfall or an excess.
    // check_phase() reports what no wait_for_count() has. Every report is an
    // A2C_TXN_COUNT UVM_ERROR naming the port. A transaction that arrives
    // after its shortfall was reported is logged as late, not counted again.
    class a2c_txn_counter #(type T = uvm_sequence_item) extends uvm_subscriber #(T);
        string port_name = "";

        protected int unsigned expected;
        protected int unsigned received;
        // Reported missing and not yet arrived.
        protected int unsigned missing;

        `uvm_component_param_utils(a2c_txn_counter#(T))

        function new(string name, uvm_component parent);
            super.new(name, parent);
        endfunction

        virtual function void write(T t);
            if (missing > 0) begin
                missing--;
                `uvm_info("A2C_TXN_COUNT", $sformatf("%s: late transaction, reported missing earlier; %0d still missing",
                                                 port_name, missing), UVM_LOW)
                return;
            end
            received++;
        endfunction

        function void expect_count(int unsigned n);
            expected += n;
        endfunction

        function int unsigned outstanding();
            return (received < expected) ? expected - received : 0;
        endfunction

        // After a report the expected count is set to the received count, so
        // a later wait_for_count() or check_phase does not report the same
        // transactions again.
        task wait_for_count(virtual a2c_clk_if clk_vif, int unsigned deadline_cycles, int unsigned quiet_cycles);
            int unsigned cycles = 0;
            while (received < expected && cycles < deadline_cycles) begin
                clk_vif.sample_edge();
                cycles++;
            end
            if (received < expected) begin
                `uvm_error("A2C_TXN_COUNT", $sformatf("%s: deadline of %0d clocks passed: expected %0d transactions, received %0d (%0d missing)",
                                                  port_name, deadline_cycles, expected, received, expected - received))
                missing += expected - received;
                expected = received;
                return;
            end
            repeat (quiet_cycles) clk_vif.sample_edge();
            if (received > expected) begin
                `uvm_error("A2C_TXN_COUNT", $sformatf("%s: by the end of the quiet window received %0d transactions, expected %0d (%0d extra)",
                                                  port_name, received, expected, received - expected))
                expected = received;
                return;
            end
            `uvm_info("A2C_TXN_COUNT", $sformatf("%s: received the %0d expected transactions", port_name, received), UVM_LOW)
        endtask

        virtual function void check_phase(uvm_phase phase);
            if (received < expected) begin
                `uvm_error("A2C_TXN_COUNT", $sformatf("%s: end of test with %0d of %0d expected transactions outstanding, which no wait_for_count covered",
                                                  port_name, outstanding(), expected))
            end
            if (received > expected) begin
                `uvm_error("A2C_TXN_COUNT", $sformatf("%s: end of test: received %0d transactions, expected %0d (%0d extra)",
                                                  port_name, received, expected, received - expected))
            end
        endfunction
    endclass : a2c_txn_counter

    // Turns each UVM_ERROR with id demote_id into UVM_INFO and counts it, so a
    // negative test can pass when the check it provokes fires.
    class a2c_error_demoter extends uvm_report_catcher;
        string       demote_id = "";
        int unsigned demoted;

        `uvm_object_utils(a2c_error_demoter)

        function new(string name = "a2c_error_demoter");
            super.new(name);
        endfunction

        virtual function action_e catch();
            if (get_severity() == UVM_ERROR && get_id() == demote_id) begin
                demoted++;
                set_severity(UVM_INFO);
                // The action was chosen for UVM_ERROR and still holds
                // UVM_COUNT; without this the quit count would still rise.
                set_action(UVM_DISPLAY);
                set_message({"expected, demoted to info: ", get_message()});
            end
            return THROW;
        endfunction
    endclass : a2c_error_demoter

endpackage : a2c_uvm_pkg

`endif // A2C_UVM_PKG_SV
