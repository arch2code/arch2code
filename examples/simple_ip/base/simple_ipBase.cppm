//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=simple_ip --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "push_ack_channel.h"

export module simple_ip.base;
import common_shared_types;
import simple_ip;
import ip;
using namespace common_shared_types_ns;
using namespace simple_ip_ns;
using namespace ip_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class simple_ipBase : public virtual blockPortBase
{
public:
    virtual ~simple_ipBase() = default;
    // dst ports
    // uCPU->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    simple_ipBase(std::string name, const char * variant) :
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
export class simple_ipInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCPU->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    simple_ipInverted(std::string name) :
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
export class simple_ipChannels
{
public:
    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    simple_ipChannels(std::string name, std::string srcName) :
    cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( simple_ipBase *a, simple_ipInverted *b)
    {
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
