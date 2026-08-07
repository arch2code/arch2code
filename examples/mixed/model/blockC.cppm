//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockC --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "rdy_vld_channel.h"
// GENERATED_CODE_END
// user #includes here
// GENERATED_CODE_BEGIN --template=moduleExport
export module mixed_blockC.block;
import mixed_blockC.base;
import mixed_mixedBlockC;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace mixed_mixedBlockC_ns;
export SC_MODULE(blockC), public blockBase, public blockCBase
{
private:

public:

    blockC(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~blockC() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(blockC);

// === Block factory registration (blockC) ===
void register_blockC_variants() {
    instanceFactory::registerBlock("blockC_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockC>(blockName, variant, bbMode)); }, "", "mixed");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _blockC_registered = (register_blockC_variants(), 0);
} // namespace
// === End block factory registration ===

blockC::blockC(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockC", name(), bbMode)
        ,blockCBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

