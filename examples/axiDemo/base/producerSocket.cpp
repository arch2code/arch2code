// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "producerSocket.h"

SC_HAS_PROCESS(producerSocket);

producerSocket::registerBlock producerSocket::registerBlock_; //register the block with the factory

void producerSocket::axiRd0Socket(void) {
    port_socket(axiRd0, "producer.axiRd0");
}

void producerSocket::axiRd1Socket(void) {
    port_socket(axiRd1, "producer.axiRd1");
}

void producerSocket::axiRd2Socket(void) {
    port_socket(axiRd2, "producer.axiRd2");
}

void producerSocket::axiRd3Socket(void) {
    port_socket(axiRd3, "producer.axiRd3");
}

void producerSocket::axiWr0Socket(void) {
    port_socket(axiWr0, "producer.axiWr0");
}

void producerSocket::axiWr1Socket(void) {
    port_socket(axiWr1, "producer.axiWr1");
}

void producerSocket::axiWr2Socket(void) {
    port_socket(axiWr2, "producer.axiWr2");
}

void producerSocket::axiWr3Socket(void) {
    port_socket(axiWr3, "producer.axiWr3");
}

void producerSocket::axiStr0Socket(void) {
    port_socket(axiStr0, "producer.axiStr0");
}

void producerSocket::axiStr1Socket(void) {
    port_socket(axiStr1, "producer.axiStr1");
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
    SC_THREAD(axiRd1Socket);
    SC_THREAD(axiRd2Socket);
    SC_THREAD(axiRd3Socket);
    SC_THREAD(axiWr0Socket);
    SC_THREAD(axiWr1Socket);
    SC_THREAD(axiWr2Socket);
    SC_THREAD(axiWr3Socket);
    SC_THREAD(axiStr0Socket);
    SC_THREAD(axiStr1Socket);

// GENERATED_CODE_END
}
