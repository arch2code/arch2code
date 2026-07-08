#ifndef HELLOWORLD_EXTERNAL_H
#define HELLOWORLD_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=helloWorld_tb --excludeInst=u_helloWorld
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import helloWorld.base;
#include "endOfTest.h"

class helloWorldExternal: public sc_module, public helloWorldInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (helloWorldExternal);

    helloWorldExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* HELLOWORLD_EXTERNAL_H */
