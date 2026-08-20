//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=blockModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "push_ack_channel.h"
#include "xpTwoCtxVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport
export module xpTwoCtx_xpTwoCtxBare.block;
import xpTwoCtx_xpTwoCtxBare.base;
import xpTwoCtx;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpTwoCtx_ns;
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpTwoCtxBare), public blockBase, public xpTwoCtxBareBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpTwoCtxBare);

    // inherited names usable unqualified (no Config:: / this->)
    using xpTwoCtxBareBase<Config>::TC_GAIN;
    using xpTwoCtxBareBase<Config>::DP_WIDTH;
    using xpTwoCtxBareBase<Config>::litIn;


    // inherited parameterized types usable unqualified (no <Config>)
    using xpTwoCtxBareBase<Config>::TC_GAIN_X2;
    using typename xpTwoCtxBareBase<Config>::dpPixelT;
    using typename xpTwoCtxBareBase<Config>::tcValT;
    using typename xpTwoCtxBareBase<Config>::dpSt;
    using typename xpTwoCtxBareBase<Config>::tcSt;

    xpTwoCtxBare(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxBare() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpTwoCtxBare<Config>::xpTwoCtxBare(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxBare", name(), bbMode)
        ,xpTwoCtxBareBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

