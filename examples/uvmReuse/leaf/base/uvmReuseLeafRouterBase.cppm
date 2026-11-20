//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module uvmReuseLeaf_uvmReuseLeafRouter.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseLeafRouterBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseLeafRouterBase() = default;
    // src ports
    // apbReg->u_uvmReuseLeaf: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg_u_uvmReuseLeaf;

    // dst ports
    // uCpu->apbReg: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafRouterBase(std::string name, const char * variant) :
        apbReg_u_uvmReuseLeaf("apbReg_u_uvmReuseLeaf")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_u_uvmReuseLeaf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_u_uvmReuseLeaf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmReuseLeafRouterInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->u_uvmReuseLeaf: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg_u_uvmReuseLeaf;

    // dst ports
    // uCpu->apbReg: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafRouterInverted(std::string name) :
        apbReg_u_uvmReuseLeaf(("apbReg_u_uvmReuseLeaf"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_u_uvmReuseLeaf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_u_uvmReuseLeaf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmReuseLeafRouterChannels
{
public:
    // src ports
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg_u_uvmReuseLeaf;

    // dst ports
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafRouterChannels(std::string name, std::string srcName) :
    apbReg_u_uvmReuseLeaf(("apbReg_u_uvmReuseLeaf"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmReuseLeafRouterBase *a, uvmReuseLeafRouterInverted *b)
    {
        a->apbReg_u_uvmReuseLeaf( apbReg_u_uvmReuseLeaf );
        b->apbReg_u_uvmReuseLeaf( apbReg_u_uvmReuseLeaf );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
