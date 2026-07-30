//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subBlockContainer --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module nested_subBlockContainer.block;
import nested_subBlockContainer.base;
import nested;
import nested_subBlock.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace nested_ns;

export SC_MODULE(subBlockContainer), public blockBase, public subBlockContainerBase
{
private:

public:
    // channels
    // Test interface
    rdy_vld_channel< test_st > src;

    //instances contained in block
    std::shared_ptr<subBlockBase> uSubBlock0;
    std::shared_ptr<subBlockBase> uSubBlock1;

    subBlockContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~subBlockContainer() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(subBlockContainer);

// === Block factory registration (subBlockContainer) ===
void register_subBlockContainer_variants() {
    instanceFactory::registerBlock("subBlockContainer_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<subBlockContainer>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _subBlockContainer_registered = (register_subBlockContainer_variants(), 0);
} // namespace
// === End block factory registration ===

subBlockContainer::subBlockContainer(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("subBlockContainer", name(), bbMode)
        ,subBlockContainerBase(name(), variant)
        ,src("subBlock_src", "subBlock")
        ,uSubBlock0(std::dynamic_pointer_cast<subBlockBase>(instanceFactory::createInstance(name(), "uSubBlock0", "subBlock", "", "nested")))
        ,uSubBlock1(std::dynamic_pointer_cast<subBlockBase>(instanceFactory::createInstance(name(), "uSubBlock1", "subBlock", "", "nested")))
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
};

