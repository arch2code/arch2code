//

// GENERATED_CODE_PARAM --block=xpDpSrc --mode=module
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
export module xpDpTop_xpDpSrc.block;
import xpDpTop_xpDpSrc.base;
import xpDpTop.xpDpSrc.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpSrc), public blockBase, public xpDpSrcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpSrc);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpSrcBase<Config>::DP_WIDTH;
    using xpDpSrcBase<Config>::out;
    using xpDpSrcBase<Config>::out2;
    using xpDpSrcBase<Config>::out4;
    using xpDpSrcBase<Config>::out3;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpSrcBase<Config>::dpPixelT;
    using typename xpDpSrcBase<Config>::dpSt;

    xpDpSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0x31;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpSrc<Config>::xpDpSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpSrc", name(), bbMode)
        ,xpDpSrcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

// Drives four samples into the mid-level IP. The algo field is left at zero: it
// is the leaf's to stamp, and the checker reads it back.
template<typename Config>
void xpDpSrc<Config>::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        dpSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.algo = 0;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
        out2->push(sample);
        out3->push(sample);
        out4->push(sample);
    }
}

