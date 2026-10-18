// Shared body of the <type>_xcheck modules, included after their ports.
// Checking starts once reset has been asserted and released, because the
// wrappers start with reset released, before the DUT has been reset. Each
// instance reports only its first X or Z, through a2c_xz_fail.

import "DPI-C" function void a2c_xz_fail(string path, string signal);

string xzPath;
bit xzArmed;
bit xzReported;

initial xzPath = $sformatf("%m");

// Arms on reset itself, not on a clock edge: the socket lockstep wrapper can
// assert and release reset in delta cycles at time 0, before the first edge.
// The level test covers a reset driven low before this process starts. A
// falling edge arms even when reset is back high by the time this process
// runs, but a 1 to X or Z edge does not, so a power-on X never arms.
initial begin
    if (rst_n === 1'b0) begin
        xzArmed = 1'b1;
    end
    forever begin
        @(negedge rst_n);
        if (!$isunknown(rst_n)) begin
            xzArmed = 1'b1;
        end
    end
end

function automatic bit xzCheckEnabled();
    return xzArmed && rst_n === 1'b1 && !xzReported;
endfunction

function automatic void xzFail(string signal);
    xzReported = 1'b1;
    $display("A2C_XZ %0t %s: %s is X or Z", $time, xzPath, signal);
    a2c_xz_fail(xzPath, signal);
endfunction
