#ifndef CORE_EXTERNAL_H
#define CORE_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=hier_tb --excludeInst=u_core
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "coreBase.h"

class coreExternal: public sc_module, public coreInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (coreExternal);

    coreExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* CORE_EXTERNAL_H */
