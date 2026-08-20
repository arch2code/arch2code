//

// GENERATED_CODE_PARAM --block=xpMtxDstPar --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxIp_xpMtxDstPar.base;
import xpMtxIp;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpMtxDstParBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxDstParBase() = default;
    static constexpr auto MI_DST_WIDTH = Config::MI_DST_WIDTH;
    // dst ports
    // External->miDstParIf: Consumer port interface, parameterized payload
    push_ack_in< miDstParSt<Config> > in;


    xpMtxDstParBase(std::string name, const char * variant) :
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
    using miDstPixelT = miDstPixelT<Config>;
    using miDstParSt = miDstParSt<Config>;
};
export template<typename Config>
class xpMtxDstParInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->miDstParIf: Consumer port interface, parameterized payload
    push_ack_out< miDstParSt<Config> > in;


    xpMtxDstParInverted(std::string name) :
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
class xpMtxDstParChannels
{
public:
    // dst ports
    // Consumer port interface, parameterized payload
    push_ack_channel< miDstParSt<Config> > in;


    xpMtxDstParChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpMtxDstParBase<Config> *a, xpMtxDstParInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
