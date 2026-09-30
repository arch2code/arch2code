//

// GENERATED_CODE_PARAM --block=xpCstUseSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstUse_xpCstUseSrc.base;
import xpCstIp;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstUseSrcBase : public virtual blockPortBase
{
public:
    virtual ~xpCstUseSrcBase() = default;
    static constexpr auto CS_PIXEL_WIDTH = Config::CS_PIXEL_WIDTH;
    // src ports
    // csDutIf->uDut: The IP's own parameterized pixel push/ack stream
    push_ack_out< csDutSt<Config> > out;


    xpCstUseSrcBase(std::string name, const char * variant) :
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
    using csPixelT = csPixelT<Config>;
    using csDutSt = csDutSt<Config>;
};
export template<typename Config>
class xpCstUseSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // csDutIf->uDut: The IP's own parameterized pixel push/ack stream
    push_ack_in< csDutSt<Config> > out;


    xpCstUseSrcInverted(std::string name) :
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
class xpCstUseSrcChannels
{
public:
    // src ports
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<Config> > out;


    xpCstUseSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpCstUseSrcBase<Config> *a, xpCstUseSrcInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
