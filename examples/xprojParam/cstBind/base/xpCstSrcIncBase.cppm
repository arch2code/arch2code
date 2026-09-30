//

// GENERATED_CODE_PARAM --block=xpCstSrcInc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpCstBind_xpCstSrcInc.base;
import xpCstBind_xpCstSup;
import xpCstIp;
using namespace xpCstBind_xpCstSup_ns;
using namespace xpCstIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpCstSrcIncBase : public virtual blockPortBase
{
public:
    virtual ~xpCstSrcIncBase() = default;
    static constexpr auto CS_PIXEL_WIDTH = Config::CS_PIXEL_WIDTH;
    // src ports
    // csIncIf->uDutA: Include-scope supporting blocks' own parameterized pixel push/ack stream
    push_ack_out< csIncSt<Config> > out;


    xpCstSrcIncBase(std::string name, const char * variant) :
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
    using csIncPixelT = csIncPixelT<Config>;
    using csDutSt = csDutSt<Config>;
    using csIncSt = csIncSt<Config>;
};
export template<typename Config>
class xpCstSrcIncInverted : public virtual blockPortBase
{
public:
    // src ports
    // csIncIf->uDutA: Include-scope supporting blocks' own parameterized pixel push/ack stream
    push_ack_in< csIncSt<Config> > out;


    xpCstSrcIncInverted(std::string name) :
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
class xpCstSrcIncChannels
{
public:
    // src ports
    // Include-scope supporting blocks' own parameterized pixel push/ack stream
    push_ack_channel< csIncSt<Config> > out;


    xpCstSrcIncChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( xpCstSrcIncBase<Config> *a, xpCstSrcIncInverted<Config> *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
