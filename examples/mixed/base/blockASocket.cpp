// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockASocket.h"

SC_HAS_PROCESS(blockASocket);

blockASocket::registerBlock blockASocket::registerBlock_; //register the block with the factory

void blockASocket::aStuffIfSocket(void) {
    port_socket(aStuffIf, "blockA.aStuffIf");
}

void blockASocket::cStuffIfSocket(void) {
    port_socket(cStuffIf, "blockA.cStuffIf");
}

void blockASocket::startDoneSocket(void) {
    port_socket(startDone, "blockA.startDone");
}

void blockASocket::dupIfSocket(void) {
    port_socket(dupIf, "blockA.dupIf");
}

blockASocket::blockASocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockA", name(), bbMode)
        ,blockABase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(aStuffIfSocket);
    SC_THREAD(cStuffIfSocket);
    SC_THREAD(startDoneSocket);
    SC_THREAD(dupIfSocket);

// GENERATED_CODE_END
}
