#include "ip_topExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=ip_top_tb --excludeInst=u_ip_top

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
#include "cpuBase.h"

ip_topExternal::ip_topExternal(sc_module_name modulename) :
    ip_topInverted("Chnl"),
    log_(name())

   ,uCPU(std::dynamic_pointer_cast<cpuBase>((force_link_cpu(), instanceFactory::createInstance(name(), "uCPU", "cpu", ""))))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCPU->cpu_main(cpu_main);

    SC_THREAD(eotThread);
// GENERATED_CODE_END
}
