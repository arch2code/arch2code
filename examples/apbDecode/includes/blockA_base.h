#ifndef BLOCKA_BASE_H
#define BLOCKA_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "apbDecodeIncludes.h"

class blockABase : public virtual blockPortBase
{
public:
    virtual ~blockABase() = default;
    // dst ports
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    blockABase(std::string name, const char * variant) :
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
class blockAInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uAPBDecode->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    blockAInverted(std::string name) :
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
class blockAChannels
{
public:
    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    blockAChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( blockABase *a, blockAInverted *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //BLOCKA_BASE_H
