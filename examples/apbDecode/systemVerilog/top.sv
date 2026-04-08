// GENERATED_CODE_PARAM --block=top
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
module top
    import apbDecode_package::*;
(
    input logic clk,
    input logic rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    apb_if #(
        .addr_t(apbAddrSt),
        .data_t(apbDataSt)
    ) apbReg (
    );


    // Instances

    cpu uCPU (
        .apbReg(apbReg),
        .clk(clk),
        .rst_n(rst_n)
    );

    someRapper uSomeRapper (
        .apbReg(apbReg),
        .clk(clk),
        .rst_n(rst_n)
    );

// GENERATED_CODE_END

endmodule : top