// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE


// GENERATED_CODE_PARAM --block=subBlockContainer
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "subBlockContainer.h"
#include "subBlockBase.h"
SC_HAS_PROCESS(subBlockContainer);

// === Block factory registration (subBlockContainer) ===
void force_link_subBlockContainer() {}

void register_subBlockContainer_variants() {
    instanceFactory::registerBlock("subBlockContainer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subBlockContainer>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _subBlockContainer_registered = (register_subBlockContainer_variants(), 0);
} // namespace
// === End block factory registration ===

subBlockContainer::subBlockContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlockContainer", name(), bbMode)
        ,subBlockContainerBase(name(), variant)
        ,src("subBlock_src", "subBlock")
        ,uSubBlock0(std::dynamic_pointer_cast<subBlockBase>((force_link_subBlock(), instanceFactory::createInstance(name(), "uSubBlock0", "subBlock", ""))))
        ,uSubBlock1(std::dynamic_pointer_cast<subBlockBase>((force_link_subBlock(), instanceFactory::createInstance(name(), "uSubBlock1", "subBlock", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uSubBlock0->dst(in);
    uSubBlock1->src(out);
    // instance to instance connections via channel
    uSubBlock0->src(src);
    uSubBlock1->dst(src);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}

