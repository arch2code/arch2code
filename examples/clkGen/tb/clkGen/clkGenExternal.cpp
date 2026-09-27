#include "workerThread.h"
#include "watchDog.h"
#include "testController.h"
#include "q_assert.h"
#include "simController.h"

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

// clkDivider toggles clkDiv every DIV_HALF_COUNT (4) cycles of the 10 ns clkRef.
static const sc_time clkDivHalfPeriod(40, SC_NS);
// The first clkDiv edge is expected at 70 ns: rstRef_n releases after 3
// clkRef cycles, then one half period of counting. The limit is a margin
// over that.
static const sc_time clkDivFirstEdgeLimit(160, SC_NS);
static const sc_time runWindow(500, SC_NS);

// Bound the run, long enough for the RTL checks to fire, then vote.
void clkGenExternal::stimulusThread(void)
{
    testController::GetInstance().register_test_name("clkGenRunWindow");
    wait(SC_ZERO_TIME);
    sc_signal_in_if<bool> *clkDiv = findClkDiv();
    if (clkDiv != nullptr) {
        checkClkDiv(*clkDiv);
    } else {
        wait(runWindow);
    }
    log_.logPrint(std::format("{} run window elapsed, voting end-of-test", name()),
                  LOG_IMPORTANT);
    watchDog::tickleWatchdog();
    testController::GetInstance().test_complete("clkGenRunWindow");
    eot_.setEndOfTest(true);
}

// The divider is RTL when the whole DUT or uDivider alone is verilated; its
// wrapper then carries a clkDiv signal, which must exist. In every other
// configuration clkDiv has no source and there is nothing to check.
sc_signal_in_if<bool> *clkGenExternal::findClkDiv(void)
{
    const std::string &vlInst = simController::vlInst;
    if (vlInst != "clkGen" && vlInst != "clkGen.uDivider") {
        return nullptr;
    }
    const std::string path = std::string(instanceFactory::testBenchQualStr) + vlInst + ".clkDiv";
    sc_signal_in_if<bool> *sig = dynamic_cast<sc_signal_in_if<bool> *>(sc_find_object(path.c_str()));
    Q_ASSERT(sig != nullptr, std::format("verilated divider signal {} not found", path));
    log_.logPrint(std::format("{} checking {}", name(), path), LOG_IMPORTANT);
    return sig;
}

// After the first edge, due by clkDivFirstEdgeLimit, each edge must follow
// the previous by exactly one half period; the timed wait fails a stopped clock.
void clkGenExternal::checkClkDiv(sc_signal_in_if<bool> &clkDiv)
{
    int edges = 0;
    sc_time lastEdge = sc_time_stamp();
    while (sc_time_stamp() < runWindow) {
        const sc_time limit = edges == 0 ? clkDivFirstEdgeLimit : clkDivHalfPeriod;
        wait(limit + limit, clkDiv.value_changed_event());
        Q_ASSERT(clkDiv.value_changed_event().triggered(),
                 std::format("clkDiv produced no edge within {} after {} edges", (limit + limit).to_string(), edges));
        const sc_time interval = sc_time_stamp() - lastEdge;
        if (edges == 0) {
            Q_ASSERT(interval <= limit,
                     std::format("first clkDiv edge came at {}, expected by {}", interval.to_string(), limit.to_string()));
        } else {
            Q_ASSERT(interval == clkDivHalfPeriod,
                     std::format("clkDiv half period was {}, expected {}", interval.to_string(), clkDivHalfPeriod.to_string()));
        }
        lastEdge = sc_time_stamp();
        edges++;
    }
}
