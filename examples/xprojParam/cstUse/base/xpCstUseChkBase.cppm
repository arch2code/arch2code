//

// GENERATED_CODE_PARAM --block=xpCstUseChk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstUse_xpCstUseChk.base;
import xpCstIp;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstUseChkBase : public virtual blockPortBase
{
public:
    virtual ~xpCstUseChkBase() = default;
    static constexpr auto CS_PIXEL_WIDTH = Config::CS_PIXEL_WIDTH;
    // dst ports
    // uDut->csDutIf: The IP's own parameterized pixel push/ack stream
    push_ack_in< csDutSt<Config> > in;


    xpCstUseChkBase(std::string name, const char * variant) :
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
    using csPixelT = csPixelT<Config>;
    using csDutSt = csDutSt<Config>;
};
export template<typename Config>
class xpCstUseChkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDut->csDutIf: The IP's own parameterized pixel push/ack stream
    push_ack_out< csDutSt<Config> > in;


    xpCstUseChkInverted(std::string name) :
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
class xpCstUseChkChannels
{
public:
    // dst ports
    // The IP's own parameterized pixel push/ack stream
    push_ack_channel< csDutSt<Config> > in;


    xpCstUseChkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpCstUseChkBase<Config> *a, xpCstUseChkInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
