//

// GENERATED_CODE_PARAM --block=xpSinkUniq --mode=module
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
export module xpSink_xpSinkUniq.block;
import xpSink_xpSinkUniq.base;
import xpSink.xpSinkUniq.config;
import xpSink_xpSinkUniq;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpSink_xpSinkUniq_ns;
export template<typename Config>
SC_MODULE(xpSinkUniq), public blockBase, public xpSinkUniqBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpSinkUniq);

    // inherited names usable unqualified (no Config:: / this->)
    using xpSinkUniqBase<Config>::SK_PIXEL_WIDTH;
    using xpSinkUniqBase<Config>::videoIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpSinkUniqBase<Config>::skPixelT;
    using typename xpSinkUniqBase<Config>::skVideoSt;

    xpSinkUniq(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSinkUniq() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Sample count and first value the source plus the middle stage produce.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t EXPECTED_FIRST_PIXEL = 0x30;
    void checkVideo(void);
    endOfTest m_eot;
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpSinkUniq<Config>::xpSinkUniq(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpSinkUniq", name(), bbMode)
        ,xpSinkUniqBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(checkVideo);
};

// Checks every sample the chain delivers against the value the source and the
// middle stage together produce, then ends the test.
template<typename Config>
void xpSinkUniq<Config>::checkVideo(void)
{
    Q_ASSERT(SK_PIXEL_WIDTH == 8, "xpSinkUniq SK_PIXEL_WIDTH must resolve to the bound variant value 8");
    m_eot.registerVoter();
    skVideoSt sample;
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        videoIn->pushReceive(sample);
        videoIn->ack();
        log_.logPrint(std::format("{} received tag {} pixel 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.data), LOG_IMPORTANT);
        Q_ASSERT((uint64_t)sample.tag == i, "chain delivered samples out of order");
        Q_ASSERT((uint64_t)sample.data == EXPECTED_FIRST_PIXEL + i, "chain delivered an unexpected pixel value");
    }
    log_.logPrint(std::format("{} checked {} samples across the chain", this->name(),
        SAMPLE_COUNT), LOG_IMPORTANT);
    m_eot.setEndOfTest(true);
}

