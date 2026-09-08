//

// GENERATED_CODE_PARAM --block=xpGainUniq --mode=module
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
export module xpGain_xpGainUniq.block;
import xpGain_xpGainUniq.base;
import xpGain.xpGainUniq.config;
import xpGain_xpGainUniq;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpGain_xpGainUniq_ns;
export template<typename Config>
SC_MODULE(xpGainUniq), public blockBase, public xpGainUniqBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpGainUniq);

    // inherited names usable unqualified (no Config:: / this->)
    using xpGainUniqBase<Config>::GN_PIXEL_WIDTH;
    using xpGainUniqBase<Config>::videoOut;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpGainUniqBase<Config>::gnPixelT;
    using typename xpGainUniqBase<Config>::gnVideoSt;

    xpGainUniq(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpGainUniq() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and first pixel value the downstream stages expect.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_PIXEL = 0x10;
    void driveVideo(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpGainUniq<Config>::xpGainUniq(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpGainUniq", name(), bbMode)
        ,xpGainUniqBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveVideo);
};

// Emits SAMPLE_COUNT tagged pixels. The width assertion pins the bound variant,
// so a parameter that stops reaching this stage across the project boundary
// fails here rather than silently truncating downstream.
template<typename Config>
void xpGainUniq<Config>::driveVideo(void)
{
    Q_ASSERT(GN_PIXEL_WIDTH == 8, "xpGainUniq GN_PIXEL_WIDTH must resolve to the bound variant value 8");
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        gnVideoSt sample{};
        sample.tag = i;
        sample.data = FIRST_PIXEL + i;
        log_.logPrint(std::format("{} pushing tag {} pixel 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data), LOG_IMPORTANT);
        videoOut->push(sample);
    }
}

