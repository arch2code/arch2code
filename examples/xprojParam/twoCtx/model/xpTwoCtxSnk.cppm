//

// GENERATED_CODE_PARAM --block=xpTwoCtxSnk --mode=module
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
export module xpTwoCtx_xpTwoCtxSnk.block;
import xpTwoCtx_xpTwoCtxSnk.base;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpTwoCtx_ns;
export template<typename Config>
SC_MODULE(xpTwoCtxSnk), public blockBase, public xpTwoCtxSnkBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpTwoCtxSnk);

    // inherited names usable unqualified (no Config:: / this->)
    using xpTwoCtxSnkBase<Config>::TC_GAIN;
    using xpTwoCtxSnkBase<Config>::in;


    // inherited parameterized types usable unqualified (no <Config>)
    using xpTwoCtxSnkBase<Config>::TC_GAIN_X2;
    using typename xpTwoCtxSnkBase<Config>::tcValT;
    using typename xpTwoCtxSnkBase<Config>::tcSt;

    xpTwoCtxSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpTwoCtxSnk() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpTwoCtxSnk<Config>::xpTwoCtxSnk(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpTwoCtxSnk", name(), bbMode)
        ,xpTwoCtxSnkBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

