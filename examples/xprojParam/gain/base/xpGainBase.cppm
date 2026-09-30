//

// GENERATED_CODE_PARAM --block=xpGain --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpGain.base;
import xpGain;
using namespace xpGain_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpGainBase : public virtual blockPortBase
{
public:
    virtual ~xpGainBase() = default;
    static constexpr auto PIXEL_WIDTH = Config::PIXEL_WIDTH;
    // src ports
    // videoIf->External: Parameterized pixel push/ack stream
    push_ack_out< videoSt<Config> > videoOut;


    xpGainBase(std::string name, const char * variant) :
        videoOut("videoOut")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        videoOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        videoOut->setLogging(verbosity);
    };
    using pixel_t = pixel_t<Config>;
    using videoSt = videoSt<Config>;
};
export template<typename Config>
class xpGainInverted : public virtual blockPortBase
{
public:
    // src ports
    // videoIf->External: Parameterized pixel push/ack stream
    push_ack_in< videoSt<Config> > videoOut;


    xpGainInverted(std::string name) :
        videoOut(("videoOut"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        videoOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        videoOut->setLogging(verbosity);
    };
};
export template<typename Config>
class xpGainChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< videoSt<Config> > videoOut;


    xpGainChannels(std::string name, std::string srcName) :
    videoOut(("videoOut"+name).c_str(), srcName)
    {};
    void bind( xpGainBase<Config> *a, xpGainInverted<Config> *b)
    {
        a->videoOut( videoOut );
        b->videoOut( videoOut );
    };
};

// GENERATED_CODE_END
