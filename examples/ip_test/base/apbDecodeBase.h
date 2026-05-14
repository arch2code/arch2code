#ifndef APBDECODE_BASE_H
#define APBDECODE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
import ip_top;
using namespace ip_top_ns;

class apbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~apbDecodeBase() = default;
    // src ports
    // apbReg->uIp0: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apb_uIp0;
    // apbReg->uIp1: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apb_uIp1;
    // apbReg->uBridge: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apb_uBridge;

    // dst ports
    // External->apbReg: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeBase(std::string name, const char * variant) :
        apb_uIp0("apb_uIp0")
        ,apb_uIp1("apb_uIp1")
        ,apb_uBridge("apb_uBridge")
        ,cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uIp0->setTimed(nsec, mode);
        apb_uIp1->setTimed(nsec, mode);
        apb_uBridge->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uIp0->setLogging(verbosity);
        apb_uIp1->setLogging(verbosity);
        apb_uBridge->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
class apbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uIp0: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apb_uIp0;
    // apbReg->uIp1: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apb_uIp1;
    // apbReg->uBridge: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apb_uBridge;

    // dst ports
    // External->apbReg: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeInverted(std::string name) :
        apb_uIp0(("apb_uIp0"+name).c_str())
        ,apb_uIp1(("apb_uIp1"+name).c_str())
        ,apb_uBridge(("apb_uBridge"+name).c_str())
        ,cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uIp0->setTimed(nsec, mode);
        apb_uIp1->setTimed(nsec, mode);
        apb_uBridge->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uIp0->setLogging(verbosity);
        apb_uIp1->setLogging(verbosity);
        apb_uBridge->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
class apbDecodeChannels
{
public:
    // src ports
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uIp1;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uBridge;

    // dst ports
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeChannels(std::string name, std::string srcName) :
    apb_uIp0(("apb_uIp0"+name).c_str(), srcName)
    ,apb_uIp1(("apb_uIp1"+name).c_str(), srcName)
    ,apb_uBridge(("apb_uBridge"+name).c_str(), srcName)
    ,cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apb_uIp0( apb_uIp0 );
        b->apb_uIp0( apb_uIp0 );
        a->apb_uIp1( apb_uIp1 );
        b->apb_uIp1( apb_uIp1 );
        a->apb_uBridge( apb_uBridge );
        b->apb_uBridge( apb_uBridge );
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};


// Force-link function (active modules-mode anchor). See plan-block-registration.md.
void force_link_apbDecode();
// GENERATED_CODE_END
#endif //APBDECODE_BASE_H
