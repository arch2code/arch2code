import a2c.endOfTest;
#include "bridgeStdTopExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=bridgeStdTop_tb --excludeInst=u_bridgeStdTop

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

bridgeStdTopExternal::bridgeStdTopExternal(sc_module_name modulename) :
    bridgeStdTopInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
