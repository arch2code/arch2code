#ifndef IP_TOP_EXTERNAL_H
#define IP_TOP_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=ip_top_tb --excludeInst=u_ip_top
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "ip_topBase.h"
#include "endOfTest.h"

//contained instances forward class declaration
class cpuBase;

class ip_topExternal: public sc_module, public ip_topInverted {

    logBlock log_;

public:

    std::shared_ptr<cpuBase> uCPU;

    SC_HAS_PROCESS (ip_topExternal);

    ip_topExternal(sc_module_name modulename);

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* IP_TOP_EXTERNAL_H */
