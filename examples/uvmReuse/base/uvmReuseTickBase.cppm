//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseTick --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module uvmReuse_uvmReuseTick.base;
import uvmReuse;
using namespace uvmReuse_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseTickBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseTickBase() = default;
    // src ports
    // uvmReuseTickIf->uTock: Tick counts
    push_ack_out< uvmReuseCountSt > out;


    uvmReuseTickBase(std::string name, const char * variant) :
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
export class uvmReuseTickInverted : public virtual blockPortBase
{
public:
    // src ports
    // uvmReuseTickIf->uTock: Tick counts
    push_ack_in< uvmReuseCountSt > out;


    uvmReuseTickInverted(std::string name) :
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
export class uvmReuseTickChannels
{
public:
    // src ports
    // Tick counts
    push_ack_channel< uvmReuseCountSt > out;


    uvmReuseTickChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName)
    {};
    void bind( uvmReuseTickBase *a, uvmReuseTickInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
