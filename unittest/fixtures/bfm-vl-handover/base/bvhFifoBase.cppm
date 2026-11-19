//

// GENERATED_CODE_PARAM --block=bvhFifo --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module bfmVlHandover_bvhFifo.base;
import bfmVlHandover_bvh;
using namespace bfmVlHandover_bvh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bvhFifoBase : public virtual blockPortBase
{
public:
    virtual ~bvhFifoBase() = default;
    // src ports
    // bvhIf->uSnk: Beat stream
    rdy_vld_out< bvhBeat > out;

    // dst ports
    // uSrc->bvhIf: Beat stream
    rdy_vld_in< bvhBeat > in;


    bvhFifoBase(std::string name, const char * variant) :
        out("out")
        ,in("in")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export class bvhFifoInverted : public virtual blockPortBase
{
public:
    // src ports
    // bvhIf->uSnk: Beat stream
    rdy_vld_in< bvhBeat > out;

    // dst ports
    // uSrc->bvhIf: Beat stream
    rdy_vld_out< bvhBeat > in;


    bvhFifoInverted(std::string name) :
        out(("out"+name).c_str())
        ,in(("in"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        out->setTimed(nsec, mode);
        in->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        out->setLogging(verbosity);
        in->setLogging(verbosity);
    };
};
export class bvhFifoChannels
{
public:
    // src ports
    // Beat stream
    rdy_vld_channel< bvhBeat > out;

    // dst ports
    // Beat stream
    rdy_vld_channel< bvhBeat > in;


    bvhFifoChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    ,in(("in"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( bvhFifoBase *a, bvhFifoInverted *b)
    {
        a->out( out );
        b->out( out );
        a->in( in );
        b->in( in );
    };
};

// GENERATED_CODE_END
