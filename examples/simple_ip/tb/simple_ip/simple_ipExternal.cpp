#include "simple_ipExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=simple_ip_tb --excludeInst=u_simple_ip

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import common_cpu.base;

simple_ipExternal::simple_ipExternal(sc_module_name modulename) :
    simple_ipInverted("Chnl"),
    log_(name())

   ,uCPU(std::dynamic_pointer_cast<cpuBase>(instanceFactory::createInstance(name(), "uCPU", "cpu", "", "common")))
// GENERATED_CODE_END
   ,fwEvent("fwEvent")
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCPU->cpu_main(cpu_main);

    SC_THREAD(eotThread);
// GENERATED_CODE_END

    SC_THREAD(fwThread);
}

void simple_ipExternal::fwThread(void)
{
    workerFactory::startSystemCThread("fw", &fwEvent);
}
