import a2c.endOfTest;
#include "helloWorldExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=helloWorld_tb --excludeInst=u_helloWorld

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
#include "helloWorldExternal.h"

helloWorldExternal::helloWorldExternal(sc_module_name modulename) :
    helloWorldInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
