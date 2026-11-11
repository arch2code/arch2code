//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMemSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module uvmMem_uvmMemSink.base;
import uvmMem;
using namespace uvmMem_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmMemSinkBase : public virtual blockPortBase
{
public:
    virtual ~uvmMemSinkBase() = default;
    // dst ports
    // u_uvmMem->uvmMemWordIf: Words read back
    rdy_vld_in< uvmMemWordSt > in;


    uvmMemSinkBase(std::string name, const char * variant) :
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
export class uvmMemSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_uvmMem->uvmMemWordIf: Words read back
    rdy_vld_out< uvmMemWordSt > in;


    uvmMemSinkInverted(std::string name) :
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
export class uvmMemSinkChannels
{
public:
    // dst ports
    // Words read back
    rdy_vld_channel< uvmMemWordSt > in;


    uvmMemSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmMemSinkBase *a, uvmMemSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
