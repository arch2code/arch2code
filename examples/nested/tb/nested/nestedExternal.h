#ifndef NESTED_EXTERNAL_H
#define NESTED_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=nested_tb --excludeInst=u_nested
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "nestedBase.h"
#include "endOfTest.h"

class nestedExternal: public sc_module, public nestedInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (nestedExternal);

    nestedExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* NESTED_EXTERNAL_H */
