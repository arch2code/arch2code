//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: uvmVideo
module uvmVideo
// Generated Import package statement(s)
import uvmVideo_package::*;
(
    raw_if.dst vin,
    axi4_stream_if.src vout,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

    // held takes each pixel beat. On the next clock held goes out, with
    // tlast if that clock is no pixel, as lv or fv has fallen, and with
    // tuser.sof if it was the first pixel since fv was low. lv high while fv
    // is low is no pixel. The outputs come from flops, so vout has two
    // clocks of latency and never waits: the interface has no backpressure.
    logic pix;
    assign pix = vin.data.fv & vin.data.lv;

    `DFFR_INST(logic, first, 1'b1)
    `DFFR_INST(logic, heldVld, 1'b0)
    `DFFEN_INST(uvmVideoBeatSt, held, pix)
    `DFFEN_INST(logic, heldSof, pix)
    `DFFR_INST(logic, outVld, 1'b0)
    `DFFEN_INST(uvmVideoBeatSt, outBeat, heldVld)
    `DFFEN_INST(logic, outSof, heldVld)
    `DFFEN_INST(logic, outLast, heldVld)

    assign n_first   = !vin.data.fv | (first & !pix);
    assign n_heldVld = pix;
    assign n_held    = uvmVideoBeatSt'(vin.data.pixels);
    assign n_heldSof = first;
    assign n_outVld  = heldVld;
    assign n_outBeat = held;
    assign n_outSof  = heldSof;
    assign n_outLast = !pix;

    assign vout.tvalid = outVld;
    assign vout.tdata  = outBeat;
    assign vout.tuser  = uvmVideoUserSt'(outSof);
    assign vout.tlast  = outLast;
    assign vout.tid    = '0;
    assign vout.tdest  = '0;
    assign vout.tstrb  = '1;
    assign vout.tkeep  = '1;

endmodule: uvmVideo
