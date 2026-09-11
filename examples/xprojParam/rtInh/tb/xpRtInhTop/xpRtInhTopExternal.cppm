//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop_tb --excludeInst=u_xpRtInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
#include "workerThread.h"
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module xpRtInh_xpRtInhTop.external;
import a2c.endOfTest;
import xpRtInh_xpRtInhTop.base;
import common_cpu.base;
import common_shared_types;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace common_shared_types_ns;

export class xpRtInhTopExternal: public sc_module, public xpRtInhTopInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (xpRtInhTopExternal);

    xpRtInhTopExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

    // Launches the firmware worker as a SystemC thread (SystemC-thread mode).
    void fwThread(void);
    sc_event fwEvent;
};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

xpRtInhTopExternal::xpRtInhTopExternal(sc_module_name modulename) :
    xpRtInhTopInverted("Chnl"),
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
};

void xpRtInhTopExternal::fwThread(void)
{
    workerFactory::startSystemCThread("fw", &fwEvent);
}

