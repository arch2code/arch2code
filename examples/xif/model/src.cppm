//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=src --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "bitTwiddling.h"
#include "q_assert.h"
#include <algorithm>
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xifVariantConfig.h"
// GENERATED_CODE_END
// user #includes here
#include "testController.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xif_src.block;
import xif_src.base;
import xif;
using namespace xif_ns;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
export template<typename Config>
SC_MODULE(src), public blockBase, public srcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(src);

    // inherited names usable unqualified (no Config:: / this->)
    using srcBase<Config>::DATA_WIDTH;
    using srcBase<Config>::FRAME_HEIGHT;
    using srcBase<Config>::FRAME_WIDTH;
    using srcBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename srcBase<Config>::streamDataT;
    using typename srcBase<Config>::streamSt;

    src(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~src() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void outThread(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
src<Config>::src(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("src", name(), bbMode)
        ,srcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(outThread);
};

#define XIF_LOOPCOUNT 16

// Drive a sequence of boundary-typed payloads out on `out`. The cross-interface
// thunker adapts each streamBndrySt onto the DUT's streamSt<Config> input.
template<typename Config>
void src<Config>::outThread(void)
{
    std::string test_name = "test_stream";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < XIF_LOOPCOUNT; loop++)
    {
        streamBndrySt t;
        t.data = loop & 0xFFFF;
        out->push(t);
    }
    log_.logPrint(std::format("Test {} complete (src)", test_name), LOG_ALWAYS);
    controller.test_complete(test_name);
}

