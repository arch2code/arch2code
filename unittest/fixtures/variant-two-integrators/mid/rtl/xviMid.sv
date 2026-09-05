//

// GENERATED_CODE_PARAM --block=xviMid
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xviMid
module xviMid
// Generated Import package statement(s)
import xviLeaf_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    push_ack_if #(.data_t(xviSt)) out_0();
    push_ack_if #(.data_t(xviSt)) out_1();
    push_ack_if #(.data_t(xviSt)) out_2();
    push_ack_if #(.data_t(xviSt)) out_3();

// Instances
xviMid_xviDrv #(.XVI_WIDTH(8)) uMidDrv (
    .out (out_0),
    .clk (clk),
    .rst_n (rst_n)
);

xviLeaf #(.XVI_WIDTH(8), .XVI_GAIN(7)) uMidLeaf (
    .in (out_0),
    .out (out_1),
    .clk (clk),
    .rst_n (rst_n)
);

xviMid_xviSnk #(.XVI_WIDTH(8)) uMidSnk (
    .in (out_1),
    .clk (clk),
    .rst_n (rst_n)
);

xviMid_xviDrv #(.XVI_WIDTH(8)) uMidOwnDrv (
    .out (out_2),
    .clk (clk),
    .rst_n (rst_n)
);

xviLeaf #(.XVI_WIDTH(8), .XVI_GAIN(5)) uMidOwnLeaf (
    .in (out_2),
    .out (out_3),
    .clk (clk),
    .rst_n (rst_n)
);

xviMid_xviSnk #(.XVI_WIDTH(8)) uMidOwnSnk (
    .in (out_3),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: xviMid
