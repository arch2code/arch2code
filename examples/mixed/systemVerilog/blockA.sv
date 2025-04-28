// GENERATED_CODE_PARAM --block=blockA --parentModule
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: blockA
module blockA
// Generated Import package statement(s)
import mixedBlockC_package::*;
import mixed_package::*;
(
    req_ack_if.src aStuffIf,
    rdy_vld_if.src cStuffIf,
    notify_ack_if.src startDone,
    apb_if.dst apbReg,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

    // Register Interfaces
    status_if #(.data_t(aRegSt)) roA();

// Instances
blockARegs #(.APB_ADDR_MASK('hff_ffff)) uBlockARegs (
    .apbReg (apbReg),
    .roA (roA),
    .clk (clk),
    .rst_n (rst_n)
);

endmodule // blockA
// GENERATED_CODE_END
