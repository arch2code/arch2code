import a2c.endOfTest;
#include "someRapperExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=top --excludeInst=uSomeRapper

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import apbDecode_cpu.base;

someRapperExternal::someRapperExternal(sc_module_name modulename) :
    someRapperInverted("Chnl"),
    log_(name())

   ,uCPU(std::dynamic_pointer_cast<cpuBase>(instanceFactory::createInstance(name(), "uCPU", "cpu", "", "apbDecode")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCPU->apbReg(apbReg);

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
