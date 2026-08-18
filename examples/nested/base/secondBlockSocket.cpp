// GENERATED_CODE_PARAM --block=secondBlock
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "secondBlockSocket.h"

SC_HAS_PROCESS(secondBlockSocket);

secondBlockSocket::registerBlock secondBlockSocket::registerBlock_; //register the block with the factory

void secondBlockSocket::primarySocket(void) {
    port_socket(primary, "secondBlock.primary");
}

void secondBlockSocket::betaSocket(void) {
    port_socket(beta, "secondBlock.beta");
}

secondBlockSocket::secondBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("secondBlock", name(), bbMode)
        ,secondBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(primarySocket);
    SC_THREAD(betaSocket);

// GENERATED_CODE_END
}
