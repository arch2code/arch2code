//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "apbDecode.h"
SC_HAS_PROCESS(apbDecode);

// === Block factory registration (apbDecode) ===
void force_link_apbDecode() {}

void register_apbDecode_variants() {
    instanceFactory::registerBlock("apbDecode_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<apbDecode>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _apbDecode_registered = (register_apbDecode_variants(), 0);
} // namespace
// === End block factory registration ===

void apbDecode::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

apbDecode::apbDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("apbDecode", name(), bbMode)
        ,apbDecodeBase(name(), variant)
        ,decoder(16, 24, cpu_main, {
            &apb_uBlockA,
            &apb_uBlockB})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

