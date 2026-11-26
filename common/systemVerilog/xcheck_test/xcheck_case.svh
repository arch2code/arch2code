// Shared part of the case modules in xcheck_tb.sv, included after each one's
// clk port, its rst_n, and CHK, the checker's path below the case. At the end
// of the run each case compares the reports a2c_xz_fail counted for that
// checker with EXP and SIG.

import "DPI-C" function int xz_count(string path);
import "DPI-C" function string xz_signal(string path);

task automatic cycles(int n);
    repeat (n) @(posedge clk);
endtask

// Two clocks of reset, as the hdl wrappers' reset drivers give.
task automatic reset_pulse();
    rst_n = 1'b0;
    cycles(2);
    rst_n = 1'b1;
endtask

// Delta cycles at time 0, before the first clock edge, as the socket lockstep
// wrapper does.
task automatic delta_reset();
    rst_n = 1'b1;
    #0 rst_n = 1'b0;
    #0 rst_n = 1'b1;
endtask

// Module scope, because a block that declares variables is a scope of its own
// in %m.
string chk;
string sig;
int n;
initial chk = $sformatf("%m.%s", CHK);

final begin
    n = xz_count(chk);
    sig = xz_signal(chk);
    if (n == EXP && sig == SIG) begin
        $display("XC_PASS %s: %0d report(s) '%s'", NAME, n, sig);
    end else begin
        $display("XC_FAIL %s (%s): expected %0d report(s) '%s', got %0d '%s'", NAME, chk, EXP, SIG, n, sig);
    end
end
