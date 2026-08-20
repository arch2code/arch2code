//

// GENERATED_CODE_PARAM --block=xpCstChkOwn --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstBind_xpCstChkOwn.base;
import xpCstBind_xpCstSup;
import xpCstIp;
using namespace xpCstBind_xpCstSup_ns;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstChkOwnBase : public virtual blockPortBase
{
public:
    virtual ~xpCstChkOwnBase() = default;
    static constexpr auto CS_OWN_WIDTH = Config::CS_OWN_WIDTH;
    // dst ports
    // uDutB->csOwnIf: Own-knob supporting blocks' own parameterized pixel push/ack stream
    push_ack_in< csOwnSt<Config> > in;


    xpCstChkOwnBase(std::string name, const char * variant) :
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
    using csOwnPixelT = csOwnPixelT<Config>;
    using csOwnSt = csOwnSt<Config>;
};
export template<typename Config>
class xpCstChkOwnInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDutB->csOwnIf: Own-knob supporting blocks' own parameterized pixel push/ack stream
    push_ack_out< csOwnSt<Config> > in;


    xpCstChkOwnInverted(std::string name) :
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
class xpCstChkOwnChannels
{
public:
    // dst ports
    // Own-knob supporting blocks' own parameterized pixel push/ack stream
    push_ack_channel< csOwnSt<Config> > in;


    xpCstChkOwnChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpCstChkOwnBase<Config> *a, xpCstChkOwnInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
