//

// GENERATED_CODE_PARAM --block=vltTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module vlTiming_vltTop.external;
import a2c.endOfTest;
import vlTiming_vltTop.base;
import vlTiming_vlt;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace vlTiming_vlt_ns;

export class vltTopExternal: public sc_module, public vltTopInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (vltTopExternal);

    vltTopExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

    // Your tests go here. A test is a member function that takes no arguments.
    // Its name is the test name, and it must match a name in the Config's
    // set_test_names list, which sets the run order. createTestBench() seeds
    // the placeholder "test_replace_me"; rename it there and here. Register
    // each test in the constructor with ADD_TEST, and add
    // #include "testController.h" to the user #includes slot. --test runs only
    // the tests you name.
    //
    // void test_replace_me(void)
    // {
    //     // ... drive and check the DUT here ...
    // }
    //
    // The generated eotThread above stops the simulation when end-of-test
    // latches, and only a vote latches it. A voter that never votes hangs the
    // run unless --scTimeLimit is set. Vote from one thread that waits for
    // every test. Keep the voter out of the test functions: a test that is
    // not run never votes, and one that runs early can end the run before
    // later tests start.
    //
    // void endOfTestVoter(void)
    // {
    //     endOfTest eot(true);
    //     testController::GetInstance().wait_all_tests_complete();
    //     eot.setEndOfTest(true);
    // }

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

vltTopExternal::vltTopExternal(sc_module_name modulename) :
    vltTopInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END

    // Register your tests and the voter here (see the member slot above).
    // ADD_TEST(test_replace_me);
    // SC_THREAD(endOfTestVoter);
};
