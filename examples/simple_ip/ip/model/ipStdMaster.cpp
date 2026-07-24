//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdMaster
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ipStdMaster.h"
SC_HAS_PROCESS(ipStdMaster);

// === Block factory registration (ipStdMaster) ===
void register_ipStdMaster_variants() {
    instanceFactory::registerBlock("ipStdMaster_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipStdMaster>(blockName, variant, bbMode)); }, "", "ip");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _ipStdMaster_registered = (register_ipStdMaster_variants(), 0);
} // namespace
// === End block factory registration ===

ipStdMaster::ipStdMaster(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipStdMaster", name(), bbMode)
        ,ipStdMasterBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

