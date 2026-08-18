// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "consumerSocket.h"

SC_HAS_PROCESS(consumerSocket);

consumerSocket::registerBlock consumerSocket::registerBlock_; //register the block with the factory

void consumerSocket::test_rdy_vldSocket(void) {
    port_socket(test_rdy_vld, "consumer.test_rdy_vld");
}

void consumerSocket::test_req_ackSocket(void) {
    port_socket(test_req_ack, "consumer.test_req_ack");
}

void consumerSocket::test_push_ackSocket(void) {
    port_socket(test_push_ack, "consumer.test_push_ack");
}

void consumerSocket::test_pop_ackSocket(void) {
    port_socket(test_pop_ack, "consumer.test_pop_ack");
}

consumerSocket::consumerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(test_rdy_vldSocket);
    SC_THREAD(test_req_ackSocket);
    SC_THREAD(test_push_ackSocket);
    SC_THREAD(test_pop_ackSocket);

// GENERATED_CODE_END
}
