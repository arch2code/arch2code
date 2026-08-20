//

// GENERATED_CODE_PARAM --block=xpCstDut --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstIp_xpCstDut.base;
import xpCstIp;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstDutBase : public virtual blockPortBase
{
public:
    virtual ~xpCstDutBase() = default;
    static constexpr auto CS_PIXEL_WIDTH = Config::CS_PIXEL_WIDTH;
    // src ports
    // csDutIf->External: The IP's own parameterized pixel push/ack stream
    push_ack_out< csDutSt<Config> > out;

    // dst ports
    // External->csDutIf: The IP's own parameterized pixel push/ack stream
    push_ack_in< csDutSt<Config> > in;


    xpCstDutBase(std::string name, const char * variant) :
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
    using csPixelT = csPixelT<Config>;
    using csDutSt = csDutSt<Config>;
};
export template<typename Config>
class xpCstDutInverted : public virtual blockPortBase
{
public:
    // src ports
    // csDutIf->External: The IP's own parameterized pixel push/ack stream
    push_ack_in< csDutSt<Config> > out;

    // dst ports
    // External->csDutIf: The IP's own parameterized pixel push/ack stream
    push_ack_out< csDutSt<Config> > in;


    xpCstDutInverted(std::string name) :
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
class xpCstDutChannels
{
public:
    // src ports
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<Config> > out;

    // dst ports
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<Config> > in;


    xpCstDutChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    ,in(("in"+name).c_str(), srcName)
    {};
    void bind( xpCstDutBase<Config> *a, xpCstDutInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
