//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module apbDecode.base;
import apbDecode;
using namespace apbDecode_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class apbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~apbDecodeBase() = default;
    // src ports
    // apbReg->uBlockA: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg_uBlockA;
    // apbReg->uBlockB: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg_uBlockB;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    apbDecodeBase(std::string name, const char * variant) :
        apbReg_uBlockA("apbReg_uBlockA")
        ,apbReg_uBlockB("apbReg_uBlockB")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBlockA->setTimed(nsec, mode);
        apbReg_uBlockB->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBlockA->setLogging(verbosity);
        apbReg_uBlockB->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class apbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBlockA: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg_uBlockA;
    // apbReg->uBlockB: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg_uBlockB;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    apbDecodeInverted(std::string name) :
        apbReg_uBlockA(("apbReg_uBlockA"+name).c_str())
        ,apbReg_uBlockB(("apbReg_uBlockB"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBlockA->setTimed(nsec, mode);
        apbReg_uBlockB->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBlockA->setLogging(verbosity);
        apbReg_uBlockB->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
export class apbDecodeChannels
{
public:
    // src ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg_uBlockB;

    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    apbDecodeChannels(std::string name, std::string srcName) :
    apbReg_uBlockA(("apbReg_uBlockA"+name).c_str(), srcName)
    ,apbReg_uBlockB(("apbReg_uBlockB"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apbReg_uBlockA( apbReg_uBlockA );
        b->apbReg_uBlockA( apbReg_uBlockA );
        a->apbReg_uBlockB( apbReg_uBlockB );
        b->apbReg_uBlockB( apbReg_uBlockB );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
