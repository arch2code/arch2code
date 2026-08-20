//

// GENERATED_CODE_PARAM --block=xpCstSrcOwn --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstBind_xpCstSrcOwn.base;
import xpCstBind_xpCstSup;
import xpCstIp;
using namespace xpCstBind_xpCstSup_ns;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstSrcOwnBase : public virtual blockPortBase
{
public:
    virtual ~xpCstSrcOwnBase() = default;
    static constexpr auto CS_OWN_WIDTH = Config::CS_OWN_WIDTH;
    // src ports
    // csOwnIf->uDutB: Own-knob supporting blocks' own parameterized pixel push/ack stream
    push_ack_out< csOwnSt<Config> > out;


    xpCstSrcOwnBase(std::string name, const char * variant) :
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
    using csOwnPixelT = csOwnPixelT<Config>;
    using csOwnSt = csOwnSt<Config>;
};
export template<typename Config>
class xpCstSrcOwnInverted : public virtual blockPortBase
{
public:
    // src ports
    // csOwnIf->uDutB: Own-knob supporting blocks' own parameterized pixel push/ack stream
    push_ack_in< csOwnSt<Config> > out;


    xpCstSrcOwnInverted(std::string name) :
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
class xpCstSrcOwnChannels
{
public:
    // src ports
    // Own-knob supporting blocks' own parameterized pixel push/ack stream
    push_ack_channel< csOwnSt<Config> > out;


    xpCstSrcOwnChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpCstSrcOwnBase<Config> *a, xpCstSrcOwnInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
