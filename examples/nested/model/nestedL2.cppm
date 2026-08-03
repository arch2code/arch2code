//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL2 --mode=module
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
export module nested_nestedL2.block;
import nested_nestedL2.base;
import nested_nestedL3.base;
import nested;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace nested_ns;
export SC_MODULE(nestedL2), public blockBase, public nestedL2Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL3Base> uNestedL3;

    nestedL2(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL2() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(nestedL2);

// === Block factory registration (nestedL2) ===
void register_nestedL2_variants() {
    instanceFactory::registerBlock("nestedL2_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL2>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedL2_registered = (register_nestedL2_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL2::nestedL2(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL2", name(), bbMode)
        ,nestedL2Base(name(), variant)
        ,uNestedL3(std::dynamic_pointer_cast<nestedL3Base>(instanceFactory::createInstance(name(), "uNestedL3", "nestedL3", "", "nested")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL3->nested3(nested2);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

