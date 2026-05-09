#ifndef IP_TOP_BASE_H
#define IP_TOP_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip_top
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "push_ack_channel.h"
import ip_top;
using namespace ip_top_ns;
import ip;
using namespace ip_ns;

class ip_topBase : public virtual blockPortBase
{
public:
    virtual ~ip_topBase() = default;
    // dst ports
    // uCPU->apbReg: CPU access to IP registers via APB
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
class ip_topInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uCPU->apbReg: CPU access to IP registers via APB
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
class ip_topChannels
{
public:
    // dst ports
    // CPU access to IP registers via APB
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


// Force-link function (active modules-mode anchor). See plan-block-registration.md.
void force_link_ip_top();
// GENERATED_CODE_END
#endif //IP_TOP_BASE_H
