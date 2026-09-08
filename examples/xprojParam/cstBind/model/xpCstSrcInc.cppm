//

// GENERATED_CODE_PARAM --block=xpCstSrcInc --mode=module
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
export module xpCstBind_xpCstSrcInc.block;
import xpCstBind_xpCstSrcInc.base;
import xpCstBind.xpCstSrcInc.config;
import xpCstBind_xpCstSup;
import xpCstIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstBind_xpCstSup_ns;
using namespace xpCstIp_ns;
export template<typename Config>
SC_MODULE(xpCstSrcInc), public blockBase, public xpCstSrcIncBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCstSrcInc);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCstSrcIncBase<Config>::CS_PIXEL_WIDTH;
    using xpCstSrcIncBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCstSrcIncBase<Config>::csPixelT;
    using typename xpCstSrcIncBase<Config>::csIncPixelT;
    using typename xpCstSrcIncBase<Config>::csDutSt;
    using typename xpCstSrcIncBase<Config>::csIncSt;

    xpCstSrcInc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstSrcInc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The two widths this assembler binds, restated here independently of the
    // YAML so the assertion is a real second opinion: DFLT_WIDTH is the IP's own
    // declared CS_PIXEL_WIDTH and USE_WIDTH is the assembler's CS_USE_WIDTH.
    static constexpr uint32_t DFLT_WIDTH = 12;
    static constexpr uint32_t USE_WIDTH = 20;
    // Sample count and the first value driven on each payload field. The pixel
    // has a non-zero high nibble so a byte-wide truncating copy shows up as a
    // mismatch, and the marker sits above the pixel so a width that resolved
    // wrongly shifts the marker rather than passing silently.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    std::string m_variant;
    uint32_t expectedWidth(void) const { return m_variant == "use" ? USE_WIDTH : DFLT_WIDTH; }
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCstSrcInc<Config>::xpCstSrcInc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstSrcInc", name(), bbMode)
        ,xpCstSrcIncBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    m_variant = variant;
    SC_THREAD(drive);
};

// Drives four samples, each stamping this block's OWN resolved width into the
// payload so every downstream block can compare it against its own. The width is
// first asserted against the value this instance's variant binds, so a use-case
// value that never reached this block fails loud and names both numbers.
template<typename Config>
void xpCstSrcInc<Config>::drive(void)
{
    Q_ASSERT(CS_PIXEL_WIDTH == expectedWidth(),
        std::format("xpCstSrcInc variant '{}' must resolve CS_PIXEL_WIDTH to {} but resolved {}",
            m_variant, expectedWidth(), (uint64_t)CS_PIXEL_WIDTH));
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        csIncSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.cfg  = CS_PIXEL_WIDTH;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
        log_.logPrint(std::format("{} drove tag {} cfg {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.cfg, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
    }
}

