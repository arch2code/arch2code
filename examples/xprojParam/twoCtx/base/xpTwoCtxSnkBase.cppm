//

// GENERATED_CODE_PARAM --block=xpTwoCtxSnk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpTwoCtx_xpTwoCtxSnk.base;
import xpTwoCtx;
using namespace xpTwoCtx_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpTwoCtxSnkBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxSnkBase() = default;
    static constexpr auto TC_GAIN = Config::TC_GAIN;
    // dst ports
    // uDut->tcIf: This file's own parameterized stream
    push_ack_in< tcSt<Config> > in;


    xpTwoCtxSnkBase(std::string name, const char * variant) :
        in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        in->setLogging(verbosity);
    };
    static constexpr auto TC_GAIN_X2 = Config::TC_GAIN * 2;
    using tcValT = tcValT<Config>;
    using tcSt = tcSt<Config>;
};
export template<typename Config>
class xpTwoCtxSnkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDut->tcIf: This file's own parameterized stream
    push_ack_out< tcSt<Config> > in;


    xpTwoCtxSnkInverted(std::string name) :
        in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        in->setLogging(verbosity);
    };
};
export template<typename Config>
class xpTwoCtxSnkChannels
{
public:
    // dst ports
    // This file's own parameterized stream
    push_ack_channel< tcSt<Config> > in;


    xpTwoCtxSnkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpTwoCtxSnkBase<Config> *a, xpTwoCtxSnkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
