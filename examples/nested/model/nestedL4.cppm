//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=nestedL4 --mode=module
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
export module nested_nestedL4.block;
import nested_nestedL4.base;
import nested_nestedL5.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
import nested;
using namespace nested_ns;

export SC_MODULE(nestedL4), public blockBase, public nestedL4Base
{
private:

public:
    //instances contained in block
    std::shared_ptr<nestedL5Base> uNestedL5;

    nestedL4(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~nestedL4() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
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

