#include "workerThread.h"
#include "watchDog.h"
#include "testController.h"

// GENERATED_CODE_PARAM --block=clkGen

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
import clkGen_clkDivider.base;
import clkGen_rstSync.base;
import clkGen_clkConsumer.base;
#include "clkGenExternal.h"

clkGenExternal::clkGenExternal(sc_module_name modulename) :
    clkGenInverted("Chnl"),
    log_(name())

   ,uDivider(std::dynamic_pointer_cast<clkDividerBase>(instanceFactory::createInstance(name(), "uDivider", "clkDivider", "", "clkGen")))
   ,uRstSync(std::dynamic_pointer_cast<rstSyncBase>(instanceFactory::createInstance(name(), "uRstSync", "rstSync", "", "clkGen")))
   ,uConsumer(std::dynamic_pointer_cast<clkConsumerBase>(instanceFactory::createInstance(name(), "uConsumer", "clkConsumer", "", "clkGen")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    SC_THREAD(stimulusThread);
}

// Bound the run, then vote. The window has to outlast a verilated DUT's reset
// release (a few clkRef edges) and several clkDiv edges beyond that, so a
// stalled clkDiv (R23) has time to show up under a waveform before the vote
// closes the run; nothing here inspects the DUT's internals directly.
void clkGenExternal::stimulusThread(void)
{
    testController::GetInstance().register_test_name("clkGenRunWindow");
    wait(SC_ZERO_TIME);
    wait(500, SC_NS);
    log_.logPrint(std::format("{} run window elapsed, voting end-of-test", name()),
                  LOG_IMPORTANT);
    watchDog::tickleWatchdog();
    testController::GetInstance().test_complete("clkGenRunWindow");
    eot_.setEndOfTest(true);
}
