// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: top
module top
// Generated Import package statement(s)
import axiDemo_package::*;
(
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd0();
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd1();
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd2();
    axi_read_if #(.addr_t(axiAddrSt), .data_t(axiDataSt)) axiRd3();
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr0();
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr1();
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr2();
    axi_write_if #(.addr_t(axiAddrSt), .data_t(axiDataSt), .strb_t(axiStrobeSt)) axiWr3();

// Instances
producer uProducer (
    .axiRd0 (axiRd0),
    .axiRd1 (axiRd1),
    .axiRd2 (axiRd2),
    .axiRd3 (axiRd3),
    .axiWr0 (axiWr0),
    .axiWr1 (axiWr1),
    .axiWr2 (axiWr2),
    .axiWr3 (axiWr3),
    .clk (clk),
    .rst_n (rst_n)
);

consumer uConsumer (
    .axiRd0 (axiRd0),
    .axiRd1 (axiRd1),
    .axiRd2 (axiRd2),
    .axiRd3 (axiRd3),
    .axiWr0 (axiWr0),
    .axiWr1 (axiWr1),
    .axiWr2 (axiWr2),
    .axiWr3 (axiWr3),
    .clk (clk),
    .rst_n (rst_n)
);


// GENERATED_CODE_END
endmodule: top