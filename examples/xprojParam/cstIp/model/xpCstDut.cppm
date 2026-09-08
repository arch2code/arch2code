//

// GENERATED_CODE_PARAM --block=xpCstDut --mode=module
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
export module xpCstIp_xpCstDut.block;
import xpCstIp_xpCstDut.base;
import xpCstIp.xpCstDut.config;
import xpCstIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpCstIp_ns;
export template<typename Config>
SC_MODULE(xpCstDut), public blockBase, public xpCstDutBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpCstDut);

    // inherited names usable unqualified (no Config:: / this->)
    using xpCstDutBase<Config>::CS_PIXEL_WIDTH;
    using xpCstDutBase<Config>::in;
    using xpCstDutBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpCstDutBase<Config>::csPixelT;
    using typename xpCstDutBase<Config>::csDutSt;

    xpCstDut(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpCstDut() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // The producer's sample count and the increment this stage adds to the
    // pixel. The IP knows nothing about any use-case value, so it asserts only
    // the relation it can own: the width its producer resolved, carried in the
    // payload, must equal the width this instance resolved.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t DATA_INCREMENT = 0x20;
    void forward(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpCstDut<Config>::xpCstDut(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpCstDut", name(), bbMode)
        ,xpCstDutBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forward);
};

// Forwards every sample, adding a fixed increment to the pixel. Each sample
// carries the width its producer resolved, so the equality below is the
// end-to-end propagation check on the producer side of this block: it fails
// naming both widths if the producer and this instance did not resolve the same
// CS_PIXEL_WIDTH.
template<typename Config>
void xpCstDut<Config>::forward(void)
{
    csDutSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        Q_ASSERT((uint64_t)sample.cfg == CS_PIXEL_WIDTH,
            std::format("xpCstDut producer resolved CS_PIXEL_WIDTH {} but this instance resolved {}",
                (uint64_t)sample.cfg, (uint64_t)CS_PIXEL_WIDTH));
        sample.data = (uint64_t)sample.data + DATA_INCREMENT;
        log_.logPrint(std::format("{} forwarding tag {} cfg {} data 0x{:x} mark 0x{:x}", this->name(),
            (uint64_t)sample.tag, (uint64_t)sample.cfg, (uint64_t)sample.data, (uint64_t)sample.mark),
            LOG_IMPORTANT);
        out->push(sample);
    }
}

