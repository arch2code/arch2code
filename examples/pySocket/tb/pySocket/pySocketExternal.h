#ifndef PYSOCKET_EXTERNAL_H
#define PYSOCKET_EXTERNAL_H
// 

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "pySocketBase.h"
#include "endOfTest.h"

class pySocketExternal: public sc_module, public pySocketInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (pySocketExternal);

    pySocketExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* PYSOCKET_EXTERNAL_H */
