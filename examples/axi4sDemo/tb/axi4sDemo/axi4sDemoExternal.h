#ifndef AXI4SDEMO_EXTERNAL_H
#define AXI4SDEMO_EXTERNAL_H
//

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=axi4sDemo_tb --excludeInst=u_axi4sDemo
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "axi4sDemoBase.h"
#include "endOfTest.h"

class axi4sDemo_tbExternal: public sc_module, public axi4sDemoInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (axi4sDemo_tbExternal);

    axi4sDemo_tbExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* AXI4SDEMO_EXTERNAL_H */
