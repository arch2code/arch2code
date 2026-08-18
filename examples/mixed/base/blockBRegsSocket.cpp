// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockBRegsSocket.h"

SC_HAS_PROCESS(blockBRegsSocket);

blockBRegsSocket::registerBlock blockBRegsSocket::registerBlock_; //register the block with the factory

void blockBRegsSocket::roBsizeObserve(void) {
    port_observe(roBsize, "blockBRegs.roBsize", [](const std::string &obs_name, const auto &val) {
        if constexpr (requires { val.irq; }) {
            socket_observe_irq(obs_name, static_cast<bool>(val.irq));
        }
    });
}

blockBRegsSocket::blockBRegsSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockBRegs", name(), bbMode)
        ,blockBRegsBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(roBsizeObserve);

// GENERATED_CODE_END
}
