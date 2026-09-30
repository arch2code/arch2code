//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtInhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module xpRtInh_xpRtInhTop.base;
import common_shared_types;
import xpRtInh;
using namespace common_shared_types_ns;
using namespace xpRtInh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpRtInhTopBase : public virtual blockPortBase
{
public:
    virtual ~xpRtInhTopBase() = default;
    // dst ports
    // uCPU->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    xpRtInhTopBase(std::string name, const char * variant) :
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
export class xpRtInhTopInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCPU->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    xpRtInhTopInverted(std::string name) :
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
export class xpRtInhTopChannels
{
public:
    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    xpRtInhTopChannels(std::string name, std::string srcName) :
    cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( xpRtInhTopBase *a, xpRtInhTopInverted *b)
    {
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
