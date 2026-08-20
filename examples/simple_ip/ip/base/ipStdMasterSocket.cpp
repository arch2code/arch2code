// GENERATED_CODE_PARAM --block=ipStdMaster
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipStdMasterSocket.h"

SC_HAS_PROCESS(ipStdMasterSocket);

ipStdMasterSocket::registerBlock ipStdMasterSocket::registerBlock_; //register the block with the factory

void ipStdMasterSocket::apbOutSocket(void) {
    port_socket(apbOut, "ipStdMaster.apbOut", {0x300u, 0x304u, 0x308u, 0x30cu, 0x310u, 0x318u, 0x31cu, 0x320u, 0x324u, 0x328u}, 0x3ffu);
}

ipStdMasterSocket::ipStdMasterSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdMaster", name(), bbMode)
        ,ipStdMasterBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(apbOutSocket);

// GENERATED_CODE_END
}
