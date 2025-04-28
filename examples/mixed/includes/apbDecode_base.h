#ifndef APBDECODE_BASE_H
#define APBDECODE_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

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
    // uCPU->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    apbDecodeBase(std::string name, const char * variant) :
        apb_uBlockA("apb_uBlockA")
        ,apb_uBlockB("apb_uBlockB")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uBlockA->setTimed(nsec, mode);
        apb_uBlockB->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uBlockA->setLogging(verbosity);
        apb_uBlockB->setLogging(verbosity);
        apbReg->setLogging(verbosity);
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
    // uCPU->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    apbDecodeInverted(std::string name) :
        apb_uBlockA(("apb_uBlockA"+name).c_str())
        ,apb_uBlockB(("apb_uBlockB"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apb_uBlockA->setTimed(nsec, mode);
        apb_uBlockB->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apb_uBlockA->setLogging(verbosity);
        apb_uBlockB->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
class apbDecodeChannels
{
public:
    // src ports
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockA;
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apb_uBlockB;

    // dst ports
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    apbDecodeChannels(std::string name, std::string srcName) :
    apb_uBlockA(("apb_uBlockA"+name).c_str(), srcName)
    ,apb_uBlockB(("apb_uBlockB"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( apbDecodeBase *a, apbDecodeInverted *b)
    {
        a->apb_uBlockA( apb_uBlockA );
        b->apb_uBlockA( apb_uBlockA );
        a->apb_uBlockB( apb_uBlockB );
        b->apb_uBlockB( apb_uBlockB );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //APBDECODE_BASE_H
