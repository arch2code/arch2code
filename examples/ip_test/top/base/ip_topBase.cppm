//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ip_top --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"
#include "push_ack_channel.h"

export module ip_test_ip_top.base;
import common_shared_types;
import ip_test_ip_top;
import ip_test_src;
import ip;
import ipBridge;
using namespace common_shared_types_ns;
using namespace ip_test_ip_top_ns;
using namespace ip_test_src_ns;
using namespace ip_ns;
using namespace ipBridge_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class ip_topBase : public virtual blockPortBase
{
public:
    virtual ~ip_topBase() = default;
    // dst ports
    // uCPU->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > cpu_main;


    ip_topBase(std::string name, const char * variant) :
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
export class ip_topInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCPU->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > cpu_main;


    ip_topInverted(std::string name) :
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
export class ip_topChannels
{
public:
    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > cpu_main;


    ip_topChannels(std::string name, std::string srcName) :
    cpu_main(("cpu_main"+name).c_str(), srcName)
    {};
    void bind( ip_topBase *a, ip_topInverted *b)
    {
        a->cpu_main( cpu_main );
        b->cpu_main( cpu_main );
    };
};

// GENERATED_CODE_END
