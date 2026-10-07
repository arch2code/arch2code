//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "push_ack_channel.h"

export module twoClk.base;
import twoClk;
import twoClkIp;
using namespace twoClk_ns;
using namespace twoClkIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkBase : public virtual blockPortBase
{
public:
    virtual ~twoClkBase() = default;
    // dst ports
    // uCpu->twoClkReg: twoClkCpu access to twoClkTable's tbl memory
    apb_in< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkBase(std::string name, const char * variant) :
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
export class twoClkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCpu->twoClkReg: twoClkCpu access to twoClkTable's tbl memory
    apb_out< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkInverted(std::string name) :
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
export class twoClkChannels
{
public:
    // dst ports
    // twoClkCpu access to twoClkTable's tbl memory
    apb_channel< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkChannels(std::string name, std::string srcName) :
    twoClkReg(("twoClkReg"+name).c_str(), srcName)
    {};
    void bind( twoClkBase *a, twoClkInverted *b)
    {
        a->twoClkReg( twoClkReg );
        b->twoClkReg( twoClkReg );
    };
};

// GENERATED_CODE_END
