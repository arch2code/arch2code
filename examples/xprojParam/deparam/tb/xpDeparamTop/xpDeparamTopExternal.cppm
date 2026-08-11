//

// GENERATED_CODE_PARAM --block=xpDeparamTop_tb --excludeInst=u_xpDeparamTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module xpDeparam_xpDeparamTop.external;
import a2c.endOfTest;
import xpDeparam_xpDeparamTop.base;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header


export class xpDeparamTopExternal: public sc_module, public xpDeparamTopInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (xpDeparamTopExternal);

    xpDeparamTopExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

xpDeparamTopExternal::xpDeparamTopExternal(sc_module_name modulename) :
    xpDeparamTopInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

