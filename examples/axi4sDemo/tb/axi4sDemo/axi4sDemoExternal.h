#ifndef AXI4SDEMO_EXTERNAL_H
#define AXI4SDEMO_EXTERNAL_H
//

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=axi4sDemo_tb --excludeInst=u_axi4sDemo
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import axi4sDemo.base;
import axi4sDemo_axi4s_m_drv.base;
import axi4sDemo_axi4s_s_drv.base;
import axi4sDemo_tb;
using namespace axi4sDemo_tb_ns;

class axi4sDemoExternal: public sc_module, public axi4sDemoInverted {

    logBlock log_;

public:

    std::shared_ptr<axi4s_m_drvBase> u_axi4s_m_drv;
    std::shared_ptr<axi4s_s_drvBase> u_axi4s_s_drv;

    SC_HAS_PROCESS (axi4sDemoExternal);

    axi4sDemoExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* AXI4SDEMO_EXTERNAL_H */
