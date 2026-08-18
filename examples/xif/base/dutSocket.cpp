// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "dutSocket.h"

template<> dutSocket<dutDutV0Config>::registerBlock dutSocket<dutDutV0Config>::registerBlock_("dutV0"); //register the block with the factory

template<typename Config>
void dutSocket<Config>::streamInSocket(void) {
    port_socket(this->streamIn, "dut.streamIn");
}

template<typename Config>
void dutSocket<Config>::streamOutSocket(void) {
    port_socket(this->streamOut, "dut.streamOut");
}

template<typename Config>
dutSocket<Config>::dutSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dut", name(), bbMode)
        ,dutBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(streamInSocket);
    SC_THREAD(streamOutSocket);

// GENERATED_CODE_END
}
