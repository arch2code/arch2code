//

// GENERATED_CODE_PARAM --block=xpDpLeaf --mode=module
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
export module xpDpLeaf.block;
import xpDpLeaf.base;
import xpDpLeaf.xpDpLeaf.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpLeaf), public blockBase, public xpDpLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpLeafBase<Config>::DP_ALGO;
    using xpDpLeafBase<Config>::DP_WIDTH;
    using xpDpLeafBase<Config>::in;
    using xpDpLeafBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpLeafBase<Config>::dpPixelT;
    using typename xpDpLeafBase<Config>::dpSt;

    xpDpLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Number of samples the chain carries end to end.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    void forward(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpLeaf<Config>::xpDpLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpLeaf", name(), bbMode)
        ,xpDpLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forward);
};

// Stamps this instance's own resolved DP_ALGO into every sample it forwards, so
// a consumer anywhere downstream can read back the algorithm this leaf was
// actually configured at. The leaf asserts nothing about the value: it has no
// way to know which consumer configured it.
template<typename Config>
void xpDpLeaf<Config>::forward(void)
{
    dpSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        sample.algo = DP_ALGO;
        log_.logPrint(std::format("{} forwarding tag {} at algo {}", this->name(),
            (uint64_t)sample.tag, (uint64_t)DP_ALGO), LOG_IMPORTANT);
        out->push(sample);
    }
}

