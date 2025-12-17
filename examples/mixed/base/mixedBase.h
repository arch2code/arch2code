#ifndef MIXED_BASE_H
#define MIXED_BASE_H

// GENERATED_CODE_PARAM --block=mixed
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "notify_ack_channel.h"
#include "rdy_vld_channel.h"
#include "req_ack_channel.h"
#include "mixedIncludes.h"
#include "mixedBlockCIncludes.h"

class mixedBase : public virtual blockPortBase
{
public:
    virtual ~mixedBase() = default;
    // dst ports
    // uCPU->apbReg: CPU access to SoC registers in the design
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    mixedBase(std::string name, const char * variant) :
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
class mixedInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCPU->apbReg: CPU access to SoC registers in the design
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    mixedInverted(std::string name) :
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
class mixedChannels
{
public:
    // dst ports
    // CPU access to SoC registers in the design
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    mixedChannels(std::string name, std::string srcName) :
    cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( mixedBase *a, mixedInverted *b)
    {
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END

#endif // MIXED_BASE_H
