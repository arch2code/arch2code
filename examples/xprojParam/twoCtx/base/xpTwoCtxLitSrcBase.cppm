//

// GENERATED_CODE_PARAM --block=xpTwoCtxLitSrc --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpTwoCtx_xpTwoCtxLitSrc.base;
import xpTwoCtx;
using namespace xpTwoCtx_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpTwoCtxLitSrcBase : public virtual blockPortBase
{
public:
    virtual ~xpTwoCtxLitSrcBase() = default;
    // src ports
    // litIf->uBare: Literal, non-parameterizable stream
    push_ack_out< litSt > litOut;


    xpTwoCtxLitSrcBase(std::string name, const char * variant) :
        litOut("litOut")
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        litOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        litOut->setLogging(verbosity);
    };
};
export class xpTwoCtxLitSrcInverted : public virtual blockPortBase
{
public:
    // src ports
    // litIf->uBare: Literal, non-parameterizable stream
    push_ack_in< litSt > litOut;


    xpTwoCtxLitSrcInverted(std::string name) :
        litOut(("litOut"+name).c_str())
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        litOut->setTimed(nsec, mode);
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
        litOut->setLogging(verbosity);
    };
};
export class xpTwoCtxLitSrcChannels
{
public:
    // src ports
    // Literal, non-parameterizable stream
    push_ack_channel< litSt > litOut;


    xpTwoCtxLitSrcChannels(std::string name, std::string srcName) :
    litOut(("litOut"+name).c_str(), srcName)
    {};
    void bind( xpTwoCtxLitSrcBase *a, xpTwoCtxLitSrcInverted *b)
    {
        a->litOut( litOut );
        b->litOut( litOut );
    };
};

// GENERATED_CODE_END
