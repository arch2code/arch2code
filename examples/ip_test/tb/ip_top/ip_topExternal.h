#ifndef IP_TOP_EXTERNAL_H
#define IP_TOP_EXTERNAL_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"
#include "logging.h"

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=tbExternal --section=header

#include "ip_topBase.h"
#include "ipConfig.h"
#include "srcConfig.h"
#include "push_ack_port_thunker.h"
#include "endOfTest.h"

//contained instances forward class declaration
class apbDecodeBase;
class bridgeDriverBase;
template<typename Config> class ipBase;
class ipBridgeBase;
template<typename Config> class srcBase;

class ip_topExternal: public sc_module, public ip_topInverted {

    logBlock log_;

public:

    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<srcBase<srcVariantSrc0Config>> uSrc;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
    std::shared_ptr<ipBase<ipVariant1Config>> uIp1;
    std::shared_ptr<bridgeDriverBase> uBridgeDriver;
    std::shared_ptr<ipBridgeBase> uBridge;

    SC_HAS_PROCESS (ip_topExternal);

    ip_topExternal(sc_module_name modulename);

    // src out0 push/ack stream
    push_ack_channel< srcOut0St<srcVariantSrc0Config> > out0;
    // src out1 push/ack stream
    push_ack_channel< srcOut1St<srcVariantSrc0Config> > out1;
    // Non-parameterized 8-bit Q10 bridge data interface
    push_ack_channel< data8St > out8;
    // Non-parameterized 70-bit Q10 bridge data interface
    push_ack_channel< data70St > out70;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp1;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uBridge;
    apb_channel< apbAddrSt, apbDataSt > _ext_cm_uAPBDecode_cpu_main;

    // cross-interface thunkers
    push_ack_port_thunker<srcOut0St<srcVariantSrc0Config>, ipDataSt<ipVariant0Config>> thunker_out0_uIp0;
    push_ack_port_thunker<srcOut1St<srcVariantSrc0Config>, ipDataSt<ipVariant1Config>> thunker_out1_uIp1;

    // Thread monitoring the end of test event to stop simulation
    void eotThread(void) {
        wait((endOfTestState::GetInstance().eotEvent));
        sc_stop();
    }

// GENERATED_CODE_END
};

#endif /* IP_TOP_EXTERNAL_H */
