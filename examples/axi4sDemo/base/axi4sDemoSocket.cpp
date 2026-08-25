// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "axi4sDemoSocket.h"

SC_HAS_PROCESS(axi4sDemoSocket);

axi4sDemoSocket::registerBlock axi4sDemoSocket::registerBlock_; //register the block with the factory

void axi4sDemoSocket::axis4_t1Socket(void) {
    port_socket(axis4_t1, "axi4sDemo.axis4_t1");
}

void axi4sDemoSocket::axis4_t2Socket(void) {
    port_socket(axis4_t2, "axi4sDemo.axis4_t2");
}

axi4sDemoSocket::axi4sDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("axi4sDemo", name(), bbMode)
        ,axi4sDemoBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(axis4_t1Socket);
    SC_THREAD(axis4_t2Socket);

// GENERATED_CODE_END
}
