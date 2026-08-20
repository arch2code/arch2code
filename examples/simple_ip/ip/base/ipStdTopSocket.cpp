// GENERATED_CODE_PARAM --block=ipStdTop
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipStdTopSocket.h"

SC_HAS_PROCESS(ipStdTopSocket);

ipStdTopSocket::registerBlock ipStdTopSocket::registerBlock_; //register the block with the factory

ipStdTopSocket::ipStdTopSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdTop", name(), bbMode)
        ,ipStdTopBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
