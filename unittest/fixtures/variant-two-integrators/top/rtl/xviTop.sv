//

// GENERATED_CODE_PARAM --block=xviTop
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: xviTop
module xviTop
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
xviTop_xviTopDrv #(.XVI_WIDTH(8)) uTopDrv (
    .out (out_0),
    .clk (clk),
    .rst_n (rst_n)
);

xviLeaf #(.XVI_WIDTH(8), .XVI_GAIN(3)) uTopLeaf (
    .in (out_0),
    .out (out_1),
    .clk (clk),
    .rst_n (rst_n)
);

xviTop_xviTopSnk #(.XVI_WIDTH(8)) uTopSnk (
    .in (out_1),
    .clk (clk),
    .rst_n (rst_n)
);

xviTop_xviTopDrv #(.XVI_WIDTH(8)) uTopOwnDrv (
    .out (out_2),
    .clk (clk),
    .rst_n (rst_n)
);

xviLeaf #(.XVI_WIDTH(8), .XVI_GAIN(9)) uTopOwnLeaf (
    .in (out_2),
    .out (out_3),
    .clk (clk),
    .rst_n (rst_n)
);

xviTop_xviTopSnk #(.XVI_WIDTH(8)) uTopOwnSnk (
    .in (out_3),
    .clk (clk),
    .rst_n (rst_n)
);

// GENERATED_CODE_END

endmodule: xviTop
