//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "src.h"
#include "ipLeafBase.h"
// === Block factory registration (src) ===
namespace {
[[maybe_unused]] int _src_registered = []() -> int {
    instanceFactory::registerBlock("src_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<src<srcVariantSrc0Config>>(blockName, variant, bbMode)); }, "variantSrc0");
    return 0;
}();
} // namespace
// === End block factory registration ===

template<typename Config>
src<Config>::src(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("src", name(), bbMode)
        ,srcBase<Config>(name(), variant)
        ,uLeaf(std::dynamic_pointer_cast<ipLeafBase<ipLeafVariantLeaf0Config>>(instanceFactory::createInstance(name(), "uLeaf", "ipLeaf", "variantLeaf0")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveOut0);
    SC_THREAD(driveOut1);
};

template<typename Config>
void src<Config>::driveOut0(void)
{
    srcOut0St<Config> d{};
    d.data = 0xA5;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x} marker {} on out0", this->name(), (uint64_t)d.data, (uint64_t)d.marker), LOG_IMPORTANT);
    this->out0->push(d);
}

template<typename Config>
void src<Config>::driveOut1(void)
{
    srcOut1St<Config> d{};
    d.data.word[0] = 0x5A;
    d.data.word[1] = 0x2A;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x}{:016x} marker {} on out1", this->name(), d.data.word[1], d.data.word[0], (uint64_t)d.marker), LOG_IMPORTANT);
    this->out1->push(d);
}
