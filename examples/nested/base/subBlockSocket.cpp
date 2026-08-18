// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "subBlockSocket.h"

SC_HAS_PROCESS(subBlockSocket);

subBlockSocket::registerBlock subBlockSocket::registerBlock_; //register the block with the factory

void subBlockSocket::srcSocket(void) {
    port_socket(src, "subBlock.src");
}

void subBlockSocket::dstSocket(void) {
    port_socket(dst, "subBlock.dst");
}

subBlockSocket::subBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlock", name(), bbMode)
        ,subBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(srcSocket);
    SC_THREAD(dstSocket);

// GENERATED_CODE_END
}
