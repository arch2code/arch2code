// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "firstBlockSocket.h"

SC_HAS_PROCESS(firstBlockSocket);

firstBlockSocket::registerBlock firstBlockSocket::registerBlock_; //register the block with the factory

void firstBlockSocket::primarySocket(void) {
    port_socket(primary, "firstBlock.primary");
}

void firstBlockSocket::responseSocket(void) {
    port_socket(response, "firstBlock.response");
}

firstBlockSocket::firstBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("firstBlock", name(), bbMode)
        ,firstBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(primarySocket);
    SC_THREAD(responseSocket);

// GENERATED_CODE_END
}
