// GENERATED_CODE_PARAM --block=blockB
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockBSocket.h"

SC_HAS_PROCESS(blockBSocket);

blockBSocket::registerBlock blockBSocket::registerBlock_; //register the block with the factory

blockBSocket::blockBSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockB", name(), bbMode)
        ,blockBBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
