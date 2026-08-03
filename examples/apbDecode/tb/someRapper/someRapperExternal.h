#ifndef SOMERAPPER_EXTERNAL_H
#define SOMERAPPER_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=top --excludeInst=uSomeRapper
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import apbDecode_someRapper.base;
import apbDecode;
using namespace apbDecode_ns;

//contained instances forward class declaration
class cpuBase;

class someRapperExternal: public sc_module, public someRapperInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (someRapperExternal);

    someRapperExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* SOMERAPPER_EXTERNAL_H */
