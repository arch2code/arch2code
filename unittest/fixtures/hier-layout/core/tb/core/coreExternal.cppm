//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=hier_tb --excludeInst=u_core --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "workerThread.h"
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module hier_core.external;
import a2c.endOfTest;
import hier_core.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header


export class coreExternal: public sc_module, public coreInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (coreExternal);

    coreExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

    // Your stimulus goes here. The generated eotThread above stops the
    // simulation when end-of-test latches, and a vote is the only thing that
    // latches it. Nothing else bounds the run: scTimeLimit is unset by default
    // and the framework watchdog's periodic wake rules out event starvation, so
    // a test that never votes hangs rather than reaching final().
    // The testbench config's createTestBench() seeds testController with the
    // placeholder test "test_replace_me", and its final() fails unless every
    // seeded test has completed. Rename the placeholder there, use the same
    // name below, and add #include "testController.h" to the user #includes slot.
    // Uncomment the lines below and the matching pair in the constructor body
    // to get a test that terminates cleanly, then drive the DUT inside the
    // thread.
    //
    // void stimulusThread(void)
    // {
    //     testController &tests = testController::GetInstance();
    //     tests.register_test_name("test_replace_me");
    //     tests.wait_test("test_replace_me");
    //
    //     // ... drive the DUT here ...
    //
    //     tests.test_complete("test_replace_me");
    //     eot_.setEndOfTest(true);
    // }
    //
    // private:
    //     endOfTest eot_{true};   // registers this thread as a voter

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

coreExternal::coreExternal(sc_module_name modulename) :
    coreInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END

    // Register your stimulus thread here (see the member slot above for the pair).
    // SC_THREAD(stimulusThread);
};
