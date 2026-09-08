//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkSink --mode=module
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
export module twoClk_twoClkSink.block;
import twoClk_twoClkSink.base;
import twoClkIp;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClkIp_ns;
export SC_MODULE(twoClkSink), public blockBase, public twoClkSinkBase
{
private:

public:

    twoClkSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkSink() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // The end-of-test vote is cast only after every word has arrived with the
    // expected payload, so it is itself the evidence the connection carried.
    void receiveIn(void);
    endOfTest eot_{true};
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkSink);

// === Block factory registration (twoClkSink) ===
void register_twoClkSink_variants() {
    instanceFactory::registerBlock("twoClkSink_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkSink>(blockName, variant, bbMode)); }, "", "twoClk");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkSink_registered = (register_twoClkSink_variants(), 0);
} // namespace
// === End block factory registration ===

twoClkSink::twoClkSink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkSink", name(), bbMode)
        ,twoClkSinkBase(name(), variant)
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

void twoClkSink::receiveIn(void)
{
    // Arm only now: before the burst starts there is no progress to expect.
    watchDog::enableWatchdog();
    for (unsigned i = 0; i < TWO_CLK_BURST_WORDS; ++i) {
        twoClkDataSt d;
        in->pushReceive(d);
        log_.logPrint(std::format("{} received word {} = 0x{:02x} on in",
                                  this->name(), i, (uint64_t)d.data), LOG_IMPORTANT);
        Q_ASSERT(d.data == (twoClkDataT)(TWO_CLK_BURST_BASE + i),
                 "twoClkSink received an unexpected payload word");
        in->ack();
        // A checked word that has been acked is consumed traffic, so this is the
        // sink's only honest evidence that the connection is still moving.
        watchDog::tickleWatchdog();
    }
    log_.logPrint(std::format("{} received all {} words, voting end-of-test",
                              this->name(), TWO_CLK_BURST_WORDS), LOG_IMPORTANT);
    eot_.setEndOfTest(true);
};

