// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "bridgeDriverSocket.h"

SC_HAS_PROCESS(bridgeDriverSocket);

bridgeDriverSocket::registerBlock bridgeDriverSocket::registerBlock_; //register the block with the factory

void bridgeDriverSocket::out8Socket(void) {
    port_socket(out8, "bridgeDriver.out8");
}

void bridgeDriverSocket::out70Socket(void) {
    port_socket(out70, "bridgeDriver.out70");
}

bridgeDriverSocket::bridgeDriverSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bridgeDriver", name(), bbMode)
        ,bridgeDriverBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(out8Socket);
    SC_THREAD(out70Socket);

// GENERATED_CODE_END
}
