// GENERATED_CODE_PARAM --block=lastBlock
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "lastBlockSocket.h"

SC_HAS_PROCESS(lastBlockSocket);

lastBlockSocket::registerBlock lastBlockSocket::registerBlock_; //register the block with the factory

void lastBlockSocket::betaSocket(void) {
    port_socket(beta, "lastBlock.beta");
}

void lastBlockSocket::responseSocket(void) {
    port_socket(response, "lastBlock.response");
}

lastBlockSocket::lastBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("lastBlock", name(), bbMode)
        ,lastBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(betaSocket);
    SC_THREAD(responseSocket);

// GENERATED_CODE_END
}
