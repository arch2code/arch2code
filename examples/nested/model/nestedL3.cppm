//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL3 --mode=module
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
export module nested_nestedL3.block;
import nested_nestedL3.base;
import nested_nestedL4.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
import nested;
using namespace nested_ns;

export SC_MODULE(nestedL3), public blockBase, public nestedL3Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL4Base> uNestedL4;

    nestedL3(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL3() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(nestedL3);

// === Block factory registration (nestedL3) ===
void register_nestedL3_variants() {
    instanceFactory::registerBlock("nestedL3_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<nestedL3>(blockName, variant, bbMode)); }, "", "nested");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _nestedL3_registered = (register_nestedL3_variants(), 0);
} // namespace
// === End block factory registration ===

nestedL3::nestedL3(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("nestedL3", name(), bbMode)
        ,nestedL3Base(name(), variant)
        ,uNestedL4(std::dynamic_pointer_cast<nestedL4Base>(instanceFactory::createInstance(name(), "uNestedL4", "nestedL4", "", "nested")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)
    uNestedL4->nested4(nested3);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

