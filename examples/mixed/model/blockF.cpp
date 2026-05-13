//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE


// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "blockF.h"
// === Block factory registration (blockF) ===
namespace {
[[gnu::used]] std::shared_ptr<blockBase> _blockF_instantiate_variant_0(
    const char * blockName, const char * variant, blockBaseMode bbMode) {
    return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<blockFVariant0Config>>(blockName, variant, bbMode));
}
[[maybe_unused, gnu::used]] auto _blockF_instantiate_variant_0_anchor = &_blockF_instantiate_variant_0;
[[gnu::used]] std::shared_ptr<blockBase> _blockF_instantiate_variant_1(
    const char * blockName, const char * variant, blockBaseMode bbMode) {
    return static_cast<std::shared_ptr<blockBase>>(std::make_shared<blockF<blockFVariant1Config>>(blockName, variant, bbMode));
}
[[maybe_unused, gnu::used]] auto _blockF_instantiate_variant_1_anchor = &_blockF_instantiate_variant_1;
} // namespace
// === End block factory registration ===

template<typename Config>
blockF<Config>::blockF(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("blockF", name(), bbMode)
        ,blockFBase<Config>(name(), variant)
        ,test(name(), "test", mems, Config::bob)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
}
