// GENERATED_CODE_PARAM --block=subBlockContainer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "subBlockContainerSocket.h"

SC_HAS_PROCESS(subBlockContainerSocket);

subBlockContainerSocket::registerBlock subBlockContainerSocket::registerBlock_; //register the block with the factory

void subBlockContainerSocket::inSocket(void) {
    port_socket(in, "subBlockContainer.in");
}

void subBlockContainerSocket::outSocket(void) {
    port_socket(out, "subBlockContainer.out");
}

subBlockContainerSocket::subBlockContainerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlockContainer", name(), bbMode)
        ,subBlockContainerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(inSocket);
    SC_THREAD(outSocket);

// GENERATED_CODE_END
}
