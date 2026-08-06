import a2c.endOfTest;
#include "nestedExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=nested_tb --excludeInst=u_nested

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import a2c.endOfTest;
#include "nestedExternal.h"

nestedExternal::nestedExternal(sc_module_name modulename) :
    nestedInverted("Chnl"),
    log_(name())

// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
