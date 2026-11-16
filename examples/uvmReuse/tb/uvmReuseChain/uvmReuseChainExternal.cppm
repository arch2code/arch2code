//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuse_tb --excludeInst=u_uvmReuseChain --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module uvmReuse_uvmReuseChain.external;
import a2c.endOfTest;
import uvmReuse_uvmReuseChain.base;
import uvmReuse_uvmReuseDrv.base;
import uvmReuse_uvmReuseSink.base;
import uvmReuse.uvmReuseChain.config;
import uvmReuseLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace uvmReuseLeaf_ns;

export class uvmReuseChainExternal: public sc_module, public uvmReuseChainInverted<uvmReuse_uvmReuseChainV8Config> {

    logBlock log_;

public:

    std::shared_ptr<uvmReuseDrvBase> uDrv;
    std::shared_ptr<uvmReuseSinkBase> uSink;

    SC_HAS_PROCESS (uvmReuseChainExternal);

    uvmReuseChainExternal(sc_module_name modulename);

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

uvmReuseChainExternal::uvmReuseChainExternal(sc_module_name modulename) :
    uvmReuseChainInverted<uvmReuse_uvmReuseChainV8Config>("Chnl"),
    log_(name())

   ,uDrv(std::dynamic_pointer_cast<uvmReuseDrvBase>(instanceFactory::createInstance(name(), "uDrv", "uvmReuseDrv", "", "uvmReuse")))
   ,uSink(std::dynamic_pointer_cast<uvmReuseSinkBase>(instanceFactory::createInstance(name(), "uSink", "uvmReuseSink", "", "uvmReuse")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uDrv->out(in);
    uSink->in(out);
    uDrv->apbReg(apbReg);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END

    // Register your tests and the voter here (see the member slot above).
    // ADD_TEST(test_replace_me);
    // SC_THREAD(endOfTestVoter);
};
