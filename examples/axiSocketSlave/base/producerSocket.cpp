// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "producerSocket.h"

SC_HAS_PROCESS(producerSocket);

producerSocket::registerBlock producerSocket::registerBlock_; //register the block with the factory

void producerSocket::axiRd0Socket(void) {
    port_socket(axiRd0, "producer.axiRd0");
}

void producerSocket::axiWr0Socket(void) {
    port_socket(axiWr0, "producer.axiWr0");
}

producerSocket::producerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("producer", name(), bbMode)
        ,producerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(axiRd0Socket);
    SC_THREAD(axiWr0Socket);

// GENERATED_CODE_END
}
