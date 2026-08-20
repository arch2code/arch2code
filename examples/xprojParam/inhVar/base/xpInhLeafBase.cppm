//

// GENERATED_CODE_PARAM --block=xpInhLeaf --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpInhVar_xpInhLeaf.base;
import xpInhVar_xpInhCont;
using namespace xpInhVar_xpInhCont_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpInhLeafBase : public virtual blockPortBase
{
public:
    virtual ~xpInhLeafBase() = default;
    static constexpr auto INH_ALGO = Config::INH_ALGO;
    static constexpr auto INH_WIDTH = Config::INH_WIDTH;
    // src ports
    // inhIf->uLeafB: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > out;

    // dst ports
    // uLeafA->inhIf: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > in;


    xpInhLeafBase(std::string name, const char * variant) :
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
    using inhPixelT = inhPixelT<Config>;
    using inhSt = inhSt<Config>;
};
export template<typename Config>
class xpInhLeafInverted : public virtual blockPortBase
{
public:
    // src ports
    // inhIf->uLeafB: Parameterized pixel push/ack stream
    push_ack_in< inhSt<Config> > out;

    // dst ports
    // uLeafA->inhIf: Parameterized pixel push/ack stream
    push_ack_out< inhSt<Config> > in;


    xpInhLeafInverted(std::string name) :
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
class xpInhLeafChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > out;

    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< inhSt<Config> > in;


    xpInhLeafChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( xpInhLeafBase<Config> *a, xpInhLeafInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
