// GENERATED_CODE_PARAM --block=axiSocketMaster_tb
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axiSocketMaster_tbSocket.h"

SC_HAS_PROCESS(axiSocketMaster_tbSocket);

axiSocketMaster_tbSocket::registerBlock axiSocketMaster_tbSocket::registerBlock_; //register the block with the factory

axiSocketMaster_tbSocket::axiSocketMaster_tbSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiSocketMaster_tb", name(), bbMode)
        ,axiSocketMaster_tbBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
