// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "hierVlDemoSocket.h"

SC_HAS_PROCESS(hierVlDemoSocket);

hierVlDemoSocket::registerBlock hierVlDemoSocket::registerBlock_; //register the block with the factory

void hierVlDemoSocket::axis4_t1Socket(void) {
    port_socket(axis4_t1, "hierVlDemo.axis4_t1");
}

void hierVlDemoSocket::axis4_t2Socket(void) {
    port_socket(axis4_t2, "hierVlDemo.axis4_t2");
}

hierVlDemoSocket::hierVlDemoSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("hierVlDemo", name(), bbMode)
        ,hierVlDemoBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(axis4_t1Socket);
    SC_THREAD(axis4_t2Socket);

// GENERATED_CODE_END
}
