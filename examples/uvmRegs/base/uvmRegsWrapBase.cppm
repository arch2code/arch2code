//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmRegsWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module uvmRegs_uvmRegsWrap.base;
import uvmRegs;
using namespace uvmRegs_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmRegsWrapBase : public virtual blockPortBase
{
public:
    virtual ~uvmRegsWrapBase() = default;
    // dst ports
    // uRouter->apbReg: Register bus
    apb_in< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsWrapBase(std::string name, const char * variant) :
        apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsWrapInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uRouter->apbReg: Register bus
    apb_out< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsWrapInverted(std::string name) :
        apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg->setLogging(verbosity);
    };
};
export class uvmRegsWrapChannels
{
public:
    // dst ports
    // Register bus
    apb_channel< uvmRegsAddrSt, uvmRegsDataSt > apbReg;


    uvmRegsWrapChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmRegsWrapBase *a, uvmRegsWrapInverted *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
