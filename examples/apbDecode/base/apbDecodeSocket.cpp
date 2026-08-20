// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "apbDecodeSocket.h"

SC_HAS_PROCESS(apbDecodeSocket);

apbDecodeSocket::registerBlock apbDecodeSocket::registerBlock_; //register the block with the factory

void apbDecodeSocket::apbReg_uBlockASocket(void) {
    port_socket(apbReg_uBlockA, "apbDecode.apbReg_uBlockA", {0x200u, 0x204u, 0x208u, 0x20cu, 0x210u, 0x214u, 0x218u, 0x21cu}, 0x3ffu);
}

void apbDecodeSocket::apbReg_uBlockBSocket(void) {
    port_socket(apbReg_uBlockB, "apbDecode.apbReg_uBlockB", {0x200u, 0x208u}, 0x3ffu);
}

apbDecodeSocket::apbDecodeSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("apbDecode", name(), bbMode)
        ,apbDecodeBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(apbReg_uBlockASocket);
    SC_THREAD(apbReg_uBlockBSocket);

// GENERATED_CODE_END
}
