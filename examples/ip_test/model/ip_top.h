#ifndef IP_TOP_H
#define IP_TOP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "ip_topBase.h"
#include "push_ack_port_thunker.h"
#include "ip_topConfig.h"
#include "srcConfig.h"
#include "ipConfig.h"
import ip_top;
using namespace ip_top_ns;
import src;
using namespace src_ns;
import ip;
using namespace ip_ns;
//contained instances forward class declaration
class apbDecodeBase;
template<typename Config> class srcBase;
template<typename Config> class ipBase;

SC_MODULE(ip_top), public blockBase, public ip_topBase
{
private:

public:
    // channels
    // src out0 push/ack stream
    push_ack_channel< srcOut0St<srcVariantSrc0Config> > out0;
    // src out1 push/ack stream
    push_ack_channel< srcOut1St<srcVariantSrc0Config> > out1;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp1;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<srcBase<srcVariantSrc0Config>> uSrc;
    std::shared_ptr<ipBase<ipVariant0Config>> uIp0;
    std::shared_ptr<ipBase<ipVariant1Config>> uIp1;

    // cross-interface thunkers
    push_ack_port_thunker<srcOut0St<srcVariantSrc0Config>, ipDataSt<ipVariant0Config>> thunker_out0_uIp0;
    push_ack_port_thunker<srcOut1St<srcVariantSrc0Config>, ipDataSt<ipVariant1Config>> thunker_out1_uIp1;

    ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_top() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IP_TOP_H
