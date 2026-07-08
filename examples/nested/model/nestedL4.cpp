//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL4
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL4.h"
import nestedL5.base;
SC_HAS_PROCESS(nestedL4);

// === Block factory registration (nestedL4) ===
void register_nestedL4_variants() {
    instanceFactory::registerBlock("nestedL4_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL4>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedL4_registered = (register_nestedL4_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL4::nestedL4(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL4", name(), bbMode)
        ,nestedL4Base(name(), variant)
        ,uNestedL5(std::dynamic_pointer_cast<nestedL5Base>(instanceFactory::createInstance(name(), "uNestedL5", "nestedL5", "", "nested")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL5->nested5(nested4);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

