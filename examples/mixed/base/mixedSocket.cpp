// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "mixedSocket.h"

SC_HAS_PROCESS(mixedSocket);

mixedSocket::registerBlock mixedSocket::registerBlock_; //register the block with the factory

mixedSocket::mixedSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("mixed", name(), bbMode)
        ,mixedBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
