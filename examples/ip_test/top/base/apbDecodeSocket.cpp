// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "apbDecodeSocket.h"

SC_HAS_PROCESS(apbDecodeSocket);

apbDecodeSocket::registerBlock apbDecodeSocket::registerBlock_; //register the block with the factory

void apbDecodeSocket::apbReg_uBridgeSocket(void) {
    port_socket(apbReg_uBridge, "apbDecode.apbReg_uBridge");
}

void apbDecodeSocket::apbReg_uIp0Socket(void) {
    port_socket(apbReg_uIp0, "apbDecode.apbReg_uIp0");
}

void apbDecodeSocket::apbReg_uIp1Socket(void) {
    port_socket(apbReg_uIp1, "apbDecode.apbReg_uIp1");
}

apbDecodeSocket::apbDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("apbDecode", name(), bbMode)
        ,apbDecodeBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(apbReg_uBridgeSocket);
    SC_THREAD(apbReg_uIp0Socket);
    SC_THREAD(apbReg_uIp1Socket);

// GENERATED_CODE_END
}
