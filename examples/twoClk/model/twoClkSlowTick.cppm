//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowTick --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here
#include "watchDog.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module twoClk_twoClkSlowTick.block;
import twoClk_twoClkSlowTick.base;
import twoClkIp;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
import twoClk;
using namespace twoClk_ns;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClkIp_ns;
export SC_MODULE(twoClkSlowTick), public blockBase, public twoClkSlowTickBase
{
private:

public:

    twoClkSlowTick(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkSlowTick() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // push() is blocking, so returning from the last one proves the sink acked
    // every tick - which is what the end-of-test vote reports.
    void driveOut(void);
    endOfTest eot_{true};
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkSlowTick);

// === Block factory registration (twoClkSlowTick) ===
void register_twoClkSlowTick_variants() {
    instanceFactory::registerBlock("twoClkSlowTick_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkSlowTick>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkSlowTick_registered = (register_twoClkSlowTick_variants(), 0);
} // namespace
// === End block factory registration ===

twoClkSlowTick::twoClkSlowTick(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkSlowTick", name(), bbMode)
        ,twoClkSlowTickBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // Enabler registration commits this block to reporting progress below. It is
    // elaboration-time, so it always precedes every enable vote, and a config that
    // verilates this block away registers nothing and is correctly left unwatched.
    watchDog::registerEnabler();
    SC_THREAD(driveOut);
};

void twoClkSlowTick::driveOut(void)
{
    // Arm only now: before the first tick there is no progress to expect.
    watchDog::enableWatchdog();
    for (unsigned i = 0; i < TWO_CLK_TICK_WORDS; ++i) {
        // The timed wait is the model's cadence; push() returning only once the
        // sink has acked is what proves the handshake, not the wait itself.
        wait(TWO_CLK_TICK_DIV * TWO_CLK_SLOW_PERIOD_NS, SC_NS);
        twoClkDataSt d;
        d.data = (twoClkDataT)i;
        log_.logPrint(std::format("{} pushing tick {} = 0x{:02x} on out",
                                  this->name(), i, (uint64_t)d.data), LOG_IMPORTANT);
        out->push(d);
        watchDog::tickleWatchdog();
    }
    log_.logPrint(std::format("{} all {} ticks acked, voting end-of-test",
                              this->name(), TWO_CLK_TICK_WORDS), LOG_IMPORTANT);
    eot_.setEndOfTest(true);
};

