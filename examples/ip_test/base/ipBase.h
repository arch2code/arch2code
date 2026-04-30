#ifndef IP_BASE_H
#define IP_BASE_H

//copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=baseClassDecl
#include "apb_channel.h"
#include "rdy_vld_channel.h"
#include "ipIncludes.h"
#include "ip_topIncludes.h"

class ipBase : public virtual blockPortBase
{
public:
    virtual ~ipBase() = default;
    const uint64_t IP_DATA_WIDTH;
    const uint64_t IP_MEM_DEPTH;
    // dst ports
    // uSrc->ipDataIf: IP data stream
    rdy_vld_in< ipDataSt > ipDataIf;
    // uAPBDecode->apbReg: CPU access to IP registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    ipBase(std::string name, const char * variant) :
        IP_DATA_WIDTH(instanceFactory::getParam("ip", variant, "IP_DATA_WIDTH"))
        ,IP_MEM_DEPTH(instanceFactory::getParam("ip", variant, "IP_MEM_DEPTH"))
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
class ipInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uSrc->ipDataIf: IP data stream
    rdy_vld_out< ipDataSt > ipDataIf;
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
class ipChannels
{
public:
    // dst ports
    // IP data stream
    rdy_vld_channel< ipDataSt > ipDataIf;
    // CPU access to IP registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    ipChannels(std::string name, std::string srcName) :
    ipDataIf(("ipDataIf"+name).c_str(), srcName)
    ,apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( ipBase *a, ipInverted *b)
    {
        a->ipDataIf( ipDataIf );
        b->ipDataIf( ipDataIf );
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
#endif //IP_BASE_H
