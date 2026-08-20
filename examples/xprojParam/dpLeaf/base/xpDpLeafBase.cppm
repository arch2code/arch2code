//

// GENERATED_CODE_PARAM --block=xpDpLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpLeaf.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpDpLeafBase : public virtual blockPortBase
{
public:
    virtual ~xpDpLeafBase() = default;
    static constexpr auto DP_ALGO = Config::DP_ALGO;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    // src ports
    // dpIf->External: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > out;

    // dst ports
    // External->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > in;


    xpDpLeafBase(std::string name, const char * variant) :
        out("out")
        ,in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpDpLeafInverted : public virtual blockPortBase
{
public:
    // src ports
    // dpIf->External: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > out;

    // dst ports
    // External->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > in;


    xpDpLeafInverted(std::string name) :
        out(("out"+name).c_str())
        ,in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export template<typename Config>
class xpDpLeafChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > out;

    // dst ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > in;


    xpDpLeafChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( xpDpLeafBase<Config> *a, xpDpLeafInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
