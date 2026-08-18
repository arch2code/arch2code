// GENERATED_CODE_PARAM --block=simple
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "simpleSocket.h"

SC_HAS_PROCESS(simpleSocket);

simpleSocket::registerBlock simpleSocket::registerBlock_; //register the block with the factory

simpleSocket::simpleSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("simple", name(), bbMode)
        ,simpleBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
