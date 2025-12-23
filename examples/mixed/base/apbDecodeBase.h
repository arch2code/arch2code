#ifndef APBDECODE_BASE_H
#define APBDECODE_BASE_H

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "mixedIncludes.h"

class apbDecodeBase : public virtual blockPortBase
{
public:
    virtual ~apbDecodeBase() = default;
    // src ports
    // apbReg->uBlockA: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apb_uBlockA;
    // apbReg->uBlockB: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apb_uBlockB;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeBase(std::string name, const char * variant) :
        apb_uBlockA("apb_uBlockA")
        ,apb_uBlockB("apb_uBlockB")
        ,cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uBlockA->setTimed(nsec, mode);
        apb_uBlockB->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uBlockA->setLogging(verbosity);
        apb_uBlockB->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
class apbDecodeInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uBlockA: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apb_uBlockA;
    // apbReg->uBlockB: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apb_uBlockB;

    // dst ports
    // External->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeInverted(std::string name) :
        apb_uBlockA(("apb_uBlockA"+name).c_str())
        ,apb_uBlockB(("apb_uBlockB"+name).c_str())
        ,cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uBlockA->setTimed(nsec, mode);
        apb_uBlockB->setTimed(nsec, mode);
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uBlockA->setLogging(verbosity);
        apb_uBlockB->setLogging(verbosity);
        cpu_main->setLogging(verbosity);
    };
};
class apbDecodeChannels
{
public:
    // src ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockA;
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockB;

    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    apbDecodeChannels(std::string name, std::string srcName) :
    apb_uBlockA(("apb_uBlockA"+name).c_str(), srcName)
    ,apb_uBlockB(("apb_uBlockB"+name).c_str(), srcName)
    ,cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apb_uBlockA( apb_uBlockA );
        b->apb_uBlockA( apb_uBlockA );
        a->apb_uBlockB( apb_uBlockB );
        b->apb_uBlockB( apb_uBlockB );
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END

#endif // APBDECODE_BASE_H
