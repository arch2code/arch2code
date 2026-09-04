//

// GENERATED_CODE_PARAM --block=vliLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "vliContVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "q_assert.h"
// GENERATED_CODE_BEGIN --template=moduleExport
export module vlInh_vliLeaf.block;
import vlInh_vliLeaf.base;
import vlInh_vliCont;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace vlInh_vliCont_ns;
export template<typename Config>
SC_MODULE(vliLeaf), public blockBase, public vliLeafBase<Config>
{
private:

public:
    SC_HAS_PROCESS(vliLeaf);

    // inherited names usable unqualified (no Config:: / this->)
    using vliLeafBase<Config>::VLI_ALGO;
    using vliLeafBase<Config>::VLI_WIDTH;
    using vliLeafBase<Config>::out;
    using vliLeafBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename vliLeafBase<Config>::vliPixelT;
    using typename vliLeafBase<Config>::vliSt;

    vliLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~vliLeaf() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    // Number of samples the chain carries end to end.
    static constexpr uint32_t SAMPLE_COUNT = 4;
    // The leaf ADDS a step to every payload and lets the sum wrap at its own
    // width, so the answer depends on the full width rather than on the bits
    // that happen to survive. rtl/vliLeaf.sv computes the same thing.
    static constexpr uint32_t DATA_MASK = (1u << Config::VLI_WIDTH) - 1;
    static constexpr uint32_t DATA_STEP = 1u << (Config::VLI_WIDTH - 3);
    void forward(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
vliLeaf<Config>::vliLeaf(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("vliLeaf", name(), bbMode)
        ,vliLeafBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(forward);
};

// Stamps the VLI_ALGO and VLI_WIDTH of the Config this instance was built at.
// The ordinary chain selects the leaf's own variant. The inherited chains take
// their container Configs. rtl/vliLeaf.sv stamps the same fields, so a Verilated
// leaf built at the wrong Config reads back wrong.
template<typename Config>
void vliLeaf<Config>::forward(void)
{
    vliSt sample{};
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        in->pushReceive(sample);
        in->ack();
        sample.algo = VLI_ALGO;
        sample.wid  = VLI_WIDTH;
        sample.data = ((uint32_t)sample.data + DATA_STEP) & DATA_MASK;
        log_.logPrint(std::format("{} forwarding tag {} at algo {} width {} data 0x{:x}",
            this->name(), (uint64_t)sample.tag, (uint64_t)VLI_ALGO, (uint64_t)VLI_WIDTH,
            (uint64_t)sample.data), LOG_IMPORTANT);
        out->push(sample);
    }
}
