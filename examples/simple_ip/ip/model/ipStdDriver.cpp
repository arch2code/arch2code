//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDriver
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ipStdDriver.h"
SC_HAS_PROCESS(ipStdDriver);

// === Block factory registration (ipStdDriver) ===
void register_ipStdDriver_variants() {
    instanceFactory::registerBlock("ipStdDriver_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipStdDriver>(blockName, variant, bbMode)); }, "", "ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipStdDriver_registered = (register_ipStdDriver_variants(), 0);
} // namespace
// === End block factory registration ===

ipStdDriver::ipStdDriver(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdDriver", name(), bbMode)
        ,ipStdDriverBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

