//

// GENERATED_CODE_PARAM --block=bvhSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module bfmVlHandover_bvhSrc.base;
import bfmVlHandover_bvh;
using namespace bfmVlHandover_bvh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bvhSrcBase : public virtual blockPortBase
{
public:
    virtual ~bvhSrcBase() = default;
    // src ports
    // bvhIf->uFifo: Beat stream
    rdy_vld_out< bvhBeat > out;


    bvhSrcBase(std::string name, const char * variant) :
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
export class bvhSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // bvhIf->uFifo: Beat stream
    rdy_vld_in< bvhBeat > out;


    bvhSrcInverted(std::string name) :
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
export class bvhSrcChannels
{
public:
    // src ports
    // Beat stream
    rdy_vld_channel< bvhBeat > out;


    bvhSrcChannels(std::string name, std::string srcName) :
    out(("out"+name).c_str(), srcName, BACKPRESSURE_ALLOWED)
    {};
    void bind( bvhSrcBase *a, bvhSrcInverted *b)
    {
        a->out( out );
        b->out( out );
    };
};

// GENERATED_CODE_END
