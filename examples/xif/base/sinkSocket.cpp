// GENERATED_CODE_PARAM --block=sink
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "sinkSocket.h"

template<> sinkSocket<sinkSinkV0Config>::registerBlock sinkSocket<sinkSinkV0Config>::registerBlock_("sinkV0"); //register the block with the factory

template<typename Config>
void sinkSocket<Config>::inSocket(void) {
    port_socket(this->in, "sink.in");
}

template<typename Config>
sinkSocket<Config>::sinkSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("sink", name(), bbMode)
        ,sinkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(inSocket);

// GENERATED_CODE_END
}
