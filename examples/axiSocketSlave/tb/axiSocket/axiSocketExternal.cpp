#include "workerThread.h"

// GENERATED_CODE_PARAM --block=axiSocket

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
#include "axiSocketExternal.h"

axiSocketExternal::axiSocketExternal(sc_module_name modulename) :
    axiSocketInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    // Register your stimulus thread here (see the header for the pair).
    // SC_THREAD(stimulusThread);
}

// Minimal test that terminates cleanly. Uncomment together with the header
// declarations, then replace the body with real stimulus. Voting end-of-test is
// what wakes the generated eotThread and stops the simulation; without a vote
// the run aborts on the end-of-test assertion in the testbench Config.
//
// void axiSocketExternal::stimulusThread(void)
// {
//     wait(SC_ZERO_TIME);
//
//     // ... drive the DUT here ...
//
//     eot_.setEndOfTest(true);
// }
