// GENERATED_CODE_PARAM --block=axiDemo
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axiDemoSocket.h"

SC_HAS_PROCESS(axiDemoSocket);

axiDemoSocket::registerBlock axiDemoSocket::registerBlock_; //register the block with the factory

axiDemoSocket::axiDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axiDemo", name(), bbMode)
        ,axiDemoBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );

// GENERATED_CODE_END
}
