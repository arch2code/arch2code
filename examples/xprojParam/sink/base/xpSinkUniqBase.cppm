//

// GENERATED_CODE_PARAM --block=xpSinkUniq --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpSink_xpSinkUniq.base;
import xpSink_xpSinkUniq;
using namespace xpSink_xpSinkUniq_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpSinkUniqBase : public virtual blockPortBase
{
public:
    virtual ~xpSinkUniqBase() = default;
    static constexpr auto SK_PIXEL_WIDTH = Config::SK_PIXEL_WIDTH;
    // dst ports
    // External->skVideoIf: Parameterized pixel push/ack stream
    push_ack_in< skVideoSt<Config> > videoIn;


    xpSinkUniqBase(std::string name, const char * variant) :
        videoIn("videoIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        videoIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        videoIn->setLogging(verbosity);
    };
    using skPixelT = skPixelT<Config>;
    using skVideoSt = skVideoSt<Config>;
};
export template<typename Config>
class xpSinkUniqInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->skVideoIf: Parameterized pixel push/ack stream
    push_ack_out< skVideoSt<Config> > videoIn;


    xpSinkUniqInverted(std::string name) :
        videoIn(("videoIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        videoIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        videoIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpSinkUniqChannels
{
public:
    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< skVideoSt<Config> > videoIn;


    xpSinkUniqChannels(std::string name, std::string srcName) :
    videoIn(("videoIn"+name).c_str(), srcName)
    {};
    void bind( xpSinkUniqBase<Config> *a, xpSinkUniqInverted<Config> *b)
    {
        a->videoIn( videoIn );
        b->videoIn( videoIn );
    };
};

// GENERATED_CODE_END
