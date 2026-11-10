//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=top --excludeInst=uAhbSoc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module ahbDecode_ahbSoc.external;
import a2c.endOfTest;
import ahbDecode_ahbSoc.base;
import ahbDecode_cpu.base;
import ahbDecode;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace ahbDecode_ns;

export class ahbSocExternal: public sc_module, public ahbSocInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (ahbSocExternal);

    ahbSocExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

ahbSocExternal::ahbSocExternal(sc_module_name modulename) :
    ahbSocInverted("Chnl"),
    log_(name())

   ,uCPU(std::dynamic_pointer_cast<cpuBase>(instanceFactory::createInstance(name(), "uCPU", "cpu", "", "ahbDecode")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    uCPU->ahbReg(ahbReg);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};
