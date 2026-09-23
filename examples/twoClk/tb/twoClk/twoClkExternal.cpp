#include "workerThread.h"
#include "watchDog.h"

// GENERATED_CODE_PARAM --block=twoClk_tb --excludeInst=u_twoClk

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
import twoClk_twoClkCpu.base;
#include "twoClkExternal.h"

twoClkExternal::twoClkExternal(sc_module_name modulename) :
    twoClkInverted("Chnl"),
    log_(name())

   ,uCpu(std::dynamic_pointer_cast<twoClkCpuBase>(instanceFactory::createInstance(name(), "uCpu", "twoClkCpu", "", "twoClk")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCpu->twoClkReg(twoClkReg);

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    SC_THREAD(stimulusThread);
}

// Bound the run, then vote: this is only the External's own vote, cast once
// its fixed 200 ns window elapses. In every verilated configuration the cpu's
// tbl write/read/compare pass takes longer than this window, so the cpu's own
// vote is what actually closes those runs; this vote only has to outlast a
// model-only run, where every other voter finishes well inside the window.
void twoClkExternal::stimulusThread(void)
{
    wait(SC_ZERO_TIME);
    wait(200, SC_NS);
    log_.logPrint(std::format("{} run window elapsed, voting end-of-test", name()),
                  LOG_IMPORTANT);
    // Closing the window is the run's last progress event, so the shutdown that
    // follows is not charged as a stall. The External is deliberately not an
    // enabler: only a block that keeps tickling may arm the watchdog.
    watchDog::tickleWatchdog();
    eot_.setEndOfTest(true);
}
