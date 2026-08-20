//

// GENERATED_CODE_PARAM --block=xpTwoCtxSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpDpLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpTwoCtx_xpTwoCtxSrc.block;
import xpTwoCtx_xpTwoCtxSrc.base;
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
    using typename xpTwoCtxSrcBase<Config>::dpPixelT;
    using typename xpTwoCtxSrcBase<Config>::dpSt;

    xpTwoCtxSrc(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxSrc() override = default;

    // GENERATED_CODE_END
    // block implementation members

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
};

