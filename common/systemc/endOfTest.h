#ifndef ENDOFTEST_H
#define ENDOFTEST_H
// copyright QiStor 2022

#include <systemc.h>
#include <atomic>

// global class to hold conf information
// use this class if you just want to know if the test is done or not
class endOfTestState {
    friend class endOfTest;  // Declare endOfTest as a friend class

public:
    static endOfTestState &GetInstance() {
        static endOfTestState instance;
        return instance;
    }
    endOfTestState(const endOfTestState&) = delete;
    bool isEndOfTest(void) {return done;};
    void forceEndOfTest(void) {done = true;}; // bypass counting

    sc_event eotEvent; // event to signal end of test

private:
    // for explicit use cases where you just want to explicitly declare end of test
    inline void setEndOfTest(bool isEnd)
    {
        if (isEnd) {
            endOfTestCounter++;
            if (endOfTestCounter>=voters) {
                done = true;
                eotEvent.notify(SC_ZERO_TIME); // notify the event
            }
        } else {
            endOfTestCounter--;
        }
    }
    void registerVoter(void)
    {
        voters++;
    }

    std::atomic<int> endOfTestCounter = 0;
    std::atomic<int> voters = 0;
    std::atomic<bool> done = false;
    endOfTestState() {};

};

// this class is for voters who determine if the test is ending or not
class endOfTest {
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



#endif //ENDOFTEST_H
