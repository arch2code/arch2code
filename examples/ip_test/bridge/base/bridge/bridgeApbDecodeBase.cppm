//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module bridgeApbDecode.base;
import shared_types;
using namespace shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bridgeApbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~bridgeApbDecodeBase() = default;
    // src ports
    // apbReg->uBridgeIp0: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // apbReg->uBridgeIp1: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;


    bridgeApbDecodeBase(std::string name, const char * variant) :
        apbReg_uBridgeIp0("apbReg_uBridgeIp0")
        ,apbReg_uBridgeIp1("apbReg_uBridgeIp1")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBridgeIp0->setTimed(nsec, mode);
        apbReg_uBridgeIp1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBridgeIp0->setLogging(verbosity);
        apbReg_uBridgeIp1->setLogging(verbosity);
    };
};
export class bridgeApbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBridgeIp0: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // apbReg->uBridgeIp1: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;


    bridgeApbDecodeInverted(std::string name) :
        apbReg_uBridgeIp0(("apbReg_uBridgeIp0"+name).c_str())
        ,apbReg_uBridgeIp1(("apbReg_uBridgeIp1"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBridgeIp0->setTimed(nsec, mode);
        apbReg_uBridgeIp1->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBridgeIp0->setLogging(verbosity);
        apbReg_uBridgeIp1->setLogging(verbosity);
    };
};
export class bridgeApbDecodeChannels
{
public:
    // src ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridgeIp0;
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBridgeIp1;


    bridgeApbDecodeChannels(std::string name, std::string srcName) :
    apbReg_uBridgeIp0(("apbReg_uBridgeIp0"+name).c_str(), srcName)
    ,apbReg_uBridgeIp1(("apbReg_uBridgeIp1"+name).c_str(), srcName)
    {};
    void bind( bridgeApbDecodeBase *a, bridgeApbDecodeInverted *b)
    {
        a->apbReg_uBridgeIp0( apbReg_uBridgeIp0 );
        b->apbReg_uBridgeIp0( apbReg_uBridgeIp0 );
        a->apbReg_uBridgeIp1( apbReg_uBridgeIp1 );
        b->apbReg_uBridgeIp1( apbReg_uBridgeIp1 );
    };
};

// GENERATED_CODE_END
