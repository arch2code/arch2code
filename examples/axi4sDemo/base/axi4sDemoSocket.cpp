// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axi4sDemoSocket.h"

SC_HAS_PROCESS(axi4sDemoSocket);

axi4sDemoSocket::registerBlock axi4sDemoSocket::registerBlock_; //register the block with the factory

axi4sDemoSocket::axi4sDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4sDemo", name(), bbMode)
        ,axi4sDemoBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
