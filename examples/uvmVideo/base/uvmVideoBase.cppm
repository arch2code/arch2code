//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi4_stream_channel.h"
#include "raw_channel.h"

export module uvmVideo.base;
import uvmVideo;
using namespace uvmVideo_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmVideoBase : public virtual blockPortBase
{
public:
    virtual ~uvmVideoBase() = default;
    // src ports
    // uvmVideoAxisIf->uSink: UG934 video
    axi4_stream_out< uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt > vout;

    // dst ports
    // uSrc->uvmVideoRawIf: Raw video, one beat per clock
    raw_in< uvmVideoRawSt > vin;


    uvmVideoBase(std::string name, const char * variant) :
        vout("vout")
        ,vin("vin")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        vout->setTimed(nsec, mode);
        vin->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        vout->setLogging(verbosity);
        vin->setLogging(verbosity);
    };
};
export class uvmVideoInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmVideoAxisIf->uSink: UG934 video
    axi4_stream_in< uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt > vout;

    // dst ports
    // uSrc->uvmVideoRawIf: Raw video, one beat per clock
    raw_out< uvmVideoRawSt > vin;


    uvmVideoInverted(std::string name) :
        vout(("vout"+name).c_str())
        ,vin(("vin"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        vout->setTimed(nsec, mode);
        vin->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        vout->setLogging(verbosity);
        vin->setLogging(verbosity);
    };
};
export class uvmVideoChannels
{
public:
    // src ports
    // UG934 video
    axi4_stream_channel< uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt > vout;

    // dst ports
    // Raw video, one beat per clock
    raw_channel< uvmVideoRawSt > vin;


    uvmVideoChannels(std::string name, std::string srcName) :
    vout(("vout"+name).c_str(), srcName, BACKPRESSURE_NONE)
    ,vin(("vin"+name).c_str(), srcName)
    {};
    void bind( uvmVideoBase *a, uvmVideoInverted *b)
    {
        a->vout( vout );
        b->vout( vout );
        a->vin( vin );
        b->vin( vin );
    };
};

// GENERATED_CODE_END
