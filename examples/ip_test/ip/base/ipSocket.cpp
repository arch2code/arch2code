// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipSocket.h"

template<> ipSocket<ipVariant0Config>::registerBlock ipSocket<ipVariant0Config>::registerBlock_("variant0"); //register the block with the factory

template<typename Config>
void ipSocket<Config>::ipDataIfSocket(void) {
    port_socket(this->ipDataIf, "ip.ipDataIf");
}

template<typename Config>
ipSocket<Config>::ipSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ip", name(), bbMode)
        ,ipBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(ipDataIfSocket);

// GENERATED_CODE_END
}
