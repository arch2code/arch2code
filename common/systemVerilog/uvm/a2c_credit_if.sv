`ifndef A2C_CREDIT_IF_SV
`define A2C_CREDIT_IF_SV

`timescale 1ns/1ps

// The Mode B rendezvous of a port with no handshake, whose model lane cannot
// wait on its own pins (memory). The UVM responder drives credit with the
// number of transactions the DUT lane has made, and the model's BFM holds its
// transaction n until credit exceeds n, raising held while it waits. The pins
// are two-state, like the testbench top's.
interface a2c_credit_if;
    bit [31:0] credit;
    bit        held;
endinterface : a2c_credit_if

`endif // A2C_CREDIT_IF_SV
