// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=socketConstructor --section=initSocket
#include "blockFSocket.h"

template<> blockFSocket<blockFVariant0Config>::registerBlock blockFSocket<blockFVariant0Config>::registerBlock_("variant0"); //register the block with the factory
template<> blockFSocket<blockFVariant1Config>::registerBlock blockFSocket<blockFVariant1Config>::registerBlock_("variant1"); //register the block with the factory

template<typename Config>
void blockFSocket<Config>::cStuffIfSocket(void) {
    port_socket(this->cStuffIf, "blockF.cStuffIf");
}

template<typename Config>
void blockFSocket<Config>::dStuffIfSocket(void) {
    port_socket(this->dStuffIf, "blockF.dStuffIf");
}

template<typename Config>
void blockFSocket<Config>::dSinSocket(void) {
    port_socket(this->dSin, "blockF.dSin");
}

template<typename Config>
void blockFSocket<Config>::dSoutSocket(void) {
    port_socket(this->dSout, "blockF.dSout");
}

template<typename Config>
void blockFSocket<Config>::rwDObserve(void) {
    port_observe(this->rwD, "blockF.rwD", [](const std::string &obs_name, const auto &val) {
        if constexpr (requires { val.irq; }) {
            socket_observe_irq(obs_name, static_cast<bool>(val.irq));
        }
    });
}

template<typename Config>
blockFSocket<Config>::blockFSocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockF", name(), bbMode)
        ,blockFBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=socketConstructor --section=bodySocket
{
    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );
    SC_THREAD(cStuffIfSocket);
    SC_THREAD(dStuffIfSocket);
    SC_THREAD(dSinSocket);
    SC_THREAD(dSoutSocket);
    SC_THREAD(rwDObserve);

// GENERATED_CODE_END
}
