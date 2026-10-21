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

    // Called at a rising edge, this waits to that edge's drive point.
    task automatic skew_after_edge();
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

    // The times of the last edges, and the period, from which a waiter tells
    // a clock that has stopped. The steady period changes only when three
    // consecutive intervals between rising edges agree within an eighth, and
    // becomes the longest of them. So the gap of a clock that stopped and ran
    // again changes nothing, nor do the two intervals a runt pulse makes,
    // even one just after a falling edge, whose two intervals are near half
    // a period each. A real change of frequency, slower or faster, is taken
    // on the third rising edge at the new rate. Until then a waiter judges
    // the new intervals by the old period, so a clock that slows in one step
    // by more than a waiter's stop limit reads as stopped to that waiter.
    //
    // A clock gated in short bursts at uneven gaps may never give three
    // agreeing intervals. Until it does, the period is the shortest interval
    // seen so far, so such a clock still has a stop limit once it has risen
    // twice. In that state a runt pulse sets the period to its own short
    // interval and so shortens the stop limit; a waiter whose limit is only
    // a period or two can then read the next ordinary gap as a stop.
    realtime last_rise;
    realtime last_fall;
    realtime period;
    // The three-agree period, 0 until one exists; period follows it from then.
    realtime steady;
    bit      risen;
    // The last two intervals, the later first.
    realtime intervals[2];

    always @(posedge clk) begin
        realtime interval;
        realtime hi;
        realtime lo;
        if (risen && $realtime > last_rise) begin
            interval = $realtime - last_rise;
            hi       = interval;
            lo       = interval;
            foreach (intervals[i]) begin
                if (intervals[i] > hi) hi = intervals[i];
                if (intervals[i] < lo) lo = intervals[i];
            end
            if (lo > 0 && (hi - lo) * 8 <= hi) steady = hi;
            if (steady > 0) period = steady;
            else if (period == 0 || interval < period) period = interval;
            intervals[1] = intervals[0];
            intervals[0] = interval;
        end
        risen     = 1'b1;
        last_rise = $realtime;
    end

    always @(negedge clk) last_fall = $realtime;

    // Waits on posedge clk, which an @(cb) also matches, but returns with
    // running clear, and no edge, once (max(periods, 1) + 0.5) periods have
    // passed since the last rising edge without another. A clock with no
    // period yet, one that has risen only once, is waited for with no limit.
    // A clock that has never risen counts as stopped: the drain reads that
    // as a domain gated off for the whole test.
    task automatic next_rise(int unsigned periods, output bit running);
        edge_or_stop(1'b1, 1'b1, periods, running);
    endtask

    // As sample_edge(), with the stop of next_rise() counted from the last
    // falling edge. A clock that has never risen is waited for with no
    // limit too, as one that has not started yet.
    task automatic next_sample(int unsigned periods, output bit running);
        edge_or_stop(1'b0, 1'b0, periods, running);
    endtask

    task automatic edge_or_stop(bit rising, bit unrisen_stops, int unsigned periods, output bit running);
        realtime last = rising ? last_rise : last_fall;
        realtime limit;
        bit      got = 1'b0;
        // Called at an edge whose always block has not run yet.
        if (rising && clk === 1'b1 && last_rise < last_fall) last = $realtime;
        if (!rising && clk === 1'b0 && last_fall < last_rise) last = $realtime;
        running = 1'b0;
        if (period == 0) begin
            if (!risen && unrisen_stops) return;
            if (rising) @(posedge clk);
            else @(negedge clk);
            running = 1'b1;
            return;
        end
        limit = last + (((periods > 0) ? periods : 1) + 0.5) * period - $realtime;
        if (limit <= 0) return;
        fork
            begin
                fork
                    begin
                        if (rising) @(posedge clk);
                        else @(negedge clk);
                        got = 1'b1;
                    end
                    #(limit);
                join_any
                disable fork;
            end
        join
        running = got;
    endtask

endinterface : a2c_clk_if

`endif // A2C_CLK_IF_SV
