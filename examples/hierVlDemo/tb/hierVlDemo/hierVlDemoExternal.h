#ifndef AXI4SDEMO_EXTERNAL_H
#define AXI4SDEMO_EXTERNAL_H
//

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=hierVlDemo_tb --excludeInst=u_hierVlDemo
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import hierVlDemo.base;
import hierVlDemo_axi4s_m_drv.base;
import hierVlDemo_axi4s_s_drv.base;
import hierVlDemo_tb;
using namespace hierVlDemo_tb_ns;

class hierVlDemoExternal: public sc_module, public hierVlDemoInverted {

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
};

#endif /* AXI4SDEMO_EXTERNAL_H */
