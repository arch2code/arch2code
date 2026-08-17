// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "pySocket_tbSocket.h"

SC_HAS_PROCESS(pySocket_tbSocket);

pySocket_tbSocket::registerBlock pySocket_tbSocket::registerBlock_; //register the block with the factory

pySocket_tbSocket::pySocket_tbSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket_tb", name(), bbMode)
        ,pySocket_tbBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
