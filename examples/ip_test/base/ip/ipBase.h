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

template<typename Config>
class ipBase : public virtual blockPortBase
{
public:
    virtual ~ipBase() = default;
    static constexpr auto IP_DATA_WIDTH = Config::IP_DATA_WIDTH;
    static constexpr auto IP_MEM_DEPTH = Config::IP_MEM_DEPTH;
    static constexpr auto IP_NONCONST_DEPTH = Config::IP_NONCONST_DEPTH;
    // dst ports
    // uSrc->ipDataIf: IP data push/ack stream
    push_ack_in< ipDataSt<Config> > ipDataIf;
    // uAPBDecode->ipReg: Register bus the ip block consumes
    apb_in< ipRegAddrSt, ipRegDataSt > regs;


    ipBase(std::string name, const char * variant) :
        ipDataIf("ipDataIf")
        ,regs("regs")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipDataIf->setTimed(nsec, mode);
        regs->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ipDataIf->setLogging(verbosity);
        regs->setLogging(verbosity);
    };
    static constexpr auto IP_DATA_WIDTH_X2 = Config::IP_DATA_WIDTH_X2;
    static constexpr auto IP_DATA_WIDTH_X4 = Config::IP_DATA_WIDTH_X4;
    static constexpr auto IP_MEM_DEPTH_X2 = Config::IP_MEM_DEPTH_X2;
    static constexpr auto IP_MEM_DEPTH_X4 = Config::IP_MEM_DEPTH_X4;
    using ipDataT = ipDataT<Config>;
    using ipMemAddrT = ipMemAddrT<Config>;
    using ipDerivedWidthT = ipDerivedWidthT<Config>;
    using ipDerivedMemAddrT = ipDerivedMemAddrT<Config>;
    using ipDataSt = ipDataSt<Config>;
    using ipCfgSt = ipCfgSt<Config>;
    using ipMemSt = ipMemSt<Config>;
    using ipMemAddrSt = ipMemAddrSt<Config>;
    using ipBurstSt = ipBurstSt<Config>;
    using ipDerivedMemAddrSt = ipDerivedMemAddrSt<Config>;
    using ipParamNestedSt = ipParamNestedSt<Config>;
};
template<typename Config>
class ipInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uSrc->ipDataIf: IP data push/ack stream
    push_ack_out< ipDataSt<Config> > ipDataIf;
    // uAPBDecode->ipReg: Register bus the ip block consumes
    apb_out< ipRegAddrSt, ipRegDataSt > regs;


    ipInverted(std::string name) :
        ipDataIf(("ipDataIf"+name).c_str())
        ,regs(("regs"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        ipDataIf->setTimed(nsec, mode);
        regs->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        ipDataIf->setLogging(verbosity);
        regs->setLogging(verbosity);
    };
};
template<typename Config>
class ipChannels
{
public:
    // dst ports
    // IP data push/ack stream
    push_ack_channel< ipDataSt<Config> > ipDataIf;
    // Register bus the ip block consumes
    apb_channel< ipRegAddrSt, ipRegDataSt > regs;


    ipChannels(std::string name, std::string srcName) :
    ipDataIf(("ipDataIf"+name).c_str(), srcName)
    ,regs(("regs"+name).c_str(), srcName)
    {};
    void bind( ipBase<Config> *a, ipInverted<Config> *b)
    {
        a->ipDataIf( ipDataIf );
        b->ipDataIf( ipDataIf );
        a->regs( regs );
        b->regs( regs );
    };
};

// GENERATED_CODE_END
#endif //IP_BASE_H
