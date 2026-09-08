#include "workerThread.h"
#include "watchDog.h"

// GENERATED_CODE_PARAM --block=twoClk_tb --excludeInst=u_twoClk

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
#include "twoClkExternal.h"

twoClkExternal::twoClkExternal(sc_module_name modulename) :
    twoClkInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    SC_THREAD(stimulusThread);
}

// Bound the run, then vote. The window has to outlast the slowest
// configuration, which is a verilated DUT: its wrapper clock is 1 ns, it holds
// reset until 5 ns, and it needs one handshake per burst word after that. It
// also outlasts the 100 ns framework startup gate, so the vote is never the
// thing being waited on in a model-only run.
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
