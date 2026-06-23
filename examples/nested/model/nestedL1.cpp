//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL1
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "nestedL1.h"
#include "nestedL2Base.h"
SC_HAS_PROCESS(nestedL1);

// === Block factory registration (nestedL1) ===
void force_link_nestedL1() {}

void register_nestedL1_variants() {
    instanceFactory::registerBlock("nestedL1_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL1>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _nestedL1_registered = (register_nestedL1_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL1::nestedL1(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL1", name(), bbMode)
        ,nestedL1Base(name(), variant)
        ,uNestedL2(std::dynamic_pointer_cast<nestedL2Base>((force_link_nestedL2(), instanceFactory::createInstance(name(), "uNestedL2", "nestedL2", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL2->nested2(nested1);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

