#include "axi4sDemoExternal.h"
#include "workerThread.h"

// GENERATED_CODE_PARAM --block=axi4sDemo --inst=axi4sDemo_tb.u_axi4sDemo

// GENERATED_CODE_BEGIN --template=tbExternal --section=init
#include "axi4s_m_drvBase.h"
#include "axi4s_s_drvBase.h"

axi4sDemoExternal::axi4sDemoExternal(sc_module_name modulename) :
    axi4sDemoInverted("Chnl"),
    log_(name())
   ,u_axi4s_m_drv(std::dynamic_pointer_cast<axi4s_m_drvBase>( instanceFactory::createInstance(name(), "u_axi4s_m_drv", "axi4s_m_drv", "")))
   ,u_axi4s_s_drv(std::dynamic_pointer_cast<axi4s_s_drvBase>( instanceFactory::createInstance(name(), "u_axi4s_s_drv", "axi4s_s_drv", "")))
// GENERATED_CODE_END
// GENERATED_CODE_BEGIN --template=tbExternal --section=body
{
    u_axi4s_m_drv->axis4_t1(axis4_t1);
    u_axi4s_s_drv->axis4_t2(axis4_t2);

    SC_THREAD(eotThread);

// GENERATED_CODE_END
}
