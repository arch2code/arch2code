#ifndef IP_TOP_EXTERNAL_H
#define IP_TOP_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "ip_topBase.h"
#include "ip_topConfig.h"
#include "ipConfig.h"
#include "endOfTest.h"

//contained instances forward class declaration
class apbDecodeBase;
template<typename Config> class ipBase;
class srcBase;

class ip_topExternal: public sc_module, public ip_topInverted {

    logBlock log_;

public:

    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<srcBase> uSrc;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
    std::shared_ptr<ipBase<ipVariant1Config>> uIp1;

    SC_HAS_PROCESS (ip_topExternal);

    ip_topExternal(sc_module_name modulename);

    // IP data push/ack stream
    push_ack_channel< ipDataSt<ipVariant0Config> > out0;
    // IP data push/ack stream
    push_ack_channel< ipDataSt<ipVariant1Config> > out1;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp1;

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* IP_TOP_EXTERNAL_H */
