//

// GENERATED_CODE_PARAM --block=bvhFifo
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: bvhFifo
module bvhFifo
// Generated Import package statement(s)
import bvh_package::*;
(
    rdy_vld_if.dst in,
    rdy_vld_if.src out,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // A push at an edge is visible on out the next cycle, so a beat leaves one
    // clock after it enters. in.rdy depends only on the fill level, never on
    // out.rdy, so a full FIFO stops the source until the sink pops.
    localparam int unsigned PTR_W = $clog2(BVH_FIFO_DEPTH);
    typedef bvhBeat [BVH_FIFO_DEPTH-1:0] entriesT;

    `DFFR_INST(entriesT, entries, '0)
    `DFFR_INST(logic [PTR_W-1:0], wrPtr, '0)
    `DFFR_INST(logic [PTR_W-1:0], rdPtr, '0)
    `DFFR_INST(logic [PTR_W:0], count, '0)

    logic push, pop;

    assign in.rdy  = (count != (PTR_W+1)'(BVH_FIFO_DEPTH));
    assign out.vld = (count != '0);
    assign out.data = entries[rdPtr];
    assign push = in.vld && in.rdy;
    assign pop  = out.vld && out.rdy;

    always_comb begin
        n_entries = entries;
        n_wrPtr   = wrPtr;
        n_rdPtr   = rdPtr;
        n_count   = count;
        if (push) begin
            n_entries[wrPtr] = in.data;
            n_wrPtr = wrPtr + PTR_W'(1);
        end
        if (pop) begin
            n_rdPtr = rdPtr + PTR_W'(1);
        end
        n_count = count + (PTR_W+1)'(push) - (PTR_W+1)'(pop);
    end

endmodule: bvhFifo
