//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSlowSink --mode=module
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
export module twoClk_twoClkSlowSink.block;
import twoClk_twoClkSlowSink.base;
import twoClkIp;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
import twoClk;
using namespace twoClk_ns;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClkIp_ns;
export SC_MODULE(twoClkSlowSink), public blockBase, public twoClkSlowSinkBase
{
private:

public:

    twoClkSlowSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkSlowSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // The end-of-test vote is cast only after every tick word has arrived with
    // the expected payload and cadence, so it is itself the evidence the
    // connection carried both correctly.
    void receiveIn(void);
    endOfTest eot_{true};
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkSlowSink);

// === Block factory registration (twoClkSlowSink) ===
void register_twoClkSlowSink_variants() {
    instanceFactory::registerBlock("twoClkSlowSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkSlowSink>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkSlowSink_registered = (register_twoClkSlowSink_variants(), 0);
} // namespace
// === End block factory registration ===

twoClkSlowSink::twoClkSlowSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkSlowSink", name(), bbMode)
        ,twoClkSlowSinkBase(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    // Enabler registration commits this block to reporting progress below. It is
    // elaboration-time, so it always precedes every enable vote, and a config that
    // verilates this block away registers nothing and is correctly left unwatched.
    watchDog::registerEnabler();
    SC_THREAD(receiveIn);
};

void twoClkSlowSink::receiveIn(void)
{
    // Arm only now: before the first tick there is no progress to expect.
    watchDog::enableWatchdog();
    sc_time last;
    for (unsigned i = 0; i < TWO_CLK_TICK_WORDS; ++i) {
        twoClkDataSt d;
        in->pushReceive(d);
        sc_time now = sc_time_stamp();
        Q_ASSERT(d.data == (twoClkDataT)i,
                 "twoClkSlowSink received an unexpected tick value");
        // Exact equality: in the verilated-tick run a block clocked by clk
        // instead of clkSlow arrives every TWO_CLK_TICK_DIV ns rather than
        // TWO_CLK_TICK_DIV * TWO_CLK_SLOW_PERIOD_NS. The first interval is
        // start-up (reset release plus handshake), so it is not checked.
        if (i > 0) {
            Q_ASSERT(now - last == sc_time(TWO_CLK_TICK_DIV * TWO_CLK_SLOW_PERIOD_NS, SC_NS),
                     "twoClkSlowSink tick cadence is not TWO_CLK_TICK_DIV clkSlow periods");
        }
        log_.logPrint(std::format("{} received tick {} = 0x{:02x} on in at {}",
                                  this->name(), i, (uint64_t)d.data, now.to_string()), LOG_IMPORTANT);
        last = now;
        in->ack();
        // A checked word that has been acked is consumed traffic, so this is the
        // sink's only honest evidence that the connection is still moving.
        watchDog::tickleWatchdog();
    }
    log_.logPrint(std::format("{} received all {} ticks, voting end-of-test",
                              this->name(), TWO_CLK_TICK_WORDS), LOG_IMPORTANT);
    eot_.setEndOfTest(true);
};

