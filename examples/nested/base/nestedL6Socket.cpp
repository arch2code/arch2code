// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "nestedL6Socket.h"

SC_HAS_PROCESS(nestedL6Socket);

nestedL6Socket::registerBlock nestedL6Socket::registerBlock_; //register the block with the factory

void nestedL6Socket::nested6Socket(void) {
    port_socket(nested6, "nestedL6.nested6");
}

nestedL6Socket::nestedL6Socket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL6", name(), bbMode)
        ,nestedL6Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(nested6Socket);

// GENERATED_CODE_END
}
