#ifndef BRIDGEAPBDECODE_BASE_H
#define BRIDGEAPBDECODE_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
import shared_types;
using namespace shared_types_ns;

class bridgeApbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~bridgeApbDecodeBase() = default;
    // src ports
    // apbReg->uBridgeIp0: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // apbReg->uBridgeIp1: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    bridgeApbDecodeBase(std::string name, const char * variant) :
        apbReg_uBridgeIp0("apbReg_uBridgeIp0")
        ,apbReg_uBridgeIp1("apbReg_uBridgeIp1")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBridgeIp0->setTimed(nsec, mode);
        apbReg_uBridgeIp1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBridgeIp0->setLogging(verbosity);
        apbReg_uBridgeIp1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class bridgeApbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBridgeIp0: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // apbReg->uBridgeIp1: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;

    // dst ports
    // External->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    bridgeApbDecodeInverted(std::string name) :
        apbReg_uBridgeIp0(("apbReg_uBridgeIp0"+name).c_str())
        ,apbReg_uBridgeIp1(("apbReg_uBridgeIp1"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBridgeIp0->setTimed(nsec, mode);
        apbReg_uBridgeIp1->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBridgeIp0->setLogging(verbosity);
        apbReg_uBridgeIp1->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class bridgeApbDecodeChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;

    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    bridgeApbDecodeChannels(std::string name, std::string srcName) :
    apbReg_uBridgeIp0(("apbReg_uBridgeIp0"+name).c_str(), srcName)
    ,apbReg_uBridgeIp1(("apbReg_uBridgeIp1"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( bridgeApbDecodeBase *a, bridgeApbDecodeInverted *b)
    {
        a->apbReg_uBridgeIp0( apbReg_uBridgeIp0 );
        b->apbReg_uBridgeIp0( apbReg_uBridgeIp0 );
        a->apbReg_uBridgeIp1( apbReg_uBridgeIp1 );
        b->apbReg_uBridgeIp1( apbReg_uBridgeIp1 );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};


// Force-link function (active modules-mode anchor).
void force_link_bridgeApbDecode();
// GENERATED_CODE_END
#endif //BRIDGEAPBDECODE_BASE_H
