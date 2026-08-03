import a2c.endOfTest;
#include "hierVlDemoExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=hierVlDemo_tb --excludeInst=u_hierVlDemo

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
import hierVlDemo_axi4s_m_drv.base;
import hierVlDemo_axi4s_s_drv.base;

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
}
