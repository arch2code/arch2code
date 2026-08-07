//

// GENERATED_CODE_PARAM --block=hierVlDemo_tb --excludeInst=u_hierVlDemo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=tbExternalModuleHeader
module;
#include "systemc.h"
#include "logging.h"
#include "instanceFactory.h"
// GENERATED_CODE_END
// user #includes here (global module fragment - attaches to the global module)
// Plain non-modular headers, including any whose definitions live in a .cpp.
// GENERATED_CODE_BEGIN --template=moduleExport --fileMapKey=tbExternal
export module hierVlDemo.external;
import a2c.endOfTest;
import hierVlDemo.base;
import hierVlDemo_axi4s_m_drv.base;
import hierVlDemo_axi4s_s_drv.base;
import hierVlDemo_tb;
// GENERATED_CODE_END
// user imports here (module preamble - imports FIRST, then purview #includes)
// A #include here closes the preamble and attaches to THIS module; use it only for
// headers that name module or Config types.
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

using namespace hierVlDemo_tb_ns;

export class hierVlDemoExternal: public sc_module, public hierVlDemoInverted {

    logBlock log_;

public:

    std::shared_ptr<axi4s_m_drvBase> u_axi4s_m_drv;
    std::shared_ptr<axi4s_s_drvBase> u_axi4s_s_drv;

    SC_HAS_PROCESS (hierVlDemoExternal);

    hierVlDemoExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

    // GENERATED_CODE_END
    // external implementation members

};

// GENERATED_CODE_BEGIN --template=tbExternal --section=init

hierVlDemoExternal::hierVlDemoExternal(sc_module_name modulename) :
    hierVlDemoInverted("Chnl"),
    log_(name())

   ,u_axi4s_m_drv(std::dynamic_pointer_cast<axi4s_m_drvBase>(instanceFactory::createInstance(name(), "u_axi4s_m_drv", "axi4s_m_drv", "", "hierVlDemo")))
   ,u_axi4s_s_drv(std::dynamic_pointer_cast<axi4s_s_drvBase>(instanceFactory::createInstance(name(), "u_axi4s_s_drv", "axi4s_s_drv", "", "hierVlDemo")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    // instance to instance connections via channel
    u_axi4s_m_drv->axis4_t1(axis4_t1);
    u_axi4s_s_drv->axis4_t2(axis4_t2);

    SC_THREAD(eotThread);
    // GENERATED_CODE_END
};

