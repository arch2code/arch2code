// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "producerSocket.h"

SC_HAS_PROCESS(producerSocket);

producerSocket::registerBlock producerSocket::registerBlock_; //register the block with the factory

void producerSocket::test_rdy_vldSocket(void) {
    port_socket(test_rdy_vld, "producer.test_rdy_vld");
}

void producerSocket::test_req_ackSocket(void) {
    port_socket(test_req_ack, "producer.test_req_ack");
}

void producerSocket::test_push_ackSocket(void) {
    port_socket(test_push_ack, "producer.test_push_ack");
}

void producerSocket::test_pop_ackSocket(void) {
    port_socket(test_pop_ack, "producer.test_pop_ack");
}

producerSocket::producerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
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
