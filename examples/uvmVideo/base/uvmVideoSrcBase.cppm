//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideoSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "raw_channel.h"

export module uvmVideo_uvmVideoSrc.base;
import uvmVideo;
using namespace uvmVideo_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmVideoSrcBase : public virtual blockPortBase
{
public:
    virtual ~uvmVideoSrcBase() = default;
    // src ports
    // uvmVideoRawIf->u_uvmVideo: Raw video, one beat per clock
    raw_out< uvmVideoRawSt > out;


    uvmVideoSrcBase(std::string name, const char * variant) :
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
};
export class uvmVideoSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmVideoRawIf->u_uvmVideo: Raw video, one beat per clock
    raw_in< uvmVideoRawSt > out;


    uvmVideoSrcInverted(std::string name) :
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
export class uvmVideoSrcChannels
{
public:
    // src ports
    // Raw video, one beat per clock
    raw_channel< uvmVideoRawSt > out;


    uvmVideoSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( uvmVideoSrcBase *a, uvmVideoSrcInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
