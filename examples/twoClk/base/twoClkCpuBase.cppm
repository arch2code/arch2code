//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkCpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module twoClk_twoClkCpu.base;
import twoClk;
using namespace twoClk_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkCpuBase : public virtual blockPortBase
{
public:
    virtual ~twoClkCpuBase() = default;
    // src ports
    // twoClkReg->u_twoClk: twoClkCpu access to twoClkTable's tbl memory
    apb_out< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkCpuBase(std::string name, const char * variant) :
        twoClkReg("twoClkReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        twoClkReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        twoClkReg->setLogging(verbosity);
    };
};
export class twoClkCpuInverted : public virtual blockPortBase
{
public:
    // src ports
    // twoClkReg->u_twoClk: twoClkCpu access to twoClkTable's tbl memory
    apb_in< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkCpuInverted(std::string name) :
        twoClkReg(("twoClkReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        twoClkReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        twoClkReg->setLogging(verbosity);
    };
};
export class twoClkCpuChannels
{
public:
    // src ports
    // twoClkCpu access to twoClkTable's tbl memory
    apb_channel< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkCpuChannels(std::string name, std::string srcName) :
    twoClkReg(("twoClkReg"+name).c_str(), srcName)
    {};
    void bind( twoClkCpuBase *a, twoClkCpuInverted *b)
    {
        a->twoClkReg( twoClkReg );
        b->twoClkReg( twoClkReg );
    };
};

// GENERATED_CODE_END
