//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE


// GENERATED_CODE_PARAM --block=blockC
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockC.h"
SC_HAS_PROCESS(blockC);

// === Block factory registration (blockC) ===
void force_link_blockC() {}

void register_blockC_variants() {
    instanceFactory::registerBlock("blockC_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockC>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _blockC_registered = (register_blockC_variants(), 0);
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
}
