//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=twoClkDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module twoClk_twoClkDecode.base;
import twoClk;
using namespace twoClk_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class twoClkDecodeBase : public virtual blockPortBase
{
public:
    virtual ~twoClkDecodeBase() = default;
    // src ports
    // twoClkReg->uTable: twoClkCpu access to twoClkTable's tbl memory
    apb_out< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg_uTable;

    // dst ports
    // External->twoClkReg: twoClkCpu access to twoClkTable's tbl memory
    apb_in< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkDecodeBase(std::string name, const char * variant) :
        twoClkReg_uTable("twoClkReg_uTable")
        ,twoClkReg("twoClkReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        twoClkReg_uTable->setTimed(nsec, mode);
        twoClkReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        twoClkReg_uTable->setLogging(verbosity);
        twoClkReg->setLogging(verbosity);
    };
};
export class twoClkDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // twoClkReg->uTable: twoClkCpu access to twoClkTable's tbl memory
    apb_in< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg_uTable;

    // dst ports
    // External->twoClkReg: twoClkCpu access to twoClkTable's tbl memory
    apb_out< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkDecodeInverted(std::string name) :
        twoClkReg_uTable(("twoClkReg_uTable"+name).c_str())
        ,twoClkReg(("twoClkReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        twoClkReg_uTable->setTimed(nsec, mode);
        twoClkReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        twoClkReg_uTable->setLogging(verbosity);
        twoClkReg->setLogging(verbosity);
    };
};
export class twoClkDecodeChannels
{
public:
    // src ports
    // twoClkCpu access to twoClkTable's tbl memory
    apb_channel< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg_uTable;

    // dst ports
    // twoClkCpu access to twoClkTable's tbl memory
    apb_channel< twoClkRegAddrSt, twoClkRegDataSt > twoClkReg;


    twoClkDecodeChannels(std::string name, std::string srcName) :
    twoClkReg_uTable(("twoClkReg_uTable"+name).c_str(), srcName)
    ,twoClkReg(("twoClkReg"+name).c_str(), srcName)
    {};
    void bind( twoClkDecodeBase *a, twoClkDecodeInverted *b)
    {
        a->twoClkReg_uTable( twoClkReg_uTable );
        b->twoClkReg_uTable( twoClkReg_uTable );
        a->twoClkReg( twoClkReg );
        b->twoClkReg( twoClkReg );
    };
};

// GENERATED_CODE_END
