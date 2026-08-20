//

// GENERATED_CODE_PARAM --block=xpDpMidStdTop_tb --excludeInst=u_xpDpMidStdTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module xpDpMid_xpDpMidStdTop.external;
import a2c.endOfTest;
import xpDpMid_xpDpMidStdTop.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header


export class xpDpMidStdTopExternal: public sc_module, public xpDpMidStdTopInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (xpDpMidStdTopExternal);

    xpDpMidStdTopExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

xpDpMidStdTopExternal::xpDpMidStdTopExternal(sc_module_name modulename) :
    xpDpMidStdTopInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

