//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module xpRtInh_xpRtWrap.base;
import common_shared_types;
import xpRtInh;
using namespace common_shared_types_ns;
using namespace xpRtInh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpRtWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpRtWrapBase() = default;
    static constexpr auto RT_WIDTH = Config::RT_WIDTH;
    // dst ports
    // uPrimeDecode->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    xpRtWrapBase(std::string name, const char * variant) :
        apbReg("apbReg")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg->setLogging(verbosity);
    };
    using cfgDataT = cfgDataT<Config>;
    using cfgSt = cfgSt<Config>;
};
export template<typename Config>
class xpRtWrapInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uPrimeDecode->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    xpRtWrapInverted(std::string name) :
        apbReg(("apbReg"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        apbReg->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        apbReg->setLogging(verbosity);
    };
};
export template<typename Config>
class xpRtWrapChannels
{
public:
    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    xpRtWrapChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( xpRtWrapBase<Config> *a, xpRtWrapInverted<Config> *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
