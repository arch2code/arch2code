// GENERATED_CODE_PARAM --block=nested
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedSocket.h"

SC_HAS_PROCESS(nestedSocket);

nestedSocket::registerBlock nestedSocket::registerBlock_; //register the block with the factory

nestedSocket::nestedSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nested", name(), bbMode)
        ,nestedBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
