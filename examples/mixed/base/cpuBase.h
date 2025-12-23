#ifndef CPU_BASE_H
#define CPU_BASE_H

// GENERATED_CODE_PARAM --block=cpu
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "mixedIncludes.h"

class cpuBase : public virtual blockPortBase
{
public:
    virtual ~cpuBase() = default;
    // src ports
    // apbReg->u_mixed: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    cpuBase(std::string name, const char * variant) :
        cpu_main("cpu_main")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cpu_main->setLogging(verbosity);
    };
};
class cpuInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->u_mixed: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    cpuInverted(std::string name) :
        cpu_main(("cpu_main"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        cpu_main->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        cpu_main->setLogging(verbosity);
    };
};
class cpuChannels
{
public:
    // src ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    cpuChannels(std::string name, std::string srcName) :
    cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( cpuBase *a, cpuInverted *b)
    {
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END

#endif // CPU_BASE_H
