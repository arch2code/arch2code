//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare --mode=module
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
export module xpTwoCtx_xpTwoCtxBare.block;
import xpTwoCtx_xpTwoCtxBare.base;
import xpTwoCtx.xpTwoCtxBare.config;
import xpTwoCtx;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpTwoCtx_ns;
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpTwoCtxBare), public blockBase, public xpTwoCtxBareBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpTwoCtxBare);

    // inherited names usable unqualified (no Config:: / this->)
    using xpTwoCtxBareBase<Config>::TC_GAIN;
    using xpTwoCtxBareBase<Config>::DP_WIDTH;
    using xpTwoCtxBareBase<Config>::litIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using xpTwoCtxBareBase<Config>::TC_GAIN_X2;
    using xpTwoCtxBareBase<Config>::DP_WIDTH_X2;
    using typename xpTwoCtxBareBase<Config>::dpPixelT;
    using typename xpTwoCtxBareBase<Config>::tcValT;
    using typename xpTwoCtxBareBase<Config>::dpSt;
    using typename xpTwoCtxBareBase<Config>::tcSt;

    xpTwoCtxBare(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxBare() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static_assert(!requires { Config::DP_ALGO; },
        "xpTwoCtxBare's Config must not carry DP_ALGO from the included context");
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_V = 0x1000;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpTwoCtxBare<Config>::xpTwoCtxBare(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxBare", name(), bbMode)
        ,xpTwoCtxBareBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// DP_WIDTH comes from the included file and TC_GAIN from this one; both must
// reach this params-only block at their bound values.
template<typename Config>
void xpTwoCtxBare<Config>::check(void)
{
    m_eot.registerVoter();
    Q_ASSERT(DP_WIDTH == 12, "xpTwoCtxBare DP_WIDTH did not resolve to the bound variant value");
    Q_ASSERT(TC_GAIN == 5, "xpTwoCtxBare TC_GAIN did not resolve to the bound variant value");
    Q_ASSERT(TC_GAIN_X2 == 10, "xpTwoCtxBare TC_GAIN_X2 did not derive from the bound TC_GAIN");
    Q_ASSERT(DP_WIDTH_X2 == 24, "xpTwoCtxBare DP_WIDTH_X2 did not derive from the bound DP_WIDTH");
    litSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        litIn->pushReceive(sample);
        litIn->ack();
        Q_ASSERT((uint64_t)sample.v == FIRST_V + i, "xpTwoCtxBare v field mismatch");
    }
    log_.logPrint(std::format("{} checked {} samples at DP_WIDTH {} TC_GAIN {}", this->name(),
        SAMPLE_COUNT, (uint64_t)DP_WIDTH, (uint64_t)TC_GAIN), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

