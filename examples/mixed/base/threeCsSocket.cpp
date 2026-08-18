// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "threeCsSocket.h"

SC_HAS_PROCESS(threeCsSocket);

threeCsSocket::registerBlock threeCsSocket::registerBlock_; //register the block with the factory

void threeCsSocket::see0Socket(void) {
    port_socket(see0, "threeCs.see0");
}

void threeCsSocket::see1Socket(void) {
    port_socket(see1, "threeCs.see1");
}

void threeCsSocket::see2Socket(void) {
    port_socket(see2, "threeCs.see2");
}

threeCsSocket::threeCsSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("threeCs", name(), bbMode)
        ,threeCsBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(see0Socket);
    SC_THREAD(see1Socket);
    SC_THREAD(see2Socket);

// GENERATED_CODE_END
}
