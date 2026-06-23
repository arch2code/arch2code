//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeDriver
// GENERATED_CODE_BEGIN --template=constructor --section=init
#include "bridgeDriver.h"
SC_HAS_PROCESS(bridgeDriver);

// === Block factory registration (bridgeDriver) ===
void force_link_bridgeDriver() {}

void register_bridgeDriver_variants() {
    instanceFactory::registerBlock("bridgeDriver_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<bridgeDriver>(blockName, variant, bbMode)); }, "");
}

namespace {
[[maybe_unused]] int _bridgeDriver_registered = (register_bridgeDriver_variants(), 0);
} // namespace
// === End block factory registration ===

bridgeDriver::bridgeDriver(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("bridgeDriver", name(), bbMode)
        ,bridgeDriverBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveOut8);
    SC_THREAD(driveOut70);
};

void bridgeDriver::driveOut8(void)
{
    data8St d{};
    d.data = 0xA5;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x} marker {} on out8", this->name(), (uint64_t)d.data, (uint64_t)d.marker), LOG_IMPORTANT);
    this->out8->push(d);
}

void bridgeDriver::driveOut70(void)
{
    data70St d{};
    d.data.word[0] = 0x5A;
    d.data.word[1] = 0x2A;
    d.marker = 1;
    log_.logPrint(std::format("{} pushing 0x{:x}{:016x} marker {} on out70", this->name(), d.data.word[1], d.data.word[0], (uint64_t)d.marker), LOG_IMPORTANT);
    this->out70->push(d);
}

