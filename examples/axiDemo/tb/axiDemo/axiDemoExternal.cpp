#include "axiDemoExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=axiDemo_tb --excludeInst=u_axiDemo

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

axiDemoExternal::axiDemoExternal(sc_module_name modulename) :
    axiDemoInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
