// GENERATED_CODE_PARAM --block=nestedL2
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedL2Socket.h"

SC_HAS_PROCESS(nestedL2Socket);

nestedL2Socket::registerBlock nestedL2Socket::registerBlock_; //register the block with the factory

void nestedL2Socket::nested2Socket(void) {
    port_socket(nested2, "nestedL2.nested2");
}

nestedL2Socket::nestedL2Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL2", name(), bbMode)
        ,nestedL2Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(nested2Socket);

// GENERATED_CODE_END
}
