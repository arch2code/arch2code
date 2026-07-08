#ifndef SIMPLE_EXTERNAL_H
#define SIMPLE_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=simple_tb --excludeInst=u_simple
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import simple.base;
#include "endOfTest.h"

class simpleExternal: public sc_module, public simpleInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (simpleExternal);

    simpleExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* SIMPLE_EXTERNAL_H */
