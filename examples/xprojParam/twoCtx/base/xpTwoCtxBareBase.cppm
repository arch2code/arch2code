//

// GENERATED_CODE_PARAM --block=xpTwoCtxBare --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpTwoCtx_xpTwoCtxBare.base;
import xpTwoCtx;
import xpDpLeaf;
using namespace xpTwoCtx_ns;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpTwoCtxBareBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxBareBase() = default;
    static constexpr auto TC_GAIN = Config::TC_GAIN;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    // dst ports
    // uLitSrc->litIf: Literal, non-parameterizable stream
    push_ack_in< litSt > litIn;


    xpTwoCtxBareBase(std::string name, const char * variant) :
        litIn("litIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        litIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        litIn->setLogging(verbosity);
    };
    static constexpr auto TC_GAIN_X2 = Config::TC_GAIN_X2;
    using dpPixelT = dpPixelT<Config>;
    using tcValT = tcValT<Config>;
    using dpSt = dpSt<Config>;
    using tcSt = tcSt<Config>;
};
export template<typename Config>
class xpTwoCtxBareInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uLitSrc->litIf: Literal, non-parameterizable stream
    push_ack_out< litSt > litIn;


    xpTwoCtxBareInverted(std::string name) :
        litIn(("litIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        litIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        litIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpTwoCtxBareChannels
{
public:
    // dst ports
    // Literal, non-parameterizable stream
    push_ack_channel< litSt > litIn;


    xpTwoCtxBareChannels(std::string name, std::string srcName) :
    litIn(("litIn"+name).c_str(), srcName)
    {};
    void bind( xpTwoCtxBareBase<Config> *a, xpTwoCtxBareInverted<Config> *b)
    {
        a->litIn( litIn );
        b->litIn( litIn );
    };
};

// GENERATED_CODE_END
