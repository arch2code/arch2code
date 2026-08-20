//

// GENERATED_CODE_PARAM --block=xpTwoCtxTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
#include "xpDpLeafVariantConfig.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module xpTwoCtx_xpTwoCtxTop.external;
import a2c.endOfTest;
import xpTwoCtx_xpTwoCtxTop.base;
import xpTwoCtx;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace xpTwoCtx_ns;

export class xpTwoCtxTopExternal: public sc_module, public xpTwoCtxTopInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (xpTwoCtxTopExternal);

    xpTwoCtxTopExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

xpTwoCtxTopExternal::xpTwoCtxTopExternal(sc_module_name modulename) :
    xpTwoCtxTopInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

