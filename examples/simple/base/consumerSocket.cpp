// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "consumerSocket.h"

SC_HAS_PROCESS(consumerSocket);

consumerSocket::registerBlock consumerSocket::registerBlock_; //register the block with the factory

void consumerSocket::tag0Socket(void) {
    port_socket(tag0, "consumer.tag0");
}

void consumerSocket::tag1Socket(void) {
    port_socket(tag1, "consumer.tag1");
}

consumerSocket::consumerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(tag0Socket);
    SC_THREAD(tag1Socket);

// GENERATED_CODE_END
}
