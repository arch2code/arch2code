#ifndef CPU_BASE_H
#define CPU_BASE_H

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "mixedIncludes.h"

class cpuBase : public virtual blockPortBase
{
public:
    virtual ~cpuBase() = default;
    // src ports
    // apbReg->uAPBDecode: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > apbReg;


    cpuBase(std::string name, const char * variant) :
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
class cpuInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->uAPBDecode: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > apbReg;


    cpuInverted(std::string name) :
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
class cpuChannels
{
public:
    // src ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    cpuChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( cpuBase *a, cpuInverted *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END

#endif //CPU_BASE_H
