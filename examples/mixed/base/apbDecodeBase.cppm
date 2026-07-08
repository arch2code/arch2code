//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module apbDecode.base;
import mixed;
using namespace mixed_ns;
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
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeBase(std::string name, const char * variant) :
        apbReg_uBlockA("apbReg_uBlockA")
        ,apbReg_uBlockB("apbReg_uBlockB")
        ,cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBlockA->setTimed(nsec, mode);
        apbReg_uBlockB->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBlockA->setLogging(verbosity);
        apbReg_uBlockB->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
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
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeInverted(std::string name) :
        apbReg_uBlockA(("apbReg_uBlockA"+name).c_str())
        ,apbReg_uBlockB(("apbReg_uBlockB"+name).c_str())
        ,cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg_uBlockA->setTimed(nsec, mode);
        apbReg_uBlockB->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg_uBlockA->setLogging(verbosity);
        apbReg_uBlockB->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
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
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeChannels(std::string name, std::string srcName) :
    apbReg_uBlockA(("apbReg_uBlockA"+name).c_str(), srcName)
    ,apbReg_uBlockB(("apbReg_uBlockB"+name).c_str(), srcName)
    ,cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apbReg_uBlockA( apbReg_uBlockA );
        b->apbReg_uBlockA( apbReg_uBlockA );
        a->apbReg_uBlockB( apbReg_uBlockB );
        b->apbReg_uBlockB( apbReg_uBlockB );
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
