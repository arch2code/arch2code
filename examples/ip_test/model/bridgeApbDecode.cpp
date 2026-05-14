//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "bridgeApbDecode.h"
SC_HAS_PROCESS(bridgeApbDecode);

// === Block factory registration (bridgeApbDecode) ===
void force_link_bridgeApbDecode() {}

void register_bridgeApbDecode_variants() {
    instanceFactory::registerBlock("bridgeApbDecode_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeApbDecode>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _bridgeApbDecode_registered = (register_bridgeApbDecode_variants(), 0);
} // namespace
// === End block factory registration ===

void bridgeApbDecode::routerDecode(void) //handle apb routing for register
{
    log_.logPrint(std::format("SystemC Thread:{} started", __func__));
    decoder.decodeThread();
}

bridgeApbDecode::bridgeApbDecode(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bridgeApbDecode", name(), bbMode)
        ,bridgeApbDecodeBase(name(), variant)
        ,decoder(16, 20, apbReg, {
            &apb_uBridgeIp0,
            &apb_uBridgeIp1})
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    SC_THREAD(routerDecode);
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

