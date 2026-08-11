//

// GENERATED_CODE_PARAM --block=xpFilter --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpFilter.base;
import xpFilter;
using namespace xpFilter_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpFilterBase : public virtual blockPortBase
{
public:
    virtual ~xpFilterBase() = default;
    static constexpr auto PIXEL_WIDTH = Config::PIXEL_WIDTH;
    // src ports
    // videoIf->External: Parameterized pixel push/ack stream
    push_ack_out< videoSt<Config> > videoOut;

    // dst ports
    // External->videoIf: Parameterized pixel push/ack stream
    push_ack_in< videoSt<Config> > videoIn;


    xpFilterBase(std::string name, const char * variant) :
        videoOut("videoOut")
        ,videoIn("videoIn")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        videoOut->setTimed(nsec, mode);
        videoIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        videoOut->setLogging(verbosity);
        videoIn->setLogging(verbosity);
    };
    using pixel_t = pixel_t<Config>;
    using videoSt = videoSt<Config>;
};
export template<typename Config>
class xpFilterInverted : public virtual blockPortBase
{
public:
    // src ports
    // videoIf->External: Parameterized pixel push/ack stream
    push_ack_in< videoSt<Config> > videoOut;

    // dst ports
    // External->videoIf: Parameterized pixel push/ack stream
    push_ack_out< videoSt<Config> > videoIn;


    xpFilterInverted(std::string name) :
        videoOut(("videoOut"+name).c_str())
        ,videoIn(("videoIn"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        videoOut->setTimed(nsec, mode);
        videoIn->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        videoOut->setLogging(verbosity);
        videoIn->setLogging(verbosity);
    };
};
export template<typename Config>
class xpFilterChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<Config> > videoOut;

    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<Config> > videoIn;


    xpFilterChannels(std::string name, std::string srcName) :
    videoOut(("videoOut"+name).c_str(), srcName)
    ,videoIn(("videoIn"+name).c_str(), srcName)
    {};
    void bind( xpFilterBase<Config> *a, xpFilterInverted<Config> *b)
    {
        a->videoOut( videoOut );
        b->videoOut( videoOut );
        a->videoIn( videoIn );
        b->videoIn( videoIn );
    };
};

// GENERATED_CODE_END
