//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module uvmReuseLeaf_uvmReuseLeafSrc.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseLeafSrcBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseLeafSrcBase() = default;
    // src ports
    // uvmReuseVideoIf->u_uvmReuseLeaf: Video, one pixel per beat
    rdy_vld_out< uvmReuseBeatSt > out;


    uvmReuseLeafSrcBase(std::string name, const char * variant) :
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
export class uvmReuseLeafSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmReuseVideoIf->u_uvmReuseLeaf: Video, one pixel per beat
    rdy_vld_in< uvmReuseBeatSt > out;


    uvmReuseLeafSrcInverted(std::string name) :
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
export class uvmReuseLeafSrcChannels
{
public:
    // src ports
    // Video, one pixel per beat
    rdy_vld_channel< uvmReuseBeatSt > out;


    uvmReuseLeafSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmReuseLeafSrcBase *a, uvmReuseLeafSrcInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
