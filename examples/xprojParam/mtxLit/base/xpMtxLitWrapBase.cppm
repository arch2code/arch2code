//

// GENERATED_CODE_PARAM --block=xpMtxLitWrap --mode=module
// GENERATED_CODE_BEGIN --template=moduleScaffold --section=baseModuleHeader
module;
#include "systemc.h"
#include "push_ack_channel.h"

export module xpMtxLit_xpMtxLitWrap.base;
import xpMtxLit_xpMtxLitTop;
import xpMtxIp;
using namespace xpMtxLit_xpMtxLitTop_ns;
using namespace xpMtxIp_ns;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=baseClassDecl

export class xpMtxLitWrapBase : public virtual blockPortBase
{
public:
    virtual ~xpMtxLitWrapBase() = default;


    xpMtxLitWrapBase(std::string name, const char * variant) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxLitWrapInverted : public virtual blockPortBase
{
public:


    xpMtxLitWrapInverted(std::string name) 
    {};
    void setTimed(int nsec, timedDelayMode mode) override
    {
        setTimedLocal(nsec, mode);
    };
    void setLogging(verbosity_e verbosity) override
    {
    };
};
export class xpMtxLitWrapChannels
{
public:


    xpMtxLitWrapChannels(std::string name, std::string srcName) 
    {};
    void bind( xpMtxLitWrapBase *a, xpMtxLitWrapInverted *b)
    {
    };
};

// GENERATED_CODE_END
