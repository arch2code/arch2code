//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsBridgeRouter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module uvmRegs_uvmRegsBridgeRouter.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmRegsBridgeRouterBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsBridgeRouterBase() = default;
    // src ports
    // apbReg->uDeep: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uDeep;

    // dst ports
    // External->apbReg: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsBridgeRouterBase(std::string name, const char * variant) :
        apbReg_uDeep("apbReg_uDeep")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uDeep->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uDeep->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsBridgeRouterInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uDeep: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uDeep;

    // dst ports
    // External->apbReg: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsBridgeRouterInverted(std::string name) :
        apbReg_uDeep(("apbReg_uDeep"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uDeep->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uDeep->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsBridgeRouterChannels
{
public:
    // src ports
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg_uDeep;

    // dst ports
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsBridgeRouterChannels(std::string name, std::string srcName) :
    apbReg_uDeep(("apbReg_uDeep"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmRegsBridgeRouterBase *a, uvmRegsBridgeRouterInverted *b)
    {
        a->apbReg_uDeep( apbReg_uDeep );
        b->apbReg_uDeep( apbReg_uDeep );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
