//

// GENERATED_CODE_PARAM --block=bvhTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "rdy_vld_channel.h"

export module bfmVlHandover_bvhTop.base;
import bfmVlHandover_bvh;
using namespace bfmVlHandover_bvh_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class bvhTopBase : public virtual blockPortBase
{
public:
    virtual ~bvhTopBase() = default;


    bvhTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class bvhTopInverted : public virtual blockPortBase
{
public:


    bvhTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class bvhTopChannels
{
public:


    bvhTopChannels(std::string name, std::string srcName)
    {};
    void bind( bvhTopBase *a, bvhTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
