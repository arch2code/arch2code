//

// GENERATED_CODE_PARAM --block=xpInhLeaf --mode=module
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
export module xpInhVar_xpInhLeaf.block;
import xpInhVar_xpInhLeaf.base;
import xpInhVar.xpInhLeaf.config;
import xpInhVar_xpInhCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpInhVar_xpInhCont_ns;
export template<typename Config>
SC_MODULE(xpInhLeaf), public blockBase, public xpInhLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpInhLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using xpInhLeafBase<Config>::INH_ALGO;
    using xpInhLeafBase<Config>::INH_WIDTH;
    using xpInhLeafBase<Config>::out;
    using xpInhLeafBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpInhLeafBase<Config>::inhPixelT;
    using typename xpInhLeafBase<Config>::inhSt;

    xpInhLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpInhLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Number of samples the chain carries end to end.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    void forward(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpInhLeaf<Config>::xpInhLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpInhLeaf", name(), bbMode)
        ,xpInhLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forward);
};

// Stamps the INH_ALGO of the Config this instance was actually built at into
// every sample it forwards. The leaf declares no variant of its own: its Config
// is whatever its container was instantiated at, so this value is the only
// observable answer to "which member of the leaf's type family did the factory
// hand back".
template<typename Config>
void xpInhLeaf<Config>::forward(void)
{
    inhSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        sample.algo = INH_ALGO;
        log_.logPrint(std::format("{} forwarding tag {} at algo {}", this->name(),
            (uint64_t)sample.tag, (uint64_t)INH_ALGO), LOG_IMPORTANT);
        out->push(sample);
    }
}

