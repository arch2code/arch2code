// GENERATED_CODE_PARAM --block=dataGen
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "dataGenSocket.h"

SC_HAS_PROCESS(dataGenSocket);

dataGenSocket::registerBlock dataGenSocket::registerBlock_; //register the block with the factory

void dataGenSocket::outSocket(void) {
    port_socket(out, "dataGen.out");
}

dataGenSocket::dataGenSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dataGen", name(), bbMode)
        ,dataGenBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(outSocket);

// GENERATED_CODE_END
}
