// GENERATED_CODE_PARAM --block=nestedL3
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedL3Socket.h"

SC_HAS_PROCESS(nestedL3Socket);

nestedL3Socket::registerBlock nestedL3Socket::registerBlock_; //register the block with the factory

void nestedL3Socket::nested3Socket(void) {
    port_socket(nested3, "nestedL3.nested3");
}

nestedL3Socket::nestedL3Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL3", name(), bbMode)
        ,nestedL3Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(nested3Socket);

// GENERATED_CODE_END
}
