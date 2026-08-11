//

// GENERATED_CODE_PARAM --block=xpFilterUniq --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpFilterUniqVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpFilter_xpFilterUniq.block;
import xpFilter_xpFilterUniq.base;
import xpFilter_xpFilterUniq;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpFilter_xpFilterUniq_ns;
export template<typename Config>
SC_MODULE(xpFilterUniq), public blockBase, public xpFilterUniqBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpFilterUniq);

    // inherited names usable unqualified (no Config:: / this->)
    using xpFilterUniqBase<Config>::FL_PIXEL_WIDTH;
    using xpFilterUniqBase<Config>::videoIn;
    using xpFilterUniqBase<Config>::videoOut;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpFilterUniqBase<Config>::flPixelT;
    using typename xpFilterUniqBase<Config>::flVideoSt;

    xpFilterUniq(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpFilterUniq() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Offset this stage adds to every pixel it forwards.
    static constexpr uint32_t PIXEL_OFFSET = 0x20;
    void filterVideo(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpFilterUniq<Config>::xpFilterUniq(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpFilterUniq", name(), bbMode)
        ,xpFilterUniqBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(filterVideo);
};

// Adds a fixed offset to every arriving pixel and forwards it, so the sink's
// expected values are only reachable if the payload survives both project hops.
template<typename Config>
void xpFilterUniq<Config>::filterVideo(void)
{
    Q_ASSERT(FL_PIXEL_WIDTH == 8, "xpFilterUniq FL_PIXEL_WIDTH must resolve to the bound variant value 8");
    flVideoSt sample;
    while (true) {
        videoIn->pushReceive(sample);
        videoIn->ack();
        sample.data = sample.data + PIXEL_OFFSET;
        log_.logPrint(std::format("{} forwarding tag {} pixel 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data), LOG_IMPORTANT);
        videoOut->push(sample);
    }
}

