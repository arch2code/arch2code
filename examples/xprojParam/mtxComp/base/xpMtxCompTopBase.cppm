//

// GENERATED_CODE_PARAM --block=xpMtxCompTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpMtxComp_xpMtxCompTop.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxCompTopBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxCompTopBase() = default;


    xpMtxCompTopBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxCompTopInverted : public virtual blockPortBase
{
public:


    xpMtxCompTopInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxCompTopChannels
{
public:


    xpMtxCompTopChannels(std::string name, std::string srcName)
    {};
    void bind( xpMtxCompTopBase *a, xpMtxCompTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
