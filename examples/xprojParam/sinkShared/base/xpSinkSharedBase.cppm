//

// GENERATED_CODE_PARAM --block=xpSinkShared --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpSinkShared.base;
import xpGain;
using namespace xpGain_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpSinkSharedBase : public virtual blockPortBase
{
public:
    virtual ~xpSinkSharedBase() = default;
    static constexpr auto PIXEL_WIDTH = Config::PIXEL_WIDTH;
    // dst ports
    // External->videoIf: Parameterized pixel push/ack stream
    push_ack_in< videoSt<Config> > videoIn;


    xpSinkSharedBase(std::string name, const char * variant) :
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
    using pixel_t = pixel_t<Config>;
    using videoSt = videoSt<Config>;
};
export template<typename Config>
class xpSinkSharedInverted : public virtual blockPortBase
{
public:
    // dst ports
    // External->videoIf: Parameterized pixel push/ack stream
    push_ack_out< videoSt<Config> > videoIn;


    xpSinkSharedInverted(std::string name) :
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
class xpSinkSharedChannels
{
public:
    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<Config> > videoIn;


    xpSinkSharedChannels(std::string name, std::string srcName) :
    videoIn(("videoIn"+name).c_str(), srcName)
    {};
    void bind( xpSinkSharedBase<Config> *a, xpSinkSharedInverted<Config> *b)
    {
        a->videoIn( videoIn );
        b->videoIn( videoIn );
    };
};

// GENERATED_CODE_END
