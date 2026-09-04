//

// GENERATED_CODE_PARAM --block=xpDpWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpTop_xpDpWrap.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpDpWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpDpWrapBase() = default;
    static constexpr auto MID_ALGO = Config::MID_ALGO;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;


    xpDpWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpDpWrapInverted : public virtual blockPortBase
{
public:


    xpDpWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export template<typename Config>
class xpDpWrapChannels
{
public:


    xpDpWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpDpWrapBase<Config> *a, xpDpWrapInverted<Config> *b)
    {
    };
};

// GENERATED_CODE_END
