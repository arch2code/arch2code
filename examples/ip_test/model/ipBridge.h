#ifndef IPBRIDGE_H
#define IPBRIDGE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "ipBridgeBase.h"
#include "push_ack_port_thunker.h"
#include "ipConfig.h"
import ip_top;
using namespace ip_top_ns;
import ipBridge;
using namespace ipBridge_ns;
import ip;
using namespace ip_ns;
//contained instances forward class declaration
class bridgeApbDecodeBase;
template<typename Config> class ipBase;

SC_MODULE(ipBridge), public blockBase, public ipBridgeBase
{
private:

public:
    // channels
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uBridgeIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uBridgeIp1;

    //instances contained in block
    std::shared_ptr<bridgeApbDecodeBase> uBridgeAPBDecode;
    std::shared_ptr<ipBase<ipVariant0Config>> uBridgeIp0;
    std::shared_ptr<ipBase<ipVariant1Config>> uBridgeIp1;

    // cross-interface thunkers
    push_ack_port_thunker<data8St, ipDataSt<ipVariant0Config>> thunker_uBridgeIp0;
    push_ack_port_thunker<data70St, ipDataSt<ipVariant1Config>> thunker_uBridgeIp1;

    ipBridge(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ipBridge() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IPBRIDGE_H
