//

// GENERATED_CODE_PARAM --block=xpTwoCtxWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpTwoCtx_xpTwoCtxWrap.base;
import xpDpLeaf;
import xpTwoCtx;
using namespace xpDpLeaf_ns;
using namespace xpTwoCtx_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpTwoCtxWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxWrapBase() = default;


    xpTwoCtxWrapBase(std::string name, const char * variant)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpTwoCtxWrapInverted : public virtual blockPortBase
{
public:


    xpTwoCtxWrapInverted(std::string name)
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpTwoCtxWrapChannels
{
public:


    xpTwoCtxWrapChannels(std::string name, std::string srcName)
    {};
    void bind( xpTwoCtxWrapBase *a, xpTwoCtxWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
