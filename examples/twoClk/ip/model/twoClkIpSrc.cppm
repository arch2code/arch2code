//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkIpSrc --mode=module
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
export module twoClkIp_twoClkIpSrc.block;
import twoClkIp_twoClkIpSrc.base;
import twoClkIp;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace twoClkIp_ns;
export SC_MODULE(twoClkIpSrc), public blockBase, public twoClkIpSrcBase
{
private:

public:

    twoClkIpSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~twoClkIpSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members

private:
    // push() is blocking, so returning from the last one proves the sink acked
    // every word - which is what the end-of-test vote reports.
    void driveOut(void);
    endOfTest eot_{true};
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
SC_HAS_PROCESS(twoClkIpSrc);

// === Block factory registration (twoClkIpSrc) ===
void register_twoClkIpSrc_variants() {
    instanceFactory::registerBlock("twoClkIpSrc_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>(std::make_shared<twoClkIpSrc>(blockName, variant, bbMode)); }, "", "twoClkIp");
}

namespace {
[[maybe_unused]] A2C_REGISTRATION_RETAIN int _twoClkIpSrc_registered = (register_twoClkIpSrc_variants(), 0);
} // namespace
// === End block factory registration ===

twoClkIpSrc::twoClkIpSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("twoClkIpSrc", name(), bbMode)
        ,twoClkIpSrcBase(name(), variant)
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

void twoClkIpSrc::driveOut(void)
{
    // Arm only now: before the burst starts there is no progress to expect.
    watchDog::enableWatchdog();
    for (unsigned i = 0; i < TWO_CLK_BURST_WORDS; ++i) {
        twoClkDataSt d;
        d.data = (twoClkDataT)(TWO_CLK_BURST_BASE + i);
        log_.logPrint(std::format("{} pushing word {} = 0x{:02x} on out",
                                  this->name(), i, (uint64_t)d.data), LOG_IMPORTANT);
        out->push(d);
        // push() returns only once the word was acked, so this is a completed
        // handshake, not merely an attempt to send one.
        watchDog::tickleWatchdog();
    }
    log_.logPrint(std::format("{} burst of {} words acked, voting end-of-test",
                              this->name(), TWO_CLK_BURST_WORDS), LOG_IMPORTANT);
    eot_.setEndOfTest(true);
};

