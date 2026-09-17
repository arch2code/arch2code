//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=rstSync --mode=module
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
export module clkGen_rstSync.block;
import clkGen_rstSync.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(rstSync), public blockBase, public rstSyncBase
{
private:

public:

    rstSync(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~rstSync() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(rstSync);

// === Block factory registration (rstSync) ===
void register_rstSync_variants() {
    instanceFactory::registerBlock("rstSync_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<rstSync>(blockName, variant, bbMode)); }, "", "clkGen");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _rstSync_registered = (register_rstSync_variants(), 0);
} // namespace
// === End block factory registration ===

rstSync::rstSync(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("rstSync", name(), bbMode)
        ,rstSyncBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

