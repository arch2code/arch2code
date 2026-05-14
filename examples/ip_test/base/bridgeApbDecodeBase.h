#ifndef BRIDGEAPBDECODE_BASE_H
#define BRIDGEAPBDECODE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
import ip_top;
using namespace ip_top_ns;

class bridgeApbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~bridgeApbDecodeBase() = default;
    // src ports
    // apbReg->uBridgeIp0: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apb_uBridgeIp0;
    // apbReg->uBridgeIp1: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apb_uBridgeIp1;

    // dst ports
    // External->apbReg: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    bridgeApbDecodeBase(std::string name, const char * variant) :
        apb_uBridgeIp0("apb_uBridgeIp0")
        ,apb_uBridgeIp1("apb_uBridgeIp1")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uBridgeIp0->setTimed(nsec, mode);
        apb_uBridgeIp1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uBridgeIp0->setLogging(verbosity);
        apb_uBridgeIp1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class bridgeApbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBridgeIp0: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apb_uBridgeIp0;
    // apbReg->uBridgeIp1: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apb_uBridgeIp1;

    // dst ports
    // External->apbReg: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    bridgeApbDecodeInverted(std::string name) :
        apb_uBridgeIp0(("apb_uBridgeIp0"+name).c_str())
        ,apb_uBridgeIp1(("apb_uBridgeIp1"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uBridgeIp0->setTimed(nsec, mode);
        apb_uBridgeIp1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uBridgeIp0->setLogging(verbosity);
        apb_uBridgeIp1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class bridgeApbDecodeChannels
{
public:
    // src ports
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uBridgeIp0;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apb_uBridgeIp1;

    // dst ports
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    bridgeApbDecodeChannels(std::string name, std::string srcName) :
    apb_uBridgeIp0(("apb_uBridgeIp0"+name).c_str(), srcName)
    ,apb_uBridgeIp1(("apb_uBridgeIp1"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( bridgeApbDecodeBase *a, bridgeApbDecodeInverted *b)
    {
        a->apb_uBridgeIp0( apb_uBridgeIp0 );
        b->apb_uBridgeIp0( apb_uBridgeIp0 );
        a->apb_uBridgeIp1( apb_uBridgeIp1 );
        b->apb_uBridgeIp1( apb_uBridgeIp1 );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};


// Force-link function (active modules-mode anchor). See plan-block-registration.md.
void force_link_bridgeApbDecode();
// GENERATED_CODE_END
#endif //BRIDGEAPBDECODE_BASE_H
