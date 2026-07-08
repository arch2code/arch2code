//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL6
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL6.h"
SC_HAS_PROCESS(nestedL6);

// === Block factory registration (nestedL6) ===
void register_nestedL6_variants() {
    instanceFactory::registerBlock("nestedL6_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL6>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedL6_registered = (register_nestedL6_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL6::nestedL6(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL6", name(), bbMode)
        ,nestedL6Base(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

