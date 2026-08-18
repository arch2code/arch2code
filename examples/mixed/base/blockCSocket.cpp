// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockCSocket.h"

SC_HAS_PROCESS(blockCSocket);

blockCSocket::registerBlock blockCSocket::registerBlock_; //register the block with the factory

void blockCSocket::seeSocket(void) {
    port_socket(see, "blockC.see");
}

blockCSocket::blockCSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockC", name(), bbMode)
        ,blockCBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(seeSocket);

// GENERATED_CODE_END
}
