// GENERATED_CODE_PARAM --block=axi4s_s_drv
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axi4s_s_drvSocket.h"

SC_HAS_PROCESS(axi4s_s_drvSocket);

axi4s_s_drvSocket::registerBlock axi4s_s_drvSocket::registerBlock_; //register the block with the factory

void axi4s_s_drvSocket::axis4_t2Socket(void) {
    port_socket(axis4_t2, "axi4s_s_drv.axis4_t2");
}

axi4s_s_drvSocket::axi4s_s_drvSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4s_s_drv", name(), bbMode)
        ,axi4s_s_drvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(axis4_t2Socket);

// GENERATED_CODE_END
}
