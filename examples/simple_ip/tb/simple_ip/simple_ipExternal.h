#ifndef SIMPLE_IP_EXTERNAL_H
#define SIMPLE_IP_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=simple_ip_tb --excludeInst=u_simple_ip
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "instanceFactory.h"
import simple_ip.base;
import shared_types;
using namespace shared_types_ns;
#include "endOfTest.h"

//contained instances forward class declaration
class cpuBase;

class simple_ipExternal: public sc_module, public simple_ipInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (simple_ipExternal);

    simple_ipExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END

    // Launches the firmware worker as a SystemC thread (SystemC-thread mode).
    void fwThread(void);
    sc_event fwEvent;

};

#endif /* SIMPLE_IP_EXTERNAL_H */
