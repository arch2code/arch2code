//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk_tb --excludeInst=u_twoClk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "workerThread.h"
#include "watchDog.h"
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module twoClk.external;
import a2c.endOfTest;
import twoClk.base;
import twoClk_twoClkCpu.base;
import twoClk;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace twoClk_ns;

export class twoClkExternal: public sc_module, public twoClkInverted {

    logBlock log_;

public:

    std::shared_ptr<twoClkCpuBase> uCpu;

    SC_HAS_PROCESS (twoClkExternal);

    twoClkExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

    // twoClk has no boundary ports, so there is nothing for the External to
    // drive: the DUT's own producer is the stimulus and its own sink is the
    // checker. What the External owns is the run window. End-of-test needs
    // EVERY registered voter, and only the block models that are actually
    // elaborated register one, so this voter is what lets the same testbench
    // terminate in all seven configurations while still requiring the surviving
    // block model(s) to have seen their traffic first:
    //   model only                - all five block models + this voter
    //   --vlInst twoClk.uIpSrc    - sink + this voter (proves RTL -> model)
    //   --vlInst twoClk.uSink     - producer + this voter (proves model -> RTL)
    //   --vlInst twoClk.uSlowTick - slow sink + this voter (RTL -> model, BFM on clkSlow)
    //   --vlInst twoClk.uSlowSink - slow tick + this voter (model -> RTL on clkSlow)
    //   --vlInst twoClk.uTable    - cpu + this voter (proves model -> RTL through the bridge)
    //   --vlInst twoClk           - cpu + this voter (model -> RTL through the verilated router and bridge)
    void stimulusThread(void);

private:
    endOfTest eot_{true};
};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

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
};

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
