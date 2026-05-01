#include "pySocketExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=pySocket

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

pySocketExternal::pySocketExternal(sc_module_name modulename) :
    pySocketInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
