//

// GENERATED_CODE_PARAM --block=xpTwoCtxSrc --mode=module
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
export module xpTwoCtx_xpTwoCtxSrc.block;
import xpTwoCtx_xpTwoCtxSrc.base;
import xpTwoCtx.xpTwoCtxSrc.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpTwoCtxSrc), public blockBase, public xpTwoCtxSrcBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpTwoCtxSrc);

    // inherited names usable unqualified (no Config:: / this->)
    using xpTwoCtxSrcBase<Config>::DP_WIDTH;
    using xpTwoCtxSrcBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using xpTwoCtxSrcBase<Config>::DP_WIDTH_X2;
    using typename xpTwoCtxSrcBase<Config>::dpPixelT;
    using typename xpTwoCtxSrcBase<Config>::dpSt;

    xpTwoCtxSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members
private:
    static constexpr uint32_t SAMPLE_COUNT = 4;
    static constexpr uint32_t FIRST_TAG = 0;
    static constexpr uint32_t FIRST_DATA = 0xA00;
    static constexpr uint32_t FIRST_MARK = 0x50;
    void drive(void);
};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpTwoCtxSrc<Config>::xpTwoCtxSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxSrc", name(), bbMode)
        ,xpTwoCtxSrcBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
    SC_THREAD(drive);
};

template<typename Config>
void xpTwoCtxSrc<Config>::drive(void)
{
    for (uint32_t i = 0; i < SAMPLE_COUNT; i++) {
        dpSt sample{};
        sample.tag  = FIRST_TAG + i;
        sample.algo = 0;
        sample.data = FIRST_DATA + i;
        sample.mark = FIRST_MARK + i;
        out->push(sample);
    }
}

