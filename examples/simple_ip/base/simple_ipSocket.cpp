// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "simple_ipSocket.h"

SC_HAS_PROCESS(simple_ipSocket);

simple_ipSocket::registerBlock simple_ipSocket::registerBlock_; //register the block with the factory

simple_ipSocket::simple_ipSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("simple_ip", name(), bbMode)
        ,simple_ipBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
