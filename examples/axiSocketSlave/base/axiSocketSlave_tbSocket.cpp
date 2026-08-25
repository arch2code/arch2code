// GENERATED_CODE_PARAM --block=axiSocketSlave_tb
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axiSocketSlave_tbSocket.h"

SC_HAS_PROCESS(axiSocketSlave_tbSocket);

axiSocketSlave_tbSocket::registerBlock axiSocketSlave_tbSocket::registerBlock_; //register the block with the factory

axiSocketSlave_tbSocket::axiSocketSlave_tbSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocketSlave_tb", name(), bbMode)
        ,axiSocketSlave_tbBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
