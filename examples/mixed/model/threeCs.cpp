//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE


// GENERATED_CODE_PARAM --block=threeCs
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "threeCs.h"
#include "blockCBase.h"
SC_HAS_PROCESS(threeCs);

// === Block factory registration (threeCs) ===
void force_link_threeCs() {}

void register_threeCs_variants() {
    instanceFactory::registerBlock("threeCs_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<threeCs>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _threeCs_registered = (register_threeCs_variants(), 0);
} // namespace
// === End block factory registration ===

threeCs::threeCs(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("threeCs", name(), bbMode)
        ,threeCsBase(name(), variant)
        ,uBlockC0(std::dynamic_pointer_cast<blockCBase>((force_link_blockC(), instanceFactory::createInstance(name(), "uBlockC0", "blockC", ""))))
        ,uBlockC1(std::dynamic_pointer_cast<blockCBase>((force_link_blockC(), instanceFactory::createInstance(name(), "uBlockC1", "blockC", ""))))
        ,uBlockC2(std::dynamic_pointer_cast<blockCBase>((force_link_blockC(), instanceFactory::createInstance(name(), "uBlockC2", "blockC", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uBlockC0->see(see0);
    uBlockC1->see(see1);
    uBlockC2->see(see2);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}
