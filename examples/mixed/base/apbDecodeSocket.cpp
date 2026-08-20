// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "apbDecodeSocket.h"

SC_HAS_PROCESS(apbDecodeSocket);

apbDecodeSocket::registerBlock apbDecodeSocket::registerBlock_; //register the block with the factory

void apbDecodeSocket::apbReg_uBlockASocket(void) {
    port_socket(apbReg_uBlockA, "apbDecode.apbReg_uBlockA", {0xc0u}, 0xffu);
}

void apbDecodeSocket::apbReg_uBlockBSocket(void) {
    port_socket(apbReg_uBlockB, "apbDecode.apbReg_uBlockB", {0x140u, 0x148u}, 0x1ffu);
}

void apbDecodeSocket::apbReg_uBlockGSocket(void) {
    port_socket(apbReg_uBlockG, "apbDecode.apbReg_uBlockG", {0x0u}, 0x7u);
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
    SC_THREAD(apbReg_uBlockGSocket);

// GENERATED_CODE_END
}
