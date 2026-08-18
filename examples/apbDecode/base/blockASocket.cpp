// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockASocket.h"

SC_HAS_PROCESS(blockASocket);

blockASocket::registerBlock blockASocket::registerBlock_; //register the block with the factory

blockASocket::blockASocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
