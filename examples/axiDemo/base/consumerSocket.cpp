// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "consumerSocket.h"

SC_HAS_PROCESS(consumerSocket);

consumerSocket::registerBlock consumerSocket::registerBlock_; //register the block with the factory

void consumerSocket::axiRd0Socket(void) {
    port_socket(axiRd0, "consumer.axiRd0");
}

void consumerSocket::axiRd1Socket(void) {
    port_socket(axiRd1, "consumer.axiRd1");
}

void consumerSocket::axiRd2Socket(void) {
    port_socket(axiRd2, "consumer.axiRd2");
}

void consumerSocket::axiRd3Socket(void) {
    port_socket(axiRd3, "consumer.axiRd3");
}

void consumerSocket::axiWr0Socket(void) {
    port_socket(axiWr0, "consumer.axiWr0");
}

void consumerSocket::axiWr1Socket(void) {
    port_socket(axiWr1, "consumer.axiWr1");
}

void consumerSocket::axiWr2Socket(void) {
    port_socket(axiWr2, "consumer.axiWr2");
}

void consumerSocket::axiWr3Socket(void) {
    port_socket(axiWr3, "consumer.axiWr3");
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
    SC_THREAD(axiRd1Socket);
    SC_THREAD(axiRd2Socket);
    SC_THREAD(axiRd3Socket);
    SC_THREAD(axiWr0Socket);
    SC_THREAD(axiWr1Socket);
    SC_THREAD(axiWr2Socket);
    SC_THREAD(axiWr3Socket);

// GENERATED_CODE_END
}
