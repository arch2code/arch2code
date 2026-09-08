//

// GENERATED_CODE_PARAM --block=xpDpChk --mode=module
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
export module xpDpTop_xpDpChk.block;
import xpDpTop_xpDpChk.base;
import xpDpTop.xpDpChk.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpChk), public blockBase, public xpDpChkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpChk);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpChkBase<Config>::DP_ALGO;
    using xpDpChkBase<Config>::DP_WIDTH;
    using xpDpChkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpChkBase<Config>::dpPixelT;
    using typename xpDpChkBase<Config>::dpSt;

    xpDpChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpChk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The algorithm THIS CUSTOMER asked the ISP's debayer to be configured at.
    // Read from the CHECKER's own Config, which the customer declares directly,
    // so it is an independent path through the generator from the one that
    // reaches the leaf nested two project levels down. The chains expect
    // different algorithms, so this cannot be a single restated literal.
    static constexpr uint32_t CUSTOMER_ALGO = Config::DP_ALGO;
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0x31;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpChk<Config>::xpDpChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpChk", name(), bbMode)
        ,xpDpChkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// Reads back the algorithm the nested leaf instances resolved and compares it
// against the one this customer declared. Every other field is checked too, so a
// layout error is distinguishable from a configuration one.
template<typename Config>
void xpDpChk<Config>::check(void)
{
    m_eot.registerVoter();
    dpSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} algo {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.algo, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i,  "xpDpChk tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + i, "xpDpChk data field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "xpDpChk mark field mismatch");
        Q_ASSERT((uint64_t)sample.algo == CUSTOMER_ALGO,
            std::format("the customer declared the leaf at algorithm {} but the leaf resolved {}",
                CUSTOMER_ALGO, (uint64_t)sample.algo));
    }
    log_.logPrint(std::format("{} checked {} samples at algorithm {}", this->name(),
        SAMPLE_COUNT, (uint64_t)sample.algo), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

