//

// GENERATED_CODE_PARAM --block=xpDpMid --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpDpMid.base;
import xpDpLeaf;
using namespace xpDpLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpDpMidBase : public virtual blockPortBase
{
public:
    virtual ~xpDpMidBase() = default;
    static constexpr auto DP_WIDTH = Config::DP_WIDTH;
    static constexpr auto MID_ALGO = Config::MID_ALGO;
    // src ports
    // dpIf->uSnk: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > midOut;

    // dst ports
    // uDrv->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > midIn;


    xpDpMidBase(std::string name, const char * variant) :
        midOut("midOut")
        ,midIn("midIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        midOut->setTimed(nsec, mode);
        midIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        midOut->setLogging(verbosity);
        midIn->setLogging(verbosity);
    };
    using dpPixelT = dpPixelT<Config>;
    using dpSt = dpSt<Config>;
};
export template<typename Config>
class xpDpMidInverted : public virtual blockPortBase
{
public:
    // src ports
    // dpIf->uSnk: The leaf IP's own parameterized pixel push/ack stream
    push_ack_in< dpSt<Config> > midOut;

    // dst ports
    // uDrv->dpIf: The leaf IP's own parameterized pixel push/ack stream
    push_ack_out< dpSt<Config> > midIn;


    xpDpMidInverted(std::string name) :
        midOut(("midOut"+name).c_str())
        ,midIn(("midIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        midOut->setTimed(nsec, mode);
        midIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        midOut->setLogging(verbosity);
        midIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpDpMidChannels
{
public:
    // src ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > midOut;

    // dst ports
    // The leaf IP's own parameterized pixel push/ack stream
    push_ack_channel< dpSt<Config> > midIn;


    xpDpMidChannels(std::string name, std::string srcName) :
    midOut(("midOut"+name).c_str(), srcName)
    ,midIn(("midIn"+name).c_str(), srcName)
    {};
    void bind( xpDpMidBase<Config> *a, xpDpMidInverted<Config> *b)
    {
        a->midOut( midOut );
        b->midOut( midOut );
        a->midIn( midIn );
        b->midIn( midIn );
    };
};

// GENERATED_CODE_END
