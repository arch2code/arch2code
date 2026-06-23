//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL5
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL5.h"
#include "nestedL6Base.h"
SC_HAS_PROCESS(nestedL5);

// === Block factory registration (nestedL5) ===
void force_link_nestedL5() {}

void register_nestedL5_variants() {
    instanceFactory::registerBlock("nestedL5_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL5>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _nestedL5_registered = (register_nestedL5_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL5::nestedL5(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL5", name(), bbMode)
        ,nestedL5Base(name(), variant)
        ,uNestedL6(std::dynamic_pointer_cast<nestedL6Base>((force_link_nestedL6(), instanceFactory::createInstance(name(), "uNestedL6", "nestedL6", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL6->nested6(nested5);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

