//
#include "pySocket.h"

#include <format>

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "pySocket.h"
SC_HAS_PROCESS(pySocket);

// === Block factory registration (pySocket) ===
void register_pySocket_variants() {
    instanceFactory::registerBlock("pySocket_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<pySocket>(blockName, variant, bbMode)); }, "", "pySocket");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _pySocket_registered = (register_pySocket_variants(), 0);
} // namespace
// === End block factory registration ===

pySocket::pySocket(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("pySocket", name(), bbMode)
        ,pySocketBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};
