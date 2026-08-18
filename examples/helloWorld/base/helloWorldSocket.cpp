// GENERATED_CODE_PARAM --block=helloWorld
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "helloWorldSocket.h"

SC_HAS_PROCESS(helloWorldSocket);

helloWorldSocket::registerBlock helloWorldSocket::registerBlock_; //register the block with the factory

helloWorldSocket::helloWorldSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("helloWorld", name(), bbMode)
        ,helloWorldBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
