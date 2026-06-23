#include "simpleExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=simple_tb --excludeInst=u_simple

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

simpleExternal::simpleExternal(sc_module_name modulename) :
    simpleInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
