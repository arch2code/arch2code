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
    // Zero means nothing in the run is able to vote it to an end. Registration
    // is lazy for firmware and host-thread voters, so a zero read is only
    // meaningful once the run has had wall-clock time to register them.
    int registeredVoters(void) {return voters;};

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
        // Re-evaluate once now that latching is permitted, so a vote cast while
        // the gate was closed still latches. A project that has never voted is
        // ignored here (see evaluateEndOfTest).
        evaluateEndOfTest();
    }

    sc_event eotEvent; // event to signal end of test

private:
    // for explicit use cases where you just want to explicitly declare end of test
    inline void setEndOfTest(bool isEnd)
    {
        // Activity is recorded at vote time, never at evaluation time, so it
        // survives the closed startup gate (see evaluateEndOfTest).
        voteCast = true;
        if (isEnd) {
            endOfTestCounter++;
        } else {
            endOfTestCounter--;
        }
        evaluateEndOfTest();
    }
    // Latch and notify end-of-test only once startup is complete, at least one
    // voter has cast a vote, and the vote threshold is met. Called on each vote
    // change and once when startup completes, so an end-of-test is never missed:
    // a self-driving model-only test can register its voter, run to completion
    // and vote done entirely inside startupDelay, and that vote must still latch
    // when the gate opens.
    //
    // Invariant: a cast vote is the evidence that the test ran, and it is
    // recorded when the vote happens. Do NOT infer activity from
    // endOfTestCounter < voters here - evaluation does not run while the gate is
    // closed, so a test that finishes before the gate opens never presents that
    // condition and would never latch. voteCast is what stops the gate opening
    // from latching a project that has never voted at all, for which voters == 0
    // makes endOfTestCounter >= voters trivially true; such a project ends only
    // under an explicit scTimeLimit - the framework watchdog's periodic wake
    // keeps events queued, so event starvation cannot end it. Not latching before
    // startupComplete is therefore the only barrier against the transient
    // all-idle threshold seen while lazily-registered voters (firmware and
    // runtime host threads) are still registering, which is exactly what
    // startupDelay is sized for.
    void evaluateEndOfTest(void)
    {
        if (!startupComplete) return; // do not latch or notify during startup
        if (voteCast && endOfTestCounter>=voters) {
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
    std::atomic<bool> voteCast = false;
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
