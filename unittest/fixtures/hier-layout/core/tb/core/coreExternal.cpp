import a2c.endOfTest;
#include "coreExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=hier_tb --excludeInst=u_core

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
#include "coreExternal.h"

coreExternal::coreExternal(sc_module_name modulename) :
    coreInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
