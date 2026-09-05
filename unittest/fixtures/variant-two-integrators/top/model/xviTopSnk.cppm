//

// GENERATED_CODE_PARAM --block=xviTopSnk --mode=module
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
export module xviTop_xviTopSnk.block;
import xviTop_xviTopSnk.base;
import xviLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
import a2c.endOfTest;
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xviLeaf_ns;
export template<typename Config>
SC_MODULE(xviTopSnk), public blockBase, public xviTopSnkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xviTopSnk);

    // inherited names usable unqualified (no Config:: / this->)
    using xviTopSnkBase<Config>::XVI_WIDTH;
    using xviTopSnkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xviTopSnkBase<Config>::xviPixelT;
    using typename xviTopSnkBase<Config>::xviSt;

    xviTopSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xviTopSnk() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr unsigned XVI_TAG_COUNT = 4;

    void observe(void);

    endOfTest eot_;

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xviTopSnk<Config>::xviTopSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xviTopSnk", name(), bbMode)
        ,xviTopSnkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(observe);
};

// Log every sample that arrives. This block never reads XVI_GAIN, so the logged
// payload is the only evidence of the gain the leaf was built at.
template<typename Config>
void xviTopSnk<Config>::observe(void)
{
    eot_.registerVoter();
    for (unsigned n = 0; n < XVI_TAG_COUNT; n++) {
        xviSt sample;
        in->pushReceive(sample);
        in->ack();
        log_.logPrint(std::format("{} observed tag {} data {}", this->name(),
                                  (uint64_t)sample.tag, (uint64_t)sample.data),
                      LOG_ALWAYS);
    }
    eot_.setEndOfTest(true);
}
