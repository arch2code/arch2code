//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkDivider --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module clkGen_clkDivider.block;
import clkGen_clkDivider.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(clkDivider), public blockBase, public clkDividerBase
{
private:

public:

    clkDivider(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~clkDivider() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(clkDivider);

// === Block factory registration (clkDivider) ===
void register_clkDivider_variants() {
    instanceFactory::registerBlock("clkDivider_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkDivider>(blockName, variant, bbMode)); }, "", "clkGen");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _clkDivider_registered = (register_clkDivider_variants(), 0);
} // namespace
// === End block factory registration ===

clkDivider::clkDivider(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("clkDivider", name(), bbMode)
        ,clkDividerBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

