// GENERATED_CODE_PARAM --block=testContainer
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "testContainerSocket.h"

SC_HAS_PROCESS(testContainerSocket);

testContainerSocket::registerBlock testContainerSocket::registerBlock_; //register the block with the factory

void testContainerSocket::testSocket(void) {
    port_socket(test, "testContainer.test");
}

testContainerSocket::testContainerSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("testContainer", name(), bbMode)
        ,testContainerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(testSocket);

// GENERATED_CODE_END
}
