//

// GENERATED_CODE_PARAM --block=vliChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "vliContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlInh_vliChk.block;
import vlInh_vliChk.base;
import vlInh_vliCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlInh_vliCont_ns;
export template<typename Config>
SC_MODULE(vliChk), public blockBase, public vliChkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(vliChk);

    // inherited names usable unqualified (no Config:: / this->)
    using vliChkBase<Config>::VLI_ALGO;
    using vliChkBase<Config>::VLI_WIDTH;
    using vliChkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename vliChkBase<Config>::vliPixelT;
    using typename vliChkBase<Config>::vliSt;

    vliChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliChk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The algorithm and width the container feeding this checker was configured
    // at, read from the CHECKER's own Config. That is an independent path
    // through the generator from the one that types the leaf, so a single
    // restated literal would not do.
    static constexpr uint32_t EXPECTED_ALGO = Config::VLI_ALGO;
    static constexpr uint32_t EXPECTED_WIDTH = Config::VLI_WIDTH;
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_MARK = 0x50;
    // What the payload must be after BOTH leaves in the chain have added their
    // step to the driver's top-bit-set stimulus. Every term comes from this
    // checker's OWN Config, so the expectation is absolute: it does not ask
    // either leaf what width it thinks it is, and it is wrong for any chain
    // that lost a bit anywhere between the driver and here.
    static constexpr uint32_t DATA_MASK  = (1u << EXPECTED_WIDTH) - 1;
    static constexpr uint32_t FIRST_DATA =
        ((1u << (EXPECTED_WIDTH - 1)) + 2 * (1u << (EXPECTED_WIDTH - 3))) & DATA_MASK;
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
vliChk<Config>::vliChk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vliChk", name(), bbMode)
        ,vliChkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(check);
};

// Reads back the algorithm and width the inheriting leaves resolved and compares
// them against the ones this chain's container was configured at. Every other
// field is checked too, so a layout error stays distinguishable from a
// configuration one.
template<typename Config>
void vliChk<Config>::check(void)
{
    m_eot.registerVoter();
    vliSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} algo {} width {} data 0x{:x} mark 0x{:x}",
            this->name(), (uint64_t)sample.tag, (uint64_t)sample.algo, (uint64_t)sample.wid,
            (uint64_t)sample.data, (uint64_t)sample.mark), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i,  "vliChk tag field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "vliChk mark field mismatch");
        Q_ASSERT((uint64_t)sample.data == ((FIRST_DATA + i) & DATA_MASK),
            std::format("payload 0x{:x} expected at width {}, got 0x{:x}; a chain that "
                "lost a payload bit wraps at the wrong width",
                (FIRST_DATA + i) & DATA_MASK, EXPECTED_WIDTH, (uint64_t)sample.data));
        Q_ASSERT((uint64_t)sample.algo == EXPECTED_ALGO,
            std::format("the container was configured at algorithm {} but its leaves resolved {}",
                EXPECTED_ALGO, (uint64_t)sample.algo));
        Q_ASSERT((uint64_t)sample.wid == EXPECTED_WIDTH,
            std::format("the container was configured at width {} but its leaves resolved {}",
                EXPECTED_WIDTH, (uint64_t)sample.wid));
    }
    log_.logPrint(std::format("{} checked {} samples at algorithm {} width {}", this->name(),
        SAMPLE_COUNT, (uint64_t)sample.algo, (uint64_t)sample.wid), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}
