// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ip_topSocket.h"

SC_HAS_PROCESS(ip_topSocket);

ip_topSocket::registerBlock ip_topSocket::registerBlock_; //register the block with the factory

ip_topSocket::ip_topSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip_top", name(), bbMode)
        ,ip_topBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
