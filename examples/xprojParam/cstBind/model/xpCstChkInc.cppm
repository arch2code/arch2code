//

// GENERATED_CODE_PARAM --block=xpCstChkInc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpCstIpVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpCstBind_xpCstChkInc.block;
import xpCstBind_xpCstChkInc.base;
import xpCstIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstIp_ns;
export template<typename Config>
SC_MODULE(xpCstChkInc), public blockBase, public xpCstChkIncBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCstChkInc);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCstChkIncBase<Config>::CS_PIXEL_WIDTH;
    using xpCstChkIncBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCstChkIncBase<Config>::csPixelT;
    using typename xpCstChkIncBase<Config>::csDutSt;

    xpCstChkInc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstChkInc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Independent statement of the two widths this assembler binds; see the
    // stimulus block for why the numbers are restated rather than read back.
    static constexpr uint32_t DFLT_WIDTH = 12;
    static constexpr uint32_t USE_WIDTH = 20;
    // Mirror of the producer's field bases plus the increment the DUT adds, so
    // every field of every sample is checked end to end.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    static constexpr uint32_t DATA_INCREMENT = 0x20;
    std::string m_variant;
    uint32_t expectedWidth(void) const { return m_variant == "use" ? USE_WIDTH : DFLT_WIDTH; }
    void check(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCstChkInc<Config>::xpCstChkInc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstChkInc", name(), bbMode)
        ,xpCstChkIncBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    m_variant = variant;
    SC_THREAD(check);
};

// Checks every field of every sample, then votes the test done. Two assertions
// carry the propagation claim: this block's own resolved width against the value
// its variant binds, and the width the producing chain stamped into the payload
// against this block's own.
template<typename Config>
void xpCstChkInc<Config>::check(void)
{
    Q_ASSERT(CS_PIXEL_WIDTH == expectedWidth(),
        std::format("xpCstChkInc variant '{}' must resolve CS_PIXEL_WIDTH to {} but resolved {}",
            m_variant, expectedWidth(), (uint64_t)CS_PIXEL_WIDTH));
    m_eot.registerVoter();
    csDutSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} received tag {} cfg {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.cfg, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.cfg == CS_PIXEL_WIDTH,
            std::format("xpCstChkInc chain resolved its pixel width to {} but this instance resolved {}",
                (uint64_t)sample.cfg, (uint64_t)CS_PIXEL_WIDTH));
        Q_ASSERT((uint64_t)sample.tag  == FIRST_TAG + i, "xpCstChkInc tag field mismatch");
        Q_ASSERT((uint64_t)sample.data == FIRST_DATA + DATA_INCREMENT + i, "xpCstChkInc data field mismatch");
        Q_ASSERT((uint64_t)sample.mark == FIRST_MARK + i, "xpCstChkInc mark field mismatch");
    }
    log_.logPrint(std::format("{} checked {} samples at pixel width {}", this->name(),
        SAMPLE_COUNT, (uint64_t)CS_PIXEL_WIDTH), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

