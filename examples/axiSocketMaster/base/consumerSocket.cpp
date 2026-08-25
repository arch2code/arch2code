// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "consumerSocket.h"

SC_HAS_PROCESS(consumerSocket);

consumerSocket::registerBlock consumerSocket::registerBlock_; //register the block with the factory

void consumerSocket::axiRd0Socket(void) {
    port_socket(axiRd0, "consumer.axiRd0");
}

void consumerSocket::axiWr0Socket(void) {
    port_socket(axiWr0, "consumer.axiWr0");
}

consumerSocket::consumerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("consumer", name(), bbMode)
        ,consumerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(axiRd0Socket);
    SC_THREAD(axiWr0Socket);

// GENERATED_CODE_END
}
