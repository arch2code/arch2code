//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=cpu --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module cpu.base;
import shared_types;
using namespace shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class cpuBase : public virtual blockPortBase
{
public:
    virtual ~cpuBase() = default;
    // src ports
    // apbReg->External: CPU access to registers via APB
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
export class cpuInverted : public virtual blockPortBase
{
public:
    // src ports
    // apbReg->External: CPU access to registers via APB
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
export class cpuChannels
{
public:
    // src ports
    // CPU access to registers via APB
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
