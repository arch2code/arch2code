//

// GENERATED_CODE_PARAM --block=xpInhChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpInhContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpInhVar_xpInhChk.block;
import xpInhVar_xpInhChk.base;
import xpInhVar_xpInhCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpInhVar_xpInhCont_ns;
export template<typename Config>
SC_MODULE(xpInhChk), public blockBase, public xpInhChkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpInhChk);

    // inherited names usable unqualified (no Config:: / this->)
    using xpInhChkBase<Config>::INH_ALGO;
    using xpInhChkBase<Config>::INH_WIDTH;
    using xpInhChkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpInhChkBase<Config>::inhPixelT;
    using typename xpInhChkBase<Config>::inhSt;

    xpInhChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhChk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The algorithm the container feeding this checker was configured at, read
    // from the CHECKER's own Config. That is an independent path through the
    // generator from the one that types the leaf, so a single restated literal
    // would not do.
    static constexpr uint32_t EXPECTED_ALGO = Config::INH_ALGO;
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0x31;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpInhChk<Config>::xpInhChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpInhChk", name(), bbMode)
        ,xpInhChkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// Reads back the algorithm the inheriting leaves resolved and compares it
// against the one this chain's container was configured at. Every other field is
// checked too, so a layout error stays distinguishable from a configuration one.
template<typename Config>
void xpInhChk<Config>::check(void)
{
    m_eot.registerVoter();
    inhSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} algo {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.algo, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i,  "xpInhChk tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + i, "xpInhChk data field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "xpInhChk mark field mismatch");
        Q_ASSERT((uint64_t)sample.algo == EXPECTED_ALGO,
            std::format("the container was configured at algorithm {} but its leaves resolved {}",
                EXPECTED_ALGO, (uint64_t)sample.algo));
    }
    log_.logPrint(std::format("{} checked {} samples at algorithm {}", this->name(),
        SAMPLE_COUNT, (uint64_t)sample.algo), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

