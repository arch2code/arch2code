//

// GENERATED_CODE_PARAM --block=xpGainUniq --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpGain_xpGainUniq.base;
import xpGain_xpGainUniq;
using namespace xpGain_xpGainUniq_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpGainUniqBase : public virtual blockPortBase
{
public:
    virtual ~xpGainUniqBase() = default;
    static constexpr auto GN_PIXEL_WIDTH = Config::GN_PIXEL_WIDTH;
    // src ports
    // gnVideoIf->External: Parameterized pixel push/ack stream
    push_ack_out< gnVideoSt<Config> > videoOut;


    xpGainUniqBase(std::string name, const char * variant) :
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
    using gnPixelT = gnPixelT<Config>;
    using gnVideoSt = gnVideoSt<Config>;
};
export template<typename Config>
class xpGainUniqInverted : public virtual blockPortBase
{
public:
    // src ports
    // gnVideoIf->External: Parameterized pixel push/ack stream
    push_ack_in< gnVideoSt<Config> > videoOut;


    xpGainUniqInverted(std::string name) :
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
class xpGainUniqChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< gnVideoSt<Config> > videoOut;


    xpGainUniqChannels(std::string name, std::string srcName) :
    videoOut(("videoOut"+name).c_str(), srcName)
    {};
    void bind( xpGainUniqBase<Config> *a, xpGainUniqInverted<Config> *b)
    {
        a->videoOut( videoOut );
        b->videoOut( videoOut );
    };
};

// GENERATED_CODE_END
