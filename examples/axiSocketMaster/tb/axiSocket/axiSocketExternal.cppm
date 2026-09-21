//

// GENERATED_CODE_PARAM --block=axiSocket --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module axiSocketMaster_axiSocket.external;
import a2c.endOfTest;
import axiSocketMaster_axiSocket.base;
import axiSocketMaster_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace axiSocketMaster_tb_ns;

export class axiSocketExternal: public sc_module, public axiSocketInverted {

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
    // external implementation members

    // Your stimulus goes here. The generated eotThread above stops the
    // simulation when end-of-test latches, and the testbench Config asserts
    // that it did, so a test that never votes ends by aborting in final().
    // Uncomment the lines below and the matching pair in the constructor body
    // to get a test that terminates cleanly, then drive the DUT inside the
    // thread.
    //
    // void stimulusThread(void)
    // {
    //     wait(SC_ZERO_TIME);
    //
    //     // ... drive the DUT here ...
    //
    //     eot_.setEndOfTest(true);
    // }
    //
    // private:
    //     endOfTest eot_{true};   // registers this thread as a voter

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

axiSocketExternal::axiSocketExternal(sc_module_name modulename) :
    axiSocketInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END

    // Register your stimulus thread here (see the member slot above for the pair).
    // SC_THREAD(stimulusThread);
};

