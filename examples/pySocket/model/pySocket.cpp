//
#include "pySocket.h"

#include <format>

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "pySocket.h"
SC_HAS_PROCESS(pySocket);

pySocket::registerBlock pySocket::registerBlock_; //register the block with the factory

pySocket::pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket", name(), bbMode)
        ,pySocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
