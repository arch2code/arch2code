//

// GENERATED_CODE_PARAM --block=xpTwoCtxSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpTwoCtx_xpTwoCtxSrc.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpTwoCtxSrcBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxSrcBase() = default;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    // src ports
    // dpIf->uDut: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out;


    xpTwoCtxSrcBase(std::string name, const char * variant) :
        out("out")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
    };
    static constexpr auto DP_WIDTH_X2 = Config::DP_WIDTH * 2;
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpTwoCtxSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // dpIf->uDut: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out;


    xpTwoCtxSrcInverted(std::string name) :
        out(("out"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
    };
};
export template<typename Config>
class xpTwoCtxSrcChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out;


    xpTwoCtxSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpTwoCtxSrcBase<Config> *a, xpTwoCtxSrcInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
