// GENERATED_CODE_PARAM --block=nestedL1
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedL1Socket.h"

SC_HAS_PROCESS(nestedL1Socket);

nestedL1Socket::registerBlock nestedL1Socket::registerBlock_; //register the block with the factory

void nestedL1Socket::nested1Socket(void) {
    port_socket(nested1, "nestedL1.nested1");
}

nestedL1Socket::nestedL1Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL1", name(), bbMode)
        ,nestedL1Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(nested1Socket);

// GENERATED_CODE_END
}
