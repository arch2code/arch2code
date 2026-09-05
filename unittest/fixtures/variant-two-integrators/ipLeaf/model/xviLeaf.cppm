//

// GENERATED_CODE_PARAM --block=xviLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xviLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xviLeaf.block;
import xviLeaf.base;
import xviLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xviLeaf_ns;
export template<typename Config>
SC_MODULE(xviLeaf), public blockBase, public xviLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xviLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using xviLeafBase<Config>::XVI_WIDTH;
    using xviLeafBase<Config>::XVI_GAIN;
    using xviLeafBase<Config>::in;
    using xviLeafBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xviLeafBase<Config>::xviPixelT;
    using typename xviLeafBase<Config>::xviSt;

    xviLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    void applyGain(void);

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xviLeaf<Config>::xviLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xviLeaf", name(), bbMode)
        ,xviLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(applyGain);
};

// Scale the payload by this instance's gain, wrapping within XVI_WIDTH. The
// tag passes through unchanged.
template<typename Config>
void xviLeaf<Config>::applyGain(void)
{
    while (true) {
        xviSt sample;
        in->pushReceive(sample);
        in->ack();
        sample.data = (sample.data * XVI_GAIN) & ((1ull << XVI_WIDTH) - 1);
        out->push(sample);
    }
}
