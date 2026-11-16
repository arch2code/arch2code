//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module uvmReuse_uvmReuseRouter.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseRouterBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseRouterBase() = default;
    // src ports
    // apbReg->uLeafA: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafA;
    // apbReg->uLeafB: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafB;

    // dst ports
    // External->apbReg: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseRouterBase(std::string name, const char * variant) :
        apbReg_uLeafA("apbReg_uLeafA")
        ,apbReg_uLeafB("apbReg_uLeafB")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uLeafA->setTimed(nsec, mode);
        apbReg_uLeafB->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uLeafA->setLogging(verbosity);
        apbReg_uLeafB->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmReuseRouterInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uLeafA: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafA;
    // apbReg->uLeafB: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafB;

    // dst ports
    // External->apbReg: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseRouterInverted(std::string name) :
        apbReg_uLeafA(("apbReg_uLeafA"+name).c_str())
        ,apbReg_uLeafB(("apbReg_uLeafB"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uLeafA->setTimed(nsec, mode);
        apbReg_uLeafB->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uLeafA->setLogging(verbosity);
        apbReg_uLeafB->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmReuseRouterChannels
{
public:
    // src ports
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafA;
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg_uLeafB;

    // dst ports
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseRouterChannels(std::string name, std::string srcName) :
    apbReg_uLeafA(("apbReg_uLeafA"+name).c_str(), srcName)
    ,apbReg_uLeafB(("apbReg_uLeafB"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmReuseRouterBase *a, uvmReuseRouterInverted *b)
    {
        a->apbReg_uLeafA( apbReg_uLeafA );
        b->apbReg_uLeafA( apbReg_uLeafA );
        a->apbReg_uLeafB( apbReg_uLeafB );
        b->apbReg_uLeafB( apbReg_uLeafB );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
