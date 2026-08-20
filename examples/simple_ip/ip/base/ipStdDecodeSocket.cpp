// GENERATED_CODE_PARAM --block=ipStdDecode
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipStdDecodeSocket.h"

SC_HAS_PROCESS(ipStdDecodeSocket);

ipStdDecodeSocket::registerBlock ipStdDecodeSocket::registerBlock_; //register the block with the factory

void ipStdDecodeSocket::ipReg_uIpSocket(void) {
    port_socket(ipReg_uIp, "ipStdDecode.ipReg_uIp", {0x300u, 0x304u, 0x308u, 0x30cu, 0x310u, 0x318u, 0x31cu, 0x320u, 0x324u, 0x328u}, 0x3ffu);
}

ipStdDecodeSocket::ipStdDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdDecode", name(), bbMode)
        ,ipStdDecodeBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(ipReg_uIpSocket);

// GENERATED_CODE_END
}
