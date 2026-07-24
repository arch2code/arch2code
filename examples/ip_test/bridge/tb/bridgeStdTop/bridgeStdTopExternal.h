#ifndef BRIDGESTDTOP_EXTERNAL_H
#define BRIDGESTDTOP_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=bridgeStdTop_tb --excludeInst=u_bridgeStdTop
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import bridgeStdTop.base;
#include "endOfTest.h"

class bridgeStdTopExternal: public sc_module, public bridgeStdTopInverted {

    logBlock log_;

public:

    SC_HAS_PROCESS (bridgeStdTopExternal);

    bridgeStdTopExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* BRIDGESTDTOP_EXTERNAL_H */
