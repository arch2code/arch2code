#ifndef TWOCLK_EXTERNAL_H
#define TWOCLK_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=twoClk_tb --excludeInst=u_twoClk
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import twoClk.base;

class twoClkExternal: public sc_module, public twoClkInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (twoClkExternal);

    twoClkExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END

    // twoClk has no boundary ports, so there is nothing for the External to
    // drive: the DUT's own producer is the stimulus and its own sink is the
    // checker. What the External owns is the run window. End-of-test needs
    // EVERY registered voter, and only the block models that are actually
    // elaborated register one, so this voter is what lets the same testbench
    // terminate in all four configurations while still requiring the surviving
    // block model(s) to have seen their traffic first:
    //   model only               - producer + sink + this voter
    //   --vlInst twoClk.uIpSrc   - sink + this voter (proves RTL -> model)
    //   --vlInst twoClk.uSink    - producer + this voter (proves model -> RTL)
    //   --vlInst twoClk          - this voter alone (elaborate/clock/run only)
    void stimulusThread(void);

private:
    endOfTest eot_{true};

};

#endif /* TWOCLK_EXTERNAL_H */
