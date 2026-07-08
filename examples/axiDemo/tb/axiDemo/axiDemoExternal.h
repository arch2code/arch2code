#ifndef AXIDEMO_EXTERNAL_H
#define AXIDEMO_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=axiDemo_tb --excludeInst=u_axiDemo
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import axiDemo.base;
#include "endOfTest.h"

class axiDemoExternal: public sc_module, public axiDemoInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (axiDemoExternal);

    axiDemoExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* AXIDEMO_EXTERNAL_H */
