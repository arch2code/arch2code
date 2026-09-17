//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen --mode=module
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
export module clkGen.block;
import clkGen.base;
import clkGen_clkDivider.base;
import clkGen_rstSync.base;
import clkGen_clkConsumer.base;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export SC_MODULE(clkGen), public blockBase, public clkGenBase
{
private:

public:
    //instances contained in block
    std::shared_ptr<clkDividerBase> uDivider;
    std::shared_ptr<rstSyncBase> uRstSync;
    std::shared_ptr<clkConsumerBase> uConsumer;

    clkGen(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~clkGen() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(clkGen);

// === Block factory registration (clkGen) ===
void register_clkGen_variants() {
    instanceFactory::registerBlock("clkGen_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<clkGen>(blockName, variant, bbMode)); }, "", "clkGen");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _clkGen_registered = (register_clkGen_variants(), 0);
} // namespace
// === End block factory registration ===

clkGen::clkGen(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("clkGen", name(), bbMode)
        ,clkGenBase(name(), variant)
        ,uDivider(std::dynamic_pointer_cast<clkDividerBase>(instanceFactory::createInstance(name(), "uDivider", "clkDivider", "", "clkGen")))
        ,uRstSync(std::dynamic_pointer_cast<rstSyncBase>(instanceFactory::createInstance(name(), "uRstSync", "rstSync", "", "clkGen")))
        ,uConsumer(std::dynamic_pointer_cast<clkConsumerBase>(instanceFactory::createInstance(name(), "uConsumer", "clkConsumer", "", "clkGen")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

