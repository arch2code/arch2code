// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipBridgeSocket.h"

SC_HAS_PROCESS(ipBridgeSocket);

ipBridgeSocket::registerBlock ipBridgeSocket::registerBlock_; //register the block with the factory

void ipBridgeSocket::data8InSocket(void) {
    port_socket(data8In, "ipBridge.data8In");
}

void ipBridgeSocket::data70InSocket(void) {
    port_socket(data70In, "ipBridge.data70In");
}

ipBridgeSocket::ipBridgeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipBridge", name(), bbMode)
        ,ipBridgeBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(data8InSocket);
    SC_THREAD(data70InSocket);

// GENERATED_CODE_END
}
