//

// GENERATED_CODE_PARAM --block=xpDpMidDrv --mode=module
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
export module xpDpMid_xpDpMidDrv.block;
import xpDpMid_xpDpMidDrv.base;
import xpDpMid.xpDpMidDrv.config;
import xpDpLeaf;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=classDecl
using namespace xpDpLeaf_ns;
export template<typename Config>
SC_MODULE(xpDpMidDrv), public blockBase, public xpDpMidDrvBase<Config>
{
private:

public:
    SC_HAS_PROCESS(xpDpMidDrv);

    // inherited names usable unqualified (no Config:: / this->)
    using xpDpMidDrvBase<Config>::DP_WIDTH;
    using xpDpMidDrvBase<Config>::out;


    // inherited parameterized types usable unqualified (no <Config>)
    using typename xpDpMidDrvBase<Config>::dpPixelT;
    using typename xpDpMidDrvBase<Config>::dpSt;

    xpDpMidDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~xpDpMidDrv() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

// GENERATED_CODE_BEGIN --template=constructor --section=init
template<typename Config>
xpDpMidDrv<Config>::xpDpMidDrv(sc_module_name blockName, const char * variant, blockBaseMode bbMode)
       : sc_module(blockName)
        ,blockBase("xpDpMidDrv", name(), bbMode)
        ,xpDpMidDrvBase<Config>(name(), variant)
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=constructor --section=body
{
    log_.logPrint(std::format("Instance {} initialized.", this->name()), LOG_IMPORTANT );
    // GENERATED_CODE_END
};

