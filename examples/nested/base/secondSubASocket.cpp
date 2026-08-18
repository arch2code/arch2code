// GENERATED_CODE_PARAM --block=secondSubA
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "secondSubASocket.h"

SC_HAS_PROCESS(secondSubASocket);

secondSubASocket::registerBlock secondSubASocket::registerBlock_; //register the block with the factory

void secondSubASocket::testSocket(void) {
    port_socket(test, "secondSubA.test");
}

void secondSubASocket::primarySocket(void) {
    port_socket(primary, "secondSubA.primary");
}

secondSubASocket::secondSubASocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("secondSubA", name(), bbMode)
        ,secondSubABase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(testSocket);
    SC_THREAD(primarySocket);

// GENERATED_CODE_END
}
