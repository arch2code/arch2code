// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "mixedExternal.h"
// GENERATED_CODE_PARAM --block=mixed_tb --excludeInst=u_mixed

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
#include "cpuBase.h"

mixedExternal::mixedExternal(sc_module_name modulename) :
    mixedInverted("Chnl"),
    log_(name())

   ,uCPU(std::dynamic_pointer_cast<cpuBase>( instanceFactory::createInstance(name(), "uCPU", "cpu", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCPU->cpu_main(cpu_main);

    SC_THREAD(eotThread);
// GENERATED_CODE_END

}
