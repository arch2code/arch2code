#ifndef IP_BASE_H
#define IP_BASE_H

//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "push_ack_channel.h"
import ip;
using namespace ip_ns;
import ip_top;
using namespace ip_top_ns;

template<typename Config>
class ipBase : public virtual blockPortBase
{
public:
    virtual ~ipBase() = default;
    const uint64_t IP_DATA_WIDTH;
    const uint64_t IP_MEM_DEPTH;
    const uint64_t IP_NONCONST_DEPTH;
    // dst ports
    // uSrc->ipDataIf: IP data push/ack stream
    push_ack_in< ipDataSt<Config> > ipDataIf;
    // uAPBDecode->apbReg: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    ipBase(std::string name, const char * variant) :
        IP_DATA_WIDTH(instanceFactory::getParam("ip", variant, "IP_DATA_WIDTH"))
        ,IP_MEM_DEPTH(instanceFactory::getParam("ip", variant, "IP_MEM_DEPTH"))
        ,IP_NONCONST_DEPTH(instanceFactory::getParam("ip", variant, "IP_NONCONST_DEPTH"))
        ,ipDataIf("ipDataIf")
        ,apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipDataIf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ipDataIf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
template<typename Config>
class ipInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uSrc->ipDataIf: IP data push/ack stream
    push_ack_out< ipDataSt<Config> > ipDataIf;
    // uAPBDecode->apbReg: CPU access to IP registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    ipInverted(std::string name) :
        ipDataIf(("ipDataIf"+name).c_str())
        ,apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipDataIf->setTimed(nsec, mode);
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ipDataIf->setLogging(verbosity);
        apbReg->setLogging(verbosity);
    };
};
template<typename Config>
class ipChannels
{
public:
    // dst ports
    // IP data push/ack stream
    push_ack_channel< ipDataSt<Config> > ipDataIf;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    ipChannels(std::string name, std::string srcName) :
    ipDataIf(("ipDataIf"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( ipBase<Config> *a, ipInverted<Config> *b)
    {
        a->ipDataIf( ipDataIf );
        b->ipDataIf( ipDataIf );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
#endif //IP_BASE_H
