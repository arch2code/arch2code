//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=dut --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xifVariantConfig.h"
// GENERATED_CODE_END
// user #includes here
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xif_dut.block;
import xif_dut.base;
import xif;
// GENERATED_CODE_END
// user imports here
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xif_ns;
export template<typename Config>
SC_MODULE(dut), public blockBase, public dutBase<Config>
{
private:

public:
    SC_HAS_PROCESS(dut);

    // inherited names usable unqualified (no Config:: / this->)
    using dutBase<Config>::DATA_WIDTH;
    using dutBase<Config>::streamIn;
    using dutBase<Config>::streamOut;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename dutBase<Config>::streamDataT;
    using typename dutBase<Config>::streamSt;

    dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~dut() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void fwdThread(void);
    void doneTest(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
dut<Config>::dut(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("dut", name(), bbMode)
        ,dutBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(fwdThread);
    SC_THREAD(doneTest);
};

// Forward every received payload from streamIn to streamOut. Both ports are
// streamSt<Config>; the boundary thunkers on the src and sink sides adapt to
// the plain streamBndrySt carried by the edge blocks.
template<typename Config>
void dut<Config>::fwdThread(void)
{
    while (true)
    {
        streamSt s;
        streamIn->pushReceive(s);
        streamIn->ack();
        streamOut->push(s);
    }
}

// End-of-test bridge: wait for all self-driving tests to complete, then vote
// end-of-test so dutExternal::eotThread can sc_stop() the simulation.
template<typename Config>
void dut<Config>::doneTest(void)
{
    endOfTest eot;
    eot.registerVoter();
    testController::GetInstance().wait_all_tests_complete();
    eot.setEndOfTest(true);
}

