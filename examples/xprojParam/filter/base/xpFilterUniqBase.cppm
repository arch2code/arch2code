//

// GENERATED_CODE_PARAM --block=xpFilterUniq --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpFilter_xpFilterUniq.base;
import xpFilter_xpFilterUniq;
using namespace xpFilter_xpFilterUniq_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export template<typename Config>
class xpFilterUniqBase : public virtual blockPortBase
{
public:
    virtual ~xpFilterUniqBase() = default;
    static constexpr auto FL_PIXEL_WIDTH = Config::FL_PIXEL_WIDTH;
    // src ports
    // flVideoIf->External: Parameterized pixel push/ack stream
    push_ack_out< flVideoSt<Config> > videoOut;

    // dst ports
    // External->flVideoIf: Parameterized pixel push/ack stream
    push_ack_in< flVideoSt<Config> > videoIn;


    xpFilterUniqBase(std::string name, const char * variant) :
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
    using flPixelT = flPixelT<Config>;
    using flVideoSt = flVideoSt<Config>;
};
export template<typename Config>
class xpFilterUniqInverted : public virtual blockPortBase
{
public:
    // src ports
    // flVideoIf->External: Parameterized pixel push/ack stream
    push_ack_in< flVideoSt<Config> > videoOut;

    // dst ports
    // External->flVideoIf: Parameterized pixel push/ack stream
    push_ack_out< flVideoSt<Config> > videoIn;


    xpFilterUniqInverted(std::string name) :
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
class xpFilterUniqChannels
{
public:
    // src ports
    // Parameterized pixel push/ack stream
    push_ack_channel< flVideoSt<Config> > videoOut;

    // dst ports
    // Parameterized pixel push/ack stream
    push_ack_channel< flVideoSt<Config> > videoIn;


    xpFilterUniqChannels(std::string name, std::string srcName) :
    videoOut(("videoOut"+name).c_str(), srcName)
    ,videoIn(("videoIn"+name).c_str(), srcName)
    {};
    void bind( xpFilterUniqBase<Config> *a, xpFilterUniqInverted<Config> *b)
    {
        a->videoOut( videoOut );
        b->videoOut( videoOut );
        a->videoIn( videoIn );
        b->videoIn( videoIn );
    };
};

// GENERATED_CODE_END
