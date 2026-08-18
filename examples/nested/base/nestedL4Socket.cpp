// GENERATED_CODE_PARAM --block=nestedL4
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedL4Socket.h"

SC_HAS_PROCESS(nestedL4Socket);

nestedL4Socket::registerBlock nestedL4Socket::registerBlock_; //register the block with the factory

void nestedL4Socket::nested4Socket(void) {
    port_socket(nested4, "nestedL4.nested4");
}

nestedL4Socket::nestedL4Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL4", name(), bbMode)
        ,nestedL4Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(nested4Socket);

// GENERATED_CODE_END
}
