//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseLeafSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module uvmReuseLeaf_uvmReuseLeafSink.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseLeafSinkBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseLeafSinkBase() = default;
    // dst ports
    // u_uvmReuseLeaf->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > in;


    uvmReuseLeafSinkBase(std::string name, const char * variant) :
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
export class uvmReuseLeafSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_uvmReuseLeaf->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > in;


    uvmReuseLeafSinkInverted(std::string name) :
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
export class uvmReuseLeafSinkChannels
{
public:
    // dst ports
    // Packets, one word per beat
    rdy_vld_channel< uvmReuseBeatSt > in;


    uvmReuseLeafSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmReuseLeafSinkBase *a, uvmReuseLeafSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
