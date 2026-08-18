// GENERATED_CODE_PARAM --block=secondSubB
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "secondSubBSocket.h"

SC_HAS_PROCESS(secondSubBSocket);

secondSubBSocket::registerBlock secondSubBSocket::registerBlock_; //register the block with the factory

void secondSubBSocket::testSocket(void) {
    port_socket(test, "secondSubB.test");
}

void secondSubBSocket::betaSocket(void) {
    port_socket(beta, "secondSubB.beta");
}

secondSubBSocket::secondSubBSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("secondSubB", name(), bbMode)
        ,secondSubBBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(testSocket);
    SC_THREAD(betaSocket);

// GENERATED_CODE_END
}
