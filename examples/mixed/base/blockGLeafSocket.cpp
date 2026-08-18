// GENERATED_CODE_PARAM --block=blockGLeaf
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockGLeafSocket.h"

SC_HAS_PROCESS(blockGLeafSocket);

blockGLeafSocket::registerBlock blockGLeafSocket::registerBlock_; //register the block with the factory

void blockGLeafSocket::rwGObserve(void) {
    port_observe(rwG, "blockGLeaf.rwG", [](const std::string &obs_name, const auto &val) {
        if constexpr (requires { val.irq; }) {
            socket_observe_irq(obs_name, static_cast<bool>(val.irq));
        }
    });
}

blockGLeafSocket::blockGLeafSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockGLeaf", name(), bbMode)
        ,blockGLeafBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(rwGObserve);

// GENERATED_CODE_END
}
