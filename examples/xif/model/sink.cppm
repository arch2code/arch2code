//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=sink --mode=module
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
export module xif_sink.block;
import xif_sink.base;
import xif;
// GENERATED_CODE_END
// user imports here
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xif_ns;
export template<typename Config>
SC_MODULE(sink), public blockBase, public sinkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(sink);

    // inherited names usable unqualified (no Config:: / this->)
    using sinkBase<Config>::DATA_WIDTH;
    using sinkBase<Config>::FRAME_HEIGHT;
    using sinkBase<Config>::FRAME_WIDTH;
    using sinkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename sinkBase<Config>::streamDataT;
    using typename sinkBase<Config>::streamSt;

    sink(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~sink() override = default;

    // GENERATED_CODE_END
    // block implementation members
    void inThread(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
sink<Config>::sink(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("sink", name(), bbMode)
        ,sinkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(inThread);
};

#define XIF_LOOPCOUNT 16

// Receive the boundary-typed payload stream (adapted from the DUT's
// streamSt<Config> output by the sink-side thunker) and verify each value.
template<typename Config>
void sink<Config>::inThread(void)
{
    std::string test_name = "test_stream";
    testController &controller = testController::GetInstance();
    controller.register_test_name(test_name);
    controller.wait_test(test_name);
    for (int loop = 0; loop < XIF_LOOPCOUNT; loop++)
    {
        streamBndrySt t;
        in->pushReceive(t);
        in->ack();
        Q_ASSERT(t.data == (uint32_t)(loop & 0xFFFF), "sink stream data mismatch");
    }
    log_.logPrint(std::format("Test {} complete (sink)", test_name), LOG_ALWAYS);
    controller.test_complete(test_name);
}

