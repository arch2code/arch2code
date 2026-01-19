#ifndef MIXED_EXTERNAL_H
#define MIXED_EXTERNAL_H
// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=mixed_tb --excludeInst=u_mixed
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "mixedBase.h"
#include "endOfTest.h"

//contained instances forward class declaration
class cpuBase;

class mixedExternal: public sc_module, public mixedInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (mixedExternal);

    mixedExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END

};

#endif /* MIXED_EXTERNAL_H */
