//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideoSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "axi4_stream_channel.h"

export module uvmVideo_uvmVideoSink.base;
import uvmVideo;
using namespace uvmVideo_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmVideoSinkBase : public virtual blockPortBase
{
public:
    virtual ~uvmVideoSinkBase() = default;
    // dst ports
    // u_uvmVideo->uvmVideoAxisIf: UG934 video
    axi4_stream_in< uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt > in;


    uvmVideoSinkBase(std::string name, const char * variant) :
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
};
export class uvmVideoSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_uvmVideo->uvmVideoAxisIf: UG934 video
    axi4_stream_out< uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt > in;


    uvmVideoSinkInverted(std::string name) :
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
export class uvmVideoSinkChannels
{
public:
    // dst ports
    // UG934 video
    axi4_stream_channel< uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, uvmVideoUserSt > in;


    uvmVideoSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName, BACKPRESSURE_NONE)
    {};
    void bind( uvmVideoSinkBase *a, uvmVideoSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
