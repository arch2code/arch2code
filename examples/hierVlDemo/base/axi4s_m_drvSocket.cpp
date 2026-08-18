// GENERATED_CODE_PARAM --block=axi4s_m_drv
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axi4s_m_drvSocket.h"

SC_HAS_PROCESS(axi4s_m_drvSocket);

axi4s_m_drvSocket::registerBlock axi4s_m_drvSocket::registerBlock_; //register the block with the factory

axi4s_m_drvSocket::axi4s_m_drvSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4s_m_drv", name(), bbMode)
        ,axi4s_m_drvBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
