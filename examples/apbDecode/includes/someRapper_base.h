#ifndef SOMERAPPER_BASE_H
#define SOMERAPPER_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=someRapper
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "apbDecodeIncludes.h"

class someRapperBase : public virtual blockPortBase
{
public:
    virtual ~someRapperBase() = default;
    // src ports

    // dst ports
    // uCPU->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    someRapperBase(std::string name, const char * variant) :
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
class someRapperInverted : public virtual blockPortBase
{
public:
    // src ports

    // dst ports
    // uCPU->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    someRapperInverted(std::string name) :
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
class someRapperChannels
{
public:
    // src ports

    // dst ports
    //   apbReg
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    someRapperChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( someRapperBase *a, someRapperInverted *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //SOMERAPPER_BASE_H
