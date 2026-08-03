// copyright QiStor 2022
module;
#include <systemc.h>
#include <atomic>

export module a2c.endOfTest;

// global class to hold conf information
// use this class if you just want to know if the test is done or not
//
// This is a single C++20 module entity: every consumer `import a2c.endOfTest;`
// so `GetInstance()` yields exactly ONE instance across all translation units
// and module boundaries. Do NOT reintroduce a textual `endOfTest.h` include in a
// named-module purview - that would attach a private per-module instance and
// silently break end-of-test voting.
export class endOfTestState {
    friend class endOfTest;  // Declare endOfTest as a friend class

public:
    static endOfTestState &GetInstance() {
        static endOfTestState instance;
        return instance;
    }
    endOfTestState(const endOfTestState&) = delete;
    bool isEndOfTest(void) {return done;};
    void forceEndOfTest(void) {done = true;}; // bypass counting

    // General framework startup gate. End-of-test must not latch before the
    // framework has finished starting up: at sim time 0, before every voter has
    // registered (framework voters register lazily - e.g. firmware and runtime
    // host threads), the few registered voters can all be idle and momentarily
    // trip the threshold, which would otherwise latch `done` permanently and
    // stop the simulation before it has begun. sc_main flips this true once,
    // after simController::startupDelay, for every project (see the framework
    // startup process in scmain/main.cpp). This is independent of the
    // ascari/aura-only startupPhase/setStartupVoters barrier.
    void setStartupComplete(void)
    {
        startupComplete = true;
        // Re-evaluate once now that latching is permitted. This only latches if
        // the test has already been active and every voter is now idle; a
        // startup transient (all registered voters momentarily idle) is ignored
        // because the test was never active.
        evaluateEndOfTest();
    }

    sc_event eotEvent; // event to signal end of test

private:
    // for explicit use cases where you just want to explicitly declare end of test
    inline void setEndOfTest(bool isEnd)
    {
        if (isEnd) {
            endOfTestCounter++;
        } else {
            endOfTestCounter--;
        }
        evaluateEndOfTest();
    }
    // Latch and notify end-of-test only once startup is complete, the test has
    // actually run, and the vote threshold is met. Called on each vote change
    // and once when startup completes, so a genuine end-of-test after startup is
    // never missed.
    //
    // endOfTestCounter < voters means at least one voter is busy (a busy vote
    // decrements the counter; an idle/done vote increments it toward voters), so
    // it is direct evidence the test became active. Requiring this before
    // latching prevents the transient all-idle threshold that occurs while the
    // framework is still starting up and lazily-registered voters (firmware and
    // runtime host threads) have not yet begun driving stimulus - a window that
    // overlaps startupComplete because stimulus release is itself keyed to
    // startupDelay. A project that never becomes active (e.g. no voters) never
    // latches here and instead terminates by scTimeLimit or event starvation.
    void evaluateEndOfTest(void)
    {
        if (!startupComplete) return; // do not latch or notify during startup
        if (endOfTestCounter<voters) hasBeenActive = true; // the test actually ran
        if (hasBeenActive && endOfTestCounter>=voters) {
            done = true;
            eotEvent.notify(SC_ZERO_TIME); // notify the event
        }
    }
    void registerVoter(void)
    {
        voters++;
    }

    std::atomic<int> endOfTestCounter = 0;
    std::atomic<int> voters = 0;
    std::atomic<bool> done = false;
    std::atomic<bool> startupComplete = false;
    std::atomic<bool> hasBeenActive = false;
    endOfTestState() {};

};

// this class is for voters who determine if the test is ending or not
export class endOfTest {
public:
    endOfTest() {};
    endOfTest(bool registerVoter_) {
        if (registerVoter_) {
            eot.registerVoter();
        }
    }
    // allow stateless management of end of test in a module
    inline void setEndOfTest(bool isEnd)
    {
        // check for change of state
        if (isEnd!=voterState) {
            voterState = isEnd;
            eot.setEndOfTest(isEnd);
        }
    }
    inline bool isEndOfTest(void) {return eot.isEndOfTest();}
    void registerVoter(void) { eot.registerVoter(); }

private:
    bool voterState = false;
    endOfTestState &eot = endOfTestState::GetInstance();
};
