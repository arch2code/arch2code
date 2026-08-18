// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockDSocket.h"

SC_HAS_PROCESS(blockDSocket);

blockDSocket::registerBlock blockDSocket::registerBlock_; //register the block with the factory

void blockDSocket::cStuffIfSocket(void) {
    port_socket(cStuffIf, "blockD.cStuffIf");
}

void blockDSocket::dee0Socket(void) {
    port_socket(dee0, "blockD.dee0");
}

void blockDSocket::dee1Socket(void) {
    port_socket(dee1, "blockD.dee1");
}

void blockDSocket::outDSocket(void) {
    port_socket(outD, "blockD.outD");
}

void blockDSocket::inDSocket(void) {
    port_socket(inD, "blockD.inD");
}

void blockDSocket::btodSocket(void) {
    port_socket(btod, "blockD.btod");
}

void blockDSocket::rwDObserve(void) {
    port_observe(rwD, "blockD.rwD", [](const std::string &obs_name, const auto &val) {
        if constexpr (requires { val.irq; }) {
            socket_observe_irq(obs_name, static_cast<bool>(val.irq));
        }
    });
}

blockDSocket::blockDSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockD", name(), bbMode)
        ,blockDBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(cStuffIfSocket);
    SC_THREAD(dee0Socket);
    SC_THREAD(dee1Socket);
    SC_THREAD(outDSocket);
    SC_THREAD(inDSocket);
    SC_THREAD(btodSocket);
    SC_THREAD(rwDObserve);

// GENERATED_CODE_END
}
