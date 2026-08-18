// GENERATED_CODE_PARAM --block=nestedL5
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedL5Socket.h"

SC_HAS_PROCESS(nestedL5Socket);

nestedL5Socket::registerBlock nestedL5Socket::registerBlock_; //register the block with the factory

void nestedL5Socket::nested5Socket(void) {
    port_socket(nested5, "nestedL5.nested5");
}

nestedL5Socket::nestedL5Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL5", name(), bbMode)
        ,nestedL5Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(nested5Socket);

// GENERATED_CODE_END
}
