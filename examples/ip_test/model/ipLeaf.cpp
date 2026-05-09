//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipLeaf
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "ipLeaf.h"
// === Block factory registration (ipLeaf) ===
namespace {
[[maybe_unused]] int _ipLeaf_registered = []() -> int {
    instanceFactory::registerBlock("ipLeaf_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<ipLeaf<ipLeafVariantLeaf0Config>>(blockName, variant, bbMode)); }, "variantLeaf0");
    return 0;
}();
} // namespace
// === End block factory registration ===

template<typename Config>
ipLeaf<Config>::ipLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("ipLeaf", name(), bbMode)
        ,ipLeafBase<Config>(name(), variant)
        ,ipLeafMem(name(), "ipLeafMem", mems, Config::LEAF_MEM_DEPTH)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

