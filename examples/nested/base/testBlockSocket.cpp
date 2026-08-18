// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "testBlockSocket.h"

SC_HAS_PROCESS(testBlockSocket);

testBlockSocket::registerBlock testBlockSocket::registerBlock_; //register the block with the factory

void testBlockSocket::loop1srcSocket(void) {
    port_socket(loop1src, "testBlock.loop1src");
}

void testBlockSocket::loop1dstSocket(void) {
    port_socket(loop1dst, "testBlock.loop1dst");
}

void testBlockSocket::loop2srcSocket(void) {
    port_socket(loop2src, "testBlock.loop2src");
}

void testBlockSocket::loop2dstSocket(void) {
    port_socket(loop2dst, "testBlock.loop2dst");
}

testBlockSocket::testBlockSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("testBlock", name(), bbMode)
        ,testBlockBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(loop1srcSocket);
    SC_THREAD(loop1dstSocket);
    SC_THREAD(loop2srcSocket);
    SC_THREAD(loop2dstSocket);

// GENERATED_CODE_END
}
