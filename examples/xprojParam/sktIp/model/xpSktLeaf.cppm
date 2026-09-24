//

// GENERATED_CODE_PARAM --block=xpSktLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpSktIp_xpSktLeaf.block;
import xpSktIp_xpSktLeaf.base;
import xpSktIp.xpSktLeaf.config;
import xpSktIp;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpSktIp_ns;
export template<typename Config>
SC_MODULE(xpSktLeaf), public blockBase, public xpSktLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpSktLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using xpSktLeafBase<Config>::SK_PIXEL_WIDTH;
    using xpSktLeafBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpSktLeafBase<Config>::skPixelT;
    using typename xpSktLeafBase<Config>::skSampleSt;

    xpSktLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpSktLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_PIXEL = 0x10;
    void driveSamples(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpSktLeaf<Config>::xpSktLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpSktLeaf", name(), bbMode)
        ,xpSktLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(driveSamples);
};

// The model stands in for Python when the socket shell is not selected: the
// same four tagged samples the sidecar pushes.
template<typename Config>
void xpSktLeaf<Config>::driveSamples(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        skSampleSt sample{};
        sample.tag = i;
        sample.data = FIRST_PIXEL + i;
        out->push(sample);
    }
}

