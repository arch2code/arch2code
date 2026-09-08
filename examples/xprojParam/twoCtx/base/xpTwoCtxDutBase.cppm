//

// GENERATED_CODE_PARAM --block=xpTwoCtxDut --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpTwoCtx_xpTwoCtxDut.base;
import xpDpLeaf;
import xpTwoCtx;
using namespace xpDpLeaf_ns;
using namespace xpTwoCtx_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpTwoCtxDutBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxDutBase() = default;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    static constexpr auto TC_GAIN = Config::TC_GAIN;
    // src ports
    // tcIf->uSnk: This file's own parameterized stream
    push_ack_out< tcSt<Config> > valOut;

    // dst ports
    // uSrc->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > in;


    xpTwoCtxDutBase(std::string name, const char * variant) :
        valOut("valOut")
        ,in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        valOut->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        valOut->setLogging(verbosity);
        in->setLogging(verbosity);
    };
    static constexpr auto TC_GAIN_X2 = Config::TC_GAIN * 2;
    static constexpr auto DP_WIDTH_X2 = Config::DP_WIDTH * 2;
    using dpPixelT = dpPixelT<Config>;
    using tcValT = tcValT<Config>;
    using dpSt = dpSt<Config>;
    using tcSt = tcSt<Config>;
};
export template<typename Config>
class xpTwoCtxDutInverted : public virtual blockPortBase
{
public:
    // src ports
    // tcIf->uSnk: This file's own parameterized stream
    push_ack_in< tcSt<Config> > valOut;

    // dst ports
    // uSrc->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > in;


    xpTwoCtxDutInverted(std::string name) :
        valOut(("valOut"+name).c_str())
        ,in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        valOut->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        valOut->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export template<typename Config>
class xpTwoCtxDutChannels
{
public:
    // src ports
    // This file's own parameterized stream
    push_ack_channel< tcSt<Config> > valOut;

    // dst ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > in;


    xpTwoCtxDutChannels(std::string name, std::string srcName) :
    valOut(("valOut"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( xpTwoCtxDutBase<Config> *a, xpTwoCtxDutInverted<Config> *b)
    {
        a->valOut( valOut );
        b->valOut( valOut );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
