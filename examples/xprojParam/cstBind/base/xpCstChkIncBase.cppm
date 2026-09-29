//

// GENERATED_CODE_PARAM --block=xpCstChkInc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstBind_xpCstChkInc.base;
import xpCstBind_xpCstSup;
import xpCstIp;
using namespace xpCstBind_xpCstSup_ns;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstChkIncBase : public virtual blockPortBase
{
public:
    virtual ~xpCstChkIncBase() = default;
    static constexpr auto CS_PIXEL_WIDTH = Config::CS_PIXEL_WIDTH;
    // dst ports
    // uDutA->csIncIf: Include-scope supporting blocks' own parameterized pixel push/ack stream
    push_ack_in< csIncSt<Config> > in;


    xpCstChkIncBase(std::string name, const char * variant) :
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
    using csIncPixelT = csIncPixelT<Config>;
    using csDutSt = csDutSt<Config>;
    using csIncSt = csIncSt<Config>;
};
export template<typename Config>
class xpCstChkIncInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uDutA->csIncIf: Include-scope supporting blocks' own parameterized pixel push/ack stream
    push_ack_out< csIncSt<Config> > in;


    xpCstChkIncInverted(std::string name) :
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
class xpCstChkIncChannels
{
public:
    // dst ports
    // Include-scope supporting blocks' own parameterized pixel push/ack stream
    push_ack_channel< csIncSt<Config> > in;


    xpCstChkIncChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( xpCstChkIncBase<Config> *a, xpCstChkIncInverted<Config> *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
