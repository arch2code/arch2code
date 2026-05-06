#ifndef IP_TOP_H
#define IP_TOP_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=classDecl
#include "logging.h"
#include "instanceFactory.h"
#include "ip_topBase.h"
#include "ip_topConfig.h"
#include "ipConfig.h"
import ip_top;
using namespace ip_top_ns;
import ip;
using namespace ip_ns;
//contained instances forward class declaration
class apbDecodeBase;
template<typename Config> class srcBase;
template<typename Config> class ipBase;

template<typename Config>
SC_MODULE(ip_top), public blockBase, public ip_topBase<Config>
{
private:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock("ip_top_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>> (std::make_shared<ip_top<ipDefaultConfig>>(blockName, variant, bbMode));}, "" );
        }
    };
    static registerBlock registerBlock_;
public:
    SC_HAS_PROCESS(ip_top);

    // channels
    // IP data push/ack stream
    push_ack_channel< ipDataSt<Config> > out0;
    // IP data push/ack stream
    push_ack_channel< ipDataSt<Config> > out1;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp1;

    //instances contained in block
    std::shared_ptr<apbDecodeBase> uAPBDecode;
    std::shared_ptr<srcBase<Config>> uSrc;
    std::shared_ptr<ipBase<Config>> uIp0;
    std::shared_ptr<ipBase<Config>> uIp1;

    ip_top(sc_module_name blockName, const char * variant, blockBaseMode bbMode);
    ~ip_top() override = default;

    // GENERATED_CODE_END
    // block implementation members

};

#endif //IP_TOP_H
