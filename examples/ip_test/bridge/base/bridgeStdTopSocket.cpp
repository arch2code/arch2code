// GENERATED_CODE_PARAM --block=bridgeStdTop
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "bridgeStdTopSocket.h"

SC_HAS_PROCESS(bridgeStdTopSocket);

bridgeStdTopSocket::registerBlock bridgeStdTopSocket::registerBlock_; //register the block with the factory

bridgeStdTopSocket::bridgeStdTopSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bridgeStdTop", name(), bbMode)
        ,bridgeStdTopBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
