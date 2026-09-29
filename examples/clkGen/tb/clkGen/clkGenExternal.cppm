//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=clkGen --mode=module
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
#include "testController.h"
#include "q_assert.h"
#include "simController.h"
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module clkGen.external;
import a2c.endOfTest;
import clkGen.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import clkGen;
// GENERATED_CODE_BEGIN --template=tbExternal --section=header


export class clkGenExternal: public sc_module, public clkGenInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (clkGenExternal);

    clkGenExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

    // clkGen has no boundary ports for the External to drive: the divider
    // free-runs off clkRef/rstRef_n and the consumer free-runs off the
    // divided clock it is handed. The External owns the run window and, when
    // a verilated divider is present, checks the clkDiv it produces. Models
    // are unclocked, so a model-only run has no clkDiv to check. The
    // synchronised reset and the consumer are internal to clkGen's RTL and
    // are checked there.
    void stimulusThread(void);

private:
    sc_signal_in_if<bool> *findClkDiv(void);
    void checkClkDiv(sc_signal_in_if<bool> &clkDiv);

    endOfTest eot_{true};   // registers this thread as a voter
};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

clkGenExternal::clkGenExternal(sc_module_name modulename) :
    clkGenInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END

    SC_THREAD(stimulusThread);
};

// The clkRef period of prj/yaml/project.yaml's clocks:. The generated
// co-simulation wrapper keeps it private, so it is restated here.
static const sc_time clkRefPeriod(10, SC_NS);
// clkDivider toggles clkDiv every CLK_GEN_DIV_HALF_COUNT clkRef cycles.
static constexpr unsigned divPeriod = 2 * clkGen_ns::CLK_GEN_DIV_HALF_COUNT;   // clkRef cycles per clkDiv period
static const sc_time clkDivHalfPeriod = clkGen_ns::CLK_GEN_DIV_HALF_COUNT * clkRefPeriod;
// The first clkDiv edge is expected one half period after rstRef_n releases,
// 3 clkRef cycles in. The limit is two clkDiv periods.
static const sc_time clkDivFirstEdgeLimit = 2 * divPeriod * clkRefPeriod;
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
