//

// GENERATED_CODE_PARAM --block=bvhSnk --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module bfmVlHandover_bvhSnk.base;
import bfmVlHandover_bvh;
using namespace bfmVlHandover_bvh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bvhSnkBase : public virtual blockPortBase
{
public:
    virtual ~bvhSnkBase() = default;
    // dst ports
    // uFifo->bvhIf: Beat stream
    rdy_vld_in< bvhBeat > in;


    bvhSnkBase(std::string name, const char * variant) :
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
export class bvhSnkInverted : public virtual blockPortBase
{
public:
    // dst ports
    // uFifo->bvhIf: Beat stream
    rdy_vld_out< bvhBeat > in;


    bvhSnkInverted(std::string name) :
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
export class bvhSnkChannels
{
public:
    // dst ports
    // Beat stream
    rdy_vld_channel< bvhBeat > in;


    bvhSnkChannels(std::string name, std::string srcName) :
    in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( bvhSnkBase *a, bvhSnkInverted *b)
    {
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
