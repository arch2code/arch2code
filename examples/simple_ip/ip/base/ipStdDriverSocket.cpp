// GENERATED_CODE_PARAM --block=ipStdDriver
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "ipStdDriverSocket.h"

SC_HAS_PROCESS(ipStdDriverSocket);

ipStdDriverSocket::registerBlock ipStdDriverSocket::registerBlock_; //register the block with the factory

void ipStdDriverSocket::out0Socket(void) {
    port_socket(out0, "ipStdDriver.out0");
}

ipStdDriverSocket::ipStdDriverSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdDriver", name(), bbMode)
        ,ipStdDriverBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(out0Socket);

// GENERATED_CODE_END
}
