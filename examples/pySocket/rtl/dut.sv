//

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=moduleInterfacesInstances
//module as defined by block: pySocket_dut
module pySocket_dut
// Generated Import package statement(s)
import pySocket_tb_package::*;
(
    req_ack_if.dst test_req_ack,
    req_ack_if.dst test2Python_req_ack,
    req_ack_if.src dut2Python_req_ack,
    push_ack_if.dst test_push_ack,
    pop_ack_if.dst test_pop_ack,
    push_ack_if.src dut2Python_push_ack,
    pop_ack_if.src dut2Python_pop_ack,
    notify_ack_if.dst test_notify_ack,
    notify_ack_if.src dut2Python_notify_ack,
    rdy_vld_if.dst test_rdy_vld,
    rdy_vld_if.src dut2Python_rdy_vld,
    axi4_stream_if.dst test_axi4_stream,
    axi4_stream_if.src dut2Python_axi4_stream,
    input clk, rst_n
);

    // Interface Instances, needed for between instanced modules inside this module

// Instances
// GENERATED_CODE_END

endmodule: pySocket_dut
