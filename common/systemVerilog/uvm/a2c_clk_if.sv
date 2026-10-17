`ifndef A2C_CLK_IF_SV
`define A2C_CLK_IF_SV

`timescale 1ns/1ps

// Clock and reset of one clock domain, handed to every UVM agent beside its
// protocol interface. The framework <type>_if interfaces carry no clock, so
// their pins cannot sit in a clocking block here; the two tasks below give the
// agents the timing a clocking block would.
//
// Every boundary pin changes within DRIVE_SKEW after a rising edge: the SystemC
// BFMs and the RTL in delta cycles at the edge, the UVM drivers at DRIVE_SKEW.
// So the pins hold still from DRIVE_SKEW to the next rising edge, and a value
// read at the falling edge is the value that next rising edge samples (the
// #1step value of a clocking block input). DRIVE_SKEW must stay below half the
// clock period.
interface a2c_clk_if (input logic clk, input logic rst_n);

    localparam realtime DRIVE_SKEW = 100ps;

    clocking cb @(posedge clk);
        default input #1step;
        input rst_n;
    endclocking

    // Called at a drive point, this waits a full clock: @(cb) does not
    // match the edge that is already past.
    task automatic drive_edge();
        @(cb);
        #(DRIVE_SKEW);
    endtask

    // The pins read after this return are the ones the next rising edge
    // transfers.
    task automatic sample_edge();
        @(negedge clk);
    endtask

    // Returns at the first rising edge that samples rst_n released.
    task automatic wait_reset_release();
        do @(cb); while (cb.rst_n !== 1'b1);
    endtask

endinterface : a2c_clk_if

`endif // A2C_CLK_IF_SV
