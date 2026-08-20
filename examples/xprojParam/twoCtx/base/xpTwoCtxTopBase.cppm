//

// GENERATED_CODE_PARAM --block=xpTwoCtxTop --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "blockBase.h"

export module xpTwoCtx_xpTwoCtxTop.base;
import xpTwoCtx;
using namespace xpTwoCtx_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpTwoCtxTopBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxTopBase() = default;


    xpTwoCtxTopBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpTwoCtxTopInverted : public virtual blockPortBase
{
public:


    xpTwoCtxTopInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpTwoCtxTopChannels
{
public:


    xpTwoCtxTopChannels(std::string name, std::string srcName) 
    {};
    void bind( xpTwoCtxTopBase *a, xpTwoCtxTopInverted *b)
    {
    };
};

// GENERATED_CODE_END
