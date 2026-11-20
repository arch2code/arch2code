//copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmReuseSink --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module uvmReuse_uvmReuseSink.base;
import uvmReuseLeaf;
using namespace uvmReuseLeaf_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class uvmReuseSinkBase : public virtual blockPortBase
{
public:
    virtual ~uvmReuseSinkBase() = default;
    // dst ports
    // u_uvmReuseChain->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_in< uvmReuseBeatSt > in;


    uvmReuseSinkBase(std::string name, const char * variant) :
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
export class uvmReuseSinkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // u_uvmReuseChain->uvmReuseStreamIf: Packets, one word per beat
    rdy_vld_out< uvmReuseBeatSt > in;


    uvmReuseSinkInverted(std::string name) :
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
export class uvmReuseSinkChannels
{
public:
    // dst ports
    // Packets, one word per beat
    rdy_vld_channel< uvmReuseBeatSt > in;


    uvmReuseSinkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( uvmReuseSinkBase *a, uvmReuseSinkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
