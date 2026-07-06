//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=leaf
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "leaf.h"
SC_HAS_PROCESS(leaf);

// === Block factory registration (leaf) ===
void register_leaf_variants() {
    instanceFactory::registerBlock("leaf_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<leaf>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _leaf_registered = (register_leaf_variants(), 0);
} // namespace
// === End block factory registration ===

leaf::leaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("leaf", name(), bbMode)
        ,leafBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forward);
};

// Pass-through pipeline stage: receive a word on dIn and forward it on dOut.
void leaf::forward(void)
{
    while (true)
    {
        dat_st w;
        dIn->pushReceive(w);
        dIn->ack();
        dOut->push(w);
    }
};

