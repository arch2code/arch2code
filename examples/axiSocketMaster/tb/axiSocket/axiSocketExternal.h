#ifndef AXISOCKET_EXTERNAL_H
#define AXISOCKET_EXTERNAL_H
// 

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import axiSocketMaster_axiSocket.base;
import axiSocketMaster_tb;
using namespace axiSocketMaster_tb_ns;

class axiSocketExternal: public sc_module, public axiSocketInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (axiSocketExternal);

    axiSocketExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END

    // Your stimulus goes here. The generated eotThread above stops the
    // simulation when end-of-test latches, and the testbench Config asserts
    // that it did, so a test that never votes ends by aborting in final().
    // Uncomment the two lines below and the matching pair in the .cpp to get a
    // test that terminates cleanly, then drive the DUT inside the thread.
    //
    // void stimulusThread(void);
    //
    // private:
    //     endOfTest eot_{true};   // registers this thread as a voter

};

#endif /* AXISOCKET_EXTERNAL_H */
