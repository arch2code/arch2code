//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL5 --mode=module
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
export module nested_nestedL5.block;
import nested_nestedL5.base;
import nested_nestedL6.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
import nested;
using namespace nested_ns;

export SC_MODULE(nestedL5), public blockBase, public nestedL5Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL6Base> uNestedL6;

    nestedL5(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL5() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(nestedL5);

// === Block factory registration (nestedL5) ===
void register_nestedL5_variants() {
    instanceFactory::registerBlock("nestedL5_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL5>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedL5_registered = (register_nestedL5_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL5::nestedL5(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL5", name(), bbMode)
        ,nestedL5Base(name(), variant)
        ,uNestedL6(std::dynamic_pointer_cast<nestedL6Base>(instanceFactory::createInstance(name(), "uNestedL6", "nestedL6", "", "nested")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL6->nested6(nested5);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

