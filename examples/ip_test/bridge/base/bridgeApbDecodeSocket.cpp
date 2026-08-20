// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "bridgeApbDecodeSocket.h"

SC_HAS_PROCESS(bridgeApbDecodeSocket);

bridgeApbDecodeSocket::registerBlock bridgeApbDecodeSocket::registerBlock_; //register the block with the factory

void bridgeApbDecodeSocket::apbReg_uBridgeIp0Socket(void) {
    port_socket(apbReg_uBridgeIp0, "bridgeApbDecode.apbReg_uBridgeIp0", {0x300u, 0x304u, 0x308u, 0x30cu, 0x310u, 0x318u, 0x31cu, 0x320u, 0x324u, 0x328u}, 0x3ffu);
}

void bridgeApbDecodeSocket::apbReg_uBridgeIp1Socket(void) {
    port_socket(apbReg_uBridgeIp1, "bridgeApbDecode.apbReg_uBridgeIp1", {0x300u, 0x304u, 0x308u, 0x30cu, 0x310u, 0x318u, 0x31cu, 0x320u, 0x324u, 0x328u}, 0x3ffu);
}

bridgeApbDecodeSocket::bridgeApbDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bridgeApbDecode", name(), bbMode)
        ,bridgeApbDecodeBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(apbReg_uBridgeIp0Socket);
    SC_THREAD(apbReg_uBridgeIp1Socket);

// GENERATED_CODE_END
}
