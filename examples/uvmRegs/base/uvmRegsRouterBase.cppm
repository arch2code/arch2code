//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module uvmRegs_uvmRegsRouter.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmRegsRouterBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsRouterBase() = default;
    // src ports
    // apbReg->uScale0: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale0;
    // apbReg->uScale1: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale1;
    // apbReg->uStat: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uStat;
    // apbReg->uWrap: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uWrap;
    // apbReg->uBridge: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uBridge;

    // dst ports
    // External->apbReg: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsRouterBase(std::string name, const char * variant) :
        apbReg_uScale0("apbReg_uScale0")
        ,apbReg_uScale1("apbReg_uScale1")
        ,apbReg_uStat("apbReg_uStat")
        ,apbReg_uWrap("apbReg_uWrap")
        ,apbReg_uBridge("apbReg_uBridge")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uScale0->setTimed(nsec, mode);
        apbReg_uScale1->setTimed(nsec, mode);
        apbReg_uStat->setTimed(nsec, mode);
        apbReg_uWrap->setTimed(nsec, mode);
        apbReg_uBridge->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uScale0->setLogging(verbosity);
        apbReg_uScale1->setLogging(verbosity);
        apbReg_uStat->setLogging(verbosity);
        apbReg_uWrap->setLogging(verbosity);
        apbReg_uBridge->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsRouterInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uScale0: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale0;
    // apbReg->uScale1: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale1;
    // apbReg->uStat: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uStat;
    // apbReg->uWrap: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uWrap;
    // apbReg->uBridge: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uBridge;

    // dst ports
    // External->apbReg: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsRouterInverted(std::string name) :
        apbReg_uScale0(("apbReg_uScale0"+name).c_str())
        ,apbReg_uScale1(("apbReg_uScale1"+name).c_str())
        ,apbReg_uStat(("apbReg_uStat"+name).c_str())
        ,apbReg_uWrap(("apbReg_uWrap"+name).c_str())
        ,apbReg_uBridge(("apbReg_uBridge"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uScale0->setTimed(nsec, mode);
        apbReg_uScale1->setTimed(nsec, mode);
        apbReg_uStat->setTimed(nsec, mode);
        apbReg_uWrap->setTimed(nsec, mode);
        apbReg_uBridge->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uScale0->setLogging(verbosity);
        apbReg_uScale1->setLogging(verbosity);
        apbReg_uStat->setLogging(verbosity);
        apbReg_uWrap->setLogging(verbosity);
        apbReg_uBridge->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsRouterChannels
{
public:
    // src ports
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale0;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uScale1;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uStat;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uWrap;
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uBridge;

    // dst ports
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsRouterChannels(std::string name, std::string srcName) :
    apbReg_uScale0(("apbReg_uScale0"+name).c_str(), srcName)
    ,apbReg_uScale1(("apbReg_uScale1"+name).c_str(), srcName)
    ,apbReg_uStat(("apbReg_uStat"+name).c_str(), srcName)
    ,apbReg_uWrap(("apbReg_uWrap"+name).c_str(), srcName)
    ,apbReg_uBridge(("apbReg_uBridge"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmRegsRouterBase *a, uvmRegsRouterInverted *b)
    {
        a->apbReg_uScale0( apbReg_uScale0 );
        b->apbReg_uScale0( apbReg_uScale0 );
        a->apbReg_uScale1( apbReg_uScale1 );
        b->apbReg_uScale1( apbReg_uScale1 );
        a->apbReg_uStat( apbReg_uStat );
        b->apbReg_uStat( apbReg_uStat );
        a->apbReg_uWrap( apbReg_uWrap );
        b->apbReg_uWrap( apbReg_uWrap );
        a->apbReg_uBridge( apbReg_uBridge );
        b->apbReg_uBridge( apbReg_uBridge );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
