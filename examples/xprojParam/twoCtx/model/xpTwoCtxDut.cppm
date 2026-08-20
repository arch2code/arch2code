//

// GENERATED_CODE_PARAM --block=xpTwoCtxDut --mode=module
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
export module xpTwoCtx_xpTwoCtxDut.block;
import xpTwoCtx_xpTwoCtxDut.base;
import xpDpLeaf;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
using namespace xpTwoCtx_ns;
export template<typename Config>
SC_MODULE(xpTwoCtxDut), public blockBase, public xpTwoCtxDutBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpTwoCtxDut);

    // inherited names usable unqualified (no Config:: / this->)
    using xpTwoCtxDutBase<Config>::DP_WIDTH;
    using xpTwoCtxDutBase<Config>::TC_GAIN;
    using xpTwoCtxDutBase<Config>::in;
    using xpTwoCtxDutBase<Config>::valOut;


    // inherited parameterized types usable unqualified (no <Config>)
    using xpTwoCtxDutBase<Config>::TC_GAIN_X2;
    using typename xpTwoCtxDutBase<Config>::dpPixelT;
    using typename xpTwoCtxDutBase<Config>::tcValT;
    using typename xpTwoCtxDutBase<Config>::dpSt;
    using typename xpTwoCtxDutBase<Config>::tcSt;

    xpTwoCtxDut(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxDut() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpTwoCtxDut<Config>::xpTwoCtxDut(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxDut", name(), bbMode)
        ,xpTwoCtxDutBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

