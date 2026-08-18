// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "someRapperSocket.h"

SC_HAS_PROCESS(someRapperSocket);

someRapperSocket::registerBlock someRapperSocket::registerBlock_; //register the block with the factory

someRapperSocket::someRapperSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("someRapper", name(), bbMode)
        ,someRapperBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
