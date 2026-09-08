//

// GENERATED_CODE_PARAM --block=xpTwoCtxSnk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpTwoCtx_xpTwoCtxSnk.block;
import xpTwoCtx_xpTwoCtxSnk.base;
import xpTwoCtx.xpTwoCtxSnk.config;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpTwoCtx_ns;
export template<typename Config>
SC_MODULE(xpTwoCtxSnk), public blockBase, public xpTwoCtxSnkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpTwoCtxSnk);

    // inherited names usable unqualified (no Config:: / this->)
    using xpTwoCtxSnkBase<Config>::TC_GAIN;
    using xpTwoCtxSnkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using xpTwoCtxSnkBase<Config>::TC_GAIN_X2;
    using typename xpTwoCtxSnkBase<Config>::tcValT;
    using typename xpTwoCtxSnkBase<Config>::tcSt;

    xpTwoCtxSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxSnk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpTwoCtxSnk<Config>::xpTwoCtxSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxSnk", name(), bbMode)
        ,xpTwoCtxSnkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// Snk resolves TC_GAIN through its own file's context; matching the Dut's
// value proves the two contexts agree.
template<typename Config>
void xpTwoCtxSnk<Config>::check(void)
{
    m_eot.registerVoter();
    tcSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        Q_ASSERT((uint64_t)sample.tag == FIRST_TAG + i, "xpTwoCtxSnk tag field mismatch");
        Q_ASSERT((uint64_t)sample.val == TC_GAIN_X2 + i, "xpTwoCtxSnk val field mismatch");
    }
    log_.logPrint(std::format("{} checked {} samples at TC_GAIN_X2 {}", this->name(),
        SAMPLE_COUNT, (uint64_t)TC_GAIN_X2), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

