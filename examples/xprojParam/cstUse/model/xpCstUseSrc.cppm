//

// GENERATED_CODE_PARAM --block=xpCstUseSrc --mode=module
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
export module xpCstUse_xpCstUseSrc.block;
import xpCstUse_xpCstUseSrc.base;
import xpCstIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstIp_ns;
export template<typename Config>
SC_MODULE(xpCstUseSrc), public blockBase, public xpCstUseSrcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCstUseSrc);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCstUseSrcBase<Config>::CS_PIXEL_WIDTH;
    using xpCstUseSrcBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCstUseSrcBase<Config>::csPixelT;
    using typename xpCstUseSrcBase<Config>::csDutSt;

    xpCstUseSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstUseSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The assembler's use-case width, restated here independently of the YAML so
    // the assertion is a real second opinion rather than a restatement of what
    // the generator already decided. It is deliberately NOT the IP's declared
    // default of 12: a block that names an include-reached constant must resolve
    // the bound value, and this cell fails loud if it falls back to the default.
    static constexpr uint32_t USE_WIDTH = 20;
    // Sample count and the first value driven on each payload field. The pixel
    // has a non-zero high nibble so a byte-wide truncating copy shows up as a
    // mismatch, and the marker sits above the pixel so a width that resolved
    // wrongly shifts the marker rather than passing silently.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA10;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCstUseSrc<Config>::xpCstUseSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstUseSrc", name(), bbMode)
        ,xpCstUseSrcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives four samples, each stamping this block's OWN resolved width into the
// payload so every downstream block can compare it against its own. The width is
// first asserted against the value the assembler binds, so a use-case value that
// never reached this block fails loud and names both numbers.
template<typename Config>
void xpCstUseSrc<Config>::drive(void)
{
    Q_ASSERT(CS_PIXEL_WIDTH == USE_WIDTH,
        std::format("xpCstUseSrc must resolve CS_PIXEL_WIDTH to {} but resolved {}",
            USE_WIDTH, (uint64_t)CS_PIXEL_WIDTH));
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        csDutSt sample{};
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

