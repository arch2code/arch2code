//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=mixed_tb --excludeInst=u_mixed --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module mixed.external;
import a2c.endOfTest;
import mixed.base;
import mixed_cpu.base;
import mixed;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace mixed_ns;

export class mixedExternal: public sc_module, public mixedInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (mixedExternal);

    mixedExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

mixedExternal::mixedExternal(sc_module_name modulename) :
    mixedInverted("Chnl"),
    log_(name())

   ,uCPU(std::dynamic_pointer_cast<cpuBase>(instanceFactory::createInstance(name(), "uCPU", "cpu", "", "mixed")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCPU->cpu_main(cpu_main);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

