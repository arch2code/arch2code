//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=xpRtLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "apb_channel.h"

export module xpRtInh_xpRtLeaf.base;
import xpRtInh;
import common_shared_types;
using namespace xpRtInh_ns;
using namespace common_shared_types_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpRtLeafBase : public virtual blockPortBase
{
public:
    virtual ~xpRtLeafBase() = default;
    static constexpr auto RT_WIDTH = Config::RT_WIDTH;
    // dst ports
    // uNestDecode->apbReg: CPU access to registers via APB
    apb_in< apbAddrSt, apbDataSt > apbReg;


    xpRtLeafBase(std::string name, const char * variant) :
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
class xpRtLeafInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uNestDecode->apbReg: CPU access to registers via APB
    apb_out< apbAddrSt, apbDataSt > apbReg;


    xpRtLeafInverted(std::string name) :
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
class xpRtLeafChannels
{
public:
    // dst ports
    // CPU access to registers via APB
    apb_channel< apbAddrSt, apbDataSt > apbReg;


    xpRtLeafChannels(std::string name, std::string srcName) :
    apbReg(("apbReg"+name).c_str(), srcName)
    {};
    void bind( xpRtLeafBase<Config> *a, xpRtLeafInverted<Config> *b)
    {
        a->apbReg( apbReg );
        b->apbReg( apbReg );
    };
};

// GENERATED_CODE_END
