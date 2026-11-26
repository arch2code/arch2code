//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseTock --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module uvmReuse_uvmReuseTock.base;
import uvmReuse;
using namespace uvmReuse_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseTockBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseTockBase() = default;
    // dst ports
    // uTick->uvmReuseTickIf: Tick counts
    push_ack_in< uvmReuseCountSt > in;


    uvmReuseTockBase(std::string name, const char * variant) :
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
export class uvmReuseTockInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uTick->uvmReuseTickIf: Tick counts
    push_ack_out< uvmReuseCountSt > in;


    uvmReuseTockInverted(std::string name) :
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
export class uvmReuseTockChannels
{
public:
    // dst ports
    // Tick counts
    push_ack_channel< uvmReuseCountSt > in;


    uvmReuseTockChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName)
    {};
    void bind( uvmReuseTockBase *a, uvmReuseTockInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
