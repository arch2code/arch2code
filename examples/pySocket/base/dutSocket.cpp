// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "dutSocket.h"

SC_HAS_PROCESS(dutSocket);

dutSocket::registerBlock dutSocket::registerBlock_; //register the block with the factory

void dutSocket::test_req_ackSocket(void) {
    port_socket(test_req_ack, "dut.test_req_ack");
}

void dutSocket::test2Python_req_ackSocket(void) {
    port_socket(test2Python_req_ack, "dut.test2Python_req_ack");
}

void dutSocket::dut2Python_req_ackSocket(void) {
    port_socket(dut2Python_req_ack, "dut.dut2Python_req_ack");
}

void dutSocket::test_push_ackSocket(void) {
    port_socket(test_push_ack, "dut.test_push_ack");
}

void dutSocket::test_pop_ackSocket(void) {
    port_socket(test_pop_ack, "dut.test_pop_ack");
}

void dutSocket::dut2Python_push_ackSocket(void) {
    port_socket(dut2Python_push_ack, "dut.dut2Python_push_ack");
}

void dutSocket::dut2Python_pop_ackSocket(void) {
    port_socket(dut2Python_pop_ack, "dut.dut2Python_pop_ack");
}

void dutSocket::test_notify_ackSocket(void) {
    port_socket(test_notify_ack, "dut.test_notify_ack");
}

void dutSocket::dut2Python_notify_ackSocket(void) {
    port_socket(dut2Python_notify_ack, "dut.dut2Python_notify_ack");
}

void dutSocket::test_rdy_vldSocket(void) {
    port_socket(test_rdy_vld, "dut.test_rdy_vld");
}

void dutSocket::dut2Python_rdy_vldSocket(void) {
    port_socket(dut2Python_rdy_vld, "dut.dut2Python_rdy_vld");
}

dutSocket::dutSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dut", name(), bbMode)
        ,dutBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(test_req_ackSocket);
    SC_THREAD(test2Python_req_ackSocket);
    SC_THREAD(dut2Python_req_ackSocket);
    SC_THREAD(test_push_ackSocket);
    SC_THREAD(test_pop_ackSocket);
    SC_THREAD(dut2Python_push_ackSocket);
    SC_THREAD(dut2Python_pop_ackSocket);
    SC_THREAD(test_notify_ackSocket);
    SC_THREAD(dut2Python_notify_ackSocket);
    SC_THREAD(test_rdy_vldSocket);
    SC_THREAD(dut2Python_rdy_vldSocket);

// GENERATED_CODE_END
}
