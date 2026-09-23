//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkTable --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module twoClk_twoClkTable.base;
import twoClk;
using namespace twoClk_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkTableBase : public virtual blockPortBase
{
public:
    virtual ~twoClkTableBase() = default;
    // dst ports
    // uDecode->twoClkReg: twoClkCpu access to twoClkTable's tbl memory
    apb_in< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkTableBase(std::string name, const char * variant) :
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
export class twoClkTableInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDecode->twoClkReg: twoClkCpu access to twoClkTable's tbl memory
    apb_out< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkTableInverted(std::string name) :
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
export class twoClkTableChannels
{
public:
    // dst ports
    // twoClkCpu access to twoClkTable's tbl memory
    apb_channel< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkTableChannels(std::string name, std::string srcName) :
    twoClkReg(("twoClkReg"+name).c_str(), srcName)
    {};
    void bind( twoClkTableBase *a, twoClkTableInverted *b)
    {
        a->twoClkReg( twoClkReg );
        b->twoClkReg( twoClkReg );
    };
};

// GENERATED_CODE_END
