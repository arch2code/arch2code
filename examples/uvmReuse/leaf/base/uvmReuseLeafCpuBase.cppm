//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafCpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module uvmReuseLeaf_uvmReuseLeafCpu.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseLeafCpuBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseLeafCpuBase() = default;
    // src ports
    // apbReg->uRouter: Register bus
    apb_out< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafCpuBase(std::string name, const char * variant) :
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
export class uvmReuseLeafCpuInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uRouter: Register bus
    apb_in< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafCpuInverted(std::string name) :
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
export class uvmReuseLeafCpuChannels
{
public:
    // src ports
    // Register bus
    apb_channel< uvmReuseAddrSt, uvmReuseDataSt > apbReg;


    uvmReuseLeafCpuChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( uvmReuseLeafCpuBase *a, uvmReuseLeafCpuInverted *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
