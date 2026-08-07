//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=top --excludeInst=uSomeRapper --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module apbDecode_someRapper.external;
import a2c.endOfTest;
import apbDecode_someRapper.base;
import apbDecode_cpu.base;
import apbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace apbDecode_ns;

export class someRapperExternal: public sc_module, public someRapperInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (someRapperExternal);

    someRapperExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

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
};

